"""
Road Pothole Tracker & Surface Quality Profiler
Designed for forward-moving dashcam footage and automated road maintenance inspection.
"""

import numpy as np
import cv2

class RoadPotholeTracker:
    def __init__(self, iou_thresh=0.20, max_dist=140, max_lost_frames=6, min_hits=1, hood_cutoff=0.92):
        """
        Parameters:
            iou_thresh: IoU overlap threshold to consider the same pothole.
            max_dist: Maximum pixel distance between consecutive detections of the same pothole.
            max_lost_frames: Frames to wait before closing a track permanently.
            min_hits: Minimum detections across frames to qualify as a confirmed pothole.
            hood_cutoff: Normalized Y coordinate (0-1) where vehicle hood starts and potholes exit.
        """
        self.iou_thresh = iou_thresh
        self.max_dist = max_dist
        self.max_lost_frames = max_lost_frames
        self.min_hits = min_hits
        self.hood_cutoff = hood_cutoff
        
        self.next_id = 1
        self.active_tracks = {}   # tid -> track dict
        self.closed_tracks = {}   # tid -> track dict
        self.all_records = {}     # tid -> metadata dict

    def reset(self):
        """Reset tracker state completely."""
        self.next_id = 1
        self.active_tracks.clear()
        self.closed_tracks.clear()
        self.all_records.clear()

    @staticmethod
    def calculate_iou(boxA, boxB):
        xA = max(boxA[0], boxB[0])
        yA = max(boxA[1], boxB[1])
        xB = min(boxA[2], boxB[2])
        yB = min(boxA[3], boxB[3])
        inter_area = max(0, xB - xA) * max(0, yB - yA)
        boxA_area = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
        boxB_area = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
        union_area = boxA_area + boxB_area - inter_area
        return inter_area / union_area if union_area > 0 else 0.0

    @staticmethod
    def extract_crop(frame, bbox, margin=0.25):
        """Extract a bounding box crop with margin safely within frame bounds."""
        H, W = frame.shape[:2]
        x1, y1, x2, y2 = bbox
        bw = x2 - x1
        bh = y2 - y1
        cx1 = max(0, int(x1 - margin * bw))
        cy1 = max(0, int(y1 - margin * bh))
        cx2 = min(W, int(x2 + margin * bw))
        cy2 = min(H, int(y2 + margin * bh))
        if cx2 > cx1 and cy2 > cy1:
            return frame[cy1:cy2, cx1:cx2].copy()
        return frame[int(max(0, y1)):int(min(H, y2)), int(max(0, x1)):int(min(W, x2))].copy()

    @staticmethod
    def classify_severity(width, height, area):
        """Classify pothole severity into Minor, Moderate, or Severe based on size."""
        if area >= 4500 or max(width, height) >= 85:
            return "Severe"
        elif area >= 1800 or max(width, height) >= 50:
            return "Moderate"
        else:
            return "Minor"

    def update(self, detections, confidences, raw_frame, annotated_frame, frame_idx, timestamp_sec):
        """
        Update tracker with current frame detections.
        detections: list of [x1, y1, x2, y2]
        confidences: list of float confidences
        raw_frame: clean BGR frame (for crops)
        annotated_frame: BGR frame with drawn boxes
        frame_idx: current video frame index
        timestamp_sec: current video timestamp in seconds
        
        Returns:
            assigned_ids: list of track IDs corresponding to detections in this frame.
        """
        H, W = raw_frame.shape[:2]
        num_dets = len(detections)
        assigned_ids = [None] * num_dets
        active_tids = list(self.active_tracks.keys())

        # Scale max_dist by frame resolution
        dynamic_max_dist = self.max_dist * (H / 720.0)

        # Association step
        if active_tids and num_dets > 0:
            cost_matrix = []
            for tid in active_tids:
                t_box = self.active_tracks[tid]['bbox']
                t_cx = (t_box[0] + t_box[2]) / 2.0
                t_cy = (t_box[1] + t_box[3]) / 2.0
                row = []
                for det in detections:
                    d_cx = (det[0] + det[2]) / 2.0
                    d_cy = (det[1] + det[3]) / 2.0
                    iou = self.calculate_iou(t_box, det)
                    dist = float(np.hypot(d_cx - t_cx, d_cy - t_cy))
                    
                    # Direction check: static objects on road move downward (+Y) as camera moves forward
                    is_forward_direction = (d_cy >= t_cy - 25)
                    
                    if iou > self.iou_thresh:
                        cost = (1.0 - iou) * 30.0
                    elif dist < dynamic_max_dist and is_forward_direction:
                        cost = dist
                    else:
                        cost = 1e8  # Ineligible match
                    row.append(cost)
                cost_matrix.append(row)

            # Greedy Hungarian-style matching
            matches = []
            for t_idx, tid in enumerate(active_tids):
                for d_idx in range(num_dets):
                    c = cost_matrix[t_idx][d_idx]
                    if c < 1e7:
                        matches.append((c, t_idx, d_idx))
            matches.sort(key=lambda x: x[0])

            used_tracks = set()
            used_dets = set()
            for c, t_idx, d_idx in matches:
                tid = active_tids[t_idx]
                if tid in used_tracks or d_idx in used_dets:
                    continue
                used_tracks.add(tid)
                used_dets.add(d_idx)
                assigned_ids[d_idx] = tid
                
                det = detections[d_idx]
                conf = confidences[d_idx]
                track = self.active_tracks[tid]
                track['bbox'] = det
                track['lost'] = 0
                track['hits'] += 1
                track['last_frame'] = frame_idx
                track['last_sec'] = timestamp_sec

                bw = int(det[2] - det[0])
                bh = int(det[3] - det[1])
                b_area = bw * bh
                if b_area > track['max_area']:
                    track['max_area'] = b_area
                    track['width'] = bw
                    track['height'] = bh
                    track['severity'] = self.classify_severity(bw, bh, b_area)
                
                if conf > track['max_conf']:
                    track['max_conf'] = conf
                    crop = self.extract_crop(raw_frame, det)
                    if crop.size > 0:
                        track['crop'] = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
                    track['annotated_snapshot'] = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)

            # Age unmatched tracks
            for tid in active_tids:
                if tid not in used_tracks:
                    self.active_tracks[tid]['lost'] += 1

        else:
            for tid in active_tids:
                self.active_tracks[tid]['lost'] += 1

        # Check tracks that exited or have been lost for too long -> finalize & close
        for tid in list(self.active_tracks.keys()):
            track = self.active_tracks[tid]
            box = track['bbox']
            exited_hood = (box[3] >= H * self.hood_cutoff)
            lost_too_long = (track['lost'] > self.max_lost_frames)
            
            if exited_hood or lost_too_long:
                if track['hits'] >= self.min_hits:
                    self.closed_tracks[tid] = track
                del self.active_tracks[tid]

        # Initialize new tracks for unmatched detections
        for d_idx in range(num_dets):
            if assigned_ids[d_idx] is None:
                tid = self.next_id
                self.next_id += 1
                assigned_ids[d_idx] = tid
                det = detections[d_idx]
                conf = confidences[d_idx]
                
                crop = self.extract_crop(raw_frame, det)
                rgb_crop = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB) if crop.size > 0 else None
                rgb_full = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
                
                bw = int(det[2] - det[0])
                bh = int(det[3] - det[1])
                b_area = bw * bh
                severity = self.classify_severity(bw, bh, b_area)

                new_track = {
                    'track_id': tid,
                    'bbox': det,
                    'width': bw,
                    'height': bh,
                    'max_area': b_area,
                    'severity': severity,
                    'lost': 0,
                    'hits': 1,
                    'max_conf': conf,
                    'first_frame': frame_idx,
                    'first_sec': timestamp_sec,
                    'last_frame': frame_idx,
                    'last_sec': timestamp_sec,
                    'crop': rgb_crop,
                    'annotated_snapshot': rgb_full
                }
                self.active_tracks[tid] = new_track
                self.all_records[tid] = new_track

        return assigned_ids

    def get_confirmed_records(self):
        """Return all records that meet min_hits threshold."""
        combined = {**self.closed_tracks, **self.active_tracks}
        return {tid: rec for tid, rec in combined.items() if rec['hits'] >= self.min_hits}

    @staticmethod
    def compute_road_ranking_profile(road_name, records, duration_sec, frames_analyzed):
        """
        Compute road health rating, damage indices, and ranking profile based on physical parameters:
        - Pothole Density (Count per minute)
        - Severity Distribution (Minor, Moderate, Severe)
        - Cumulative Damaged Area
        - Pavement Health Score (0 - 100)
        - Maintenance Urgency
        """
        pothole_list = list(records.values())
        total_potholes = len(pothole_list)
        duration_min = max(0.1, duration_sec / 60.0)

        num_minor = sum(1 for p in pothole_list if p.get('severity') == 'Minor')
        num_mod = sum(1 for p in pothole_list if p.get('severity') == 'Moderate')
        num_severe = sum(1 for p in pothole_list if p.get('severity') == 'Severe')
        total_damage_area_px = sum(p.get('max_area', 0) for p in pothole_list)

        avg_conf = round(float(np.mean([p['max_conf'] for p in pothole_list])), 2) if pothole_list else 0.0
        potholes_per_min = round(total_potholes / duration_min, 1)

        # Civil Engineering Pavement Condition Index (PCI) Model
        damage_penalty = ((1.5 * num_minor) + (4.5 * num_mod) + (10.0 * num_severe)) / duration_min
        health_score = round(max(0.0, min(100.0, 100.0 - (damage_penalty * 2.2))), 1)

        if health_score >= 88.0:
            rating = "Excellent"
            urgency = "No Immediate Action"
            urgency_level = 1
        elif health_score >= 70.0:
            rating = "Good"
            urgency = "Routine Monitoring"
            urgency_level = 2
        elif health_score >= 50.0:
            rating = "Fair (Moderate)"
            urgency = "Scheduled Repair (30 Days)"
            urgency_level = 3
        elif health_score >= 30.0:
            rating = "Poor (At Risk)"
            urgency = "Priority Repair (7 Days)"
            urgency_level = 4
        else:
            rating = "Critical (Hazardous)"
            urgency = "Emergency Intervention"
            urgency_level = 5

        return {
            "Road Name": road_name,
            "Health Score (0-100)": health_score,
            "Condition Rating": rating,
            "Maintenance Urgency": urgency,
            "Urgency Level": urgency_level,
            "Total Potholes": total_potholes,
            "Severe Potholes": num_severe,
            "Moderate Potholes": num_mod,
            "Minor Potholes": num_minor,
            "Pothole Density (/min)": potholes_per_min,
            "Total Damaged Area (px²)": total_damage_area_px,
            "Avg Confidence": avg_conf,
            "Duration (s)": round(duration_sec, 1),
            "Frames Evaluated": frames_analyzed
        }

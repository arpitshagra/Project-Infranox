"""
Road Pothole Tracker & Surface Quality Profiler - Production Multi-Object Tracker
Specifically engineered for moving dashcam footage and automated road maintenance inspection.
Solves duplicate counting caused by nested/split YOLO detections, perspective jumps, and flicker.
"""

import numpy as np
import cv2

class RoadPotholeTracker:
    def __init__(self, iou_thresh=0.15, max_dist=180, max_lost_frames=15, min_hits=3, hood_cutoff=0.96):
        """
        Parameters:
            iou_thresh: IoU overlap threshold to associate consecutive detections.
            max_dist: Maximum pixel distance between consecutive detections of the same physical pothole.
            max_lost_frames: Number of frames to keep a lost track alive before closing it permanently.
            min_hits: Minimum confirmed detections across frames required to register as a real unique pothole.
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
        """Calculate standard Intersection over Union (IoU)."""
        xA = max(boxA[0], boxB[0])
        yA = max(boxA[1], boxB[1])
        xB = min(boxA[2], boxB[2])
        yB = min(boxA[3], boxB[3])
        inter_w = max(0, xB - xA)
        inter_h = max(0, yB - yA)
        inter_area = inter_w * inter_h
        if inter_area == 0:
            return 0.0
        boxA_area = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
        boxB_area = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
        union_area = boxA_area + boxB_area - inter_area
        return inter_area / union_area if union_area > 0 else 0.0

    @staticmethod
    def calculate_containment(boxA, boxB):
        """Calculate intersection over smaller box area (detects nested/subset duplicate boxes)."""
        xA = max(boxA[0], boxB[0])
        yA = max(boxA[1], boxB[1])
        xB = min(boxA[2], boxB[2])
        yB = min(boxA[3], boxB[3])
        inter_w = max(0, xB - xA)
        inter_h = max(0, yB - yA)
        inter_area = inter_w * inter_h
        if inter_area == 0:
            return 0.0
        boxA_area = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
        boxB_area = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
        min_area = min(boxA_area, boxB_area)
        return inter_area / min_area if min_area > 0 else 0.0

    @classmethod
    def filter_duplicate_frame_detections(cls, detections, confidences, containment_thresh=0.55):
        """
        Merge/suppress duplicate YOLO predictions in the SAME frame covering the same pothole.
        YOLO frequently predicts two overlapping or nested bounding boxes for one large pothole.
        """
        if len(detections) <= 1:
            return detections, confidences

        # Sort by confidence descending
        indices = sorted(range(len(confidences)), key=lambda i: confidences[i], reverse=True)
        keep = []
        
        for idx in indices:
            box = detections[idx]
            is_dup = False
            for k in keep:
                kept_box = detections[k]
                iou = cls.calculate_iou(box, kept_box)
                containment = cls.calculate_containment(box, kept_box)
                if iou > 0.40 or containment > containment_thresh:
                    is_dup = True
                    break
            if not is_dup:
                keep.append(idx)

        # Restore original order or sorted by keep
        keep.sort()
        filtered_dets = [detections[i] for i in keep]
        filtered_confs = [confidences[i] for i in keep]
        return filtered_dets, filtered_confs

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
        Pre-filters intra-frame nested duplicate boxes, then associates with active tracks.
        """
        H, W = raw_frame.shape[:2]

        # STEP 1: Eliminate same-frame duplicate / nested boxes
        clean_dets, clean_confs = self.filter_duplicate_frame_detections(detections, confidences)
        num_dets = len(clean_dets)
        assigned_ids = [None] * num_dets
        active_tids = list(self.active_tracks.keys())

        # Dynamic search distance based on vertical resolution and lane perspective
        dynamic_max_dist = self.max_dist * (H / 720.0)

        # STEP 2: Match detections to active tracks
        if active_tids and num_dets > 0:
            cost_matrix = []
            for tid in active_tids:
                t = self.active_tracks[tid]
                t_box = t['bbox']
                t_cx = (t_box[0] + t_box[2]) / 2.0
                t_cy = (t_box[1] + t_box[3]) / 2.0
                t_w = t_box[2] - t_box[0]
                t_h = t_box[3] - t_box[1]

                row = []
                for det in clean_dets:
                    d_cx = (det[0] + det[2]) / 2.0
                    d_cy = (det[1] + det[3]) / 2.0
                    d_w = det[2] - det[0]
                    d_h = det[3] - det[1]

                    iou = self.calculate_iou(t_box, det)
                    containment = self.calculate_containment(t_box, det)
                    dist = float(np.hypot(d_cx - t_cx, d_cy - t_cy))

                    # Vehicle forward motion geometry:
                    # Road potholes strictly move DOWN (+Y) in camera coordinates as vehicle approaches.
                    # As vehicle draws near, apparent size expands (d_w >= t_w * 0.7).
                    # Allow slight negative vertical tolerance (-35px) for vehicle bounce/pitch.
                    y_delta = d_cy - t_cy
                    is_forward_or_stationary = (y_delta >= -35)

                    # Dynamic distance threshold expands if the object was lost for a few frames
                    frames_gap = max(1, t['lost'] + 1)
                    allowable_dist = dynamic_max_dist * (1.0 + 0.35 * frames_gap)

                    if iou > 0.10 or containment > 0.35:
                        # Direct spatial overlap
                        cost = (1.0 - max(iou, containment * 0.8)) * 30.0
                    elif dist < allowable_dist and is_forward_or_stationary:
                        # Spatial proximity matching in forward trajectory
                        cost = dist
                    else:
                        cost = 1e8  # Ineligible match
                    row.append(cost)
                cost_matrix.append(row)

            # Greedy optimal association
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
                
                det = clean_dets[d_idx]
                conf = clean_confs[d_idx]
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

            # Increment lost counter for unmatched tracks
            for tid in active_tids:
                if tid not in used_tracks:
                    self.active_tracks[tid]['lost'] += 1
        else:
            for tid in active_tids:
                self.active_tracks[tid]['lost'] += 1

        # STEP 3: Close tracks that exited near vehicle hood or exceeded max_lost_frames
        for tid in list(self.active_tracks.keys()):
            track = self.active_tracks[tid]
            box = track['bbox']
            exited_hood = (box[3] >= H * self.hood_cutoff)
            lost_too_long = (track['lost'] > self.max_lost_frames)
            
            if exited_hood or lost_too_long:
                if track['hits'] >= self.min_hits:
                    self.closed_tracks[tid] = track
                del self.active_tracks[tid]

        # STEP 4: Initialize new tracks for unmatched detections
        for d_idx in range(num_dets):
            if assigned_ids[d_idx] is None:
                tid = self.next_id
                self.next_id += 1
                assigned_ids[d_idx] = tid
                det = clean_dets[d_idx]
                conf = clean_confs[d_idx]
                
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

        return clean_dets, clean_confs, assigned_ids

    def get_confirmed_records(self):
        """Return all unique records that meet min_hits threshold."""
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

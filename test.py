import os
import cv2
import pandas as pd
from ultralytics import YOLO
from tracker import RoadPotholeTracker

# Load pretrained pothole model
model = YOLO("best.pt")

# Input source: use 0 for webcam, or video path
video_source = "road2.mp4"
if not os.path.exists(video_source):
    downloads_path = os.path.expanduser(r"~\Downloads\road2.mp4")
    if os.path.exists(downloads_path):
        video_source = downloads_path
    else:
        video_source = 0

road_name = os.path.splitext(os.path.basename(str(video_source)))[0]
print(f"Opening input source: {video_source} (Road: {road_name})")

cap = cv2.VideoCapture(video_source)
if not cap.isOpened():
    print(f"Error: Could not open {video_source}")
    exit(1)

fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
tracker = RoadPotholeTracker(iou_thresh=0.15, max_dist=180, max_lost_frames=15, min_hits=3)

print("\n--- Starting Infranox Road Pothole Detection & Profiling ---")
frame_idx = 0
unique_detected_ids = set()

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    
    frame_idx += 1
    timestamp_sec = round(frame_idx / fps, 2)
    
    # Predict potholes at calibrated confidence threshold (0.20)
    results = model.predict(frame, conf=0.20, iou=0.50, imgsz=640, verbose=False)
    boxes = results[0].boxes
    annotated_frame = frame.copy()
    
    if len(boxes) > 0:
        xyxy = boxes.xyxy.cpu().numpy().tolist()
        confs = [round(float(c), 2) for c in boxes.conf.cpu().tolist()]
        
        clean_dets, clean_confs, assigned_ids = tracker.update(xyxy, confs, frame, annotated_frame, frame_idx, timestamp_sec)
        
        for box, tid, conf in zip(clean_dets, assigned_ids, clean_confs):
            if tid not in unique_detected_ids:
                unique_detected_ids.add(tid)
                bw = int(box[2] - box[0])
                bh = int(box[3] - box[1])
                sev = RoadPotholeTracker.classify_severity(bw, bh, bw * bh)
                print(f"🎯 New Unique Pothole Detected! [ID #{tid}] | Severity: {sev} | Conf: {conf:.2f} @ {timestamp_sec}s | Cumulative Real Potholes: {len(unique_detected_ids)}")
            
            x1, y1, x2, y2 = [int(v) for v in box]
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 165, 255), 2)
            cv2.putText(annotated_frame, f"Pothole #{tid} ({conf:.2f})", (x1, max(20, y1 - 8)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 2)

    # Optional live preview
    cv2.imshow("Infranox Road Pothole Tracking", annotated_frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

confirmed = tracker.get_confirmed_records()
duration_sec = frame_idx / fps if fps > 0 else 1.0

# 1. Export Pothole IDs to CSV
export_rows = []
for rec in sorted(confirmed.values(), key=lambda x: x["track_id"]):
    export_rows.append({
        "Pothole ID": rec["track_id"],
        "Road Name": road_name,
        "Severity": rec.get("severity", "Moderate"),
        "First Seen (s)": rec["first_sec"],
        "First Seen Frame": rec["first_frame"],
        "Last Seen (s)": rec.get("last_sec", rec["first_sec"]),
        "Width (px)": rec.get("width", 0),
        "Height (px)": rec.get("height", 0),
        "Area (px²)": rec.get("max_area", 0),
        "Highest Confidence": rec["max_conf"],
        "Frames Tracked (Hits)": rec["hits"]
    })

potholes_csv = "potholes_catalog.csv"
df_potholes = pd.DataFrame(export_rows)
df_potholes.to_csv(potholes_csv, index=False)
print(f"\n📁 Saved Pothole IDs Catalog to: {os.path.abspath(potholes_csv)}")

# 2. Compute Road Quality Ranking Profile
profile = RoadPotholeTracker.compute_road_ranking_profile(
    road_name=road_name,
    records=confirmed,
    duration_sec=duration_sec,
    frames_analyzed=frame_idx
)

print("\n" + "="*50)
print(f"📊 ROAD ASSESSMENT REPORT: {road_name}")
print("="*50)
print(f"Pavement Health Score: {profile['Health Score (0-100)']}/100")
print(f"Condition Rating:      {profile['Condition Rating']}")
print(f"Maintenance Urgency:   {profile['Maintenance Urgency']}")
print(f"Total Unique Potholes: {profile['Total Potholes']}")
print(f"  - Severe Potholes:   {profile['Severe Potholes']}")
print(f"  - Moderate Potholes: {profile['Moderate Potholes']}")
print(f"  - Minor Potholes:    {profile['Minor Potholes']}")
print(f"Pothole Density:       {profile['Pothole Density (/min)']} potholes/min")
print(f"Damaged Surface Area:  {profile['Total Damaged Area (px²)']:,} px²")
print("="*50)

road_csv = "road_assessment.csv"
df_road = pd.DataFrame([profile])
df_road.to_csv(road_csv, index=False)
print(f"📁 Saved Road Ranking Profile to: {os.path.abspath(road_csv)}")

import cv2
from ultralytics import YOLO

# Load pretrained pothole model
model = YOLO("best.pt")

# Set of unique persistent track IDs to eliminate duplicate counts
unique_potholes = set()

# Input source: use 0 for webcam, or "1.mp4" for video
video_source = "1.mp4"

# Run with ByteTrack multi-object tracking (Solution A)
# vid_stride skips frames to speed up processing
results = model.track(
    source=video_source,
    persist=True,
    tracker="bytetrack.yaml",
    conf=0.35,
    vid_stride=2,    # Process every 2nd frame (2x speed)
    stream=True,     # Stream results without RAM memory buildup
    show=True
)

print("\n--- Starting Pothole Tracking ---")
for r in results:
    if r.boxes.id is not None:
        track_ids = r.boxes.id.int().cpu().tolist()
        for tid in track_ids:
            if tid not in unique_potholes:
                unique_potholes.add(tid)
                print(f"🎯 New Unique Pothole Detected! [Pothole #{tid}] | Total Real Potholes: {len(unique_potholes)}")

print(f"\nFinal Result: Identified {len(unique_potholes)} unique physical potholes.")

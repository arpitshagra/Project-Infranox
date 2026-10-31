import os
import time
import tempfile
import cv2
import pandas as pd
import streamlit as st
from ultralytics import YOLO

# Page Configuration
st.set_page_config(
    page_title="Infranox - Pothole Detection & Tracking",
    page_icon="🚧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #64748B;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 12px;
        text-align: center;
    }
    .metric-val {
        font-size: 1.6rem;
        font-weight: bold;
        color: #0F172A;
    }
    .metric-lbl {
        font-size: 0.85rem;
        color: #64748B;
    }
    .badge-unique {
        background-color: #22C55E;
        color: white;
        padding: 3px 8px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# ----------------- Helper Functions -----------------
@st.cache_resource
def load_yolo_model(model_path="best.pt"):
    if not os.path.exists(model_path):
        return None
    return YOLO(model_path)


def get_video_info(video_path):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return None
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration_sec = total_frames / fps if fps > 0 else 0
    cap.release()
    return {
        "total_frames": total_frames,
        "fps": round(fps, 2),
        "width": width,
        "height": height,
        "duration_sec": round(duration_sec, 1)
    }

# ----------------- Header -----------------
st.markdown('<div class="main-title">🚧 Infranox Pothole Detection & Unique Tracking Studio</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Powered by <b>ByteTrack / BoT-SORT</b> multi-object tracking to eliminate duplicate pothole counts across video frames.</div>', unsafe_allow_html=True)

# ----------------- Sidebar Configuration -----------------
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Model Loading
    model_file = "best.pt"
    if os.path.exists(model_file):
        model = load_yolo_model(model_file)
        st.success(f"Model loaded: `{model_file}`")
        if model and hasattr(model, 'names'):
            st.caption(f"Target classes: {list(model.names.values())}")
    else:
        st.error(f"'{model_file}' not found in current directory!")
        model = None

    st.markdown("---")
    st.subheader("🎯 Tracking & Detection Settings")
    
    tracker_type = st.selectbox(
        "Multi-Object Tracker",
        options=["bytetrack.yaml", "botsort.yaml"],
        index=0,
        help="ByteTrack is fast and handles occlusions; BoT-SORT includes camera-motion compensation."
    )
    
    conf_thresh = st.slider(
        "Confidence Threshold",
        min_value=0.10,
        max_value=1.00,
        value=0.35,
        step=0.05,
        help="Minimum confidence score required to detect a pothole."
    )
    
    st.markdown("---")
    st.subheader("🎞️ Frame Adjustments (Sampling & Range)")
    st.info("Adjust frame skipping to process videos 3x–10x faster.")
    
    frame_step = st.slider(
        "Process Every Nth Frame (Frame Skip)",
        min_value=1,
        max_value=15,
        value=2,
        help="1 = process every frame (highest tracking fidelity)\n"
             "2 = process every 2nd frame (2x faster, recommended)\n"
             "5 = process every 5th frame (5x faster)\n"
             "10 = process every 10th frame (10x faster)"
    )

    save_annotated_video = st.checkbox(
        "Export Annotated Video (.mp4)",
        value=True,
        help="Generates an output video with tracking ID bounding boxes drawn."
    )

# ----------------- Video Source Selection -----------------
video_source_mode = st.radio(
    "Choose Video Source:",
    options=["Select Local Video from Workspace", "Upload Video File"],
    horizontal=True
)

active_video_path = None
temp_file_path = None

if video_source_mode == "Select Local Video from Workspace":
    workspace_videos = [f for f in os.listdir(".") if f.lower().endswith((".mp4", ".avi", ".mov", ".mkv")) and not f.startswith("output_")]
    if workspace_videos:
        selected_vid = st.selectbox("Available local videos:", workspace_videos, index=0)
        active_video_path = os.path.abspath(selected_vid)
    else:
        st.warning("No video files found in the workspace directory. Please upload one below.")

else:
    uploaded_file = st.file_uploader("Upload road video (MP4, AVI, MOV, MKV)", type=["mp4", "avi", "mov", "mkv"])
    if uploaded_file is not None:
        tfile = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        tfile.write(uploaded_file.read())
        tfile.flush()
        tfile.close()
        temp_file_path = tfile.name
        active_video_path = temp_file_path

# ----------------- Video Analysis & Frame Range Control -----------------
if active_video_path and os.path.exists(active_video_path):
    vid_info = get_video_info(active_video_path)
    
    if vid_info and vid_info["total_frames"] > 0:
        total_f = vid_info["total_frames"]
        
        # Display Video Information
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Resolution", f"{vid_info['width']} x {vid_info['height']}")
        col2.metric("Total Video Frames", f"{total_f:,}")
        col3.metric("Video FPS", f"{vid_info['fps']}")
        col4.metric("Duration", f"{vid_info['duration_sec']}s (~{round(vid_info['duration_sec']/60, 1)}m)")

        st.markdown("---")
        st.subheader("✂️ Frame Range Adjustment (Trimming)")
        
        # Frame Range Slider: user can adjust starting frame and ending frame
        default_max = min(total_f, 600) if total_f > 1000 else total_f
        frame_range = st.slider(
            "Select Frame Range to Analyze:",
            min_value=0,
            max_value=total_f,
            value=(0, default_max),
            step=1,
            help=f"Select the exact section of the video you want to process (0 to {total_f})."
        )
        
        start_frame, end_frame = frame_range
        selected_frames_count = max(0, end_frame - start_frame)
        frames_to_process = (selected_frames_count + frame_step - 1) // frame_step

        st.caption(
            f"📊 Analyzing **frames {start_frame} to {end_frame}** ({selected_frames_count:,} frames). "
            f"With frame step **{frame_step}**, **{frames_to_process:,} frames** will be evaluated."
        )

        st.markdown("---")

        # ----------------- Run Detection & Tracking Section -----------------
        start_button = st.button("▶ Start Unique Pothole Tracking", type="primary", use_container_width=True)

        if start_button:
            if model is None:
                st.error("Model 'best.pt' is not loaded. Cannot run inference.")
            elif frames_to_process == 0:
                st.warning("Frame range is empty. Please select a valid frame range.")
            else:
                cap = cv2.VideoCapture(active_video_path)
                cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

                output_video_path = "output_tracked_potholes.mp4"
                out_writer = None
                if save_annotated_video:
                    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                    out_fps = max(1.0, vid_info["fps"] / frame_step)
                    out_writer = cv2.VideoWriter(output_video_path, fourcc, out_fps, (vid_info["width"], vid_info["height"]))

                # UI Layout for live tracking
                prog_bar = st.progress(0, text="Initializing ByteTrack multi-object tracker...")
                
                mcol1, mcol2, mcol3, mcol4 = st.columns(4)
                stat_processed = mcol1.empty()
                stat_current_frame = mcol2.empty()
                stat_unique_potholes = mcol3.empty()
                stat_raw_count = mcol4.empty()

                video_preview_placeholder = st.empty()
                
                # Tracking state
                unique_pothole_records = {}  # {track_id: {"first_frame": ..., "first_sec": ..., "max_conf": ..., "snapshot": ...}}
                detections_timeline = []
                raw_frame_detections_count = 0
                processed_count = 0
                
                start_time = time.time()
                
                # Loop through selected frames with tracker persistence
                for current_idx in range(start_frame, end_frame, frame_step):
                    cap.set(cv2.CAP_PROP_POS_FRAMES, current_idx)
                    ret, frame = cap.read()
                    if not ret:
                        break

                    t0 = time.time()
                    
                    # RUN YOLO WITH MULTI-OBJECT TRACKING
                    results = model.track(
                        frame,
                        persist=True,
                        tracker=tracker_type,
                        conf=conf_thresh,
                        verbose=False
                    )
                    infer_time = time.time() - t0
                    
                    annotated_frame = results[0].plot()
                    boxes = results[0].boxes
                    num_detections_this_frame = len(boxes)
                    raw_frame_detections_count += num_detections_this_frame
                    timestamp_sec = round(current_idx / vid_info["fps"], 2)

                    current_active_ids = []
                    
                    # Inspect Track IDs assigned by ByteTrack / BoT-SORT
                    if boxes.id is not None:
                        track_ids = boxes.id.int().cpu().tolist()
                        confidences = boxes.conf.cpu().tolist()
                        current_active_ids = track_ids
                        
                        for tid, conf in zip(track_ids, confidences):
                            if tid not in unique_pothole_records:
                                # New unique physical pothole discovered!
                                rgb_crop = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
                                unique_pothole_records[tid] = {
                                    "track_id": tid,
                                    "first_frame": current_idx,
                                    "first_sec": timestamp_sec,
                                    "max_conf": round(float(conf), 2),
                                    "frame_hits": 1,
                                    "snapshot": rgb_crop
                                }
                            else:
                                unique_pothole_records[tid]["frame_hits"] += 1
                                if conf > unique_pothole_records[tid]["max_conf"]:
                                    unique_pothole_records[tid]["max_conf"] = round(float(conf), 2)
                                    rgb_crop = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
                                    unique_pothole_records[tid]["snapshot"] = rgb_crop

                    if num_detections_this_frame > 0:
                        detections_timeline.append({
                            "Frame": current_idx,
                            "Timestamp (s)": timestamp_sec,
                            "Active Track IDs": str(current_active_ids) if current_active_ids else "None",
                            "Potholes in Frame": num_detections_this_frame,
                            "Total Unique Potholes So Far": len(unique_pothole_records)
                        })

                    if out_writer is not None:
                        out_writer.write(annotated_frame)

                    processed_count += 1
                    
                    # Update live preview
                    rgb_preview = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
                    active_id_text = f"Track IDs: {current_active_ids}" if current_active_ids else "None"
                    video_preview_placeholder.image(
                        rgb_preview,
                        caption=f"Frame {current_idx}/{end_frame} ({timestamp_sec}s) | Active {active_id_text} | Total Unique: {len(unique_pothole_records)}",
                        use_container_width=True
                    )

                    # Update metrics & progress
                    progress_pct = int((processed_count / frames_to_process) * 100)
                    prog_bar.progress(
                        min(100, progress_pct),
                        text=f"Tracking frame {current_idx} of {end_frame} ({progress_pct}%) - Unique Potholes Found: {len(unique_pothole_records)}"
                    )

                    stat_processed.metric("Frames Analyzed", f"{processed_count} / {frames_to_process}")
                    stat_current_frame.metric("In Current Frame", f"{num_detections_this_frame}")
                    stat_unique_potholes.metric("🎯 Unique Potholes (Tracked)", f"{len(unique_pothole_records)}")
                    stat_raw_count.metric("Raw Cumulative Hits", f"{raw_frame_detections_count}",
                                          delta=f"-{raw_frame_detections_count - len(unique_pothole_records)} duplicates filtered",
                                          delta_color="normal")

                # Cleanup
                cap.release()
                if out_writer is not None:
                    out_writer.release()

                elapsed_total = round(time.time() - start_time, 1)
                prog_bar.progress(100, text=f"✅ Tracking complete in {elapsed_total}s! Identified {len(unique_pothole_records)} unique potholes.")
                st.balloons()

                # ----------------- Final Summary & Analytics -----------------
                st.markdown("---")
                st.header("📊 Unique Pothole Tracking Report")

                res1, res2, res3, res4 = st.columns(4)
                res1.metric("Analyzed Frames", f"{processed_count}")
                res2.metric("🎯 Real Unique Potholes", f"{len(unique_pothole_records)}")
                res3.metric("Raw Multi-Frame Detections", f"{raw_frame_detections_count}")
                duplicates_saved = max(0, raw_frame_detections_count - len(unique_pothole_records))
                res4.metric("Duplicates Filtered Out", f"{duplicates_saved} ({round((duplicates_saved / max(1, raw_frame_detections_count))*100, 1)}%)")

                # Download Buttons
                dcol1, dcol2 = st.columns(2)
                
                if save_annotated_video and os.path.exists(output_video_path):
                    with open(output_video_path, "rb") as vf:
                        dcol1.download_button(
                            label="⬇️ Download Annotated Video with Track IDs (.mp4)",
                            data=vf,
                            file_name="tracked_potholes.mp4",
                            mime="video/mp4",
                            use_container_width=True
                        )

                if unique_pothole_records:
                    export_rows = [
                        {
                            "Pothole ID": rec["track_id"],
                            "First Seen Frame": rec["first_frame"],
                            "First Seen Time (s)": rec["first_sec"],
                            "Highest Confidence": rec["max_conf"],
                            "Frames Tracked": rec["frame_hits"]
                        }
                        for rec in unique_pothole_records.values()
                    ]
                    df_unique = pd.DataFrame(export_rows)
                    csv_data = df_unique.to_csv(index=False).encode('utf-8')
                    dcol2.download_button(
                        label="⬇️ Download Unique Potholes CSV Catalog",
                        data=csv_data,
                        file_name="unique_potholes_catalog.csv",
                        mime="text/csv",
                        use_container_width=True
                    )

                # Snapshot Gallery of Unique Potholes
                if unique_pothole_records:
                    st.markdown("---")
                    st.subheader("📸 Unique Potholes Gallery (1 Card Per Real Pothole)")
                    st.caption("Each physical pothole is listed with its unique persistent Track ID and highest-confidence snapshot.")
                    
                    pothole_items = list(unique_pothole_records.values())
                    g_cols = st.columns(3)
                    for i, rec in enumerate(pothole_items):
                        with g_cols[i % 3]:
                            st.image(
                                rec["snapshot"],
                                caption=f"Pothole #{rec['track_id']} | First seen @ {rec['first_sec']}s (Frame {rec['first_frame']}) | Conf: {rec['max_conf']}",
                                use_container_width=True
                            )

    else:
        st.error("Could not read video metadata. Please ensure the video file is valid and readable.")

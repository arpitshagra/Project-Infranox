import os
import time
import tempfile
import cv2
import numpy as np
import pandas as pd
import streamlit as st
from ultralytics import YOLO
from tracker import RoadPotholeTracker

# Page Configuration
st.set_page_config(
    page_title="Infranox - Pothole Detection, Tracking & Road Ranking",
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
    .badge-critical {
        background-color: #EF4444;
        color: white;
        padding: 4px 10px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .badge-poor {
        background-color: #F97316;
        color: white;
        padding: 4px 10px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .badge-fair {
        background-color: #EAB308;
        color: white;
        padding: 4px 10px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .badge-good {
        background-color: #22C55E;
        color: white;
        padding: 4px 10px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)

# ----------------- Session State for Road Rankings -----------------
if "road_registry" not in st.session_state:
    st.session_state["road_registry"] = []

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


def draw_pothole_box(img, box, label, color=(0, 165, 255), thickness=2):
    """Draw stylish bounding box with label background."""
    x1, y1, x2, y2 = [int(v) for v in box]
    cv2.rectangle(img, (x1, y1), (x2, y2), color, thickness)
    
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.55
    text_thickness = 1
    (tw, th), baseline = cv2.getTextSize(label, font, font_scale, text_thickness)
    
    ty1 = max(0, y1 - th - 8)
    ty2 = y1
    cv2.rectangle(img, (x1, ty1), (x1 + tw + 6, ty2), color, -1)
    cv2.putText(img, label, (x1 + 3, ty2 - 4), font, font_scale, (255, 255, 255), text_thickness, cv2.LINE_AA)


# ----------------- Header -----------------
st.markdown('<div class="main-title">🚧 Infranox AI Pothole Detection, Tracking & Road Ranking Studio</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Tracks unique physical pothole IDs, exports structured inspection CSV records, and ranks roads by Pavement Health Score & maintenance priority.</div>', unsafe_allow_html=True)

# ----------------- Sidebar Configuration -----------------
with st.sidebar:
    st.header("⚙️ Configuration")
    
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
    st.subheader("🎯 Detection Sensitivity")
    
    conf_thresh = st.slider(
        "Confidence Threshold",
        min_value=0.05,
        max_value=0.90,
        value=0.20,
        step=0.05,
        help="Recommended: 0.20 to capture fainter & distant potholes without skipping them."
    )
    
    iou_thresh = st.slider(
        "NMS Overlap Threshold (IoU)",
        min_value=0.30,
        max_value=0.85,
        value=0.50,
        step=0.05,
        help="Prevents adjacent or clustered potholes from merging into a single box."
    )

    inference_size = st.selectbox(
        "Inference Resolution",
        options=[640, 960, 1280],
        index=0,
        help="640 is faster; 960 and 1280 improve detection of smaller distant potholes."
    )

    st.markdown("---")
    st.subheader("🚗 Tracking & Road Profiler")
    
    tracker_mode = st.selectbox(
        "Tracking Engine",
        options=[
            "Road-Aware Flow Tracker (Recommended)",
            "Pothole-Tuned ByteTrack",
            "Pothole-Tuned BoT-SORT"
        ],
        index=0,
        help="Road-Aware Flow Tracker tracks forward vehicle motion and permanently assigns unique IDs."
    )

    min_hits = st.slider(
        "Minimum Track Detections (Min Hits)",
        min_value=1,
        max_value=5,
        value=1,
        help="1 = Count every detected pothole (never drop any pothole).\n2+ = Require 2+ frames to filter single-frame flickers."
    )

    frame_step = st.slider(
        "Process Every Nth Frame (Frame Skip)",
        min_value=1,
        max_value=10,
        value=2,
        help="1 = Full fidelity.\n2 = 2x faster (recommended for dashcam video).\n5+ = Faster overview."
    )

    save_annotated_video = st.checkbox(
        "Export Annotated Video (.mp4)",
        value=True,
        help="Generates an output video with tracking ID bounding boxes drawn."
    )

# ----------------- Mode Selection -----------------
media_mode = st.radio(
    "Choose Media Input Type:",
    options=["Video Analysis & Road Ranking", "Single / Batch Image Inspection", "Road Ranking Leaderboard"],
    horizontal=True
)

# =========================================================================
# MODE 1: SINGLE / BATCH IMAGE INSPECTION
# =========================================================================
if media_mode == "Single / Batch Image Inspection":
    st.markdown("### 📸 Image Pothole Detection & Dimension Profiling")
    st.info("Upload one or more road photos to detect, locate, assign IDs, and measure every individual pothole in the frame.")
    
    uploaded_images = st.file_uploader(
        "Upload Road Image(s) (JPG, PNG, JPEG)",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True
    )
    
    if uploaded_images:
        all_image_potholes = []
        for idx, img_file in enumerate(uploaded_images):
            file_bytes = np.asarray(bytearray(img_file.read()), dtype=np.uint8)
            img = cv2.imdecode(file_bytes, 1)
            
            if img is None:
                st.error(f"Could not load image: {img_file.name}")
                continue
                
            H, W = img.shape[:2]
            
            with st.spinner(f"Analyzing {img_file.name}..."):
                results = model.predict(
                    img,
                    conf=conf_thresh,
                    iou=iou_thresh,
                    imgsz=inference_size,
                    verbose=False
                )
            
            boxes = results[0].boxes
            num_potholes = len(boxes)
            annotated_img = img.copy()
            pothole_details = []
            
            if num_potholes > 0:
                xyxy = boxes.xyxy.cpu().numpy()
                confs = boxes.conf.cpu().numpy()
                
                for p_idx, (box, conf) in enumerate(zip(xyxy, confs), start=1):
                    bw = int(box[2] - box[0])
                    bh = int(box[3] - box[1])
                    b_area = bw * bh
                    severity = RoadPotholeTracker.classify_severity(bw, bh, b_area)
                    
                    label = f"Pothole #{p_idx} [{severity}] ({conf:.2f})"
                    box_color = (0, 0, 255) if severity == "Severe" else ((0, 140, 255) if severity == "Moderate" else (0, 200, 0))
                    draw_pothole_box(annotated_img, box, label, color=box_color, thickness=3)
                    
                    crop = RoadPotholeTracker.extract_crop(img, box, margin=0.20)
                    rgb_crop = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB) if crop.size > 0 else None
                    
                    pothole_record = {
                        "Pothole ID": p_idx,
                        "Image Source": img_file.name,
                        "Confidence Score": round(float(conf), 2),
                        "Severity Level": severity,
                        "Width (px)": bw,
                        "Height (px)": bh,
                        "Estimated Area (px²)": b_area,
                        "Bounding Box": f"[{int(box[0])}, {int(box[1])}, {int(box[2])}, {int(box[3])}]",
                        "Crop": rgb_crop
                    }
                    pothole_details.append(pothole_record)
                    all_image_potholes.append(pothole_record)
            
            st.markdown(f"#### 🛣️ Results for `{img_file.name}`")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Potholes Identified", f"{num_potholes}")
            sev_count = sum(1 for p in pothole_details if p['Severity Level'] == 'Severe')
            m2.metric("Severe Potholes", f"{sev_count}")
            avg_c = round(float(np.mean([p['Confidence Score'] for p in pothole_details])), 2) if pothole_details else 0.0
            m3.metric("Avg Confidence", f"{avg_c}")
            tot_area = sum(p['Estimated Area (px²)'] for p in pothole_details)
            m4.metric("Damaged Area (px²)", f"{tot_area:,}")
            
            col_img, col_info = st.columns([2, 1])
            with col_img:
                st.image(cv2.cvtColor(annotated_img, cv2.COLOR_BGR2RGB), caption=f"{img_file.name} - {num_potholes} potholes identified", use_container_width=True)
            
            with col_info:
                if pothole_details:
                    df_img = pd.DataFrame([
                        {"ID": p["Pothole ID"], "Severity": p["Severity Level"], "Conf": p["Confidence Score"], "Dimensions": f"{p['Width (px)']}x{p['Height (px)']} px"}
                        for p in pothole_details
                    ])
                    st.dataframe(df_img, use_container_width=True, hide_index=True)
                else:
                    st.success("No potholes detected in this image.")

            if pothole_details:
                st.markdown("**Individual Pothole Inspection Gallery:**")
                g_cols = st.columns(min(4, max(1, len(pothole_details))))
                for p_i, p_data in enumerate(pothole_details):
                    with g_cols[p_i % len(g_cols)]:
                        if p_data["Crop"] is not None:
                            st.image(p_data["Crop"], caption=f"Pothole #{p_data['Pothole ID']} | {p_data['Severity Level']} | Conf: {p_data['Confidence Score']}", use_container_width=True)
            st.markdown("---")

        if all_image_potholes:
            export_df = pd.DataFrame([{k: v for k, v in p.items() if k != "Crop"} for p in all_image_potholes])
            csv_bytes = export_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "⬇️ Download All Image Pothole IDs Catalog (CSV)",
                data=csv_bytes,
                file_name="image_potholes_catalog.csv",
                mime="text/csv",
                type="primary",
                use_container_width=True
            )

# =========================================================================
# MODE 2: VIDEO ANALYSIS & ROAD RANKING
# =========================================================================
elif media_mode == "Video Analysis & Road Ranking":
    col_vmode, col_rname = st.columns([2, 1])
    with col_vmode:
        video_source_mode = st.radio(
            "Choose Video Source:",
            options=["Select Local Video from Workspace", "Upload Video File"],
            horizontal=True
        )
    with col_rname:
        custom_road_name = st.text_input("Road / Sector Name (for Ranking):", value="", placeholder="e.g. NH-44 Sector 2")

    active_video_path = None
    temp_file_path = None

    if video_source_mode == "Select Local Video from Workspace":
        candidate_dirs = [".", os.path.expanduser(r"~\Downloads")]
        workspace_videos = []
        for d in candidate_dirs:
            if os.path.exists(d):
                for f in os.listdir(d):
                    if f.lower().endswith((".mp4", ".avi", ".mov", ".mkv")) and not f.startswith("output_"):
                        full_p = os.path.abspath(os.path.join(d, f))
                        if full_p not in [v[1] for v in workspace_videos]:
                            workspace_videos.append((f"{f} ({os.path.basename(d)})", full_p))
        
        if workspace_videos:
            labels = [v[0] for v in workspace_videos]
            selected_idx = st.selectbox("Available local videos:", range(len(labels)), format_func=lambda i: labels[i])
            active_video_path = workspace_videos[selected_idx][1]
            if not custom_road_name:
                custom_road_name = os.path.splitext(os.path.basename(active_video_path))[0]
        else:
            st.warning("No video files found in workspace or Downloads. Please upload one below.")

    else:
        uploaded_file = st.file_uploader("Upload road video (MP4, AVI, MOV, MKV)", type=["mp4", "avi", "mov", "mkv"])
        if uploaded_file is not None:
            tfile = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
            tfile.write(uploaded_file.read())
            tfile.flush()
            tfile.close()
            temp_file_path = tfile.name
            active_video_path = temp_file_path
            if not custom_road_name:
                custom_road_name = os.path.splitext(uploaded_file.name)[0]

    # Video Processing Pipeline
    if active_video_path and os.path.exists(active_video_path):
        vid_info = get_video_info(active_video_path)
        
        if vid_info and vid_info["total_frames"] > 0:
            total_f = vid_info["total_frames"]
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Resolution", f"{vid_info['width']} x {vid_info['height']}")
            col2.metric("Total Video Frames", f"{total_f:,}")
            col3.metric("Video FPS", f"{vid_info['fps']}")
            col4.metric("Duration", f"{vid_info['duration_sec']}s (~{round(vid_info['duration_sec']/60, 1)}m)")

            st.markdown("---")
            st.subheader("✂️ Frame Range Adjustment (Trimming)")
            
            default_max = min(total_f, 800) if total_f > 1200 else total_f
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
            effective_duration_sec = selected_frames_count / vid_info["fps"] if vid_info["fps"] > 0 else 1.0

            st.caption(
                f"📊 Analyzing **frames {start_frame} to {end_frame}** ({selected_frames_count:,} frames, ~{round(effective_duration_sec, 1)}s). "
                f"With frame step **{frame_step}**, **{frames_to_process:,} frames** will be evaluated."
            )

            st.markdown("---")

            # Start Button
            start_button = st.button("▶ Start Unique Pothole Tracking & Road Profiling", type="primary", use_container_width=True)

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

                    prog_bar = st.progress(0, text="Initializing road tracking engine...")
                    
                    mcol1, mcol2, mcol3, mcol4 = st.columns(4)
                    stat_processed = mcol1.empty()
                    stat_current_frame = mcol2.empty()
                    stat_unique_potholes = mcol3.empty()
                    stat_raw_count = mcol4.empty()

                    video_preview_placeholder = st.empty()

                    # Initialize Tracker
                    road_tracker = None
                    tracker_yaml_path = None
                    
                    if tracker_mode == "Road-Aware Flow Tracker (Recommended)":
                        road_tracker = RoadPotholeTracker(
                            iou_thresh=iou_thresh * 0.5,
                            max_dist=140,
                            max_lost_frames=max(3, 8 // frame_step),
                            min_hits=min_hits
                        )
                    elif tracker_mode == "Pothole-Tuned ByteTrack":
                        tracker_yaml_path = os.path.abspath("trackers/pothole_bytetrack.yaml")
                        if hasattr(model, 'predictor') and model.predictor is not None:
                            model.predictor.trackers = None
                    else:
                        tracker_yaml_path = os.path.abspath("trackers/pothole_botsort.yaml")
                        if hasattr(model, 'predictor') and model.predictor is not None:
                            model.predictor.trackers = None

                    unique_pothole_records = {}
                    detections_timeline = []
                    raw_frame_detections_count = 0
                    processed_count = 0
                    start_time = time.time()

                    color_palette = [
                        (0, 165, 255), (0, 255, 0), (255, 105, 180),
                        (255, 215, 0), (0, 220, 255), (147, 112, 219),
                        (50, 205, 50), (255, 69, 0), (70, 130, 180)
                    ]

                    # Video Loop
                    for current_idx in range(start_frame, end_frame, frame_step):
                        cap.set(cv2.CAP_PROP_POS_FRAMES, current_idx)
                        ret, frame = cap.read()
                        if not ret:
                            break

                        timestamp_sec = round(current_idx / vid_info["fps"], 2)
                        annotated_frame = frame.copy()
                        current_active_ids = []

                        # OPTION A: ROAD-AWARE FLOW TRACKER
                        if road_tracker is not None:
                            results = model.predict(
                                frame,
                                conf=conf_thresh,
                                iou=iou_thresh,
                                imgsz=inference_size,
                                verbose=False
                            )
                            boxes = results[0].boxes
                            num_dets = len(boxes)
                            raw_frame_detections_count += num_dets

                            if num_dets > 0:
                                xyxy = boxes.xyxy.cpu().numpy().tolist()
                                confs = [round(float(c), 2) for c in boxes.conf.cpu().tolist()]
                                
                                assigned_ids = road_tracker.update(
                                    xyxy, confs, frame, annotated_frame, current_idx, timestamp_sec
                                )
                                current_active_ids = assigned_ids

                                for box, tid, conf in zip(xyxy, assigned_ids, confs):
                                    color = color_palette[tid % len(color_palette)]
                                    label = f"Pothole #{tid} ({conf:.2f})"
                                    draw_pothole_box(annotated_frame, box, label, color=color, thickness=2)

                            unique_pothole_records = road_tracker.get_confirmed_records()

                        # OPTION B: TUNED BYTETRACK / BOTSORT
                        else:
                            results = model.track(
                                frame,
                                persist=True,
                                tracker=tracker_yaml_path,
                                conf=conf_thresh,
                                iou=iou_thresh,
                                imgsz=inference_size,
                                verbose=False
                            )
                            boxes = results[0].boxes
                            num_dets = len(boxes)
                            raw_frame_detections_count += num_dets

                            annotated_frame = results[0].plot()

                            if boxes.id is not None:
                                track_ids = boxes.id.int().cpu().tolist()
                                confidences = boxes.conf.cpu().tolist()
                                xyxy_boxes = boxes.xyxy.cpu().numpy().tolist()
                                current_active_ids = track_ids

                                for tid, conf, b_box in zip(track_ids, confidences, xyxy_boxes):
                                    crop = RoadPotholeTracker.extract_crop(frame, b_box, margin=0.20)
                                    rgb_crop = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB) if crop.size > 0 else None
                                    
                                    bw = int(b_box[2] - b_box[0])
                                    bh = int(b_box[3] - b_box[1])
                                    b_area = bw * bh
                                    severity = RoadPotholeTracker.classify_severity(bw, bh, b_area)
                                    
                                    if tid not in unique_pothole_records:
                                        unique_pothole_records[tid] = {
                                            "track_id": tid,
                                            "first_frame": current_idx,
                                            "first_sec": timestamp_sec,
                                            "last_frame": current_idx,
                                            "last_sec": timestamp_sec,
                                            "width": bw,
                                            "height": bh,
                                            "max_area": b_area,
                                            "severity": severity,
                                            "max_conf": round(float(conf), 2),
                                            "hits": 1,
                                            "crop": rgb_crop,
                                            "annotated_snapshot": cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
                                        }
                                    else:
                                        rec = unique_pothole_records[tid]
                                        rec["hits"] += 1
                                        rec["last_frame"] = current_idx
                                        rec["last_sec"] = timestamp_sec
                                        if b_area > rec["max_area"]:
                                            rec["max_area"] = b_area
                                            rec["width"] = bw
                                            rec["height"] = bh
                                            rec["severity"] = severity
                                        if conf > rec["max_conf"]:
                                            rec["max_conf"] = round(float(conf), 2)
                                            if rgb_crop is not None:
                                                rec["crop"] = rgb_crop
                                            rec["annotated_snapshot"] = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)

                        if num_dets > 0:
                            detections_timeline.append({
                                "Frame": current_idx,
                                "Timestamp (s)": timestamp_sec,
                                "Active Track IDs": str(current_active_ids) if current_active_ids else "None",
                                "Potholes in Frame": num_dets,
                                "Total Unique Potholes So Far": len(unique_pothole_records)
                            })

                        if out_writer is not None:
                            out_writer.write(annotated_frame)

                        processed_count += 1

                        rgb_preview = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
                        active_id_text = f"Active IDs: {current_active_ids}" if current_active_ids else "None"
                        video_preview_placeholder.image(
                            rgb_preview,
                            caption=f"Frame {current_idx}/{end_frame} ({timestamp_sec}s) | {active_id_text} | Total Unique: {len(unique_pothole_records)}",
                            use_container_width=True
                        )

                        progress_pct = int((processed_count / frames_to_process) * 100)
                        prog_bar.progress(
                            min(100, progress_pct),
                            text=f"Tracking frame {current_idx} of {end_frame} ({progress_pct}%) - Unique Potholes Found: {len(unique_pothole_records)}"
                        )

                        stat_processed.metric("Frames Analyzed", f"{processed_count} / {frames_to_process}")
                        stat_current_frame.metric("In Current Frame", f"{num_dets}")
                        stat_unique_potholes.metric("🎯 Real Unique Potholes", f"{len(unique_pothole_records)}")
                        stat_raw_count.metric("Raw Cumulative Hits", f"{raw_frame_detections_count}",
                                              delta=f"-{max(0, raw_frame_detections_count - len(unique_pothole_records))} duplicates filtered",
                                              delta_color="normal")

                    cap.release()
                    if out_writer is not None:
                        out_writer.release()

                    if road_tracker is not None:
                        unique_pothole_records = road_tracker.get_confirmed_records()

                    elapsed_total = round(time.time() - start_time, 1)
                    prog_bar.progress(100, text=f"✅ Tracking complete in {elapsed_total}s! Identified {len(unique_pothole_records)} distinct physical potholes.")
                    st.balloons()

                    # =========================================================
                    # ROAD RANKING & CIVIL HEALTH PROFILE CALCULATION
                    # =========================================================
                    road_profile = RoadPotholeTracker.compute_road_ranking_profile(
                        road_name=custom_road_name,
                        records=unique_pothole_records,
                        duration_sec=effective_duration_sec,
                        frames_analyzed=processed_count
                    )

                    # Update session state registry for leaderboard
                    existing_idx = next((i for i, r in enumerate(st.session_state["road_registry"]) if r["Road Name"] == custom_road_name), None)
                    if existing_idx is not None:
                        st.session_state["road_registry"][existing_idx] = road_profile
                    else:
                        st.session_state["road_registry"].append(road_profile)

                    # ----------------- Road Health Profile Display -----------------
                    st.markdown("---")
                    st.header(f"🛣️ Road Quality Assessment: `{custom_road_name}`")
                    
                    rcol1, rcol2, rcol3, rcol4 = st.columns(4)
                    rcol1.metric("Pavement Health Score", f"{road_profile['Health Score (0-100)']}/100")
                    rcol2.metric("Condition Rating", f"{road_profile['Condition Rating']}")
                    rcol3.metric("Maintenance Urgency", f"{road_profile['Maintenance Urgency']}")
                    rcol4.metric("Pothole Density", f"{road_profile['Pothole Density (/min)']} /min")

                    st.markdown("**Road Condition Gauge:**")
                    score_val = road_profile['Health Score (0-100)']
                    st.progress(score_val / 100.0, text=f"Health Score: {score_val}% ({road_profile['Condition Rating']})")

                    st.markdown("---")
                    st.subheader("📊 Pothole Severity & Defect Breakdown")
                    b1, b2, b3, b4 = st.columns(4)
                    b1.metric("🔴 Severe Potholes", f"{road_profile['Severe Potholes']}")
                    b2.metric("🟡 Moderate Potholes", f"{road_profile['Moderate Potholes']}")
                    b3.metric("🟢 Minor Potholes", f"{road_profile['Minor Potholes']}")
                    b4.metric("Total Surface Damage Area", f"{road_profile['Total Damaged Area (px²)']:,} px²")

                    # ----------------- CSV EXPORTS -----------------
                    st.markdown("---")
                    st.subheader("📥 Export Inspection Catalogs & Reports")
                    
                    # Prepare Pothole CSV
                    export_potholes = []
                    for rec in sorted(unique_pothole_records.values(), key=lambda x: x["track_id"]):
                        export_potholes.append({
                            "Pothole ID": rec["track_id"],
                            "Road Name": custom_road_name,
                            "Severity": rec.get("severity", "Moderate"),
                            "First Seen Timestamp (s)": rec["first_sec"],
                            "First Seen Frame": rec["first_frame"],
                            "Last Seen Timestamp (s)": rec.get("last_sec", rec["first_sec"]),
                            "Duration Visible (s)": round(rec.get("last_sec", rec["first_sec"]) - rec["first_sec"], 2),
                            "Width (px)": rec.get("width", 0),
                            "Height (px)": rec.get("height", 0),
                            "Estimated Area (px²)": rec.get("max_area", 0),
                            "Highest Confidence Score": rec["max_conf"],
                            "Frames Tracked (Hits)": rec["hits"]
                        })
                    
                    df_potholes = pd.DataFrame(export_potholes)
                    csv_potholes_data = df_potholes.to_csv(index=False).encode('utf-8')
                    
                    # Automatically save to workspace disk
                    csv_save_path = "potholes_catalog.csv"
                    df_potholes.to_csv(csv_save_path, index=False)

                    # Prepare Road Ranking CSV
                    df_rank = pd.DataFrame(st.session_state["road_registry"]).sort_values(by="Health Score (0-100)", ascending=True)
                    df_rank["Rank (Worst to Best)"] = range(1, len(df_rank) + 1)
                    csv_rank_data = df_rank.to_csv(index=False).encode('utf-8')

                    dcol1, dcol2, dcol3 = st.columns(3)
                    dcol1.download_button(
                        label="⬇️ Download Pothole IDs CSV Catalog",
                        data=csv_potholes_data,
                        file_name=f"{custom_road_name}_potholes_catalog.csv",
                        mime="text/csv",
                        type="primary",
                        use_container_width=True
                    )

                    dcol2.download_button(
                        label="⬇️ Download Road Rankings Leaderboard (CSV)",
                        data=csv_rank_data,
                        file_name="road_rankings_leaderboard.csv",
                        mime="text/csv",
                        use_container_width=True
                    )

                    if save_annotated_video and os.path.exists(output_video_path):
                        with open(output_video_path, "rb") as vf:
                            dcol3.download_button(
                                label="⬇️ Download Annotated Video with Track IDs (.mp4)",
                                data=vf,
                                file_name=f"{custom_road_name}_tracked_potholes.mp4",
                                mime="video/mp4",
                                use_container_width=True
                            )

                    # ----------------- Unique Potholes Gallery -----------------
                    if unique_pothole_records:
                        st.markdown("---")
                        st.subheader(f"📸 Unique Potholes Gallery ({len(unique_pothole_records)} Distinct Potholes Identified)")
                        st.caption("Each physical pothole is displayed with its persistent Track ID, highest detection confidence, dimensions, and close-up crop.")
                        
                        view_mode = st.radio("Gallery View Mode:", ["Close-up Pothole Crops", "Full Frame Context"], horizontal=True)

                        pothole_items = sorted(unique_pothole_records.values(), key=lambda x: x["track_id"])
                        g_cols = st.columns(3)
                        for i, rec in enumerate(pothole_items):
                            with g_cols[i % 3]:
                                img_to_show = rec["crop"] if (view_mode == "Close-up Pothole Crops" and rec.get("crop") is not None) else rec.get("annotated_snapshot")
                                if img_to_show is not None:
                                    st.image(
                                        img_to_show,
                                        caption=f"Pothole #{rec['track_id']} | Severity: {rec.get('severity', 'N/A')} | Seen @ {rec['first_sec']}s | Conf: {rec['max_conf']} | Area: {rec.get('max_area', 0)} px²",
                                        use_container_width=True
                                    )

        else:
            st.error("Could not read video metadata. Please ensure the video file is valid and readable.")

# =========================================================================
# MODE 3: ROAD RANKING LEADERBOARD
# =========================================================================
else:
    st.markdown("### 🏆 Comprehensive Road Quality Ranking Leaderboard")
    st.info("Ranks all analyzed road segments based on Pavement Health Score, Pothole Density, Severity Distribution, and Repair Urgency.")

    if st.session_state["road_registry"]:
        df_registry = pd.DataFrame(st.session_state["road_registry"])
        
        sort_by = st.selectbox(
            "Rank Roads By:",
            options=[
                "Most Urgent Maintenance (Lowest Health Score First)",
                "Best Condition (Highest Health Score First)",
                "Highest Pothole Density",
                "Most Severe Potholes"
            ]
        )

        if sort_by == "Most Urgent Maintenance (Lowest Health Score First)":
            df_sorted = df_registry.sort_values(by="Health Score (0-100)", ascending=True).reset_index(drop=True)
        elif sort_by == "Best Condition (Highest Health Score First)":
            df_sorted = df_registry.sort_values(by="Health Score (0-100)", ascending=False).reset_index(drop=True)
        elif sort_by == "Highest Pothole Density":
            df_sorted = df_registry.sort_values(by="Pothole Density (/min)", ascending=False).reset_index(drop=True)
        else:
            df_sorted = df_registry.sort_values(by="Severe Potholes", ascending=False).reset_index(drop=True)

        df_sorted.insert(0, "Rank #", range(1, len(df_sorted) + 1))
        
        display_cols = [
            "Rank #", "Road Name", "Health Score (0-100)", "Condition Rating",
            "Maintenance Urgency", "Total Potholes", "Severe Potholes", "Moderate Potholes",
            "Minor Potholes", "Pothole Density (/min)", "Total Damaged Area (px²)", "Duration (s)"
        ]
        
        st.dataframe(df_sorted[display_cols], use_container_width=True, hide_index=True)

        # Summary Bar Chart
        st.markdown("#### 📊 Comparative Health Scores")
        chart_data = df_sorted.set_index("Road Name")["Health Score (0-100)"]
        st.bar_chart(chart_data)

        # Export Button
        csv_board = df_sorted.to_csv(index=False).encode('utf-8')
        dcol1, dcol2 = st.columns([1, 1])
        dcol1.download_button(
            "⬇️ Download Road Rankings Leaderboard CSV",
            data=csv_board,
            file_name="road_rankings_leaderboard.csv",
            mime="text/csv",
            type="primary",
            use_container_width=True
        )
        if dcol2.button("🗑️ Clear Road Rankings Registry"):
            st.session_state["road_registry"] = []
            st.rerun()

    else:
        st.warning("No roads evaluated yet in this session. Analyze road videos or photos to automatically populate this leaderboard!")
        st.markdown("""
        **Parameters Used for Road Ranking:**
        - **Pothole Density:** Frequency of potholes per minute of road footage.
        - **Severity Weighting:** Disproportionately penalizes deep/large craters vs superficial surface chips.
        - **Pavement Health Score (0–100):** Comprehensive civil engineering condition index.
        - **Repair Urgency:** Actionable schedule recommendations (Emergency Intervention, Priority Repair, Routine Monitoring).
        """)

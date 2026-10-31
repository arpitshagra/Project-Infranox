import os
import time
import tempfile
import cv2
import numpy as np
import pandas as pd
import streamlit as st
from ultralytics import YOLO
from tracker import RoadPotholeTracker
from streamlit_folium import st_folium
import map_service

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

# ----------------- Session State for Road Rankings & Interactive Map -----------------
if "road_registry" not in st.session_state:
    st.session_state["road_registry"] = []

if "map_roads" not in st.session_state:
    st.session_state["map_roads"] = map_service.load_community_roads()

if "active_route" not in st.session_state:
    st.session_state["active_route"] = None

if "origin_info" not in st.session_state:
    st.session_state["origin_info"] = None

if "dest_info" not in st.session_state:
    st.session_state["dest_info"] = None

# Click-to-pin state for Route Planner (Mode 4)
if "map_click_state" not in st.session_state:
    st.session_state["map_click_state"] = "waiting_origin"  # "waiting_origin" | "waiting_dest" | "both_set"
if "click_origin" not in st.session_state:
    st.session_state["click_origin"] = None   # {"lat":..., "lon":..., "address":...}
if "click_dest" not in st.session_state:
    st.session_state["click_dest"] = None

# Click-to-pin state for Video Survey mode (Mode 1)
if "survey_click_state" not in st.session_state:
    st.session_state["survey_click_state"] = "waiting_origin"
if "survey_click_origin" not in st.session_state:
    st.session_state["survey_click_origin"] = None
if "survey_click_dest" not in st.session_state:
    st.session_state["survey_click_dest"] = None

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
        max_value=6,
        value=3,
        help="3+ (Recommended) = Ensures only genuine potholes tracked across multiple frames are counted, eliminating flickers and duplicates.\n1 = Unfiltered (counts single-frame detections)."
    )

    frame_step = st.slider(
        "Process Every Nth Frame (Frame Skip)",
        min_value=1,
        max_value=10,
        value=1,
        help="1 = Full frame fidelity (Recommended for highest tracking accuracy without losing pothole continuity).\n2 = 2x faster.\n5+ = Fast rough overview."
    )

    save_annotated_video = st.checkbox(
        "Export Annotated Video (.mp4)",
        value=True,
        help="Generates an output video with tracking ID bounding boxes drawn."
    )

# ----------------- Mode Selection -----------------
media_mode = st.radio(
    "Choose Studio Mode:",
    options=[
        "Video Analysis & Road Ranking",
        "Single / Batch Image Inspection",
        "Road Ranking Leaderboard",
        "🗺️ Live Road Map & Route Planner"
    ],
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
    st.markdown("### 🎥 Road Video Survey & Automated Surface Profiling")
    st.info("Upload road dashcam video, specify the Start (Origin) and End (Destination) points. Infranox will automatically track all unique potholes, compute the road's Pavement Health Score, and plot it on the community map for future travelers!")

    col_vmode, col_rname = st.columns([1, 1])
    with col_vmode:
        video_source_mode = st.radio(
            "Choose Video Source:",
            options=["Select Local Video from Workspace", "Upload Video File"],
            horizontal=True
        )
    with col_rname:
        custom_road_name = st.text_input("Road / Route Name:", value="", placeholder="e.g. NH-44 Expressway Sector 1")

    # ── Survey start/end — Click-to-Pin on map ────────────────────────────
    st.markdown("#### 📍 Set Survey Start & End Points on Map")

    s_state = st.session_state["survey_click_state"]
    s_co    = st.session_state["survey_click_origin"]
    s_cd    = st.session_state["survey_click_dest"]

    # Status banner
    if s_state == "waiting_origin":
        st.info("🟢 **Step 1:** Click the map below to pin your **Survey Start Point (Origin)**.")
    elif s_state == "waiting_dest":
        st.info(f"🏁 **Step 2:** Click the map to pin your **Survey End Point (Destination)**.\n\n"
                f"🟢 **Start set:** {s_co['address'] if s_co else ''}")
    else:
        st.success(
            f"✅ **Survey route pinned!**  \n"
            f"🟢 **Start:** {s_co['address'] if s_co else ''}  \n"
            f"🏁 **End:** {s_cd['address'] if s_cd else ''}"
        )

    s_reset_col, s_fallback_col = st.columns([1, 3])
    with s_reset_col:
        if st.button("🔄 Reset Survey Pins", key="reset_survey_pins", use_container_width=True):
            st.session_state["survey_click_state"]  = "waiting_origin"
            st.session_state["survey_click_origin"] = None
            st.session_state["survey_click_dest"]   = None
            st.rerun()

    with s_fallback_col:
        with st.expander("⌨️ Or type addresses manually"):
            sf1, sf2 = st.columns(2)
            sft_start = sf1.text_input("Start Point:", placeholder="e.g. Connaught Place, New Delhi", key="sft_start_txt")
            sft_end   = sf2.text_input("End Point:",   placeholder="e.g. India Gate, New Delhi",      key="sft_end_txt")
            if st.button("✅ Set Typed Points", key="sft_set_btn"):
                with st.spinner("Geocoding..."):
                    r1 = map_service.geocode_location(sft_start)
                    r2 = map_service.geocode_location(sft_end)
                if r1 and r2:
                    st.session_state["survey_click_origin"] = {"lat": r1[0], "lon": r1[1], "address": r1[2]}
                    st.session_state["survey_click_dest"]   = {"lat": r2[0], "lon": r2[1], "address": r2[2]}
                    st.session_state["survey_click_state"]  = "both_set"
                    st.rerun()
                else:
                    st.error("Could not geocode one or both addresses.")

    # Build survey pin-picker mini-map
    survey_pin_map = map_service.build_road_quality_map(
        road_segments=[],
        click_origin=s_co,
        click_dest=s_cd,
        zoom=11
    )
    survey_map_data = st_folium(survey_pin_map, width="100%", height=380,
                                returned_objects=["last_clicked"], key="survey_pin_map")

    if survey_map_data and survey_map_data.get("last_clicked"):
        s_lat = survey_map_data["last_clicked"]["lat"]
        s_lon = survey_map_data["last_clicked"]["lng"]
        cur_s = st.session_state["survey_click_state"]
        if cur_s == "waiting_origin":
            with st.spinner("Reverse geocoding..."):
                addr = map_service.reverse_geocode(s_lat, s_lon)
            st.session_state["survey_click_origin"] = {"lat": s_lat, "lon": s_lon, "address": addr}
            st.session_state["survey_click_state"]  = "waiting_dest"
            st.rerun()
        elif cur_s == "waiting_dest":
            with st.spinner("Reverse geocoding..."):
                addr = map_service.reverse_geocode(s_lat, s_lon)
            st.session_state["survey_click_dest"]  = {"lat": s_lat, "lon": s_lon, "address": addr}
            st.session_state["survey_click_state"] = "both_set"
            st.rerun()
        elif cur_s == "both_set":
            # Third click resets origin
            with st.spinner("Reverse geocoding new start..."):
                addr = map_service.reverse_geocode(s_lat, s_lon)
            st.session_state["survey_click_origin"] = {"lat": s_lat, "lon": s_lon, "address": addr}
            st.session_state["survey_click_dest"]   = None
            st.session_state["survey_click_state"]  = "waiting_dest"
            st.rerun()

    # Derive survey_start_point / survey_end_point for downstream pipeline
    survey_start_point = s_co["address"] if s_co else "Connaught Place, New Delhi"
    survey_end_point   = s_cd["address"] if s_cd else "India Gate, New Delhi"
    st.caption("ℹ️ Click on the map above to set the road corridor. The Start & End points automatically plot this road on the live community map for future travelers.")

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
                            iou_thresh=0.15,
                            max_dist=180,
                            max_lost_frames=max(8, 16 // frame_step),
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

                            if num_dets > 0:
                                xyxy = boxes.xyxy.cpu().numpy().tolist()
                                confs = [round(float(c), 2) for c in boxes.conf.cpu().tolist()]
                                
                                clean_dets, clean_confs, assigned_ids = road_tracker.update(
                                    xyxy, confs, frame, annotated_frame, current_idx, timestamp_sec
                                )
                                current_active_ids = assigned_ids
                                raw_frame_detections_count += len(clean_dets)

                                for box, tid, conf in zip(clean_dets, assigned_ids, clean_confs):
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

                    # Automatically register road survey to OpenStreetMap community database
                    survey_entry = None
                    if survey_start_point.strip() and survey_end_point.strip():
                        with st.spinner("🗺️ Geocoding and plotting surveyed road onto live OpenStreetMap network..."):
                            survey_entry, updated_roads = map_service.register_video_survey_road(
                                road_name=custom_road_name,
                                start_query=survey_start_point,
                                end_query=survey_end_point,
                                health_score=road_profile['Health Score (0-100)'],
                                condition_rating=road_profile['Condition Rating'],
                                urgency=road_profile['Maintenance Urgency'],
                                unique_pothole_records=unique_pothole_records,
                                video_duration_sec=effective_duration_sec
                            )
                            st.session_state["map_roads"] = updated_roads

                    # ----------------- Road Health Profile Display -----------------
                    st.markdown("---")
                    st.header(f"🛣️ Road Quality Assessment: `{custom_road_name}`")
                    
                    if survey_entry:
                        st.success(
                            f"🗺️ **Road Automatically Mapped on OpenStreetMap!** `{custom_road_name}` "
                            f"(Health Score: **{road_profile['Health Score (0-100)']}/100**, {road_profile['Condition Rating']}) "
                            f"is now plotted on the live network with {len(survey_entry['potholes'])} pothole pins. "
                            f"Future travelers selecting routes along this corridor will be notified of this road's score!"
                        )

                    rcol1, rcol2, rcol3, rcol4 = st.columns(4)
                    rcol1.metric("Pavement Health Score", f"{road_profile['Health Score (0-100)']}/100")
                    rcol2.metric("Condition Rating", f"{road_profile['Condition Rating']}")
                    rcol3.metric("Maintenance Urgency", f"{road_profile['Maintenance Urgency']}")
                    rcol4.metric("Pothole Density", f"{road_profile['Pothole Density (/min)']} /min")

                    st.markdown("**Road Condition Gauge:**")
                    score_val = road_profile['Health Score (0-100)']
                    st.progress(score_val / 100.0, text=f"Health Score: {score_val}% ({road_profile['Condition Rating']})")

                    # Live Mini-Map Preview of the surveyed road
                    if survey_entry:
                        st.markdown("**🗺️ Surveyed Road Map Preview:**")
                        mini_map = map_service.build_road_quality_map([survey_entry], zoom=14)
                        st_folium(mini_map, width="100%", height=340, returned_objects=[])

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

                    # Option to pin evaluated road to the interactive map
                    with st.expander("📍 Pin this Evaluated Road to the Live Interactive Map"):
                        st.caption(f"Plot **{custom_road_name}** (Score: {road_profile['Health Score (0-100)']}/100) onto the OpenStreetMap network:")
                        m_col1, m_col2 = st.columns(2)
                        with m_col1:
                            v_start = st.text_input("Segment Start Point (Address or Lat, Lon):", value="", key="vid_start_map", placeholder="e.g. Connaught Place or 28.6328, 77.2197")
                        with m_col2:
                            v_end = st.text_input("Segment End Point (Address or Lat, Lon):", value="", key="vid_end_map", placeholder="e.g. India Gate or 28.6129, 77.2295")

                        if st.button("📍 Add to Live Map Network", key="btn_add_vid_map"):
                            if not v_start.strip() or not v_end.strip():
                                st.warning("Please provide both Start and End locations.")
                            else:
                                def parse_loc(txt):
                                    if "," in txt and all(part.strip().replace(".", "").replace("-", "").isdigit() for part in txt.split(",")):
                                        p = txt.split(",")
                                        return float(p[0]), float(p[1])
                                    loc = map_service.geocode_location(txt)
                                    return (loc[0], loc[1]) if loc else None

                                p1 = parse_loc(v_start)
                                p2 = parse_loc(v_end)
                                if p1 and p2:
                                    r_color = "#22C55E" if road_profile['Health Score (0-100)'] >= 70 else ("#EAB308" if road_profile['Health Score (0-100)'] >= 50 else "#EF4444")
                                    poly = map_service.get_osrm_route(p1[0], p1[1], p2[0], p2[1])
                                    coords = poly["coordinates"] if (poly and poly.get("coordinates")) else [[p1[0], p1[1]], [p2[0], p2[1]]]
                                    
                                    # Create sample pothole geo-markers along the road segment for each detected pothole
                                    pothole_pins = []
                                    num_p = len(unique_pothole_records)
                                    if coords and num_p > 0:
                                        step_idx = max(1, len(coords) // (num_p + 1))
                                        for p_i, p_rec in enumerate(sorted(unique_pothole_records.values(), key=lambda x: x["track_id"])):
                                            c_idx = min(len(coords) - 1, (p_i + 1) * step_idx)
                                            pothole_pins.append({
                                                "id": p_rec["track_id"],
                                                "lat": coords[c_idx][0],
                                                "lon": coords[c_idx][1],
                                                "severity": p_rec.get("severity", "Moderate"),
                                                "conf": p_rec["max_conf"],
                                                "area": p_rec.get("max_area", 2000)
                                            })

                                    st.session_state["map_roads"].append({
                                        "road_name": custom_road_name,
                                        "rating": road_profile["Condition Rating"],
                                        "health_score": road_profile["Health Score (0-100)"],
                                        "color": r_color,
                                        "urgency": road_profile["Maintenance Urgency"],
                                        "potholes_count": len(unique_pothole_records),
                                        "coordinates": coords,
                                        "potholes": pothole_pins
                                    })
                                    st.success(f"✅ Plotted '{custom_road_name}' with {len(pothole_pins)} pothole markers on the map! Switch to '🗺️ Live Road Map & Route Planner' to view.")
                                else:
                                    st.error("Could not geocode locations. Please verify addresses or enter latitude, longitude.")

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
elif media_mode == "Road Ranking Leaderboard":
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

# =========================================================================
# MODE 4: LIVE ROAD MAP & ROUTE PLANNER (Click-to-Pin)
# =========================================================================
else:
    st.markdown("### 🗺️ Live Road Quality Map & Safe Route Planner")
    st.markdown("Visualize surveyed roads with color-coded pavement ratings, inspect pothole hazard pins, and plan routes by **clicking directly on the map**.")

    # ── Click-to-pin status banner ──────────────────────────────────────
    click_state = st.session_state["map_click_state"]
    co = st.session_state["click_origin"]
    cd = st.session_state["click_dest"]

    if click_state == "waiting_origin":
        st.info("🟢 **Step 1:** Click anywhere on the map below to set your **Boarding Point (Origin)**.")
    elif click_state == "waiting_dest":
        st.info(f"🏁 **Step 2:** Click on the map to set your **Destination**.\n\n"
                f"🟢 **Boarding set:** {co['address'] if co else ''}")
    else:
        st.success(
            f"✅ **Route set!**  \n"
            f"🟢 **From:** {co['address'] if co else ''}  \n"
            f"🏁 **To:** {cd['address'] if cd else ''}"
        )

    # ── Reset button ─────────────────────────────────────────────────────
    reset_col, fallback_col = st.columns([1, 3])
    with reset_col:
        if st.button("🔄 Reset & Choose New Route", use_container_width=True):
            st.session_state["map_click_state"] = "waiting_origin"
            st.session_state["click_origin"] = None
            st.session_state["click_dest"] = None
            st.session_state["active_route"] = None
            st.session_state["origin_info"] = None
            st.session_state["dest_info"] = None
            st.rerun()

    # ── Text-input fallback ──────────────────────────────────────────────
    with fallback_col:
        with st.expander("⌨️ Or type addresses instead (fallback)"):
            fc1, fc2, fc3 = st.columns([2, 2, 1])
            fallback_origin = fc1.text_input("Boarding Point:", placeholder="e.g. Connaught Place, Delhi", label_visibility="collapsed")
            fallback_dest   = fc2.text_input("Destination:", placeholder="e.g. India Gate, Delhi", label_visibility="collapsed")
            if fc3.button("🚀 Go", use_container_width=True):
                with st.spinner("Geocoding..."):
                    orig_res = map_service.geocode_location(fallback_origin)
                    dest_res = map_service.geocode_location(fallback_dest)
                if orig_res and dest_res:
                    st.session_state["click_origin"] = {"lat": orig_res[0], "lon": orig_res[1], "address": orig_res[2]}
                    st.session_state["click_dest"]   = {"lat": dest_res[0], "lon": dest_res[1], "address": dest_res[2]}
                    st.session_state["origin_info"]  = st.session_state["click_origin"]
                    st.session_state["dest_info"]    = st.session_state["click_dest"]
                    route = map_service.get_osrm_route(orig_res[0], orig_res[1], dest_res[0], dest_res[1])
                    st.session_state["active_route"] = route
                    st.session_state["map_click_state"] = "both_set"
                    st.rerun()
                else:
                    st.error("Could not geocode one or both addresses.")

    # ── Route metrics strip (shown once route is ready) ──────────────────
    if st.session_state["active_route"] and st.session_state["origin_info"] and st.session_state["dest_info"]:
        route = st.session_state["active_route"]
        advisory = map_service.compute_route_road_health(route["coordinates"], st.session_state["map_roads"])

        st.markdown("---")
        mcol1, mcol2, mcol3, mcol4 = st.columns(4)
        mcol1.metric("Driving Distance", f"{route['distance_km']} km")
        mcol2.metric("Estimated Travel Time", f"{route['duration_min']} mins")
        mcol3.metric("Route Pavement Health", f"{advisory['route_pci']}/100")
        mcol4.metric("Safety Assessment", advisory["safety_status"])

        if "High Hazard" in advisory["safety_status"]:
            st.error(f"⚠️ **Road Safety Warning:** {advisory['advice']}")
        elif "Moderate" in advisory["safety_status"]:
            st.warning(f"🔔 **Road Condition Notice:** {advisory['advice']}")
        else:
            st.success(f"✅ **Route Pavement Clear:** {advisory['advice']}")

        if advisory.get("surveyed_segments_hit"):
            st.markdown("##### 📋 Previously Surveyed Road Corridors along this Route:")
            survey_cols = st.columns(min(3, len(advisory["surveyed_segments_hit"])))
            for s_i, seg in enumerate(advisory["surveyed_segments_hit"]):
                with survey_cols[s_i % len(survey_cols)]:
                    score_col = "#22C55E" if seg["health_score"] >= 70 else ("#EAB308" if seg["health_score"] >= 50 else "#EF4444")
                    st.markdown(f"""
                    <div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 10px; margin-bottom: 8px;">
                        <b style="color: #0F172A;">{seg['road_name']}</b><br>
                        Pavement Health: <span style="font-weight: bold; color: {score_col};">{seg['health_score']}/100 ({seg['rating']})</span><br>
                        <span style="font-size: 0.82rem; color: #64748B;">Potholes Reported: {seg['potholes_count']} | Survey Date: {seg['survey_date']}</span>
                    </div>
                    """, unsafe_allow_html=True)

    # ── Map Legend ────────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("🗺️ Interactive Road Surface Quality Map")
    st.markdown("""
    <div style="display: flex; flex-wrap: wrap; gap: 20px; align-items: center; margin-bottom: 12px; font-size: 0.9rem;">
        <div><b>Road Ratings:</b></div>
        <div><span style="color: #22C55E; font-size: 1.2rem;">■</span> Excellent / Good (PCI ≥ 70)</div>
        <div><span style="color: #EAB308; font-size: 1.2rem;">■</span> Fair (PCI 50–69)</div>
        <div><span style="color: #EF4444; font-size: 1.2rem;">■</span> Critical / Severe (PCI &lt; 50)</div>
        <div><span style="color: #2563EB; font-size: 1.2rem;">━ ━</span> Planned Route</div>
        <div><span style="color: red;">⚠️</span> Pothole Hazard Pin</div>
    </div>
    <div style="background:#EFF6FF; border:1px solid #BFDBFE; border-radius:6px; padding:8px 14px; font-size:0.9rem; margin-bottom:10px;">
        💡 <b>Click on the map</b> to drop pins — 1st click = 🟢 Origin, 2nd click = 🏁 Destination. Route auto-calculates!
    </div>
    """, unsafe_allow_html=True)

    # ── Build and render interactive Folium map ───────────────────────────
    map_obj = map_service.build_road_quality_map(
        road_segments=st.session_state["map_roads"],
        route_data=st.session_state["active_route"],
        origin_info=st.session_state["origin_info"],
        dest_info=st.session_state["dest_info"],
        click_origin=st.session_state["click_origin"] if click_state in ("waiting_dest",) else None,
        click_dest=st.session_state["click_dest"] if click_state == "waiting_dest" else None,
    )

    map_data = st_folium(map_obj, width="100%", height=580, returned_objects=["last_clicked"])

    # ── Handle map click events ───────────────────────────────────────────
    if map_data and map_data.get("last_clicked"):
        clicked_lat = map_data["last_clicked"]["lat"]
        clicked_lon = map_data["last_clicked"]["lng"]

        current_state = st.session_state["map_click_state"]

        if current_state == "waiting_origin":
            with st.spinner("Reverse geocoding clicked location..."):
                addr = map_service.reverse_geocode(clicked_lat, clicked_lon)
            st.session_state["click_origin"] = {"lat": clicked_lat, "lon": clicked_lon, "address": addr}
            st.session_state["map_click_state"] = "waiting_dest"
            st.rerun()

        elif current_state == "waiting_dest":
            with st.spinner("Reverse geocoding & calculating route..."):
                addr = map_service.reverse_geocode(clicked_lat, clicked_lon)
                route = map_service.get_osrm_route(
                    st.session_state["click_origin"]["lat"],
                    st.session_state["click_origin"]["lon"],
                    clicked_lat, clicked_lon
                )
            st.session_state["click_dest"]   = {"lat": clicked_lat, "lon": clicked_lon, "address": addr}
            st.session_state["active_route"] = route
            st.session_state["origin_info"]  = st.session_state["click_origin"]
            st.session_state["dest_info"]    = st.session_state["click_dest"]
            st.session_state["map_click_state"] = "both_set"
            st.rerun()

        elif current_state == "both_set":
            # Third click resets to a new origin selection
            with st.spinner("Reverse geocoding new origin..."):
                addr = map_service.reverse_geocode(clicked_lat, clicked_lon)
            st.session_state["click_origin"] = {"lat": clicked_lat, "lon": clicked_lon, "address": addr}
            st.session_state["click_dest"]   = None
            st.session_state["active_route"] = None
            st.session_state["origin_info"]  = None
            st.session_state["dest_info"]    = None
            st.session_state["map_click_state"] = "waiting_dest"
            st.rerun()

    # ── Manage Roads on Map container ─────────────────────────────────────
    with st.expander("📍 Add / Register New Surveyed Road to Map"):
        st.markdown("Add newly inspected roads or custom GPS road segments to the live OpenStreetMap network:")
        acol1, acol2, acol3 = st.columns(3)
        with acol1:
            new_rname = st.text_input("Road Name:", value="", placeholder="e.g. Outer Ring Road Phase 2")
        with acol2:
            new_rscore = st.slider("Health Score (0-100):", min_value=0, max_value=100, value=75)
        with acol3:
            new_rurgency = st.selectbox("Maintenance Urgency:", ["Routine Monitoring", "Scheduled Repair (30 Days)", "Priority Repair (7 Days)", "Emergency Intervention"])

        st.caption("Enter Start & End Coordinates or Location Names:")
        gcol1, gcol2 = st.columns(2)
        with gcol1:
            start_loc_txt = st.text_input("Segment Start Point (Address or Lat, Lon):", value="", placeholder="e.g. 28.6300, 77.2200 or Connaught Place")
        with gcol2:
            end_loc_txt = st.text_input("Segment End Point (Address or Lat, Lon):", value="", placeholder="e.g. 28.6140, 77.2280 or India Gate")

        if st.button("➕ Plot New Road on Live Map", type="secondary"):
            if not new_rname.strip() or not start_loc_txt.strip() or not end_loc_txt.strip():
                st.warning("Please provide a Road Name and both Start and End locations.")
            else:
                def parse_or_geocode(txt):
                    if "," in txt and all(part.strip().replace(".", "").replace("-", "").isdigit() for part in txt.split(",")):
                        parts = txt.split(",")
                        return float(parts[0]), float(parts[1])
                    res = map_service.geocode_location(txt)
                    return (res[0], res[1]) if res else None

                p_start = parse_or_geocode(start_loc_txt)
                p_end = parse_or_geocode(end_loc_txt)

                if p_start and p_end:
                    r_color = "#22C55E" if new_rscore >= 70 else ("#EAB308" if new_rscore >= 50 else "#EF4444")
                    r_rating = "Good" if new_rscore >= 70 else ("Fair (Moderate)" if new_rscore >= 50 else "Critical (Hazardous)")

                    osrm_poly = map_service.get_osrm_route(p_start[0], p_start[1], p_end[0], p_end[1])
                    coords = osrm_poly["coordinates"] if (osrm_poly and osrm_poly.get("coordinates")) else [[p_start[0], p_start[1]], [p_end[0], p_end[1]]]

                    st.session_state["map_roads"].append({
                        "road_name": new_rname,
                        "rating": r_rating,
                        "health_score": float(new_rscore),
                        "color": r_color,
                        "urgency": new_rurgency,
                        "potholes_count": 0,
                        "coordinates": coords,
                        "potholes": []
                    })
                    st.success(f"✅ Successfully plotted '{new_rname}' with health rating {new_rscore}/100 on the live map!")
                    st.rerun()
                else:
                    st.error("Could not parse coordinates or locate addresses. Please check format.")

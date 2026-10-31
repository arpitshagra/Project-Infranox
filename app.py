import os
import time
import tempfile
import datetime
import json
import cv2
import numpy as np
import pandas as pd
import streamlit as st
from ultralytics import YOLO
from tracker import RoadPotholeTracker
from streamlit_folium import st_folium
import map_service

# =========================================================================
# PAGE CONFIGURATION & STYLING
# =========================================================================
st.set_page_config(
    page_title="INFRANOX | AI Road Intelligence Platform",
    page_icon="🚧",
    layout="wide",
    initial_sidebar_state="expanded"
)

PREMIUM_CSS = '''
<style>
    /* Import Google Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    /* Base */
    html, body, [class*="css"] { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important; }
    .stApp { background-color: #F8FAFC !important; color: #0F172A; }
    
    /* Hide default streamlit elements */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header[data-testid="stHeader"] { background: transparent; }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0F172A 0%, #1E293B 100%) !important;
        border-right: 1px solid #1E3A5F;
    }
    [data-testid="stSidebar"] * { color: #CBD5E1 !important; }
    [data-testid="stSidebar"] .stRadio label { 
        color: #94A3B8 !important; 
        font-size: 0.92rem !important;
        font-weight: 500 !important;
        padding: 8px 14px !important;
        border-radius: 8px !important;
        display: block !important;
        transition: all 0.2s ease !important;
        margin-bottom: 3px !important;
    }
    [data-testid="stSidebar"] .stRadio label:hover { 
        background: rgba(255,255,255,0.08) !important;
        color: #F1F5F9 !important;
    }
    [data-testid="stSidebar"] .stRadio div[aria-checked="true"] > label,
    [data-testid="stSidebar"] .stRadio div[data-checked="true"] > label {
        background: rgba(14, 165, 233, 0.18) !important;
        color: #38BDF8 !important;
        font-weight: 700 !important;
        border-left: 3px solid #0EA5E9 !important;
    }
    
    /* Main content padding */
    .main .block-container { 
        padding: 2rem 2.5rem !important; 
        max-width: 1440px !important;
    }
    
    /* Hero gradient text */
    .hero-title {
        font-size: 2.9rem;
        font-weight: 800;
        background: linear-gradient(135deg, #1D4ED8 0%, #0EA5E9 50%, #10B981 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        line-height: 1.18;
        margin-bottom: 0.8rem;
        letter-spacing: -0.02em;
    }
    
    /* Metric / KPI card */
    .kpi-card {
        background: white;
        border-radius: 16px;
        padding: 1.35rem 1.25rem;
        box-shadow: 0 1px 4px rgba(0,0,0,0.05), 0 4px 18px rgba(0,0,0,0.03);
        border: 1px solid #E2E8F0;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        text-align: center;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .kpi-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 22px rgba(0,0,0,0.08);
        border-color: #CBD5E1;
    }
    .kpi-number { 
        font-size: 2.25rem; 
        font-weight: 800; 
        color: #0F172A; 
        line-height: 1.1; 
        margin-bottom: 0.25rem;
    }
    .kpi-label { 
        font-size: 0.8rem; 
        font-weight: 700; 
        color: #475569; 
        text-transform: uppercase; 
        letter-spacing: 0.05em;
    }
    .kpi-sub {
        font-size: 0.78rem;
        color: #94A3B8;
        margin-top: 0.35rem;
        font-weight: 500;
    }
    
    /* Feature card */
    .feature-card {
        background: white;
        border-radius: 16px;
        padding: 1.6rem;
        border: 1px solid #E2E8F0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.04);
        height: 100%;
        display: flex;
        flex-direction: column;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .feature-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 24px rgba(0,0,0,0.08);
        border-color: #93C5FD;
    }
    .feature-icon {
        font-size: 2rem;
        margin-bottom: 0.85rem;
        display: inline-block;
        background: #EFF6FF;
        width: 52px;
        height: 52px;
        line-height: 52px;
        text-align: center;
        border-radius: 12px;
    }
    .feature-title {
        font-size: 1.12rem;
        font-weight: 700;
        color: #0F172A;
        margin-bottom: 0.5rem;
    }
    .feature-desc {
        font-size: 0.88rem;
        color: #64748B;
        line-height: 1.6;
    }
    
    /* Section header */
    .section-header {
        font-size: 1.65rem;
        font-weight: 800;
        color: #0F172A;
        margin-bottom: 0.3rem;
        letter-spacing: -0.01em;
    }
    .section-sub {
        font-size: 0.95rem;
        color: #64748B;
        margin-bottom: 1.5rem;
        line-height: 1.5;
    }
    
    /* Badges */
    .badge {
        display: inline-block;
        padding: 3px 12px;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.03em;
        text-align: center;
    }
    .badge-excellent { background: #D1FAE5; color: #065F46; border: 1px solid #A7F3D0; }
    .badge-good { background: #DCFCE7; color: #166534; border: 1px solid #BBF7D0; }
    .badge-fair { background: #FEF3C7; color: #92400E; border: 1px solid #FDE68A; }
    .badge-poor { background: #FEE2E2; color: #991B1B; border: 1px solid #FECACA; }
    .badge-critical { background: #FEE2E2; color: #7F1D1D; border: 1px solid #FCA5A5; font-weight: 700; }
    
    .badge-submitted { background: #DBEAFE; color: #1E40AF; border: 1px solid #BFDBFE; }
    .badge-review { background: #FEF3C7; color: #92400E; border: 1px solid #FDE68A; }
    .badge-resolved { background: #DCFCE7; color: #166534; border: 1px solid #BBF7D0; }

    /* Step card (How It Works) */
    .step-card {
        background: white;
        border-radius: 12px;
        padding: 1.25rem 1.4rem;
        border-left: 4px solid #1D4ED8;
        border-top: 1px solid #E2E8F0;
        border-right: 1px solid #E2E8F0;
        border-bottom: 1px solid #E2E8F0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.03);
        margin-bottom: 0.85rem;
        height: 100%;
    }
    .step-num {
        font-size: 0.75rem;
        font-weight: 800;
        color: #1D4ED8;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 0.25rem;
    }
    .step-title { font-size: 1.02rem; font-weight: 700; color: #0F172A; }
    .step-desc { font-size: 0.85rem; color: #64748B; margin-top: 0.35rem; line-height: 1.5; }
    
    /* Road rank card */
    .road-rank-card {
        background: white;
        border-radius: 14px;
        padding: 1.25rem 1.5rem;
        border: 1px solid #E2E8F0;
        margin-bottom: 0.85rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 1px 4px rgba(0,0,0,0.04);
        transition: transform 0.15s ease;
    }
    .road-rank-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 14px rgba(0,0,0,0.06);
    }
    
    /* Complaint card */
    .complaint-card {
        background: white;
        border-radius: 14px;
        padding: 1.4rem;
        border: 1px solid #E2E8F0;
        margin-bottom: 1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }
    
    /* Upload zone */
    [data-testid="stFileUploader"] {
        border: 2px dashed #93C5FD !important;
        border-radius: 12px !important;
        background: #F8FAFC !important;
        padding: 1.2rem !important;
    }
    
    /* Buttons */
    .stButton > button {
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        transition: all 0.2s ease !important;
        padding: 0.55rem 1.25rem !important;
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #1D4ED8, #0EA5E9) !important;
        border: none !important;
        color: white !important;
        box-shadow: 0 4px 12px rgba(29,78,216,0.3) !important;
    }
    .stButton > button[kind="primary"]:hover {
        box-shadow: 0 6px 20px rgba(29,78,216,0.45) !important;
        transform: translateY(-1px) !important;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        background: #F1F5F9;
        padding: 6px;
        border-radius: 12px;
        margin-bottom: 1.5rem;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px !important;
        padding: 10px 22px !important;
        font-weight: 600 !important;
        font-size: 0.92rem !important;
        color: #64748B !important;
    }
    .stTabs [aria-selected="true"] {
        background: white !important;
        color: #1D4ED8 !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08) !important;
    }
    
    /* Alert / info boxes */
    .info-box {
        background: #EFF6FF;
        border: 1px solid #BFDBFE;
        border-radius: 10px;
        padding: 1rem 1.25rem;
        color: #1E40AF;
        font-size: 0.9rem;
        margin-bottom: 1rem;
        line-height: 1.5;
    }
    .success-box {
        background: #ECFDF5;
        border: 1px solid #A7F3D0;
        border-radius: 10px;
        padding: 1rem 1.25rem;
        color: #065F46;
        font-size: 0.9rem;
        margin-bottom: 1rem;
    }
    .warning-box {
        background: #FFFBEB;
        border: 1px solid #FDE68A;
        border-radius: 10px;
        padding: 1rem 1.25rem;
        color: #92400E;
        font-size: 0.9rem;
        margin-bottom: 1rem;
    }
    
    /* Divider */
    .divider { 
        height: 1px; 
        background: linear-gradient(90deg, transparent, #E2E8F0, transparent); 
        margin: 2rem 0;
    }
    
    /* Sidebar brand */
    .sidebar-brand {
        padding: 1.25rem 0.75rem 1rem 0.75rem;
        border-bottom: 1px solid rgba(255,255,255,0.08);
        margin-bottom: 1rem;
    }
    .brand-logo { font-size: 1.45rem; font-weight: 800; color: #F8FAFC !important; letter-spacing: -0.02em; }
    .brand-tagline { font-size: 0.76rem; color: #94A3B8 !important; margin-top: 2px; }
    
    /* Nav section label */
    .nav-section-label {
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #64748B !important;
        padding: 0.5rem 0.75rem 0.25rem 0.75rem;
        margin-top: 0.5rem;
    }
    
    /* Metrics */
    [data-testid="stMetric"] {
        background: white;
        padding: 1rem 1.25rem;
        border-radius: 12px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    }
    [data-testid="stMetricLabel"] { font-weight: 600; color: #64748B; font-size: 0.85rem; }
    [data-testid="stMetricValue"] { font-weight: 800; color: #0F172A; }
    
    /* Progress bar */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #1D4ED8, #0EA5E9) !important;
    }

    /* Podium cards */
    .podium-card {
        background: white;
        border-radius: 14px;
        padding: 1.25rem;
        border: 1px solid #E2E8F0;
        text-align: center;
        box-shadow: 0 2px 10px rgba(0,0,0,0.04);
    }
</style>
'''
st.markdown(PREMIUM_CSS, unsafe_allow_html=True)

# =========================================================================
# SESSION STATE INITIALIZATION (PRESERVE ALL REQUIRED KEYS)
# =========================================================================
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

# Click-to-pin state for Route Planner
if "map_click_state" not in st.session_state:
    st.session_state["map_click_state"] = "waiting_origin"
if "click_origin" not in st.session_state:
    st.session_state["click_origin"] = None
if "click_dest" not in st.session_state:
    st.session_state["click_dest"] = None

# Click-to-pin state for Video Survey
if "survey_click_state" not in st.session_state:
    st.session_state["survey_click_state"] = "waiting_origin"
if "survey_click_origin" not in st.session_state:
    st.session_state["survey_click_origin"] = None
if "survey_click_dest" not in st.session_state:
    st.session_state["survey_click_dest"] = None

# Citizen Complaints Portal
if "complaints" not in st.session_state:
    st.session_state["complaints"] = [
        {
            "id": "CMP-1042",
            "name": "Rajesh Kumar",
            "phone": "+91 98101 23456",
            "location": "Connaught Place Radial 3 near Regal Cinema",
            "description": "Deep asphalt crater on outer lane causing dangerous bike skids during evening traffic.",
            "severity": "Critical",
            "timestamp": "2026-10-30 14:15",
            "status": "Under Review",
            "photo_bytes": None
        },
        {
            "id": "CMP-1043",
            "name": "Ananya Sharma",
            "phone": "+91 98712 34567",
            "location": "Barakhamba Road junction opposite Metro Pillar 44",
            "description": "Multiple edge cracks and medium depressions after recent rain; needs early patch repair.",
            "severity": "Moderate",
            "timestamp": "2026-10-31 09:30",
            "status": "Submitted",
            "photo_bytes": None
        }
    ]

# Navigation State
if "active_nav" not in st.session_state:
    st.session_state["active_nav"] = "🏠 Home"

# Auto-populate initial road registry from disk if empty
if not st.session_state["road_registry"]:
    if os.path.exists("road_assessment.csv"):
        try:
            init_df = pd.read_csv("road_assessment.csv")
            if not init_df.empty:
                st.session_state["road_registry"] = init_df.to_dict(orient="records")
        except Exception:
            pass

    # Ensure monitored community roads are reflected in registry
    if len(st.session_state["road_registry"]) < len(st.session_state["map_roads"]):
        existing_names = {r.get("Road Name", "") for r in st.session_state["road_registry"]}
        for mr in st.session_state["map_roads"]:
            rname = mr.get("road_name", "Surveyed Road")
            if rname not in existing_names:
                p_count = mr.get("potholes_count", len(mr.get("potholes", [])))
                h_score = float(mr.get("health_score", 70.0))
                cond = mr.get("rating", "Good" if h_score >= 70 else ("Fair" if h_score >= 50 else "Critical"))
                urg = mr.get("urgency", "Routine Monitoring" if h_score >= 70 else ("Scheduled Repair" if h_score >= 50 else "Emergency Intervention"))
                
                # Count severities if potholes present
                p_list = mr.get("potholes", [])
                s_sev = sum(1 for p in p_list if p.get("severity") == "Severe")
                s_mod = sum(1 for p in p_list if p.get("severity") == "Moderate")
                s_min = sum(1 for p in p_list if p.get("severity") == "Minor")
                if s_sev == 0 and s_mod == 0 and s_min == 0 and p_count > 0:
                    s_sev = p_count // 3
                    s_mod = p_count // 2
                    s_min = max(0, p_count - s_sev - s_mod)

                st.session_state["road_registry"].append({
                    "Road Name": rname,
                    "Health Score (0-100)": round(h_score, 1),
                    "Condition Rating": cond,
                    "Maintenance Urgency": urg,
                    "Urgency Level": 5 if h_score < 40 else (3 if h_score < 70 else 1),
                    "Total Potholes": p_count,
                    "Severe Potholes": s_sev,
                    "Moderate Potholes": s_mod,
                    "Minor Potholes": s_min,
                    "Pothole Density (/min)": round(p_count * 1.5, 1),
                    "Total Damaged Area (px²)": p_count * 14200,
                    "Avg Confidence": 0.76,
                    "Duration (s)": 60.0,
                    "Frames Evaluated": 1800
                })

# =========================================================================
# HELPER FUNCTIONS
# =========================================================================
@st.cache_resource
def load_yolo_model(model_path="best.pt"):
    if not os.path.exists(model_path):
        return None
    try:
        return YOLO(model_path)
    except Exception as e:
        st.error(f"Error loading model: {e}")
        return None


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


def get_health_badge_html(score):
    if score >= 80:
        return f'<span class="badge badge-excellent">Excellent ({score}/100)</span>'
    elif score >= 70:
        return f'<span class="badge badge-good">Good ({score}/100)</span>'
    elif score >= 50:
        return f'<span class="badge badge-fair">Fair ({score}/100)</span>'
    elif score >= 35:
        return f'<span class="badge badge-poor">Poor ({score}/100)</span>'
    else:
        return f'<span class="badge badge-critical">Critical ({score}/100)</span>'


# =========================================================================
# SIDEBAR SETUP & NAVIGATION
# =========================================================================
model_file = "best.pt"
model = load_yolo_model(model_file)

with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand">
        <div class="brand-logo">🚧 INFRANOX</div>
        <div class="brand-tagline">AI Road Intelligence & Pavement Safety</div>
    </div>
    """, unsafe_allow_html=True)

    # Model status indicator
    if model is not None:
        st.markdown(
            '<div style="background: rgba(16, 185, 129, 0.15); border: 1px solid #10B981; border-radius: 8px; padding: 6px 10px; margin-bottom: 12px; font-size: 0.78rem; color: #6EE7B7;">'
            '● <b>Model Active:</b> YOLOv8 Pothole Detector</div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            '<div style="background: rgba(239, 68, 68, 0.15); border: 1px solid #EF4444; border-radius: 8px; padding: 6px 10px; margin-bottom: 12px; font-size: 0.78rem; color: #FCA5A5;">'
            '▲ <b>Model Offline:</b> best.pt not found</div>',
            unsafe_allow_html=True
        )

    st.markdown('<div class="nav-section-label">PLATFORM VIEWS</div>', unsafe_allow_html=True)
    
    NAV_PAGES = [
        "🏠 Home",
        "📊 Dashboard",
        "🎯 AI Detection Studio",
        "🗺️ Road Map",
        "📈 Road Intelligence",
        "📝 Complaint Portal",
        "📋 Reports & Analytics"
    ]
    
    current_idx = NAV_PAGES.index(st.session_state["active_nav"]) if st.session_state["active_nav"] in NAV_PAGES else 0
    selected_page = st.radio(
        "Navigation Menu",
        options=NAV_PAGES,
        index=current_idx,
        label_visibility="collapsed"
    )
    
    if selected_page != st.session_state["active_nav"]:
        st.session_state["active_nav"] = selected_page
        st.rerun()

    st.markdown('<div class="divider" style="margin: 1.2rem 0;"></div>', unsafe_allow_html=True)
    
    # Expandable detection settings
    with st.expander("⚙️ Inference & Detection Settings", expanded=False):
        st.caption("Customize YOLO thresholding and tracking parameters:")
        
        conf_thresh = st.slider(
            "Confidence Threshold",
            min_value=0.05,
            max_value=0.90,
            value=0.20,
            step=0.05,
            help="Captures fainter & distant potholes without missing defects."
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
            help="640 is real-time fast; 960 & 1280 improve distant detection."
        )

        tracker_mode = st.selectbox(
            "Tracking Engine",
            options=[
                "Road-Aware Flow Tracker (Recommended)",
                "Pothole-Tuned ByteTrack",
                "Pothole-Tuned BoT-SORT"
            ],
            index=0,
            help="Compensates for forward vehicle speed to maintain unique persistent track IDs."
        )

        min_hits = st.slider(
            "Min Track Detections (Min Hits)",
            min_value=1,
            max_value=6,
            value=3,
            help="Ensures only genuine defects tracked across multiple frames are counted."
        )

        frame_step = st.slider(
            "Process Frame Skip (Every Nth)",
            min_value=1,
            max_value=10,
            value=1,
            help="1 = full fidelity; 2 = 2x speed; 5+ = quick scan."
        )

        save_annotated_video = st.checkbox(
            "Export Annotated Video (.mp4)",
            value=True,
            help="Generates an output video with tracking bounding boxes drawn."
        )

    st.markdown("""
    <div style="padding: 12px 6px; font-size: 0.72rem; color: #64748B; border-top: 1px solid rgba(255,255,255,0.06); margin-top: 2rem;">
        <div><b>INFRANOX PLATFORM v2.4</b></div>
        <div>Neural Vision • GIS Route Engine</div>
        <div style="color: #475569; margin-top: 4px;">Connected to OpenStreetMap & OSRM</div>
    </div>
    """, unsafe_allow_html=True)


# =========================================================================
# PAGE 1: 🏠 HOME / LANDING
# =========================================================================
if st.session_state["active_nav"] == "🏠 Home":
    # Hero Section
    st.markdown("""
    <div style="background: linear-gradient(135deg, #0F172A 0%, #1E293B 55%, #0F172A 100%); border-radius: 20px; padding: 3rem 2.5rem; margin-bottom: 2rem; border: 1px solid #334155; box-shadow: 0 12px 36px rgba(0,0,0,0.22); text-align: center;">
        <div style="display: inline-block; padding: 4px 16px; border-radius: 20px; background: rgba(14, 165, 233, 0.15); border: 1px solid #0EA5E9; color: #38BDF8; font-size: 0.8rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 1.2rem;">
            Autonomous Infrastructure Vision & GIS Intelligence
        </div>
        <h1 class="hero-title" style="margin-bottom: 0.85rem;">
            AI-Powered Road Intelligence & Pavement Safety
        </h1>
        <p style="font-size: 1.12rem; color: #94A3B8; max-width: 840px; margin: 0 auto 1.8rem auto; line-height: 1.6;">
            Transform video dashcams and mobile footage into actionable municipal infrastructure intelligence. 
            Real-time neural pothole detection, optical flow-compensated defect tracking, ASTM D6433 Pavement Condition Index (PCI) profiling, and live OpenStreetMap hazard corridors.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # CTA Buttons
    c_btn1, c_btn2, c_btn3, c_btn4 = st.columns(4)
    with c_btn1:
        if st.button("🚀 Launch Detection Studio", type="primary", use_container_width=True):
            st.session_state["active_nav"] = "🎯 AI Detection Studio"
            st.rerun()
    with c_btn2:
        if st.button("🗺️ Explore Live Road Map", use_container_width=True):
            st.session_state["active_nav"] = "🗺️ Road Map"
            st.rerun()
    with c_btn3:
        if st.button("📊 View Executive Dashboard", use_container_width=True):
            st.session_state["active_nav"] = "📊 Dashboard"
            st.rerun()
    with c_btn4:
        if st.button("📝 Citizen Hazard Portal", use_container_width=True):
            st.session_state["active_nav"] = "📝 Complaint Portal"
            st.rerun()

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # Real-Time Statistics Row (Pulled from live data)
    roads_count = len(st.session_state["map_roads"])
    
    # Calculate real pothole counts
    total_potholes = 0
    if os.path.exists("potholes_catalog.csv"):
        try:
            df_cat = pd.read_csv("potholes_catalog.csv")
            total_potholes = len(df_cat)
        except Exception:
            total_potholes = sum(r.get("potholes_count", len(r.get("potholes", []))) for r in st.session_state["map_roads"])
    else:
        total_potholes = sum(r.get("potholes_count", len(r.get("potholes", []))) for r in st.session_state["map_roads"])

    scores = [float(r.get("health_score", 0)) for r in st.session_state["map_roads"] if "health_score" in r]
    avg_health = round(float(np.mean(scores)), 1) if scores else 68.5
    critical_roads = sum(1 for s in scores if s < 50)

    st.markdown('<div class="section-header">Live Road Network Vital Signs</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Synchronized telemetry from municipal road inspections, dashcam surveys, and verified citizen reports.</div>', unsafe_allow_html=True)

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-number">{total_potholes:,}</div>
            <div class="kpi-label">Potholes Cataloged</div>
            <div class="kpi-sub">Verified unique physical defects</div>
        </div>
        """, unsafe_allow_html=True)
    with k2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-number">{roads_count}</div>
            <div class="kpi-label">Inspected Corridors</div>
            <div class="kpi-sub">Registered OpenStreetMap segments</div>
        </div>
        """, unsafe_allow_html=True)
    with k3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-number">{avg_health}<span style="font-size: 1.2rem; color: #64748B;">/100</span></div>
            <div class="kpi-label">Average Pavement Health</div>
            <div class="kpi-sub">ASTM D6433 Pavement Condition Index</div>
        </div>
        """, unsafe_allow_html=True)
    with k4:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-number" style="color: #EF4444;">{critical_roads}</div>
            <div class="kpi-label">Critical Hazard Roads</div>
            <div class="kpi-sub">Require immediate priority repair</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # Core Capabilities Grid
    st.markdown('<div class="section-header">Next-Generation Engineering Capabilities</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Designed for municipal highway departments, civil engineering contractors, and smart-city mobility operators.</div>', unsafe_allow_html=True)

    f1, f2, f3, f4 = st.columns(4)
    with f1:
        st.markdown("""
        <div class="feature-card">
            <span class="feature-icon">🎯</span>
            <div class="feature-title">Precision YOLOv8 Vision</div>
            <div class="feature-desc">Sub-second neural defect segmentation tuned for faint surface fissures, complex shadows, wet asphalt, and deep craters.</div>
        </div>
        """, unsafe_allow_html=True)
    with f2:
        st.markdown("""
        <div class="feature-card">
            <span class="feature-icon">🔄</span>
            <div class="feature-title">Road-Aware Flow Tracking</div>
            <div class="feature-desc">Forward-velocity motion compensation binds physical defects with permanent unique IDs, eliminating multi-frame duplicate counts.</div>
        </div>
        """, unsafe_allow_html=True)
    with f3:
        st.markdown("""
        <div class="feature-card">
            <span class="feature-icon">🗺️</span>
            <div class="feature-title">Live GIS Road Maps</div>
            <div class="feature-desc">Automated OpenStreetMap synchronization with OSRM routing, color-coded safety corridors, and interactive click-to-pin navigation.</div>
        </div>
        """, unsafe_allow_html=True)
    with f4:
        st.markdown("""
        <div class="feature-card">
            <span class="feature-icon">📊</span>
            <div class="feature-title">Automated Civil Profiler</div>
            <div class="feature-desc">ASTM D6433-inspired Pavement Condition Index (PCI 0-100), defect surface density analysis, and work-order urgency scheduling.</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # How It Works Workflow
    st.markdown('<div class="section-header">Operational Workflow</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">From raw camera footage to synchronized municipal maintenance work orders in four automated steps:</div>', unsafe_allow_html=True)

    s1, s2, s3, s4 = st.columns(4)
    with s1:
        st.markdown("""
        <div class="step-card">
            <div class="step-num">Step 01</div>
            <div class="step-title">Capture & Ingest</div>
            <div class="step-desc">Upload vehicle dashcam video, drone footage, or smartphone photos with designated corridor coordinates.</div>
        </div>
        """, unsafe_allow_html=True)
    with s2:
        st.markdown("""
        <div class="step-card">
            <div class="step-num">Step 02</div>
            <div class="step-title">AI Detection & Tracking</div>
            <div class="step-desc">Infranox neural vision identifies physical potholes and binds them with persistent unique track IDs.</div>
        </div>
        """, unsafe_allow_html=True)
    with s3:
        st.markdown("""
        <div class="step-card">
            <div class="step-num">Step 03</div>
            <div class="step-title">PCI Health Scoring</div>
            <div class="step-desc">Computes defect density, surface damage area, and classifies urgency from Routine to Emergency Intervention.</div>
        </div>
        """, unsafe_allow_html=True)
    with s4:
        st.markdown("""
        <div class="step-card">
            <div class="step-num">Step 04</div>
            <div class="step-title">GIS Sync & Action</div>
            <div class="step-desc">Automatically plots surveyed segment to the live community map with safety advisories for daily commuters.</div>
        </div>
        """, unsafe_allow_html=True)


# =========================================================================
# PAGE 2: 📊 DASHBOARD
# =========================================================================
elif st.session_state["active_nav"] == "📊 Dashboard":
    st.markdown('<div class="section-header">📊 Municipal Infrastructure Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Network-wide health distribution, severity indices, and condition audits across surveyed corridors.</div>', unsafe_allow_html=True)

    # Data aggregation
    map_roads = st.session_state["map_roads"]
    total_roads = len(map_roads)
    
    # Load catalog data if available
    total_catalog_potholes = 0
    severe_count = 0
    mod_count = 0
    minor_count = 0
    
    if os.path.exists("potholes_catalog.csv"):
        try:
            df_cat = pd.read_csv("potholes_catalog.csv")
            total_catalog_potholes = len(df_cat)
            if "Severity" in df_cat.columns:
                severe_count = int((df_cat["Severity"] == "Severe").sum())
                mod_count = int((df_cat["Severity"] == "Moderate").sum())
                minor_count = int((df_cat["Severity"] == "Minor").sum())
        except Exception:
            pass

    if total_catalog_potholes == 0:
        for r in map_roads:
            p_list = r.get("potholes", [])
            total_catalog_potholes += len(p_list)
            for p in p_list:
                s = p.get("severity", "Moderate")
                if s == "Severe":
                    severe_count += 1
                elif s == "Moderate":
                    mod_count += 1
                else:
                    minor_count += 1

    scores = [float(r.get("health_score", 0)) for r in map_roads if "health_score" in r]
    avg_score = round(float(np.mean(scores)), 1) if scores else 65.0
    critical_roads = sum(1 for s in scores if s < 50)

    # Top KPI Cards
    dk1, dk2, dk3, dk4 = st.columns(4)
    with dk1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-number">{total_catalog_potholes:,}</div>
            <div class="kpi-label">Potholes Detected</div>
            <div class="kpi-sub">Across {total_roads} monitored road corridors</div>
        </div>
        """, unsafe_allow_html=True)
    with dk2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-number">{total_roads}</div>
            <div class="kpi-label">Corridors Inspected</div>
            <div class="kpi-sub">GIS mapped and scored</div>
        </div>
        """, unsafe_allow_html=True)
    with dk3:
        badge_class = "badge-excellent" if avg_score >= 80 else ("badge-good" if avg_score >= 70 else ("badge-fair" if avg_score >= 50 else "badge-critical"))
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-number">{avg_score}</div>
            <div class="kpi-label">Avg Pavement Health</div>
            <div class="kpi-sub"><span class="badge {badge_class}">Network Status</span></div>
        </div>
        """, unsafe_allow_html=True)
    with dk4:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-number" style="color: #EF4444;">{critical_roads}</div>
            <div class="kpi-label">Critical Roads (PCI &lt; 50)</div>
            <div class="kpi-sub">Priority repair scheduling</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # Visualizations Row
    vcol1, vcol2 = st.columns([3, 2])
    
    with vcol1:
        st.markdown("#### 📈 Road Pavement Health Comparison (PCI 0–100)")
        st.caption("Standardized ASTM Pavement Condition Index for all surveyed corridors:")
        
        # Prepare bar chart data
        chart_records = []
        for r in map_roads:
            chart_records.append({
                "Road Name": r.get("road_name", "Unknown"),
                "Health Score": float(r.get("health_score", 0.0))
            })
        if chart_records:
            df_chart = pd.DataFrame(chart_records).set_index("Road Name")
            st.bar_chart(df_chart, height=320)
        else:
            st.info("No road survey records available.")

    with vcol2:
        st.markdown("#### 🎯 Defect Severity Distribution")
        st.caption("Relative breakdown of registered pothole impact classifications:")
        
        tot_classified = max(1, severe_count + mod_count + minor_count)
        p_sev = round((severe_count / tot_classified) * 100, 1)
        p_mod = round((mod_count / tot_classified) * 100, 1)
        p_min = round((minor_count / tot_classified) * 100, 1)

        st.markdown(f"""
        <div style="background: white; border-radius: 14px; padding: 1.5rem; border: 1px solid #E2E8F0; box-shadow: 0 1px 4px rgba(0,0,0,0.04);">
            <div style="margin-bottom: 1.25rem;">
                <div style="display: flex; justify-content: space-between; font-size: 0.88rem; font-weight: 700; color: #991B1B; margin-bottom: 4px;">
                    <span>🔴 Severe / Critical Defects</span>
                    <span>{severe_count} ({p_sev}%)</span>
                </div>
                <div style="background: #FEE2E2; height: 10px; border-radius: 6px; overflow: hidden;">
                    <div style="background: #EF4444; width: {p_sev}%; height: 100%;"></div>
                </div>
            </div>
            <div style="margin-bottom: 1.25rem;">
                <div style="display: flex; justify-content: space-between; font-size: 0.88rem; font-weight: 700; color: #92400E; margin-bottom: 4px;">
                    <span>🟡 Moderate Defects</span>
                    <span>{mod_count} ({p_mod}%)</span>
                </div>
                <div style="background: #FEF3C7; height: 10px; border-radius: 6px; overflow: hidden;">
                    <div style="background: #F59E0B; width: {p_mod}%; height: 100%;"></div>
                </div>
            </div>
            <div>
                <div style="display: flex; justify-content: space-between; font-size: 0.88rem; font-weight: 700; color: #166534; margin-bottom: 4px;">
                    <span>🟢 Minor Surface Chips</span>
                    <span>{minor_count} ({p_min}%)</span>
                </div>
                <div style="background: #DCFCE7; height: 10px; border-radius: 6px; overflow: hidden;">
                    <div style="background: #10B981; width: {p_min}%; height: 100%;"></div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Severity bar chart
        sev_df = pd.DataFrame({
            "Severity": ["Severe (Critical)", "Moderate", "Minor"],
            "Count": [severe_count, mod_count, minor_count]
        }).set_index("Severity")
        st.bar_chart(sev_df, height=180)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # Monitored Road Corridors Cards Grid
    st.markdown("#### 🛣️ Monitored Corridors & Pavement Condition Profiles")
    st.caption("Detailed civil condition records for each registered corridor:")

    r_cols = st.columns(min(3, max(1, len(map_roads))))
    for idx, r in enumerate(map_roads):
        with r_cols[idx % len(r_cols)]:
            score = float(r.get("health_score", 0))
            rating = r.get("rating", "N/A")
            urgency = r.get("urgency", "Routine Monitoring")
            p_cnt = r.get("potholes_count", len(r.get("potholes", [])))
            r_name = r.get("road_name", f"Corridor #{idx+1}")
            
            badge_html = get_health_badge_html(score)
            progress_val = min(100.0, max(0.0, score)) / 100.0
            
            st.markdown(f"""
            <div style="background: white; border-radius: 14px; padding: 1.25rem 1.4rem; border: 1px solid #E2E8F0; margin-bottom: 1rem; box-shadow: 0 1px 4px rgba(0,0,0,0.04);">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.5rem;">
                    <b style="font-size: 1rem; color: #0F172A;">{r_name}</b>
                    {badge_html}
                </div>
                <div style="font-size: 0.85rem; color: #64748B; margin-bottom: 0.75rem;">
                    Maintenance: <b style="color: #0F172A;">{urgency}</b> • Defects: <b>{p_cnt}</b>
                </div>
                <div style="background: #F1F5F9; border-radius: 999px; height: 8px; overflow: hidden;">
                    <div style="background: {r.get('color', '#2563EB')}; width: {score}%; height: 100%;"></div>
                </div>
                <div style="font-size: 0.75rem; color: #94A3B8; margin-top: 6px; text-align: right;">
                    PCI Health: {score}/100
                </div>
            </div>
            """, unsafe_allow_html=True)


# =========================================================================
# PAGE 3: 🎯 AI DETECTION STUDIO (PRESERVE ALL DETECTION & TRACKING LOGIC)
# =========================================================================
elif st.session_state["active_nav"] == "🎯 AI Detection Studio":
    st.markdown('<div class="section-header">🎯 AI Detection Studio</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">High-precision neural defect identification, forward-motion tracking, and automated road condition profiling.</div>', unsafe_allow_html=True)

    tab_video, tab_image = st.tabs(["📹 Video Survey & Road Profiler", "📸 Single / Batch Image Inspection"])

    # -------------------------------------------------------------------------
    # TAB 1: VIDEO ANALYSIS & ROAD RANKING
    # -------------------------------------------------------------------------
    with tab_video:
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
                                    returned_objects=["last_clicked"], key="studio_survey_map")

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
                with st.spinner("Reverse geocoding new start..."):
                    addr = map_service.reverse_geocode(s_lat, s_lon)
                st.session_state["survey_click_origin"] = {"lat": s_lat, "lon": s_lon, "address": addr}
                st.session_state["survey_click_dest"]   = None
                st.session_state["survey_click_state"]  = "waiting_dest"
                st.rerun()

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

                        # Compute Civil Profile
                        road_profile = RoadPotholeTracker.compute_road_ranking_profile(
                            road_name=custom_road_name,
                            records=unique_pothole_records,
                            duration_sec=effective_duration_sec,
                            frames_analyzed=processed_count
                        )

                        # Update session state registry for leaderboard
                        existing_idx = next((i for i, r in enumerate(st.session_state["road_registry"]) if r.get("Road Name") == custom_road_name), None)
                        if existing_idx is not None:
                            st.session_state["road_registry"][existing_idx] = road_profile
                        else:
                            st.session_state["road_registry"].append(road_profile)

                        # Register road survey to OpenStreetMap community database
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

                        # Display Assessment Cards
                        st.markdown("---")
                        st.header(f"🛣️ Road Quality Assessment: `{custom_road_name}`")
                        
                        if survey_entry:
                            st.success(
                                f"🗺️ **Road Automatically Mapped on OpenStreetMap!** `{custom_road_name}` "
                                f"(Health Score: **{road_profile['Health Score (0-100)']}/100**, {road_profile['Condition Rating']}) "
                                f"is now plotted on the live network with {len(survey_entry['potholes'])} pothole pins."
                            )

                        rcol1, rcol2, rcol3, rcol4 = st.columns(4)
                        rcol1.metric("Pavement Health Score", f"{road_profile['Health Score (0-100)']}/100")
                        rcol2.metric("Condition Rating", f"{road_profile['Condition Rating']}")
                        rcol3.metric("Maintenance Urgency", f"{road_profile['Maintenance Urgency']}")
                        rcol4.metric("Pothole Density", f"{road_profile['Pothole Density (/min)']} /min")

                        st.markdown("**Road Condition Gauge:**")
                        score_val = road_profile['Health Score (0-100)']
                        st.progress(score_val / 100.0, text=f"Health Score: {score_val}% ({road_profile['Condition Rating']})")

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

                        # Export Catalogs
                        st.markdown("---")
                        st.subheader("📥 Export Inspection Catalogs & Reports")
                        
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
                        
                        # Save to workspace disk
                        df_potholes.to_csv("potholes_catalog.csv", index=False)

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

                        # Unique Potholes Gallery
                        if unique_pothole_records:
                            st.markdown("---")
                            st.subheader(f"📸 Unique Potholes Gallery ({len(unique_pothole_records)} Distinct Potholes Identified)")
                            
                            view_mode = st.radio("Gallery View Mode:", ["Close-up Pothole Crops", "Full Frame Context"], horizontal=True)

                            pothole_items = sorted(unique_pothole_records.values(), key=lambda x: x["track_id"])
                            g_cols = st.columns(3)
                            for i, rec in enumerate(pothole_items):
                                with g_cols[i % 3]:
                                    img_to_show = rec["crop"] if (view_mode == "Close-up Pothole Crops" and rec.get("crop") is not None) else rec.get("annotated_snapshot")
                                    if img_to_show is not None:
                                        st.image(
                                            img_to_show,
                                            caption=f"Pothole #{rec['track_id']} | Severity: {rec.get('severity', 'N/A')} | Conf: {rec['max_conf']}",
                                            use_container_width=True
                                        )

            else:
                st.error("Could not read video metadata. Please ensure the video file is valid.")

    # -------------------------------------------------------------------------
    # TAB 2: IMAGE INSPECTION
    # -------------------------------------------------------------------------
    with tab_image:
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
# PAGE 4: 🗺️ ROAD MAP & ROUTE PLANNER (PRESERVE ALL MAP LOGIC)
# =========================================================================
elif st.session_state["active_nav"] == "🗺️ Road Map":
    st.markdown('<div class="section-header">🗺️ Live Road Quality Map & Safe Route Planner</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Visualize surveyed roads with color-coded pavement ratings, inspect pothole hazard pins, and plan routes by <b>clicking directly on the map</b>.</div>', unsafe_allow_html=True)

    # Click-to-pin status banner
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

    # Reset button
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

    # Text-input fallback
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

    # Route metrics strip
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
                    <div style="background-color: white; border: 1px solid #E2E8F0; border-radius: 10px; padding: 12px; margin-bottom: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
                        <b style="color: #0F172A;">{seg['road_name']}</b><br>
                        Pavement Health: <span style="font-weight: bold; color: {score_col};">{seg['health_score']}/100 ({seg['rating']})</span><br>
                        <span style="font-size: 0.82rem; color: #64748B;">Potholes Reported: {seg['potholes_count']} | Survey Date: {seg['survey_date']}</span>
                    </div>
                    """, unsafe_allow_html=True)

    # Map Legend
    st.markdown("---")
    st.subheader("🗺️ Interactive Road Surface Quality Map")
    st.markdown("""
    <div style="display: flex; flex-wrap: wrap; gap: 20px; align-items: center; margin-bottom: 12px; font-size: 0.88rem;">
        <div><b>Corridor Ratings:</b></div>
        <div><span style="color: #22C55E; font-size: 1.2rem;">■</span> Excellent / Good (PCI ≥ 70)</div>
        <div><span style="color: #EAB308; font-size: 1.2rem;">■</span> Fair (PCI 50–69)</div>
        <div><span style="color: #EF4444; font-size: 1.2rem;">■</span> Critical / Severe (PCI &lt; 50)</div>
        <div><span style="color: #2563EB; font-size: 1.2rem;">━ ━</span> Planned Route</div>
        <div><span style="color: red;">⚠️</span> Pothole Hazard Pin</div>
    </div>
    <div style="background:#EFF6FF; border:1px solid #BFDBFE; border-radius:8px; padding:10px 16px; font-size:0.88rem; margin-bottom:12px; color: #1E40AF;">
        💡 <b>Click on the map</b> to drop pins — 1st click = 🟢 Origin, 2nd click = 🏁 Destination. Route auto-calculates!
    </div>
    """, unsafe_allow_html=True)

    # Render interactive Folium map
    map_obj = map_service.build_road_quality_map(
        road_segments=st.session_state["map_roads"],
        route_data=st.session_state["active_route"],
        origin_info=st.session_state["origin_info"],
        dest_info=st.session_state["dest_info"],
        click_origin=st.session_state["click_origin"] if click_state in ("waiting_dest",) else None,
        click_dest=st.session_state["click_dest"] if click_state == "waiting_dest" else None,
    )

    map_data = st_folium(map_obj, width="100%", height=580, returned_objects=["last_clicked"])

    # Handle map click events
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
            with st.spinner("Reverse geocoding new origin..."):
                addr = map_service.reverse_geocode(clicked_lat, clicked_lon)
            st.session_state["click_origin"] = {"lat": clicked_lat, "lon": clicked_lon, "address": addr}
            st.session_state["click_dest"]   = None
            st.session_state["active_route"] = None
            st.session_state["origin_info"]  = None
            st.session_state["dest_info"]    = None
            st.session_state["map_click_state"] = "waiting_dest"
            st.rerun()

    # Add / Register New Surveyed Road to Map container
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


# =========================================================================
# PAGE 5: 📈 ROAD INTELLIGENCE (LEADERBOARD)
# =========================================================================
elif st.session_state["active_nav"] == "📈 Road Intelligence":
    st.markdown('<div class="section-header">📈 Comprehensive Road Quality Leaderboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Cross-comparison of analyzed road segments ranked by ASTM Pavement Health Score, Defect Density, and Maintenance Urgency.</div>', unsafe_allow_html=True)

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

        # Top 3 Podium Highlights
        st.markdown("#### 🏆 Priority Highlights")
        pod_cols = st.columns(min(3, len(df_sorted)))
        medals = ["🥇", "🥈", "🥉"]
        
        for i in range(min(3, len(df_sorted))):
            row = df_sorted.iloc[i]
            with pod_cols[i]:
                score = float(row["Health Score (0-100)"])
                badge_html = get_health_badge_html(score)
                st.markdown(f"""
                <div class="podium-card">
                    <div style="font-size: 1.8rem; margin-bottom: 4px;">{medals[i]}</div>
                    <div style="font-size: 1rem; font-weight: 800; color: #0F172A; margin-bottom: 6px;">{row['Road Name']}</div>
                    <div style="margin-bottom: 8px;">{badge_html}</div>
                    <div style="font-size: 0.8rem; color: #64748B;">Urgency: <b>{row.get('Maintenance Urgency', 'N/A')}</b></div>
                    <div style="font-size: 0.8rem; color: #64748B;">Potholes: <b>{row.get('Total Potholes', 0)}</b> ({row.get('Severe Potholes', 0)} severe)</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown('<div class="divider" style="margin: 1.5rem 0;"></div>', unsafe_allow_html=True)
        
        # Display Table
        display_cols = [
            "Rank #", "Road Name", "Health Score (0-100)", "Condition Rating",
            "Maintenance Urgency", "Total Potholes", "Severe Potholes", "Moderate Potholes",
            "Minor Potholes", "Pothole Density (/min)", "Total Damaged Area (px²)", "Duration (s)"
        ]
        available_cols = [c for c in display_cols if c in df_sorted.columns]
        st.dataframe(df_sorted[available_cols], use_container_width=True, hide_index=True)

        # Summary Bar Chart
        st.markdown("#### 📊 Comparative Health Scores")
        chart_data = df_sorted.set_index("Road Name")["Health Score (0-100)"]
        st.bar_chart(chart_data)

        # Export and Clear Controls
        csv_board = df_sorted.to_csv(index=False).encode('utf-8')
        dcol1, dcol2 = st.columns([1, 1])
        with dcol1:
            st.download_button(
                "⬇️ Download Road Rankings Leaderboard CSV",
                data=csv_board,
                file_name="road_rankings_leaderboard.csv",
                mime="text/csv",
                type="primary",
                use_container_width=True
            )
        with dcol2:
            if st.button("🗑️ Clear Road Rankings Registry", use_container_width=True):
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
# PAGE 6: 📝 PUBLIC COMPLAINT PORTAL
# =========================================================================
elif st.session_state["active_nav"] == "📝 Complaint Portal":
    st.markdown('<div class="section-header">📝 Public Complaint & Grievance Portal</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Citizen reporting and municipal work-order tracking system for hazardous potholes and surface damage.</div>', unsafe_allow_html=True)

    # Complaints Summary KPIs
    complaints_list = st.session_state["complaints"]
    total_cmp = len(complaints_list)
    sub_cmp = sum(1 for c in complaints_list if c["status"] == "Submitted")
    rev_cmp = sum(1 for c in complaints_list if c["status"] == "Under Review")
    res_cmp = sum(1 for c in complaints_list if c["status"] == "Resolved")

    ck1, ck2, ck3, ck4 = st.columns(4)
    with ck1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-number">{total_cmp}</div>
            <div class="kpi-label">Total Reports</div>
            <div class="kpi-sub">Citizen grievances logged</div>
        </div>
        """, unsafe_allow_html=True)
    with ck2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-number" style="color: #2563EB;">{sub_cmp}</div>
            <div class="kpi-label">Submitted</div>
            <div class="kpi-sub">Awaiting team assignment</div>
        </div>
        """, unsafe_allow_html=True)
    with ck3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-number" style="color: #D97706;">{rev_cmp}</div>
            <div class="kpi-label">Under Review</div>
            <div class="kpi-sub">Inspection team dispatched</div>
        </div>
        """, unsafe_allow_html=True)
    with ck4:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-number" style="color: #10B981;">{res_cmp}</div>
            <div class="kpi-label">Resolved</div>
            <div class="kpi-sub">Pavement repaired & cleared</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    form_col, list_col = st.columns([1, 1])

    # Left: Submission Form
    with form_col:
        st.markdown("#### 📢 Submit Road Defect Report")
        with st.form("complaint_form", clear_on_submit=True):
            c_name = st.text_input("Your Full Name:", placeholder="e.g. Vikramaditya Singh")
            c_phone = st.text_input("Phone Number / Email:", placeholder="e.g. +91 98123 45678")
            c_loc = st.text_input("Road Location / Landmark:", placeholder="e.g. Outer Ring Road near IIT Flyover")
            
            c_sev = st.selectbox(
                "Estimated Hazard Severity:",
                options=[
                    "Critical (Deep crater / hazard to two-wheelers & cars)",
                    "Moderate (Noticeable depression / requires slowing down)",
                    "Minor (Surface chipping / cracking)"
                ]
            )
            c_desc = st.text_area("Detailed Description:", placeholder="Describe the defect, approximate depth/width, and any nearby landmark.")
            c_photo = st.file_uploader("Upload Photo Evidence (Optional):", type=["jpg", "png", "jpeg"])
            
            submit_btn = st.form_submit_button("🚨 Submit Hazard Complaint", type="primary", use_container_width=True)

            if submit_btn:
                if not c_name.strip() or not c_loc.strip():
                    st.error("Please provide both your Name and the Road Location.")
                else:
                    sev_clean = "Critical" if "Critical" in c_sev else ("Moderate" if "Moderate" in c_sev else "Minor")
                    photo_bytes = c_photo.read() if c_photo is not None else None
                    
                    new_entry = {
                        "id": f"CMP-{int(time.time()) % 10000:04d}",
                        "name": c_name.strip(),
                        "phone": c_phone.strip(),
                        "location": c_loc.strip(),
                        "description": c_desc.strip(),
                        "severity": sev_clean,
                        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "status": "Submitted",
                        "photo_bytes": photo_bytes
                    }
                    st.session_state["complaints"].insert(0, new_entry)
                    st.success(f"✅ Complaint {new_entry['id']} successfully lodged with municipal highway control!")
                    st.rerun()

    # Right: Existing Complaints Feed
    with list_col:
        st.markdown("#### 📋 Live Grievance Tracking Feed")
        
        status_filter = st.selectbox("Filter by Status:", ["All", "Submitted", "Under Review", "Resolved"])
        
        filtered_complaints = [
            c for c in st.session_state["complaints"]
            if status_filter == "All" or c["status"] == status_filter
        ]

        if not filtered_complaints:
            st.info("No complaints found matching this status filter.")
        else:
            for c_idx, cmp in enumerate(filtered_complaints):
                # Badges
                s_cls = "badge-critical" if cmp["severity"] == "Critical" else ("badge-fair" if cmp["severity"] == "Moderate" else "badge-good")
                stat_cls = "badge-submitted" if cmp["status"] == "Submitted" else ("badge-review" if cmp["status"] == "Under Review" else "badge-resolved")

                st.markdown(f"""
                <div class="complaint-card">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <div>
                            <b style="font-size: 0.95rem; color: #0F172A;">{cmp['id']}</b> • 
                            <span style="font-size: 0.8rem; color: #64748B;">{cmp['timestamp']}</span>
                        </div>
                        <div>
                            <span class="badge {s_cls}">{cmp['severity']}</span>
                            <span class="badge {stat_cls}">{cmp['status']}</span>
                        </div>
                    </div>
                    <div style="font-weight: 600; color: #1E293B; margin-bottom: 4px; font-size: 0.9rem;">
                        📍 {cmp['location']}
                    </div>
                    <div style="font-size: 0.85rem; color: #475569; margin-bottom: 8px; line-height: 1.4;">
                        "{cmp['description']}"
                    </div>
                    <div style="font-size: 0.78rem; color: #94A3B8;">
                        Reported by: <b>{cmp['name']}</b> ({cmp['phone']})
                    </div>
                </div>
                """, unsafe_allow_html=True)

                if cmp.get("photo_bytes") is not None:
                    st.image(cmp["photo_bytes"], caption=f"Evidence for {cmp['id']}", use_container_width=True)

                # Quick status change controls
                c_act1, c_act2 = st.columns(2)
                with c_act1:
                    if cmp["status"] == "Submitted":
                        if st.button(f"🔍 Mark Under Review", key=f"rev_{cmp['id']}_{c_idx}", use_container_width=True):
                            cmp["status"] = "Under Review"
                            st.rerun()
                with c_act2:
                    if cmp["status"] != "Resolved":
                        if st.button(f"✅ Mark Resolved", key=f"res_{cmp['id']}_{c_idx}", use_container_width=True):
                            cmp["status"] = "Resolved"
                            st.rerun()


# =========================================================================
# PAGE 7: 📋 REPORTS & ANALYTICS
# =========================================================================
elif st.session_state["active_nav"] == "📋 Reports & Analytics":
    st.markdown('<div class="section-header">📋 Reports, Catalogs & Data Analytics</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Inspect persistent pothole catalogs, audit trail records, and export civil maintenance datasets.</div>', unsafe_allow_html=True)

    tab_cat, tab_road, tab_gis, tab_stats = st.tabs([
        "🗂️ Pothole Detection Catalog",
        "🛣️ Road Assessment Registry",
        "🗺️ Community GIS Network (JSON)",
        "📊 Statistical Analysis"
    ])

    # TAB 1: Potholes Catalog
    with tab_cat:
        st.markdown("#### 🗂️ Pothole Detections Catalog (CSV)")
        if os.path.exists("potholes_catalog.csv"):
            try:
                df_cat = pd.read_csv("potholes_catalog.csv")
                
                fcol1, fcol2, fcol3 = st.columns(3)
                with fcol1:
                    if "Severity" in df_cat.columns:
                        sev_opts = ["All"] + list(df_cat["Severity"].unique())
                        sel_sev = st.selectbox("Filter by Severity:", sev_opts)
                    else:
                        sel_sev = "All"
                with fcol2:
                    if "Highest Confidence Score" in df_cat.columns:
                        min_conf_val = float(df_cat["Highest Confidence Score"].min())
                        max_conf_val = float(df_cat["Highest Confidence Score"].max())
                        min_conf = st.slider("Min Confidence:", min_value=0.0, max_value=1.0, value=min_conf_val, step=0.05)
                    else:
                        min_conf = 0.0
                with fcol3:
                    search_road = st.text_input("Search Road Name:", placeholder="e.g. video_preview")

                filtered_cat = df_cat.copy()
                if sel_sev != "All" and "Severity" in filtered_cat.columns:
                    filtered_cat = filtered_cat[filtered_cat["Severity"] == sel_sev]
                if "Highest Confidence Score" in filtered_cat.columns:
                    filtered_cat = filtered_cat[filtered_cat["Highest Confidence Score"] >= min_conf]
                if search_road.strip() and "Road Name" in filtered_cat.columns:
                    filtered_cat = filtered_cat[filtered_cat["Road Name"].astype(str).str.contains(search_road.strip(), case=False)]

                st.dataframe(filtered_cat, use_container_width=True)
                
                csv_cat_bytes = filtered_cat.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "⬇️ Download Filtered Pothole Catalog CSV",
                    data=csv_cat_bytes,
                    file_name="potholes_catalog_filtered.csv",
                    mime="text/csv",
                    type="primary"
                )
            except Exception as e:
                st.error(f"Error loading potholes catalog: {e}")
        else:
            st.info("No 'potholes_catalog.csv' found yet. Process a road video survey in AI Detection Studio to generate.")

    # TAB 2: Road Assessment Registry
    with tab_road:
        st.markdown("#### 🛣️ Road Quality Assessment Dataset")
        if os.path.exists("road_assessment.csv"):
            try:
                df_ra = pd.read_csv("road_assessment.csv")
                st.dataframe(df_ra, use_container_width=True)
                
                csv_ra_bytes = df_ra.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "⬇️ Download Road Assessment CSV",
                    data=csv_ra_bytes,
                    file_name="road_assessment.csv",
                    mime="text/csv",
                    type="primary"
                )
            except Exception as e:
                st.error(f"Error loading road assessment: {e}")
        else:
            st.info("No 'road_assessment.csv' found.")

    # TAB 3: Community GIS Network JSON
    with tab_gis:
        st.markdown("#### 🗺️ Community Road Network Database (JSON)")
        if os.path.exists("community_road_network.json"):
            try:
                with open("community_road_network.json", "r") as jf:
                    gis_data = json.load(jf)
                
                st.caption(f"Currently managing **{len(gis_data)} persistent surveyed corridors** on OpenStreetMap:")
                
                # Show summary
                gis_summary = []
                for entry in gis_data:
                    gis_summary.append({
                        "Road Name": entry.get("road_name"),
                        "Health Score": entry.get("health_score"),
                        "Rating": entry.get("rating"),
                        "Urgency": entry.get("urgency"),
                        "Potholes Pinned": len(entry.get("potholes", [])),
                        "Waypoints Count": len(entry.get("coordinates", []))
                    })
                st.dataframe(pd.DataFrame(gis_summary), use_container_width=True)
                
                with st.expander("🔍 View Raw JSON Specification"):
                    st.json(gis_data)

                json_bytes = json.dumps(gis_data, indent=2).encode('utf-8')
                st.download_button(
                    "⬇️ Download community_road_network.json",
                    data=json_bytes,
                    file_name="community_road_network.json",
                    mime="application/json",
                    type="primary"
                )
            except Exception as e:
                st.error(f"Error reading community road network: {e}")
        else:
            st.info("community_road_network.json not found.")

    # TAB 4: Statistical Visualizations
    with tab_stats:
        st.markdown("#### 📊 Pavement Condition & Detection Statistics")
        
        if os.path.exists("potholes_catalog.csv"):
            try:
                df_stat = pd.read_csv("potholes_catalog.csv")
                
                scol1, scol2 = st.columns(2)
                with scol1:
                    st.markdown("##### Defect Severity Breakdown")
                    if "Severity" in df_stat.columns:
                        sev_dist = df_stat["Severity"].value_counts()
                        st.bar_chart(sev_dist)
                
                with scol2:
                    st.markdown("##### Detection Confidence Distribution")
                    if "Highest Confidence Score" in df_stat.columns:
                        conf_hist, bin_edges = np.histogram(df_stat["Highest Confidence Score"], bins=10, range=(0, 1))
                        df_hist = pd.DataFrame({
                            "Confidence Range": [f"{bin_edges[i]:.1f}-{bin_edges[i+1]:.1f}" for i in range(len(conf_hist))],
                            "Count": conf_hist
                        }).set_index("Confidence Range")
                        st.bar_chart(df_hist)

                st.markdown("##### Pothole Area vs Duration Visible")
                if "Estimated Area (px²)" in df_stat.columns and "Duration Visible (s)" in df_stat.columns:
                    area_df = df_stat[["Estimated Area (px²)", "Duration Visible (s)"]].copy()
                    st.scatter_chart(area_df, x="Duration Visible (s)", y="Estimated Area (px²)")

            except Exception as e:
                st.error(f"Error compiling statistics: {e}")
        else:
            st.info("Generate pothole catalog data by analyzing footage in the Detection Studio.")

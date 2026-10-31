# Project Infranox - AI Pothole Detection, Tracking & Road Quality Ranking 🚧

An intelligent computer vision system for road asset and road surface monitoring. It uses **YOLO** for high-accuracy pothole detection, specialized directional tracking to assign persistent IDs to every unique physical pothole, exports structured CSV inspection logs, and ranks road quality using civil engineering pavement condition metrics.

---

## ✨ Key Capabilities

- **Unique Physical Pothole Tracking:** 
  - Prevents double-counting by following each pothole across video frames under a persistent ID.
  - Directional forward-motion gating ensures old potholes that have rolled behind the vehicle are closed and never hijack new potholes down the road.
  - Option to choose between the **Road-Aware Flow Tracker**, **Pothole-Tuned ByteTrack**, and **BoT-SORT**.
- **Structured CSV Export:**
  - Automatically exports all detected pothole IDs with exact timestamps, frames, bounding box dimensions, surface area ($px^2$), confidence score, and severity classification.
- **Road Quality Profiling & Ranking:**
  - Evaluates and ranks road segments based on:
    - **Pavement Health Score (0–100):** Comprehensive condition score.
    - **Pothole Density:** Frequency of potholes per minute of driving.
    - **Severity Distribution:** Breakdown of Severe, Moderate, and Minor potholes.
    - **Cumulative Surface Damage Area ($px^2$).**
    - **Maintenance Urgency:** Actionable recommendations (Emergency Intervention, Priority Repair, Scheduled Repair, Routine Monitoring).
  - **Dynamic Road Ranking Leaderboard:** Compare multiple roads, sort by worst-to-best or best-to-worst, view bar charts, and export the leaderboard CSV.
- **Single & Batch Image Inspection:**
  - Upload road photos (`.jpg`, `.png`, `.jpeg`) to detect, count, and crop every individual pothole in the scene.
- **Interactive OpenStreetMap & Route Navigation:**
  - Color-coded road polylines displaying pavement ratings: 🟢 **Good/Excellent**, 🟡 **Fair**, and 🔴 **Critical/Severe**.
  - Interactive pothole hazard pins with hover tooltips and metadata popups (ID, severity, confidence, damaged area).
  - **Boarding & Destination Route Planner:** Enter origin & destination or select corridor presets. Uses free OpenStreetMap Nominatim geocoding and OSRM driving engine to plot the exact route with turn-by-turn driving trajectory, distance, duration, and pavement safety advisories.
  - Layer switcher: Standard OpenStreetMap, Humanitarian Detail Map, and Esri Satellite Imagery.
- **Interactive Streamlit Web Dashboard:**
  - Frame range trimming slider, adjustable frame skip (1x–10x), detection confidence slider, IoU threshold slider, and inference resolution options (640, 960, 1280).
  - Close-up cropped gallery of each detected pothole.

---

## 📁 Repository Structure

```text
Project-Infranox/
├── app.py                # Streamlit web dashboard with detection, tracking, CSV export & road ranking
├── test.py               # Standalone CLI / webcam script with CSV logging & road profiling
├── tracker.py            # Road-Aware Directional Tracker & Pavement Condition scoring engine
├── best.pt               # Pretrained YOLO pothole detection model weights
├── requirements.txt      # Python dependencies (ultralytics, opencv, streamlit, pandas, lapx)
├── trackers/             # Tuned tracker configurations
│   ├── pothole_bytetrack.yaml
│   └── pothole_botsort.yaml
├── .streamlit/           # Streamlit configuration
├── .gitignore            # Git ignore rules
└── README.md             # Project documentation
```

---

## 🚀 Quick Start

### 1. Installation
```bash
git clone https://github.com/arpitshagra/Project-Infranox.git
cd Project-Infranox
pip install -r requirements.txt
```

### 2. Launch the Web UI
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

### 3. Run Standalone Script
```bash
python test.py
```
*(Automatically processes road video/webcam, prints road health metrics, and generates `potholes_catalog.csv` and `road_assessment.csv`)*

---

## 🛠️ Tech Stack
- **Model:** YOLO (Ultralytics)
- **Tracking:** Road-Aware Directional Flow MOT, ByteTrack, BoT-SORT
- **UI:** Streamlit
- **Analytics & Data:** Pandas, NumPy, OpenCV

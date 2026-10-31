# Project Infranox - AI Pothole Detection & Tracking System 🚧

An intelligent computer vision system for road asset and road surface monitoring. It uses **YOLO** for real-time pothole detection and **ByteTrack / BoT-SORT** multi-object tracking to eliminate duplicate pothole counts across video frames.

---

## ✨ Features

- **Real-Time Pothole Detection:** Powered by a customized YOLO model (`best.pt`).
- **Unique Multi-Object Tracking:** Uses **ByteTrack / BoT-SORT** algorithms to assign persistent IDs to each pothole, ensuring a single physical pothole is counted **only once** as a vehicle drives past.
- **Interactive Streamlit Web Dashboard:**
  - Drag-and-drop video upload (`.mp4`, `.avi`, `.mov`, `.mkv`) or select workspace videos.
  - **Frame Range Adjustment (Trimming):** Select specific sections/timeframes of video to inspect.
  - **Frame Sampling (Frame Skip):** Process every $N$-th frame (e.g. 2x to 10x faster) to efficiently process long road videos with minimal computing power.
  - **Real-Time Live Video Display:** Displays detections, bounding boxes, and active tracking IDs on screen.
  - **Export Capabilities:** Download annotated output video with bounding boxes and track IDs, export a structured CSV catalog, and view a snapshot gallery of detected potholes.
- **Standalone CLI / Webcam Script (`test.py`):** For direct terminal usage or live webcam detection.

---

## 📁 Repository Structure

```text
Project-Infranox/
├── app.py                # Streamlit web frontend with unique tracking & frame controls
├── test.py               # Standalone Python script for video/webcam detection
├── best.pt               # Pretrained YOLO pothole detection model weights
├── requirements.txt      # Python dependencies (ultralytics, opencv, streamlit, lapx)
├── .streamlit/           # Streamlit configuration
├── .gitignore            # Git ignore rules (filters out large video binaries)
└── README.md             # Project documentation
```

---

## 🚀 Quick Start

### 1. Installation
Clone this repository and install the required dependencies:
```bash
git clone https://github.com/arpitshagra/Project-Infranox.git
cd Project-Infranox
pip install -r requirements.txt
```

### 2. Launch the Web UI
Run the interactive Streamlit dashboard:
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

### 3. Run Standalone Script
To run pothole detection directly in the terminal on a video or webcam:
```bash
python test.py
```
*(To use live webcam instead of video, edit `test.py` and set `video_source = 0`)*

---

## 🛠️ Tech Stack
- **Model:** YOLO (Ultralytics)
- **Tracking:** ByteTrack & BoT-SORT
- **UI:** Streamlit
- **Computer Vision:** OpenCV (cv2)
- **Core:** Python, PyTorch


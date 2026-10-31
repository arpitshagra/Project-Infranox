import React, { useState, useEffect } from 'react';
import { 
  Video, 
  Image as ImageIcon, 
  Play, 
  Upload, 
  Settings2, 
  CheckCircle2, 
  Download, 
  Sliders, 
  Layers, 
  MapPin, 
  AlertTriangle,
  FileSpreadsheet,
  Film
} from 'lucide-react';

export default function DetectionStudio({ onSurveyComplete }) {
  const [activeTab, setActiveTab] = useState('video'); // 'video' | 'image'

  // Common Inference Settings
  const [confThresh, setConfThresh] = useState(0.20);
  const [iouThresh, setIouThresh] = useState(0.50);
  const [imgsz, setImgsz] = useState(640);

  // Video Survey State
  const [videoFile, setVideoFile] = useState(null);
  const [localVideos, setLocalVideos] = useState([]);
  const [selectedLocalVideo, setSelectedLocalVideo] = useState('');
  const [roadName, setRoadName] = useState('NH-44 Expressway Sector 1');
  const [startPoint, setStartPoint] = useState('Connaught Place, New Delhi');
  const [endPoint, setEndPoint] = useState('India Gate, New Delhi');
  const [minHits, setMinHits] = useState(3);
  const [frameStep, setFrameStep] = useState(1);
  const [maxFrames, setMaxFrames] = useState(600);
  const [isProcessingVideo, setIsProcessingVideo] = useState(false);
  const [videoResult, setVideoResult] = useState(null);

  // Image Detection State
  const [imageFile, setImageFile] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [isProcessingImage, setIsProcessingImage] = useState(false);
  const [imageResult, setImageResult] = useState(null);

  useEffect(() => {
    // Load local videos from API
    fetch('/api/videos/local')
      .then(res => res.json())
      .then(data => {
        setLocalVideos(data);
        if (data.length > 0) setSelectedLocalVideo(data[0].path);
      })
      .catch(err => console.log('Error loading local videos:', err));
  }, []);

  // Handle Video Processing
  const handleProcessVideo = async () => {
    setIsProcessingVideo(true);
    setVideoResult(null);

    const formData = new FormData();
    if (videoFile) {
      formData.append('file', videoFile);
    } else if (selectedLocalVideo) {
      formData.append('video_path', selectedLocalVideo);
    }
    formData.append('road_name', roadName);
    formData.append('start_point', startPoint);
    formData.append('end_point', endPoint);
    formData.append('start_frame', 0);
    formData.append('max_frames', maxFrames);
    formData.append('frame_step', frameStep);
    formData.append('min_hits', minHits);
    formData.append('conf_thresh', confThresh);
    formData.append('iou_thresh', iouThresh);
    formData.append('imgsz', imgsz);

    try {
      const res = await fetch('/api/detect/video', {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      if (res.ok) {
        setVideoResult(data);
        if (onSurveyComplete) onSurveyComplete();
      } else {
        alert(data.detail || 'Error processing video.');
      }
    } catch (err) {
      console.error(err);
      alert('Network error while processing video.');
    } finally {
      setIsProcessingVideo(false);
    }
  };

  // Handle Image Upload & Detection
  const handleProcessImage = async () => {
    if (!imageFile) return;
    setIsProcessingImage(true);
    setImageResult(null);

    const formData = new FormData();
    formData.append('file', imageFile);
    formData.append('conf_thresh', confThresh);
    formData.append('iou_thresh', iouThresh);
    formData.append('imgsz', imgsz);

    try {
      const res = await fetch('/api/detect/image', {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      if (res.ok) {
        setImageResult(data);
      } else {
        alert(data.detail || 'Error processing image.');
      }
    } catch (err) {
      console.error(err);
      alert('Network error processing image.');
    } finally {
      setIsProcessingImage(false);
    }
  };

  return (
    <div className="space-y-8 py-6">
      {/* Studio Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            AI Detection Studio & Pothole Profiler
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Analyze dashcam video feeds or static road photos using YOLOv8 multi-frame RoadPotholeTracker.
          </p>
        </div>

        {/* Studio Sub-Tabs */}
        <div className="flex bg-slate-100 p-1 rounded-xl">
          <button
            onClick={() => setActiveTab('video')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-bold transition-all ${
              activeTab === 'video'
                ? 'bg-white text-slate-900 shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Video className="w-4 h-4 text-blue-600" />
            Video Survey & Profiling
          </button>
          <button
            onClick={() => setActiveTab('image')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-bold transition-all ${
              activeTab === 'image'
                ? 'bg-white text-slate-900 shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <ImageIcon className="w-4 h-4 text-cyan-600" />
            Image Inspection
          </button>
        </div>
      </div>

      {/* Model Hyperparameters Drawer */}
      <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
            <Sliders className="w-3.5 h-3.5 text-blue-600" />
            Detection & Tracking Hyperparameters
          </span>
          <span className="text-xs text-slate-400 font-medium">Model: best.pt (YOLOv8)</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
          <div>
            <div className="flex justify-between text-xs font-semibold text-slate-700 mb-1">
              <span>Confidence Threshold</span>
              <span className="text-blue-600">{confThresh.toFixed(2)}</span>
            </div>
            <input
              type="range"
              min="0.05"
              max="0.80"
              step="0.05"
              value={confThresh}
              onChange={(e) => setConfThresh(parseFloat(e.target.value))}
              className="w-full accent-blue-600"
            />
          </div>

          <div>
            <div className="flex justify-between text-xs font-semibold text-slate-700 mb-1">
              <span>NMS IoU Threshold</span>
              <span className="text-blue-600">{iouThresh.toFixed(2)}</span>
            </div>
            <input
              type="range"
              min="0.20"
              max="0.80"
              step="0.05"
              value={iouThresh}
              onChange={(e) => setIouThresh(parseFloat(e.target.value))}
              className="w-full accent-blue-600"
            />
          </div>

          <div>
            <div className="flex justify-between text-xs font-semibold text-slate-700 mb-1">
              <span>Inference Resolution</span>
              <span className="text-blue-600">{imgsz} px</span>
            </div>
            <select
              value={imgsz}
              onChange={(e) => setImgsz(parseInt(e.target.value))}
              className="w-full text-xs font-semibold border border-slate-200 rounded-lg p-2 bg-slate-50"
            >
              <option value={640}>640x640 (Fastest)</option>
              <option value={960}>960x960 (Balanced)</option>
              <option value={1280}>1280x1280 (High Detail)</option>
            </select>
          </div>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* TAB 1: VIDEO SURVEY PIPELINE */}
      {/* ========================================================================= */}
      {activeTab === 'video' && (
        <div className="space-y-6">
          {/* Video Configuration Inputs */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-6">
            <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <Film className="w-4 h-4 text-blue-600" />
              1. Video Feed Source & Route Mapping
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Local video or Upload */}
              <div className="space-y-3">
                <label className="text-xs font-bold text-slate-700">Choose Video Source:</label>
                {localVideos.length > 0 && (
                  <div className="space-y-2">
                    <span className="text-xs text-slate-500">Workspace / Downloads Videos:</span>
                    <select
                      value={selectedLocalVideo}
                      onChange={(e) => {
                        setSelectedLocalVideo(e.target.value);
                        setVideoFile(null);
                      }}
                      className="w-full text-xs font-medium border border-slate-200 rounded-lg p-2.5 bg-slate-50"
                    >
                      {localVideos.map((v, i) => (
                        <option key={i} value={v.path}>
                          {v.filename} ({v.folder})
                        </option>
                      ))}
                    </select>
                  </div>
                )}

                <div className="pt-2">
                  <span className="text-xs text-slate-500 block mb-1">Or Upload Custom Video:</span>
                  <input
                    type="file"
                    accept="video/mp4,video/avi,video/mov,video/mkv"
                    onChange={(e) => {
                      if (e.target.files?.[0]) {
                        setVideoFile(e.target.files[0]);
                        setSelectedLocalVideo('');
                      }
                    }}
                    className="w-full text-xs text-slate-500 file:mr-3 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                  />
                </div>
              </div>

              {/* Road metadata */}
              <div className="space-y-3">
                <div>
                  <label className="text-xs font-bold text-slate-700">Road / Corridor Name:</label>
                  <input
                    type="text"
                    value={roadName}
                    onChange={(e) => setRoadName(e.target.value)}
                    placeholder="e.g. NH-44 Expressway Sector 1"
                    className="w-full mt-1 text-xs font-medium border border-slate-200 rounded-lg p-2.5 bg-slate-50"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs font-bold text-slate-700">Start (Origin):</label>
                    <input
                      type="text"
                      value={startPoint}
                      onChange={(e) => setStartPoint(e.target.value)}
                      placeholder="e.g. Connaught Place"
                      className="w-full mt-1 text-xs font-medium border border-slate-200 rounded-lg p-2.5 bg-slate-50"
                    />
                  </div>
                  <div>
                    <label className="text-xs font-bold text-slate-700">End (Destination):</label>
                    <input
                      type="text"
                      value={endPoint}
                      onChange={(e) => setEndPoint(e.target.value)}
                      placeholder="e.g. India Gate"
                      className="w-full mt-1 text-xs font-medium border border-slate-200 rounded-lg p-2.5 bg-slate-50"
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Tracking Tuning (Min Hits & Max Frames) */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 pt-4 border-t border-slate-100">
              <div>
                <label className="text-xs font-bold text-slate-700 block mb-1">
                  Min Track Hits ({minHits}+ frames)
                </label>
                <input
                  type="range"
                  min="1"
                  max="6"
                  value={minHits}
                  onChange={(e) => setMinHits(parseInt(e.target.value))}
                  className="w-full accent-blue-600"
                />
                <span className="text-[11px] text-slate-400">Filters single-frame flickers & hood reflections</span>
              </div>

              <div>
                <label className="text-xs font-bold text-slate-700 block mb-1">
                  Frame Skip Step ({frameStep}x)
                </label>
                <input
                  type="range"
                  min="1"
                  max="5"
                  value={frameStep}
                  onChange={(e) => setFrameStep(parseInt(e.target.value))}
                  className="w-full accent-blue-600"
                />
                <span className="text-[11px] text-slate-400">1 = High fidelity, 2 = 2x faster</span>
              </div>

              <div>
                <label className="text-xs font-bold text-slate-700 block mb-1">
                  Max Frames Limit ({maxFrames} frames)
                </label>
                <input
                  type="number"
                  min="50"
                  max="2000"
                  step="50"
                  value={maxFrames}
                  onChange={(e) => setMaxFrames(parseInt(e.target.value))}
                  className="w-full text-xs border border-slate-200 rounded-lg p-2 bg-slate-50"
                />
                <span className="text-[11px] text-slate-400">Caps analysis duration for speed</span>
              </div>
            </div>

            {/* Run Survey Button */}
            <div className="pt-2">
              <button
                onClick={handleProcessVideo}
                disabled={isProcessingVideo}
                className="w-full py-4 rounded-xl font-bold text-sm bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700 text-white shadow-md shadow-blue-500/20 disabled:opacity-50 transition-all flex items-center justify-center gap-2"
              >
                {isProcessingVideo ? (
                  <>
                    <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    Tracking Physical Potholes & Computing Road Profile...
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4 fill-current" />
                    Execute Road-Aware Pothole Tracking & Civil Profiling
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Video Result View */}
          {videoResult && (
            <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-6">
              <div className="flex items-center justify-between border-b border-slate-100 pb-4">
                <div className="space-y-1">
                  <span className="text-xs font-bold text-emerald-600 uppercase tracking-wider flex items-center gap-1">
                    <CheckCircle2 className="w-4 h-4" />
                    Inspection Complete & Synced to OpenStreetMap
                  </span>
                  <h3 className="text-xl font-extrabold text-slate-900">
                    {videoResult.road_profile?.['Road Name']}
                  </h3>
                </div>

                <div className="flex items-center gap-2">
                  <a
                    href="/api/reports/potholes.csv"
                    className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold transition"
                  >
                    <Download className="w-3.5 h-3.5" />
                    Potholes CSV
                  </a>
                  {videoResult.video_url && (
                    <a
                      href={videoResult.video_url}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold transition shadow-sm"
                    >
                      <Video className="w-3.5 h-3.5" />
                      Download Tracked MP4
                    </a>
                  )}
                </div>
              </div>

              {/* Civil Score Metrics */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
                  <span className="text-xs text-slate-500 font-medium">Pavement Health (PCI)</span>
                  <p className="text-2xl font-black text-slate-900 mt-1">
                    {videoResult.road_profile?.['Health Score (0-100)']}/100
                  </p>
                  <span className="text-[11px] font-bold text-blue-600">
                    {videoResult.road_profile?.['Condition Rating']}
                  </span>
                </div>

                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
                  <span className="text-xs text-slate-500 font-medium">Confirmed Unique Defects</span>
                  <p className="text-2xl font-black text-slate-900 mt-1">
                    {videoResult.unique_potholes_count}
                  </p>
                  <span className="text-[11px] text-slate-500">
                    Density: {videoResult.road_profile?.['Pothole Density (/min)']} /min
                  </span>
                </div>

                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
                  <span className="text-xs text-slate-500 font-medium">Maintenance Urgency</span>
                  <p className="text-sm font-bold text-slate-800 mt-2">
                    {videoResult.road_profile?.['Maintenance Urgency']}
                  </p>
                </div>

                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
                  <span className="text-xs text-slate-500 font-medium">Severity Distribution</span>
                  <p className="text-xs font-semibold text-slate-700 mt-1.5">
                    🔴 {videoResult.road_profile?.['Severe Potholes']} Severe • 🟡 {videoResult.road_profile?.['Moderate Potholes']} Mod • 🟢 {videoResult.road_profile?.['Minor Potholes']} Minor
                  </p>
                </div>
              </div>

              {/* Physical Pothole Crops Gallery */}
              {videoResult.potholes && videoResult.potholes.length > 0 && (
                <div className="space-y-3 pt-4 border-t border-slate-100">
                  <h4 className="text-sm font-bold text-slate-900">
                    📸 Unique Potholes Inspection Gallery ({videoResult.potholes.length} Distinct Craters)
                  </h4>
                  <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 gap-3">
                    {videoResult.potholes.map((p, idx) => (
                      <div key={idx} className="bg-slate-50 p-2 rounded-xl border border-slate-200 space-y-1 text-center">
                        {p.crop_base64 ? (
                          <img
                            src={p.crop_base64}
                            alt={`Pothole #${p.track_id}`}
                            className="w-full h-24 object-cover rounded-lg"
                          />
                        ) : (
                          <div className="w-full h-24 bg-slate-200 rounded-lg flex items-center justify-center text-xs text-slate-400">
                            No crop
                          </div>
                        )}
                        <p className="font-bold text-xs text-slate-900 mt-1">ID #{p.track_id}</p>
                        <p className={`text-[10px] font-semibold ${
                          p.severity === 'Severe' ? 'text-rose-600' : (p.severity === 'Moderate' ? 'text-amber-600' : 'text-emerald-600')
                        }`}>
                          {p.severity} • {p.max_conf}
                        </p>
                        <p className="text-[9px] text-slate-400">Seen @ {p.first_sec}s</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 2: SINGLE / BATCH IMAGE INSPECTION */}
      {/* ========================================================================= */}
      {activeTab === 'image' && (
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-6">
            <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <ImageIcon className="w-4 h-4 text-cyan-600" />
              Upload Static Road Photo
            </h3>

            <div className="space-y-4">
              <input
                type="file"
                accept="image/*"
                onChange={(e) => {
                  if (e.target.files?.[0]) {
                    setImageFile(e.target.files[0]);
                    setImagePreview(URL.createObjectURL(e.target.files[0]));
                    setImageResult(null);
                  }
                }}
                className="w-full text-xs text-slate-500 file:mr-3 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-cyan-50 file:text-cyan-700 hover:file:bg-cyan-100"
              />

              {imagePreview && (
                <div className="relative rounded-xl overflow-hidden border border-slate-200 max-h-[400px] flex justify-center bg-slate-950">
                  <img src={imagePreview} alt="Selected road" className="max-h-[400px] object-contain" />
                </div>
              )}

              <button
                onClick={handleProcessImage}
                disabled={!imageFile || isProcessingImage}
                className="w-full py-3.5 rounded-xl font-bold text-sm bg-cyan-600 hover:bg-cyan-700 text-white shadow-md shadow-cyan-500/20 disabled:opacity-50 transition flex items-center justify-center gap-2"
              >
                {isProcessingImage ? (
                  <>
                    <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    Running YOLOv8 Inspection...
                  </>
                ) : (
                  <>
                    <CheckCircle2 className="w-4 h-4" />
                    Detect Potholes & Measure Dimensions
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Image Detection Result */}
          {imageResult && (
            <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-6">
              <div className="flex items-center justify-between border-b border-slate-100 pb-4">
                <div>
                  <h3 className="text-lg font-bold text-slate-900">
                    Inspection Results: {imageResult.num_potholes} Potholes Detected
                  </h3>
                  <p className="text-xs text-slate-500">
                    🔴 {imageResult.severe_count} Severe • 🟡 {imageResult.moderate_count} Moderate • 🟢 {imageResult.minor_count} Minor
                  </p>
                </div>
                <span className="px-3 py-1 rounded-full text-xs font-bold bg-cyan-50 text-cyan-700 border border-cyan-200">
                  Total Damage Area: {imageResult.total_damage_area.toLocaleString()} px²
                </span>
              </div>

              {/* Annotated Image View */}
              {imageResult.annotated_image && (
                <div className="rounded-xl overflow-hidden border border-slate-200 bg-slate-950 flex justify-center">
                  <img
                    src={imageResult.annotated_image}
                    alt="Annotated road"
                    className="max-h-[500px] object-contain"
                  />
                </div>
              )}

              {/* Pothole Crop Gallery */}
              {imageResult.potholes && imageResult.potholes.length > 0 && (
                <div className="space-y-3">
                  <h4 className="text-sm font-bold text-slate-900">Close-up Defect Crops:</h4>
                  <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 gap-3">
                    {imageResult.potholes.map((p, idx) => (
                      <div key={idx} className="bg-slate-50 p-2 rounded-xl border border-slate-200 text-center space-y-1">
                        <img src={p.crop_base64} alt={`Pothole #${p.id}`} className="w-full h-24 object-cover rounded-lg" />
                        <p className="font-bold text-xs text-slate-900 mt-1">Pothole #{p.id}</p>
                        <p className={`text-[10px] font-semibold ${
                          p.severity === 'Severe' ? 'text-rose-600' : (p.severity === 'Moderate' ? 'text-amber-600' : 'text-emerald-600')
                        }`}>
                          {p.severity} • {p.confidence}
                        </p>
                        <p className="text-[9px] text-slate-400">{p.width}x{p.height} px ({p.area} px²)</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}


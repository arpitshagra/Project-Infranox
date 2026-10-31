import React, { useState, useEffect } from 'react';
import { 
  AlertCircle, 
  Send, 
  CheckCircle2, 
  Clock, 
  ShieldCheck, 
  Camera, 
  MapPin, 
  User, 
  Phone 
} from 'lucide-react';

export default function ComplaintPortal() {
  const [complaints, setComplaints] = useState([]);
  const [name, setName] = useState('');
  const [contact, setContact] = useState('');
  const [location, setLocation] = useState('');
  const [description, setDescription] = useState('');
  const [severity, setSeverity] = useState('Critical');
  const [photoBase64, setPhotoBase64] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [successTicket, setSuccessTicket] = useState(null);

  const fetchComplaints = () => {
    fetch('/api/complaints')
      .then(res => res.json())
      .then(data => setComplaints(data))
      .catch(err => console.log('Error loading complaints:', err));
  };

  useEffect(() => {
    fetchComplaints();
  }, []);

  const handlePhotoUpload = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setPhotoBase64(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    setSuccessTicket(null);

    try {
      const res = await fetch('/api/complaints', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name,
          contact,
          location,
          description,
          severity,
          photo_base64: photoBase64 || null
        })
      });
      const data = await res.json();
      if (res.ok) {
        setSuccessTicket(data.complaint);
        setName('');
        setContact('');
        setLocation('');
        setDescription('');
        setPhotoBase64('');
        fetchComplaints();
      }
    } catch (err) {
      alert('Error submitting grievance ticket.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleUpdateStatus = async (complaintId, newStatus) => {
    try {
      const res = await fetch(`/api/complaints/${complaintId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus })
      });
      if (res.ok) {
        fetchComplaints();
      }
    } catch (err) {
      alert('Error updating status.');
    }
  };

  return (
    <div className="space-y-8 py-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            Citizen Pothole Grievance & Complaint Portal
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Empower citizens to report dangerous road craters directly to municipal authorities with photo verification.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Submission Form */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-5">
          <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-rose-600" />
            File New Road Defect Complaint
          </h3>

          {successTicket && (
            <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl space-y-1 text-xs text-emerald-800">
              <p className="font-bold flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                Ticket Generated: {successTicket.id}
              </p>
              <p>Your complaint has been submitted to the municipal road engineers for site inspection.</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-xs font-bold text-slate-700">Citizen Name</label>
              <div className="relative mt-1">
                <User className="w-3.5 h-3.5 absolute left-3 top-3 text-slate-400" />
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Ramesh Kumar"
                  className="w-full text-xs pl-8 pr-3 py-2.5 border border-slate-200 rounded-lg bg-slate-50 font-medium"
                />
              </div>
            </div>

            <div>
              <label className="text-xs font-bold text-slate-700">Phone or Email</label>
              <div className="relative mt-1">
                <Phone className="w-3.5 h-3.5 absolute left-3 top-3 text-slate-400" />
                <input
                  type="text"
                  required
                  value={contact}
                  onChange={(e) => setContact(e.target.value)}
                  placeholder="e.g. +91 98765 43210"
                  className="w-full text-xs pl-8 pr-3 py-2.5 border border-slate-200 rounded-lg bg-slate-50 font-medium"
                />
              </div>
            </div>

            <div>
              <label className="text-xs font-bold text-slate-700">Defect Location / Landmark</label>
              <div className="relative mt-1">
                <MapPin className="w-3.5 h-3.5 absolute left-3 top-3 text-slate-400" />
                <input
                  type="text"
                  required
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  placeholder="e.g. Barakhamba Road near Gate 2 Metro"
                  className="w-full text-xs pl-8 pr-3 py-2.5 border border-slate-200 rounded-lg bg-slate-50 font-medium"
                />
              </div>
            </div>

            <div>
              <label className="text-xs font-bold text-slate-700">Perceived Hazard Severity</label>
              <select
                value={severity}
                onChange={(e) => setSeverity(e.target.value)}
                className="w-full text-xs font-semibold border border-slate-200 rounded-lg p-2.5 mt-1 bg-slate-50"
              >
                <option value="Critical">🔴 Critical (Deep crater, risk of accident)</option>
                <option value="Moderate">🟡 Moderate (Surface breaking, bumps)</option>
                <option value="Minor">🟢 Minor (Small superficial chip)</option>
              </select>
            </div>

            <div>
              <label className="text-xs font-bold text-slate-700">Description</label>
              <textarea
                required
                rows={3}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Describe width, depth, lane affected..."
                className="w-full text-xs border border-slate-200 rounded-lg p-2.5 mt-1 bg-slate-50 font-medium"
              />
            </div>

            <div>
              <label className="text-xs font-bold text-slate-700 block mb-1">Upload Photo Proof (Optional)</label>
              <input
                type="file"
                accept="image/*"
                onChange={handlePhotoUpload}
                className="w-full text-xs text-slate-500 file:mr-3 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-blue-50 file:text-blue-700"
              />
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full py-3 rounded-xl font-bold text-xs bg-rose-600 hover:bg-rose-700 text-white shadow-md shadow-rose-500/20 disabled:opacity-50 transition flex items-center justify-center gap-2"
            >
              {isSubmitting ? 'Filing Complaint...' : (
                <>
                  <Send className="w-3.5 h-3.5" />
                  Submit Grievance to Municipal Agency
                </>
              )}
            </button>
          </form>
        </div>

        {/* Complaints Live Feed & Authority Management */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold text-slate-900">
              Active Municipal Complaints ({complaints.length} Logged)
            </h3>
            <span className="text-xs text-slate-500">Live Authority Workflow</span>
          </div>

          <div className="space-y-3">
            {complaints.map((c) => (
              <div key={c.id} className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-3">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-extrabold text-xs text-blue-700 bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
                        {c.id}
                      </span>
                      <span className={`text-[11px] font-bold px-2 py-0.5 rounded-full ${
                        c.severity === 'Critical' ? 'bg-rose-50 text-rose-700 border border-rose-200' : 'bg-amber-50 text-amber-700 border border-amber-200'
                      }`}>
                        {c.severity} Hazard
                      </span>
                      <span className="text-xs text-slate-400">• {c.created_at}</span>
                    </div>
                    <h4 className="font-bold text-slate-900 text-sm mt-1">{c.location}</h4>
                  </div>

                  <span className={`px-2.5 py-1 rounded-full text-xs font-bold ${
                    c.status === 'Resolved' 
                      ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' 
                      : (c.status === 'Under Review' ? 'bg-blue-50 text-blue-700 border border-blue-200' : 'bg-amber-50 text-amber-700 border border-amber-200')
                  }`}>
                    {c.status}
                  </span>
                </div>

                <p className="text-xs text-slate-600 leading-relaxed">{c.description}</p>
                <p className="text-[11px] text-slate-400">Reported by <b>{c.name}</b> ({c.contact})</p>

                {/* Status action buttons for municipal engineer */}
                <div className="flex items-center gap-2 pt-2 border-t border-slate-100">
                  <span className="text-[11px] text-slate-400 font-medium">Update Status:</span>
                  <button
                    onClick={() => handleUpdateStatus(c.id, 'Under Review')}
                    className="px-2.5 py-1 rounded-md text-[11px] font-bold bg-blue-50 hover:bg-blue-100 text-blue-700 transition"
                  >
                    Mark Under Review
                  </button>
                  <button
                    onClick={() => handleUpdateStatus(c.id, 'Resolved')}
                    className="px-2.5 py-1 rounded-md text-[11px] font-bold bg-emerald-50 hover:bg-emerald-100 text-emerald-700 transition"
                  >
                    Mark Resolved
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}


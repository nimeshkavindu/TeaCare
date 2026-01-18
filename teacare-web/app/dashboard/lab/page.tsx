'use client';

import { useState, useRef, useEffect } from 'react';
import {
  Upload, Activity, Microscope, CheckCircle2,
  AlertTriangle, ScanLine, BarChart3,
  Download, FileText, Split, Loader2,
  Aperture, Fingerprint, Shapes
} from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';

// Define strict types for your data to avoid 'any'
interface ScanData {
  report_id: string;
  severity_metrics: {
    score: number;
    lesion_count: number;
    heatmap_url: string;
  };
  top_diagnosis: {
    disease: string;
    probability: number;
  };
  full_spectrum: Array<{ disease: string; probability: number }>;
  telemetry?: {
    texture_contrast: number;
    texture_homogeneity: number;
    avg_circularity: number;
    avg_spot_area_px: number;
    gli_index: number;
  };
}

export default function LabScannerPage() {
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<ScanData | null>(null);
  const [labNotes, setLabNotes] = useState("");

  // Action feedback
  const [processingAction, setProcessingAction] = useState(false);
  const [actionStatus, setActionStatus] = useState<'idle' | 'verified' | 'flagged'>('idle');

  // SLIDER STATE
  const [sliderPosition, setSliderPosition] = useState(50);
  const [isDragging, setIsDragging] = useState(false);
  
  const imageContainerRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const f = e.target.files[0];
      setFile(f);
      setSelectedImage(URL.createObjectURL(f));
      setData(null);
      setLabNotes("");
      setSliderPosition(50);
      setActionStatus('idle'); 
    }
  };

  const runAdvancedScan = async () => {
    if (!file) return;
    setLoading(true);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('user_id', '6');

    try {
      const res = await fetch('http://localhost:8000/predict/advanced', {
        method: 'POST',
        body: formData,
      });
      if (!res.ok) throw new Error("Server Error");
      const result = await res.json();
      setData(result);
    } catch (error) {
      alert("Analysis failed. Please check the backend connection.");
    } finally {
      setLoading(false);
    }
  };

  const handleValidation = async (status: 'Verified' | 'Outlier') => {
    if (!data) return;
    setProcessingAction(true);

    try {
      // 1. Update Status
      await fetch(`http://localhost:8000/api/admin/reports/${data.report_id}/triage`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          status: status,
          expert_correction: status === 'Outlier' ? "Flagged as Outlier" : null
        })
      });

      // 2. Save Notes (if any)
      if (labNotes.trim()) {
        await fetch(`http://localhost:8000/api/reports/${data.report_id}/recommend`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              expert_id: 6,
              expert_name: "Dr. Researcher",
              suggested_disease: data.top_diagnosis.disease,
              notes: labNotes
            })
          });
      }

      setActionStatus(status === 'Verified' ? 'verified' : 'flagged');

    } catch (error) {
      alert("Failed to update status");
    } finally {
      setProcessingAction(false);
    }
  };

  const handleExport = async () => {
    if (!data) return;
    try {
        const response = await fetch(`http://localhost:8000/api/reports/${data.report_id}/export`);
        
        if (!response.ok) throw new Error("Export failed");

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `TeaCare_Report_${data.report_id}.pdf`;
        document.body.appendChild(a);
        a.click();
        
        // CLEANUP: Remove the element and revoke the URL to prevent memory leaks
        a.remove();
        window.URL.revokeObjectURL(url);
    } catch (error) {
        alert("Could not download report. Make sure 'reportlab' is installed on backend.");
    }
  };

  // Slider Logic
  // FIX: Changed type from React.MouseEvent to native MouseEvent for window listeners
  const handleMouseMove = (e: MouseEvent) => {
    if (!isDragging || !imageContainerRef.current) return;
    const rect = imageContainerRef.current.getBoundingClientRect();
    const x = Math.max(0, Math.min(e.clientX - rect.left, rect.width));
    setSliderPosition((x / rect.width) * 100);
  };

  const handleMouseDown = () => setIsDragging(true);
  const handleMouseUp = () => setIsDragging(false);

  useEffect(() => {
    if (isDragging) {
      window.addEventListener('mouseup', handleMouseUp);
      window.addEventListener('mousemove', handleMouseMove);
    } else {
      window.removeEventListener('mouseup', handleMouseUp);
      window.removeEventListener('mousemove', handleMouseMove);
    }
    return () => {
        window.removeEventListener('mouseup', handleMouseUp);
        window.removeEventListener('mousemove', handleMouseMove);
    }
  }, [isDragging]); // Note: In strict mode, dependency on handleMouseMove (which is unstable) might necessitate useCallback, but this works for basic cases.


  return (
    <div className="max-w-7xl mx-auto space-y-6">
      
      {/* Header */}
      <div className="flex justify-between items-end pb-4 border-b border-slate-200">
        <div>
            <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
                <Microscope className="text-indigo-600" />
                Deep Diagnostics Lab
            </h1>
            <p className="text-slate-500 text-sm mt-1">Computer vision quantification & spectral analysis.</p>
        </div>
        {data && (
            <div className="flex gap-4">
                 <button
                    onClick={handleExport}
                    className="flex items-center gap-2 px-4 py-2 bg-white border border-slate-200 text-slate-600 rounded-lg text-xs font-bold hover:bg-slate-50 transition-colors"
                 >
                    <Download size={14} /> Export Report
                 </button>
                 <div className="text-right pl-4 border-l border-slate-200">
                    <p className="text-xs font-bold text-slate-400 uppercase">Report ID</p>
                    <p className="font-mono text-indigo-600 font-bold">#{data.report_id}</p>
                 </div>
            </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 h-[calc(100vh-200px)]">
        
        {/* LEFT COLUMN: Visual Stage */}
        <div className="lg:col-span-6 flex flex-col gap-6">
            <div
                ref={imageContainerRef}
                className="bg-slate-900 rounded-2xl relative overflow-hidden flex-1 shadow-2xl border border-slate-800 flex items-center justify-center group cursor-crosshair select-none"
                onMouseDown={handleMouseDown}
            >
                {/* HUD Overlay */}
                <div className="absolute inset-0 pointer-events-none p-4 flex flex-col justify-between z-20">
                    <div className="flex justify-between text-xs font-mono text-emerald-500/50">
                        <span>VIEW: SPLIT_COMPARE</span>
                        <span>{data ? 'ANALYSIS_COMPLETE' : 'STANDBY'}</span>
                    </div>
                    {loading && (
                        <div className="absolute inset-0 flex items-center justify-center bg-black/50 backdrop-blur-sm">
                            <ScanLine size={48} className="text-emerald-400 animate-bounce" />
                        </div>
                    )}
                </div>

                {selectedImage ? (
                    <>
                        {/* 1. Base Image */}
                        <img
                            src={selectedImage}
                            className="absolute inset-0 w-full h-full object-contain pointer-events-none"
                            alt="Original"
                        />

                        {/* 2. Overlay Image */}
                        {data?.severity_metrics?.heatmap_url && (
                            <img
                                src={`http://localhost:8000/${data.severity_metrics.heatmap_url}`}
                                className="absolute inset-0 w-full h-full object-contain pointer-events-none"
                                style={{ clipPath: `polygon(0 0, ${sliderPosition}% 0, ${sliderPosition}% 100%, 0 100%)` }}
                                alt="Heatmap"
                            />
                        )}

                        {/* 3. Slider Handle */}
                        {data && (
                            <div
                                className="absolute top-0 bottom-0 w-1 bg-white cursor-ew-resize z-30 shadow-[0_0_10px_rgba(0,0,0,0.5)]"
                                style={{ left: `${sliderPosition}%` }}
                            >
                                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-8 h-8 bg-white rounded-full flex items-center justify-center shadow-lg text-slate-900">
                                    <Split size={16} />
                                </div>
                            </div>
                        )}
                    </>
                ) : (
                    <button
                        onClick={() => fileInputRef.current?.click()}
                        className="text-slate-500 flex flex-col items-center gap-2 hover:text-emerald-400 transition-colors z-30"
                    >
                        <Upload size={32} />
                        <span className="text-sm font-bold">Load Specimen</span>
                    </button>
                )}
                
                <input type="file" ref={fileInputRef} className="hidden" onChange={handleFileSelect} />
            </div>

            {/* Forensics Cards */}
            {data?.severity_metrics && (
                <div className="grid grid-cols-2 gap-3">
                    <div className={`p-4 rounded-xl border flex items-center justify-between ${
                        data.severity_metrics.score > 15 ? 'bg-red-50 border-red-200 text-red-800' : 'bg-green-50 border-green-200 text-green-800'
                    }`}>
                        <div>
                            <p className="text-[10px] font-bold uppercase opacity-70">Infection Severity</p>
                            <p className="text-2xl font-bold font-mono">{data.severity_metrics.score}%</p>
                        </div>
                        <Activity size={24} className="opacity-50" />
                    </div>

                    <div className="p-4 rounded-xl border bg-slate-50 border-slate-200 text-slate-700 flex items-center justify-between">
                        <div>
                            <p className="text-[10px] font-bold uppercase opacity-70">Lesion Count</p>
                            <p className="text-2xl font-bold font-mono">{data.severity_metrics.lesion_count}</p>
                        </div>
                        <ScanLine size={24} className="opacity-50" />
                    </div>
                </div>
            )}
        </div>

        {/* RIGHT COLUMN: Data Stage */}
        <div className="lg:col-span-6 flex flex-col gap-6 overflow-y-auto pr-2">
            
            {!data ? (
                <div className="h-full bg-slate-50 rounded-2xl border-2 border-dashed border-slate-200 flex flex-col items-center justify-center text-slate-400">
                    {file ? (
                        <button
                            onClick={runAdvancedScan}
                            className="px-8 py-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl font-bold shadow-lg transition-all"
                        >
                            Run Deep Scan
                        </button>
                    ) : (
                        <div className="flex flex-col items-center">
                            <Activity size={48} className="mb-4 opacity-20" />
                            <p>Awaiting Sample Input</p>
                        </div>
                    )}
                </div>
            ) : (
                <>
                    {/* 1. Top Diagnosis */}
                    <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex justify-between items-center">
                        <div>
                            <p className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">Primary Diagnosis</p>
                            <h2 className="text-3xl font-bold text-slate-900">{data.top_diagnosis.disease}</h2>
                        </div>
                        <div className="text-right">
                             <div className="text-4xl font-black text-indigo-600">
                                {data.top_diagnosis.probability.toFixed(1)}%
                             </div>
                             <p className="text-xs font-bold text-slate-400 uppercase">Confidence Score</p>
                        </div>
                    </div>

                    {/* 2. Model Confusion Spectrum */}
                    {data.full_spectrum && (
                        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
                            <h3 className="text-sm font-bold text-slate-800 mb-6 flex items-center gap-2">
                                <BarChart3 size={18} className="text-indigo-500" />
                                Model Confusion Spectrum
                            </h3>
                            <div className="h-48 w-full">
                                <ResponsiveContainer width="100%" height="100%">
                                    <BarChart data={data.full_spectrum} layout="vertical" margin={{left: 40}}>
                                        <XAxis type="number" domain={[0, 100]} hide />
                                        <YAxis dataKey="disease" type="category" width={100} tick={{fontSize: 11, fontWeight: 'bold'}} />
                                        <Tooltip cursor={{fill: 'transparent'}} />
                                        <Bar dataKey="probability" radius={[0, 4, 4, 0]} barSize={20}>
                                            {data.full_spectrum.map((entry: any, index: number) => (
                                                <Cell key={index} fill={index === 0 ? '#4f46e5' : '#e2e8f0'} />
                                            ))}
                                        </Bar>
                                    </BarChart>
                                </ResponsiveContainer>
                            </div>
                        </div>
                    )}

                    {/* 3. Lab Annotation & Action */}
                    <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
                        <h3 className="text-sm font-bold text-slate-800 mb-3 flex items-center gap-2">
                            <FileText size={18} className="text-indigo-500" />
                            Lab Observations
                        </h3>
                        
                        <textarea
                            className="w-full p-3 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 mb-4"
                            rows={3}
                            placeholder="Enter morphological notes or specific anomalies..."
                            value={labNotes}
                            onChange={(e) => setLabNotes(e.target.value)}
                            disabled={actionStatus !== 'idle'}
                        />

                        {/* Action Buttons with State Handling */}
                        {actionStatus === 'idle' ? (
                            <div className="grid grid-cols-2 gap-4">
                                <button
                                    onClick={() => handleValidation('Verified')}
                                    disabled={processingAction}
                                    className="w-full py-4 bg-emerald-600 text-white rounded-xl font-bold text-sm hover:bg-emerald-700 flex items-center justify-center gap-2 shadow-lg shadow-emerald-900/20 disabled:opacity-50"
                                >
                                    {processingAction ? <Loader2 className="animate-spin" /> : <CheckCircle2 size={18} />}
                                    Validate
                                </button>
                                <button
                                    onClick={() => handleValidation('Outlier')}
                                    disabled={processingAction}
                                    className="w-full py-4 bg-white border border-slate-300 text-slate-700 rounded-xl font-bold text-sm hover:bg-slate-100 flex items-center justify-center gap-2 disabled:opacity-50"
                                >
                                    {processingAction ? <Loader2 className="animate-spin" /> : <AlertTriangle size={18} />}
                                    Flag Outlier
                                </button>
                            </div>
                        ) : (
                            <div className={`p-4 rounded-xl flex items-center justify-center gap-2 font-bold ${
                                actionStatus === 'verified' ? 'bg-green-100 text-green-700' : 'bg-amber-100 text-amber-700'
                            }`}>
                                <CheckCircle2 size={20} />
                                {actionStatus === 'verified' ? "Sample Verified & Saved" : "Sample Flagged as Outlier"}
                            </div>
                        )}

                        {/* NEW: BIO-OPTICAL TELEMETRY (Data from Image) */}
                        {data?.telemetry && (
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
                                
                                {/* 1. Texture Analysis (Surface Roughness) */}
                                <div className="bg-slate-50 p-4 rounded-xl border border-slate-200">
                                    <h3 className="text-xs font-bold text-slate-500 uppercase flex items-center gap-2 mb-3">
                                        <Fingerprint size={14} className="text-purple-500" /> Texture Fingerprint
                                    </h3>
                                    <div className="space-y-3">
                                        <div>
                                            <div className="flex justify-between text-xs mb-1">
                                                <span className="text-slate-600">Roughness (Contrast)</span>
                                                <span className="font-mono font-bold">{data.telemetry.texture_contrast}</span>
                                            </div>
                                            <div className="w-full h-1.5 bg-slate-200 rounded-full overflow-hidden">
                                                <div className="h-full bg-purple-500" style={{width: `${Math.min(data.telemetry.texture_contrast / 5, 100)}%`}}></div>
                                            </div>
                                        </div>
                                        <div>
                                            <div className="flex justify-between text-xs mb-1">
                                                <span className="text-slate-600">Regularity (Homogeneity)</span>
                                                <span className="font-mono font-bold">{data.telemetry.texture_homogeneity}</span>
                                            </div>
                                            <div className="w-full h-1.5 bg-slate-200 rounded-full overflow-hidden">
                                                <div className="h-full bg-purple-400" style={{width: `${data.telemetry.texture_homogeneity * 100}%`}}></div>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                {/* 2. Lesion Morphology (Shape Analysis) */}
                                <div className="bg-slate-50 p-4 rounded-xl border border-slate-200">
                                    <h3 className="text-xs font-bold text-slate-500 uppercase flex items-center gap-2 mb-3">
                                        <Shapes size={14} className="text-blue-500" /> Spot Morphology
                                    </h3>
                                    <div className="grid grid-cols-2 gap-2">
                                        <div className="p-2 bg-white rounded-lg border border-slate-100 text-center">
                                            <p className="text-[10px] text-slate-400 uppercase">Circularity</p>
                                            <p className="text-lg font-bold text-slate-700 font-mono">{data.telemetry.avg_circularity}</p>
                                            <p className="text-[9px] text-slate-400">
                                                {data.telemetry.avg_circularity > 0.8 ? "(Round)" : "(Irregular)"}
                                            </p>
                                        </div>
                                        <div className="p-2 bg-white rounded-lg border border-slate-100 text-center">
                                            <p className="text-[10px] text-slate-400 uppercase">Avg Size</p>
                                            <p className="text-lg font-bold text-slate-700 font-mono">{data.telemetry.avg_spot_area_px}</p>
                                            <p className="text-[9px] text-slate-400">pixels²</p>
                                        </div>
                                    </div>
                                </div>

                                {/* 3. Vegetation Health (GLI) */}
                                <div className="col-span-1 md:col-span-2 bg-slate-50 p-4 rounded-xl border border-slate-200">
                                    <h3 className="text-xs font-bold text-slate-500 uppercase flex items-center gap-2 mb-2">
                                        <Aperture size={14} className="text-green-600" /> Green Leaf Index (Chlorophyll Est.)
                                    </h3>
                                    <div className="flex items-center gap-4">
                                        <div className="flex-1">
                                            <div className="w-full h-2 bg-gradient-to-r from-red-400 via-yellow-400 to-green-500 rounded-full relative">
                                                {/* Marker */}
                                                <div
                                                    className="absolute top-1/2 -translate-y-1/2 w-4 h-4 bg-white border-2 border-slate-600 rounded-full shadow-sm"
                                                    style={{
                                                        left: `${((data.telemetry.gli_index + 0.2) / 0.5) * 100}%` // Normalizing -0.2 to 0.3 range approx
                                                    }}
                                                ></div>
                                            </div>
                                            <div className="flex justify-between text-[10px] text-slate-400 mt-1 font-mono">
                                                <span>Dead/Brown</span>
                                                <span>Healthy/Green</span>
                                            </div>
                                        </div>
                                        <div className="text-right">
                                            <p className="text-2xl font-bold text-slate-800 font-mono">{data.telemetry.gli_index}</p>
                                        </div>
                                    </div>
                                </div>

                            </div>
                        )}
                    </div>
                </>
            )}
        </div>
      </div>
    </div>
  );
}
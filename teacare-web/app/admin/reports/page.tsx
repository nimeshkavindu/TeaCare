'use client';
import { useState, useEffect } from 'react';
import { FileText, CheckCircle, AlertOctagon, Edit3, XCircle, X, Save, Microscope, User } from 'lucide-react';

// 1. Define Recommendation Interface
interface Recommendation {
  recommendation_id: number;
  expert_name: string;
  suggested_disease: string;
  notes: string;
  timestamp: string;
}

// 2. Update Report Interface to include Recommendations
interface Report {
  report_id: number;
  disease_name: string;
  confidence: string;
  image_url: string;
  timestamp: string;
  is_correct: string;      
  user_correction: string; 
  verification_status: string; 
  expert_correction: string;
  recommendations: Recommendation[]; // <--- New Array from Backend
}

interface DiseaseOption {
  id: number;
  name: string;
}

export default function ReportsTriagePage() {
  const [reports, setReports] = useState<Report[]>([]);
  const [diseases, setDiseases] = useState<DiseaseOption[]>([]);
  const [filter, setFilter] = useState("all");
  const [isLoading, setIsLoading] = useState(true);
  const [isManualEntry, setIsManualEntry] = useState(false);

  // Modal State
  const [selectedReport, setSelectedReport] = useState<Report | null>(null);
  const [correctionValue, setCorrectionValue] = useState("");
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Fetch Data
  const fetchData = async () => {
    setIsLoading(true);
    try {
      const resReports = await fetch(`http://localhost:8000/api/admin/reports_triage?filter_by=${filter}`);
      if (resReports.ok) setReports(await resReports.json());

      const resDiseases = await fetch('http://localhost:8000/api/diseases');
      if (resDiseases.ok) setDiseases(await resDiseases.json());
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [filter]);

  // Actions
  const handleVerify = async (id: number) => {
    await updateStatus(id, "Verified", null);
  };

  const openCorrectionModal = (report: Report) => {
    setSelectedReport(report);
    
    // Check if the current correction is in our list of known diseases
    const existing = report.expert_correction || report.user_correction || "";
    const isKnown = diseases.some(d => d.name === existing);
    
    if (existing && !isKnown) {
        // If it has a value but it's NOT in the list, switch to manual mode
        setIsManualEntry(true);
        setCorrectionValue(existing);
    } else {
        setIsManualEntry(false);
        setCorrectionValue(existing);
    }
    
    setIsModalOpen(true);
};

  const submitCorrection = async () => {
    if (!selectedReport) return;
    await updateStatus(selectedReport.report_id, "Corrected", correctionValue);
    setIsModalOpen(false);
  };

  const updateStatus = async (id: number, status: string, correction: string | null) => {
    await fetch(`http://localhost:8000/api/admin/reports/${id}/triage`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status, expert_correction: correction }),
    });
    fetchData(); 
  };

  return (
    <div className="p-8 max-w-7xl mx-auto relative">
      <header className="mb-8 flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 flex items-center gap-3">
            <div className="p-2 bg-blue-100 text-blue-600 rounded-lg"><FileText size={32} /></div>
            Disease Reports Triage
          </h1>
          <p className="text-slate-500 mt-2 ml-14">Verify AI predictions and resolve user conflicts.</p>
        </div>

        <div className="flex gap-2 bg-white p-1 rounded-lg border border-slate-200 shadow-sm">
          {['all', 'pending', 'conflict'].map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-4 py-2 rounded-md text-sm font-bold capitalize transition-all ${
                filter === f ? 'bg-slate-900 text-white' : 'text-slate-500 hover:bg-slate-50'
              }`}
            >
              {f}
            </button>
          ))}
        </div>
      </header>

      {/* --- TABLE --- */}
      <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-slate-50 border-b border-slate-200 text-xs font-bold text-slate-500 uppercase tracking-wider">
              <th className="p-4">ID</th>
              <th className="p-4">Image</th>
              <th className="p-4">AI Prediction</th>
              <th className="p-4">Feedback & Insights</th>
              <th className="p-4">Status</th>
              <th className="p-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {reports.map((r) => {
              const isConflict = r.is_correct === "No";
              const status = r.verification_status || "Pending";
              const hasRecs = r.recommendations && r.recommendations.length > 0;

              return (
                <tr key={r.report_id} className={`hover:bg-slate-50 transition-colors ${isConflict ? 'bg-red-50/50' : ''}`}>
                  <td className="p-4 font-mono text-xs text-slate-400">#{r.report_id}</td>
                  <td className="p-4">
                    <img src={`http://localhost:8000/${r.image_url}`} alt="Leaf" className="w-16 h-16 object-cover rounded-lg border border-slate-200 shadow-sm"/>
                  </td>
                  <td className="p-4">
                    <div className="font-bold text-slate-800">{r.disease_name}</div>
                    <div className="text-xs text-slate-500 bg-slate-100 inline-block px-2 py-0.5 rounded mt-1">{r.confidence} Conf.</div>
                  </td>

                  {/* Feedback & Expert Insights Column */}
                  <td className="p-4">
                    <div className="space-y-2">
                        {/* User Feedback */}
                        {r.is_correct === "No" && (
                            <div className="text-red-600 text-xs flex items-center gap-1">
                                <XCircle size={12} /> User disagreed
                            </div>
                        )}
                        
                        {/* Expert Badge */}
                        {hasRecs && (
                            <div className="inline-flex items-center gap-1 px-2 py-1 bg-indigo-50 text-indigo-700 text-xs font-bold rounded-md border border-indigo-100">
                                <Microscope size={12} /> {r.recommendations.length} Expert Opinions
                            </div>
                        )}
                        {!hasRecs && r.is_correct === "Unknown" && <span className="text-slate-300 text-xs">-</span>}
                    </div>
                  </td>

                  {/* Status */}
                  <td className="p-4">
                    {(() => {
                      switch (status) {
                        case "Pending": return <span className="px-2 py-1 bg-yellow-100 text-yellow-700 text-xs font-bold rounded-full">Pending</span>;
                        case "Verified": return <span className="px-2 py-1 bg-green-100 text-green-700 text-xs font-bold rounded-full">Verified</span>;
                        case "Auto-Verified": return <span className="px-2 py-1 bg-blue-50 text-blue-700 text-xs font-bold rounded-full">Auto-Verified</span>;
                        case "Corrected": return <span className="px-2 py-1 bg-purple-100 text-purple-700 text-xs font-bold rounded-full">Corrected</span>;
                        default: return <span className="px-2 py-1 bg-slate-100 text-slate-600 text-xs font-bold rounded-full">{status}</span>;
                      }
                    })()}
                  </td>

                  <td className="p-4 text-right space-x-2">
                    <button onClick={() => openCorrectionModal(r)} className="text-sm font-medium text-slate-500 hover:text-indigo-600 underline">
                        Review
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* --- REVIEW & CORRECTION MODAL --- */}
      {isModalOpen && selectedReport && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl shadow-xl w-full max-w-2xl p-0 overflow-hidden flex flex-col max-h-[90vh]">
                
                {/* Header */}
                <div className="p-6 border-b border-slate-100 flex justify-between items-center bg-slate-50">
                    <div>
                        <h3 className="text-lg font-bold text-slate-800">Review Report #{selectedReport.report_id}</h3>
                        <p className="text-sm text-slate-500">AI Prediction: <span className="font-bold">{selectedReport.disease_name}</span></p>
                    </div>
                    <button onClick={() => setIsModalOpen(false)}><X size={20} className="text-slate-400 hover:text-slate-600" /></button>
                </div>

                <div className="p-6 overflow-y-auto">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                        {/* Image */}
                        <img 
                            src={`http://localhost:8000/${selectedReport.image_url}`} 
                            className="w-full h-48 object-cover rounded-xl border border-slate-200" 
                        />
                        
                        {/* Expert Recommendations List */}
                        <div className="space-y-3">
                            <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Expert Opinions</h4>
                            
                            {selectedReport.recommendations && selectedReport.recommendations.length > 0 ? (
                                selectedReport.recommendations.map(rec => (
                                    <div key={rec.recommendation_id} className="p-3 bg-indigo-50 border border-indigo-100 rounded-lg text-sm">
                                        <div className="flex justify-between items-start mb-1">
                                            <span className="font-bold text-indigo-900 flex items-center gap-1">
                                                <User size={12}/> {rec.expert_name}
                                            </span>
                                            <button 
                                                onClick={() => setCorrectionValue(rec.suggested_disease)}
                                                className="text-xs bg-white text-indigo-600 px-2 py-1 rounded border border-indigo-200 hover:bg-indigo-600 hover:text-white transition-colors"
                                            >
                                                Apply
                                            </button>
                                        </div>
                                        <p className="text-indigo-800 font-medium">Suggestion: {rec.suggested_disease}</p>
                                        <p className="text-indigo-600 text-xs italic mt-1">"{rec.notes}"</p>
                                    </div>
                                ))
                            ) : (
                                <div className="p-4 border border-dashed border-slate-300 rounded-lg text-center text-slate-400 text-sm">
                                    No expert reviews yet.
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Final Decision Form */}
                    <div className="pt-6 border-t border-slate-100">
                        <label className="text-sm font-bold text-slate-700 mb-2 block">Admin Final Decision</label>

                        {/* TOGGLE: Choose between Dropdown or Manual Text */}
                        {!isManualEntry ? (
                            <div className="mb-6">
                                <select 
                                    className="w-full p-3 border border-slate-300 rounded-lg bg-white focus:ring-2 focus:ring-indigo-500 outline-none"
                                    value={correctionValue}
                                    onChange={(e) => {
                                        if (e.target.value === "__NEW__") {
                                            setIsManualEntry(true);
                                            setCorrectionValue(""); // Clear it so user can type fresh
                                        } else {
                                            setCorrectionValue(e.target.value);
                                        }
                                    }}
                                >
                                    <option value="">-- Select Correct Disease --</option>
                                    {diseases.map(d => (
                                        <option key={d.id} value={d.name}>{d.name}</option>
                                    ))}
                                    {/* The Magic Option */}
                                    <option value="__NEW__" className="font-bold text-indigo-600 bg-indigo-50">+ Add New / Other</option>
                                </select>
                            </div>
                        ) : (
                            <div className="mb-6 bg-indigo-50 p-4 rounded-xl border border-indigo-100">
                                <div className="flex justify-between items-center mb-2">
                                    <span className="text-xs font-bold text-indigo-700 uppercase tracking-wider">Manual Entry Mode</span>
                                    <button 
                                        onClick={() => { setIsManualEntry(false); setCorrectionValue(""); }}
                                        className="text-xs text-slate-400 hover:text-slate-600 underline"
                                    >
                                        Back to List
                                    </button>
                                </div>
                                <input 
                                    type="text" 
                                    placeholder="Type the disease name here..." 
                                    className="w-full p-3 border border-indigo-300 rounded-lg bg-white focus:ring-2 focus:ring-indigo-500 outline-none text-indigo-900 font-medium"
                                    value={correctionValue}
                                    onChange={(e) => setCorrectionValue(e.target.value)}
                                    autoFocus
                                />
                                <p className="text-xs text-indigo-400 mt-2">
                                    Note: This will save a new disease name to the report, but won't automatically add it to your Knowledge Base.
                                </p>
                            </div>
                        )}

                        {/* Action Buttons */}
                        <div className="flex justify-end gap-3">
                            <button onClick={() => setIsModalOpen(false)} className="px-4 py-2 text-slate-500 font-medium hover:bg-slate-100 rounded-lg">Cancel</button>
                            
                            <button 
                                onClick={() => updateStatus(selectedReport.report_id, "Verified", null)}
                                className="px-4 py-2 bg-green-50 text-green-700 font-bold rounded-lg hover:bg-green-100 border border-green-200"
                            >
                                Confirm AI was Correct
                            </button>
                            
                            <button 
                                onClick={submitCorrection}
                                disabled={!correctionValue}
                                className={`px-6 py-2 text-white font-bold rounded-lg flex items-center gap-2 ${
                                    correctionValue ? 'bg-indigo-600 hover:bg-indigo-700 shadow-md shadow-indigo-200' : 'bg-slate-300 cursor-not-allowed'
                                }`}
                            >
                                <Save size={18} /> Save Correction
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
      )}

    </div>
  );
}
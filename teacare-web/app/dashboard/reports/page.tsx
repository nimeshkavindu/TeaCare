'use client';
import { useState, useEffect } from 'react';
import Cookies from 'js-cookie'; 
import { useRouter } from 'next/navigation';
import { 
  Microscope, FileText, CheckCircle, Clock, Send, 
  UserCheck, AlertTriangle, X 
} from 'lucide-react';

// --- Types ---
interface Recommendation {
  recommendation_id: number;
  expert_name: string;
  suggested_disease: string;
  notes: string;
  timestamp: string;
}

interface Report {
  report_id: number;
  disease_name: string;
  confidence: string;
  image_url: string;
  timestamp: string;
  is_correct: string;      
  user_correction: string; 
  verification_status: string; 
  recommendations: Recommendation[];
}

interface User {
  user_id: number;
  full_name: string;
  email: string;
  role: string;
}

export default function ResearcherReviewPage() {
  const router = useRouter();
  
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [reports, setReports] = useState<Report[]>([]);
  const [diseases, setDiseases] = useState<{id: number, name: string}[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  
  const [filter, setFilter] = useState("pending");
  const [selectedReport, setSelectedReport] = useState<Report | null>(null);
  const [suggestion, setSuggestion] = useState("");
  const [notes, setNotes] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isManualEntry, setIsManualEntry] = useState(false);

 // --- 1. Load User Session (Fixed for your Login Logic) ---
  useEffect(() => {
    // 1. Read the specific cookies set by LoginPage
    const token = Cookies.get('token');
    const role = Cookies.get('role');
    const userId = Cookies.get('user_id');
    const userName = Cookies.get('user_name');

    // 2. Validate essential data exists
    if (!token || !role || !userId) {
      router.push('/login'); 
      return;
    }

    // 3. Construct the user object manually since we don't have a JSON cookie
    const userData: User = {
      user_id: parseInt(userId),
      full_name: userName || 'Unknown Expert',
      role: role,
      email: '' // Email isn't in your cookies, but it's not strictly needed for the API call
    };

    // DEBUG
    console.log("Logged in as:", userData.full_name, "| Role:", userData.role);
    
    // 4. Set State
    setCurrentUser(userData);

    // 5. Fetch Data
    fetchData();
  }, []);

  // --- 2. Fetch Data ---
  const fetchData = async () => {
    setIsLoading(true);
    try {
      const apiFilter = filter === 'all' ? 'all' : filter; 
      const res = await fetch(`http://localhost:8000/api/admin/reports_triage?filter_by=${apiFilter}`);
      
      if (res.ok) {
        const data = await res.json();
        setReports(data);
      }

      const resDiseases = await fetch('http://localhost:8000/api/diseases');
      if (resDiseases.ok) setDiseases(await resDiseases.json());
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [filter]);

  // --- 3. Submit Logic ---
  const handleSubmitRecommendation = async () => {
    if (!selectedReport || !suggestion || !currentUser) return;
    setIsSubmitting(true);

    try {
      const payload = {
        expert_id: currentUser.user_id,
        expert_name: currentUser.full_name,
        suggested_disease: suggestion,
        notes: notes
      };

      const res = await fetch(`http://localhost:8000/api/reports/${selectedReport.report_id}/recommend`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        setSelectedReport(null);
        setSuggestion("");
        setNotes("");
        setIsManualEntry(false);
        fetchData(); 
      } else {
        // If backend blocks it (403), show alert
        alert("Server Error: Your account role might not have permission to submit.");
      }
    } catch (e) {
      console.error(e);
    } finally {
      setIsSubmitting(false);
    }
  };

  const hasUserReviewed = (report: Report) => {
    if (!currentUser) return false;
    return report.recommendations.some(r => r.expert_name === currentUser.full_name);
  };

  if (!currentUser) return null;

  return (
    <div className="p-8 max-w-7xl mx-auto min-h-screen bg-slate-50/50">
      
      <header className="mb-8 flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
            <h1 className="text-3xl font-bold text-slate-900 flex items-center gap-3">
            <div className="p-2 bg-purple-100 text-purple-600 rounded-lg shadow-sm">
                <Microscope size={32} />
            </div>
            Expert Diagnostic Console
            </h1>
            <p className="text-slate-500 mt-2">
              Welcome, <span className="font-bold text-purple-700">{currentUser.full_name}</span> ({currentUser.role}). Review pending cases.
            </p>
        </div>

        <div className="flex bg-white p-1 rounded-lg border border-slate-200 shadow-sm">
            {['all', 'pending', 'conflict'].map((f) => (
                <button
                    key={f}
                    onClick={() => setFilter(f)}
                    className={`px-4 py-2 rounded-md text-sm font-bold capitalize transition-all ${
                        filter === f ? 'bg-purple-600 text-white shadow-md' : 'text-slate-500 hover:bg-slate-50'
                    }`}
                >
                    {f}
                </button>
            ))}
        </div>
      </header>

      {/* Reports Grid */}
      {isLoading ? (
        <div className="text-center py-20 text-slate-400">Loading clinical data...</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {reports.map((report) => {
            const hasDisagreement = report.is_correct === "No";
            const myRecommendation = hasUserReviewed(report);
            const status = report.verification_status || "Pending";

            return (
              <div 
                key={report.report_id} 
                className={`bg-white rounded-xl border shadow-sm hover:shadow-md transition-all group ${
                  hasDisagreement ? 'border-red-100' : 'border-slate-200'
                }`}
              >
                <div className="relative h-48 w-full bg-slate-100 rounded-t-xl overflow-hidden">
                  <img 
                    src={`http://localhost:8000/${report.image_url}`} 
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                  />
                  <div className="absolute top-3 right-3 flex gap-2">
                    <span className="bg-black/60 backdrop-blur-md text-white text-xs font-bold px-2 py-1 rounded-md">
                      {report.confidence}
                    </span>
                  </div>
                  
                  <div className="absolute top-3 left-3">
                    <span className={`text-[10px] font-bold px-2 py-1 rounded-md border ${
                        status === 'Pending' ? 'bg-yellow-100 text-yellow-700 border-yellow-200' :
                        status === 'Verified' ? 'bg-green-100 text-green-700 border-green-200' :
                        status === 'Auto-Verified' ? 'bg-blue-100 text-blue-700 border-blue-200' :
                        'bg-purple-100 text-purple-700 border-purple-200'
                    }`}>
                        {status}
                    </span>
                  </div>

                  {hasDisagreement && (
                    <div className="absolute bottom-0 left-0 right-0 bg-red-500/90 text-white text-xs font-bold px-3 py-1.5 flex items-center justify-center gap-2">
                      <AlertTriangle size={12} /> Farmer Disagreed
                    </div>
                  )}
                </div>

                <div className="p-5">
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <p className="text-xs text-slate-400 font-bold uppercase tracking-wider mb-1">AI Prediction</p>
                      <h3 className="text-lg font-bold text-slate-800">{report.disease_name}</h3>
                    </div>
                    {myRecommendation && (
                        <div className="p-1.5 bg-green-50 text-green-600 rounded-full" title="You reviewed this">
                            <CheckCircle size={18} />
                        </div>
                    )}
                  </div>

                  <div className="flex items-center gap-2 mt-4 text-xs text-slate-500 bg-slate-50 p-2 rounded-lg border border-slate-100">
                    <UserCheck size={14} className="text-purple-500" />
                    {report.recommendations.length > 0 
                      ? `${report.recommendations.length} Expert opinions submitted`
                      : "No expert reviews yet"}
                  </div>

                  <button 
                    onClick={() => {
                        setSelectedReport(report);
                        setSuggestion(report.disease_name);
                        setIsManualEntry(false);
                    }}
                    className={`w-full mt-5 border-2 font-bold py-2.5 rounded-lg transition-colors flex items-center justify-center gap-2 ${
                        myRecommendation 
                        ? 'bg-purple-50 border-purple-200 text-purple-700' 
                        : 'bg-white border-purple-600 text-purple-700 hover:bg-purple-600 hover:text-white'
                    }`}
                  >
                    <Microscope size={18} />
                    {myRecommendation ? "Edit My Opinion" : "Review Case"}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {selectedReport && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[100] flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-4xl h-[85vh] flex overflow-hidden">
            
            <div className="w-1/2 bg-slate-900 relative hidden md:block">
                <img 
                    src={`http://localhost:8000/${selectedReport.image_url}`} 
                    className="w-full h-full object-contain"
                />
                <div className="absolute bottom-0 inset-x-0 bg-gradient-to-t from-black/80 to-transparent p-6 text-white">
                    <p className="text-sm font-mono text-slate-300 opacity-70 mb-1">Case ID: #{selectedReport.report_id}</p>
                    <h2 className="text-2xl font-bold">{selectedReport.disease_name}</h2>
                    <p className="text-slate-300 text-sm mt-1">AI Confidence: {selectedReport.confidence}</p>
                </div>
            </div>

            <div className="w-full md:w-1/2 flex flex-col">
                <div className="p-5 border-b border-slate-100 flex justify-between items-center">
                    <h3 className="font-bold text-lg text-slate-800 flex items-center gap-2">
                        <FileText size={20} className="text-purple-600"/> Clinical Review
                    </h3>
                    <button onClick={() => setSelectedReport(null)} className="text-slate-400 hover:text-slate-600">
                        <X size={24} />
                    </button>
                </div>

                <div className="flex-1 overflow-y-auto p-6 space-y-6">
                    
                    {selectedReport.recommendations.length > 0 && (
                        <div className="space-y-3">
                            <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Peer Opinions</h4>
                            {selectedReport.recommendations.map((rec) => (
                                <div key={rec.recommendation_id} className={`p-3 border rounded-lg text-sm ${rec.expert_name === currentUser.full_name ? 'bg-purple-50 border-purple-200' : 'bg-slate-50 border-slate-100'}`}>
                                    <div className="flex justify-between mb-1">
                                        <span className={`font-bold ${rec.expert_name === currentUser.full_name ? 'text-purple-700' : 'text-slate-700'}`}>
                                            {rec.expert_name} {rec.expert_name === currentUser.full_name && '(You)'}
                                        </span>
                                        <span className="text-slate-400 text-xs">{rec.timestamp}</span>
                                    </div>
                                    <p className="text-slate-600">
                                        Suggested: <span className="font-semibold text-purple-700">{rec.suggested_disease}</span>
                                    </p>
                                    {rec.notes && <p className="text-slate-500 italic mt-1">"{rec.notes}"</p>}
                                </div>
                            ))}
                        </div>
                    )}

                    <div className="space-y-4 pt-2">
                        <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Your Diagnosis</h4>
                        
                        <div>
                            <label className="block text-sm font-semibold text-slate-700 mb-1.5">Disease Identification</label>
                            
                            {!isManualEntry ? (
                                <select 
                                    className="w-full p-3 border border-slate-300 rounded-lg bg-white focus:ring-2 focus:ring-purple-500 outline-none"
                                    value={suggestion}
                                    onChange={(e) => {
                                        if (e.target.value === "__NEW__") {
                                            setIsManualEntry(true);
                                            setSuggestion(""); 
                                        } else {
                                            setSuggestion(e.target.value);
                                        }
                                    }}
                                >
                                    <option value="">-- Select Disease --</option>
                                    {diseases.map(d => (
                                        <option key={d.id} value={d.name}>{d.name}</option>
                                    ))}
                                    <option value="Unknown/Other">Unknown / Other</option>
                                    <option value="__NEW__" className="font-bold text-purple-600 bg-purple-50">+ Enter New Disease</option>
                                </select>
                            ) : (
                                <div className="space-y-2">
                                    <div className="flex justify-between items-center">
                                        <span className="text-xs text-purple-600 font-bold uppercase tracking-wider">Manual Entry Mode</span>
                                        <button 
                                            onClick={() => { setIsManualEntry(false); setSuggestion(""); }}
                                            className="text-xs text-slate-400 hover:text-slate-600 underline"
                                        >
                                            Back to List
                                        </button>
                                    </div>
                                    <input 
                                        type="text" 
                                        className="w-full p-3 border border-purple-300 rounded-lg bg-purple-50 focus:ring-2 focus:ring-purple-500 outline-none text-purple-900 placeholder:text-purple-300"
                                        placeholder="Type disease name..."
                                        value={suggestion}
                                        onChange={(e) => setSuggestion(e.target.value)}
                                        autoFocus
                                    />
                                </div>
                            )}
                        </div>

                        <div>
                            <label className="block text-sm font-semibold text-slate-700 mb-1.5">Clinical Notes</label>
                            <textarea 
                                className="w-full p-3 border border-slate-300 rounded-lg bg-white focus:ring-2 focus:ring-purple-500 outline-none h-32 resize-none text-sm"
                                placeholder="Describe visual symptoms (e.g., distinct yellow halo, necrotic center)..."
                                value={notes}
                                onChange={(e) => setNotes(e.target.value)}
                            ></textarea>
                        </div>
                    </div>
                </div>

                <div className="p-5 border-t border-slate-100 bg-slate-50 flex justify-end gap-3">
                    <button 
                        onClick={() => setSelectedReport(null)}
                        className="px-5 py-2.5 text-slate-500 font-bold hover:bg-slate-200 rounded-lg transition-colors"
                    >
                        Cancel
                    </button>
                    <button 
                        onClick={handleSubmitRecommendation}
                        disabled={isSubmitting || !suggestion}
                        className={`px-6 py-2.5 text-white font-bold rounded-lg flex items-center gap-2 shadow-lg shadow-purple-200 ${
                            isSubmitting ? 'bg-purple-400' : 'bg-purple-600 hover:bg-purple-700'
                        }`}
                    >
                        <Send size={18} />
                        {isSubmitting ? 'Submitting...' : 'Submit Opinion'}
                    </button>
                </div>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
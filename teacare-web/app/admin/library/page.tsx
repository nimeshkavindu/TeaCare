'use client';
import { useState, useEffect } from 'react';
import { 
  BookOpen, CheckCircle, XCircle, Clock, Trash2, 
  AlertTriangle, Eye, Search, X, FileText, 
  Stethoscope, Shield, User, Image as ImageIcon 
} from 'lucide-react';

// 1. Updated Interface to match backend data
interface Pathogen {
  id: number;
  name: string;
  scientific_name: string;
  description: string;
  symptoms: string;
  prevention: string; // Added
  treatment: string;  // Added
  image_url: string;
  status: string; 
  submitted_by: string;
  timestamp: string;
}

export default function AdminLibraryPage() {
  const [entries, setEntries] = useState<Pathogen[]>([]);
  const [filter, setFilter] = useState('Pending');
  const [isLoading, setIsLoading] = useState(true);
  
  // 2. State for the Detail Modal
  const [selectedEntry, setSelectedEntry] = useState<Pathogen | null>(null);

  // Load Data
  const fetchLibrary = async () => {
    setIsLoading(true);
    try {
      const res = await fetch('http://localhost:8000/api/library?status=all');
      if (res.ok) setEntries(await res.json());
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchLibrary();
  }, []);

  // Actions
  const handleStatus = async (id: number, status: string) => {
    if(!confirm(`Are you sure you want to mark this as ${status}?`)) return;

    await fetch(`http://localhost:8000/api/admin/library/${id}/status`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status })
    });
    
    // Close modal if open and refresh
    setSelectedEntry(null); 
    fetchLibrary();
  };

  const handleDelete = async (id: number) => {
    if(!confirm("This will permanently delete this entry. Continue?")) return;

    await fetch(`http://localhost:8000/api/admin/library/${id}`, {
      method: 'DELETE'
    });
    setSelectedEntry(null);
    fetchLibrary();
  };

  // Filter Logic
  const filteredEntries = entries.filter(e => 
    filter === 'All' ? true : e.status === filter
  );

  return (
    <div className="p-8 max-w-7xl mx-auto">
      
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-end mb-8 gap-4">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 flex items-center gap-3">
            <div className="p-2 bg-blue-100 text-blue-700 rounded-lg">
                <BookOpen size={32} />
            </div>
            Library Moderation
          </h1>
          <p className="text-slate-500 mt-2 ml-14">
            Review and approve pathogen definitions submitted by researchers.
          </p>
        </div>

        {/* Filter Tabs */}
        <div className="flex bg-white p-1 rounded-lg border border-slate-200 shadow-sm">
            {['Pending', 'Approved', 'Rejected', 'All'].map((f) => (
                <button
                    key={f}
                    onClick={() => setFilter(f)}
                    className={`px-4 py-2 rounded-md text-sm font-bold transition-all ${
                        filter === f 
                        ? 'bg-slate-800 text-white shadow' 
                        : 'text-slate-500 hover:bg-slate-50'
                    }`}
                >
                    {f}
                </button>
            ))}
        </div>
      </div>

      {/* Content */}
      {isLoading ? (
        <div className="text-center py-20 text-slate-400">Loading entries...</div>
      ) : (
        <div className="space-y-4">
            {filteredEntries.length === 0 && (
                <div className="text-center py-12 bg-slate-50 rounded-xl border border-dashed border-slate-300">
                    <p className="text-slate-400 font-medium">No {filter} entries found.</p>
                </div>
            )}

            {filteredEntries.map((entry) => (
                <div key={entry.id} className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden flex flex-col md:flex-row">
                    
                    {/* Image Sidebar */}
                    <div className="w-full md:w-48 h-48 md:h-auto bg-slate-100 relative shrink-0">
                        {entry.image_url ? (
                            <img src={`http://localhost:8000/${entry.image_url}`} className="w-full h-full object-cover" />
                        ) : (
                            <div className="w-full h-full flex items-center justify-center text-slate-400 text-xs">No Image</div>
                        )}
                        <div className="absolute top-2 left-2">
                            <span className={`px-2 py-1 text-xs font-bold rounded shadow-sm border ${
                                entry.status === 'Approved' ? 'bg-green-100 text-green-700 border-green-200' :
                                entry.status === 'Pending' ? 'bg-amber-100 text-amber-700 border-amber-200' :
                                'bg-red-100 text-red-700 border-red-200'
                            }`}>
                                {entry.status}
                            </span>
                        </div>
                    </div>

                    {/* Content Body */}
                    <div className="p-6 flex-1 flex flex-col justify-between">
                        <div>
                            <div className="flex justify-between items-start">
                                <div>
                                    <h3 className="text-xl font-bold text-slate-800">{entry.name}</h3>
                                    <p className="text-sm text-slate-500 italic">{entry.scientific_name}</p>
                                </div>
                                <div className="text-right">
                                    <p className="text-xs text-slate-400">Submitted by</p>
                                    <p className="text-sm font-bold text-slate-700">{entry.submitted_by}</p>
                                </div>
                            </div>

                            <p className="mt-4 text-slate-600 text-sm line-clamp-2">{entry.description}</p>
                            
                            <div className="mt-4 flex gap-4 text-xs">
                                <div className="bg-slate-50 px-3 py-2 rounded border border-slate-100">
                                    <span className="font-bold block text-slate-700 mb-1">Symptoms</span>
                                    <span className="text-slate-500 line-clamp-1">{entry.symptoms}</span>
                                </div>
                                <button 
                                    onClick={() => setSelectedEntry(entry)} 
                                    className="text-blue-600 font-bold hover:underline ml-auto flex items-center gap-1"
                                >
                                    <Eye size={14} /> View Full Details
                                </button>
                            </div>
                        </div>

                        {/* Action Bar */}
                        <div className="mt-6 pt-4 border-t border-slate-100 flex justify-end gap-3">
                            {entry.status === 'Pending' && (
                                <>
                                    <button 
                                        onClick={() => handleDelete(entry.id)}
                                        className="px-4 py-2 text-red-600 font-bold hover:bg-red-50 rounded-lg transition-colors flex items-center gap-2"
                                    >
                                        <XCircle size={18} /> Reject
                                    </button>
                                    <button 
                                        onClick={() => handleStatus(entry.id, 'Approved')}
                                        className="px-6 py-2 bg-green-600 hover:bg-green-700 text-white font-bold rounded-lg shadow-md shadow-green-100 transition-colors flex items-center gap-2"
                                    >
                                        <CheckCircle size={18} /> Approve
                                    </button>
                                </>
                            )}
                            
                            {entry.status === 'Approved' && (
                                <button 
                                    onClick={() => handleStatus(entry.id, 'Pending')}
                                    className="px-4 py-2 text-slate-500 font-bold hover:bg-slate-100 rounded-lg flex items-center gap-2"
                                >
                                    <Clock size={18} /> Revoke Approval
                                </button>
                            )}

                            <button 
                                onClick={() => handleDelete(entry.id)}
                                className="p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg ml-auto"
                                title="Delete Permanently"
                            >
                                <Trash2 size={18} />
                            </button>
                        </div>
                    </div>
                </div>
            ))}
        </div>
      )}

      {/* --- DETAIL MODAL (NEW) --- */}
      {selectedEntry && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl shadow-2xl w-full max-w-4xl h-[90vh] flex overflow-hidden">
                {/* Left: Image */}
                <div className="w-1/3 bg-slate-100 relative hidden md:block">
                    {selectedEntry.image_url ? (
                        <img src={`http://localhost:8000/${selectedEntry.image_url}`} className="w-full h-full object-cover" />
                    ) : (
                        <div className="w-full h-full flex items-center justify-center text-slate-400"><ImageIcon size={64}/></div>
                    )}
                    <div className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-black/80 to-transparent text-white">
                        <p className="font-bold">{selectedEntry.name}</p>
                        <p className="text-xs opacity-80 italic">{selectedEntry.scientific_name}</p>
                    </div>
                </div>

                {/* Right: Info */}
                <div className="w-full md:w-2/3 flex flex-col">
                    <div className="p-6 border-b border-slate-100 flex justify-between items-center bg-slate-50">
                        <div>
                            <h2 className="text-2xl font-bold text-slate-800">Review Entry #{selectedEntry.id}</h2>
                            <div className="flex items-center gap-3 mt-1">
                                <span className={`text-xs px-2 py-0.5 rounded font-bold border ${
                                    selectedEntry.status === 'Approved' ? 'bg-green-100 text-green-700 border-green-200' :
                                    selectedEntry.status === 'Pending' ? 'bg-amber-100 text-amber-700 border-amber-200' : 
                                    'bg-red-100 text-red-700 border-red-200'
                                }`}>
                                    {selectedEntry.status}
                                </span>
                            </div>
                        </div>
                        <button onClick={() => setSelectedEntry(null)} className="p-2 hover:bg-slate-200 rounded-full transition-colors">
                            <X size={24} className="text-slate-400" />
                        </button>
                    </div>

                    <div className="flex-1 overflow-y-auto p-6 space-y-6">
                        {/* Description */}
                        <div>
                            <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wide mb-2 flex items-center gap-2">
                                <FileText size={16} className="text-blue-600"/> Description
                            </h3>
                            <p className="text-slate-600 leading-relaxed text-sm">{selectedEntry.description}</p>
                        </div>

                        {/* Symptoms */}
                        <div className="p-4 bg-red-50 rounded-xl border border-red-100">
                            <h3 className="text-sm font-bold text-red-800 uppercase tracking-wide mb-2 flex items-center gap-2">
                                <AlertTriangle size={16}/> Visible Symptoms
                            </h3>
                            <p className="text-red-700 text-sm">{selectedEntry.symptoms}</p>
                        </div>

                        {/* Treatment & Prevention Grid */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div>
                                <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wide mb-2 flex items-center gap-2">
                                    <Stethoscope size={16} className="text-blue-600"/> Treatment
                                </h3>
                                <p className="text-slate-600 text-sm whitespace-pre-line">{selectedEntry.treatment || "No data provided."}</p>
                            </div>
                            <div>
                                <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wide mb-2 flex items-center gap-2">
                                    <Shield size={16} className="text-green-600"/> Prevention
                                </h3>
                                <p className="text-slate-600 text-sm whitespace-pre-line">{selectedEntry.prevention || "No data provided."}</p>
                            </div>
                        </div>

                        {/* Meta Info */}
                        <div className="pt-6 mt-6 border-t border-slate-100 text-xs text-slate-400 flex items-center gap-2">
                            <User size={12} /> Submitted by: <span className="font-medium text-slate-600">{selectedEntry.submitted_by}</span>
                        </div>
                    </div>
                    
                    {/* Modal Footer Actions */}
                    <div className="p-4 border-t border-slate-100 bg-slate-50 flex justify-end gap-3">
                        <button 
                            onClick={() => setSelectedEntry(null)}
                            className="px-4 py-2 text-slate-500 font-bold hover:bg-slate-200 rounded-lg"
                        >
                            Close
                        </button>
                        
                        {selectedEntry.status === 'Pending' && (
                            <>
                                <button 
                                    onClick={() => handleStatus(selectedEntry.id, 'Rejected')}
                                    className="px-4 py-2 bg-red-100 text-red-700 font-bold rounded-lg hover:bg-red-200 border border-red-200"
                                >
                                    Reject
                                </button>
                                <button 
                                    onClick={() => handleStatus(selectedEntry.id, 'Approved')}
                                    className="px-6 py-2 bg-green-600 text-white font-bold rounded-lg hover:bg-green-700 shadow-lg shadow-green-200"
                                >
                                    Approve & Publish
                                </button>
                            </>
                        )}
                    </div>
                </div>
            </div>
        </div>
      )}

    </div>
  );
}
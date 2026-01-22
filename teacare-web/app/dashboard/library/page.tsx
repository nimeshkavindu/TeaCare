'use client';
import { useState, useEffect } from 'react';
import Cookies from 'js-cookie'; 
import { 
  Book, Plus, Search, Image as ImageIcon, 
  CheckCircle, Clock, AlertCircle, Save, X, 
  Stethoscope, Shield, FileText, User 
} from 'lucide-react';

// 1. Updated Interface to include all fields
interface Pathogen {
  id: number;
  name: string;
  scientific_name: string;
  description: string;
  symptoms: string;
  prevention: string;
  treatment: string;
  image_url: string;
  status: string; 
  submitted_by?: string;
}

export default function LibraryPage() {
  const [diseases, setDiseases] = useState<Pathogen[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  
  // Modal States
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [selectedDisease, setSelectedDisease] = useState<Pathogen | null>(null); // <--- New State for Detail View
  
  const [isLoading, setIsLoading] = useState(true);
  
  // Form State
  const [formData, setFormData] = useState({
    name: '', scientific_name: '', description: '',
    symptoms: '', prevention: '', treatment: ''
  });
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [currentUser, setCurrentUser] = useState<any>(null);

  // 1. Load User & Data
  useEffect(() => {
    const userName = Cookies.get('user_name');
    const userId = Cookies.get('user_id');

    if (userName && userId) {
        setCurrentUser({
            user_id: userId,
            full_name: userName
        });
    } else {
        console.warn("No user logged in found in cookies");
    }

    fetchLibrary();
  }, []);

  const fetchLibrary = async () => {
    setIsLoading(true);
    try {
      const res = await fetch('http://localhost:8000/api/library?status=all');
      if (res.ok) setDiseases(await res.json());
    } finally {
      setIsLoading(false);
    }
  };

  // 2. Submit Logic
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentUser) return;
    setIsSubmitting(true);

    const data = new FormData();
    data.append('name', formData.name);
    data.append('scientific_name', formData.scientific_name);
    data.append('description', formData.description);
    data.append('symptoms', formData.symptoms);
    data.append('prevention', formData.prevention);
    data.append('treatment', formData.treatment);
    data.append('submitted_by', currentUser.full_name);
    if (imageFile) data.append('file', imageFile);

    try {
      const res = await fetch('http://localhost:8000/api/library', {
        method: 'POST',
        body: data,
      });

      if (res.ok) {
        setIsAddModalOpen(false);
        setFormData({ name: '', scientific_name: '', description: '', symptoms: '', prevention: '', treatment: '' });
        setImageFile(null);
        fetchLibrary(); 
        alert("Submission Successful! Sent for Admin Approval.");
      }
    } catch (error) {
      console.error(error);
      alert("Failed to submit.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const filteredDiseases = diseases.filter(d => 
    d.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
    d.scientific_name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="p-8 max-w-7xl mx-auto min-h-screen">
      
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-end mb-8 gap-4">
        <div>
            <h1 className="text-3xl font-bold text-slate-900 flex items-center gap-3">
                <div className="p-2 bg-emerald-100 text-emerald-700 rounded-lg">
                    <Book size={32} />
                </div>
                Pathogen Library
            </h1>
            <p className="text-slate-500 mt-2 ml-14">
                The official reference database for tea diseases.
            </p>
        </div>
        
        <button 
            onClick={() => setIsAddModalOpen(true)}
            className="bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-2.5 px-6 rounded-lg flex items-center gap-2 shadow-lg shadow-emerald-200 transition-all"
        >
            <Plus size={20} /> Add New Pathogen
        </button>
      </div>

      {/* Search Bar */}
      <div className="relative mb-8">
        <Search className="absolute left-4 top-3.5 text-slate-400" size={20} />
        <input 
            type="text" 
            placeholder="Search by common or scientific name..." 
            className="w-full pl-12 pr-4 py-3 bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-emerald-500 outline-none text-slate-700"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
        />
      </div>

      {/* Content Grid */}
      {isLoading ? (
        <div className="text-center py-20 text-slate-400">Loading library...</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredDiseases.map((d) => (
                <div key={d.id} className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden hover:shadow-md transition-shadow group">
                    {/* Image Header */}
                    <div className="h-48 bg-slate-100 relative">
                        {d.image_url ? (
                            <img src={`http://localhost:8000/${d.image_url}`} className="w-full h-full object-cover" />
                        ) : (
                            <div className="w-full h-full flex items-center justify-center text-slate-300">
                                <ImageIcon size={48} />
                            </div>
                        )}
                        
                        {/* Status Badge */}
                        <div className="absolute top-3 right-3">
                            {d.status === 'Approved' ? (
                                <span className="bg-white/90 backdrop-blur text-emerald-700 text-xs font-bold px-2 py-1 rounded-md flex items-center gap-1 shadow-sm">
                                    <CheckCircle size={12} /> Approved
                                </span>
                            ) : (
                                <span className="bg-white/90 backdrop-blur text-amber-600 text-xs font-bold px-2 py-1 rounded-md flex items-center gap-1 shadow-sm">
                                    <Clock size={12} /> Pending Review
                                </span>
                            )}
                        </div>
                    </div>

                    <div className="p-5">
                        <h3 className="text-lg font-bold text-slate-800">{d.name}</h3>
                        <p className="text-sm text-slate-500 italic mb-3">{d.scientific_name}</p>
                        <p className="text-sm text-slate-600 line-clamp-3">{d.description}</p>
                        
                        <div className="mt-4 pt-4 border-t border-slate-100 flex justify-between items-center text-xs text-slate-400">
                            <span>ID: KB-{d.id}</span>
                            <button 
                                onClick={() => setSelectedDisease(d)} // <--- FIXED: Added onClick handler
                                className="text-emerald-600 font-bold hover:underline"
                            >
                                View Details
                            </button>
                        </div>
                    </div>
                </div>
            ))}
        </div>
      )}

      {/* --- 1. VIEW DETAILS MODAL (NEW) --- */}
      {selectedDisease && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl shadow-2xl w-full max-w-4xl h-[90vh] flex overflow-hidden">
                {/* Left: Image */}
                <div className="w-1/3 bg-slate-100 relative hidden md:block">
                    {selectedDisease.image_url ? (
                        <img src={`http://localhost:8000/${selectedDisease.image_url}`} className="w-full h-full object-cover" />
                    ) : (
                        <div className="w-full h-full flex items-center justify-center text-slate-400"><ImageIcon size={64}/></div>
                    )}
                    <div className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-black/80 to-transparent text-white">
                        <p className="font-bold">{selectedDisease.name}</p>
                        <p className="text-xs opacity-80 italic">{selectedDisease.scientific_name}</p>
                    </div>
                </div>

                {/* Right: Info */}
                <div className="w-full md:w-2/3 flex flex-col">
                    <div className="p-6 border-b border-slate-100 flex justify-between items-center">
                        <div>
                            <h2 className="text-2xl font-bold text-slate-800">{selectedDisease.name}</h2>
                            <div className="flex items-center gap-3 mt-1">
                                <span className="text-sm text-slate-500 italic">{selectedDisease.scientific_name}</span>
                                {selectedDisease.status === 'Approved' ? 
                                    <span className="text-xs bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded font-bold">Approved</span> : 
                                    <span className="text-xs bg-amber-100 text-amber-700 px-2 py-0.5 rounded font-bold">Pending Review</span>
                                }
                            </div>
                        </div>
                        <button onClick={() => setSelectedDisease(null)} className="p-2 hover:bg-slate-100 rounded-full transition-colors">
                            <X size={24} className="text-slate-400" />
                        </button>
                    </div>

                    <div className="flex-1 overflow-y-auto p-6 space-y-6">
                        {/* Description */}
                        <div>
                            <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wide mb-2 flex items-center gap-2">
                                <FileText size={16} className="text-emerald-600"/> Description
                            </h3>
                            <p className="text-slate-600 leading-relaxed text-sm">{selectedDisease.description}</p>
                        </div>

                        {/* Symptoms */}
                        <div className="p-4 bg-red-50 rounded-xl border border-red-100">
                            <h3 className="text-sm font-bold text-red-800 uppercase tracking-wide mb-2 flex items-center gap-2">
                                <AlertCircle size={16}/> Visible Symptoms
                            </h3>
                            <p className="text-red-700 text-sm">{selectedDisease.symptoms}</p>
                        </div>

                        {/* Treatment & Prevention Grid */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div>
                                <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wide mb-2 flex items-center gap-2">
                                    <Stethoscope size={16} className="text-blue-600"/> Treatment
                                </h3>
                                <p className="text-slate-600 text-sm whitespace-pre-line">{selectedDisease.treatment || "No treatment data available."}</p>
                            </div>
                            <div>
                                <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wide mb-2 flex items-center gap-2">
                                    <Shield size={16} className="text-green-600"/> Prevention
                                </h3>
                                <p className="text-slate-600 text-sm whitespace-pre-line">{selectedDisease.prevention || "No prevention data available."}</p>
                            </div>
                        </div>

                        {/* Meta Info */}
                        {selectedDisease.submitted_by && (
                            <div className="pt-6 mt-6 border-t border-slate-100 text-xs text-slate-400 flex items-center gap-2">
                                <User size={12} /> Contributed by: <span className="font-medium text-slate-600">{selectedDisease.submitted_by}</span>
                            </div>
                        )}
                    </div>
                    
                    <div className="p-4 border-t border-slate-100 bg-slate-50 flex justify-end">
                        <button 
                            onClick={() => setSelectedDisease(null)}
                            className="px-6 py-2 bg-slate-800 text-white font-bold rounded-lg hover:bg-slate-900 transition-colors"
                        >
                            Close
                        </button>
                    </div>
                </div>
            </div>
        </div>
      )}

      {/* --- 2. ADD MODAL --- */}
      {isAddModalOpen && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
                <div className="p-6 border-b border-slate-100 flex justify-between items-center bg-slate-50 sticky top-0 z-10">
                    <h2 className="text-xl font-bold text-slate-800 flex items-center gap-2">
                        <Plus size={24} className="text-emerald-600"/> New Knowledge Entry
                    </h2>
                    <button onClick={() => setIsAddModalOpen(false)}><X size={24} className="text-slate-400 hover:text-slate-600" /></button>
                </div>

                <form onSubmit={handleSubmit} className="p-6 space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-bold text-slate-700 mb-1">Common Name</label>
                            <input required type="text" className="w-full p-2 border rounded-lg" placeholder="e.g. Blister Blight"
                                value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})} />
                        </div>
                        <div>
                            <label className="block text-sm font-bold text-slate-700 mb-1">Scientific Name</label>
                            <input required type="text" className="w-full p-2 border rounded-lg italic" placeholder="e.g. Exobasidium vexans"
                                value={formData.scientific_name} onChange={e => setFormData({...formData, scientific_name: e.target.value})} />
                        </div>
                    </div>

                    <div>
                        <label className="block text-sm font-bold text-slate-700 mb-1">Description</label>
                        <textarea required className="w-full p-2 border rounded-lg h-24" 
                            value={formData.description} onChange={e => setFormData({...formData, description: e.target.value})} />
                    </div>

                    <div>
                        <label className="block text-sm font-bold text-slate-700 mb-1">Visible Symptoms</label>
                        <textarea required className="w-full p-2 border rounded-lg h-20" placeholder="What should the farmer look for?"
                            value={formData.symptoms} onChange={e => setFormData({...formData, symptoms: e.target.value})} />
                    </div>
                    
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-bold text-slate-700 mb-1">Treatment</label>
                            <textarea className="w-full p-2 border rounded-lg h-20" 
                                value={formData.treatment} onChange={e => setFormData({...formData, treatment: e.target.value})} />
                        </div>
                        <div>
                            <label className="block text-sm font-bold text-slate-700 mb-1">Prevention</label>
                            <textarea className="w-full p-2 border rounded-lg h-20" 
                                value={formData.prevention} onChange={e => setFormData({...formData, prevention: e.target.value})} />
                        </div>
                    </div>

                    <div>
                        <label className="block text-sm font-bold text-slate-700 mb-1">Reference Image</label>
                        <div className="border-2 border-dashed border-slate-300 rounded-lg p-6 text-center hover:bg-slate-50 transition cursor-pointer relative">
                            <input type="file" className="absolute inset-0 opacity-0 cursor-pointer" 
                                onChange={(e) => setImageFile(e.target.files ? e.target.files[0] : null)} />
                            <div className="flex flex-col items-center">
                                <ImageIcon size={32} className="text-slate-400 mb-2" />
                                <span className="text-sm text-slate-500 font-medium">
                                    {imageFile ? imageFile.name : "Click to upload a clear reference photo"}
                                </span>
                            </div>
                        </div>
                    </div>

                    <div className="pt-4 flex justify-end gap-3">
                        <button type="button" onClick={() => setIsAddModalOpen(false)} className="px-5 py-2 text-slate-500 font-bold hover:bg-slate-100 rounded-lg">Cancel</button>
                        <button type="submit" disabled={isSubmitting} className="px-6 py-2 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-lg flex items-center gap-2">
                            <Save size={18} /> {isSubmitting ? 'Submitting...' : 'Submit to Library'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
      )}

    </div>
  );
}
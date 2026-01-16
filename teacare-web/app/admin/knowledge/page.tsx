'use client';
import { useState, useEffect } from 'react';
import { BookOpen, Plus, Edit2, Trash2, Save, X, FlaskConical, Leaf } from 'lucide-react';

// Types match your Database
interface Treatment {
  type: string;
  title: string;
  instruction: string;
  safety_tip: string;
}

interface Disease {
  disease_id: number;
  name: string;
  symptoms: string[];
  causes: string[];
  treatments: Treatment[];
}

export default function KnowledgeBasePage() {
  const [diseases, setDiseases] = useState<Disease[]>([]);
  const [loading, setLoading] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  
  // Form State
  const [formName, setFormName] = useState('');
  const [formSymptoms, setFormSymptoms] = useState('');
  const [formCauses, setFormCauses] = useState('');
  const [formTreatments, setFormTreatments] = useState<Treatment[]>([]);

  const fetchDiseases = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/diseases');
      if (res.ok) setDiseases(await res.json());
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchDiseases(); }, []);

  // --- FORM HANDLERS ---

  const handleSave = async () => {
    if (!formName) return alert("Disease Name is required");

    const payload = {
        name: formName,
        symptoms: formSymptoms.split('\n').filter(line => line.trim() !== ''),
        causes: formCauses.split('\n').filter(line => line.trim() !== ''),
        treatments: formTreatments,
    };

    await fetch('http://localhost:8000/api/admin/diseases', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    setIsEditing(false);
    resetForm();
    fetchDiseases();
  };

  const resetForm = () => {
    setFormName('');
    setFormSymptoms('');
    setFormCauses('');
    setFormTreatments([]);
  };

  const openEdit = (d: Disease) => {
    setFormName(d.name);
    setFormSymptoms(d.symptoms ? d.symptoms.join('\n') : '');
    setFormCauses(d.causes ? d.causes.join('\n') : '');
    setFormTreatments(d.treatments || []);
    setIsEditing(true);
  };

  const addTreatment = () => {
    setFormTreatments([...formTreatments, { type: 'Organic', title: '', instruction: '', safety_tip: '' }]);
  };

  const updateTreatment = (index: number, field: keyof Treatment, value: string) => {
    const updated = [...formTreatments];
    updated[index] = { ...updated[index], [field]: value };
    setFormTreatments(updated);
  };

  const removeTreatment = (index: number) => {
    setFormTreatments(formTreatments.filter((_, i) => i !== index));
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Delete this entry?")) return;
    await fetch(`http://localhost:8000/api/admin/diseases/${id}`, { method: 'DELETE' });
    fetchDiseases();
  };

  return (
    <div className="p-8 max-w-7xl mx-auto relative">
      <header className="mb-8 flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 flex items-center gap-3">
            <div className="p-2 bg-amber-100 text-amber-600 rounded-lg"><BookOpen size={32} /></div>
            Knowledge Base
          </h1>
          <p className="text-slate-500 mt-2 ml-14">Manage diseases and their specific treatments.</p>
        </div>
        <button 
          onClick={() => { resetForm(); setIsEditing(true); }}
          className="flex items-center gap-2 bg-slate-900 text-white px-4 py-2 rounded-lg hover:bg-slate-800 transition-colors"
        >
          <Plus size={18} /> Add Disease
        </button>
      </header>

      {/* --- LIST VIEW --- */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {diseases.map((d) => (
          <div key={d.disease_id} className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 flex flex-col hover:border-amber-200 transition-colors">
            <div className="flex justify-between items-start mb-4">
              <h3 className="text-xl font-bold text-slate-800">{d.name}</h3>
              <div className="flex gap-2">
                <button onClick={() => openEdit(d)} className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg"><Edit2 size={16} /></button>
                <button onClick={() => handleDelete(d.disease_id)} className="p-2 text-red-600 hover:bg-red-50 rounded-lg"><Trash2 size={16} /></button>
              </div>
            </div>
            <div className="text-sm text-slate-600 space-y-2">
                <p><span className="font-bold">Symptoms:</span> {d.symptoms?.length || 0}</p>
                <p><span className="font-bold">Treatments:</span> {d.treatments?.length || 0}</p>
            </div>
          </div>
        ))}
      </div>

      {/* --- EDIT/ADD MODAL --- */}
      {isEditing && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-y-auto flex flex-col">
            
            {/* Modal Header */}
            <div className="p-6 border-b border-slate-100 flex justify-between items-center bg-white sticky top-0 z-10">
              <h2 className="text-xl font-bold text-slate-800">{formName ? `Edit: ${formName}` : "Add New Disease"}</h2>
              <button onClick={() => setIsEditing(false)}><X size={24} className="text-slate-400" /></button>
            </div>

            <div className="p-8 space-y-6 overflow-y-auto">
              {/* Name */}
              <div>
                <label className="block text-sm font-bold text-slate-700 mb-2">Disease Name</label>
                <input type="text" value={formName} onChange={(e) => setFormName(e.target.value)}
                  className="w-full px-4 py-2 rounded-lg border border-slate-300" placeholder="e.g. Blister Blight" />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Symptoms */}
                <div>
                  <label className="block text-sm font-bold text-slate-700 mb-2">Symptoms (One per line)</label>
                  <textarea rows={5} value={formSymptoms} onChange={(e) => setFormSymptoms(e.target.value)}
                    className="w-full px-4 py-2 rounded-lg border border-slate-300" placeholder="- White spots..." />
                </div>
                {/* Causes */}
                <div>
                  <label className="block text-sm font-bold text-slate-700 mb-2">Causes (One per line)</label>
                  <textarea rows={5} value={formCauses} onChange={(e) => setFormCauses(e.target.value)}
                    className="w-full px-4 py-2 rounded-lg border border-slate-300" placeholder="- High humidity..." />
                </div>
              </div>

              {/* Treatments Section */}
              <div className="border-t border-slate-100 pt-6">
                <div className="flex justify-between items-center mb-4">
                    <label className="text-lg font-bold text-slate-800">Treatments</label>
                    <button onClick={addTreatment} className="text-sm bg-green-50 text-green-700 px-3 py-1 rounded-lg font-bold hover:bg-green-100 flex items-center gap-1">
                        <Plus size={14}/> Add Treatment
                    </button>
                </div>

                <div className="space-y-4">
                    {formTreatments.map((t, i) => (
                        <div key={i} className="p-4 bg-slate-50 rounded-xl border border-slate-200 relative group">
                            <button onClick={() => removeTreatment(i)} className="absolute top-2 right-2 text-slate-400 hover:text-red-500"><X size={16} /></button>
                            
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-3">
                                <div>
                                    <label className="text-xs font-bold text-slate-500 uppercase">Type</label>
                                    <select value={t.type} onChange={(e) => updateTreatment(i, 'type', e.target.value)}
                                        className="w-full p-2 rounded border border-slate-300 text-sm mt-1">
                                        <option value="Organic">Organic</option>
                                        <option value="Chemical">Chemical</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="text-xs font-bold text-slate-500 uppercase">Title</label>
                                    <input type="text" value={t.title} onChange={(e) => updateTreatment(i, 'title', e.target.value)}
                                        className="w-full p-2 rounded border border-slate-300 text-sm mt-1" placeholder="e.g. Neem Oil" />
                                </div>
                            </div>
                            <div className="mb-3">
                                <label className="text-xs font-bold text-slate-500 uppercase">Instructions</label>
                                <input type="text" value={t.instruction} onChange={(e) => updateTreatment(i, 'instruction', e.target.value)}
                                    className="w-full p-2 rounded border border-slate-300 text-sm mt-1" placeholder="e.g. Spray in evening" />
                            </div>
                            <div>
                                <label className="text-xs font-bold text-slate-500 uppercase">Safety Tip</label>
                                <input type="text" value={t.safety_tip} onChange={(e) => updateTreatment(i, 'safety_tip', e.target.value)}
                                    className="w-full p-2 rounded border border-slate-300 text-sm mt-1 text-red-600" placeholder="e.g. Wear gloves" />
                            </div>
                        </div>
                    ))}
                    {formTreatments.length === 0 && <p className="text-slate-400 text-center italic text-sm">No treatments added yet.</p>}
                </div>
              </div>
            </div>

            <div className="p-6 border-t border-slate-100 bg-slate-50 flex justify-end gap-3">
              <button onClick={() => setIsEditing(false)} className="px-4 py-2 text-slate-600 font-medium hover:bg-slate-200 rounded-lg">Cancel</button>
              <button onClick={handleSave} className="flex items-center gap-2 bg-amber-600 text-white px-6 py-2 rounded-lg hover:bg-amber-700 font-bold shadow-sm">
                <Save size={18} /> Save Changes
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
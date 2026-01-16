'use client';
import { useState } from 'react';
import { FileText, UploadCloud, CheckCircle, AlertTriangle, Book, Loader2 } from 'lucide-react';

export default function RAGUploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [category, setCategory] = useState("General");
  const [isUploading, setIsUploading] = useState(false);
  const [status, setStatus] = useState<{ type: 'success' | 'error' | null; msg: string }>({ type: null, msg: '' });

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selected = e.target.files[0];
      if (selected.type !== 'application/pdf') {
        setStatus({ type: 'error', msg: 'Only PDF files are allowed.' });
        return;
      }
      setFile(selected);
      setStatus({ type: null, msg: '' });
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setIsUploading(true);
    setStatus({ type: null, msg: '' });

    const formData = new FormData();
    formData.append('file', file);
    formData.append('category', category);

    try {
      const res = await fetch('http://localhost:8000/upload_book', {
        method: 'POST',
        body: formData,
      });

      const data = await res.json();

      if (res.ok) {
        setStatus({ type: 'success', msg: data.message });
        setFile(null); // Clear file after success
      } else {
        setStatus({ type: 'error', msg: data.detail || 'Upload failed' });
      }
    } catch (error) {
      setStatus({ type: 'error', msg: 'Server connection failed' });
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900 flex items-center gap-3">
          <div className="p-2 bg-indigo-100 text-indigo-600 rounded-lg">
            <Book size={32} />
          </div>
          ChatBot Training Center
        </h1>
        <p className="text-slate-500 mt-2 ml-14">
          Upload official PDF manuals to train the Chatbot. The AI will read, chunk, and memorize these documents.
        </p>
      </header>

      {/* --- UPLOAD CARD --- */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-8">
        <h2 className="text-xl font-bold text-slate-800 mb-6">Upload New Manual</h2>

        <div className="space-y-6">
          
          {/* 1. Category Input */}
          <div>
            <label className="block text-sm font-bold text-slate-700 mb-2">Category</label>
            <select 
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full md:w-1/2 px-4 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-indigo-500"
            >
              <option value="General">General Guide</option>
              <option value="Disease Control">Disease Control</option>
              <option value="Fertilizer">Fertilizer Guidelines</option>
              <option value="Harvesting">Harvesting Standards</option>
            </select>
          </div>

          {/* 2. Drag & Drop Zone */}
          <div className={`border-2 border-dashed rounded-xl p-10 flex flex-col items-center justify-center text-center transition-colors
            ${file ? 'border-indigo-500 bg-indigo-50' : 'border-slate-300 hover:border-indigo-400 hover:bg-slate-50'}`}>
            
            <input 
              type="file" 
              accept="application/pdf"
              onChange={handleFileChange} 
              className="hidden" 
              id="file-upload"
            />
            
            <label htmlFor="file-upload" className="cursor-pointer flex flex-col items-center">
              {file ? (
                <>
                  <FileText size={48} className="text-indigo-600 mb-4" />
                  <p className="text-lg font-bold text-indigo-900">{file.name}</p>
                  <p className="text-sm text-indigo-600 mt-1">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                  <p className="text-xs text-indigo-400 mt-4 font-semibold">Click to change file</p>
                </>
              ) : (
                <>
                  <UploadCloud size={48} className="text-slate-400 mb-4" />
                  <p className="text-lg font-bold text-slate-700">Click to upload PDF</p>
                  <p className="text-sm text-slate-400 mt-1">or drag and drop here</p>
                </>
              )}
            </label>
          </div>

          {/* 3. Action Buttons */}
          <div className="flex justify-end pt-4">
            <button
              onClick={handleUpload}
              disabled={!file || isUploading}
              className={`flex items-center gap-2 px-8 py-3 rounded-lg font-bold shadow-md transition-all
                ${!file || isUploading 
                  ? 'bg-slate-100 text-slate-400 cursor-not-allowed' 
                  : 'bg-indigo-600 text-white hover:bg-indigo-700 hover:shadow-lg'}`}
            >
              {isUploading ? (
                <>
                  <Loader2 size={20} className="animate-spin" /> Processing PDF...
                </>
              ) : (
                <>
                  <UploadCloud size={20} /> Start Ingestion
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* --- STATUS MESSAGES --- */}
      {status.msg && (
        <div className={`mt-6 p-4 rounded-xl flex items-start gap-3 border ${
          status.type === 'success' ? 'bg-green-50 border-green-200 text-green-800' : 'bg-red-50 border-red-200 text-red-800'
        }`}>
          {status.type === 'success' ? <CheckCircle size={24} /> : <AlertTriangle size={24} />}
          <div>
            <p className="font-bold">{status.type === 'success' ? 'Ingestion Complete!' : 'Upload Failed'}</p>
            <p className="text-sm opacity-90">{status.msg}</p>
          </div>
        </div>
      )}
    </div>
  );
}
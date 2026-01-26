'use client';
import { useState } from 'react';
import axios from 'axios';
import { Megaphone, Send, AlertCircle, CheckCircle2, Loader2 } from 'lucide-react';

export default function AnnouncementPage() {
  const [formData, setFormData] = useState({ title: '', message: '' });
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [statusMsg, setStatusMsg] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setStatus('loading');
    setStatusMsg('');

    try {
      // 1. Send to Backend
      await axios.post('http://127.0.0.1:8000/api/admin/announce', formData);
      
      // 2. Success Feedback
      setStatus('success');
      setStatusMsg('Announcement broadcasted to all users successfully.');
      setFormData({ title: '', message: '' }); // Clear form
      
      // Reset status after 3 seconds
      setTimeout(() => setStatus('idle'), 3000);

    } catch (err: any) {
      setStatus('error');
      setStatusMsg('Failed to send announcement. Is the server running?');
      console.error(err);
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-3">
          <div className="p-3 bg-indigo-100 text-indigo-600 rounded-xl">
            <Megaphone size={24} />
          </div>
          Global Announcements
        </h1>
        <p className="text-slate-500 mt-2 ml-14">
          Send push notifications and alerts to all registered Farmers, Experts, and Researchers.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* LEFT: FORM */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
            <form onSubmit={handleSubmit} className="space-y-6">
              
              {/* Title Input */}
              <div>
                <label className="block text-sm font-bold text-slate-700 mb-2">
                  Announcement Title
                </label>
                <input
                  type="text"
                  required
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  placeholder="e.g., Heavy Rain Alert: All Estates"
                  className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition"
                />
              </div>

              {/* Message Input */}
              <div>
                <label className="block text-sm font-bold text-slate-700 mb-2">
                  Message Content
                </label>
                <textarea
                  required
                  rows={5}
                  value={formData.message}
                  onChange={(e) => setFormData({ ...formData, message: e.target.value })}
                  placeholder="Type your message here..."
                  className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition resize-none"
                />
              </div>

              {/* Submit Button */}
              <div className="pt-2">
                <button
                  type="submit"
                  disabled={status === 'loading'}
                  className="w-full flex items-center justify-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-3 px-6 rounded-xl transition disabled:opacity-70 disabled:cursor-not-allowed"
                >
                  {status === 'loading' ? (
                    <>
                      <Loader2 size={20} className="animate-spin" /> Sending...
                    </>
                  ) : (
                    <>
                      <Send size={20} /> Broadcast Now
                    </>
                  )}
                </button>
              </div>

              {/* Status Messages */}
              {status === 'success' && (
                <div className="p-4 bg-green-50 text-green-700 rounded-xl flex items-center gap-3 border border-green-100 animate-in fade-in slide-in-from-bottom-2">
                  <CheckCircle2 size={20} />
                  <span className="font-medium">{statusMsg}</span>
                </div>
              )}

              {status === 'error' && (
                <div className="p-4 bg-red-50 text-red-700 rounded-xl flex items-center gap-3 border border-red-100 animate-in fade-in slide-in-from-bottom-2">
                  <AlertCircle size={20} />
                  <span className="font-medium">{statusMsg}</span>
                </div>
              )}
            </form>
          </div>
        </div>

        {/* RIGHT: PREVIEW / TIPS */}
        <div className="space-y-6">
          <div className="bg-slate-50 rounded-2xl border border-slate-200 p-6">
            <h3 className="font-bold text-slate-800 mb-4 text-sm uppercase tracking-wide">Preview</h3>
            
            {/* Notification Preview Card */}
            <div className="bg-white p-4 rounded-xl shadow-sm border border-slate-100">
              <div className="flex gap-3">
                <div className="h-10 w-10 bg-indigo-100 text-indigo-600 rounded-full flex items-center justify-center flex-shrink-0">
                  <Megaphone size={18} />
                </div>
                <div>
                  <h4 className="font-bold text-slate-900 text-sm">
                    {formData.title || "Announcement Title"}
                  </h4>
                  <p className="text-slate-500 text-xs mt-1 leading-relaxed">
                    {formData.message || "Your message content will appear here exactly as the user sees it."}
                  </p>
                  <span className="text-[10px] text-slate-400 mt-2 block">Just now</span>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-blue-50 rounded-2xl border border-blue-100 p-6">
            <h3 className="font-bold text-blue-800 mb-2 text-sm flex items-center gap-2">
              <AlertCircle size={16} /> Best Practices
            </h3>
            <ul className="text-xs text-blue-700 space-y-2 list-disc ml-4">
              <li>Keep titles short and urgent (e.g., "Meeting Alert", "System Update").</li>
              <li>Avoid sending more than one global alert per day to prevent user fatigue.</li>
              <li>This message will appear in the <b>Notifications</b> tab for all 2,000+ users.</li>
            </ul>
          </div>
        </div>

      </div>
    </div>
  );
}
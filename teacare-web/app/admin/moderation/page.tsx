'use client';
import { useState, useEffect } from 'react';
import { ShieldAlert, Trash2, CheckCircle, MessageSquare, AlertTriangle, ExternalLink } from 'lucide-react';

interface ReportedPost {
  post: {
    post_id: number;
    title: string;
    content: string;
    author_name: string;
    image_url: string | null;
    timestamp: string;
  };
  report_count: number;
  reasons: string[];
}

export default function ModerationPage() {
  const [reports, setReports] = useState<ReportedPost[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchReports = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/admin/reports');
      if (res.ok) setReports(await res.json());
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, []);

  const handleDelete = async (postId: number) => {
    if (!confirm('Are you sure? This will permanently delete the post.')) return;
    
    await fetch(`http://localhost:8000/api/admin/posts/${postId}`, { method: 'DELETE' });
    // Remove from UI
    setReports(reports.filter(r => r.post.post_id !== postId));
  };

  const handleDismiss = async (postId: number) => {
    await fetch(`http://localhost:8000/api/admin/posts/${postId}/dismiss`, { method: 'POST' });
    // Remove from UI
    setReports(reports.filter(r => r.post.post_id !== postId));
  };

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900 flex items-center gap-3">
          <div className="p-2 bg-red-100 text-red-600 rounded-lg"><ShieldAlert size={32} /></div>
          Forum Moderation
        </h1>
        <p className="text-slate-500 mt-2 ml-14">Review posts flagged by users for spam or inappropriate content.</p>
      </header>

      {loading ? (
        <div className="text-center py-12 text-slate-400">Loading reports...</div>
      ) : reports.length === 0 ? (
        <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center">
          <div className="bg-green-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
            <CheckCircle className="text-green-600" size={32} />
          </div>
          <h3 className="text-lg font-bold text-slate-800">All Clear!</h3>
          <p className="text-slate-500 mt-2">There are no reported posts pending review.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-6">
          {reports.map((item) => (
            <div key={item.post.post_id} className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden flex flex-col md:flex-row">
              
              {/* Report Stats (Left Side) */}
              <div className="bg-red-50 p-6 md:w-64 flex flex-col justify-center border-r border-red-100">
                <div className="flex items-center gap-2 text-red-700 font-bold mb-2">
                  <AlertTriangle size={20} />
                  <span>{item.report_count} Reports</span>
                </div>
                <div className="text-xs text-red-600/80 uppercase font-bold tracking-wider mb-2">Reasons:</div>
                <div className="flex flex-wrap gap-2">
                  {item.reasons.map((reason, i) => (
                    <span key={i} className="px-2 py-1 bg-white text-red-600 text-xs rounded border border-red-100">
                      {reason}
                    </span>
                  ))}
                </div>
              </div>

              {/* Post Content (Middle) */}
              <div className="p-6 flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-xs font-bold bg-slate-100 text-slate-600 px-2 py-1 rounded">
                    @{item.post.author_name}
                  </span>
                  <span className="text-xs text-slate-400">{item.post.timestamp}</span>
                </div>
                
                <h3 className="text-lg font-bold text-slate-900 mb-2">{item.post.title}</h3>
                <p className="text-slate-600 text-sm mb-4 line-clamp-2">{item.post.content}</p>

                {item.post.image_url && (
                  <div className="flex items-center gap-2 text-xs text-blue-600 font-medium cursor-pointer">
                     <ExternalLink size={12} /> View Attached Image
                  </div>
                )}
              </div>

              {/* Actions (Right Side) */}
              <div className="p-6 bg-slate-50 border-l border-slate-100 flex flex-col justify-center gap-3 md:w-48">
                <button 
                  onClick={() => handleDelete(item.post.post_id)}
                  className="flex items-center justify-center gap-2 w-full py-2 bg-white border border-red-200 text-red-600 rounded-lg hover:bg-red-50 font-medium transition-colors shadow-sm"
                >
                  <Trash2 size={16} /> Delete Post
                </button>
                <button 
                  onClick={() => handleDismiss(item.post.post_id)}
                  className="flex items-center justify-center gap-2 w-full py-2 bg-white border border-slate-200 text-slate-600 rounded-lg hover:bg-slate-100 font-medium transition-colors"
                >
                  <CheckCircle size={16} /> Keep Post
                </button>
              </div>

            </div>
          ))}
        </div>
      )}
    </div>
  );
}
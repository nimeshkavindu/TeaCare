'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import axios from 'axios';
import Cookies from 'js-cookie'; 
import { Lock, Mail, AlertCircle, Sprout } from 'lucide-react';

export default function LoginPage() {
  const router = useRouter();
  const [formData, setFormData] = useState({ identifier: '', secret: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      // 1. Call Python Backend
      const res = await axios.post('http://127.0.0.1:8000/login', {
        identifier: formData.identifier,
        secret: formData.secret
      });

      const { role, user_id, name } = res.data;

      // 2. Set Cookies 
      // We set them to expire in 1 day
      Cookies.set('token', 'valid-session', { expires: 1 }); 
      Cookies.set('role', role, { expires: 1 });
      Cookies.set('user_id', user_id, { expires: 1 });
      Cookies.set('user_name', name, { expires: 1 });

      // 3. Redirect based on Role
      if (role === 'admin') {
        router.push('/admin');
      } else if (role === 'researcher') {
        router.push('/dashboard');
      } else {
        setError('Farmers must use the mobile app.');
        Cookies.remove('token'); 
      }

    } catch (err) {
      setError('Invalid credentials. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50">
      <div className="bg-white p-8 rounded-2xl shadow-xl w-full max-w-md border border-slate-100">
        
        {/* Header */}
        <div className="text-center mb-8">
          <div className="bg-green-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
            <Sprout className="text-green-600" size={32} />
          </div>
          <h1 className="text-2xl font-bold text-slate-800">TeaCare Portal</h1>
          <p className="text-slate-500 text-sm">Authorized Personnel Only</p>
        </div>

        {/* Form */}
        <form onSubmit={handleLogin} className="space-y-6">
          {error && (
            <div className="p-3 bg-red-50 text-red-600 text-sm rounded-lg flex items-center gap-2">
              <AlertCircle size={16} /> {error}
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Email / ID</label>
            <div className="relative">
              <Mail className="absolute left-3 top-3 text-slate-400" size={18} />
              <input
                type="text"
                required
                className="w-full pl-10 pr-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 outline-none transition text-slate-900"
                placeholder="researcher@teacare.com"
                onChange={(e) => setFormData({...formData, identifier: e.target.value})}
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Password</label>
            <div className="relative">
              <Lock className="absolute left-3 top-3 text-slate-400" size={18} />
              <input
                type="password"
                required
                className="w-full pl-10 pr-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 outline-none transition text-slate-900"
                placeholder="••••••••"
                onChange={(e) => setFormData({...formData, secret: e.target.value})}
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-green-700 hover:bg-green-800 text-white font-bold py-3 rounded-lg transition disabled:opacity-50 flex justify-center items-center"
          >
            {loading ? 'Verifying...' : 'Sign In'}
          </button>
        </form>
        
        <div className="mt-6 text-center">
            <Link href="/register" className="text-sm text-green-600 hover:underline">
                Register As a Researcher
            </Link>
        </div>
      </div>
    </div>
  );
}
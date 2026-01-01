'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import axios from 'axios';
import { User, Mail, Lock, CheckCircle, AlertCircle, Sprout, ArrowLeft } from 'lucide-react';

export default function RegisterPage() {
  const router = useRouter();
  
  // Form State
  const [formData, setFormData] = useState({
    fullName: '',
    email: '',
    password: '',
    confirmPassword: ''
  });
  
  // UI State
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [errorMsg, setErrorMsg] = useState('');

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // 1. Client-side Validation
    if (formData.password !== formData.confirmPassword) {
      setStatus('error');
      setErrorMsg("Passwords do not match.");
      return;
    }
    if (formData.password.length < 6) {
      setStatus('error');
      setErrorMsg("Password must be at least 6 characters.");
      return;
    }

    setStatus('loading');
    setErrorMsg('');

    try {
      // 2. Prepare Payload for Backend
      // Matches your UserRegister Pydantic model
      const payload = {
        full_name: formData.fullName,
        contact_type: "email",       // Web users always use email
        contact_value: formData.email,
        secret: formData.password,
        role: "researcher"           // Auto-assign role
      };

      // 3. Send Request
      await axios.post('http://127.0.0.1:8000/register', payload);

      // 4. Success Handling
      setStatus('success');
      setTimeout(() => router.push('/login'), 2000); // Redirect after 2s

    } catch (err: any) {
      setStatus('error');
      // Extract error message from FastAPI response
      const serverError = err.response?.data?.detail || "Registration failed. Please try again.";
      setErrorMsg(serverError);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      
      {/* Back to Login Link */}
      <div className="sm:mx-auto sm:w-full sm:max-w-md mb-6">
        <Link href="/login" className="flex items-center gap-2 text-sm text-slate-500 hover:text-green-600 transition">
            <ArrowLeft size={16} /> Back to Login
        </Link>
      </div>

      {/* Header */}
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <div className="bg-green-100 w-12 h-12 rounded-xl flex items-center justify-center mx-auto mb-4">
            <Sprout className="text-green-600" size={24} />
        </div>
        <h2 className="text-3xl font-bold text-slate-900">
          Researcher Registration
        </h2>
        <p className="mt-2 text-sm text-slate-600">
          Join the TeaCare scientific community
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-10 shadow-xl shadow-slate-200/50 sm:rounded-2xl border border-slate-100">
          
          {status === 'success' ? (
            <div className="text-center py-10 animate-in zoom-in duration-300">
              <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-green-100 mb-4">
                <CheckCircle className="h-8 w-8 text-green-600" />
              </div>
              <h3 className="text-xl font-bold text-slate-900">Account Created!</h3>
              <p className="mt-2 text-sm text-slate-500">Redirecting you to the login page...</p>
            </div>
          ) : (
            <form className="space-y-6" onSubmit={handleRegister}>
              
              {/* Error Alert */}
              {status === 'error' && (
                <div className="bg-red-50 border border-red-100 rounded-lg p-3 flex items-start gap-3">
                  <AlertCircle className="text-red-600 mt-0.5" size={18} />
                  <p className="text-sm text-red-600">{errorMsg}</p>
                </div>
              )}

              {/* Full Name */}
              <div>
                <label className="block text-sm font-medium text-slate-700">Full Name</label>
                <div className="mt-1 relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <User className="h-5 w-5 text-slate-400" />
                  </div>
                  <input
                    type="text"
                    required
                    className="block w-full pl-10 border-slate-300 rounded-lg focus:ring-green-500 focus:border-green-500 p-2.5 border text-slate-900 sm:text-sm transition"
                    placeholder="Dr. Kamal Perera"
                    onChange={(e) => setFormData({...formData, fullName: e.target.value})}
                  />
                </div>
              </div>

              {/* Email */}
              <div>
                <label className="block text-sm font-medium text-slate-700">Institutional Email</label>
                <div className="mt-1 relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <Mail className="h-5 w-5 text-slate-400" />
                  </div>
                  <input
                    type="email"
                    required
                    className="block w-full pl-10 border-slate-300 rounded-lg focus:ring-green-500 focus:border-green-500 p-2.5 border text-slate-900 sm:text-sm transition"
                    placeholder="research@tri.lk"
                    onChange={(e) => setFormData({...formData, email: e.target.value})}
                  />
                </div>
              </div>

              {/* Password */}
              <div>
                <label className="block text-sm font-medium text-slate-700">Password</label>
                <div className="mt-1 relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <Lock className="h-5 w-5 text-slate-400" />
                  </div>
                  <input
                    type="password"
                    required
                    className="block w-full pl-10 border-slate-300 rounded-lg focus:ring-green-500 focus:border-green-500 p-2.5 border text-slate-900 sm:text-sm transition"
                    placeholder="••••••••"
                    onChange={(e) => setFormData({...formData, password: e.target.value})}
                  />
                </div>
              </div>

              {/* Confirm Password */}
              <div>
                <label className="block text-sm font-medium text-slate-700">Confirm Password</label>
                <div className="mt-1 relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <Lock className="h-5 w-5 text-slate-400" />
                  </div>
                  <input
                    type="password"
                    required
                    className="block w-full pl-10 border-slate-300 rounded-lg focus:ring-green-500 focus:border-green-500 p-2.5 border text-slate-900 sm:text-sm transition"
                    placeholder="••••••••"
                    onChange={(e) => setFormData({...formData, confirmPassword: e.target.value})}
                  />
                </div>
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={status === 'loading'}
                className="w-full flex justify-center py-3 px-4 border border-transparent rounded-lg shadow-sm text-sm font-bold text-white bg-green-700 hover:bg-green-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-70 disabled:cursor-not-allowed transition-all"
              >
                {status === 'loading' ? 'Creating Account...' : 'Register'}
              </button>
            </form>
          )}

          {/* Footer Link */}
          {status !== 'success' && (
            <div className="mt-6">
                <div className="relative">
                    <div className="absolute inset-0 flex items-center">
                        <div className="w-full border-t border-slate-200" />
                    </div>
                    <div className="relative flex justify-center text-sm">
                        <span className="px-2 bg-white text-slate-500">Already registered?</span>
                    </div>
                </div>
                <div className="mt-6 text-center">
                    <Link href="/login" className="font-medium text-green-700 hover:text-green-600 transition">
                        Sign in to your account
                    </Link>
                </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
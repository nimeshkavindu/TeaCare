'use client';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import Cookies from 'js-cookie';
import { 
  LayoutDashboard, 
  Users, 
  ShieldAlert, 
  BookOpen, 
  LogOut, 
  Sprout,
  ScrollText,
  Bot,
  ClipboardList
} from 'lucide-react';

// Update the menu items array
const adminLinks = [
  { href: '/admin', label: 'System Health', icon: LayoutDashboard },
  { href: '/admin/users', label: 'User Management', icon: Users },
  { href: '/admin/moderation', label: 'Forum Moderation', icon: ShieldAlert },
  { href: '/admin/knowledge', label: 'Knowledge Base', icon: BookOpen },
  { href: '/admin/logs', label: 'Activity Logs', icon: ScrollText }, 
  { href: '/admin/rag', label: 'Chatbot Training', icon: Bot },
  { href: '/admin/reports', label: 'Disease Reports', icon: ClipboardList },
];

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();

const handleLogout = () => {
    // Remove all session cookies
    Cookies.remove('token');
    Cookies.remove('role');
    Cookies.remove('user_id');
    Cookies.remove('user_name');

    // Redirect to Login Page
    router.push('/login');
  };

  return (
    <div className="flex h-screen bg-slate-50">
      
      {/* --- SIDEBAR --- */}
      <aside className="w-64 bg-slate-900 text-slate-100 flex flex-col shadow-xl z-10 fixed h-full">
        <div className="p-6 border-b border-slate-800 flex items-center gap-3">
          <div className="bg-green-600 p-2 rounded-lg">
            <Sprout size={24} className="text-white" />
          </div>
          <div>
            <h1 className="font-bold text-lg tracking-wide">TeaCare</h1>
            <p className="text-xs text-slate-400 uppercase tracking-wider">Admin Console</p>
          </div>
        </div>

        <nav className="flex-1 px-4 py-6 space-y-2">
          {adminLinks.map((link) => {
            const Icon = link.icon;
            const isActive = pathname === link.href;
            
            return (
              <Link 
                key={link.href} 
                href={link.href}
                className={`
                  flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 group
                  ${isActive 
                    ? 'bg-green-600 text-white shadow-lg shadow-green-900/20' 
                    : 'text-slate-400 hover:bg-slate-800 hover:text-white'}
                `}
              >
                <Icon size={20} className={isActive ? 'animate-pulse' : ''} />
                <span className="font-medium text-sm">{link.label}</span>
              </Link>
            );
          })}
        </nav>

        <div className="p-4 border-t border-slate-800">
          <button 
              onClick={handleLogout}
              className="flex items-center gap-3 w-full px-4 py-3 text-slate-400 hover:text-red-400 hover:bg-red-950/30 rounded-xl transition-all">
            <LogOut size={20} />
            <span className="font-medium text-sm">Sign Out</span>
          </button>
        </div>
      </aside>

      <main className="flex-1 ml-64 p-8 overflow-y-auto h-full">
        <div className="max-w-6xl mx-auto animate-in fade-in slide-in-from-bottom-4 duration-500">
          {children}
        </div>
      </main>
      
    </div>
  );
}
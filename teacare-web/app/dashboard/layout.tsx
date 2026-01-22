'use client';
import { useState, useEffect } from 'react'; // <--- Added imports
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  LayoutDashboard, 
  Microscope, 
  Map as MapIcon, 
  LineChart, 
  BookOpen, 
  LogOut, 
  Sprout,
  FileText,
  Book,
} from 'lucide-react';
import Cookies from 'js-cookie';
import { useRouter } from 'next/navigation';

const researchLinks = [
  { href: '/dashboard', label: 'Overview', icon: LayoutDashboard },
  { href: '/dashboard/lab', label: 'Leaf Scanner', icon: Microscope },
  { href: '/dashboard/reports', label: 'Disease Reports', icon: FileText },
  { href: '/dashboard/map', label: 'Epidemiology Map', icon: MapIcon },
  { href: '/dashboard/analytics', label: 'Temporal Analytics', icon: LineChart },
  { href: '/dashboard/library', label: 'Pathogen Library', icon: Book },
];

export default function ResearcherLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  
  // --- NEW: User Name State ---
  const [userName, setUserName] = useState('Researcher'); 

  // --- NEW: Load Name from Cookie ---
  useEffect(() => {
    const storedName = Cookies.get('user_name');
    if (storedName) {
      setUserName(storedName);
    }
  }, []);

  const handleLogout = () => {
    // Clear all auth cookies
    Cookies.remove('token');
    Cookies.remove('role');
    Cookies.remove('user_id');
    Cookies.remove('user_name');
    router.push('/login');
  };

  return (
    <div className="flex h-screen bg-slate-50">
      
      {/* Sidebar */}
      <aside className="w-64 bg-green-900 text-slate-100 flex flex-col fixed h-full z-40 shadow-xl">
        {/* Brand */}
        <div className="p-6 border-b border-green-800 flex items-center gap-3">
          <div className="bg-white p-2 rounded-lg">
            <Sprout size={24} className="text-green-800" />
          </div>
          <div>
            <h1 className="font-bold text-lg tracking-wide text-white">TeaCare</h1>
            <p className="text-xs text-green-200 uppercase tracking-wider">Research Lab</p>
          </div>
        </div>

        {/* Nav Links */}
        <nav className="flex-1 px-4 py-6 space-y-2">
          {researchLinks.map((link) => {
            const Icon = link.icon;
            const isActive = pathname === link.href;
            
            return (
              <Link 
                key={link.href} 
                href={link.href}
                className={`
                  flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 group
                  ${isActive 
                    ? 'bg-white text-green-900 shadow-lg' 
                    : 'text-green-100 hover:bg-green-800 hover:text-white'}
                `}
              >
                <Icon size={20} />
                <span className="font-medium text-sm">{link.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* User Profile & Logout */}
        <div className="p-4 border-t border-green-800 bg-green-950/30">
          <div className="flex items-center gap-3 mb-4 px-2">
             {/* Dynamic Initials */}
             <div className="w-8 h-8 rounded-full bg-green-700 flex items-center justify-center text-xs font-bold ring-2 ring-green-600">
               {userName.charAt(0).toUpperCase()}
             </div>
             
             {/* Dynamic Name */}
             <div className="overflow-hidden">
                <p className="text-sm font-medium text-white truncate w-32" title={userName}>
                    {userName}
                </p>
                <p className="text-xs text-green-300">Logged In</p>
             </div>
          </div>
          
          <button 
            onClick={handleLogout}
            className="flex items-center gap-3 w-full px-4 py-2 text-green-200 hover:text-white hover:bg-red-500/20 rounded-lg transition-all text-sm"
          >
            <LogOut size={18} />
            <span>Sign Out</span>
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 ml-64 p-8 overflow-y-auto h-full z-0 relative">
        <div className="max-w-7xl mx-auto animate-in fade-in slide-in-from-bottom-4 duration-500">
          {children}
        </div>
      </main>
      
    </div>
  );
}
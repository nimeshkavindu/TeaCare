'use client';
import { useState, useEffect } from 'react';
import { Search, Trash2, Shield, Sprout, FlaskConical, GraduationCap, Ban, CheckCircle } from 'lucide-react';

interface User {
  user_id: number;
  full_name: string;
  email: string | null;
  phone_number: string | null;
  role: string;
  is_active: boolean;  
  last_login: string | null; 
}

export default function UserManagement() {
  const [users, setUsers] = useState<User[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);

  const fetchUsers = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/users');
      if (res.ok) setUsers(await res.json());
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchUsers(); }, []);

  // Handle Ban/Unban
  const toggleStatus = async (id: number, currentStatus: boolean) => {
    const action = currentStatus ? 'Ban' : 'Activate';
    if (!confirm(`Are you sure you want to ${action} this user?`)) return;

    await fetch(`http://localhost:8000/api/users/${id}/status`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ is_active: !currentStatus })
    });
    fetchUsers();
  };

  const handleRoleChange = async (id: number, newRole: string) => {
    await fetch(`http://localhost:8000/api/users/${id}/role`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ role: newRole })
    });
    fetchUsers();
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Permanently delete user?')) return;
    await fetch(`http://localhost:8000/api/users/${id}`, { method: 'DELETE' });
    setUsers(users.filter(u => u.user_id !== id));
  };

  const filteredUsers = users.filter(user => 
    user.full_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (user.email && user.email.includes(searchTerm))
  );

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <header className="mb-8 flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">User Management</h1>
          <p className="text-slate-500 mt-1">Manage farmers, experts, researchers, and admins.</p>
        </div>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
          <input 
            type="text" 
            placeholder="Search users..." 
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10 pr-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500/20 w-64"
          />
        </div>
      </header>

      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <table className="w-full text-left text-sm text-slate-600">
          <thead className="bg-slate-50 border-b border-slate-100 text-xs uppercase font-semibold text-slate-500">
            <tr>
              <th className="px-6 py-4">User</th>
              <th className="px-6 py-4">Role</th>
              <th className="px-6 py-4">Status</th>
              <th className="px-6 py-4">Last Active</th>
              <th className="px-6 py-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {filteredUsers.map((user) => (
              <tr key={user.user_id} className={`hover:bg-slate-50/50 transition-colors ${!user.is_active ? 'bg-red-50/30' : ''}`}>
                <td className="px-6 py-4">
                  <div className="flex items-center gap-3">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white font-bold text-xs ${user.is_active ? 'bg-slate-400' : 'bg-red-300'}`}>
                      {user.full_name[0]}
                    </div>
                    <div>
                      <div className="font-medium text-slate-900">{user.full_name}</div>
                      <div className="text-xs text-slate-400 font-mono">{user.email || user.phone_number}</div>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4">
                  <RoleBadge role={user.role} />
                </td>
                <td className="px-6 py-4">
                  {user.is_active ? (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-green-100 text-green-700">
                      Active
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-red-100 text-red-700">
                      Banned
                    </span>
                  )}
                </td>
                <td className="px-6 py-4 text-xs text-slate-400">
                  {user.last_login || "Never"}
                </td>
                <td className="px-6 py-4 text-right flex justify-end gap-2">
                  {/* Role Dropdown */}
                  <select 
  // Simple handler: No need to manually lowercase anything anymore
  onChange={(e) => handleRoleChange(user.user_id, e.target.value)}
  
  className="text-xs border border-slate-200 rounded px-2 py-1 bg-white cursor-pointer hover:border-green-500"
  
  // Simple value: Directly matches the database (which is now lowercase)
  value={user.role} 
>
  {/* The 'value' is what gets sent to DB (lowercase) */}
  {/* The text inside >...< is what the user SEES (Title Case) */}
  <option value="farmer">Farmer</option>
  <option value="expert">Expert</option>
  <option value="researcher">Researcher</option>
  <option value="admin">Admin</option>
</select>
                  {/* Ban/Unban Button */}
                  <button 
                    onClick={() => toggleStatus(user.user_id, user.is_active)}
                    className={`p-1.5 rounded-lg transition-colors ${user.is_active ? 'text-slate-400 hover:text-amber-600 hover:bg-amber-50' : 'text-green-500 hover:bg-green-50'}`}
                    title={user.is_active ? "Ban User" : "Activate User"}
                  >
                    {user.is_active ? <Ban size={16} /> : <CheckCircle size={16} />}
                  </button>

                  {/* Delete Button */}
                  <button 
                    onClick={() => handleDelete(user.user_id)}
                    className="p-1.5 text-slate-300 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                  >
                    <Trash2 size={16} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// --- UPDATED BADGE COMPONENT ---
function RoleBadge({ role }: { role: string }) {
  const r = role.toLowerCase();
  
  if (r === 'admin') return <Badge color="purple" icon={Shield} label="Admin" />;
  if (r === 'researcher') return <Badge color="blue" icon={FlaskConical} label="Researcher" />;
  if (r === 'expert') return <Badge color="indigo" icon={GraduationCap} label="Expert" />; // New Expert Badge
  return <Badge color="green" icon={Sprout} label="Farmer" />;
}

function Badge({ color, icon: Icon, label }: any) {
  // Tailwind Safe-list hack or just dynamic strings
  const colors: any = {
    purple: "bg-purple-100 text-purple-700 border-purple-200",
    blue: "bg-blue-100 text-blue-700 border-blue-200",
    indigo: "bg-indigo-100 text-indigo-700 border-indigo-200",
    green: "bg-green-100 text-green-700 border-green-200"
  };
  
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold border ${colors[color]}`}>
      <Icon size={12} /> {label}
    </span>
  );
}

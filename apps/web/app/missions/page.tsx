'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import DashboardShell from '@/components/DashboardShell';

export default function MissionsPage() {
  const [missions, setMissions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.missions.list().then(setMissions).finally(() => setLoading(false));
  }, []);

  return (
    <DashboardShell>
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <p className="text-sm text-slate-500">{missions.length} mission{missions.length !== 1 && 's'}</p>
          <button className="px-4 py-2 bg-rosclaw-600 text-white text-sm rounded hover:bg-rosclaw-700">+ New Mission</button>
        </div>
        {loading ? <div className="text-sm text-slate-500">Loading...</div> : missions.length === 0 ? (
          <div className="bg-white rounded-lg border border-slate-200 p-8 text-center"><p className="text-slate-500">No missions yet.</p></div>
        ) : (
          <div className="bg-white rounded-lg border border-slate-200 overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-slate-50 border-b border-slate-200"><tr>
                <th className="text-left px-4 py-3 font-medium text-slate-600">Mission</th>
                <th className="text-left px-4 py-3 font-medium text-slate-600">Robot</th>
                <th className="text-left px-4 py-3 font-medium text-slate-600">Status</th>
                <th className="text-left px-4 py-3 font-medium text-slate-600">Actions</th>
              </tr></thead>
              <tbody>
                {missions.map((m: any) => (
                  <tr key={m.id} className="border-b border-slate-100 hover:bg-slate-50">
                    <td className="px-4 py-3"><Link href={`/missions/${m.id}`} className="text-rosclaw-600 hover:underline font-medium">{m.title}</Link></td>
                    <td className="px-4 py-3 text-slate-500">{m.robot_id}</td>
                    <td className="px-4 py-3"><span className={`px-2 py-0.5 rounded text-xs font-medium ${m.status === 'running' ? 'bg-blue-100 text-blue-800' : m.status === 'completed' ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-100 text-slate-600'}`}>{m.status}</span></td>
                    <td className="px-4 py-3"><div className="flex gap-2">{m.status === 'running' && <button className="px-2 py-1 text-xs bg-amber-100 text-amber-800 rounded">Pause</button>}{(m.status === 'running' || m.status === 'pending') && <button className="px-2 py-1 text-xs bg-red-100 text-red-800 rounded">Abort</button>}</div></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </DashboardShell>
  );
}

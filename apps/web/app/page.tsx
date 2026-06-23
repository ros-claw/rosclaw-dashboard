'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import DashboardShell from '@/components/DashboardShell';
import ModeBadge from '@/components/ModeBadge';

interface SystemStatus {
  overall: string;
  service: string;
  version: string;
  modules: { name: string; status: string; mode: string; message?: string; detail: any }[];
}

export default function RobotRegistryPage() {
  const [robots, setRobots] = useState<any[]>([]);
  const [missions, setMissions] = useState<any[]>([]);
  const [skills, setSkills] = useState<any[]>([]);
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.robots.list(),
      api.missions.list(),
      api.skills.list(),
      api.status.get().catch(() => null),
    ]).then(([r, m, s, st]) => {
      setRobots(r);
      setMissions(m);
      setSkills(s);
      setStatus(st);
      setLoading(false);
    });
  }, []);

  const onlineCount = robots.filter((r: any) => r.status === 'online').length;

  return (
    <DashboardShell>
      <div className="space-y-6">
        {/* System status */}
        {status && (
          <div className="bg-white rounded-lg border border-slate-200 p-4">
            <div className="flex items-center justify-between mb-3">
              <h2 className="font-medium text-slate-800">System Status</h2>
              <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                status.overall === 'healthy' ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'
              }`}>
                {status.overall}
              </span>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
              {status.modules.map((mod) => (
                <div
                  key={mod.name}
                  className="text-xs p-2 bg-slate-50 rounded border border-slate-100"
                  title={mod.message || ''}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-slate-700">{mod.name}</span>
                    <ModeBadge mode={mod.mode} />
                  </div>
                  <div className={mod.status === 'healthy' ? 'text-emerald-600' : 'text-amber-600'}>
                    {mod.status}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Overview stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg border border-slate-200 p-4">
            <p className="text-sm text-slate-500">Robots</p>
            <p className="text-2xl font-bold text-slate-800">{robots.length}</p>
            <p className="text-xs text-emerald-600">{onlineCount} online</p>
          </div>
          <div className="bg-white rounded-lg border border-slate-200 p-4">
            <p className="text-sm text-slate-500">Missions</p>
            <p className="text-2xl font-bold text-slate-800">{missions.length}</p>
            <p className="text-xs text-slate-400">{missions.filter((m: any) => m.status === 'running').length} running</p>
          </div>
          <div className="bg-white rounded-lg border border-slate-200 p-4">
            <p className="text-sm text-slate-500">Skills</p>
            <p className="text-2xl font-bold text-slate-800">{skills.length}</p>
          </div>
          <div className="bg-white rounded-lg border border-slate-200 p-4">
            <p className="text-sm text-slate-500">Status</p>
            <p className="text-2xl font-bold text-emerald-600">Operational</p>
          </div>
        </div>

        <div className="flex items-center justify-between">
          <p className="text-sm text-slate-500">{robots.length} robot{robots.length !== 1 && 's'} registered</p>
          <button className="px-4 py-2 bg-rosclaw-600 text-white text-sm rounded hover:bg-rosclaw-700">+ Import Robot</button>
        </div>
        {loading ? <div className="text-sm text-slate-500">Loading...</div> : robots.length === 0 ? (
          <div className="bg-white rounded-lg border border-slate-200 p-8 text-center">
            <p className="text-slate-500">No robots registered yet.</p>
          </div>
        ) : (
          <div className="bg-white rounded-lg border border-slate-200 overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-slate-50 border-b border-slate-200"><tr>
                <th className="text-left px-4 py-3 font-medium text-slate-600">Robot ID</th>
                <th className="text-left px-4 py-3 font-medium text-slate-600">Name</th>
                <th className="text-left px-4 py-3 font-medium text-slate-600">Model</th>
                <th className="text-left px-4 py-3 font-medium text-slate-600">Status</th>
              </tr></thead>
              <tbody>
                {robots.map((robot: any) => (
                  <tr key={robot.id} className="border-b border-slate-100 hover:bg-slate-50">
                    <td className="px-4 py-3"><Link href={`/robots/${robot.id}`} className="text-rosclaw-600 hover:underline font-medium">{robot.id}</Link></td>
                    <td className="px-4 py-3">{robot.name}</td>
                    <td className="px-4 py-3 text-slate-500">{robot.model}</td>
                    <td className="px-4 py-3"><span className={`px-2 py-0.5 rounded text-xs font-medium ${robot.status === 'online' ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-100 text-slate-600'}`}>{robot.status}</span></td>
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

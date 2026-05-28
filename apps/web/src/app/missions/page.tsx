'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import DashboardShell from '@/components/DashboardShell';

interface Mission {
  id: string;
  robot_id: string;
  agent_id: string | null;
  title: string;
  status: string;
  started_at: string | null;
  ended_at: string | null;
}

export default function MissionsPage() {
  const [missions, setMissions] = useState<Mission[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [newMission, setNewMission] = useState({ id: '', robot_id: '', agent_id: '', title: '' });

  useEffect(() => {
    loadMissions();
  }, []);

  const loadMissions = () => {
    setLoading(true);
    api.missions.list().then(setMissions).finally(() => setLoading(false));
  };

  const statusBadge = (status: string) => {
    const colors: Record<string, string> = {
      pending: 'bg-slate-100 text-slate-600',
      running: 'bg-blue-100 text-blue-800',
      paused: 'bg-amber-100 text-amber-800',
      completed: 'bg-emerald-100 text-emerald-800',
      aborted: 'bg-red-100 text-red-800',
    };
    return (
      <span className={`px-2 py-0.5 rounded text-xs font-medium ${colors[status] || colors.pending}`}>
        {status}
      </span>
    );
  };

  const handleCreate = async () => {
    if (!newMission.id || !newMission.robot_id || !newMission.title) return;
    await api.missions.create(newMission);
    setShowCreate(false);
    setNewMission({ id: '', robot_id: '', agent_id: '', title: '' });
    loadMissions();
  };

  const handlePause = async (id: string) => {
    await api.missions.pause(id);
    loadMissions();
  };

  const handleResume = async (id: string) => {
    await api.missions.resume(id);
    loadMissions();
  };

  const handleAbort = async (id: string) => {
    await api.missions.abort(id);
    loadMissions();
  };

  return (
    <DashboardShell>
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <p className="text-sm text-slate-500">
            {missions.length} mission{missions.length !== 1 && 's'}
          </p>
          <button
            onClick={() => setShowCreate(!showCreate)}
            className="px-4 py-2 bg-rosclaw-600 text-white text-sm rounded hover:bg-rosclaw-700 transition-colors"
          >
            {showCreate ? 'Cancel' : '+ New Mission'}
          </button>
        </div>

        {showCreate && (
          <div className="bg-white rounded-lg border border-slate-200 p-4 space-y-3">
            <h3 className="font-medium">Create Mission</h3>
            <div className="grid grid-cols-4 gap-3">
              <input
                placeholder="Mission ID"
                value={newMission.id}
                onChange={(e) => setNewMission({ ...newMission, id: e.target.value })}
                className="px-3 py-2 border border-slate-200 rounded text-sm"
              />
              <input
                placeholder="Robot ID"
                value={newMission.robot_id}
                onChange={(e) => setNewMission({ ...newMission, robot_id: e.target.value })}
                className="px-3 py-2 border border-slate-200 rounded text-sm"
              />
              <input
                placeholder="Agent ID (optional)"
                value={newMission.agent_id}
                onChange={(e) => setNewMission({ ...newMission, agent_id: e.target.value })}
                className="px-3 py-2 border border-slate-200 rounded text-sm"
              />
              <input
                placeholder="Title"
                value={newMission.title}
                onChange={(e) => setNewMission({ ...newMission, title: e.target.value })}
                className="px-3 py-2 border border-slate-200 rounded text-sm"
              />
            </div>
            <button
              onClick={handleCreate}
              className="px-4 py-2 bg-emerald-600 text-white text-sm rounded hover:bg-emerald-700 transition-colors"
            >
              Create
            </button>
          </div>
        )}

        {loading ? (
          <div className="text-sm text-slate-500">Loading...</div>
        ) : missions.length === 0 ? (
          <div className="bg-white rounded-lg border border-slate-200 p-8 text-center">
            <p className="text-slate-500">No missions yet.</p>
          </div>
        ) : (
          <div className="bg-white rounded-lg border border-slate-200 overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="text-left px-4 py-3 font-medium text-slate-600">Mission</th>
                  <th className="text-left px-4 py-3 font-medium text-slate-600">Robot</th>
                  <th className="text-left px-4 py-3 font-medium text-slate-600">Agent</th>
                  <th className="text-left px-4 py-3 font-medium text-slate-600">Status</th>
                  <th className="text-left px-4 py-3 font-medium text-slate-600">Started</th>
                  <th className="text-left px-4 py-3 font-medium text-slate-600">Actions</th>
                </tr>
              </thead>
              <tbody>
                {missions.map((m) => (
                  <tr key={m.id} className="border-b border-slate-100 hover:bg-slate-50">
                    <td className="px-4 py-3">
                      <Link href={`/missions/${m.id}`} className="text-rosclaw-600 hover:underline font-medium">
                        {m.title}
                      </Link>
                    </td>
                    <td className="px-4 py-3 text-slate-500">{m.robot_id}</td>
                    <td className="px-4 py-3 text-slate-500">{m.agent_id || '-'}</td>
                    <td className="px-4 py-3">{statusBadge(m.status)}</td>
                    <td className="px-4 py-3 text-slate-500">
                      {m.started_at ? new Date(m.started_at).toLocaleString() : '-'}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex gap-2">
                        {m.status === 'running' && (
                          <button
                            onClick={() => handlePause(m.id)}
                            className="px-2 py-1 text-xs bg-amber-100 text-amber-800 rounded hover:bg-amber-200"
                          >
                            Pause
                          </button>
                        )}
                        {m.status === 'paused' && (
                          <button
                            onClick={() => handleResume(m.id)}
                            className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded hover:bg-blue-200"
                          >
                            Resume
                          </button>
                        )}
                        {(m.status === 'running' || m.status === 'paused' || m.status === 'pending') && (
                          <button
                            onClick={() => handleAbort(m.id)}
                            className="px-2 py-1 text-xs bg-red-100 text-red-800 rounded hover:bg-red-200"
                          >
                            Abort
                          </button>
                        )}
                      </div>
                    </td>
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

'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import DashboardShell from '@/components/DashboardShell';

export default function MissionTracePage() {
  const { id } = useParams();
  const [trace, setTrace] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (id) api.missions.trace(id as string).then(setTrace).finally(() => setLoading(false));
  }, [id]);

  return (
    <DashboardShell>
      <div className="space-y-4">
        <Link href="/missions" className="text-sm text-rosclaw-600 hover:underline">← Back to Missions</Link>
        {loading ? <div className="text-sm text-slate-500">Loading...</div> : trace ? (
          <div className="space-y-4">
            <div className="bg-white rounded-lg border border-slate-200 p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold">{trace.mission.title}</h2>
                <span className={`px-2 py-1 rounded text-xs font-medium ${trace.mission.status === 'running' ? 'bg-blue-100 text-blue-800' : 'bg-slate-100 text-slate-600'}`}>{trace.mission.status}</span>
              </div>
              <dl className="grid grid-cols-4 gap-4 text-sm">
                <div><dt className="text-slate-500">Mission ID</dt><dd className="font-medium">{trace.mission.id}</dd></div>
                <div><dt className="text-slate-500">Robot</dt><dd className="font-medium">{trace.mission.robot_id}</dd></div>
                <div><dt className="text-slate-500">Agent</dt><dd className="font-medium">{trace.mission.agent_id || '-'}</dd></div>
                <div><dt className="text-slate-500">Started</dt><dd className="font-medium">{trace.mission.started_at ? new Date(trace.mission.started_at).toLocaleString() : '-'}</dd></div>
              </dl>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-white rounded-lg border border-slate-200 p-4">
                <h3 className="font-medium mb-3">Execution Trace ({trace.events.length} events)</h3>
                {trace.events.length === 0 ? <div className="text-sm text-slate-500">No events recorded.</div> : (
                  <div className="space-y-2">{trace.events.map((e: any) => (
                    <div key={e.id} className="p-2 bg-slate-50 rounded text-sm">
                      <div className="font-medium">{e.event_type}</div>
                      {e.payload_json && <pre className="text-xs text-slate-500 mt-1 bg-white p-1 rounded">{JSON.stringify(JSON.parse(e.payload_json), null, 2)}</pre>}
                    </div>
                  ))}</div>)}
              </div>
              <div className="bg-white rounded-lg border border-slate-200 p-4">
                <h3 className="font-medium mb-3">Skill Runs ({trace.skill_runs.length})</h3>
                {trace.skill_runs.length === 0 ? <div className="text-sm text-slate-500">No skill runs recorded.</div> : (
                  <div className="space-y-2">{trace.skill_runs.map((s: any) => (
                    <div key={s.id} className="flex items-center justify-between p-2 bg-slate-50 rounded text-sm">
                      <div><div className="font-medium">{s.skill_name}</div></div>
                      <span className={`px-2 py-0.5 rounded text-xs font-medium ${s.status === 'running' ? 'bg-blue-100 text-blue-800' : 'bg-slate-100 text-slate-600'}`}>{s.status}</span>
                    </div>
                  ))}</div>)}
              </div>
            </div>
          </div>
        ) : (
          <div className="text-slate-500">Mission not found.</div>
        )}
      </div>
    </DashboardShell>
  );
}

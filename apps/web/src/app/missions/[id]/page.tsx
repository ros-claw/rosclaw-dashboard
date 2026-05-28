'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import DashboardShell from '@/components/DashboardShell';

interface TraceEvent {
  id: string;
  event_type: string;
  payload_json: string | null;
  timestamp: string;
}

interface SkillRun {
  id: string;
  skill_name: string;
  status: string;
  started_at: string | null;
  ended_at: string | null;
}

export default function MissionTracePage() {
  const { id } = useParams();
  const [trace, setTrace] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (id) {
      api.missions.trace(id as string).then(setTrace).finally(() => setLoading(false));
    }
  }, [id]);

  const eventIcon = (type: string) => {
    const icons: Record<string, string> = {
      intent: 'I',
      memory_retrieved: 'M',
      skill_selected: 'S',
      safety_check: 'Sa',
      ros_action: 'R',
      sensor_evidence: 'Se',
      replan: 'Re',
      memory_updated: 'Mu',
      failure: 'F',
      completed: 'C',
    };
    return icons[type] || '?';
  };

  const eventColor = (type: string) => {
    const colors: Record<string, string> = {
      intent: 'bg-blue-100 text-blue-800',
      memory_retrieved: 'bg-purple-100 text-purple-800',
      skill_selected: 'bg-emerald-100 text-emerald-800',
      safety_check: 'bg-amber-100 text-amber-800',
      ros_action: 'bg-rosclaw-100 text-rosclaw-800',
      sensor_evidence: 'bg-cyan-100 text-cyan-800',
      replan: 'bg-orange-100 text-orange-800',
      memory_updated: 'bg-purple-100 text-purple-800',
      failure: 'bg-red-100 text-red-800',
      completed: 'bg-emerald-100 text-emerald-800',
    };
    return colors[type] || 'bg-slate-100 text-slate-600';
  };

  return (
    <DashboardShell>
      <div className="space-y-4">
        <Link href="/missions" className="text-sm text-rosclaw-600 hover:underline">← Back to Missions</Link>

        {loading ? (
          <div className="text-sm text-slate-500">Loading...</div>
        ) : trace ? (
          <div className="space-y-4">
            <div className="bg-white rounded-lg border border-slate-200 p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold">{trace.mission.title}</h2>
                <span className={`px-2 py-1 rounded text-xs font-medium ${
                  trace.mission.status === 'running' ? 'bg-blue-100 text-blue-800' :
                  trace.mission.status === 'completed' ? 'bg-emerald-100 text-emerald-800' :
                  trace.mission.status === 'aborted' ? 'bg-red-100 text-red-800' :
                  'bg-slate-100 text-slate-600'
                }`}>
                  {trace.mission.status}
                </span>
              </div>
              <dl className="grid grid-cols-4 gap-4 text-sm">
                <div>
                  <dt className="text-slate-500">Mission ID</dt>
                  <dd className="font-medium">{trace.mission.id}</dd>
                </div>
                <div>
                  <dt className="text-slate-500">Robot</dt>
                  <dd className="font-medium">{trace.mission.robot_id}</dd>
                </div>
                <div>
                  <dt className="text-slate-500">Agent</dt>
                  <dd className="font-medium">{trace.mission.agent_id || '-'}</dd>
                </div>
                <div>
                  <dt className="text-slate-500">Started</dt>
                  <dd className="font-medium">
                    {trace.mission.started_at ? new Date(trace.mission.started_at).toLocaleString() : '-'}
                  </dd>
                </div>
              </dl>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="bg-white rounded-lg border border-slate-200 p-4">
                <h3 className="font-medium mb-3">Execution Trace ({trace.events.length} events)</h3>
                {trace.events.length === 0 ? (
                  <div className="text-sm text-slate-500">No events recorded.</div>
                ) : (
                  <div className="space-y-2">
                    {trace.events.map((e: TraceEvent, i: number) => (
                      <div key={e.id} className="flex items-start gap-3 p-2 bg-slate-50 rounded">
                        <div className="flex flex-col items-center">
                          <span className={`w-6 h-6 flex items-center justify-center rounded-full text-xs font-bold ${eventColor(e.event_type)}`}>
                            {eventIcon(e.event_type)}
                          </span>
                          {i < trace.events.length - 1 && (
                            <div className="w-px h-4 bg-slate-200 mt-1"></div>
                          )}
                        </div>
                        <div className="flex-1">
                          <div className="text-sm font-medium">{e.event_type}</div>
                          {e.payload_json && (
                            <pre className="text-xs text-slate-500 mt-1 bg-white p-1 rounded">{JSON.stringify(JSON.parse(e.payload_json), null, 2)}</pre>
                          )}
                          <div className="text-xs text-slate-400 mt-1">
                            {new Date(e.timestamp).toLocaleTimeString()}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="bg-white rounded-lg border border-slate-200 p-4">
                <h3 className="font-medium mb-3">Skill Runs ({trace.skill_runs.length})</h3>
                {trace.skill_runs.length === 0 ? (
                  <div className="text-sm text-slate-500">No skill runs recorded.</div>
                ) : (
                  <div className="space-y-2">
                    {trace.skill_runs.map((s: SkillRun) => (
                      <div key={s.id} className="flex items-center justify-between p-2 bg-slate-50 rounded text-sm">
                        <div>
                          <div className="font-medium">{s.skill_name}</div>
                          <div className="text-xs text-slate-500">
                            {s.started_at ? new Date(s.started_at).toLocaleTimeString() : '-'}
                            {s.ended_at && ` → ${new Date(s.ended_at).toLocaleTimeString()}`}
                          </div>
                        </div>
                        <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                          s.status === 'running' ? 'bg-blue-100 text-blue-800' :
                          s.status === 'completed' ? 'bg-emerald-100 text-emerald-800' :
                          s.status === 'failed' ? 'bg-red-100 text-red-800' :
                          'bg-slate-100 text-slate-600'
                        }`}>
                          {s.status}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
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

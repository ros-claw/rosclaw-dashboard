'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import DashboardShell from '@/components/DashboardShell';

interface Episode {
  mission_id: string;
  robot_id: string;
  agent_id: string;
  title: string;
  status: string;
  started_at: string | null;
  ended_at: string | null;
  skill_count: number;
  event_count: number;
  skills: { name: string; status: string }[];
  timeline: { type: string; timestamp: string | null }[];
}

export default function EpisodesPage() {
  const [episodes, setEpisodes] = useState<Episode[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.episodes.list().then((data: any) => {
      setEpisodes(data);
      setLoading(false);
    });
  }, []);

  return (
    <DashboardShell>
      <div className="space-y-4">
        {loading ? (
          <div className="text-sm text-slate-500">Loading episodes...</div>
        ) : episodes.length === 0 ? (
          <div className="bg-white rounded-lg border border-slate-200 p-8 text-center">
            <p className="text-slate-500">No episodes recorded yet.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {episodes.map((ep) => (
              <div key={ep.mission_id} className="bg-white rounded-lg border border-slate-200 p-5">
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <h3 className="font-semibold text-slate-800">{ep.title}</h3>
                    <p className="text-xs text-slate-500">Mission: {ep.mission_id} | Robot: {ep.robot_id}</p>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                      ep.status === 'completed' ? 'bg-emerald-100 text-emerald-800' :
                      ep.status === 'running' ? 'bg-blue-100 text-blue-800' :
                      'bg-slate-100 text-slate-600'
                    }`}>
                      {ep.status}
                    </span>
                    <Link
                      href={`/episodes/${ep.mission_id}`}
                      className="text-xs text-rosclaw-600 hover:underline"
                    >
                      View Trace
                    </Link>
                  </div>
                </div>

                <div className="relative pl-4 border-l-2 border-slate-200 space-y-3">
                  {ep.timeline.slice(0, 8).map((t, i) => (
                    <div key={i} className="relative">
                      <div className="absolute -left-[21px] top-1 w-2.5 h-2.5 rounded-full bg-rosclaw-500" />
                      <div className="text-xs">
                        <span className="text-slate-500">
                          {t.timestamp ? new Date(t.timestamp).toLocaleTimeString() : '—'}
                        </span>
                        <span className="ml-2 font-medium text-slate-700">{t.type}</span>
                      </div>
                    </div>
                  ))}
                  {ep.timeline.length > 8 && (
                    <div className="text-xs text-slate-400">+ {ep.timeline.length - 8} more events</div>
                  )}
                </div>

                {ep.skills.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-2">
                    {ep.skills.map((s, i) => (
                      <span key={i} className="px-2 py-0.5 bg-slate-100 rounded text-xs text-slate-600">
                        {s.name} ({s.status})
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </DashboardShell>
  );
}

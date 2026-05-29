'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import DashboardShell from '@/components/DashboardShell';

interface TraceStep {
  stage: string;
  label: string;
  description?: string;
  status?: string;
  timestamp: string | null;
}

interface TraceData {
  mission_id: string;
  robot_id: string;
  title: string;
  status: string;
  trace: TraceStep[];
}

export default function EpisodeTracePage() {
  const { id } = useParams();
  const [trace, setTrace] = useState<TraceData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    api.episodes.trace(id as string)
      .then((data: any) => {
        setTrace(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [id]);

  return (
    <DashboardShell>
      <div className="space-y-4">
        <Link href="/episodes" className="text-sm text-rosclaw-600 hover:underline">
          Back to Episodes
        </Link>

        {loading ? (
          <div className="text-sm text-slate-500">Loading trace...</div>
        ) : !trace ? (
          <div className="bg-white rounded-lg border border-slate-200 p-8 text-center">
            <p className="text-slate-500">Trace not found.</p>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="bg-white rounded-lg border border-slate-200 p-5">
              <h2 className="text-lg font-semibold text-slate-800">{trace.title}</h2>
              <p className="text-sm text-slate-500">
                Mission: {trace.mission_id} | Robot: {trace.robot_id} | Status: {trace.status}
              </p>
            </div>

            <div className="bg-white rounded-lg border border-slate-200 p-5">
              <h3 className="text-sm font-medium text-slate-700 mb-4">Full Trace</h3>
              <div className="relative pl-4 border-l-2 border-slate-200 space-y-4">
                {trace.trace.map((step, i) => (
                  <div key={i} className="relative">
                    <div className={`absolute -left-[21px] top-1 w-3 h-3 rounded-full ${
                      step.stage === 'agent_input' ? 'bg-blue-500' :
                      step.stage === 'skill_execution' ? 'bg-emerald-500' :
                      step.stage === 'event' ? 'bg-amber-500' :
                      step.stage === 'robot_execution' ? 'bg-purple-500' :
                      'bg-slate-400'
                    }`} />
                    <div className="text-sm">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-slate-800">{step.label}</span>
                        {step.status && (
                          <span className="text-xs text-slate-500">({step.status})</span>
                        )}
                      </div>
                      {step.description && (
                        <p className="text-xs text-slate-500 mt-0.5">{step.description}</p>
                      )}
                      {step.timestamp && (
                        <p className="text-xs text-slate-400 mt-0.5">
                          {new Date(step.timestamp).toLocaleString()}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </DashboardShell>
  );
}

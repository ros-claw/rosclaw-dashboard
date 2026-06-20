'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { useReplayStore } from '@/stores/replayStore';
import type { TraceEvent } from '@rosclaw/timeline-core';

interface FailureAnalysisPanelProps {
  runId: string;
  events: TraceEvent[];
}

export default function FailureAnalysisPanel({ runId, events }: FailureAnalysisPanelProps) {
  const [failures, setFailures] = useState<TraceEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const jumpToEvent = useReplayStore((s) => s.jumpToEvent);

  useEffect(() => {
    setLoading(true);
    api.runs
      .failures(runId)
      .then((res: { failures?: TraceEvent[]; events?: TraceEvent[] }) => {
        setFailures(res.failures || res.events || []);
      })
      .catch(() => {
        const local = events.filter(
          (e) => e.track === 'failure' || e.severity === 'error' || e.tags?.includes('failure'),
        );
        setFailures(local);
      })
      .finally(() => setLoading(false));
  }, [runId, events]);

  return (
    <div className="bg-white border border-rose-200 rounded-lg overflow-hidden">
      <div className="px-4 py-2 border-b border-rose-100 bg-rose-50 text-sm font-medium text-rose-800">
        Failure Analysis
      </div>
      <div className="p-4">
        {loading ? (
          <p className="text-sm text-slate-500">Loading failures...</p>
        ) : failures.length === 0 ? (
          <p className="text-sm text-slate-500">No failure events in this run.</p>
        ) : (
          <ul className="space-y-2">
            {failures.map((f) => (
              <li
                key={f.id}
                className="flex items-center justify-between gap-3 text-sm border border-slate-100 rounded p-2"
              >
                <div className="min-w-0">
                  <p className="font-medium text-slate-800 truncate">{f.title}</p>
                  <p className="text-xs text-slate-500">
                    {f.t_rel.toFixed(2)}s · {f.type} · {f.entity || '—'}
                  </p>
                </div>
                <button
                  onClick={() => jumpToEvent(f)}
                  className="px-3 py-1 rounded bg-rose-600 text-white text-xs hover:bg-rose-700 whitespace-nowrap"
                >
                  Jump
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

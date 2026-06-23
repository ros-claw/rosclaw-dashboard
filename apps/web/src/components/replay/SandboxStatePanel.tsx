'use client';

import { useMemo } from 'react';
import { useReplayStore } from '@/stores/replayStore';

interface SandboxStatePanelProps {
  states?: Record<string, unknown>[];
}

export default function SandboxStatePanel({ states }: SandboxStatePanelProps) {
  const currentTime = useReplayStore((s) => s.currentTime);

  const state = useMemo(() => {
    if (!states || states.length === 0) return null;
    return states.reduce((best, s) => {
      const t = typeof s.t_rel === 'number' ? s.t_rel : -Infinity;
      if (!best || Math.abs(t - currentTime) < Math.abs((best.t_rel as number) - currentTime)) {
        return s;
      }
      return best;
    }, null as Record<string, unknown> | null);
  }, [states, currentTime]);

  if (!state) {
    return (
      <div className="bg-slate-100 border border-slate-200 rounded-lg flex items-center justify-center h-32 text-sm text-slate-500">
        No sandbox state snapshots
      </div>
    );
  }

  return (
    <div className="bg-white border border-slate-200 rounded-lg p-3">
      <p className="text-xs font-medium text-slate-500 mb-2">Sandbox State @ {currentTime.toFixed(2)}s</p>
      <pre className="bg-slate-50 rounded p-2 text-xs overflow-auto max-h-40">
        {JSON.stringify(state, null, 2)}
      </pre>
    </div>
  );
}

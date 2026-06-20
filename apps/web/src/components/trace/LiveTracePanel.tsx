'use client';

import { useMemo, useState } from 'react';
import TraceTimeline from './TraceTimeline';
import type { TraceEvent } from '@rosclaw/timeline-core';

interface LiveTracePanelProps {
  events: TraceEvent[];
  connected: boolean;
  error: string | null;
  onClose: () => void;
}

export default function LiveTracePanel({
  events,
  connected,
  error,
  onClose,
}: LiveTracePanelProps) {
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null);

  const duration = useMemo(() => {
    const max = events.length ? Math.max(...events.map((e) => e.t_rel)) : 0;
    return Math.max(max + 5, 10);
  }, [events]);

  const currentTime = useMemo(() => {
    return events.length ? Math.max(...events.map((e) => e.t_rel)) : 0;
  }, [events]);

  const selected = events.find((e) => e.id === selectedEventId) || null;

  return (
    <div className="bg-white rounded-lg border border-slate-200 p-4 space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="relative flex h-3 w-3">
            <span
              className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${
                connected ? 'bg-emerald-400' : 'bg-rose-400'
              }`}
            />
            <span
              className={`relative inline-flex rounded-full h-3 w-3 ${
                connected ? 'bg-emerald-500' : 'bg-rose-500'
              }`}
            />
          </span>
          <h2 className="font-medium text-slate-800">Live Trace</h2>
          {error && <span className="text-xs text-rose-600">{error}</span>}
          {<span className="text-xs text-slate-500">{events.length} events</span>}
        </div>
        <button
          onClick={onClose}
          className="text-sm text-slate-500 hover:text-slate-700 font-medium"
        >
          Stop
        </button>
      </div>

      <TraceTimeline
        events={events}
        duration={duration}
        currentTime={currentTime}
        selectedEventId={selectedEventId}
        onSelectEvent={(e) => setSelectedEventId(e.id)}
        onSeek={() => {}}
      />

      {selected && (
        <div className="text-xs text-slate-600 border-t border-slate-100 pt-2">
          <p className="font-medium">{selected.title}</p>
          <p className="text-slate-500">{selected.summary || selected.type} @ {selected.t_rel.toFixed(2)}s</p>
        </div>
      )}
    </div>
  );
}

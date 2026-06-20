'use client';

import { useRef } from 'react';
import {
  TRACE_TRACKS,
  TRACK_COLORS,
  type TraceEvent,
  type TraceTrack,
} from '@rosclaw/timeline-core';

interface TraceTimelineProps {
  events: TraceEvent[];
  duration: number;
  currentTime: number;
  selectedEventId: string | null;
  onSelectEvent: (event: TraceEvent) => void;
  onSeek: (t: number) => void;
}

const severityColor = (severity: string) => {
  switch (severity) {
    case 'failure':
    case 'error':
    case 'critical':
      return 'bg-rose-500';
    case 'warning':
      return 'bg-amber-500';
    case 'info':
    default:
      return 'bg-slate-500';
  }
};

export default function TraceTimeline({
  events,
  duration,
  currentTime,
  selectedEventId,
  onSelectEvent,
  onSeek,
}: TraceTimelineProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const lanes: Record<TraceTrack, TraceEvent[]> = {
    task: [],
    agent: [],
    tool: [],
    provider: [],
    sandbox: [],
    runtime: [],
    robot: [],
    critic: [],
    memory: [],
    auto: [],
    failure: [],
  };
  for (const e of events) {
    if (lanes[e.track]) lanes[e.track].push(e);
  }

  const handleTrackClick = (track: TraceTrack, e: React.MouseEvent) => {
    const rect = containerRef.current?.getBoundingClientRect();
    if (!rect || duration <= 0) return;
    const x = e.clientX - rect.left - 96; // offset label column width
    const width = rect.width - 96;
    if (width <= 0) return;
    const ratio = Math.max(0, Math.min(1, x / width));
    onSeek(ratio * duration);
  };

  const currentPct = duration > 0 ? (currentTime / duration) * 100 : 0;

  return (
    <div
      ref={containerRef}
      className="bg-white border border-slate-200 rounded-lg overflow-hidden"
    >
      <div className="px-4 py-2 border-b border-slate-200 bg-slate-50 text-sm font-medium text-slate-700 flex items-center justify-between">
        <span>Trace Timeline</span>
        <span className="text-xs text-slate-500">
          {events.length} events · {duration.toFixed(1)}s
        </span>
      </div>
      <div className="divide-y divide-slate-100">
        {TRACE_TRACKS.map((track) => (
          <div key={track} className="flex items-center h-9 relative">
            <div
              className="w-24 px-3 text-xs font-semibold flex items-center border-r border-slate-100"
              style={{ color: TRACK_COLORS[track] }}
            >
              {track.charAt(0).toUpperCase() + track.slice(1)}
            </div>
            <div
              className="flex-1 relative h-full cursor-crosshair"
              onClick={(e) => handleTrackClick(track, e)}
            >
              {lanes[track].map((event) => {
                const left =
                  duration > 0 ? (event.t_rel / duration) * 100 : 0;
                const selected = selectedEventId === event.id;
                return (
                  <button
                    key={event.id}
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      onSelectEvent(event);
                    }}
                    title={`${event.title} @ ${event.t_rel.toFixed(2)}s`}
                    className={`absolute top-1/2 -translate-y-1/2 w-2.5 h-2.5 rounded-full ${severityColor(
                      event.severity,
                    )} ${
                      selected ? 'ring-2 ring-offset-1 ring-rosclaw-500' : ''
                    }`}
                    style={{ left: `calc(${left}% - 5px)` }}
                  />
                );
              })}
              <div
                className="absolute top-0 bottom-0 w-px bg-rosclaw-500 z-10 pointer-events-none"
                style={{ left: `${currentPct}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

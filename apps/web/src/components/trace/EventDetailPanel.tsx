'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import type { TraceEvent } from '@rosclaw/timeline-core';

interface EventDetailPanelProps {
  event: TraceEvent | null;
}

export default function EventDetailPanel({ event }: EventDetailPanelProps) {
  const [related, setRelated] = useState<TraceEvent[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!event) {
      setRelated([]);
      return;
    }
    setLoading(true);
    api.runs
      .searchEvents(event.run_id, event.id, 5.0)
      .then((res: { events: TraceEvent[] }) => setRelated(res.events))
      .catch(() => setRelated([]))
      .finally(() => setLoading(false));
  }, [event]);

  if (!event) {
    return (
      <div className="bg-white border border-slate-200 rounded-lg p-4 text-sm text-slate-500">
        Select an event from the timeline to inspect details.
      </div>
    );
  }

  return (
    <div className="bg-white border border-slate-200 rounded-lg overflow-hidden">
      <div className="px-4 py-2 border-b border-slate-200 bg-slate-50 text-sm font-medium text-slate-700">
        Event Detail
      </div>
      <div className="p-4 space-y-3 text-sm">
        <div className="flex flex-wrap gap-2">
          <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-700 text-xs">
            {event.track}
          </span>
          <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-700 text-xs">
            {event.type}
          </span>
          <span
            className={`px-2 py-0.5 rounded text-xs font-medium ${
              event.severity === 'error'
                ? 'bg-rose-100 text-rose-700'
                : event.severity === 'warning'
                  ? 'bg-amber-100 text-amber-700'
                  : 'bg-emerald-100 text-emerald-700'
            }`}
          >
            {event.severity}
          </span>
        </div>
        <h3 className="font-semibold text-slate-800">{event.title}</h3>
        {event.summary && <p className="text-slate-600">{event.summary}</p>}
        {event.entity && (
          <p className="text-xs text-slate-500">
            Entity: <span className="font-mono">{event.entity}</span>
          </p>
        )}
        <p className="text-xs text-slate-500">
          t = {event.t_rel.toFixed(3)}s · {new Date(event.ts * 1000).toISOString()}
        </p>

        {event.payload && (
          <div className="mt-2">
            <p className="text-xs font-medium text-slate-500 mb-1">Payload</p>
            <pre className="bg-slate-50 rounded p-2 text-xs overflow-auto max-h-40">
              {JSON.stringify(event.payload, null, 2)}
            </pre>
          </div>
        )}

        {event.tags && event.tags.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {event.tags.map((tag) => (
              <span key={tag} className="px-2 py-0.5 rounded bg-blue-50 text-blue-700 text-xs">
                {tag}
              </span>
            ))}
          </div>
        )}

        {event.links && event.links.length > 0 && (
          <div className="mt-2">
            <p className="text-xs font-medium text-slate-500 mb-1">Links</p>
            <ul className="space-y-1">
              {event.links.map((link) => (
                <li key={link} className="text-xs font-mono text-slate-600 truncate">
                  {link}
                </li>
              ))}
            </ul>
          </div>
        )}

        <div className="mt-3">
          <p className="text-xs font-medium text-slate-500 mb-1">
            Related Events {loading && '(loading)'}
          </p>
          {related.length === 0 ? (
            <p className="text-xs text-slate-400">No related events found.</p>
          ) : (
            <ul className="space-y-1 max-h-40 overflow-auto">
              {related.map((r) => (
                <li key={r.id} className="text-xs text-slate-600">
                  <span className="font-mono text-slate-400">{r.t_rel.toFixed(2)}s</span>{' '}
                  {r.title}
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}

'use client';

import { useEffect, useState, useRef } from 'react';
import DashboardShell from '@/components/DashboardShell';

interface EventMessage {
  event_id: string;
  robot_id: string;
  timestamp: number;
  type: string;
  source: string;
  payload: Record<string, any>;
}

export default function EventsPage() {
  const [events, setEvents] = useState<EventMessage[]>([]);
  const [connected, setConnected] = useState(false);
  const [eventCount, setEventCount] = useState(0);
  const wsRef = useRef<WebSocket | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const ws = new WebSocket(`${protocol}//${window.location.host}/api/events/stream`);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
      ws.send(JSON.stringify({ action: 'history', topic: '*', limit: 50 }));
    };
    ws.onclose = () => setConnected(false);
    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      if (msg.type === 'history' && msg.events) {
        setEvents(prev => [...msg.events.reverse(), ...prev].slice(-100));
        setEventCount(c => c + msg.events.length);
      } else if (msg.type === 'pong') {
        // ignore
      } else if (msg.event_id) {
        setEvents(prev => [...prev, msg].slice(-100));
        setEventCount(c => c + 1);
      }
    };

    const ping = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ action: 'ping', timestamp: Date.now() }));
      }
    }, 10000);

    return () => {
      clearInterval(ping);
      ws.close();
    };
  }, []);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [events]);

  const topicCounts = events.reduce((acc, e) => {
    acc[e.type] = (acc[e.type] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const topicStats = Object.entries(topicCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10);

  return (
    <DashboardShell>
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className={`w-2.5 h-2.5 rounded-full ${connected ? 'bg-emerald-500' : 'bg-red-500'}`} />
            <span className="text-sm text-slate-500">{connected ? 'Connected' : 'Disconnected'}</span>
          </div>
          <span className="text-sm text-slate-500">Total events: {eventCount}</span>
        </div>

        <div className="bg-white rounded-lg border border-slate-200 p-4">
          <h3 className="text-sm font-medium text-slate-700 mb-2">Topic Statistics</h3>
          <div className="flex flex-wrap gap-2">
            {topicStats.map(([topic, count]) => (
              <span key={topic} className="px-2 py-1 bg-slate-100 rounded text-xs text-slate-600">
                {topic}: {count}
              </span>
            ))}
            {topicStats.length === 0 && <span className="text-xs text-slate-400">No events yet</span>}
          </div>
        </div>

        <div
          ref={scrollRef}
          className="bg-slate-900 rounded-lg p-4 font-mono text-xs h-96 overflow-auto"
        >
          {events.length === 0 ? (
            <p className="text-slate-500">Waiting for events...</p>
          ) : (
            <div className="space-y-1">
              {events.map((e, i) => (
                <div key={`${e.event_id}-${i}`} className="flex gap-3 text-slate-300">
                  <span className="text-slate-500 shrink-0 w-14">
                    {new Date(e.timestamp * 1000).toLocaleTimeString()}
                  </span>
                  <span className={`shrink-0 w-32 truncate ${
                    e.type.startsWith('agent.') ? 'text-emerald-400' :
                    e.type.startsWith('skill.') ? 'text-blue-400' :
                    e.type.startsWith('safety.') ? 'text-amber-400' :
                    'text-slate-400'
                  }`}>
                    {e.type}
                  </span>
                  <span className="text-slate-500 shrink-0 w-20 truncate">{e.robot_id}</span>
                  <span className="truncate text-slate-400">
                    {JSON.stringify(e.payload).slice(0, 120)}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </DashboardShell>
  );
}

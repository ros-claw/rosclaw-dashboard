'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import type { TraceEvent } from '@rosclaw/timeline-core';

interface LiveStatus {
  connected: boolean;
  error: string | null;
}

interface UseLiveTraceReturn {
  events: TraceEvent[];
  status: LiveStatus;
  start: () => void;
  stop: () => void;
  clear: () => void;
}

function getWsUrl(): string {
  const apiBase = process.env.NEXT_PUBLIC_API_URL || '';
  if (apiBase.startsWith('http')) {
    return apiBase.replace(/^http/, 'ws') + '/api/runs/live';
  }
  if (typeof window === 'undefined') return '';
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${protocol}//${window.location.host}/api/runs/live`;
}

export function useLiveTrace(): UseLiveTraceReturn {
  const [events, setEvents] = useState<TraceEvent[]>([]);
  const [status, setStatus] = useState<LiveStatus>({ connected: false, error: null });
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectRef = useRef<number | null>(null);

  const stop = useCallback(() => {
    if (reconnectRef.current) {
      window.clearTimeout(reconnectRef.current);
      reconnectRef.current = null;
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setStatus({ connected: false, error: null });
  }, []);

  const clear = useCallback(() => {
    setEvents([]);
  }, []);

  const connect = useCallback(() => {
    if (typeof window === 'undefined') return;
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    try {
      const url = getWsUrl();
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        setStatus({ connected: true, error: null });
      };

      ws.onmessage = (message) => {
        try {
          const data = JSON.parse(message.data);
          if (data.type === 'live_start') {
            return;
          }
          if (data.type === 'pong') {
            return;
          }
          const event = data as TraceEvent;
          setEvents((prev) => {
            if (prev.some((e) => e.id === event.id)) return prev;
            return [...prev, event].sort((a, b) => a.t_rel - b.t_rel);
          });
        } catch {
          // ignore malformed messages
        }
      };

      ws.onerror = () => {
        setStatus((s) => ({ ...s, error: 'Live connection error' }));
      };

      ws.onclose = () => {
        setStatus({ connected: false, error: 'Live stream disconnected' });
        wsRef.current = null;
      };
    } catch (err) {
      setStatus({ connected: false, error: 'Failed to open live stream' });
    }
  }, []);

  const start = useCallback(() => {
    clear();
    connect();
  }, [clear, connect]);

  useEffect(() => {
    return () => stop();
  }, [stop]);

  return { events, status, start, stop, clear };
}

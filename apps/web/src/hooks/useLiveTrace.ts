'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import type { TraceEvent } from '@rosclaw/timeline-core';

interface LiveStatus {
  connected: boolean;
  error: string | null;
  offlineRunId: string | null;
}

interface UseLiveTraceReturn {
  events: TraceEvent[];
  status: LiveStatus;
  start: () => void;
  stop: () => void;
  clear: () => void;
}

function getWsUrl(sessionId: string): string {
  const apiBase = process.env.NEXT_PUBLIC_API_URL || '';
  if (apiBase.startsWith('http')) {
    return `${apiBase.replace(/^http/, 'ws')}/api/live/${sessionId}/events`;
  }
  if (typeof window === 'undefined') return '';
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${protocol}//${window.location.host}/api/live/${sessionId}/events`;
}

export function useLiveTrace(sessionId: string | null): UseLiveTraceReturn {
  const [events, setEvents] = useState<TraceEvent[]>([]);
  const [status, setStatus] = useState<LiveStatus>({
    connected: false,
    error: null,
    offlineRunId: null,
  });
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectRef = useRef<number | null>(null);
  const sessionIdRef = useRef(sessionId);

  useEffect(() => {
    sessionIdRef.current = sessionId;
  }, [sessionId]);

  const stop = useCallback(() => {
    if (reconnectRef.current) {
      window.clearTimeout(reconnectRef.current);
      reconnectRef.current = null;
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setStatus((s) => ({ ...s, connected: false, error: null }));
  }, []);

  const clear = useCallback(() => {
    setEvents([]);
    setStatus((s) => ({ ...s, offlineRunId: null }));
  }, []);

  const connect = useCallback(() => {
    const sid = sessionIdRef.current;
    if (typeof window === 'undefined' || !sid) return;
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    try {
      const url = getWsUrl(sid);
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        setStatus({ connected: true, error: null, offlineRunId: null });
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
          if (data.type === 'offline_ready') {
            setStatus((s) => ({ ...s, offlineRunId: data.offline_run_id || null }));
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
        setStatus((s) => ({ ...s, connected: false, error: 'Live stream disconnected' }));
        wsRef.current = null;
        // Auto-reconnect once after a short delay unless stop was called.
        if (sessionIdRef.current && reconnectRef.current === null) {
          reconnectRef.current = window.setTimeout(() => {
            reconnectRef.current = null;
            connect();
          }, 2000);
        }
      };
    } catch (err) {
      setStatus((s) => ({ ...s, connected: false, error: 'Failed to open live stream' }));
    }
  }, []);

  const start = useCallback(() => {
    clear();
    connect();
  }, [clear, connect]);

  useEffect(() => {
    return () => stop();
  }, [stop]);

  useEffect(() => {
    if (sessionId) {
      start();
    } else {
      stop();
      clear();
    }
  }, [sessionId, start, stop, clear]);

  return { events, status, start, stop, clear };
}

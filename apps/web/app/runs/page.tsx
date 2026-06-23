'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import DashboardShell from '@/components/DashboardShell';
import LiveTracePanel from '@/components/trace/LiveTracePanel';
import { useLiveTrace } from '@/hooks/useLiveTrace';
import type { RunSummary } from '@rosclaw/timeline-core';

const STATUS_OPTIONS = ['all', 'success', 'failure', 'running', 'unknown'];

export default function RunsPage() {
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState('all');
  const [search, setSearch] = useState('');
  const [live, setLive] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const { events, status: liveStatus, start, stop, clear } = useLiveTrace(sessionId);

  useEffect(() => {
    api.runs
      .list({ limit: 500 })
      .then((res: { runs: RunSummary[]; total: number }) => {
        setRuns(res.runs);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message || 'Failed to load runs');
        setLoading(false);
      });
  }, []);

  const toggleLive = useCallback(async () => {
    if (live) {
      if (sessionId) {
        try {
          await api.live.close(sessionId);
        } catch {
          // ignore close errors
        }
      }
      stop();
      setSessionId(null);
      setLive(false);
      return;
    }
    clear();
    try {
      const session = await api.live.create({ robot_id: 'dashboard', task: 'live trace' });
      setSessionId(session.session_id);
      setLive(true);
    } catch (err: any) {
      setError(err.message || 'Failed to start live session');
    }
  }, [live, sessionId, stop, clear]);

  // Refresh runs list after a session is archived.
  useEffect(() => {
    if (!liveStatus.offlineRunId) return;
    api.runs.list({ limit: 500 }).then((res: { runs: RunSummary[]; total: number }) => {
      setRuns(res.runs);
    });
  }, [liveStatus.offlineRunId]);

  const filtered = useMemo(() => {
    const term = search.trim().toLowerCase();
    return runs.filter((run) => {
      const matchesStatus = status === 'all' || run.status === status;
      const matchesSearch =
        !term ||
        run.run_id.toLowerCase().includes(term) ||
        (run.task || '').toLowerCase().includes(term) ||
        (run.robot_id || '').toLowerCase().includes(term);
      return matchesStatus && matchesSearch;
    });
  }, [runs, status, search]);

  const statusBadge = (s?: string) => {
    const color =
      s === 'success'
        ? 'bg-emerald-100 text-emerald-800'
        : s === 'failure'
          ? 'bg-rose-100 text-rose-800'
          : s === 'running'
            ? 'bg-blue-100 text-blue-800'
            : 'bg-slate-100 text-slate-600';
    return (
      <span className={`px-2 py-0.5 rounded text-xs font-medium ${color}`}>
        {s || 'unknown'}
      </span>
    );
  };

  return (
    <DashboardShell>
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="flex items-center gap-2">
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value)}
              className="border border-slate-300 rounded px-3 py-2 text-sm bg-white"
            >
              {STATUS_OPTIONS.map((s) => (
                <option key={s} value={s}>
                  {s === 'all' ? 'All statuses' : s.charAt(0).toUpperCase() + s.slice(1)}
                </option>
              ))}
            </select>
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search run ID, task, robot..."
              className="border border-slate-300 rounded px-3 py-2 text-sm w-64"
            />
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={toggleLive}
              className={`px-3 py-2 rounded text-sm font-medium border ${
                live
                  ? 'bg-rose-50 border-rose-200 text-rose-700'
                  : 'bg-white border-slate-300 text-slate-700 hover:bg-slate-50'
              }`}
            >
              {live ? 'Stop Live' : 'Live Trace'}
            </button>
            <p className="text-sm text-slate-500">
              {filtered.length} of {runs.length} run{runs.length !== 1 && 's'}
            </p>
          </div>
        </div>

        {live && (
          <LiveTracePanel
            events={events}
            connected={liveStatus.connected}
            error={liveStatus.error}
            offlineRunId={liveStatus.offlineRunId}
            onClose={() => toggleLive()}
          />
        )}

        {error && (
          <div className="bg-rose-50 border border-rose-200 text-rose-700 px-4 py-3 rounded text-sm">
            {error}
          </div>
        )}

        {loading ? (
          <div className="text-sm text-slate-500">Loading practice runs...</div>
        ) : filtered.length === 0 ? (
          <div className="bg-white rounded-lg border border-slate-200 p-8 text-center">
            <p className="text-slate-500">No practice runs found.</p>
          </div>
        ) : (
          <div className="bg-white rounded-lg border border-slate-200 overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="text-left px-4 py-3 font-medium text-slate-600">Run ID</th>
                  <th className="text-left px-4 py-3 font-medium text-slate-600">Status</th>
                  <th className="text-left px-4 py-3 font-medium text-slate-600">Robot</th>
                  <th className="text-left px-4 py-3 font-medium text-slate-600">Task</th>
                  <th className="text-left px-4 py-3 font-medium text-slate-600">Duration</th>
                  <th className="text-left px-4 py-3 font-medium text-slate-600">Events</th>
                  <th className="text-left px-4 py-3 font-medium text-slate-600">Failures</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((run) => (
                  <tr key={run.run_id} className="border-b border-slate-100 hover:bg-slate-50">
                    <td className="px-4 py-3">
                      <Link
                        href={`/runs/${run.run_id}`}
                        className="text-rosclaw-600 hover:underline font-medium"
                      >
                        {run.run_id}
                      </Link>
                    </td>
                    <td className="px-4 py-3">{statusBadge(run.status)}</td>
                    <td className="px-4 py-3 text-slate-600">{run.robot_id || '—'}</td>
                    <td className="px-4 py-3 text-slate-600">{run.task || '—'}</td>
                    <td className="px-4 py-3 text-slate-600">
                      {run.duration_sec != null ? `${run.duration_sec.toFixed(1)}s` : '—'}
                    </td>
                    <td className="px-4 py-3 text-slate-600">{run.event_count ?? '—'}</td>
                    <td className="px-4 py-3">
                      {run.failure_count ? (
                        <span className="px-2 py-0.5 rounded text-xs font-medium bg-rose-100 text-rose-800">
                          {run.failure_count}
                        </span>
                      ) : (
                        <span className="text-slate-400">0</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </DashboardShell>
  );
}

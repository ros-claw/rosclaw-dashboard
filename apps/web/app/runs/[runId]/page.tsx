'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import DashboardShell from '@/components/DashboardShell';
import TraceTimeline from '@/components/trace/TraceTimeline';
import EventDetailPanel from '@/components/trace/EventDetailPanel';
import FailureAnalysisPanel from '@/components/trace/FailureAnalysisPanel';
import ExportPanel from '@/components/export/ExportPanel';
import VideoPanel from '@/components/replay/VideoPanel';
import CurvesPanel from '@/components/replay/CurvesPanel';
import TrajectoryPanel from '@/components/replay/TrajectoryPanel';
import SandboxStatePanel from '@/components/replay/SandboxStatePanel';
import { useReplayStore } from '@/stores/replayStore';
import type { RunDetail, ReplayManifest, TraceEvent } from '@rosclaw/timeline-core';

function formatTime(t: number) {
  const m = Math.floor(t / 60);
  const s = Math.floor(t % 60);
  const ms = Math.floor((t % 1) * 1000);
  return `${m}:${s.toString().padStart(2, '0')}.${ms.toString().padStart(3, '0')}`;
}

export default function RunTracePage() {
  const params = useParams();
  const runId = (params?.runId as string) || '';
  const [run, setRun] = useState<RunDetail | null>(null);
  const [manifest, setManifest] = useState<ReplayManifest | null>(null);
  const [events, setEvents] = useState<TraceEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const {
    currentTime,
    duration,
    playing,
    speed,
    selectedEventId,
    setRun: setReplayRun,
    seek,
    toggle,
    setSpeed,
    selectEvent,
    jumpToEvent,
    tick,
  } = useReplayStore();

  useEffect(() => {
    if (!runId) return;
    setLoading(true);
    Promise.all([
      api.runs.get(runId),
      api.runs.replay(runId),
      api.runs.events(runId, { limit: 1000 }),
    ])
      .then(([runRes, manifestRes, eventsRes]) => {
        setRun(runRes as RunDetail);
        setManifest(manifestRes as ReplayManifest);
        const list = Array.isArray(eventsRes)
          ? eventsRes
          : (eventsRes as { events: TraceEvent[] }).events || [];
        setEvents(list);
        const dur =
          (manifestRes as ReplayManifest).duration_sec ||
          (runRes as RunDetail).duration_sec ||
          0;
        setReplayRun(runId, dur);
      })
      .catch((err) => setError(err.message || 'Failed to load trace'))
      .finally(() => setLoading(false));
  }, [runId, setReplayRun]);

  useEffect(() => {
    if (!playing) return;
    let raf = 0;
    const loop = (now: number) => {
      tick(now);
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
  }, [playing, tick]);

  const handleSelectEvent = (e: TraceEvent) => {
    selectEvent(e.id);
    jumpToEvent(e);
  };

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

  if (loading) {
    return (
      <DashboardShell>
        <div className="text-sm text-slate-500">Loading trace viewer...</div>
      </DashboardShell>
    );
  }

  if (error || !run) {
    return (
      <DashboardShell>
        <div className="bg-rose-50 border border-rose-200 text-rose-700 px-4 py-3 rounded text-sm">
          {error || 'Run not found'}
        </div>
      </DashboardShell>
    );
  }

  return (
    <DashboardShell>
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-sm text-slate-500">
              <Link href="/runs" className="hover:text-rosclaw-600">Runs</Link>
              <span>/</span>
              <span className="font-mono">{runId}</span>
            </div>
            <div className="flex items-center gap-3">
              <h1 className="text-xl font-semibold text-slate-800">
                {run.task || 'Untitled run'}
              </h1>
              {statusBadge(run.status)}
            </div>
            <p className="text-sm text-slate-500">
              Robot: {run.robot_id || '—'} · Duration:{' '}
              {run.duration_sec != null ? `${run.duration_sec.toFixed(1)}s` : '—'} · Events:{' '}
              {run.event_count ?? events.length} · Failures: {run.failure_count ?? 0}
            </p>
          </div>
          <ExportPanel runId={runId} />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="lg:col-span-2 space-y-4">
            <div className="bg-white border border-slate-200 rounded-lg p-3 space-y-3">
                <div className="flex items-center gap-3">
                  <button
                    onClick={toggle}
                    className="px-4 py-2 rounded bg-rosclaw-600 text-white text-sm font-medium hover:bg-rosclaw-700"
                  >
                    {playing ? 'Pause' : 'Play'}
                  </button>
                  <div className="flex items-center gap-2 text-sm">
                    <button
                      onClick={() => setSpeed(0.5)}
                      className={`px-2 py-1 rounded border ${speed === 0.5 ? 'bg-slate-100' : ''}`}
                    >
                      0.5x
                    </button>
                    <button
                      onClick={() => setSpeed(1)}
                      className={`px-2 py-1 rounded border ${speed === 1 ? 'bg-slate-100' : ''}`}
                    >
                      1x
                    </button>
                    <button
                      onClick={() => setSpeed(2)}
                      className={`px-2 py-1 rounded border ${speed === 2 ? 'bg-slate-100' : ''}`}
                    >
                      2x
                    </button>
                  </div>
                  <span className="text-sm font-mono text-slate-600">
                    {formatTime(currentTime)} / {formatTime(duration)}
                  </span>
                </div>
                <input
                  type="range"
                  min={0}
                  max={duration || 1}
                  step={0.01}
                  value={currentTime}
                  onChange={(e) => seek(parseFloat(e.target.value))}
                  className="w-full"
                />
              </div>

            <TraceTimeline
              events={events}
              duration={duration || 1}
              currentTime={currentTime}
              selectedEventId={selectedEventId}
              onSelectEvent={handleSelectEvent}
              onSeek={seek}
            />

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <VideoPanel media={manifest?.media || []} runId={runId} />
                <CurvesPanel curves={manifest?.curves || []} runId={runId} />
                <TrajectoryPanel trajectory={manifest?.trajectory} runId={runId} />
                <SandboxStatePanel states={manifest?.sandbox_states} />
              </div>
          </div>

          <div className="space-y-4">
              <FailureAnalysisPanel runId={runId} events={events} />
              <EventDetailPanel
                event={events.find((e) => e.id === selectedEventId) || null}
              />
          </div>
        </div>
      </div>
    </DashboardShell>
  );
}

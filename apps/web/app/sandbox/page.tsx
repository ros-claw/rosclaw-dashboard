'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import DashboardShell from '@/components/DashboardShell';

interface SandboxRun {
  run_id: string;
  episode_id?: string;
  robot_id?: string;
  task?: string;
  status: string;
  duration_sec?: number;
  sandbox_result?: {
    decision?: string;
    risk_score?: number;
    reason?: string;
    checks?: string[];
    replay_id?: string;
  };
}

export default function SandboxReplayPage() {
  const [runs, setRuns] = useState<SandboxRun[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.runs.list({ limit: 100 })
      .then((res: any) => {
        const withSandbox = (res.runs || []).filter((r: any) =>
          r.sandbox_result || r.status === 'failure' || (r.tracks || []).includes('sandbox')
        );
        setRuns(withSandbox);
      })
      .finally(() => setLoading(false));
  }, []);

  return (
    <DashboardShell>
      <div className="space-y-6">
        <div className="bg-white rounded-lg border border-slate-200 p-4">
          <h2 className="font-medium text-slate-800">Sandbox Replay</h2>
          <p className="text-sm text-slate-500 mt-1">Review sandbox decisions, risk scores, and replay IDs for practice runs.</p>
        </div>

        {loading ? (
          <div className="text-sm text-slate-500">Loading sandbox runs...</div>
        ) : runs.length === 0 ? (
          <div className="bg-white rounded-lg border border-slate-200 p-8 text-center">
            <p className="text-slate-500">No sandbox runs found.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4">
            {runs.map((run) => {
              const decision = run.sandbox_result?.decision || 'N/A';
              const isBlock = decision === 'BLOCK';
              const isAllow = decision === 'ALLOW';
              return (
                <div key={run.run_id} className="bg-white rounded-lg border border-slate-200 p-4">
                  <div className="flex items-center justify-between mb-3">
                    <div>
                      <Link href={`/runs/${run.run_id}`} className="font-medium text-rosclaw-600 hover:underline">
                        {run.episode_id || run.run_id}
                      </Link>
                      <div className="text-xs text-slate-500">{run.robot_id} &bull; {run.task}</div>
                    </div>
                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                      isBlock ? 'bg-red-100 text-red-800' :
                      isAllow ? 'bg-emerald-100 text-emerald-800' :
                      'bg-slate-100 text-slate-600'
                    }`}>
                      {decision}
                    </span>
                  </div>
                  {run.sandbox_result?.risk_score !== undefined && (
                    <div className="text-sm text-slate-600 mb-1">Risk score: {run.sandbox_result.risk_score}</div>
                  )}
                  {run.sandbox_result?.reason && (
                    <div className="text-sm text-slate-600 mb-1">Reason: {run.sandbox_result.reason}</div>
                  )}
                  {run.sandbox_result?.checks && (
                    <div className="text-xs text-slate-500 mb-2">Checks: {run.sandbox_result.checks.join(', ')}</div>
                  )}
                  {run.sandbox_result?.replay_id && (
                    <div className="text-xs font-mono text-slate-400">Replay: {run.sandbox_result.replay_id}</div>
                  )}
                  <div className="mt-3 flex gap-2">
                    <Link href={`/runs/${run.run_id}`}
                      className="text-xs px-3 py-1.5 bg-slate-800 text-white rounded hover:bg-slate-900"
                    >
                      Open Trace
                    </Link>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </DashboardShell>
  );
}

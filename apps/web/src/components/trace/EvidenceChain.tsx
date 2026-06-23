'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';

interface EvidenceNode {
  id: string;
  type: string;
  track: string;
  label: string;
  t_rel: number;
  severity: string;
  payload?: Record<string, any>;
}

interface EvidenceEdge {
  source: string;
  target: string;
  relation: string;
}

interface EvidenceGraph {
  run_id: string;
  focus_event_id?: string | null;
  nodes: EvidenceNode[];
  edges: EvidenceEdge[];
}

interface EvidenceChainProps {
  runId: string;
  failureId?: string | null;
}

const TRACK_COLORS: Record<string, string> = {
  task: 'border-slate-400',
  agent: 'border-blue-400',
  tool: 'border-indigo-400',
  provider: 'border-purple-400',
  sandbox: 'border-amber-400',
  runtime: 'border-cyan-400',
  robot: 'border-emerald-400',
  critic: 'border-pink-400',
  memory: 'border-violet-400',
  auto: 'border-lime-400',
  failure: 'border-rose-500',
};

export default function EvidenceChain({ runId, failureId }: EvidenceChainProps) {
  const [graph, setGraph] = useState<EvidenceGraph | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    const promise = failureId
      ? api.runs.failureEvidence(runId, failureId)
      : api.runs.evidence(runId);
    promise
      .then((g) => {
        setGraph(g as EvidenceGraph);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message || 'Failed to load evidence');
        setLoading(false);
      });
  }, [runId, failureId]);

  if (loading) return <div className="text-sm text-slate-500">Loading evidence chain...</div>;
  if (error || !graph)
    return <div className="text-sm text-rose-600">{error || 'No evidence available'}</div>;

  const sorted = [...graph.nodes].sort((a, b) => a.t_rel - b.t_rel);

  return (
    <div className="bg-white rounded-lg border border-slate-200 p-4 space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="font-medium text-slate-800">Evidence Chain</h2>
        <span className="text-xs text-slate-500">{sorted.length} nodes</span>
      </div>
      <div className="space-y-2 max-h-96 overflow-y-auto pr-1">
        {sorted.map((node, idx) => (
          <div
            key={node.id}
            className={`relative pl-3 py-2 border-l-4 ${TRACK_COLORS[node.track] || 'border-slate-300'} bg-slate-50 rounded`}
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-600 uppercase tracking-wide">
                {node.track}
              </span>
              <span className="text-xs text-slate-400">{node.t_rel.toFixed(2)}s</span>
            </div>
            <p className="text-sm text-slate-800 font-medium">{node.label}</p>
            {node.severity !== 'info' && (
              <span
                className={`inline-block mt-1 text-[10px] px-1.5 py-0.5 rounded font-medium ${
                  node.severity === 'error' || node.severity === 'failure'
                    ? 'bg-rose-100 text-rose-700'
                    : 'bg-amber-100 text-amber-700'
                }`}
              >
                {node.severity}
              </span>
            )}
            {node.payload && Object.keys(node.payload).length > 0 && (
              <details className="mt-1">
                <summary className="text-[10px] text-slate-500 cursor-pointer">Payload</summary>
                <pre className="text-[10px] text-slate-600 mt-1 overflow-x-auto">
                  {JSON.stringify(node.payload, null, 2)}
                </pre>
              </details>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

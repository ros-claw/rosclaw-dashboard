'use client';

import { useState } from 'react';
import { api } from '@/lib/api';

interface FailureAnalysisPanelProps {
  runId: string;
  events: any[];
}

export default function FailureAnalysisPanel({ runId, events }: FailureAnalysisPanelProps) {
  const [failures, setFailures] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [memoryAnswer, setMemoryAnswer] = useState<any>(null);
  const [howHint, setHowHint] = useState<any>(null);
  const [asking, setAsking] = useState(false);

  const loadFailures = async () => {
    setLoading(true);
    try {
      const res = await api.runs.failures(runId);
      setFailures(res.failures || []);
    } catch {
      setFailures(events.filter((e) => e.track === 'failure' || e.severity === 'failure'));
    } finally {
      setLoading(false);
    }
  };

  const askMemory = async () => {
    setAsking(true);
    try {
      const res = await api.memory.explain({ question: 'What happened?', run_id: runId });
      setMemoryAnswer(res);
    } finally {
      setAsking(false);
    }
  };

  const askHow = async () => {
    setAsking(true);
    try {
      const res = await api.how.recovery({ run_id: runId });
      setHowHint(res);
    } finally {
      setAsking(false);
    }
  };

  return (
    <div className="bg-white border border-rose-200 rounded-lg overflow-hidden">
      <div className="px-4 py-2 border-b border-rose-100 bg-rose-50 text-sm font-medium text-rose-800 flex justify-between items-center">
        <span>Failure Analysis</span>
        <button onClick={loadFailures} className="text-xs text-rose-700 hover:underline">
          Refresh
        </button>
      </div>
      <div className="p-4 space-y-4">
        {loading ? (
          <p className="text-sm text-slate-500">Loading failures...</p>
        ) : failures.length === 0 ? (
          <p className="text-sm text-slate-500">No failure events in this run.</p>
        ) : (
          <ul className="space-y-2">
            {failures.map((f) => (
              <li key={f.id} className="text-sm border border-slate-100 rounded p-2">
                <p className="font-medium text-slate-800">{f.title}</p>
                <p className="text-xs text-slate-500">
                  {f.t_rel?.toFixed(2)}s · {f.type} · {f.entity || '—'}
                </p>
              </li>
            ))}
          </ul>
        )}

        <div className="flex gap-2">
          <button
            onClick={askMemory}
            disabled={asking}
            className="flex-1 px-3 py-2 bg-slate-800 text-white text-xs rounded hover:bg-slate-900 disabled:opacity-50"
          >
            {asking ? 'Asking Memory...' : 'Ask Memory'}
          </button>
          <button
            onClick={askHow}
            disabled={asking}
            className="flex-1 px-3 py-2 bg-rose-600 text-white text-xs rounded hover:bg-rose-700 disabled:opacity-50"
          >
            {asking ? 'Asking How...' : 'Get Recovery Hint'}
          </button>
        </div>

        {memoryAnswer && (
          <div className="bg-slate-50 rounded p-3 text-sm space-y-1">
            <p className="font-medium text-slate-700">Memory</p>
            <p className="text-slate-600">{memoryAnswer.answer}</p>
            {memoryAnswer.recovery_suggestion && (
              <p className="text-xs text-emerald-700">Suggestion: {memoryAnswer.recovery_suggestion}</p>
            )}
          </div>
        )}

        {howHint && (
          <div className="bg-rose-50 rounded p-3 text-sm space-y-1">
            <p className="font-medium text-rose-800">How Recovery</p>
            <p className="text-slate-700">{howHint.recovery_hint}</p>
            <p className="text-xs text-slate-500">
              Patch: {JSON.stringify(howHint.parameter_patch)}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

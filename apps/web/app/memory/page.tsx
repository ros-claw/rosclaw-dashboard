'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import DashboardShell from '@/components/DashboardShell';

export default function MemoryPage() {
  const [entries, setEntries] = useState<any[]>([]);
  const [stats, setStats] = useState<{ total_entries: number; by_type: Record<string, number> } | null>(null);
  const [loading, setLoading] = useState(true);
  const [robotId, setRobotId] = useState('');
  const [memoryType, setMemoryType] = useState('');
  const [question, setQuestion] = useState('What happened?');
  const [runId, setRunId] = useState('');
  const [explainResult, setExplainResult] = useState<any>(null);
  const [explaining, setExplaining] = useState(false);

  const load = () => {
    setLoading(true);
    const params: Record<string, string> = {};
    if (robotId) params.robot_id = robotId;
    if (memoryType) params.memory_type = memoryType;
    const qs = new URLSearchParams(params).toString();
    Promise.all([
      fetch(qs ? `/api/memory?${qs}` : '/api/memory').then((r) => r.json()),
      api.memory.stats(),
    ])
      .then(([entriesData, statsData]) => {
        setEntries(entriesData);
        setStats(statsData);
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
  }, [robotId, memoryType]);

  const explain = async () => {
    setExplaining(true);
    try {
      const res = await api.memory.explain({ question, run_id: runId || undefined });
      setExplainResult(res);
    } finally {
      setExplaining(false);
    }
  };

  const typeColor = (type: string) => {
    switch (type) {
      case 'episodic': return 'bg-blue-100 text-blue-800';
      case 'semantic': return 'bg-emerald-100 text-emerald-800';
      case 'procedural': return 'bg-amber-100 text-amber-800';
      default: return 'bg-slate-100 text-slate-600';
    }
  };

  return (
    <DashboardShell>
      <div className="space-y-6">
        {/* Explain panel */}
        <div className="bg-white rounded-lg border border-slate-200 p-4 space-y-4">
          <h3 className="font-medium text-slate-800">Memory Explain</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <input
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Ask a question..."
              className="border border-slate-200 rounded p-2 text-sm"
            />
            <input
              value={runId}
              onChange={(e) => setRunId(e.target.value)}
              placeholder="Run ID (optional)"
              className="border border-slate-200 rounded p-2 text-sm"
            />
            <button
              onClick={explain}
              disabled={explaining}
              className="px-4 py-2 bg-slate-800 text-white text-sm rounded hover:bg-slate-900 disabled:opacity-50"
            >
              {explaining ? 'Explaining...' : 'Ask Memory'}
            </button>
          </div>
          {explainResult && (
            <div className="bg-slate-50 rounded p-3 text-sm space-y-2">
              <p className="font-medium text-slate-700">Answer</p>
              <p className="text-slate-600">{explainResult.answer}</p>
              {explainResult.failure_stage && <p className="text-xs text-slate-500">Stage: {explainResult.failure_stage}</p>}
              {explainResult.key_events?.length > 0 && (
                <div className="text-xs text-slate-500">
                  Key events:
                  <ul className="mt-1 space-y-0.5">
                    {explainResult.key_events.map((e: string, i: number) => <li key={i}>{e}</li>)}
                  </ul>
                </div>
              )}
              {explainResult.recovery_suggestion && <p className="text-xs text-emerald-700">Suggestion: {explainResult.recovery_suggestion}</p>}
              {explainResult.similar_history?.length > 0 && (
                <div className="text-xs text-slate-500">Similar history: {explainResult.similar_history.join(', ')}</div>
              )}
            </div>
          )}
        </div>

        {/* Filters */}
        <div className="flex flex-wrap gap-3 items-center">
          <input
            value={robotId}
            onChange={(e) => setRobotId(e.target.value)}
            placeholder="Filter by robot"
            className="border border-slate-200 rounded p-2 text-sm"
          />
          <select
            value={memoryType}
            onChange={(e) => setMemoryType(e.target.value)}
            className="border border-slate-200 rounded p-2 text-sm"
          >
            <option value="">All types</option>
            <option value="episodic">Episodic</option>
            <option value="semantic">Semantic</option>
            <option value="procedural">Procedural</option>
          </select>
          <button onClick={load} className="px-3 py-2 border border-slate-200 rounded text-sm hover:bg-slate-50">Refresh</button>
          {stats && (
            <div className="flex gap-2 text-xs">
              {Object.entries(stats.by_type).map(([type, count]) => (
                <span key={type} className={`px-2 py-1 rounded font-medium ${typeColor(type)}`}>
                  {type}: {count}
                </span>
              ))}
            </div>
          )}
        </div>

        {loading ? (
          <div className="text-sm text-slate-500">Loading...</div>
        ) : entries.length === 0 ? (
          <div className="bg-white rounded-lg border border-slate-200 p-8 text-center">
            <p className="text-slate-500">No memory entries found.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {entries.map((entry: any) => (
              <div key={entry.id} className="bg-white rounded-lg border border-slate-200 p-4">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-medium text-sm">{entry.id}</h3>
                  <span className={`px-2 py-0.5 rounded text-xs font-medium ${typeColor(entry.memory_type)}`}>{entry.memory_type}</span>
                </div>
                <p className="text-sm text-slate-500 mb-2 font-mono break-all">{entry.content_json}</p>
                <div className="text-xs text-slate-400 space-y-1">
                  {entry.source_skill && <div>Source skill: {entry.source_skill}</div>}
                  {entry.source_mission && <div>Source mission: {entry.source_mission}</div>}
                  <div>Confidence: {entry.confidence}</div>
                  <div>Robot: {entry.robot_id}</div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </DashboardShell>
  );
}

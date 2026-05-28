'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import DashboardShell from '@/components/DashboardShell';

export default function MemoryPage() {
  const [entries, setEntries] = useState<any[]>([]);
  const [stats, setStats] = useState<{ total_entries: number; by_type: Record<string, number> } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.memory.list(), api.memory.stats()])
      .then(([entriesData, statsData]) => {
        setEntries(entriesData);
        setStats(statsData);
      })
      .finally(() => setLoading(false));
  }, []);

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
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <p className="text-sm text-slate-500">{entries.length} memory entries</p>
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
          <div className="grid grid-cols-2 gap-4">
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

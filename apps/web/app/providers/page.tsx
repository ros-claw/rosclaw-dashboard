'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import DashboardShell from '@/components/DashboardShell';

interface Provider {
  id: string;
  name: string;
  type: string;
  healthy: boolean;
  latency_ms: number;
  success_rate: number;
  request_count: number;
  error_count: number;
  load_percent: number;
}

export default function ProvidersPage() {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.providers.list().then((data: any) => {
      setProviders(data);
      setLoading(false);
    });
  }, []);

  const avgLatency = providers.length > 0
    ? providers.reduce((s, p) => s + p.latency_ms, 0) / providers.length
    : 0;
  const avgSuccess = providers.length > 0
    ? providers.reduce((s, p) => s + p.success_rate, 0) / providers.length
    : 0;

  return (
    <DashboardShell>
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white rounded-lg border border-slate-200 p-4">
            <p className="text-sm text-slate-500">Total Providers</p>
            <p className="text-2xl font-bold text-slate-800">{providers.length}</p>
          </div>
          <div className="bg-white rounded-lg border border-slate-200 p-4">
            <p className="text-sm text-slate-500">Avg Latency</p>
            <p className="text-2xl font-bold text-slate-800">{avgLatency.toFixed(1)} ms</p>
          </div>
          <div className="bg-white rounded-lg border border-slate-200 p-4">
            <p className="text-sm text-slate-500">Avg Success Rate</p>
            <p className="text-2xl font-bold text-emerald-600">{(avgSuccess * 100).toFixed(2)}%</p>
          </div>
        </div>

        {loading ? (
          <div className="text-sm text-slate-500">Loading providers...</div>
        ) : (
          <div className="bg-white rounded-lg border border-slate-200 overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="text-left px-4 py-3 font-medium text-slate-600">Provider</th>
                  <th className="text-left px-4 py-3 font-medium text-slate-600">Type</th>
                  <th className="text-left px-4 py-3 font-medium text-slate-600">Health</th>
                  <th className="text-right px-4 py-3 font-medium text-slate-600">Latency</th>
                  <th className="text-right px-4 py-3 font-medium text-slate-600">Success</th>
                  <th className="text-right px-4 py-3 font-medium text-slate-600">Load</th>
                </tr>
              </thead>
              <tbody>
                {providers.map((p) => (
                  <tr key={p.id} className="border-b border-slate-100 hover:bg-slate-50">
                    <td className="px-4 py-3 font-medium">{p.name}</td>
                    <td className="px-4 py-3 text-slate-500">{p.type}</td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-0.5 rounded text-xs font-medium ${p.healthy ? 'bg-emerald-100 text-emerald-800' : 'bg-red-100 text-red-800'}`}>
                        {p.healthy ? 'Healthy' : 'Degraded'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right">{p.latency_ms.toFixed(1)} ms</td>
                    <td className="px-4 py-3 text-right">{(p.success_rate * 100).toFixed(2)}%</td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <div className="w-16 h-2 bg-slate-100 rounded-full overflow-hidden">
                          <div className="h-full bg-rosclaw-500 rounded-full" style={{ width: `${Math.min(p.load_percent, 100)}%` }} />
                        </div>
                        <span className="text-xs text-slate-500">{p.load_percent.toFixed(0)}%</span>
                      </div>
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

'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import DashboardShell from '@/components/DashboardShell';

export default function SafetyPage() {
  const [audits, setAudits] = useState<any[]>([]);
  const [rules, setRules] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.safety.audits(), api.safety.rules()])
      .then(([auditsData, rulesData]) => {
        setAudits(auditsData);
        setRules(rulesData);
      })
      .finally(() => setLoading(false));
  }, []);

  const statusColor = (status: string) => {
    switch (status) {
      case 'passed': return 'bg-emerald-100 text-emerald-800';
      case 'failed': return 'bg-red-100 text-red-800';
      case 'pending': return 'bg-amber-100 text-amber-800';
      default: return 'bg-slate-100 text-slate-600';
    }
  };

  const toggleRule = async (id: string) => {
    await api.safety.toggleRule(id);
    const updated = await api.safety.rules();
    setRules(updated);
  };

  return (
    <DashboardShell>
      <div className="space-y-4">
        {loading ? (
          <div className="text-sm text-slate-500">Loading...</div>
        ) : (
          <>
            {/* Safety Rules */}
            <div className="bg-white rounded-lg border border-slate-200 p-4">
              <h3 className="font-medium mb-3">Safety Rules ({rules.length})</h3>
              {rules.length === 0 ? (
                <p className="text-sm text-slate-500">No safety rules configured.</p>
              ) : (
                <div className="space-y-2">
                  {rules.map((rule: any) => (
                    <div key={rule.id} className="flex items-center justify-between p-3 bg-slate-50 rounded">
                      <div>
                        <div className="font-medium text-sm">{rule.rule_name}</div>
                        <div className="text-xs text-slate-500">{rule.rule_type} &bull; {rule.robot_id}</div>
                        <div className="text-xs font-mono text-slate-400 mt-1">{rule.parameters_json}</div>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className={`px-2 py-0.5 rounded text-xs font-medium ${rule.active ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-100 text-slate-600'}`}>
                          {rule.active ? 'Active' : 'Inactive'}
                        </span>
                        <button
                          onClick={() => toggleRule(rule.id)}
                          className="text-xs px-3 py-1.5 border border-slate-200 rounded hover:bg-slate-100"
                        >
                          Toggle
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Safety Audits */}
            <div className="bg-white rounded-lg border border-slate-200 p-4">
              <h3 className="font-medium mb-3">Safety Audit Log ({audits.length})</h3>
              {audits.length === 0 ? (
                <p className="text-sm text-slate-500">No safety audits recorded.</p>
              ) : (
                <div className="space-y-2">
                  {audits.map((audit: any) => (
                    <div key={audit.id} className="flex items-center justify-between p-3 bg-slate-50 rounded">
                      <div>
                        <div className="font-medium text-sm">{audit.audit_type}</div>
                        <div className="text-xs text-slate-500">{audit.robot_id}</div>
                        <div className="text-xs font-mono text-slate-400 mt-1">{audit.findings_json}</div>
                      </div>
                      <span className={`px-2 py-0.5 rounded text-xs font-medium ${statusColor(audit.status)}`}>
                        {audit.status}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Emergency Stop */}
            <div className="bg-white rounded-lg border border-slate-200 p-4">
              <h3 className="font-medium mb-2">Emergency Stop</h3>
              <button className="w-full py-3 bg-red-600 text-white rounded font-medium hover:bg-red-700 transition-colors">
                STOP ALL ROBOTS
              </button>
            </div>
          </>
        )}
      </div>
    </DashboardShell>
  );
}

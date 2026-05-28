'use client';

import DashboardShell from '@/components/DashboardShell';

export default function SafetyPage() {
  return (
    <DashboardShell>
      <div className="space-y-4">
        <div className="grid grid-cols-3 gap-4">
          <div className="bg-white rounded-lg border border-slate-200 p-4">
            <h3 className="font-medium mb-2">Emergency Stop</h3>
            <button className="w-full py-3 bg-red-600 text-white rounded font-medium hover:bg-red-700 transition-colors">
              STOP ALL ROBOTS
            </button>
          </div>

          <div className="bg-white rounded-lg border border-slate-200 p-4">
            <h3 className="font-medium mb-2">Speed Limits</h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-slate-500">Default</span>
                <span>0.8 m/s</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Near Human</span>
                <span>0.2 m/s</span>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg border border-slate-200 p-4">
            <h3 className="font-medium mb-2">Pending Approvals</h3>
            <div className="text-sm text-slate-500">No pending approvals.</div>
          </div>
        </div>

        <div className="bg-white rounded-lg border border-slate-200 p-4">
          <h3 className="font-medium mb-3">Safety Audit Log</h3>
          <div className="text-sm text-slate-500">No safety events recorded.</div>
        </div>
      </div>
    </DashboardShell>
  );
}

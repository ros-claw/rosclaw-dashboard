'use client';

import DashboardShell from '@/components/DashboardShell';

export default function MemoryPage() {
  return (
    <DashboardShell>
      <div className="bg-white rounded-lg border border-slate-200 p-8 text-center">
        <h3 className="text-lg font-medium mb-2">Memory Inspector</h3>
        <p className="text-slate-500">Memory integration with rosclaw-memory is coming in a future sprint.</p>
        <div className="mt-4 grid grid-cols-3 gap-4 text-sm">
          {['Spatial Memory', 'Episodic Memory', 'Skill Memory', 'Failure Memory', 'Object Memory', 'Semantic Map'].map((type) => (
            <div key={type} className="p-3 bg-slate-50 rounded text-slate-500">
              {type}
            </div>
          ))}
        </div>
      </div>
    </DashboardShell>
  );
}

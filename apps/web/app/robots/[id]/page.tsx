'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import DashboardShell from '@/components/DashboardShell';

export default function RobotDetailPage() {
  const { id } = useParams();
  const [robot, setRobot] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (id) api.robots.get(id as string).then(setRobot).finally(() => setLoading(false));
  }, [id]);

  return (
    <DashboardShell>
      <div className="space-y-4">
        <Link href="/" className="text-sm text-rosclaw-600 hover:underline">← Back to Registry</Link>
        {loading ? <div className="text-sm text-slate-500">Loading...</div> : robot ? (
          <div className="bg-white rounded-lg border border-slate-200 p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold">{robot.name}</h2>
              <span className={`px-2 py-1 rounded text-xs font-medium ${robot.status === 'online' ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-100 text-slate-600'}`}>{robot.status}</span>
            </div>
            <dl className="grid grid-cols-2 gap-4 text-sm">
              <div><dt className="text-slate-500">Robot ID</dt><dd className="font-medium">{robot.id}</dd></div>
              <div><dt className="text-slate-500">Model</dt><dd className="font-medium">{robot.model}</dd></div>
              <div><dt className="text-slate-500">e-URDF Version</dt><dd className="font-medium">{robot.eurdf_version}</dd></div>
              <div><dt className="text-slate-500">Registered</dt><dd className="font-medium">{robot.created_at ? new Date(robot.created_at).toLocaleDateString() : '-'}</dd></div>
            </dl>
          </div>
        ) : (
          <div className="text-slate-500">Robot not found.</div>
        )}
      </div>
    </DashboardShell>
  );
}

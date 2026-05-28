'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import DashboardShell from '@/components/DashboardShell';

export default function EmbodimentPage() {
  const [robots, setRobots] = useState<any[]>([]);
  const [selectedRobot, setSelectedRobot] = useState<string>('');
  const [embodiment, setEmbodiment] = useState<any>(null);

  useEffect(() => {
    api.robots.list().then((r: any[]) => {
      setRobots(r);
      if (r.length > 0) setSelectedRobot(r[0].id);
    });
  }, []);

  useEffect(() => {
    if (selectedRobot) api.robots.embodiment(selectedRobot).then(setEmbodiment);
  }, [selectedRobot]);

  return (
    <DashboardShell>
      <div className="space-y-4">
        <div className="flex items-center gap-4">
          <label className="text-sm text-slate-500">Robot:</label>
          <select value={selectedRobot} onChange={(e) => setSelectedRobot(e.target.value)} className="px-3 py-1.5 border border-slate-200 rounded text-sm">
            {robots.map((r) => <option key={r.id} value={r.id}>{r.name} ({r.id})</option>)}
          </select>
        </div>
        {embodiment ? (
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-white rounded-lg border border-slate-200 p-4">
              <h3 className="font-medium mb-3">Sensors ({embodiment.sensors.length})</h3>
              {embodiment.sensors.map((s: any) => (
                <div key={s.id} className="text-sm p-2 bg-slate-50 rounded mb-2">
                  <div className="font-medium">{s.name}</div>
                  <div className="text-slate-500">{s.type} — {s.frame_id}</div>
                </div>
              ))}
            </div>
            <div className="bg-white rounded-lg border border-slate-200 p-4">
              <h3 className="font-medium mb-3">Actuators ({embodiment.actuators.length})</h3>
              {embodiment.actuators.map((a: any) => (
                <div key={a.id} className="text-sm p-2 bg-slate-50 rounded mb-2">
                  <div className="font-medium">{a.name}</div>
                  <div className="text-slate-500">{a.type} — {a.command_topic || 'no topic'}</div>
                </div>
              ))}
            </div>
            <div className="bg-white rounded-lg border border-slate-200 p-4">
              <h3 className="font-medium mb-3">Skills ({embodiment.skills.length})</h3>
              {embodiment.skills.map((s: any) => (
                <div key={s.id} className="text-sm p-2 bg-slate-50 rounded mb-2">
                  <div className="font-medium">{s.name}</div>
                  <div className="text-slate-500">{s.skill_type} {s.approval_required && '• Approval required'}</div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="text-sm text-slate-500">Select a robot to view embodiment.</div>
        )}
      </div>
    </DashboardShell>
  );
}

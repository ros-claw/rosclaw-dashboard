'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import DashboardShell from '@/components/DashboardShell';

export default function SkillsPage() {
  const [robots, setRobots] = useState<any[]>([]);
  const [selectedRobot, setSelectedRobot] = useState<string>('');
  const [skills, setSkills] = useState<any[]>([]);

  useEffect(() => {
    api.robots.list().then((r: any[]) => {
      setRobots(r);
      if (r.length > 0) setSelectedRobot(r[0].id);
    });
  }, []);

  useEffect(() => {
    if (selectedRobot) api.robots.skills(selectedRobot).then(setSkills);
  }, [selectedRobot]);

  return (
    <DashboardShell>
      <div className="space-y-4">
        <div className="flex items-center gap-4">
          <label className="text-sm text-slate-500">Robot:</label>
          <select value={selectedRobot} onChange={(e) => setSelectedRobot(e.target.value)} className="px-3 py-1.5 border border-slate-200 rounded text-sm">
            {robots.map((r) => <option key={r.id} value={r.id}>{r.name}</option>)}
          </select>
        </div>
        <div className="grid grid-cols-2 gap-4">
          {skills.map((skill: any) => (
            <div key={skill.id} className="bg-white rounded-lg border border-slate-200 p-4">
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-medium">{skill.name}</h3>
                <span className={`px-2 py-0.5 rounded text-xs font-medium ${skill.status === 'ready' ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-100 text-slate-600'}`}>{skill.status}</span>
              </div>
              <p className="text-sm text-slate-500 mb-2">{skill.description || 'No description'}</p>
              <div className="text-xs text-slate-400">Type: {skill.skill_type}{skill.approval_required && ' • Approval required'}</div>
            </div>
          ))}
        </div>
        {skills.length === 0 && <div className="bg-white rounded-lg border border-slate-200 p-8 text-center"><p className="text-slate-500">No skills found.</p></div>}
      </div>
    </DashboardShell>
  );
}

'use client';

import { useEffect, useState } from 'react';
import { useReplayStore } from '@/stores/replayStore';
import { api } from '@/lib/api';
import type { ReplayManifestTrajectory } from '@rosclaw/timeline-core';

interface TrajectoryPanelProps {
  trajectory?: ReplayManifestTrajectory;
  runId: string;
}

interface Pose {
  t_rel: number;
  x: number;
  y: number;
}

export default function TrajectoryPanel({ trajectory, runId }: TrajectoryPanelProps) {
  const currentTime = useReplayStore((s) => s.currentTime);
  const [poses, setPoses] = useState<Pose[]>([]);

  useEffect(() => {
    if (!trajectory) return;
    api.runs
      .trajectory(runId)
      .then((data: unknown) => {
        if (!Array.isArray(data)) return;
        const parsed = data
          .map((d) => {
            if (typeof d !== 'object' || d === null) return null;
            const t = (d as { t_rel?: number }).t_rel;
            const x = (d as { x?: number }).x;
            const y = (d as { y?: number }).y;
            return typeof t === 'number' && typeof x === 'number' && typeof y === 'number'
              ? { t_rel: t, x, y }
              : null;
          })
          .filter((p): p is Pose => p !== null);
        setPoses(parsed);
      })
      .catch(() => setPoses([]));
  }, [trajectory, runId]);

  if (!trajectory || poses.length === 0) {
    return (
      <div className="bg-slate-100 border border-slate-200 rounded-lg flex items-center justify-center h-48 text-sm text-slate-500">
        No trajectory available
      </div>
    );
  }

  const xs = poses.map((p) => p.x);
  const ys = poses.map((p) => p.y);
  const minX = Math.min(...xs);
  const maxX = Math.max(...xs);
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys);
  const rangeX = maxX - minX || 1;
  const rangeY = maxY - minY || 1;
  const pad = 10;
  const width = 280;
  const height = 180;

  const scaleX = (x: number) => pad + ((x - minX) / rangeX) * (width - pad * 2);
  const scaleY = (y: number) => height - (pad + ((y - minY) / rangeY) * (height - pad * 2));

  const path = poses
    .map((p, i) => `${i === 0 ? 'M' : 'L'} ${scaleX(p.x)} ${scaleY(p.y)}`)
    .join(' ');

  const current = poses.reduce((best, p) => {
    if (!best || Math.abs(p.t_rel - currentTime) < Math.abs(best.t_rel - currentTime)) {
      return p;
    }
    return best;
  }, null as Pose | null);

  return (
    <div className="bg-white border border-slate-200 rounded-lg p-3">
      <p className="text-xs font-medium text-slate-500 mb-2">
        Trajectory ({poses.length} poses)
      </p>
      <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-48">
        <rect width={width} height={height} fill="#f8fafc" />
        <path d={path} fill="none" stroke="#0ea5e9" strokeWidth={2} />
        {current && (
          <circle
            cx={scaleX(current.x)}
            cy={scaleY(current.y)}
            r={5}
            fill="#ef4444"
          />
        )}
      </svg>
    </div>
  );
}

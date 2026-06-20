'use client';

import { useEffect, useState } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
} from 'recharts';
import { useReplayStore } from '@/stores/replayStore';
import { api } from '@/lib/api';
import type { ReplayManifestCurve } from '@rosclaw/timeline-core';

interface CurvesPanelProps {
  curves: ReplayManifestCurve[];
  runId: string;
}

interface Sample {
  t_rel: number;
  value: number;
}

export default function CurvesPanel({ curves, runId }: CurvesPanelProps) {
  const currentTime = useReplayStore((s) => s.currentTime);
  const [samples, setSamples] = useState<Sample[]>([]);

  useEffect(() => {
    if (curves.length === 0) return;
    const first = curves[0];
    api.runs
      .curves(runId, first.name)
      .then((data: unknown) => {
        if (!Array.isArray(data)) return;
        const parsed = data
          .map((d) => {
            if (typeof d !== 'object' || d === null) return null;
            const t = (d as { t_rel?: number }).t_rel;
            let v = (d as { value?: number }).value;
            if (typeof v !== 'number') {
              const values = Object.values(d).filter(
                (x): x is number => typeof x === 'number',
              );
              v = values.length > 1 ? values[1] : NaN;
            }
            return typeof t === 'number' && typeof v === 'number'
              ? { t_rel: t, value: v }
              : null;
          })
          .filter((s): s is Sample => s !== null);
        setSamples(parsed);
      })
      .catch(() => setSamples([]));
  }, [curves, runId]);

  if (curves.length === 0) {
    return (
      <div className="bg-slate-100 border border-slate-200 rounded-lg flex items-center justify-center h-48 text-sm text-slate-500">
        No curves available
      </div>
    );
  }

  return (
    <div className="bg-white border border-slate-200 rounded-lg p-3">
      <p className="text-xs font-medium text-slate-500 mb-2">
        Curve: {curves[0].name} ({samples.length} samples)
      </p>
      <div className="h-48">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={samples} margin={{ top: 5, right: 5, bottom: 5, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis dataKey="t_rel" type="number" tick={{ fontSize: 10 }} />
            <YAxis tick={{ fontSize: 10 }} />
            <Tooltip />
            <Line
              type="monotone"
              dataKey="value"
              stroke="#0ea5e9"
              strokeWidth={2}
              dot={false}
              isAnimationActive={false}
            />
            <ReferenceLine x={currentTime} stroke="#ef4444" strokeDasharray="4 4" />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

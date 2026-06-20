'use client';

import { useState } from 'react';
import { api } from '@/lib/api';
import type { ExportJobCreate, ExportJobStatus } from '@rosclaw/timeline-core';

interface ExportPanelProps {
  runId: string;
}

const FORMATS: { key: ExportJobCreate['format']; label: string }[] = [
  { key: 'rlds', label: 'RLDS' },
  { key: 'lerobot', label: 'LeRobot' },
  { key: 'failure_case', label: 'Failure Case' },
  { key: 'skill_candidate', label: 'Skill Candidate' },
];

export default function ExportPanel({ runId }: ExportPanelProps) {
  const [jobs, setJobs] = useState<ExportJobStatus[]>([]);

  const startExport = async (format: ExportJobCreate['format']) => {
    try {
      const job = await api.export.create({ run_id: runId, format });
      setJobs((prev) => [...prev, job]);
      pollJob(job.job_id);
    } catch (err) {
      // eslint-disable-next-line no-console
      console.error('Export failed', err);
    }
  };

  const pollJob = (jobId: string) => {
    const interval = setInterval(async () => {
      try {
        const job = await api.export.get(jobId);
        setJobs((prev) => prev.map((j) => (j.job_id === jobId ? job : j)));
        if (job.state === 'completed' || job.state === 'failed') {
          clearInterval(interval);
        }
      } catch {
        clearInterval(interval);
      }
    }, 1500);
  };

  return (
    <div className="bg-white border border-slate-200 rounded-lg overflow-hidden">
      <div className="px-4 py-2 border-b border-slate-200 bg-slate-50 text-sm font-medium text-slate-700">
        Export
      </div>
      <div className="p-4 space-y-4">
        <div className="grid grid-cols-2 gap-2">
          {FORMATS.map(({ key, label }) => (
            <button
              key={key}
              onClick={() => startExport(key)}
              className="px-3 py-2 rounded border border-slate-300 text-sm hover:bg-slate-50"
            >
              {label}
            </button>
          ))}
        </div>

        {jobs.length > 0 && (
          <div className="space-y-2">
            {jobs.map((job) => (
              <div
                key={job.job_id}
                className="text-sm border border-slate-100 rounded p-2 flex items-center justify-between gap-2"
              >
                <div className="min-w-0">
                  <p className="font-medium text-slate-700 truncate">
                    {job.format} · {job.state}
                  </p>
                  <div className="w-full bg-slate-100 rounded h-1.5 mt-1">
                    <div
                      className={`h-1.5 rounded ${
                        job.state === 'failed'
                          ? 'bg-rose-500'
                          : job.state === 'completed'
                            ? 'bg-emerald-500'
                            : 'bg-blue-500'
                      }`}
                      style={{ width: `${Math.max(5, job.progress * 100)}%` }}
                    />
                  </div>
                  {job.error && <p className="text-xs text-rose-600 mt-1">{job.error}</p>}
                </div>
                {job.state === 'completed' && job.result_url && (
                  <a
                    href={api.export.downloadUrl(job.job_id)}
                    download
                    className="px-3 py-1 rounded bg-emerald-600 text-white text-xs hover:bg-emerald-700 whitespace-nowrap"
                  >
                    Download
                  </a>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

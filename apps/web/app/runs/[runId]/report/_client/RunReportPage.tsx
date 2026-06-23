'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import DashboardShell from '@/components/DashboardShell';

interface ReportSection {
  title: string;
  status: string;
  findings: string[];
  evidence?: Record<string, any>;
}

interface Report {
  run_id: string;
  generated_at: number;
  verdict: 'PASS' | 'PARTIAL' | 'FAIL';
  summary: string;
  sections: ReportSection[];
  artifacts: { name: string; path: string; mime_type: string }[];
}

export default function RunReportPage() {
  const params = useParams();
  const runId = (params?.runId as string) || '';
  const [report, setReport] = useState<Report | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadReport = async () => {
    if (!runId) return;
    setLoading(true);
    try {
      const res = await api.runs.report.get(runId);
      setReport(res.report);
      setError(null);
    } catch (err: any) {
      if (err.message?.includes('404') || err.message?.includes('not found')) {
        setReport(null);
      } else {
        setError(err.message || 'Failed to load report');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReport();
  }, [runId]);

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      const res = await api.runs.report.create(runId);
      setReport(res.report);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to generate report');
    } finally {
      setGenerating(false);
    }
  };

  const verdictColor =
    report?.verdict === 'PASS'
      ? 'bg-emerald-100 text-emerald-800'
      : report?.verdict === 'FAIL'
        ? 'bg-rose-100 text-rose-800'
        : 'bg-amber-100 text-amber-800';

  return (
    <DashboardShell>
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-sm text-slate-500">
              <Link href="/runs" className="hover:text-rosclaw-600">Runs</Link>
              <span>/</span>
              <Link href={`/runs/${runId}`} className="hover:text-rosclaw-600">{runId}</Link>
              <span>/</span>
              <span>Acceptance Report</span>
            </div>
            <h1 className="text-xl font-semibold text-slate-800">Acceptance Report</h1>
          </div>
          <div className="flex items-center gap-3">
            {report && (
              <a
                href={api.runs.report.downloadUrl(runId)}
                download
                className="px-4 py-2 bg-slate-800 text-white text-sm rounded hover:bg-slate-900"
              >
                Download
              </a>
            )}
            <button
              onClick={handleGenerate}
              disabled={generating}
              className="px-4 py-2 bg-rosclaw-600 text-white text-sm rounded hover:bg-rosclaw-700 disabled:opacity-50"
            >
              {generating ? 'Generating...' : report ? 'Regenerate' : 'Generate Report'}
            </button>
          </div>
        </div>

        {loading && <div className="text-sm text-slate-500">Loading report...</div>}

        {error && (
          <div className="bg-rose-50 border border-rose-200 text-rose-700 px-4 py-3 rounded text-sm">
            {error}
          </div>
        )}

        {!loading && !report && !error && (
          <div className="bg-white border border-slate-200 rounded-lg p-8 text-center space-y-4">
            <p className="text-slate-500">No acceptance report has been generated for this run yet.</p>
            <button
              onClick={handleGenerate}
              disabled={generating}
              className="px-4 py-2 bg-rosclaw-600 text-white text-sm rounded hover:bg-rosclaw-700 disabled:opacity-50"
            >
              {generating ? 'Generating...' : 'Generate Report'}
            </button>
          </div>
        )}

        {report && (
          <div className="space-y-4">
            <div className="bg-white border border-slate-200 rounded-lg p-4 flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Verdict</p>
                <span className={`px-2 py-1 rounded text-sm font-semibold ${verdictColor}`}>
                  {report.verdict}
                </span>
              </div>
              <div className="text-right">
                <p className="text-sm text-slate-500">Generated</p>
                <p className="text-sm text-slate-700">
                  {new Date(report.generated_at * 1000).toLocaleString()}
                </p>
              </div>
            </div>

            <div className="bg-white border border-slate-200 rounded-lg p-4">
              <h2 className="font-medium text-slate-800 mb-2">Summary</h2>
              <p className="text-sm text-slate-600">{report.summary}</p>
            </div>

            <div className="bg-white border border-slate-200 rounded-lg p-4 space-y-4">
              <h2 className="font-medium text-slate-800">Sections</h2>
              {report.sections.map((section) => (
                <div key={section.title} className="border-t border-slate-100 pt-3 first:border-0 first:pt-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="text-sm font-semibold text-slate-700">{section.title}</h3>
                    <span
                      className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${
                        section.status === 'pass'
                          ? 'bg-emerald-100 text-emerald-700'
                          : section.status === 'fail'
                            ? 'bg-rose-100 text-rose-700'
                            : 'bg-slate-100 text-slate-600'
                      }`}
                    >
                      {section.status}
                    </span>
                  </div>
                  <ul className="list-disc list-inside text-sm text-slate-600">
                    {section.findings.map((finding, idx) => (
                      <li key={idx}>{finding}</li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </DashboardShell>
  );
}

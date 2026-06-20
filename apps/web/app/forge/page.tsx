'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import DashboardShell from '@/components/DashboardShell';

export default function ForgePage() {
  const [bundles, setBundles] = useState<any[]>([]);
  const [sdkDoc, setSdkDoc] = useState('');
  const [target, setTarget] = useState('mcp_server');
  const [compiling, setCompiling] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.forge.bundles().then((r) => {
      setBundles(r.bundles || []);
      setLoading(false);
    });
  }, []);

  const compile = async () => {
    setCompiling(true);
    try {
      const res = await api.forge.compile({ sdk_doc: sdkDoc, target, staging: true });
      setResult(res);
      const list = await api.forge.bundles();
      setBundles(list.bundles || []);
    } finally {
      setCompiling(false);
    }
  };

  return (
    <DashboardShell>
      <div className="space-y-6">
        <div className="bg-white rounded-lg border border-slate-200 p-4 space-y-4">
          <h2 className="font-medium text-slate-800">Forge Bundle Compiler</h2>
          <div className="space-y-2">
            <label className="text-sm text-slate-500">SDK Description</label>
            <textarea
              value={sdkDoc}
              onChange={(e) => setSdkDoc(e.target.value)}
              rows={4}
              className="w-full border border-slate-200 rounded p-2 text-sm"
              placeholder="Paste a hardware SDK description..."
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm text-slate-500">Target</label>
            <select
              value={target}
              onChange={(e) => setTarget(e.target.value)}
              className="w-full border border-slate-200 rounded p-2 text-sm"
            >
              <option value="mcp_server">MCP Server</option>
              <option value="skill_package">Skill Package</option>
              <option value="provider_manifest">Provider Manifest</option>
              <option value="eurdf_patch">e-URDF Patch</option>
              <option value="sandbox_spec">Sandbox Spec</option>
            </select>
          </div>
          <button
            onClick={compile}
            disabled={!sdkDoc || compiling}
            className="px-4 py-2 bg-rosclaw-600 text-white text-sm rounded hover:bg-rosclaw-700 disabled:opacity-50"
          >
            {compiling ? 'Compiling...' : 'Compile & Validate'}
          </button>

          {result && (
            <div className={`rounded p-3 text-sm space-y-2 ${result.status === 'validated' ? 'bg-emerald-50 border border-emerald-200' : 'bg-rose-50 border border-rose-200'}`}>
              <p className="font-medium">Status: {result.status}</p>
              <p className="text-slate-600">Bundle ID: {result.bundle_id}</p>
              <div className="text-xs text-slate-500">
                Checks:
                <ul className="mt-1 space-y-0.5">
                  {result.validation.checks.map((c: any) => (
                    <li key={c.name} className={c.passed ? 'text-emerald-700' : 'text-rose-700'}>
                      {c.name}: {c.passed ? 'PASS' : 'FAIL'}
                    </li>
                  ))}
                </ul>
              </div>
              {result.staging_path && <p className="text-xs text-slate-500">Staging: {result.staging_path}</p>}
              {result.validation.errors?.length > 0 && (
                <div className="text-xs text-rose-700">Errors: {result.validation.errors.join(', ')}</div>
              )}
            </div>
          )}
        </div>

        <div className="bg-white rounded-lg border border-slate-200 p-4">
          <h3 className="font-medium text-slate-800 mb-3">Generated Bundles</h3>
          {loading ? (
            <p className="text-sm text-slate-500">Loading...</p>
          ) : bundles.length === 0 ? (
            <p className="text-sm text-slate-500">No bundles generated yet.</p>
          ) : (
            <div className="space-y-2">
              {bundles.map((b) => (
                <div key={b.bundle_id} className="border border-slate-100 rounded p-3 text-sm">
                  <div className="flex justify-between">
                    <span className="font-medium">{b.bundle_id}</span>
                    <span className={`text-xs px-2 py-0.5 rounded ${b.validation?.valid ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'}`}>
                      {b.validation?.valid ? 'validated' : 'blocked'}
                    </span>
                  </div>
                  <p className="text-xs text-slate-500">Target: {b.target} · Files: {b.files?.length}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </DashboardShell>
  );
}

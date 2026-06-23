'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import DashboardShell from '@/components/DashboardShell';

interface BundleFile {
  path: string;
  content: string;
  size: number;
}

interface Bundle {
  bundle_id: string;
  target: string;
  status: string;
  files: BundleFile[];
  validation: {
    valid?: boolean;
    checks?: { name: string; passed: boolean }[];
    errors?: string[];
    warnings?: string[];
  };
  created_at?: string;
}

export default function ForgePage() {
  const [bundles, setBundles] = useState<any[]>([]);
  const [selected, setSelected] = useState<Bundle | null>(null);
  const [sdkDoc, setSdkDoc] = useState('');
  const [target, setTarget] = useState('mcp_server');
  const [compiling, setCompiling] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [activeFile, setActiveFile] = useState<BundleFile | null>(null);
  const [search, setSearch] = useState('');

  useEffect(() => {
    loadBundles();
  }, []);

  const loadBundles = async () => {
    setLoading(true);
    const r = await api.forge.bundles();
    setBundles(r.bundles || []);
    setLoading(false);
  };

  const compile = async () => {
    setCompiling(true);
    try {
      const res = await api.forge.compile({ sdk_doc: sdkDoc, target, staging: true });
      setResult(res);
      await loadBundles();
    } finally {
      setCompiling(false);
    }
  };

  const selectBundle = async (bundleId: string) => {
    const b = await api.forge.get(bundleId);
    setSelected(b);
    setActiveFile(b.files?.[0] || null);
  };

  const filteredBundles = search
    ? bundles.filter((b) =>
        b.bundle_id.toLowerCase().includes(search.toLowerCase()) ||
        b.target.toLowerCase().includes(search.toLowerCase())
      )
    : bundles;

  const validCount = bundles.filter((b) => b.validation?.valid).length;
  const blockedCount = bundles.length - validCount;

  return (
    <DashboardShell>
      <div className="space-y-6">
        {/* Compiler */}
        <div className="bg-white rounded-lg border border-slate-200 p-4 space-y-4">
          <h2 className="font-medium text-slate-800">Forge Bundle Compiler</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <input
              value={sdkDoc}
              onChange={(e) => setSdkDoc(e.target.value)}
              placeholder="Paste a hardware SDK description..."
              className="border border-slate-200 rounded p-2 text-sm md:col-span-2"
            />
            <select
              value={target}
              onChange={(e) => setTarget(e.target.value)}
              className="border border-slate-200 rounded p-2 text-sm"
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

        {/* Summary */}
        <div className="flex gap-4">
          <div className="bg-white rounded border border-slate-200 px-4 py-3 text-sm">
            <span className="text-slate-500">Total: </span>
            <span className="font-medium">{bundles.length}</span>
          </div>
          <div className="bg-white rounded border border-slate-200 px-4 py-3 text-sm">
            <span className="text-slate-500">Validated: </span>
            <span className="font-medium text-emerald-700">{validCount}</span>
          </div>
          <div className="bg-white rounded border border-slate-200 px-4 py-3 text-sm">
            <span className="text-slate-500">Blocked: </span>
            <span className="font-medium text-rose-700">{blockedCount}</span>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Bundle list */}
          <div className="lg:col-span-1 bg-white rounded-lg border border-slate-200 p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-medium text-slate-800">Generated Bundles</h3>
              <button onClick={loadBundles} className="text-xs px-2 py-1 border border-slate-200 rounded hover:bg-slate-50">Refresh</button>
            </div>
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search bundles..."
              className="w-full border border-slate-200 rounded p-2 text-sm mb-3"
            />
            {loading ? (
              <p className="text-sm text-slate-500">Loading...</p>
            ) : filteredBundles.length === 0 ? (
              <p className="text-sm text-slate-500">No bundles found.</p>
            ) : (
              <div className="space-y-2">
                {filteredBundles.map((b) => (
                  <button
                    key={b.bundle_id}
                    onClick={() => selectBundle(b.bundle_id)}
                    className={`w-full text-left border rounded p-3 text-sm hover:border-rosclaw-400 transition-colors ${
                      selected?.bundle_id === b.bundle_id ? 'border-rosclaw-500 bg-rosclaw-50' : 'border-slate-100'
                    }`}
                  >
                    <div className="flex justify-between">
                      <span className="font-medium truncate">{b.bundle_id}</span>
                      <span className={`text-xs px-2 py-0.5 rounded shrink-0 ml-2 ${b.validation?.valid ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'}`}>
                        {b.validation?.valid ? 'validated' : 'blocked'}
                      </span>
                    </div>
                    <p className="text-xs text-slate-500">Target: {b.target} · Files: {b.files?.length}</p>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Bundle detail */}
          <div className="lg:col-span-2 bg-white rounded-lg border border-slate-200 p-4">
            {!selected ? (
              <div className="h-48 flex items-center justify-center text-sm text-slate-500">Select a bundle to view details.</div>
            ) : (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-medium text-slate-800">{selected.bundle_id}</h3>
                    <p className="text-xs text-slate-500">Target: {selected.target} · Created: {selected.created_at}</p>
                  </div>
                  <span className={`text-xs px-2 py-1 rounded font-medium ${
                    selected.status === 'validated' ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'
                  }`}>{selected.status}</span>
                </div>

                {/* Validation drill-down */}
                {selected.validation && (
                  <div className="bg-slate-50 rounded p-3 text-sm">
                    <p className="font-medium mb-2">Validation Checks</p>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                      {(selected.validation.checks || []).map((c) => (
                        <div key={c.name} className="flex items-center justify-between bg-white rounded px-3 py-2 border border-slate-100">
                          <span className="text-slate-600">{c.name}</span>
                          <span className={`text-xs px-2 py-0.5 rounded font-medium ${c.passed ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'}`}>
                            {c.passed ? 'PASS' : 'FAIL'}
                          </span>
                        </div>
                      ))}
                    </div>
                    {selected.validation.errors && selected.validation.errors.length > 0 && (
                      <div className="mt-2 text-xs text-rose-700">Errors: {selected.validation.errors.join(', ')}</div>
                    )}
                    {selected.validation.warnings && selected.validation.warnings.length > 0 && (
                      <div className="mt-2 text-xs text-amber-700">Warnings: {selected.validation.warnings.join(', ')}</div>
                    )}
                  </div>
                )}

                {/* File tree + preview */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div className="md:col-span-1 border border-slate-100 rounded">
                    <p className="text-xs font-medium text-slate-500 px-3 py-2 border-b border-slate-100">Files</p>
                    <div className="p-2 space-y-1">
                      {selected.files.map((f) => (
                        <button
                          key={f.path}
                          onClick={() => setActiveFile(f)}
                          className={`w-full text-left text-xs px-2 py-1.5 rounded truncate ${
                            activeFile?.path === f.path ? 'bg-rosclaw-100 text-rosclaw-800' : 'hover:bg-slate-50 text-slate-600'
                          }`}
                        >
                          {f.path}
                        </button>
                      ))}
                    </div>
                  </div>
                  <div className="md:col-span-3 border border-slate-100 rounded">
                    <div className="flex items-center justify-between px-3 py-2 border-b border-slate-100">
                      <span className="text-xs font-medium text-slate-500">{activeFile?.path || 'No file selected'}</span>
                      {activeFile && <span className="text-xs text-slate-400">{activeFile.size} bytes</span>}
                    </div>
                    <pre className="p-3 text-xs overflow-auto max-h-96 text-slate-600">
                      {activeFile?.content || 'Select a file to preview.'}
                    </pre>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </DashboardShell>
  );
}

import type {
  TraceEvent,
  RunSummary,
  RunDetail,
  ReplayManifest,
  EventFilter,
  ExportJobCreate,
  ExportJobStatus,
} from '@rosclaw/timeline-core';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

function buildQuery(params?: Record<string, string | number | undefined>): string {
  if (!params) return '';
  const entries = Object.entries(params).filter(([, v]) => v !== undefined && v !== '');
  if (entries.length === 0) return '';
  const qs = new URLSearchParams();
  for (const [k, v] of entries) qs.set(k, String(v));
  return `?${qs.toString()}`;
}

async function fetchApi(path: string, options?: RequestInit) {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || `HTTP ${res.status}`);
  }
  return res.json();
}

export const api = {
  robots: {
    list: () => fetchApi('/api/robots'),
    get: (id: string) => fetchApi(`/api/robots/${id}`),
    create: (data: any) => fetchApi('/api/robots', { method: 'POST', body: JSON.stringify(data) }),
    import: (data: any) => fetchApi('/api/robots/import', { method: 'POST', body: JSON.stringify(data) }),
    embodiment: (id: string) => fetchApi(`/api/robots/${id}/embodiment`),
    sensors: (id: string) => fetchApi(`/api/robots/${id}/sensors`),
    actuators: (id: string) => fetchApi(`/api/robots/${id}/actuators`),
    skills: (id: string) => fetchApi(`/api/robots/${id}/skills`),
    health: (id: string) => fetchApi(`/api/robots/${id}/health`),
  },
  missions: {
    list: () => fetchApi('/api/missions'),
    get: (id: string) => fetchApi(`/api/missions/${id}`),
    create: (data: any) => fetchApi('/api/missions', { method: 'POST', body: JSON.stringify(data) }),
    pause: (id: string) => fetchApi(`/api/missions/${id}/pause`, { method: 'POST' }),
    resume: (id: string) => fetchApi(`/api/missions/${id}/resume`, { method: 'POST' }),
    abort: (id: string) => fetchApi(`/api/missions/${id}/abort`, { method: 'POST' }),
    trace: (id: string) => fetchApi(`/api/missions/${id}/trace`),
  },
  skills: {
    list: () => fetchApi('/api/skills'),
    get: (id: string) => fetchApi(`/api/skills/${id}`),
  },
  mcap: {
    list: () => fetchApi('/api/mcap'),
    get: (id: string) => fetchApi(`/api/mcap/${id}`),
    import: (data: any) => fetchApi('/api/mcap/import', { method: 'POST', body: JSON.stringify(data) }),
    topics: (id: string) => fetchApi(`/api/mcap/${id}/topics`),
    foxgloveLayout: (id: string) => fetchApi(`/api/mcap/${id}/foxglove-layout`),
  },
  memory: {
    list: () => fetchApi('/api/memory'),
    stats: () => fetchApi('/api/memory/stats/summary'),
    explain: (data: { question: string; run_id?: string; robot_id?: string }) =>
      fetchApi('/api/memory/explain', { method: 'POST', body: JSON.stringify(data) }),
  },
  how: {
    recovery: (data: { run_id: string; failure_event_id?: string }) =>
      fetchApi('/api/how/recovery', { method: 'POST', body: JSON.stringify(data) }),
  },
  status: {
    get: () => fetchApi('/api/status'),
  },
  mcp: {
    tools: () => fetchApi('/api/mcp/tools'),
    call: (tool: string, arguments_?: Record<string, any>) =>
      fetchApi('/api/mcp/call', { method: 'POST', body: JSON.stringify({ tool, arguments: arguments_ || {} }) }),
  },
  forge: {
    compile: (data: { sdk_doc: string; target?: string; staging?: boolean }) =>
      fetchApi('/api/forge/compile', { method: 'POST', body: JSON.stringify(data) }) as Promise<any>,
    validate: (data: { bundle_id: string; bundle: any }) =>
      fetchApi('/api/forge/validate', { method: 'POST', body: JSON.stringify(data) }) as Promise<any>,
    bundles: () => fetchApi('/api/forge/bundles') as Promise<{ bundles: any[] }>,
  },
  safety: {
    audits: () => fetchApi('/api/safety/audits'),
    rules: () => fetchApi('/api/safety/rules'),
    toggleRule: (id: string) => fetchApi(`/api/safety/rules/${id}/toggle`, { method: 'POST' }),
  },
  providers: {
    list: () => fetchApi('/api/providers'),
    get: (id: string) => fetchApi(`/api/providers/${id}`),
  },
  episodes: {
    list: () => fetchApi('/api/episodes'),
    trace: (id: string) => fetchApi(`/api/episodes/${id}/trace`),
  },
  runtime: {
    list: () => fetchApi('/api/runtime'),
    status: (id: string) => fetchApi(`/api/runtime/${id}/status`),
  },
  runs: {
    list: (params?: { status?: string; search?: string; limit?: number; offset?: number }) =>
      fetchApi(`/api/runs${buildQuery(params)}`),
    get: (runId: string) => fetchApi(`/api/runs/${runId}`) as Promise<RunDetail>,
    events: (
      runId: string,
      params?: { track?: string; type?: string; severity?: string; limit?: number; offset?: number },
    ) => fetchApi(`/api/runs/${runId}/events${buildQuery(params)}`),
    filterEvents: (runId: string, filter: EventFilter) =>
      fetchApi(`/api/runs/${runId}/events/filter`, {
        method: 'POST',
        body: JSON.stringify(filter),
      }),
    searchEvents: (runId: string, eventId: string, windowSec = 5.0) =>
      fetchApi(
        `/api/runs/${runId}/events/search?event_id=${encodeURIComponent(eventId)}&window_sec=${windowSec}`,
      ),
    failures: (runId: string) => fetchApi(`/api/runs/${runId}/failures`),
    replay: (runId: string) => fetchApi(`/api/runs/${runId}/replay`) as Promise<ReplayManifest>,
    curves: (runId: string, curveName: string) =>
      fetchApi(`/api/runs/${runId}/curves/${encodeURIComponent(curveName)}`),
    trajectory: (runId: string) => fetchApi(`/api/runs/${runId}/trajectory`),
  },
  export: {
    create: (data: ExportJobCreate) =>
      fetchApi('/api/export', { method: 'POST', body: JSON.stringify(data) }) as Promise<ExportJobStatus>,
    get: (jobId: string) => fetchApi(`/api/export/${jobId}`) as Promise<ExportJobStatus>,
    list: (runId?: string) =>
      fetchApi(`/api/export${buildQuery({ run_id: runId, limit: 100, offset: 0 })}`),
    downloadUrl: (jobId: string) => `${API_BASE}/api/export/${jobId}/download`,
  },
  media: {
    url: (runId: string, path: string) =>
      `${API_BASE}/api/runs/${runId}/media/${encodeURIComponent(path)}`,
  },
};

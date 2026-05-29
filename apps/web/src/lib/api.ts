const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

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
};

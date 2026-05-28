/**
 * ROSClaw SDK
 *
 * Client SDK for integrating with the ROSClaw Dashboard API.
 * Provides typed methods for robots, missions, MCAP, and skills.
 */

export interface SDKConfig {
  baseURL: string;
  apiKey?: string;
}

export class ROSClawSDK {
  private baseURL: string;
  private apiKey?: string;

  constructor(config: SDKConfig) {
    this.baseURL = config.baseURL.replace(/\/$/, '');
    this.apiKey = config.apiKey;
  }

  private async request(path: string, options?: RequestInit) {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...((options?.headers as Record<string, string>) || {}),
    };
    if (this.apiKey) headers['X-API-Key'] = this.apiKey;

    const res = await fetch(`${this.baseURL}${path}`, { ...options, headers });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  }

  async listRobots() {
    return this.request('/api/robots');
  }

  async getRobot(id: string) {
    return this.request(`/api/robots/${id}`);
  }

  async listMissions() {
    return this.request('/api/missions');
  }

  async getMissionTrace(id: string) {
    return this.request(`/api/missions/${id}/trace`);
  }

  async listMCAP() {
    return this.request('/api/mcap');
  }
}

export default ROSClawSDK;

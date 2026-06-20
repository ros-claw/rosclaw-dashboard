/**
 * Timeline Core
 *
 * Unified timeline engine that correlates:
 * - MCAP playback time
 * - Agent execution events
 * - Skill runs
 * - Safety events
 * - Memory writes
 *
 * MVP: placeholder data structures. Full implementation provides
 * a reactive timeline with swimlanes for each event category.
 */

export interface TimelineEvent {
  id: string;
  timestamp: number;
  type: 'intent' | 'skill' | 'safety' | 'memory' | 'sensor' | 'ros_action' | 'failure' | 'human';
  label: string;
  mission_id: string;
  metadata: Record<string, unknown>;
}

export interface TimelineLane {
  id: string;
  label: string;
  color: string;
  events: TimelineEvent[];
}

export interface TimelineState {
  startTime: number;
  endTime: number;
  currentTime: number;
  playing: boolean;
  speed: number;
  lanes: TimelineLane[];
}

export function createTimelineState(events: TimelineEvent[]): TimelineState {
  if (events.length === 0) {
    return {
      startTime: 0,
      endTime: 0,
      currentTime: 0,
      playing: false,
      speed: 1,
      lanes: [],
    };
  }

  const times = events.map((e) => e.timestamp);
  const byType = new Map<string, TimelineEvent[]>();

  for (const e of events) {
    const list = byType.get(e.type) || [];
    list.push(e);
    byType.set(e.type, list);
  }

  const laneColors: Record<TimelineEvent['type'], string> = {
    intent: '#3b82f6',
    skill: '#10b981',
    safety: '#f59e0b',
    memory: '#8b5cf6',
    sensor: '#06b6d4',
    ros_action: '#0ea5e9',
    failure: '#ef4444',
    human: '#ec4899',
  };

  const lanes: TimelineLane[] = [];
  for (const [type, typeEvents] of byType) {
    lanes.push({
      id: type,
      label: type.charAt(0).toUpperCase() + type.slice(1),
      color: laneColors[type as TimelineEvent['type']] || '#64748b',
      events: typeEvents.sort((a, b) => a.timestamp - b.timestamp),
    });
  }

  return {
    startTime: Math.min(...times),
    endTime: Math.max(...times),
    currentTime: Math.min(...times),
    playing: false,
    speed: 1,
    lanes,
  };
}

/** Physical Trace Viewer event tracks. */
export type TraceTrack =
  | 'task'
  | 'agent'
  | 'tool'
  | 'provider'
  | 'sandbox'
  | 'runtime'
  | 'robot'
  | 'critic'
  | 'memory'
  | 'auto'
  | 'failure';

export const TRACE_TRACKS: TraceTrack[] = [
  'task',
  'agent',
  'tool',
  'provider',
  'sandbox',
  'runtime',
  'robot',
  'critic',
  'memory',
  'auto',
  'failure',
];

export const TRACK_COLORS: Record<TraceTrack, string> = {
  task: '#3b82f6',
  agent: '#10b981',
  tool: '#f59e0b',
  provider: '#8b5cf6',
  sandbox: '#06b6d4',
  runtime: '#0ea5e9',
  robot: '#ec4899',
  critic: '#6366f1',
  memory: '#64748b',
  auto: '#14b8a6',
  failure: '#ef4444',
};

/** Normalized trace event produced by the run indexer. */
export interface TraceEvent {
  id: string;
  run_id: string;
  ts: number;
  t_rel: number;
  source: string;
  type: string;
  track: TraceTrack;
  severity: string;
  title: string;
  summary?: string;
  entity?: string;
  payload?: Record<string, unknown>;
  links?: string[];
  tags?: string[];
}

export interface EventFilter {
  track?: TraceTrack;
  type?: string;
  severity?: string;
  entity?: string;
  start_t?: number;
  end_t?: number;
  tags?: string[];
  limit?: number;
  offset?: number;
}

export interface RunSummary {
  run_id: string;
  status: string;
  robot_id?: string;
  task?: string;
  started_at?: number;
  ended_at?: number;
  duration_sec?: number;
  event_count?: number;
  failure_count?: number;
  tracks?: TraceTrack[];
  has_media?: boolean;
  has_trajectory?: boolean;
  has_curves?: boolean;
  manifest_path?: string;
}

export interface RunDetail extends RunSummary {
  manifest?: Record<string, unknown>;
}

export interface ReplayManifestMedia {
  kind: 'video' | 'image' | 'audio' | string;
  path: string;
  name?: string;
  url: string;
  mime_type?: string;
  start_t_rel?: number;
  end_t_rel?: number;
}

export interface ReplayManifestCurve {
  name: string;
  url: string;
  sample_count?: number;
  start_t_rel?: number;
  end_t_rel?: number;
}

export interface ReplayManifestTrajectory {
  url: string;
  sample_count?: number;
  start_t_rel?: number;
  end_t_rel?: number;
}

export interface ReplayManifest {
  run_id: string;
  duration_sec: number;
  tracks: TraceTrack[];
  media: ReplayManifestMedia[];
  curves: ReplayManifestCurve[];
  trajectory?: ReplayManifestTrajectory;
  sandbox_states?: Record<string, unknown>[];
}

export interface ExportJobCreate {
  run_id: string;
  format: 'rlds' | 'lerobot' | 'failure_case' | 'skill_candidate';
  params?: {
    start_t?: number;
    end_t?: number;
  };
}

export interface ExportJobStatus {
  job_id: string;
  run_id: string;
  format: string;
  state: 'queued' | 'running' | 'validating' | 'packaging' | 'completed' | 'failed';
  progress: number;
  result_url?: string;
  error?: string;
  created_at?: number;
  updated_at?: number;
}

export function groupByTrack(events: TraceEvent[]): Record<TraceTrack, TraceEvent[]> {
  const groups = {} as Record<TraceTrack, TraceEvent[]>;
  for (const track of TRACE_TRACKS) {
    groups[track] = [];
  }
  for (const e of events) {
    if (!groups[e.track]) groups[e.track] = [];
    groups[e.track].push(e);
  }
  return groups;
}

export function findFailures(events: TraceEvent[]): TraceEvent[] {
  return events.filter((e) => e.track === 'failure' || e.severity === 'failure');
}

export function findRelated(
  events: TraceEvent[],
  event: TraceEvent,
  windowSec = 5.0,
): TraceEvent[] {
  const eventLinks = new Set(event.links || []);
  const eventTags = new Set(event.tags || []);
  return events.filter((e) => {
    if (e.id === event.id) return false;
    const eLinks = new Set(e.links || []);
    const isLinked =
      eventLinks.has(e.id) ||
      eLinks.has(event.id) ||
      [...eventLinks].some((l) => eLinks.has(l));
    if (isLinked) return true;
    const inWindow = Math.abs(e.t_rel - event.t_rel) <= windowSec;
    const sharesEntity = Boolean(event.entity && e.entity === event.entity);
    const sharesTags = (e.tags || []).some((t) => eventTags.has(t));
    return inWindow && (sharesEntity || sharesTags);
  });
}

export function clampTime(time: number, start: number, end: number): number {
  return Math.max(start, Math.min(end, time));
}

export function eventAtTime(events: TraceEvent[], t: number): TraceEvent | null {
  let best: TraceEvent | null = null;
  for (const e of events) {
    if (e.t_rel <= t && (!best || e.t_rel > best.t_rel)) {
      best = e;
    }
  }
  return best;
}

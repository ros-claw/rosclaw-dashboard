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
      color: laneColors[type] || '#64748b',
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

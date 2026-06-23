import { describe, expect, it } from 'vitest';
import {
  clampTime,
  eventAtTime,
  findFailures,
  findRelated,
  groupByTrack,
  type TraceEvent,
  type TraceTrack,
} from '@rosclaw/timeline-core';

const runId = 'golden_pick_cube_failure';

const makeEvent = (
  id: string,
  t_rel: number,
  track: TraceTrack,
  overrides: Partial<TraceEvent> = {},
): TraceEvent => ({
  id,
  run_id: runId,
  ts: 1_700_000_000 + t_rel,
  t_rel,
  source: track,
  type: 'event',
  track,
  severity: 'info',
  title: id,
  ...overrides,
});

const events: TraceEvent[] = [
  makeEvent('evt_task_001', 0.0, 'task', { title: 'Pick cube task started' }),
  makeEvent('evt_agent_001', 1.2, 'agent', { title: 'Plan grasp' }),
  makeEvent('evt_provider_001', 2.5, 'provider', { title: 'Move to pre-grasp' }),
  makeEvent('evt_tool_001', 4.0, 'tool', { title: 'Open gripper', entity: 'gripper' }),
  makeEvent('evt_tool_002', 6.0, 'tool', {
    title: 'Close gripper',
    entity: 'gripper',
    links: ['evt_failure_001'],
  }),
  makeEvent('evt_critic_001', 8.0, 'critic', {
    title: 'Slip detected',
    tags: ['failure', 'slip'],
    entity: 'cube',
  }),
  makeEvent('evt_failure_001', 8.1, 'failure', {
    title: 'Cube dropped',
    severity: 'failure',
    entity: 'cube',
    links: ['evt_tool_002', 'evt_critic_001'],
    tags: ['failure'],
  }),
  makeEvent('evt_sandbox_001', 10.0, 'sandbox', { title: 'Cube left on table' }),
];

describe('timeline-core helpers', () => {
  it('groupByTrack returns every track with correct events', () => {
    const grouped = groupByTrack(events);
    expect(grouped.task).toHaveLength(1);
    expect(grouped.tool).toHaveLength(2);
    expect(grouped.failure).toHaveLength(1);
    expect(grouped.auto).toHaveLength(0);
    expect(grouped.tool.map((e) => e.id)).toEqual(['evt_tool_001', 'evt_tool_002']);
  });

  it('findFailures returns failure-track and failure-severity events', () => {
    const failures = findFailures(events);
    expect(failures).toHaveLength(1);
    expect(failures[0].id).toBe('evt_failure_001');
    expect(failures[0].severity).toBe('failure');
  });

  it('findRelated returns explicitly linked events regardless of window', () => {
    const failure = events.find((e) => e.id === 'evt_failure_001')!;
    const related = findRelated(events, failure, 0.5);
    const ids = related.map((e) => e.id);
    expect(ids).toContain('evt_tool_002');
    expect(ids).toContain('evt_critic_001');
    expect(ids).not.toContain('evt_failure_001');
    expect(ids).not.toContain('evt_task_001');
  });

  it('findRelated returns nearby events with shared entity or tags', () => {
    const tool2 = events.find((e) => e.id === 'evt_tool_002')!;
    const related = findRelated(events, tool2, 2.0);
    const ids = related.map((e) => e.id);
    // evt_tool_001 shares entity within window
    expect(ids).toContain('evt_tool_001');
    // evt_failure_001 is linked
    expect(ids).toContain('evt_failure_001');
    // evt_critic_001 shares failure tag with evt_failure_001 but not tool2 tags
    expect(ids).not.toContain('evt_critic_001');
  });

  it('clampTime keeps time within bounds', () => {
    expect(clampTime(-1, 0, 10)).toBe(0);
    expect(clampTime(5, 0, 10)).toBe(5);
    expect(clampTime(15, 0, 10)).toBe(10);
  });

  it('eventAtTime finds the latest event at or before the given time', () => {
    expect(eventAtTime(events, -1)?.id).toBeUndefined();
    expect(eventAtTime(events, 0)?.id).toBe('evt_task_001');
    expect(eventAtTime(events, 7.9)?.id).toBe('evt_tool_002');
    expect(eventAtTime(events, 42)?.id).toBe('evt_sandbox_001');
  });
});

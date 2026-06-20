import { create } from 'zustand';
import type { TraceEvent } from '@rosclaw/timeline-core';

interface ReplayState {
  runId: string | null;
  duration: number;
  currentTime: number;
  playing: boolean;
  speed: number;
  selectedEventId: string | null;
  lastTick: number;

  setRun: (runId: string, duration: number) => void;
  play: () => void;
  pause: () => void;
  toggle: () => void;
  seek: (t: number) => void;
  step: (delta: number) => void;
  setSpeed: (speed: number) => void;
  jumpToEvent: (event: TraceEvent) => void;
  selectEvent: (id: string | null) => void;
  tick: (now: number) => void;
}

export const useReplayStore = create<ReplayState>((set, get) => ({
  runId: null,
  duration: 0,
  currentTime: 0,
  playing: false,
  speed: 1,
  selectedEventId: null,
  lastTick: 0,

  setRun: (runId, duration) =>
    set({ runId, duration, currentTime: 0, playing: false, selectedEventId: null }),

  play: () => set({ playing: true, lastTick: performance.now() }),

  pause: () => set({ playing: false }),

  toggle: () => {
    const { playing } = get();
    if (playing) {
      set({ playing: false });
    } else {
      set({ playing: true, lastTick: performance.now() });
    }
  },

  seek: (t) => {
    const { duration } = get();
    set({ currentTime: Math.max(0, Math.min(duration, t)) });
  },

  step: (delta) => {
    const { duration, currentTime } = get();
    set({ currentTime: Math.max(0, Math.min(duration, currentTime + delta)) });
  },

  setSpeed: (speed) => set({ speed: Math.max(0.25, Math.min(4, speed)) }),

  jumpToEvent: (event) =>
    set({
      currentTime: Math.max(0, event.t_rel),
      selectedEventId: event.id,
    }),

  selectEvent: (id) => set({ selectedEventId: id }),

  tick: (now) => {
    const { playing, lastTick, speed, duration, currentTime } = get();
    if (!playing) return;
    const elapsed = ((now - lastTick) / 1000) * speed;
    const next = currentTime + elapsed;
    if (next >= duration) {
      set({ currentTime: duration, playing: false });
    } else {
      set({ currentTime: next, lastTick: now });
    }
  },
}));

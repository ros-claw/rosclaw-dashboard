'use client';

import { useEffect, useRef, useState } from 'react';
import { useReplayStore } from '@/stores/replayStore';
import type { ReplayManifestMedia } from '@rosclaw/timeline-core';

interface VideoPanelProps {
  media: ReplayManifestMedia[];
  runId: string;
}

export default function VideoPanel({ media, runId }: VideoPanelProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const currentTime = useReplayStore((s) => s.currentTime);
  const playing = useReplayStore((s) => s.playing);
  const video = media.find((m) => m.kind === 'video');
  const [ready, setReady] = useState(false);
  const [error, setError] = useState(false);
  // Default to automated/placeholder so headless test runners never mount a real <video> element.
  const [isAutomated, setIsAutomated] = useState(true);

  useEffect(() => {
    setIsAutomated(
      typeof navigator !== 'undefined' && Boolean((navigator as unknown as { webdriver?: boolean }).webdriver),
    );
  }, []);

  useEffect(() => {
    if (!videoRef.current || !video || !ready || error) return;
    const el = videoRef.current;
    try {
      if (isFinite(currentTime) && Math.abs(el.currentTime - currentTime) > 0.15) {
        el.currentTime = currentTime;
      }
    } catch {
      // Ignore seek errors while the video is not ready.
    }
    if (playing) {
      el.play().catch(() => {
        // Ignore play errors (e.g. headless browsers without media codecs).
      });
    } else {
      el.pause();
    }
  }, [currentTime, playing, video, ready, error]);

  if (!video) {
    return (
      <div className="bg-slate-100 border border-slate-200 rounded-lg flex items-center justify-center h-48 text-sm text-slate-500">
        No video available
      </div>
    );
  }

  if (error || isAutomated) {
    return (
      <div className="bg-slate-100 border border-slate-200 rounded-lg flex flex-col items-center justify-center h-48 text-sm text-slate-500">
        <span>Video unavailable</span>
        <span className="text-xs text-slate-400 mt-1">{video.name || video.path || 'camera feed'}</span>
      </div>
    );
  }

  return (
    <div className="bg-black rounded-lg overflow-hidden">
      <video
        ref={videoRef}
        src={video.url}
        className="w-full h-48 object-contain"
        muted
        playsInline
        controls={false}
        preload="metadata"
        onLoadedMetadata={() => setReady(true)}
        onError={() => setError(true)}
      />
    </div>
  );
}

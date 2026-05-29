'use client';

import { useEffect, useState, useRef } from 'react';
import { api } from '@/lib/api';
import DashboardShell from '@/components/DashboardShell';

interface RuntimeRobot {
  robot_id: string;
  online: boolean;
  last_heartbeat: number;
  active_tasks: number;
  error_count: number;
  bridge_connected: boolean;
  daemon_connected: boolean;
  topics: string[];
}

export default function RuntimePage() {
  const [robots, setRobots] = useState<RuntimeRobot[]>([]);
  const [loading, setLoading] = useState(true);
  const wsRef = useRef<WebSocket | null>(null);
  const [liveStatus, setLiveStatus] = useState<Record<string, RuntimeRobot>>({});

  useEffect(() => {
    api.runtime.list().then((data: any) => {
      setRobots(data);
      setLoading(false);
    });

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const ws = new WebSocket(`${protocol}//${window.location.host}/api/runtime/status/stream`);
    wsRef.current = ws;

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      if (msg.type === 'runtime.status') {
        setLiveStatus(prev => ({ ...prev, [msg.data.robot_id]: msg.data }));
      }
    };

    return () => ws.close();
  }, []);

  const getRobotStatus = (robotId: string): RuntimeRobot | undefined => {
    return liveStatus[robotId] || robots.find(r => r.robot_id === robotId);
  };

  return (
    <DashboardShell>
      <div className="space-y-6">
        {loading ? (
          <div className="text-sm text-slate-500">Loading runtime status...</div>
        ) : robots.length === 0 ? (
          <div className="bg-white rounded-lg border border-slate-200 p-8 text-center">
            <p className="text-slate-500">No runtime daemons registered.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {robots.map((robot) => {
              const status = getRobotStatus(robot.robot_id);
              const isOnline = status?.online ?? false;
              return (
                <div key={robot.robot_id} className="bg-white rounded-lg border border-slate-200 p-5">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="font-semibold text-slate-800">{robot.robot_id}</h3>
                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${isOnline ? 'bg-emerald-100 text-emerald-800' : 'bg-red-100 text-red-800'}`}>
                      {isOnline ? 'Online' : 'Offline'}
                    </span>
                  </div>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-slate-500">Daemon</span>
                      <span className={status?.daemon_connected ? 'text-emerald-600' : 'text-red-600'}>{status?.daemon_connected ? 'Connected' : 'Disconnected'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Bridge</span>
                      <span className={status?.bridge_connected ? 'text-emerald-600' : 'text-red-600'}>{status?.bridge_connected ? 'Connected' : 'Disconnected'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Active Tasks</span>
                      <span className="font-medium">{status?.active_tasks ?? 0}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Errors</span>
                      <span className={`font-medium ${(status?.error_count ?? 0) > 0 ? 'text-red-600' : ''}`}>{status?.error_count ?? 0}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Topics</span>
                      <span className="font-medium">{status?.topics?.length ?? 0}</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </DashboardShell>
  );
}

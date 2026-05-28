/**
 * ROSClaw Robot Daemon
 *
 * Bridges robot telemetry (ROS 2 topics, diagnostics, system metrics)
 * to the ROSClaw Dashboard via WebSocket.
 *
 * MVP: placeholder scaffold. Full implementation requires ROS 2 client
 * libraries (rclpy or rclnodejs) and foxglove_bridge integration.
 */

import { WebSocketServer } from 'ws';

const PORT = process.env.ROBOT_DAEMON_PORT ? parseInt(process.env.ROBOT_DAEMON_PORT) : 8765;
const ROBOT_ID = process.env.ROBOT_ID || 'unknown';

const wss = new WebSocketServer({ port: PORT });

wss.on('connection', (ws) => {
  console.log(`[${ROBOT_ID}] Client connected`);

  ws.send(JSON.stringify({
    type: 'hello',
    robot_id: ROBOT_ID,
    timestamp: Date.now(),
  }));

  ws.on('message', (data) => {
    try {
      const msg = JSON.parse(data.toString());
      console.log(`[${ROBOT_ID}] Received:`, msg.type);
    } catch {
      // ignore
    }
  });

  ws.on('close', () => {
    console.log(`[${ROBOT_ID}] Client disconnected`);
  });
});

console.log(`ROSClaw Robot Daemon running for ${ROBOT_ID} on ws://localhost:${PORT}`);

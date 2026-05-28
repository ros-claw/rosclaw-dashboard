import type { FoxgloveLayout, FoxgloveLayoutConfig, PanelConfig } from './types.js';

/**
 * Generate a Foxglove layout JSON from e-URDF sensor and actuator configuration.
 *
 * Maps e-URDF sensors to appropriate Foxglove panels:
 * - rgbd_camera / rgb_camera → Image panel
 * - lidar_2d / lidar_3d → 3D panel (LaserScan)
 * - imu → Plot panel
 * - force_torque → Plot panel
 * - joint states → Plot panel
 * - TF → 3D panel
 * - diagnostics → DiagnosticSummary panel
 * - Agent/skill events → RawMessages / StateTransitions panel
 */
export function generateLayout(config: FoxgloveLayoutConfig): FoxgloveLayout {
  const imagePanels: PanelConfig[] = [];
  const plotPanels: PanelConfig[] = [];
  const threeDPanels: PanelConfig[] = [];
  const rawPanels: PanelConfig[] = [];

  for (const panel of config.panels) {
    switch (panel.type) {
      case 'Image':
        imagePanels.push(panel);
        break;
      case '3D':
        threeDPanels.push(panel);
        break;
      case 'Plot':
        plotPanels.push(panel);
        break;
      case 'RawMessages':
      case 'StateTransitions':
      case 'DiagnosticSummary':
        rawPanels.push(panel);
        break;
    }
  }

  // Build a 2x2 grid layout
  const topLeft = imagePanels[0]
    ? { url: `./Image`, topic: imagePanels[0].topic }
    : threeDPanels[0]
      ? { url: `./3D`, topic: threeDPanels[0].topic }
      : { url: `./3D`, topic: '/tf' };

  const topRight = threeDPanels[0] && imagePanels[0]
    ? { url: `./3D`, topic: threeDPanels[0].topic }
    : plotPanels[0]
      ? { url: `./Plot`, topic: plotPanels[0].topic }
      : { url: `./Plot`, topic: '/joint_states' };

  const bottomLeft = plotPanels[0] && (imagePanels[0] || threeDPanels[0])
    ? { url: `./Plot`, topic: plotPanels[0].topic }
    : rawPanels[0]
      ? { url: `./RawMessages`, topic: rawPanels[0].topic }
      : { url: `./DiagnosticSummary`, topic: '/diagnostics' };

  const bottomRight = rawPanels[0] && plotPanels.length > 0
    ? { url: `./RawMessages`, topic: rawPanels[0].topic }
    : { url: `./StateTransitions`, topic: '/rosclaw/agent_events' };

  return {
    layout: {
      direction: 'row',
      first: {
        direction: 'column',
        first: topLeft,
        second: bottomLeft,
        splitPercentage: 50,
      },
      second: {
        direction: 'column',
        first: topRight,
        second: bottomRight,
        splitPercentage: 50,
      },
      splitPercentage: 50,
    },
  };
}

/**
 * Generate a default layout for a robot based on its e-URDF topics.
 */
export function generateDefaultLayout(
  robot_id: string,
  topics: Array<{ topic: string; type: string }>
): FoxgloveLayout {
  const panels: PanelConfig[] = topics.map((t) => {
    const panelType = mapTopicToPanelType(t.topic, t.type);
    return { type: panelType, topic: t.topic };
  });

  return generateLayout({
    robot_id,
    display_name: `${robot_id} Layout`,
    panels,
  });
}

function mapTopicToPanelType(topic: string, _messageType: string): PanelConfig['type'] {
  if (topic.includes('camera') || topic.includes('image')) return 'Image';
  if (topic.includes('scan') || topic.includes('pointcloud')) return '3D';
  if (topic.includes('joint_states') || topic.includes('wrench')) return 'Plot';
  if (topic.includes('diagnostic')) return 'DiagnosticSummary';
  if (topic.includes('rosclaw')) return 'StateTransitions';
  if (topic === '/tf' || topic === '/tf_static') return '3D';
  return 'RawMessages';
}

export * from './types.js';

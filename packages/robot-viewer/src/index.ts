/**
 * Robot Viewer
 *
 * 3D visualization components for e-URDF robot models.
 * MVP: placeholder. Full implementation uses Three.js / React Three Fiber
 * to render URDF links, joints, sensors, and actuators.
 */

export interface ViewerConfig {
  robot_id: string;
  urdf_url: string;
  width: number;
  height: number;
}

export function createViewer(_config: ViewerConfig): { destroy: () => void } {
  // Placeholder: full implementation loads URDF via THREE.js
  return { destroy: () => {} };
}

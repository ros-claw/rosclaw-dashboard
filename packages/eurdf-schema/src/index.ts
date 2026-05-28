/**
 * e-URDF Schema v0.1
 * Embodied Universal Robot Description Format
 */

export interface EURDFRobot {
  version: string;
  robot_id: string;
  display_name: string;
  base_model: string;
  sources: {
    urdf: string;
    meshes?: string;
    calibration?: string;
  };
  frames: Record<string, string>;
  body_parts: Record<string, BodyPart>;
  sensors: Record<string, Sensor>;
  actuators: Record<string, Actuator>;
  runtime: RuntimeConfig;
}

export interface BodyPart {
  type: string;
  links?: string[];
  joints?: string[];
  actuators?: string[];
  sensors?: string[];
}

export interface Sensor {
  type: string;
  frame_id: string;
  topics: Record<string, string>;
  health?: SensorHealth;
  calibration?: Calibration;
}

export interface SensorHealth {
  min_fps?: number;
  min_hz?: number;
  max_latency_ms?: number;
}

export interface Calibration {
  camera_matrix?: number[][];
  distortion_coeffs?: number[];
  extrinsics?: Transform;
}

export interface Transform {
  translation: [number, number, number];
  rotation: [number, number, number, number];
}

export interface Actuator {
  type: string;
  command_topic?: string;
  feedback_topics?: Record<string, string>;
  limits?: ActuatorLimits;
}

export interface ActuatorLimits {
  max_linear_x?: number;
  max_linear_y?: number;
  max_linear_z?: number;
  max_angular_x?: number;
  max_angular_y?: number;
  max_angular_z?: number;
  max_position?: number;
  min_position?: number;
  max_velocity?: number;
  max_effort?: number;
}

export interface RuntimeConfig {
  ros?: {
    distro: string;
    required_topics?: string[];
  };
  foxglove_bridge?: {
    host: string;
    port: number;
  };
}

export interface RobotSkills {
  version: string;
  robot_id: string;
  skills: Record<string, Skill>;
}

export interface Skill {
  type: string;
  description: string;
  requires: SkillRequirements;
  ros?: {
    action?: string;
    service?: string;
    topic?: string;
  };
  safety: SkillSafety;
}

export interface SkillRequirements {
  sensors?: string[];
  actuators?: string[];
  frames?: string[];
  memory?: string[];
}

export interface SkillSafety {
  approval_required: boolean;
  max_speed?: number;
  max_force?: number;
  human_proximity_required?: boolean;
}

export interface RobotSafety {
  version: string;
  robot_id: string;
  emergency_stop: EmergencyStop;
  speed_limits: SpeedLimits;
  forbidden_zones?: ForbiddenZones;
  approval_required: ApprovalRule[];
  policy_events: PolicyEvents;
}

export interface EmergencyStop {
  topic: string;
  mode: 'latched' | 'momentary';
}

export interface SpeedLimits {
  default: VelocityLimit;
  near_human?: VelocityLimit;
  indoor?: VelocityLimit;
  outdoor?: VelocityLimit;
}

export interface VelocityLimit {
  linear_x: number;
  linear_y?: number;
  angular_z: number;
}

export interface ForbiddenZones {
  source: string;
}

export interface ApprovalRule {
  skill: string;
  reason?: string;
}

export interface PolicyEvents {
  publish_topic: string;
}

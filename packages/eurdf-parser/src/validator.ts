import { z } from 'zod';
import type { EURDFRobot, RobotSkills, RobotSafety } from '@rosclaw/eurdf-schema';

const SensorHealthSchema = z.object({
  min_fps: z.number().optional(),
  min_hz: z.number().optional(),
  max_latency_ms: z.number().optional(),
});

const SensorSchema = z.object({
  type: z.string(),
  frame_id: z.string(),
  topics: z.record(z.string()),
  health: SensorHealthSchema.optional(),
});

const ActuatorSchema = z.object({
  type: z.string(),
  command_topic: z.string().optional(),
  feedback_topics: z.record(z.string()).optional(),
  limits: z.record(z.number()).optional(),
});

const BodyPartSchema = z.object({
  type: z.string(),
  links: z.array(z.string()).optional(),
  joints: z.array(z.string()).optional(),
  actuators: z.array(z.string()).optional(),
  sensors: z.array(z.string()).optional(),
});

const EURDFSchema = z.object({
  version: z.string(),
  robot_id: z.string(),
  display_name: z.string(),
  base_model: z.string(),
  sources: z.object({
    urdf: z.string(),
    meshes: z.string().optional(),
    calibration: z.string().optional(),
  }),
  frames: z.record(z.string()),
  body_parts: z.record(BodyPartSchema),
  sensors: z.record(SensorSchema),
  actuators: z.record(ActuatorSchema),
  runtime: z.object({
    ros: z.object({
      distro: z.string(),
      required_topics: z.array(z.string()).optional(),
    }).optional(),
    foxglove_bridge: z.object({
      host: z.string(),
      port: z.number(),
    }).optional(),
  }),
});

const SkillSchema = z.object({
  type: z.string(),
  description: z.string(),
  requires: z.object({
    sensors: z.array(z.string()).optional(),
    actuators: z.array(z.string()).optional(),
    frames: z.array(z.string()).optional(),
    memory: z.array(z.string()).optional(),
  }),
  ros: z.object({
    action: z.string().optional(),
    service: z.string().optional(),
    topic: z.string().optional(),
  }).optional(),
  safety: z.object({
    approval_required: z.boolean(),
    max_speed: z.number().optional(),
    max_force: z.number().optional(),
  }),
});

const SkillsSchema = z.object({
  version: z.string(),
  robot_id: z.string(),
  skills: z.record(SkillSchema),
});

const SafetySchema = z.object({
  version: z.string(),
  robot_id: z.string(),
  emergency_stop: z.object({
    topic: z.string(),
    mode: z.enum(['latched', 'momentary']),
  }),
  speed_limits: z.object({
    default: z.object({
      linear_x: z.number(),
      linear_y: z.number().optional(),
      angular_z: z.number(),
    }),
    near_human: z.object({
      linear_x: z.number(),
      angular_z: z.number(),
    }).optional(),
  }),
  forbidden_zones: z.object({
    source: z.string(),
  }).optional(),
  approval_required: z.array(z.object({
    skill: z.string(),
    reason: z.string().optional(),
  })),
  policy_events: z.object({
    publish_topic: z.string(),
  }),
});

export class EURDFValidationError extends Error {
  constructor(public issues: z.ZodIssue[]) {
    super(`e-URDF validation failed: ${issues.length} issues`);
  }
}

export function validateEURDF(data: unknown): EURDFRobot {
  const result = EURDFSchema.safeParse(data);
  if (!result.success) {
    throw new EURDFValidationError(result.error.issues);
  }
  return result.data as EURDFRobot;
}

export function validateSkills(data: unknown): RobotSkills {
  const result = SkillsSchema.safeParse(data);
  if (!result.success) {
    throw new EURDFValidationError(result.error.issues);
  }
  return result.data as RobotSkills;
}

export function validateSafety(data: unknown): RobotSafety {
  const result = SafetySchema.safeParse(data);
  if (!result.success) {
    throw new EURDFValidationError(result.error.issues);
  }
  return result.data as RobotSafety;
}

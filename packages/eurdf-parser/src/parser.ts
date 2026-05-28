import yaml from 'js-yaml';
import fs from 'fs/promises';
import path from 'path';
import { validateEURDF, validateSkills, validateSafety, EURDFValidationError } from './validator.js';
import type { EURDFRobot, RobotSkills, RobotSafety } from '@rosclaw/eurdf-schema';

export interface ParsedRobot {
  eurdf: EURDFRobot;
  skills: RobotSkills | null;
  safety: RobotSafety | null;
  directory: string;
}

export async function parseRobotDirectory(dir: string): Promise<ParsedRobot> {
  const eurdfPath = path.join(dir, 'robot.eurdf.yaml');
  const skillsPath = path.join(dir, 'robot.skills.yaml');
  const safetyPath = path.join(dir, 'robot.safety.yaml');

  const eurdfContent = await fs.readFile(eurdfPath, 'utf-8');
  const eurdf = validateEURDF(yaml.load(eurdfContent));

  let skills: RobotSkills | null = null;
  try {
    const skillsContent = await fs.readFile(skillsPath, 'utf-8');
    skills = validateSkills(yaml.load(skillsContent));
  } catch {
    // skills optional
  }

  let safety: RobotSafety | null = null;
  try {
    const safetyContent = await fs.readFile(safetyPath, 'utf-8');
    safety = validateSafety(yaml.load(safetyContent));
  } catch {
    // safety optional
  }

  return { eurdf, skills, safety, directory: dir };
}

export function generateTopicBindingTable(robot: ParsedRobot): Array<{
  sensor: string;
  topic: string;
  type: string;
  frame_id: string;
  body_part?: string;
}> {
  const results = [];
  for (const [sensorName, sensor] of Object.entries(robot.eurdf.sensors)) {
    for (const [topicName, topicPath] of Object.entries(sensor.topics)) {
      const bodyPart = Object.entries(robot.eurdf.body_parts).find(
        ([, bp]) => bp.sensors?.includes(sensorName)
      )?.[0];

      results.push({
        sensor: sensorName,
        topic: topicPath,
        type: topicName,
        frame_id: sensor.frame_id,
        body_part: bodyPart,
      });
    }
  }
  return results;
}

export function generateSkillDependencyGraph(robot: ParsedRobot): Array<{
  skill: string;
  sensors: string[];
  actuators: string[];
  frames: string[];
  approval_required: boolean;
}> {
  if (!robot.skills) return [];
  return Object.entries(robot.skills.skills).map(([name, skill]) => ({
    skill: name,
    sensors: skill.requires.sensors || [],
    actuators: skill.requires.actuators || [],
    frames: skill.requires.frames || [],
    approval_required: skill.safety.approval_required,
  }));
}

export { validateEURDF, validateSkills, validateSafety, EURDFValidationError };

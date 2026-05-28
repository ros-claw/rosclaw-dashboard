#!/usr/bin/env node
import { parseRobotDirectory, generateTopicBindingTable, generateSkillDependencyGraph } from './parser.js';

const command = process.argv[2];
const target = process.argv[3];

async function main() {
  if (!command || !target) {
    console.log('Usage: eurdf-validate <command> <path>');
    console.log('Commands:');
    console.log('  validate <robot-dir>    Validate e-URDF, skills, and safety YAML');
    console.log('  inspect <robot-dir>     Show topic bindings and skill dependencies');
    console.log('  generate-layout <robot-dir>  Generate Foxglove layout JSON');
    process.exit(1);
  }

  try {
    const robot = await parseRobotDirectory(target);

    switch (command) {
      case 'validate':
        console.log('✓ e-URDF valid:', robot.eurdf.robot_id);
        console.log('  Display name:', robot.eurdf.display_name);
        console.log('  Base model:', robot.eurdf.base_model);
        console.log('  Body parts:', Object.keys(robot.eurdf.body_parts).join(', '));
        console.log('  Sensors:', Object.keys(robot.eurdf.sensors).join(', '));
        console.log('  Actuators:', Object.keys(robot.eurdf.actuators).join(', '));
        if (robot.skills) {
          console.log('✓ Skills valid:', Object.keys(robot.skills.skills).length, 'skills');
        }
        if (robot.safety) {
          console.log('✓ Safety valid:', robot.safety.approval_required.length, 'approval rules');
        }
        break;

      case 'inspect':
        console.log('\n=== Topic Bindings ===');
        const bindings = generateTopicBindingTable(robot);
        for (const b of bindings) {
          console.log(`  ${b.sensor} (${b.type}): ${b.topic} [frame: ${b.frame_id}]${b.body_part ? ` [body: ${b.body_part}]` : ''}`);
        }
        console.log('\n=== Skill Dependencies ===');
        const deps = generateSkillDependencyGraph(robot);
        for (const d of deps) {
          console.log(`  ${d.skill}: sensors=[${d.sensors.join(', ')}] actuators=[${d.actuators.join(', ')}] approval=${d.approval_required}`);
        }
        break;

      case 'generate-layout':
        // Will be implemented by foxglove-layout-generator package
        console.log('Use: rosclaw-dashboard generate-layout', target);
        break;

      default:
        console.error('Unknown command:', command);
        process.exit(1);
    }
  } catch (err) {
    console.error('Error:', err instanceof Error ? err.message : err);
    process.exit(1);
  }
}

main();

#!/usr/bin/env python3
"""Seed script to import sample robots into the ROSClaw API database."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from src.models.database import Base, Mission, AgentEvent, SkillRun, Skill, MemoryEntry, SafetyAudit, SafetyRule
from src.services.robot_service import import_robot_from_directory

DB_URL = "sqlite:///./rosclaw.db"
ROBOTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'robots'))

ROBOTS = [
    ("go2_lab_001", os.path.join(ROBOTS_DIR, "unitree_go2")),
    ("ur5e_lab_002", os.path.join(ROBOTS_DIR, "ur5e")),
    ("tb4_lab_003", os.path.join(ROBOTS_DIR, "turtlebot4")),
]


def main():
    engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = Session()

    for robot_id, directory in ROBOTS:
        if not os.path.exists(directory):
            print(f"Warning: directory not found: {directory}")
            continue
        try:
            robot = import_robot_from_directory(db, robot_id, directory)
            print(f"Imported: {robot.id} — {robot.name}")
        except Exception as e:
            print(f"Error importing {robot_id}: {e}")

    # Seed sample missions
    if db.query(Mission).count() == 0:
        missions = [
            Mission(id="mission_001", robot_id="go2_lab_001", agent_id="agent_alpha", title="Lab Patrol Round 1", status="completed", started_at=datetime.utcnow(), ended_at=datetime.utcnow()),
            Mission(id="mission_002", robot_id="ur5e_lab_002", agent_id="agent_beta", title="Pick-and-Place Demo", status="running", started_at=datetime.utcnow()),
            Mission(id="mission_003", robot_id="tb4_lab_003", agent_id="agent_gamma", title="Map Exploration", status="pending"),
        ]
        for m in missions:
            db.merge(m)
        db.commit()
        print(f"Seeded {len(missions)} missions")

    # Seed sample skill runs
    if db.query(SkillRun).count() == 0:
        runs = [
            SkillRun(id="run_001", mission_id="mission_001", skill_name="walk_forward", status="completed", started_at=datetime.utcnow(), ended_at=datetime.utcnow()),
            SkillRun(id="run_002", mission_id="mission_002", skill_name="grasp_object", status="running", started_at=datetime.utcnow()),
            SkillRun(id="run_003", mission_id="mission_003", skill_name="navigate_to_goal", status="pending"),
        ]
        for r in runs:
            db.merge(r)
        db.commit()
        print(f"Seeded {len(runs)} skill runs")

    # Seed sample agent events
    if db.query(AgentEvent).count() == 0:
        events = [
            AgentEvent(id="evt_001", mission_id="mission_001", event_type="mission_start", payload_json='{"reason": "scheduled"}'),
            AgentEvent(id="evt_002", mission_id="mission_001", event_type="skill_complete", payload_json='{"skill": "walk_forward"}'),
            AgentEvent(id="evt_003", mission_id="mission_002", event_type="mission_start", payload_json='{"reason": "user_request"}'),
            AgentEvent(id="evt_004", mission_id="mission_003", event_type="mission_queued", payload_json='{"reason": "scheduled"}'),
        ]
        for e in events:
            db.merge(e)
        db.commit()
        print(f"Seeded {len(events)} agent events")

    # Seed global skills
    if db.query(Skill).count() == 0:
        skills = [
            Skill(id="sk_walk", robot_id="go2_lab_001", name="walk_forward", skill_type="locomotion", status="ready", approval_required=False, description="Basic forward walking gait"),
            Skill(id="sk_grasp", robot_id="ur5e_lab_002", name="grasp_object", skill_type="manipulation", status="ready", approval_required=True, description="6-DOF grasp with force feedback"),
            Skill(id="sk_nav", robot_id="tb4_lab_003", name="navigate_to_goal", skill_type="navigation", status="ready", approval_required=False, description="SLAM-based autonomous navigation"),
            Skill(id="sk_patrol", robot_id="go2_lab_001", name="patrol_perimeter", skill_type="surveillance", status="beta", approval_required=True, description="Autonomous perimeter patrol with anomaly detection"),
        ]
        for s in skills:
            db.merge(s)
        db.commit()
        print(f"Seeded {len(skills)} skills")

    # Seed sample memory entries
    if db.query(MemoryEntry).count() == 0:
        entries = [
            MemoryEntry(id="mem_001", robot_id="go2_lab_001", memory_type="episodic", content_json='{"event": "encountered_obstacle", "location": "lab_corridor_a", "outcome": "rerouted"}', source_skill="navigate_to", source_mission="mission_001", confidence=0.95),
            MemoryEntry(id="mem_002", robot_id="go2_lab_001", memory_type="semantic", content_json='{"fact": "doorway_width", "value": "0.9m", "location": "lab_entrance"}', source_skill="inspect_object", confidence=0.88),
            MemoryEntry(id="mem_003", robot_id="ur5e_lab_002", memory_type="procedural", content_json='{"steps": ["approach", "align", "grasp", "lift", "place"], "object_type": "box_10kg"}', source_skill="grasp_object", source_mission="mission_002", confidence=0.92),
            MemoryEntry(id="mem_004", robot_id="tb4_lab_003", memory_type="episodic", content_json='{"event": "new_room_discovered", "area": "3.2m_x_4.1m", "features": ["table", "chairs"]}', source_skill="navigate_to_goal", source_mission="mission_003", confidence=0.78),
        ]
        for e in entries:
            db.merge(e)
        db.commit()
        print(f"Seeded {len(entries)} memory entries")

    # Seed sample safety audits
    if db.query(SafetyAudit).count() == 0:
        audits = [
            SafetyAudit(id="audit_001", robot_id="go2_lab_001", audit_type="pre_mission", status="passed", findings_json='{"checks": ["joint_limits", "battery", "lidar_clean"], "result": "all_ok"}'),
            SafetyAudit(id="audit_002", robot_id="ur5e_lab_002", audit_type="periodic", status="passed", findings_json='{"checks": ["force_limits", "workspace_clear", "e_stop"], "result": "all_ok"}'),
            SafetyAudit(id="audit_003", robot_id="tb4_lab_003", audit_type="pre_mission", status="failed", findings_json='{"checks": ["joint_limits", "battery", "lidar_clean"], "result": "battery_low"}'),
        ]
        for a in audits:
            db.merge(a)
        db.commit()
        print(f"Seeded {len(audits)} safety audits")

    # Seed sample safety rules
    if db.query(SafetyRule).count() == 0:
        rules = [
            SafetyRule(id="rule_001", robot_id="go2_lab_001", rule_name="Max Speed Indoor", rule_type="speed_limit", parameters_json='{"max_linear": 1.0, "max_angular": 0.5, "unit": "m/s"}', active=True),
            SafetyRule(id="rule_002", robot_id="ur5e_lab_002", rule_name="Force Limit Grasp", rule_type="force_limit", parameters_json='{"max_force": 50.0, "unit": "N"}', active=True),
            SafetyRule(id="rule_003", robot_id="tb4_lab_003", rule_name="Collision Buffer", rule_type="collision_zone", parameters_json='{"buffer_m": 0.3, "slowdown_buffer_m": 0.6}', active=True),
            SafetyRule(id="rule_004", robot_id="go2_lab_001", rule_name="Emergency Stop Zone", rule_type="emergency_stop", parameters_json='{"zone_radius_m": 0.5, "trigger": "human_proximity"}', active=False),
        ]
        for r in rules:
            db.merge(r)
        db.commit()
        print(f"Seeded {len(rules)} safety rules")

    db.close()
    print("Done.")


if __name__ == "__main__":
    main()

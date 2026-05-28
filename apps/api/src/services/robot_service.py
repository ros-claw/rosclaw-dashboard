import os
import yaml
from sqlalchemy.orm import Session

from models.database import Robot, Sensor, Actuator, Skill
from models.schemas import RobotCreate, RobotResponse


def get_robots(db: Session, skip: int = 0, limit: int = 100):
    robots = db.query(Robot).offset(skip).limit(limit).all()
    return [RobotResponse.model_validate(r) for r in robots]


def get_robot(db: Session, robot_id: str):
    robot = db.query(Robot).filter(Robot.id == robot_id).first()
    if robot:
        return RobotResponse.model_validate(robot)
    return None


def create_robot(db: Session, robot: RobotCreate):
    db_robot = Robot(**robot.model_dump())
    db.add(db_robot)
    db.commit()
    db.refresh(db_robot)
    return RobotResponse.model_validate(db_robot)


def import_robot_from_directory(db: Session, robot_id: str, directory: str):
    eurdf_path = os.path.join(directory, "robot.eurdf.yaml")
    skills_path = os.path.join(directory, "robot.skills.yaml")

    if not os.path.exists(eurdf_path):
        raise FileNotFoundError(f"e-URDF file not found: {eurdf_path}")

    with open(eurdf_path) as f:
        eurdf = yaml.safe_load(f)

    robot = Robot(
        id=robot_id,
        name=eurdf.get("display_name", robot_id),
        model=eurdf.get("base_model", "unknown"),
        eurdf_version=eurdf.get("version", "v0.1.0"),
        status="offline",
    )
    db.merge(robot)

    # Import sensors
    for sid, sdata in eurdf.get("sensors", {}).items():
        sensor = Sensor(
            id=f"{robot_id}_{sid}",
            robot_id=robot_id,
            name=sid,
            type=sdata.get("type", "unknown"),
            frame_id=sdata.get("frame_id"),
            health_status="unknown",
        )
        db.merge(sensor)

    # Import actuators
    for aid, adata in eurdf.get("actuators", {}).items():
        actuator = Actuator(
            id=f"{robot_id}_{aid}",
            robot_id=robot_id,
            name=aid,
            type=adata.get("type", "unknown"),
            command_topic=adata.get("command_topic"),
            health_status="unknown",
        )
        db.merge(actuator)

    # Import skills
    if os.path.exists(skills_path):
        with open(skills_path) as f:
            skills_data = yaml.safe_load(f)
        for skid, skdata in skills_data.get("skills", {}).items():
            skill = Skill(
                id=f"{robot_id}_{skid}",
                robot_id=robot_id,
                name=skid,
                skill_type=skdata.get("type", "unknown"),
                status="ready" if skdata.get("requires") else "unknown",
                approval_required=skdata.get("safety", {}).get("approval_required", False),
                description=skdata.get("description"),
            )
            db.merge(skill)

    db.commit()
    return get_robot(db, robot_id)


def get_robot_embodiment(db: Session, robot_id: str):
    from models.schemas import SensorResponse, ActuatorResponse, SkillResponse, EmbodimentResponse

    robot = db.query(Robot).filter(Robot.id == robot_id).first()
    if not robot:
        return None

    sensors = db.query(Sensor).filter(Sensor.robot_id == robot_id).all()
    actuators = db.query(Actuator).filter(Actuator.robot_id == robot_id).all()
    skills = db.query(Skill).filter(Skill.robot_id == robot_id).all()

    return EmbodimentResponse(
        robot=RobotResponse.model_validate(robot),
        sensors=[SensorResponse.model_validate(s) for s in sensors],
        actuators=[ActuatorResponse.model_validate(a) for a in actuators],
        skills=[SkillResponse.model_validate(s) for s in skills],
    )

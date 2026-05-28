from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from models.database import get_db
from models.schemas import RobotCreate, RobotResponse, RobotImportRequest, EmbodimentResponse
from services.robot_service import get_robots, get_robot, create_robot, import_robot_from_directory, get_robot_embodiment

router = APIRouter(prefix="/robots", tags=["robots"])


@router.get("", response_model=list[RobotResponse])
def list_robots(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return get_robots(db, skip=skip, limit=limit)


@router.get("/{robot_id}", response_model=RobotResponse)
def read_robot(robot_id: str, db: Session = Depends(get_db)):
    robot = get_robot(db, robot_id)
    if not robot:
        raise HTTPException(status_code=404, detail="Robot not found")
    return robot


@router.post("", response_model=RobotResponse, status_code=201)
def register_robot(robot: RobotCreate, db: Session = Depends(get_db)):
    existing = get_robot(db, robot.id)
    if existing:
        raise HTTPException(status_code=409, detail="Robot already exists")
    return create_robot(db, robot)


@router.post("/import", response_model=RobotResponse)
def import_robot(req: RobotImportRequest, db: Session = Depends(get_db)):
    try:
        return import_robot_from_directory(db, req.robot_id, req.directory)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{robot_id}/embodiment", response_model=EmbodimentResponse)
def read_embodiment(robot_id: str, db: Session = Depends(get_db)):
    embodiment = get_robot_embodiment(db, robot_id)
    if not embodiment:
        raise HTTPException(status_code=404, detail="Robot not found")
    return embodiment


@router.get("/{robot_id}/sensors")
def read_robot_sensors(robot_id: str, db: Session = Depends(get_db)):
    embodiment = get_robot_embodiment(db, robot_id)
    if not embodiment:
        raise HTTPException(status_code=404, detail="Robot not found")
    return embodiment.sensors


@router.get("/{robot_id}/actuators")
def read_robot_actuators(robot_id: str, db: Session = Depends(get_db)):
    embodiment = get_robot_embodiment(db, robot_id)
    if not embodiment:
        raise HTTPException(status_code=404, detail="Robot not found")
    return embodiment.actuators


@router.get("/{robot_id}/skills")
def read_robot_skills(robot_id: str, db: Session = Depends(get_db)):
    embodiment = get_robot_embodiment(db, robot_id)
    if not embodiment:
        raise HTTPException(status_code=404, detail="Robot not found")
    return embodiment.skills


@router.get("/{robot_id}/health")
def read_robot_health(robot_id: str, db: Session = Depends(get_db)):
    robot = get_robot(db, robot_id)
    if not robot:
        raise HTTPException(status_code=404, detail="Robot not found")
    return {"status": robot.status, "robot_id": robot_id}

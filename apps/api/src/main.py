from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from models.database import init_db
from routers import robots_router, missions_router, mcap_router, skills_router, memory_router, safety_router, events_router, runtime_router

app = FastAPI(
    title=settings.app_name,
    description="ROSClaw Dashboard API — e-URDF-native Physical AI control plane",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(robots_router, prefix="/api")
app.include_router(missions_router, prefix="/api")
app.include_router(mcap_router, prefix="/api")
app.include_router(skills_router, prefix="/api")
app.include_router(memory_router, prefix="/api")
app.include_router(safety_router, prefix="/api")
app.include_router(events_router, prefix="/api")
app.include_router(runtime_router, prefix="/api")


@app.on_event("startup")
async def on_startup():
    init_db()
    # Auto-start agent daemons for all registered robots
    from sqlalchemy.orm import Session
    from models.database import get_db, Robot
    from services.agent_daemon import get_or_create_daemon
    db = next(get_db())
    robots = db.query(Robot).all()
    for robot in robots:
        daemon = get_or_create_daemon(robot.id)
        await daemon.start()


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok", "version": "0.1.0", "service": "rosclaw-api"}

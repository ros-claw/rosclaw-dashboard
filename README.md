# ROSClaw Dashboard

e-URDF-native Physical AI Control Plane — unifying robot embodiment, live telemetry, MCAP replay, agent missions, skill execution, memory inspection, and simulation feedback.

## Architecture

```
rosclaw-dashboard/
├── apps/
│   ├── api/              FastAPI backend (SQLite + DuckDB)
│   ├── web/              Next.js dashboard frontend
│   └── robot-daemon/     WebSocket bridge for robot telemetry
├── packages/
│   ├── eurdf-schema/      TypeScript interfaces for e-URDF
│   ├── eurdf-parser/      YAML parser + Zod validator + CLI
│   ├── mcap-indexer/      MCAP file indexing
│   ├── foxglove-layout-generator/  Foxglove layout generator
│   ├── robot-viewer/      3D robot viewer (Three.js)
│   ├── timeline-core/     Unified timeline engine
│   └── sdk/               Client SDK
├── robots/
│   ├── unitree_go2/       Unitree Go2 sample config
│   ├── ur5e/              UR5e sample config
│   └── turtlebot4/        TurtleBot4 sample config
└── docs/                  Documentation
```

## Quick Start

### Prerequisites

- Node.js >= 22
- pnpm (`corepack enable`)
- Python >= 3.11

### Install

```bash
pnpm install
cd apps/api && python -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"
```

### Run Backend

```bash
cd apps/api
source .venv/bin/activate
uvicorn src.main:app --reload --port 8000

# Seed sample robots
python scripts/seed.py
```

### Run Frontend

```bash
cd apps/web
pnpm dev
```

Visit `http://localhost:3000`

### Run Robot Daemon

```bash
cd apps/robot-daemon
pnpm build
ROBOT_ID=go2_lab_001 pnpm start
```

## V0.1 MVP Features

| Feature | Status |
|---------|--------|
| e-URDF Schema & Parser | Done |
| Robot Registry | Done |
| Embodiment Explorer | Done |
| MCAP Import / Index | Done |
| Foxglove Layout Generator | Done |
| Mission Board | Done |
| Agent Execution Trace | Done |
| Unified Timeline (stub) | Done |
| Safety Center | Done |
| Memory Inspector | Done |

## Dashboard Pages

1. **Robot Registry** — Register and manage robots
2. **Embodiment Explorer** — Browse sensors, actuators, skills
3. **Live Robot Console** — Real-time telemetry (via robot-daemon)
4. **Agent Mission Control** — Mission board with pause/resume/abort
5. **MCAP Replay & Review** — MCAP file management and Foxglove integration
6. **Skill & Capability Matrix** — Skill readiness per robot
7. **Memory Inspector** — rosclaw-memory integration (future)
8. **Safety & Approval Center** — Emergency stop, speed limits, approvals

## API Endpoints

```
GET  /health
GET  /api/robots
POST /api/robots
POST /api/robots/import
GET  /api/robots/{id}
GET  /api/robots/{id}/embodiment
GET  /api/robots/{id}/sensors
GET  /api/robots/{id}/actuators
GET  /api/robots/{id}/skills
GET  /api/missions
POST /api/missions
GET  /api/missions/{id}
GET  /api/missions/{id}/trace
POST /api/missions/{id}/pause
POST /api/missions/{id}/resume
POST /api/missions/{id}/abort
GET  /api/mcap
POST /api/mcap/import
GET  /api/mcap/{id}/foxglove-layout
GET  /api/memory
GET  /api/memory/stats/summary
GET  /api/safety/audits
GET  /api/safety/rules
POST /api/safety/rules/{id}/toggle
```

## e-URDF Format

Robots are described by YAML sidecars alongside URDF:

```
robots/{robot_id}/
  robot.eurdf.yaml    # Body model, sensors, actuators, frames
  robot.skills.yaml   # Skill definitions and requirements
  robot.safety.yaml   # Safety limits and approval rules
```

## License

MIT

# ROSClaw API

FastAPI backend for ROSClaw Dashboard.

## Setup

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Run

```bash
uvicorn src.main:app --reload --port 8000
```

## Test

```bash
pytest
```

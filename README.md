# Minimal Workflow Engine (AI Engineering assignment)

This repository implements a small backend workflow/agent engine as required by the coding assignment.

Quick start

1. Create a virtual environment and install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Run the app:

```powershell
uvicorn app.main:app --reload --port 8000
```

Endpoints

- `POST /graph/create` - create a graph. Use `{"preset":"code_review"}` to create the sample.
- `POST /graph/run` - run a graph. Body: `{"graph_id": "<id>", "initial_state": {...}, "wait": false}`
- `GET /graph/state/{run_id}` - fetch current state and logs of a run.
- `WS /ws/{run_id}` - optional websocket to stream logs/state.

What it supports

- Nodes as Python functions (sync or async) that accept and modify a `state` dict.
- In-memory registry of nodes and in-memory storage of graphs and runs (simple, easy to reason about).
- Basic branching/explicit next support: a node can return `{"next": "node_name"}` to jump.
- Looping: sample `assess_loop` node demonstrates looping until a threshold.

Sample workflow implemented

Option A: Code Review Mini-Agent. The sample uses simple rule-based tools:
- `extract` - naive function extractor
- `complexity` - simple complexity heuristic
- `detect` - detect TODO/FIXME and long lines
- `suggest` - suggestions + compute a quality score
- `assess_loop` - loops until `quality_score >= threshold` (simplified)

What I'd improve with more time

- Persist graphs and runs in SQLite/Postgres instead of memory.
- Provide a richer graph creation schema and validation (using Pydantic schemas).
- Add authentication and permissions for graphs/runs.
- Add unit tests and CI workflow.
- Add server-side streaming (async queues) for precise websocket log streaming.

Notes

- The sample workflow is intentionally rule-based and small; this submission focuses on clarity and structure.

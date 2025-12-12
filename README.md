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

WebSocket streaming and logging

- The server now supports push-based WebSocket streaming for runs. Connect to `ws://127.0.0.1:<port>/ws/{run_id}` to receive step-by-step events (JSON) while a run executes. Events look like:

```json
{
	"type": "step",
	"run_id": "...",
	"node": "extract",
	"state": { /* current state snapshot */ },
	"log": "[RUNNING] extract",
	"status": "running"
}
```

- If the server can't create a push queue at run time, the websocket endpoint automatically falls back to polling snapshots of the run state.
- The server emits structured logging to the console; enable file logging by piping stdout or extending the logging config in `app/main.py`.

Port note: if you run the server on a different port (e.g. `8001`) use that port for REST and WS endpoints, for example `http://127.0.0.1:8001/graph/create` and `ws://127.0.0.1:8001/ws/{run_id}`.

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
Screenshots:

<img width="987" height="731" alt="Screenshot 2025-12-12 115303" src="https://github.com/user-attachments/assets/016b9dd1-4fd0-4727-b812-e66529a4b3fb" />
<img width="993" height="692" alt="Screenshot 2025-12-12 115350" src="https://github.com/user-attachments/assets/9e02a1ad-fcd9-4681-99df-09cd17944897" />
<img width="1428" height="917" alt="Screenshot 2025-12-12 115426" src="https://github.com/user-attachments/assets/85aa3d18-bf78-4786-ba93-1f7d6e85b2ec" />
<img width="880" height="459" alt="Screenshot 2025-12-12 121941" src="https://github.com/user-attachments/assets/80d209ff-0baf-462b-940c-db98c9468638" />
<img width="1088" height="409" alt="image" src="https://github.com/user-attachments/assets/5eedb96e-1e81-4dcc-95d3-39a2ebd4e80e" />





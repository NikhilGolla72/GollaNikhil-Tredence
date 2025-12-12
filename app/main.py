import asyncio
import uuid
from fastapi import FastAPI, HTTPException, WebSocket
from pydantic import BaseModel
from typing import Dict, Any

from app.engine import GraphEngine
from app.tools import (
    extract_functions,
    check_complexity,
    detect_issues,
    suggest_improvements,
)
from app.workflows.code_review import build_code_review_graph


app = FastAPI(title="Minimal Workflow Engine")
engine = GraphEngine()

# register nodes
engine.register_node("extract", extract_functions)
engine.register_node("complexity", check_complexity)
engine.register_node("detect", detect_issues)
engine.register_node("suggest", suggest_improvements)

# helper node to assess loop logic
async def assess_loop(state: Dict[str, Any]):
    # check quality score and decide to loop or finish
    threshold = 80
    quality = state.get("quality_score", 0)
    if quality < threshold:
        # pretend we apply suggestions and reduce issues_count
        state_updates = {"issues_count": max(0, state.get("issues_count", 0) - 1)}
        # jump back to complexity to re-evaluate
        return {"state": state_updates, "next": "complexity"}
    return {}

engine.register_node("assess_loop", assess_loop)


class CreateGraphRequest(BaseModel):
    # either describe nodes/edges or request a preset
    preset: str = None
    nodes: Dict[str, Any] = None
    edges: Dict[str, str] = None


class RunGraphRequest(BaseModel):
    graph_id: str
    initial_state: Dict[str, Any]
    wait: bool = False


@app.post("/graph/create")
async def create_graph(req: CreateGraphRequest):
    if req.preset == "code_review":
        graph = build_code_review_graph()
        graph_id = engine.create_graph(graph)
        return {"graph_id": graph_id}

    if not req.nodes or not req.edges:
        raise HTTPException(status_code=400, detail="Provide 'preset' or both 'nodes' and 'edges'")

    graph_def = {"start": list(req.nodes.keys())[0], "nodes": list(req.nodes.keys()), "edges": req.edges}
    graph_id = engine.create_graph(graph_def)
    return {"graph_id": graph_id}


@app.post("/graph/run")
async def run_graph(req: RunGraphRequest):
    graph = engine.graphs.get(req.graph_id)
    if graph is None:
        raise HTTPException(status_code=404, detail="Graph not found")
    run_queue = asyncio.Queue()

    # generate run_id up-front and start background task with it so we
    # can return the run_id immediately for non-waiting calls.
    run_id = str(uuid.uuid4())

    # start background execution (engine.run_graph will create the run entry immediately)
    task = asyncio.create_task(engine.run_graph(req.graph_id, req.initial_state, run_id=run_id, run_queue=run_queue))

    if req.wait:
        # wait for completion and return final run result
        run = await task
        return {"run_id": run["id"], "state": run["state"], "log": run["log"]}

    # background started — return run id immediately
    return {"run_id": run_id}


@app.get("/graph/state/{run_id}")
async def get_state(run_id: str):
    run = engine.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return {"run_id": run_id, "state": run["state"], "status": run["status"], "log": run["log"]}


@app.websocket("/ws/{run_id}")
async def websocket_stream(websocket: WebSocket, run_id: str):
    await websocket.accept()
    # naive: stream latest logs for the run periodically
    try:
        while True:
            run = engine.get_run(run_id)
            if run:
                await websocket.send_json({"state": run.get("state"), "status": run.get("status"), "log": run.get("log")})
                if run.get("status") in ("completed", "failed"):
                    break
            await asyncio.sleep(0.5)
    except Exception:
        await websocket.close()

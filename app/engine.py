import asyncio
import uuid
import logging
from typing import Callable, Dict, Any, Optional

logger = logging.getLogger(__name__)


class GraphEngine:
    def __init__(self):
        # graphs: graph_id -> graph_def
        self.graphs: Dict[str, Dict[str, Any]] = {}
        # runs: run_id -> run info (state, status, log, queue)
        self.runs: Dict[str, Dict[str, Any]] = {}
        # registry of node functions by name
        self.node_registry: Dict[str, Callable] = {}

    def register_node(self, name: str, fn: Callable):
        self.node_registry[name] = fn

    def create_graph(self, graph_def: Dict[str, Any]) -> str:
        graph_id = str(uuid.uuid4())
        self.graphs[graph_id] = graph_def
        return graph_id

    def get_graph(self, graph_id: str) -> Dict[str, Any]:
        return self.graphs[graph_id]

    def get_run(self, run_id: str) -> Dict[str, Any]:
        return self.runs.get(run_id)

    async def _run_node(self, node_name: str, state: Dict[str, Any], run: Dict[str, Any]):
        fn = self.node_registry.get(node_name)
        if fn is None:
            run["log"].append(f"[ERROR] Node '{node_name}' not found")
            logger.error("Node '%s' not found", node_name)
            return None
        run["log"].append(f"[RUNNING] {node_name}")
        logger.info("Running node %s for run %s", node_name, run.get("id"))
        try:
            if asyncio.iscoroutinefunction(fn):
                out = await fn(state)
            else:
                out = fn(state)
        except Exception as e:
            run["log"].append(f"[EXCEPTION] {node_name}: {e}")
            logger.exception("Exception in node %s: %s", node_name, e)
            raise

        # merge state
        if isinstance(out, dict):
            # support returning {'state': {...}, 'next': 'node'} or direct state updates
            if "state" in out:
                state.update(out.get("state", {}))
            else:
                # assume returns state updates
                state.update(out)
            # optional next
            return out.get("next")
        else:
            return None

    async def run_graph(self, graph_id: str, initial_state: Dict[str, Any], run_id: Optional[str] = None, run_queue: Optional[asyncio.Queue] = None):
        graph = self.graphs.get(graph_id)
        if graph is None:
            raise KeyError("graph not found")

        if run_id is None:
            run_id = str(uuid.uuid4())

        run = {
            "id": run_id,
            "graph_id": graph_id,
            "state": dict(initial_state),
            "status": "running",
            "log": [],
        }
        # attach the optional run_queue so external consumers (websockets) can stream events
        run["queue"] = run_queue
        logger.info("Created run %s for graph %s", run_id, graph_id)
        self.runs[run_id] = run

        start_node = graph.get("start")
        if start_node is None:
            run["status"] = "failed"
            run["log"].append("no start node configured")
            return run

        current = start_node
        try:
            while current:
                # allow external streaming
                run["current_node"] = current
                next_node = await self._run_node(current, run["state"], run)
                # stream log/state event if queue provided
                if run_queue is not None:
                    try:
                        await run_queue.put({
                            "type": "step",
                            "run_id": run_id,
                            "node": current,
                            "state": dict(run["state"]),
                            "log": run["log"][-1],
                            "status": run["status"],
                        })
                    except Exception:
                        logger.exception("Failed to push to run queue for run %s", run_id)
                # if node returned explicit next
                if next_node:
                    current = next_node
                    continue
                # otherwise use edges
                edges = graph.get("edges", {})
                current = edges.get(current)
        except Exception:
            run["status"] = "failed"
            return run

        run["status"] = "completed"
        return run

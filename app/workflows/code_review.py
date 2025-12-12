from typing import Dict, Any


def build_code_review_graph(threshold: int = 80) -> Dict[str, Any]:
    # nodes are names that must be registered in the engine's node registry
    nodes = [
        "extract",
        "complexity",
        "detect",
        "suggest",
        "assess_loop",
    ]

    edges = {
        "extract": "complexity",
        "complexity": "detect",
        "detect": "suggest",
        # 'suggest' will lead to 'assess_loop' which decides to stop or repeat
        "suggest": "assess_loop",
    }

    # start node
    graph = {
        "name": "code_review",
        "start": "extract",
        "nodes": nodes,
        "edges": edges,
        "meta": {"threshold": threshold},
    }
    return graph

import json
from typing import Dict, List
from .types import Node, Edge


def merge_graphs(graphs: List[Dict[str, object]]) -> Dict[str, object]:
    node_map: Dict[str, Node] = {}
    edges: List[Edge] = []
    meta: Dict[str, object] = {}

    for g in graphs:
        for n in g.get("nodes", []):
            node = Node(id=n["id"], type=n["type"], properties=n.get("properties", {}))
            if node.id not in node_map:
                node_map[node.id] = node
            else:
                node_map[node.id].properties.update(node.properties)
        for e in g.get("edges", []):
            edges.append(Edge(source=e["source"], target=e["target"], type=e["type"], properties=e.get("properties", {})))
        gm = g.get("meta")
        if isinstance(gm, dict):
            if "outlineSummary" in gm:
                existing = meta.get("outlineSummary") or []
                meta["outlineSummary"] = list(existing) + list(gm.get("outlineSummary") or [])

    seen = set()
    unique_edges: List[Edge] = []
    for e in edges:
        key = (e.source, e.target, e.type, json.dumps(e.properties, sort_keys=True))
        if key not in seen:
            seen.add(key)
            unique_edges.append(e)

    return {
        "nodes": [n.__dict__ for n in node_map.values()],
        "edges": [e.__dict__ for e in unique_edges],
        **({"meta": meta} if meta else {}),
    }



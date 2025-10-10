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
            edges.append(
                Edge(
                    source=e["source"],
                    target=e["target"],
                    type=e["type"],
                    properties=e.get("properties", {}),
                )
            )
        gm = g.get("meta")
        if isinstance(gm, dict):
            # Preserve outlineSummary
            if "outlineSummary" in gm:
                existing = meta.get("outlineSummary") or []
                meta["outlineSummary"] = list(existing) + list(
                    gm.get("outlineSummary") or []
                )
            # Preserve other metadata from the first graph (usually the main one)
            if not meta:
                meta.update(gm)
            # Add course-specific metadata
            if "level" in gm or "course_id" in gm or "status" in gm:
                if "courses" not in meta:
                    meta["courses"] = []
                meta["courses"].append({
                    "level": gm.get("level"),
                    "course_id": gm.get("course_id"),
                    "status": gm.get("status"),
                    "error": gm.get("error")
                })
            # Preserve course parsing statistics
            if "courses_parsed" in gm:
                meta["courses_parsed"] = gm["courses_parsed"]
            if "courses_successful" in gm:
                meta["courses_successful"] = gm["courses_successful"]
            if "courses_failed" in gm:
                meta["courses_failed"] = gm["courses_failed"]
            if "total_courses_found" in gm:
                meta["total_courses_found"] = gm["total_courses_found"]

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

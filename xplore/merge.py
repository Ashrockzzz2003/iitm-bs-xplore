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

    # Create direct level-to-course relationships
    # Find all level nodes
    level_nodes = {node_id: node for node_id, node in node_map.items() 
                  if node.type == "Level"}
    
    # Find all course nodes
    course_nodes = {node_id: node for node_id, node in node_map.items() 
                   if node.type == "Course"}
    
    # Ensure Foundation level exists
    foundation_level_id = "level:foundation"
    if foundation_level_id not in level_nodes:
        foundation_level = Node(
            id=foundation_level_id,
            type="Level",
            properties={"title": "FOUNDATION"}
        )
        node_map[foundation_level_id] = foundation_level
        level_nodes[foundation_level_id] = foundation_level
        # Connect Foundation level to program
        edges.append(
            Edge(
                source="program:IITM_BS",
                target=foundation_level_id,
                type="HAS_LEVEL",
                properties={}
            )
        )

    # Create level-to-course mapping based on course metadata and course codes
    for course_id, course in course_nodes.items():
        course_meta = None
        # Find course metadata from the merged graphs
        for g in graphs:
            # Check if this graph has course metadata
            if "meta" in g and "level" in g["meta"]:
                course_id_from_meta = g["meta"].get("course_id")
                if course_id_from_meta == course.properties.get("courseId"):
                    course_meta = g["meta"]
                    break
            # Also check the courses array format
            if "meta" in g and "courses" in g["meta"]:
                for course_info in g["meta"]["courses"]:
                    if course_info.get("course_id") == course.properties.get("courseId"):
                        course_meta = course_info
                        break
            if course_meta:
                break
        
        # Determine level from metadata or course code
        level_name = None
        if course_meta and course_meta.get("level"):
            level_name = course_meta["level"]
        else:
            # Infer level from course code
            course_code = course.properties.get("courseId", "")
            if course_code.startswith(("BSMA100", "BSCS100", "BSHS100")):
                level_name = "Foundation"
            elif course_code.startswith(("BSMA200", "BSCS200", "BSHS200", "BSMS200", "BSSE200", "BSDA200")):
                level_name = "Diploma"
            elif course_code.startswith(("BSMA300", "BSCS300", "BSHS300", "BSMS300", "BSSE300", "BSDA300", "BSGN300")):
                level_name = "Degree"
            elif course_code.startswith(("BSMA400", "BSCS400", "BSHS400", "BSMS400", "BSSE400", "BSDA400", "BSBT400")):
                level_name = "Degree"
            elif course_code.startswith(("BSMA500", "BSCS500", "BSHS500", "BSMS500", "BSSE500", "BSDA500", "BSEE500")):
                level_name = "Degree"
            elif course_code.startswith(("BSMA600", "BSCS600", "BSHS600", "BSMS600", "BSSE600", "BSDA600")):
                level_name = "Degree"
            elif course_code.startswith(("BSMA690", "BSCS690", "BSHS690", "BSMS690", "BSSE690", "BSDA690")):
                level_name = "Degree"
        
        if level_name:
            # Find matching level node
            matching_level = None
            for level_id, level in level_nodes.items():
                level_title = level.properties.get("title", "").upper()
                if level_name.upper() in level_title or level_title in level_name.upper():
                    matching_level = level_id
                    break
            
            if matching_level:
                # Create direct edge from level to course
                edges.append(
                    Edge(
                        source=matching_level,
                        target=course_id,
                        type="CONTAINS",
                        properties={"what": "course"}
                    )
                )

    # Deduplicate course attributes to remove duplicate content
    for node_id, node in node_map.items():
        if node.type == "Course":
            properties = node.properties
            if "attributes" in properties:
                attributes = properties["attributes"]
                # Find and remove duplicate content across different fields
                content_signatures = {}
                fields_to_remove = []
                
                for field_name, field_content in attributes.items():
                    if isinstance(field_content, dict):
                        # Check paragraphs
                        if "paragraphs" in field_content:
                            paragraphs = field_content["paragraphs"]
                            if paragraphs:
                                # Create a signature based on the first paragraph (usually the title)
                                signature = paragraphs[0].strip() if paragraphs else ""
                                if signature and signature in content_signatures:
                                    # This is a duplicate, mark for removal
                                    fields_to_remove.append(field_name)
                                else:
                                    content_signatures[signature] = field_name
                        
                        # Check bullets for duplicates
                        elif "bullets" in field_content:
                            bullets = field_content["bullets"]
                            if bullets:
                                # Create signature from first bullet
                                signature = bullets[0].strip() if bullets else ""
                                if signature and signature in content_signatures:
                                    fields_to_remove.append(field_name)
                                else:
                                    content_signatures[signature] = field_name
                        
                        # Check fields for duplicates
                        elif "fields" in field_content:
                            fields = field_content["fields"]
                            if fields:
                                # Create signature from field values
                                field_values = list(fields.values())
                                if field_values:
                                    signature = field_values[0].strip() if field_values else ""
                                    if signature and signature in content_signatures:
                                        fields_to_remove.append(field_name)
                                    else:
                                        content_signatures[signature] = field_name
                
                # Remove duplicate fields
                for field_name in fields_to_remove:
                    del attributes[field_name]

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

from typing import Dict, List, Optional
from bs4 import BeautifulSoup, Tag
from .types import Node, Edge
from .outline import build_outline, SectionOutline
from .utils import slugify


def parse_generic_html(
    html: str, root_id: str = "doc:ROOT", root_title: str = "Document"
) -> Dict[str, object]:
    soup = BeautifulSoup(html, "lxml")
    outline_roots = build_outline(soup)

    nodes: Dict[str, Node] = {}
    edges: List[Edge] = []
    outline_summary: List[Dict[str, object]] = []

    def ensure_node(nid: str, ntype: str, props: Dict[str, object]) -> Node:
        if nid not in nodes:
            nodes[nid] = Node(id=nid, type=ntype, properties=dict(props))
        else:
            nodes[nid].properties.update(props)
        return nodes[nid]

    root = ensure_node(root_id, "Document", {"title": root_title})

    def next_sibling_section_content(header: Tag) -> List[Tag]:
        content_nodes: List[Tag] = []
        level = (
            int(header.name[1]) if header.name and header.name.startswith("h") else 7
        )
        node = header
        while True:
            node = node.find_next_sibling()
            if node is None:
                break
            if isinstance(node, Tag) and node.name and node.name.startswith("h"):
                hlevel = int(node.name[1])
                if hlevel <= level:
                    break
            content_nodes.append(node)
        return content_nodes

    def extract_tables(nodes: List[Tag]) -> List[List[List[str]]]:
        tables_rows: List[List[List[str]]] = []
        for table in [n for parent in nodes for n in parent.select("table")]:
            tbody = table.find("tbody") or table
            table_data: List[List[str]] = []
            for tr in tbody.find_all("tr"):
                cells = tr.find_all(["th", "td"])
                row = [(c.get_text(" ", strip=True) or "").strip() for c in cells]
                if any(cell for cell in row):
                    table_data.append(row)
            if table_data:
                tables_rows.append(table_data)
        return tables_rows

    def register_outline(
        node: SectionOutline, parent_id: Optional[str], depth: int
    ) -> None:
        sec_id = f"section:{slugify(node.title) or (node.tag_id or 'untitled')}"
        props = {
            "title": node.title,
            "level": node.level,
            "childCount": node.child_count(),
            "depth": depth,
            "isParent": node.child_count() > 0,
        }
        if node.tag_id:
            props["anchorId"] = node.tag_id
        sec_node = ensure_node(sec_id, "Section", props)
        edges.append(
            Edge(
                source=(parent_id or root.id),
                target=sec_node.id,
                type="HAS_SECTION",
                properties={"hierarchical": True},
            )
        )
        for child in node.children:
            register_outline(child, sec_node.id, depth + 1)

    for r in outline_roots:
        register_outline(r, parent_id=None, depth=0)

    # Attach table data to sections that reference an anchorId
    for n in list(nodes.values()):
        if n.type == "Section" and n.properties.get("anchorId"):
            start = soup.find(id=n.properties.get("anchorId"))
            if start is not None:
                content_nodes = next_sibling_section_content(start)
                tables = extract_tables(content_nodes)
                if tables:
                    n.properties["tables"] = tables

    def iter_outline(nodes_: List[SectionOutline]):
        for n in nodes_:
            yield n
            for c in iter_outline(n.children):
                yield c

    def pack_outline(n: SectionOutline) -> Dict[str, object]:
        return {
            "title": n.title,
            "level": n.level,
            "anchorId": n.tag_id,
            "sectionId": f"section:{slugify(n.title) or (n.tag_id or 'untitled')}",
        }

    parents_ = [n for n in iter_outline(outline_roots) if n.child_count() > 0]
    for p in parents_:
        outline_summary.append(
            {
                "parent": pack_outline(p),
                "children": [pack_outline(c) for c in p.children],
            }
        )

    return {
        "nodes": [n.__dict__ for n in nodes.values()],
        "edges": [e.__dict__ for e in edges],
        "meta": {"outlineSummary": outline_summary},
    }

import argparse
import json
from pathlib import Path
from typing import List
from bs4 import BeautifulSoup

from xplore import parse_academics_html, parse_course_html, parse_generic_html, merge_graphs
from xplore.outline import build_outline, SectionOutline


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse IITM BS HTML into a knowledge graph JSON")
    parser.add_argument("--academics", type=str, help="Path to academics.html", required=False)
    parser.add_argument("--course-files", type=str, nargs="*", help="Paths to course HTML pages", default=None)
    parser.add_argument("--generic", type=str, nargs="*", help="Paths to generic HTML pages", default=None)
    parser.add_argument("--output", type=str, help="Path to write KG JSON (default: print)")
    parser.add_argument("--out-dir", type=str, default="outputs", help="Directory for generated JSON files when a bare filename is given")
    parser.add_argument("--outline-summary", action="store_true", help="Print logical summary: each parent section and its immediate children")
    args = parser.parse_args()

    graphs: List[dict] = []

    if args.academics:
        html = Path(args.academics).read_text(encoding="utf-8", errors="ignore")
        graphs.append(parse_academics_html(html, base_url=str(Path(args.academics).parent)))
        if args.outline_summary:
            soup = BeautifulSoup(html, "lxml")
            roots = build_outline(soup)
            def compact(text: str, max_len: int = 120) -> str:
                t = (text or "").strip()
                return t if len(t) <= max_len else (t[: max_len - 1] + "…")
            def iter_nodes(nodes: List[SectionOutline]):
                for n in nodes:
                    yield n
                    for c in iter_nodes(n.children):
                        yield c
            parents = [n for n in iter_nodes(roots) if n.child_count() > 0]
            for p in parents:
                anchor = f" #{p.tag_id}" if p.tag_id else ""
                print(f"Parent: {compact(p.title)} (h{p.level}, children={p.child_count()}){anchor}")
                for c in p.children:
                    canchor = f" #{c.tag_id}" if c.tag_id else ""
                    print(f"  - Child: {compact(c.title)} (h{c.level}){canchor}")

    if args.course_files:
        for cf in args.course_files:
            html = Path(cf).read_text(encoding="utf-8", errors="ignore")
            graphs.append(parse_course_html(html, source_path=cf))

    if args.generic:
        for gf in args.generic:
            html = Path(gf).read_text(encoding="utf-8", errors="ignore")
            graphs.append(parse_generic_html(html, root_id=f"doc:{Path(gf).stem}", root_title=Path(gf).name))

    if not graphs:
        raise SystemExit("No input files provided. Use --academics and/or --course-files or --generic")

    kg = merge_graphs(graphs)
    out = json.dumps(kg, indent=2, ensure_ascii=False)
    if args.output:
        out_path = Path(args.output)
        # If user provided a bare filename (no directory), place it under --out-dir
        if not out_path.is_absolute() and (out_path.parent == Path(".")):
            out_path = Path(args.out_dir) / out_path.name
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(out, encoding="utf-8")
    else:
        print(out)


if __name__ == "__main__":
    main()



"""
Output Handling Module

Handles writing knowledge graph data to files and printing output.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional


def write_output(
    kg: Dict[str, Any], 
    output_path: str, 
    out_dir: str, 
    parser_used: Optional[str]
) -> None:
    """Write knowledge graph to file or print to stdout.
    
    This function handles the final output of the knowledge graph extraction process.
    It can either save to a file or print to stdout based on the output_path parameter.
    """
    out = json.dumps(kg, indent=2, ensure_ascii=False)

    if output_path:
        out_path = Path(output_path)
        # If user provided a bare filename (no directory), place it under --out-dir
        if not out_path.is_absolute() and (out_path.parent == Path(".")):
            out_path = Path(out_dir) / out_path.name
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(out, encoding="utf-8")
        print(f"Knowledge graph saved to: {out_path}")
        if parser_used:
            print(f"Parser used: {parser_used}")
    else:
        # Print to stdout if no output path specified
        print(out)

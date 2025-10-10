from .types import Node, Edge
from .outline import SectionOutline, build_outline
from .academics import parse_academics_html
from .course import parse_course_html
from .merge import merge_graphs
from .generic import parse_generic_html
from . import utils

__all__ = [
    "Node",
    "Edge",
    "SectionOutline",
    "build_outline",
    "parse_academics_html",
    "parse_course_html",
    "parse_generic_html",
    "merge_graphs",
    "utils",
]



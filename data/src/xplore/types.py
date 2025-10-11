from dataclasses import dataclass
from typing import Dict


@dataclass
class Node:
    id: str
    type: str
    properties: Dict[str, object]


@dataclass
class Edge:
    source: str
    target: str
    type: str
    properties: Dict[str, object]

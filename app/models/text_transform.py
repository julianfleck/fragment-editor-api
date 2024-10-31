from dataclasses import dataclass
from typing import List, Dict, Any, Union


@dataclass
class Version:
    text: str
    final_tokens: int
    final_percentage: float


@dataclass
class Length:
    target_percentage: int
    target_tokens: int
    versions: List[Version]


@dataclass
class Fragment:
    lengths: List[Length]


@dataclass
class TransformationResponse:
    fragments: List[Fragment]
    metadata: Dict[str, Any]
    type: str = "fragments"

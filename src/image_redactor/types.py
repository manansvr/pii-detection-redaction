# src/image_redactor/types.py

from dataclasses import dataclass
from typing import List, Optional, Tuple

@dataclass
class BoundingBox:
    left: int
    top: int
    width: int
    height: int
    entity_type: str
    score: Optional[float] = None


@dataclass
class RedactionResult:
    output_path: str
    boxes: List[BoundingBox]
    text_entities: List[str]

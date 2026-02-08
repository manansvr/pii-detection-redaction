# src/imageRedactor/types.py

from dataclasses import dataclass
from typing import List, Optional, Tuple

@dataclass
class BoundingBox:
    left: int
    top: int
    width: int
    height: int
    entityType: str
    score: Optional[float] = None


@dataclass
class RedactionResult:
    """this holds the output image path and metadata about redacted regions."""
    outputPath: str
    boxes: List[BoundingBox]
    textEntities: List[str]

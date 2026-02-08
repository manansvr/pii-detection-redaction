# src/textdetector/formatter.py

from __future__ import annotations

from typing import List, Dict
from presidio_analyzer import RecognizerResult


def resultsToJson(results: List[RecognizerResult], text: str) -> List[Dict]:
    """
    this converts the presidio recognizer result list to json-friendly objects,
    including matched value slices for convenience.
    """
    return [
        {
            "type": r.entity_type,
            "start": r.start,
            "end": r.end,
            "score": round(float(r.score), 4),
            "value": text[r.start:r.end],
        }
        for r in results
    ]
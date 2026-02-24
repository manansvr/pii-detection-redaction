# src/textdetector/formatter.py

from __future__ import annotations

from typing import List, Dict
from presidio_analyzer import RecognizerResult


def results_to_json(results: List[RecognizerResult], text: str) -> List[Dict]:
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
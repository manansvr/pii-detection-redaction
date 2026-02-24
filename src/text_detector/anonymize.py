# src/textdetector/anonymize.py

from __future__ import annotations

from typing import Dict, List
from presidio_anonymizer import AnonymizerEngine
from presidio_analyzer import RecognizerResult


def build_default_operators(
    results: List[RecognizerResult],
) -> Dict[str, Dict]:
    entities = {r.entity_type for r in results}
    return {
        ent: {"type": "replace", "new_value": f"<{ent}>"}
        for ent in entities
    }


def anonymize_text(
    text: str,
    analyzer_results: List[RecognizerResult],
    operators: Dict[str, Dict] | None = None,
) -> str:
    anonymizer = AnonymizerEngine()

    if operators is None:
        operators = build_default_operators(analyzer_results)

    anonymized = anonymizer.anonymize(
        text=text,
        analyzer_results=analyzer_results,
        operators=operators,
    )

    return anonymized.text
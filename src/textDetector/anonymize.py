# src/textdetector/anonymize.py

from __future__ import annotations

from typing import Dict, List
from presidio_anonymizer import AnonymizerEngine
from presidio_analyzer import RecognizerResult


def buildDefaultOperators(
    results: List[RecognizerResult],
) -> Dict[str, Dict]:
    """
    this builds a simple operator config replacing each entity with <entity_type>.
    """
    entities = {r.entity_type for r in results}
    return {
        ent: {"type": "replace", "new_value": f"<{ent}>"}
        for ent in entities
    }


def anonymizeText(
    text: str,
    analyzerResults: List[RecognizerResult],
    operators: Dict[str, Dict] | None = None,
) -> str:
    """
    this applies presidio anonymizer using detected analyzer results.
    """
    anonymizer = AnonymizerEngine()

    if operators is None:
        operators = buildDefaultOperators(analyzerResults)

    anonymized = anonymizer.anonymize(
        text=text,
        analyzer_results=analyzerResults,
        operators=operators,
    )

    return anonymized.text
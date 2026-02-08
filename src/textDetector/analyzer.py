# src/textdetector/analyzer.py

from __future__ import annotations

from presidio_analyzer import AnalyzerEngine
from common import buildPresidioAnalyzer


def buildAnalyzer(language: str = "en") -> AnalyzerEngine:
    """
    builds a presidio analyzer engine using spacy via spacynlpengine.
    uses shared utility to avoid code duplication.
    """
    return buildPresidioAnalyzer(language)

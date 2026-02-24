# src/csv_redactor/analyzer.py

from __future__ import annotations

from presidio_analyzer import AnalyzerEngine
from common import build_presidio_analyzer


def build_analyzer(language: str = "en") -> AnalyzerEngine:
    return build_presidio_analyzer(language)

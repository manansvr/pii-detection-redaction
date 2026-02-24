# src/text_detector/chunker.py

from __future__ import annotations

from typing import Iterable, Tuple, Dict, List
from presidio_analyzer import AnalyzerEngine, RecognizerResult


def chunk_text(
    text: str,
    size: int = 5000,
    overlap: int = 300,
) -> Iterable[Tuple[int, str]]:
    if size <= 0:
        raise ValueError("Size Must Be > 0")
    if overlap < 0:
        raise ValueError("Over-Lap Must Be >= 0")

    L = len(text)
    i = 0

    while i < L:
        start = i if i == 0 else max(0, i - overlap)
        end = min(L, i + size)
        yield start, text[start:end]
        i += size


def analyze_long_text(
    analyzer: AnalyzerEngine,
    text: str,
    language: str = "en",
    size: int = 5000,
    overlap: int = 300,
    min_score: float = 0.0,
    entities: List[str] | None = None,
) -> List[RecognizerResult]:
    results_by_key: Dict[
        Tuple[int, int, str],
        RecognizerResult,
    ] = {}

    for start_offset, chunk in chunk_text(text, size=size, overlap=overlap):
        chunk_results = analyzer.analyze(text=chunk, language=language, entities=entities)

        for r in chunk_results:
            if r.score < min_score:
                continue

            global_start = start_offset + r.start
            global_end = start_offset + r.end
            key = (global_start, global_end, r.entity_type)

            existing = results_by_key.get(key)
            if not existing or r.score > existing.score:
                results_by_key[key] = RecognizerResult(
                    entity_type=r.entity_type,
                    start=global_start,
                    end=global_end,
                    score=r.score,
                    analysis_explanation=r.analysis_explanation,
                    recognition_metadata=r.recognition_metadata,
                )

    return sorted(
        results_by_key.values(),
        key=lambda x: (x.start, x.end, x.entity_type),
    )
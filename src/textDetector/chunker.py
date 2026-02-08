# src/textdetector/chunker.py

from __future__ import annotations

from typing import Iterable, Tuple, Dict, List
from presidio_analyzer import AnalyzerEngine, RecognizerResult


def chunkText(
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


def analyzeLongText(
    analyzer: AnalyzerEngine,
    text: str,
    language: str = "en",
    size: int = 5000,
    overlap: int = 300,
    minScore: float = 0.0,
) -> List[RecognizerResult]:
    resultsByKey: Dict[
        Tuple[int, int, str],
        RecognizerResult,
    ] = {}

    for startOffset, chunk in chunkText(text, size=size, overlap=overlap):
        chunkResults = analyzer.analyze(text=chunk, language=language)

        for r in chunkResults:
            if r.score < minScore:
                continue

            globalStart = startOffset + r.start
            globalEnd = startOffset + r.end
            key = (globalStart, globalEnd, r.entity_type)

            existing = resultsByKey.get(key)
            if not existing or r.score > existing.score:
                resultsByKey[key] = RecognizerResult(
                    entity_type=r.entity_type,
                    start=globalStart,
                    end=globalEnd,
                    score=r.score,
                    analysis_explanation=r.analysis_explanation,
                    recognition_metadata=r.recognition_metadata,
                )

    return sorted(
        resultsByKey.values(),
        key=lambda x: (x.start, x.end, x.entity_type),
    )
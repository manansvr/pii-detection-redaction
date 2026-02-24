# src/csv_redactor/redactor.py

from __future__ import annotations

import csv
from typing import List, Dict, Tuple
from pathlib import Path
from presidio_analyzer import AnalyzerEngine, RecognizerResult
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig


def analyze_csv_file(
    analyzer: AnalyzerEngine,
    file_path: str | Path,
    language: str = "en",
    min_score: float = 0.0,
    skip_header: bool = True,
    delimiter: str = ",",
    entities: List[str] | None = None,
) -> Tuple[List[List[str]], List[Dict]]:
    file_path = Path(file_path)
    detections = []

    with file_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f, delimiter=delimiter)
        rows = list(reader)

    start_row = 1 if skip_header and len(rows) > 0 else 0

    for row_idx in range(start_row, len(rows)):
        row = rows[row_idx]
        for col_idx, cell_value in enumerate(row):
            if not cell_value or not cell_value.strip():
                continue

            results = analyzer.analyze(text=cell_value, language=language, entities=entities)

            for r in results:
                if r.score >= min_score:
                    detections.append({
                        "row": row_idx,
                        "column": col_idx,
                        "entity_type": r.entity_type,
                        "start": r.start,
                        "end": r.end,
                        "score": r.score,
                        "value": cell_value[r.start:r.end],
                        "cell_value": cell_value,
                    })

    return rows, detections


def redact_csv_file(
    analyzer: AnalyzerEngine,
    input_path: str | Path,
    output_path: str | Path,
    language: str = "en",
    min_score: float = 0.0,
    skip_header: bool = True,
    delimiter: str = ",",
    redaction_char: str = "*",
    use_entity_labels: bool = False,
    entities: List[str] | None = None,
) -> Tuple[List[Dict], int]:
    input_path = Path(input_path)
    output_path = Path(output_path)

    rows, detections = analyze_csv_file(
        analyzer=analyzer,
        file_path=input_path,
        language=language,
        min_score=min_score,
        skip_header=skip_header,
        delimiter=delimiter,
        entities=entities,
    )

    redacted_rows = [list(row) for row in rows]

    cell_detections: Dict[Tuple[int, int], List[RecognizerResult]] = {}

    for det in detections:
        key = (det["row"], det["column"])
        if key not in cell_detections:
            cell_detections[key] = []

        cell_detections[key].append(
            RecognizerResult(
                entity_type=det["entity_type"],
                start=det["start"],
                end=det["end"],
                score=det["score"],
            )
        )

    anonymizer = AnonymizerEngine()
    redacted_cell_count = 0

    for (row_idx, col_idx), results in cell_detections.items():
        original_value = rows[row_idx][col_idx]

        if use_entity_labels:
            operators = {
                r.entity_type: OperatorConfig("replace", {"new_value": f"<{r.entity_type}>"})
                for r in results
            }
        else:
            operators = {
                r.entity_type: OperatorConfig("mask", {"masking_char": redaction_char, "chars_to_mask": 100, "from_end": False})
                for r in results
            }

        anonymized = anonymizer.anonymize(
            text=original_value,
            analyzer_results=results,
            operators=operators,
        )

        redacted_rows[row_idx][col_idx] = anonymized.text
        redacted_cell_count += 1

    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=delimiter)
        writer.writerows(redacted_rows)

    return detections, redacted_cell_count

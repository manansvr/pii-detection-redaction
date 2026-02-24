# src/csv_redactor/formatter.py

from __future__ import annotations

from typing import List, Dict


def results_to_json(detections: List[Dict]) -> List[Dict]:
    return [
        {
            "row": d["row"],
            "column": d["column"],
            "entity_type": d["entity_type"],
            "start": d["start"],
            "end": d["end"],
            "score": round(float(d["score"]), 4),
            "value": d["value"],
            "cell_value": d["cell_value"],
        }
        for d in detections
    ]


def summarize_detections(detections: List[Dict]) -> Dict:
    entity_counts = {}
    affected_cells = set()

    for d in detections:
        entity_type = d["entity_type"]
        entity_counts[entity_type] = entity_counts.get(entity_type, 0) + 1
        affected_cells.add((d["row"], d["column"]))

    return {
        "total_detections": len(detections),
        "affected_cells": len(affected_cells),
        "by_entity_type": entity_counts,
    }

# src/text_detector/relationships.py

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
from presidio_analyzer import RecognizerResult


@dataclass
class Owner:
    id: int
    span: Tuple[int, int]
    name: str


@dataclass
class Assignment:
    result: RecognizerResult
    owner_id: Optional[int]


def _split_lines_with_span(text: str) -> List[Tuple[int, int, str]]:
    lines = []
    i = 0
    for segment in text.splitlines(True):
        start = i
        end = i + len(segment)
        lines.append((start, end, segment))
        i = end

    return lines if lines else [(0, len(text), text)]


def _contains_token(local_part: str, tokens: List[str]) -> bool:
    lp = re.sub(r"[^a-z0-9]+", "", local_part.lower())
    return any(t for t in tokens if len(t) >= 3 and t.lower() in lp)


def _extract_person_tokens(name: str) -> List[str]:
    return [t for t in re.split(r"[^A-Za-z0-9]+", name) if t]


def _nearest_person_by_distance(owners: List[Owner], position: int) -> Optional[int]:
    if not owners:
        return None
    return min(owners, key=lambda o: abs(o.span[0] - position)).id


def assign_relationships(
    text: str,
    results: List[RecognizerResult]
) -> Tuple[List[Owner], List[Assignment]]:
    owners: List[Owner] = []
    for idx, r in enumerate([x for x in results if x.entity_type == "PERSON"]):
        owners.append(
            Owner(
                id=len(owners) + 1,
                span=(r.start, r.end),
                name=text[r.start : r.end],
            )
        )

    lines = _split_lines_with_span(text)

    person_tokens: Dict[int, List[str]] = {
        o.id: _extract_person_tokens(o.name) for o in owners
    }

    assignments: List[Assignment] = []

    for r in results:
        if r.entity_type == "PERSON":
            assignments.append(Assignment(result=r, owner_id=None))
            continue

        owner_id: Optional[int] = None

        for ls, lc, _ in lines:
            if r.start >= ls and r.end <= lc:
                same_line = [
                    o for o in owners if o.span[0] >= ls and o.span[1] <= lc
                ]
                if same_line:
                    owner_id = min(
                        same_line,
                        key=lambda o: abs(o.span[0] - r.start),
                    ).id
                break

        if owner_id is None and r.entity_type == "EMAIL_ADDRESS":
            value = text[r.start : r.end]
            if "@" in value:
                local_part = value.split("@", 1)[0]
                for o in owners:
                    if _contains_token(local_part, person_tokens[o.id]):
                        owner_id = o.id
                        break

        if owner_id is None:
            owner_id = _nearest_person_by_distance(owners, r.start)

        assignments.append(Assignment(result=r, owner_id=owner_id))

    return owners, assignments


def mask_with_relationships(
    text: str,
    results: List[RecognizerResult]
) -> str:
    owners, assignments = assign_relationships(text, results)

    person_labels: Dict[int, str] = {
        o.id: f"PERSON_{o.id}" for o in owners
    }

    repl_spans: List[Tuple[int, int, str]] = []

    for a in assignments:
        r = a.result
        ct = r.entity_type
        original = text[r.start : r.end]

        if ct == "PERSON":
            owner_id = None
            for o in owners:
                if o.span == (r.start, r.end):
                    owner_id = o.id
                    break
            replacement = person_labels.get(owner_id, "<PERSON>")
            repl_spans.append((r.start, r.end, replacement))
            continue

        if a.owner_id is not None:
            base = ct
            replacement = f"<{base}_PERSON_{a.owner_id}>"
        else:
            replacement = f"<{ct}>"

        if ct == "PHONE_NUMBER":
            digits = re.sub(r"\D", "", original)
            masked = "*" * len(digits)
            replacement = replacement.replace("<PHONE_NUMBER>", f"<PHONE_NUMBER_{masked}>")

        repl_spans.append((r.start, r.end, replacement))

    repl_spans.sort(key=lambda x: x[0], reverse=True)

    masked = text
    for s, e, rep in repl_spans:
        masked = masked[:s] + rep + masked[e:]

    return masked
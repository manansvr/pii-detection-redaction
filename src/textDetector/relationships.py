# src/textdetector/relationships.py

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
    ownerId: Optional[int]


def _splitLinesWithSpan(text: str) -> List[Tuple[int, int, str]]:
    """
    this splits by newline while keeping global start/end spans for each line,
    and returns: list of (line_start_idx, line_end_idx, line_text).
    """
    lines = []
    i = 0
    for segment in text.splitlines(True):
        start = i
        end = i + len(segment)
        lines.append((start, end, segment))
        i = end

    return lines if lines else [(0, len(text), text)]


def _containsToken(localPart: str, tokens: List[str]) -> bool:
    """this checks if any token (len>=3) from tokens occurs in localpart."""
    lp = re.sub(r"[^a-z0-9]+", "", localPart.lower())
    return any(t for t in tokens if len(t) >= 3 and t.lower() in lp)


def _extractPersonTokens(name: str) -> List[str]:
    return [t for t in re.split(r"[^A-Za-z0-9]+", name) if t]


def _nearestPersonByDistance(owners: List[Owner], position: int) -> Optional[int]:
    """finds the nearest person owner by character distance"""
    if not owners:
        return None
    return min(owners, key=lambda o: abs(o.span[0] - position)).id


def assignRelationships(
    text: str,
    results: List[RecognizerResult]
) -> Tuple[List[Owner], List[Assignment]]:
    """
    this assigns non-person entities to person 'owners' using simple heuristics:
    1) this has same line proximity
    2) and email local-part contains person name tokens
    3) and the nearest person by char distance
    and returns (owners, assignments).
    """

    # this collects person owners
    owners: List[Owner] = []
    for idx, r in enumerate([x for x in results if x.entity_type == "PERSON"]):
        owners.append(
            Owner(
                id=len(owners) + 1,
                span=(r.start, r.end),
                name=text[r.start : r.end],
            )
        )

    # this precomputes the line ranges
    lines = _splitLinesWithSpan(text)

    # this precomputes person tokens
    personTokens: Dict[int, List[str]] = {
        o.id: _extractPersonTokens(o.name) for o in owners
    }

    assignments: List[Assignment] = []

    for r in results:
        if r.entity_type == "PERSON":
            assignments.append(Assignment(result=r, ownerId=None))
            continue

        ownerId: Optional[int] = None

        # 1) this is the same line proximity
        for ls, lc, _ in lines:
            if r.start >= ls and r.end <= lc:
                # this finds any person whose span is inside the same line
                sameLine = [
                    o for o in owners if o.span[0] >= ls and o.span[1] <= lc
                ]
                if sameLine:
                    # if there multiple persons on the line, pick nearest by distance
                    ownerId = min(
                        sameLine,
                        key=lambda o: abs(o.span[0] - r.start),
                    ).id
                break

        # 2) this is the email username contains person tokens
        if ownerId is None and r.entity_type == "EMAIL_ADDRESS":
            value = text[r.start : r.end]
            if "@" in value:
                localPart = value.split("@", 1)[0]
                for o in owners:
                    if _containsToken(localPart, personTokens[o.id]):
                        ownerId = o.id
                        break

        # 3) this is the nearest person by char distance (fall-back)
        if ownerId is None:
            ownerId = _nearestPersonByDistance(owners, r.start)

        assignments.append(Assignment(result=r, ownerId=ownerId))

    return owners, assignments


def maskWithRelationships(
    text: str,
    results: List[RecognizerResult]
) -> str:
    """
    this builds a replacement plan with relationship-aware placeholders and
    apply it to the original text. we do not use the anonymizer engine here,
    because we need per-entity-instance placeholders, not per-type.
    """

    owners, assignments = assignRelationships(text, results)

    # this builds labels per owner
    personLabels: Dict[int, str] = {
        o.id: f"PERSON_{o.id}" for o in owners
    }

    # this replaces per entity instance
    replSpans: List[Tuple[int, int, str]] = []

    for a in assignments:
        r = a.result
        ct = r.entity_type
        original = text[r.start : r.end]

        # this is the person itself
        if ct == "PERSON":
            # if this person is also in owners, replace with the label
            # find owner id whose span equals r
            ownerId = None
            for o in owners:
                if o.span == (r.start, r.end):
                    ownerId = o.id
                    break
            replacement = personLabels.get(ownerId, "<PERSON>")
            replSpans.append((r.start, r.end, replacement))
            continue

        # non-person: derive placeholder using owner relationship
        if a.ownerId is not None:
            base = ct
            replacement = f"<{base}_PERSON_{a.ownerId}>"
        else:
            replacement = f"<{ct}>"

        # this is the minor format-aware tweaks:
        if ct == "PHONE_NUMBER":
            # mask all digits but keep formatting length
            digits = re.sub(r"\D", "", original)
            masked = "*" * len(digits)
            # if formatting preservation is needed, just replace whole token
            replacement = replacement  # already relationship-aware placeholder

        # this pushes replacement
        replSpans.append((r.start, r.end, replacement))

    # this sorts by start descending to avoid index shifts while replacing
    replSpans.sort(key=lambda x: x[0], reverse=True)

    masked = text
    for s, e, rep in replSpans:
        masked = masked[:s] + rep + masked[e:]

    return masked
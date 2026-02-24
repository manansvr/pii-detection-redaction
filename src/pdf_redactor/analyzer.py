# src/pdf_redactor/analyzer.py

from __future__ import annotations

import re
from pathlib import Path
from typing import List, Tuple

from presidio_analyzer import (
    AnalyzerEngine,
    PatternRecognizer,
    Pattern,
    RecognizerResult,
)

from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTChar, LTTextLine

from pprint import pprint
from common import build_presidio_analyzer

from entity_mapping import build_au_recognizers, AbnRecognizer


def build_analyzer(language: str = "en") -> AnalyzerEngine:
    return build_presidio_analyzer(language)


def analyze_pdf_to_bboxes(
    pdf_path: Path,
    analyzer: AnalyzerEngine,
    language: str = "en",
    min_score: float = 0.0,
    entities: List[str] | None = None,
) -> List[List[Tuple[float, float, float, float, str]]]:
    per_page: List[List[Tuple[float, float, float, float, str]]] = []

    for page_layout in extract_pages(str(pdf_path)):
        page_bboxes: List[Tuple[float, float, float, float, str]] = []

        for element in page_layout:
            if not isinstance(element, LTTextContainer):
                continue

            text = element.get_text()
            if not text.strip():
                continue

            results = analyzer.analyze(text=text, language=language, entities=entities)

            for res in results:
                if res.score < min_score:
                    continue
                x0, y0, x1, y1 = element.bbox
                page_bboxes.append((x0, y0, x1, y1, res.entity_type))

        per_page.append(page_bboxes)

    return per_page


name_token_re = re.compile(
    r"""
    (?:
        [a-z][a-z]+(?:-[a-z][a-z]+)*
        |
        [a-z]\.
    )
    """,
    re.VERBOSE,
)

name_seq_re = re.compile(
    rf"{name_token_re.pattern}(?:\s+{name_token_re.pattern}){{0,3}}",
    re.VERBOSE,
)

title_name_re = re.compile(
    r"^(?P<title>Mr\.?|Mrs\.?|Ms\.?|Miss|Dr\.?|Professor|Prof\.?|Sir|Madam|Ma'am)\s+(?P<name>.+)$",
    re.IGNORECASE,
)

greeting_name_re = re.compile(
    r"^(?P<greet>Hello|Hi|Hey|Dear|Good\s+(?:morning|afternoon|evening))[\s,:\-]+(?P<name>.+)$",
    re.IGNORECASE,
)


def union_bbox(chars: List[LTChar]) -> Tuple[float, float, float, float]:
    x0 = min(ch.bbox[0] for ch in chars)
    y0 = min(ch.bbox[1] for ch in chars)
    x1 = max(ch.bbox[2] for ch in chars)
    y1 = max(ch.bbox[3] for ch in chars)
    return (x0, y0, x1, y1)


def _pad_rect(
    r: Tuple[float, float, float, float],
    pad: float = 1.5,
) -> Tuple[float, float, float, float]:
    x0, y0, x1, y1 = r
    return (x0 - pad, y0 - pad, x1 + pad, y1 + pad)


def normalize_person_name(s: str) -> str:
    s = s.strip()
    s = re.sub(r"\.(?=\b)", "", s)  # "A." -> "A"
    s = re.sub(r"\s+", " ", s)
    return s.lower()


def name_variants(name: str) -> List[str]:
    base = normalize_person_name(name)
    variants = {base}

    nodots = re.sub(r"\.", "", name)
    variants.add(normalize_person_name(nodots))

    if "," in name:
        parts = [p.strip() for p in name.split(",", 1)]
        if len(parts) == 2 and parts[0] and parts[1]:
            swapped = f"{parts[1]} {parts[0]}"
            variants.add(normalize_person_name(swapped))

    return list(variants)


def find_all_matches_ci(
    text: str,
    needle: str,
) -> List[Tuple[int, int]]:
    if not needle:
        return []

    pat = re.compile(rf"(?i)(?<!\w){re.escape(needle)}(?!\w)")
    return [m.span() for m in pat.finditer(text)]


def spans_overlap(a: Tuple[int, int], b: Tuple[int, int]) -> bool:
    return not (a[1] <= b[0] or b[1] <= a[0])

def analyzePDFToLayout(
    pdfPath: str,
    analyzer: "AnalyzerEngine",
    language: str = "en",
) -> list[tuple[float, float, float, float, str, float]]:
    page_layouts: list[list[float, float, float, float, str, float]] = []
    known_spans: set[str] = set()

    for page_layout in analyzer.get_layout(pdfPath):
        page_items: list[float, float, float, float, str, float] = []

        for element in page_layout:
            if not isinstance(element, LTTextContainer):
                continue

            chars: list[LTChar] = []
            for text_line in element:
                if isinstance(text_line, LTTextLine):
                    for ch in text_line:
                        if isinstance(ch, LTChar):
                            chars.append(ch)

            if not chars:
                continue

            container_text = "".join(ch.get_text() for ch in chars)
            if not container_text.strip():
                continue

            results = analyzer.analyze(
                text=container_text,
                language=language,
            )

            covered_spans: list[tuple[int, int]] = []

            for res in results:
                start, end = res.start, res.end
                if end <= start:
                    continue

                entity_type = res.entity_type
                score = res.score

                if entity_type in ("PERSON", "ORGANIZATION"):
                    prefix = container_text[:start].rstrip()
                    if prefix.endswith(":"):
                        colon_idx = prefix.rfind(":")
                        start = colon_idx + 1
                        while start < end and container_text[start].isspace():
                            start += 1

                while end > start and container_text[end - 1] in ".,;:":
                    end -= 1

                if end <= start:
                    continue

                key = f"{entity_type}:{container_text[start:end]}"
                if key in known_spans:
                    continue
                known_spans.add(key)

                span_chars = chars[start:end]
                x0 = min(ch.x0 for ch in span_chars)
                y0 = min(ch.y0 for ch in span_chars)
                x1 = max(ch.x1 for ch in span_chars)
                y1 = max(ch.y1 for ch in span_chars)

                page_items.append((x0, y0, x1, y1, entity_type, score))
                covered_spans.append((start, end))

            if not covered_spans:
                continue

        page_layouts.append(page_items)

    return page_layouts


from spacy.matcher import Matcher
from spacy.language import Language


def build_common_title_recognizer() -> Matcher:
    matcher = Matcher(None)

    matcher.add(
        "COMMON_TITLE",
        [
            [
                {"LOWER": {"IN": [
                    "Mr", "mr.", "Mrs", "mrs.", "Ms", "ms.",
                    "Mx", "mx.", "Miss",
                    "Sir",
                    "Dr", "dr.",
                    "Professor", "prof."
                ]}}
            ],
            [
                {"LOWER": {"IN": [
                    "applicant", "candidate", "customer", "patient",
                    "client", "employee", "student", "recipient", "borrower"
                ]}}
            ],
        ],
    )

    return matcher


def build_person_with_title_recognizer() -> Matcher:
    title_pattern = [
        {
            "LOWER": {
                "IN": [
                    "Mr", "mr.", "Mrs", "mrs.", "Ms", "ms.",
                    "Dr", "dr.", "Prof", "prof.", "Professor",
                    "Sir", "Madam", "Miss"
                ]
            }
        }
    ]

    given_name = {"IS_TITLE": True, "OP": "+"}
    initials = {"TEXT": {"REGEX": r"([A-Z]\.)+"}}
    surname = {"IS_TITLE": True}

    pattern = [
        {"OP": "*", **title_pattern[0]},
        {"OP": "+", "OR": [given_name, initials]},
        surname,
    ]

    matcher = Matcher(None)
    matcher.add(
        "PERSON_WITH_TITLE",
        [pattern],
    )

    return matcher


def build_person_after_greeting_recognizer() -> Matcher:
    greeting = {
        "LOWER": {
            "IN": [
                "Hello", "Hi", "Dear",
                "Good Morning", "Good Afternoon", "Good Evening"
            ]
        }
    }

    name_tokens = [
        {"IS_TITLE": True},
        {"IS_TITLE": True, "OP": "*"},
    ]

    pattern = [
        greeting,
        {"IS_PUNCT": True, "OP": "?"},
        *name_tokens,
    ]

    matcher = Matcher(None)
    matcher.add(
        "PERSON_AFTER_GREETING",
        [pattern],
    )

    return matcher


@Language.component("build_analyzers")
def build_analyzers(nlp: Language, name: str = "ner"):
    matcher = Matcher(nlp.vocab)

    for m in build_common_title_recognizer():
        matcher.add(*m)

    for m in build_person_with_title_recognizer():
        matcher.add(*m)

    for m in build_person_after_greeting_recognizer():
        matcher.add(*m)

    return matcher
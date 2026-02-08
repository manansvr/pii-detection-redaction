# src/pdfredactor/analyzer.py

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
from common import buildPresidioAnalyzer


def buildAnalyzer(language: str = "en") -> AnalyzerEngine:
    """
    builds a presidio analyzer engine for pdf processing.
    uses shared utility to avoid code duplication.
    """
    return buildPresidioAnalyzer(language)


def analyzePdfToBboxes(
    pdfPath: Path,
    analyzer: AnalyzerEngine,
    language: str = "en",
) -> List[List[Tuple[float, float, float, float, str]]]:
    """
    analyzes pdf and returns bounding boxes for each page.
    returns list of pages, where each page is a list of (x0, y0, x1, y1, entitytype) tuples.
    """
    perPage: List[List[Tuple[float, float, float, float, str]]] = []

    for pageLayout in extract_pages(str(pdfPath)):
        pageBboxes: List[Tuple[float, float, float, float, str]] = []

        for element in pageLayout:
            if not isinstance(element, LTTextContainer):
                continue

            text = element.get_text()
            if not text.strip():
                continue

            results = analyzer.analyze(text=text, language=language)

            for res in results:
                # use element bbox as approximation
                x0, y0, x1, y1 = element.bbox
                pageBboxes.append((x0, y0, x1, y1, res.entity_type))

        perPage.append(pageBboxes)

    return perPage


# this matches name tokens like "john", "ana-maria", or initials "a."
nameTokenRe = re.compile(
    r"""
    (?:
        [a-z][a-z]+(?:-[a-z][a-z]+)*   # capitalized word (with optional hyphens)
        |
        [a-z]\.                        # initial like "a."
    )
    """,
    re.VERBOSE,
)

# this allows 1-4 tokens (first [middle/initial] last [suffix-like token])
nameSeqRe = re.compile(
    rf"{nameTokenRe.pattern}(?:\s+{nameTokenRe.pattern}){{0,3}}",
    re.VERBOSE,
)

# this trims "title + name" to just the name part
titleNameRe = re.compile(
    r"^(?P<title>Mr\.?|Mrs\.?|Ms\.?|Miss|Dr\.?|Professor|Prof\.?|Sir|Madam|Ma'am)\s+(?P<name>.+)$",
    re.IGNORECASE,
)

# this trims "greeting + name" to just the name part
greetingNameRe = re.compile(
    r"^(?P<greet>Hello|Hi|Hey|Dear|Good\s+(?:morning|afternoon|evening))[\s,:\-]+(?P<name>.+)$",
    re.IGNORECASE,
)


def _union_bbox(chars: List[LTChar]) -> Tuple[float, float, float, float]:
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


def _normalize_person_name(s: str) -> str:
    """
    this normalizes a person name for dictionary matching:
    - strip
    - remove trailing dots on initials
    - collapse multiple spaces
    - lowercase
    """
    s = s.strip()
    s = re.sub(r"\.(?=\b)", "", s)  # "A." -> "A"
    s = re.sub(r"\s+", " ", s)
    return s.lower()


def _name_variants(name: str) -> List[str]:
    """
    this generates a few simple variants to improve repeat matching:
    - as-is normalized
    - remove dots from initials
    - optional 'last, first' <-> 'first last' swap if comma present
    """
    base = _normalize_person_name(name)
    variants = {base}

    nodots = re.sub(r"\.", "", name)
    variants.add(_normalize_person_name(nodots))

    if "," in name:
        parts = [p.strip() for p in name.split(",", 1)]
        if len(parts) == 2 and parts[0] and parts[1]:
            swapped = f"{parts[1]} {parts[0]}"
            variants.add(_normalize_person_name(swapped))

    return list(variants)


def _find_all_matches_ci(
    text: str,
    needle: str,
) -> List[Tuple[int, int]]:
    """
    this finds all case-insensitive, word-boundary matches for 'needle' in 'text'.
    we treat boundaries around the whole string; inner spaces are literal.
    """
    if not needle:
        return []

    pat = re.compile(rf"(?i)(?<!\w){re.escape(needle)}(?!\w)")
    return [m.span() for m in pat.finditer(text)]


def _spans_overlap(a: Tuple[int, int], b: Tuple[int, int]) -> bool:
    return not (a[1] <= b[0] or b[1] <= a[0])

def analyzePdfToLayout(
    pdfPath: str,
    analyzer: "AnalyzerEngine",
    language: str = "en",
) -> list[tuple[float, float, float, float, str, float]]:
    """
    this is a post-processing step: returns a list of normalized entity spans:
        (x0, y0, x1, y1, entity_type, score)

    the strategy used:
    - iterate through each page’s layout
    - group letters into words and word containers
    - run precision matching per text container
    - map matched spans back to pdf letter coordinates
    """

    page_layouts: list[list[float, float, float, float, str, float]] = []
    known_spans: set[str] = set()

    for page_layout in analyzer.get_layout(pdf_path):
        page_items: list[float, float, float, float, str, float] = []

        for element in page_layout:
            if not isinstance(element, LTTextContainer):
                continue

            # collect characters in order
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

            # run analyzer on the full container text
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

                # special handling: strip prefixes like "name:", "title:", etc.
                if entity_type in ("PERSON", "ORGANIZATION"):
                    prefix = container_text[:start].rstrip()
                    if prefix.endswith(":"):
                        colon_idx = prefix.rfind(":")
                        start = colon_idx + 1
                        while start < end and container_text[start].isspace():
                            start += 1

                # trim trailing punctuation
                while end > start and container_text[end - 1] in ".,;:":
                    end -= 1

                if end <= start:
                    continue

                # avoid duplicates
                key = f"{entity_type}:{container_text[start:end]}"
                if key in known_spans:
                    continue
                known_spans.add(key)

                # map character span back to bounding box
                span_chars = chars[start:end]
                x0 = min(ch.x0 for ch in span_chars)
                y0 = min(ch.y0 for ch in span_chars)
                x1 = max(ch.x1 for ch in span_chars)
                y1 = max(ch.y1 for ch in span_chars)

                page_items.append((x0, y0, x1, y1, entity_type, score))
                covered_spans.append((start, end))

            # optional: handle unmatched text chunks
            if not covered_spans:
                continue

        page_layouts.append(page_items)

    return page_layouts

class ABNRecognizer(PatternRecognizer):
    """
    detects australian business numbers (abn) with checksum validation.

    abn format:
    - 11 digits (may contain spaces)
    - checksum: subtract 1 from first digit,
      multiply digits by weights and mod 89
    """

    ABN_WEIGHTS = [10, 1, 3, 5, 7, 9, 11, 13, 15, 17, 19]

    def __init__(self):
        patterns = [
            Pattern(
                name="abn",
                regex=r"\b(?:\d[ ]?){11}\b",
                score=0.5,
            )
        ]

        super().__init__(
            supported_entity="AU_ABN",
            patterns=patterns,
            context=["abn", "australian business number"],
        )

    @staticmethod
    def isValidAbn(text: str) -> bool:
        digits = [int(c) for c in text if c.isdigit()]
        if len(digits) != 11:
            return False

        digits[0] -= 1
        total = sum(d * w for d, w in zip(digits, ABNRecognizer.ABN_WEIGHTS))
        return total % 89 == 0

    def validateResult(self, patternText: str) -> bool:
        digitsOnly = "".join(c for c in patternText if c.isdigit())
        return self.isValidAbn(digitsOnly)

def buildAuRecognizers() -> list[PatternRecognizer]:
    recognizers: list[PatternRecognizer] = []

    # abn
    recognizers.append(ABNRecognizer())

    # australian bank account numbers
    bank_patterns = [
        Pattern(
            name="bank_account",
            regex=r"\b\d{6}[- ]?\d{6,10}\b",
            score=0.45,
        )
    ]

    recognizers.append(
        PatternRecognizer(
            supported_entity="AU_BANK_ACCOUNT",
            patterns=bank_patterns,
            context=[
                "Bank Account",
                "Account Number",
                "BSB",
            ],
        )
    )

    # australian states / territories
    recognizers.append(
        PatternRecognizer(
            supported_entity="AU_STATE",
            deny_list=[
                "NSW",
                "VIC",
                "QLD",
                "SA",
                "WA",
                "TAS",
                "ACT",
                "NT",
                "New South Wales",
                "Victoria",
                "Queensland",
                "South Australia",
                "Western Australia",
                "Tasmania",
                "Australian Capital Territory",
                "Northern Territory",
            ],
        )
    )

    # australian postcodes
    postcode_patterns = [
        Pattern(
            name="postcode",
            regex=r"\b\d{4}\b",
            score=0.4,
        )
    ]

    recognizers.append(
        PatternRecognizer(
            supported_entity="AU_POSTCODE",
            patterns=postcode_patterns,
            context=[
                "Postcode",
                "Postal Code",
                "Post Code",
                "Delivery Address",
                "Suburb",
            ],
        )
    )

    return recognizers

from spacy.matcher import Matcher
from spacy.language import Language


def buildCommonTitleRecognizer() -> Matcher:
    """
    this recognizes common english name titles.
    implemented as a deny-list for precision.
    """
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


def buildPersonWithTitleRecognizer() -> Matcher:
    """
    this recognizes sequences like:
    - mr. john smith
    - dr jane doe
    - prof. r. feynman
    - sir isaac newton
    - madam curie
    - miss alice

    this handles cases with:
    - optional one or more titles
    - multiple given names
    - initials with trailing dots
    - hyphenated surnames
    """

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


def buildPersonAfterGreetingRecognizer() -> Matcher:
    """
    this recognizes names that follow a greeting, e.g.:
    - hello john
    - hi jane doe
    - dear dr smith
    - good morning, ms jones

    this function will trim the span to only the name portion during post-processing.
    """

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
def buildAnalyzers(nlp: Language, name: str = "ner"):
    """
    this builds the pipeline analyzer module and registers
    all specific custom entities.

    requires a installed spacy english model.
    """
    matcher = Matcher(nlp.vocab)

    # common titles
    for m in build_common_title_recognizer():
        matcher.add(*m)

    # title + person recognizers
    for m in build_person_with_title_recognizer():
        matcher.add(*m)

    # greeting + person recognizers
    for m in build_person_after_greeting_recognizer():
        matcher.add(*m)

    return matcher
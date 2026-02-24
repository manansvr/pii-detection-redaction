# src/common/common.py

from __future__ import annotations

import spacy
from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import SpacyNlpEngine

from entity_mapping import build_au_recognizers


def pick_spacy_model(
    preferred: str = "en_core_web_lg",
    fallback: str = "en_core_web_sm",
) -> str:
    for model_name in (preferred, fallback):
        try:
            spacy.load(model_name)
            return model_name
        except Exception:
            continue

    raise RuntimeError(
        f"No spaCy English Model Installed. Run:\n"
        f"  python -m spacy download {preferred}\n"
        f"or:\n"
        f"  python -m spacy download {fallback}"
    )


def build_presidio_analyzer(
    language: str = "en",
    include_au_recognizers: bool = True
) -> AnalyzerEngine:
    model_name = pick_spacy_model()

    nlp_engine = SpacyNlpEngine(
        models=[{"lang_code": language, "model_name": model_name}]
    )

    analyzer = AnalyzerEngine(
        nlp_engine=nlp_engine,
        supported_languages=[language],
    )

    if include_au_recognizers:
        au_recognizers = build_au_recognizers()
        for recognizer in au_recognizers:
            analyzer.registry.add_recognizer(recognizer)

    return analyzer
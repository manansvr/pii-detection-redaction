# src/common/common.py

"""
common utilities for building presidio analyzer engines with spacy models.
shared across text detector, pdf redactor, and image redactor modules.
"""

from __future__ import annotations

import spacy
from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import SpacyNlpEngine


def pickSpacyModel(
    preferred: str = "en_core_web_lg",
    fallback: str = "en_core_web_sm",
) -> str:
    """
    returns a spacy model package name which is installed & loadable.
    prefers `preferred`; falls back to `fallback` if needed.
    raises if neither is available (prompts user to install).

    args:
        preferred: preferred model name (default: en_core_web_lg)
        fallback: fallback model name (default: en_core_web_sm)

    returns:
        name of the available model

    raises:
        run time error: if neither model is available
    """
    for modelName in (preferred, fallback):
        try:
            spacy.load(modelName)
            return modelName
        except Exception:
            continue

    raise RuntimeError(
        f"No spaCy English Model Installed. Run:\n"
        f"  python -m spacy download {preferred}\n"
        f"or:\n"
        f"  python -m spacy download {fallback}"
    )


def buildPresidioAnalyzer(language: str = "en") -> AnalyzerEngine:
    """
    builds a presidio analyzer engine using spacy via spacy nlp engine.
    fixes the common 'lang_code is missing' error by passing the correct
    models structure.

    args:
        language: language code (default: "en")

    returns:
        configured analyzer engine instance
    """
    modelName = pickSpacyModel()

    # models must be a list of dicts with lang_code & model_name
    nlpEngine = SpacyNlpEngine(
        models=[{"lang_code": language, "model_name": modelName}]
    )

    analyzer = AnalyzerEngine(
        nlp_engine=nlpEngine,
        supported_languages=[language],
    )

    return analyzer
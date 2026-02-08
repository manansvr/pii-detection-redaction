# src/textdetector/cli.py

from __future__ import annotations

import sys
import json
import argparse
from pathlib import Path

from .analyzer import buildAnalyzer
from .chunker import analyzeLongText
from .formatter import resultsToJson
from .anonymize import anonymizeText
from .relationships import maskWithRelationships


def parseArgs():
    p = argparse.ArgumentParser(
        description="PII Detection On Long Strings Using Microsoft Presidio"
    )

    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--text", type=str, help="Raw Text To Analyze")
    group.add_argument(
        "--in",
        dest="infile",
        type=str,
        help="Path To A Text File To Analyze",
    )

    p.add_argument(
        "--lang",
        type=str,
        default="en",
        help="Language Code (Default: en)",
    )

    p.add_argument(
        "--size",
        type=int,
        default=5000,
        help="Chunk Size In Characters (Default: 5000)",
    )

    p.add_argument(
        "--overlap",
        type=int,
        default=300,
        help="Overlap Between Chunks (Default: 300)",
    )

    p.add_argument(
        "--min-score",
        type=float,
        default=0.0,
        help="Minimum Confidence Score (Default: 0.0)",
    )

    p.add_argument(
        "--anonymize",
        action="store_true",
        help="Also Emit Redacted Text To Stderr",
    )

    p.add_argument(
        "--mask-to-file",
        type=str,
        default=None,
        help="Relationship-Aware Masking: Write To This File",
    )

    p.add_argument(
        "--print-text",
        action="store_true",
        help="Echo Input Length & Preview",
    )

    return p.parse_args()


def readInputText(args) -> str:
    if args.text is not None:
        return args.text

    infile = Path(args.infile)
    if infile.exists():
        return infile.read_text(encoding="utf-8")

    # this tries relative to project root (one level up from src/)
    projectRoot = Path(__file__).resolve().parents[2]
    candidate = projectRoot / args.infile
    if candidate.exists():
        return candidate.read_text(encoding="utf-8")

    samplesCandidate = projectRoot / "samples" / infile.name
    if samplesCandidate.exists():
        return samplesCandidate.read_text(encoding="utf-8")

    raise FileNotFoundError(
        f"Cannot Find Input File At '{infile}' or '{candidate}' or '{samplesCandidate}'"
    )


def main():
    args = parseArgs()
    text = readInputText(args)

    if args.print_text:
        preview = text[:200].replace("\n", " ")
        print(
            f"# Input Chars: {len(text)} | Preview: {preview}...\n",
            file=sys.stderr,
        )

    analyzer = buildAnalyzer(language=args.lang)
    results = analyzeLongText(
        analyzer=analyzer,
        text=text,
        language=args.lang,
        size=args.size,
        overlap=args.overlap,
        minScore=args.min_score,
    )

    # this is a json file (detected entities) to stdout
    print(
        json.dumps(
            resultsToJson(results, text),
            ensure_ascii=False,
            indent=2,
        )
    )

    # this is optional type-only anonymizer (per entity type)
    if args.anonymize:
        redacted = anonymizeText(text, results)
        print("\n# Anonymized text (type-only):\n", file=sys.stderr)
        print(redacted, file=sys.stderr)

    # this is relationship-aware masking -> write to file
    if args.mask_to_file:
        masked = maskWithRelationships(text, results)
        outPath = Path(args.mask_to_file)

        # this resolves relative to current working directory
        outPath.write_text(masked, encoding="utf-8")
        print(
            f"\n# Saved relationship-masked text -> {outPath.resolve()}",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
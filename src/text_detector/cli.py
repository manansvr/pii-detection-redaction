# src/text_detector/cli.py

from __future__ import annotations

import sys
import json
import argparse
from pathlib import Path

from .analyzer import build_analyzer
from .chunker import analyze_long_text
from .formatter import results_to_json
from .anonymize import anonymize_text
from .relationships import mask_with_relationships


def parse_args():
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
        help="Language Code",
    )

    p.add_argument(
        "--size",
        type=int,
        default=5000,
        help="Chunk Size In Characters",
    )

    p.add_argument(
        "--overlap",
        type=int,
        default=300,
        help="Overlap Between Chunks In Characters",
    )

    p.add_argument(
        "--min-score",
        type=float,
        default=0.0,
        help="Minimum Confidence Score For Detected Entities",
    )

    p.add_argument(
        "--entities",
        nargs="+",
        default=None,
        help="Specific Entity Types To Detect (e.g., AU_TFN AU_MEDICARE). If Not Specified, All Entity Types Are Detected.",
    )

    p.add_argument(
        "--anonymize",
        action="store_true",
        help="Also Emit Redacted Text To stderr",
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


def read_input_text(args) -> str:
    if args.text is not None:
        return args.text

    infile = Path(args.infile)
    if infile.exists():
        return infile.read_text(encoding="utf-8")

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
    args = parse_args()
    text = read_input_text(args)

    if args.print_text:
        preview = text[:200].replace("\n", " ")
        print(
            f"# Input Chars: {len(text)} | Preview: {preview}...\n",
            file=sys.stderr,
        )

    analyzer = build_analyzer(language=args.lang)
    results = analyze_long_text(
        analyzer=analyzer,
        text=text,
        language=args.lang,
        size=args.size,
        overlap=args.overlap,
        min_score=args.min_score,
        entities=args.entities,
    )

    print(
        json.dumps(
            results_to_json(results, text),
            ensure_ascii=False,
            indent=2,
        )
    )

    if args.anonymize:
        redacted = anonymize_text(text, results)
        print("\n# Anonymized text (type-only):\n", file=sys.stderr)
        print(redacted, file=sys.stderr)

    if args.mask_to_file:
        masked = mask_with_relationships(text, results)
        outPath = Path(args.mask_to_file)

        outPath.write_text(masked, encoding="utf-8")
        print(
            f"\n# Saved relationship-masked text -> {outPath.resolve()}",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
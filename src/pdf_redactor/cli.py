# src/pdf_redactor/cli.py

from __future__ import annotations

import argparse
from pathlib import Path

from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

from .analyzer import build_analyzer, analyze_pdf_to_bboxes
from .redactor import write_redacted_pdf


def parse_args():
    p = argparse.ArgumentParser(
        description="Analyze + Visually Redact A PDF Using Presidio + pdfminer.six + pikepdf"
    )

    p.add_argument(
        "--in",
        dest="infile",
        required=True,
        help="Path To Input PDF",
    )

    p.add_argument(
        "--out",
        dest="outfile",
        default=None,
        help="Path To Output PDF",
    )

    p.add_argument(
        "--lang",
        default="en",
        help="Language Code",
    )

    p.add_argument(
        "--no-labels",
        action="store_true",
        help="Do Not Draw White Labels On Top Of Black Boxes",
    )

    p.add_argument(
        "--label-prefix",
        default="",
        help="Optional Prefix For Labels",
    )

    p.add_argument(
        "--attach-original",
        action="store_true",
        help="Attach Original PDF To The Output For Reference",
    )

    p.add_argument(
        "--min-score",
        type=float,
        default=0.0,
        help="Minimum Confidence Score For Detected Entities (default: 0.0)",
    )

    p.add_argument(
        "--entities",
        nargs="+",
        default=None,
        help="Specific Entity Types To Detect (e.g., AU_TFN AU_MEDICARE). If Not Specified, All Entity Types Are Detected.",
    )

    return p.parse_args()


def main():
    args = parse_args()

    src = Path(args.infile).resolve()
    if not src.exists():
        raise FileNotFoundError(src)

    dst = (
        Path(args.outfile).resolve()
        if args.outfile
        else src.with_name(src.stem + "_redacted.pdf")
    )

    analyzer: AnalyzerEngine = build_analyzer(language=args.lang)

    print(f"[1/3] Analyzing PII + Collecting B-Boxes From: {src}")
    per_page = analyze_pdf_to_bboxes(
        src,
        analyzer,
        language=args.lang,
        min_score=args.min_score,
        entities=args.entities,
    )

    total = sum(len(p) for p in per_page)
    print(f"[2/3] Found {total} PII Spans Across {len(per_page)} pages")

    print(f"[3/3] Writing Redacted PDF To: {dst}")
    write_redacted_pdf(
        src_pdf=src,
        dst_pdf=dst,
        per_page_bboxes=per_page,
        draw_labels=(not args.no_labels),
        label_prefix=args.label_prefix,
        attach_original=args.attach_original,
    )

    print("Completed.")


if __name__ == "__main__":
    main()
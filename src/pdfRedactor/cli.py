# src/pdfredactor/cli.py

from __future__ import annotations

import argparse
from pathlib import Path

from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

from .analyzer import buildAnalyzer, analyzePdfToBboxes
from .redactor import writeRedactedPdf


def parseArgs():
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
        help="Path To Output PDF (default: <in>_redacted.pdf)",
    )

    p.add_argument(
        "--lang",
        default="en",
        help="Language Code (Default: en)",
    )

    p.add_argument(
        "--no-labels",
        action="store_true",
        help="Do Not Draw White Labels On Top Of Black Boxes",
    )

    p.add_argument(
        "--label-prefix",
        default="",
        help="Optional Prefix For Labels (e.g. 'PII: ')",
    )

    p.add_argument(
        "--attach-original",
        action="store_true",
        help="Attach Original PDF To The Output",
    )

    return p.parse_args()


def main():
    args = parseArgs()

    src = Path(args.infile).resolve()
    if not src.exists():
        raise FileNotFoundError(src)

    dst = (
        Path(args.outfile).resolve()
        if args.outfile
        else src.with_name(src.stem + "_redacted.pdf")
    )

    analyzer: AnalyzerEngine = buildAnalyzer(language=args.lang)

    print(f"[1/3] Analyzing PII + Collecting B-Boxes From: {src}")
    perPage = analyzePdfToBboxes(src, analyzer, language=args.lang)

    total = sum(len(p) for p in perPage)
    print(f"[2/3] Found {total} PII Spans Across {len(perPage)} pages")

    print(f"[3/3] Writing Redacted PDF To: {dst}")
    writeRedactedPdf(
        srcPdf=src,
        dstPdf=dst,
        perPageBboxes=perPage,
        drawLabels=(not args.no_labels),
        labelPrefix=args.label_prefix,
        attachOriginal=args.attach_original,
    )

    print("Completed.")


if __name__ == "__main__":
    main()
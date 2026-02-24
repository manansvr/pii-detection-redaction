# src/csv_redactor/cli.py

from __future__ import annotations

import sys
import json
import argparse
from pathlib import Path

from .analyzer import build_analyzer
from .redactor import analyze_csv_file, redact_csv_file
from .formatter import results_to_json, summarize_detections


def parse_args():
    p = argparse.ArgumentParser(
        description="PII/SPI Detection and Redaction for CSV Files Using Microsoft Presidio"
    )

    p.add_argument(
        "--in",
        dest="infile",
        type=str,
        required=True,
        help="Path To Input CSV File",
    )

    p.add_argument(
        "--out",
        dest="outfile",
        type=str,
        help="Path To Output Redacted CSV File",
    )

    p.add_argument(
        "--lang",
        type=str,
        default="en",
        help="Language Code (default: en)",
    )

    p.add_argument(
        "--min-score",
        type=float,
        default=0.0,
        help="Minimum Confidence Score For Detected Entities (default: 0.0)",
    )

    p.add_argument(
        "--delimiter",
        type=str,
        default=",",
        help="CSV Delimiter Character (default: ,)",
    )

    p.add_argument(
        "--no-skip-header",
        dest="skip_header",
        action="store_false",
        default=True,
        help="Process First Row As Data Instead Of Header (default: False)",
    )

    p.add_argument(
        "--redaction-char",
        type=str,
        default="*",
        help="Character To Use For Redaction (default: *)",
    )

    p.add_argument(
        "--use-labels",
        action="store_true",
        help="Replace PII With Entity Type Labels Like <PERSON>, <EMAIL> Instead Of Redaction Chars",
    )

    p.add_argument(
        "--json-output",
        type=str,
        help="Save Detection Results To JSON File",
    )

    p.add_argument(
        "--summary",
        action="store_true",
        help="Print Summary Of Detections",
    )

    p.add_argument(
        "--entities",
        nargs="+",
        default=None,
        help="Specific Entity Types To Detect (e.g., AU_TFN AU_MEDICARE). If Not Specified, All Entity Types Are Detected.",
    )

    return p.parse_args()


def find_input_file(file_path: str) -> Path:
    infile = Path(file_path)

    if infile.exists():
        return infile

    project_root = Path(__file__).resolve().parents[2]
    candidate = project_root / file_path
    if candidate.exists():
        return candidate

    samples_candidate = project_root / "samples" / infile.name
    if samples_candidate.exists():
        return samples_candidate

    raise FileNotFoundError(
        f"Cannot Find Input File At '{infile}' or '{candidate}' or '{samples_candidate}'"
    )


def main():
    args = parse_args()

    try:
        input_path = find_input_file(args.infile)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"# Analyzing CSV: {input_path}", file=sys.stderr)

    analyzer = build_analyzer(language=args.lang)

    if args.outfile:
        output_path = Path(args.outfile)

        detections, redacted_count = redact_csv_file(
            analyzer=analyzer,
            input_path=input_path,
            output_path=output_path,
            language=args.lang,
            min_score=args.min_score,
            skip_header=args.skip_header,
            delimiter=args.delimiter,
            redaction_char=args.redaction_char,
            use_entity_labels=args.use_labels,
            entities=args.entities,
        )

        print(f"# Redacted {redacted_count} cells", file=sys.stderr)
        print(f"# Saved Redacted CSV to: {output_path.resolve()}", file=sys.stderr)
    else:
        rows, detections = analyze_csv_file(
            analyzer=analyzer,
            file_path=input_path,
            language=args.lang,
            min_score=args.min_score,
            skip_header=args.skip_header,
            delimiter=args.delimiter,
            entities=args.entities,
        )

        print(f"# Found {len(detections)} PII/SPI detections", file=sys.stderr)

    formatted_results = results_to_json(detections)
    print(
        json.dumps(
            formatted_results,
            ensure_ascii=False,
            indent=2,
        )
    )

    if args.json_output:
        json_path = Path(args.json_output)
        json_path.write_text(
            json.dumps(formatted_results, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"\n# Saved Detection Results To: {json_path.resolve()}", file=sys.stderr)

    if args.summary:
        summary = summarize_detections(detections)
        print("\n# Summary:", file=sys.stderr)
        print(f"#   Total Detections: {summary['total_detections']}", file=sys.stderr)
        print(f"#   Affected Cells: {summary['affected_cells']}", file=sys.stderr)
        print("#   By Entity Type:", file=sys.stderr)

        for entity_type, count in summary["by_entity_type"].items():
            print(f"#     {entity_type}: {count}", file=sys.stderr)


if __name__ == "__main__":
    main()

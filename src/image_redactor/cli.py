# src/image_redactor/cli.py

from __future__ import annotations

import argparse
from pathlib import Path

from .redactor import ImageRedactor, RedactionStyle


def parse_args():
    ap = argparse.ArgumentParser(
        description="Redact PII From Images Using Presidio & OCR"
    )

    ap.add_argument(
        "--in",
        dest="input_path",
        type=str,
        required=True,
        help="Input Image Path"
    )

    ap.add_argument(
        "--out",
        dest="output_path",
        type=str,
        required=True,
        help="Output Image Path"
    )

    ap.add_argument(
        "--entities",
        nargs="*",
        default=None,
        help="Entity Types To Redact"
    )

    ap.add_argument(
        "--lang",
        type=str,
        default="eng",
        help="OCR Languages"
    )

    ap.add_argument(
        "--mode",
        type=str,
        choices=["fill", "blur", "pixelate", "rectangle"],
        default="fill",
        help="Redaction Mode"
    )

    ap.add_argument(
        "--fill",
        type=str,
        default="#000000",
        help="Fill Color For Fill/Rectangle Mode (HEX)"
    )

    ap.add_argument(
        "--padding",
        type=int,
        default=2,
        help="Padding Around Redaction Boxes"
    )

    ap.add_argument(
        "--blur-radius",
        type=int,
        default=8,
        help="Blur Radius For Blur Mode"
    )

    ap.add_argument(
        "--pixel-size",
        type=int,
        default=12,
        help="Pixel Size For Pixelate Mode"
    )

    ap.add_argument(
        "--labels",
        action="store_true",
        help="Draw Entity Labels On Redacted Regions"
    )

    ap.add_argument(
        "--min-score",
        type=float,
        default=0.0,
        help="Minimum Confidence Score"
    )

    return ap.parse_args()


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


def main():
    args = parse_args()

    input_path = Path(args.input_path)
    if not input_path.exists():
        print(f"Error: Input File Not Found: {args.input_path}")
        return 1

    output_path = Path(args.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    redactor = ImageRedactor(ocr_languages=args.lang)

    style = RedactionStyle(
        mode=args.mode,
        fill_color=hex_to_rgb(args.fill),
        blur_radius=args.blur_radius,
        pixel_size=args.pixel_size,
        padding=args.padding,
    )

    print(f"Processing: {input_path}")
    print(f"OCR Language: {args.lang}")
    print(f"Redaction Mode: {args.mode}")

    result = redactor.redact_file(
        input_path=str(input_path),
        output_path=str(output_path),
        entities=args.entities,
        style=style,
        draw_labels=args.labels,
        score_threshold=args.min_score,
    )

    print(f"\n✓ Redacted Image Saved To: {result.output_path}")
    print(f"✓ Detected {len(result.boxes)} PII Entities:")

    for box in result.boxes:
        print(f"  • {box.entity_type:20s} @ ({box.left:4d}, {box.top:4d})")

    return 0


if __name__ == "__main__":
    exit(main())
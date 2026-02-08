# src/imageredactor/cli.py

from __future__ import annotations

import argparse
from pathlib import Path

from .redactor import ImageRedactor, RedactionStyle


def parseArgs():
    """
    parses command-line arguments for image pii redaction.
    """
    ap = argparse.ArgumentParser(
        description="Redact PII From Images Using Presidio & OCR"
    )

    ap.add_argument(
        "--in",
        dest="inputPath",
        type=str,
        required=True,
        help="Input Image Path"
    )

    ap.add_argument(
        "--out",
        dest="outputPath",
        type=str,
        required=True,
        help="Output Image Path"
    )

    ap.add_argument(
        "--entities",
        nargs="*",
        default=None,
        help="Entity Types To Redact (default: all)"
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
        help="Minimum Confidence Score (Default: 0.0)"
    )

    return ap.parse_args()


def hexToRgb(hexColor: str) -> tuple[int, int, int]:
    """
    converts hex color string to rgb tuple.

    args:
        hex color: hex color string (e.g., "#ff0000" or "ff0000")

    returns:
        rgb tuple (r, g, b)
    """
    hexColor = hexColor.lstrip("#")
    return tuple(int(hexColor[i:i + 2], 16) for i in (0, 2, 4))


def main():
    """
    main entry point for image redaction cli.
    """
    args = parseArgs()

    # validate input file exists
    inputPath = Path(args.inputPath)
    if not inputPath.exists():
        print(f"Error: Input File Not Found: {args.inputPath}")
        return 1

    # create output directory if needed
    outputPath = Path(args.outputPath)
    outputPath.parent.mkdir(parents=True, exist_ok=True)

    # initialize redactor
    redactor = ImageRedactor(ocrLanguages=args.lang)

    # configure redaction style
    style = RedactionStyle(
        mode=args.mode,
        fillColor=hexToRgb(args.fill),
        blurRadius=args.blurRadius,
        pixelSize=args.pixelSize,
        padding=args.padding,
    )

    # perform redaction
    print(f"Processing: {inputPath}")
    print(f"OCR Language: {args.lang}")
    print(f"Redaction Mode: {args.mode}")

    result = redactor.redactFile(
        inputPath=str(inputPath),
        outputPath=str(outputPath),
        entities=args.entities,
        style=style,
        drawLabels=args.labels,
        scoreThreshold=args.min_score,
    )

    # report results
    print(f"\n✓ Redacted Image Saved To: {result.outputPath}")
    print(f"✓ Detected {len(result.boxes)} PII Entities:")

    for box in result.boxes:
        print(f"  • {box.entityType:20s} @ ({box.left:4d}, {box.top:4d})")

    return 0


if __name__ == "__main__":
    exit(main())
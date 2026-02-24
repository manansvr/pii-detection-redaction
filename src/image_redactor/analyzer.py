# src/image_redactor/analyzer.py
"""
Image PII Redaction CLI.

Command-line interface for detecting and redacting PII from images using
OCR (Optical Character Recognition) and visual redaction techniques.

Supported Redaction Styles:
    - fill: Solid color rectangles (default: black)
    - blur: Gaussian blur effect
    - pixelate: Mosaic/pixelation effect
    - rectangle: Outlined rectangles

Features:
    - Multi-language OCR support via Tesseract
    - Customizable redaction colors
    - Adjustable blur and pixelation parameters
    - Confidence threshold filtering
    - Multiple image format support (JPG, PNG, etc.)

Usage:
    python -m image_redactor.analyzer --in photo.jpg --out redacted.jpg
    python -m image_redactor.analyzer --in scan.png --out redacted.png --mode blur
"""
#!/usr/bin/env python3

import argparse
from image_redactor import ImageRedactor, RedactionStyle


def main():
    ap = argparse.ArgumentParser(
        description="Redact PII From Images Using Presidio."
    )

    ap.add_argument("--in", dest="input_path", required=True, help="Input Image Path")
    ap.add_argument("--out", dest="output_path", required=True, help="Output Image Path")
    ap.add_argument(
        "--entities", nargs="*", default=None, help="Entity Types To Redact"
    )

    ap.add_argument(
        "--lang", default="eng", help="OCR Languages"
    )

    ap.add_argument(
        "--mode",
        choices=["fill", "blur", "pixelate", "rectangle"],
        default="fill",
        help="Redaction Mode"
    )

    ap.add_argument(
        "--fill",
        default="#000000",
        help="Fill Color For Fill/Rectangle (HEX)",
    )

    ap.add_argument(
        "--padding",
        type=int,
        default=2,
        help="Padding Around Boxes"
    )

    ap.add_argument(
        "--blur",
        type=int,
        default=8,
        help="Blur Radius For Blur Mode"
    )

    ap.add_argument(
        "--pixel",
        type=int,
        default=12,
        help="Pixel Size For Pixelate Mode"
    )

    ap.add_argument(
        "--labels",
        action="store_true",
        help="Draw Entity Labels On Top Of Redactions"
    )

    args = ap.parse_args()

    def hex_to_rgb(h):
        h = h.lstrip("#")
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

    redactor = ImageRedactor(ocr_languages=args.lang)

    style = RedactionStyle(
        mode=args.mode,
        fill_color=hex_to_rgb(args.fill),
        blur_radius=args.blur,
        pixel_size=args.pixel,
        padding=args.padding,
    )

    res = redactor.redact_file(
        input_path=args.input_path,
        output_path=args.output_path,
        entities=args.entities,
        style=style,
        draw_labels=args.labels,
    )

    print(f"Redacted Image Saved To: {res.output_path}")
    print(f"Detected {len(res.boxes)} Entities:")
    for box in res.boxes:
        print(f"  - {box.entity_type} @ ({box.left}, {box.top})")


if __name__ == "__main__":
    main()
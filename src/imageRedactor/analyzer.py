# src/imageRedactor/analyzer.py
#!/usr/bin/env python3

import argparse
from imageRedactor import ImageRedactor, RedactionStyle


def main():
    ap = argparse.ArgumentParser(
        description="Redact PII From Images Using Presidio."
    )

    ap.add_argument("--in", dest="inputPath", required=True, help="Input Image Path")
    ap.add_argument("--out", dest="outputPath", required=True, help="Output Image Path")
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
    )

    ap.add_argument(
        "--fill",
        default="#000000",
        help="Fill Color For Fill/Rectangle (HEX)",
    )

    ap.add_argument(
        "--padding", type=int, default=2, help="Padding Around Boxes"
    )

    ap.add_argument(
        "--blur", type=int, default=8, help="Blur Radius For Blur Mode"
    )

    ap.add_argument(
        "--pixel", type=int, default=12, help="Pixel Size For Pixelate Mode"
    )

    ap.add_argument(
        "--labels", action="store_true", help="Draw Entity Labels"
    )

    args = ap.parse_args()

    def hexToRgb(h):
        h = h.lstrip("#")
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

    redactor = ImageRedactor(ocrLanguages=args.lang)

    style = RedactionStyle(
        mode=args.mode,
        fillColor=hexToRgb(args.fill),
        blurRadius=args.blur,
        pixelSize=args.pixel,
        padding=args.padding,
    )

    res = redactor.redactFile(
        inputPath=args.inputPath,
        outputPath=args.outputPath,
        entities=args.entities,
        style=style,
        drawLabels=args.labels,
    )

    print(f"Redacted Image Saved To: {res.outputPath}")
    print(f"Detected {len(res.boxes)} Entities:")
    for box in res.boxes:
        print(f"  - {box.entityType} @ ({box.left}, {box.top})")


if __name__ == "__main__":
    main()
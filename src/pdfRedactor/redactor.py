# src/pdfredactor/redactor.py

from __future__ import annotations

from pathlib import Path
from typing import List, Tuple, Dict, Optional

from pikepdf import Pdf, Name, Dictionary, Array, AttachedFileSpec
from pprint import pprint


def _escapePdfText(s: str) -> str:
    return s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _rectStream(
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    fillRgb: Tuple[float, float, float] = (0.0, 0.0, 0.0),
) -> bytes:
    """
    black (or colored) filled rectangle covering [x0,y0]..[x1,y1].
    """
    r, g, b = fillRgb
    w, h = max(0.0, x1 - x0), max(0.0, y1 - y0)
    # 'rg' sets non-stroking color (fill). we only fill.
    return f"{r:.3f} {g:.3f} {b:.3f} rg {x0} {y0} {w} {h} re f Q\n".encode(
        "ascii"
    )


def _labelStream(
    x: float,
    y: float,
    text: str,
    fontTag: str = "/F1",
    size: int = 8,
    rgb: Tuple[float, float, float] = (1.0, 1.0, 1.0),
) -> bytes:
    # default white text unless color passed
    r, g, b = rgb
    s = _escapePdfText(text)
    return (
        f"BT {fontTag} {size} Tf {r:.3f} {g:.3f} {b:.3f} rg 1 0 0 1 {x} {y} Tm ({s}) Tj ET\n"
        .encode("ascii")
    )


def _ensureHelveticaFont(pdf: Pdf, page) -> str:
    """
    this is to ensure a type1 helvetica font is available as /f1 in page resources.
    this returns the font tag string (e.g., '/f1').
    """
    resources = page.obj.get("/Resources", None)
    if resources is None:
        resources = pdf.make_indirect(Dictionary())
        page.obj["/Resources"] = resources

    fontDict = resources.get("/Font", None)
    if fontDict is None:
        fontDict = Dictionary()
        resources["/Font"] = fontDict

    if "/F1" not in fontDict:
        helv = Dictionary(
            Type=Name.Font,
            Subtype=Name.Type1,
            BaseFont=Name.Helvetica,
        )
        fontRef = pdf.make_indirect(helv)
        fontDict["/F1"] = fontRef

    return "/F1"


# this maps entity types to severity buckets. override per call if needed.
defaultSeverityMap: Dict[str, str] = {
    # financial / highly sensitive
    "AU_BANK_ACCOUNT": "high",
    "AU_BSB": "high",
    "AU_ABN": "high",

    # identity / personal
    "PERSON_WITH_TITLE": "medium",
    "PERSON_AFTER_GREETING": "medium",
    "PERSON": "medium",
    "REPEATED_NAME": "medium",

    # low sensitivity
    "AU_STATE": "low",
    "AU_POSTCODE": "low",
    "NAME_TITLE": "low",
}

# this maps severity bucket to rgb fill (0..1).
# keep high as red, medium as orange, low as blue. tweak to your taste.
defaultColorMap: Dict[str, Tuple[float, float, float]] = {
    "high": (0.85, 0.10, 0.10),    # red
    "medium": (1.00, 0.55, 0.00),  # orange
    "low": (0.10, 0.40, 0.85),     # blue
    "_default": (0.00, 0.00, 0.00),  # black
}


def writeRedactedPdf(
    srcPdf: Path,
    dstPdf: Path,
    perPageBboxes: List[List[Tuple]],  # accept 5- or 6-tuples
    drawLabels: bool = True,
    labelPrefix: str = "",
    attachOriginal: bool = False,
    severityMap: Optional[Dict[str, str]] = None,
    colorMap: Optional[Dict[str, Tuple[float, float, float]]] = None,
) -> None:
    """
    this appends rectangles (and optional labels) over detected pii on each page,
    then saves to dstpdf. optionally embed the source file.
    color of masks depends on severity of the entity type (high/medium/low).
    also prints confidence score as black text overlay near the top-left of the mask.
    """
    sevMap = {**defaultSeverityMap, **(severityMap or {})}
    colMap = {**defaultColorMap, **(colorMap or {})}

    def _colorForEntity(entityType: str) -> Tuple[float, float, float]:
        sev = sevMap.get(entityType, "low")
        return colMap.get(sev, colMap.get("_default", (0.0, 0.0, 0.0)))

    with Pdf.open(str(srcPdf)) as pdf:
        for pageIndex, items in enumerate(perPageBboxes):
            if not items:
                continue

            page = pdf.pages[pageIndex]
            fontTag = _ensureHelveticaFont(pdf, page) if drawLabels else "/F1"

            # this builds one content stream per page
            ops = b""
            for item in items:
                # support both (x0,y0,x1,y1,entity) and (x0,y0,x1,y1,entity,score)
                if len(item) >= 6:
                    x0, y0, x1, y1, entityType, score = item[:6]
                else:
                    x0, y0, x1, y1, entityType = item[:5]
                    score = None  # unknown

                fillRgb = _colorForEntity(entityType)
                ops += _rectStream(x0, y0, x1, y1, fillRgb=fillRgb)

                if drawLabels:
                    # light label color logic: white text for dark fill, otherwise black text
                    # simple luminance threshold
                    lum = (
                        0.2126 * fillRgb[0]
                        + 0.7152 * fillRgb[1]
                        + 0.0722 * fillRgb[2]
                    )
                    textRgb = (1.0, 1.0, 1.0) if lum < 0.5 else (0.0, 0.0, 0.0)

                    label = f"{labelPrefix}{entityType}"
                    # entity label near top-left inside mask
                    ops += _labelStream(
                        x0 + 2,
                        y1 - 10,
                        label,
                        fontTag=fontTag,
                        size=8,
                        rgb=textRgb,
                    )

                    # confidence overlay in black, stacked just below the label if present.
                    confText = (
                        f"conf: {score:.2f}"
                        if isinstance(score, (int, float))
                        else "conf: n/a"
                    )
                    confY = y1 - (20 if drawLabels else 10)
                    ops += _labelStream(
                        x0 + 2,
                        confY,
                        confText,
                        fontTag=fontTag,
                        size=8,
                        rgb=(0.0, 0.0, 0.0),
                    )

            page.contents_add(pdf.make_stream(ops))

        if attachOriginal:
            filespec = AttachedFileSpec.from_filepath(pdf, srcPdf)
            pdf.attachments[srcPdf.name] = filespec

        pdf.save(str(dstPdf))
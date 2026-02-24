# src/pdf_redactor/redactor.py

from __future__ import annotations

from pathlib import Path
from typing import List, Tuple, Dict, Optional

from pikepdf import Pdf, Name, Dictionary, Array, AttachedFileSpec
from pprint import pprint

from entity_mapping import AU_ENTITY_SEVERITY_MAP, AU_ENTITY_COLOR_MAP


def escape_pdf_text(s: str) -> str:
    return s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def rect_stream(
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    fill_rgb: Tuple[float, float, float] = (0.0, 0.0, 0.0),
) -> bytes:
    r, g, b = fill_rgb
    w, h = max(0.0, x1 - x0), max(0.0, y1 - y0)
    return f"{r:.3f} {g:.3f} {b:.3f} rg {x0} {y0} {w} {h} re f Q\n".encode(
        "ascii"
    )


def label_stream(
    x: float,
    y: float,
    text: str,
    font_tag: str = "/F1",
    size: int = 8,
    rgb: Tuple[float, float, float] = (1.0, 1.0, 1.0),
) -> bytes:
    r, g, b = rgb
    s = escape_pdf_text(text)
    return (
        f"BT {font_tag} {size} Tf {r:.3f} {g:.3f} {b:.3f} rg 1 0 0 1 {x} {y} Tm ({s}) Tj ET\n"
        .encode("ascii")
    )


def ensure_helvetica_font(pdf: Pdf, page) -> str:
    resources = page.obj.get("/Resources", None)
    if resources is None:
        resources = pdf.make_indirect(Dictionary())
        page.obj["/Resources"] = resources

    font_dict = resources.get("/Font", None)
    if font_dict is None:
        font_dict = Dictionary()
        resources["/Font"] = font_dict

    if "/F1" not in font_dict:
        helv = Dictionary(
            Type=Name.Font,
            Subtype=Name.Type1,
            BaseFont=Name.Helvetica,
        )
        font_ref = pdf.make_indirect(helv)
        font_dict["/F1"] = font_ref

    return "/F1"


default_severity_map = AU_ENTITY_SEVERITY_MAP
default_color_map = AU_ENTITY_COLOR_MAP


def write_redacted_pdf(
    src_pdf: Path,
    dst_pdf: Path,
    per_page_bboxes: List[List[Tuple]],
    draw_labels: bool = True,
    label_prefix: str = "",
    attach_original: bool = False,
    severity_map: Optional[Dict[str, str]] = None,
    color_map: Optional[Dict[str, Tuple[float, float, float]]] = None,
) -> None:
    sev_map = {**default_severity_map, **(severity_map or {})}
    col_map = {**default_color_map, **(color_map or {})}

    def _color_for_entity(entity_type: str) -> Tuple[float, float, float]:
        sev = sev_map.get(entity_type, "low")
        return col_map.get(sev, col_map.get("_default", (0.0, 0.0, 0.0)))

    with Pdf.open(str(src_pdf)) as pdf:
        for page_index, items in enumerate(per_page_bboxes):
            if not items:
                continue

            page = pdf.pages[page_index]
            font_tag = ensure_helvetica_font(pdf, page) if draw_labels else "/F1"

            ops = b""
            for item in items:
                if len(item) >= 6:
                    x0, y0, x1, y1, entity_type, score = item[:6]
                else:
                    x0, y0, x1, y1, entity_type = item[:5]
                    score = None

                fill_rgb = _color_for_entity(entity_type)
                ops += rect_stream(x0, y0, x1, y1, fill_rgb=fill_rgb)

                if draw_labels:
                    lum = (
                        0.2126 * fill_rgb[0]
                        + 0.7152 * fill_rgb[1]
                        + 0.0722 * fill_rgb[2]
                    )
                    text_rgb = (1.0, 1.0, 1.0) if lum < 0.5 else (0.0, 0.0, 0.0)

                    label = f"{label_prefix}{entity_type}"

                    ops += label_stream(
                        x0 + 2,
                        y1 - 10,
                        label,
                        font_tag=font_tag,
                        size=8,
                        rgb=text_rgb,
                    )

                    conf_text = (
                        f"conf: {score:.2f}"
                        if isinstance(score, (int, float))
                        else "conf: n/a"
                    )
                    conf_y = y1 - (20 if draw_labels else 10)
                    ops += label_stream(
                        x0 + 2,
                        conf_y,
                        conf_text,
                        font_tag=font_tag,
                        size=8,
                        rgb=(0.0, 0.0, 0.0),
                    )

            page.contents_add(pdf.make_stream(ops))

        if attach_original:
            filespec = AttachedFileSpec.from_filepath(pdf, src_pdf)
            pdf.attachments[src_pdf.name] = filespec

        pdf.save(str(dst_pdf))
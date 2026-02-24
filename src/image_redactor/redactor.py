# src/image_redactor/redactor.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional, Tuple

from PIL import Image
import pytesseract

from presidio_analyzer import AnalyzerEngine, RecognizerResult
from presidio_image_redactor import ImageRedactorEngine

from .exceptions import ImageRedactorError
from .types import BoundingBox, RedactionResult


@dataclass
class RedactionStyle:
    mode: str = "fill"
    fill_color: Tuple[int, int, int] = (0, 0, 0)
    outline_color: Tuple[int, int, int] = (255, 0, 0)
    blur_radius: int = 8
    pixel_size: int = 12
    stroke_width: int = 3
    padding: int = 2


class ImageRedactor:
    def __init__(
        self,
        analyzer_engine: Optional[AnalyzerEngine] = None,
        ocr_languages: str = "eng",
        tesseract_cmd_override: Optional[str] = None,
    ) -> None:
        if tesseract_cmd_override:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd_override

        self.ocr_languages = ocr_languages
        self.analyzer = analyzer_engine or AnalyzerEngine()
        self.engine = ImageRedactorEngine(analyzer_engine=self.analyzer)

    def redact_file(
        self,
        input_path: str,
        output_path: str,
        entities: Optional[Iterable[str]] = None,
        score_threshold: float = 0.35,
        style: Optional[RedactionStyle] = None,
        draw_labels: bool = False,
    ) -> RedactionResult:
        try:
            image = Image.open(input_path).convert("RGB")
        except Exception as e:
            raise ImageRedactorError(
                f"Failed to open image '{input_path}': {e}"
            ) from e

        return self._redact_image_core(
            image=image,
            output_path=output_path,
            entities=list(entities) if entities else None,
            score_threshold=score_threshold,
            style=style or RedactionStyle(),
            draw_labels=draw_labels,
        )

    def redact_bytes(
        self,
        image_bytes: bytes,
        output_path: str,
        entities: Optional[Iterable[str]] = None,
        score_threshold: float = 0.35,
        style: Optional[RedactionStyle] = None,
        draw_labels: bool = False,
    ) -> RedactionResult:
        from io import BytesIO

        try:
            image = Image.open(BytesIO(image_bytes)).convert("RGB")
        except Exception as e:
            raise ImageRedactorError(
                f"Failed To Open Image From Bytes: {e}"
            ) from e

        return self._redact_image_core(
            image=image,
            output_path=output_path,
            entities=list(entities) if entities else None,
            score_threshold=score_threshold,
            style=style or RedactionStyle(),
            draw_labels=draw_labels,
        )

    def _redact_image_core(
        self,
        image: Image.Image,
        output_path: str,
        entities: Optional[List[str]],
        score_threshold: float,
        style: RedactionStyle,
        draw_labels: bool,
    ) -> RedactionResult:
        redact_kwargs = {
            "padding": style.padding,
            "draw_rectangle": style.mode == "rectangle",
            "stroke_width": style.stroke_width,
            "draw_text": draw_labels,
            "fill": style.fill_color if style.mode in ("fill", "rectangle") else None,
            "blur_radius": style.blur_radius if style.mode == "blur" else None,
            "pixel_size": style.pixel_size if style.mode == "pixelate" else None,
            "outline": style.outline_color if style.mode == "rectangle" else None,
            "score_threshold": score_threshold,
            "entities": entities,
            "ocr_language": self.ocr_languages,
        }

        try:
            redacted_image, boxes, text_entities = self.engine.redact(
                image=image,
                **{k: v for k, v in redact_kwargs.items() if v is not None}
            )
        except TypeError:
            try:
                redacted_image, boxes, text_entities = self.engine.redact(
                    image=image,
                    padding=style.padding,
                    score_threshold=score_threshold,
                    entities=entities,
                    ocr_language=self.ocr_languages,
                    fill=style.fill_color if style.mode in ("fill", "rectangle") else None,
                )
            except Exception as e:
                raise ImageRedactorError(f"Image Redaction Failed: {e}") from e
        except Exception as e:
            raise ImageRedactorError(f"Image Redaction Failed: {e}") from e

        try:
            redacted_image.save(output_path)
        except Exception as e:
            raise ImageRedactorError(
                f"Failed to save redacted image to '{output_path}': {e}"
            ) from e

        bbox_objs: List[BoundingBox] = []
        for bb in boxes or []:
            try:
                bbox_objs.append(
                    BoundingBox(
                        left=int(bb.get("left", 0)),
                        top=int(bb.get("top", 0)),
                        width=int(bb.get("width", 0)),
                        height=int(bb.get("height", 0)),
                        entity_type=str(bb.get("entity_type", "UNKNOWN")),
                        score=bb.get("score"),
                    )
                )
            except Exception:
                pass

        return RedactionResult(
            output_path=output_path,
            boxes=bbox_objs,
            text_entities=list(text_entities or []),
        )
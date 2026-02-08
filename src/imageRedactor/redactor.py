# src/imageRedactor/redactor.py

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
    """
    this configures how to redact detected regions.

    options:
        mode: "fill" | "blur" | "pixelate" | "rectangle"
        fillcolor: rgb tuple when mode is "fill" or rectangle fill.
        outlinecolor: rgb tuple for rectangle outline (if rectangle mode).
        blurradius: blur radius (for "blur" mode).
        pixelsize: pixelation block size (for "pixelate" mode).
        strokewidth: outline thickness (rectangle mode).
        padding: extra pixels to expand each detected box on all sides.
    """

    mode: str = "fill"
    fillColor: Tuple[int, int, int] = (0, 0, 0)
    outlineColor: Tuple[int, int, int] = (255, 0, 0)
    blurRadius: int = 8
    pixelSize: int = 12
    strokeWidth: int = 3
    padding: int = 2


class ImageRedactor:
    """
    this is a thin wrapper around presidio's image redactor engine + analyzer engine.

    - runs ocr + pii detection
    - redacts detected regions using configurable styles
    - saves the redacted image and returns metadata
    """

    def __init__(
        self,
        analyzerEngine: Optional[AnalyzerEngine] = None,
        ocrLanguages: str = "eng",
        tesseractCmdOverride: Optional[str] = None,
    ) -> None:
        """
        arguments:
            analyzerengine:
                optional custom analyzer engine (preloaded recognizers, etc.)
            ocrlanguages:
                tesseract language codes (e.g. "eng", "eng+spa")
            tesseractcmdoverride:
                full path to tesseract executable (windows or custom)
        """
        if tesseractCmdOverride:
            pytesseract.pytesseract.tesseract_cmd = tesseractCmdOverride

        self.ocrLanguages = ocrLanguages
        self.analyzer = analyzerEngine or AnalyzerEngine()
        self.engine = ImageRedactorEngine(analyzer_engine=self.analyzer)

    def redactFile(
        self,
        inputPath: str,
        outputPath: str,
        entities: Optional[Iterable[str]] = None,
        scoreThreshold: float = 0.35,
        style: Optional[RedactionStyle] = None,
        drawLabels: bool = False,
    ) -> RedactionResult:
        """
        redacts pii from an image on disk and saves it.

        arguments:
            inputpath:
                path to source image (png/jpg/jpeg/bmp/tiff)
            outputpath:
                path to write the redacted image
            entities:
                restrict to specific pii entity types
                (e.g. ["phone_number", "email_address"])
            scorethreshold:
                confidence threshold (0..1)
            style:
                redaction style configuration
            drawlabels:
                overlay entity labels near boxes (if supported)

        returns:
            redactionresult with bounding boxes and entity list
        """
        try:
            image = Image.open(inputPath).convert("RGB")
        except Exception as e:
            raise ImageRedactorError(
                f"Failed to open image '{inputPath}': {e}"
            ) from e

        return self._redactImageCore(
            image=image,
            outputPath=outputPath,
            entities=list(entities) if entities else None,
            scoreThreshold=scoreThreshold,
            style=style or RedactionStyle(),
            drawLabels=drawLabels,
        )

    def redactBytes(
        self,
        imageBytes: bytes,
        outputPath: str,
        entities: Optional[Iterable[str]] = None,
        scoreThreshold: float = 0.35,
        style: Optional[RedactionStyle] = None,
        drawLabels: bool = False,
    ) -> RedactionResult:
        """
        redacts pii from image bytes (png/jpeg etc.) and saves to outputpath.
        """
        from io import BytesIO

        try:
            image = Image.open(BytesIO(imageBytes)).convert("RGB")
        except Exception as e:
            raise ImageRedactorError(
                f"Failed To Open Image From Bytes: {e}"
            ) from e

        return self._redactImageCore(
            image=image,
            outputPath=outputPath,
            entities=list(entities) if entities else None,
            scoreThreshold=scoreThreshold,
            style=style or RedactionStyle(),
            drawLabels=drawLabels,
        )

    def _redactImageCore(
        self,
        image: Image.Image,
        outputPath: str,
        entities: Optional[List[str]],
        scoreThreshold: float,
        style: RedactionStyle,
        drawLabels: bool,
    ) -> RedactionResult:
        """
        this is the core wrapper around presidio's image redactor engine.redact().
        """

        redactKwargs = {
            "padding": style.padding,
            "draw_rectangle": style.mode == "rectangle",
            "stroke_width": style.strokeWidth,
            "draw_text": drawLabels,
            "fill": style.fillColor if style.mode in ("fill", "rectangle") else None,
            "blur_radius": style.blurRadius if style.mode == "blur" else None,
            "pixel_size": style.pixelSize if style.mode == "pixelate" else None,
            "outline": style.outlineColor if style.mode == "rectangle" else None,
            "score_threshold": scoreThreshold,
            "entities": entities,
            "ocr_language": self.ocrLanguages,
        }

        try:
            redactedImage, boxes, textEntities = self.engine.redact(
                image=image,
                **{k: v for k, v in redactKwargs.items() if v is not None}
            )
        except TypeError:
            try:
                redactedImage, boxes, textEntities = self.engine.redact(
                    image=image,
                    padding=style.padding,
                    score_threshold=scoreThreshold,
                    entities=entities,
                    ocr_language=self.ocrLanguages,
                    fill=style.fillColor if style.mode in ("fill", "rectangle") else None,
                )
            except Exception as e:
                raise ImageRedactorError(f"Image Redaction Failed: {e}") from e
        except Exception as e:
            raise ImageRedactorError(f"Image Redaction Failed: {e}") from e

        try:
            redactedImage.save(outputPath)
        except Exception as e:
            raise ImageRedactorError(
                f"Failed to save redacted image to '{outputPath}': {e}"
            ) from e

        bboxObjs: List[BoundingBox] = []
        for bb in boxes or []:
            try:
                bboxObjs.append(
                    BoundingBox(
                        left=int(bb.get("left", 0)),
                        top=int(bb.get("top", 0)),
                        width=int(bb.get("width", 0)),
                        height=int(bb.get("height", 0)),
                        entityType=str(bb.get("entity_type", "UNKNOWN")),
                        score=bb.get("score"),
                    )
                )
            except Exception:
                pass

        return RedactionResult(
            outputPath=outputPath,
            boxes=bboxObjs,
            textEntities=list(textEntities or []),
        )
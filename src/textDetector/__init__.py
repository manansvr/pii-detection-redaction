# src/textdetector/__init__.py

from .analyzer import buildAnalyzer
from .chunker import analyzeLongText
from .formatter import resultsToJson
from .anonymize import anonymizeText
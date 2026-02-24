# src/textdetector/__init__.py

from .analyzer import build_analyzer
from .chunker import analyze_long_text
from .formatter import results_to_json
from .anonymize import anonymize_text
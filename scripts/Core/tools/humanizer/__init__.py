"""
Paper Humanizer Module for Project Prometheus

This module provides tools for detecting and removing AI-generated
text patterns from academic papers.
"""

from .detector import AIDetectionMetrics, detect_ai_patterns
from .transformer import SentenceTransformer, VoiceTransformer
from .humanizer import PaperHumanizer, humanize_paper
from .quality_checker import HumanizationQualityChecker

__all__ = [
    'AIDetectionMetrics',
    'detect_ai_patterns',
    'SentenceTransformer',
    'VoiceTransformer',
    'PaperHumanizer',
    'humanize_paper',
    'HumanizationQualityChecker'
]

__version__ = '1.0.0'

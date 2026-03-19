"""
Bilingual Paper Module for Project Prometheus

This module provides tools for creating bilingual (Chinese-English)
academic papers in LaTeX format.
"""

from .generator import BilingualPaperGenerator, BilingualConfig
from .translator import SectionTranslator
from .template import BilingualTemplateManager

__all__ = [
    'BilingualPaperGenerator',
    'BilingualConfig',
    'SectionTranslator',
    'BilingualTemplateManager'
]

__version__ = '1.0.0'

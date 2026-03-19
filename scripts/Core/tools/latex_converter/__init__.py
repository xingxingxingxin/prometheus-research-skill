"""
LaTeX Converter Module for Project Prometheus

This module provides tools for converting Markdown research papers
to LaTeX format for academic publication.
"""

from .converter import MarkdownToLatexConverter, ConversionConfig, convert_markdown_to_latex
from .main_generator import MainTexGenerator, PaperMetadata, generate_main_tex
from .bib_generator import BibTeXGenerator, Reference
from .figure_processor import FigureProcessor
from .table_processor import TableProcessor
from .compiler import LaTeXCompiler, CompilationResult, compile_latex_project
from .linter import LaTeXLinter, LintIssue, lint_latex_project

__all__ = [
    'MarkdownToLatexConverter',
    'ConversionConfig',
    'convert_markdown_to_latex',
    'MainTexGenerator',
    'PaperMetadata',
    'generate_main_tex',
    'BibTeXGenerator',
    'Reference',
    'FigureProcessor',
    'TableProcessor',
    'LaTeXCompiler',
    'CompilationResult',
    'compile_latex_project',
    'LaTeXLinter',
    'LintIssue',
    'lint_latex_project'
]

__version__ = '1.0.0'

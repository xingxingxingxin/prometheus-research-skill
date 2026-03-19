"""
Markdown to LaTeX Converter

Converts Markdown paper sections to LaTeX format using pypandoc.
"""

import re
import os
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field

try:
    import pypandoc
    PYPANDOC_AVAILABLE = True
except ImportError:
    PYPANDOC_AVAILABLE = False


@dataclass
class ConversionConfig:
    """LaTeX conversion configuration."""
    template_path: str = "templates/neurips_2024.tex"
    bibliography_style: str = "plain"
    document_class: str = "article"
    packages: List[str] = field(default_factory=lambda: [
        "amsmath", "amssymb", "graphicx", "booktabs",
        "hyperref", "algorithm", "algorithmic", "tikz"
    ])
    use_pypandoc: bool = True


class MarkdownToLatexConverter:
    """Convert Markdown paper to LaTeX format."""

    def __init__(self, config: ConversionConfig = None):
        self.config = config or ConversionConfig()
        self.section_mapping = {
            "abstract": "abstract",
            "introduction": "section",
            "related_work": "section",
            "method": "section",
            "experiments": "section",
            "results": "section",
            "discussion": "section",
            "conclusion": "section"
        }

    def convert_file(self, input_path: str, output_path: str) -> str:
        """Convert a single Markdown file to LaTeX."""
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Preprocess content
        content = self._preprocess_markdown(content)

        # Convert using pypandoc if available
        if PYPANDOC_AVAILABLE and self.config.use_pypandoc:
            try:
                output = pypandoc.convert_text(
                    content,
                    'latex',
                    format='md',
                    extra_args=['--mathjax']
                )
            except Exception as e:
                print(f"pypandoc conversion failed: {e}")
                output = self._native_convert(content)
        else:
            output = self._native_convert(content)

        # Postprocess LaTeX
        output = self._postprocess_latex(output)

        # Write output
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(output)

        return output

    def convert_paper(self, paper_dir: str, output_dir: str) -> Dict[str, str]:
        """Convert all paper sections to LaTeX."""
        results = {}
        sections_dir = Path(paper_dir) / "sections"

        if sections_dir.exists():
            for md_file in sorted(sections_dir.glob("*.md")):
                section_name = md_file.stem
                output_path = Path(output_dir) / "sections" / f"{section_name}.tex"
                results[section_name] = self.convert_file(
                    str(md_file), str(output_path)
                )

        return results

    def _native_convert(self, content: str) -> str:
        """Native Markdown to LaTeX conversion (fallback)."""
        # Headers
        content = re.sub(r'^# (.+)$', r'\\section{\1}', content, flags=re.MULTILINE)
        content = re.sub(r'^## (.+)$', r'\\subsection{\1}', content, flags=re.MULTILINE)
        content = re.sub(r'^### (.+)$', r'\\subsubsection{\1}', content, flags=re.MULTILINE)

        # Bold and italic
        content = re.sub(r'\*\*(.+?)\*\*', r'\\textbf{\1}', content)
        content = re.sub(r'\*(.+?)\*', r'\\textit{\1}', content)

        # Inline math
        content = re.sub(r'\$(.+?)\$', r'$\1$', content)

        # Display math
        content = re.sub(r'\$\$(.+?)\$\$', r'\\begin{equation}\1\\end{equation}', content, flags=re.DOTALL)

        # Code blocks
        content = re.sub(r'```(\w*)\n(.*?)```', r'\\begin{verbatim}\2\\end{verbatim}', content, flags=re.DOTALL)

        # Lists
        content = re.sub(r'^- (.+)$', r'\\item \1', content, flags=re.MULTILINE)
        content = re.sub(r'(\n\\item .+)+', r'\\begin{itemize}\g<0>\n\\end{itemize}', content)

        return content

    def _preprocess_markdown(self, content: str) -> str:
        """Preprocess Markdown content."""
        # Convert custom equation environment
        content = re.sub(
            r'\$\$(.*?)\$\$',
            r'\\begin{equation}\1\\end{equation}',
            content,
            flags=re.DOTALL
        )

        # Convert figure references
        content = re.sub(
            r'!\[(.*?)\]\((.*?)\)',
            r'\\begin{figure}[h]\n\\centering\n\\includegraphics[width=0.8\\textwidth]{\2}\n\\caption{\1}\n\\end{figure}',
            content
        )

        # Convert table format
        content = self._convert_tables(content)

        return content

    def _postprocess_latex(self, content: str) -> str:
        """Postprocess LaTeX output."""
        # Fix equation numbering
        content = re.sub(
            r'\\begin{equation\*}',
            r'\\begin{equation}',
            content
        )
        content = re.sub(
            r'\\end{equation\*}',
            r'\\end{equation}',
            content
        )

        # Add labels to sections
        def add_label(match):
            title = match.group(1)
            label = re.sub(r'[^a-zA-Z0-9]', '_', title.lower())
            return f'\\section{{{title}}}\\label{{sec:{label}}}'

        content = re.sub(
            r'\\section{(.*?)}',
            add_label,
            content
        )

        return content

    def _convert_tables(self, content: str) -> str:
        """Convert Markdown tables to LaTeX format."""
        # Find table patterns
        table_pattern = r'\|(.+)\|\n\|[-| ]+\|\n((?:\|.+\|\n?)+)'

        def replace_table(match):
            headers = [h.strip() for h in match.group(1).split('|') if h.strip()]
            rows = []
            for row in match.group(2).strip().split('\n'):
                cells = [c.strip() for c in row.split('|') if c.strip()]
                if cells:
                    rows.append(cells)

            if not headers or not rows:
                return match.group(0)

            latex = '\\begin{table}[h]\n\\centering\n'
            latex += '\\begin{tabular}{' + 'l' * len(headers) + '}\n'
            latex += '\\toprule\n'
            latex += ' & '.join(headers) + ' \\\\\n'
            latex += '\\midrule\n'
            for row in rows:
                if len(row) == len(headers):
                    latex += ' & '.join(row) + ' \\\\\n'
            latex += '\\bottomrule\n'
            latex += '\\end{tabular}\n'
            latex += '\\end{table}'

            return latex

        return re.sub(table_pattern, replace_table, content)


def convert_markdown_to_latex(
    input_path: str,
    output_path: str,
    template: str = "neurips"
) -> str:
    """Main conversion function."""
    config = ConversionConfig()

    # Set template based on target
    template_map = {
        "neurips": "templates/neurips_2024.tex",
        "icml": "templates/icml2024.tex",
        "acl": "templates/acl2024.tex",
        "aaai": "templates/aaai2024.tex",
        "iclr": "templates/iclr2024.tex"
    }
    config.template_path = template_map.get(template, config.template_path)

    converter = MarkdownToLatexConverter(config)
    return converter.convert_file(input_path, output_path)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Convert Markdown to LaTeX")
    parser.add_argument("--input", "-i", required=True, help="Input Markdown file/directory")
    parser.add_argument("--output", "-o", required=True, help="Output LaTeX file/directory")
    parser.add_argument("--template", "-t", default="neurips", help="Target template")

    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if input_path.is_dir():
        converter = MarkdownToLatexConverter()
        results = converter.convert_paper(str(input_path), str(output_path))
        print(f"Converted {len(results)} sections")
    else:
        convert_markdown_to_latex(str(input_path), str(output_path), args.template)
        print(f"Converted {input_path} -> {output_path}")

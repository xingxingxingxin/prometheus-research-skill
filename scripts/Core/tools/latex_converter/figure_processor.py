"""
Figure Processor

Process and convert figures for LaTeX documents.
"""

import subprocess
import os
from pathlib import Path
from typing import List, Tuple, Optional
import shutil


class FigureProcessor:
    """Process figures for LaTeX."""

    SUPPORTED_FORMATS = ['.png', '.jpg', '.jpeg', '.svg', '.pdf', '.eps']

    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def convert_to_pdf(self, input_path: str) -> Optional[str]:
        """Convert image to PDF format (vector)."""
        input_path = Path(input_path)
        if not input_path.exists():
            print(f"File not found: {input_path}")
            return None

        output_path = self.output_dir / f"{input_path.stem}.pdf"

        # Already PDF
        if input_path.suffix.lower() == '.pdf':
            shutil.copy(input_path, output_path)
            return str(output_path)

        # SVG to PDF using Inkscape (if available)
        if input_path.suffix.lower() == '.svg':
            try:
                subprocess.run([
                    'inkscape', '--export-pdf', str(output_path),
                    str(input_path)
                ], check=True, capture_output=True)
                return str(output_path)
            except (subprocess.CalledProcessError, FileNotFoundError):
                pass

        # Try ImageMagick for other formats
        try:
            subprocess.run([
                'convert', str(input_path), str(output_path)
            ], check=True, capture_output=True)
            return str(output_path)
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

        # Fallback: copy original file
        output_path = self.output_dir / input_path.name
        shutil.copy(input_path, output_path)
        return str(output_path)

    def optimize_figures(self, figures_dir: str) -> List[str]:
        """Optimize all figures in directory."""
        results = []
        figures_path = Path(figures_dir)

        if not figures_path.exists():
            print(f"Figures directory not found: {figures_path}")
            return results

        for fig in figures_path.iterdir():
            if fig.suffix.lower() in self.SUPPORTED_FORMATS:
                output = self.convert_to_pdf(str(fig))
                if output:
                    results.append(output)

        return results

    def generate_figure_latex(
        self,
        image_path: str,
        caption: str,
        label: str,
        width: str = "0.8\\textwidth",
        position: str = "t"
    ) -> str:
        """Generate LaTeX figure environment."""
        return f'''\\begin{{figure}}[{position}]
\\centering
\\includegraphics[width={width}]{{{image_path}}}
\\caption{{{caption}}}
\\label{{fig:{label}}}
\\end{{figure}}'''

    def generate_subfigure_latex(
        self,
        images: List[Tuple[str, str]],  # [(path, caption), ...]
        main_caption: str,
        main_label: str,
        width: str = "0.45\\textwidth"
    ) -> str:
        """Generate LaTeX subfigure environment."""
        latex = f"\\begin{{figure}}[t]\n\\centering\n"

        for i, (img_path, caption) in enumerate(images):
            latex += f"\\begin{{subfigure}}[b]{{{width}}}\n"
            latex += f"    \\includegraphics[width=\\textwidth]{{{img_path}}}\n"
            latex += f"    \\caption{{{caption}}}\n"
            latex += f"    \\label{{fig:{main_label}_{i}}}\n"
            latex += f"\\end{{subfigure}}\n"
            if i < len(images) - 1:
                latex += "\\hfill\n"

        latex += f"\\caption{{{main_caption}}}\n"
        latex += f"\\label{{fig:{main_label}}}\n"
        latex += "\\end{figure}"

        return latex

    def scan_and_generate_figures(
        self,
        figures_dir: str,
        output_tex: str = None
    ) -> List[dict]:
        """Scan figures directory and generate LaTeX for each."""
        figures_path = Path(figures_dir)
        figures_info = []

        for fig in sorted(figures_path.iterdir()):
            if fig.suffix.lower() in self.SUPPORTED_FORMATS:
                label = fig.stem
                caption = label.replace('_', ' ').title()

                figures_info.append({
                    'path': str(fig),
                    'label': label,
                    'caption': caption,
                    'latex': self.generate_figure_latex(
                        str(fig), caption, label
                    )
                })

        if output_tex:
            with open(output_tex, 'w', encoding='utf-8') as f:
                for fig in figures_info:
                    f.write(fig['latex'])
                    f.write('\n\n')

        return figures_info


class TikZGenerator:
    """Generate TikZ diagrams."""

    @staticmethod
    def generate_architecture_diagram(
        components: List[dict],
        connections: List[Tuple[str, str]],
        output_path: str = None
    ) -> str:
        """Generate TikZ architecture diagram."""
        latex = r'''
\begin{figure*}[t]
\centering
\begin{tikzpicture}[
    node distance=1.5cm,
    block/.style={rectangle, draw, fill=blue!20, minimum width=2cm, minimum height=1cm, align=center},
    arrow/.style={->, >=stealth, thick}
]
'''

        # Add nodes
        for i, comp in enumerate(components):
            name = comp.get('name', f'node{i}')
            label = comp.get('label', name)
            pos = comp.get('position', '')
            latex += f'    \\node[block] ({name}) {{{label}}};\n'

        # Add connections
        for src, dst in connections:
            latex += f'    \\draw[arrow] ({src}) -- ({dst});\n'

        latex += r'''
\end{tikzpicture}
\caption{System architecture overview.}
\label{fig:architecture}
\end{figure*}
'''

        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(latex)

        return latex


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Process figures for LaTeX")
    parser.add_argument("--input", "-i", required=True, help="Input figures directory")
    parser.add_argument("--output", "-o", required=True, help="Output directory")
    parser.add_argument("--tex", "-t", help="Generate .tex file for figures")

    args = parser.parse_args()

    processor = FigureProcessor(args.output)
    results = processor.optimize_figures(args.input)

    print(f"Processed {len(results)} figures")

    if args.tex:
        processor.scan_and_generate_figures(args.input, args.tex)
        print(f"Generated {args.tex}")

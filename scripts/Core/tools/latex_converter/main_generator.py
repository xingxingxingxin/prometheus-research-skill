"""
Main.tex Generator

Generates the main LaTeX file for paper compilation.
"""

from pathlib import Path
from typing import List, Optional, Dict
from dataclasses import dataclass
import yaml


@dataclass
class Author:
    """Author information."""
    name: str
    affiliation: str
    email: str


@dataclass
class PaperMetadata:
    """Paper metadata for LaTeX generation."""
    title: str
    authors: List[Dict]
    abstract: str
    keywords: List[str]
    conference: str = "neurips"


class MainTexGenerator:
    """Generate main.tex file for paper."""

    TEMPLATE_MAP = {
        "neurips": "neurips_2024",
        "icml": "icml2024",
        "acl": "acl2024",
        "aaai": "aaai2024",
        "iclr": "iclr2024"
    }

    def __init__(self, metadata: PaperMetadata):
        self.metadata = metadata

    def generate(self, output_path: str) -> str:
        """Generate main.tex content."""
        template = self._get_template()
        content = template.format(
            title=self.metadata.title,
            authors=self._format_authors(),
            abstract=self._clean_abstract(self.metadata.abstract),
            style_package=self.TEMPLATE_MAP.get(
                self.metadata.conference, "neurips_2024"
            )
        )

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return content

    def _get_template(self) -> str:
        """Get LaTeX template string."""
        return r'''\documentclass{{article}}
\usepackage{{{style_package}}}

\usepackage[utf8]{{inputenc}}
\usepackage[T1]{{fontenc}}
\usepackage{{hyperref}}
\usepackage{{booktabs}}
\usepackage{{amsmath,amssymb,amsfonts}}
\usepackage{{graphicx}}
\usepackage{{algorithm}}
\usepackage{{algorithmic}}
\usepackage{{tikz}}
\usepackage{{microtype}}

% For Chinese support (uncomment if needed)
% \usepackage{{ctex}}

\title{{{title}}}

{authors}

\begin{{document}}

\maketitle

\begin{{abstract}}
{abstract}
\end{{abstract}}

% Main content
\input{{sections/01_introduction}}
\input{{sections/02_related_work}}
\input{{sections/03_method}}
\input{{sections/04_experiments}}
\input{{sections/05_results}}
\input{{sections/06_discussion}}
\input{{sections/07_conclusion}}

% References
\bibliographystyle{{plain}}
\bibliography{{references}}

\end{{document}}
'''

    def _format_authors(self) -> str:
        """Format authors for LaTeX."""
        if not self.metadata.authors:
            return "\\author{Anonymous}"

        author_blocks = []
        for i, author in enumerate(self.metadata.authors):
            name = author.get('name', 'Anonymous')
            affiliation = author.get('affiliation', 'Unknown Institution')
            email = author.get('email', '')

            block = f"{name} \\\\\n{affiliation}"
            if email:
                block += f" \\\\\n\\texttt{{{email}}}"

            if i < len(self.metadata.authors) - 1:
                block += " \\\\\n\\And"

            author_blocks.append(block)

        return "\\author{\n" + "\n".join(author_blocks) + "\n}"

    def _clean_abstract(self, abstract: str) -> str:
        """Clean abstract text."""
        # Remove extra whitespace
        abstract = ' '.join(abstract.split())
        # Escape special characters
        abstract = abstract.replace('%', '\\%')
        return abstract


def generate_main_tex(
    paper_info: dict,
    output_path: str,
    conference: str = "neurips"
) -> str:
    """Generate main.tex from paper info."""
    metadata = PaperMetadata(
        title=paper_info.get('title', 'Untitled'),
        authors=paper_info.get('authors', []),
        abstract=paper_info.get('abstract', ''),
        keywords=paper_info.get('keywords', []),
        conference=conference
    )

    generator = MainTexGenerator(metadata)
    return generator.generate(output_path)


def load_paper_metadata(yaml_path: str) -> PaperMetadata:
    """Load paper metadata from YAML file."""
    with open(yaml_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    return PaperMetadata(
        title=data.get('title', 'Untitled'),
        authors=data.get('authors', []),
        abstract=data.get('abstract', ''),
        keywords=data.get('keywords', []),
        conference=data.get('conference', 'neurips')
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate main.tex")
    parser.add_argument("--config", "-c", required=True, help="YAML config file")
    parser.add_argument("--output", "-o", default="latex/main.tex", help="Output path")
    parser.add_argument("--conference", "-t", default="neurips", help="Target conference")

    args = parser.parse_args()

    metadata = load_paper_metadata(args.config)
    generator = MainTexGenerator(metadata)
    generator.generate(args.output)
    print(f"Generated {args.output}")

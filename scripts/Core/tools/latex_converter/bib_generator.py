"""
BibTeX Generator

Generates BibTeX files from paper citations.
"""

import re
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Reference:
    """Single reference entry."""
    key: str
    ref_type: str  # article, inproceedings, misc, etc.
    authors: List[str] = field(default_factory=list)
    title: str = ""
    year: int = 2024
    journal: str = ""
    booktitle: str = ""
    volume: str = ""
    number: str = ""
    pages: str = ""
    doi: str = ""
    url: str = ""
    publisher: str = ""


class BibTeXGenerator:
    """Generate BibTeX file from references."""

    def __init__(self):
        self.references: List[Reference] = []

    def add_reference(self, ref: Reference):
        """Add a reference."""
        self.references.append(ref)

    def add_from_dict(self, ref_dict: Dict):
        """Add reference from dictionary."""
        ref = Reference(
            key=ref_dict.get('key', ''),
            ref_type=ref_dict.get('type', 'misc'),
            authors=ref_dict.get('authors', []),
            title=ref_dict.get('title', ''),
            year=ref_dict.get('year', 2024),
            journal=ref_dict.get('journal', ''),
            booktitle=ref_dict.get('booktitle', ''),
            volume=ref_dict.get('volume', ''),
            number=ref_dict.get('number', ''),
            pages=ref_dict.get('pages', ''),
            doi=ref_dict.get('doi', ''),
            url=ref_dict.get('url', '')
        )
        self.add_reference(ref)

    def from_markdown_citations(self, content: str) -> List[Reference]:
        """Extract citations from Markdown content."""
        # Pattern for markdown citations
        # Format: [@author2024] or [@author1; @author2]
        pattern = r'@\[?([a-zA-Z][a-zA-Z0-9_]*)]?(\d{4})'
        matches = re.findall(pattern, content)

        refs = []
        seen_keys = set()

        for author, year in matches:
            key = f"{author.lower()}{year}"
            if key not in seen_keys:
                refs.append(Reference(
                    key=key,
                    ref_type="misc",
                    authors=[author],
                    title="[Title needed]",
                    year=int(year)
                ))
                seen_keys.add(key)

        return refs

    def scan_markdown_files(self, directory: str) -> List[Reference]:
        """Scan all Markdown files for citations."""
        all_refs = []
        seen_keys = set()

        for md_file in Path(directory).rglob('*.md'):
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()

            refs = self.from_markdown_citations(content)
            for ref in refs:
                if ref.key not in seen_keys:
                    all_refs.append(ref)
                    seen_keys.add(ref.key)

        return all_refs

    def generate_bibtex(self) -> str:
        """Generate BibTeX content."""
        lines = []
        for ref in self.references:
            lines.append(self._format_entry(ref))
        return '\n\n'.join(lines)

    def _format_entry(self, ref: Reference) -> str:
        """Format single BibTeX entry."""
        entry = f"@{ref.ref_type}{{{ref.key},\n"

        # Authors
        if ref.authors:
            authors_str = " and ".join(ref.authors)
            entry += f"    author = {{{authors_str}}},\n"

        # Title
        if ref.title:
            entry += f"    title = {{{ref.title}}},\n"

        # Year
        entry += f"    year = {{{ref.year}}},\n"

        # Optional fields
        if ref.journal:
            entry += f"    journal = {{{ref.journal}}},\n"
        if ref.booktitle:
            entry += f"    booktitle = {{{ref.booktitle}}},\n"
        if ref.volume:
            entry += f"    volume = {{{ref.volume}}},\n"
        if ref.number:
            entry += f"    number = {{{ref.number}}},\n"
        if ref.pages:
            entry += f"    pages = {{{ref.pages}}},\n"
        if ref.doi:
            entry += f"    doi = {{{ref.doi}}},\n"
        if ref.url:
            entry += f"    url = {{{ref.url}}},\n"
        if ref.publisher:
            entry += f"    publisher = {{{ref.publisher}}},\n"

        entry += "}"
        return entry

    def save(self, output_path: str):
        """Save to .bib file."""
        content = self.generate_bibtex()
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def load_existing(self, bib_path: str):
        """Load existing BibTeX file."""
        with open(bib_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse entries
        entry_pattern = r'@(\w+)\{([^,]+),([^@]+)\}'
        matches = re.findall(entry_pattern, content, re.DOTALL)

        for ref_type, key, fields in matches:
            ref = Reference(key=key.strip(), ref_type=ref_type.lower())

            # Parse fields
            for line in fields.split('\n'):
                line = line.strip()
                if '=' in line:
                    field_name, field_value = line.split('=', 1)
                    field_name = field_name.strip().lower()
                    field_value = field_value.strip(' {},\n')

                    if field_name == 'author':
                        ref.authors = [a.strip() for a in field_value.split(' and ')]
                    elif field_name == 'title':
                        ref.title = field_value
                    elif field_name == 'year':
                        try:
                            ref.year = int(field_value)
                        except ValueError:
                            pass
                    elif field_name == 'journal':
                        ref.journal = field_value
                    elif field_name == 'booktitle':
                        ref.booktitle = field_value

            self.references.append(ref)


# Common reference templates
REFERENCE_TEMPLATES = {
    "neurips": """@inproceedings{{{key},
    author = {{{author}}},
    title = {{{title}}},
    booktitle = {{Advances in Neural Information Processing Systems}},
    year = {{{year}}},
    pages = {{{pages}}}
}""",
    "icml": """@inproceedings{{{key},
    author = {{{author}}},
    title = {{{title}}},
    booktitle = {{Proceedings of the International Conference on Machine Learning}},
    year = {{{year}}},
    pages = {{{pages}}}
}""",
    "arxiv": """@article{{{key},
    author = {{{author}}},
    title = {{{title}}},
    journal = {{arXiv preprint arXiv:{arxiv_id}}},
    year = {{{year}}}
}"""
}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate BibTeX")
    parser.add_argument("--input", "-i", help="Input Markdown file/directory")
    parser.add_argument("--output", "-o", default="references.bib", help="Output .bib file")
    parser.add_argument("--existing", "-e", help="Existing .bib file to merge")

    args = parser.parse_args()

    generator = BibTeXGenerator()

    # Load existing
    if args.existing:
        generator.load_existing(args.existing)

    # Scan for citations
    if args.input:
        input_path = Path(args.input)
        if input_path.is_dir():
            refs = generator.scan_markdown_files(str(input_path))
        else:
            with open(input_path, 'r', encoding='utf-8') as f:
                refs = generator.from_markdown_citations(f.read())

        for ref in refs:
            # Check if already exists
            if not any(r.key == ref.key for r in generator.references):
                generator.add_reference(ref)

    # Save
    generator.save(args.output)
    print(f"Generated {args.output} with {len(generator.references)} references")

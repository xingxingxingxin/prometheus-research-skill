"""
Bilingual Paper Generator

Generate bilingual (Chinese-English) academic papers in LaTeX.
"""

from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field
import os


@dataclass
class BilingualConfig:
    """Configuration for bilingual paper generation."""
    primary_language: str = "english"  # "english" or "chinese"
    include_abstract_both: bool = True  # Include abstract in both languages
    parallel_sections: bool = False  # Side-by-side sections (advanced)
    chinese_font: str = "SimSun"  # Default Chinese font
    english_font: str = "Times New Roman"
    conference: str = "neurips"
    output_format: str = "single"  # "single", "separate", or "parallel"


class BilingualPaperGenerator:
    """Generate bilingual academic papers."""

    BILINGUAL_TEMPLATE = r'''\documentclass[{page_size}]{{article}}

% ==================== 宏包 ====================
\usepackage[utf8]{{inputenc}}
\usepackage[T1]{{fontenc}}

% 中文支持
\usepackage{{xeCJK}}
\setCJKmainfont{{{chinese_font}}}
\setmainfont{{{english_font}}}

% 其他宏包
\usepackage{{hyperref}}
\usepackage{{booktabs}}
\usepackage{{amsmath,amssymb,amsfonts}}
\usepackage{{graphicx}}
\usepackage{{algorithm}}
\usepackage{{algorithmic}}
\usepackage{{tikz}}
\usepackage{{microtype}}
\usepackage{{multicol}}  % 用于并排显示

% 会议样式
\usepackage{{{style_package}}}

% ==================== 文档信息 ====================
\title{{{title}}}

{authors}

\begin{{document}}

\maketitle

% ==================== 双语摘要 ====================
{abstract_section}

% ==================== 正文 ====================
{main_content}

% ==================== 参考文献 ====================
\bibliographystyle{{plain}}
\bibliography{{references}}

\end{{document}}
'''

    def __init__(self, config: BilingualConfig = None):
        self.config = config or BilingualConfig()
        self.template_manager = BilingualTemplateManager()

    def generate(
        self,
        paper_data: Dict,
        output_dir: str,
        output_format: str = None
    ) -> Dict[str, str]:
        """Generate bilingual paper."""
        output_format = output_format or self.config.output_format
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        results = {}

        if output_format == "single":
            # 单文件双语版本
            results['main.tex'] = self._generate_single_file(paper_data, output_path)
        elif output_format == "separate":
            # 分离的英文和中文版本
            results['main_en.tex'] = self._generate_english_version(paper_data, output_path)
            results['main_zh.tex'] = self._generate_chinese_version(paper_data, output_path)
        elif output_format == "parallel":
            # 并排双语版本
            results['main_parallel.tex'] = self._generate_parallel_version(paper_data, output_path)

        return results

    def _generate_single_file(self, paper_data: Dict, output_path: Path) -> str:
        """Generate single bilingual file."""
        # 构建双语摘要
        abstract_section = self._build_bilingual_abstract(paper_data)

        # 构建正文
        main_content = self._build_main_content(paper_data)

        # 生成 LaTeX
        content = self.BILINGUAL_TEMPLATE.format(
            page_size='11pt',
            chinese_font=self.config.chinese_font,
            english_font=self.config.english_font,
            style_package=self._get_style_package(),
            title=paper_data.get('title', 'Untitled'),
            authors=self._format_authors(paper_data.get('authors', [])),
            abstract_section=abstract_section,
            main_content=main_content
        )

        output_file = output_path / 'main.tex'
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)

        return str(output_file)

    def _generate_english_version(self, paper_data: Dict, output_path: Path) -> str:
        """Generate English-only version."""
        template = self._get_english_template()

        content = template.format(
            style_package=self._get_style_package(),
            title=paper_data.get('title', 'Untitled'),
            authors=self._format_authors(paper_data.get('authors', [])),
            abstract=paper_data.get('abstract_en', paper_data.get('abstract', '')),
            main_content=self._build_english_sections(paper_data)
        )

        output_file = output_path / 'main_en.tex'
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)

        return str(output_file)

    def _generate_chinese_version(self, paper_data: Dict, output_path: Path) -> str:
        """Generate Chinese-only version."""
        template = self._get_chinese_template()

        content = template.format(
            chinese_font=self.config.chinese_font,
            style_package=self._get_style_package(),
            title=paper_data.get('title_zh', paper_data.get('title', '未命名')),
            authors=self._format_authors(paper_data.get('authors', [])),
            abstract=paper_data.get('abstract_zh', ''),
            main_content=self._build_chinese_sections(paper_data)
        )

        output_file = output_path / 'main_zh.tex'
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)

        return str(output_file)

    def _generate_parallel_version(self, paper_data: Dict, output_path: Path) -> str:
        """Generate parallel bilingual version (side-by-side)."""
        template = self._get_parallel_template()

        content = template.format(
            chinese_font=self.config.chinese_font,
            english_font=self.config.english_font,
            style_package=self._get_style_package(),
            title_en=paper_data.get('title', 'Untitled'),
            title_zh=paper_data.get('title_zh', '未命名'),
            authors=self._format_authors(paper_data.get('authors', [])),
            abstract_en=paper_data.get('abstract_en', paper_data.get('abstract', '')),
            abstract_zh=paper_data.get('abstract_zh', ''),
            main_content=self._build_parallel_sections(paper_data)
        )

        output_file = output_path / 'main_parallel.tex'
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)

        return str(output_file)

    def _build_bilingual_abstract(self, paper_data: Dict) -> str:
        """Build bilingual abstract section."""
        abstract_en = paper_data.get('abstract_en', paper_data.get('abstract', ''))
        abstract_zh = paper_data.get('abstract_zh', '')

        if not abstract_zh:
            return f"\\begin{{abstract}}\n{abstract_en}\n\\end{{abstract}}"

        return f'''\\begin{{abstract}}
{abstract_en}
\\end{{abstract}}

\\begin{{abstract}}
\\textbf{{摘要 (Chinese Abstract)}}

{abstract_zh}
\\end{{abstract}}'''

    def _build_main_content(self, paper_data: Dict) -> str:
        """Build main content sections."""
        sections = paper_data.get('sections', [])

        content_parts = []
        for section in sections:
            content_parts.append(f"\\input{{sections/{section}}}")

        return '\n'.join(content_parts) if content_parts else "% Content sections here"

    def _build_english_sections(self, paper_data: Dict) -> str:
        """Build English-only sections."""
        sections = paper_data.get('sections_en', paper_data.get('sections', []))
        return '\n'.join(f"\\input{{sections/{s}}}" for s in sections)

    def _build_chinese_sections(self, paper_data: Dict) -> str:
        """Build Chinese-only sections."""
        sections = paper_data.get('sections_zh', paper_data.get('sections', []))
        return '\n'.join(f"\\input{{sections/{s}}}" for s in sections)

    def _build_parallel_sections(self, paper_data: Dict) -> str:
        """Build parallel bilingual sections."""
        sections_en = paper_data.get('sections_en', paper_data.get('sections', []))
        sections_zh = paper_data.get('sections_zh', paper_data.get('sections', []))

        content = []
        for i, (sec_en, sec_zh) in enumerate(zip(sections_en, sections_zh)):
            content.append(f'''
\\begin{{multicols}}{{2}}
\\input{{sections/{sec_en}}}
\\columnbreak
\\input{{sections/{sec_zh}}}
\\end{{multicols}}
''')
        return '\n'.join(content)

    def _get_style_package(self) -> str:
        """Get conference style package."""
        style_map = {
            'neurips': 'neurips_2024',
            'icml': 'icml2024',
            'acl': 'acl2024',
            'aaai': 'aaai2024',
            'iclr': 'iclr2024'
        }
        return style_map.get(self.config.conference, 'neurips_2024')

    def _format_authors(self, authors: List[Dict]) -> str:
        """Format authors for LaTeX."""
        if not authors:
            return "\\author{Anonymous}"

        author_blocks = []
        for i, author in enumerate(authors):
            name = author.get('name', 'Anonymous')
            affiliation = author.get('affiliation', '')
            email = author.get('email', '')

            block = f"{name}"
            if affiliation:
                block += f" \\\\\n{affiliation}"
            if email:
                block += f" \\\\\n\\texttt{{{email}}}"

            if i < len(authors) - 1:
                block += " \\\\\n\\And"

            author_blocks.append(block)

        return "\\author{\n" + "\n".join(author_blocks) + "\n}"

    def _get_english_template(self) -> str:
        """Get English-only template."""
        return r'''\documentclass[11pt]{{article}}
\usepackage{{{style_package}}}
\usepackage[utf8]{{inputenc}}
\usepackage[T1]{{fontenc}}
\usepackage{{hyperref}}
\usepackage{{booktabs}}
\usepackage{{amsmath,amssymb,amsfonts}}
\usepackage{{graphicx}}

\title{{{title}}}
{authors}

\begin{{document}}
\maketitle

\begin{{abstract}}
{abstract}
\end{{abstract}}

{main_content}

\bibliographystyle{{plain}}
\bibliography{{references}}

\end{{document}}
'''

    def _get_chinese_template(self) -> str:
        """Get Chinese-only template."""
        return r'''\documentclass[11pt]{{article}}
\usepackage{{{style_package}}}
\usepackage{{xeCJK}}
\setCJKmainfont{{{chinese_font}}}
\usepackage{{hyperref}}
\usepackage{{booktabs}}
\usepackage{{amsmath,amssymb,amsfonts}}
\usepackage{{graphicx}}

\title{{{title}}}
{authors}

\begin{{document}}
\maketitle

\begin{{abstract}}
{abstract}
\end{{abstract}}

{main_content}

\bibliographystyle{{plain}}
\bibliography{{references}}

\end{{document}}
'''

    def _get_parallel_template(self) -> str:
        """Get parallel bilingual template."""
        return r'''\documentclass[11pt]{{article}}
\usepackage{{{style_package}}}
\usepackage{{xeCJK}}
\setCJKmainfont{{{chinese_font}}}
\setmainfont{{{english_font}}}
\usepackage{{hyperref}}
\usepackage{{booktabs}}
\usepackage{{amsmath,amssymb,amsfonts}}
\usepackage{{graphicx}}
\usepackage{{multicol}}

\title{{{title_en}} / {title_zh}}}
{authors}

\begin{{document}}
\maketitle

\begin{{multicols}}{{2}}
\begin{{abstract}}
{abstract_en}
\end{{abstract}}
\columnbreak
\begin{{abstract}}
{abstract_zh}
\end{{abstract}}
\end{{multicols}}

{main_content}

\bibliographystyle{{plain}}
\bibliography{{references}}

\end{{document}}
'''


class BilingualTemplateManager:
    """Manage bilingual paper templates."""

    def get_template(self, name: str) -> str:
        """Get template by name."""
        templates = {
            'single': BilingualPaperGenerator.BILINGUAL_TEMPLATE,
            'english': BilingualPaperGenerator()._get_english_template(),
            'chinese': BilingualPaperGenerator()._get_chinese_template(),
            'parallel': BilingualPaperGenerator()._get_parallel_template()
        }
        return templates.get(name, templates['single'])


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate bilingual paper")
    parser.add_argument("--config", "-c", required=True, help="Paper config YAML")
    parser.add_argument("--output", "-o", default="latex_bilingual/", help="Output directory")
    parser.add_argument("--format", "-f", choices=['single', 'separate', 'parallel'],
                       default='single', help="Output format")

    args = parser.parse_args()

    import yaml
    with open(args.config, 'r', encoding='utf-8') as f:
        paper_data = yaml.safe_load(f)

    config = BilingualConfig(output_format=args.format)
    generator = BilingualPaperGenerator(config)
    results = generator.generate(paper_data, args.output)

    print(f"Generated {len(results)} file(s):")
    for name, path in results.items():
        print(f"  - {name}: {path}")

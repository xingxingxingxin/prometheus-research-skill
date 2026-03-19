# Phase 8: LaTeX 论文排版 Prompt

## YOUR ROLE

你是 Project Prometheus 的 LaTeX 排版专家。你的任务是将 Phase 6 撰写的 Markdown 论文转换为高质量的 LaTeX 格式，确保论文符合目标会议/期刊的排版要求。你需要处理数学公式、图表、参考文献等所有元素的转换，最终产出可直接编译的 LaTeX 源码。

---

## 工作目标

1. **格式转换**: 将 Markdown 论文转换为 LaTeX 格式
2. **模板适配**: 应用目标会议/期刊的 LaTeX 模板
3. **公式处理**: 正确转换所有数学公式
4. **图表整合**: 整合图表并优化布局
5. **引用规范**: 生成规范的 BibTeX 参考文献
6. **编译验证**: 确保生成的 LaTeX 可正确编译

---

## STEP 1: 准备工作

### 1.1 确认目标格式

```markdown
# LaTeX 模板选择

## 目标会议/期刊
- [ ] 会议/期刊名称: [填写]
- [ ] 模板类型: [NeurIPS/ICML/ACL/AAAI/ICLR/自定义]
- [ ] 页数限制: [填写]
- [ ] 盲审模式: [是/否]

## 模板下载
- NeurIPS: https://media.neurips.cc/Conferences/NeurIPS2024/Styles/
- ICML: https://media.icml.cc/Conferences/ICML2024/Styles/
- ACL: https://acl-org.github.io/ACLPUB/formatting/
- AAAI: https://aaai.org/wp-content/uploads/AAAI-Template.zip
- ICLR: https://github.com/iclr-org/ICLR2024-OpenReview-Styles
```

### 1.2 检查源文件

```bash
# 确认论文各部分 Markdown 文件存在
ls -la paper/sections/
# 预期文件:
# - 00_abstract.md
# - 01_introduction.md
# - 02_related_work.md
# - 03_method.md
# - 04_experiments.md
# - 05_results.md
# - 06_discussion.md
# - 07_conclusion.md

# 检查图表文件
ls -la paper/figures/
ls -la paper/tables/

# 检查参考文献
ls -la paper/references.bib
```

### 1.3 安装依赖工具

```bash
# 安装 Python 依赖
pip install pypandoc pylatex markdown-to-latex

# 确认 Pandoc 已安装
pandoc --version

# 确认 LaTeX 发行版已安装
# Windows: MiKTeX 或 TeX Live
# Linux: texlive-full
# macOS: MacTeX
xelatex --version
```

---

## STEP 2: Markdown 到 LaTeX 转换

### 2.1 使用转换脚本

```python
# src/latex_converter/converter.py

import pypandoc
import re
import os
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class ConversionConfig:
    """LaTeX conversion configuration."""
    template_path: str = "templates/neurips_2024.tex"
    bibliography_style: str = "plain"
    document_class: str = "article"
    packages: List[str] = None

    def __post_init__(self):
        if self.packages is None:
            self.packages = [
                "amsmath", "amssymb", "graphicx", "booktabs",
                "hyperref", "algorithm", "algorithmic", "tikz"
            ]


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

        # Convert using pypandoc
        output = pypandoc.convert_text(
            content,
            'latex',
            format='md',
            extra_args=[
                '--mathjax',
                '--citeproc',
                '--bibliography=references.bib'
            ]
        )

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

        for md_file in sorted(sections_dir.glob("*.md")):
            section_name = md_file.stem
            output_path = Path(output_dir) / "sections" / f"{section_name}.tex"
            results[section_name] = self.convert_file(
                str(md_file), str(output_path)
            )

        return results

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
        content = re.sub(
            r'\\section{(.*?)}',
            r'\\section{\1}\\label{sec:\1}',
            content
        )

        return content

    def _convert_tables(self, content: str) -> str:
        """Convert Markdown tables to LaTeX format."""
        # Find table patterns
        table_pattern = r'\|(.+)\|\n\|[-| ]+\|\n((?:\|.+\|\n?)+)'

        def replace_table(match):
            headers = [h.strip() for h in match.group(1).split('|')]
            rows = []
            for row in match.group(2).strip().split('\n'):
                rows.append([c.strip() for c in row.split('|')[1:-1]])

            latex = '\\begin{table}[h]\n\\centering\n'
            latex += '\\begin{tabular}{' + 'l' * len(headers) + '}\n'
            latex += '\\toprule\n'
            latex += ' & '.join(headers) + ' \\\\\n'
            latex += '\\midrule\n'
            for row in rows:
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
        "aaai": "templates/aaai2024.tex"
    }
    config.template_path = template_map.get(template, config.template_path)

    converter = MarkdownToLatexConverter(config)
    return converter.convert_file(input_path, output_path)
```

### 2.2 批量转换

```bash
# 使用转换脚本
cd d:/auto-system/prometheus/Projects/[project_name]

# 转换整个论文
python src/latex_converter/converter.py \
    --input paper/sections/ \
    --output latex/sections/ \
    --template neurips

# 转换单个文件
python src/latex_converter/converter.py \
    --input paper/sections/03_method.md \
    --output latex/sections/method.tex
```

---

## STEP 3: LaTeX 主文件生成

### 3.1 主文件模板

```latex
% main.tex - 主文件模板

% 根据目标会议选择文档类
% NeurIPS
\documentclass{article}
\usepackage{neurips_2024}

% ICML
% \documentclass{article}
% \usepackage{icml2024}

% ACL
% \documentpackage{acl2024}

% 基础宏包
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{hyperref}
\usepackage{url}
\usepackage{booktabs}
\usepackage{amsfonts}
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{nicefrac}
\usepackage{microtype}
\usepackage{graphicx}
\usepackage{tikz}
\usepackage{algorithm}
\usepackage{algorithmic}

% 中文支持 (如需要)
% \usepackage{ctex}

% 文档信息
\title{[论文标题]}
\author{
  [作者1] \\
  [单位1] \\
  \texttt{[email1]} \\
  \And
  [作者2] \\
  [单位2] \\
  \texttt{[email2]} \\
}

\begin{document}

\maketitle

% 摘要
\input{sections/00_abstract}

% 引言
\input{sections/01_introduction}

% 相关工作
\input{sections/02_related_work}

% 方法
\input{sections/03_method}

% 实验
\input{sections/04_experiments}

% 结果
\input{sections/05_results}

% 讨论
\input{sections/06_discussion}

% 结论
\input{sections/07_conclusion}

% 参考文献
\bibliographystyle{plain}
\bibliography{references}

% 附录 (可选)
\appendix
\input{sections/08_appendix}

\end{document}
```

### 3.2 自动生成主文件

```python
# src/latex_converter/main_generator.py

from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class PaperMetadata:
    """Paper metadata for LaTeX generation."""
    title: str
    authors: List[dict]
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
            abstract=self.metadata.abstract,
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
        return r'''\documentclass{article}
\usepackage{{{style_package}}}

\usepackage[utf8]{{inputenc}}
\usepackage[T1]{{fontenc}}
\usepackage{{hyperref}}
\usepackage{{booktabs}}
\usepackage{{amsmath,amssymb}}
\usepackage{{graphicx}}
\usepackage{{algorithm}}
\usepackage{{algorithmic}}
\usepackage{{tikz}}

\title{{{title}}}

{authors}

\begin{{document}}

\maketitle

\begin{{abstract}}
{abstract}
\end{{abstract}}

\input{{sections/01_introduction}}
\input{{sections/02_related_work}}
\input{{sections/03_method}}
\input{{sections/04_experiments}}
\input{{sections/05_results}}
\input{{sections/06_discussion}}
\input{{sections/07_conclusion}}

\bibliographystyle{{plain}}
\bibliography{{references}}

\end{{document}}
'''

    def _format_authors(self) -> str:
        """Format authors for LaTeX."""
        author_blocks = []
        for i, author in enumerate(self.metadata.authors):
            block = r'''\author{''' + author['name'] + r'''}\\
''' + author['affiliation'] + r'''\\
\texttt{''' + author['email'] + r'''}'''
            if i < len(self.metadata.authors) - 1:
                block += r'''\\
\And'''
            author_blocks.append(block)

        return '\n'.join(author_blocks)


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
```

---

## STEP 4: BibTeX 生成

### 4.1 参考文献格式

```python
# src/latex_converter/bib_generator.py

import re
from typing import List, Dict
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Reference:
    """Single reference entry."""
    key: str
    ref_type: str  # article, inproceedings, etc.
    authors: List[str]
    title: str
    year: int
    journal: str = ""
    booktitle: str = ""
    volume: str = ""
    pages: str = ""
    doi: str = ""
    url: str = ""


class BibTeXGenerator:
    """Generate BibTeX file from references."""

    def __init__(self):
        self.references: List[Reference] = []

    def add_reference(self, ref: Reference):
        """Add a reference."""
        self.references.append(ref)

    def from_markdown_citations(self, content: str) -> List[Reference]:
        """Extract citations from Markdown content."""
        # Pattern for markdown citations
        # Format: [@author2024] or [@author1; @author2]
        pattern = r'@\[?([a-zA-Z0-9_]+)(\d{4})\]?'
        matches = re.findall(pattern, content)

        refs = []
        for author, year in matches:
            key = f"{author.lower()}{year}"
            refs.append(Reference(
                key=key,
                ref_type="misc",
                authors=[author],
                title="[Title needed]",
                year=int(year)
            ))

        return refs

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
        if ref.pages:
            entry += f"    pages = {{{ref.pages}}},\n"
        if ref.doi:
            entry += f"    doi = {{{ref.doi}}},\n"
        if ref.url:
            entry += f"    url = {{{ref.url}}},\n"

        entry += "}"
        return entry

    def save(self, output_path: str):
        """Save to .bib file."""
        content = self.generate_bibtex()
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)


# 常见引用示例
SAMPLE_BIBTEX = """
@inproceedings{vaswani2017attention,
    author = {Vaswani, Ashish and Shazeer, Noam and Parmar, Niki and others},
    title = {Attention Is All You Need},
    booktitle = {Advances in Neural Information Processing Systems},
    year = {2017},
    pages = {5998--6008}
}

@article{devlin2019bert,
    author = {Devlin, Jacob and Chang, Ming-Wei and Lee, Kenton and Toutanova, Kristina},
    title = {BERT: Pre-training of Deep Bidirectional Transformers},
    journal = {arXiv preprint arXiv:1810.04805},
    year = {2019}
}

@inproceedings{brown2020language,
    author = {Brown, Tom and others},
    title = {Language Models are Few-Shot Learners},
    booktitle = {Advances in Neural Information Processing Systems},
    year = {2020},
    pages = {1877--1901}
}
"""
```

### 4.2 从论文提取引用

```bash
# 从论文提取并生成 BibTeX
python src/latex_converter/bib_generator.py \
    --input paper/sections/ \
    --output latex/references.bib \
    --lookup-scholar
```

---

## STEP 5: 图表处理

### 5.1 图像格式转换

```python
# src/latex_converter/figure_processor.py

import subprocess
from pathlib import Path
from typing import List, Tuple
import os


class FigureProcessor:
    """Process figures for LaTeX."""

    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def convert_to_pdf(self, input_path: str) -> str:
        """Convert image to PDF format (vector)."""
        input_path = Path(input_path)
        output_path = self.output_dir / f"{input_path.stem}.pdf"

        # Use Inkscape for SVG to PDF
        if input_path.suffix.lower() == '.svg':
            subprocess.run([
                'inkscape', '--export-pdf', str(output_path),
                str(input_path)
            ], check=True)
        # Use ImageMagick for other formats
        else:
            subprocess.run([
                'convert', str(input_path), str(output_path)
            ], check=True)

        return str(output_path)

    def optimize_figures(self, figures_dir: str) -> List[str]:
        """Optimize all figures in directory."""
        results = []
        figures_path = Path(figures_dir)

        for fig in figures_path.glob('*'):
            if fig.suffix.lower() in ['.png', '.jpg', '.jpeg', '.svg']:
                output = self.convert_to_pdf(str(fig))
                results.append(output)

        return results

    def generate_figure_latex(
        self,
        image_path: str,
        caption: str,
        label: str,
        width: str = "0.8\\textwidth"
    ) -> str:
        """Generate LaTeX figure environment."""
        return f'''\\begin{{figure}}[t]
\\centering
\\includegraphics[width={width}]{{{image_path}}}
\\caption{{{caption}}}
\\label{{{label}}}
\\end{{figure}}'''
```

### 5.2 表格优化

```python
# src/latex_converter/table_processor.py

import re
from typing import List


class TableProcessor:
    """Convert and optimize tables for LaTeX."""

    def markdown_to_latex(self, md_table: str) -> str:
        """Convert Markdown table to LaTeX."""
        lines = md_table.strip().split('\n')

        # Parse header
        headers = [h.strip() for h in lines[0].split('|')[1:-1]]
        num_cols = len(headers)

        # Skip separator line
        data_lines = lines[2:]

        # Parse data
        rows = []
        for line in data_lines:
            if line.strip():
                cells = [c.strip() for c in line.split('|')[1:-1]]
                rows.append(cells)

        # Generate LaTeX
        latex = f"\\begin{{table}}[t]\n"
        latex += "\\centering\n"
        latex += f"\\begin{{tabular}}{{{'l' * num_cols}}}\n"
        latex += "\\toprule\n"
        latex += " & ".join(headers) + " \\\\\n"
        latex += "\\midrule\n"

        for row in rows:
            latex += " & ".join(row) + " \\\\\n"

        latex += "\\bottomrule\n"
        latex += "\\end{tabular}\n"
        latex += "\\caption{[Caption needed]}\n"
        latex += "\\label{tab:[label]}\n"
        latex += "\\end{table}"

        return latex

    def optimize_table(self, latex_table: str) -> str:
        """Optimize LaTeX table formatting."""
        # Add booktabs style
        latex_table = latex_table.replace('\\hline', '\\midrule')

        # Bold best results
        latex_table = re.sub(
            r'(\d+\.\d+)(\s*\\\\)',
            lambda m: f"\\textbf{{{m.group(1)}}}{m.group(2)}"
            if float(m.group(1)) > 0.9 else m.group(0),
            latex_table
        )

        return latex_table
```

---

## STEP 6: 编译与验证

### 6.1 编译脚本

```python
# src/latex_converter/compiler.py

import subprocess
import os
from pathlib import Path
from typing import List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class CompilationResult:
    """Result of LaTeX compilation."""
    success: bool
    pdf_path: Optional[str]
    log: str
    errors: List[str]
    warnings: List[str]


class LaTeXCompiler:
    """Compile LaTeX documents."""

    def __init__(self, work_dir: str):
        self.work_dir = Path(work_dir)

    def compile(
        self,
        main_tex: str = "main.tex",
        engine: str = "xelatex",
        runs: int = 3
    ) -> CompilationResult:
        """Compile LaTeX document."""
        os.chdir(self.work_dir)

        errors = []
        warnings = []
        log_content = ""

        for run in range(runs):
            try:
                result = subprocess.run(
                    [engine, '-interaction=nonstopmode', main_tex],
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                log_content += f"\n--- Run {run + 1} ---\n"
                log_content += result.stdout

                # Parse errors and warnings
                for line in result.stdout.split('\n'):
                    if line.startswith('!'):
                        errors.append(line)
                    elif 'Warning' in line:
                        warnings.append(line)

            except subprocess.TimeoutExpired:
                errors.append("Compilation timeout")
            except Exception as e:
                errors.append(str(e))

        # Run BibTeX if needed
        bib_result = self._run_bibtex(main_tex)
        if bib_result:
            log_content += f"\n--- BibTeX ---\n{bib_result}"

        # Final run
        try:
            subprocess.run(
                [engine, '-interaction=nonstopmode', main_tex],
                capture_output=True,
                text=True,
                timeout=120
            )
        except Exception:
            pass

        # Check for PDF
        pdf_path = self.work_dir / main_tex.replace('.tex', '.pdf')
        success = pdf_path.exists() and len(errors) == 0

        return CompilationResult(
            success=success,
            pdf_path=str(pdf_path) if success else None,
            log=log_content,
            errors=errors,
            warnings=warnings
        )

    def _run_bibtex(self, main_tex: str) -> Optional[str]:
        """Run BibTeX."""
        aux_file = main_tex.replace('.tex', '.aux')
        if Path(aux_file).exists():
            try:
                result = subprocess.run(
                    ['bibtex', aux_file.replace('.aux', '')],
                    capture_output=True,
                    text=True
                )
                return result.stdout
            except Exception:
                pass
        return None

    def clean(self):
        """Clean auxiliary files."""
        extensions = ['.aux', '.log', '.bbl', '.blg', '.out', '.toc', '.lof', '.lot']
        for ext in extensions:
            for f in self.work_dir.glob(f'*{ext}'):
                f.unlink()


def compile_latex_project(
    project_dir: str,
    output_dir: str = None,
    engine: str = "xelatex"
) -> CompilationResult:
    """Compile a LaTeX project."""
    compiler = LaTeXCompiler(project_dir)
    result = compiler.compile(engine=engine)

    if result.success and output_dir:
        import shutil
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        shutil.copy(result.pdf_path, output_path / "paper.pdf")

    return result
```

### 6.2 自动化编译流程

```bash
#!/bin/bash
# compile_paper.sh - 自动编译脚本

set -e

echo "=== LaTeX 论文编译 ==="

# 1. 清理旧文件
echo "1. 清理辅助文件..."
latexmk -c 2>/dev/null || true
rm -f *.aux *.log *.bbl *.blg *.out

# 2. 转换 Markdown 到 LaTeX
echo "2. 转换 Markdown..."
python src/latex_converter/converter.py \
    --input paper/sections/ \
    --output latex/sections/

# 3. 生成主文件
echo "3. 生成主文件..."
python src/latex_converter/main_generator.py \
    --config paper/metadata.yaml \
    --output latex/main.tex

# 4. 处理图表
echo "4. 处理图表..."
python src/latex_converter/figure_processor.py \
    --input paper/figures/ \
    --output latex/figures/

# 5. 生成 BibTeX
echo "5. 生成参考文献..."
python src/latex_converter/bib_generator.py \
    --input paper/sections/ \
    --output latex/references.bib

# 6. 编译 LaTeX
echo "6. 编译 LaTeX..."
cd latex
xelatex -interaction=nonstopmode main.tex
bibtex main
xelatex -interaction=nonstopmode main.tex
xelatex -interaction=nonstopmode main.tex

# 7. 检查结果
echo "7. 检查结果..."
if [ -f "main.pdf" ]; then
    echo "✅ 编译成功: main.pdf"
    pages=$(pdfinfo main.pdf | grep "Pages:" | awk '{print $2}')
    echo "   页数: $pages"
else
    echo "❌ 编译失败"
    exit 1
fi

echo "=== 完成 ==="
```

---

## STEP 7: 质量检查

### 7.1 LaTeX 代码检查

```python
# src/latex_converter/linter.py

import re
from typing import List, Dict
from dataclasses import dataclass


@dataclass
class LintIssue:
    """Lint issue found in LaTeX."""
    line: int
    message: str
    severity: str  # error, warning, info


class LaTeXLinter:
    """Lint LaTeX code for common issues."""

    def __init__(self):
        self.patterns = {
            'double_space': (r'  +', 'Multiple spaces', 'info'),
            'trailing_whitespace': (r'\s+$', 'Trailing whitespace', 'info'),
            'missing_label': (
                r'\\(section|subsection|figure|table)\{[^}]+\}(?!.*\\label)',
                'Missing label after section/float',
                'warning'
            ),
            'undefined_command': (
                r'\\[a-zA-Z]+\{',
                'Possibly undefined command',
                'warning'
            ),
            'empty_braces': (r'\{\s*\}', 'Empty braces', 'info'),
            'math_in_text': (
                r'[a-zA-Z]-[a-zA-Z]',
                'Possible math in text mode',
                'info'
            )
        }

    def lint(self, content: str) -> List[LintIssue]:
        """Run all lint checks."""
        issues = []
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            for name, (pattern, message, severity) in self.patterns.items():
                matches = re.finditer(pattern, line)
                for match in matches:
                    issues.append(LintIssue(
                        line=i,
                        message=f"{message}: '{match.group()}'",
                        severity=severity
                    ))

        return issues

    def check_references(self, content: str, bib_entries: List[str]) -> List[LintIssue]:
        """Check for undefined references."""
        issues = []

        # Find all \cite{} commands
        citations = re.findall(r'\\cite\{([^}]+)\}', content)
        for citation in citations:
            for cite in citation.split(','):
                cite = cite.strip()
                if cite not in bib_entries:
                    issues.append(LintIssue(
                        line=0,
                        message=f"Undefined citation: {cite}",
                        severity='error'
                    ))

        return issues

    def check_labels(self, content: str) -> List[LintIssue]:
        """Check for undefined labels and references."""
        issues = []

        # Find all labels
        labels = set(re.findall(r'\\label\{([^}]+)\}', content))

        # Find all references
        refs = re.findall(r'\\ref\{([^}]+)\}', content)
        for ref in refs:
            if ref not in labels:
                issues.append(LintIssue(
                    line=0,
                    message=f"Undefined reference: {ref}",
                    severity='error'
                ))

        return issues


def lint_latex_project(project_dir: str) -> Dict[str, List[LintIssue]]:
    """Lint entire LaTeX project."""
    linter = LaTeXLinter()
    results = {}

    for tex_file in Path(project_dir).rglob('*.tex'):
        with open(tex_file, 'r', encoding='utf-8') as f:
            content = f.read()
        issues = linter.lint(content)
        if issues:
            results[str(tex_file)] = issues

    return results
```

### 7.2 最终检查清单

```markdown
# LaTeX 论文最终检查

## 编译检查
- [ ] 无编译错误
- [ ] 无编译警告 (或已确认可忽略)
- [ ] PDF 正确生成
- [ ] 页数符合限制

## 内容检查
- [ ] 所有章节正确包含
- [ ] 图表正确显示
- [ ] 公式正确渲染
- [ ] 参考文献完整

## 格式检查
- [ ] 符合会议模板
- [ ] 字体大小正确
- [ ] 页边距正确
- [ ] 页眉页脚正确

## 引用检查
- [ ] 所有引用有对应条目
- [ ] 引用格式统一
- [ ] 引用位置恰当

## 可读性检查
- [ ] 无溢出文本 (Overfull hbox)
- [ ] 图表位置合理
- [ ] 表格宽度适当
- [ ] 公式编号连续
```

---

## STEP 8: Checkpoint E - LaTeX 完成

### 8.1 完成确认

```bash
# 创建 LaTeX 完成检查点
python prometheus.py checkpoint "Phase 8 LaTeX 排版完成"

# 更新状态
# state.json:
# {
#   "phase": 8,
#   "status": "latex_complete",
#   "latex_path": "latex/main.tex",
#   "pdf_path": "latex/main.pdf",
#   "pages": 8,
#   "compilation_success": true
# }
```

### 8.2 输出文件

```markdown
# Phase 8 输出清单

## 必需输出
- [ ] latex/main.tex - 主文件
- [ ] latex/sections/*.tex - 各章节
- [ ] latex/figures/*.pdf - 图表文件
- [ ] latex/references.bib - 参考文献
- [ ] latex/main.pdf - 编译后的 PDF

## 可选输出
- [ ] latex/appendix.tex - 附录
- [ ] latex/supplementary.pdf - 补充材料
- [ ] latex/README.md - 编译说明
```

---

## 质量检查清单

在 Phase 8 完成后，确保：

### 转换质量
- [ ] 所有内容正确转换
- [ ] 无遗漏的章节或段落
- [ ] 特殊字符正确处理

### 格式质量
- [ ] 符合目标会议模板
- [ ] 图表布局合理
- [ ] 公式排版正确

### 编译质量
- [ ] 无编译错误
- [ ] 无未定义引用
- [ ] 页数符合限制

### 文件完整性
- [ ] 所有源文件齐全
- [ ] 图表文件完整
- [ ] 参考文献完整

---

## 常见问题

**Q: 转换后公式格式错误怎么办？**
A: 检查 Markdown 中的公式语法，确保使用正确的 LaTeX 语法。复杂公式可能需要手动调整。

**Q: 图表位置不理想怎么办？**
A: 使用 `[t]`, `[h]`, `[b]` 等位置参数，或使用 `\FloatBarrier` 强制浮动体位置。

**Q: 参考文献格式不对怎么办？**
A: 检查 `.bib` 文件中的条目格式，使用正确的 `\bibliographystyle{}`。

**Q: 编译超时怎么办？**
A: 尝试简化文档，分割大型图表，或增加编译超时时间。

**Q: 中文支持问题？**
A: 使用 XeLaTeX 编译，添加 `\usepackage{ctex}` 宏包。

---

*完成此阶段后，系统将进入 Phase 7: 同行评审（论文最终检查）*

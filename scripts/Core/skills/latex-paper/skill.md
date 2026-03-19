# LaTeX Paper Formatting Skill

Convert Markdown research papers to LaTeX format for academic publication.

## Usage

```
/latex-paper [options]
```

### Options

- `--input, -i`: Input Markdown file or directory
- `--output, -o`: Output LaTeX file or directory
- `--template, -t`: Target template (neurips, icml, acl, aaai, iclr)
- `--compile, -c`: Compile to PDF after conversion
- `--check, -C`: Run quality checks only

### Examples

```bash
# Convert single file
/latex-paper -i paper.md -o paper.tex -t neurips

# Convert entire paper
/latex-paper -i paper/ -o latex/ -t icml --compile

# Quality check only
/latex-paper -C -i latex/
```

## Features

1. **Markdown to LaTeX Conversion**
   - Section headers
   - Math equations
   - Figures and tables
   - Citations

2. **Template Support**
   - NeurIPS 2024
   - ICML 2024
   - ACL 2024
   - AAAI 2024
   - ICLR 2024

3. **BibTeX Generation**
   - Extract citations from Markdown
   - Generate .bib file
   - Validate references

4. **Quality Checks**
   - Compilation validation
   - Reference checking
   - Format compliance

## Workflow

1. Read Markdown input
2. Convert to LaTeX using pypandoc
3. Apply conference template
4. Process figures and tables
5. Generate BibTeX
6. Compile to PDF (optional)
7. Run quality checks

## Dependencies

- pypandoc
- pylatex (optional)
- XeLaTeX or pdfLaTeX

## Installation

```bash
pip install pypandoc pylatex
# Install Pandoc from https://pandoc.org/installing.html
# Install LaTeX distribution (MiKTeX, TeX Live, or MacTeX)
```

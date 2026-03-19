# LaTeX Templates for Academic Papers

This directory contains LaTeX templates for major machine learning and NLP conferences.

## Available Templates

### 1. ICML Template (`icml_template.tex`)
Template for the **International Conference on Machine Learning** (ICML).

**Features:**
- ICML 2025 style formatting
- Two-column layout
- Author and affiliation handling
- Algorithm and equation examples
- Table and figure examples

**Usage:**
```bash
# You need the icml2025.sty file from the ICML website
# Download from: https://icml.cc/Conferences/2025/StyleAuthorInstructions
pdflatex icml_template.tex
bibtex icml_template
pdflatex icml_template.tex
pdflatex icml_template.tex
```

### 2. NeurIPS Template (`neurips_template.tex`)
Template for the **Conference on Neural Information Processing Systems** (NeurIPS).

**Features:**
- NeurIPS 2025 style formatting
- Theorem and proof environments
- Detailed algorithm pseudocode
- Ablation study tables
- Broader impact section

**Usage:**
```bash
# You need the neurips_2025.sty file from the NeurIPS website
# Download from: https://neurips.cc/Conferences/2025/PresenterInstructions
pdflatex neurips_template.tex
bibtex neurips_template
pdflatex neurips_template.tex
pdflatex neurips_template.tex
```

### 3. ACL Template (`acl_template.tex`)
Template for the **Annual Meeting of the Association for Computational Linguistics** (ACL).

**Features:**
- ACL 2025 style formatting
- NLP-specific sections (linguistic analysis, error analysis)
- Ethical considerations section
- Limitations section (required by ACL)
- Qualitative examples table

**Usage:**
```bash
# You need the acl.sty file from the ACL website
# Download from: https://2025.aclweb.org/calls/papers/
pdflatex acl_template.tex
bibtex acl_template
pdflatex acl_template.tex
pdflatex acl_template.tex
```

## Shared Files

### `references.bib`
A BibTeX bibliography file with example entries for:
- Journal articles
- Conference papers
- Books and book chapters
- Preprints (arXiv)
- Technical reports
- Datasets
- Software packages
- Online resources

## Directory Structure

```
latex_template/
├── README.md                 # This file
├── icml_template.tex        # ICML conference template
├── neurips_template.tex     # NeurIPS conference template
├── acl_template.tex         # ACL conference template
├── references.bib           # Shared bibliography file
├── figures/                  # Directory for figures (create as needed)
│   └── .gitkeep
└── sections/                 # Directory for included sections (optional)
    └── .gitkeep
```

## Common Commands

### Compilation
```bash
# Standard compilation with BibTeX
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex

# Using latexmk (recommended)
latexmk -pdf main.tex

# Clean auxiliary files
latexmk -c
```

### Bibliography Management
```bash
# Using BibTeX
bibtex main

# Using BibLaTeX (modern alternative)
# Add to preamble: \usepackage[backend=biber]{biblatex}
biber main
```

## Best Practices

### 1. File Organization
- Keep figures in a `figures/` subdirectory
- Use `\input{}` to include separate section files
- Maintain a clean bibliography file with consistent formatting

### 2. Version Control
- Commit `.tex` and `.bib` files
- Ignore auxiliary files (`.aux`, `.log`, `.bbl`, etc.)
- Use meaningful commit messages

### 3. Writing Tips
- Use `\citep{}` for parenthetical citations: (Author, Year)
- Use `\citet{}` for textual citations: Author (Year)
- Label equations, figures, and tables for easy reference
- Use `\autoref{}` or `\cref{}` for automatic reference formatting

### 4. Tables
```latex
% Use booktabs for professional tables
\usepackage{booktabs}

\begin{table}[t]
    \centering
    \caption{Table caption.}
    \label{tab:label}
    \begin{tabular}{lcc}
        \toprule
        Method & Metric 1 & Metric 2 \\
        \midrule
        Baseline & 85.2 & 0.84 \\
        Ours & \textbf{91.5} & \textbf{0.90} \\
        \bottomrule
    \end{tabular}
\end{table}
```

### 5. Figures
```latex
\begin{figure}[t]
    \centering
    \includegraphics[width=\columnwidth]{figures/example.pdf}
    \caption{Figure caption.}
    \label{fig:label}
\end{figure}
```

### 6. Algorithms
```latex
\usepackage{algorithm}
\usepackage{algorithmic}

\begin{algorithm}[t]
   \caption{Algorithm Name}
   \label{alg:label}
\begin{algorithmic}
   \STATE \textbf{Input:} Input description
   \STATE \textbf{Output:} Output description
   \STATE Do something
\end{algorithmic}
\end{algorithm}
```

## Conference Style Files

Each template requires the conference's official style file (`.sty`):

1. **ICML**: Download from the [ICML website](https://icml.cc/)
2. **NeurIPS**: Download from the [NeurIPS website](https://neurips.cc/)
3. **ACL**: Download from the [ACL website](https://aclweb.org/)

## Additional Resources

- [Overleaf Documentation](https://www.overleaf.com/learn)
- [LaTeX Wikibook](https://en.wikibooks.org/wiki/LaTeX)
- [Conference-specific templates on Overleaf](https://www.overleaf.com/gallery/tagged/conference)

## Notes

- Templates are based on 2025 conference guidelines
- Always check the latest conference requirements before submission
- Style files may change year to year
- Some conferences use OpenReview or CMT for submissions

## License

These templates are provided for academic use. Conference style files may have specific license terms.

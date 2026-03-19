"""
Bilingual Template Manager

Manage LaTeX templates for bilingual papers.
"""

from pathlib import Path
from typing import Dict, Optional


class BilingualTemplateManager:
    """Manage LaTeX templates for bilingual papers."""

    DEFAULT_TEMPLATES = {
        'neurips_bilingual': r'''% NeurIPS 2024 Bilingual Template
\documentclass{article}
\usepackage{neurips_2024}

% 中文支持
\usepackage{xeCJK}
\setCJKmainfont{SimSun}

\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{hyperref}
\usepackage{booktabs}
\usepackage{amsmath,amssymb}
\usepackage{graphicx}

\title{%%TITLE%%}
\author{%%AUTHORS%%}

\begin{document}
\maketitle

%%ABSTRACT%%

%%CONTENT%%

\bibliographystyle{plain}
\bibliography{references}

\end{document}
''',

        'ctex_article': r'''% CTeX Article Template
\documentclass[UTF8]{ctexart}

\usepackage{hyperref}
\usepackage{booktabs}
\usepackage{amsmath,amssymb}
\usepackage{graphicx}

\title{%%TITLE%%}
\author{%%AUTHORS%%}

\begin{document}
\maketitle

%%ABSTRACT%%

%%CONTENT%%

\bibliographystyle{plain}
\bibliography{references}

\end{document}
''',

        'parallel': r'''% Parallel Bilingual Template
\documentclass[11pt]{article}

\usepackage{xeCJK}
\setCJKmainfont{SimSun}
\setmainfont{Times New Roman}

\usepackage{multicol}
\usepackage{hyperref}
\usepackage{booktabs}
\usepackage{amsmath,amssymb}
\usepackage{graphicx}

\title{%%TITLE_EN%% / %%TITLE_ZH%%}
\author{%%AUTHORS%%}

\begin{document}
\maketitle

\begin{multicols}{2}
\begin{abstract}
%%ABSTRACT_EN%%
\end{abstract}
\columnbreak
\begin{abstract}
%%ABSTRACT_ZH%%
\end{abstract}
\end{multicols}

%%CONTENT%%

\end{document}
'''
    }

    def __init__(self, template_dir: str = None):
        self.template_dir = Path(template_dir) if template_dir else None
        self.custom_templates: Dict[str, str] = {}

    def get_template(self, name: str) -> Optional[str]:
        """Get template by name."""
        # Check custom templates first
        if name in self.custom_templates:
            return self.custom_templates[name]

        # Check default templates
        if name in self.DEFAULT_TEMPLATES:
            return self.DEFAULT_TEMPLATES[name]

        # Check file system
        if self.template_dir:
            template_file = self.template_dir / f"{name}.tex"
            if template_file.exists():
                return template_file.read_text(encoding='utf-8')

        return None

    def add_template(self, name: str, content: str):
        """Add a custom template."""
        self.custom_templates[name] = content

    def list_templates(self) -> list:
        """List available templates."""
        templates = list(self.DEFAULT_TEMPLATES.keys())
        templates.extend(self.custom_templates.keys())

        if self.template_dir:
            for f in self.template_dir.glob('*.tex'):
                templates.append(f.stem)

        return list(set(templates))

    def fill_template(
        self,
        template_name: str,
        replacements: Dict[str, str]
    ) -> str:
        """Fill template with content."""
        template = self.get_template(template_name)
        if not template:
            raise ValueError(f"Template '{template_name}' not found")

        result = template
        for key, value in replacements.items():
            placeholder = f"%%{key}%%"
            result = result.replace(placeholder, value)

        return result


if __name__ == "__main__":
    manager = BilingualTemplateManager()

    print("Available templates:", manager.list_templates())

    # Test template filling
    content = manager.fill_template('ctex_article', {
        'TITLE': '测试论文标题',
        'AUTHORS': '张三 \\and 李四',
        'ABSTRACT': '\\begin{abstract} 这是摘要内容。 \\end{abstract}',
        'CONTENT': '\\section{引言} 这是正文内容。'
    })

    print("\nGenerated content (first 500 chars):")
    print(content[:500])

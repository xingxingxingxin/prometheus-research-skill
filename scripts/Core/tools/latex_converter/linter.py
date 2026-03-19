"""
LaTeX Linter

Check LaTeX code for common issues and best practices.
"""

import re
from typing import List, Dict, Set
from dataclasses import dataclass
from pathlib import Path


@dataclass
class LintIssue:
    """Lint issue found in LaTeX."""
    file: str
    line: int
    column: int
    message: str
    severity: str  # error, warning, info
    rule: str


class LaTeXLinter:
    """Lint LaTeX code for common issues."""

    RULES = {
        'double_space': {
            'pattern': r'  +',
            'message': 'Multiple consecutive spaces',
            'severity': 'info'
        },
        'trailing_whitespace': {
            'pattern': r'[ \t]+$',
            'message': 'Trailing whitespace',
            'severity': 'info'
        },
        'missing_label_section': {
            'pattern': r'\\(?:section|subsection|subsubsection)\{([^}]+)\}(?!\s*\\label)',
            'message': 'Section without label',
            'severity': 'warning'
        },
        'empty_braces': {
            'pattern': r'\{\s*\}',
            'message': 'Empty braces',
            'severity': 'info'
        },
        'obsolete_command': {
            'pattern': r'\\(centerline|bf|it|rm|sc|sl|tt)(?![a-zA-Z])',
            'message': 'Obsolete command, use modern alternative',
            'severity': 'warning'
        },
        'hline_usage': {
            'pattern': r'\\hline',
            'message': 'Consider using booktabs (\\toprule, \\midrule, \\bottomrule)',
            'severity': 'info'
        },
        'incorrect_spacing': {
            'pattern': r'\\cite\{[^}]+\}[a-zA-Z]',
            'message': 'Missing space after citation',
            'severity': 'info'
        }
    }

    def __init__(self):
        self.issues: List[LintIssue] = []

    def lint_file(self, file_path: str) -> List[LintIssue]:
        """Lint a single LaTeX file."""
        self.issues = []

        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            self._check_line(file_path, i, line)

        # Additional checks
        self._check_references(file_path, content)
        self._check_labels(file_path, content)

        return self.issues

    def _check_line(self, file_path: str, line_num: int, line: str):
        """Check a single line for issues."""
        for rule_name, rule in self.RULES.items():
            matches = re.finditer(rule['pattern'], line)
            for match in matches:
                self.issues.append(LintIssue(
                    file=file_path,
                    line=line_num,
                    column=match.start() + 1,
                    message=f"{rule['message']}: '{match.group()}'",
                    severity=rule['severity'],
                    rule=rule_name
                ))

    def _check_references(self, file_path: str, content: str):
        """Check for reference issues."""
        # Find all citations
        citations = set(re.findall(r'\\cite[pt]?\{([^}]+)\}', content))

        # Find all labels
        labels = set(re.findall(r'\\label\{([^}]+)\}', content))

        # Find all references
        refs = set(re.findall(r'\\(?:ref|eqref|autoref|cref)\{([^}]+)\}', content))

        # Check for undefined references
        for ref in refs:
            if ref not in labels:
                self.issues.append(LintIssue(
                    file=file_path,
                    line=0,
                    column=0,
                    message=f"Undefined reference: {ref}",
                    severity='error',
                    rule='undefined_ref'
                ))

    def _check_labels(self, file_path: str, content: str):
        """Check for label issues."""
        # Find all labels
        labels = re.findall(r'\\label\{([^}]+)\}', content)

        # Check for duplicates
        seen = set()
        for label in labels:
            if label in seen:
                self.issues.append(LintIssue(
                    file=file_path,
                    line=0,
                    column=0,
                    message=f"Duplicate label: {label}",
                    severity='error',
                    rule='duplicate_label'
                ))
            seen.add(label)

        # Check label naming conventions
        for label in labels:
            if not re.match(r'^(fig|tab|sec|eq|alg|lst|ch|app|thm|lem|def|cor|prop):', label):
                self.issues.append(LintIssue(
                    file=file_path,
                    line=0,
                    column=0,
                    message=f"Label '{label}' doesn't follow naming convention (prefix:)",
                    severity='info',
                    rule='label_convention'
                ))

    def check_bibtex(self, bib_path: str, citations: Set[str]) -> List[LintIssue]:
        """Check BibTeX file for issues."""
        issues = []

        try:
            with open(bib_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Find all entry keys
            entry_keys = set(re.findall(r'@\w+\{([^,]+),', content))

            # Check for missing entries
            missing = citations - entry_keys
            for key in missing:
                issues.append(LintIssue(
                    file=bib_path,
                    line=0,
                    column=0,
                    message=f"Missing BibTeX entry for citation: {key}",
                    severity='error',
                    rule='missing_bibtex'
                ))

            # Check for unused entries
            unused = entry_keys - citations
            for key in unused:
                issues.append(LintIssue(
                    file=bib_path,
                    line=0,
                    column=0,
                    message=f"Unused BibTeX entry: {key}",
                    severity='info',
                    rule='unused_bibtex'
                ))

        except FileNotFoundError:
            issues.append(LintIssue(
                file=bib_path,
                line=0,
                column=0,
                message="BibTeX file not found",
                severity='error',
                rule='missing_file'
            ))

        return issues


def lint_latex_project(project_dir: str) -> Dict[str, List[LintIssue]]:
    """Lint entire LaTeX project."""
    linter = LaTeXLinter()
    results = {}
    project_path = Path(project_dir)

    # Lint all .tex files
    for tex_file in project_path.rglob('*.tex'):
        issues = linter.lint_file(str(tex_file))
        if issues:
            results[str(tex_file.relative_to(project_path))] = issues

    # Collect all citations
    all_citations = set()
    for tex_file in project_path.rglob('*.tex'):
        with open(tex_file, 'r', encoding='utf-8') as f:
            content = f.read()
        citations = re.findall(r'\\cite[pt]?\{([^}]+)\}', content)
        for cite in citations:
            all_citations.update(c.strip() for c in cite.split(','))

    # Check BibTeX
    for bib_file in project_path.rglob('*.bib'):
        issues = linter.check_bibtex(str(bib_file), all_citations)
        if issues:
            results[str(bib_file.relative_to(project_path))] = issues

    return results


def format_lint_report(results: Dict[str, List[LintIssue]]) -> str:
    """Format lint results as readable report."""
    if not results:
        return "No issues found."

    lines = ["LaTeX Lint Report", "=" * 50, ""]

    total_errors = 0
    total_warnings = 0
    total_info = 0

    for file_path, issues in results.items():
        lines.append(f"\n{file_path}")
        lines.append("-" * len(file_path))

        for issue in sorted(issues, key=lambda x: (x.line, x.column)):
            severity_icon = {'error': 'E', 'warning': 'W', 'info': 'I'}[issue.severity]
            loc = f"{issue.line}:{issue.column}" if issue.line > 0 else "global"
            lines.append(f"  [{severity_icon}] {loc}: {issue.message} ({issue.rule})")

            if issue.severity == 'error':
                total_errors += 1
            elif issue.severity == 'warning':
                total_warnings += 1
            else:
                total_info += 1

    lines.append("")
    lines.append("=" * 50)
    lines.append(f"Summary: {total_errors} errors, {total_warnings} warnings, {total_info} info")

    return '\n'.join(lines)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Lint LaTeX project")
    parser.add_argument("project", help="Project directory")
    parser.add_argument("--json", "-j", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    results = lint_latex_project(args.project)

    if args.json:
        import json
        output = {
            file: [
                {
                    'line': i.line,
                    'column': i.column,
                    'message': i.message,
                    'severity': i.severity,
                    'rule': i.rule
                }
                for i in issues
            ]
            for file, issues in results.items()
        }
        print(json.dumps(output, indent=2))
    else:
        print(format_lint_report(results))

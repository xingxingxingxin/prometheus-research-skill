"""
Table Processor

Convert and optimize tables for LaTeX.
"""

import re
from typing import List, Optional, Tuple
from pathlib import Path


class TableProcessor:
    """Convert and optimize tables for LaTeX."""

    def markdown_to_latex(
        self,
        md_table: str,
        caption: str = None,
        label: str = None
    ) -> str:
        """Convert Markdown table to LaTeX."""
        lines = md_table.strip().split('\n')

        if len(lines) < 2:
            return ""

        # Parse header
        headers = [h.strip() for h in lines[0].split('|') if h.strip()]
        num_cols = len(headers)

        if num_cols == 0:
            return ""

        # Parse data rows (skip separator line)
        rows = []
        for line in lines[2:]:
            cells = [c.strip() for c in line.split('|') if c.strip()]
            if cells and len(cells) == num_cols:
                rows.append(cells)

        # Generate LaTeX
        latex = "\\begin{table}[t]\n"
        latex += "\\centering\n"

        # Determine column alignment
        col_spec = 'l' * num_cols

        latex += f"\\begin{{tabular}}{{{col_spec}}}\n"
        latex += "\\toprule\n"
        latex += " & ".join(headers) + " \\\\\n"
        latex += "\\midrule\n"

        for row in rows:
            latex += " & ".join(row) + " \\\\\n"

        latex += "\\bottomrule\n"
        latex += "\\end{tabular}\n"

        if caption:
            latex += f"\\caption{{{caption}}}\n"
        if label:
            latex += f"\\label{{tab:{label}}}\n"

        latex += "\\end{table}"

        return latex

    def latex_to_markdown(self, latex_table: str) -> str:
        """Convert LaTeX table back to Markdown."""
        # Extract rows
        rows = []
        in_tabular = False

        for line in latex_table.split('\n'):
            line = line.strip()

            if '\\begin{tabular}' in line:
                in_tabular = True
                continue
            if '\\end{tabular}' in line:
                in_tabular = False
                continue

            if in_tabular and '&' in line:
                # Remove LaTeX commands
                line = re.sub(r'\\\\$', '', line)
                line = re.sub(r'\\(top|mid|bottom)rule', '', line)

                # Split cells
                cells = [c.strip() for c in line.split('&')]
                if cells and any(c for c in cells):
                    rows.append(cells)

        if not rows:
            return ""

        # Generate Markdown
        num_cols = len(rows[0])
        md = "| " + " | ".join(rows[0]) + " |\n"
        md += "| " + " | ".join(["---"] * num_cols) + " |\n"

        for row in rows[1:]:
            md += "| " + " | ".join(row) + " |\n"

        return md

    def optimize_table(self, latex_table: str) -> str:
        """Optimize LaTeX table formatting."""
        # Replace \hline with booktabs
        latex_table = latex_table.replace('\\hline', '\\midrule')

        # Remove double midrules
        latex_table = re.sub(r'\\midrule\s*\\midrule', '\\midrule', latex_table)

        # Ensure proper spacing
        latex_table = re.sub(r'\\\\\s*\n', '\\\\\n', latex_table)

        return latex_table

    def bold_best_values(
        self,
        latex_table: str,
        column_indices: List[int] = None,
        higher_is_better: bool = True
    ) -> str:
        """Bold the best values in specified columns."""
        if column_indices is None:
            return latex_table

        lines = latex_table.split('\n')
        result_lines = []

        # Extract numeric values per column
        column_values = {i: [] for i in column_indices}

        for line in lines:
            if '&' in line and '\\\\' in line:
                cells = [c.strip() for c in line.split('&')]
                for i in column_indices:
                    if i < len(cells):
                        # Extract numeric value
                        match = re.search(r'([\d.]+)', cells[i])
                        if match:
                            try:
                                val = float(match.group(1))
                                column_values[i].append((val, len(result_lines)))
                            except ValueError:
                                pass
                result_lines.append(line)
            else:
                result_lines.append(line)

        # Find best values
        for i in column_indices:
            if column_values[i]:
                if higher_is_better:
                    best_val = max(v for v, _ in column_values[i])
                else:
                    best_val = min(v for v, _ in column_values[i])

                # Bold the best value
                for val, line_idx in column_values[i]:
                    if val == best_val:
                        line = result_lines[line_idx]
                        cells = line.split('&')
                        if i < len(cells):
                            # Bold numeric values
                            cells[i] = re.sub(
                                r'([\d.]+)',
                                r'\\textbf{\1}',
                                cells[i]
                            )
                            result_lines[line_idx] = '&'.join(cells)

        return '\n'.join(result_lines)

    def generate_results_table(
        self,
        data: List[dict],
        columns: List[str],
        caption: str = "Results comparison.",
        label: str = "results"
    ) -> str:
        """Generate results table from data."""
        latex = "\\begin{table}[t]\n"
        latex += "\\centering\n"
        latex += f"\\begin{{tabular}}{{l{'c' * (len(columns) - 1)}}}\n"
        latex += "\\toprule\n"
        latex += " & ".join(columns) + " \\\\\n"
        latex += "\\midrule\n"

        for row in data:
            values = [str(row.get(col, '')) for col in columns]
            latex += " & ".join(values) + " \\\\\n"

        latex += "\\bottomrule\n"
        latex += "\\end{tabular}\n"
        latex += f"\\caption{{{caption}}}\n"
        latex += f"\\label{{tab:{label}}}\n"
        latex += "\\end{table}"

        return latex


def scan_markdown_tables(content: str) -> List[str]:
    """Extract all tables from Markdown content."""
    tables = []
    table_pattern = r'(\|.+\|\n\|[-| ]+\|\n(?:\|.+\|\n?)+)'

    matches = re.findall(table_pattern, content)
    return list(matches)


def convert_all_tables(content: str, processor: TableProcessor = None) -> str:
    """Convert all Markdown tables in content to LaTeX."""
    if processor is None:
        processor = TableProcessor()

    tables = scan_markdown_tables(content)

    for table in tables:
        latex_table = processor.markdown_to_latex(table)
        content = content.replace(table, latex_table)

    return content


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Process tables for LaTeX")
    parser.add_argument("--input", "-i", required=True, help="Input file")
    parser.add_argument("--output", "-o", help="Output file")
    parser.add_argument("--format", "-f", choices=['md2tex', 'tex2md'], default='md2tex')

    args = parser.parse_args()

    with open(args.input, 'r', encoding='utf-8') as f:
        content = f.read()

    processor = TableProcessor()

    if args.format == 'md2tex':
        result = convert_all_tables(content, processor)
    else:
        # Single table conversion
        result = processor.latex_to_markdown(content)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(result)
        print(f"Output written to {args.output}")
    else:
        print(result)

"""
LaTeX Compiler

Compile LaTeX documents and manage the compilation process.
"""

import subprocess
import os
import shutil
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class CompilationResult:
    """Result of LaTeX compilation."""
    success: bool
    pdf_path: Optional[str]
    log: str
    errors: List[str]
    warnings: List[str]
    pages: int = 0


class LaTeXCompiler:
    """Compile LaTeX documents."""

    def __init__(self, work_dir: str):
        self.work_dir = Path(work_dir)
        self.aux_extensions = ['.aux', '.log', '.bbl', '.blg', '.out', '.toc', '.lof', '.lot', '.fls', '.fdb_latexmk']

    def compile(
        self,
        main_tex: str = "main.tex",
        engine: str = "xelatex",
        runs: int = 3,
        timeout: int = 120
    ) -> CompilationResult:
        """Compile LaTeX document."""
        original_dir = os.getcwd()
        os.chdir(self.work_dir)

        errors = []
        warnings = []
        log_content = ""

        try:
            for run in range(runs):
                try:
                    result = subprocess.run(
                        [engine, '-interaction=nonstopmode', main_tex],
                        capture_output=True,
                        text=True,
                        timeout=timeout
                    )
                    log_content += f"\n--- Run {run + 1} ---\n"
                    log_content += result.stdout

                    if result.returncode != 0 and run == 0:
                        # Parse errors
                        for line in result.stdout.split('\n'):
                            if line.startswith('!'):
                                errors.append(line)
                            elif 'Warning' in line or 'warning' in line:
                                warnings.append(line)

                except subprocess.TimeoutExpired:
                    errors.append(f"Compilation timeout after {timeout}s")
                except FileNotFoundError:
                    errors.append(f"LaTeX engine '{engine}' not found. Please install a LaTeX distribution.")
                    break
                except Exception as e:
                    errors.append(str(e))

            # Run BibTeX if .aux exists
            bib_result = self._run_bibtex(main_tex)
            if bib_result:
                log_content += f"\n--- BibTeX ---\n{bib_result}"

                # Extra run after BibTeX
                try:
                    subprocess.run(
                        [engine, '-interaction=nonstopmode', main_tex],
                        capture_output=True,
                        text=True,
                        timeout=timeout
                    )
                except Exception:
                    pass

            # Check for PDF
            pdf_path = self.work_dir / main_tex.replace('.tex', '.pdf')
            success = pdf_path.exists() and len(errors) == 0

            # Get page count
            pages = self._get_page_count(str(pdf_path)) if success else 0

            return CompilationResult(
                success=success,
                pdf_path=str(pdf_path) if success else None,
                log=log_content,
                errors=errors,
                warnings=warnings,
                pages=pages
            )

        finally:
            os.chdir(original_dir)

    def _run_bibtex(self, main_tex: str) -> Optional[str]:
        """Run BibTeX."""
        aux_base = main_tex.replace('.tex', '')
        aux_file = aux_base + '.aux'

        if (self.work_dir / aux_file).exists():
            try:
                result = subprocess.run(
                    ['bibtex', aux_base],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                return result.stdout + result.stderr
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
        return None

    def _get_page_count(self, pdf_path: str) -> int:
        """Get page count from PDF."""
        try:
            result = subprocess.run(
                ['pdfinfo', pdf_path],
                capture_output=True,
                text=True
            )
            for line in result.stdout.split('\n'):
                if line.startswith('Pages:'):
                    return int(line.split()[1])
        except (subprocess.SubprocessError, ValueError, FileNotFoundError):
            pass

        # Fallback: estimate from log
        try:
            log_file = pdf_path.replace('.pdf', '.log')
            with open(log_file, 'r') as f:
                content = f.read()
                match = self._search(r'Output written on .* \((\d+) pages', content)
                if match:
                    return int(match.group(1))
        except Exception:
            pass

        return 0

    def _search(self, pattern: str, text: str):
        """Search for pattern in text."""
        import re
        return re.search(pattern, text)

    def clean(self):
        """Clean auxiliary files."""
        for ext in self.aux_extensions:
            for f in self.work_dir.glob(f'*{ext}'):
                try:
                    f.unlink()
                except Exception:
                    pass

    def copy_to_output(self, output_dir: str, include_source: bool = False):
        """Copy compiled files to output directory."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Copy PDF
        for pdf in self.work_dir.glob('*.pdf'):
            shutil.copy(pdf, output_path / pdf.name)

        # Copy source if requested
        if include_source:
            for tex in self.work_dir.glob('*.tex'):
                shutil.copy(tex, output_path / tex.name)
            for bib in self.work_dir.glob('*.bib'):
                shutil.copy(bib, output_path / bib.name)


def compile_latex_project(
    project_dir: str,
    output_dir: str = None,
    engine: str = "xelatex",
    clean_first: bool = True
) -> CompilationResult:
    """Compile a LaTeX project."""
    compiler = LaTeXCompiler(project_dir)

    if clean_first:
        compiler.clean()

    result = compiler.compile(engine=engine)

    if result.success and output_dir:
        compiler.copy_to_output(output_dir)

    return result


def check_latex_installation() -> dict:
    """Check LaTeX installation status."""
    status = {
        'latex': False,
        'pdflatex': False,
        'xelatex': False,
        'bibtex': False,
        'pandoc': False
    }

    for cmd in ['latex', 'pdflatex', 'xelatex', 'bibtex', 'pandoc']:
        try:
            result = subprocess.run(
                [cmd, '--version' if cmd != 'bibtex' else '-version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            status[cmd] = result.returncode == 0 or True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            status[cmd] = False

    return status


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Compile LaTeX project")
    parser.add_argument("--project", "-p", required=True, help="Project directory")
    parser.add_argument("--output", "-o", help="Output directory for PDF")
    parser.add_argument("--engine", "-e", default="xelatex", help="LaTeX engine")
    parser.add_argument("--clean", "-c", action="store_true", help="Clean before compile")
    parser.add_argument("--check", action="store_true", help="Check installation only")

    args = parser.parse_args()

    if args.check:
        status = check_latex_installation()
        print("LaTeX Installation Status:")
        for tool, available in status.items():
            print(f"  {tool}: {'Available' if available else 'Not found'}")
    else:
        result = compile_latex_project(
            args.project,
            args.output,
            args.engine,
            args.clean
        )

        if result.success:
            print(f"Compilation successful!")
            print(f"PDF: {result.pdf_path}")
            print(f"Pages: {result.pages}")
        else:
            print("Compilation failed!")
            for error in result.errors:
                print(f"  Error: {error}")

        if result.warnings:
            print("\nWarnings:")
            for warning in result.warnings[:5]:  # Show first 5 warnings
                print(f"  {warning}")

"""
LaTeX 自动编译工具
==================

自动编译 LaTeX 文档，支持多种编译器（pdflatex, xelatex, lualatex）。
输入 .tex 文件路径，输出 PDF 文件，并提供错误处理和日志记录。
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any


@dataclass
class CompilationResult:
    """编译结果"""
    success: bool
    pdf_path: Optional[str]
    log_path: Optional[str]
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    compilation_time: float = 0.0
    compiler: str = ""
    runs: int = 0
    details: Dict[str, Any] = field(default_factory=dict)


class LaTeXCompiler:
    """LaTeX 编译器封装"""

    # 支持的编译器
    COMPILERS = {
        'pdflatex': {
            'command': 'pdflatex',
            'extension': '.pdf',
            'supports_chinese': False,
            'description': '标准 LaTeX 编译器（不支持中文）'
        },
        'xelatex': {
            'command': 'xelatex',
            'extension': '.pdf',
            'supports_chinese': True,
            'description': 'XeLaTeX 编译器（支持 Unicode 和中文）'
        },
        'lualatex': {
            'command': 'lualatex',
            'extension': '.pdf',
            'supports_chinese': True,
            'description': 'LuaLaTeX 编译器（支持 Lua 脚本和中文）'
        }
    }

    def __init__(self,
                 compiler: str = 'pdflatex',
                 output_dir: str = None,
                 clean_aux: bool = True,
                 max_runs: int = 3,
                 timeout: int = 300):
        """
        初始化 LaTeX 编译器

        Args:
            compiler: 编译器类型 (pdflatex, xelatex, lualatex)
            output_dir: 输出目录（默认与源文件同目录）
            clean_aux: 是否清理辅助文件
            max_runs: 最大编译次数（用于解决交叉引用）
            timeout: 编译超时时间（秒）
        """
        if compiler not in self.COMPILERS:
            raise ValueError(f"不支持的编译器: {compiler}。"
                           f"支持的编译器: {list(self.COMPILERS.keys())}")

        self.compiler = compiler
        self.output_dir = output_dir
        self.clean_aux = clean_aux
        self.max_runs = max_runs
        self.timeout = timeout

        # 检查编译器是否可用
        self._check_compiler_available()

    def _check_compiler_available(self) -> bool:
        """检查编译器是否安装"""
        compiler_cmd = self.COMPILERS[self.compiler]['command']

        try:
            result = subprocess.run(
                [compiler_cmd, '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return True
        except FileNotFoundError:
            raise RuntimeError(
                f"编译器 '{compiler_cmd}' 未安装。"
                f"请安装 TeX Live 或 MiKTeX。"
            )
        except subprocess.TimeoutExpired:
            return True  # 命令存在但超时

    def _detect_chinese(self, tex_path: str) -> bool:
        """
        检测文档是否包含中文

        Args:
            tex_path: .tex 文件路径

        Returns:
            是否包含中文
        """
        try:
            with open(tex_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 检测中文字符
            chinese_pattern = re.compile(r'[\u4e00-\u9fff]')
            return bool(chinese_pattern.search(content))
        except Exception:
            return False

    def _auto_select_compiler(self, tex_path: str) -> str:
        """
        自动选择编译器

        Args:
            tex_path: .tex 文件路径

        Returns:
            编译器名称
        """
        has_chinese = self._detect_chinese(tex_path)

        if has_chinese and self.compiler == 'pdflatex':
            print(f"检测到中文内容，自动切换到 xelatex 编译器")
            return 'xelatex'

        return self.compiler

    def _parse_log_file(self, log_path: str) -> tuple:
        """
        解析日志文件提取错误和警告

        Args:
            log_path: 日志文件路径

        Returns:
            (errors, warnings) 元组
        """
        errors = []
        warnings = []

        try:
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                log_content = f.read()

            # 提取错误
            error_patterns = [
                r'! (.+)',
                r'Error: (.+)',
                r'Fatal error occurred (.+)'
            ]

            for pattern in error_patterns:
                matches = re.findall(pattern, log_content)
                errors.extend(matches)

            # 提取警告
            warning_patterns = [
                r'Warning: (.+)',
                r'LaTeX Warning: (.+)',
                r'Package (\w+) Warning: (.+)'
            ]

            for pattern in warning_patterns:
                matches = re.findall(pattern, log_content)
                if isinstance(matches[0], tuple) if matches else False:
                    warnings.extend([f"{m[0]}: {m[1]}" for m in matches])
                else:
                    warnings.extend(matches)

        except Exception as e:
            errors.append(f"无法解析日志文件: {str(e)}")

        # 去重
        errors = list(dict.fromkeys(errors))
        warnings = list(dict.fromkeys(warnings))

        return errors, warnings

    def _get_aux_files(self, tex_path: str, output_dir: str) -> List[str]:
        """
        获取辅助文件列表

        Args:
            tex_path: .tex 文件路径
            output_dir: 输出目录

        Returns:
            辅助文件列表
        """
        base_name = Path(tex_path).stem
        aux_extensions = [
            '.aux', '.log', '.out', '.toc', '.lof', '.lot',
            '.fls', '.fdb_latexmk', '.bbl', '.blg', '.synctex.gz',
            '.idx', '.ilg', '.ind', '.brf', '.nav', '.snm', '.vrb'
        ]

        aux_files = []
        for ext in aux_extensions:
            aux_file = os.path.join(output_dir, base_name + ext)
            if os.path.exists(aux_file):
                aux_files.append(aux_file)

        return aux_files

    def compile(self, tex_path: str,
                output_dir: str = None,
                extra_options: List[str] = None) -> CompilationResult:
        """
        编译 LaTeX 文档

        Args:
            tex_path: .tex 文件路径
            output_dir: 输出目录（覆盖默认设置）
            extra_options: 额外的编译器选项

        Returns:
            CompilationResult
        """
        import time

        start_time = time.time()

        # 验证输入文件
        tex_path = os.path.abspath(tex_path)
        if not os.path.exists(tex_path):
            return CompilationResult(
                success=False,
                pdf_path=None,
                log_path=None,
                errors=[f"文件不存在: {tex_path}"],
                details={'input_file': tex_path}
            )

        if not tex_path.endswith('.tex'):
            return CompilationResult(
                success=False,
                pdf_path=None,
                log_path=None,
                errors=["输入文件必须是 .tex 文件"],
                details={'input_file': tex_path}
            )

        # 确定输出目录
        if output_dir is None:
            output_dir = self.output_dir or os.path.dirname(tex_path)

        output_dir = os.path.abspath(output_dir)
        os.makedirs(output_dir, exist_ok=True)

        # 自动选择编译器
        compiler = self._auto_select_compiler(tex_path)
        compiler_cmd = self.COMPILERS[compiler]['command']

        # 准备编译命令
        base_name = Path(tex_path).stem
        pdf_path = os.path.join(output_dir, base_name + '.pdf')
        log_path = os.path.join(output_dir, base_name + '.log')

        # 构建命令
        cmd = [
            compiler_cmd,
            '-interaction=nonstopmode',  # 非交互模式
            '-file-line-error',          # 文件行号错误格式
            f'-output-directory={output_dir}',
        ]

        if extra_options:
            cmd.extend(extra_options)

        cmd.append(tex_path)

        # 多次编译（解决交叉引用）
        errors = []
        warnings = []
        runs = 0
        success = False

        for run in range(self.max_runs):
            runs += 1
            print(f"编译运行 {runs}/{self.max_runs}...")

            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                    cwd=os.path.dirname(tex_path)
                )

                # 检查是否成功
                if os.path.exists(pdf_path):
                    success = True

                # 解析日志
                if os.path.exists(log_path):
                    run_errors, run_warnings = self._parse_log_file(log_path)
                    errors.extend(run_errors)
                    warnings.extend(run_warnings)

                # 检查是否需要再次编译
                if os.path.exists(log_path):
                    with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                        log_content = f.read()

                    # 如果日志中出现这些标记，需要再次编译
                    rerun_markers = [
                        'Rerun to get',
                        'Please rerun LaTeX',
                        'Label(s) may have changed'
                    ]

                    needs_rerun = any(marker in log_content for marker in rerun_markers)

                    if not needs_rerun or run == self.max_runs - 1:
                        break

            except subprocess.TimeoutExpired:
                errors.append(f"编译超时（超过 {self.timeout} 秒）")
                success = False
                break
            except Exception as e:
                errors.append(f"编译过程中发生错误: {str(e)}")
                success = False
                break

        # 清理辅助文件
        if self.clean_aux and success:
            aux_files = self._get_aux_files(tex_path, output_dir)
            for aux_file in aux_files:
                try:
                    os.remove(aux_file)
                except Exception:
                    pass

        compilation_time = time.time() - start_time

        # 去重错误和警告
        errors = list(dict.fromkeys(errors))
        warnings = list(dict.fromkeys(warnings))

        return CompilationResult(
            success=success,
            pdf_path=pdf_path if success else None,
            log_path=log_path,
            errors=errors,
            warnings=warnings,
            compilation_time=compilation_time,
            compiler=compiler,
            runs=runs,
            details={
                'input_file': tex_path,
                'output_directory': output_dir,
                'command': ' '.join(cmd)
            }
        )

    def compile_with_bibliography(self, tex_path: str,
                                  output_dir: str = None,
                                  bib_tool: str = 'bibtex') -> CompilationResult:
        """
        编译 LaTeX 文档（包含参考文献）

        完整流程：latex -> bibtex -> latex -> latex

        Args:
            tex_path: .tex 文件路径
            output_dir: 输出目录
            bib_tool: 参考文献工具 (bibtex, biber)

        Returns:
            CompilationResult
        """
        import time

        start_time = time.time()

        # 确定输出目录
        if output_dir is None:
            output_dir = self.output_dir or os.path.dirname(tex_path)

        output_dir = os.path.abspath(output_dir)
        os.makedirs(output_dir, exist_ok=True)

        base_name = Path(tex_path).stem
        aux_path = os.path.join(output_dir, base_name + '.aux')
        pdf_path = os.path.join(output_dir, base_name + '.pdf')
        log_path = os.path.join(output_dir, base_name + '.log')

        all_errors = []
        all_warnings = []

        # 临时禁用清理
        original_clean_aux = self.clean_aux
        self.clean_aux = False

        try:
            # 第一次编译（生成 .aux）
            print("步骤 1/4: 首次 LaTeX 编译...")
            result1 = self.compile(tex_path, output_dir)
            all_errors.extend(result1.errors)
            all_warnings.extend(result1.warnings)

            if not result1.success:
                return result1

            # 运行 bibtex/biber
            print(f"步骤 2/4: 运行 {bib_tool}...")
            try:
                if bib_tool == 'biber':
                    bib_cmd = ['biber', '--output-directory', output_dir, base_name]
                else:
                    bib_cmd = ['bibtex', aux_path]

                bib_result = subprocess.run(
                    bib_cmd,
                    capture_output=True,
                    text=True,
                    timeout=60
                )

                if bib_result.returncode != 0:
                    all_warnings.append(f"{bib_tool} 警告: {bib_result.stderr}")

            except FileNotFoundError:
                all_errors.append(f"{bib_tool} 未找到，跳过参考文献编译")
            except subprocess.TimeoutExpired:
                all_errors.append(f"{bib_tool} 超时")
            except Exception as e:
                all_errors.append(f"{bib_tool} 错误: {str(e)}")

            # 第二次编译
            print("步骤 3/4: 第二次 LaTeX 编译...")
            result2 = self.compile(tex_path, output_dir)
            all_errors.extend(result2.errors)
            all_warnings.extend(result2.warnings)

            # 第三次编译
            print("步骤 4/4: 最终 LaTeX 编译...")
            result3 = self.compile(tex_path, output_dir)
            all_errors.extend(result3.errors)
            all_warnings.extend(result3.warnings)

            compilation_time = time.time() - start_time

            # 现在清理辅助文件
            if original_clean_aux:
                aux_files = self._get_aux_files(tex_path, output_dir)
                for aux_file in aux_files:
                    try:
                        os.remove(aux_file)
                    except Exception:
                        pass

            return CompilationResult(
                success=result3.success,
                pdf_path=pdf_path if result3.success else None,
                log_path=log_path,
                errors=list(dict.fromkeys(all_errors)),
                warnings=list(dict.fromkeys(all_warnings)),
                compilation_time=compilation_time,
                compiler=self.compiler,
                runs=4,
                details={
                    'input_file': tex_path,
                    'output_directory': output_dir,
                    'bib_tool': bib_tool,
                    'workflow': 'latex -> bibtex -> latex -> latex'
                }
            )

        finally:
            self.clean_aux = original_clean_aux

    def result_to_dict(self, result: CompilationResult) -> Dict[str, Any]:
        """将 CompilationResult 转换为字典"""
        return {
            'success': result.success,
            'pdf_path': result.pdf_path,
            'log_path': result.log_path,
            'errors': result.errors,
            'warnings': result.warnings,
            'compilation_time': round(result.compilation_time, 2),
            'compiler': result.compiler,
            'runs': result.runs,
            'details': result.details
        }

    def save_result(self, result: CompilationResult,
                    output_path: str,
                    format: str = 'json') -> None:
        """
        保存编译结果

        Args:
            result: 编译结果
            output_path: 输出路径
            format: 输出格式 (json, txt, markdown)
        """
        result_dict = self.result_to_dict(result)
        path = Path(output_path)

        if format == 'json':
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(result_dict, f, indent=2, ensure_ascii=False)

        elif format == 'txt':
            with open(path, 'w', encoding='utf-8') as f:
                f.write(f"LaTeX 编译结果\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"状态: {'成功' if result.success else '失败'}\n")
                f.write(f"编译器: {result.compiler}\n")
                f.write(f"编译次数: {result.runs}\n")
                f.write(f"耗时: {result.compilation_time:.2f} 秒\n")

                if result.pdf_path:
                    f.write(f"\nPDF 文件: {result.pdf_path}\n")
                if result.log_path:
                    f.write(f"日志文件: {result.log_path}\n")

                if result.errors:
                    f.write(f"\n错误 ({len(result.errors)}):\n")
                    for err in result.errors:
                        f.write(f"  - {err}\n")

                if result.warnings:
                    f.write(f"\n警告 ({len(result.warnings)}):\n")
                    for warn in result.warnings:
                        f.write(f"  - {warn}\n")

        elif format == 'markdown':
            with open(path, 'w', encoding='utf-8') as f:
                f.write(f"# LaTeX 编译结果\n\n")
                f.write(f"## 概要\n\n")
                f.write(f"| 项目 | 值 |\n")
                f.write(f"|------|----|\n")
                f.write(f"| 状态 | {'✅ 成功' if result.success else '❌ 失败'} |\n")
                f.write(f"| 编译器 | {result.compiler} |\n")
                f.write(f"| 编译次数 | {result.runs} |\n")
                f.write(f"| 耗时 | {result.compilation_time:.2f}s |\n")

                if result.pdf_path:
                    f.write(f"| PDF | `{result.pdf_path}` |\n")

                if result.errors:
                    f.write(f"\n## 错误\n\n")
                    for err in result.errors:
                        f.write(f"- {err}\n")

                if result.warnings:
                    f.write(f"\n## 警告\n\n")
                    for warn in result.warnings:
                        f.write(f"- {warn}\n")

        print(f"结果已保存到 {path}")


def create_simple_tex(content: str, output_path: str) -> str:
    """
    创建简单的 LaTeX 文档

    Args:
        content: 文档内容
        output_path: 输出路径

    Returns:
        创建的文件路径
    """
    template = r"""\documentclass{article}
\usepackage[utf8]{inputenc}

\begin{document}

%s

\end{document}
"""

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(template % content)

    return output_path


def print_result(result: CompilationResult):
    """打印编译结果"""
    print("\n" + "=" * 60)
    print(f"LaTeX 编译结果")
    print("=" * 60)
    print(f"状态: {'✅ 成功' if result.success else '❌ 失败'}")
    print(f"编译器: {result.compiler}")
    print(f"编译次数: {result.runs}")
    print(f"耗时: {result.compilation_time:.2f} 秒")

    if result.pdf_path:
        print(f"\nPDF 文件: {result.pdf_path}")

    if result.errors:
        print(f"\n错误 ({len(result.errors)}):")
        for err in result.errors[:5]:  # 只显示前5个错误
            print(f"  ❌ {err}")
        if len(result.errors) > 5:
            print(f"  ... 还有 {len(result.errors) - 5} 个错误")

    if result.warnings:
        print(f"\n警告 ({len(result.warnings)}):")
        for warn in result.warnings[:5]:  # 只显示前5个警告
            print(f"  ⚠️  {warn}")
        if len(result.warnings) > 5:
            print(f"  ... 还有 {len(result.warnings) - 5} 个警告")

    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description='LaTeX 自动编译工具')

    parser.add_argument('input', help='输入 .tex 文件路径')
    parser.add_argument('--output-dir', '-o', help='输出目录')
    parser.add_argument('--compiler', '-c',
                        choices=['pdflatex', 'xelatex', 'lualatex'],
                        default='pdflatex',
                        help='编译器类型 (默认: pdflatex)')
    parser.add_argument('--bib', '-b',
                        action='store_true',
                        help='编译参考文献 (运行 bibtex)')
    parser.add_argument('--bib-tool',
                        choices=['bibtex', 'biber'],
                        default='bibtex',
                        help='参考文献工具 (默认: bibtex)')
    parser.add_argument('--max-runs', '-r',
                        type=int,
                        default=3,
                        help='最大编译次数 (默认: 3)')
    parser.add_argument('--timeout', '-t',
                        type=int,
                        default=300,
                        help='编译超时时间/秒 (默认: 300)')
    parser.add_argument('--keep-aux',
                        action='store_true',
                        help='保留辅助文件')
    parser.add_argument('--save-result',
                        metavar='FILE',
                        help='保存编译结果到文件')
    parser.add_argument('--format', '-f',
                        choices=['json', 'txt', 'markdown'],
                        default='json',
                        help='结果输出格式 (默认: json)')

    args = parser.parse_args()

    # 创建编译器
    try:
        compiler = LaTeXCompiler(
            compiler=args.compiler,
            output_dir=args.output_dir,
            clean_aux=not args.keep_aux,
            max_runs=args.max_runs,
            timeout=args.timeout
        )
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)

    # 编译
    if args.bib:
        result = compiler.compile_with_bibliography(
            args.input,
            output_dir=args.output_dir,
            bib_tool=args.bib_tool
        )
    else:
        result = compiler.compile(args.input, args.output_dir)

    # 打印结果
    print_result(result)

    # 保存结果
    if args.save_result:
        compiler.save_result(result, args.save_result, args.format)

    # 返回状态码
    sys.exit(0 if result.success else 1)


if __name__ == "__main__":
    main()

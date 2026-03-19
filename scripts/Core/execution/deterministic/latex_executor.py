"""
LaTeX Executor - LaTeX编译执行器

处理 T090-T091 LaTeX编译任务，纯代码执行
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import subprocess
import shutil
import os


class LatexExecutor:
    """
    LaTeX编译执行器

    执行确定性LaTeX编译任务，无需LLM：
    - T090: 编译英文PDF
    - T091: 编译中文PDF
    """

    # LaTeX引擎配置
    ENGINE_CONFIGS = {
        "pdflatex": {
            "command": "pdflatex",
            "supports_chinese": False,
            "extension": ".tex",
        },
        "xelatex": {
            "command": "xelatex",
            "supports_chinese": True,
            "extension": ".tex",
        },
        "lualatex": {
            "command": "lualatex",
            "supports_chinese": True,
            "extension": ".tex",
        },
    }

    def __init__(self, project_dir: Path = None):
        self.project_dir = project_dir or Path.cwd()
        self.latex_dir = self.project_dir / "latex"
        self.output_dir = self.project_dir / "output"

    def execute(self, task: Dict, context: Dict) -> Dict:
        """
        执行LaTeX编译任务

        Args:
            task: 任务字典
            context: 执行上下文

        Returns:
            Dict: 执行结果
        """
        task_id = task.get("id", "")

        if task_id == "T090":
            return self._compile_english_pdf(task, context)
        elif task_id == "T091":
            return self._compile_chinese_pdf(task, context)
        else:
            return {
                "success": False,
                "task_id": task_id,
                "error": f"Unknown LaTeX task: {task_id}",
            }

    def _compile_english_pdf(self, task: Dict, context: Dict) -> Dict:
        """T090: 编译英文PDF"""
        # 查找主tex文件
        main_tex = self._find_main_tex(language="english")

        if not main_tex:
            return {
                "success": False,
                "task_id": "T090",
                "error": "No main English .tex file found in latex directory",
            }

        # 编译
        result = self._compile_latex(
            tex_file=main_tex,
            engine="pdflatex",
            output_name="paper_en.pdf",
        )

        return {
            "success": result["success"],
            "task_id": "T090",
            "outputs": {
                "tex_file": str(main_tex),
                "output_pdf": result.get("output_pdf"),
                "engine": "pdflatex",
                "compilation_log": result.get("log"),
            },
            "error": result.get("error"),
        }

    def _compile_chinese_pdf(self, task: Dict, context: Dict) -> Dict:
        """T091: 编译中文PDF"""
        # 查找中文tex文件
        main_tex = self._find_main_tex(language="chinese")

        if not main_tex:
            # 尝试使用英文版 + 中文配置
            main_tex = self._find_main_tex()
            if main_tex:
                # 检查是否有中文内容
                if not self._has_chinese_content(main_tex):
                    return {
                        "success": False,
                        "task_id": "T091",
                        "error": "No Chinese content found in tex files",
                    }

        if not main_tex:
            return {
                "success": False,
                "task_id": "T091",
                "error": "No .tex file found for Chinese compilation",
            }

        # 使用xelatex编译（支持中文）
        result = self._compile_latex(
            tex_file=main_tex,
            engine="xelatex",
            output_name="paper_zh.pdf",
        )

        return {
            "success": result["success"],
            "task_id": "T091",
            "outputs": {
                "tex_file": str(main_tex),
                "output_pdf": result.get("output_pdf"),
                "engine": "xelatex",
                "compilation_log": result.get("log"),
            },
            "error": result.get("error"),
        }

    def _find_main_tex(self, language: str = None) -> Optional[Path]:
        """查找主tex文件"""
        if not self.latex_dir.exists():
            return None

        # 按优先级查找
        candidates = []

        if language == "english":
            candidates = [
                self.latex_dir / "main_en.tex",
                self.latex_dir / "paper_en.tex",
                self.latex_dir / "main.tex",
            ]
        elif language == "chinese":
            candidates = [
                self.latex_dir / "main_zh.tex",
                self.latex_dir / "paper_zh.tex",
                self.latex_dir / "main.tex",
            ]
        else:
            candidates = [
                self.latex_dir / "main.tex",
                self.latex_dir / "paper.tex",
            ]

        for candidate in candidates:
            if candidate.exists():
                return candidate

        # 查找任意tex文件
        for tex_file in self.latex_dir.glob("*.tex"):
            # 排除子文件
            if "_" not in tex_file.stem or tex_file.stem in ["main_en", "main_zh", "paper_en", "paper_zh"]:
                return tex_file

        return None

    def _has_chinese_content(self, tex_file: Path) -> bool:
        """检查文件是否包含中文"""
        try:
            with open(tex_file, "r", encoding="utf-8") as f:
                content = f.read()

            # 简单的中文检测
            for char in content:
                if '\u4e00' <= char <= '\u9fff':
                    return True

            return False
        except Exception:
            return False

    def _compile_latex(
        self,
        tex_file: Path,
        engine: str = "pdflatex",
        output_name: str = None,
        passes: int = 2,
    ) -> Dict:
        """
        执行LaTeX编译

        Args:
            tex_file: tex文件路径
            engine: 编译引擎
            output_name: 输出文件名
            passes: 编译次数（处理引用）

        Returns:
            Dict: 编译结果
        """
        # 检查引擎是否可用
        engine_config = self.ENGINE_CONFIGS.get(engine)
        if not engine_config:
            return {
                "success": False,
                "error": f"Unknown engine: {engine}",
            }

        command = shutil.which(engine_config["command"])
        if not command:
            return {
                "success": False,
                "error": f"LaTeX engine '{engine}' not found. Please install it.",
            }

        # 确保输出目录存在
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 准备输出文件名
        if output_name is None:
            output_name = tex_file.stem + ".pdf"

        output_pdf = self.output_dir / output_name

        # 工作目录
        work_dir = tex_file.parent

        # 编译命令
        cmd = [
            command,
            "-interaction=nonstopmode",
            "-output-directory=" + str(self.output_dir),
            str(tex_file),
        ]

        log_output = []

        try:
            # 多次编译处理引用
            for i in range(passes):
                result = subprocess.run(
                    cmd,
                    cwd=str(work_dir),
                    capture_output=True,
                    text=True,
                    timeout=300,  # 5分钟超时
                )

                log_output.append(f"=== Pass {i+1} ===")
                log_output.append(result.stdout[-2000:] if len(result.stdout) > 2000 else result.stdout)

                if result.returncode != 0 and i == 0:
                    # 第一次编译失败，但继续尝试
                    log_output.append(f"Warning: First pass returned code {result.returncode}")

            # 检查PDF是否生成
            if output_pdf.exists():
                return {
                    "success": True,
                    "output_pdf": str(output_pdf),
                    "log": "\n".join(log_output),
                }
            else:
                # 检查其他位置
                alt_pdf = work_dir / (tex_file.stem + ".pdf")
                if alt_pdf.exists():
                    # 移动到输出目录
                    shutil.move(str(alt_pdf), str(output_pdf))
                    return {
                        "success": True,
                        "output_pdf": str(output_pdf),
                        "log": "\n".join(log_output),
                    }

                return {
                    "success": False,
                    "error": "PDF file was not generated",
                    "log": "\n".join(log_output),
                }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Compilation timed out (300s)",
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    def check_latex_installation(self) -> Dict:
        """检查LaTeX环境"""
        results = {}

        for engine, config in self.ENGINE_CONFIGS.items():
            command = shutil.which(config["command"])
            results[engine] = {
                "installed": command is not None,
                "path": command,
                "supports_chinese": config["supports_chinese"],
            }

        return results

    def get_compilation_status(self) -> Dict:
        """获取编译状态"""
        status = {
            "latex_dir_exists": self.latex_dir.exists(),
            "output_dir_exists": self.output_dir.exists(),
            "tex_files": [],
            "pdf_files": [],
        }

        if self.latex_dir.exists():
            status["tex_files"] = [f.name for f in self.latex_dir.glob("*.tex")]

        if self.output_dir.exists():
            status["pdf_files"] = [f.name for f in self.output_dir.glob("*.pdf")]

        return status

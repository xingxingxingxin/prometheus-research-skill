"""
论文摘要总结工具
================

用于 Phase 1: 文献调研阶段总结论文内容。
使用 Claude AI 生成结构化的论文摘要。
"""

import argparse
import json
import os
import sys
import textwrap
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

try:
    import anthropic
except ImportError:
    print("错误: 请先安装 anthropic 库: pip install anthropic")
    sys.exit(1)


# 默认配置
DEFAULT_MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 4096
TEMPERATURE = 0.3

# PDF 提取相关
try:
    import pypdf
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False


class PaperSummarizer:
    """论文摘要生成器"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        max_tokens: int = MAX_TOKENS,
        temperature: float = TEMPERATURE
    ):
        """
        初始化总结器

        Args:
            api_key: Anthropic API 密钥，如果不提供则从环境变量读取
            model: 使用的模型
            max_tokens: 最大输出 token 数
            temperature: 生成温度
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "未找到 API 密钥。请设置 ANTHROPIC_API_KEY 环境变量，"
                "或在初始化时传入 api_key 参数。"
            )

        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

    def extract_text_from_pdf(self, pdf_path: str, max_pages: int = 50) -> str:
        """
        从 PDF 文件提取文本

        Args:
            pdf_path: PDF 文件路径
            max_pages: 最大提取页数

        Returns:
            提取的文本内容
        """
        if not PDF_SUPPORT:
            raise ImportError(
                "PDF 支持未启用。请安装 pypdf: pip install pypdf"
            )

        text_parts = []

        try:
            with open(pdf_path, 'rb') as f:
                reader = pypdf.PdfReader(f)
                total_pages = len(reader.pages)
                pages_to_read = min(total_pages, max_pages)

                for i in range(pages_to_read):
                    page = reader.pages[i]
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)

                if total_pages > max_pages:
                    text_parts.append(
                        f"\n[注: PDF 共 {total_pages} 页，仅提取前 {max_pages} 页]"
                    )

        except Exception as e:
            raise RuntimeError(f"读取 PDF 失败: {e}")

        return "\n\n".join(text_parts)

    def read_text_file(self, file_path: str) -> str:
        """
        读取文本文件

        Args:
            file_path: 文件路径

        Returns:
            文件内容
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    def read_paper(self, source: str) -> str:
        """
        读取论文内容

        Args:
            source: 论文来源（文件路径或文本内容）

        Returns:
            论文文本内容
        """
        source_path = Path(source)

        # 检查是否为文件路径
        if source_path.exists() and source_path.is_file():
            if source_path.suffix.lower() == '.pdf':
                return self.extract_text_from_pdf(str(source_path))
            else:
                return self.read_text_file(str(source_path))

        # 否则视为原始文本
        return source

    def summarize(
        self,
        paper_content: str,
        title: Optional[str] = None,
        focus_areas: Optional[List[str]] = None,
        detail_level: str = "medium"
    ) -> Dict[str, Any]:
        """
        生成论文摘要

        Args:
            paper_content: 论文文本内容
            title: 论文标题（可选）
            focus_areas: 关注的重点领域（可选）
            detail_level: 详细程度 (brief, medium, detailed)

        Returns:
            结构化摘要
        """
        # 构建提示词
        prompt = self._build_prompt(paper_content, title, focus_areas, detail_level)

        # 调用 API
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            summary_text = message.content[0].text

        except anthropic.APIError as e:
            raise RuntimeError(f"API 调用失败: {e}")

        # 解析结果
        summary = self._parse_summary(summary_text)
        summary["model"] = self.model
        summary["generated_at"] = datetime.now().isoformat()
        summary["detail_level"] = detail_level

        return summary

    def _build_prompt(
        self,
        paper_content: str,
        title: Optional[str],
        focus_areas: Optional[List[str]],
        detail_level: str
    ) -> str:
        """构建提示词"""

        detail_instructions = {
            "brief": "提供一个简洁的摘要，每个部分不超过 2-3 句话。",
            "medium": "提供一个适中的摘要，每个部分 3-5 句话，包含关键细节。",
            "detailed": "提供一个详细的摘要，深入分析每个方面。"
        }

        focus_instruction = ""
        if focus_areas:
            focus_instruction = f"\n请特别关注以下方面: {', '.join(focus_areas)}"

        title_instruction = f"\n论文标题: {title}" if title else ""

        prompt = f"""请分析以下论文内容，生成一个结构化的摘要。

{title_instruction}
{focus_instruction}

详细程度: {detail_instructions.get(detail_level, detail_instructions['medium'])}

请按照以下 JSON 格式输出摘要:

{{
    "title": "论文标题",
    "main_topic": "研究主题（一句话概括）",
    "background": {{
        "problem": "研究问题是什么",
        "motivation": "为什么要研究这个问题",
        "gap": "现有研究的不足"
    }},
    "methodology": {{
        "approach": "采用的方法/框架",
        "key_innovations": ["创新点1", "创新点2"],
        "data": "使用的数据集/实验设置"
    }},
    "results": {{
        "main_findings": ["主要发现1", "主要发现2"],
        "performance": "性能表现（如有）",
        "limitations": "局限性和不足"
    }},
    "contributions": {{
        "theoretical": "理论贡献",
        "practical": "实践贡献",
        "future_directions": ["未来研究方向1", "未来研究方向2"]
    }},
    "relevance_assessment": {{
        "novelty": "创新性评分（1-5）",
        "significance": "重要性评分（1-5）",
        "reproducibility": "可复现性评估"
    }},
    "key_points": ["要点1", "要点2", "要点3", "要点4", "要点5"],
    "citation_suggestion": "如果引用这篇论文，建议引用的关键点"
}}

---

论文内容:

{paper_content}
"""
        return prompt

    def _parse_summary(self, summary_text: str) -> Dict[str, Any]:
        """解析摘要结果"""
        # 尝试提取 JSON 部分
        try:
            # 查找 JSON 块
            start_idx = summary_text.find('{')
            end_idx = summary_text.rfind('}') + 1

            if start_idx != -1 and end_idx > start_idx:
                json_str = summary_text[start_idx:end_idx]
                return json.loads(json_str)
            else:
                # 如果没有找到 JSON，返回原始文本
                return {
                    "raw_text": summary_text,
                    "parse_error": "未找到有效的 JSON 格式"
                }

        except json.JSONDecodeError as e:
            return {
                "raw_text": summary_text,
                "parse_error": str(e)
            }

    def summarize_file(
        self,
        file_path: str,
        output_path: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        总结文件并可选保存结果

        Args:
            file_path: 输入文件路径
            output_path: 输出文件路径（可选）
            **kwargs: 传递给 summarize 的其他参数

        Returns:
            摘要结果
        """
        # 读取文件
        content = self.read_paper(file_path)

        # 生成摘要
        summary = self.summarize(content, **kwargs)

        # 添加源文件信息
        summary["source_file"] = str(file_path)

        # 保存结果
        if output_path:
            self.save_summary(summary, output_path)

        return summary

    def save_summary(self, summary: Dict[str, Any], output_path: str) -> None:
        """保存摘要到文件"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        print(f"摘要已保存到: {output_file}")

    def summarize_batch(
        self,
        file_paths: List[str],
        output_dir: str,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        批量总结论文

        Args:
            file_paths: 文件路径列表
            output_dir: 输出目录
            **kwargs: 其他参数

        Returns:
            摘要列表
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        results = []

        for i, file_path in enumerate(file_paths, 1):
            print(f"[{i}/{len(file_paths)}] 处理: {file_path}")

            try:
                input_file = Path(file_path)
                output_file = output_path / f"{input_file.stem}_summary.json"

                summary = self.summarize_file(
                    file_path,
                    output_path=str(output_file),
                    **kwargs
                )
                summary["status"] = "success"
                results.append(summary)

            except Exception as e:
                print(f"  错误: {e}")
                results.append({
                    "source_file": str(file_path),
                    "status": "error",
                    "error": str(e)
                })

        return results

    def format_summary_markdown(self, summary: Dict[str, Any]) -> str:
        """
        将摘要格式化为 Markdown

        Args:
            summary: 摘要字典

        Returns:
            Markdown 格式的文本
        """
        lines = []

        lines.append(f"# {summary.get('title', '论文摘要')}")
        lines.append("")
        lines.append(f"> 主题: {summary.get('main_topic', '')}")
        lines.append("")

        # 背景
        if 'background' in summary:
            bg = summary['background']
            lines.append("## 研究背景")
            lines.append("")
            if bg.get('problem'):
                lines.append(f"**研究问题**: {bg['problem']}")
            if bg.get('motivation'):
                lines.append(f"**研究动机**: {bg['motivation']}")
            if bg.get('gap'):
                lines.append(f"**研究空白**: {bg['gap']}")
            lines.append("")

        # 方法
        if 'methodology' in summary:
            method = summary['methodology']
            lines.append("## 研究方法")
            lines.append("")
            if method.get('approach'):
                lines.append(f"**方法**: {method['approach']}")
            if method.get('key_innovations'):
                lines.append("**创新点**:")
                for inn in method['key_innovations']:
                    lines.append(f"- {inn}")
            if method.get('data'):
                lines.append(f"**数据**: {method['data']}")
            lines.append("")

        # 结果
        if 'results' in summary:
            results = summary['results']
            lines.append("## 研究结果")
            lines.append("")
            if results.get('main_findings'):
                lines.append("**主要发现**:")
                for finding in results['main_findings']:
                    lines.append(f"- {finding}")
            if results.get('performance'):
                lines.append(f"**性能表现**: {results['performance']}")
            if results.get('limitations'):
                lines.append(f"**局限性**: {results['limitations']}")
            lines.append("")

        # 贡献
        if 'contributions' in summary:
            contrib = summary['contributions']
            lines.append("## 贡献")
            lines.append("")
            if contrib.get('theoretical'):
                lines.append(f"**理论贡献**: {contrib['theoretical']}")
            if contrib.get('practical'):
                lines.append(f"**实践贡献**: {contrib['practical']}")
            if contrib.get('future_directions'):
                lines.append("**未来方向**:")
                for direction in contrib['future_directions']:
                    lines.append(f"- {direction}")
            lines.append("")

        # 关键点
        if summary.get('key_points'):
            lines.append("## 关键要点")
            lines.append("")
            for i, point in enumerate(summary['key_points'], 1):
                lines.append(f"{i}. {point}")
            lines.append("")

        # 引用建议
        if summary.get('citation_suggestion'):
            lines.append("## 引用建议")
            lines.append("")
            lines.append(summary['citation_suggestion'])
            lines.append("")

        # 元信息
        lines.append("---")
        lines.append("")
        lines.append(f"*生成时间: {summary.get('generated_at', '')}*")
        lines.append(f"*模型: {summary.get('model', '')}*")

        return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='论文摘要总结工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 总结单个 PDF
  python paper_summarizer.py paper.pdf -o summary.json

  # 总结文本文件
  python paper_summarizer.py paper.txt -o summary.json

  # 直接输入文本
  python paper_summarizer.py --text "论文摘要内容..." -o summary.json

  # 指定详细程度
  python paper_summarizer.py paper.pdf --detail detailed -o summary.json

  # 批量处理
  python paper_summarizer.py paper1.pdf paper2.pdf --batch --output-dir ./summaries

  # 输出 Markdown 格式
  python paper_summarizer.py paper.pdf --format markdown -o summary.md
        """
    )

    parser.add_argument('files', nargs='*', help='输入文件路径（PDF 或文本）')
    parser.add_argument('--text', '-t', type=str, help='直接输入文本内容')
    parser.add_argument('--output', '-o', type=str, help='输出文件路径')
    parser.add_argument('--output-dir', type=str, help='批量输出目录')
    parser.add_argument('--batch', action='store_true', help='批量处理模式')
    parser.add_argument('--title', type=str, help='论文标题')
    parser.add_argument('--focus', nargs='+', help='关注重点领域')
    parser.add_argument('--detail', '-d',
                        choices=['brief', 'medium', 'detailed'],
                        default='medium',
                        help='详细程度 (默认: medium)')
    parser.add_argument('--format', '-f',
                        choices=['json', 'markdown'],
                        default='json',
                        help='输出格式 (默认: json)')
    parser.add_argument('--model', '-m', type=str, default=DEFAULT_MODEL,
                        help=f'使用的模型 (默认: {DEFAULT_MODEL})')
    parser.add_argument('--api-key', type=str, help='Anthropic API 密钥')
    parser.add_argument('--max-tokens', type=int, default=MAX_TOKENS,
                        help=f'最大输出 token (默认: {MAX_TOKENS})')

    args = parser.parse_args()

    # 初始化总结器
    try:
        summarizer = PaperSummarizer(
            api_key=args.api_key,
            model=args.model,
            max_tokens=args.max_tokens
        )
    except ValueError as e:
        print(f"错误: {e}")
        sys.exit(1)

    # 处理直接输入的文本
    if args.text:
        print("总结文本内容...")
        summary = summarizer.summarize(
            args.text,
            title=args.title,
            focus_areas=args.focus,
            detail_level=args.detail
        )

        if args.output:
            output_file = Path(args.output)
            if args.format == 'markdown':
                content = summarizer.format_summary_markdown(summary)
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(content)
            else:
                summarizer.save_summary(summary, args.output)
        else:
            if args.format == 'markdown':
                print(summarizer.format_summary_markdown(summary))
            else:
                print(json.dumps(summary, indent=2, ensure_ascii=False))

        return

    # 检查输入文件
    if not args.files:
        parser.print_help()
        return

    # 批量处理
    if args.batch or len(args.files) > 1:
        output_dir = args.output_dir or './summaries'
        print(f"批量处理 {len(args.files)} 个文件...")
        print(f"输出目录: {output_dir}")
        print()

        results = summarizer.summarize_batch(
            args.files,
            output_dir,
            title=args.title,
            focus_areas=args.focus,
            detail_level=args.detail
        )

        # 统计结果
        success = sum(1 for r in results if r.get('status') == 'success')
        errors = len(results) - success
        print(f"\n完成: 成功 {success}, 失败 {errors}")

        return

    # 单文件处理
    file_path = args.files[0]
    print(f"总结文件: {file_path}")

    try:
        summary = summarizer.summarize_file(
            file_path,
            title=args.title,
            focus_areas=args.focus,
            detail_level=args.detail
        )

        # 输出结果
        if args.output:
            output_file = Path(args.output)
            if args.format == 'markdown':
                content = summarizer.format_summary_markdown(summary)
                output_file.parent.mkdir(parents=True, exist_ok=True)
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Markdown 摘要已保存到: {output_file}")
            else:
                summarizer.save_summary(summary, args.output)
        else:
            if args.format == 'markdown':
                print()
                print(summarizer.format_summary_markdown(summary))
            else:
                print()
                print(json.dumps(summary, indent=2, ensure_ascii=False))

    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

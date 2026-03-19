"""
Academic Writing Skill - 学术写作技能

LLM辅助的学术写作能力
"""

from typing import Dict, Any, List
from pathlib import Path

from Core.skills.base import LLMAssistedSkill, SkillContext, SkillResult


class AcademicWritingSkill(LLMAssistedSkill):
    """
    学术写作技能

    使用LLM辅助进行学术论文写作
    """

    name = "academic_writing"
    description = "Write academic paper sections with LLM assistance"
    inputs = ["section_type", "content_outline"]
    outputs = ["written_content", "word_count"]

    # 各部分的写作模板
    SECTION_TEMPLATES = {
        "abstract": """Write a concise abstract (150-250 words) for an academic paper.

Key requirements:
- Summarize the research problem, method, results, and conclusions
- Use clear, precise language
- Avoid citations and abbreviations

Content outline:
{outline}

Please write the abstract:""",

        "introduction": """Write the Introduction section for an academic paper.

Structure:
1. Background and motivation
2. Problem statement
3. Research objectives
4. Contributions
5. Paper organization

Content outline:
{outline}

Please write the introduction:""",

        "related_work": """Write the Related Work section for an academic paper.

Structure:
1. Categorize existing work by approach
2. Compare and contrast methods
3. Identify research gaps
4. Position current work

Content outline:
{outline}

Please write the related work section:""",

        "methods": """Write the Methods section for an academic paper.

Requirements:
- Describe the proposed approach in detail
- Explain the rationale behind design choices
- Include mathematical formulations where appropriate

Content outline:
{outline}

Please write the methods section:""",

        "experiments": """Write the Experiments section for an academic paper.

Structure:
1. Experimental setup
2. Datasets
3. Baselines
4. Evaluation metrics
5. Results and analysis

Content outline:
{outline}

Please write the experiments section:""",

        "conclusion": """Write the Conclusion section for an academic paper.

Structure:
1. Summary of contributions
2. Key findings
3. Limitations
4. Future work

Content outline:
{outline}

Please write the conclusion:""",
    }

    def execute(self, context: SkillContext) -> SkillResult:
        """
        执行学术写作

        Args:
            context: 执行上下文

        Returns:
            SkillResult: 写作结果
        """
        import time
        start_time = time.time()

        # 获取输入
        section_type = context.inputs.get("section_type", "introduction")
        outline = context.inputs.get("content_outline", context.inputs.get("outline", ""))

        if not outline:
            return SkillResult(
                success=False,
                error="No content outline provided",
            )

        # 获取模板
        template = self.SECTION_TEMPLATES.get(section_type)
        if not template:
            return SkillResult(
                success=False,
                error=f"Unknown section type: {section_type}",
            )

        # 构建prompt
        prompt = template.format(outline=outline)

        # 添加上下文信息
        if context.metadata.get("title"):
            prompt = f"Paper Title: {context.metadata['title']}\n\n" + prompt

        if context.metadata.get("research_focus"):
            prompt = f"Research Focus: {context.metadata['research_focus']}\n\n" + prompt

        # 获取模型并生成
        try:
            model = self.get_model("writing")
            if model is None:
                return SkillResult(
                    success=False,
                    error="No model available for writing",
                )

            response = model.generate(prompt, max_tokens=4096)

            if not response.success:
                return SkillResult(
                    success=False,
                    error=f"Model generation failed: {response.metadata.get('error', 'Unknown error')}",
                )

            content = response.content
            word_count = len(content.split())

            # 保存结果
            output_file = self._save_content(context, section_type, content)

            execution_time = time.time() - start_time

            return SkillResult(
                success=True,
                outputs={
                    "written_content": content,
                    "word_count": word_count,
                    "section_type": section_type,
                    "output_file": str(output_file),
                },
                artifacts=[str(output_file)],
                llm_calls=1,
                execution_time=execution_time,
            )

        except Exception as e:
            return SkillResult(
                success=False,
                error=str(e),
            )

    def _save_content(self, context: SkillContext, section_type: str, content: str) -> Path:
        """保存写作内容"""
        project_dir = context.working_dir or Path.cwd()
        paper_dir = project_dir / "paper"
        paper_dir.mkdir(parents=True, exist_ok=True)

        output_file = paper_dir / f"{section_type}.md"

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(f"# {section_type.title()}\n\n")
            f.write(content)

        return output_file


# 导出
__all__ = ["AcademicWritingSkill"]

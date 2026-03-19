"""
Semantic Literature Search Skill - 语义文献搜索技能

使用RAG和API进行文献搜索，纯代码执行
"""

from typing import Dict, Any, List
from pathlib import Path

from Core.skills.base import DeterministicSkill, SkillContext, SkillResult


class SemanticLiteratureSearchSkill(DeterministicSkill):
    """
    语义文献搜索技能

    使用向量相似度和学术API搜索相关文献
    """

    name = "semantic_literature_search"
    description = "Search academic papers using semantic similarity and academic APIs"
    inputs = ["query"]
    outputs = ["papers", "search_metadata"]
    mcp_required = ["semantic_scholar", "arxiv"]

    def __init__(self, project_dir: Path = None):
        self.project_dir = project_dir

    def execute(self, context: SkillContext) -> SkillResult:
        """
        执行语义文献搜索

        Args:
            context: 执行上下文

        Returns:
            SkillResult: 搜索结果
        """
        import time
        start_time = time.time()

        # 获取查询
        query = context.inputs.get("query") or context.metadata.get("query")
        if not query:
            return SkillResult(
                success=False,
                error="No query provided for search",
            )

        max_results = context.inputs.get("max_results", 20)

        papers = []

        # 使用学术API搜索
        try:
            api_papers = self._search_apis(query, max_results)
            papers.extend(api_papers)
        except Exception as e:
            return SkillResult(
                success=False,
                error=f"Search failed: {e}",
            )

        # 去重
        papers = self._deduplicate(papers)

        # 保存结果
        output_file = self._save_results(context, papers)

        execution_time = time.time() - start_time

        return SkillResult(
            success=True,
            outputs={
                "papers": papers[:max_results],
                "search_metadata": {
                    "query": query,
                    "total_found": len(papers),
                    "returned": min(len(papers), max_results),
                    "sources": ["semantic_scholar", "arxiv"],
                },
                "output_file": str(output_file),
            },
            artifacts=[str(output_file)],
            execution_time=execution_time,
        )

    def _search_apis(self, query: str, max_results: int) -> List[Dict]:
        """使用学术API搜索"""
        results = []

        # Semantic Scholar
        try:
            from Core.tools.semantic_scholar_search import SemanticScholarSearcher
            searcher = SemanticScholarSearcher()
            s2_papers = searcher.search(query, limit=max_results // 2)
            results.extend(s2_papers)
        except Exception:
            pass

        # arXiv
        try:
            from Core.tools.arxiv_search import ArxivSearcher
            searcher = ArxivSearcher()
            arxiv_papers = searcher.search(query, max_results=max_results // 2)
            results.extend(arxiv_papers)
        except Exception:
            pass

        return results

    def _deduplicate(self, papers: List[Dict]) -> List[Dict]:
        """去重"""
        seen = set()
        unique = []

        for paper in papers:
            # 使用DOI或标题作为唯一键
            key = paper.get("doi") or paper.get("title", "").lower()
            if key not in seen:
                seen.add(key)
                unique.append(paper)

        return unique

    def _save_results(self, context: SkillContext, papers: List[Dict]) -> Path:
        """保存搜索结果"""
        import json

        project_dir = context.working_dir or self.project_dir or Path.cwd()
        output_dir = project_dir / "data" / "search_results"
        output_dir.mkdir(parents=True, exist_ok=True)

        task_id = context.task_id or "search"
        output_file = output_dir / f"{task_id}_semantic_search.json"

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump({
                "task_id": task_id,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "count": len(papers),
                "papers": papers,
            }, f, ensure_ascii=False, indent=2)

        return output_file


# 导出
__all__ = ["SemanticLiteratureSearchSkill"]

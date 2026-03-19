"""
Search Executor - 文献搜索执行器

处理 T005-T010 文献搜索任务，纯代码执行
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import json
import time


class SearchExecutor:
    """
    文献搜索执行器

    执行确定性文献搜索任务，无需LLM
    """

    # 任务ID到搜索类型的映射
    SEARCH_CONFIGS = {
        "T005": {
            "source": "semantic_scholar",
            "description": "Semantic Scholar 核心关键词搜索",
            "limit": 20,
        },
        "T006": {
            "source": "arxiv",
            "description": "arXiv 最新预印本搜索",
            "limit": 15,
        },
        "T007": {
            "source": "semantic_scholar",
            "description": "综述论文搜索",
            "limit": 10,
            "filter": {"publicationType": "Review"},
        },
        "T008": {
            "source": "semantic_scholar",
            "description": "高引用经典论文搜索",
            "limit": 10,
            "sort": "citationCount:desc",
        },
        "T009": {
            "source": "multi",
            "description": "交叉领域论文搜索",
            "limit": 10,
        },
        "T010": {
            "source": "semantic_scholar",
            "description": "最新会议论文搜索",
            "limit": 15,
            "filter": {"year": "2024-"},
        },
    }

    def __init__(self, project_dir: Path = None):
        self.project_dir = project_dir or Path.cwd()
        self._searchers = {}

    def _get_searcher(self, source: str):
        """获取搜索器实例"""
        if source in self._searchers:
            return self._searchers[source]

        if source == "semantic_scholar":
            try:
                import sys
                sys.path.insert(0, str(self.project_dir))
                from Core.tools.semantic_scholar_search import SemanticScholarSearcher
                self._searchers[source] = SemanticScholarSearcher()
            except ImportError:
                self._searchers[source] = self._create_fallback_searcher("semantic_scholar")

        elif source == "arxiv":
            try:
                import sys
                sys.path.insert(0, str(self.project_dir))
                from Core.tools.arxiv_search import ArxivSearcher
                self._searchers[source] = ArxivSearcher()
            except ImportError:
                self._searchers[source] = self._create_fallback_searcher("arxiv")

        else:
            self._searchers[source] = self._create_fallback_searcher(source)

        return self._searchers[source]

    def _create_fallback_searcher(self, source: str):
        """创建降级搜索器（当原搜索器不可用时）"""
        return FallbackSearcher(source)

    def execute(self, task: Dict, context: Dict) -> Dict:
        """
        执行搜索任务

        Args:
            task: 任务字典
            context: 执行上下文

        Returns:
            Dict: 执行结果
        """
        task_id = task.get("id", "")
        config = self.SEARCH_CONFIGS.get(task_id, {})

        # 从上下文获取查询
        query = self._extract_query(task, context)
        if not query:
            return {
                "success": False,
                "error": "No query provided for search",
                "task_id": task_id,
            }

        # 获取搜索源
        source = config.get("source", "semantic_scholar")

        try:
            # 执行搜索
            papers = self._execute_search(
                source=source,
                query=query,
                limit=config.get("limit", 20),
                filters=config.get("filter"),
                sort=config.get("sort"),
            )

            # 保存结果
            output_file = self._save_results(task_id, papers, context)

            return {
                "success": True,
                "task_id": task_id,
                "outputs": {
                    "papers_found": len(papers),
                    "output_file": str(output_file),
                    "source": source,
                },
                "artifacts": [str(output_file)],
            }

        except Exception as e:
            return {
                "success": False,
                "task_id": task_id,
                "error": str(e),
            }

    def _extract_query(self, task: Dict, context: Dict) -> str:
        """从任务或上下文提取查询"""
        # 优先使用任务中的查询
        if "query" in task:
            return task["query"]

        # 从描述中提取
        description = task.get("description", "")
        # 简单提取（实际可以用更复杂的逻辑）

        # 从上下文获取
        if "research_topic" in context:
            return context["research_topic"]

        if "topic" in context:
            return context["topic"]

        return description

    def _execute_search(
        self,
        source: str,
        query: str,
        limit: int = 20,
        filters: Dict = None,
        sort: str = None,
    ) -> List[Dict]:
        """执行搜索"""
        searcher = self._get_searcher(source)

        if source == "semantic_scholar":
            return searcher.search(query, limit=limit)

        elif source == "arxiv":
            return searcher.search(query, max_results=limit)

        elif source == "multi":
            # 多源搜索
            results = []
            for s in ["semantic_scholar", "arxiv"]:
                try:
                    s_results = self._get_searcher(s).search(query, limit=limit // 2)
                    results.extend(s_results)
                except Exception:
                    pass
            return results[:limit]

        return []

    def _save_results(
        self,
        task_id: str,
        papers: List[Dict],
        context: Dict
    ) -> Path:
        """保存搜索结果"""
        # 确定输出目录
        data_dir = self.project_dir / "data" / "search_results"
        data_dir.mkdir(parents=True, exist_ok=True)

        # 生成文件名
        source = self.SEARCH_CONFIGS.get(task_id, {}).get("source", "unknown")
        filename = f"{task_id}_{source}_{int(time.time())}.json"
        output_file = data_dir / filename

        # 保存
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump({
                "task_id": task_id,
                "source": source,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "count": len(papers),
                "papers": papers,
            }, f, ensure_ascii=False, indent=2)

        return output_file


class FallbackSearcher:
    """降级搜索器（当原搜索器不可用时使用）"""

    def __init__(self, source: str):
        self.source = source

    def search(self, query: str, limit: int = 20, **kwargs) -> List[Dict]:
        """返回占位结果"""
        print(f"Warning: Using fallback searcher for {self.source}")
        return [{
            "title": f"[Fallback] Search result for: {query}",
            "source": self.source,
            "note": "Original searcher not available",
        }]

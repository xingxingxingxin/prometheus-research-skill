"""
Semantic Scholar MCP Connector

MCP协议兼容的Semantic Scholar连接器
"""

from typing import Dict, Any, List
import json

from Core.mcp.protocol import MCPConnector, MCPToolDefinition, MCPToolResult, MCPResource


class SemanticScholarMCP(MCPConnector):
    """
    Semantic Scholar MCP连接器

    提供论文搜索和获取功能
    """

    connector_name = "semantic_scholar"
    connector_version = "1.0.0"

    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self._searcher = None

    def _get_searcher(self):
        """获取搜索器实例"""
        if self._searcher is None:
            try:
                import sys
                from pathlib import Path
                # 添加项目路径
                project_root = Path(__file__).parent.parent.parent.parent
                if str(project_root) not in sys.path:
                    sys.path.insert(0, str(project_root))

                from Core.tools.semantic_scholar_search import SemanticScholarSearcher
                self._searcher = SemanticScholarSearcher(api_key=self.api_key)
            except ImportError:
                pass
        return self._searcher

    def get_tools(self) -> List[MCPToolDefinition]:
        """获取工具列表"""
        return [
            MCPToolDefinition(
                name="semantic_scholar_search",
                description="Search academic papers on Semantic Scholar",
                input_schema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results",
                            "default": 20
                        },
                        "year_range": {
                            "type": "string",
                            "description": "Year range filter (e.g., '2020-2024')"
                        },
                        "fields_of_study": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Filter by fields of study"
                        }
                    },
                    "required": ["query"]
                }
            ),
            MCPToolDefinition(
                name="semantic_scholar_get_paper",
                description="Get detailed information about a paper by its Semantic Scholar ID or DOI",
                input_schema={
                    "type": "object",
                    "properties": {
                        "paper_id": {
                            "type": "string",
                            "description": "Semantic Scholar paper ID or DOI"
                        },
                        "include_citations": {
                            "type": "boolean",
                            "description": "Include citation information",
                            "default": False
                        },
                        "include_references": {
                            "type": "boolean",
                            "description": "Include reference information",
                            "default": False
                        }
                    },
                    "required": ["paper_id"]
                }
            ),
            MCPToolDefinition(
                name="semantic_scholar_get_author",
                description="Get author information by Semantic Scholar author ID",
                input_schema={
                    "type": "object",
                    "properties": {
                        "author_id": {
                            "type": "string",
                            "description": "Semantic Scholar author ID"
                        }
                    },
                    "required": ["author_id"]
                }
            ),
            MCPToolDefinition(
                name="semantic_scholar_get_citations",
                description="Get papers that cite a given paper",
                input_schema={
                    "type": "object",
                    "properties": {
                        "paper_id": {
                            "type": "string",
                            "description": "Semantic Scholar paper ID"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of citations",
                            "default": 50
                        }
                    },
                    "required": ["paper_id"]
                }
            ),
        ]

    def execute_tool(self, tool_name: str, arguments: Dict) -> MCPToolResult:
        """执行工具"""
        if tool_name == "semantic_scholar_search":
            return self._search(arguments)
        elif tool_name == "semantic_scholar_get_paper":
            return self._get_paper(arguments)
        elif tool_name == "semantic_scholar_get_author":
            return self._get_author(arguments)
        elif tool_name == "semantic_scholar_get_citations":
            return self._get_citations(arguments)
        else:
            return MCPToolResult.error_result(f"Unknown tool: {tool_name}")

    def _search(self, arguments: Dict) -> MCPToolResult:
        """执行搜索"""
        searcher = self._get_searcher()

        if searcher is None:
            return MCPToolResult.error_result("Semantic Scholar searcher not available")

        try:
            query = arguments.get("query", "")
            limit = arguments.get("limit", 20)

            papers = searcher.search(
                query=query,
                limit=limit,
                year_range=arguments.get("year_range"),
                fields_of_study=arguments.get("fields_of_study"),
            )

            return MCPToolResult.text_result(
                json.dumps(papers, indent=2, ensure_ascii=False)
            )

        except Exception as e:
            return MCPToolResult.error_result(f"Search failed: {e}")

    def _get_paper(self, arguments: Dict) -> MCPToolResult:
        """获取论文详情"""
        searcher = self._get_searcher()

        if searcher is None:
            return MCPToolResult.error_result("Semantic Scholar searcher not available")

        try:
            paper_id = arguments.get("paper_id", "")

            paper = searcher.get_paper(
                paper_id=paper_id,
                include_citations=arguments.get("include_citations", False),
                include_references=arguments.get("include_references", False),
            )

            if paper is None:
                return MCPToolResult.error_result(f"Paper not found: {paper_id}")

            return MCPToolResult.text_result(
                json.dumps(paper, indent=2, ensure_ascii=False)
            )

        except Exception as e:
            return MCPToolResult.error_result(f"Get paper failed: {e}")

    def _get_author(self, arguments: Dict) -> MCPToolResult:
        """获取作者信息"""
        # 简化实现
        return MCPToolResult.text_result(
            json.dumps({"note": "Author lookup not implemented in base searcher"})
        )

    def _get_citations(self, arguments: Dict) -> MCPToolResult:
        """获取引用"""
        searcher = self._get_searcher()

        if searcher is None:
            return MCPToolResult.error_result("Semantic Scholar searcher not available")

        try:
            paper_id = arguments.get("paper_id", "")
            limit = arguments.get("limit", 50)

            citations = searcher.get_citations(paper_id, limit=limit)

            return MCPToolResult.text_result(
                json.dumps(citations, indent=2, ensure_ascii=False)
            )

        except Exception as e:
            return MCPToolResult.error_result(f"Get citations failed: {e}")

"""
arXiv MCP Connector

MCP协议兼容的arXiv连接器
"""

from typing import Dict, Any, List
import json

from Core.mcp.protocol import MCPConnector, MCPToolDefinition, MCPToolResult


class ArxivMCP(MCPConnector):
    """
    arXiv MCP连接器

    提供预印本论文搜索功能
    """

    connector_name = "arxiv"
    connector_version = "1.0.0"

    def __init__(self):
        self._searcher = None

    def _get_searcher(self):
        """获取搜索器实例"""
        if self._searcher is None:
            try:
                from Core.tools.arxiv_search import ArxivSearcher
                self._searcher = ArxivSearcher()
            except ImportError:
                pass
        return self._searcher

    def get_tools(self) -> List[MCPToolDefinition]:
        """获取工具列表"""
        return [
            MCPToolDefinition(
                name="arxiv_search",
                description="Search preprint papers on arXiv",
                input_schema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query"
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of results",
                            "default": 15
                        },
                        "categories": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "arXiv categories (e.g., ['cs.AI', 'cs.LG'])"
                        },
                        "sort_by": {
                            "type": "string",
                            "enum": ["relevance", "lastUpdatedDate", "submittedDate"],
                            "description": "Sort order",
                            "default": "relevance"
                        }
                    },
                    "required": ["query"]
                }
            ),
            MCPToolDefinition(
                name="arxiv_get_paper",
                description="Get paper information by arXiv ID",
                input_schema={
                    "type": "object",
                    "properties": {
                        "arxiv_id": {
                            "type": "string",
                            "description": "arXiv paper ID (e.g., '2301.12345')"
                        }
                    },
                    "required": ["arxiv_id"]
                }
            ),
        ]

    def execute_tool(self, tool_name: str, arguments: Dict) -> MCPToolResult:
        """执行工具"""
        if tool_name == "arxiv_search":
            return self._search(arguments)
        elif tool_name == "arxiv_get_paper":
            return self._get_paper(arguments)
        else:
            return MCPToolResult.error_result(f"Unknown tool: {tool_name}")

    def _search(self, arguments: Dict) -> MCPToolResult:
        """执行搜索"""
        searcher = self._get_searcher()

        if searcher is None:
            return MCPToolResult.error_result("arXiv searcher not available")

        try:
            query = arguments.get("query", "")
            max_results = arguments.get("max_results", 15)

            papers = searcher.search(
                query=query,
                max_results=max_results,
                categories=arguments.get("categories"),
                sort_by=arguments.get("sort_by", "relevance"),
            )

            return MCPToolResult.text_result(
                json.dumps(papers, indent=2, ensure_ascii=False)
            )

        except Exception as e:
            return MCPToolResult.error_result(f"Search failed: {e}")

    def _get_paper(self, arguments: Dict) -> MCPToolResult:
        """获取论文"""
        searcher = self._get_searcher()

        if searcher is None:
            return MCPToolResult.error_result("arXiv searcher not available")

        try:
            arxiv_id = arguments.get("arxiv_id", "")

            paper = searcher.get_paper(arxiv_id)

            if paper is None:
                return MCPToolResult.error_result(f"Paper not found: {arxiv_id}")

            return MCPToolResult.text_result(
                json.dumps(paper, indent=2, ensure_ascii=False)
            )

        except Exception as e:
            return MCPToolResult.error_result(f"Get paper failed: {e}")

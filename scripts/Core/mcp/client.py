"""
MCP Client - MCP客户端

提供统一的MCP调用接口
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import json


class MCPClient:
    """
    MCP客户端

    提供便捷的工具调用接口
    """

    def __init__(self, registry=None):
        """
        初始化客户端

        Args:
            registry: MCP注册表（可选，默认使用全局注册表）
        """
        if registry is None:
            from .protocol import get_mcp_registry
            self.registry = get_mcp_registry()
        else:
            self.registry = registry

    def list_tools(self) -> List[Dict]:
        """列出所有可用工具"""
        all_tools = []
        for connector_name, tools in self.registry.get_all_tools().items():
            for tool in tools:
                all_tools.append({
                    "connector": connector_name,
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.input_schema,
                })
        return all_tools

    def call(self, tool_name: str, **kwargs) -> Dict:
        """
        调用工具

        Args:
            tool_name: 工具名称
            **kwargs: 工具参数

        Returns:
            Dict: 调用结果
        """
        result = self.registry.execute_tool(tool_name, kwargs)

        # 提取文本内容
        text_content = ""
        for block in result.content:
            if block.get("type") == "text":
                text_content += block.get("text", "")

        return {
            "success": not result.is_error,
            "content": text_content,
            "raw": result.to_mcp_format(),
        }

    def search_papers(self, query: str, limit: int = 20, source: str = "semantic_scholar") -> Dict:
        """
        搜索论文的便捷方法

        Args:
            query: 搜索查询
            limit: 结果数量限制
            source: 搜索源

        Returns:
            Dict: 搜索结果
        """
        tool_name = f"{source}_search" if "_" not in source else source

        # 尝试不同的工具名称
        possible_names = [
            "search_papers",
            f"{source}_search",
            "semantic_scholar_search",
            "arxiv_search",
        ]

        for name in possible_names:
            connector_name, _ = self.registry.find_tool(name)
            if connector_name:
                return self.call(name, query=query, limit=limit)

        return {"success": False, "error": f"No search tool found for source: {source}"}

    def get_paper(self, paper_id: str, source: str = "semantic_scholar") -> Dict:
        """
        获取论文详情

        Args:
            paper_id: 论文ID
            source: 数据源

        Returns:
            Dict: 论文信息
        """
        tool_name = f"{source}_get_paper"

        connector_name, _ = self.registry.find_tool(tool_name)
        if connector_name:
            return self.call(tool_name, paper_id=paper_id)

        return {"success": False, "error": f"No get_paper tool found for source: {source}"}

    def read_file(self, file_path: str) -> Dict:
        """
        读取文件

        Args:
            file_path: 文件路径

        Returns:
            Dict: 文件内容
        """
        return self.call("read_file", path=file_path)

    def write_file(self, file_path: str, content: str) -> Dict:
        """
        写入文件

        Args:
            file_path: 文件路径
            content: 文件内容

        Returns:
            Dict: 操作结果
        """
        return self.call("write_file", path=file_path, content=content)

    def list_directory(self, dir_path: str) -> Dict:
        """
        列出目录内容

        Args:
            dir_path: 目录路径

        Returns:
            Dict: 目录内容列表
        """
        return self.call("list_directory", path=dir_path)


class AsyncMCPClient(MCPClient):
    """
    异步MCP客户端

    支持异步调用（需要异步连接器支持）
    """

    async def call_async(self, tool_name: str, **kwargs) -> Dict:
        """异步调用工具"""
        # 当前实现使用同步调用
        # 未来可以扩展为真正的异步
        return self.call(tool_name, **kwargs)

    async def search_papers_async(self, query: str, limit: int = 20, source: str = "semantic_scholar") -> Dict:
        """异步搜索论文"""
        return self.search_papers(query, limit, source)

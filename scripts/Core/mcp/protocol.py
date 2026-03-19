"""
MCP Protocol - Model Context Protocol 实现

遵循 MCP 规范的工具和资源接口
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import json


@dataclass
class MCPToolDefinition:
    """
    MCP工具定义

    遵循 MCP specification 的工具定义格式
    """

    name: str
    description: str
    input_schema: Dict[str, Any]  # JSON Schema

    def to_mcp_format(self) -> Dict:
        """转换为MCP格式"""
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "MCPToolDefinition":
        """从字典创建"""
        return cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            input_schema=data.get("inputSchema", data.get("input_schema", {})),
        )


@dataclass
class MCPToolResult:
    """
    MCP工具执行结果
    """

    content: List[Dict[str, Any]]  # Content blocks
    is_error: bool = False

    def to_mcp_format(self) -> Dict:
        """转换为MCP格式"""
        return {
            "content": self.content,
            "isError": self.is_error,
        }

    @classmethod
    def text_result(cls, text: str, is_error: bool = False) -> "MCPToolResult":
        """创建文本结果"""
        return cls(
            content=[{"type": "text", "text": text}],
            is_error=is_error,
        )

    @classmethod
    def error_result(cls, error_message: str) -> "MCPToolResult":
        """创建错误结果"""
        return cls.text_result(error_message, is_error=True)


@dataclass
class MCPResource:
    """
    MCP资源定义
    """

    uri: str
    name: str
    description: str = ""
    mime_type: str = "text/plain"

    def to_mcp_format(self) -> Dict:
        return {
            "uri": self.uri,
            "name": self.name,
            "description": self.description,
            "mimeType": self.mime_type,
        }


class MCPConnector(ABC):
    """
    MCP连接器基类

    实现此接口以创建MCP兼容的工具连接器
    """

    # 子类应该定义的属性
    connector_name: str = "base"
    connector_version: str = "1.0.0"

    @abstractmethod
    def get_tools(self) -> List[MCPToolDefinition]:
        """
        获取可用工具列表

        Returns:
            List[MCPToolDefinition]: 工具定义列表
        """
        pass

    @abstractmethod
    def execute_tool(self, tool_name: str, arguments: Dict) -> MCPToolResult:
        """
        执行工具调用

        Args:
            tool_name: 工具名称
            arguments: 工具参数

        Returns:
            MCPToolResult: 执行结果
        """
        pass

    def get_resources(self) -> List[MCPResource]:
        """
        获取可用资源列表

        Returns:
            List[MCPResource]: 资源列表
        """
        return []

    def read_resource(self, uri: str) -> str:
        """
        读取资源内容

        Args:
            uri: 资源URI

        Returns:
            str: 资源内容
        """
        raise NotImplementedError(f"Resource reading not supported: {uri}")

    def get_connector_info(self) -> Dict:
        """获取连接器信息"""
        return {
            "name": self.connector_name,
            "version": self.connector_version,
            "tools": [t.name for t in self.get_tools()],
            "resources": [r.uri for r in self.get_resources()],
        }


class MCPRegistry:
    """
    MCP连接器注册表

    管理所有MCP连接器
    """

    def __init__(self):
        self._connectors: Dict[str, MCPConnector] = {}

    def register(self, connector: MCPConnector):
        """注册连接器"""
        self._connectors[connector.connector_name] = connector

    def unregister(self, name: str):
        """注销连接器"""
        self._connectors.pop(name, None)

    def get_connector(self, name: str) -> Optional[MCPConnector]:
        """获取连接器"""
        return self._connectors.get(name)

    def list_connectors(self) -> List[str]:
        """列出所有连接器"""
        return list(self._connectors.keys())

    def get_all_tools(self) -> Dict[str, List[MCPToolDefinition]]:
        """获取所有连接器的工具"""
        return {
            name: connector.get_tools()
            for name, connector in self._connectors.items()
        }

    def find_tool(self, tool_name: str) -> tuple:
        """
        查找工具

        Args:
            tool_name: 工具名称

        Returns:
            tuple: (connector_name, tool_definition) 或 (None, None)
        """
        for name, connector in self._connectors.items():
            for tool in connector.get_tools():
                if tool.name == tool_name:
                    return name, tool
        return None, None

    def execute_tool(self, tool_name: str, arguments: Dict) -> MCPToolResult:
        """
        执行工具（自动查找连接器）

        Args:
            tool_name: 工具名称
            arguments: 工具参数

        Returns:
            MCPToolResult: 执行结果
        """
        connector_name, _ = self.find_tool(tool_name)

        if connector_name is None:
            return MCPToolResult.error_result(f"Tool not found: {tool_name}")

        connector = self._connectors[connector_name]
        return connector.execute_tool(tool_name, arguments)


# 全局注册表
_registry: Optional[MCPRegistry] = None


def get_mcp_registry() -> MCPRegistry:
    """获取全局MCP注册表"""
    global _registry
    if _registry is None:
        _registry = MCPRegistry()
        _load_builtin_connectors(_registry)
    return _registry


def _load_builtin_connectors(registry: MCPRegistry):
    """加载内置连接器"""
    # 加载 Semantic Scholar 连接器
    try:
        from .connectors.semantic_scholar import SemanticScholarMCP
        registry.register(SemanticScholarMCP())
    except ImportError:
        pass

    # 加载 arXiv 连接器
    try:
        from .connectors.arxiv import ArxivMCP
        registry.register(ArxivMCP())
    except ImportError:
        pass

    # 加载文件系统连接器
    try:
        from .connectors.filesystem import FilesystemMCP
        registry.register(FilesystemMCP())
    except ImportError:
        pass

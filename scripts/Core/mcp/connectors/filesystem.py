"""
Filesystem MCP Connector

MCP协议兼容的文件系统连接器
"""

from typing import Dict, Any, List
from pathlib import Path
import json
import os

from Core.mcp.protocol import MCPConnector, MCPToolDefinition, MCPToolResult, MCPResource


class FilesystemMCP(MCPConnector):
    """
    文件系统MCP连接器

    提供文件读写操作
    """

    connector_name = "filesystem"
    connector_version = "1.0.0"

    def __init__(self, allowed_paths: List[str] = None):
        """
        初始化

        Args:
            allowed_paths: 允许访问的路径列表
        """
        self.allowed_paths = allowed_paths or ["."]

    def _resolve_path(self, path: str) -> Path:
        """解析并验证路径"""
        p = Path(path).resolve()

        # 检查是否在允许的路径内
        allowed = False
        for allowed_path in self.allowed_paths:
            allowed_p = Path(allowed_path).resolve()
            try:
                p.relative_to(allowed_p)
                allowed = True
                break
            except ValueError:
                pass

        if not allowed:
            raise PermissionError(f"Access denied: {path}")

        return p

    def get_tools(self) -> List[MCPToolDefinition]:
        """获取工具列表"""
        return [
            MCPToolDefinition(
                name="read_file",
                description="Read content from a file",
                input_schema={
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "File path to read"
                        },
                        "encoding": {
                            "type": "string",
                            "description": "File encoding",
                            "default": "utf-8"
                        }
                    },
                    "required": ["path"]
                }
            ),
            MCPToolDefinition(
                name="write_file",
                description="Write content to a file",
                input_schema={
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "File path to write"
                        },
                        "content": {
                            "type": "string",
                            "description": "Content to write"
                        },
                        "encoding": {
                            "type": "string",
                            "description": "File encoding",
                            "default": "utf-8"
                        },
                        "mode": {
                            "type": "string",
                            "enum": ["write", "append"],
                            "description": "Write mode",
                            "default": "write"
                        }
                    },
                    "required": ["path", "content"]
                }
            ),
            MCPToolDefinition(
                name="list_directory",
                description="List contents of a directory",
                input_schema={
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Directory path"
                        },
                        "pattern": {
                            "type": "string",
                            "description": "Glob pattern to filter files"
                        }
                    },
                    "required": ["path"]
                }
            ),
            MCPToolDefinition(
                name="create_directory",
                description="Create a new directory",
                input_schema={
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Directory path to create"
                        }
                    },
                    "required": ["path"]
                }
            ),
            MCPToolDefinition(
                name="delete_file",
                description="Delete a file",
                input_schema={
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "File path to delete"
                        }
                    },
                    "required": ["path"]
                }
            ),
            MCPToolDefinition(
                name="file_exists",
                description="Check if a file or directory exists",
                input_schema={
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Path to check"
                        }
                    },
                    "required": ["path"]
                }
            ),
            MCPToolDefinition(
                name="get_file_info",
                description="Get file metadata (size, modified time, etc.)",
                input_schema={
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "File path"
                        }
                    },
                    "required": ["path"]
                }
            ),
        ]

    def get_resources(self) -> List[MCPResource]:
        """获取资源列表"""
        resources = []

        for allowed_path in self.allowed_paths:
            p = Path(allowed_path)
            if p.exists():
                resources.append(MCPResource(
                    uri=f"file://{p.absolute()}",
                    name=f"Directory: {p.name}",
                    description=f"Allowed directory: {p}",
                    mime_type="inode/directory",
                ))

        return resources

    def execute_tool(self, tool_name: str, arguments: Dict) -> MCPToolResult:
        """执行工具"""
        try:
            if tool_name == "read_file":
                return self._read_file(arguments)
            elif tool_name == "write_file":
                return self._write_file(arguments)
            elif tool_name == "list_directory":
                return self._list_directory(arguments)
            elif tool_name == "create_directory":
                return self._create_directory(arguments)
            elif tool_name == "delete_file":
                return self._delete_file(arguments)
            elif tool_name == "file_exists":
                return self._file_exists(arguments)
            elif tool_name == "get_file_info":
                return self._get_file_info(arguments)
            else:
                return MCPToolResult.error_result(f"Unknown tool: {tool_name}")

        except PermissionError as e:
            return MCPToolResult.error_result(str(e))
        except Exception as e:
            return MCPToolResult.error_result(f"Operation failed: {e}")

    def _read_file(self, arguments: Dict) -> MCPToolResult:
        """读取文件"""
        path = self._resolve_path(arguments.get("path", ""))
        encoding = arguments.get("encoding", "utf-8")

        if not path.exists():
            return MCPToolResult.error_result(f"File not found: {path}")

        if not path.is_file():
            return MCPToolResult.error_result(f"Not a file: {path}")

        with open(path, "r", encoding=encoding) as f:
            content = f.read()

        return MCPToolResult.text_result(content)

    def _write_file(self, arguments: Dict) -> MCPToolResult:
        """写入文件"""
        path = self._resolve_path(arguments.get("path", ""))
        content = arguments.get("content", "")
        encoding = arguments.get("encoding", "utf-8")
        mode = arguments.get("mode", "write")

        # 确保父目录存在
        path.parent.mkdir(parents=True, exist_ok=True)

        write_mode = "a" if mode == "append" else "w"

        with open(path, write_mode, encoding=encoding) as f:
            f.write(content)

        return MCPToolResult.text_result(f"Successfully wrote to {path}")

    def _list_directory(self, arguments: Dict) -> MCPToolResult:
        """列出目录"""
        path = self._resolve_path(arguments.get("path", ""))
        pattern = arguments.get("pattern", "*")

        if not path.exists():
            return MCPToolResult.error_result(f"Directory not found: {path}")

        if not path.is_dir():
            return MCPToolResult.error_result(f"Not a directory: {path}")

        items = []
        for item in path.glob(pattern):
            items.append({
                "name": item.name,
                "type": "directory" if item.is_dir() else "file",
                "size": item.stat().st_size if item.is_file() else None,
            })

        return MCPToolResult.text_result(
            json.dumps(items, indent=2)
        )

    def _create_directory(self, arguments: Dict) -> MCPToolResult:
        """创建目录"""
        path = self._resolve_path(arguments.get("path", ""))

        path.mkdir(parents=True, exist_ok=True)

        return MCPToolResult.text_result(f"Successfully created directory: {path}")

    def _delete_file(self, arguments: Dict) -> MCPToolResult:
        """删除文件"""
        path = self._resolve_path(arguments.get("path", ""))

        if not path.exists():
            return MCPToolResult.error_result(f"File not found: {path}")

        if path.is_dir():
            path.rmdir()
        else:
            path.unlink()

        return MCPToolResult.text_result(f"Successfully deleted: {path}")

    def _file_exists(self, arguments: Dict) -> MCPToolResult:
        """检查文件是否存在"""
        path = self._resolve_path(arguments.get("path", ""))

        result = {
            "exists": path.exists(),
            "is_file": path.is_file() if path.exists() else False,
            "is_directory": path.is_dir() if path.exists() else False,
            "path": str(path),
        }

        return MCPToolResult.text_result(json.dumps(result))

    def _get_file_info(self, arguments: Dict) -> MCPToolResult:
        """获取文件信息"""
        path = self._resolve_path(arguments.get("path", ""))

        if not path.exists():
            return MCPToolResult.error_result(f"File not found: {path}")

        stat = path.stat()

        info = {
            "path": str(path),
            "name": path.name,
            "size": stat.st_size,
            "modified": stat.st_mtime,
            "is_file": path.is_file(),
            "is_directory": path.is_dir(),
            "extension": path.suffix,
        }

        return MCPToolResult.text_result(json.dumps(info, indent=2))

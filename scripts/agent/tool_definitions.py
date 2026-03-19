#!/usr/bin/env python3
"""
Project Prometheus - Tool Definitions
======================================

This module defines all tools available to the Prometheus agent.
It provides:
- Wrappers around existing Core tools for agent use
- New tools for agent-specific operations
- Tool schema definitions for API integration
- Tool execution and validation

Categories:
- file: File system operations
- search: Literature and web search
- analysis: Data analysis and statistics
- code: Code execution and management
- git: Version control operations
- state: State and task management
- communication: Reporting and messaging
- knowledge: Knowledge base operations

Usage:
    from agent.tool_definitions import (
        ToolDefinition, ToolRegistry, register_all_tools,
        get_tool_registry, execute_tool
    )

    # Get the global registry
    registry = get_tool_registry()

    # Register all built-in tools
    register_all_tools()

    # Execute a tool
    result = execute_tool("semantic_scholar_search", query="transformer", max_results=10)
"""

import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Type, Union

# Add Core directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "Core"))


# ============================================================================
# Tool Schema Definitions
# ============================================================================

@dataclass
class ParameterSchema:
    """Schema definition for a tool parameter."""
    name: str
    type: str  # "string", "integer", "number", "boolean", "array", "object"
    description: str
    required: bool = True
    default: Any = None
    enum: Optional[List[str]] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    pattern: Optional[str] = None  # Regex pattern for strings

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for API."""
        result = {
            "type": self.type,
            "description": self.description
        }
        if self.enum:
            result["enum"] = self.enum
        if self.min_value is not None:
            result["minimum"] = self.min_value
        if self.max_value is not None:
            result["maximum"] = self.max_value
        if self.pattern:
            result["pattern"] = self.pattern
        return result


@dataclass
class ToolDefinition:
    """Definition of a tool available to the agent."""

    name: str
    description: str
    parameters: List[ParameterSchema]
    category: str
    implementation: Optional[Callable] = None
    returns: str = "JSON object with results"
    examples: List[str] = field(default_factory=list)
    version: str = "1.0.0"
    requires_auth: bool = False
    dangerous: bool = False  # Flag for potentially harmful operations
    sandbox_safe: bool = True  # Can be run in sandboxed environment

    def to_schema(self) -> Dict[str, Any]:
        """Convert to JSON schema format for API."""
        properties = {}
        required = []

        for param in self.parameters:
            properties[param.name] = param.to_dict()
            if param.required:
                required.append(param.name)

        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required
            },
            "returns": self.returns,
            "category": self.category,
            "dangerous": self.dangerous
        }

    def validate_parameters(self, **kwargs) -> tuple[bool, Optional[str]]:
        """
        Validate provided parameters against schema.

        Returns:
            Tuple of (is_valid, error_message)
        """
        param_names = {p.name for p in self.parameters}
        param_map = {p.name: p for p in self.parameters}

        # Check required parameters
        for param in self.parameters:
            if param.required and param.name not in kwargs:
                return False, f"Missing required parameter: {param.name}"

        # Validate provided parameters
        for key, value in kwargs.items():
            if key not in param_names:
                return False, f"Unknown parameter: {key}"

            param = param_map[key]
            expected_type = param.type

            # Type validation
            if value is not None:
                type_valid = self._validate_type(value, expected_type, param)
                if not type_valid:
                    return False, f"Invalid type for {key}: expected {expected_type}"

            # Enum validation
            if param.enum and value not in param.enum:
                return False, f"Invalid value for {key}: must be one of {param.enum}"

            # Range validation
            if param.min_value is not None and isinstance(value, (int, float)):
                if value < param.min_value:
                    return False, f"Value for {key} below minimum: {param.min_value}"

            if param.max_value is not None and isinstance(value, (int, float)):
                if value > param.max_value:
                    return False, f"Value for {key} above maximum: {param.max_value}"

        return True, None

    def _validate_type(self, value: Any, expected_type: str, param: ParameterSchema) -> bool:
        """Validate value against expected type."""
        type_mapping = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "array": list,
            "object": dict
        }

        expected = type_mapping.get(expected_type)
        if expected is None:
            return True  # Unknown type, skip validation

        # Special case: integer should also accept float that equals an integer
        if expected_type == "integer" and isinstance(value, float):
            return value == int(value)

        return isinstance(value, expected)


# ============================================================================
# Tool Registry
# ============================================================================

class ToolRegistry:
    """Registry for all available tools."""

    def __init__(self):
        """Initialize the tool registry."""
        self._tools: Dict[str, ToolDefinition] = {}
        self._categories: Dict[str, List[str]] = {}

    def register(self, tool: ToolDefinition) -> None:
        """
        Register a tool definition.

        Args:
            tool: ToolDefinition to register
        """
        if tool.name in self._tools:
            raise ValueError(f"Tool already registered: {tool.name}")

        self._tools[tool.name] = tool
        self._categories.setdefault(tool.category, []).append(tool.name)

    def unregister(self, name: str) -> bool:
        """
        Unregister a tool.

        Args:
            name: Tool name to unregister

        Returns:
            True if tool was removed, False if not found
        """
        if name in self._tools:
            tool = self._tools.pop(name)
            if tool.category in self._categories:
                self._categories[tool.category].remove(name)
            return True
        return False

    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """
        Get a tool by name.

        Args:
            name: Tool name

        Returns:
            ToolDefinition or None if not found
        """
        return self._tools.get(name)

    def list_tools(self, category: Optional[str] = None) -> List[ToolDefinition]:
        """
        List all registered tools.

        Args:
            category: Optional category filter

        Returns:
            List of ToolDefinitions
        """
        if category:
            tool_names = self._categories.get(category, [])
            return [self._tools[name] for name in tool_names if name in self._tools]
        return list(self._tools.values())

    def list_categories(self) -> List[str]:
        """Get all tool categories."""
        return list(self._categories.keys())

    def get_schemas(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get JSON schemas for tools.

        Args:
            category: Optional category filter

        Returns:
            List of tool schemas
        """
        return [tool.to_schema() for tool in self.list_tools(category)]

    def execute(self, name: str, **kwargs) -> Dict[str, Any]:
        """
        Execute a tool with given parameters.

        Args:
            name: Tool name
            **kwargs: Tool parameters

        Returns:
            Dictionary with execution results
        """
        tool = self.get_tool(name)
        if not tool:
            return {
                "success": False,
                "error": f"Tool not found: {name}",
                "output": None
            }

        # Validate parameters
        is_valid, error = tool.validate_parameters(**kwargs)
        if not is_valid:
            return {
                "success": False,
                "error": error,
                "output": None
            }

        # Execute implementation
        if tool.implementation is None:
            return {
                "success": False,
                "error": f"No implementation for tool: {name}",
                "output": None
            }

        try:
            result = tool.implementation(**kwargs)
            return {
                "success": True,
                "error": None,
                "output": result,
                "tool": name,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "output": None,
                "tool": name,
                "timestamp": datetime.now().isoformat()
            }


# Global registry instance
_global_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """Get the global tool registry."""
    global _global_registry
    if _global_registry is None:
        _global_registry = ToolRegistry()
    return _global_registry


def execute_tool(name: str, **kwargs) -> Dict[str, Any]:
    """
    Execute a tool using the global registry.

    Args:
        name: Tool name
        **kwargs: Tool parameters

    Returns:
        Execution result dictionary
    """
    return get_tool_registry().execute(name, **kwargs)


# ============================================================================
# Tool Implementations
# ============================================================================

def _create_file_tools() -> List[ToolDefinition]:
    """Create file operation tool definitions."""

    def read_file(path: str, encoding: str = "utf-8") -> Dict[str, Any]:
        """Read file contents."""
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        if not file_path.is_file():
            raise ValueError(f"Not a file: {path}")

        content = file_path.read_text(encoding=encoding)
        return {
            "path": str(file_path.absolute()),
            "content": content,
            "size": len(content),
            "lines": content.count('\n') + 1
        }

    def write_file(path: str, content: str, encoding: str = "utf-8", create_dirs: bool = True) -> Dict[str, Any]:
        """Write content to file."""
        file_path = Path(path)
        existed = file_path.exists()
        if create_dirs:
            file_path.parent.mkdir(parents=True, exist_ok=True)

        file_path.write_text(content, encoding=encoding)
        return {
            "path": str(file_path.absolute()),
            "size": len(content),
            "lines": content.count('\n') + 1,
            "created": not existed
        }

    def list_directory(path: str, pattern: str = "*", recursive: bool = False) -> Dict[str, Any]:
        """List directory contents."""
        dir_path = Path(path)
        if not dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {path}")
        if not dir_path.is_dir():
            raise ValueError(f"Not a directory: {path}")

        if recursive:
            items = list(dir_path.rglob(pattern))
        else:
            items = list(dir_path.glob(pattern))

        files = []
        dirs = []
        for item in items:
            if item.is_file():
                stat = item.stat()
                files.append({
                    "name": item.name,
                    "path": str(item.relative_to(dir_path)),
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
            elif item.is_dir():
                dirs.append({
                    "name": item.name,
                    "path": str(item.relative_to(dir_path))
                })

        return {
            "path": str(dir_path.absolute()),
            "files": files,
            "directories": dirs,
            "total_files": len(files),
            "total_directories": len(dirs)
        }

    def delete_file(path: str, confirm: bool = False) -> Dict[str, Any]:
        """Delete a file."""
        if not confirm:
            raise ValueError("Deletion requires confirm=True parameter")

        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        file_path.unlink()
        return {"deleted": str(file_path.absolute())}

    def copy_file(source: str, destination: str, create_dirs: bool = True) -> Dict[str, Any]:
        """Copy a file."""
        import shutil
        src = Path(source)
        dst = Path(destination)

        if not src.exists():
            raise FileNotFoundError(f"Source not found: {source}")

        if create_dirs:
            dst.parent.mkdir(parents=True, exist_ok=True)

        shutil.copy2(src, dst)
        return {
            "source": str(src.absolute()),
            "destination": str(dst.absolute()),
            "size": dst.stat().st_size
        }

    def move_file(source: str, destination: str, create_dirs: bool = True) -> Dict[str, Any]:
        """Move a file."""
        import shutil
        src = Path(source)
        dst = Path(destination)

        if not src.exists():
            raise FileNotFoundError(f"Source not found: {source}")

        if create_dirs:
            dst.parent.mkdir(parents=True, exist_ok=True)

        shutil.move(str(src), str(dst))
        return {
            "source": str(src),
            "destination": str(dst.absolute())
        }

    def search_in_files(path: str, pattern: str, file_pattern: str = "*", recursive: bool = True) -> Dict[str, Any]:
        """Search for pattern in files."""
        import re
        dir_path = Path(path)

        if recursive:
            files = list(dir_path.rglob(file_pattern))
        else:
            files = list(dir_path.glob(file_pattern))

        results = []
        regex = re.compile(pattern, re.IGNORECASE)

        for file_path in files:
            if not file_path.is_file():
                continue
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                for i, line in enumerate(content.split('\n'), 1):
                    if regex.search(line):
                        results.append({
                            "file": str(file_path.relative_to(dir_path)),
                            "line": i,
                            "content": line.strip()[:200]
                        })
            except Exception:
                continue

        return {
            "pattern": pattern,
            "path": str(dir_path.absolute()),
            "matches": results[:100],  # Limit results
            "total_matches": len(results)
        }

    return [
        ToolDefinition(
            name="read_file",
            description="Read the contents of a file from the filesystem",
            parameters=[
                ParameterSchema("path", "string", "Path to the file to read", required=True),
                ParameterSchema("encoding", "string", "File encoding", required=False, default="utf-8")
            ],
            category="file",
            implementation=read_file,
            returns="File content and metadata",
            examples=['read_file(path="README.md")'],
            sandbox_safe=True
        ),
        ToolDefinition(
            name="write_file",
            description="Write content to a file, creating it if it doesn't exist",
            parameters=[
                ParameterSchema("path", "string", "Path to write the file", required=True),
                ParameterSchema("content", "string", "Content to write", required=True),
                ParameterSchema("encoding", "string", "File encoding", required=False, default="utf-8"),
                ParameterSchema("create_dirs", "boolean", "Create parent directories if needed", required=False, default=True)
            ],
            category="file",
            implementation=write_file,
            returns="File metadata after write",
            examples=['write_file(path="output.txt", content="Hello World")'],
            sandbox_safe=True
        ),
        ToolDefinition(
            name="list_directory",
            description="List contents of a directory",
            parameters=[
                ParameterSchema("path", "string", "Directory path", required=True),
                ParameterSchema("pattern", "string", "Glob pattern to filter files", required=False, default="*"),
                ParameterSchema("recursive", "boolean", "Search recursively", required=False, default=False)
            ],
            category="file",
            implementation=list_directory,
            returns="List of files and directories",
            examples=['list_directory(path="src", pattern="*.py")'],
            sandbox_safe=True
        ),
        ToolDefinition(
            name="delete_file",
            description="Delete a file from the filesystem",
            parameters=[
                ParameterSchema("path", "string", "Path to file to delete", required=True),
                ParameterSchema("confirm", "boolean", "Must be true to confirm deletion", required=True)
            ],
            category="file",
            implementation=delete_file,
            returns="Deletion confirmation",
            examples=['delete_file(path="temp.txt", confirm=True)'],
            dangerous=True,
            sandbox_safe=False
        ),
        ToolDefinition(
            name="copy_file",
            description="Copy a file to a new location",
            parameters=[
                ParameterSchema("source", "string", "Source file path", required=True),
                ParameterSchema("destination", "string", "Destination file path", required=True),
                ParameterSchema("create_dirs", "boolean", "Create parent directories if needed", required=False, default=True)
            ],
            category="file",
            implementation=copy_file,
            returns="Copy operation result",
            examples=['copy_file(source="a.txt", destination="b.txt")'],
            sandbox_safe=True
        ),
        ToolDefinition(
            name="move_file",
            description="Move a file to a new location",
            parameters=[
                ParameterSchema("source", "string", "Source file path", required=True),
                ParameterSchema("destination", "string", "Destination file path", required=True),
                ParameterSchema("create_dirs", "boolean", "Create parent directories if needed", required=False, default=True)
            ],
            category="file",
            implementation=move_file,
            returns="Move operation result",
            examples=['move_file(source="old.txt", destination="new.txt")'],
            sandbox_safe=False
        ),
        ToolDefinition(
            name="search_in_files",
            description="Search for a regex pattern in files",
            parameters=[
                ParameterSchema("path", "string", "Directory to search in", required=True),
                ParameterSchema("pattern", "string", "Regex pattern to search for", required=True),
                ParameterSchema("file_pattern", "string", "Glob pattern for files to search", required=False, default="*"),
                ParameterSchema("recursive", "boolean", "Search recursively", required=False, default=True)
            ],
            category="file",
            implementation=search_in_files,
            returns="List of matches",
            examples=['search_in_files(path="src", pattern="TODO", file_pattern="*.py")'],
            sandbox_safe=True
        )
    ]


def _create_search_tools() -> List[ToolDefinition]:
    """Create search tool definitions."""

    def semantic_scholar_search(query: str, max_results: int = 50, year_start: Optional[int] = None,
                                 year_end: Optional[int] = None, open_access_only: bool = False) -> Dict[str, Any]:
        """Search Semantic Scholar for papers."""
        try:
            from tools.semantic_scholar_search import SemanticScholarSearcher
            searcher = SemanticScholarSearcher()

            year_range = None
            if year_start or year_end:
                year_range = (year_start or 1900, year_end or datetime.now().year)

            papers = searcher.search(
                query=query,
                max_results=max_results,
                year_range=year_range,
                open_access_only=open_access_only
            )

            return {
                "query": query,
                "total_results": len(papers),
                "papers": papers
            }
        except ImportError:
            return {"error": "semantic_scholar_search module not available", "papers": []}

    def arxiv_search(query: str, max_results: int = 50, category: Optional[str] = None) -> Dict[str, Any]:
        """Search arXiv for papers."""
        try:
            from tools.arxiv_search import ArxivSearcher
            searcher = ArxivSearcher()

            papers = searcher.search(
                query=query,
                max_results=max_results,
                category=category
            )

            return {
                "query": query,
                "total_results": len(papers),
                "papers": papers
            }
        except ImportError:
            return {"error": "arxiv_search module not available", "papers": []}

    def google_scholar_search(query: str, max_results: int = 20) -> Dict[str, Any]:
        """Search Google Scholar for papers."""
        try:
            from tools.google_scholar_search import GoogleScholarSearcher
            searcher = GoogleScholarSearcher()

            papers = searcher.search(query=query, max_results=max_results)

            return {
                "query": query,
                "total_results": len(papers),
                "papers": papers
            }
        except ImportError:
            return {"error": "google_scholar_search module not available", "papers": []}

    return [
        ToolDefinition(
            name="semantic_scholar_search",
            description="Search Semantic Scholar academic database for research papers",
            parameters=[
                ParameterSchema("query", "string", "Search query keywords", required=True),
                ParameterSchema("max_results", "integer", "Maximum number of results", required=False, default=50, min_value=1, max_value=500),
                ParameterSchema("year_start", "integer", "Start year for papers", required=False),
                ParameterSchema("year_end", "integer", "End year for papers", required=False),
                ParameterSchema("open_access_only", "boolean", "Only return open access papers", required=False, default=False)
            ],
            category="search",
            implementation=semantic_scholar_search,
            returns="List of papers with metadata",
            examples=['semantic_scholar_search(query="transformer neural network", max_results=20)'],
            requires_auth=False
        ),
        ToolDefinition(
            name="arxiv_search",
            description="Search arXiv preprint server for research papers",
            parameters=[
                ParameterSchema("query", "string", "Search query", required=True),
                ParameterSchema("max_results", "integer", "Maximum number of results", required=False, default=50, min_value=1, max_value=500),
                ParameterSchema("category", "string", "arXiv category filter (e.g., cs.AI, cs.LG)", required=False)
            ],
            category="search",
            implementation=arxiv_search,
            returns="List of arXiv papers",
            examples=['arxiv_search(query="attention mechanism", category="cs.LG")'],
            requires_auth=False
        ),
        ToolDefinition(
            name="google_scholar_search",
            description="Search Google Scholar for academic papers (rate limited)",
            parameters=[
                ParameterSchema("query", "string", "Search query", required=True),
                ParameterSchema("max_results", "integer", "Maximum number of results", required=False, default=20, min_value=1, max_value=100)
            ],
            category="search",
            implementation=google_scholar_search,
            returns="List of papers with citation counts",
            examples=['google_scholar_search(query="deep learning survey")'],
            requires_auth=False
        )
    ]


def _create_analysis_tools() -> List[ToolDefinition]:
    """Create analysis tool definitions."""

    def statistical_test(data_file: str, test_type: str, alpha: float = 0.05) -> Dict[str, Any]:
        """Perform statistical significance tests."""
        try:
            from tools.statistical_test import StatisticalTester
            tester = StatisticalTester()

            result = tester.run_test(
                data_file=data_file,
                test_type=test_type,
                alpha=alpha
            )

            return result
        except ImportError:
            return {"error": "statistical_test module not available"}

    def visualize_results(data_file: str, plot_type: str, output_file: str,
                          title: Optional[str] = None, x_label: Optional[str] = None,
                          y_label: Optional[str] = None) -> Dict[str, Any]:
        """Generate visualization plots from data."""
        try:
            from tools.result_visualizer import ResultVisualizer
            visualizer = ResultVisualizer()

            result = visualizer.create_plot(
                data_file=data_file,
                plot_type=plot_type,
                output_file=output_file,
                title=title,
                x_label=x_label,
                y_label=y_label
            )

            return result
        except ImportError:
            return {"error": "result_visualizer module not available"}

    def summarize_paper(source: str, detail_level: str = "medium") -> Dict[str, Any]:
        """Summarize a research paper using AI."""
        try:
            from tools.paper_summarizer import PaperSummarizer
            summarizer = PaperSummarizer()

            summary = summarizer.summarize(
                paper_content=source,
                detail_level=detail_level
            )

            return summary
        except ImportError:
            return {"error": "paper_summarizer module not available"}

    def latex_compile(tex_file: str, output_dir: Optional[str] = None) -> Dict[str, Any]:
        """Compile LaTeX document to PDF."""
        try:
            from tools.latex_compiler import LatexCompiler
            compiler = LatexCompiler()

            result = compiler.compile(tex_file, output_dir=output_dir)

            return result
        except ImportError:
            return {"error": "latex_compiler module not available"}

    return [
        ToolDefinition(
            name="statistical_test",
            description="Perform statistical significance tests on data",
            parameters=[
                ParameterSchema("data_file", "string", "Path to data file (CSV/JSON)", required=True),
                ParameterSchema("test_type", "string", "Type of test", required=True,
                               enum=["t-test", "wilcoxon", "anova", "mann-whitney", "chi-square"]),
                ParameterSchema("alpha", "number", "Significance level", required=False, default=0.05, min_value=0.001, max_value=0.1)
            ],
            category="analysis",
            implementation=statistical_test,
            returns="Test results including p-value and effect size",
            examples=['statistical_test(data_file="results.csv", test_type="t-test")']
        ),
        ToolDefinition(
            name="visualize_results",
            description="Create visualization plots from experimental data",
            parameters=[
                ParameterSchema("data_file", "string", "Path to data file", required=True),
                ParameterSchema("plot_type", "string", "Type of plot", required=True,
                               enum=["line", "bar", "heatmap", "scatter", "box", "violin"]),
                ParameterSchema("output_file", "string", "Output file path", required=True),
                ParameterSchema("title", "string", "Plot title", required=False),
                ParameterSchema("x_label", "string", "X-axis label", required=False),
                ParameterSchema("y_label", "string", "Y-axis label", required=False)
            ],
            category="analysis",
            implementation=visualize_results,
            returns="Generated plot file path",
            examples=['visualize_results(data_file="data.csv", plot_type="bar", output_file="plot.png")']
        ),
        ToolDefinition(
            name="summarize_paper",
            description="Generate an AI-powered summary of a research paper",
            parameters=[
                ParameterSchema("source", "string", "Paper file path or text content", required=True),
                ParameterSchema("detail_level", "string", "Level of detail", required=False, default="medium",
                               enum=["brief", "medium", "detailed"])
            ],
            category="analysis",
            implementation=summarize_paper,
            returns="Structured paper summary",
            examples=['summarize_paper(source="paper.pdf", detail_level="detailed")'],
            requires_auth=True
        ),
        ToolDefinition(
            name="latex_compile",
            description="Compile a LaTeX document to PDF",
            parameters=[
                ParameterSchema("tex_file", "string", "Path to .tex file", required=True),
                ParameterSchema("output_dir", "string", "Output directory for PDF", required=False)
            ],
            category="analysis",
            implementation=latex_compile,
            returns="Compilation result and PDF path",
            examples=['latex_compile(tex_file="paper.tex")']
        )
    ]


def _create_code_tools() -> List[ToolDefinition]:
    """Create code execution tool definitions."""

    def run_python(script_path: str, args: Optional[List[str]] = None, timeout: int = 300) -> Dict[str, Any]:
        """Run a Python script."""
        cmd = [sys.executable, script_path]
        if args:
            cmd.extend(args)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(Path(script_path).parent)
            )

            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"Script timed out after {timeout} seconds"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def run_tests(test_path: str, pattern: str = "test_*.py", verbose: bool = True) -> Dict[str, Any]:
        """Run pytest tests."""
        cmd = [sys.executable, "-m", "pytest", test_path, "-v" if verbose else "", "-q"]
        cmd = [c for c in cmd if c]  # Remove empty strings

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600
            )

            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "errors": result.stderr
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def pip_install(package: str, upgrade: bool = False) -> Dict[str, Any]:
        """Install a Python package."""
        cmd = [sys.executable, "-m", "pip", "install"]
        if upgrade:
            cmd.append("--upgrade")
        cmd.append(package)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )

            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "errors": result.stderr
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def check_syntax(file_path: str) -> Dict[str, Any]:
        """Check Python syntax without running the file."""
        import py_compile

        try:
            py_compile.compile(file_path, doraise=True)
            return {
                "success": True,
                "file": file_path,
                "errors": []
            }
        except py_compile.PyCompileError as e:
            return {
                "success": False,
                "file": file_path,
                "errors": [str(e)]
            }

    return [
        ToolDefinition(
            name="run_python",
            description="Execute a Python script",
            parameters=[
                ParameterSchema("script_path", "string", "Path to Python script", required=True),
                ParameterSchema("args", "array", "Command line arguments", required=False),
                ParameterSchema("timeout", "integer", "Timeout in seconds", required=False, default=300, max_value=3600)
            ],
            category="code",
            implementation=run_python,
            returns="Script execution results",
            examples=['run_python(script_path="train.py", args=["--epochs", "10"])'],
            dangerous=True,
            sandbox_safe=False
        ),
        ToolDefinition(
            name="run_tests",
            description="Run pytest test suite",
            parameters=[
                ParameterSchema("test_path", "string", "Path to test file or directory", required=True),
                ParameterSchema("pattern", "string", "Test file pattern", required=False, default="test_*.py"),
                ParameterSchema("verbose", "boolean", "Verbose output", required=False, default=True)
            ],
            category="code",
            implementation=run_tests,
            returns="Test results",
            examples=['run_tests(test_path="tests/")'],
            sandbox_safe=True
        ),
        ToolDefinition(
            name="pip_install",
            description="Install a Python package using pip",
            parameters=[
                ParameterSchema("package", "string", "Package name to install", required=True),
                ParameterSchema("upgrade", "boolean", "Upgrade if already installed", required=False, default=False)
            ],
            category="code",
            implementation=pip_install,
            returns="Installation result",
            examples=['pip_install(package="numpy", upgrade=True)'],
            dangerous=True,
            sandbox_safe=False
        ),
        ToolDefinition(
            name="check_syntax",
            description="Check Python file for syntax errors without executing",
            parameters=[
                ParameterSchema("file_path", "string", "Path to Python file", required=True)
            ],
            category="code",
            implementation=check_syntax,
            returns="Syntax check results",
            examples=['check_syntax(file_path="main.py")'],
            sandbox_safe=True
        )
    ]


def _create_git_tools() -> List[ToolDefinition]:
    """Create Git operation tool definitions."""

    def git_status() -> Dict[str, Any]:
        """Get Git repository status."""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True
            )

            changes = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    status = line[:2].strip()
                    file_path = line[3:]
                    changes.append({"status": status, "file": file_path})

            return {
                "success": True,
                "has_changes": len(changes) > 0,
                "changes": changes
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def git_commit(message: str, add_all: bool = False) -> Dict[str, Any]:
        """Create a Git commit."""
        try:
            if add_all:
                subprocess.run(["git", "add", "-A"], check=True, capture_output=True)

            result = subprocess.run(
                ["git", "commit", "-m", message],
                capture_output=True,
                text=True
            )

            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr if result.returncode != 0 else None
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def git_push(remote: str = "origin", branch: str = "master") -> Dict[str, Any]:
        """Push changes to remote repository."""
        try:
            result = subprocess.run(
                ["git", "push", remote, branch],
                capture_output=True,
                text=True
            )

            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr if result.returncode != 0 else None
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def git_log(max_count: int = 10, oneline: bool = True) -> Dict[str, Any]:
        """Get Git commit history."""
        try:
            cmd = ["git", "log", f"-{max_count}"]
            if oneline:
                cmd.append("--oneline")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )

            commits = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    commits.append(line)

            return {
                "success": True,
                "commits": commits
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def git_diff(file_path: Optional[str] = None, staged: bool = False) -> Dict[str, Any]:
        """Show Git diff."""
        try:
            cmd = ["git", "diff"]
            if staged:
                cmd.append("--staged")
            if file_path:
                cmd.append(file_path)

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )

            return {
                "success": True,
                "diff": result.stdout
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def git_branch(create: Optional[str] = None, delete: Optional[str] = None,
                   list_all: bool = False) -> Dict[str, Any]:
        """Manage Git branches."""
        try:
            if create:
                result = subprocess.run(
                    ["git", "checkout", "-b", create],
                    capture_output=True,
                    text=True
                )
                return {
                    "success": result.returncode == 0,
                    "branch": create,
                    "output": result.stdout
                }
            elif delete:
                result = subprocess.run(
                    ["git", "branch", "-d", delete],
                    capture_output=True,
                    text=True
                )
                return {
                    "success": result.returncode == 0,
                    "output": result.stdout,
                    "error": result.stderr if result.returncode != 0 else None
                }
            else:
                cmd = ["git", "branch"]
                if list_all:
                    cmd.append("-a")
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True
                )
                branches = [b.strip() for b in result.stdout.strip().split('\n') if b.strip()]
                return {
                    "success": True,
                    "branches": branches
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

    return [
        ToolDefinition(
            name="git_status",
            description="Get the current Git repository status",
            parameters=[],
            category="git",
            implementation=git_status,
            returns="Repository status and changes",
            examples=['git_status()'],
            sandbox_safe=True
        ),
        ToolDefinition(
            name="git_commit",
            description="Create a new Git commit",
            parameters=[
                ParameterSchema("message", "string", "Commit message", required=True),
                ParameterSchema("add_all", "boolean", "Stage all changes before commit", required=False, default=False)
            ],
            category="git",
            implementation=git_commit,
            returns="Commit result",
            examples=['git_commit(message="Add new feature", add_all=True)'],
            sandbox_safe=False
        ),
        ToolDefinition(
            name="git_push",
            description="Push commits to remote repository",
            parameters=[
                ParameterSchema("remote", "string", "Remote name", required=False, default="origin"),
                ParameterSchema("branch", "string", "Branch name", required=False, default="master")
            ],
            category="git",
            implementation=git_push,
            returns="Push result",
            examples=['git_push(remote="origin", branch="main")'],
            dangerous=True,
            sandbox_safe=False
        ),
        ToolDefinition(
            name="git_log",
            description="View Git commit history",
            parameters=[
                ParameterSchema("max_count", "integer", "Maximum number of commits", required=False, default=10),
                ParameterSchema("oneline", "boolean", "Show one line per commit", required=False, default=True)
            ],
            category="git",
            implementation=git_log,
            returns="List of commits",
            examples=['git_log(max_count=20)'],
            sandbox_safe=True
        ),
        ToolDefinition(
            name="git_diff",
            description="Show changes in working directory or staged changes",
            parameters=[
                ParameterSchema("file_path", "string", "Specific file to diff", required=False),
                ParameterSchema("staged", "boolean", "Show staged changes", required=False, default=False)
            ],
            category="git",
            implementation=git_diff,
            returns="Diff output",
            examples=['git_diff(staged=True)'],
            sandbox_safe=True
        ),
        ToolDefinition(
            name="git_branch",
            description="List, create, or delete Git branches",
            parameters=[
                ParameterSchema("create", "string", "Create new branch with this name", required=False),
                ParameterSchema("delete", "string", "Delete branch with this name", required=False),
                ParameterSchema("list_all", "boolean", "List all branches (including remote)", required=False, default=False)
            ],
            category="git",
            implementation=git_branch,
            returns="Branch information",
            examples=['git_branch(create="feature-xyz")', 'git_branch(list_all=True)'],
            sandbox_safe=False
        )
    ]


def _create_state_tools() -> List[ToolDefinition]:
    """Create state management tool definitions."""

    def get_state() -> Dict[str, Any]:
        """Get the current system state."""
        try:
            from progress import get_state as _get_state
            state = _get_state()
            return state.state
        except ImportError:
            return {"error": "progress module not available"}

    def update_state(key: str, value: Any) -> Dict[str, Any]:
        """Update a state value."""
        try:
            from progress import get_state
            state = get_state()
            state.update(**{key: value})
            return {"success": True, "key": key}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_task(task_id: str) -> Dict[str, Any]:
        """Get task details by ID."""
        try:
            from progress import get_tasks
            tasks = get_tasks()
            # Implementation depends on TaskManager structure
            return {"task_id": task_id, "status": "pending"}
        except ImportError:
            return {"error": "progress module not available"}

    def get_next_task(phase: Optional[str] = None) -> Dict[str, Any]:
        """Get the next pending task."""
        try:
            from progress import get_tasks
            tasks = get_tasks()
            task = tasks.get_next_pending_task(phase)
            return task or {"status": "no_pending_tasks"}
        except ImportError:
            return {"error": "progress module not available"}

    def complete_task(phase_id: str, task_id: str, notes: Optional[str] = None) -> Dict[str, Any]:
        """Mark a task as completed."""
        try:
            from progress import get_tasks
            tasks = get_tasks()
            success = tasks.mark_task_passed(phase_id, task_id)
            return {"success": success, "task_id": task_id}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_progress() -> Dict[str, Any]:
        """Get overall progress summary."""
        try:
            from progress import get_tasks
            tasks = get_tasks()
            return tasks.get_progress_summary()
        except ImportError:
            return {"error": "progress module not available"}

    return [
        ToolDefinition(
            name="get_state",
            description="Get the current system state",
            parameters=[],
            category="state",
            implementation=get_state,
            returns="Current state dictionary",
            examples=['get_state()']
        ),
        ToolDefinition(
            name="update_state",
            description="Update a value in the system state",
            parameters=[
                ParameterSchema("key", "string", "State key (supports dot notation)", required=True),
                ParameterSchema("value", "object", "Value to set", required=True)
            ],
            category="state",
            implementation=update_state,
            returns="Update confirmation",
            examples=['update_state(key="current_phase", value="coding")']
        ),
        ToolDefinition(
            name="get_task",
            description="Get details of a specific task",
            parameters=[
                ParameterSchema("task_id", "string", "Task ID to retrieve", required=True)
            ],
            category="state",
            implementation=get_task,
            returns="Task details",
            examples=['get_task(task_id="LIT-001")']
        ),
        ToolDefinition(
            name="get_next_task",
            description="Get the next pending task to work on",
            parameters=[
                ParameterSchema("phase", "string", "Filter by phase", required=False)
            ],
            category="state",
            implementation=get_next_task,
            returns="Next task details or status",
            examples=['get_next_task(phase="literature_review")']
        ),
        ToolDefinition(
            name="complete_task",
            description="Mark a task as completed",
            parameters=[
                ParameterSchema("phase_id", "string", "Phase ID", required=True),
                ParameterSchema("task_id", "string", "Task ID", required=True),
                ParameterSchema("notes", "string", "Optional completion notes", required=False)
            ],
            category="state",
            implementation=complete_task,
            returns="Completion status",
            examples=['complete_task(phase_id="literature_review", task_id="LIT-001")']
        ),
        ToolDefinition(
            name="get_progress",
            description="Get overall project progress summary",
            parameters=[],
            category="state",
            implementation=get_progress,
            returns="Progress statistics",
            examples=['get_progress()']
        )
    ]


def _create_communication_tools() -> List[ToolDefinition]:
    """Create communication tool definitions."""

    def send_report(filename: str, content: str, report_type: str = "general") -> Dict[str, Any]:
        """Send a report to the outbox."""
        try:
            from progress import get_comm
            comm = get_comm()
            filepath = comm.send_report(filename, content)
            return {
                "success": True,
                "path": str(filepath),
                "type": report_type
            }
        except ImportError:
            # Fallback: write to Communication/outbox
            outbox_dir = Path("Communication/outbox")
            outbox_dir.mkdir(parents=True, exist_ok=True)
            filepath = outbox_dir / filename
            filepath.write_text(content, encoding='utf-8')
            return {
                "success": True,
                "path": str(filepath),
                "type": report_type
            }

    def check_commands() -> Dict[str, Any]:
        """Check for new commands from inbox."""
        try:
            from progress import get_comm
            comm = get_comm()
            commands = comm.check_commands()
            return {
                "success": True,
                "commands": commands,
                "count": len(commands)
            }
        except ImportError:
            # Fallback: read from Communication/inbox
            inbox_dir = Path("Communication/inbox")
            if not inbox_dir.exists():
                return {"success": True, "commands": [], "count": 0}

            commands = []
            for cmd_file in inbox_dir.glob("*.txt"):
                content = cmd_file.read_text(encoding='utf-8')
                commands.append({
                    "file": cmd_file.name,
                    "content": content
                })

            return {"success": True, "commands": commands, "count": len(commands)}

    def log_message(message: str, level: str = "INFO") -> Dict[str, Any]:
        """Log a message to the system log."""
        try:
            from progress import get_logger
            logger = get_logger()
            logger.log(message, level=level)
            return {"success": True, "level": level}
        except ImportError:
            # Fallback: append to log file
            log_dir = Path("Logs")
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / f"prometheus_{datetime.now().strftime('%Y%m%d')}.log"
            timestamp = datetime.now().isoformat()
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(f"[{timestamp}] [{level}] {message}\n")
            return {"success": True, "level": level}

    def generate_report(template: str, data: Dict[str, Any], output_format: str = "markdown") -> Dict[str, Any]:
        """Generate a formatted report from template."""
        try:
            from tools.report_generator import ReportGenerator
            generator = ReportGenerator()

            content = generator.generate(
                template=template,
                data=data,
                output_format=output_format
            )

            return {
                "success": True,
                "content": content,
                "format": output_format
            }
        except ImportError:
            return {"error": "report_generator module not available"}

    return [
        ToolDefinition(
            name="send_report",
            description="Send a report to the outbox for human review",
            parameters=[
                ParameterSchema("filename", "string", "Report filename", required=True),
                ParameterSchema("content", "string", "Report content", required=True),
                ParameterSchema("report_type", "string", "Type of report", required=False, default="general",
                               enum=["general", "approval", "progress", "error", "completion"])
            ],
            category="communication",
            implementation=send_report,
            returns="Confirmation and file path",
            examples=['send_report(filename="progress.md", content="# Progress Report\\n...")']
        ),
        ToolDefinition(
            name="check_commands",
            description="Check for new commands from human operators",
            parameters=[],
            category="communication",
            implementation=check_commands,
            returns="List of pending commands",
            examples=['check_commands()']
        ),
        ToolDefinition(
            name="log_message",
            description="Log a message to the system log",
            parameters=[
                ParameterSchema("message", "string", "Message to log", required=True),
                ParameterSchema("level", "string", "Log level", required=False, default="INFO",
                               enum=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
            ],
            category="communication",
            implementation=log_message,
            returns="Logging confirmation",
            examples=['log_message(message="Task completed", level="INFO")']
        ),
        ToolDefinition(
            name="generate_report",
            description="Generate a formatted report from template and data",
            parameters=[
                ParameterSchema("template", "string", "Template name or content", required=True),
                ParameterSchema("data", "object", "Data to fill template", required=True),
                ParameterSchema("output_format", "string", "Output format", required=False, default="markdown",
                               enum=["markdown", "html", "text"])
            ],
            category="communication",
            implementation=generate_report,
            returns="Generated report content",
            examples=['generate_report(template="progress", data={"phase": "coding", "tasks": 10})']
        )
    ]


def _create_knowledge_tools() -> List[ToolDefinition]:
    """Create knowledge base tool definitions."""

    def add_finding(content: str, category: str = "general", importance: int = 1) -> Dict[str, Any]:
        """Add a finding to the knowledge base."""
        try:
            from progress import get_knowledge
            kb = get_knowledge()
            finding_id = kb.add_finding(content, category, importance=importance)
            return {"success": True, "finding_id": finding_id}
        except ImportError:
            # Fallback: save to JSON file
            kb_file = Path("Knowledge/findings.json")
            kb_file.parent.mkdir(parents=True, exist_ok=True)

            findings = []
            if kb_file.exists():
                findings = json.loads(kb_file.read_text(encoding='utf-8'))

            finding_id = f"FIND-{len(findings) + 1:04d}"
            finding = {
                "id": finding_id,
                "content": content,
                "category": category,
                "importance": importance,
                "created_at": datetime.now().isoformat()
            }
            findings.append(finding)

            kb_file.write_text(json.dumps(findings, indent=2, ensure_ascii=False), encoding='utf-8')
            return {"success": True, "finding_id": finding_id}

    def search_knowledge(query: str, category: Optional[str] = None) -> Dict[str, Any]:
        """Search the knowledge base."""
        try:
            from progress import get_knowledge
            kb = get_knowledge()
            results = kb.search(query, category=category)
            return {"success": True, "results": results, "query": query}
        except ImportError:
            # Fallback: simple search in JSON file
            kb_file = Path("Knowledge/findings.json")
            if not kb_file.exists():
                return {"success": True, "results": [], "query": query}

            findings = json.loads(kb_file.read_text(encoding='utf-8'))
            query_lower = query.lower()

            results = [
                f for f in findings
                if query_lower in f.get("content", "").lower()
                and (category is None or f.get("category") == category)
            ]

            return {"success": True, "results": results, "query": query}

    def get_best_practices(topic: Optional[str] = None) -> Dict[str, Any]:
        """Get best practices from knowledge base."""
        try:
            from progress import get_knowledge
            kb = get_knowledge()
            practices = kb.get_best_practices(topic=topic)
            return {"success": True, "practices": practices}
        except ImportError:
            return {"success": True, "practices": [], "note": "Knowledge base not available"}

    def update_best_practice(topic: str, content: str) -> Dict[str, Any]:
        """Update or create a best practice entry."""
        try:
            from progress import get_knowledge
            kb = get_knowledge()
            kb.update_best_practice(topic, content)
            return {"success": True, "topic": topic}
        except ImportError:
            # Fallback: save to JSON file
            bp_file = Path("Knowledge/best_practices.json")
            bp_file.parent.mkdir(parents=True, exist_ok=True)

            practices = {}
            if bp_file.exists():
                practices = json.loads(bp_file.read_text(encoding='utf-8'))

            practices[topic] = {
                "content": content,
                "updated_at": datetime.now().isoformat()
            }

            bp_file.write_text(json.dumps(practices, indent=2, ensure_ascii=False), encoding='utf-8')
            return {"success": True, "topic": topic}

    return [
        ToolDefinition(
            name="add_finding",
            description="Add a research finding to the knowledge base",
            parameters=[
                ParameterSchema("content", "string", "Finding content", required=True),
                ParameterSchema("category", "string", "Finding category", required=False, default="general"),
                ParameterSchema("importance", "integer", "Importance level (1-5)", required=False, default=1,
                               min_value=1, max_value=5)
            ],
            category="knowledge",
            implementation=add_finding,
            returns="Finding ID",
            examples=['add_finding(content="Transformer models excel at sequence tasks", category="architecture")']
        ),
        ToolDefinition(
            name="search_knowledge",
            description="Search the knowledge base for relevant information",
            parameters=[
                ParameterSchema("query", "string", "Search query", required=True),
                ParameterSchema("category", "string", "Filter by category", required=False)
            ],
            category="knowledge",
            implementation=search_knowledge,
            returns="Matching findings",
            examples=['search_knowledge(query="attention mechanism")']
        ),
        ToolDefinition(
            name="get_best_practices",
            description="Retrieve best practices from knowledge base",
            parameters=[
                ParameterSchema("topic", "string", "Filter by topic", required=False)
            ],
            category="knowledge",
            implementation=get_best_practices,
            returns="List of best practices",
            examples=['get_best_practices(topic="code_review")']
        ),
        ToolDefinition(
            name="update_best_practice",
            description="Add or update a best practice entry",
            parameters=[
                ParameterSchema("topic", "string", "Best practice topic", required=True),
                ParameterSchema("content", "string", "Best practice content", required=True)
            ],
            category="knowledge",
            implementation=update_best_practice,
            returns="Update confirmation",
            examples=['update_best_practice(topic="testing", content="Always write unit tests")']
        )
    ]


# ============================================================================
# Tool Registration
# ============================================================================

def register_all_tools(registry: Optional[ToolRegistry] = None) -> ToolRegistry:
    """
    Register all available tools.

    Args:
        registry: Optional registry to register tools to.
                 If None, uses the global registry.

    Returns:
        ToolRegistry with all tools registered
    """
    if registry is None:
        registry = get_tool_registry()

    # Register all tool categories
    for tool in _create_file_tools():
        registry.register(tool)

    for tool in _create_search_tools():
        registry.register(tool)

    for tool in _create_analysis_tools():
        registry.register(tool)

    for tool in _create_code_tools():
        registry.register(tool)

    for tool in _create_git_tools():
        registry.register(tool)

    for tool in _create_state_tools():
        registry.register(tool)

    for tool in _create_communication_tools():
        registry.register(tool)

    for tool in _create_knowledge_tools():
        registry.register(tool)

    return registry


def get_tools_by_category(category: str) -> List[ToolDefinition]:
    """
    Get all tools in a specific category.

    Args:
        category: Tool category

    Returns:
        List of ToolDefinitions
    """
    return get_tool_registry().list_tools(category)


def get_tool_schema(name: str) -> Optional[Dict[str, Any]]:
    """
    Get the JSON schema for a specific tool.

    Args:
        name: Tool name

    Returns:
        Tool schema or None if not found
    """
    tool = get_tool_registry().get_tool(name)
    return tool.to_schema() if tool else None


def list_all_tools() -> List[str]:
    """Get names of all registered tools."""
    return [t.name for t in get_tool_registry().list_tools()]


# ============================================================================
# CLI Interface
# ============================================================================

def main():
    """Command-line interface for tool management."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Prometheus Tool Definitions Manager"
    )

    parser.add_argument(
        '--list', '-l', action='store_true',
        help='List all registered tools'
    )
    parser.add_argument(
        '--category', '-c', type=str,
        help='Filter by category'
    )
    parser.add_argument(
        '--schema', '-s', type=str,
        help='Get schema for a specific tool'
    )
    parser.add_argument(
        '--execute', '-e', type=str,
        help='Execute a tool (provide JSON args via stdin)'
    )
    parser.add_argument(
        '--export', type=str,
        help='Export all tool schemas to file'
    )

    args = parser.parse_args()

    # Register all tools
    register_all_tools()
    registry = get_tool_registry()

    if args.list:
        tools = registry.list_tools(args.category)
        print(f"Registered Tools ({len(tools)}):")
        print("-" * 60)
        for tool in tools:
            dangerous_marker = " [!]" if tool.dangerous else ""
            auth_marker = " [auth]" if tool.requires_auth else ""
            print(f"  {tool.name}{dangerous_marker}{auth_marker}")
            print(f"    Category: {tool.category}")
            print(f"    Description: {tool.description[:60]}...")
            print()

    elif args.schema:
        tool = registry.get_tool(args.schema)
        if tool:
            print(json.dumps(tool.to_schema(), indent=2))
        else:
            print(f"Tool not found: {args.schema}")

    elif args.execute:
        import sys
        tool_name = args.execute

        # Read JSON args from stdin
        try:
            args_json = sys.stdin.read()
            kwargs = json.loads(args_json) if args_json.strip() else {}
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON arguments: {e}")
            return

        result = registry.execute(tool_name, **kwargs)
        print(json.dumps(result, indent=2, default=str))

    elif args.export:
        schemas = registry.get_schemas()
        with open(args.export, 'w', encoding='utf-8') as f:
            json.dump(schemas, f, indent=2)
        print(f"Exported {len(schemas)} tool schemas to {args.export}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()

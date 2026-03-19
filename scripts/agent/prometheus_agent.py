#!/usr/bin/env python3
"""
Project Prometheus - Agent SDK Integration
============================================

This module provides a wrapper for Claude Agent SDK integration,
enabling the Prometheus system to operate as an autonomous agent.

Features:
- Prompt loading and management for different phases
- State management integration
- Tool registration and execution
- Session management and context handling
- Error recovery and retry mechanisms
- Custom base_url support for Anthropic-compatible APIs

Environment Variables:
    ANTHROPIC_API_KEY: API key for Anthropic or compatible service
    ANTHROPIC_BASE_URL: (Optional) Custom API endpoint
        Examples:
        - 智谱AI: https://open.bigmodel.cn/api/anthropic
        - OpenRouter: https://openrouter.ai/api/v1

Usage:
    from agent.prometheus_agent import PrometheusAgent, get_agent

    # Get the agent instance
    agent = get_agent()

    # Initialize and run
    agent.initialize()
    agent.run_phase("literature_review")

    # Or run a specific task
    agent.run_task("LIT-001")

Using with custom API endpoint:
    # Windows PowerShell
    $env:ANTHROPIC_API_KEY="your-api-key"
    $env:ANTHROPIC_BASE_URL="https://open.bigmodel.cn/api/anthropic"
"""

import json
import os
import sys
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Type, Union

# ============================================================================
# Anthropic SDK Import
# ============================================================================
try:
    import anthropic
    ANTHROPIC_SDK_AVAILABLE = True
except ImportError:
    ANTHROPIC_SDK_AVAILABLE = False
    anthropic = None

# Add Core directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "Core"))

from progress import (
    StateManager, TaskManager, LogManager, KnowledgeBaseManager,
    SessionManager, GitManager, CommunicationManager,
    get_state, get_tasks, get_logger, get_knowledge, get_session, get_git, get_comm
)


# ============================================================================
# Enums and Data Classes
# ============================================================================

class AgentStatus(Enum):
    """Agent status enumeration."""
    IDLE = "idle"
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    WAITING_APPROVAL = "waiting_approval"
    ERROR = "error"
    COMPLETED = "completed"


class Phase(Enum):
    """Research phases enumeration."""
    LITERATURE_REVIEW = "literature_review"
    HYPOTHESIS_DESIGN = "hypothesis_design"
    CODING = "coding"
    EXECUTION = "execution"
    ANALYSIS = "analysis"
    WRITING = "writing"
    PEER_REVIEW = "peer_review"


@dataclass
class ToolResult:
    """Result of a tool execution."""
    success: bool
    output: Any
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentContext:
    """Context for agent execution."""
    phase: Phase
    task_id: Optional[str] = None
    attempt: int = 0
    max_attempts: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# Prompt Loader
# ============================================================================

class PromptLoader:
    """Loads and manages prompts for different phases."""

    # Mapping of phase to prompt file names
    PHASE_PROMPTS = {
        Phase.LITERATURE_REVIEW: "phase1_literature.md",
        Phase.HYPOTHESIS_DESIGN: "phase2_hypothesis.md",
        Phase.CODING: "phase3_coding.md",
        Phase.EXECUTION: "phase4_execution.md",
        Phase.ANALYSIS: "phase5_analysis.md",
        Phase.WRITING: "phase6_writing.md",
        Phase.PEER_REVIEW: "phase7_review.md",
    }

    # Special purpose prompts
    SPECIAL_PROMPTS = {
        "initializer": "initializer_prompt.md",
        "research_agent": "research_agent_prompt.md",
        "error_recovery": "error_recovery.md",
        "self_evolution": "self_evolution.md",
    }

    def __init__(self, prompts_dir: Optional[Path] = None):
        """
        Initialize the prompt loader.

        Args:
            prompts_dir: Directory containing prompt files.
                        Defaults to Core/prompts/
        """
        self.prompts_dir = prompts_dir or self._get_default_prompts_dir()
        self._cache: Dict[str, str] = {}

    def _get_default_prompts_dir(self) -> Path:
        """Get the default prompts directory."""
        return Path(__file__).parent.parent / "Core" / "prompts"

    def load_prompt(self, name: str, use_cache: bool = True) -> str:
        """
        Load a prompt by name.

        Args:
            name: Prompt name (e.g., "phase1_literature" or "initializer")
            use_cache: Whether to use cached prompts

        Returns:
            Prompt content as string

        Raises:
            FileNotFoundError: If prompt file doesn't exist
        """
        if use_cache and name in self._cache:
            return self._cache[name]

        # Determine the file name
        if name in self.SPECIAL_PROMPTS:
            filename = self.SPECIAL_PROMPTS[name]
        elif name.startswith("phase") or name in [p.value for p in Phase]:
            # Map phase name to prompt file
            phase_key = name if name.startswith("phase") else f"phase{name.split('_')[-1]}"
            for phase, fname in self.PHASE_PROMPTS.items():
                if phase.value in name or fname.startswith(phase_key):
                    filename = fname
                    break
            else:
                filename = f"{name}.md"
        else:
            filename = f"{name}.md"

        filepath = self.prompts_dir / filename

        if not filepath.exists():
            raise FileNotFoundError(f"Prompt file not found: {filepath}")

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        if use_cache:
            self._cache[name] = content

        return content

    def load_phase_prompt(self, phase: Phase, use_cache: bool = True) -> str:
        """
        Load the prompt for a specific phase.

        Args:
            phase: The phase to load prompt for
            use_cache: Whether to use cached prompts

        Returns:
            Prompt content as string
        """
        filename = self.PHASE_PROMPTS.get(phase)
        if not filename:
            raise ValueError(f"No prompt defined for phase: {phase}")

        if use_cache and filename in self._cache:
            return self._cache[filename]

        filepath = self.prompts_dir / filename

        if not filepath.exists():
            raise FileNotFoundError(f"Phase prompt file not found: {filepath}")

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        if use_cache:
            self._cache[filename] = content

        return content

    def get_all_available_prompts(self) -> List[str]:
        """
        Get a list of all available prompt names.

        Returns:
            List of prompt names
        """
        prompts = []

        # Add phase prompts
        for phase in Phase:
            prompts.append(f"phase:{phase.value}")

        # Add special prompts
        prompts.extend(self.SPECIAL_PROMPTS.keys())

        return prompts

    def clear_cache(self) -> None:
        """Clear the prompt cache."""
        self._cache.clear()


# ============================================================================
# Tool Registry
# ============================================================================

class AgentTool:
    """Represents a tool that the agent can use."""

    def __init__(
        self,
        name: str,
        description: str,
        func: Callable,
        parameters: Optional[Dict[str, Any]] = None,
        required_params: Optional[List[str]] = None
    ):
        """
        Initialize an agent tool.

        Args:
            name: Tool name
            description: Tool description
            func: Function to execute
            parameters: JSON schema for parameters
            required_params: List of required parameter names
        """
        self.name = name
        self.description = description
        self.func = func
        self.parameters = parameters or {}
        self.required_params = required_params or []

    def execute(self, **kwargs) -> ToolResult:
        """
        Execute the tool with given parameters.

        Args:
            **kwargs: Tool parameters

        Returns:
            ToolResult with execution result
        """
        try:
            # Validate required parameters
            missing = [p for p in self.required_params if p not in kwargs]
            if missing:
                return ToolResult(
                    success=False,
                    output=None,
                    error=f"Missing required parameters: {missing}"
                )

            # Execute the function
            result = self.func(**kwargs)

            return ToolResult(
                success=True,
                output=result
            )

        except Exception as e:
            return ToolResult(
                success=False,
                output=None,
                error=str(e)
            )

    def to_schema(self) -> Dict[str, Any]:
        """
        Convert tool to JSON schema format for API.

        Returns:
            Dictionary with tool schema
        """
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": self.parameters,
                "required": self.required_params
            }
        }


class ToolRegistry:
    """Registry for agent tools."""

    def __init__(self):
        """Initialize the tool registry."""
        self._tools: Dict[str, AgentTool] = {}
        self._categories: Dict[str, List[str]] = {}

    def register(
        self,
        name: str,
        description: str,
        func: Optional[Callable] = None,
        parameters: Optional[Dict[str, Any]] = None,
        required_params: Optional[List[str]] = None,
        category: str = "general"
    ) -> Union[AgentTool, Callable]:
        """
        Register a tool.

        Can be used as a decorator or directly.

        Args:
            name: Tool name
            description: Tool description
            func: Function to execute (optional if used as decorator)
            parameters: JSON schema for parameters
            required_params: List of required parameter names
            category: Tool category for organization

        Returns:
            AgentTool instance or decorator function
        """
        def decorator(f: Callable) -> AgentTool:
            tool = AgentTool(
                name=name,
                description=description,
                func=f,
                parameters=parameters,
                required_params=required_params
            )
            self._tools[name] = tool
            self._categories.setdefault(category, []).append(name)
            return tool

        if func is not None:
            return decorator(func)
        return decorator

    def get_tool(self, name: str) -> Optional[AgentTool]:
        """
        Get a tool by name.

        Args:
            name: Tool name

        Returns:
            AgentTool or None if not found
        """
        return self._tools.get(name)

    def list_tools(self, category: Optional[str] = None) -> List[AgentTool]:
        """
        List all registered tools.

        Args:
            category: Filter by category (optional)

        Returns:
            List of AgentTool instances
        """
        if category:
            tool_names = self._categories.get(category, [])
            return [self._tools[name] for name in tool_names if name in self._tools]
        return list(self._tools.values())

    def get_tools_schema(self) -> List[Dict[str, Any]]:
        """
        Get JSON schema for all tools.

        Returns:
            List of tool schemas
        """
        return [tool.to_schema() for tool in self._tools.values()]

    def unregister(self, name: str) -> bool:
        """
        Unregister a tool.

        Args:
            name: Tool name

        Returns:
            True if tool was removed, False if not found
        """
        if name in self._tools:
            del self._tools[name]
            # Remove from categories
            for cat_tools in self._categories.values():
                if name in cat_tools:
                    cat_tools.remove(name)
            return True
        return False


# ============================================================================
# Agent Configuration
# ============================================================================

@dataclass
class AgentConfig:
    """Configuration for the Prometheus agent."""

    # Model settings
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 4096
    temperature: float = 0.7

    # Execution settings
    max_attempts: int = 3
    retry_delay: float = 5.0
    timeout: int = 300

    # Behavior settings
    auto_commit: bool = True
    require_approval: bool = False
    verbose: bool = True

    # Paths
    base_dir: Optional[Path] = None
    prompts_dir: Optional[Path] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentConfig":
        """Create config from dictionary."""
        if "base_dir" in data and isinstance(data["base_dir"], str):
            data["base_dir"] = Path(data["base_dir"])
        if "prompts_dir" in data and isinstance(data["prompts_dir"], str):
            data["prompts_dir"] = Path(data["prompts_dir"])
        return cls(**{k: v for k, v in data.items() if hasattr(cls, k)})


# ============================================================================
# Prometheus Agent
# ============================================================================

class PrometheusAgent:
    """
    Main agent class for Project Prometheus.

    This class integrates:
    - Claude Agent SDK for AI capabilities
    - State management for tracking progress
    - Tool registry for executing actions
    - Prompt loader for phase-specific instructions
    """

    def __init__(
        self,
        config: Optional[AgentConfig] = None,
        state_manager: Optional[StateManager] = None,
        task_manager: Optional[TaskManager] = None,
        log_manager: Optional[LogManager] = None,
        knowledge_manager: Optional[KnowledgeBaseManager] = None,
        session_manager: Optional[SessionManager] = None,
        git_manager: Optional[GitManager] = None,
        comm_manager: Optional[CommunicationManager] = None
    ):
        """
        Initialize the Prometheus agent.

        Args:
            config: Agent configuration
            state_manager: State manager instance
            task_manager: Task manager instance
            log_manager: Log manager instance
            knowledge_manager: Knowledge base manager instance
            session_manager: Session manager instance
            git_manager: Git manager instance
            comm_manager: Communication manager instance
        """
        self.config = config or AgentConfig()

        # Initialize managers
        self.state = state_manager or get_state()
        self.tasks = task_manager or get_tasks()
        self.logger = log_manager or get_logger()
        self.knowledge = knowledge_manager or get_knowledge()
        self.session = session_manager or get_session()
        self.git = git_manager or get_git()
        self.comm = comm_manager or get_comm()

        # Initialize components
        self.prompt_loader = PromptLoader(self.config.prompts_dir)
        self.tool_registry = ToolRegistry()

        # Agent state
        self._status = AgentStatus.IDLE
        self._current_context: Optional[AgentContext] = None
        self._initialized = False

        # Register built-in tools
        self._register_builtin_tools()

    def _register_builtin_tools(self) -> None:
        """Register built-in tools for the agent."""
        # File operations
        @self.tool_registry.register(
            name="read_file",
            description="Read a file from the filesystem",
            parameters={
                "path": {"type": "string", "description": "File path to read"}
            },
            required_params=["path"],
            category="file"
        )
        def read_file(path: str) -> str:
            filepath = Path(path)
            if not filepath.exists():
                raise FileNotFoundError(f"File not found: {path}")
            return filepath.read_text(encoding='utf-8')

        @self.tool_registry.register(
            name="write_file",
            description="Write content to a file",
            parameters={
                "path": {"type": "string", "description": "File path to write"},
                "content": {"type": "string", "description": "Content to write"}
            },
            required_params=["path", "content"],
            category="file"
        )
        def write_file(path: str, content: str) -> str:
            filepath = Path(path)
            filepath.parent.mkdir(parents=True, exist_ok=True)
            filepath.write_text(content, encoding='utf-8')
            return f"File written: {path}"

        @self.tool_registry.register(
            name="list_directory",
            description="List contents of a directory",
            parameters={
                "path": {"type": "string", "description": "Directory path"}
            },
            required_params=["path"],
            category="file"
        )
        def list_directory(path: str) -> List[str]:
            dirpath = Path(path)
            if not dirpath.exists():
                raise FileNotFoundError(f"Directory not found: {path}")
            return [str(p.name) for p in dirpath.iterdir()]

        # State operations
        @self.tool_registry.register(
            name="get_state",
            description="Get the current system state",
            parameters={},
            category="state"
        )
        def get_current_state() -> Dict[str, Any]:
            return self.state.state

        @self.tool_registry.register(
            name="update_state",
            description="Update the system state",
            parameters={
                "key": {"type": "string", "description": "State key (supports dot notation)"},
                "value": {"type": "any", "description": "Value to set"}
            },
            required_params=["key", "value"],
            category="state"
        )
        def update_state(key: str, value: Any) -> str:
            self.state.update(**{key: value})
            return f"State updated: {key}"

        # Task operations
        @self.tool_registry.register(
            name="get_next_task",
            description="Get the next pending task",
            parameters={
                "phase": {"type": "string", "description": "Phase ID to filter (optional)"}
            },
            category="task"
        )
        def get_next_task(phase: Optional[str] = None) -> Optional[Dict[str, Any]]:
            return self.tasks.get_next_pending_task(phase)

        @self.tool_registry.register(
            name="mark_task_complete",
            description="Mark a task as completed",
            parameters={
                "phase_id": {"type": "string", "description": "Phase ID"},
                "task_id": {"type": "string", "description": "Task ID"}
            },
            required_params=["phase_id", "task_id"],
            category="task"
        )
        def mark_task_complete(phase_id: str, task_id: str) -> str:
            success = self.tasks.mark_task_passed(phase_id, task_id)
            if success:
                return f"Task {task_id} marked as complete"
            return f"Failed to mark task {task_id} as complete"

        # Git operations
        @self.tool_registry.register(
            name="git_commit",
            description="Create a git commit",
            parameters={
                "message": {"type": "string", "description": "Commit message"},
                "add_all": {"type": "boolean", "description": "Add all changes"}
            },
            required_params=["message"],
            category="git"
        )
        def git_commit(message: str, add_all: bool = True) -> str:
            success = self.git.commit(message, add_all=add_all)
            if success:
                return f"Commit created: {message}"
            return "Failed to create commit"

        @self.tool_registry.register(
            name="git_status",
            description="Get the current git status",
            parameters={},
            category="git"
        )
        def git_status() -> Dict[str, List[str]]:
            return self.git.get_status()

        # Knowledge operations
        @self.tool_registry.register(
            name="add_finding",
            description="Add a research finding to the knowledge base",
            parameters={
                "content": {"type": "string", "description": "Finding content"},
                "category": {"type": "string", "description": "Finding category"},
                "importance": {"type": "integer", "description": "Importance (1-5)"}
            },
            required_params=["content"],
            category="knowledge"
        )
        def add_finding(content: str, category: str = "general", importance: int = 1) -> str:
            finding_id = self.knowledge.add_finding(content, category, importance=importance)
            return f"Finding added: {finding_id}"

        @self.tool_registry.register(
            name="search_knowledge",
            description="Search the knowledge base",
            parameters={
                "query": {"type": "string", "description": "Search query"}
            },
            required_params=["query"],
            category="knowledge"
        )
        def search_knowledge(query: str) -> Dict[str, Any]:
            return self.knowledge.search(query)

        # Communication operations
        @self.tool_registry.register(
            name="send_report",
            description="Send a report to the outbox",
            parameters={
                "filename": {"type": "string", "description": "Report filename"},
                "content": {"type": "string", "description": "Report content"}
            },
            required_params=["filename", "content"],
            category="communication"
        )
        def send_report(filename: str, content: str) -> str:
            filepath = self.comm.send_report(filename, content)
            return f"Report sent: {filepath}"

        @self.tool_registry.register(
            name="check_commands",
            description="Check for new commands from inbox",
            parameters={},
            category="communication"
        )
        def check_commands() -> List[str]:
            return self.comm.check_commands()

    @property
    def status(self) -> AgentStatus:
        """Get the current agent status."""
        return self._status

    def set_status(self, status: AgentStatus, reason: Optional[str] = None) -> None:
        """
        Set the agent status.

        Args:
            status: New status
            reason: Optional reason for status change
        """
        self._status = status
        self.state.set_status(status.value, reason)
        self.logger.log(f"Agent status changed to: {status.value}", level="INFO")

    def initialize(self) -> bool:
        """
        Initialize the agent.

        Returns:
            True if initialization successful
        """
        try:
            self.set_status(AgentStatus.INITIALIZING)

            # Validate system state
            state = self.state.state
            if not state.get("current_project"):
                self.logger.log("No project initialized", level="WARNING")

            # Start a new session
            self.session.start_session(
                task_id=state.get("current_task"),
                phase=state.get("current_phase"),
                project=state.get("current_project")
            )

            self._initialized = True
            self.set_status(AgentStatus.IDLE, "Agent initialized successfully")

            self.logger.log("Prometheus agent initialized", level="INFO")
            return True

        except Exception as e:
            self.set_status(AgentStatus.ERROR, str(e))
            self.logger.error(f"Failed to initialize agent: {e}")
            return False

    def get_phase_prompt(self, phase: Union[Phase, str]) -> str:
        """
        Get the prompt for a specific phase.

        Args:
            phase: Phase enum or phase string

        Returns:
            Prompt content
        """
        if isinstance(phase, str):
            phase = Phase(phase)
        return self.prompt_loader.load_phase_prompt(phase)

    def create_execution_context(
        self,
        phase: Union[Phase, str],
        task_id: Optional[str] = None,
        **kwargs
    ) -> AgentContext:
        """
        Create an execution context.

        Args:
            phase: Phase for the context
            task_id: Optional task ID
            **kwargs: Additional context metadata

        Returns:
            AgentContext instance
        """
        if isinstance(phase, str):
            phase = Phase(phase)

        return AgentContext(
            phase=phase,
            task_id=task_id,
            max_attempts=self.config.max_attempts,
            metadata=kwargs
        )

    def execute_tool(self, tool_name: str, **kwargs) -> ToolResult:
        """
        Execute a registered tool.

        Args:
            tool_name: Name of the tool to execute
            **kwargs: Tool parameters

        Returns:
            ToolResult with execution result
        """
        tool = self.tool_registry.get_tool(tool_name)
        if not tool:
            return ToolResult(
                success=False,
                output=None,
                error=f"Tool not found: {tool_name}"
            )

        self.logger.log(f"Executing tool: {tool_name}", level="INFO")
        result = tool.execute(**kwargs)

        if not result.success:
            self.logger.error(f"Tool execution failed: {result.error}")

        return result

    def run_task(self, task_id: str, phase: Optional[str] = None) -> bool:
        """
        Run a specific task.

        Args:
            task_id: Task ID to run
            phase: Optional phase ID

        Returns:
            True if task completed successfully
        """
        if not self._initialized:
            self.initialize()

        self.set_status(AgentStatus.RUNNING)

        try:
            # Update state with current task
            self.state.set_task(task_id)

            # Get task details
            task_info = self.tasks.get_next_pending_task(phase)
            if not task_info or task_info.get('task', {}).get('task_id') != task_id:
                self.logger.log(f"Task {task_id} not found or already completed", level="WARNING")
                return False

            task = task_info['task']
            phase_id = task_info['phase_id']

            # Create context
            context = self.create_execution_context(
                phase=phase_id,
                task_id=task_id,
                task_description=task.get('description')
            )
            self._current_context = context

            # Get the phase prompt
            try:
                phase_enum = Phase(phase_id)
                prompt = self.get_phase_prompt(phase_enum)
            except (ValueError, FileNotFoundError):
                # Fall back to research agent prompt
                prompt = self.prompt_loader.load_prompt("research_agent")

            # Log task start
            self.logger.log(
                f"Starting task {task_id}: {task.get('description', 'No description')}",
                level="INFO"
            )

            # Check if task requires human approval
            if task.get('requires_human_approval'):
                self.set_status(
                    AgentStatus.WAITING_APPROVAL,
                    f"Task {task_id} requires human approval"
                )
                self.comm.send_report(
                    f"approval_request_{task_id}.md",
                    f"# Approval Request\n\nTask: {task_id}\nDescription: {task.get('description')}"
                )
                return False

            # ========================================
            # 真正的 Agent SDK 调用
            # ========================================
            task['attempts'] = task.get('attempts', 0) + 1
            
            # 执行任务并获取结果
            success, output = self._execute_with_claude(prompt, context)
            
            if success:
                # 检查是否有完成承诺
                if self._check_completion_promise(output):
                    self.tasks.mark_task_passed(phase_id, task_id)
                    self.logger.log(f"Task {task_id} completed successfully", level="INFO")
                    
                    # 提交 Git
                    if self.config.auto_commit:
                        self.git.commit(f"Complete {task_id}: {task.get('description', '')[:50]}")
                else:
                    self.logger.log(f"Task {task_id} executed but no completion promise detected", level="WARNING")
            else:
                self.logger.error(f"Task {task_id} execution failed: {output}")
                task['last_error'] = output

            self.set_status(AgentStatus.IDLE)
            return success

        except Exception as e:
            self.set_status(AgentStatus.ERROR, str(e))
            self.logger.error(f"Task execution failed: {e}")
            return False

    def _execute_with_claude(
        self, 
        prompt: str, 
        context: AgentContext,
        max_tool_iterations: int = 20
    ) -> tuple[bool, str]:
        """
        使用 Claude Agent SDK 执行任务
        
        Args:
            prompt: 任务提示词
            context: 执行上下文
            max_tool_iterations: 最大工具调用迭代次数
            
        Returns:
            (成功标志, 输出内容)
        """
        if not ANTHROPIC_SDK_AVAILABLE:
            return self._execute_with_cli_fallback(prompt, context)
        
        try:
            # 初始化 Anthropic 客户端
            # 支持自定义 base_url（如智谱AI、OpenRouter 等兼容 API）
            api_key = os.environ.get("ANTHROPIC_API_KEY")
            base_url = os.environ.get("ANTHROPIC_BASE_URL")  # 可选：自定义 API 端点

            client_kwargs = {"api_key": api_key}
            if base_url:
                client_kwargs["base_url"] = base_url

            client = anthropic.Anthropic(**client_kwargs)
            
            # 构建消息
            messages = [{"role": "user", "content": prompt}]
            
            # 获取工具定义
            tools = self._get_tool_definitions_for_api()
            
            # 工具调用循环
            iteration = 0
            final_response = None
            
            while iteration < max_tool_iterations:
                iteration += 1
                
                # 调用 Claude API
                response = client.messages.create(
                    model=self.config.model,
                    max_tokens=self.config.max_tokens,
                    temperature=self.config.temperature,
                    system=self._get_system_prompt(),
                    messages=messages,
                    tools=tools if tools else None,
                )
                
                # 检查响应类型
                has_tool_use = False
                response_text = ""
                
                for block in response.content:
                    if block.type == "text":
                        response_text += block.text
                    elif block.type == "tool_use":
                        has_tool_use = True
                        
                        # 执行工具
                        tool_result = self._execute_tool_from_api(block)
                        
                        # 添加到消息历史
                        messages.append({"role": "assistant", "content": response.content})
                        messages.append({
                            "role": "user",
                            "content": [{
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": json.dumps(tool_result) if isinstance(tool_result, dict) else str(tool_result)
                            }]
                        })
                
                # 如果没有工具调用，检查是否完成
                if not has_tool_use:
                    final_response = response_text
                    break
                
                # 更新最终响应
                final_response = response_text
            
            if final_response is None:
                return False, "Max tool iterations reached without final response"
            
            return True, final_response
            
        except anthropic.APIError as e:
            self.logger.error(f"Claude API error: {e}")
            return False, f"API Error: {str(e)}"
        except Exception as e:
            self.logger.error(f"Execution error: {e}")
            return False, str(e)
    
    def _execute_with_cli_fallback(self, prompt: str, context: AgentContext) -> tuple[bool, str]:
        """
        回退到 CLI 模式执行
        
        当 Anthropic SDK 不可用时使用
        """
        import subprocess
        
        self.logger.log("Anthropic SDK not available, using CLI fallback", level="WARNING")
        
        try:
            result = subprocess.run(
                ['claude', '--print', '--permission-mode', 'bypassPermissions'],
                input=prompt,
                capture_output=True,
                text=True,
                timeout=self.config.timeout,
                cwd=self.config.base_dir or Path.cwd(),
                encoding='utf-8',
                errors='replace'
            )
            
            if result.returncode == 0:
                return True, result.stdout
            else:
                return False, result.stderr
                
        except subprocess.TimeoutExpired:
            return False, f"Execution timeout ({self.config.timeout}s)"
        except FileNotFoundError:
            return False, "Claude CLI not found. Install with: npm install -g @anthropic-ai/claude-code"
        except Exception as e:
            return False, str(e)
    
    def _get_tool_definitions_for_api(self) -> List[Dict]:
        """获取 Claude API 格式的工具定义"""
        tools = []
        
        for tool_name, tool in self.tool_registry._tools.items():
            tool_def = {
                "name": tool_name,
                "description": tool.description,
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": tool.required_params
                }
            }
            
            # 添加参数
            for param_name, param_spec in tool.parameters.items():
                tool_def["input_schema"]["properties"][param_name] = param_spec
            
            tools.append(tool_def)
        
        return tools
    
    def _execute_tool_from_api(self, tool_use_block) -> Any:
        """执行来自 API 的工具调用"""
        tool_name = tool_use_block.name
        tool_input = tool_use_block.input
        
        try:
            result = self.execute_tool(tool_name, **tool_input)
            return result.output if result.success else {"error": result.error}
        except Exception as e:
            return {"error": str(e)}
    
    def _get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """You are Prometheus, an autonomous research agent. Your role is to:

1. Execute research tasks systematically
2. Use available tools to read files, write code, and manage the project
3. When a task is complete, output: <promise>PROMETHEUS_COMPLETE</promise>

Available capabilities:
- Read and write files
- Execute shell commands
- Manage git operations
- Track progress in state files

Always:
- Check state.json and operational.log at the start
- Commit your changes with descriptive messages
- Update task status when complete"""

    def _check_completion_promise(self, output: str) -> bool:
        """检查输出中是否包含完成承诺"""
        patterns = [
            '<promise>PROMETHEUS_COMPLETE</promise>',
            '<promise>TASK_COMPLETE</promise>',
            '<promise>COMPLETE</promise>',
        ]
        
        output_upper = output.upper()
        for pattern in patterns:
            if pattern.upper() in output_upper:
                return True
        
        # 使用正则匹配任意 promise 标签
        if re.search(r'<promise[^>]*>.*?</promise>', output, re.IGNORECASE):
            return True
        
        return False

    def run_phase(self, phase: Union[Phase, str]) -> bool:
        """
        Run all tasks in a phase.

        Args:
            phase: Phase to run

        Returns:
            True if all tasks completed successfully
        """
        if not self._initialized:
            self.initialize()

        if isinstance(phase, str):
            phase = Phase(phase)

        self.set_status(AgentStatus.RUNNING)

        try:
            # Update state
            self.state.update(current_phase=phase.value)

            # Get phase tasks
            phase_tasks = self.tasks.get_current_phase_tasks(phase.value)
            if not phase_tasks:
                self.logger.log(f"No tasks found for phase: {phase.value}", level="WARNING")
                return True

            self.logger.log(
                f"Starting phase: {phase.value} with {len(phase_tasks)} tasks",
                level="INFO"
            )

            # Process each task
            for task in phase_tasks:
                if task.get('passes'):
                    continue

                success = self.run_task(task['task_id'], phase.value)
                if not success:
                    if self._status == AgentStatus.WAITING_APPROVAL:
                        return False
                    # Continue with next task on failure

            self.set_status(AgentStatus.IDLE)
            return True

        except Exception as e:
            self.set_status(AgentStatus.ERROR, str(e))
            self.logger.error(f"Phase execution failed: {e}")
            return False

    def pause(self) -> None:
        """Pause the agent execution."""
        self.set_status(AgentStatus.PAUSED, "Agent paused by user")

    def resume(self) -> None:
        """Resume the agent execution."""
        if self._status == AgentStatus.PAUSED:
            self.set_status(AgentStatus.IDLE, "Agent resumed")

    def shutdown(self, summary: Optional[str] = None) -> None:
        """
        Shutdown the agent.

        Args:
            summary: Optional session summary
        """
        try:
            # End the session
            self.session.end_session(summary=summary, status="completed")

            # Commit any pending changes
            if self.config.auto_commit and self.git.has_changes():
                self.git.commit(
                    self.git.generate_commit_message(
                        "SESSION",
                        f"Session end: {datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    )
                )

            self.set_status(AgentStatus.COMPLETED, "Agent shutdown complete")
            self.logger.log("Prometheus agent shutdown complete", level="INFO")

        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")

    def get_status_report(self) -> Dict[str, Any]:
        """
        Get a comprehensive status report.

        Returns:
            Dictionary with agent status information
        """
        state = self.state.state
        progress = self.tasks.get_progress_summary()
        session_summary = self.session.get_session_summary()

        return {
            "agent_status": self._status.value,
            "initialized": self._initialized,
            "current_phase": state.get("current_phase"),
            "current_task": state.get("current_task"),
            "project": state.get("current_project"),
            "progress": progress,
            "session": session_summary,
            "tools_registered": len(self.tool_registry.list_tools()),
            "knowledge_stats": self.knowledge.get_statistics()
        }

    def register_tool(
        self,
        name: str,
        description: str,
        func: Callable,
        parameters: Optional[Dict[str, Any]] = None,
        required_params: Optional[List[str]] = None,
        category: str = "custom"
    ) -> AgentTool:
        """
        Register a custom tool.

        Args:
            name: Tool name
            description: Tool description
            func: Function to execute
            parameters: JSON schema for parameters
            required_params: List of required parameter names
            category: Tool category

        Returns:
            AgentTool instance
        """
        return self.tool_registry.register(
            name=name,
            description=description,
            func=func,
            parameters=parameters,
            required_params=required_params,
            category=category
        )


# ============================================================================
# Convenience Functions and Global Instance
# ============================================================================

_agent_instance: Optional[PrometheusAgent] = None


def get_agent(config: Optional[AgentConfig] = None, reload: bool = False) -> PrometheusAgent:
    """
    Get the global agent instance.

    Args:
        config: Optional agent configuration
        reload: Force reload the agent

    Returns:
        PrometheusAgent instance
    """
    global _agent_instance

    if _agent_instance is None or reload:
        _agent_instance = PrometheusAgent(config=config)

    return _agent_instance


def reset_agent() -> None:
    """Reset the global agent instance."""
    global _agent_instance
    if _agent_instance:
        _agent_instance.shutdown()
    _agent_instance = None


# ============================================================================
# CLI Interface
# ============================================================================

def main():
    """Command-line interface for the agent."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Prometheus Agent - Claude Agent SDK Integration"
    )

    parser.add_argument(
        '--init', action='store_true',
        help='Initialize the agent'
    )
    parser.add_argument(
        '--status', action='store_true',
        help='Show agent status'
    )
    parser.add_argument(
        '--run-task', type=str,
        help='Run a specific task by ID'
    )
    parser.add_argument(
        '--run-phase', type=str,
        help='Run all tasks in a phase'
    )
    parser.add_argument(
        '--list-tools', action='store_true',
        help='List all registered tools'
    )
    parser.add_argument(
        '--list-prompts', action='store_true',
        help='List all available prompts'
    )
    parser.add_argument(
        '--show-prompt', type=str,
        help='Show a specific prompt'
    )

    args = parser.parse_args()

    agent = get_agent()

    if args.init:
        print("Initializing Prometheus agent...")
        success = agent.initialize()
        print(f"Initialization {'successful' if success else 'failed'}")

    elif args.status:
        report = agent.get_status_report()
        print(json.dumps(report, indent=2, default=str))

    elif args.run_task:
        agent.initialize()
        success = agent.run_task(args.run_task)
        print(f"Task {'completed' if success else 'failed'}")

    elif args.run_phase:
        agent.initialize()
        success = agent.run_phase(args.run_phase)
        print(f"Phase {'completed' if success else 'failed'}")

    elif args.list_tools:
        tools = agent.tool_registry.list_tools()
        for tool in tools:
            print(f"- {tool.name}: {tool.description}")

    elif args.list_prompts:
        prompts = agent.prompt_loader.get_all_available_prompts()
        for prompt in prompts:
            print(f"- {prompt}")

    elif args.show_prompt:
        try:
            content = agent.prompt_loader.load_prompt(args.show_prompt)
            print(content)
        except FileNotFoundError as e:
            print(f"Error: {e}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()

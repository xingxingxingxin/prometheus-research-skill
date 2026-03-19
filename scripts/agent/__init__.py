#!/usr/bin/env python3
"""
Project Prometheus - Agent Module
==================================

This module provides Claude Agent SDK integration for Project Prometheus.

Classes:
    - PrometheusAgent: Main agent class
    - AgentConfig: Configuration dataclass
    - AgentStatus: Status enumeration
    - Phase: Research phases enumeration
    - PromptLoader: Prompt loading and management
    - ToolRegistry: Tool registration and execution
    - AgentTool: Tool representation
    - ToolDefinition: Tool schema and implementation
    - ParameterSchema: Parameter schema definition
    - LoopRunner: Autonomous loop execution
    - LoopConfig: Loop configuration
    - LoopStatus: Loop status enumeration
    - CheckpointManager: Checkpoint management
    - ContextManager: Context window management

Usage:
    from agent import PrometheusAgent, get_agent

    agent = get_agent()
    agent.initialize()
    agent.run_phase("literature_review")

    # Or use tool definitions directly
    from agent import register_all_tools, execute_tool

    register_all_tools()
    result = execute_tool("semantic_scholar_search", query="transformer")

    # Or run the autonomous loop
    from agent import LoopRunner, get_loop_runner

    runner = get_loop_runner()
    runner.run(max_iterations=10)
"""

from .prometheus_agent import (
    # Main classes
    PrometheusAgent,
    AgentConfig,
    AgentStatus,
    AgentContext,
    Phase,
    ToolResult,

    # Components
    PromptLoader,
    ToolRegistry,
    AgentTool,

    # Convenience functions
    get_agent,
    reset_agent,
)

from .tool_definitions import (
    # Classes
    ToolDefinition,
    ParameterSchema,
    ToolRegistry as ToolRegistryV2,

    # Functions
    register_all_tools,
    get_tool_registry,
    execute_tool,
    get_tools_by_category,
    get_tool_schema,
    list_all_tools,
)

from .loop_runner import (
    # Classes
    LoopRunner,
    LoopConfig,
    LoopStatus,
    LoopState,
    CheckpointManager,
    ContextManager,

    # Convenience functions
    get_loop_runner,
    reset_loop_runner,
)

__all__ = [
    # Main classes
    "PrometheusAgent",
    "AgentConfig",
    "AgentStatus",
    "AgentContext",
    "Phase",
    "ToolResult",

    # Components
    "PromptLoader",
    "ToolRegistry",
    "AgentTool",

    # Tool definitions
    "ToolDefinition",
    "ParameterSchema",
    "ToolRegistryV2",

    # Loop runner
    "LoopRunner",
    "LoopConfig",
    "LoopStatus",
    "LoopState",
    "CheckpointManager",
    "ContextManager",

    # Convenience functions - Agent
    "get_agent",
    "reset_agent",

    # Convenience functions - Tools
    "register_all_tools",
    "get_tool_registry",
    "execute_tool",
    "get_tools_by_category",
    "get_tool_schema",
    "list_all_tools",

    # Convenience functions - Loop
    "get_loop_runner",
    "reset_loop_runner",
]

__version__ = "1.0.0"

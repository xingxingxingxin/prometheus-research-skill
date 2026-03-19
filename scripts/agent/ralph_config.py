#!/usr/bin/env python3
"""
Project Prometheus - Ralph Loop Configuration
==============================================

This module provides configuration management and execution mode
detection for Ralph Loop integration.

Usage:
    from agent.ralph_config import (
        determine_execution_mode,
        TaskExecutionMode,
        RalphConfig
    )

    mode = determine_execution_mode(task, phase)
    if mode == TaskExecutionMode.RALPH_LOOP:
        # Use Ralph Loop execution
    else:
        # Standard single-pass execution
"""

from enum import Enum
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from pathlib import Path
import yaml


class TaskExecutionMode(Enum):
    """Execution mode for a task."""
    SINGLE_PASS = "single_pass"      # Execute once, check result
    RALPH_LOOP = "ralph_loop"        # Enable iterative execution


@dataclass
class RalphConfig:
    """
    Configuration for Ralph Loop behavior.

    Attributes:
        enabled: Whether Ralph Loop is globally enabled
        default_max_iterations: Default maximum iterations per task
        completion_promise: Default promise tag to detect
        iteration_timeout: Timeout per iteration in seconds
        backoff_strategy: Strategy for delays between iterations
        backoff_base: Base for exponential backoff
        max_backoff: Maximum backoff delay in seconds
        on_max_iterations: Behavior when max iterations reached
        phases_enabled: Set of phases where Ralph Loop is enabled
        task_overrides: Per-task configuration overrides
    """
    enabled: bool = True
    default_max_iterations: int = 20
    completion_promise: str = "PROMETHEUS_COMPLETE"
    iteration_timeout: int = 300
    backoff_strategy: str = "exponential"  # linear, exponential, fixed
    backoff_base: float = 2.0
    max_backoff: float = 60.0
    on_max_iterations: str = "checkpoint"  # checkpoint, fail, continue
    phases_enabled: Set[str] = field(default_factory=lambda: {
        'coding', 'execution', 'analysis'
    })
    task_overrides: Dict[str, Dict] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict) -> 'RalphConfig':
        """Create config from dictionary."""
        phases = data.get('phases_enabled', {})
        if isinstance(phases, dict):
            # Convert dict with boolean values to set of enabled phases
            phases_enabled = {k for k, v in phases.items() if v}
        elif isinstance(phases, (list, set)):
            phases_enabled = set(phases)
        else:
            phases_enabled = {'coding', 'execution', 'analysis'}

        return cls(
            enabled=data.get('enabled', True),
            default_max_iterations=data.get('default_max_iterations', 20),
            completion_promise=data.get('completion_promise', 'PROMETHEUS_COMPLETE'),
            iteration_timeout=data.get('iteration_timeout', 300),
            backoff_strategy=data.get('backoff_strategy', 'exponential'),
            backoff_base=data.get('backoff_base', 2.0),
            max_backoff=data.get('max_backoff', 60.0),
            on_max_iterations=data.get('on_max_iterations', 'checkpoint'),
            phases_enabled=phases_enabled,
            task_overrides=data.get('task_overrides', {})
        )

    def get_task_config(self, task_id: str) -> Dict:
        """
        Get configuration for a specific task, including any overrides.

        Args:
            task_id: Task identifier

        Returns:
            Configuration dictionary for the task
        """
        base_config = {
            'max_iterations': self.default_max_iterations,
            'completion_promise': self.completion_promise,
            'iteration_timeout': self.iteration_timeout
        }

        # Apply task-specific overrides
        if task_id in self.task_overrides:
            base_config.update(self.task_overrides[task_id])

        return base_config


# Default phases that benefit from Ralph Loop iteration
RALPH_DEFAULT_PHASES = {
    'coding',       # Code implementation often needs iteration
    'execution',    # Running experiments may need debugging
    'analysis',     # Data analysis may need refinement
}

# Phases that typically don't need iteration
SINGLE_PASS_PHASES = {
    'literature_review',  # Usually one-shot search and summarize
    'writing',            # Writing can be done incrementally without loop
    'humanization',       # Text transformation is usually straightforward
    'latex',              # Formatting is deterministic
    'review',             # Review is typically one-shot
}


def determine_execution_mode(
    task: Dict,
    phase: str,
    config: Optional[RalphConfig] = None,
    force_mode: Optional[TaskExecutionMode] = None
) -> TaskExecutionMode:
    """
    Determine the execution mode for a task.

    Args:
        task: Task dictionary with properties
        phase: Current phase name
        config: RalphConfig instance (uses default if None)
        force_mode: Override mode if specified

    Returns:
        TaskExecutionMode indicating how to execute the task
    """
    # Allow force override
    if force_mode:
        return force_mode

    # Use default config if not provided
    if config is None:
        config = RalphConfig()

    # Check if Ralph Loop is globally enabled
    if not config.enabled:
        return TaskExecutionMode.SINGLE_PASS

    # Check for explicit task-level setting
    if task.get('ralph_loop') is True:
        return TaskExecutionMode.RALPH_LOOP
    if task.get('ralph_loop') is False:
        return TaskExecutionMode.SINGLE_PASS

    # Check for task override in config
    task_id = task.get('task_id', task.get('id', ''))
    if task_id in config.task_overrides:
        override = config.task_overrides[task_id]
        if override.get('enabled') is True:
            return TaskExecutionMode.RALPH_LOOP
        if override.get('enabled') is False:
            return TaskExecutionMode.SINGLE_PASS

    # Check phase-based enabling
    phase_lower = phase.lower().replace(' ', '_').replace('-', '_')

    # Match phase name variations
    if phase_lower in config.phases_enabled:
        return TaskExecutionMode.RALPH_LOOP

    # Partial phase matching (e.g., "Phase 3: Coding" matches "coding")
    for enabled_phase in config.phases_enabled:
        if enabled_phase.lower() in phase_lower:
            return TaskExecutionMode.RALPH_LOOP

    # Check task complexity indicators
    if _is_complex_task(task):
        return TaskExecutionMode.RALPH_LOOP

    # Default to single-pass
    return TaskExecutionMode.SINGLE_PASS


def _is_complex_task(task: Dict) -> bool:
    """
    Determine if a task is complex enough to warrant Ralph Loop.

    Args:
        task: Task dictionary

    Returns:
        True if task appears complex
    """
    # Check for multiple completion criteria
    criteria = task.get('completion_criteria', [])
    if isinstance(criteria, list) and len(criteria) > 2:
        return True

    # Check for code-related keywords
    code_keywords = ['implement', 'code', 'debug', 'fix', 'refactor', 'test']
    desc = task.get('description', task.get('desc', '')).lower()
    if any(kw in desc for kw in code_keywords):
        return True

    # Check for iterative keywords
    iterative_keywords = ['iterate', 'refine', 'improve', 'optimize']
    if any(kw in desc for kw in iterative_keywords):
        return True

    return False


def load_ralph_config(config_path: Optional[Path] = None) -> RalphConfig:
    """
    Load Ralph configuration from YAML file.

    Args:
        config_path: Path to config file (defaults to config.yaml in project root)

    Returns:
        RalphConfig instance
    """
    if config_path is None:
        # Find config.yaml in project root
        config_path = Path(__file__).parent.parent / 'config.yaml'

    if not config_path.exists():
        return RalphConfig()

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            full_config = yaml.safe_load(f) or {}

        ralph_section = full_config.get('ralph', {})
        return RalphConfig.from_dict(ralph_section)

    except Exception as e:
        print(f"[RALPH] Warning: Could not load config: {e}")
        return RalphConfig()


def get_iteration_backoff(
    iteration: int,
    strategy: str = "exponential",
    base: float = 2.0,
    max_backoff: float = 60.0
) -> float:
    """
    Calculate backoff delay for a given iteration.

    Args:
        iteration: Current iteration number
        strategy: Backoff strategy (linear, exponential, fixed)
        base: Base delay or multiplier
        max_backoff: Maximum backoff delay

    Returns:
        Delay in seconds
    """
    if strategy == "fixed":
        return min(base, max_backoff)

    if strategy == "linear":
        delay = base * iteration
    else:  # exponential
        delay = base ** min(iteration, 10)  # Cap exponent to avoid overflow

    return min(delay, max_backoff)


def should_use_ralph_for_phase(phase: str, config: Optional[RalphConfig] = None) -> bool:
    """
    Quick check if Ralph Loop should be used for a phase.

    Args:
        phase: Phase name
        config: Optional RalphConfig

    Returns:
        True if Ralph Loop is recommended for this phase
    """
    if config is None:
        config = RalphConfig()

    phase_lower = phase.lower().replace(' ', '_').replace('-', '_')

    for enabled_phase in config.phases_enabled:
        if enabled_phase.lower() in phase_lower:
            return True

    return False


# Convenience function for CLI
def print_ralph_status(config: RalphConfig) -> None:
    """Print current Ralph configuration status."""
    print("\n=== Ralph Loop Configuration ===")
    print(f"Enabled: {config.enabled}")
    print(f"Max Iterations: {config.default_max_iterations}")
    print(f"Completion Promise: {config.completion_promise}")
    print(f"Iteration Timeout: {config.iteration_timeout}s")
    print(f"On Max Iterations: {config.on_max_iterations}")
    print(f"Enabled Phases: {', '.join(config.phases_enabled)}")

    if config.task_overrides:
        print(f"Task Overrides: {len(config.task_overrides)} tasks")

    print("================================\n")

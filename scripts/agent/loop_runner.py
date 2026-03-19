#!/usr/bin/env python3
"""
Project Prometheus - Loop Runner
=================================

This module implements the agent execution loop, managing sessions,
context switching, and progress saving for autonomous operation.

Features:
- Main execution loop with configurable iteration limits
- Session management and automatic checkpointing
- Context window management and summarization
- Progress tracking and persistence
- Error recovery and retry mechanisms
- Graceful shutdown handling

Usage:
    from agent.loop_runner import LoopRunner, get_loop_runner

    # Create and run the loop
    runner = get_loop_runner()
    runner.run(max_iterations=10)

    # Or run with custom configuration
    runner = LoopRunner(
        max_iterations=100,
        checkpoint_interval=5,
        auto_commit=True
    )
    runner.run()
"""

import json
import os
import signal
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Type, Union

# Add Core directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "Core"))

from progress import (
    StateManager, TaskManager, LogManager, KnowledgeBaseManager,
    SessionManager, GitManager, CommunicationManager,
    get_state, get_tasks, get_logger, get_knowledge, get_session, get_git, get_comm
)

# Import agent module
sys.path.insert(0, str(Path(__file__).parent))
from prometheus_agent import (
    PrometheusAgent, AgentConfig, AgentStatus, AgentContext, Phase,
    get_agent, reset_agent
)

# Import Ralph Loop modules
try:
    from ralph_loop import RalphLoopManager, RalphStatus, get_ralph, reset_ralph
    from ralph_config import (
        determine_execution_mode, TaskExecutionMode, RalphConfig,
        load_ralph_config, get_iteration_backoff
    )
    RALPH_AVAILABLE = True
except ImportError:
    RALPH_AVAILABLE = False

# Import Ralph Debug module
try:
    from ralph_debug import RalphDebugger, DebugStatus, get_debugger, with_ralph_debug
    RALPH_DEBUG_AVAILABLE = True
except ImportError:
    RALPH_DEBUG_AVAILABLE = False


# ============================================================================
# Enums and Data Classes
# ============================================================================

class LoopStatus(Enum):
    """Loop execution status."""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"
    COMPLETED = "completed"


@dataclass
class LoopConfig:
    """Configuration for the loop runner."""
    # Iteration settings
    max_iterations: int = 100
    max_time_seconds: int = 3600  # 1 hour default

    # Checkpoint settings
    checkpoint_interval: int = 5  # Create checkpoint every N iterations
    auto_save_progress: bool = True

    # Context management
    max_context_tokens: int = 100000
    context_summarization_threshold: float = 0.8  # Summarize at 80% capacity

    # Error handling
    max_consecutive_errors: int = 3
    error_backoff_base: float = 2.0  # Exponential backoff base
    max_error_backoff: float = 60.0  # Maximum backoff in seconds

    # Behavior settings
    auto_commit: bool = True
    commit_interval: int = 1  # Commit every N completed tasks
    pause_on_approval_needed: bool = True
    check_commands_interval: int = 3  # Check for commands every N iterations

    # Ralph Loop settings
    ralph_enabled: bool = True  # Enable Ralph Loop integration
    ralph_max_iterations: int = 20  # Max iterations per Ralph Loop task

    # Paths
    loop_state_file: Optional[Path] = None


@dataclass
class LoopState:
    """State of the loop execution."""
    iteration: int = 0
    started_at: Optional[str] = None
    last_iteration_at: Optional[str] = None
    tasks_completed_this_run: int = 0
    consecutive_errors: int = 0
    last_error: Optional[str] = None
    current_task_id: Optional[str] = None
    status: LoopStatus = LoopStatus.IDLE
    checkpoints: List[Dict[str, Any]] = field(default_factory=list)


# ============================================================================
# Checkpoint Manager
# ============================================================================

class CheckpointManager:
    """Manages checkpoints for the loop runner."""

    def __init__(self, checkpoint_dir: Optional[Path] = None):
        """Initialize checkpoint manager.

        Args:
            checkpoint_dir: Directory to store checkpoints.
        """
        self.checkpoint_dir = checkpoint_dir or \
            Path(__file__).parent.parent / "Checkpoints"
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def create_checkpoint(
        self,
        loop_state: LoopState,
        agent_context: Optional[AgentContext] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a checkpoint.

        Args:
            loop_state: Current loop state.
            agent_context: Current agent context.
            metadata: Additional metadata.

        Returns:
            Checkpoint ID.
        """
        checkpoint_id = f"checkpoint_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

        checkpoint = {
            "checkpoint_id": checkpoint_id,
            "created_at": datetime.now().isoformat(),
            "loop_state": {
                "iteration": loop_state.iteration,
                "tasks_completed_this_run": loop_state.tasks_completed_this_run,
                "consecutive_errors": loop_state.consecutive_errors,
                "current_task_id": loop_state.current_task_id,
                "status": loop_state.status.value,
            },
            "agent_context": {
                "phase": agent_context.phase.value if agent_context else None,
                "task_id": agent_context.task_id if agent_context else None,
                "attempt": agent_context.attempt if agent_context else 0,
                "metadata": agent_context.metadata if agent_context else {},
            } if agent_context else None,
            "metadata": metadata or {},
        }

        # Save checkpoint file
        checkpoint_file = self.checkpoint_dir / f"{checkpoint_id}.json"
        with open(checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(checkpoint, f, indent=2, ensure_ascii=False)

        # Add to loop state checkpoints list
        loop_state.checkpoints.append({
            "checkpoint_id": checkpoint_id,
            "created_at": checkpoint["created_at"],
            "iteration": loop_state.iteration,
        })

        return checkpoint_id

    def load_checkpoint(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """Load a checkpoint.

        Args:
            checkpoint_id: Checkpoint ID to load.

        Returns:
            Checkpoint data or None if not found.
        """
        checkpoint_file = self.checkpoint_dir / f"{checkpoint_id}.json"

        if not checkpoint_file.exists():
            return None

        with open(checkpoint_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_latest_checkpoint(self) -> Optional[Dict[str, Any]]:
        """Get the most recent checkpoint.

        Returns:
            Latest checkpoint data or None if no checkpoints exist.
        """
        checkpoints = list(self.checkpoint_dir.glob("checkpoint_*.json"))

        if not checkpoints:
            return None

        # Sort by modification time, get latest
        latest = max(checkpoints, key=lambda p: p.stat().st_mtime)
        return self.load_checkpoint(latest.stem)

    def list_checkpoints(self, limit: int = 10) -> List[Dict[str, Any]]:
        """List available checkpoints.

        Args:
            limit: Maximum number of checkpoints to return.

        Returns:
            List of checkpoint metadata.
        """
        checkpoints = list(self.checkpoint_dir.glob("checkpoint_*.json"))

        # Sort by modification time, newest first
        checkpoints.sort(key=lambda p: p.stat().st_mtime, reverse=True)

        result = []
        for cp_file in checkpoints[:limit]:
            try:
                with open(cp_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                result.append({
                    "checkpoint_id": data.get("checkpoint_id"),
                    "created_at": data.get("created_at"),
                    "iteration": data.get("loop_state", {}).get("iteration"),
                })
            except (json.JSONDecodeError, IOError):
                continue

        return result

    def cleanup_old_checkpoints(self, keep_count: int = 10) -> int:
        """Remove old checkpoints, keeping only the most recent.

        Args:
            keep_count: Number of checkpoints to keep.

        Returns:
            Number of checkpoints removed.
        """
        checkpoints = list(self.checkpoint_dir.glob("checkpoint_*.json"))

        if len(checkpoints) <= keep_count:
            return 0

        # Sort by modification time, newest first
        checkpoints.sort(key=lambda p: p.stat().st_mtime, reverse=True)

        # Remove old checkpoints
        removed = 0
        for cp_file in checkpoints[keep_count:]:
            try:
                cp_file.unlink()
                removed += 1
            except OSError:
                continue

        return removed


# ============================================================================
# Context Manager
# ============================================================================

class ContextManager:
    """Manages context window for the loop runner."""

    def __init__(
        self,
        max_tokens: int = 100000,
        summarization_threshold: float = 0.8
    ):
        """Initialize context manager.

        Args:
            max_tokens: Maximum context token limit.
            summarization_threshold: Threshold ratio to trigger summarization.
        """
        self.max_tokens = max_tokens
        self.summarization_threshold = summarization_threshold
        self._context_history: List[Dict[str, Any]] = []
        self._current_tokens_estimate = 0

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text.

        Simple estimation: ~4 characters per token.

        Args:
            text: Text to estimate.

        Returns:
            Estimated token count.
        """
        return len(text) // 4

    def add_context(
        self,
        content: str,
        context_type: str = "general",
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add content to context history.

        Args:
            content: Content to add.
            context_type: Type of context (e.g., "task", "error", "result").
            metadata: Additional metadata.
        """
        token_estimate = self.estimate_tokens(content)

        self._context_history.append({
            "timestamp": datetime.now().isoformat(),
            "content": content,
            "context_type": context_type,
            "token_estimate": token_estimate,
            "metadata": metadata or {},
        })

        self._current_tokens_estimate += token_estimate

    def should_summarize(self) -> bool:
        """Check if context should be summarized.

        Returns:
            True if summarization threshold exceeded.
        """
        return (
            self._current_tokens_estimate >=
            self.max_tokens * self.summarization_threshold
        )

    def get_context_summary(self) -> Dict[str, Any]:
        """Get summary of current context.

        Returns:
            Context summary dictionary.
        """
        by_type: Dict[str, int] = {}
        for ctx in self._context_history:
            ctx_type = ctx.get("context_type", "general")
            by_type[ctx_type] = by_type.get(ctx_type, 0) + 1

        return {
            "total_entries": len(self._context_history),
            "estimated_tokens": self._current_tokens_estimate,
            "max_tokens": self.max_tokens,
            "utilization": round(self._current_tokens_estimate / self.max_tokens, 2),
            "entries_by_type": by_type,
            "should_summarize": self.should_summarize(),
        }

    def create_summary_for_handoff(self) -> str:
        """Create a summary for context handoff.

        Returns:
            Summary string.
        """
        if not self._context_history:
            return "No previous context available."

        # Group by type
        by_type: Dict[str, List[str]] = {}
        for ctx in self._context_history:
            ctx_type = ctx.get("context_type", "general")
            if ctx_type not in by_type:
                by_type[ctx_type] = []
            by_type[ctx_type].append(ctx.get("content", "")[:200])  # Truncate

        lines = ["## Context Summary for Handoff\n"]

        for ctx_type, contents in by_type.items():
            lines.append(f"### {ctx_type.title()} ({len(contents)} entries)")
            for i, content in enumerate(contents[-5:], 1):  # Last 5 of each type
                lines.append(f"{i}. {content}...")
            lines.append("")

        return "\n".join(lines)

    def clear(self) -> None:
        """Clear context history."""
        self._context_history.clear()
        self._current_tokens_estimate = 0


# ============================================================================
# Loop Runner
# ============================================================================

class LoopRunner:
    """
    Main execution loop for autonomous agent operation.

    This class manages the continuous execution of the agent,
    handling session management, context switching, progress saving,
    and error recovery.
    """

    def __init__(
        self,
        config: Optional[LoopConfig] = None,
        agent: Optional[PrometheusAgent] = None,
        state_manager: Optional[StateManager] = None,
        task_manager: Optional[TaskManager] = None,
        log_manager: Optional[LogManager] = None,
        session_manager: Optional[SessionManager] = None,
        git_manager: Optional[GitManager] = None,
        comm_manager: Optional[CommunicationManager] = None,
    ):
        """Initialize the loop runner.

        Args:
            config: Loop configuration.
            agent: Prometheus agent instance.
            state_manager: State manager instance.
            task_manager: Task manager instance.
            log_manager: Log manager instance.
            session_manager: Session manager instance.
            git_manager: Git manager instance.
            comm_manager: Communication manager instance.
        """
        self.config = config or LoopConfig()

        # Initialize managers
        self.state = state_manager or get_state()
        self.tasks = task_manager or get_tasks()
        self.logger = log_manager or get_logger()
        self.session = session_manager or get_session()
        self.git = git_manager or get_git()
        self.comm = comm_manager or get_comm()

        # Initialize agent
        self.agent = agent or get_agent()

        # Initialize helper managers
        self.checkpoint_manager = CheckpointManager()
        self.context_manager = ContextManager(
            max_tokens=self.config.max_context_tokens,
            summarization_threshold=self.config.context_summarization_threshold
        )

        # Loop state
        self._loop_state = LoopState()
        self._shutdown_requested = False
        self._pause_requested = False

        # Register signal handlers
        self._register_signal_handlers()

        # Callbacks
        self._pre_iteration_callbacks: List[Callable] = []
        self._post_iteration_callbacks: List[Callable] = []
        self._error_callbacks: List[Callable] = []

        # Ralph Loop integration
        self.ralph: Optional[Any] = None
        self.ralph_config: Optional[Any] = None
        if RALPH_AVAILABLE and self.config.ralph_enabled:
            self.ralph_config = load_ralph_config()
            self.ralph = get_ralph({
                'max_iterations': self.config.ralph_max_iterations,
                'completion_promise': 'PROMETHEUS_COMPLETE'
            })
            self.logger.log("Ralph Loop integration enabled", level="INFO")

    def _register_signal_handlers(self) -> None:
        """Register signal handlers for graceful shutdown."""
        def handle_shutdown(signum, frame):
            self.logger.log(f"Received signal {signum}, requesting shutdown", level="INFO")
            self._shutdown_requested = True

        def handle_pause(signum, frame):
            self.logger.log(f"Received signal {signum}, toggling pause", level="INFO")
            self._pause_requested = not self._pause_requested

        # Register handlers (may not work on all platforms)
        try:
            signal.signal(signal.SIGINT, handle_shutdown)
            signal.signal(signal.SIGTERM, handle_shutdown)
        except (OSError, ValueError):
            pass  # Signal handling not supported

    def register_callback(
        self,
        callback_type: str,
        callback: Callable
    ) -> None:
        """Register a callback function.

        Args:
            callback_type: Type of callback ('pre_iteration', 'post_iteration', 'error').
            callback: Callback function.
        """
        if callback_type == 'pre_iteration':
            self._pre_iteration_callbacks.append(callback)
        elif callback_type == 'post_iteration':
            self._post_iteration_callbacks.append(callback)
        elif callback_type == 'error':
            self._error_callbacks.append(callback)

    def _execute_callbacks(self, callbacks: List[Callable], *args, **kwargs) -> None:
        """Execute a list of callbacks.

        Args:
            callbacks: List of callback functions.
            *args: Positional arguments for callbacks.
            **kwargs: Keyword arguments for callbacks.
        """
        for callback in callbacks:
            try:
                callback(*args, **kwargs)
            except Exception as e:
                self.logger.error(f"Callback error: {e}")

    def _check_commands(self) -> Optional[str]:
        """Check for commands from inbox.

        Returns:
            Command string or None.
        """
        commands = self.comm.check_commands()

        for cmd in commands:
            cmd_upper = cmd.upper().strip()

            if cmd_upper == "PAUSE":
                self._pause_requested = True
                self.logger.log("Pause command received", level="INFO")
                return "PAUSE"

            elif cmd_upper == "RESUME":
                self._pause_requested = False
                self.logger.log("Resume command received", level="INFO")
                return "RESUME"

            elif cmd_upper == "STOP" or cmd_upper == "SHUTDOWN":
                self._shutdown_requested = True
                self.logger.log("Stop command received", level="INFO")
                return "STOP"

            elif cmd_upper.startswith("APPROVE"):
                # Handle approval
                self.logger.log(f"Approval received: {cmd}", level="INFO")
                return cmd

            elif cmd_upper.startswith("REJECT"):
                # Handle rejection
                self.logger.log(f"Rejection received: {cmd}", level="INFO")
                return cmd

        return None

    def _handle_pause(self) -> None:
        """Handle pause state."""
        self._loop_state.status = LoopStatus.PAUSED
        self.logger.log("Loop paused, waiting for resume...", level="INFO")

        # Create checkpoint while paused
        self.checkpoint_manager.create_checkpoint(
            self._loop_state,
            self.agent._current_context
        )

        # Wait loop
        while self._pause_requested and not self._shutdown_requested:
            time.sleep(1)

            # Check for resume command periodically
            cmd = self._check_commands()
            if cmd == "RESUME":
                break

        self._loop_state.status = LoopStatus.RUNNING
        self.logger.log("Loop resumed", level="INFO")

    def _handle_error(self, error: Exception, context: Optional[str] = None) -> None:
        """Handle an error during execution.

        Args:
            error: The exception that occurred.
            context: Additional context about the error.
        """
        self._loop_state.consecutive_errors += 1
        self._loop_state.last_error = str(error)

        # Log the error
        self.logger.error(f"Loop error: {error}", trace=context)

        # Record in session
        self.session.record_error(
            error_type=type(error).__name__,
            error_message=str(error),
            context=context
        )

        # Add to context
        self.context_manager.add_context(
            f"Error: {error}",
            context_type="error",
            metadata={"consecutive_errors": self._loop_state.consecutive_errors}
        )

        # Execute error callbacks
        self._execute_callbacks(
            self._error_callbacks,
            error=error,
            context=context,
            consecutive_errors=self._loop_state.consecutive_errors
        )

        # Check if Ralph Debug is available and should be used
        if RALPH_DEBUG_AVAILABLE and self._loop_state.consecutive_errors <= self.config.max_consecutive_errors:
            self._attempt_ralph_debug(error, context)

        # Check if we should stop due to too many errors
        if self._loop_state.consecutive_errors >= self.config.max_consecutive_errors:
            self.logger.error(
                f"Max consecutive errors ({self.config.max_consecutive_errors}) reached. "
                "Requesting shutdown."
            )
            self._shutdown_requested = True

    def _attempt_ralph_debug(self, error: Exception, context: Optional[str] = None) -> Optional[bool]:
        """Attempt to debug using Ralph Debug loop.

        Args:
            error: The exception that occurred
            context: Additional context

        Returns:
            True if debug succeeded, False if failed, None if not attempted
        """
        if not RALPH_DEBUG_AVAILABLE:
            return None

        debugger = get_debugger({
            'max_debug_iterations': 3,  # Quick debug attempts
            'debug_timeout': 60
        })

        task_id = self._loop_state.current_task_id or 'unknown'
        phase = self.agent._current_context.phase.value if hasattr(self.agent, '_current_context') and self.agent._current_context else 'unknown'

        self.logger.log(
            f"[RALPH-DEBUG] Attempting debug for error: {type(error).__name__}",
            level="INFO"
        )

        # Execute with debug - the retry logic is handled internally
        result = debugger.execute_with_debug(
            func=lambda: self._retry_current_task(),
            error_context={
                'task_id': task_id,
                'phase': phase,
                'original_error': str(error)
            },
            max_debug_iterations=3
        )

        if result.success:
            self.logger.log(
                f"[RALPH-DEBUG] Debug successful after {result.iteration} iterations",
                level="INFO"
            )
            self._loop_state.consecutive_errors = 0  # Reset on successful debug
            return True
        elif result.needs_human_help:
            self.logger.log(
                f"[RALPH-DEBUG] Debug requires human intervention",
                level="WARNING"
            )
            # Pause for human review
            self._pause_requested = True
            return False

        return False

    def _retry_current_task(self) -> bool:
        """Retry the current task after a debug fix attempt.

        Returns:
            True if retry succeeded
        """
        if not self._loop_state.current_task_id:
            return False

        # Get task info
        task_info = self._get_next_task()
        if not task_info:
            return False

        task = task_info['task']
        phase_id = task_info['phase_id']
        task_id = task['task_id']

        try:
            # Re-run the task
            success = self.agent.run_task(task_id, phase_id)
            return success
        except Exception as e:
            # Debug loop will catch this
            raise

    def _apply_error_backoff(self) -> None:
        """Apply exponential backoff after errors."""
        if self._loop_state.consecutive_errors > 0:
            backoff = min(
                self.config.error_backoff_base ** self._loop_state.consecutive_errors,
                self.config.max_error_backoff
            )
            self.logger.log(
                f"Applying backoff: {backoff:.1f}s after {self._loop_state.consecutive_errors} errors",
                level="INFO"
            )
            time.sleep(backoff)

    def _create_checkpoint_if_needed(self) -> None:
        """Create checkpoint if interval reached."""
        if self._loop_state.iteration % self.config.checkpoint_interval == 0:
            checkpoint_id = self.checkpoint_manager.create_checkpoint(
                self._loop_state,
                self.agent._current_context
            )
            self.logger.log(
                f"Checkpoint created: {checkpoint_id} at iteration {self._loop_state.iteration}",
                level="INFO"
            )

    def _commit_if_needed(self) -> None:
        """Create git commit if needed."""
        if (self.config.auto_commit and
            self._loop_state.tasks_completed_this_run % self.config.commit_interval == 0 and
            self.git.has_changes()):

            commit_message = self.git.generate_commit_message(
                "LOOP",
                f"Auto-commit after {self._loop_state.tasks_completed_this_run} tasks"
            )
            success = self.git.commit(commit_message, add_all=True)

            if success:
                self.logger.log("Auto-commit created", level="INFO")
            else:
                self.logger.log("Auto-commit failed", level="WARNING")

    def _get_next_task(self) -> Optional[Dict[str, Any]]:
        """Get the next task to execute.

        Returns:
            Task info dictionary or None if no tasks pending.
        """
        task_info = self.tasks.get_next_pending_task()

        if not task_info:
            return None

        # Check if agent is waiting for approval
        if self.agent.status == AgentStatus.WAITING_APPROVAL:
            if self.config.pause_on_approval_needed:
                self._pause_requested = True
            return None

        return task_info

    def _execute_iteration(self) -> bool:
        """Execute a single iteration of the loop.

        Returns:
            True if a task was completed, False otherwise.
        """
        iteration_start = datetime.now()
        self._loop_state.iteration += 1

        # Execute pre-iteration callbacks
        self._execute_callbacks(
            self._pre_iteration_callbacks,
            iteration=self._loop_state.iteration
        )

        # Log iteration start
        self.logger.log(
            f"Starting iteration {self._loop_state.iteration}",
            level="INFO"
        )

        # Check for commands periodically
        if self._loop_state.iteration % self.config.check_commands_interval == 0:
            self._check_commands()

        # Handle pause state
        if self._pause_requested:
            self._handle_pause()

        # Check for shutdown
        if self._shutdown_requested:
            return False

        # Get next task
        task_info = self._get_next_task()

        if not task_info:
            self.logger.log("No pending tasks found", level="INFO")

            # Check if all tasks are complete
            progress = self.tasks.get_progress_summary()
            if progress.get('pending_tasks', 0) == 0:
                self.logger.log("All tasks completed!", level="INFO")
                self._loop_state.status = LoopStatus.COMPLETED
                self._shutdown_requested = True

            return False

        # Extract task info
        task = task_info['task']
        phase_id = task_info['phase_id']
        task_id = task['task_id']

        self._loop_state.current_task_id = task_id

        # Add to context
        self.context_manager.add_context(
            f"Task: {task_id} - {task.get('description', 'No description')}",
            context_type="task",
            metadata={"phase_id": phase_id, "task_id": task_id}
        )

        # Determine execution mode (Ralph Loop vs Single-pass)
        use_ralph = False
        if RALPH_AVAILABLE and self.ralph and self.config.ralph_enabled:
            mode = determine_execution_mode(task, phase_id, self.ralph_config)
            use_ralph = (mode == TaskExecutionMode.RALPH_LOOP)
            if use_ralph:
                self.logger.log(
                    f"Using Ralph Loop mode for task {task_id}",
                    level="INFO"
                )

        # Execute task via agent
        task_completed = False

        try:
            # Ensure agent is initialized
            if not self.agent._initialized:
                self.agent.initialize()

            # Run the task (with or without Ralph Loop)
            if use_ralph:
                success = self._execute_with_ralph(task, phase_id)
            else:
                success = self.agent.run_task(task_id, phase_id)

            if success:
                # Mark task as completed
                self.tasks.mark_task_passed(phase_id, task_id)
                self._loop_state.tasks_completed_this_run += 1
                self._loop_state.consecutive_errors = 0  # Reset error counter
                task_completed = True

                self.logger.log(
                    f"Task {task_id} completed successfully",
                    level="INFO"
                )

                # Add to context
                self.context_manager.add_context(
                    f"Completed: {task_id}",
                    context_type="result",
                    metadata={"success": True}
                )

        except Exception as e:
            self._handle_error(e, context=f"Task: {task_id}")

        finally:
            self._loop_state.current_task_id = None
            self._loop_state.last_iteration_at = datetime.now().isoformat()

        # Execute post-iteration callbacks
        self._execute_callbacks(
            self._post_iteration_callbacks,
            iteration=self._loop_state.iteration,
            task_completed=task_completed
        )

        # Create checkpoint if needed
        self._create_checkpoint_if_needed()

        # Commit if needed
        self._commit_if_needed()

        # Check context capacity
        if self.context_manager.should_summarize():
            summary = self.context_manager.create_summary_for_handoff()
            self.session.increment_context_window()
            self.context_manager.clear()

            # Add summary as new context
            self.context_manager.add_context(
                summary,
                context_type="handoff_summary"
            )

            self.logger.log(
                "Context window summarized and cleared",
                level="INFO"
            )

        return task_completed

    def _execute_with_ralph(self, task: Dict, phase_id: str) -> bool:
        """Execute a task using Ralph Loop mode.

        Ralph Loop allows iterative execution until completion promise
        is detected or max iterations reached.

        Args:
            task: Task dictionary
            phase_id: Phase identifier

        Returns:
            True if task completed successfully
        """
        task_id = task.get('task_id', task.get('id', 'unknown'))
        task_desc = task.get('description', task.get('desc', ''))

        # Get task-specific config
        task_config = self.ralph_config.get_task_config(task_id) if self.ralph_config else {}

        # Update Ralph manager with task config
        max_iterations = task_config.get('max_iterations', self.config.ralph_max_iterations)
        completion_promise = task_config.get('completion_promise', 'PROMETHEUS_COMPLETE')

        # Prepare Ralph state file
        prompt = self._generate_ralph_prompt(task, phase_id, task_config)
        self.ralph.prepare_state_file(
            task_id=task_id,
            task_desc=task_desc,
            prompt=prompt,
            phase=phase_id
        )

        self.logger.log(
            f"[RALPH] Starting Ralph Loop for {task_id} | max_iterations={max_iterations}",
            level="INFO"
        )

        # Iterative execution loop
        iteration_count = 0
        success = False

        while self.ralph.should_continue():
            iteration_count += 1

            self.logger.log(
                f"[RALPH] Iteration {iteration_count}/{max_iterations} for {task_id}",
                level="INFO"
            )

            try:
                # Run the task
                result = self.agent.run_task(task_id, phase_id)

                # Check for completion promise in output
                # (The agent's output should contain the promise if complete)
                if result and self._check_ralph_completion():
                    self.logger.log(
                        f"[RALPH] Completion promise detected for {task_id}",
                        level="INFO"
                    )
                    self.ralph.mark_completed()
                    success = True
                    break

                # Increment iteration
                self.ralph.increment_iteration(
                    iteration_summary=f"Completed iteration {iteration_count}"
                )

                # Apply backoff delay
                backoff = get_iteration_backoff(
                    iteration=iteration_count,
                    strategy="exponential",
                    base=2.0,
                    max_backoff=30.0
                )
                if backoff > 0:
                    import time
                    time.sleep(backoff)

            except Exception as e:
                self.logger.error(f"[RALPH] Error in iteration {iteration_count}: {e}")
                self.ralph.increment_iteration(
                    iteration_summary=f"Error: {str(e)[:100]}"
                )

        # Handle max iterations reached
        if not success and iteration_count >= max_iterations:
            report = self.ralph.mark_max_iterations_reached()
            self._handle_ralph_max_iterations(task, phase_id, report)

        return success

    def _generate_ralph_prompt(self, task: Dict, phase_id: str, config: Dict) -> str:
        """Generate prompt for Ralph Loop execution.

        Args:
            task: Task dictionary
            phase_id: Phase identifier
            config: Task-specific configuration

        Returns:
            Generated prompt string
        """
        task_id = task.get('task_id', task.get('id', 'unknown'))
        task_desc = task.get('description', task.get('desc', ''))
        max_iterations = config.get('max_iterations', self.config.ralph_max_iterations)
        completion_promise = config.get('completion_promise', 'PROMETHEUS_COMPLETE')

        # Load prompt template
        template_path = Path(__file__).parent.parent / "Core" / "prompts" / "ralph_task.md"

        try:
            if template_path.exists():
                template = template_path.read_text(encoding='utf-8')
                # Replace placeholders
                prompt = template.replace('{{task_id}}', task_id)
                prompt = prompt.replace('{{task_desc}}', task_desc)
                prompt = prompt.replace('{{phase}}', phase_id)
                prompt = prompt.replace('{{max_iterations}}', str(max_iterations))
                prompt = prompt.replace('{{completion_promise}}', completion_promise)
                prompt = prompt.replace('{{iteration}}', '0')
                prompt = prompt.replace('{{project_context}}', f'Phase: {phase_id}')
                prompt = prompt.replace('{{previous_attempts}}', 'None - first iteration')
                prompt = prompt.replace('{{files_modified}}', 'None yet')
                prompt = prompt.replace('{{completion_criteria}}', task_desc)
                prompt = prompt.replace('{{task_specific_context}}', '')
                return prompt
        except Exception as e:
            self.logger.error(f"Error loading Ralph prompt template: {e}")

        # Fallback to basic prompt
        return f"""# Ralph Loop Task: {task_id}

## Task Description
{task_desc}

## Phase: {phase_id}

## Instructions
1. Complete this task through iterative improvement
2. Each iteration, review previous work and continue
3. When complete, output: <promise>{completion_promise}</promise>

## Max Iterations: {max_iterations}
"""

    def _check_ralph_completion(self) -> bool:
        """Check if Ralph Loop completion was signaled.

        Checks git commits and recent files for completion promise.

        Returns:
            True if completion detected
        """
        import subprocess

        try:
            # Check recent git commit messages for promise
            result = subprocess.run(
                ['git', 'log', '-1', '--pretty=%B'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                if self.ralph.check_completion(result.stdout):
                    return True

            # Check operational log
            log_path = Path(__file__).parent.parent / "Logs" / "operational.log"
            if log_path.exists():
                recent_log = subprocess.run(
                    ['tail', '-50', str(log_path)],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if recent_log.returncode == 0:
                    if self.ralph.check_completion(recent_log.stdout):
                        return True

        except Exception:
            pass

        return False

    def _handle_ralph_max_iterations(self, task: Dict, phase_id: str, report: Dict) -> None:
        """Handle case where Ralph Loop reached max iterations.

        Args:
            task: Task dictionary
            phase_id: Phase identifier
            report: Max iterations report from Ralph
        """
        task_id = task.get('task_id', 'unknown')

        self.logger.log(
            f"[RALPH] Max iterations reached for {task_id}, creating checkpoint",
            level="WARNING"
        )

        # Create checkpoint for human review
        checkpoint_id = self.checkpoint_manager.create_checkpoint(
            loop_state=self._loop_state,
            agent_context=self.agent.context if hasattr(self.agent, 'context') else None,
            metadata={
                'type': 'ralph_max_iterations',
                'task_id': task_id,
                'phase_id': phase_id,
                'ralph_report': report
            }
        )

        # Send help request to human
        help_request = f"""# Ralph Loop Max Iterations Reached

## Task: {task_id}
## Phase: {phase_id}

### Summary
- Iterations attempted: {report.get('total_iterations', 'unknown')}
- Max allowed: {report.get('max_iterations', 'unknown')}

### What was tried
{self._get_ralph_iteration_summary()}

### Suggested Actions
1. Review checkpoint: {checkpoint_id}
2. APPROVE to continue with current progress
3. REJECT to rollback and try alternative approach
4. MODIFY task requirements if needed
"""

        # Write to outbox
        outbox_path = Path(__file__).parent.parent / "Communication" / "outbox"
        outbox_path.mkdir(parents=True, exist_ok=True)
        help_file = outbox_path / f"ralph_help_{task_id}.md"
        help_file.write_text(help_request, encoding='utf-8')

        self.logger.log(
            f"[RALPH] Help request written to {help_file}",
            level="INFO"
        )

    def _get_ralph_iteration_summary(self) -> str:
        """Get summary of Ralph Loop iterations for help request.

        Returns:
            Summary string
        """
        if not self.ralph or not self.ralph.state.iteration_history:
            return "No iteration history available"

        lines = []
        for entry in self.ralph.state.iteration_history[-5:]:  # Last 5 iterations
            lines.append(f"- Iteration {entry.get('iteration', '?')}: {entry.get('summary', 'No summary')}")

        return "\n".join(lines)

    def run(
        self,
        max_iterations: Optional[int] = None,
        max_time_seconds: Optional[int] = None,
        resume_from_checkpoint: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run the main execution loop.

        Args:
            max_iterations: Override max iterations from config.
            max_time_seconds: Override max time from config.
            resume_from_checkpoint: Checkpoint ID to resume from.

        Returns:
            Summary of the loop execution.
        """
        # Apply overrides
        max_iterations = max_iterations or self.config.max_iterations
        max_time_seconds = max_time_seconds or self.config.max_time_seconds

        # Initialize
        self._loop_state = LoopState()
        self._loop_state.started_at = datetime.now().isoformat()
        self._loop_state.status = LoopStatus.RUNNING
        self._shutdown_requested = False
        self._pause_requested = False

        # Resume from checkpoint if specified
        if resume_from_checkpoint:
            checkpoint = self.checkpoint_manager.load_checkpoint(resume_from_checkpoint)
            if checkpoint:
                self._loop_state.iteration = checkpoint.get('loop_state', {}).get('iteration', 0)
                self._loop_state.tasks_completed_this_run = \
                    checkpoint.get('loop_state', {}).get('tasks_completed_this_run', 0)
                self.logger.log(
                    f"Resumed from checkpoint: {resume_from_checkpoint}",
                    level="INFO"
                )
            else:
                self.logger.log(
                    f"Checkpoint not found: {resume_from_checkpoint}, starting fresh",
                    level="WARNING"
                )

        # Start session
        session_id = self.session.start_session(
            task_id="LOOP_RUNNER",
            phase="loop_execution",
            project=self.state.state.get('current_project', 'prometheus')
        )

        self.logger.log(
            f"Starting loop execution (max_iterations={max_iterations}, "
            f"max_time={max_time_seconds}s)",
            level="INFO"
        )

        start_time = datetime.now()

        try:
            while (
                not self._shutdown_requested and
                self._loop_state.iteration < max_iterations and
                (datetime.now() - start_time).total_seconds() < max_time_seconds and
                self._loop_state.status not in (LoopStatus.COMPLETED, LoopStatus.ERROR)
            ):
                # Apply error backoff if needed
                self._apply_error_backoff()

                # Execute iteration
                try:
                    self._execute_iteration()
                except Exception as e:
                    self._handle_error(e, context="Iteration execution")

        except KeyboardInterrupt:
            self.logger.log("Loop interrupted by user", level="INFO")
            self._shutdown_requested = True

        finally:
            # Finalize
            self._loop_state.status = LoopStatus.STOPPED if self._shutdown_requested else self._loop_state.status

            # Create final checkpoint
            final_checkpoint = self.checkpoint_manager.create_checkpoint(
                self._loop_state,
                self.agent._current_context,
                metadata={"reason": "loop_end"}
            )

            # Final commit
            if self.config.auto_commit and self.git.has_changes():
                self.git.commit(
                    self.git.generate_commit_message(
                        "LOOP_END",
                        f"Loop completed: {self._loop_state.tasks_completed_this_run} tasks"
                    ),
                    add_all=True
                )

            # End session
            self.session.end_session(
                summary=f"Loop completed: {self._loop_state.tasks_completed_this_run} tasks in {self._loop_state.iteration} iterations",
                status="completed" if not self._shutdown_requested else "interrupted"
            )

            self.logger.log(
                f"Loop ended: status={self._loop_state.status.value}, "
                f"iterations={self._loop_state.iteration}, "
                f"tasks_completed={self._loop_state.tasks_completed_this_run}",
                level="INFO"
            )

        # Return summary
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        return {
            "status": self._loop_state.status.value,
            "iterations": self._loop_state.iteration,
            "tasks_completed": self._loop_state.tasks_completed_this_run,
            "consecutive_errors": self._loop_state.consecutive_errors,
            "last_error": self._loop_state.last_error,
            "started_at": self._loop_state.started_at,
            "ended_at": end_time.isoformat(),
            "duration_seconds": duration,
            "final_checkpoint": final_checkpoint,
            "context_summary": self.context_manager.get_context_summary(),
        }

    def stop(self) -> None:
        """Request the loop to stop."""
        self._shutdown_requested = True
        self.logger.log("Stop requested", level="INFO")

    def pause(self) -> None:
        """Request the loop to pause."""
        self._pause_requested = True
        self.logger.log("Pause requested", level="INFO")

    def resume(self) -> None:
        """Request the loop to resume from pause."""
        self._pause_requested = False
        self.logger.log("Resume requested", level="INFO")

    def get_status(self) -> Dict[str, Any]:
        """Get current loop status.

        Returns:
            Status dictionary.
        """
        return {
            "status": self._loop_state.status.value,
            "iteration": self._loop_state.iteration,
            "current_task_id": self._loop_state.current_task_id,
            "tasks_completed_this_run": self._loop_state.tasks_completed_this_run,
            "consecutive_errors": self._loop_state.consecutive_errors,
            "last_error": self._loop_state.last_error,
            "shutdown_requested": self._shutdown_requested,
            "pause_requested": self._pause_requested,
            "context_summary": self.context_manager.get_context_summary(),
            "agent_status": self.agent.status.value,
        }

    def save_loop_state(self) -> None:
        """Save loop state to file."""
        if self.config.loop_state_file is None:
            self.config.loop_state_file = \
                Path(__file__).parent.parent / "Core" / "workflow" / "loop_state.json"

        state_data = {
            "iteration": self._loop_state.iteration,
            "started_at": self._loop_state.started_at,
            "last_iteration_at": self._loop_state.last_iteration_at,
            "tasks_completed_this_run": self._loop_state.tasks_completed_this_run,
            "consecutive_errors": self._loop_state.consecutive_errors,
            "last_error": self._loop_state.last_error,
            "current_task_id": self._loop_state.current_task_id,
            "status": self._loop_state.status.value,
            "saved_at": datetime.now().isoformat(),
        }

        self.config.loop_state_file.parent.mkdir(parents=True, exist_ok=True)

        with open(self.config.loop_state_file, 'w', encoding='utf-8') as f:
            json.dump(state_data, f, indent=2, ensure_ascii=False)

    def load_loop_state(self) -> bool:
        """Load loop state from file.

        Returns:
            True if state was loaded, False otherwise.
        """
        if self.config.loop_state_file is None:
            self.config.loop_state_file = \
                Path(__file__).parent.parent / "Core" / "workflow" / "loop_state.json"

        if not self.config.loop_state_file.exists():
            return False

        try:
            with open(self.config.loop_state_file, 'r', encoding='utf-8') as f:
                state_data = json.load(f)

            self._loop_state.iteration = state_data.get('iteration', 0)
            self._loop_state.started_at = state_data.get('started_at')
            self._loop_state.last_iteration_at = state_data.get('last_iteration_at')
            self._loop_state.tasks_completed_this_run = \
                state_data.get('tasks_completed_this_run', 0)
            self._loop_state.consecutive_errors = state_data.get('consecutive_errors', 0)
            self._loop_state.last_error = state_data.get('last_error')
            self._loop_state.current_task_id = state_data.get('current_task_id')
            self._loop_state.status = LoopStatus(state_data.get('status', 'idle'))

            return True

        except (json.JSONDecodeError, ValueError, KeyError) as e:
            self.logger.error(f"Failed to load loop state: {e}")
            return False


# ============================================================================
# Convenience Functions and Global Instance
# ============================================================================

_loop_runner_instance: Optional[LoopRunner] = None


def get_loop_runner(
    config: Optional[LoopConfig] = None,
    reload: bool = False
) -> LoopRunner:
    """Get the global loop runner instance.

    Args:
        config: Optional loop configuration.
        reload: Force reload the instance.

    Returns:
        LoopRunner instance.
    """
    global _loop_runner_instance

    if _loop_runner_instance is None or reload:
        _loop_runner_instance = LoopRunner(config=config)

    return _loop_runner_instance


def reset_loop_runner() -> None:
    """Reset the global loop runner instance."""
    global _loop_runner_instance

    if _loop_runner_instance:
        _loop_runner_instance.stop()
    _loop_runner_instance = None


# ============================================================================
# CLI Interface
# ============================================================================

def main():
    """Command-line interface for the loop runner."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Prometheus Loop Runner - Autonomous Agent Execution"
    )

    parser.add_argument(
        '--run', action='store_true',
        help='Run the loop'
    )
    parser.add_argument(
        '--max-iterations', type=int, default=100,
        help='Maximum iterations to run (default: 100)'
    )
    parser.add_argument(
        '--max-time', type=int, default=3600,
        help='Maximum time in seconds (default: 3600)'
    )
    parser.add_argument(
        '--checkpoint-interval', type=int, default=5,
        help='Checkpoint every N iterations (default: 5)'
    )
    parser.add_argument(
        '--resume', type=str,
        help='Resume from checkpoint ID'
    )
    parser.add_argument(
        '--status', action='store_true',
        help='Show current status'
    )
    parser.add_argument(
        '--list-checkpoints', action='store_true',
        help='List available checkpoints'
    )
    parser.add_argument(
        '--no-auto-commit', action='store_true',
        help='Disable auto-commit'
    )

    args = parser.parse_args()

    config = LoopConfig(
        max_iterations=args.max_iterations,
        max_time_seconds=args.max_time,
        checkpoint_interval=args.checkpoint_interval,
        auto_commit=not args.no_auto_commit,
    )

    runner = get_loop_runner(config=config)

    if args.run:
        print("Starting Prometheus Loop Runner...")
        print(f"  Max iterations: {args.max_iterations}")
        print(f"  Max time: {args.max_time}s")
        print(f"  Checkpoint interval: {args.checkpoint_interval}")
        print()

        result = runner.run(resume_from_checkpoint=args.resume)

        print("\nLoop Completed!")
        print(f"  Status: {result['status']}")
        print(f"  Iterations: {result['iterations']}")
        print(f"  Tasks completed: {result['tasks_completed']}")
        print(f"  Duration: {result['duration_seconds']:.1f}s")

    elif args.status:
        status = runner.get_status()
        print(json.dumps(status, indent=2, default=str))

    elif args.list_checkpoints:
        checkpoints = runner.checkpoint_manager.list_checkpoints()
        if checkpoints:
            print("Available checkpoints:")
            for cp in checkpoints:
                print(f"  - {cp['checkpoint_id']}: iteration {cp['iteration']}, {cp['created_at']}")
        else:
            print("No checkpoints available.")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()

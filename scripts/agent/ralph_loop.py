#!/usr/bin/env python3
"""
Project Prometheus - Ralph Loop Manager
========================================

This module implements the Ralph Loop mechanism for deep iteration
on individual tasks. Ralph Loop allows Claude to iteratively improve
on a task until completion criteria are met.

Ralph Loop Concept:
- Stop Hook intercepts Claude's exit attempts
- Same prompt is re-injected, Claude sees previous work in files
- Completion is signaled via <promise>TAG</promise>
- Max iterations as safety net

Usage:
    from agent.ralph_loop import RalphLoopManager

    ralph = RalphLoopManager(config={
        'max_iterations': 20,
        'completion_promise': 'TASK_COMPLETE'
    })

    ralph.prepare_state_file(task_id, task_desc, prompt)

    # Check for completion in output
    if ralph.check_completion(output):
        ralph.cleanup()
"""

import re
import json
import shutil
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


class RalphStatus(Enum):
    """Ralph Loop execution status."""
    IDLE = "idle"
    ACTIVE = "active"
    COMPLETED = "completed"
    MAX_ITERATIONS_REACHED = "max_iterations_reached"
    ERROR = "error"


@dataclass
class RalphState:
    """State of a Ralph Loop execution."""
    active: bool = False
    iteration: int = 0
    max_iterations: int = 20
    completion_promise: str = "TASK_COMPLETE"
    task_id: str = ""
    task_desc: str = ""
    started_at: str = ""
    last_iteration_at: str = ""
    phase: str = ""
    iteration_history: List[Dict] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            'active': self.active,
            'iteration': self.iteration,
            'max_iterations': self.max_iterations,
            'completion_promise': self.completion_promise,
            'task_id': self.task_id,
            'task_desc': self.task_desc,
            'started_at': self.started_at,
            'last_iteration_at': self.last_iteration_at,
            'phase': self.phase,
            'iteration_history': self.iteration_history
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'RalphState':
        return cls(
            active=data.get('active', False),
            iteration=data.get('iteration', 0),
            max_iterations=data.get('max_iterations', 20),
            completion_promise=data.get('completion_promise', 'TASK_COMPLETE'),
            task_id=data.get('task_id', ''),
            task_desc=data.get('task_desc', ''),
            started_at=data.get('started_at', ''),
            last_iteration_at=data.get('last_iteration_at', ''),
            phase=data.get('phase', ''),
            iteration_history=data.get('iteration_history', [])
        )


class RalphLoopManager:
    """
    Ralph Loop Manager - Manages iterative task execution.

    The Ralph Loop allows Claude to iteratively work on a task
    until a completion promise is detected or max iterations reached.
    """

    STATE_FILE = Path(".claude/ralph-loop.local.md")
    LOG_FILE = Path("Logs/ralph_loop.log")

    # Regex pattern for completion promise detection
    PROMISE_PATTERN = re.compile(r'<promise\s*(?:type="[^"]*")?\s*>([^<]+)</promise>', re.IGNORECASE)

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize Ralph Loop Manager.

        Args:
            config: Configuration dictionary with keys:
                - max_iterations: Maximum iterations (default: 20)
                - completion_promise: Promise tag to detect (default: 'TASK_COMPLETE')
                - iteration_timeout: Timeout per iteration in seconds (default: 300)
                - log_iterations: Whether to log each iteration (default: True)
        """
        config = config or {}
        self.config = config
        self.max_iterations = config.get('max_iterations', 20)
        self.completion_promise = config.get('completion_promise', 'TASK_COMPLETE')
        self.iteration_timeout = config.get('iteration_timeout', 300)
        self.log_iterations = config.get('log_iterations', True)

        self.state = RalphState(
            max_iterations=self.max_iterations,
            completion_promise=self.completion_promise
        )

        # Ensure directories exist
        self.STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        self.LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    def prepare_state_file(self, task_id: str, task_desc: str, prompt: str,
                           phase: str = "", additional_context: str = "") -> None:
        """
        Create Ralph Loop state file.

        This file is read by the Stop Hook to determine whether to
        continue iteration or allow exit.

        Args:
            task_id: Task identifier
            task_desc: Task description
            prompt: The prompt to execute
            phase: Current phase name
            additional_context: Extra context to include
        """
        now = datetime.now().isoformat()

        self.state = RalphState(
            active=True,
            iteration=0,
            max_iterations=self.max_iterations,
            completion_promise=self.completion_promise,
            task_id=task_id,
            task_desc=task_desc,
            started_at=now,
            last_iteration_at=now,
            phase=phase,
            iteration_history=[]
        )

        content = f"""---
active: true
iteration: 0
max_iterations: {self.max_iterations}
completion_promise: "{self.completion_promise}"
task_id: "{task_id}"
task_desc: "{task_desc}"
started_at: "{now}"
last_iteration_at: "{now}"
phase: "{phase}"
---

# Ralph Loop Task: {task_id}

## Task Description
{task_desc}

## Phase
{phase or 'Not specified'}

## Instructions

You are in **Ralph Loop** mode - an iterative execution environment.

### How It Works
1. Each iteration, you see the same task prompt
2. Your previous work persists in the project files and git history
3. Review what was tried before and continue improving
4. When the task is **fully complete**, output:
   `<promise>{self.completion_promise}</promise>`

### Current Iteration: 0 / {self.max_iterations}

### Task Prompt
{prompt}

{additional_context}

## Important Reminders
- Don't repeat failed approaches
- Check git log and recent files to see previous attempts
- Focus on making progress each iteration
- If blocked after multiple attempts, describe the blocker
- Output the promise tag ONLY when task is truly complete
"""

        self.STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        self.STATE_FILE.write_text(content, encoding='utf-8')

        self._log(f"[RALPH] Task {task_id} prepared | max_iterations={self.max_iterations}")

    def check_completion(self, output: str) -> bool:
        """
        Check if output contains completion promise.

        Args:
            output: Claude's output text

        Returns:
            True if completion promise detected
        """
        # Check for exact match first
        exact_pattern = f"<promise>{self.completion_promise}</promise>"
        if exact_pattern in output:
            return True

        # Check for any promise tag (more flexible)
        matches = self.PROMISE_PATTERN.findall(output)
        if matches:
            for match in matches:
                if match.strip().upper() == self.completion_promise.upper():
                    return True
                # Also accept generic completion promises
                if match.strip().upper() in ['COMPLETE', 'DONE', 'FINISHED', 'TASK_COMPLETE']:
                    return True

        return False

    def extract_promise(self, output: str) -> Optional[str]:
        """
        Extract promise value from output.

        Args:
            output: Claude's output text

        Returns:
            Promise value if found, None otherwise
        """
        matches = self.PROMISE_PATTERN.findall(output)
        return matches[0].strip() if matches else None

    def increment_iteration(self, iteration_summary: Optional[str] = None) -> int:
        """
        Increment iteration counter and update state file.

        Args:
            iteration_summary: Optional summary of what happened in this iteration

        Returns:
            New iteration count
        """
        self.state.iteration += 1
        self.state.last_iteration_at = datetime.now().isoformat()

        if iteration_summary:
            self.state.iteration_history.append({
                'iteration': self.state.iteration,
                'timestamp': self.state.last_iteration_at,
                'summary': iteration_summary
            })

        self._update_state_file()

        self._log(f"[RALPH] Iteration {self.state.iteration}/{self.max_iterations} | task={self.state.task_id}")

        return self.state.iteration

    def _update_state_file(self) -> None:
        """Update the state file with current state."""
        if not self.STATE_FILE.exists():
            return

        # Read existing content
        content = self.STATE_FILE.read_text(encoding='utf-8')

        # Update iteration count in content
        content = re.sub(
            r'iteration: \d+',
            f'iteration: {self.state.iteration}',
            content
        )
        content = re.sub(
            r'last_iteration_at: "[^"]*"',
            f'last_iteration_at: "{self.state.last_iteration_at}"',
            content
        )
        content = re.sub(
            r'### Current Iteration: \d+ / \d+',
            f'### Current Iteration: {self.state.iteration} / {self.max_iterations}',
            content
        )

        self.STATE_FILE.write_text(content, encoding='utf-8')

    def is_active(self) -> bool:
        """Check if Ralph Loop is currently active."""
        return self.state.active and self.state.iteration < self.max_iterations

    def should_continue(self) -> bool:
        """
        Check if Ralph Loop should continue iterating.

        Returns:
            True if more iterations are allowed
        """
        return self.state.active and self.state.iteration < self.max_iterations

    def get_remaining_iterations(self) -> int:
        """Get number of remaining iterations."""
        return max(0, self.max_iterations - self.state.iteration)

    def mark_completed(self) -> None:
        """Mark the Ralph Loop as completed successfully."""
        self.state.active = False
        self._log(f"[RALPH] Task {self.state.task_id} completed after {self.state.iteration} iterations")
        self.cleanup()

    def mark_max_iterations_reached(self) -> Dict[str, Any]:
        """
        Mark that max iterations were reached without completion.

        Returns:
            Dict with information for checkpoint/review
        """
        self.state.active = False

        report = {
            'status': 'max_iterations_reached',
            'task_id': self.state.task_id,
            'task_desc': self.state.task_desc,
            'phase': self.state.phase,
            'total_iterations': self.state.iteration,
            'max_iterations': self.max_iterations,
            'started_at': self.state.started_at,
            'ended_at': datetime.now().isoformat(),
            'iteration_history': self.state.iteration_history,
            'suggested_actions': [
                'Review the task and current progress',
                'APPROVE to continue with current state',
                'REJECT to rollback and try alternative approach',
                'MODIFY task requirements if needed'
            ]
        }

        self._log(f"[RALPH] Max iterations reached for {self.state.task_id}")

        return report

    def cleanup(self) -> None:
        """Remove Ralph Loop state file."""
        if self.STATE_FILE.exists():
            self.STATE_FILE.unlink()
            self._log(f"[RALPH] Cleaned up state file for {self.state.task_id}")

        self.state = RalphState(
            max_iterations=self.max_iterations,
            completion_promise=self.completion_promise
        )

    def load_state(self) -> Optional[RalphState]:
        """
        Load state from file if it exists.

        Returns:
            RalphState if file exists, None otherwise
        """
        if not self.STATE_FILE.exists():
            return None

        try:
            content = self.STATE_FILE.read_text(encoding='utf-8')

            # Parse YAML frontmatter
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    frontmatter = parts[1]
                    state_data = {}

                    for line in frontmatter.strip().split('\n'):
                        if ':' in line:
                            key, value = line.split(':', 1)
                            key = key.strip()
                            value = value.strip().strip('"')
                            state_data[key] = value

                    self.state = RalphState.from_dict(state_data)
                    return self.state

        except Exception as e:
            self._log(f"[RALPH] Error loading state: {e}")

        return None

    def get_status(self) -> Dict[str, Any]:
        """Get current Ralph Loop status."""
        return {
            'active': self.state.active,
            'task_id': self.state.task_id,
            'phase': self.state.phase,
            'iteration': self.state.iteration,
            'max_iterations': self.max_iterations,
            'remaining': self.get_remaining_iterations(),
            'completion_promise': self.completion_promise,
            'started_at': self.state.started_at,
            'last_iteration_at': self.state.last_iteration_at
        }

    def _log(self, message: str) -> None:
        """Write to Ralph Loop log file."""
        if self.log_iterations:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with open(self.LOG_FILE, 'a', encoding='utf-8') as f:
                f.write(f"[{timestamp}] {message}\n")


# Singleton instance
_ralph_instance: Optional[RalphLoopManager] = None


def get_ralph(config: Optional[Dict] = None) -> RalphLoopManager:
    """Get or create Ralph Loop manager singleton."""
    global _ralph_instance
    if _ralph_instance is None:
        _ralph_instance = RalphLoopManager(config)
    elif config:
        # Update config if provided
        _ralph_instance.config.update(config)
        _ralph_instance.max_iterations = config.get('max_iterations', _ralph_instance.max_iterations)
        _ralph_instance.completion_promise = config.get('completion_promise', _ralph_instance.completion_promise)
    return _ralph_instance


def reset_ralph() -> None:
    """Reset Ralph Loop manager singleton."""
    global _ralph_instance
    if _ralph_instance:
        _ralph_instance.cleanup()
    _ralph_instance = None

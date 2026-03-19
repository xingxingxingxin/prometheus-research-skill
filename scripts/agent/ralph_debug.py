#!/usr/bin/env python3
"""
Project Prometheus - Ralph Debug Module
========================================

This module implements the Ralph Loop debug mechanism, replacing the
traditional retry-based Debug Loop with iterative improvement.

Based on the "Ralph Wiggum" technique, this allows Claude to iteratively
debug and fix issues until the code runs successfully.

Usage:
    from agent.ralph_debug import RalphDebugger, get_debugger

    debugger = get_debugger()

    # Execute with automatic debug loop
    success = debugger.execute_with_debug(
        func=lambda: run_experiment(),
        error_context={"task_id": "EXP-001", "phase": "execution"},
        max_debug_iterations=5
    )
"""

import re
import json
import traceback
import subprocess
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, field

# GEP Integration
try:
    from Core.gep import Signal, GEPSelector, get_selector
    from Core.gep.models import SelectorDecision
    GEP_AVAILABLE = True
except ImportError:
    GEP_AVAILABLE = False
    Signal = None
    GEPSelector = None
    get_selector = None
    SelectorDecision = None


class DebugStatus(Enum):
    """Debug loop status."""
    IDLE = "idle"
    DEBUGGING = "debugging"
    FIXED = "fixed"
    FAILED = "failed"
    NEEDS_HELP = "needs_help"


@dataclass
class DebugContext:
    """Context for a debug session."""
    task_id: str = ""
    phase: str = ""
    original_error: str = ""
    error_type: str = ""
    iteration: int = 0
    max_iterations: int = 5
    attempts: List[Dict] = field(default_factory=list)
    started_at: str = ""
    last_attempt_at: str = ""
    files_modified: List[str] = field(default_factory=list)
    status: DebugStatus = DebugStatus.IDLE

    def to_dict(self) -> Dict:
        return {
            'task_id': self.task_id,
            'phase': self.phase,
            'original_error': self.original_error,
            'error_type': self.error_type,
            'iteration': self.iteration,
            'max_iterations': self.max_iterations,
            'attempts': self.attempts,
            'started_at': self.started_at,
            'last_attempt_at': self.last_attempt_at,
            'files_modified': self.files_modified,
            'status': self.status.value
        }


@dataclass
class DebugResult:
    """Result of a debug attempt."""
    success: bool
    iteration: int
    error: Optional[str] = None
    fix_applied: Optional[str] = None
    output: Optional[str] = None
    needs_human_help: bool = False


class RalphDebugger:
    """
    Ralph Debugger - Iterative debugging using Ralph Loop.

    This class replaces the traditional retry-based Debug Loop with
    an iterative improvement approach where Claude sees previous
    attempts and builds on them.
    """

    STATE_FILE = Path(".claude/ralph-debug.local.md")
    LOG_FILE = Path("Logs/ralph_debug.log")

    # Error patterns that indicate fixable issues
    FIXABLE_ERRORS = {
        'SyntaxError': True,
        'IndentationError': True,
        'NameError': True,
        'TypeError': True,
        'ValueError': True,
        'AttributeError': True,
        'ImportError': True,
        'ModuleNotFoundError': True,
        'FileNotFoundError': True,
        'PermissionError': True,
        'KeyError': True,
        'IndexError': True,
        'RuntimeError': True,  # Some runtime errors are fixable
        'AssertionError': True,
    }

    # Errors that typically need human intervention
    COMPLEX_ERRORS = {
        'MemoryError': False,  # Usually need config changes
        'RecursionError': False,  # Need algorithm changes
        'TimeoutError': False,  # Need optimization
        'SystemError': False,  # System-level issues
    }

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize Ralph Debugger.

        Args:
            config: Configuration dictionary with keys:
                - max_debug_iterations: Max debug attempts (default: 5)
                - debug_timeout: Timeout per debug attempt (default: 300)
                - auto_rollback: Auto rollback on repeated failures (default: True)
                - escalation_threshold: Failures before escalation (default: 3)
                - use_gep: Enable GEP integration (default: True)
        """
        config = config or {}
        self.config = config
        self.max_debug_iterations = config.get('max_debug_iterations', 5)
        self.debug_timeout = config.get('debug_timeout', 300)
        self.auto_rollback = config.get('auto_rollback', True)
        self.escalation_threshold = config.get('escalation_threshold', 3)
        self.use_gep = config.get('use_gep', True) and GEP_AVAILABLE

        self.context = DebugContext()

        # Initialize GEP if available
        self.gep_selector = None
        if self.use_gep and get_selector:
            try:
                self.gep_selector = get_selector(config)
                self._log("[RALPH-DEBUG] GEP Selector initialized successfully")
            except Exception as e:
                self._log(f"[RALPH-DEBUG] Failed to initialize GEP Selector: {e}")

        # Ensure directories exist
        self.STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        self.LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    def execute_with_debug(
        self,
        func: Callable[[], Any],
        error_context: Optional[Dict] = None,
        validate_func: Optional[Callable[[], bool]] = None,
        max_debug_iterations: Optional[int] = None,
        on_fix_attempt: Optional[Callable[[int, str], None]] = None
    ) -> DebugResult:
        """
        Execute a function with Ralph Loop debugging.

        Args:
            func: Function to execute
            error_context: Context information for error reporting
            validate_func: Optional validation function to verify success
            max_debug_iterations: Override max iterations
            on_fix_attempt: Callback for each fix attempt

        Returns:
            DebugResult with success status and details
        """
        max_iter = max_debug_iterations or self.max_debug_iterations

        # Initialize debug context
        self.context = DebugContext(
            task_id=error_context.get('task_id', 'unknown') if error_context else 'unknown',
            phase=error_context.get('phase', 'unknown') if error_context else 'unknown',
            max_iterations=max_iter,
            started_at=datetime.now().isoformat(),
            status=DebugStatus.DEBUGGING
        )

        self._log(f"[RALPH-DEBUG] Starting debug session for {self.context.task_id}")

        for iteration in range(1, max_iter + 1):
            self.context.iteration = iteration
            self.context.last_attempt_at = datetime.now().isoformat()

            self._log(f"[RALPH-DEBUG] Iteration {iteration}/{max_iter}")

            try:
                # Attempt execution
                result = func()

                # Run validation if provided
                if validate_func:
                    if not validate_func():
                        raise AssertionError("Validation function returned False")

                # Success!
                self.context.status = DebugStatus.FIXED
                self._log(f"[RALPH-DEBUG] Fixed after {iteration} iteration(s)")

                # Record GEP success if we had a previous GEP decision
                if self.use_gep and iteration > 1 and hasattr(self, '_last_gep_decision') and self._last_gep_decision:
                    self._record_gep_attempt(
                        self._last_gep_decision,
                        f"Fixed in iteration {iteration}",
                        True,
                        str(result) if result else "Success"
                    )

                self._cleanup()
                return DebugResult(
                    success=True,
                    iteration=iteration,
                    output=str(result) if result else None
                )

            except Exception as e:
                error_str = str(e)
                error_type = type(e).__name__

                # Record attempt
                attempt = {
                    'iteration': iteration,
                    'error_type': error_type,
                    'error_message': error_str,
                    'traceback': traceback.format_exc(),
                    'timestamp': datetime.now().isoformat()
                }
                self.context.attempts.append(attempt)

                if iteration == 1:
                    self.context.original_error = error_str
                    self.context.error_type = error_type

                self._log(f"[RALPH-DEBUG] Error in iteration {iteration}: {error_type}: {error_str[:100]}")

                # Check if we should escalate
                if not self._is_fixable(e):
                    self._log(f"[RALPH-DEBUG] Error type {error_type} marked as unfixable, escalating")
                    return self._handle_escalation(error_type, error_str, iteration)

                # Get GEP strategy if available
                gep_decision = None
                if self.gep_selector:
                    signal = self._extract_signal(e, error_context)
                    if signal:
                        gep_decision = self._get_gep_strategy(signal)
                        # Save for potential success recording
                        self._last_gep_decision = gep_decision

                # Prepare debug state for next iteration
                self._prepare_debug_state(error_str, error_type, iteration, gep_decision)

                # Call callback if provided
                if on_fix_attempt:
                    on_fix_attempt(iteration, error_str)

        # Max iterations reached
        self.context.status = DebugStatus.FAILED
        self._log(f"[RALPH-DEBUG] Max iterations ({max_iter}) reached without fix")

        return self._handle_max_iterations()

    def _is_fixable(self, error: Exception) -> bool:
        """Check if an error type is likely fixable through iteration."""
        error_type = type(error).__name__

        # Check explicit lists
        if error_type in self.FIXABLE_ERRORS:
            return self.FIXABLE_ERRORS[error_type]
        if error_type in self.COMPLEX_ERRORS:
            return self.COMPLEX_ERRORS[error_type]

        # Default: assume fixable
        return True

    def _extract_signal(self, error: Exception, error_context: Optional[Dict] = None) -> Optional['Signal']:
        """
        Extract a GEP Signal from an exception.

        Args:
            error: The exception that occurred
            error_context: Additional context about the error

        Returns:
            Signal object or None if GEP not available
        """
        if not GEP_AVAILABLE or not Signal:
            return None

        context = error_context or {}

        # Extract file and line info from traceback
        tb = traceback.format_exc()
        file_path = ""
        line_number = 0

        # Parse traceback for file/line info
        tb_match = re.search(r'File "([^"]+)", line (\d+)', tb)
        if tb_match:
            file_path = tb_match.group(1)
            line_number = int(tb_match.group(2))

        signal = Signal(
            error_type=type(error).__name__,
            error_message=str(error),
            phase=context.get('phase', ''),
            task_id=context.get('task_id', ''),
            file_path=file_path,
            line_number=line_number,
            traceback=tb,
            context=context
        )

        return signal

    def _get_gep_strategy(self, signal: 'Signal') -> Optional['SelectorDecision']:
        """
        Get GEP strategy recommendation for a signal.

        Args:
            signal: The error signal

        Returns:
            SelectorDecision or None if GEP not available
        """
        if not self.gep_selector:
            return None

        try:
            decision = self.gep_selector.select(signal)
            self._log(f"[RALPH-DEBUG] GEP selected gene: {decision.selected_gene} (confidence: {decision.confidence:.2f})")
            return decision
        except Exception as e:
            self._log(f"[RALPH-DEBUG] GEP selection failed: {e}")
            return None

    def _get_gep_strategy_prompt(self, decision: 'SelectorDecision') -> str:
        """Get GEP strategy prompt for debug state."""
        if not self.gep_selector or not decision:
            return ""

        try:
            return self.gep_selector.get_execution_prompt(decision, self.context.to_dict())
        except Exception as e:
            self._log(f"[RALPH-DEBUG] Failed to generate GEP prompt: {e}")
            return ""

    def _record_gep_attempt(self, decision: 'SelectorDecision', action: str, success: bool, result: str) -> None:
        """Record a GEP attempt and its outcome."""
        if not self.gep_selector or not decision:
            return

        try:
            event_id, capsule_id = self.gep_selector.record_attempt(
                decision=decision,
                action_taken=action,
                success=success,
                result=result,
                blast_radius=self.context.files_modified
            )
            self._log(f"[RALPH-DEBUG] GEP event recorded: {event_id}, capsule: {capsule_id}")
        except Exception as e:
            self._log(f"[RALPH-DEBUG] Failed to record GEP attempt: {e}")

    def _prepare_debug_state(self, error_str: str, error_type: str, iteration: int, gep_decision: Optional['SelectorDecision'] = None) -> None:
        """Prepare debug state file for next iteration."""
        # Get GEP strategy if available
        gep_section = ""
        if gep_decision:
            gep_prompt = self._get_gep_strategy_prompt(gep_decision)
            if gep_prompt:
                gep_section = f"""
## GEP Recommended Strategy

{gep_prompt}

"""

        content = f"""---
active: true
iteration: {iteration}
max_iterations: {self.context.max_iterations}
task_id: "{self.context.task_id}"
phase: "{self.context.phase}"
error_type: "{error_type}"
started_at: "{self.context.started_at}"
gep_enabled: {self.gep_selector is not None}
---

# Ralph Debug Session

## Task: {self.context.task_id}
## Phase: {self.context.phase}
## Iteration: {iteration} / {self.context.max_iterations}

## Original Error
```
{self.context.original_error[:500]}
```

## Current Error ({error_type})
```
{error_str[:500]}
```
{gep_section}
## Previous Attempts

{self._format_previous_attempts()}

## Your Mission

Fix this error through iterative debugging:

1. **Analyze the error**: Understand what went wrong
2. **Review previous attempts**: Check what was tried before
3. **Apply a fix**: Modify the code to resolve the issue
4. **Verify**: Run tests to confirm the fix works

## Debug Commands

```bash
# View recent changes
git diff HEAD~1

# Run the failing code
python -c "import the_module; the_module.test()"

# Run tests
pytest tests/test_related.py -v

# Check syntax
python -m py_compile the_module.py
```

## When Fixed

Output: `<promise>DEBUG_FIXED</promise>`

## If Blocked

Output: `<promise type="blocked">NEEDS_DEBUG_HELP</promise>`
"""

        self.STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        self.STATE_FILE.write_text(content, encoding='utf-8')

    def _format_previous_attempts(self) -> str:
        """Format previous attempts for debug state."""
        if not self.context.attempts:
            return "None - this is the first attempt"

        lines = []
        for i, attempt in enumerate(self.context.attempts[-3:], 1):  # Last 3 attempts
            lines.append(f"### Attempt {attempt['iteration']}")
            lines.append(f"- Error: {attempt['error_type']}")
            lines.append(f"- Message: {attempt['error_message'][:200]}")
            lines.append("")

        return "\n".join(lines)

    def _handle_escalation(self, error_type: str, error_str: str, iteration: int) -> DebugResult:
        """Handle case where error requires escalation."""
        self.context.status = DebugStatus.NEEDS_HELP

        # Record GEP failure if we had a decision
        if self.use_gep and hasattr(self, '_last_gep_decision') and self._last_gep_decision:
            self._record_gep_attempt(
                self._last_gep_decision,
                f"Escalated after {iteration} iterations",
                False,
                f"Unfixable error: {error_type}"
            )

        # Create help request
        help_request = self._create_help_request(error_type, error_str, iteration)

        # Write to outbox
        outbox_path = Path("Communication/outbox")
        outbox_path.mkdir(parents=True, exist_ok=True)
        help_file = outbox_path / f"debug_help_{self.context.task_id}.md"
        help_file.write_text(help_request, encoding='utf-8')

        self._log(f"[RALPH-DEBUG] Help request written to {help_file}")

        self._cleanup()

        return DebugResult(
            success=False,
            iteration=iteration,
            error=error_str,
            needs_human_help=True
        )

    def _handle_max_iterations(self) -> DebugResult:
        """Handle case where max iterations reached."""
        # Record GEP failure if we had a decision
        if self.use_gep and hasattr(self, '_last_gep_decision') and self._last_gep_decision:
            self._record_gep_attempt(
                self._last_gep_decision,
                f"Max iterations ({self.context.iteration}) reached",
                False,
                self.context.original_error
            )

        help_request = self._create_help_request(
            self.context.error_type,
            self.context.original_error,
            self.context.iteration
        )

        # Write to outbox
        outbox_path = Path("Communication/outbox")
        outbox_path.mkdir(parents=True, exist_ok=True)
        help_file = outbox_path / f"debug_help_{self.context.task_id}.md"
        help_file.write_text(help_request, encoding='utf-8')

        self._cleanup()

        return DebugResult(
            success=False,
            iteration=self.context.iteration,
            error=self.context.original_error,
            needs_human_help=True
        )

    def _create_help_request(self, error_type: str, error_str: str, iteration: int) -> str:
        """Create a help request for human intervention."""
        return f"""# Ralph Debug - Help Request

## Task: {self.context.task_id}
## Phase: {self.context.phase}

### Error Summary
- **Type**: {error_type}
- **Message**: {error_str[:500]}
- **Attempts**: {iteration}

### Debug History

{self._format_debug_history()}

### Suggested Actions

1. Review the error and recent code changes
2. Check if this is a known issue
3. Consider:
   - APPROVE: Continue with current state
   - ROLLBACK: Revert to last known good state
   - MODIFY: Adjust the approach
   - SKIP: Skip this task and continue

### Files Modified During Debug
{chr(10).join(f'- {f}' for f in self.context.files_modified) or 'None'}

---
*Generated by Ralph Debug at {datetime.now().isoformat()}*
"""

    def _format_debug_history(self) -> str:
        """Format full debug history for help request."""
        if not self.context.attempts:
            return "No debug attempts recorded."

        lines = []
        for attempt in self.context.attempts:
            lines.append(f"#### Iteration {attempt['iteration']}")
            lines.append(f"- **Error**: {attempt['error_type']}")
            lines.append(f"- **Time**: {attempt['timestamp']}")
            lines.append(f"- **Message**:")
            lines.append(f"  ```")
            lines.append(f"  {attempt['error_message'][:300]}")
            lines.append(f"  ```")
            lines.append("")

        return "\n".join(lines)

    def get_status(self) -> Dict:
        """Get current debug status."""
        status = {
            'status': self.context.status.value,
            'task_id': self.context.task_id,
            'phase': self.context.phase,
            'iteration': self.context.iteration,
            'max_iterations': self.context.max_iterations,
            'attempts': len(self.context.attempts),
            'error_type': self.context.error_type,
            'gep_enabled': self.gep_selector is not None
        }

        # Add GEP status if available
        if self.gep_selector:
            try:
                gep_status = self.gep_selector.get_status()
                status['gep_status'] = gep_status
            except Exception as e:
                status['gep_status'] = {'error': str(e)}

        return status

    def _cleanup(self) -> None:
        """Clean up debug state."""
        if self.STATE_FILE.exists():
            self.STATE_FILE.unlink()

    def _log(self, message: str) -> None:
        """Write to debug log."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(self.LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {message}\n")

    def check_completion_promise(self, output: str) -> bool:
        """Check if output contains debug completion promise."""
        patterns = [
            '<promise>DEBUG_FIXED</promise>',
            '<promise type="success">DEBUG_FIXED</promise>',
        ]
        return any(p in output for p in patterns)

    def check_help_promise(self, output: str) -> bool:
        """Check if output contains help request promise."""
        patterns = [
            '<promise type="blocked">NEEDS_DEBUG_HELP</promise>',
            '<promise>NEEDS_DEBUG_HELP</promise>',
        ]
        return any(p in output for p in patterns)


# Singleton instance
_debugger_instance: Optional[RalphDebugger] = None


def get_debugger(config: Optional[Dict] = None) -> RalphDebugger:
    """Get or create Ralph debugger singleton."""
    global _debugger_instance
    if _debugger_instance is None:
        _debugger_instance = RalphDebugger(config)
    elif config:
        _debugger_instance.config.update(config)
        _debugger_instance.max_debug_iterations = config.get(
            'max_debug_iterations',
            _debugger_instance.max_debug_iterations
        )
    return _debugger_instance


def reset_debugger() -> None:
    """Reset Ralph debugger singleton."""
    global _debugger_instance
    if _debugger_instance:
        _debugger_instance._cleanup()
    _debugger_instance = None


# Convenience function for wrapping functions with debug loop
def with_ralph_debug(
    func: Callable[[], Any],
    task_id: str = "",
    phase: str = "",
    max_iterations: int = 5,
    validate: Optional[Callable[[], bool]] = None
) -> DebugResult:
    """
    Execute a function with Ralph Loop debugging.

    Args:
        func: Function to execute
        task_id: Task identifier for context
        phase: Phase name for context
        max_iterations: Max debug iterations
        validate: Optional validation function

    Returns:
        DebugResult with success status
    """
    debugger = get_debugger()
    return debugger.execute_with_debug(
        func=func,
        error_context={'task_id': task_id, 'phase': phase},
        validate_func=validate,
        max_debug_iterations=max_iterations
    )

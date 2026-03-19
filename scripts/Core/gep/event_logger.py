#!/usr/bin/env python3
"""
Project Prometheus - GEP Event Logger
======================================

Logs evolution events to form a traceable event chain.

Events record the complete history of evolution attempts, successes,
failures, and validations.

Usage:
    from Core.gep.event_logger import EventLogger

    logger = EventLogger()

    # Log an event
    event = logger.log_event(
        type="attempt",
        gene_id="gene_syntax_fix",
        signal={"error_type": "SyntaxError"},
        action_taken="Fixed missing bracket"
    )

    # Get event chain
    chain = logger.get_event_chain(event_id)
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid

from .models import EvolutionEvent, ValidationReport


class EventLogger:
    """
    Event Logger - Records evolution events.

    Responsible for:
    - Logging events to JSONL file
    - Building event chains via parent_event_id
    - Querying events by various criteria
    - Generating event summaries
    """

    EVENTS_PATH = Path("Data/gep/events.jsonl")
    VALIDATION_PATH = Path("Data/gep/validations.jsonl")

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize Event Logger.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.events: Dict[str, EvolutionEvent] = {}
        self.validations: Dict[str, ValidationReport] = {}

        # Ensure data directory exists
        self.EVENTS_PATH.parent.mkdir(parents=True, exist_ok=True)

        # Load existing events
        self._load_events()

    def _load_events(self) -> None:
        """Load events from JSONL file."""
        if self.EVENTS_PATH.exists():
            try:
                with open(self.EVENTS_PATH, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            data = json.loads(line)
                            event = EvolutionEvent.from_dict(data)
                            self.events[event.id] = event
                        except json.JSONDecodeError:
                            continue
            except Exception as e:
                print(f"[EventLogger] Error loading events: {e}")

    def _generate_id(self) -> str:
        """Generate a unique event ID."""
        return f"evt_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"

    def log_event(
        self,
        type: str,
        gene_id: Optional[str] = None,
        capsule_id: Optional[str] = None,
        signal: Optional[Dict] = None,
        action_taken: str = "",
        result: str = "",
        parent_event_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> EvolutionEvent:
        """
        Log an evolution event.

        Args:
            type: Event type (attempt, success, failure, validation)
            gene_id: ID of the gene used
            capsule_id: ID of the capsule created/used
            signal: The triggering signal
            action_taken: Description of action taken
            result: Result description
            parent_event_id: Parent event for chaining
            metadata: Additional metadata

        Returns:
            The created event
        """
        event = EvolutionEvent(
            id=self._generate_id(),
            type=type,
            gene_id=gene_id,
            capsule_id=capsule_id,
            signal=signal or {},
            action_taken=action_taken,
            result=result,
            parent_event_id=parent_event_id,
            metadata=metadata or {}
        )

        # Store in memory
        self.events[event.id] = event

        # Append to file
        self._append_event(event)

        return event

    def _append_event(self, event: EvolutionEvent) -> None:
        """Append event to JSONL file."""
        try:
            with open(self.EVENTS_PATH, 'a', encoding='utf-8') as f:
                f.write(json.dumps(event.to_dict(), ensure_ascii=False) + '\n')
        except Exception as e:
            print(f"[EventLogger] Error appending event: {e}")

    def log_validation(
        self,
        event_id: str,
        passed: bool,
        metrics: Optional[Dict] = None,
        errors: Optional[List[str]] = None,
        test_results: Optional[List[Dict]] = None
    ) -> ValidationReport:
        """
        Log a validation report for an event.

        Args:
            event_id: The associated event ID
            passed: Whether validation passed
            metrics: Validation metrics
            errors: List of errors if failed
            test_results: Test results

        Returns:
            The created validation report
        """
        report = ValidationReport(
            event_id=event_id,
            passed=passed,
            metrics=metrics or {},
            errors=errors or [],
            test_results=test_results or []
        )

        # Store in memory
        self.validations[report.event_id] = report

        # Append to file
        try:
            with open(self.VALIDATION_PATH, 'a', encoding='utf-8') as f:
                f.write(json.dumps(report.to_dict(), ensure_ascii=False) + '\n')
        except Exception as e:
            print(f"[EventLogger] Error appending validation: {e}")

        return report

    def get_event(self, event_id: str) -> Optional[EvolutionEvent]:
        """
        Get an event by ID.

        Args:
            event_id: The event identifier

        Returns:
            Event or None if not found
        """
        return self.events.get(event_id)

    def get_event_chain(self, event_id: str) -> List[EvolutionEvent]:
        """
        Get the full event chain leading to an event.

        Args:
            event_id: The event identifier

        Returns:
            List of events from root to this event
        """
        chain = []
        current_id = event_id
        visited = set()

        while current_id and current_id not in visited:
            visited.add(current_id)
            event = self.events.get(current_id)
            if not event:
                break
            chain.append(event)
            current_id = event.parent_event_id

        # Reverse to get chronological order
        chain.reverse()
        return chain

    def get_events_by_gene(self, gene_id: str, limit: int = 50) -> List[EvolutionEvent]:
        """
        Get events for a specific gene.

        Args:
            gene_id: The gene identifier
            limit: Maximum events to return

        Returns:
            List of events using that gene
        """
        events = [e for e in self.events.values() if e.gene_id == gene_id]
        events.sort(key=lambda x: x.timestamp, reverse=True)
        return events[:limit]

    def get_events_by_type(self, type: str, limit: int = 50) -> List[EvolutionEvent]:
        """
        Get events of a specific type.

        Args:
            type: The event type
            limit: Maximum events to return

        Returns:
            List of events of that type
        """
        events = [e for e in self.events.values() if e.type == type]
        events.sort(key=lambda x: x.timestamp, reverse=True)
        return events[:limit]

    def get_events_by_capsule(self, capsule_id: str) -> List[EvolutionEvent]:
        """
        Get events for a specific capsule.

        Args:
            capsule_id: The capsule identifier

        Returns:
            List of events referencing that capsule
        """
        events = [e for e in self.events.values() if e.capsule_id == capsule_id]
        events.sort(key=lambda x: x.timestamp, reverse=True)
        return events

    def get_recent_events(self, limit: int = 50) -> List[EvolutionEvent]:
        """
        Get most recent events.

        Args:
            limit: Maximum events to return

        Returns:
            List of recent events
        """
        events = list(self.events.values())
        events.sort(key=lambda x: x.timestamp, reverse=True)
        return events[:limit]

    def get_children(self, event_id: str) -> List[EvolutionEvent]:
        """
        Get child events of an event.

        Args:
            event_id: The parent event identifier

        Returns:
            List of child events
        """
        children = [e for e in self.events.values() if e.parent_event_id == event_id]
        children.sort(key=lambda x: x.timestamp)
        return children

    def create_success_chain(
        self,
        attempt_event: EvolutionEvent,
        gene_id: str,
        capsule_id: str,
        result: str
    ) -> EvolutionEvent:
        """
        Create a success event linked to an attempt.

        Args:
            attempt_event: The original attempt event
            gene_id: The gene that succeeded
            capsule_id: The capsule created
            result: Result description

        Returns:
            The success event
        """
        return self.log_event(
            type="success",
            gene_id=gene_id,
            capsule_id=capsule_id,
            signal=attempt_event.signal,
            action_taken=attempt_event.action_taken,
            result=result,
            parent_event_id=attempt_event.id
        )

    def create_failure_chain(
        self,
        attempt_event: EvolutionEvent,
        result: str,
        metadata: Optional[Dict] = None
    ) -> EvolutionEvent:
        """
        Create a failure event linked to an attempt.

        Args:
            attempt_event: The original attempt event
            result: Failure description
            metadata: Additional failure metadata

        Returns:
            The failure event
        """
        return self.log_event(
            type="failure",
            gene_id=attempt_event.gene_id,
            signal=attempt_event.signal,
            action_taken=attempt_event.action_taken,
            result=result,
            parent_event_id=attempt_event.id,
            metadata=metadata
        )

    def get_statistics(self) -> Dict[str, Any]:
        """Get event statistics."""
        total = len(self.events)
        if total == 0:
            return {
                'total_events': 0,
                'by_type': {},
                'success_rate': 0,
                'avg_chain_length': 0
            }

        by_type = {}
        success_count = 0
        failure_count = 0
        chain_lengths = []

        for event in self.events.values():
            by_type[event.type] = by_type.get(event.type, 0) + 1
            if event.type == 'success':
                success_count += 1
            elif event.type == 'failure':
                failure_count += 1

            # Calculate chain lengths
            chain = self.get_event_chain(event.id)
            if len(chain) > 1:
                chain_lengths.append(len(chain))

        success_rate = success_count / (success_count + failure_count) if (success_count + failure_count) > 0 else 0
        avg_chain = sum(chain_lengths) / len(chain_lengths) if chain_lengths else 0

        return {
            'total_events': total,
            'by_type': by_type,
            'success_rate': success_rate,
            'avg_chain_length': avg_chain,
            'validations_recorded': len(self.validations)
        }

    def cleanup_old_events(self, max_age_days: int = 30, keep_chains: bool = True) -> int:
        """
        Remove old events.

        Args:
            max_age_days: Maximum age in days
            keep_chains: Whether to keep events that are part of chains

        Returns:
            Number of events removed
        """
        cutoff = datetime.now().timestamp() - (max_age_days * 86400)
        to_remove = []

        for event_id, event in self.events.items():
            try:
                created = datetime.fromisoformat(event.timestamp).timestamp()
                if created < cutoff:
                    # Check if part of a chain
                    if keep_chains:
                        has_children = any(e.parent_event_id == event_id for e in self.events.values())
                        has_parent = event.parent_event_id and event.parent_event_id in self.events
                        if has_children or has_parent:
                            continue
                    to_remove.append(event_id)
            except (ValueError, TypeError):
                pass

        for event_id in to_remove:
            del self.events[event_id]

        if to_remove:
            self._rewrite_events()

        return len(to_remove)

    def _rewrite_events(self) -> None:
        """Rewrite all events to JSONL file."""
        try:
            with open(self.EVENTS_PATH, 'w', encoding='utf-8') as f:
                for event in self.events.values():
                    f.write(json.dumps(event.to_dict(), ensure_ascii=False) + '\n')
        except Exception as e:
            print(f"[EventLogger] Error rewriting events: {e}")

    def export_chain(self, event_id: str, format: str = "markdown") -> str:
        """
        Export an event chain as a formatted string.

        Args:
            event_id: The event identifier
            format: Output format (markdown, json)

        Returns:
            Formatted string
        """
        chain = self.get_event_chain(event_id)

        if format == "json":
            return json.dumps([e.to_dict() for e in chain], indent=2)

        # Markdown format
        lines = ["# Evolution Event Chain\n"]

        for i, event in enumerate(chain):
            lines.append(f"## Step {i + 1}: {event.type.upper()}")
            lines.append(f"- **ID**: {event.id}")
            if event.gene_id:
                lines.append(f"- **Gene**: {event.gene_id}")
            if event.capsule_id:
                lines.append(f"- **Capsule**: {event.capsule_id}")
            if event.action_taken:
                lines.append(f"- **Action**: {event.action_taken}")
            if event.result:
                lines.append(f"- **Result**: {event.result}")
            lines.append(f"- **Time**: {event.timestamp}")
            lines.append("")

        return "\n".join(lines)


# Singleton instance
_logger_instance: Optional[EventLogger] = None


def get_event_logger(config: Optional[Dict] = None) -> EventLogger:
    """Get or create EventLogger singleton."""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = EventLogger(config)
    elif config:
        _logger_instance.config.update(config)
    return _logger_instance


def reset_event_logger() -> None:
    """Reset EventLogger singleton."""
    global _logger_instance
    _logger_instance = None

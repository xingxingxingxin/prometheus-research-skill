#!/usr/bin/env python3
"""
Project Prometheus - GEP Selector
==================================

Selects the best evolution strategy based on signals.

The Selector coordinates between:
- Gene matching (strategy templates)
- Capsule retrieval (successful past fixes)
- Event history (what was tried before)

Usage:
    from Core.gep.selector import GEPSelector

    selector = GEPSelector()

    # Make a selection decision
    decision = selector.select(signal)

    # Get strategy prompt
    prompt = selector.get_execution_prompt(decision)
"""

from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

from .models import Signal, Gene, Capsule, SelectorDecision
from .gene_manager import GeneManager, get_gene_manager
from .capsule_store import CapsuleStore, get_capsule_store
from .event_logger import EventLogger, get_event_logger


class GEPSelector:
    """
    GEP Selector - Coordinates strategy selection.

    The Selector is the main entry point for GEP. It:
    1. Takes a signal (error context)
    2. Matches against Gene library
    3. Retrieves relevant Capsules
    4. Checks event history for previous attempts
    5. Returns a decision with recommended strategy
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize GEP Selector.

        Args:
            config: Optional configuration dictionary
                - gene_weight: Weight for gene match score (default: 0.5)
                - capsule_weight: Weight for capsule confidence (default: 0.3)
                - history_weight: Weight for history factor (default: 0.2)
                - min_confidence: Minimum confidence threshold (default: 0.3)
        """
        self.config = config or {}
        self.gene_weight = self.config.get('gene_weight', 0.5)
        self.capsule_weight = self.config.get('capsule_weight', 0.3)
        self.history_weight = self.config.get('history_weight', 0.2)
        self.min_confidence = self.config.get('min_confidence', 0.3)

        # Initialize components
        self.gene_manager = get_gene_manager(config)
        self.capsule_store = get_capsule_store(config)
        self.event_logger = get_event_logger(config)

    def select(
        self,
        signal: Signal,
        max_genes: int = 3,
        max_capsules: int = 5
    ) -> SelectorDecision:
        """
        Make a strategy selection decision.

        Args:
            signal: The triggering signal
            max_genes: Maximum genes to consider
            max_capsules: Maximum capsules to retrieve

        Returns:
            SelectorDecision with recommended strategy
        """
        # Match genes
        matched_genes = self.gene_manager.match_genes(
            signal,
            min_score=self.min_confidence,
            max_results=max_genes
        )

        # Search for relevant capsules
        query = self._build_search_query(signal)
        related_capsules = self.capsule_store.search_capsules(
            query,
            max_results=max_capsules,
            min_confidence=self.min_confidence
        )

        # Check event history
        history_factor = self._get_history_factor(signal)

        # Make selection
        selected_gene, confidence, reason = self._make_selection(
            matched_genes,
            related_capsules,
            history_factor
        )

        # Build decision
        decision = SelectorDecision(
            signal=signal,
            matched_genes=[(g.id, s) for g, s in matched_genes],
            selected_gene=selected_gene.id if selected_gene else None,
            related_capsules=[c.id for c, _ in related_capsules],
            decision_reason=reason,
            confidence=confidence
        )

        return decision

    def _build_search_query(self, signal: Signal) -> str:
        """Build a search query from the signal."""
        parts = []

        if signal.error_type:
            parts.append(signal.error_type)

        if signal.error_message:
            # Extract key terms from error message
            words = signal.error_message.split()[:10]
            parts.extend(words)

        if signal.file_path:
            # Add file extension as context
            ext = signal.file_path.rsplit('.', 1)[-1] if '.' in signal.file_path else ''
            if ext:
                parts.append(ext)

        return ' '.join(parts)

    def _get_history_factor(self, signal: Signal) -> Dict[str, Any]:
        """Get historical context for similar signals."""
        # Get recent events with similar error type
        recent = self.event_logger.get_recent_events(limit=50)

        similar_attempts = []
        for event in recent:
            event_error = event.signal.get('error_type', '')
            if event_error == signal.error_type:
                similar_attempts.append(event)

        if not similar_attempts:
            return {'factor': 0.5, 'attempts': 0, 'recent_success': None}

        # Calculate success rate
        successes = sum(1 for e in similar_attempts if e.type == 'success')
        total = len(similar_attempts)

        # Get most recent outcome
        recent_outcome = similar_attempts[0].type if similar_attempts else None

        return {
            'factor': successes / total if total > 0 else 0.5,
            'attempts': total,
            'recent_success': recent_outcome == 'success'
        }

    def _make_selection(
        self,
        matched_genes: List[Tuple[Gene, float]],
        related_capsules: List[Tuple[Capsule, float]],
        history_factor: Dict[str, Any]
    ) -> Tuple[Optional[Gene], float, str]:
        """
        Make the final selection decision.

        Returns:
            Tuple of (selected_gene, confidence, reason)
        """
        if not matched_genes and not related_capsules:
            return None, 0.0, "No matching strategies found"

        reasons = []

        # Check if we have a high-confidence capsule
        if related_capsules:
            best_capsule, capsule_score = related_capsules[0]
            if capsule_score > 0.8:
                # Use the gene from the capsule
                gene = self.gene_manager.get_gene(best_capsule.gene_id)
                if gene:
                    confidence = (
                        self.capsule_weight * capsule_score +
                        self.gene_weight * 0.5 +  # Assume gene is decent match
                        self.history_weight * history_factor['factor']
                    )
                    reason = f"High-confidence capsule match (capsule: {best_capsule.id})"
                    return gene, confidence, reason

        # Otherwise, use best matching gene
        if matched_genes:
            best_gene, gene_score = matched_genes[0]

            # Boost score if we have supporting capsules
            capsule_boost = 0
            if related_capsules:
                for capsule, _ in related_capsules[:2]:
                    if capsule.gene_id == best_gene.id:
                        capsule_boost = 0.1
                        reasons.append(f"Supported by capsule {capsule.id}")
                        break

            confidence = (
                self.gene_weight * gene_score +
                self.capsule_weight * (capsule_boost * 10) +
                self.history_weight * history_factor['factor']
            )

            reason = f"Best gene match (score: {gene_score:.2f})"
            if history_factor['attempts'] > 0:
                reason += f", history: {history_factor['attempts']} similar attempts"
            if capsule_boost:
                reason += ", capsule support"

            return best_gene, confidence, reason

        # Fallback: use gene from first capsule
        if related_capsules:
            capsule, _ = related_capsules[0]
            gene = self.gene_manager.get_gene(capsule.gene_id)
            if gene:
                confidence = capsule.confidence * 0.5
                return gene, confidence, f"Fallback to capsule gene (capsule: {capsule.id})"

        return None, 0.0, "No suitable strategy found"

    def get_execution_prompt(
        self,
        decision: SelectorDecision,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate an execution prompt from a decision.

        Args:
            decision: The selector decision
            context: Additional execution context

        Returns:
            Formatted prompt string
        """
        context = context or {}

        lines = ["# GEP Evolution Strategy\n"]

        # Signal info
        lines.append("## Trigger Signal")
        lines.append(f"- **Error Type**: {decision.signal.error_type}")
        lines.append(f"- **File**: {decision.signal.file_path}")
        if decision.signal.line_number:
            lines.append(f"- **Line**: {decision.signal.line_number}")
        lines.append(f"- **Message**: {decision.signal.error_message[:200]}")
        lines.append("")

        # Decision info
        lines.append("## Strategy Selection")
        lines.append(f"- **Confidence**: {decision.confidence:.2%}")
        lines.append(f"- **Reason**: {decision.decision_reason}")
        lines.append("")

        # Selected gene
        if decision.selected_gene:
            gene = self.gene_manager.get_gene(decision.selected_gene)
            if gene:
                gene_prompt = self.gene_manager.get_strategy_prompt(gene, context)
                lines.append(gene_prompt)
                lines.append("")

        # Related capsules (as reference)
        if decision.related_capsules:
            lines.append("## Related Successful Fixes")
            for i, capsule_id in enumerate(decision.related_capsules[:3], 1):
                capsule = self.capsule_store.get_capsule(capsule_id)
                if capsule:
                    lines.append(f"### Capsule {i}: {capsule_id}")
                    lines.append(f"- **Trigger**: {capsule.trigger[:100]}")
                    lines.append(f"- **Summary**: {capsule.summary[:200]}")
                    lines.append(f"- **Confidence**: {capsule.confidence:.2%}")
                    lines.append("")

        # Matched alternatives
        if decision.matched_genes and len(decision.matched_genes) > 1:
            lines.append("## Alternative Strategies")
            for gene_id, score in decision.matched_genes[1:4]:
                gene = self.gene_manager.get_gene(gene_id)
                if gene:
                    lines.append(f"- **{gene.name}** (score: {score:.2f})")
            lines.append("")

        return "\n".join(lines)

    def record_attempt(
        self,
        decision: SelectorDecision,
        action_taken: str,
        success: bool,
        result: str = "",
        blast_radius: Optional[List[str]] = None
    ) -> Tuple[str, Optional[str]]:
        """
        Record an execution attempt and its result.

        Args:
            decision: The selector decision
            action_taken: What action was taken
            success: Whether it succeeded
            result: Result description
            blast_radius: Files modified

        Returns:
            Tuple of (event_id, capsule_id if success)
        """
        # Log attempt event
        attempt_event = self.event_logger.log_event(
            type="attempt",
            gene_id=decision.selected_gene,
            signal=decision.signal.to_dict(),
            action_taken=action_taken
        )

        capsule_id = None

        if success:
            # Create capsule
            capsule = Capsule(
                id=f"cap_{attempt_event.id}",
                trigger=decision.signal.error_message[:200],
                gene_id=decision.selected_gene or "",
                confidence=decision.confidence,
                blast_radius=blast_radius or [],
                outcome="success",
                context={
                    'error_type': decision.signal.error_type,
                    'file_path': decision.signal.file_path,
                    'action_taken': action_taken
                },
                summary=result[:500]
            )

            # Add to store
            self.capsule_store.add_capsule(capsule)
            capsule_id = capsule.id

            # Create success event
            self.event_logger.create_success_chain(
                attempt_event,
                decision.selected_gene or "",
                capsule_id,
                result
            )

            # Update gene stats
            if decision.selected_gene:
                self.gene_manager.update_gene_stats(decision.selected_gene, True)

        else:
            # Create failure event
            self.event_logger.create_failure_chain(
                attempt_event,
                result,
                {'decision_confidence': decision.confidence}
            )

            # Update gene stats
            if decision.selected_gene:
                self.gene_manager.update_gene_stats(decision.selected_gene, False)

        return attempt_event.id, capsule_id

    def get_status(self) -> Dict[str, Any]:
        """Get selector status summary."""
        gene_stats = self.gene_manager.get_stats_summary()
        capsule_stats = self.capsule_store.get_stats()
        event_stats = self.event_logger.get_statistics()

        return {
            'genes': gene_stats,
            'capsules': capsule_stats,
            'events': event_stats,
            'config': {
                'gene_weight': self.gene_weight,
                'capsule_weight': self.capsule_weight,
                'history_weight': self.history_weight,
                'min_confidence': self.min_confidence
            }
        }


# Singleton instance
_selector_instance: Optional[GEPSelector] = None


def get_selector(config: Optional[Dict] = None) -> GEPSelector:
    """Get or create GEPSelector singleton."""
    global _selector_instance
    if _selector_instance is None:
        _selector_instance = GEPSelector(config)
    elif config:
        _selector_instance.config.update(config)
        _selector_instance.gene_weight = config.get('gene_weight', _selector_instance.gene_weight)
        _selector_instance.capsule_weight = config.get('capsule_weight', _selector_instance.capsule_weight)
        _selector_instance.history_weight = config.get('history_weight', _selector_instance.history_weight)
        _selector_instance.min_confidence = config.get('min_confidence', _selector_instance.min_confidence)
    return _selector_instance


def reset_selector() -> None:
    """Reset GEPSelector singleton."""
    global _selector_instance
    _selector_instance = None

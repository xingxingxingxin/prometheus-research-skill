#!/usr/bin/env python3
"""
Project Prometheus - GEP Gene Manager
======================================

Manages the Gene library: loading, matching, and executing genes.

Usage:
    from Core.gep.gene_manager import GeneManager

    manager = GeneManager()

    # Match genes against a signal
    matches = manager.match_genes(signal)

    # Get strategy prompt for a gene
    prompt = manager.get_strategy_prompt(gene, context)

    # Update gene statistics
    manager.update_gene_stats(gene_id, success=True)
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import re

from .models import Gene, GeneCategory, Signal


class GeneManager:
    """
    Gene Manager - Loads and manages the Gene library.

    Responsible for:
    - Loading genes from JSON files
    - Matching signals to genes
    - Generating strategy prompts
    - Tracking gene usage statistics
    """

    DEFAULT_GENES_PATH = Path(__file__).parent / "defaults" / "genes.json"
    CUSTOM_GENES_PATH = Path("Data/gep/custom_genes.json")
    STATS_PATH = Path("Data/gep/gene_stats.json")

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize Gene Manager.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.genes: Dict[str, Gene] = {}
        self.gene_stats: Dict[str, Dict] = {}

        # Ensure data directory exists
        self.STATS_PATH.parent.mkdir(parents=True, exist_ok=True)

        # Load genes and stats
        self._load_genes()
        self._load_stats()

    def _load_genes(self) -> None:
        """Load genes from default and custom JSON files."""
        # Load default genes
        if self.DEFAULT_GENES_PATH.exists():
            self._load_genes_from_file(self.DEFAULT_GENES_PATH)

        # Load custom genes (overrides defaults with same ID)
        if self.CUSTOM_GENES_PATH.exists():
            self._load_genes_from_file(self.CUSTOM_GENES_PATH)

    def _load_genes_from_file(self, filepath: Path) -> None:
        """Load genes from a JSON file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            for gene_data in data.get('genes', []):
                gene = Gene.from_dict(gene_data)
                self.genes[gene.id] = gene

        except Exception as e:
            print(f"[GeneManager] Error loading genes from {filepath}: {e}")

    def _load_stats(self) -> None:
        """Load gene statistics from file."""
        if self.STATS_PATH.exists():
            try:
                with open(self.STATS_PATH, 'r', encoding='utf-8') as f:
                    self.gene_stats = json.load(f)
            except Exception:
                self.gene_stats = {}

    def _save_stats(self) -> None:
        """Save gene statistics to file."""
        try:
            with open(self.STATS_PATH, 'w', encoding='utf-8') as f:
                json.dump(self.gene_stats, f, indent=2)
        except Exception as e:
            print(f"[GeneManager] Error saving stats: {e}")

    def get_gene(self, gene_id: str) -> Optional[Gene]:
        """
        Get a gene by ID.

        Args:
            gene_id: The gene identifier

        Returns:
            Gene object or None if not found
        """
        return self.genes.get(gene_id)

    def get_all_genes(self) -> List[Gene]:
        """Get all loaded genes."""
        return list(self.genes.values())

    def get_genes_by_category(self, category: GeneCategory) -> List[Gene]:
        """
        Get genes filtered by category.

        Args:
            category: The gene category to filter

        Returns:
            List of genes in that category
        """
        return [g for g in self.genes.values() if g.category == category]

    def match_genes(
        self,
        signal: Signal,
        min_score: float = 0.1,
        max_results: int = 5
    ) -> List[Tuple[Gene, float]]:
        """
        Match genes against a signal.

        Args:
            signal: The signal to match against
            min_score: Minimum match score (0-1)
            max_results: Maximum number of results

        Returns:
            List of (Gene, score) tuples, sorted by score descending
        """
        matches = []

        for gene in self.genes.values():
            score = gene.matches_signal(signal)

            # Apply stats modifier
            stats = self.gene_stats.get(gene.id, {})
            if stats:
                # Boost score based on recent success rate
                recent_success_rate = stats.get('recent_success_rate', gene.success_rate)
                score = score * 0.8 + recent_success_rate * 0.2

            if score >= min_score:
                matches.append((gene, score))

        # Sort by score descending
        matches.sort(key=lambda x: x[1], reverse=True)

        return matches[:max_results]

    def get_best_gene(self, signal: Signal) -> Optional[Tuple[Gene, float]]:
        """
        Get the best matching gene for a signal.

        Args:
            signal: The signal to match

        Returns:
            Tuple of (Gene, score) or None if no match
        """
        matches = self.match_genes(signal, min_score=0.1, max_results=1)
        return matches[0] if matches else None

    def get_strategy_prompt(self, gene: Gene, context: Dict[str, Any]) -> str:
        """
        Generate a strategy prompt for a gene.

        Args:
            gene: The gene to generate prompt for
            context: Execution context (error details, file info, etc.)

        Returns:
            Formatted prompt string
        """
        return gene.get_strategy_prompt(context)

    def update_gene_stats(self, gene_id: str, success: bool) -> None:
        """
        Update gene statistics after an execution.

        Args:
            gene_id: The gene identifier
            success: Whether the execution was successful
        """
        if gene_id not in self.gene_stats:
            self.gene_stats[gene_id] = {
                'use_count': 0,
                'success_count': 0,
                'failure_count': 0,
                'recent_success_rate': 0.5,
                'last_used': None
            }

        stats = self.gene_stats[gene_id]
        stats['use_count'] += 1
        stats['last_used'] = datetime.now().isoformat()

        if success:
            stats['success_count'] += 1
        else:
            stats['failure_count'] += 1

        # Calculate recent success rate (last 20 uses)
        total = stats['success_count'] + stats['failure_count']
        if total > 0:
            stats['recent_success_rate'] = stats['success_count'] / total

        self._save_stats()

        # Also update the in-memory gene
        if gene_id in self.genes:
            gene = self.genes[gene_id]
            gene.use_count = stats['use_count']
            gene.success_rate = stats['recent_success_rate']

    def add_custom_gene(self, gene: Gene) -> bool:
        """
        Add a custom gene to the library.

        Args:
            gene: The gene to add

        Returns:
            True if successful
        """
        try:
            # Add to memory
            self.genes[gene.id] = gene

            # Save to custom genes file
            self._save_custom_genes()

            return True
        except Exception as e:
            print(f"[GeneManager] Error adding custom gene: {e}")
            return False

    def _save_custom_genes(self) -> None:
        """Save all custom genes to the custom genes file."""
        try:
            # For simplicity, save all genes as custom
            # In a production system, we'd track which are custom vs default
            data = {
                'version': '1.0.0',
                'description': 'Custom genes for GEP',
                'genes': [g.to_dict() for g in self.genes.values()]
            }

            with open(self.CUSTOM_GENES_PATH, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[GeneManager] Error saving custom genes: {e}")

    def remove_gene(self, gene_id: str) -> bool:
        """
        Remove a gene from the library.

        Args:
            gene_id: The gene identifier to remove

        Returns:
            True if successful, False if not found
        """
        if gene_id in self.genes:
            del self.genes[gene_id]
            self._save_custom_genes()
            return True
        return False

    def get_stats_summary(self) -> Dict[str, Any]:
        """Get a summary of gene statistics."""
        total_uses = sum(s.get('use_count', 0) for s in self.gene_stats.values())
        total_success = sum(s.get('success_count', 0) for s in self.gene_stats.values())

        most_used = max(
            self.gene_stats.items(),
            key=lambda x: x[1].get('use_count', 0),
            default=(None, {})
        )

        most_successful = max(
            [(k, v) for k, v in self.gene_stats.items() if v.get('use_count', 0) >= 5],
            key=lambda x: x[1].get('recent_success_rate', 0),
            default=(None, {})
        )

        return {
            'total_genes': len(self.genes),
            'total_uses': total_uses,
            'overall_success_rate': total_success / total_uses if total_uses > 0 else 0,
            'most_used_gene': most_used[0],
            'most_used_count': most_used[1].get('use_count', 0) if most_used[1] else 0,
            'most_successful_gene': most_successful[0],
            'most_successful_rate': most_successful[1].get('recent_success_rate', 0) if most_successful[1] else 0
        }


# Singleton instance
_manager_instance: Optional[GeneManager] = None


def get_gene_manager(config: Optional[Dict] = None) -> GeneManager:
    """Get or create GeneManager singleton."""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = GeneManager(config)
    elif config:
        _manager_instance.config.update(config)
    return _manager_instance


def reset_gene_manager() -> None:
    """Reset GeneManager singleton."""
    global _manager_instance
    _manager_instance = None

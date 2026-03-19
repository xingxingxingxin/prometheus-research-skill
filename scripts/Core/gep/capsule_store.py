#!/usr/bin/env python3
"""
Project Prometheus - GEP Capsule Store
=======================================

Manages Capsule storage and retrieval with RAG integration.

Capsules record successful evolution/repair attempts and can be
semantically searched for reuse.

Usage:
    from Core.gep.capsule_store import CapsuleStore

    store = CapsuleStore()

    # Add a capsule
    store.add_capsule(capsule)

    # Search for relevant capsules
    results = store.search_capsules("syntax error in parser")

    # Update confidence after reuse
    store.update_confidence(capsule_id, success=True)
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import hashlib

from .models import Capsule


class CapsuleStore:
    """
    Capsule Store - Manages successful evolution capsules.

    Responsible for:
    - Storing capsules persistently
    - Integrating with RAG for semantic search
    - Tracking capsule confidence and use counts
    - Managing capsule lifecycle
    """

    CAPSULES_PATH = Path("Data/gep/capsules.jsonl")
    INDEX_PATH = Path("Data/gep/capsule_index.json")

    def __init__(self, config: Optional[Dict] = None, rag_manager=None):
        """
        Initialize Capsule Store.

        Args:
            config: Optional configuration dictionary
            rag_manager: Optional RAG manager for semantic search
        """
        self.config = config or {}
        self.rag_manager = rag_manager
        self.capsules: Dict[str, Capsule] = {}
        self.index: Dict[str, List[str]] = {}  # keyword -> capsule_ids

        # Ensure data directory exists
        self.CAPSULES_PATH.parent.mkdir(parents=True, exist_ok=True)

        # Load existing capsules
        self._load_capsules()
        self._load_index()

    def _load_capsules(self) -> None:
        """Load capsules from JSONL file."""
        if not self.CAPSULES_PATH.exists():
            return

        try:
            with open(self.CAPSULES_PATH, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        capsule = Capsule.from_dict(data)
                        self.capsules[capsule.id] = capsule
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            print(f"[CapsuleStore] Error loading capsules: {e}")

    def _load_index(self) -> None:
        """Load keyword index."""
        if self.INDEX_PATH.exists():
            try:
                with open(self.INDEX_PATH, 'r', encoding='utf-8') as f:
                    self.index = json.load(f)
            except Exception:
                self.index = {}

    def _save_index(self) -> None:
        """Save keyword index."""
        try:
            with open(self.INDEX_PATH, 'w', encoding='utf-8') as f:
                json.dump(self.index, f, indent=2)
        except Exception as e:
            print(f"[CapsuleStore] Error saving index: {e}")

    def add_capsule(self, capsule: Capsule) -> bool:
        """
        Add a capsule to the store.

        Args:
            capsule: The capsule to add

        Returns:
            True if successful
        """
        try:
            # Add to memory
            self.capsules[capsule.id] = capsule

            # Append to JSONL file
            with open(self.CAPSULES_PATH, 'a', encoding='utf-8') as f:
                f.write(json.dumps(capsule.to_dict(), ensure_ascii=False) + '\n')

            # Update keyword index
            self._index_capsule(capsule)

            # Add to RAG if available
            self._add_to_rag(capsule)

            return True
        except Exception as e:
            print(f"[CapsuleStore] Error adding capsule: {e}")
            return False

    def _index_capsule(self, capsule: Capsule) -> None:
        """Index capsule keywords for quick lookup."""
        # Extract keywords from trigger and summary
        text = f"{capsule.trigger} {capsule.summary}".lower()
        keywords = self._extract_keywords(text)

        for keyword in keywords:
            if keyword not in self.index:
                self.index[keyword] = []
            if capsule.id not in self.index[keyword]:
                self.index[keyword].append(capsule.id)

        self._save_index()

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text."""
        # Simple keyword extraction
        # In production, could use NLP libraries
        stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
                      'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
                      'would', 'could', 'should', 'may', 'might', 'must', 'to',
                      'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from', 'as',
                      'and', 'or', 'but', 'if', 'then', 'else', 'when', 'this',
                      'that', 'these', 'those', 'it', 'its', 'they', 'them'}

        words = re.findall(r'\b[a-z_]+\b', text.lower())
        return [w for w in words if w not in stop_words and len(w) > 2]

    def _add_to_rag(self, capsule: Capsule) -> None:
        """Add capsule to RAG system for semantic search."""
        # Try to get RAG manager if not already set
        if not self.rag_manager:
            self.rag_manager = self._init_rag_manager()
        
        if not self.rag_manager:
            # RAG not available, skip semantic indexing
            return

        try:
            # Create searchable document
            doc_id = f"capsule_{capsule.id}"
            content = capsule.to_searchable_text()
            metadata = {
                'type': 'capsule',
                'capsule_id': capsule.id,
                'gene_id': capsule.gene_id,
                'confidence': capsule.confidence,
                'outcome': capsule.outcome,
                'created_at': capsule.created_at
            }

            # Add to RAG index
            if hasattr(self.rag_manager, 'index_document'):
                self.rag_manager.index_document(doc_id, content, metadata)
            elif hasattr(self.rag_manager, 'add_document'):
                self.rag_manager.add_document(doc_id, content, metadata)
        except Exception as e:
            # Log warning but don't fail
            import warnings
            warnings.warn(f"[CapsuleStore] RAG indexing failed: {e}")
    
    def _init_rag_manager(self):
        """Initialize RAG manager with fallback options."""
        # Try different import paths
        import_paths = [
            ('Core.rag.rag_manager', 'get_rag_manager'),
            ('Core.rag', 'get_rag_manager'),
            ('rag_manager', 'get_rag_manager'),
        ]
        
        for module_path, func_name in import_paths:
            try:
                import importlib
                module = importlib.import_module(module_path)
                get_rag_func = getattr(module, func_name)
                
                # Try to initialize with fallback settings
                rag = get_rag_func()
                print(f"[CapsuleStore] RAG initialized from {module_path}")
                return rag
            except ImportError:
                continue
            except Exception as e:
                print(f"[CapsuleStore] RAG init failed ({module_path}): {e}")
                continue
        
        # RAG not available - this is OK, we'll use keyword search
        print("[CapsuleStore] RAG not available, using keyword search only")
        return None

    def get_capsule(self, capsule_id: str) -> Optional[Capsule]:
        """
        Get a capsule by ID.

        Args:
            capsule_id: The capsule identifier

        Returns:
            Capsule or None if not found
        """
        return self.capsules.get(capsule_id)

    def search_capsules(
        self,
        query: str,
        max_results: int = 5,
        min_confidence: float = 0.3
    ) -> List[Tuple[Capsule, float]]:
        """
        Search for relevant capsules.

        Uses both keyword matching and semantic search (if RAG available).

        Args:
            query: Search query
            max_results: Maximum results to return
            min_confidence: Minimum confidence threshold

        Returns:
            List of (Capsule, relevance_score) tuples
        """
        results = []

        # Try semantic search first via RAG
        rag_results = self._search_via_rag(query, max_results * 2)

        if rag_results:
            for doc_id, score in rag_results:
                if doc_id.startswith('capsule_'):
                    capsule_id = doc_id[8:]  # Remove 'capsule_' prefix
                    capsule = self.capsules.get(capsule_id)
                    if capsule and capsule.confidence >= min_confidence:
                        results.append((capsule, score))

        # Also do keyword-based search
        keyword_results = self._search_via_keywords(query, max_results * 2)

        # Merge results, preferring higher scores
        seen_ids = {r[0].id for r in results}
        for capsule, score in keyword_results:
            if capsule.id not in seen_ids and capsule.confidence >= min_confidence:
                results.append((capsule, score * 0.8))  # Slightly lower score for keyword match
                seen_ids.add(capsule.id)

        # Sort by score and return top results
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:max_results]

    def _search_via_rag(self, query: str, max_results: int) -> List[Tuple[str, float]]:
        """Search via RAG semantic search."""
        if not self.rag_manager:
            return []

        try:
            if hasattr(self.rag_manager, 'search'):
                results = self.rag_manager.search(query, top_k=max_results)
                return [(r.get('id', ''), r.get('score', 0)) for r in results]
        except Exception as e:
            print(f"[CapsuleStore] RAG search error: {e}")

        return []

    def _search_via_keywords(self, query: str, max_results: int) -> List[Tuple[Capsule, float]]:
        """Search via keyword matching."""
        keywords = self._extract_keywords(query)

        # Count matches for each capsule
        match_counts: Dict[str, int] = {}
        for keyword in keywords:
            if keyword in self.index:
                for capsule_id in self.index[keyword]:
                    match_counts[capsule_id] = match_counts.get(capsule_id, 0) + 1

        # Convert to results
        results = []
        max_matches = max(match_counts.values()) if match_counts else 1

        for capsule_id, count in match_counts.items():
            capsule = self.capsules.get(capsule_id)
            if capsule:
                # Score based on match count and confidence
                score = (count / max_matches) * 0.5 + capsule.confidence * 0.5
                results.append((capsule, score))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:max_results]

    def update_confidence(self, capsule_id: str, success: bool) -> bool:
        """
        Update capsule confidence after reuse.

        Args:
            capsule_id: The capsule identifier
            success: Whether the reuse was successful

        Returns:
            True if successful, False if capsule not found
        """
        capsule = self.capsules.get(capsule_id)
        if not capsule:
            return False

        # Update use count
        capsule.use_count += 1

        # Update confidence using exponential moving average
        alpha = 0.3  # Weight for new observation
        if success:
            capsule.confidence = alpha * 1.0 + (1 - alpha) * capsule.confidence
        else:
            capsule.confidence = alpha * 0.0 + (1 - alpha) * capsule.confidence

        # Rewrite the JSONL file with updated capsule
        self._rewrite_capsules()

        return True

    def _rewrite_capsules(self) -> None:
        """Rewrite all capsules to JSONL file."""
        try:
            with open(self.CAPSULES_PATH, 'w', encoding='utf-8') as f:
                for capsule in self.capsules.values():
                    f.write(json.dumps(capsule.to_dict(), ensure_ascii=False) + '\n')
        except Exception as e:
            print(f"[CapsuleStore] Error rewriting capsules: {e}")

    def get_capsules_by_gene(self, gene_id: str) -> List[Capsule]:
        """
        Get all capsules for a specific gene.

        Args:
            gene_id: The gene identifier

        Returns:
            List of capsules using that gene
        """
        return [c for c in self.capsules.values() if c.gene_id == gene_id]

    def get_top_capsules(self, limit: int = 10) -> List[Capsule]:
        """
        Get top capsules by confidence and use count.

        Args:
            limit: Maximum number to return

        Returns:
            List of top capsules
        """
        scored = [(c, c.confidence * 0.6 + min(c.use_count / 10, 0.4)) for c in self.capsules.values()]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [c for c, _ in scored[:limit]]

    def cleanup_old_capsules(self, max_age_days: int = 90, min_confidence: float = 0.3) -> int:
        """
        Remove old, low-confidence capsules.

        Args:
            max_age_days: Maximum age in days
            min_confidence: Minimum confidence to keep

        Returns:
            Number of capsules removed
        """
        cutoff = datetime.now().timestamp() - (max_age_days * 86400)
        to_remove = []

        for capsule_id, capsule in self.capsules.items():
            try:
                created = datetime.fromisoformat(capsule.created_at).timestamp()
                if created < cutoff and capsule.confidence < min_confidence and capsule.use_count < 3:
                    to_remove.append(capsule_id)
            except (ValueError, TypeError):
                # Invalid date, consider for removal
                if capsule.use_count < 3:
                    to_remove.append(capsule_id)

        for capsule_id in to_remove:
            del self.capsules[capsule_id]

        if to_remove:
            self._rewrite_capsules()
            self._rebuild_index()

        return len(to_remove)

    def _rebuild_index(self) -> None:
        """Rebuild the keyword index."""
        self.index = {}
        for capsule in self.capsules.values():
            self._index_capsule(capsule)

    def get_stats(self) -> Dict[str, Any]:
        """Get capsule store statistics."""
        if not self.capsules:
            return {
                'total_capsules': 0,
                'avg_confidence': 0,
                'total_uses': 0,
                'by_outcome': {}
            }

        outcomes = {}
        total_uses = 0
        total_confidence = 0

        for capsule in self.capsules.values():
            outcomes[capsule.outcome] = outcomes.get(capsule.outcome, 0) + 1
            total_uses += capsule.use_count
            total_confidence += capsule.confidence

        return {
            'total_capsules': len(self.capsules),
            'avg_confidence': total_confidence / len(self.capsules),
            'total_uses': total_uses,
            'by_outcome': outcomes
        }


# Import re for keyword extraction
import re

# Singleton instance
_store_instance: Optional[CapsuleStore] = None


def get_capsule_store(config: Optional[Dict] = None) -> CapsuleStore:
    """Get or create CapsuleStore singleton."""
    global _store_instance
    if _store_instance is None:
        _store_instance = CapsuleStore(config)
    elif config:
        _store_instance.config.update(config)
    return _store_instance


def reset_capsule_store() -> None:
    """Reset CapsuleStore singleton."""
    global _store_instance
    _store_instance = None

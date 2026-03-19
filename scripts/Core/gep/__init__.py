"""
Project Prometheus - GEP (Genome Evolution Protocol) Module
==========================================================

This module implements the GEP protocol for AI agent self-evolution,
inspired by EvoMap/evolver project.

GEP enables:
- Adaptive fault repair through Gene pattern matching
- Experience reuse via Capsule semantic search
- Evolution chain tracking for auditability
- Confidence-weighted strategy selection

Core Concepts:
- Gene: Reusable evolution strategy template
- Capsule: Successful fix record with confidence score
- Event: Evolution event forming a chain

Usage:
    from Core.gep import GeneManager, CapsuleStore, EvolutionEventLogger
    from Core.gep.models import Gene, Capsule, EvolutionEvent
"""

from .models import (
    Gene, GeneCategory, Capsule, EvolutionEvent,
    ValidationReport, Signal, SelectorDecision
)
from .gene_manager import GeneManager, get_gene_manager
from .capsule_store import CapsuleStore, get_capsule_store
from .event_logger import EventLogger, get_event_logger
from .selector import GEPSelector, get_selector

__all__ = [
    # Models
    'Gene',
    'GeneCategory',
    'Capsule',
    'EvolutionEvent',
    'ValidationReport',
    'Signal',
    'SelectorDecision',
    # Managers
    'GeneManager',
    'get_gene_manager',
    'CapsuleStore',
    'get_capsule_store',
    'EventLogger',
    'get_event_logger',
    'GEPSelector',
    'get_selector',
]

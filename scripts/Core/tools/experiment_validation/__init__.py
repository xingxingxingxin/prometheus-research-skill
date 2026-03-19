"""
Experiment Validation Tools for Project Prometheus

This package provides tools for validating experiments:
- FeasibilityChecker: Pre-assess experiment feasibility
- DataLeakageDetector: Detect potential data leakage
- ResultSanityChecker: Check result reasonableness
- MVPStrategy: Minimum Viable Experiment strategy
- EnvironmentSnapshot: Capture environment for reproducibility
"""

from .feasibility_checker import (
    ExperimentFeasibilityChecker,
    FeasibilityReport,
    check_experiment_feasibility
)
from .data_leakage_detector import (
    DataLeakageDetector,
    LeakageReport,
    detect_data_leakage
)
from .result_sanity_checker import (
    ResultSanityChecker,
    SanityReport,
    check_result_sanity
)
from .mvp_strategy import (
    MVPExperimentStrategy,
    MVPTier,
    get_mvp_strategy
)
from .env_snapshot import (
    EnvironmentSnapshot,
    SnapshotReport,
    capture_environment
)

__all__ = [
    'ExperimentFeasibilityChecker',
    'FeasibilityReport',
    'check_experiment_feasibility',
    'DataLeakageDetector',
    'LeakageReport',
    'detect_data_leakage',
    'ResultSanityChecker',
    'SanityReport',
    'check_result_sanity',
    'MVPExperimentStrategy',
    'MVPTier',
    'get_mvp_strategy',
    'EnvironmentSnapshot',
    'SnapshotReport',
    'capture_environment'
]

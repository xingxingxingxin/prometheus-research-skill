"""
Result Sanity Checker

Check experimental results for reasonableness and detect anomalies.
Identifies overfitting, suspicious improvements, and unrealistic metrics.
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import math


class AnomalyType(Enum):
    """Types of result anomalies."""
    OVERFITTING = "overfitting"
    TOO_GOOD_TO_BE_TRUE = "too_good_to_be_true"
    BASELINE_TOO_LOW = "baseline_too_low"
    IMPROVEMENT_SUSPICIOUS = "improvement_suspicious"
    METRIC_INCONSISTENCY = "metric_inconsistency"
    VARIANCE_TOO_LOW = "variance_too_low"
    TRAIN_VAL_GAP = "train_val_gap"
    COMPARE_TO_SOTA = "compare_to_sota"


class SeverityLevel(Enum):
    """Severity levels for anomalies."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class AnomalyIssue:
    """Detected anomaly issue."""
    anomaly_type: AnomalyType
    severity: SeverityLevel
    description: str
    metric_name: str
    observed_value: float
    expected_range: Tuple[float, float]
    suggestion: str


@dataclass
class SanityReport:
    """Comprehensive sanity check report."""
    is_sane: bool
    anomaly_count: int
    critical_count: int
    issues: List[AnomalyIssue]
    confidence_score: float  # 0-100, higher is more confident in results
    summary: str
    recommendations: List[str]


# Common baselines and reasonable ranges for different tasks
TASK_BASELINES = {
    "image_classification": {
        "mnist": {"random": 0.1, "simple": 0.92, "sota": 0.998},
        "cifar10": {"random": 0.1, "simple": 0.70, "sota": 0.99},
        "cifar100": {"random": 0.01, "simple": 0.45, "sota": 0.96},
        "imagenet": {"random": 0.001, "simple": 0.50, "sota": 0.91},
    },
    "text_classification": {
        "imdb": {"random": 0.5, "simple": 0.85, "sota": 0.97},
        "sst2": {"random": 0.5, "simple": 0.85, "sota": 0.97},
        "ag_news": {"random": 0.25, "simple": 0.88, "sota": 0.95},
    },
    "ner": {
        "conll2003": {"random": 0.0, "simple": 0.85, "sota": 0.95},
    },
    "machine_translation": {
        "wmt14_en_de": {"random": 0.0, "simple": 25, "sota": 35},  # BLEU
        "wmt14_en_fr": {"random": 0.0, "simple": 35, "sota": 45},
    },
    "question_answering": {
        "squad1.1": {"random": 0.0, "simple": 0.70, "sota": 0.94},  # F1
        "squad2.0": {"random": 0.0, "simple": 0.65, "sota": 0.90},
    },
    "language_modeling": {
        "wikitext2": {"random": -1.0, "simple": 100, "sota": 15},  # perplexity
        "ptb": {"random": -1.0, "simple": 80, "sota": 35},
    }
}

# Reasonable improvement ranges over baselines
REASONABLE_IMPROVEMENT = {
    "minor": 0.02,      # 2% improvement is minor
    "moderate": 0.05,   # 5% improvement is moderate
    "significant": 0.10, # 10% improvement is significant
    "major": 0.20,      # 20% improvement is major
    "breakthrough": 0.30  # 30%+ requires extra scrutiny
}


class ResultSanityChecker:
    """
    Check experimental results for sanity and reasonableness.

    Validates:
    - Metric values are within reasonable ranges
    - Improvements over baselines are plausible
    - No signs of overfitting or data leakage
    - Consistency across multiple metrics
    """

    def __init__(self):
        self.issues: List[AnomalyIssue] = []

    def check_results(
        self,
        results: Dict[str, Any],
        task_type: str,
        dataset_name: str,
        baseline_results: Optional[Dict[str, float]] = None,
        train_results: Optional[Dict[str, float]] = None
    ) -> SanityReport:
        """
        Perform comprehensive sanity check on experimental results.

        Args:
            results: Dictionary of metric name -> value for test/val set
            task_type: Type of task (e.g., "image_classification")
            dataset_name: Name of dataset (e.g., "cifar10")
            baseline_results: Results of baseline methods
            train_results: Results on training set (for overfitting detection)

        Returns:
            SanityReport with detailed analysis
        """
        self.issues = []

        # Get expected ranges for this task/dataset
        baselines = self._get_baselines(task_type, dataset_name)

        # Check individual metrics
        for metric_name, value in results.items():
            self._check_metric_value(metric_name, value, baselines, task_type)

        # Check for overfitting
        if train_results:
            self._check_overfitting(results, train_results)

        # Check improvements over baseline
        if baseline_results:
            self._check_improvements(results, baseline_results)

        # Check metric consistency
        self._check_metric_consistency(results, task_type)

        # Check variance (if multiple runs provided)
        if 'std' in results or 'runs' in results:
            self._check_variance(results)

        # Generate report
        return self._generate_report(results)

    def _get_baselines(self, task_type: str, dataset_name: str) -> Dict[str, float]:
        """Get baseline expectations for a task/dataset."""
        dataset_lower = dataset_name.lower()

        if task_type in TASK_BASELINES:
            for dataset_key, baselines in TASK_BASELINES[task_type].items():
                if dataset_key in dataset_lower or dataset_lower in dataset_key:
                    return baselines

        # Default baselines if not found
        return {"random": 0.0, "simple": 0.5, "sota": 0.9}

    def _check_metric_value(
        self,
        metric_name: str,
        value: float,
        baselines: Dict[str, float],
        task_type: str
    ) -> None:
        """Check if a metric value is within reasonable range."""
        metric_lower = metric_name.lower()

        # Determine if higher is better
        higher_is_better = not any(
            kw in metric_lower for kw in ['loss', 'error', 'perplexity', 'rmse', 'mae']
        )

        random_baseline = baselines.get('random', 0.0)
        sota_baseline = baselines.get('sota', 1.0)

        # Check if too good to be true
        if higher_is_better:
            if value > sota_baseline * 1.05:  # 5% above SOTA
                self.issues.append(AnomalyIssue(
                    anomaly_type=AnomalyType.TOO_GOOD_TO_BE_TRUE,
                    severity=SeverityLevel.HIGH,
                    description=f"{metric_name} ({value:.4f}) exceeds SOTA ({sota_baseline:.4f}) significantly",
                    metric_name=metric_name,
                    observed_value=value,
                    expected_range=(random_baseline, sota_baseline * 1.02),
                    suggestion="Verify data leakage, check evaluation methodology"
                ))
            elif value > sota_baseline * 1.02:
                self.issues.append(AnomalyIssue(
                    anomaly_type=AnomalyType.COMPARE_TO_SOTA,
                    severity=SeverityLevel.MEDIUM,
                    description=f"{metric_name} ({value:.4f}) exceeds SOTA ({sota_baseline:.4f})",
                    metric_name=metric_name,
                    observed_value=value,
                    expected_range=(random_baseline, sota_baseline),
                    suggestion="Document methodology carefully, provide reproducibility details"
                ))
        else:  # Lower is better (loss, error, etc.)
            if value < sota_baseline * 0.95:
                self.issues.append(AnomalyIssue(
                    anomaly_type=AnomalyType.TOO_GOOD_TO_BE_TRUE,
                    severity=SeverityLevel.HIGH,
                    description=f"{metric_name} ({value:.4f}) is significantly lower than SOTA ({sota_baseline:.4f})",
                    metric_name=metric_name,
                    observed_value=value,
                    expected_range=(sota_baseline * 0.98, baselines.get('simple', sota_baseline * 2)),
                    suggestion="Verify evaluation methodology, check for label leakage"
                ))

        # Check if suspiciously low
        if higher_is_better and value < random_baseline * 1.1 and value > 0:
            self.issues.append(AnomalyIssue(
                anomaly_type=AnomalyType.BASELINE_TOO_LOW,
                severity=SeverityLevel.MEDIUM,
                description=f"{metric_name} ({value:.4f}) is near random baseline ({random_baseline:.4f})",
                metric_name=metric_name,
                observed_value=value,
                expected_range=(baselines.get('simple', 0.5), sota_baseline),
                suggestion="Check if model is training properly, review hyperparameters"
            ))

    def _check_overfitting(
        self,
        test_results: Dict[str, float],
        train_results: Dict[str, float]
    ) -> None:
        """Check for signs of overfitting."""
        for metric in test_results:
            if metric not in train_results:
                continue

            test_val = test_results[metric]
            train_val = train_results[metric]

            metric_lower = metric.lower()
            higher_is_better = not any(
                kw in metric_lower for kw in ['loss', 'error', 'perplexity', 'rmse', 'mae']
            )

            # Calculate gap
            if higher_is_better:
                gap = train_val - test_val
                gap_ratio = gap / max(train_val, 0.001)
            else:
                gap = test_val - train_val
                gap_ratio = gap / max(train_val, 0.001)

            # Check for significant train-test gap
            if gap_ratio > 0.15:  # 15% gap
                self.issues.append(AnomalyIssue(
                    anomaly_type=AnomalyType.TRAIN_VAL_GAP,
                    severity=SeverityLevel.HIGH if gap_ratio > 0.3 else SeverityLevel.MEDIUM,
                    description=f"Large train-test gap for {metric}: train={train_val:.4f}, test={test_val:.4f} (gap={gap_ratio*100:.1f}%)",
                    metric_name=metric,
                    observed_value=gap_ratio,
                    expected_range=(0.0, 0.15),
                    suggestion="Consider regularization, more data augmentation, or early stopping"
                ))
            elif gap_ratio > 0.05:
                self.issues.append(AnomalyIssue(
                    anomaly_type=AnomalyType.OVERFITTING,
                    severity=SeverityLevel.LOW,
                    description=f"Moderate train-test gap for {metric}: {gap_ratio*100:.1f}%",
                    metric_name=metric,
                    observed_value=gap_ratio,
                    expected_range=(0.0, 0.05),
                    suggestion="Monitor for overfitting during training"
                ))

            # Check for perfect training (suspicious)
            if higher_is_better and train_val > 0.999:
                self.issues.append(AnomalyIssue(
                    anomaly_type=AnomalyType.OVERFITTING,
                    severity=SeverityLevel.MEDIUM,
                    description=f"Near-perfect training accuracy ({train_val:.4f}) indicates potential overfitting",
                    metric_name=metric,
                    observed_value=train_val,
                    expected_range=(0.8, 0.99),
                    suggestion="Add regularization or check for data leakage in training set"
                ))

    def _check_improvements(
        self,
        results: Dict[str, float],
        baseline_results: Dict[str, float]
    ) -> None:
        """Check if improvements over baseline are reasonable."""
        for metric in results:
            if metric not in baseline_results:
                continue

            current = results[metric]
            baseline = baseline_results[metric]

            metric_lower = metric.lower()
            higher_is_better = not any(
                kw in metric_lower for kw in ['loss', 'error', 'perplexity', 'rmse', 'mae']
            )

            # Calculate improvement
            if higher_is_better:
                if baseline > 0:
                    improvement = (current - baseline) / baseline
                else:
                    improvement = current - baseline
            else:
                if baseline > 0:
                    improvement = (baseline - current) / baseline
                else:
                    improvement = baseline - current

            # Check for suspicious improvements
            if improvement > REASONABLE_IMPROVEMENT["breakthrough"]:
                self.issues.append(AnomalyIssue(
                    anomaly_type=AnomalyType.IMPROVEMENT_SUSPICIOUS,
                    severity=SeverityLevel.HIGH,
                    description=f"Suspicious improvement over baseline for {metric}: {improvement*100:.1f}%",
                    metric_name=metric,
                    observed_value=improvement,
                    expected_range=(0.0, REASONABLE_IMPROVEMENT["breakthrough"]),
                    suggestion="Verify methodology, check for data leakage, compare with SOTA"
                ))
            elif improvement > REASONABLE_IMPROVEMENT["major"]:
                self.issues.append(AnomalyIssue(
                    anomaly_type=AnomalyType.IMPROVEMENT_SUSPICIOUS,
                    severity=SeverityLevel.MEDIUM,
                    description=f"Large improvement over baseline for {metric}: {improvement*100:.1f}%",
                    metric_name=metric,
                    observed_value=improvement,
                    expected_range=(0.0, REASONABLE_IMPROVEMENT["major"]),
                    suggestion="Document methodology, provide ablation studies"
                ))

    def _check_metric_consistency(
        self,
        results: Dict[str, float],
        task_type: str
    ) -> None:
        """Check consistency between related metrics."""
        # Check accuracy-precision-recall consistency
        if 'accuracy' in results and 'precision' in results and 'recall' in results:
            acc = results['accuracy']
            prec = results['precision']
            rec = results['recall']

            # F1 should be approximately 2*prec*rec/(prec+rec)
            if 'f1' in results:
                expected_f1 = 2 * prec * rec / max(prec + rec, 0.001)
                actual_f1 = results['f1']

                if abs(expected_f1 - actual_f1) > 0.05:
                    self.issues.append(AnomalyIssue(
                        anomaly_type=AnomalyType.METRIC_INCONSISTENCY,
                        severity=SeverityLevel.MEDIUM,
                        description=f"F1 ({actual_f1:.4f}) doesn't match precision ({prec:.4f}) and recall ({rec:.4f})",
                        metric_name="f1",
                        observed_value=actual_f1,
                        expected_range=(expected_f1 - 0.02, expected_f1 + 0.02),
                        suggestion="Check metric calculation implementation"
                    ))

        # Check loss vs accuracy consistency
        if 'loss' in results and 'accuracy' in results:
            loss = results['loss']
            acc = results['accuracy']

            # High accuracy shouldn't have high loss
            if acc > 0.9 and loss > 0.5:
                self.issues.append(AnomalyIssue(
                    anomaly_type=AnomalyType.METRIC_INCONSISTENCY,
                    severity=SeverityLevel.LOW,
                    description=f"High accuracy ({acc:.4f}) with high loss ({loss:.4f}) is unusual",
                    metric_name="loss",
                    observed_value=loss,
                    expected_range=(0.0, 0.3),
                    suggestion="Check loss function implementation or class balance"
                ))

    def _check_variance(self, results: Dict[str, Any]) -> None:
        """Check if variance across runs is reasonable."""
        if 'std' in results:
            std = results['std']
            mean = results.get('mean', results.get('accuracy', results.get('score', 0.5)))

            cv = std / max(mean, 0.001)  # Coefficient of variation

            # Very low variance is suspicious (results too stable)
            if cv < 0.001 and mean > 0:
                self.issues.append(AnomalyIssue(
                    anomaly_type=AnomalyType.VARIANCE_TOO_LOW,
                    severity=SeverityLevel.LOW,
                    description=f"Variance is suspiciously low (CV={cv:.4f})",
                    metric_name="variance",
                    observed_value=cv,
                    expected_range=(0.01, 0.1),
                    suggestion="Results are unusually stable - verify multiple independent runs"
                ))

            # Very high variance is concerning
            if cv > 0.2:
                self.issues.append(AnomalyIssue(
                    anomaly_type=AnomalyType.VARIANCE_TOO_LOW,
                    severity=SeverityLevel.MEDIUM,
                    description=f"High variance across runs (CV={cv:.4f})",
                    metric_name="variance",
                    observed_value=cv,
                    expected_range=(0.01, 0.1),
                    suggestion="Results are unstable - consider more runs or fix random seeds"
                ))

    def _generate_report(self, results: Dict[str, float]) -> SanityReport:
        """Generate comprehensive sanity report."""
        critical_count = sum(
            1 for issue in self.issues
            if issue.severity in [SeverityLevel.CRITICAL, SeverityLevel.HIGH]
        )

        # Calculate confidence score
        confidence = 100.0
        for issue in self.issues:
            if issue.severity == SeverityLevel.CRITICAL:
                confidence -= 40
            elif issue.severity == SeverityLevel.HIGH:
                confidence -= 25
            elif issue.severity == SeverityLevel.MEDIUM:
                confidence -= 10
            elif issue.severity == SeverityLevel.LOW:
                confidence -= 3
        confidence = max(confidence, 0)

        # Determine if results are sane
        is_sane = critical_count == 0

        # Generate summary
        if is_sane:
            summary = f"Results appear reasonable (confidence: {confidence:.0f}%)"
            if len(self.issues) > 0:
                summary += f" with {len(self.issues)} minor concerns"
        else:
            summary = f"Results have {critical_count} critical issues requiring attention"

        # Generate recommendations
        recommendations = list(set(issue.suggestion for issue in self.issues))

        return SanityReport(
            is_sane=is_sane,
            anomaly_count=len(self.issues),
            critical_count=critical_count,
            issues=self.issues,
            confidence_score=confidence,
            summary=summary,
            recommendations=recommendations
        )

    def quick_check(
        self,
        accuracy: float,
        baseline_accuracy: float,
        train_accuracy: Optional[float] = None
    ) -> Tuple[bool, str]:
        """Quick sanity check for classification accuracy."""
        results = {"accuracy": accuracy}
        baseline = {"accuracy": baseline_accuracy}
        train = {"accuracy": train_accuracy} if train_accuracy else None

        report = self.check_results(
            results,
            "image_classification",
            "unknown",
            baseline,
            train
        )

        return report.is_sane, report.summary


def check_result_sanity(
    results: Dict[str, float],
    task_type: str,
    dataset_name: str,
    baseline_results: Optional[Dict[str, float]] = None,
    train_results: Optional[Dict[str, float]] = None
) -> SanityReport:
    """Convenience function for result sanity check."""
    checker = ResultSanityChecker()
    return checker.check_results(
        results,
        task_type,
        dataset_name,
        baseline_results,
        train_results
    )


if __name__ == "__main__":
    # Test result sanity checker
    checker = ResultSanityChecker()

    # Test case 1: Reasonable results
    print("Test 1: Reasonable results")
    report = checker.check_results(
        {"accuracy": 0.92, "f1": 0.90},
        "image_classification",
        "cifar10",
        {"accuracy": 0.85, "f1": 0.83}
    )
    print(f"  Is sane: {report.is_sane}")
    print(f"  Summary: {report.summary}")
    print()

    # Test case 2: Suspicious results (too good)
    print("Test 2: Suspiciously good results")
    checker2 = ResultSanityChecker()
    report2 = checker2.check_results(
        {"accuracy": 0.999, "f1": 0.998},
        "image_classification",
        "cifar10",
        {"accuracy": 0.85}
    )
    print(f"  Is sane: {report2.is_sane}")
    print(f"  Issues: {len(report2.issues)}")
    for issue in report2.issues:
        print(f"    [{issue.severity.value}] {issue.description}")
    print()

    # Test case 3: Overfitting
    print("Test 3: Overfitting detection")
    checker3 = ResultSanityChecker()
    report3 = checker3.check_results(
        {"accuracy": 0.80},
        "image_classification",
        "cifar10",
        {"accuracy": 0.70},
        {"accuracy": 0.99}  # Very high training accuracy
    )
    print(f"  Is sane: {report3.is_sane}")
    print(f"  Summary: {report3.summary}")

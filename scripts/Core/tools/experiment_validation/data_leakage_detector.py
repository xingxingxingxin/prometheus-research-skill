"""
Data Leakage Detector

Automatically detect potential data leakage in ML experiments.
Common leakage patterns: train-test contamination, feature leakage,
temporal leakage, target leakage.
"""

from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import re
import ast


class LeakageType(Enum):
    """Types of data leakage."""
    TRAIN_TEST_CONTAMINATION = "train_test_contamination"
    FEATURE_LEAKAGE = "feature_leakage"
    TARGET_LEAKAGE = "target_leakage"
    TEMPORAL_LEAKAGE = "temporal_leakage"
    PREPROCESSING_LEAKAGE = "preprocessing_leakage"
    AUGMENTATION_LEAKAGE = "augmentation_leakation"
    VALIDATION_LEAKAGE = "validation_leakage"


class SeverityLevel(Enum):
    """Severity levels for leakage detection."""
    CRITICAL = "critical"      # Definitely invalidates results
    HIGH = "high"              # Likely invalidates results
    MEDIUM = "medium"          # May affect results
    LOW = "low"                # Minor concern
    INFO = "info"              # Informational, no action needed


@dataclass
class LeakageIssue:
    """Detected leakage issue."""
    leakage_type: LeakageType
    severity: SeverityLevel
    location: str
    description: str
    suggestion: str
    code_snippet: Optional[str] = None
    line_number: Optional[int] = None


@dataclass
class LeakageReport:
    """Comprehensive leakage detection report."""
    has_critical_issues: bool
    total_issues: int
    issues_by_severity: Dict[str, int]
    issues: List[LeakageIssue]
    recommendations: List[str]
    overall_risk_score: float  # 0-100, higher is worse


class DataLeakageDetector:
    """
    Detect potential data leakage in ML experiments.

    Analyzes:
    - Code patterns that may cause leakage
    - Data split handling
    - Feature engineering practices
    - Preprocessing order
    - Data augmentation strategies
    """

    # Dangerous patterns in code
    DANGEROUS_PATTERNS = {
        # Train-test contamination
        r'fit_transform\s*\(\s*.*(?:train|test|X|data)': {
            'type': LeakageType.PREPROCESSING_LEAKAGE,
            'severity': SeverityLevel.HIGH,
            'message': 'fit_transform on combined data may cause leakage',
        },
        r'normalize\s*\(\s*.*(?:train|test).*\)': {
            'type': LeakageType.PREPROCESSING_LEAKAGE,
            'severity': SeverityLevel.MEDIUM,
            'message': 'Normalization should be fit on train only',
        },
        r'shuffle\s*\([^)]*\)\s*(?:train|data|X)': {
            'type': LeakageType.TRAIN_TEST_CONTAMINATION,
            'severity': SeverityLevel.MEDIUM,
            'message': 'Shuffling before split may cause temporal leakage',
        },

        # Feature leakage
        r'(?:target|label|y)[_\-]?(?:feature|col|column)': {
            'type': LeakageType.TARGET_LEAKAGE,
            'severity': SeverityLevel.CRITICAL,
            'message': 'Target used as feature - definite leakage',
        },
        r'(?:future|next|tomorrow|post)[_\-]?(?:feature|data)': {
            'type': LeakageType.TEMPORAL_LEAKAGE,
            'severity': SeverityLevel.CRITICAL,
            'message': 'Future information used as feature',
        },

        # Validation leakage
        r'train_test_split\s*\([^)]*random_state\s*=\s*None': {
            'type': LeakageType.VALIDATION_LEAKAGE,
            'severity': SeverityLevel.LOW,
            'message': 'No random_state set - results may not be reproducible',
        },
    }

    # Safe patterns (good practices)
    SAFE_PATTERNS = [
        r'stratify\s*=',
        r'random_state\s*=\s*\d+',
        r'shuffle\s*=\s*False',
        r'GroupKFold',
        r'TimeSeriesSplit',
    ]

    def __init__(self):
        self.detected_issues: List[LeakageIssue] = []

    def analyze_code(self, code: str, file_name: str = "unknown") -> List[LeakageIssue]:
        """
        Analyze code for potential leakage patterns.

        Args:
            code: Source code to analyze
            file_name: Name of the file for reporting

        Returns:
            List of detected issues
        """
        issues = []
        lines = code.split('\n')

        for i, line in enumerate(lines, 1):
            for pattern, info in self.DANGEROUS_PATTERNS.items():
                if re.search(pattern, line, re.IGNORECASE):
                    # Check if this is a false positive (has safe pattern nearby)
                    context = self._get_context(lines, i - 1, window=3)
                    if not any(re.search(sp, context, re.IGNORECASE) for sp in self.SAFE_PATTERNS):
                        issues.append(LeakageIssue(
                            leakage_type=info['type'],
                            severity=info['severity'],
                            location=f"{file_name}:{i}",
                            description=info['message'],
                            suggestion=self._get_suggestion(info['type']),
                            code_snippet=line.strip(),
                            line_number=i
                        ))

        self.detected_issues.extend(issues)
        return issues

    def analyze_data_split(
        self,
        split_info: Dict[str, Any],
        data_info: Optional[Dict] = None
    ) -> List[LeakageIssue]:
        """
        Analyze data split configuration for potential issues.

        Args:
            split_info: Information about how data is split
                - method: 'random', 'stratified', 'time', 'group'
                - test_size: float
                - random_state: int or None
                - has_validation: bool
            data_info: Information about the dataset
                - has_temporal_order: bool
                - has_groups: bool
                - is_imbalanced: bool

        Returns:
            List of detected issues
        """
        issues = []

        method = split_info.get('method', 'random')
        has_validation = split_info.get('has_validation', False)
        random_state = split_info.get('random_state')

        if data_info is None:
            data_info = {}

        has_temporal = data_info.get('has_temporal_order', False)
        has_groups = data_info.get('has_groups', False)
        is_imbalanced = data_info.get('is_imbalanced', False)

        # Check temporal data handling
        if has_temporal and method == 'random':
            issues.append(LeakageIssue(
                leakage_type=LeakageType.TEMPORAL_LEAKAGE,
                severity=SeverityLevel.HIGH,
                location="Data split configuration",
                description="Random split on temporal data causes future leakage",
                suggestion="Use TimeSeriesSplit or temporal holdout"
            ))

        # Check group handling
        if has_groups and method not in ['group', 'GroupKFold']:
            issues.append(LeakageIssue(
                leakage_type=LeakageType.TRAIN_TEST_CONTAMINATION,
                severity=SeverityLevel.MEDIUM,
                location="Data split configuration",
                description="Group data split without GroupKFold may cause leakage",
                suggestion="Use GroupKFold to ensure samples from same group stay together"
            ))

        # Check imbalanced data
        if is_imbalanced and method != 'stratified':
            issues.append(LeakageIssue(
                leakage_type=LeakageType.VALIDATION_LEAKAGE,
                severity=SeverityLevel.MEDIUM,
                location="Data split configuration",
                description="Imbalanced data without stratification may cause unreliable validation",
                suggestion="Use stratified sampling for imbalanced datasets"
            ))

        # Check reproducibility
        if random_state is None:
            issues.append(LeakageIssue(
                leakage_type=LeakageType.VALIDATION_LEAKAGE,
                severity=SeverityLevel.LOW,
                location="Data split configuration",
                description="No random_state set - results not reproducible",
                suggestion="Set random_state for reproducible splits"
            ))

        self.detected_issues.extend(issues)
        return issues

    def analyze_preprocessing(
        self,
        preprocessing_steps: List[Dict[str, Any]]
    ) -> List[LeakageIssue]:
        """
        Analyze preprocessing pipeline for leakage.

        Args:
            preprocessing_steps: List of preprocessing steps with:
                - name: str
                - fit_on: 'train' or 'all'
                - apply_to: list of data subsets

        Returns:
            List of detected issues
        """
        issues = []

        for i, step in enumerate(preprocessing_steps):
            name = step.get('name', 'unknown')
            fit_on = step.get('fit_on', 'unknown')
            apply_to = step.get('apply_to', [])

            # Check if fitted on all data
            if fit_on == 'all' or 'all' in str(fit_on).lower():
                issues.append(LeakageIssue(
                    leakage_type=LeakageType.PREPROCESSING_LEAKAGE,
                    severity=SeverityLevel.HIGH,
                    location=f"Preprocessing step {i+1}: {name}",
                    description=f"'{name}' fitted on all data including test set",
                    suggestion=f"Fit '{name}' on training data only, then transform test data"
                ))

            # Check order (splitting should happen before preprocessing)
            if 'split' in name.lower() and i > 0:
                issues.append(LeakageIssue(
                    leakage_type=LeakageType.PREPROCESSING_LEAKAGE,
                    severity=SeverityLevel.HIGH,
                    location=f"Preprocessing step {i+1}: {name}",
                    description="Data split after preprocessing - test data contaminated",
                    suggestion="Split data before any preprocessing steps"
                ))

        self.detected_issues.extend(issues)
        return issues

    def analyze_augmentation(
        self,
        augmentation_config: Dict[str, Any],
        apply_to_train_only: bool = True
    ) -> List[LeakageIssue]:
        """
        Analyze data augmentation for potential leakage.

        Args:
            augmentation_config: Augmentation settings
            apply_to_train_only: Whether augmentation is applied only to training data

        Returns:
            List of detected issues
        """
        issues = []

        if not apply_to_train_only:
            issues.append(LeakageIssue(
                leakage_type=LeakageType.AUGMENTATION_LEAKAGE,
                severity=SeverityLevel.HIGH,
                location="Data augmentation",
                description="Augmentation applied to validation/test data",
                suggestion="Apply augmentation only to training data"
            ))

        # Check for test-time augmentation mixing
        if augmentation_config.get('mix_augmented', False):
            issues.append(LeakageIssue(
                leakage_type=LeakageType.AUGMENTATION_LEAKAGE,
                severity=SeverityLevel.MEDIUM,
                location="Data augmentation",
                description="Augmented samples may overlap with original samples in train/val split",
                suggestion="Ensure augmented samples are kept together with their originals during split"
            ))

        self.detected_issues.extend(issues)
        return issues

    def check_feature_correlation(
        self,
        feature_names: List[str],
        target_name: str
    ) -> List[LeakageIssue]:
        """
        Check feature names for potential target leakage indicators.

        Args:
            feature_names: List of feature names
            target_name: Name of the target variable

        Returns:
            List of detected issues
        """
        issues = []
        target_lower = target_name.lower()

        suspicious_patterns = [
            r'(?:^|_)(?:score|rating|result|outcome|answer)(?:_|$)',
            r'(?:^|_)(?:future|next|post|after)(?:_|$)',
            r'(?:^|_)(?:final|last|end)(?:_|$)',
            rf'(?:^|_){re.escape(target_lower)}(?:_|$)',
        ]

        for feature in feature_names:
            feature_lower = feature.lower()

            for pattern in suspicious_patterns:
                if re.search(pattern, feature_lower, re.IGNORECASE):
                    issues.append(LeakageIssue(
                        leakage_type=LeakageType.FEATURE_LEAKAGE,
                        severity=SeverityLevel.HIGH,
                        location=f"Feature: {feature}",
                        description=f"Feature '{feature}' may contain target information",
                        suggestion=f"Review feature '{feature}' for potential target leakage"
                    ))
                    break

        self.detected_issues.extend(issues)
        return issues

    def generate_report(self) -> LeakageReport:
        """Generate comprehensive leakage detection report."""
        # Count by severity
        severity_counts = {}
        for severity in SeverityLevel:
            severity_counts[severity.value] = sum(
                1 for issue in self.detected_issues
                if issue.severity == severity
            )

        # Check for critical issues
        has_critical = any(
            issue.severity in [SeverityLevel.CRITICAL, SeverityLevel.HIGH]
            for issue in self.detected_issues
        )

        # Calculate risk score
        risk_score = 0
        for issue in self.detected_issues:
            if issue.severity == SeverityLevel.CRITICAL:
                risk_score += 40
            elif issue.severity == SeverityLevel.HIGH:
                risk_score += 20
            elif issue.severity == SeverityLevel.MEDIUM:
                risk_score += 10
            elif issue.severity == SeverityLevel.LOW:
                risk_score += 2

        risk_score = min(risk_score, 100)

        # Generate recommendations
        recommendations = self._generate_recommendations()

        return LeakageReport(
            has_critical_issues=has_critical,
            total_issues=len(self.detected_issues),
            issues_by_severity=severity_counts,
            issues=self.detected_issues,
            recommendations=recommendations,
            overall_risk_score=risk_score
        )

    def _get_context(self, lines: List[str], center: int, window: int = 3) -> str:
        """Get context around a line."""
        start = max(0, center - window)
        end = min(len(lines), center + window + 1)
        return '\n'.join(lines[start:end])

    def _get_suggestion(self, leakage_type: LeakageType) -> str:
        """Get suggestion for fixing a leakage type."""
        suggestions = {
            LeakageType.TRAIN_TEST_CONTAMINATION:
                "Ensure train and test data are strictly separated",
            LeakageType.FEATURE_LEAKAGE:
                "Review feature engineering to remove target-correlated features",
            LeakageType.TARGET_LEAKAGE:
                "Remove any features derived from the target variable",
            LeakageType.TEMPORAL_LEAKAGE:
                "Use temporal validation (train on past, test on future)",
            LeakageType.PREPROCESSING_LEAKAGE:
                "Fit preprocessing on train data only, then transform test data",
            LeakageType.AUGMENTATION_LEAKAGE:
                "Apply augmentation only to training data",
            LeakageType.VALIDATION_LEAKAGE:
                "Use proper cross-validation with fixed random seeds",
        }
        return suggestions.get(leakage_type, "Review and fix the detected issue")

    def _generate_recommendations(self) -> List[str]:
        """Generate actionable recommendations based on detected issues."""
        recommendations = []

        # Group issues by type
        issues_by_type: Dict[LeakageType, List[LeakageIssue]] = {}
        for issue in self.detected_issues:
            if issue.leakage_type not in issues_by_type:
                issues_by_type[issue.leakage_type] = []
            issues_by_type[issue.leakage_type].append(issue)

        # Generate type-specific recommendations
        if LeakageType.PREPROCESSING_LEAKAGE in issues_by_type:
            recommendations.append(
                "Use sklearn Pipeline to ensure preprocessing is fitted only on training data"
            )

        if LeakageType.TEMPORAL_LEAKAGE in issues_by_type:
            recommendations.append(
                "For time-series data, use TimeSeriesSplit or temporal holdout validation"
            )

        if LeakageType.TARGET_LEAKAGE in issues_by_type:
            recommendations.append(
                "Audit all features for target correlation and remove leaking features"
            )

        if LeakageType.TRAIN_TEST_CONTAMINATION in issues_by_type:
            recommendations.append(
                "Ensure data split is performed before any data processing"
            )

        # General recommendations
        if self.detected_issues:
            recommendations.append(
                "Review all detected issues before finalizing experimental results"
            )

        return recommendations

    def clear(self):
        """Clear all detected issues."""
        self.detected_issues = []


def detect_data_leakage(
    code: str = "",
    split_info: Optional[Dict] = None,
    preprocessing_steps: Optional[List[Dict]] = None,
    augmentation_config: Optional[Dict] = None,
    feature_names: Optional[List[str]] = None,
    target_name: str = ""
) -> LeakageReport:
    """
    Convenience function for comprehensive leakage detection.

    Args:
        code: Source code to analyze
        split_info: Data split configuration
        preprocessing_steps: List of preprocessing steps
        augmentation_config: Data augmentation settings
        feature_names: List of feature names
        target_name: Name of target variable

    Returns:
        LeakageReport with all detected issues
    """
    detector = DataLeakageDetector()

    if code:
        detector.analyze_code(code)

    if split_info:
        detector.analyze_data_split(split_info)

    if preprocessing_steps:
        detector.analyze_preprocessing(preprocessing_steps)

    if augmentation_config:
        detector.analyze_augmentation(augmentation_config)

    if feature_names and target_name:
        detector.check_feature_correlation(feature_names, target_name)

    return detector.generate_report()


if __name__ == "__main__":
    # Test data leakage detector
    test_code = """
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

# Bad practice - fit on all data
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Then split
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y)

# Using future feature
df['future_price'] = df['price'].shift(-1)
features = ['future_price', 'volume', 'open']
"""

    detector = DataLeakageDetector()
    issues = detector.analyze_code(test_code, "example.py")

    print(f"Found {len(issues)} potential issues:")
    for issue in issues:
        print(f"  [{issue.severity.value}] {issue.description}")
        print(f"    at {issue.location}")
        print(f"    Suggestion: {issue.suggestion}")
        print()

    report = detector.generate_report()
    print(f"Overall risk score: {report.overall_risk_score}/100")
    print(f"Recommendations: {report.recommendations}")

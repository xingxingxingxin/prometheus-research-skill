"""
Experiment Feasibility Checker

Pre-assess experiment feasibility before implementation.
Evaluates computational resources, data availability, time constraints,
and technical complexity.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import re


class FeasibilityLevel(Enum):
    """Feasibility assessment levels."""
    HIGH = "high"           # Easy to implement, low risk
    MEDIUM = "medium"       # Moderate complexity, some risk
    LOW = "low"             # Complex, high risk
    NOT_RECOMMENDED = "not_recommended"  # Too risky or impractical


@dataclass
class ResourceEstimate:
    """Resource requirement estimate."""
    gpu_hours: float = 0.0
    cpu_hours: float = 0.0
    memory_gb: float = 0.0
    storage_gb: float = 0.0
    dataset_size: str = "unknown"


@dataclass
class FeasibilityReport:
    """Comprehensive feasibility assessment report."""
    overall_level: FeasibilityLevel
    resource_estimate: ResourceEstimate
    time_estimate_hours: float
    risk_factors: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    innovation_score: float = 0.0
    feasibility_score: float = 0.0
    details: Dict = field(default_factory=dict)


class ExperimentFeasibilityChecker:
    """
    Check experiment feasibility before implementation.

    Evaluates multiple dimensions:
    - Computational resource requirements
    - Data availability and size
    - Implementation complexity
    - Time constraints
    - Risk factors
    """

    # Resource thresholds (conservative estimates)
    GPU_THRESHOLD_LOW = 10  # hours
    GPU_THRESHOLD_MEDIUM = 100  # hours
    CPU_THRESHOLD_LOW = 50  # hours
    CPU_THRESHOLD_MEDIUM = 200  # hours
    MEMORY_THRESHOLD_LOW = 16  # GB
    MEMORY_THRESHOLD_MEDIUM = 64  # GB

    # Dataset size patterns
    SMALL_DATASET_PATTERNS = [
        r'\bmnist\b', r'\bcifar[-]?10\b', r'\bimdb\b',
        r'\btoy\b', r'\bsmall\b', r'\bsample\b'
    ]
    MEDIUM_DATASET_PATTERNS = [
        r'\bcifar[-]?100\b', r'\bimagenet[-]?1k\b',
        r'\bcoco\b', r'\bmedium\b'
    ]
    LARGE_DATASET_PATTERNS = [
        r'\bimagenet[-]?21k\b', r'\bcommoncrawl\b',
        r'\blarge\b', r'\bfull\b', r'\bbillion\b'
    ]

    def __init__(self):
        self.common_baselines = {
            'resnet18': {'gpu_hours': 2, 'memory_gb': 4, 'complexity': 'low'},
            'resnet50': {'gpu_hours': 8, 'memory_gb': 8, 'complexity': 'low'},
            'bert_base': {'gpu_hours': 20, 'memory_gb': 16, 'complexity': 'medium'},
            'bert_large': {'gpu_hours': 80, 'memory_gb': 32, 'complexity': 'medium'},
            'gpt2': {'gpu_hours': 50, 'memory_gb': 24, 'complexity': 'high'},
            'llama_7b': {'gpu_hours': 200, 'memory_gb': 32, 'complexity': 'high'},
            'stable_diffusion': {'gpu_hours': 100, 'memory_gb': 24, 'complexity': 'high'},
        }

    def check_feasibility(
        self,
        experiment_description: str,
        method_name: str = "",
        dataset_info: Optional[Dict] = None,
        compute_budget: Optional[Dict] = None
    ) -> FeasibilityReport:
        """
        Perform comprehensive feasibility check.

        Args:
            experiment_description: Description of the experiment
            method_name: Name of the main method/model
            dataset_info: Information about datasets
            compute_budget: Available computational resources

        Returns:
            FeasibilityReport with detailed assessment
        """
        # Parse and analyze experiment description
        desc_lower = experiment_description.lower()

        # Estimate resources
        resources = self._estimate_resources(desc_lower, method_name, dataset_info)

        # Estimate time
        time_estimate = self._estimate_time(resources, desc_lower)

        # Identify risk factors
        risks = self._identify_risks(desc_lower, resources, dataset_info)

        # Calculate innovation score
        innovation_score = self._assess_innovation(desc_lower)

        # Calculate feasibility score
        feasibility_score = self._calculate_feasibility_score(
            resources, time_estimate, len(risks)
        )

        # Determine overall level
        overall_level = self._determine_level(feasibility_score, resources)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            overall_level, resources, risks
        )

        return FeasibilityReport(
            overall_level=overall_level,
            resource_estimate=resources,
            time_estimate_hours=time_estimate,
            risk_factors=risks,
            recommendations=recommendations,
            innovation_score=innovation_score,
            feasibility_score=feasibility_score,
            details={
                'method_name': method_name,
                'dataset_info': dataset_info,
                'compute_budget': compute_budget
            }
        )

    def _estimate_resources(
        self,
        description: str,
        method_name: str,
        dataset_info: Optional[Dict]
    ) -> ResourceEstimate:
        """Estimate resource requirements."""
        estimate = ResourceEstimate()

        # Check against known baselines
        method_lower = method_name.lower() if method_name else ""
        for baseline, specs in self.common_baselines.items():
            if baseline in method_lower or baseline in description:
                estimate.gpu_hours = specs['gpu_hours']
                estimate.memory_gb = specs['memory_gb']
                break

        # Estimate based on keywords if no baseline match
        if estimate.gpu_hours == 0:
            if any(kw in description for kw in ['pretrain', 'large scale', 'distributed']):
                estimate.gpu_hours = self.GPU_THRESHOLD_MEDIUM * 2
                estimate.memory_gb = self.MEMORY_THRESHOLD_MEDIUM
            elif any(kw in description for kw in ['fine-tune', 'finetune', 'transfer']):
                estimate.gpu_hours = self.GPU_THRESHOLD_LOW
                estimate.memory_gb = self.MEMORY_THRESHOLD_LOW
            else:
                estimate.gpu_hours = self.GPU_THRESHOLD_LOW / 2
                estimate.memory_gb = self.MEMORY_THRESHOLD_LOW / 2

        # Estimate dataset size
        estimate.dataset_size = self._estimate_dataset_size(description, dataset_info)

        # Adjust based on dataset size
        if estimate.dataset_size == 'large':
            estimate.gpu_hours *= 3
            estimate.storage_gb = 100
        elif estimate.dataset_size == 'medium':
            estimate.gpu_hours *= 1.5
            estimate.storage_gb = 30
        else:
            estimate.storage_gb = 5

        # Check for multiple experiments
        if any(kw in description for kw in ['ablation', 'grid search', 'hyperparameter']):
            estimate.gpu_hours *= 2

        return estimate

    def _estimate_dataset_size(self, description: str, dataset_info: Optional[Dict]) -> str:
        """Estimate dataset size category."""
        # Check patterns
        for pattern in self.LARGE_DATASET_PATTERNS:
            if re.search(pattern, description):
                return 'large'

        for pattern in self.MEDIUM_DATASET_PATTERNS:
            if re.search(pattern, description):
                return 'medium'

        for pattern in self.SMALL_DATASET_PATTERNS:
            if re.search(pattern, description):
                return 'small'

        # Check dataset_info if available
        if dataset_info:
            samples = dataset_info.get('num_samples', 0)
            if samples > 1000000:
                return 'large'
            elif samples > 100000:
                return 'medium'
            else:
                return 'small'

        return 'unknown'

    def _estimate_time(self, resources: ResourceEstimate, description: str) -> float:
        """Estimate total time including implementation."""
        # Base implementation time
        impl_time = 0

        if any(kw in description for kw in ['novel architecture', 'new model', 'custom']):
            impl_time = 40  # hours for implementation
        elif any(kw in description for kw in ['modified', 'extended', 'adapted']):
            impl_time = 20
        else:
            impl_time = 8  # simple baseline

        # Debug and iteration time (usually 2-3x compute time)
        debug_factor = 2.5
        compute_time = resources.gpu_hours

        # Total time
        return impl_time + compute_time * debug_factor

    def _identify_risks(
        self,
        description: str,
        resources: ResourceEstimate,
        dataset_info: Optional[Dict]
    ) -> List[str]:
        """Identify potential risk factors."""
        risks = []

        # Resource risks
        if resources.gpu_hours > self.GPU_THRESHOLD_MEDIUM:
            risks.append("High GPU resource requirement - may exceed typical budget")

        if resources.memory_gb > self.MEMORY_THRESHOLD_MEDIUM:
            risks.append("High memory requirement - needs specialized hardware")

        # Implementation risks
        if any(kw in description for kw in ['novel', 'new', 'first', 'unprecedented']):
            risks.append("Novel approach - implementation uncertainty is high")

        if any(kw in description for kw in ['distributed', 'multi-gpu', 'cluster']):
            risks.append("Distributed training adds complexity and debugging difficulty")

        # Data risks
        if 'synthetic' in description:
            risks.append("Synthetic data - may not generalize to real-world scenarios")

        if dataset_info and dataset_info.get('requires_collection', False):
            risks.append("Requires new data collection - timeline risk")

        # Evaluation risks
        if any(kw in description for kw in ['human evaluation', 'user study']):
            risks.append("Human evaluation required - adds significant time and cost")

        # Reproducibility risks
        if any(kw in description for kw in ['random', 'stochastic', 'probabilistic']):
            risks.append("Stochastic methods - requires multiple runs for statistical significance")

        return risks

    def _assess_innovation(self, description: str) -> float:
        """Assess innovation level (0-100)."""
        score = 50  # baseline

        # Innovation indicators
        innovation_keywords = [
            ('novel', 15), ('new', 10), ('first', 15),
            ('unprecedented', 20), ('breakthrough', 25),
            ('innovative', 15), ('original', 10)
        ]

        for keyword, points in innovation_keywords:
            if keyword in description:
                score += points

        # Method combination innovation
        if any(kw in description for kw in ['combine', 'integrate', 'unify', 'hybrid']):
            score += 10

        # Cap at 100
        return min(score, 100)

    def _calculate_feasibility_score(
        self,
        resources: ResourceEstimate,
        time_hours: float,
        num_risks: int
    ) -> float:
        """Calculate overall feasibility score (0-100, higher is more feasible)."""
        score = 100

        # Deduct for resource requirements
        if resources.gpu_hours > self.GPU_THRESHOLD_MEDIUM:
            score -= 30
        elif resources.gpu_hours > self.GPU_THRESHOLD_LOW:
            score -= 15

        if resources.memory_gb > self.MEMORY_THRESHOLD_MEDIUM:
            score -= 20
        elif resources.memory_gb > self.MEMORY_THRESHOLD_LOW:
            score -= 10

        # Deduct for time
        if time_hours > 200:
            score -= 25
        elif time_hours > 100:
            score -= 15
        elif time_hours > 50:
            score -= 5

        # Deduct for risks
        score -= num_risks * 10

        return max(score, 0)

    def _determine_level(
        self,
        feasibility_score: float,
        resources: ResourceEstimate
    ) -> FeasibilityLevel:
        """Determine overall feasibility level."""
        if feasibility_score >= 70:
            return FeasibilityLevel.HIGH
        elif feasibility_score >= 50:
            return FeasibilityLevel.MEDIUM
        elif feasibility_score >= 30:
            return FeasibilityLevel.LOW
        else:
            return FeasibilityLevel.NOT_RECOMMENDED

    def _generate_recommendations(
        self,
        level: FeasibilityLevel,
        resources: ResourceEstimate,
        risks: List[str]
    ) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []

        if level == FeasibilityLevel.NOT_RECOMMENDED:
            recommendations.append("Consider simplifying the experiment scope")
            recommendations.append("Start with a smaller-scale pilot experiment")
        elif level == FeasibilityLevel.LOW:
            recommendations.append("Implement MVP version first")
            recommendations.append("Secure sufficient computational resources before starting")
        elif level == FeasibilityLevel.MEDIUM:
            recommendations.append("Plan for iterative development with checkpoints")
        else:
            recommendations.append("Experiment is feasible - proceed with standard workflow")

        # Resource-specific recommendations
        if resources.gpu_hours > self.GPU_THRESHOLD_LOW:
            recommendations.append("Consider using cloud GPU services for cost efficiency")

        if resources.dataset_size == 'large':
            recommendations.append("Implement data streaming to handle large datasets")

        # Risk-specific recommendations
        if any('stochastic' in r for r in risks):
            recommendations.append("Set fixed random seeds and plan for multiple runs")

        if any('human evaluation' in r for r in risks):
            recommendations.append("Prepare IRB approval if needed for human subjects")

        return recommendations

    def quick_check(self, experiment_description: str) -> Tuple[FeasibilityLevel, str]:
        """Quick feasibility check with summary."""
        report = self.check_feasibility(experiment_description)

        summary = f"Feasibility: {report.overall_level.value.upper()} "
        summary += f"(Score: {report.feasibility_score:.0f}/100)\n"
        summary += f"Estimated time: {report.time_estimate_hours:.1f} hours\n"
        summary += f"GPU hours needed: {report.resource_estimate.gpu_hours:.1f}\n"
        summary += f"Risk factors: {len(report.risk_factors)}\n"

        if report.risk_factors:
            summary += "Top risk: " + report.risk_factors[0]

        return report.overall_level, summary


def check_experiment_feasibility(
    experiment_description: str,
    method_name: str = "",
    dataset_info: Optional[Dict] = None,
    compute_budget: Optional[Dict] = None
) -> FeasibilityReport:
    """Convenience function for feasibility check."""
    checker = ExperimentFeasibilityChecker()
    return checker.check_feasibility(
        experiment_description,
        method_name,
        dataset_info,
        compute_budget
    )


if __name__ == "__main__":
    # Test feasibility checker
    checker = ExperimentFeasibilityChecker()

    # Test case 1: Simple experiment
    test1 = "Fine-tune BERT on IMDB sentiment classification dataset"
    level, summary = checker.quick_check(test1)
    print(f"Test 1:\n{summary}\n")

    # Test case 2: Complex experiment
    test2 = "Train a novel large-scale distributed architecture on ImageNet-21K with extensive hyperparameter grid search"
    report = checker.check_feasibility(test2, method_name="Novel-ViT-Large")
    print(f"Test 2: {report.overall_level.value}")
    print(f"Risks: {report.risk_factors}")
    print(f"Recommendations: {report.recommendations}")

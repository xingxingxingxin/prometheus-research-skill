"""
MVP Experiment Strategy

Implements Minimum Viable Experiment strategy for iterative development.
Defines tiered experiment levels from quick validation to full evaluation.
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import math


class MVPTier(Enum):
    """MVP experiment tiers."""
    TIER_0_SANITY = "tier_0_sanity"           # Quick sanity check
    TIER_1_MINIMAL = "tier_1_minimal"         # Minimal viable experiment
    TIER_2_STANDARD = "tier_2_standard"       # Standard experiment
    TIER_3_FULL = "tier_3_full"               # Full experiment
    TIER_4_COMPREHENSIVE = "tier_4_comprehensive"  # Comprehensive evaluation


@dataclass
class TierConfig:
    """Configuration for an MVP tier."""
    name: str
    description: str
    data_fraction: float
    num_epochs: int
    num_runs: int
    estimated_time_hours: float
    required_for_paper: bool
    checkpoint_after: bool
    success_criteria: Dict[str, float] = field(default_factory=dict)


@dataclass
class MVPPlan:
    """Complete MVP experiment plan."""
    experiment_name: str
    current_tier: MVPTier
    recommended_tiers: List[MVPTier]
    tier_configs: Dict[MVPTier, TierConfig]
    total_estimated_time: float
    checkpoints: List[str]
    decision_points: List[str]


# Default configurations for each tier
DEFAULT_TIER_CONFIGS = {
    MVPTier.TIER_0_SANITY: TierConfig(
        name="Sanity Check",
        description="Quick validation that code runs and model learns",
        data_fraction=0.01,
        num_epochs=1,
        num_runs=1,
        estimated_time_hours=0.1,
        required_for_paper=False,
        checkpoint_after=False,
        success_criteria={"min_improvement": 0.01}
    ),
    MVPTier.TIER_1_MINIMAL: TierConfig(
        name="Minimal Viable",
        description="Basic experiment with small data subset",
        data_fraction=0.1,
        num_epochs=3,
        num_runs=1,
        estimated_time_hours=0.5,
        required_for_paper=False,
        checkpoint_after=True,
        success_criteria={"min_accuracy": 0.5, "min_improvement": 0.02}
    ),
    MVPTier.TIER_2_STANDARD: TierConfig(
        name="Standard",
        description="Standard experiment with reasonable data size",
        data_fraction=0.5,
        num_epochs=10,
        num_runs=2,
        estimated_time_hours=2.0,
        required_for_paper=True,
        checkpoint_after=True,
        success_criteria={"min_accuracy": 0.6, "min_improvement": 0.03}
    ),
    MVPTier.TIER_3_FULL: TierConfig(
        name="Full",
        description="Full-scale experiment with complete data",
        data_fraction=1.0,
        num_epochs=20,
        num_runs=3,
        estimated_time_hours=8.0,
        required_for_paper=True,
        checkpoint_after=True,
        success_criteria={"min_accuracy": 0.7, "min_improvement": 0.05}
    ),
    MVPTier.TIER_4_COMPREHENSIVE: TierConfig(
        name="Comprehensive",
        description="Comprehensive evaluation with ablation and sensitivity",
        data_fraction=1.0,
        num_epochs=30,
        num_runs=5,
        estimated_time_hours=24.0,
        required_for_paper=True,
        checkpoint_after=True,
        success_criteria={"min_accuracy": 0.75, "min_improvement": 0.05, "statistical_significance": 0.95}
    )
}


class MVPExperimentStrategy:
    """
    Manage MVP (Minimum Viable Experiment) strategy.

    Provides a tiered approach to experiments:
    - Start with quick sanity checks
    - Progress to minimal experiments
    - Scale up based on results
    - Full evaluation only if needed
    """

    def __init__(self, custom_configs: Optional[Dict[MVPTier, TierConfig]] = None):
        """
        Initialize MVP strategy.

        Args:
            custom_configs: Custom tier configurations (merge with defaults)
        """
        self.tier_configs = DEFAULT_TIER_CONFIGS.copy()
        if custom_configs:
            self.tier_configs.update(custom_configs)

        self.completed_tiers: List[MVPTier] = []
        self.tier_results: Dict[MVPTier, Dict[str, Any]] = {}

    def create_plan(
        self,
        experiment_name: str,
        target_metric: str = "accuracy",
        baseline_value: float = 0.5,
        target_value: float = 0.7,
        time_budget_hours: float = 10.0,
        paper_submission: bool = False
    ) -> MVPPlan:
        """
        Create an MVP experiment plan.

        Args:
            experiment_name: Name of the experiment
            target_metric: Primary metric to optimize
            baseline_value: Baseline metric value
            target_value: Target metric value
            time_budget_hours: Available time in hours
            paper_submission: Whether this is for paper submission

        Returns:
            MVPPlan with recommended tier progression
        """
        # Determine which tiers to include based on time budget
        recommended_tiers = []
        total_time = 0.0

        for tier in MVPTier:
            config = self.tier_configs[tier]
            tier_time = config.estimated_time_hours

            # Always include sanity and minimal
            if tier in [MVPTier.TIER_0_SANITY, MVPTier.TIER_1_MINIMAL]:
                recommended_tiers.append(tier)
                total_time += tier_time
                continue

            # Include if time permits or required for paper
            if paper_submission and config.required_for_paper:
                if total_time + tier_time <= time_budget_hours * 1.5:  # Allow some overrun
                    recommended_tiers.append(tier)
                    total_time += tier_time
            elif total_time + tier_time <= time_budget_hours:
                recommended_tiers.append(tier)
                total_time += tier_time

        # Generate checkpoints
        checkpoints = []
        for tier in recommended_tiers:
            config = self.tier_configs[tier]
            if config.checkpoint_after:
                checkpoints.append(f"Complete {config.name}: Validate {target_metric} improvement")

        # Generate decision points
        decision_points = [
            "After Tier 0: If training doesn't converge, debug code",
            "After Tier 1: If no improvement over baseline, reconsider approach",
            "After Tier 2: If significant improvement, proceed to full scale",
            "After Tier 3: If close to target, consider comprehensive evaluation",
        ]

        # Determine current tier (first incomplete)
        current_tier = recommended_tiers[0] if recommended_tiers else MVPTier.TIER_0_SANITY

        return MVPPlan(
            experiment_name=experiment_name,
            current_tier=current_tier,
            recommended_tiers=recommended_tiers,
            tier_configs=self.tier_configs,
            total_estimated_time=total_time,
            checkpoints=checkpoints,
            decision_points=decision_points
        )

    def get_tier_config(self, tier: MVPTier) -> TierConfig:
        """Get configuration for a specific tier."""
        return self.tier_configs[tier]

    def record_tier_result(
        self,
        tier: MVPTier,
        results: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Record results for a completed tier.

        Args:
            tier: The completed tier
            results: Results dictionary with metrics

        Returns:
            Tuple of (success, message)
        """
        config = self.tier_configs[tier]
        self.tier_results[tier] = results
        self.completed_tiers.append(tier)

        # Check success criteria
        success = True
        messages = []

        for criterion, threshold in config.success_criteria.items():
            if criterion.startswith("min_"):
                metric = criterion.replace("min_", "")
                if metric in results:
                    if results[metric] < threshold:
                        success = False
                        messages.append(
                            f"{metric} ({results[metric]:.4f}) below minimum ({threshold:.4f})"
                        )
            elif criterion == "statistical_significance":
                if "p_value" in results:
                    if results["p_value"] > (1 - threshold):
                        success = False
                        messages.append(
                            f"Results not statistically significant (p={results['p_value']:.4f})"
                        )

        if success:
            message = f"Tier {tier.value} passed all criteria"
        else:
            message = f"Tier {tier.value} issues: {'; '.join(messages)}"

        return success, message

    def should_advance(self, current_tier: MVPTier) -> Tuple[bool, str]:
        """
        Determine if should advance to next tier.

        Args:
            current_tier: Current tier level

        Returns:
            Tuple of (should_advance, reason)
        """
        if current_tier not in self.tier_results:
            return False, "Current tier not yet completed"

        results = self.tier_results[current_tier]
        config = self.tier_configs[current_tier]

        # Check all success criteria
        for criterion, threshold in config.success_criteria.items():
            if criterion.startswith("min_"):
                metric = criterion.replace("min_", "")
                if metric in results and results[metric] < threshold:
                    return False, f"Did not meet {criterion}: {results[metric]:.4f} < {threshold:.4f}"

        # Check for signs of overfitting (if we have train metrics)
        if "train_accuracy" in results and "val_accuracy" in results:
            gap = results["train_accuracy"] - results["val_accuracy"]
            if gap > 0.2:
                return False, f"Large train-val gap ({gap:.2f}) suggests overfitting - address before advancing"

        return True, "All criteria met, ready to advance"

    def get_next_tier(self, current_tier: MVPTier) -> Optional[MVPTier]:
        """Get the next tier after current."""
        tiers = list(MVPTier)
        try:
            idx = tiers.index(current_tier)
            if idx < len(tiers) - 1:
                return tiers[idx + 1]
        except ValueError:
            pass
        return None

    def estimate_remaining_time(self) -> float:
        """Estimate remaining time based on incomplete tiers."""
        remaining = 0.0
        for tier in MVPTier:
            if tier not in self.completed_tiers:
                remaining += self.tier_configs[tier].estimated_time_hours
        return remaining

    def generate_experiment_script(
        self,
        tier: MVPTier,
        data_path: str,
        output_dir: str
    ) -> str:
        """
        Generate experiment script for a specific tier.

        Args:
            tier: Target tier
            data_path: Path to dataset
            output_dir: Output directory

        Returns:
            Python script content
        """
        config = self.tier_configs[tier]

        script = f'''"""
MVP Experiment: {config.name}
Tier: {tier.value}
Auto-generated by MVPExperimentStrategy
"""

import torch
import json
from pathlib import Path

# MVP Configuration
DATA_FRACTION = {config.data_fraction}
NUM_EPOCHS = {config.num_epochs}
NUM_RUNS = {config.num_runs}
OUTPUT_DIR = "{output_dir}"
DATA_PATH = "{data_path}"

# Success criteria
SUCCESS_CRITERIA = {config.success_criteria}

def load_data(data_path, fraction=1.0):
    """Load dataset with optional subsampling."""
    # TODO: Implement data loading
    # Use fraction parameter to subsample
    pass

def create_model():
    """Create the model."""
    # TODO: Implement model creation
    pass

def train_epoch(model, dataloader, optimizer):
    """Train for one epoch."""
    # TODO: Implement training loop
    pass

def evaluate(model, dataloader):
    """Evaluate model."""
    # TODO: Implement evaluation
    pass

def run_experiment():
    """Run the MVP experiment."""
    print(f"Starting MVP Tier: {config.name}")
    print(f"Data fraction: {{DATA_FRACTION}}")
    print(f"Epochs: {{NUM_EPOCHS}}")
    print(f"Runs: {{NUM_RUNS}}")

    results = {{
        "tier": "{tier.value}",
        "config": {{
            "data_fraction": DATA_FRACTION,
            "num_epochs": NUM_EPOCHS,
            "num_runs": NUM_RUNS
        }},
        "runs": []
    }}

    for run in range(NUM_RUNS):
        print(f"\\nRun {{run + 1}}/{{NUM_RUNS}}")

        # Load data
        train_data, val_data = load_data(DATA_PATH, DATA_FRACTION)

        # Create model
        model = create_model()
        optimizer = torch.optim.Adam(model.parameters())

        # Train
        for epoch in range(NUM_EPOCHS):
            train_loss = train_epoch(model, train_data, optimizer)
            val_metrics = evaluate(model, val_data)
            print(f"  Epoch {{epoch + 1}}: loss={{train_loss:.4f}}, val={{val_metrics}}")

        # Final evaluation
        final_metrics = evaluate(model, val_data)
        results["runs"].append(final_metrics)

    # Aggregate results
    results["mean_accuracy"] = sum(r.get("accuracy", 0) for r in results["runs"]) / NUM_RUNS
    results["std_accuracy"] = 0  # Calculate std if NUM_RUNS > 1

    # Save results
    output_path = Path(OUTPUT_DIR) / "results_{tier.value}.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\\nResults saved to {{output_path}}")
    print(f"Mean accuracy: {{results['mean_accuracy']:.4f}}")

    # Check success criteria
    success = True
    for criterion, threshold in SUCCESS_CRITERIA.items():
        if criterion.startswith("min_"):
            metric = criterion.replace("min_", "")
            if metric in results:
                if results[metric] < threshold:
                    success = False
                    print(f"FAILED: {{metric}} ({{results[metric]:.4f}}) < {{threshold}}")

    if success:
        print("\\nAll success criteria met!")
        return True
    else:
        print("\\nSome criteria not met. Review before advancing.")
        return False

if __name__ == "__main__":
    success = run_experiment()
    exit(0 if success else 1)
'''
        return script


def get_mvp_strategy(
    experiment_name: str,
    time_budget_hours: float = 10.0,
    paper_submission: bool = False
) -> MVPPlan:
    """Convenience function to get MVP plan."""
    strategy = MVPExperimentStrategy()
    return strategy.create_plan(
        experiment_name=experiment_name,
        time_budget_hours=time_budget_hours,
        paper_submission=paper_submission
    )


if __name__ == "__main__":
    # Test MVP strategy
    strategy = MVPExperimentStrategy()

    # Create a plan
    plan = strategy.create_plan(
        experiment_name="novel_classifier",
        target_metric="accuracy",
        baseline_value=0.70,
        target_value=0.85,
        time_budget_hours=8.0,
        paper_submission=True
    )

    print("MVP Experiment Plan")
    print("=" * 50)
    print(f"Experiment: {plan.experiment_name}")
    print(f"Recommended tiers: {[t.value for t in plan.recommended_tiers]}")
    print(f"Total estimated time: {plan.total_estimated_time:.1f} hours")
    print("\nCheckpoints:")
    for cp in plan.checkpoints:
        print(f"  - {cp}")
    print("\nDecision points:")
    for dp in plan.decision_points:
        print(f"  - {dp}")

    # Simulate completing Tier 0
    print("\n" + "=" * 50)
    print("Simulating Tier 0 completion...")
    success, msg = strategy.record_tier_result(
        MVPTier.TIER_0_SANITY,
        {"accuracy": 0.55, "loss": 0.8, "train_accuracy": 0.60}
    )
    print(f"Result: {msg}")

    should_advance, reason = strategy.should_advance(MVPTier.TIER_0_SANITY)
    print(f"Should advance: {should_advance} - {reason}")

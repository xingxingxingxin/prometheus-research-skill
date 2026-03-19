"""
Environment Snapshot

Capture and manage environment snapshots for reproducibility.
Records Python packages, system info, random seeds, and configurations.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import json
import os
import sys
import platform
import hashlib
import subprocess


@dataclass
class PackageInfo:
    """Information about an installed package."""
    name: str
    version: str
    location: Optional[str] = None


@dataclass
class GPUInfo:
    """Information about GPU hardware."""
    name: str
    memory_total: str
    driver_version: Optional[str] = None
    cuda_version: Optional[str] = None


@dataclass
class SnapshotReport:
    """Complete environment snapshot report."""
    snapshot_id: str
    timestamp: str
    python_version: str
    platform_info: Dict[str, str]
    packages: List[PackageInfo]
    gpu_info: List[GPUInfo]
    env_variables: Dict[str, str]
    random_seeds: Dict[str, int]
    custom_config: Dict[str, Any]
    requirements_txt: str
    reproducibility_score: float  # 0-100


class EnvironmentSnapshot:
    """
    Capture and manage environment snapshots for experiment reproducibility.

    Captures:
    - Python version and packages
    - System information
    - GPU information
    - Environment variables
    - Random seeds
    - Custom configurations
    """

    # Important packages to always track
    IMPORTANT_PACKAGES = [
        'torch', 'tensorflow', 'numpy', 'pandas', 'scikit-learn',
        'transformers', 'datasets', 'accelerate', 'wandb',
        'cuda-python', 'cupy', 'jax'
    ]

    # Environment variables that affect ML experiments
    RELEVANT_ENV_VARS = [
        'CUDA_VISIBLE_DEVICES',
        'CUDA_HOME',
        'PYTHONPATH',
        'PYTHONHASHSEED',
        'OMP_NUM_THREADS',
        'MKL_NUM_THREADS',
        'TF_FORCE_GPU_ALLOW_GROWTH',
        'XLA_FLAGS'
    ]

    def __init__(self, output_dir: str = "./snapshots"):
        """
        Initialize environment snapshot manager.

        Args:
            output_dir: Directory to save snapshots
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def capture(
        self,
        random_seeds: Optional[Dict[str, int]] = None,
        custom_config: Optional[Dict[str, Any]] = None,
        capture_pip_freeze: bool = True
    ) -> SnapshotReport:
        """
        Capture current environment snapshot.

        Args:
            random_seeds: Dictionary of random seeds used
            custom_config: Custom configuration to include
            capture_pip_freeze: Whether to capture full pip freeze

        Returns:
            SnapshotReport with complete environment information
        """
        timestamp = datetime.now().isoformat()

        # Generate snapshot ID
        snapshot_id = self._generate_snapshot_id(timestamp)

        # Capture Python version
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

        # Capture platform info
        platform_info = {
            'system': platform.system(),
            'node': platform.node(),
            'release': platform.release(),
            'version': platform.version(),
            'machine': platform.machine(),
            'processor': platform.processor()
        }

        # Capture packages
        packages = self._capture_packages(capture_pip_freeze)

        # Capture GPU info
        gpu_info = self._capture_gpu_info()

        # Capture relevant environment variables
        env_variables = {}
        for var in self.RELEVANT_ENV_VARS:
            value = os.environ.get(var, "")
            if value:
                env_variables[var] = value

        # Use provided seeds or defaults
        if random_seeds is None:
            random_seeds = {}

        # Use provided config or empty dict
        if custom_config is None:
            custom_config = {}

        # Generate requirements.txt content
        requirements_txt = self._generate_requirements(packages)

        # Calculate reproducibility score
        reproducibility_score = self._calculate_reproducibility_score(
            random_seeds, packages, gpu_info
        )

        return SnapshotReport(
            snapshot_id=snapshot_id,
            timestamp=timestamp,
            python_version=python_version,
            platform_info=platform_info,
            packages=packages,
            gpu_info=gpu_info,
            env_variables=env_variables,
            random_seeds=random_seeds,
            custom_config=custom_config,
            requirements_txt=requirements_txt,
            reproducibility_score=reproducibility_score
        )

    def save(
        self,
        snapshot: SnapshotReport,
        filename: Optional[str] = None
    ) -> str:
        """
        Save snapshot to file.

        Args:
            snapshot: SnapshotReport to save
            filename: Optional custom filename

        Returns:
            Path to saved file
        """
        if filename is None:
            filename = f"snapshot_{snapshot.snapshot_id}.json"

        filepath = os.path.join(self.output_dir, filename)

        # Convert to dictionary for JSON serialization
        data = {
            'snapshot_id': snapshot.snapshot_id,
            'timestamp': snapshot.timestamp,
            'python_version': snapshot.python_version,
            'platform_info': snapshot.platform_info,
            'packages': [
                {'name': p.name, 'version': p.version, 'location': p.location}
                for p in snapshot.packages
            ],
            'gpu_info': [
                {
                    'name': g.name,
                    'memory_total': g.memory_total,
                    'driver_version': g.driver_version,
                    'cuda_version': g.cuda_version
                }
                for g in snapshot.gpu_info
            ],
            'env_variables': snapshot.env_variables,
            'random_seeds': snapshot.random_seeds,
            'custom_config': snapshot.custom_config,
            'requirements_txt': snapshot.requirements_txt,
            'reproducibility_score': snapshot.reproducibility_score
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        # Also save requirements.txt separately
        req_path = os.path.join(self.output_dir, f"requirements_{snapshot.snapshot_id}.txt")
        with open(req_path, 'w', encoding='utf-8') as f:
            f.write(snapshot.requirements_txt)

        return filepath

    def load(self, filepath: str) -> SnapshotReport:
        """
        Load snapshot from file.

        Args:
            filepath: Path to snapshot file

        Returns:
            SnapshotReport loaded from file
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return SnapshotReport(
            snapshot_id=data['snapshot_id'],
            timestamp=data['timestamp'],
            python_version=data['python_version'],
            platform_info=data['platform_info'],
            packages=[
                PackageInfo(
                    name=p['name'],
                    version=p['version'],
                    location=p.get('location')
                )
                for p in data['packages']
            ],
            gpu_info=[
                GPUInfo(
                    name=g['name'],
                    memory_total=g['memory_total'],
                    driver_version=g.get('driver_version'),
                    cuda_version=g.get('cuda_version')
                )
                for g in data['gpu_info']
            ],
            env_variables=data['env_variables'],
            random_seeds=data['random_seeds'],
            custom_config=data['custom_config'],
            requirements_txt=data['requirements_txt'],
            reproducibility_score=data['reproducibility_score']
        )

    def compare(
        self,
        snapshot1: SnapshotReport,
        snapshot2: SnapshotReport
    ) -> Dict[str, Any]:
        """
        Compare two snapshots for compatibility.

        Args:
            snapshot1: First snapshot
            snapshot2: Second snapshot

        Returns:
            Dictionary with comparison results
        """
        differences = {
            'compatible': True,
            'python_version_match': snapshot1.python_version == snapshot2.python_version,
            'platform_match': snapshot1.platform_info['system'] == snapshot2.platform_info['system'],
            'package_differences': [],
            'gpu_differences': [],
            'warnings': []
        }

        # Check Python version
        if not differences['python_version_match']:
            differences['warnings'].append(
                f"Python version differs: {snapshot1.python_version} vs {snapshot2.python_version}"
            )

        # Check packages
        packages1 = {p.name: p.version for p in snapshot1.packages}
        packages2 = {p.name: p.version for p in snapshot2.packages}

        for name in set(list(packages1.keys()) + list(packages2.keys())):
            v1 = packages1.get(name, "not installed")
            v2 = packages2.get(name, "not installed")

            if v1 != v2:
                differences['package_differences'].append({
                    'name': name,
                    'version1': v1,
                    'version2': v2
                })

                # Flag important packages
                if name.lower() in [p.lower() for p in self.IMPORTANT_PACKAGES]:
                    differences['warnings'].append(
                        f"Important package {name} differs: {v1} vs {v2}"
                    )

        # Check GPU
        if len(snapshot1.gpu_info) != len(snapshot2.gpu_info):
            differences['gpu_differences'].append(
                f"Different number of GPUs: {len(snapshot1.gpu_info)} vs {len(snapshot2.gpu_info)}"
            )

        # Determine overall compatibility
        if differences['package_differences']:
            differences['compatible'] = False

        return differences

    def _generate_snapshot_id(self, timestamp: str) -> str:
        """Generate unique snapshot ID."""
        hash_input = timestamp + str(os.getpid())
        return hashlib.md5(hash_input.encode()).hexdigest()[:8]

    def _capture_packages(self, capture_full: bool) -> List[PackageInfo]:
        """Capture installed packages."""
        packages = []

        try:
            # Use pip list to get packages
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'list', '--format=json'],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                pip_packages = json.loads(result.stdout)
                for pkg in pip_packages:
                    packages.append(PackageInfo(
                        name=pkg['name'],
                        version=pkg['version'],
                        location=pkg.get('location')
                    ))
        except Exception:
            # Fallback: try to import key packages
            for pkg_name in self.IMPORTANT_PACKAGES:
                try:
                    module = __import__(pkg_name.replace('-', '_'))
                    version = getattr(module, '__version__', 'unknown')
                    packages.append(PackageInfo(name=pkg_name, version=version))
                except ImportError:
                    pass

        return packages

    def _capture_gpu_info(self) -> List[GPUInfo]:
        """Capture GPU information."""
        gpus = []

        try:
            # Try nvidia-smi first
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=name,memory.total,driver_version', '--format=csv,noheader'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line:
                        parts = [p.strip() for p in line.split(',')]
                        gpus.append(GPUInfo(
                            name=parts[0] if len(parts) > 0 else "Unknown",
                            memory_total=parts[1] if len(parts) > 1 else "Unknown",
                            driver_version=parts[2] if len(parts) > 2 else None,
                            cuda_version=None
                        ))
        except Exception:
            pass

        # Try PyTorch for additional GPU info
        try:
            import torch
            if torch.cuda.is_available():
                for i in range(torch.cuda.device_count()):
                    props = torch.cuda.get_device_properties(i)
                    # Update or add GPU info
                    if i < len(gpus):
                        gpus[i].cuda_version = torch.version.cuda
                    else:
                        gpus.append(GPUInfo(
                            name=props.name,
                            memory_total=f"{props.total_memory // (1024**3)} GB",
                            cuda_version=torch.version.cuda
                        ))
        except ImportError:
            pass

        return gpus

    def _generate_requirements(self, packages: List[PackageInfo]) -> str:
        """Generate requirements.txt content."""
        lines = []
        for pkg in sorted(packages, key=lambda p: p.name.lower()):
            lines.append(f"{pkg.name}=={pkg.version}")
        return '\n'.join(lines)

    def _calculate_reproducibility_score(
        self,
        random_seeds: Dict[str, int],
        packages: List[PackageInfo],
        gpu_info: List[GPUInfo]
    ) -> float:
        """Calculate reproducibility score (0-100)."""
        score = 100.0

        # Deduct if no random seeds provided
        if not random_seeds:
            score -= 30
        else:
            # Check for common seeds
            required_seeds = ['python', 'numpy', 'torch', 'random']
            missing_seeds = [s for s in required_seeds if s not in random_seeds]
            score -= len(missing_seeds) * 5

        # Deduct if packages not pinned
        unpinned = sum(1 for p in packages if p.version == 'unknown')
        if unpinned > 0:
            score -= min(unpinned * 2, 20)

        # Deduct for GPU variability
        if len(gpu_info) > 1:
            score -= 5  # Multi-GPU adds variability

        return max(score, 0)

    def generate_setup_script(
        self,
        snapshot: SnapshotReport,
        output_path: Optional[str] = None
    ) -> str:
        """
        Generate setup script to reproduce environment.

        Args:
            snapshot: SnapshotReport to use
            output_path: Optional path to save script

        Returns:
            Setup script content
        """
        script = f'''#!/bin/bash
# Environment Setup Script
# Generated from snapshot: {snapshot.snapshot_id}
# Timestamp: {snapshot.timestamp}

# Python version: {snapshot.python_version}
# Platform: {snapshot.platform_info['system']} {snapshot.platform_info['release']}

# Create virtual environment
python{snapshot.python_version.split('.')[0]}.{snapshot.python_version.split('.')[1]} -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements_{snapshot.snapshot_id}.txt

# Set environment variables
'''

        for var, value in snapshot.env_variables.items():
            script += f'export {var}="{value}"\n'

        if snapshot.random_seeds:
            script += "\n# Set random seeds\n"
            script += "export PYTHONHASHSEED=0\n"

        script += "\necho 'Environment setup complete!'\n"

        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(script)

        return script


def capture_environment(
    random_seeds: Optional[Dict[str, int]] = None,
    custom_config: Optional[Dict[str, Any]] = None,
    output_dir: str = "./snapshots"
) -> SnapshotReport:
    """Convenience function to capture environment snapshot."""
    snapshotter = EnvironmentSnapshot(output_dir)
    return snapshotter.capture(random_seeds, custom_config)


if __name__ == "__main__":
    # Test environment snapshot
    snapshotter = EnvironmentSnapshot("./test_snapshots")

    # Capture snapshot
    snapshot = snapshotter.capture(
        random_seeds={
            'python': 42,
            'numpy': 42,
            'torch': 42,
            'random': 42
        },
        custom_config={
            'model': 'resnet50',
            'dataset': 'cifar10',
            'batch_size': 128
        }
    )

    print(f"Snapshot ID: {snapshot.snapshot_id}")
    print(f"Timestamp: {snapshot.timestamp}")
    print(f"Python: {snapshot.python_version}")
    print(f"Platform: {snapshot.platform_info['system']}")
    print(f"Packages: {len(snapshot.packages)}")
    print(f"GPUs: {len(snapshot.gpu_info)}")
    print(f"Reproducibility score: {snapshot.reproducibility_score:.1f}/100")

    # Save snapshot
    filepath = snapshotter.save(snapshot)
    print(f"\nSaved to: {filepath}")

    # Generate setup script
    script = snapshotter.generate_setup_script(snapshot)
    print(f"\nGenerated setup script ({len(script)} chars)")

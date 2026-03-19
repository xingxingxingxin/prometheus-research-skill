#!/usr/bin/env python3
"""
Project Prometheus - 配置加载器
==============================

加载和管理执行配置。
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class RalphConfig:
    """Ralph Loop 配置"""
    enabled: bool = True
    max_iterations: int = 20
    completion_promise: str = "TASK_COMPLETE"
    iteration_timeout: int = 300
    backoff_strategy: str = "exponential"
    backoff_base: float = 2.0
    max_backoff: float = 60.0
    on_max_iterations: str = "checkpoint"
    phases_enabled: Dict[str, bool] = field(default_factory=lambda: {
        'coding': True, 'execution': True, 'analysis': True, 'implementation': True
    })


@dataclass
class GEPConfig:
    """GEP 配置"""
    enabled: bool = True
    gene_weight: float = 0.5
    capsule_weight: float = 0.3
    history_weight: float = 0.2
    min_confidence: float = 0.3
    auto_record_success: bool = True
    max_capsules: int = 1000
    capsule_expire_days: int = 90


@dataclass
class ExecutionConfig:
    """执行配置"""
    timeout: int = 600
    max_wait: int = 1800
    check_interval: int = 10
    max_retries: int = 3
    retry_delay: int = 60
    claude_path: str = "auto"
    permission_mode: str = "bypassPermissions"


@dataclass
class PrometheusConfig:
    """Prometheus 完整配置"""
    ralph: RalphConfig = field(default_factory=RalphConfig)
    gep: GEPConfig = field(default_factory=GEPConfig)
    execution: ExecutionConfig = field(default_factory=ExecutionConfig)


def load_config(config_path: Optional[Path] = None) -> PrometheusConfig:
    """
    加载配置文件

    Args:
        config_path: 配置文件路径，默认为 config/execution_config.yaml

    Returns:
        PrometheusConfig 实例
    """
    if config_path is None:
        config_path = Path(__file__).parent.parent / "config" / "execution_config.yaml"

    if not config_path.exists():
        return PrometheusConfig()

    try:
        import yaml
        with open(config_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}
    except ImportError:
        # 如果没有 yaml 模块，尝试使用 json
        json_path = config_path.with_suffix('.json')
        if json_path.exists():
            import json
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            return PrometheusConfig()
    except Exception:
        return PrometheusConfig()

    # 解析配置
    ralph_data = data.get('ralph', {})
    gep_data = data.get('gep', {})
    exec_data = data.get('execution', {})

    return PrometheusConfig(
        ralph=RalphConfig(
            enabled=ralph_data.get('enabled', True),
            max_iterations=ralph_data.get('max_iterations', 20),
            completion_promise=ralph_data.get('completion_promise', 'TASK_COMPLETE'),
            iteration_timeout=ralph_data.get('iteration_timeout', 300),
            backoff_strategy=ralph_data.get('backoff_strategy', 'exponential'),
            backoff_base=ralph_data.get('backoff_base', 2.0),
            max_backoff=ralph_data.get('max_backoff', 60.0),
            on_max_iterations=ralph_data.get('on_max_iterations', 'checkpoint'),
            phases_enabled=ralph_data.get('phases_enabled', {})
        ),
        gep=GEPConfig(
            enabled=gep_data.get('enabled', True),
            gene_weight=gep_data.get('gene_weight', 0.5),
            capsule_weight=gep_data.get('capsule_weight', 0.3),
            history_weight=gep_data.get('history_weight', 0.2),
            min_confidence=gep_data.get('min_confidence', 0.3),
            auto_record_success=gep_data.get('auto_record_success', True),
            max_capsules=gep_data.get('max_capsules', 1000),
            capsule_expire_days=gep_data.get('capsule_expire_days', 90)
        ),
        execution=ExecutionConfig(
            timeout=exec_data.get('timeout', 600),
            max_wait=exec_data.get('max_wait', 1800),
            check_interval=exec_data.get('check_interval', 10),
            max_retries=exec_data.get('max_retries', 3),
            retry_delay=exec_data.get('retry_delay', 60),
            claude_path=exec_data.get('claude_path', 'auto'),
            permission_mode=exec_data.get('permission_mode', 'bypassPermissions')
        )
    )


def should_use_ralph_for_phase(phase: str, config: Optional[PrometheusConfig] = None) -> bool:
    """
    检查是否应该为某个阶段启用 Ralph Loop

    Args:
        phase: 阶段名称
        config: 配置实例

    Returns:
        是否启用
    """
    if config is None:
        config = load_config()

    if not config.ralph.enabled:
        return False

    phase_lower = phase.lower().replace(' ', '_').replace('-', '_')

    for enabled_phase, is_enabled in config.ralph.phases_enabled.items():
        if is_enabled and enabled_phase.lower() in phase_lower:
            return True

    return False


# 全局配置实例
_config_instance: Optional[PrometheusConfig] = None


def get_config(reload: bool = False) -> PrometheusConfig:
    """获取全局配置实例"""
    global _config_instance
    if _config_instance is None or reload:
        _config_instance = load_config()
    return _config_instance


def reset_config():
    """重置配置"""
    global _config_instance
    _config_instance = None


if __name__ == "__main__":
    config = get_config()
    print(f"Ralph enabled: {config.ralph.enabled}")
    print(f"Ralph max iterations: {config.ralph.max_iterations}")
    print(f"GEP enabled: {config.gep.enabled}")
    print(f"Execution timeout: {config.execution.timeout}")

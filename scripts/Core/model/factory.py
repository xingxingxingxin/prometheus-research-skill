"""
Model Factory - 模型工厂

根据配置创建和配置模型后端
"""

from typing import Dict, Any, Optional
from pathlib import Path
import os
import yaml

from .base import ModelBackend, ModelConfig, ModelRouter, ModelCapability
from .claude_backend import ClaudeBackend, ClaudeOpusBackend, ClaudeSonnetBackend
from .openai_backend import OpenAIBackend, GPT4Backend, GPT4TurboBackend
from .local_backend import LocalBackend, OllamaBackend


# 全局路由器实例
_router: Optional[ModelRouter] = None


# 后端类注册表
BACKEND_REGISTRY: Dict[str, type] = {
    "claude": ClaudeBackend,
    "claude-opus": ClaudeOpusBackend,
    "claude-sonnet": ClaudeSonnetBackend,
    "openai": OpenAIBackend,
    "gpt-4": GPT4Backend,
    "gpt-4-turbo": GPT4TurboBackend,
    "local": LocalBackend,
    "ollama": OllamaBackend,
}


def create_backend(
    backend_type: str,
    config: Optional[ModelConfig] = None,
    **kwargs
) -> ModelBackend:
    """
    创建模型后端实例

    Args:
        backend_type: 后端类型 (claude, openai, local等)
        config: 模型配置
        **kwargs: 配置参数

    Returns:
        ModelBackend: 后端实例
    """
    backend_class = BACKEND_REGISTRY.get(backend_type)

    if backend_class is None:
        raise ValueError(f"Unknown backend type: {backend_type}")

    if config is None:
        config = ModelConfig(
            name=kwargs.get("name", backend_type),
            api_key=kwargs.get("api_key"),
            endpoint=kwargs.get("endpoint"),
            max_tokens=kwargs.get("max_tokens", 4096),
            temperature=kwargs.get("temperature", 0.7),
        )

    return backend_class(config)


def create_router_from_config(config: Dict[str, Any]) -> ModelRouter:
    """
    从配置字典创建路由器

    Args:
        config: 配置字典

    Returns:
        ModelRouter: 配置好的路由器
    """
    router = ModelRouter()

    backends_config = config.get("backends", {})
    routing_config = config.get("routing", {})

    for name, backend_cfg in backends_config.items():
        if not backend_cfg.get("enabled", True):
            continue

        backend_type = backend_cfg.get("type", name)

        model_config = ModelConfig(
            name=backend_cfg.get("model_name", name),
            api_key=backend_cfg.get("api_key"),
            endpoint=backend_cfg.get("endpoint"),
            max_tokens=backend_cfg.get("max_tokens", 4096),
            temperature=backend_cfg.get("temperature", 0.7),
            default_for=backend_cfg.get("default_for", []),
        )

        try:
            backend = create_backend(backend_type, model_config)
            is_default = (routing_config.get("default") == name)
            router.register_backend(name, backend, is_default)

            # 设置任务映射
            for task_type in backend_cfg.get("default_for", []):
                router.set_task_mapping(task_type, name)

        except Exception as e:
            print(f"Warning: Failed to create backend {name}: {e}")

    return router


def load_config_from_yaml(config_path: str) -> Dict[str, Any]:
    """
    从YAML文件加载配置

    Args:
        config_path: 配置文件路径

    Returns:
        Dict: 配置字典
    """
    path = Path(config_path)

    if not path.exists():
        return get_default_config()

    with open(path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    return config.get("model", get_default_config())


def get_default_config() -> Dict[str, Any]:
    """获取默认配置"""
    return {
        "backends": {
            "claude": {
                "type": "claude",
                "enabled": True,
                "model_name": "claude",
                "default_for": ["creative", "analysis", "writing"],
            },
        },
        "routing": {
            "default": "claude",
            "fallback": None,
        }
    }


def get_model_router(config_path: Optional[str] = None) -> ModelRouter:
    """
    获取全局模型路由器

    如果路由器不存在，则创建一个新的

    Args:
        config_path: 配置文件路径（可选）

    Returns:
        ModelRouter: 模型路由器
    """
    global _router

    if _router is not None:
        return _router

    # 尝试从配置文件加载
    if config_path is None:
        # 默认配置路径
        prometheus_root = Path(__file__).parent.parent.parent
        config_path = prometheus_root / "config.yaml"

    if Path(config_path).exists():
        config = load_config_from_yaml(str(config_path))
    else:
        config = get_default_config()

    _router = create_router_from_config(config)
    return _router


def reset_router():
    """重置全局路由器（用于测试）"""
    global _router
    _router = None


# 便捷函数
def generate(prompt: str, task_type: str = None, **kwargs) -> str:
    """
    便捷的生成函数

    Args:
        prompt: 输入提示
        task_type: 任务类型
        **kwargs: 额外参数

    Returns:
        str: 生成的内容
    """
    router = get_model_router()
    backend = router.get_backend(task_type)

    if backend is None:
        raise RuntimeError("No available model backend")

    response = backend.generate(prompt, **kwargs)
    return response.content

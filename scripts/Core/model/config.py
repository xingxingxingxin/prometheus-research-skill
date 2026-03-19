"""
Model Configuration - 模型配置管理

管理模型相关的配置和环境变量
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
import os


class ModelProvider(Enum):
    """模型提供商"""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    LOCAL = "local"
    CUSTOM = "custom"


@dataclass
class BackendConfig:
    """后端配置"""
    name: str
    provider: ModelProvider
    enabled: bool = True
    model_name: Optional[str] = None
    api_key: Optional[str] = None
    endpoint: Optional[str] = None
    max_tokens: int = 4096
    temperature: float = 0.7
    timeout: int = 600
    default_for: List[str] = field(default_factory=list)
    extra: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, name: str, data: Dict) -> "BackendConfig":
        """从字典创建配置"""
        provider_str = data.get("provider", data.get("type", name))
        try:
            provider = ModelProvider(provider_str.lower())
        except ValueError:
            provider = ModelProvider.CUSTOM

        return cls(
            name=name,
            provider=provider,
            enabled=data.get("enabled", True),
            model_name=data.get("model_name", data.get("model", name)),
            api_key=cls._get_api_key(data, provider),
            endpoint=data.get("endpoint"),
            max_tokens=data.get("max_tokens", 4096),
            temperature=data.get("temperature", 0.7),
            timeout=data.get("timeout", 600),
            default_for=data.get("default_for", []),
            extra=data.get("extra", {}),
        )

    @staticmethod
    def _get_api_key(data: Dict, provider: ModelProvider) -> Optional[str]:
        """获取API密钥"""
        # 直接配置的key
        if data.get("api_key"):
            return data["api_key"]

        # 环境变量
        env_var = data.get("api_key_env")
        if env_var:
            return os.environ.get(env_var)

        # 根据提供商猜测环境变量
        if provider == ModelProvider.ANTHROPIC:
            return os.environ.get("ANTHROPIC_API_KEY")
        elif provider == ModelProvider.OPENAI:
            return os.environ.get("OPENAI_API_KEY")

        return None


@dataclass
class RoutingConfig:
    """路由配置"""
    default: str = "claude"
    fallback: Optional[str] = None
    task_mapping: Dict[str, str] = field(default_factory=dict)
    deterministic_tasks: List[str] = field(default_factory=list)


@dataclass
class ModelLayerConfig:
    """模型层完整配置"""
    backends: Dict[str, BackendConfig] = field(default_factory=dict)
    routing: RoutingConfig = field(default_factory=RoutingConfig)

    @classmethod
    def from_dict(cls, data: Dict) -> "ModelLayerConfig":
        """从字典创建配置"""
        backends = {}
        for name, backend_data in data.get("backends", {}).items():
            backends[name] = BackendConfig.from_dict(name, backend_data)

        routing_data = data.get("routing", {})
        routing = RoutingConfig(
            default=routing_data.get("default", "claude"),
            fallback=routing_data.get("fallback"),
            task_mapping=routing_data.get("task_mapping", {}),
            deterministic_tasks=routing_data.get("deterministic_tasks", []),
        )

        return cls(backends=backends, routing=routing)

    def get_backend_config(self, name: str) -> Optional[BackendConfig]:
        """获取指定后端的配置"""
        return self.backends.get(name)

    def list_enabled_backends(self) -> List[str]:
        """列出所有启用的后端"""
        return [name for name, cfg in self.backends.items() if cfg.enabled]


def get_default_model_config() -> Dict[str, Any]:
    """
    获取默认模型配置

    可用于生成或更新 config.yaml
    """
    return {
        "model": {
            "backends": {
                "claude": {
                    "provider": "anthropic",
                    "enabled": True,
                    "model_name": "claude",
                    "default_for": ["creative", "analysis", "writing", "general"],
                },
                "claude-opus": {
                    "provider": "anthropic",
                    "enabled": False,
                    "model_name": "claude-opus",
                    "default_for": ["creative", "analysis"],
                },
                "openai": {
                    "provider": "openai",
                    "enabled": False,
                    "model_name": "gpt-4",
                    "api_key_env": "OPENAI_API_KEY",
                    "default_for": ["coding"],
                },
                "local": {
                    "provider": "local",
                    "enabled": False,
                    "model_name": "llama3",
                    "endpoint": "http://localhost:11434",
                    "default_for": ["formatting", "translation"],
                },
            },
            "routing": {
                "default": "claude",
                "fallback": "local",
                "task_mapping": {
                    "creative": "claude",
                    "analysis": "claude",
                    "writing": "claude",
                    "coding": "openai",
                    "formatting": "local",
                    "translation": "local",
                },
                "deterministic_tasks": [
                    "T005", "T006", "T007", "T008", "T009", "T010",
                    "T011", "T012", "T013", "T014",
                    "T015", "T016", "T017",
                    "T035", "T058", "T090", "T091"
                ]
            }
        }
    }

"""
Model Abstraction Layer - Base Classes

遵循"慢变量对抗快变量"原则：
- 模型是快变量（3-6个月迭代）
- 抽象层是慢变量（稳定接口）
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum


class ModelCapability(Enum):
    """模型能力枚举"""
    TEXT_GENERATION = "text_generation"
    CODE_GENERATION = "code_generation"
    ANALYSIS = "analysis"
    CREATIVE_WRITING = "creative_writing"
    TRANSLATION = "translation"


@dataclass
class ModelResponse:
    """模型响应封装"""
    content: str
    tokens_used: int = 0
    model_name: str = ""
    finish_reason: str = "complete"
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def success(self) -> bool:
        return self.finish_reason in ["complete", "stop"]


@dataclass
class ModelConfig:
    """模型配置"""
    name: str
    api_key: Optional[str] = None
    endpoint: Optional[str] = None
    max_tokens: int = 4096
    temperature: float = 0.7
    capabilities: List[ModelCapability] = field(default_factory=list)
    default_for: List[str] = field(default_factory=list)


class ModelBackend(ABC):
    """
    模型后端抽象基类

    实现此接口以支持新的模型后端
    """

    def __init__(self, config: ModelConfig):
        self.config = config
        self._available: Optional[bool] = None

    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> ModelResponse:
        """
        生成响应

        Args:
            prompt: 输入提示
            **kwargs: 额外参数 (temperature, max_tokens等)

        Returns:
            ModelResponse: 模型响应
        """
        pass

    @abstractmethod
    def generate_with_context(
        self,
        system_prompt: str,
        user_prompt: str,
        context: List[Dict[str, str]],
        **kwargs
    ) -> ModelResponse:
        """
        带上下文的生成

        Args:
            system_prompt: 系统提示
            user_prompt: 用户提示
            context: 对话上下文 [{"role": "user/assistant", "content": "..."}]
            **kwargs: 额外参数

        Returns:
            ModelResponse: 模型响应
        """
        pass

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """
        计算文本token数

        Args:
            text: 输入文本

        Returns:
            int: token数量
        """
        pass

    def is_available(self) -> bool:
        """
        检查后端是否可用

        Returns:
            bool: 是否可用
        """
        if self._available is not None:
            return self._available

        try:
            self._available = self._check_availability()
        except Exception:
            self._available = False

        return self._available

    def _check_availability(self) -> bool:
        """子类实现具体可用性检查"""
        return True

    @property
    def name(self) -> str:
        return self.config.name

    def get_capabilities(self) -> List[ModelCapability]:
        return self.config.capabilities

    def has_capability(self, capability: ModelCapability) -> bool:
        return capability in self.config.capabilities


class ModelRouter:
    """
    模型路由器

    根据任务类型路由到合适的模型后端
    """

    def __init__(self):
        self._backends: Dict[str, ModelBackend] = {}
        self._default_backend: Optional[str] = None
        self._task_mapping: Dict[str, str] = {}

    def register_backend(self, name: str, backend: ModelBackend, is_default: bool = False):
        """
        注册模型后端

        Args:
            name: 后端名称
            backend: 后端实例
            is_default: 是否为默认后端
        """
        self._backends[name] = backend
        if is_default or self._default_backend is None:
            self._default_backend = name

    def set_task_mapping(self, task_type: str, backend_name: str):
        """
        设置任务类型到后端的映射

        Args:
            task_type: 任务类型 (creative, analysis, coding等)
            backend_name: 后端名称
        """
        self._task_mapping[task_type] = backend_name

    def get_backend(self, task_type: str = None) -> Optional[ModelBackend]:
        """
        获取合适的后端

        Args:
            task_type: 任务类型

        Returns:
            ModelBackend: 后端实例，如果没有可用的则返回None
        """
        # 1. 尝试按任务类型获取
        if task_type and task_type in self._task_mapping:
            backend_name = self._task_mapping[task_type]
            backend = self._backends.get(backend_name)
            if backend and backend.is_available():
                return backend

        # 2. 使用默认后端
        if self._default_backend:
            backend = self._backends.get(self._default_backend)
            if backend and backend.is_available():
                return backend

        # 3. 遍历找第一个可用的
        for backend in self._backends.values():
            if backend.is_available():
                return backend

        return None

    def list_backends(self) -> List[str]:
        """列出所有注册的后端"""
        return list(self._backends.keys())

    def list_available_backends(self) -> List[str]:
        """列出所有可用的后端"""
        return [name for name, backend in self._backends.items()
                if backend.is_available()]

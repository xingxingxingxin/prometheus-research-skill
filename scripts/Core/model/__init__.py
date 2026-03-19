# Core/model - Model Abstraction Layer
# 热拔插模型接口，支持多后端切换

from .base import ModelBackend, ModelResponse, ModelRouter
from .factory import get_model_router, create_backend

__all__ = [
    'ModelBackend',
    'ModelResponse',
    'ModelRouter',
    'get_model_router',
    'create_backend'
]

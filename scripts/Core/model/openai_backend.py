"""
OpenAI Backend - OpenAI 模型后端

支持 GPT-4, GPT-4-turbo, GPT-3.5-turbo 等
"""

from typing import Dict, Any, List, Optional
import os

from .base import ModelBackend, ModelResponse, ModelConfig, ModelCapability


class OpenAIBackend(ModelBackend):
    """
    OpenAI 模型后端

    需要 openai 包: pip install openai
    """

    # 模型名称到API名称的映射
    MODEL_MAPPING = {
        "gpt-4": "gpt-4",
        "gpt-4-turbo": "gpt-4-turbo-preview",
        "gpt-4o": "gpt-4o",
        "gpt-3.5-turbo": "gpt-3.5-turbo",
        "o1": "o1",
        "o1-mini": "o1-mini",
    }

    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self._client = None

    def _check_availability(self) -> bool:
        """检查 OpenAI 是否可用"""
        api_key = self.config.api_key or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            return False

        try:
            import openai
            self._client = openai.OpenAI(api_key=api_key)
            return True
        except ImportError:
            return False

    def _get_api_model_name(self) -> str:
        """获取API使用的模型名称"""
        name = self.config.name.lower()
        return self.MODEL_MAPPING.get(name, name)

    def generate(self, prompt: str, **kwargs) -> ModelResponse:
        """
        使用 OpenAI API 生成响应
        """
        if not self.is_available():
            return ModelResponse(
                content="",
                finish_reason="error",
                metadata={"error": "OpenAI not available (check API key)"}
            )

        try:
            response = self._client.chat.completions.create(
                model=self._get_api_model_name(),
                messages=[{"role": "user", "content": prompt}],
                max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
                temperature=kwargs.get("temperature", self.config.temperature),
            )

            choice = response.choices[0]
            return ModelResponse(
                content=choice.message.content,
                tokens_used=response.usage.total_tokens if response.usage else 0,
                model_name=response.model,
                finish_reason=choice.finish_reason,
                metadata={
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                }
            )

        except Exception as e:
            return ModelResponse(
                content="",
                finish_reason="error",
                metadata={"error": str(e)}
            )

    def generate_with_context(
        self,
        system_prompt: str,
        user_prompt: str,
        context: List[Dict[str, str]],
        **kwargs
    ) -> ModelResponse:
        """带上下文的生成"""
        if not self.is_available():
            return ModelResponse(
                content="",
                finish_reason="error",
                metadata={"error": "OpenAI not available"}
            )

        messages = []

        # 添加系统提示
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        # 添加对话历史
        for msg in context:
            messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            })

        # 添加当前用户提示
        messages.append({"role": "user", "content": user_prompt})

        try:
            response = self._client.chat.completions.create(
                model=self._get_api_model_name(),
                messages=messages,
                max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
                temperature=kwargs.get("temperature", self.config.temperature),
            )

            choice = response.choices[0]
            return ModelResponse(
                content=choice.message.content,
                tokens_used=response.usage.total_tokens if response.usage else 0,
                model_name=response.model,
                finish_reason=choice.finish_reason,
                metadata={
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                }
            )

        except Exception as e:
            return ModelResponse(
                content="",
                finish_reason="error",
                metadata={"error": str(e)}
            )

    def count_tokens(self, text: str) -> int:
        """使用 tiktoken 计算token数"""
        try:
            import tiktoken
            encoding = tiktoken.encoding_for_model(self._get_api_model_name())
            return len(encoding.encode(text))
        except ImportError:
            # 降级到估算
            return len(text) // 4


class GPT4Backend(OpenAIBackend):
    """GPT-4 专用后端"""

    def __init__(self, config: ModelConfig = None):
        if config is None:
            config = ModelConfig(
                name="gpt-4",
                capabilities=[
                    ModelCapability.TEXT_GENERATION,
                    ModelCapability.ANALYSIS,
                    ModelCapability.CODE_GENERATION,
                ],
                default_for=["coding", "general"]
            )
        super().__init__(config)


class GPT4TurboBackend(OpenAIBackend):
    """GPT-4-turbo 专用后端"""

    def __init__(self, config: ModelConfig = None):
        if config is None:
            config = ModelConfig(
                name="gpt-4-turbo",
                capabilities=[
                    ModelCapability.TEXT_GENERATION,
                    ModelCapability.ANALYSIS,
                    ModelCapability.CODE_GENERATION,
                ],
                max_tokens=128000,  # 更大的上下文窗口
                default_for=["long_context"]
            )
        super().__init__(config)

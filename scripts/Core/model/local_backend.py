"""
Local Backend - 本地模型后端

支持 Ollama, LM Studio, vLLM 等本地推理服务
"""

from typing import Dict, Any, List, Optional
import os
import json
import urllib.request
import urllib.error

from .base import ModelBackend, ModelResponse, ModelConfig, ModelCapability


class LocalBackend(ModelBackend):
    """
    本地模型后端

    支持多种本地推理服务:
    - Ollama (默认)
    - LM Studio
    - vLLM
    - 其他 OpenAI 兼容 API
    """

    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self._endpoint = self._get_endpoint()
        self._backend_type = self._detect_backend_type()

    def _get_endpoint(self) -> str:
        """获取API端点"""
        if self.config.endpoint:
            return self.config.endpoint

        # 默认端点
        return os.environ.get(
            "LOCAL_LLM_ENDPOINT",
            "http://localhost:11434"  # Ollama 默认
        )

    def _detect_backend_type(self) -> str:
        """检测后端类型"""
        endpoint = self._endpoint.lower()

        if "11434" in endpoint or "ollama" in endpoint:
            return "ollama"
        elif "1234" in endpoint or "lmstudio" in endpoint:
            return "lmstudio"
        elif "8000" in endpoint or "vllm" in endpoint:
            return "vllm"
        else:
            return "openai_compatible"

    def _check_availability(self) -> bool:
        """检查本地服务是否可用"""
        try:
            if self._backend_type == "ollama":
                url = f"{self._endpoint}/api/tags"
            else:
                url = f"{self._endpoint}/v1/models"

            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=5) as response:
                return response.status == 200
        except Exception:
            return False

    def generate(self, prompt: str, **kwargs) -> ModelResponse:
        """使用本地模型生成响应"""
        if not self.is_available():
            return ModelResponse(
                content="",
                finish_reason="error",
                metadata={"error": f"Local backend not available at {self._endpoint}"}
            )

        if self._backend_type == "ollama":
            return self._generate_ollama(prompt, **kwargs)
        else:
            return self._generate_openai_compatible(prompt, **kwargs)

    def _generate_ollama(self, prompt: str, **kwargs) -> ModelResponse:
        """Ollama API 调用"""
        url = f"{self._endpoint}/api/generate"

        data = {
            "model": self.config.name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": kwargs.get("max_tokens", self.config.max_tokens),
                "temperature": kwargs.get("temperature", self.config.temperature),
            }
        }

        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )

            with urllib.request.urlopen(req, timeout=kwargs.get("timeout", 300)) as response:
                result = json.loads(response.read().decode("utf-8"))

                return ModelResponse(
                    content=result.get("response", ""),
                    tokens_used=result.get("eval_count", 0) + result.get("prompt_eval_count", 0),
                    model_name=self.config.name,
                    finish_reason="complete" if result.get("done") else "incomplete",
                    metadata={
                        "backend": "ollama",
                        "eval_count": result.get("eval_count", 0),
                        "prompt_eval_count": result.get("prompt_eval_count", 0),
                    }
                )

        except urllib.error.URLError as e:
            return ModelResponse(
                content="",
                finish_reason="error",
                metadata={"error": f"Connection error: {e}"}
            )
        except Exception as e:
            return ModelResponse(
                content="",
                finish_reason="error",
                metadata={"error": str(e)}
            )

    def _generate_openai_compatible(self, prompt: str, **kwargs) -> ModelResponse:
        """OpenAI 兼容 API 调用"""
        url = f"{self._endpoint}/v1/chat/completions"

        data = {
            "model": self.config.name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "temperature": kwargs.get("temperature", self.config.temperature),
        }

        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )

            with urllib.request.urlopen(req, timeout=kwargs.get("timeout", 300)) as response:
                result = json.loads(response.read().decode("utf-8"))

                choice = result.get("choices", [{}])[0]
                usage = result.get("usage", {})

                return ModelResponse(
                    content=choice.get("message", {}).get("content", ""),
                    tokens_used=usage.get("total_tokens", 0),
                    model_name=result.get("model", self.config.name),
                    finish_reason=choice.get("finish_reason", "complete"),
                    metadata={
                        "backend": self._backend_type,
                        "prompt_tokens": usage.get("prompt_tokens", 0),
                        "completion_tokens": usage.get("completion_tokens", 0),
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
        if self._backend_type == "ollama":
            # Ollama 风格
            full_prompt = ""
            if system_prompt:
                full_prompt += f"System: {system_prompt}\n\n"

            for msg in context:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                full_prompt += f"{role.capitalize()}: {content}\n\n"

            full_prompt += f"User: {user_prompt}\n\nAssistant:"
            return self._generate_ollama(full_prompt, **kwargs)
        else:
            # OpenAI 兼容风格
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})

            for msg in context:
                messages.append(msg)

            messages.append({"role": "user", "content": user_prompt})

            url = f"{self._endpoint}/v1/chat/completions"
            data = {
                "model": self.config.name,
                "messages": messages,
                "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                "temperature": kwargs.get("temperature", self.config.temperature),
            }

            try:
                req = urllib.request.Request(
                    url,
                    data=json.dumps(data).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST"
                )

                with urllib.request.urlopen(req, timeout=kwargs.get("timeout", 300)) as response:
                    result = json.loads(response.read().decode("utf-8"))
                    choice = result.get("choices", [{}])[0]
                    usage = result.get("usage", {})

                    return ModelResponse(
                        content=choice.get("message", {}).get("content", ""),
                        tokens_used=usage.get("total_tokens", 0),
                        model_name=result.get("model", self.config.name),
                        finish_reason=choice.get("finish_reason", "complete"),
                        metadata={"backend": self._backend_type}
                    )

            except Exception as e:
                return ModelResponse(
                    content="",
                    finish_reason="error",
                    metadata={"error": str(e)}
                )

    def count_tokens(self, text: str) -> int:
        """估算token数"""
        return len(text) // 4


class OllamaBackend(LocalBackend):
    """Ollama 专用后端"""

    def __init__(self, config: ModelConfig = None):
        if config is None:
            config = ModelConfig(
                name="llama3",
                endpoint="http://localhost:11434",
                capabilities=[
                    ModelCapability.TEXT_GENERATION,
                    ModelCapability.TRANSLATION,
                ],
                default_for=["formatting", "translation"]
            )
        super().__init__(config)

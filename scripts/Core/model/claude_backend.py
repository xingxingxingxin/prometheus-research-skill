"""
Claude Backend - Anthropic Claude 模型后端

通过 Claude CLI 调用，保持与现有系统的兼容性
"""

import subprocess
import json
import shutil
from typing import Dict, Any, Optional, List
from pathlib import Path

from .base import ModelBackend, ModelResponse, ModelConfig, ModelCapability


class ClaudeBackend(ModelBackend):
    """
    Claude 模型后端

    使用 Claude CLI 进行调用，支持：
    - claude (默认模型)
    - claude opus
    - claude sonnet
    """

    # CLI模型名称映射
    MODEL_ALIASES = {
        "claude": "claude",
        "claude-3-opus": "opus",
        "claude-3-sonnet": "sonnet",
        "claude-3-haiku": "haiku",
        "claude-opus": "opus",
        "claude-sonnet": "sonnet",
        "claude-haiku": "haiku",
    }

    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self._cli_path = self._find_cli()

    def _find_cli(self) -> Optional[str]:
        """查找 Claude CLI 路径"""
        return shutil.which("claude")

    def _check_availability(self) -> bool:
        """检查 Claude CLI 是否可用"""
        if not self._cli_path:
            return False
        try:
            result = subprocess.run(
                [self._cli_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except Exception:
            return False

    def _get_model_flag(self) -> List[str]:
        """获取模型标志参数"""
        model_name = self.config.name.lower()
        alias = self.MODEL_ALIASES.get(model_name, "")

        if alias and alias != "claude":
            return [alias]
        return []

    def generate(self, prompt: str, **kwargs) -> ModelResponse:
        """
        使用 Claude CLI 生成响应

        Args:
            prompt: 输入提示
            **kwargs: 额外参数
                - max_tokens: 最大token数
                - temperature: 温度
                - timeout: 超时时间（秒）
                - working_dir: 工作目录

        Returns:
            ModelResponse: 模型响应
        """
        if not self.is_available():
            return ModelResponse(
                content="",
                finish_reason="error",
                metadata={"error": "Claude CLI not available"}
            )

        timeout = kwargs.get("timeout", 600)
        working_dir = kwargs.get("working_dir", Path.cwd())

        # 构建命令
        cmd = [self._cli_path]
        cmd.extend(self._get_model_flag())

        # 添加其他参数
        if kwargs.get("max_tokens"):
            cmd.extend(["--max-tokens", str(kwargs["max_tokens"])])

        try:
            result = subprocess.run(
                cmd,
                input=prompt,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(working_dir)
            )

            if result.returncode == 0:
                return ModelResponse(
                    content=result.stdout,
                    tokens_used=self._estimate_tokens(prompt, result.stdout),
                    model_name=self.config.name,
                    finish_reason="complete",
                    metadata={"cli_success": True}
                )
            else:
                return ModelResponse(
                    content=result.stderr,
                    finish_reason="error",
                    metadata={
                        "error": f"Claude CLI failed with code {result.returncode}",
                        "stderr": result.stderr
                    }
                )

        except subprocess.TimeoutExpired:
            return ModelResponse(
                content="",
                finish_reason="timeout",
                metadata={"error": f"Timeout after {timeout}s"}
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
        """
        带上下文的生成

        将系统提示和对话历史组合成完整prompt
        """
        # 构建完整prompt
        full_prompt = ""

        # 添加系统提示
        if system_prompt:
            full_prompt += f"<system>\n{system_prompt}\n</system>\n\n"

        # 添加对话历史
        for msg in context:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "user":
                full_prompt += f"Human: {content}\n\n"
            elif role == "assistant":
                full_prompt += f"Assistant: {content}\n\n"

        # 添加当前用户提示
        full_prompt += f"Human: {user_prompt}\n\nAssistant:"

        return self.generate(full_prompt, **kwargs)

    def count_tokens(self, text: str) -> int:
        """
        估算token数量

        使用简单的启发式方法：~4字符/token
        """
        return self._estimate_tokens(text, "")

    def _estimate_tokens(self, prompt: str, response: str) -> int:
        """估算总token数"""
        total_chars = len(prompt) + len(response)
        return total_chars // 4  # 粗略估算


class ClaudeOpusBackend(ClaudeBackend):
    """Claude Opus 专用后端"""

    def __init__(self, config: ModelConfig = None):
        if config is None:
            config = ModelConfig(
                name="claude-opus",
                capabilities=[
                    ModelCapability.TEXT_GENERATION,
                    ModelCapability.ANALYSIS,
                    ModelCapability.CREATIVE_WRITING,
                ],
                default_for=["creative", "analysis", "writing"]
            )
        super().__init__(config)


class ClaudeSonnetBackend(ClaudeBackend):
    """Claude Sonnet 专用后端"""

    def __init__(self, config: ModelConfig = None):
        if config is None:
            config = ModelConfig(
                name="claude-sonnet",
                capabilities=[
                    ModelCapability.TEXT_GENERATION,
                    ModelCapability.CODE_GENERATION,
                    ModelCapability.ANALYSIS,
                ],
                default_for=["coding", "general"]
            )
        super().__init__(config)

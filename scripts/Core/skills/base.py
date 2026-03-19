"""
Skill Base - 技能基类

定义原子化技能的接口和类型
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from enum import Enum
from pathlib import Path


class SkillType(Enum):
    """技能类型"""
    DETERMINISTIC = "deterministic"   # 纯代码，0次LLM调用
    LLM_ASSISTED = "llm_assisted"     # LLM+代码，1次调用
    AGENTIC = "agentic"               # 完全推理，3+次调用


@dataclass
class SkillContext:
    """技能执行上下文"""
    project_name: str
    task_id: str
    inputs: Dict[str, Any] = field(default_factory=dict)
    working_dir: Path = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.working_dir and not isinstance(self.working_dir, Path):
            self.working_dir = Path(self.working_dir)


@dataclass
class SkillResult:
    """技能执行结果"""
    success: bool
    outputs: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    artifacts: List[str] = field(default_factory=list)
    llm_calls: int = 0
    execution_time: float = 0.0

    def to_dict(self) -> Dict:
        return {
            "success": self.success,
            "outputs": self.outputs,
            "error": self.error,
            "artifacts": self.artifacts,
            "llm_calls": self.llm_calls,
            "execution_time": self.execution_time,
        }


class Skill(ABC):
    """
    技能基类

    所有原子技能必须继承此类并实现 execute 方法
    """

    # 子类必须定义的类属性
    name: str
    description: str
    skill_type: SkillType
    inputs: List[str] = []
    outputs: List[str] = []
    mcp_required: List[str] = []

    @abstractmethod
    def execute(self, context: SkillContext) -> SkillResult:
        """
        执行技能

        Args:
            context: 执行上下文

        Returns:
            SkillResult: 执行结果
        """
        pass

    def validate_inputs(self, context: SkillContext) -> tuple:
        """
        验证输入

        Returns:
            tuple: (is_valid, error_message)
        """
        for input_name in self.inputs:
            if input_name not in context.inputs and input_name not in context.metadata:
                return False, f"Missing required input: {input_name}"
        return True, None

    def estimate_llm_calls(self) -> int:
        """
        估计LLM调用次数

        Returns:
            int: 预计调用次数
        """
        if self.skill_type == SkillType.DETERMINISTIC:
            return 0
        elif self.skill_type == SkillType.LLM_ASSISTED:
            return 1
        else:
            return 3  # AGENTIC类型的默认估计

    def get_info(self) -> Dict:
        """获取技能信息"""
        return {
            "name": self.name,
            "description": self.description,
            "type": self.skill_type.value,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "mcp_required": self.mcp_required,
            "estimated_llm_calls": self.estimate_llm_calls(),
        }


class CompositeSkill(Skill):
    """
    复合技能

    由多个原子技能组合而成
    """

    def __init__(self, sub_skills: List[Skill]):
        self.sub_skills = sub_skills

    def execute(self, context: SkillContext) -> SkillResult:
        """按顺序执行子技能"""
        import time

        total_llm_calls = 0
        all_outputs = {}
        all_artifacts = []

        for skill in self.sub_skills:
            # 验证输入
            is_valid, error = skill.validate_inputs(context)
            if not is_valid:
                return SkillResult(
                    success=False,
                    error=f"Validation failed for {skill.name}: {error}",
                    llm_calls=total_llm_calls,
                )

            # 执行子技能
            start_time = time.time()
            result = skill.execute(context)
            total_llm_calls += result.llm_calls

            if not result.success:
                return SkillResult(
                    success=False,
                    error=f"Sub-skill {skill.name} failed: {result.error}",
                    outputs=all_outputs,
                    llm_calls=total_llm_calls,
                )

            # 合并输出
            all_outputs.update(result.outputs)
            all_artifacts.extend(result.artifacts)

            # 更新上下文供下一个技能使用
            context.metadata.update(result.outputs)

        return SkillResult(
            success=True,
            outputs=all_outputs,
            artifacts=all_artifacts,
            llm_calls=total_llm_calls,
        )


class DeterministicSkill(Skill):
    """确定性技能基类（纯代码执行）"""

    skill_type = SkillType.DETERMINISTIC

    def estimate_llm_calls(self) -> int:
        return 0


class LLMAssistedSkill(Skill):
    """LLM辅助技能基类"""

    skill_type = SkillType.LLM_ASSISTED

    def __init__(self, model_router=None):
        self.model_router = model_router

    def get_model(self, task_type: str = None):
        """获取模型后端"""
        if self.model_router is None:
            from Core.model.factory import get_model_router
            self.model_router = get_model_router()
        return self.model_router.get_backend(task_type)

    def estimate_llm_calls(self) -> int:
        return 1


class AgenticSkill(Skill):
    """智能体技能基类（完全LLM推理）"""

    skill_type = SkillType.AGENTIC

    def __init__(self, model_router=None, max_iterations: int = 5):
        self.model_router = model_router
        self.max_iterations = max_iterations

    def get_model(self, task_type: str = None):
        """获取模型后端"""
        if self.model_router is None:
            from Core.model.factory import get_model_router
            self.model_router = get_model_router()
        return self.model_router.get_backend(task_type)

    def estimate_llm_calls(self) -> int:
        return self.max_iterations

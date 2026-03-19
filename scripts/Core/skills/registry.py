"""
Skill Registry - 技能注册表

管理和查找可用技能
"""

from typing import Dict, List, Optional, Type
from pathlib import Path
import importlib
import os

from .base import Skill, SkillType, SkillContext, SkillResult


class SkillRegistry:
    """
    技能注册表

    管理所有可用技能，提供查找和执行接口
    """

    def __init__(self):
        self._skills: Dict[str, Skill] = {}
        self._task_skill_map: Dict[str, str] = {}
        self._load_builtin_skills()

    def _load_builtin_skills(self):
        """加载内置技能"""
        # 文献技能
        try:
            from .atomic.literature.search import SemanticLiteratureSearchSkill
            self.register(SemanticLiteratureSearchSkill())
        except ImportError:
            pass

        # 写作技能
        try:
            from .atomic.writing.academic import AcademicWritingSkill
            self.register(AcademicWritingSkill())
        except ImportError:
            pass

        # 分析技能
        try:
            from .atomic.analysis.statistical import StatisticalAnalysisSkill
            self.register(StatisticalAnalysisSkill())
        except ImportError:
            pass

        # 注册任务映射
        self._setup_task_mapping()

    def _setup_task_mapping(self):
        """设置任务到技能的映射"""
        # 文献搜索任务
        for task_id in ["T005", "T006", "T007", "T008", "T009", "T010"]:
            self._task_skill_map[task_id] = "semantic_literature_search"

        # 统计分析任务
        self._task_skill_map["T058"] = "statistical_analysis"

        # 写作任务
        for task_id in ["T063", "T064", "T065", "T066", "T067", "T068"]:
            self._task_skill_map[task_id] = "academic_writing"

    def register(self, skill: Skill) -> None:
        """
        注册技能

        Args:
            skill: 技能实例
        """
        self._skills[skill.name] = skill

    def unregister(self, name: str) -> bool:
        """
        注销技能

        Args:
            name: 技能名称

        Returns:
            bool: 是否成功
        """
        if name in self._skills:
            del self._skills[name]
            return True
        return False

    def get(self, name: str) -> Optional[Skill]:
        """
        获取技能

        Args:
            name: 技能名称

        Returns:
            Skill: 技能实例，不存在返回None
        """
        return self._skills.get(name)

    def get_for_task(self, task: Dict) -> Optional[Skill]:
        """
        根据任务获取技能

        Args:
            task: 任务字典

        Returns:
            Skill: 技能实例
        """
        # 1. 优先使用显式指定的技能
        skill_name = task.get("skill")
        if skill_name:
            return self.get(skill_name)

        # 2. 根据任务ID映射
        task_id = task.get("id", "")
        if task_id in self._task_skill_map:
            return self.get(self._task_skill_map[task_id])

        # 3. 根据任务类型推断
        task_type = task.get("type", "")
        if task_type == "deterministic":
            # 查找确定性技能
            for skill in self._skills.values():
                if skill.skill_type == SkillType.DETERMINISTIC:
                    # 简单匹配
                    if any(kw in task.get("description", "").lower()
                           for kw in ["搜索", "search", "下载", "download"]):
                        return skill

        return None

    def list_skills(self, skill_type: SkillType = None) -> List[Skill]:
        """
        列出技能

        Args:
            skill_type: 技能类型过滤

        Returns:
            List[Skill]: 技能列表
        """
        if skill_type:
            return [s for s in self._skills.values()
                    if s.skill_type == skill_type]
        return list(self._skills.values())

    def list_skill_names(self, skill_type: SkillType = None) -> List[str]:
        """列出技能名称"""
        skills = self.list_skills(skill_type)
        return [s.name for s in skills]

    def get_skills_info(self) -> List[Dict]:
        """获取所有技能信息"""
        return [skill.get_info() for skill in self._skills.values()]

    def load_user_skills(self, skills_dir: Path = None):
        """
        加载用户自定义技能

        Args:
            skills_dir: 技能目录路径
        """
        if skills_dir is None:
            skills_dir = Path(__file__).parent / "user"

        if not skills_dir.exists():
            return

        for py_file in skills_dir.glob("*.py"):
            if py_file.name.startswith("_"):
                continue

            try:
                # 动态导入
                module_name = py_file.stem
                spec = importlib.util.spec_from_file_location(
                    f"user_skills.{module_name}",
                    py_file
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # 查找技能类
                for name in dir(module):
                    obj = getattr(module, name)
                    if (isinstance(obj, type) and
                            issubclass(obj, Skill) and
                            obj is not Skill):
                        try:
                            skill = obj()
                            self.register(skill)
                        except Exception:
                            pass

            except Exception as e:
                print(f"Error loading user skill {py_file}: {e}")

    def execute_skill(
        self,
        skill_name: str,
        context: SkillContext
    ) -> SkillResult:
        """
        执行技能

        Args:
            skill_name: 技能名称
            context: 执行上下文

        Returns:
            SkillResult: 执行结果
        """
        skill = self.get(skill_name)
        if skill is None:
            return SkillResult(
                success=False,
                error=f"Skill not found: {skill_name}",
            )

        # 验证输入
        is_valid, error = skill.validate_inputs(context)
        if not is_valid:
            return SkillResult(
                success=False,
                error=error,
            )

        # 执行
        return skill.execute(context)


# 全局注册表
_registry: Optional[SkillRegistry] = None


def get_skill_registry() -> SkillRegistry:
    """获取全局技能注册表"""
    global _registry
    if _registry is None:
        _registry = SkillRegistry()
    return _registry


def register_skill(skill: Skill) -> None:
    """注册技能到全局注册表"""
    registry = get_skill_registry()
    registry.register(skill)


def get_skill(name: str) -> Optional[Skill]:
    """获取技能"""
    return get_skill_registry().get(name)


def execute_skill(skill_name: str, context: SkillContext) -> SkillResult:
    """执行技能"""
    return get_skill_registry().execute_skill(skill_name, context)

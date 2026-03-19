"""
Task Router - 任务路由器

根据任务类型路由到合适的执行策略：
- DETERMINISTIC: 纯代码执行，0次LLM调用
- SEMI_DETERMINISTIC: 代码+少量LLM
- AGENTIC: 完全LLM推理
"""

from typing import Dict, Any, Optional, Callable, Set
from enum import Enum
from dataclasses import dataclass, field
from pathlib import Path
import json


class TaskType(Enum):
    """任务类型"""
    DETERMINISTIC = "deterministic"     # 纯代码，无需LLM
    SEMI_DETERMINISTIC = "semi"         # 代码 + 少量LLM
    AGENTIC = "agentic"                 # 完全LLM推理


@dataclass
class TaskResult:
    """任务执行结果"""
    success: bool
    task_id: str
    outputs: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    artifacts: list = field(default_factory=list)
    llm_calls: int = 0
    execution_time: float = 0.0

    def to_dict(self) -> Dict:
        return {
            "success": self.success,
            "task_id": self.task_id,
            "outputs": self.outputs,
            "error": self.error,
            "artifacts": self.artifacts,
            "llm_calls": self.llm_calls,
            "execution_time": self.execution_time,
        }


class TaskRouter:
    """
    任务路由器

    根据任务ID和配置决定执行策略
    """

    # 确定性任务集合（纯代码执行，无需LLM）
    DETERMINISTIC_TASKS: Set[str] = {
        # 文献搜索 (T005-T010) - API调用
        "T005", "T006", "T007", "T008", "T009", "T010",
        # 数据处理 (T011-T014) - 去重/排序/筛选
        "T011", "T012", "T013", "T014",
        # 文件操作 (T015-T017) - PDF下载/整理
        "T015", "T016", "T017",
        # BibTeX生成 (T035)
        "T035",
        # 统计检验 (T058)
        "T058",
        # LaTeX编译 (T090-T091)
        "T090", "T091",
    }

    # 半确定性任务（代码为主，少量LLM辅助）
    SEMI_DETERMINISTIC_TASKS: Set[str] = {
        # 论文研读 (T018-T030) - 结构化提取
        "T018", "T019", "T020", "T021", "T022", "T023",
        "T024", "T025", "T026", "T027", "T028", "T029", "T030",
        # 可视化 (T059) - 模板生成
        "T059",
        # 代码生成 (T045-T051) - 模板+LLM
        "T045", "T046", "T047", "T048", "T049", "T050", "T051",
    }

    def __init__(self, project_dir: Path = None):
        self.project_dir = project_dir or Path.cwd()
        self._executors: Dict[str, Callable] = {}
        self._load_executors()

    def _load_executors(self):
        """加载确定性执行器"""
        try:
            from .deterministic.search_executor import SearchExecutor
            from .deterministic.file_executor import FileExecutor
            from .deterministic.stats_executor import StatsExecutor
            from .deterministic.latex_executor import LatexExecutor

            # 搜索执行器
            search = SearchExecutor(self.project_dir)
            for task_id in ["T005", "T006", "T007", "T008", "T009", "T010"]:
                self._executors[task_id] = search.execute

            # 文件执行器
            file_exec = FileExecutor(self.project_dir)
            for task_id in ["T011", "T012", "T013", "T014", "T015", "T016", "T017"]:
                self._executors[task_id] = file_exec.execute

            # 统计执行器
            stats = StatsExecutor(self.project_dir)
            self._executors["T058"] = stats.execute

            # LaTeX执行器
            latex = LatexExecutor(self.project_dir)
            for task_id in ["T090", "T091"]:
                self._executors[task_id] = latex.execute

        except ImportError as e:
            print(f"Warning: Could not load some executors: {e}")

    def classify_task(self, task: Dict) -> TaskType:
        """
        分类任务类型

        Args:
            task: 任务字典，包含 id, description 等

        Returns:
            TaskType: 任务类型
        """
        task_id = task.get("id", "")
        task_type = task.get("type", "")

        # 优先使用显式类型标记
        if task_type == "deterministic":
            return TaskType.DETERMINISTIC
        elif task_type == "semi":
            return TaskType.SEMI_DETERMINISTIC
        elif task_type == "agentic":
            return TaskType.AGENTIC

        # 根据任务ID判断
        if task_id in self.DETERMINISTIC_TASKS:
            return TaskType.DETERMINISTIC
        elif task_id in self.SEMI_DETERMINISTIC_TASKS:
            return TaskType.SEMI_DETERMINISTIC
        else:
            return TaskType.AGENTIC

    def execute_task(
        self,
        task: Dict,
        context: Dict[str, Any] = None,
        llm_fallback: Callable = None
    ) -> TaskResult:
        """
        执行任务

        Args:
            task: 任务字典
            context: 执行上下文
            llm_fallback: LLM回退函数

        Returns:
            TaskResult: 执行结果
        """
        import time
        start_time = time.time()

        task_type = self.classify_task(task)
        task_id = task.get("id", "unknown")

        context = context or {}
        context["project_dir"] = self.project_dir

        if task_type == TaskType.DETERMINISTIC:
            result = self._execute_deterministic(task, context)
        elif task_type == TaskType.SEMI_DETERMINISTIC:
            result = self._execute_semi(task, context, llm_fallback)
        else:
            result = self._execute_agentic(task, context, llm_fallback)

        result.execution_time = time.time() - start_time
        return result

    def _execute_deterministic(
        self,
        task: Dict,
        context: Dict
    ) -> TaskResult:
        """执行确定性任务"""
        task_id = task.get("id", "")

        executor = self._executors.get(task_id[:3])  # 使用前缀匹配
        if executor is None:
            executor = self._executors.get(task_id)

        if executor:
            try:
                result = executor(task, context)
                if isinstance(result, dict):
                    return TaskResult(
                        success=result.get("success", True),
                        task_id=task_id,
                        outputs=result.get("outputs", {}),
                        error=result.get("error"),
                        llm_calls=0,
                    )
                return result
            except Exception as e:
                return TaskResult(
                    success=False,
                    task_id=task_id,
                    error=str(e),
                    llm_calls=0,
                )
        else:
            return TaskResult(
                success=False,
                task_id=task_id,
                error=f"No executor for deterministic task: {task_id}",
                llm_calls=0,
            )

    def _execute_semi(
        self,
        task: Dict,
        context: Dict,
        llm_fallback: Callable = None
    ) -> TaskResult:
        """执行半确定性任务"""
        # 先尝试确定性执行
        result = self._execute_deterministic(task, context)
        if result.success:
            return result

        # 失败则回退到LLM
        if llm_fallback:
            try:
                llm_result = llm_fallback(task, context)
                return TaskResult(
                    success=llm_result.get("success", True),
                    task_id=task.get("id", ""),
                    outputs=llm_result,
                    llm_calls=1,
                )
            except Exception as e:
                return TaskResult(
                    success=False,
                    task_id=task.get("id", ""),
                    error=str(e),
                    llm_calls=1,
                )

        return result

    def _execute_agentic(
        self,
        task: Dict,
        context: Dict,
        llm_fallback: Callable = None
    ) -> TaskResult:
        """执行智能体任务"""
        if llm_fallback is None:
            return TaskResult(
                success=False,
                task_id=task.get("id", ""),
                error="No LLM fallback provided for agentic task",
            )

        try:
            llm_result = llm_fallback(task, context)
            return TaskResult(
                success=llm_result.get("success", True),
                task_id=task.get("id", ""),
                outputs=llm_result,
                llm_calls=llm_result.get("llm_calls", 1),
            )
        except Exception as e:
            return TaskResult(
                success=False,
                task_id=task.get("id", ""),
                error=str(e),
            )

    def get_statistics(self) -> Dict:
        """获取路由统计"""
        return {
            "deterministic_tasks": len(self.DETERMINISTIC_TASKS),
            "semi_deterministic_tasks": len(self.SEMI_DETERMINISTIC_TASKS),
            "total_tasks": 100,
            "potential_llm_reduction": len(self.DETERMINISTIC_TASKS),
        }


# 全局路由器实例
_router: Optional[TaskRouter] = None


def get_task_router(project_dir: Path = None) -> TaskRouter:
    """获取任务路由器"""
    global _router
    if _router is None or project_dir is not None:
        _router = TaskRouter(project_dir)
    return _router


def execute_task(
    task: Dict,
    context: Dict = None,
    llm_fallback: Callable = None,
    project_dir: Path = None
) -> TaskResult:
    """
    便捷的任务执行函数

    Args:
        task: 任务字典
        context: 执行上下文
        llm_fallback: LLM回退函数
        project_dir: 项目目录

    Returns:
        TaskResult: 执行结果
    """
    router = get_task_router(project_dir)
    return router.execute_task(task, context, llm_fallback)

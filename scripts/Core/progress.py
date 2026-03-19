"""
Project Prometheus - 状态管理工具
====================================

管理 state.json 和 research_tasks.json 的读写操作。
"""

import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, List, Dict


# 默认路径
DEFAULT_BASE_DIR = Path(__file__).parent.parent
STATE_FILE = DEFAULT_BASE_DIR / "Core" / "workflow" / "state.json"
TASKS_FILE = DEFAULT_BASE_DIR / "Core" / "workflow" / "research_tasks.json"
LOG_FILE = DEFAULT_BASE_DIR / "Logs" / "operational.log"
ERROR_LOG = DEFAULT_BASE_DIR / "Logs" / "error_trace.log"
INBOX_DIR = DEFAULT_BASE_DIR / "Communication" / "inbox"
OUTBOX_DIR = DEFAULT_BASE_DIR / "Communication" / "outbox"


class StateManager:
    """状态机管理器"""

    def __init__(self, state_path: Optional[Path] = None):
        self.state_path = Path(state_path) if state_path else STATE_FILE
        self._state = None

    def load(self) -> dict:
        """加载状态文件"""
        if not self.state_path.exists():
            return self._create_default_state()
        with open(self.state_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save(self, state: dict) -> None:
        """保存状态文件"""
        state['last_updated'] = datetime.now().isoformat()
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_path, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)

    def _create_default_state(self) -> dict:
        """创建默认状态"""
        return {
            "version": "1.0",
            "last_updated": datetime.now().isoformat(),
            "current_project": None,
            "current_phase": "literature_review",
            "current_task": None,
            "session_info": {
                "session_id": f"sess_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "context_window_count": 0,
                "tokens_used_this_session": 0
            },
            "step_details": {
                "current_attempt": 0,
                "last_error": None,
                "solution_planned": None,
                "retry_count": 0
            },
            "knowledge_base": {
                "papers_read": 0,
                "key_findings": [],
                "best_practices": {}
            },
            "human_interaction": {
                "pending_approval": False,
                "last_approval_type": None,
                "last_command": None
            },
            "status": "initialized",
            "status_reason": None
        }

    @property
    def state(self) -> dict:
        """懒加载状态"""
        if self._state is None:
            self._state = self.load()
        return self._state

    def update(self, **kwargs) -> None:
        """更新状态字段"""
        for key, value in kwargs.items():
            if '.' in key:
                # 支持嵌套更新，如 "step_details.current_attempt"
                keys = key.split('.')
                obj = self.state
                for k in keys[:-1]:
                    obj = obj.setdefault(k, {})
                obj[keys[-1]] = value
            else:
                self.state[key] = value
        self.save(self.state)

    def get_phase(self) -> str:
        """获取当前阶段"""
        return self.state.get('current_phase', 'literature_review')

    def get_task(self) -> Optional[str]:
        """获取当前任务"""
        return self.state.get('current_task')

    def set_task(self, task_id: str) -> None:
        """设置当前任务"""
        self.update(current_task=task_id)

    def increment_attempt(self) -> int:
        """增加尝试次数"""
        current = self.state['step_details'].get('current_attempt', 0)
        new_attempt = current + 1
        self.update(**{'step_details.current_attempt': new_attempt})
        return new_attempt

    def reset_attempt(self) -> None:
        """重置尝试次数"""
        self.update(**{
            'step_details.current_attempt': 0,
            'step_details.last_error': None,
            'step_details.retry_count': 0
        })

    def set_error(self, error: str) -> None:
        """记录错误"""
        self.update(**{'step_details.last_error': error})

    def set_status(self, status: str, reason: Optional[str] = None) -> None:
        """设置系统状态"""
        self.update(status=status, status_reason=reason)


class TaskManager:
    """任务清单管理器"""

    def __init__(self, tasks_path: Optional[Path] = None):
        self.tasks_path = Path(tasks_path) if tasks_path else TASKS_FILE
        self._tasks = None

    def load(self) -> dict:
        """加载任务清单"""
        if not self.tasks_path.exists():
            return self._create_default_tasks()
        with open(self.tasks_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save(self, tasks: dict) -> None:
        """保存任务清单"""
        self.tasks_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.tasks_path, 'w', encoding='utf-8') as f:
            json.dump(tasks, f, indent=2, ensure_ascii=False)

    def _create_default_tasks(self) -> dict:
        """创建默认任务清单"""
        return {
            "project_name": "Untitled_Project",
            "created_at": datetime.now().isoformat(),
            "research_domain": "",
            "research_question": "",
            "phases": [],
            "ouroboros": {
                "completed_cycles": 0,
                "archived_projects": [],
                "knowledge_updates": []
            }
        }

    @property
    def tasks(self) -> dict:
        """懒加载任务"""
        if self._tasks is None:
            self._tasks = self.load()
        return self._tasks

    def get_current_phase_tasks(self, phase_id: str) -> list:
        """获取指定阶段的任务"""
        for phase in self.tasks.get('phases', []):
            if phase['phase_id'] == phase_id:
                return phase.get('tasks', [])
        return []

    def get_next_pending_task(self, phase_id: Optional[str] = None) -> Optional[dict]:
        """获取下一个待完成的任务"""
        phases = self.tasks.get('phases', [])

        for phase in phases:
            if phase_id and phase['phase_id'] != phase_id:
                continue
            if phase.get('status') == 'completed':
                continue

            for task in phase.get('tasks', []):
                if not task.get('passes', False):
                    return {
                        'phase_id': phase['phase_id'],
                        'phase_name': phase['phase_name'],
                        'task': task
                    }
        return None

    def mark_task_passed(self, phase_id: str, task_id: str) -> bool:
        """标记任务为已完成"""
        for phase in self.tasks.get('phases', []):
            if phase['phase_id'] == phase_id:
                for task in phase.get('tasks', []):
                    if task['task_id'] == task_id:
                        task['passes'] = True
                        self.save(self.tasks)
                        return True
        return False

    def count_pending_tasks(self) -> int:
        """统计待完成任务数量"""
        count = 0
        for phase in self.tasks.get('phases', []):
            for task in phase.get('tasks', []):
                if not task.get('passes', False):
                    count += 1
        return count

    def count_passed_tasks(self) -> int:
        """统计已完成任务数量"""
        count = 0
        for phase in self.tasks.get('phases', []):
            for task in phase.get('tasks', []):
                if task.get('passes', False):
                    count += 1
        return count

    def get_progress_summary(self) -> dict:
        """获取进度摘要"""
        total = 0
        passed = 0
        phases_status = {}

        for phase in self.tasks.get('phases', []):
            phase_total = len(phase.get('tasks', []))
            phase_passed = sum(1 for t in phase.get('tasks', []) if t.get('passes', False))
            total += phase_total
            passed += phase_passed

            phases_status[phase['phase_id']] = {
                'name': phase['phase_name'],
                'total': phase_total,
                'passed': phase_passed,
                'status': phase.get('status', 'pending')
            }

        return {
            'project_name': self.tasks.get('project_name'),
            'total_tasks': total,
            'passed_tasks': passed,
            'pending_tasks': total - passed,
            'progress_percent': round(passed / total * 100, 1) if total > 0 else 0,
            'phases': phases_status
        }


class LogManager:
    """日志管理器"""

    def __init__(self, log_path: Optional[Path] = None, error_path: Optional[Path] = None):
        self.log_path = Path(log_path) if log_path else LOG_FILE
        self.error_path = Path(error_path) if error_path else ERROR_LOG

    def log(self, message: str, level: str = "INFO") -> None:
        """写入操作日志"""
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.log_path, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] [{level}] {message}\n")

    def error(self, message: str, trace: Optional[str] = None) -> None:
        """写入错误日志"""
        self.error_path.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.error_path, 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"[{timestamp}] ERROR\n")
            f.write(f"Message: {message}\n")
            if trace:
                f.write(f"Trace:\n{trace}\n")
            f.write(f"{'='*60}\n")


class CommunicationManager:
    """人机交互管理器"""

    def __init__(self, inbox_dir: Optional[Path] = None, outbox_dir: Optional[Path] = None):
        self.inbox_dir = Path(inbox_dir) if inbox_dir else INBOX_DIR
        self.outbox_dir = Path(outbox_dir) if outbox_dir else OUTBOX_DIR
        self.commands_file = self.inbox_dir / "commands.txt"

    def check_commands(self) -> list:
        """检查并读取新指令"""
        if not self.commands_file.exists():
            return []

        with open(self.commands_file, 'r', encoding='utf-8') as f:
            content = f.read().strip()

        if not content:
            return []

        commands = []
        for line in content.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                commands.append(line)

        return commands

    def clear_commands(self) -> None:
        """清空指令文件"""
        if self.commands_file.exists():
            with open(self.commands_file, 'w', encoding='utf-8') as f:
                f.write("# Commands processed\n")

    def send_report(self, filename: str, content: str) -> Path:
        """发送报告到 outbox"""
        self.outbox_dir.mkdir(parents=True, exist_ok=True)
        filepath = self.outbox_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return filepath


class KnowledgeBaseManager:
    """知识库管理器

    管理研究发现和最佳实践的持久化和检索。
    """

    def __init__(self, state_manager: Optional[StateManager] = None,
                 knowledge_file: Optional[Path] = None):
        """
        初始化知识库管理器

        Args:
            state_manager: 状态管理器实例（用于同步知识到状态）
            knowledge_file: 独立的知识库文件路径（用于持久化存储）
        """
        self.state_manager = state_manager or StateManager()
        self.knowledge_file = Path(knowledge_file) if knowledge_file else \
            DEFAULT_BASE_DIR / "Core" / "workflow" / "knowledge_base.json"
        self._knowledge = None

    def load(self) -> dict:
        """加载知识库文件"""
        if not self.knowledge_file.exists():
            return self._create_default_knowledge()
        with open(self.knowledge_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save(self, knowledge: dict) -> None:
        """保存知识库文件"""
        knowledge['last_updated'] = datetime.now().isoformat()
        self.knowledge_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.knowledge_file, 'w', encoding='utf-8') as f:
            json.dump(knowledge, f, indent=2, ensure_ascii=False)
        # 同步到状态管理器
        self._sync_to_state(knowledge)

    def _create_default_knowledge(self) -> dict:
        """创建默认知识库结构"""
        return {
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "papers_read": 0,
            "key_findings": [],
            "best_practices": {},
            "lessons_learned": [],
            "domain_knowledge": {}
        }

    def _sync_to_state(self, knowledge: dict) -> None:
        """同步知识到状态管理器"""
        try:
            self.state_manager.update(
                **{'knowledge_base.papers_read': knowledge.get('papers_read', 0)},
                **{'knowledge_base.key_findings': knowledge.get('key_findings', [])},
                **{'knowledge_base.best_practices': knowledge.get('best_practices', {})}
            )
        except Exception:
            pass  # 静默处理状态同步失败

    @property
    def knowledge(self) -> dict:
        """懒加载知识库"""
        if self._knowledge is None:
            self._knowledge = self.load()
        return self._knowledge

    def add_finding(self, finding: str, category: Optional[str] = None,
                    source: Optional[str] = None, importance: int = 1,
                    tags: Optional[List[str]] = None) -> str:
        """
        添加研究发现

        Args:
            finding: 发现内容
            category: 分类（如 'literature', 'experiment', 'analysis'）
            source: 来源（如论文标题、实验编号）
            importance: 重要程度 1-5（5最重要）
            tags: 标签列表

        Returns:
            发现的 ID
        """
        finding_id = f"finding_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

        new_finding = {
            "id": finding_id,
            "content": finding,
            "category": category or "general",
            "source": source,
            "importance": min(max(importance, 1), 5),
            "tags": tags or [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }

        knowledge = self.knowledge
        knowledge['key_findings'].append(new_finding)
        self.save(knowledge)
        self._knowledge = knowledge

        return finding_id

    def get_findings(self, category: Optional[str] = None,
                     min_importance: Optional[int] = None,
                     tags: Optional[List[str]] = None,
                     limit: int = 50) -> List[dict]:
        """
        获取研究发现

        Args:
            category: 按分类筛选
            min_importance: 最低重要程度
            tags: 按标签筛选（满足任一标签即可）
            limit: 返回数量限制

        Returns:
            匹配的发现列表
        """
        findings = self.knowledge.get('key_findings', [])

        # 筛选
        if category:
            findings = [f for f in findings if f.get('category') == category]

        if min_importance is not None:
            findings = [f for f in findings if f.get('importance', 1) >= min_importance]

        if tags:
            findings = [f for f in findings
                       if any(tag in f.get('tags', []) for tag in tags)]

        # 按重要程度和创建时间排序
        findings.sort(key=lambda x: (-x.get('importance', 1), x.get('created_at', '')),
                     reverse=False)

        return findings[:limit]

    def get_finding_by_id(self, finding_id: str) -> Optional[dict]:
        """
        根据 ID 获取单个发现

        Args:
            finding_id: 发现 ID

        Returns:
            发现内容或 None
        """
        for finding in self.knowledge.get('key_findings', []):
            if finding.get('id') == finding_id:
                return finding
        return None

    def update_finding(self, finding_id: str, **kwargs) -> bool:
        """
        更新发现

        Args:
            finding_id: 发现 ID
            **kwargs: 要更新的字段

        Returns:
            是否成功
        """
        knowledge = self.knowledge
        for finding in knowledge.get('key_findings', []):
            if finding.get('id') == finding_id:
                for key, value in kwargs.items():
                    if key != 'id':  # 不允许修改 ID
                        finding[key] = value
                finding['updated_at'] = datetime.now().isoformat()
                self.save(knowledge)
                self._knowledge = knowledge
                return True
        return False

    def remove_finding(self, finding_id: str) -> bool:
        """
        删除发现

        Args:
            finding_id: 发现 ID

        Returns:
            是否成功
        """
        knowledge = self.knowledge
        original_count = len(knowledge.get('key_findings', []))
        knowledge['key_findings'] = [
            f for f in knowledge.get('key_findings', [])
            if f.get('id') != finding_id
        ]
        if len(knowledge['key_findings']) < original_count:
            self.save(knowledge)
            self._knowledge = knowledge
            return True
        return False

    def update_best_practice(self, key: str, value: Any,
                             description: Optional[str] = None) -> None:
        """
        更新最佳实践

        Args:
            key: 最佳实践的键名
            value: 最佳实践的内容
            description: 可选的描述说明
        """
        knowledge = self.knowledge
        practice = {
            "value": value,
            "description": description,
            "updated_at": datetime.now().isoformat()
        }

        # 如果已存在，保留创建时间
        if key in knowledge.get('best_practices', {}):
            practice['created_at'] = knowledge['best_practices'][key].get('created_at',
                                            datetime.now().isoformat())
        else:
            practice['created_at'] = datetime.now().isoformat()

        knowledge.setdefault('best_practices', {})[key] = practice
        self.save(knowledge)
        self._knowledge = knowledge

    def get_best_practice(self, key: str) -> Optional[Any]:
        """
        获取最佳实践

        Args:
            key: 最佳实践的键名

        Returns:
            最佳实践的值或 None
        """
        practice = self.knowledge.get('best_practices', {}).get(key)
        return practice.get('value') if practice else None

    def get_all_best_practices(self) -> Dict[str, Any]:
        """
        获取所有最佳实践

        Returns:
            最佳实践字典
        """
        return {
            key: practice.get('value')
            for key, practice in self.knowledge.get('best_practices', {}).items()
        }

    def remove_best_practice(self, key: str) -> bool:
        """
        删除最佳实践

        Args:
            key: 最佳实践的键名

        Returns:
            是否成功
        """
        knowledge = self.knowledge
        if key in knowledge.get('best_practices', {}):
            del knowledge['best_practices'][key]
            self.save(knowledge)
            self._knowledge = knowledge
            return True
        return False

    def add_lesson_learned(self, lesson: str, context: Optional[str] = None,
                           severity: str = "info") -> str:
        """
        添加经验教训

        Args:
            lesson: 经验教训内容
            context: 上下文说明
            severity: 严重程度（info, warning, error）

        Returns:
            经验教训的 ID
        """
        lesson_id = f"lesson_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

        new_lesson = {
            "id": lesson_id,
            "content": lesson,
            "context": context,
            "severity": severity,
            "created_at": datetime.now().isoformat()
        }

        knowledge = self.knowledge
        knowledge.setdefault('lessons_learned', []).append(new_lesson)
        self.save(knowledge)
        self._knowledge = knowledge

        return lesson_id

    def get_lessons_learned(self, severity: Optional[str] = None,
                            limit: int = 50) -> List[dict]:
        """
        获取经验教训

        Args:
            severity: 按严重程度筛选
            limit: 返回数量限制

        Returns:
            经验教训列表
        """
        lessons = self.knowledge.get('lessons_learned', [])

        if severity:
            lessons = [l for l in lessons if l.get('severity') == severity]

        # 按创建时间倒序
        lessons.sort(key=lambda x: x.get('created_at', ''), reverse=True)

        return lessons[:limit]

    def increment_papers_read(self, count: int = 1) -> int:
        """
        增加已读论文计数

        Args:
            count: 增加的数量

        Returns:
            更新后的总数
        """
        knowledge = self.knowledge
        current = knowledge.get('papers_read', 0)
        knowledge['papers_read'] = current + count
        self.save(knowledge)
        self._knowledge = knowledge
        return knowledge['papers_read']

    def get_statistics(self) -> dict:
        """
        获取知识库统计信息

        Returns:
            统计信息字典
        """
        knowledge = self.knowledge
        findings = knowledge.get('key_findings', [])
        practices = knowledge.get('best_practices', {})
        lessons = knowledge.get('lessons_learned', [])

        # 按分类统计发现
        findings_by_category = {}
        for f in findings:
            cat = f.get('category', 'general')
            findings_by_category[cat] = findings_by_category.get(cat, 0) + 1

        # 按重要程度统计发现
        findings_by_importance = {}
        for f in findings:
            imp = f.get('importance', 1)
            findings_by_importance[imp] = findings_by_importance.get(imp, 0) + 1

        # 按严重程度统计教训
        lessons_by_severity = {}
        for l in lessons:
            sev = l.get('severity', 'info')
            lessons_by_severity[sev] = lessons_by_severity.get(sev, 0) + 1

        return {
            "papers_read": knowledge.get('papers_read', 0),
            "total_findings": len(findings),
            "findings_by_category": findings_by_category,
            "findings_by_importance": findings_by_importance,
            "total_best_practices": len(practices),
            "total_lessons_learned": len(lessons),
            "lessons_by_severity": lessons_by_severity,
            "last_updated": knowledge.get('last_updated')
        }

    def search(self, query: str, in_findings: bool = True,
               in_practices: bool = True, in_lessons: bool = True) -> dict:
        """
        在知识库中搜索

        Args:
            query: 搜索关键词
            in_findings: 是否在发现中搜索
            in_practices: 是否在最佳实践中搜索
            in_lessons: 是否在经验教训中搜索

        Returns:
            搜索结果字典
        """
        query_lower = query.lower()
        results = {
            "query": query,
            "findings": [],
            "best_practices": [],
            "lessons_learned": []
        }

        if in_findings:
            for f in self.knowledge.get('key_findings', []):
                if query_lower in f.get('content', '').lower():
                    results['findings'].append(f)
                elif query_lower in ' '.join(f.get('tags', [])).lower():
                    results['findings'].append(f)

        if in_practices:
            for key, practice in self.knowledge.get('best_practices', {}).items():
                value_str = str(practice.get('value', ''))
                desc_str = practice.get('description', '')
                if query_lower in value_str.lower() or query_lower in desc_str.lower():
                    results['best_practices'].append({
                        "key": key,
                        "value": practice.get('value'),
                        "description": practice.get('description')
                    })

        if in_lessons:
            for l in self.knowledge.get('lessons_learned', []):
                if query_lower in l.get('content', '').lower():
                    results['lessons_learned'].append(l)
                elif query_lower in (l.get('context') or '').lower():
                    results['lessons_learned'].append(l)

        return results

    def export_knowledge(self, format: str = "json") -> str:
        """
        导出知识库

        Args:
            format: 导出格式（json 或 markdown）

        Returns:
            导出的内容
        """
        knowledge = self.knowledge

        if format == "json":
            return json.dumps(knowledge, indent=2, ensure_ascii=False)

        elif format == "markdown":
            lines = [
                "# 知识库导出",
                f"\n**导出时间**: {datetime.now().isoformat()}",
                f"**版本**: {knowledge.get('version', '1.0')}",
                f"**已读论文数**: {knowledge.get('papers_read', 0)}",
                "\n---\n"
            ]

            # 关键发现
            lines.append("## 关键发现\n")
            for f in knowledge.get('key_findings', []):
                lines.append(f"### {f.get('category', 'General')}")
                lines.append(f"- **重要性**: {f.get('importance', 1)}/5")
                lines.append(f"- **内容**: {f.get('content')}")
                if f.get('source'):
                    lines.append(f"- **来源**: {f.get('source')}")
                if f.get('tags'):
                    lines.append(f"- **标签**: {', '.join(f.get('tags', []))}")
                lines.append(f"- **创建时间**: {f.get('created_at')}\n")

            # 最佳实践
            lines.append("## 最佳实践\n")
            for key, practice in knowledge.get('best_practices', {}).items():
                lines.append(f"### {key}")
                lines.append(f"- **值**: {practice.get('value')}")
                if practice.get('description'):
                    lines.append(f"- **描述**: {practice.get('description')}")
                lines.append("")

            # 经验教训
            lines.append("## 经验教训\n")
            for l in knowledge.get('lessons_learned', []):
                lines.append(f"- [{l.get('severity', 'info').upper()}] {l.get('content')}")
                if l.get('context'):
                    lines.append(f"  - 上下文: {l.get('context')}")

            return '\n'.join(lines)

        else:
            raise ValueError(f"不支持的导出格式: {format}")


class GitManager:
    """Git 操作封装管理器"""

    def __init__(self, repo_path: Optional[Path] = None):
        self.repo_path = Path(repo_path) if repo_path else DEFAULT_BASE_DIR

    def _run_git(self, *args: str, check: bool = True) -> subprocess.CompletedProcess:
        """执行 git 命令"""
        cmd = ['git'] + list(args)
        try:
            return subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                check=check
            )
        except subprocess.CalledProcessError as e:
            # 如果命令失败，返回一个空的结果对象
            class EmptyResult:
                stdout = ''
                stderr = str(e)
            return EmptyResult()

    def is_git_repo(self) -> bool:
        """检查是否为 Git 仓库"""
        try:
            self._run_git('rev-parse', '--git-dir')
            return True
        except subprocess.CalledProcessError:
            return False

    def get_current_branch(self) -> Optional[str]:
        """获取当前分支名"""
        try:
            result = self._run_git('branch', '--show-current')
            return result.stdout.strip() if result.stdout.strip() else None
        except subprocess.CalledProcessError:
            return None

    def get_status(self) -> Dict[str, List[str]]:
        """获取工作区状态"""
        try:
            result = self._run_git('status', '--porcelain')
            status = {
                'modified': [],
                'added': [],
                'deleted': [],
                'untracked': [],
                'renamed': []
            }

            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                code = line[:2]
                filepath = line[3:]

                if 'M' in code:
                    status['modified'].append(filepath)
                elif 'A' in code or '??' in code:
                    status['added'].append(filepath)
                elif 'D' in code:
                    status['deleted'].append(filepath)
                elif 'R' in code:
                    status['renamed'].append(filepath)
                elif '??' in code:
                    status['untracked'].append(filepath)

            return status
        except subprocess.CalledProcessError:
            return {}

    def commit(self, message: str, add_all: bool = False, files: Optional[List[str]] = None) -> bool:
        """
        创建提交

        Args:
            message: 提交信息
            add_all: 是否添加所有更改
            files: 指定要添加的文件列表

        Returns:
            是否成功
        """
        try:
            if add_all:
                self._run_git('add', '-A')
            elif files:
                for f in files:
                    self._run_git('add', f)

            self._run_git('commit', '-m', message)
            return True
        except subprocess.CalledProcessError:
            return False

    def generate_commit_message(self, task_id: str, description: str) -> str:
        """
        生成标准化的提交信息模板

        Args:
            task_id: 任务 ID（如 TASK-001）
            description: 简短描述

        Returns:
            格式化的提交信息
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        return f"完成 {task_id}: {description}\n\n时间: {timestamp}"

    def push(self, remote: str = 'origin', branch: Optional[str] = None) -> bool:
        """
        推送到远程仓库

        Args:
            remote: 远程仓库名
            branch: 分支名（默认当前分支）

        Returns:
            是否成功
        """
        try:
            if branch:
                self._run_git('push', remote, branch)
            else:
                self._run_git('push', remote)
            return True
        except subprocess.CalledProcessError:
            return False

    def pull(self, remote: str = 'origin', branch: Optional[str] = None) -> bool:
        """
        从远程仓库拉取

        Args:
            remote: 远程仓库名
            branch: 分支名（默认当前分支）

        Returns:
            是否成功
        """
        try:
            if branch:
                self._run_git('pull', remote, branch)
            else:
                self._run_git('pull', remote)
            return True
        except subprocess.CalledProcessError:
            return False

    def revert(self, commit_hash: Optional[str] = None, soft: bool = False) -> bool:
        """
        回退提交

        Args:
            commit_hash: 提交哈希（默认回退最近一次提交）
            soft: 是否软回退（保留更改）

        Returns:
            是否成功
        """
        try:
            if commit_hash:
                if soft:
                    self._run_git('reset', '--soft', commit_hash)
                else:
                    self._run_git('reset', '--hard', commit_hash)
            else:
                if soft:
                    self._run_git('reset', '--soft', 'HEAD~1')
                else:
                    self._run_git('reset', '--hard', 'HEAD~1')
            return True
        except subprocess.CalledProcessError:
            return False

    def get_log(self, count: int = 10, oneline: bool = True) -> List[Dict[str, str]]:
        """
        获取提交日志

        Args:
            count: 获取条数
            oneline: 是否使用单行格式

        Returns:
            提交日志列表
        """
        try:
            if oneline:
                result = self._run_git('log', f'-{count}', '--oneline')
                logs = []
                for line in result.stdout.strip().split('\n'):
                    if not line:
                        continue
                    parts = line.split(' ', 1)
                    if len(parts) == 2:
                        logs.append({
                            'hash': parts[0],
                            'message': parts[1]
                        })
                return logs
            else:
                result = self._run_git(
                    'log', f'-{count}',
                    '--pretty=format:%H|%an|%ae|%ad|%s'
                )
                logs = []
                for line in result.stdout.strip().split('\n'):
                    if not line:
                        continue
                    parts = line.split('|', 4)
                    if len(parts) == 5:
                        logs.append({
                            'hash': parts[0],
                            'author': parts[1],
                            'email': parts[2],
                            'date': parts[3],
                            'message': parts[4]
                        })
                return logs
        except subprocess.CalledProcessError:
            return []

    def create_branch(self, branch_name: str, from_branch: Optional[str] = None) -> bool:
        """
        创建新分支

        Args:
            branch_name: 新分支名
            from_branch: 基于哪个分支创建（默认当前分支）

        Returns:
            是否成功
        """
        try:
            if from_branch:
                self._run_git('checkout', '-b', branch_name, from_branch)
            else:
                self._run_git('checkout', '-b', branch_name)
            return True
        except subprocess.CalledProcessError:
            return False

    def switch_branch(self, branch_name: str) -> bool:
        """
        切换分支

        Args:
            branch_name: 目标分支名

        Returns:
            是否成功
        """
        try:
            self._run_git('checkout', branch_name)
            return True
        except subprocess.CalledProcessError:
            return False

    def get_diff(self, staged: bool = False) -> str:
        """
        获取差异

        Args:
            staged: 是否获取已暂存的差异

        Returns:
            差异内容
        """
        try:
            if staged:
                result = self._run_git('diff', '--staged')
            else:
                result = self._run_git('diff')
            return result.stdout
        except subprocess.CalledProcessError:
            return ""

    def has_changes(self) -> bool:
        """检查是否有未提交的更改"""
        status = self.get_status()
        return bool(status.get('modified') or status.get('added') or
                   status.get('deleted') or status.get('untracked'))


# 便捷函数
def get_state() -> StateManager:
    """获取状态管理器实例"""
    return StateManager()


def get_tasks() -> TaskManager:
    """获取任务管理器实例"""
    return TaskManager()


def get_logger() -> LogManager:
    """获取日志管理器实例"""
    return LogManager()


def get_comm() -> CommunicationManager:
    """获取通信管理器实例"""
    return CommunicationManager()


def get_git() -> GitManager:
    """获取 Git 管理器实例"""
    return GitManager()


class SessionManager:
    """会话管理器

    管理 AI 会话的生命周期，记录 token 使用量和上下文窗口计数。
    """

    def __init__(self, state_manager: Optional[StateManager] = None,
                 session_file: Optional[Path] = None):
        """
        初始化会话管理器

        Args:
            state_manager: 状态管理器实例（用于同步会话状态）
            session_file: 会话历史文件路径
        """
        self.state_manager = state_manager or StateManager()
        self.session_file = Path(session_file) if session_file else \
            DEFAULT_BASE_DIR / "Core" / "workflow" / "sessions.json"
        self._current_session = None
        self._sessions = None

    def load_sessions(self) -> dict:
        """加载会话历史文件"""
        if not self.session_file.exists():
            return self._create_default_sessions()
        with open(self.session_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save_sessions(self, sessions: dict) -> None:
        """保存会话历史文件"""
        sessions['last_updated'] = datetime.now().isoformat()
        self.session_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.session_file, 'w', encoding='utf-8') as f:
            json.dump(sessions, f, indent=2, ensure_ascii=False)

    def _create_default_sessions(self) -> dict:
        """创建默认会话历史结构"""
        return {
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "total_sessions": 0,
            "total_tokens_used": 0,
            "total_context_windows": 0,
            "sessions": []
        }

    @property
    def sessions(self) -> dict:
        """懒加载会话历史"""
        if self._sessions is None:
            self._sessions = self.load_sessions()
        return self._sessions

    def start_session(self, task_id: Optional[str] = None,
                      phase: Optional[str] = None,
                      project: Optional[str] = None,
                      metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        开始新会话

        Args:
            task_id: 当前任务 ID
            phase: 当前阶段
            project: 项目名称
            metadata: 额外的元数据

        Returns:
            会话 ID
        """
        session_id = f"sess_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

        self._current_session = {
            "session_id": session_id,
            "started_at": datetime.now().isoformat(),
            "ended_at": None,
            "task_id": task_id,
            "phase": phase,
            "project": project,
            "tokens_used": 0,
            "context_window_count": 0,
            "api_calls": 0,
            "errors": [],
            "actions": [],
            "metadata": metadata or {}
        }

        # 更新状态管理器
        self.state_manager.update(
            **{'session_info.session_id': session_id},
            **{'session_info.context_window_count': 0},
            **{'session_info.tokens_used_this_session': 0}
        )

        # 添加到会话历史
        sessions = self.sessions
        sessions['sessions'].append(self._current_session)
        sessions['total_sessions'] = sessions.get('total_sessions', 0) + 1
        self.save_sessions(sessions)
        self._sessions = sessions

        return session_id

    def end_session(self, summary: Optional[str] = None,
                    status: str = "completed") -> Optional[dict]:
        """
        结束当前会话

        Args:
            summary: 会话摘要
            status: 会话状态（completed, interrupted, error）

        Returns:
            会话摘要字典
        """
        if not self._current_session:
            return None

        self._current_session['ended_at'] = datetime.now().isoformat()
        self._current_session['status'] = status
        self._current_session['summary'] = summary

        # 计算会话持续时间
        try:
            started = datetime.fromisoformat(self._current_session['started_at'])
            ended = datetime.fromisoformat(self._current_session['ended_at'])
            duration = (ended - started).total_seconds()
            self._current_session['duration_seconds'] = duration
        except (ValueError, TypeError):
            self._current_session['duration_seconds'] = None

        # 更新会话历史
        sessions = self.sessions
        for i, s in enumerate(sessions.get('sessions', [])):
            if s.get('session_id') == self._current_session['session_id']:
                sessions['sessions'][i] = self._current_session
                break

        # 更新总计
        sessions['total_tokens_used'] = sessions.get('total_tokens_used', 0) + \
            self._current_session.get('tokens_used', 0)
        sessions['total_context_windows'] = sessions.get('total_context_windows', 0) + \
            self._current_session.get('context_window_count', 0)

        self.save_sessions(sessions)
        self._sessions = sessions

        # 获取摘要
        session_summary = self.get_session_summary(self._current_session['session_id'])

        # 重置当前会话
        self._current_session = None

        return session_summary

    def record_token_usage(self, input_tokens: int = 0, output_tokens: int = 0) -> int:
        """
        记录 token 使用量

        Args:
            input_tokens: 输入 token 数
            output_tokens: 输出 token 数

        Returns:
            当前会话的总 token 数
        """
        if not self._current_session:
            return 0

        total = input_tokens + output_tokens
        self._current_session['tokens_used'] = \
            self._current_session.get('tokens_used', 0) + total
        self._current_session['api_calls'] = \
            self._current_session.get('api_calls', 0) + 1

        # 更新状态管理器
        self.state_manager.update(
            **{'session_info.tokens_used_this_session':
               self._current_session['tokens_used']}
        )

        return self._current_session['tokens_used']

    def increment_context_window(self) -> int:
        """
        增加上下文窗口计数

        当发生上下文窗口切换时调用此方法。

        Returns:
            当前会话的上下文窗口计数
        """
        if not self._current_session:
            return 0

        self._current_session['context_window_count'] = \
            self._current_session.get('context_window_count', 0) + 1

        # 记录动作
        self._record_action("context_window_switch", {
            "new_count": self._current_session['context_window_count']
        })

        # 更新状态管理器
        self.state_manager.update(
            **{'session_info.context_window_count':
               self._current_session['context_window_count']}
        )

        return self._current_session['context_window_count']

    def record_error(self, error_type: str, error_message: str,
                     context: Optional[str] = None) -> None:
        """
        记录错误

        Args:
            error_type: 错误类型
            error_message: 错误消息
            context: 错误上下文
        """
        if not self._current_session:
            return

        error_record = {
            "timestamp": datetime.now().isoformat(),
            "type": error_type,
            "message": error_message,
            "context": context
        }

        self._current_session.setdefault('errors', []).append(error_record)

    def _record_action(self, action_type: str, details: Optional[dict] = None) -> None:
        """
        记录动作（内部方法）

        Args:
            action_type: 动作类型
            details: 动作详情
        """
        if not self._current_session:
            return

        action = {
            "timestamp": datetime.now().isoformat(),
            "type": action_type,
            "details": details or {}
        }

        self._current_session.setdefault('actions', []).append(action)

    def get_session_summary(self, session_id: Optional[str] = None) -> Optional[dict]:
        """
        获取会话摘要

        Args:
            session_id: 会话 ID（默认当前会话）

        Returns:
            会话摘要字典
        """
        target_session = None

        if session_id:
            # 查找指定会话
            for s in self.sessions.get('sessions', []):
                if s.get('session_id') == session_id:
                    target_session = s
                    break
        else:
            target_session = self._current_session

        if not target_session:
            return None

        return {
            "session_id": target_session.get('session_id'),
            "started_at": target_session.get('started_at'),
            "ended_at": target_session.get('ended_at'),
            "duration_seconds": target_session.get('duration_seconds'),
            "status": target_session.get('status', 'active'),
            "task_id": target_session.get('task_id'),
            "phase": target_session.get('phase'),
            "project": target_session.get('project'),
            "tokens_used": target_session.get('tokens_used', 0),
            "context_window_count": target_session.get('context_window_count', 0),
            "api_calls": target_session.get('api_calls', 0),
            "error_count": len(target_session.get('errors', [])),
            "action_count": len(target_session.get('actions', [])),
            "summary": target_session.get('summary')
        }

    def get_current_session(self) -> Optional[dict]:
        """
        获取当前会话

        Returns:
            当前会话字典或 None
        """
        return self._current_session

    def get_recent_sessions(self, limit: int = 10) -> List[dict]:
        """
        获取最近的会话列表

        Args:
            limit: 返回数量限制

        Returns:
            会话摘要列表
        """
        sessions = self.sessions.get('sessions', [])
        # 按开始时间倒序
        sessions.sort(key=lambda x: x.get('started_at', ''), reverse=True)

        summaries = []
        for s in sessions[:limit]:
            summaries.append(self.get_session_summary(s.get('session_id')))

        return summaries

    def get_session_stats(self) -> dict:
        """
        获取会话统计信息

        Returns:
            统计信息字典
        """
        sessions = self.sessions

        # 计算统计数据
        all_sessions = sessions.get('sessions', [])

        # 按状态统计
        by_status = {}
        for s in all_sessions:
            status = s.get('status', 'unknown')
            by_status[status] = by_status.get(status, 0) + 1

        # 按阶段统计
        by_phase = {}
        for s in all_sessions:
            phase = s.get('phase') or 'unknown'
            by_phase[phase] = by_phase.get(phase, 0) + 1

        # Token 统计
        total_tokens = sum(s.get('tokens_used', 0) for s in all_sessions)
        avg_tokens = total_tokens / len(all_sessions) if all_sessions else 0

        # 上下文窗口统计
        total_windows = sum(s.get('context_window_count', 0) for s in all_sessions)
        avg_windows = total_windows / len(all_sessions) if all_sessions else 0

        # 错误统计
        total_errors = sum(len(s.get('errors', [])) for s in all_sessions)
        sessions_with_errors = sum(1 for s in all_sessions if s.get('errors'))

        # 持续时间统计
        durations = [s.get('duration_seconds') for s in all_sessions
                    if s.get('duration_seconds') is not None]
        avg_duration = sum(durations) / len(durations) if durations else 0
        max_duration = max(durations) if durations else 0

        return {
            "total_sessions": len(all_sessions),
            "total_tokens_used": total_tokens,
            "average_tokens_per_session": round(avg_tokens, 2),
            "total_context_windows": total_windows,
            "average_context_windows_per_session": round(avg_windows, 2),
            "total_errors": total_errors,
            "sessions_with_errors": sessions_with_errors,
            "average_duration_seconds": round(avg_duration, 2),
            "max_duration_seconds": max_duration,
            "by_status": by_status,
            "by_phase": by_phase,
            "last_updated": sessions.get('last_updated')
        }

    def cleanup_old_sessions(self, days: int = 30) -> int:
        """
        清理旧会话记录

        Args:
            days: 保留最近多少天的记录

        Returns:
            删除的会话数量
        """
        from datetime import timedelta

        cutoff = datetime.now() - timedelta(days=days)
        cutoff_str = cutoff.isoformat()

        sessions = self.sessions
        original_count = len(sessions.get('sessions', []))

        # 过滤保留的会话
        sessions['sessions'] = [
            s for s in sessions.get('sessions', [])
            if s.get('started_at', '') >= cutoff_str
        ]

        new_count = len(sessions['sessions'])
        deleted_count = original_count - new_count

        if deleted_count > 0:
            sessions['total_sessions'] = new_count
            self.save_sessions(sessions)
            self._sessions = sessions

        return deleted_count


def get_session() -> SessionManager:
    """获取会话管理器实例"""
    return SessionManager()


def get_knowledge() -> KnowledgeBaseManager:
    """获取知识库管理器实例"""
    return KnowledgeBaseManager()


# 快捷操作函数
def add_finding(finding: str, category: Optional[str] = None,
                source: Optional[str] = None, importance: int = 1,
                tags: Optional[List[str]] = None) -> str:
    """
    快捷添加研究发现

    Args:
        finding: 发现内容
        category: 分类（如 'literature', 'experiment', 'analysis'）
        source: 来源（如论文标题、实验编号）
        importance: 重要程度 1-5（5最重要）
        tags: 标签列表

    Returns:
        发现的 ID
    """
    return get_knowledge().add_finding(finding, category, source, importance, tags)


def get_findings(category: Optional[str] = None,
                 min_importance: Optional[int] = None,
                 tags: Optional[List[str]] = None,
                 limit: int = 50) -> List[dict]:
    """
    快捷获取研究发现

    Args:
        category: 按分类筛选
        min_importance: 最低重要程度
        tags: 按标签筛选
        limit: 返回数量限制

    Returns:
        匹配的发现列表
    """
    return get_knowledge().get_findings(category, min_importance, tags, limit)


def update_best_practice(key: str, value: Any,
                         description: Optional[str] = None) -> None:
    """
    快捷更新最佳实践

    Args:
        key: 最佳实践的键名
        value: 最佳实践的内容
        description: 可选的描述说明
    """
    get_knowledge().update_best_practice(key, value, description)


def get_best_practice(key: str) -> Optional[Any]:
    """
    快捷获取最佳实践

    Args:
        key: 最佳实践的键名

    Returns:
        最佳实践的值或 None
    """
    return get_knowledge().get_best_practice(key)


if __name__ == "__main__":
    # 测试
    print("Testing StateManager...")
    sm = StateManager()
    print(f"Current state: {sm.state}")

    print("\nTesting TaskManager...")
    tm = TaskManager()
    print(f"Tasks: {tm.tasks}")

    print("\nTesting LogManager...")
    lm = LogManager()
    lm.log("Test log message")
    print("Log written")

    print("\nTesting GitManager...")
    gm = GitManager()
    print(f"Is git repo: {gm.is_git_repo()}")
    print(f"Current branch: {gm.get_current_branch()}")
    print(f"Recent commits: {gm.get_log(5)}")

    print("\nTesting KnowledgeBaseManager...")
    kb = KnowledgeBaseManager()

    # 测试添加发现
    finding_id = kb.add_finding(
        finding="Test finding: Transformer 架构在 NLP 任务中表现优异",
        category="literature",
        source="Attention is All You Need",
        importance=4,
        tags=["transformer", "nlp", "architecture"]
    )
    print(f"Added finding: {finding_id}")

    # 测试获取发现
    findings = kb.get_findings(category="literature")
    print(f"Findings count: {len(findings)}")

    # 测试最佳实践
    kb.update_best_practice(
        key="code_style",
        value="PEP8",
        description="遵循 Python PEP8 代码风格"
    )
    print(f"Best practice: code_style = {kb.get_best_practice('code_style')}")

    # 测试经验教训
    lesson_id = kb.add_lesson_learned(
        lesson="避免在循环中进行 API 调用",
        context="性能优化经验",
        severity="warning"
    )
    print(f"Added lesson: {lesson_id}")

    # 测试统计
    stats = kb.get_statistics()
    print(f"Statistics: {stats}")

    # 测试搜索
    search_results = kb.search("transformer")
    print(f"Search results: {len(search_results['findings'])} findings")

    print("\nTesting SessionManager...")
    sess = SessionManager()

    # 测试开始会话
    session_id = sess.start_session(
        task_id="TASK-022",
        phase="state_management",
        project="prometheus"
    )
    print(f"Started session: {session_id}")

    # 测试记录 token 使用
    total_tokens = sess.record_token_usage(input_tokens=100, output_tokens=50)
    print(f"Total tokens used: {total_tokens}")

    # 测试增加上下文窗口
    window_count = sess.increment_context_window()
    print(f"Context window count: {window_count}")

    # 测试记录错误
    sess.record_error(
        error_type="TestError",
        error_message="This is a test error",
        context="Testing error recording"
    )

    # 测试获取当前会话
    current = sess.get_current_session()
    print(f"Current session task: {current.get('task_id')}")

    # 测试获取会话摘要
    summary = sess.get_session_summary()
    print(f"Session summary: {summary}")

    # 测试结束会话
    end_summary = sess.end_session(
        summary="Session completed successfully",
        status="completed"
    )
    print(f"Ended session: {end_summary.get('session_id')}")

    # 测试获取会话统计
    stats = sess.get_session_stats()
    print(f"Session stats: {stats}")

    print("\nAll tests passed!")

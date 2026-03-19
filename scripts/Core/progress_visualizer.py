#!/usr/bin/env python3
"""
进度可视化模块
===============

提供终端进度条和统计信息的可视化显示功能。
使用 rich 库实现美观的终端 UI。

功能:
- 进度条显示 (整体和分阶段)
- 统计面板
- 任务列表显示
- 实时状态更新
"""

import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# 尝试导入 rich 库
try:
    from rich.console import Console
    from rich.progress import (
        Progress, BarColumn, TextColumn, TimeElapsedColumn,
        MofNCompleteColumn, TaskProgressColumn
    )
    from rich.table import Table
    from rich.panel import Panel
    from rich.layout import Layout
    from rich.live import Live
    from rich.text import Text
    from rich.style import Style
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

# 添加 Core 目录到路径
sys.path.insert(0, str(Path(__file__).parent))
from progress import get_tasks, get_state


class ProgressVisualizer:
    """进度可视化器

    提供多种进度可视化方式:
    - 文本模式: 简单的文本进度条
    - Rich 模式: 美观的终端 UI (需要 rich 库)
    """

    def __init__(self, use_rich: bool = True):
        """初始化可视化器

        Args:
            use_rich: 是否使用 rich 库（如果可用）
        """
        self.tasks_manager = get_tasks()
        self.state_manager = get_state()
        self.use_rich = use_rich and RICH_AVAILABLE

        if self.use_rich:
            self.console = Console()

    def is_rich_available(self) -> bool:
        """检查 rich 库是否可用"""
        return self.use_rich

    def display_overall_progress(self) -> None:
        """显示整体进度"""
        summary = self.tasks_manager.get_progress_summary()

        if self.use_rich:
            self._display_overall_progress_rich(summary)
        else:
            self._display_overall_progress_text(summary)

    def _display_overall_progress_rich(self, summary: Dict) -> None:
        """使用 rich 显示整体进度"""
        total = summary['total_tasks']
        completed = summary['passed_tasks']
        percent = summary['progress_percent']

        # 创建进度条
        progress = Progress(
            TextColumn("[bold blue]整体进度", justify="right"),
            BarColumn(bar_width=50, complete_style="green", finished_style="bold green"),
            TaskProgressColumn(),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
        )

        task = progress.add_task("", total=total)
        progress.update(task, completed=completed)

        # 创建统计面板
        stats_text = Text()
        stats_text.append(f"总任务: {total}\n")
        stats_text.append(f"已完成: ", style="green")
        stats_text.append(f"{completed}\n")
        stats_text.append(f"待完成: ", style="yellow")
        stats_text.append(f"{summary['pending_tasks']}\n")
        stats_text.append(f"完成度: ", style="bold")
        stats_text.append(f"{percent}%")

        panel = Panel(
            stats_text,
            title="[bold]项目进度统计[/bold]",
            border_style="blue",
            padding=(1, 2)
        )

        self.console.print()
        self.console.print(panel)
        self.console.print()
        self.console.print(progress)
        self.console.print()

    def _display_overall_progress_text(self, summary: Dict) -> None:
        """使用纯文本显示整体进度"""
        total = summary['total_tasks']
        completed = summary['passed_tasks']
        percent = summary['progress_percent']

        # 创建简单的文本进度条 (使用 ASCII 兼容字符)
        bar_length = 40
        filled = int(bar_length * percent / 100)
        bar = "#" * filled + "-" * (bar_length - filled)

        print()
        print("=" * 60)
        print("  项目进度")
        print("=" * 60)
        print()
        print(f"  [{bar}] {percent}%")
        print()
        print(f"  总任务: {total}")
        print(f"  已完成: {completed}")
        print(f"  待完成: {summary['pending_tasks']}")
        print()

    def display_phase_progress(self) -> None:
        """显示各阶段进度"""
        summary = self.tasks_manager.get_progress_summary()
        state = self.state_manager.state

        if self.use_rich:
            self._display_phase_progress_rich(summary, state)
        else:
            self._display_phase_progress_text(summary, state)

    def _display_phase_progress_rich(self, summary: Dict, state: Dict) -> None:
        """使用 rich 显示各阶段进度"""
        current_phase = state.get('current_phase', '')

        # 创建表格
        table = Table(
            title="[bold]各阶段进度[/bold]",
            show_header=True,
            header_style="bold magenta",
            border_style="blue"
        )

        table.add_column("状态", style="cyan", width=4)
        table.add_column("阶段", style="white", width=30)
        table.add_column("进度", justify="right", width=10)
        table.add_column("进度条", width=25)
        table.add_column("完成度", justify="right", width=8)

        for phase_id, info in summary['phases'].items():
            # 状态图标
            if info['status'] == 'completed':
                status = "[green]✓[/green]"
            elif phase_id == current_phase:
                status = "[yellow]●[/yellow]"
            else:
                status = "[dim]○[/dim]"

            # 阶段名称
            name = info['name']
            if phase_id == current_phase:
                name = f"[bold yellow]{name}[/bold yellow]"

            # 进度文本
            progress_text = f"{info['passed']}/{info['total']}"

            # 进度条
            total = info['total']
            completed = info['passed']
            if total > 0:
                percent = int(completed / total * 100)
            else:
                percent = 0

            bar_length = 20
            filled = int(bar_length * percent / 100)
            bar = "[green]█[/green]" * filled + "[dim]░[/dim]" * (bar_length - filled)

            # 完成度
            percent_text = f"{percent}%"
            if percent == 100:
                percent_text = f"[green]{percent}%[/green]"
            elif percent > 0:
                percent_text = f"[yellow]{percent}%[/yellow]"

            table.add_row(status, name, progress_text, bar, percent_text)

        self.console.print()
        self.console.print(table)
        self.console.print()

    def _display_phase_progress_text(self, summary: Dict, state: Dict) -> None:
        """使用纯文本显示各阶段进度"""
        current_phase = state.get('current_phase', '')

        print("-" * 60)
        print("  各阶段进度")
        print("-" * 60)
        print()

        for phase_id, info in summary['phases'].items():
            # 状态图标
            if info['status'] == 'completed':
                status = "[✓]"
            elif phase_id == current_phase:
                status = "[●]"
            else:
                status = "[ ]"

            # 进度条
            total = info['total']
            completed = info['passed']
            if total > 0:
                percent = int(completed / total * 100)
            else:
                percent = 0

            bar_length = 20
            filled = int(bar_length * percent / 100)
            bar = "#" * filled + "-" * (bar_length - filled)

            current_marker = " <-- 当前" if phase_id == current_phase else ""
            print(f"  {status} {info['name']}")
            print(f"      [{bar}] {completed}/{total} ({percent}%){current_marker}")

        print()

    def display_task_list(self, phase_id: Optional[str] = None,
                          show_completed: bool = False) -> None:
        """显示任务列表

        Args:
            phase_id: 指定阶段 ID，为 None 则显示所有任务
            show_completed: 是否显示已完成的任务
        """
        tasks_data = self.tasks_manager.tasks

        if self.use_rich:
            self._display_task_list_rich(tasks_data, phase_id, show_completed)
        else:
            self._display_task_list_text(tasks_data, phase_id, show_completed)

    def _display_task_list_rich(self, tasks_data: Dict,
                                 phase_id: Optional[str],
                                 show_completed: bool) -> None:
        """使用 rich 显示任务列表"""
        state = self.state_manager.state
        current_task = state.get('current_task', '')

        table = Table(
            title="[bold]任务列表[/bold]",
            show_header=True,
            header_style="bold magenta",
            border_style="blue"
        )

        table.add_column("状态", width=4)
        table.add_column("任务 ID", style="cyan", width=12)
        table.add_column("描述", width=40)
        table.add_column("尝试", justify="right", width=6)

        for phase in tasks_data.get('phases', []):
            pid = phase.get('phase_id', '')

            # 过滤阶段
            if phase_id and pid != phase_id:
                continue

            # 添加阶段标题
            table.add_row(
                "", f"[bold]{phase.get('phase_name', pid)}[/bold]", "", ""
            )

            for task in phase.get('tasks', []):
                task_id = task.get('task_id', '')
                passed = task.get('passes', False)
                attempts = task.get('attempts', 0)

                # 跳过已完成的任务
                if passed and not show_completed:
                    continue

                # 状态图标
                if passed:
                    status = "[green]✓[/green]"
                elif task_id == current_task:
                    status = "[yellow]●[/yellow]"
                else:
                    status = "[dim]○[/dim]"

                # 描述
                desc = task.get('description', '')[:38]
                if task_id == current_task:
                    desc = f"[bold yellow]{desc}[/bold yellow]"

                # 尝试次数
                attempts_text = str(attempts) if attempts > 0 else "-"
                if attempts >= 3:
                    attempts_text = f"[red]{attempts}[/red]"
                elif attempts >= 1:
                    attempts_text = f"[yellow]{attempts}[/yellow]"

                table.add_row(status, task_id, desc, attempts_text)

        self.console.print()
        self.console.print(table)
        self.console.print()

    def _display_task_list_text(self, tasks_data: Dict,
                                 phase_id: Optional[str],
                                 show_completed: bool) -> None:
        """使用纯文本显示任务列表"""
        state = self.state_manager.state
        current_task = state.get('current_task', '')

        print("-" * 60)
        print("  任务列表")
        print("-" * 60)
        print()

        for phase in tasks_data.get('phases', []):
            pid = phase.get('phase_id', '')

            # 过滤阶段
            if phase_id and pid != phase_id:
                continue

            print(f"  {phase.get('phase_name', pid)}")

            for task in phase.get('tasks', []):
                task_id = task.get('task_id', '')
                passed = task.get('passes', False)
                attempts = task.get('attempts', 0)

                # 跳过已完成的任务
                if passed and not show_completed:
                    continue

                # 状态图标
                if passed:
                    status = "[✓]"
                elif task_id == current_task:
                    status = "[●]"
                else:
                    status = "[ ]"

                desc = task.get('description', '')
                current_marker = " <-- 当前" if task_id == current_task else ""

                print(f"    {status} {task_id}: {desc}{current_marker}")

            print()

    def display_status_dashboard(self) -> None:
        """显示完整的状态仪表板"""
        state = self.state_manager.state
        summary = self.tasks_manager.get_progress_summary()

        if self.use_rich:
            self._display_dashboard_rich(state, summary)
        else:
            self._display_dashboard_text(state, summary)

    def _display_dashboard_rich(self, state: Dict, summary: Dict) -> None:
        """使用 rich 显示完整仪表板"""
        # 清屏
        self.console.clear()

        # 标题
        title = Text()
        title.append("Project Prometheus", style="bold blue")
        title.append(" - ", style="dim")
        title.append("系统状态", style="white")

        self.console.print(Panel(title, border_style="blue"))
        self.console.print()

        # 项目信息
        info_table = Table(show_header=False, box=None, padding=(0, 2))
        info_table.add_column("Key", style="cyan")
        info_table.add_column("Value", style="white")

        info_table.add_row("项目名称", str(state.get('current_project', 'N/A')))
        info_table.add_row("当前阶段", str(state.get('current_phase', 'N/A')))
        info_table.add_row("当前任务", str(state.get('current_task', 'N/A')))
        info_table.add_row("系统状态", str(state.get('status', 'N/A')))
        info_table.add_row("最后更新", str(state.get('last_updated', 'N/A')))

        self.console.print(Panel(info_table, title="[bold]项目信息[/bold]", border_style="green"))
        self.console.print()

        # 进度
        self._display_overall_progress_rich(summary)

        # 阶段进度
        self._display_phase_progress_rich(summary, state)

        # 知识库统计
        kb = state.get('knowledge_base', {})
        kb_text = Text()
        kb_text.append(f"论文阅读: {kb.get('papers_read', 0)} 篇\n")
        kb_text.append(f"关键发现: {len(kb.get('key_findings', []))} 条\n")
        kb_text.append(f"最佳实践: {len(kb.get('best_practices', {}))} 条")

        self.console.print(Panel(kb_text, title="[bold]知识库[/bold]", border_style="yellow"))
        self.console.print()

    def _display_dashboard_text(self, state: Dict, summary: Dict) -> None:
        """使用纯文本显示完整仪表板"""
        print("\n" + "=" * 60)
        print("  Project Prometheus - 系统状态")
        print("=" * 60)
        print()

        # 项目信息
        print("-" * 40)
        print("  项目信息")
        print("-" * 40)
        print(f"  项目名称: {state.get('current_project', 'N/A')}")
        print(f"  当前阶段: {state.get('current_phase', 'N/A')}")
        print(f"  当前任务: {state.get('current_task', 'N/A')}")
        print(f"  系统状态: {state.get('status', 'N/A')}")
        print(f"  最后更新: {state.get('last_updated', 'N/A')}")
        print()

        # 进度
        self._display_overall_progress_text(summary)

        # 阶段进度
        self._display_phase_progress_text(summary, state)

        # 知识库统计
        kb = state.get('knowledge_base', {})
        print("-" * 40)
        print("  知识库")
        print("-" * 40)
        print(f"  论文阅读: {kb.get('papers_read', 0)} 篇")
        print(f"  关键发现: {len(kb.get('key_findings', []))} 条")
        print(f"  最佳实践: {len(kb.get('best_practices', {}))} 条")
        print()

    def create_progress_bar(self, total: int, description: str = "") -> Any:
        """创建一个进度条对象用于迭代

        Args:
            total: 总任务数
            description: 进度条描述

        Returns:
            Progress 对象或 None
        """
        if not self.use_rich:
            return None

        progress = Progress(
            TextColumn(f"[bold blue]{description}"[:30], justify="right"),
            BarColumn(bar_width=40),
            TaskProgressColumn(),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            console=self.console
        )

        return progress

    def print_summary(self) -> None:
        """打印进度摘要（简短版）"""
        summary = self.tasks_manager.get_progress_summary()

        if self.use_rich:
            text = Text()
            text.append("进度: ")
            text.append(f"{summary['passed_tasks']}/{summary['total_tasks']}", style="bold cyan")
            text.append(" (")
            text.append(f"{summary['progress_percent']}%", style="bold green")
            text.append(")")
            self.console.print(text)
        else:
            print(f"进度: {summary['passed_tasks']}/{summary['total_tasks']} ({summary['progress_percent']}%)")

    def print_message(self, message: str, style: str = "info") -> None:
        """打印带样式的消息

        Args:
            message: 消息内容
            style: 样式类型 (info, success, warning, error)
        """
        if self.use_rich:
            style_map = {
                "info": "blue",
                "success": "green",
                "warning": "yellow",
                "error": "red bold"
            }
            text = Text(message, style=style_map.get(style, "white"))
            self.console.print(text)
        else:
            prefix_map = {
                "info": "[INFO]",
                "success": "[OK]",
                "warning": "[WARN]",
                "error": "[ERROR]"
            }
            print(f"{prefix_map.get(style, '[INFO]')} {message}")


# 全局实例
_visualizer: Optional[ProgressVisualizer] = None


def get_visualizer(use_rich: bool = True) -> ProgressVisualizer:
    """获取全局可视化器实例

    Args:
        use_rich: 是否使用 rich 库
    """
    global _visualizer
    if _visualizer is None:
        _visualizer = ProgressVisualizer(use_rich=use_rich)
    return _visualizer


def display_progress() -> None:
    """快捷函数：显示完整进度"""
    viz = get_visualizer()
    viz.display_overall_progress()
    viz.display_phase_progress()


def display_dashboard() -> None:
    """快捷函数：显示完整仪表板"""
    viz = get_visualizer()
    viz.display_status_dashboard()


def print_progress_summary() -> None:
    """快捷函数：打印进度摘要"""
    viz = get_visualizer()
    viz.print_summary()


# 命令行接口
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="进度可视化工具")
    parser.add_argument('--dashboard', action='store_true', help='显示完整仪表板')
    parser.add_argument('--progress', action='store_true', help='显示进度条')
    parser.add_argument('--phases', action='store_true', help='显示各阶段进度')
    parser.add_argument('--tasks', action='store_true', help='显示任务列表')
    parser.add_argument('--all', action='store_true', help='显示所有信息')
    parser.add_argument('--phase', type=str, help='指定阶段 ID')
    parser.add_argument('--no-rich', action='store_true', help='不使用 rich 库')

    args = parser.parse_args()

    viz = ProgressVisualizer(use_rich=not args.no_rich)

    if not viz.is_rich_available() and not args.no_rich:
        print("提示: rich 库未安装，使用简单文本模式")
        print("      使用 'pip install rich' 安装 rich 库以获得更好的显示效果")
        print()

    if args.dashboard:
        viz.display_status_dashboard()
    elif args.progress:
        viz.display_overall_progress()
    elif args.phases:
        viz.display_phase_progress()
    elif args.tasks:
        viz.display_task_list(phase_id=args.phase, show_completed=True)
    elif args.all:
        viz.display_status_dashboard()
        viz.display_task_list(phase_id=args.phase, show_completed=True)
    else:
        # 默认显示进度
        viz.display_overall_progress()
        viz.display_phase_progress()

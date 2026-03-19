#!/usr/bin/env python3
"""
任务选择器模块
==============

提供交互式任务选择功能，支持终端菜单和键盘导航。

Usage:
    from task_selector import TaskSelector, get_task_selector

    selector = get_task_selector()
    selected = selector.run()
"""

import json
import os
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable

# 跨平台键盘输入支持
try:
    # Windows
    import msvcrt
    PLATFORM = "windows"
except ImportError:
    # Unix/Linux/macOS
    import tty
    import termios
    PLATFORM = "unix"


class TaskSelector:
    """交互式任务选择器

    提供终端菜单界面，允许用户通过键盘选择待执行的任务。

    Attributes:
        tasks_file: 任务清单文件路径
        page_size: 每页显示的任务数量
    """

    def __init__(self, tasks_file: Optional[Path] = None, page_size: int = 10):
        """初始化任务选择器

        Args:
            tasks_file: 任务清单文件路径，默认为 Projects/current/research_tasks.json
            page_size: 每页显示的任务数量
        """
        base_dir = Path(__file__).parent.parent
        self.tasks_file = tasks_file or (base_dir / "Projects" / "current" / "research_tasks.json")
        self.page_size = page_size

        # 内部状态
        self.tasks_data: Dict[str, Any] = {}
        self.flat_tasks: List[Dict[str, Any]] = []
        self.current_index: int = 0
        self.current_page: int = 0
        self.selected_tasks: List[str] = []
        self.multi_select: bool = False
        self.running: bool = False

        # 原始终端设置（Unix）
        self._original_termios = None

    def _load_tasks(self) -> bool:
        """加载任务数据

        Returns:
            是否成功加载
        """
        if not self.tasks_file.exists():
            print(f"错误: 任务文件不存在: {self.tasks_file}")
            return False

        try:
            with open(self.tasks_file, 'r', encoding='utf-8') as f:
                self.tasks_data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"错误: 任务文件格式错误: {e}")
            return False
        except Exception as e:
            print(f"错误: 无法读取任务文件: {e}")
            return False

        # 展平任务列表
        self.flat_tasks = []
        phases = self.tasks_data.get("phases", [])

        for phase in phases:
            phase_id = phase.get("phase_id", "unknown")
            phase_name = phase.get("phase_name", phase_id)

            for task in phase.get("tasks", []):
                task_id = task.get("task_id", "unknown")
                task_desc = task.get("description", "无描述")
                task_status = task.get("passes", False)
                requires_approval = task.get("requires_human_approval", False)

                self.flat_tasks.append({
                    "task_id": task_id,
                    "description": task_desc,
                    "phase_id": phase_id,
                    "phase_name": phase_name,
                    "passes": task_status,
                    "requires_approval": requires_approval,
                    "attempts": task.get("attempts", 0),
                    "last_error": task.get("last_error")
                })

        return True

    def _get_pending_tasks(self) -> List[Dict[str, Any]]:
        """获取待完成任务列表

        Returns:
            待完成任务列表
        """
        return [t for t in self.flat_tasks if not t["passes"]]

    def _get_terminal_size(self) -> tuple:
        """获取终端大小

        Returns:
            (行数, 列数)
        """
        try:
            size = os.get_terminal_size()
            return (size.lines, size.columns)
        except Exception:
            return (24, 80)  # 默认大小

    def _clear_screen(self):
        """清屏"""
        os.system('cls' if PLATFORM == "windows" else 'clear')

    def _move_cursor(self, row: int, col: int):
        """移动光标到指定位置"""
        print(f"\033[{row};{col}H", end="")

    def _hide_cursor(self):
        """隐藏光标"""
        print("\033[?25l", end="")

    def _show_cursor(self):
        """显示光标"""
        print("\033[?25h", end="")

    def _set_terminal_raw(self):
        """设置终端为原始模式（Unix）"""
        if PLATFORM == "unix":
            self._original_termios = termios.tcgetattr(sys.stdin)
            tty.setraw(sys.stdin)

    def _restore_terminal(self):
        """恢复终端设置（Unix）"""
        if PLATFORM == "unix" and self._original_termios:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self._original_termios)

    def _get_key(self) -> str:
        """获取键盘输入

        Returns:
            按键名称
        """
        if PLATFORM == "windows":
            ch = msvcrt.getch()
            if ch == b'\xe0':  # 方向键前缀
                ch = msvcrt.getch()
                if ch == b'H':
                    return 'UP'
                elif ch == b'P':
                    return 'DOWN'
                elif ch == b'K':
                    return 'LEFT'
                elif ch == b'M':
                    return 'RIGHT'
            elif ch == b'\r':
                return 'ENTER'
            elif ch == b' ':
                return 'SPACE'
            elif ch == b'q' or ch == b'Q':
                return 'QUIT'
            elif ch == b'a' or ch == b'A':
                return 'SELECT_ALL'
            elif ch == b'n' or ch == b'N':
                return 'NEXT_PAGE'
            elif ch == b'p' or ch == b'P':
                return 'PREV_PAGE'
            return ch.decode('utf-8', errors='ignore')
        else:
            ch = sys.stdin.read(1)
            if ch == '\x1b':  # ESC 序列
                ch2 = sys.stdin.read(1)
                if ch2 == '[':
                    ch3 = sys.stdin.read(1)
                    if ch3 == 'A':
                        return 'UP'
                    elif ch3 == 'B':
                        return 'DOWN'
                    elif ch3 == 'C':
                        return 'RIGHT'
                    elif ch3 == 'D':
                        return 'LEFT'
                return 'ESC'
            elif ch == '\r' or ch == '\n':
                return 'ENTER'
            elif ch == ' ':
                return 'SPACE'
            elif ch == 'q' or ch == 'Q':
                return 'QUIT'
            elif ch == 'a' or ch == 'A':
                return 'SELECT_ALL'
            elif ch == 'n' or ch == 'N':
                return 'NEXT_PAGE'
            elif ch == 'p' or ch == 'P':
                return 'PREV_PAGE'
            return ch

    def _render_menu(self, tasks: List[Dict[str, Any]]):
        """渲染菜单

        Args:
            tasks: 要显示的任务列表
        """
        self._clear_screen()

        # 标题
        print("=" * 60)
        print("  Project Prometheus - 任务选择器")
        print("=" * 60)
        print()

        if not tasks:
            print("  没有待完成的任务！")
            print()
            print("  按 Q 退出...")
            return

        # 计算分页
        total_tasks = len(tasks)
        total_pages = (total_tasks + self.page_size - 1) // self.page_size

        start_idx = self.current_page * self.page_size
        end_idx = min(start_idx + self.page_size, total_tasks)
        page_tasks = tasks[start_idx:end_idx]

        # 显示模式
        mode_str = "[多选模式]" if self.multi_select else "[单选模式]"
        print(f"  {mode_str} 第 {self.current_page + 1}/{max(total_pages, 1)} 页 "
              f"(共 {total_tasks} 个任务)")
        print()
        print("-" * 60)

        # 显示任务列表
        for i, task in enumerate(page_tasks):
            global_idx = start_idx + i
            is_selected = task["task_id"] in self.selected_tasks
            is_current = global_idx == self.current_index

            # 选择标记
            if self.multi_select:
                checkbox = "[x]" if is_selected else "[ ]"
            else:
                checkbox = "→" if is_current else " "

            # 高亮当前行
            if is_current:
                print(f"  \033[7m{checkbox} {task['task_id']:<12} {task['description'][:40]}\033[0m")
            else:
                print(f"  {checkbox} {task['task_id']:<12} {task['description'][:40]}")

            # 显示阶段信息（如果是当前行）
            if is_current:
                print(f"      阶段: {task['phase_name']}")
                if task.get("requires_approval"):
                    print("      [需要人工审批]")
                print()

        print("-" * 60)
        print()

        # 操作提示
        print("  操作说明:")
        if self.multi_select:
            print("  ↑/↓  移动光标    SPACE  选择/取消    A  全选")
        else:
            print("  ↑/↓  移动光标    ENTER  选择")
        print("  N/P  翻页         Q  退出")
        print()

        # 显示已选任务
        if self.selected_tasks:
            print(f"  已选择 {len(self.selected_tasks)} 个任务: {', '.join(self.selected_tasks[:5])}",
                  end="")
            if len(self.selected_tasks) > 5:
                print("...")
            else:
                print()

    def run(self, multi_select: bool = False,
            filter_func: Optional[Callable[[Dict], bool]] = None) -> Optional[List[str]]:
        """运行任务选择器

        Args:
            multi_select: 是否允许多选
            filter_func: 任务过滤函数，返回 True 表示包含该任务

        Returns:
            选中的任务 ID 列表，如果取消选择则返回 None
        """
        # 加载任务
        if not self._load_tasks():
            return None

        # 获取待完成任务
        tasks = self._get_pending_tasks()

        # 应用过滤器
        if filter_func:
            tasks = [t for t in tasks if filter_func(t)]

        if not tasks:
            print("没有符合条件的待完成任务")
            return None

        # 初始化状态
        self.multi_select = multi_select
        self.current_index = 0
        self.current_page = 0
        self.selected_tasks = []
        self.running = True

        try:
            # 设置终端
            self._set_terminal_raw()
            self._hide_cursor()

            # 主循环
            while self.running:
                self._render_menu(tasks)
                sys.stdout.flush()

                # 处理输入
                try:
                    key = self._get_key()
                except Exception:
                    continue

                total_tasks = len(tasks)
                total_pages = (total_tasks + self.page_size - 1) // self.page_size
                current_task = tasks[self.current_index] if self.current_index < total_tasks else None

                if key == 'UP':
                    if self.current_index > 0:
                        self.current_index -= 1
                        # 更新页码
                        self.current_page = self.current_index // self.page_size

                elif key == 'DOWN':
                    if self.current_index < total_tasks - 1:
                        self.current_index += 1
                        self.current_page = self.current_index // self.page_size

                elif key == 'NEXT_PAGE' or key == 'RIGHT':
                    if self.current_page < total_pages - 1:
                        self.current_page += 1
                        self.current_index = self.current_page * self.page_size

                elif key == 'PREV_PAGE' or key == 'LEFT':
                    if self.current_page > 0:
                        self.current_page -= 1
                        self.current_index = self.current_page * self.page_size

                elif key == 'ENTER':
                    if current_task:
                        if self.multi_select:
                            # 多选模式下，Enter 确认选择
                            if self.selected_tasks:
                                self.running = False
                        else:
                            # 单选模式下，Enter 选择并退出
                            self.selected_tasks = [current_task["task_id"]]
                            self.running = False

                elif key == 'SPACE':
                    if self.multi_select and current_task:
                        task_id = current_task["task_id"]
                        if task_id in self.selected_tasks:
                            self.selected_tasks.remove(task_id)
                        else:
                            self.selected_tasks.append(task_id)

                elif key == 'SELECT_ALL':
                    if self.multi_select:
                        # 切换全选/取消全选
                        page_start = self.current_page * self.page_size
                        page_end = min(page_start + self.page_size, total_tasks)
                        page_tasks = tasks[page_start:page_end]
                        page_ids = [t["task_id"] for t in page_tasks]

                        # 检查当前页是否全部选中
                        all_selected = all(tid in self.selected_tasks for tid in page_ids)

                        if all_selected:
                            # 取消当前页选择
                            for tid in page_ids:
                                if tid in self.selected_tasks:
                                    self.selected_tasks.remove(tid)
                        else:
                            # 选中当前页
                            for tid in page_ids:
                                if tid not in self.selected_tasks:
                                    self.selected_tasks.append(tid)

                elif key == 'QUIT' or key == 'ESC':
                    self.selected_tasks = []
                    self.running = False

        finally:
            # 恢复终端
            self._show_cursor()
            self._restore_terminal()
            self._clear_screen()

        # 返回结果
        if self.selected_tasks:
            return self.selected_tasks
        return None

    def run_simple(self, multi_select: bool = False,
                   filter_func: Optional[Callable[[Dict], bool]] = None) -> Optional[List[str]]:
        """运行简化版任务选择器（无原始模式）

        使用简单的数字选择方式，适用于不支持原始模式的终端。

        Args:
            multi_select: 是否允许多选
            filter_func: 任务过滤函数

        Returns:
            选中的任务 ID 列表
        """
        # 加载任务
        if not self._load_tasks():
            return None

        # 获取待完成任务
        tasks = self._get_pending_tasks()

        # 应用过滤器
        if filter_func:
            tasks = [t for t in tasks if filter_func(t)]

        if not tasks:
            print("没有符合条件的待完成任务")
            return None

        while True:
            self._clear_screen()

            # 标题
            print("=" * 60)
            print("  Project Prometheus - 任务选择器 (简化版)")
            print("=" * 60)
            print()

            mode_str = "[多选模式]" if multi_select else "[单选模式]"
            print(f"  {mode_str} 共 {len(tasks)} 个待完成任务")
            print()
            print("-" * 60)

            # 显示任务列表
            for i, task in enumerate(tasks):
                is_selected = task["task_id"] in self.selected_tasks

                if multi_select:
                    checkbox = "[x]" if is_selected else "[ ]"
                    print(f"  {i+1:2}. {checkbox} {task['task_id']:<12} {task['description'][:40]}")
                else:
                    print(f"  {i+1:2}. {task['task_id']:<12} {task['description'][:40]}")

                # 如果任务数太多，只显示前 20 个
                if i >= 19 and len(tasks) > 20:
                    print(f"  ... 还有 {len(tasks) - 20} 个任务未显示")
                    break

            print("-" * 60)
            print()

            # 操作提示
            print("  输入编号选择任务")
            if multi_select:
                print("  输入多个编号（用空格分隔）进行多选")
                print("  输入 'done' 确认选择")
            print("  输入 'q' 退出")
            print()

            # 获取输入
            try:
                user_input = input("  请选择: ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                return None

            if user_input.lower() == 'q':
                return None

            if multi_select and user_input.lower() == 'done':
                if self.selected_tasks:
                    return self.selected_tasks
                print("  请先选择至少一个任务")
                continue

            # 解析选择
            try:
                if multi_select:
                    # 多选模式：解析多个编号
                    indices = [int(x) - 1 for x in user_input.split()]
                    for idx in indices:
                        if 0 <= idx < len(tasks):
                            task_id = tasks[idx]["task_id"]
                            if task_id in self.selected_tasks:
                                self.selected_tasks.remove(task_id)
                            else:
                                self.selected_tasks.append(task_id)
                else:
                    # 单选模式
                    idx = int(user_input) - 1
                    if 0 <= idx < len(tasks):
                        return [tasks[idx]["task_id"]]
                    print("  无效的编号，请重试")
            except ValueError:
                print("  无效的输入，请输入数字编号")

    def select_interactive(self, multi_select: bool = False,
                          filter_func: Optional[Callable[[Dict], bool]] = None,
                          force_simple: bool = False) -> Optional[List[str]]:
        """智能选择交互模式

        根据终端能力自动选择完整版或简化版界面。

        Args:
            multi_select: 是否允许多选
            filter_func: 任务过滤函数
            force_simple: 强制使用简化版

        Returns:
            选中的任务 ID 列表
        """
        # 检测是否支持原始模式
        supports_raw = True

        # Windows 上 msvcrt 可用
        # Unix 上需要 termios
        if PLATFORM == "unix":
            try:
                import termios
            except ImportError:
                supports_raw = False

        # 检测是否在管道或重定向中
        if not sys.stdin.isatty() or not sys.stdout.isatty():
            supports_raw = False

        if force_simple or not supports_raw:
            return self.run_simple(multi_select, filter_func)
        else:
            return self.run(multi_select, filter_func)


# 单例模式
_task_selector_instance: Optional[TaskSelector] = None


def get_task_selector() -> TaskSelector:
    """获取任务选择器实例

    Returns:
        TaskSelector 实例
    """
    global _task_selector_instance
    if _task_selector_instance is None:
        _task_selector_instance = TaskSelector()
    return _task_selector_instance


# 命令行入口
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Project Prometheus 任务选择器")
    parser.add_argument('--multi', '-m', action='store_true',
                       help='允许多选模式')
    parser.add_argument('--simple', '-s', action='store_true',
                       help='使用简化版界面')
    parser.add_argument('--phase', '-p', type=str,
                       help='只显示指定阶段的任务')

    args = parser.parse_args()

    selector = get_task_selector()

    # 阶段过滤
    filter_func = None
    if args.phase:
        filter_func = lambda t: args.phase in t["phase_id"]

    # 选择模式
    if args.simple:
        result = selector.run_simple(multi_select=args.multi, filter_func=filter_func)
    else:
        result = selector.select_interactive(multi_select=args.multi, filter_func=filter_func)

    if result:
        print()
        print("选中的任务:")
        for task_id in result:
            print(f"  - {task_id}")
    else:
        print()
        print("已取消选择")

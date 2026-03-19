#!/usr/bin/env python3
"""
Project Prometheus - 全自主科研智能体系统
==========================================

基于 Anthropic "Effective Harnesses for Long-Running Agents" 论文设计

Usage:
    python prometheus.py --init              # 初始化新项目
    python prometheus.py --status            # 查看系统状态
    python prometheus.py --run               # 运行科研执行智能体
    python prometheus.py --checkpoint        # 生成检查点报告
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# 添加 Core 目录到路径
sys.path.insert(0, str(Path(__file__).parent / "Core"))

from progress import (
    StateManager, TaskManager, LogManager, CommunicationManager,
    get_state, get_tasks, get_logger, get_comm, get_git, GitManager
)
from checkpoint_manager import CheckpointManager, get_checkpoint_manager
from export_manager import ExportManager, get_export_manager
from task_selector import TaskSelector, get_task_selector
from progress_visualizer import ProgressVisualizer, get_visualizer
from exception_handler import (
    install_global_exception_handler, uninstall_global_exception_handler,
    PrometheusError, TaskError, StateError, ConfigurationError,
    ExternalAPIError, ResourceError, SecurityError, ErrorContext,
    safe_execute, safe_execute_with_default
)


# 路径配置
BASE_DIR = Path(__file__).parent
PROMPTS_DIR = BASE_DIR / "Core" / "prompts"


class Prometheus:
    """Project Prometheus 主控制器"""

    def __init__(self):
        self.state = get_state()
        self.tasks = get_tasks()
        self.logger = get_logger()
        self.comm = get_comm()
        self.checkpoint_manager = get_checkpoint_manager()
        self.git_manager = get_git()
        self.export_manager = get_export_manager()
        self.task_selector = get_task_selector()
        self.visualizer = get_visualizer()

    def init_system(self, project_name: str, research_domain: str,
                    research_question: str) -> None:
        """初始化系统"""
        print("=" * 50)
        print("  Project Prometheus - 系统初始化")
        print("=" * 50)
        print()

        # 1. 创建目录结构
        print("[1/6] 创建目录结构...")
        self._create_directories()
        print("      [OK] 完成")

        # 2. 初始化状态文件
        print("[2/6] 初始化状态文件...")
        self._init_state(project_name)
        print("      [OK] 完成")

        # 3. 创建任务清单
        print("[3/6] 创建任务清单...")
        self._create_default_tasks(project_name, research_domain, research_question)
        print("      [OK] 完成")

        # 4. 创建 init.sh
        print("[4/6] 创建启动脚本...")
        self._ensure_init_script()
        print("      [OK] 完成")

        # 5. Git 初始化
        print("[5/6] Git 初始化...")
        self._init_git()
        print("      [OK] 完成")

        # 6. 生成就绪报告
        print("[6/6] 生成就绪报告...")
        self._generate_ready_report(project_name, research_domain)
        print("      [OK] 完成")

        print()
        print("=" * 50)
        print(f"  项目 '{project_name}' 初始化完成!")
        print("=" * 50)
        print()
        print("下一步:")
        print("  1. 编辑 Projects/{project_name}/research_tasks.json 添加具体任务")
        print("  2. 运行 'python prometheus.py --status' 查看状态")
        print("  3. 运行 'python automation/task_executor.py --project Projects/{project_name} --loop' 启动执行")

    def _create_directories(self) -> None:
        """创建目录结构"""
        dirs = [
            BASE_DIR / "Core" / "prompts",
            BASE_DIR / "Core" / "tools",
            BASE_DIR / "Projects",
            BASE_DIR / "Logs",
            BASE_DIR / "Communication" / "inbox",
            BASE_DIR / "Communication" / "outbox",
            BASE_DIR / "Archives",
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)

        # 创建空的 commands.txt
        commands_file = BASE_DIR / "Communication" / "inbox" / "commands.txt"
        if not commands_file.exists():
            commands_file.write_text("# 在此写入指令控制智能体\n", encoding='utf-8')

    def _init_state(self, project_name: str) -> None:
        """初始化状态文件"""
        state = {
            "version": "1.0",
            "last_updated": datetime.now().isoformat(),
            "current_project": project_name,
            "current_phase": "literature_review",
            "current_task": None,
            "session_info": {
                "session_id": f"init_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
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
        self.state.save(state)

    def _create_default_tasks(self, project_name: str,
                              research_domain: str,
                              research_question: str) -> None:
        """创建默认任务清单"""
        tasks = {
            "project_name": project_name,
            "created_at": datetime.now().isoformat(),
            "research_domain": research_domain,
            "research_question": research_question,
            "phases": [
                {
                    "phase_id": "literature_review",
                    "phase_name": "Phase 1: 深度文献调研",
                    "status": "pending",
                    "tasks": [
                        {
                            "task_id": "LIT-001",
                            "description": "广度搜索：抓取相关论文",
                            "steps": [
                                "确定搜索关键词",
                                "调用 Arxiv/Semantic Scholar API",
                                "存储到数据库",
                                "去重和排序"
                            ],
                            "passes": False,
                            "attempts": 0,
                            "last_error": None
                        },
                        {
                            "task_id": "LIT-002",
                            "description": "深度阅读：精读核心论文",
                            "steps": [
                                "筛选高引用论文",
                                "提取关键信息",
                                "总结方法论"
                            ],
                            "passes": False,
                            "attempts": 0,
                            "last_error": None
                        },
                        {
                            "task_id": "LIT-003",
                            "description": "聚类分析：识别研究主题",
                            "steps": [
                                "读取论文摘要",
                                "执行聚类算法",
                                "生成主题报告"
                            ],
                            "passes": False,
                            "attempts": 0,
                            "last_error": None
                        },
                        {
                            "task_id": "LIT-004",
                            "description": "Research Gap 分析",
                            "steps": [
                                "识别未解决问题",
                                "评估研究机会",
                                "生成 Gap 报告"
                            ],
                            "passes": False,
                            "attempts": 0,
                            "last_error": None
                        },
                        {
                            "task_id": "LIT-005",
                            "description": "Checkpoint A: 人类审批研究方向",
                            "steps": [
                                "生成审批请求报告",
                                "写入 Communication/outbox/",
                                "等待人类回复",
                                "记录选择结果"
                            ],
                            "passes": False,
                            "attempts": 0,
                            "last_error": None,
                            "requires_human_approval": True,
                            "approval_status": "pending"
                        }
                    ]
                },
                {
                    "phase_id": "hypothesis_design",
                    "phase_name": "Phase 2: 假设与实验设计",
                    "status": "pending",
                    "tasks": [
                        {
                            "task_id": "HYP-001",
                            "description": "形式化研究假设",
                            "steps": ["明确假设陈述", "定义变量", "确定预期结果"],
                            "passes": False,
                            "attempts": 0,
                            "last_error": None
                        },
                        {
                            "task_id": "HYP-002",
                            "description": "设计实验方案",
                            "steps": ["确定数据集", "设计评估指标", "选择 Baseline"],
                            "passes": False,
                            "attempts": 0,
                            "last_error": None
                        },
                        {
                            "task_id": "HYP-003",
                            "description": "设计消融实验",
                            "steps": ["识别关键组件", "设计消融方案"],
                            "passes": False,
                            "attempts": 0,
                            "last_error": None
                        },
                        {
                            "task_id": "HYP-004",
                            "description": "资源评估",
                            "steps": ["估算计算资源", "评估时间需求"],
                            "passes": False,
                            "attempts": 0,
                            "last_error": None
                        },
                        {
                            "task_id": "HYP-005",
                            "description": "Checkpoint B: 人类审批实验设计",
                            "steps": ["生成审批请求", "等待人类确认"],
                            "passes": False,
                            "attempts": 0,
                            "last_error": None,
                            "requires_human_approval": True,
                            "approval_status": "pending"
                        }
                    ]
                },
                {
                    "phase_id": "coding",
                    "phase_name": "Phase 3: 自动化编码",
                    "status": "pending",
                    "tasks": [
                        {"task_id": "COD-001", "description": "创建项目结构", "steps": ["创建目录", "初始化环境"], "passes": False, "attempts": 0, "last_error": None},
                        {"task_id": "COD-002", "description": "实现数据处理模块", "steps": ["数据加载", "预处理", "数据增强"], "passes": False, "attempts": 0, "last_error": None},
                        {"task_id": "COD-003", "description": "实现模型/算法", "steps": ["核心逻辑", "接口设计"], "passes": False, "attempts": 0, "last_error": None},
                        {"task_id": "COD-004", "description": "实现训练流程", "steps": ["训练循环", "检查点保存", "日志记录"], "passes": False, "attempts": 0, "last_error": None},
                        {"task_id": "COD-005", "description": "实现评估流程", "steps": ["评估指标", "结果可视化"], "passes": False, "attempts": 0, "last_error": None},
                        {"task_id": "COD-006", "description": "单元测试", "steps": ["编写测试", "运行测试"], "passes": False, "attempts": 0, "last_error": None}
                    ]
                },
                {
                    "phase_id": "execution",
                    "phase_name": "Phase 4: 执行与监控",
                    "status": "pending",
                    "tasks": [
                        {"task_id": "EXE-001", "description": "Sanity Check", "steps": ["小数据测试", "1 Epoch 运行"], "passes": False, "attempts": 0, "last_error": None},
                        {"task_id": "EXE-002", "description": "全量训练", "steps": ["主实验", "日志监控"], "passes": False, "attempts": 0, "last_error": None},
                        {"task_id": "EXE-003", "description": "消融实验", "steps": ["执行消融", "记录结果"], "passes": False, "attempts": 0, "last_error": None},
                        {"task_id": "EXE-004", "description": "Checkpoint C: 人类审批实验结果", "steps": ["生成报告", "等待审批"], "passes": False, "attempts": 0, "last_error": None, "requires_human_approval": True}
                    ]
                },
                {
                    "phase_id": "analysis",
                    "phase_name": "Phase 5: 数据分析",
                    "status": "pending",
                    "tasks": [
                        {"task_id": "ANA-001", "description": "数据整理", "steps": ["收集结果", "数据清洗"], "passes": False, "attempts": 0, "last_error": None},
                        {"task_id": "ANA-002", "description": "统计检验", "steps": ["显著性检验", "P-value 计算"], "passes": False, "attempts": 0, "last_error": None},
                        {"task_id": "ANA-003", "description": "可视化", "steps": ["生成图表", "PDF/SVG 导出"], "passes": False, "attempts": 0, "last_error": None},
                        {"task_id": "ANA-004", "description": "Checkpoint D: 人类审批分析结论", "steps": ["生成报告", "等待审批"], "passes": False, "attempts": 0, "last_error": None, "requires_human_approval": True}
                    ]
                },
                {
                    "phase_id": "writing",
                    "phase_name": "Phase 6: 论文撰写",
                    "status": "pending",
                    "tasks": [
                        {"task_id": "WRI-001", "description": "初始化 LaTeX", "steps": ["选择模板", "设置格式"], "passes": False, "attempts": 0, "last_error": None},
                        {"task_id": "WRI-002", "description": "撰写 Introduction", "steps": ["背景介绍", "贡献陈述"], "passes": False, "attempts": 0, "last_error": None},
                        {"task_id": "WRI-003", "description": "撰写 Related Work", "steps": ["文献综述", "对比分析"], "passes": False, "attempts": 0, "last_error": None},
                        {"task_id": "WRI-004", "description": "撰写 Method", "steps": ["方法描述", "算法伪代码"], "passes": False, "attempts": 0, "last_error": None},
                        {"task_id": "WRI-005", "description": "撰写 Experiments", "steps": ["实验设置", "结果展示"], "passes": False, "attempts": 0, "last_error": None},
                        {"task_id": "WRI-006", "description": "迭代润色", "steps": ["语言优化", "格式调整"], "passes": False, "attempts": 0, "last_error": None}
                    ]
                },
                {
                    "phase_id": "peer_review",
                    "phase_name": "Phase 7: 自我同行评审",
                    "status": "pending",
                    "tasks": [
                        {"task_id": "REV-001", "description": "模拟评审", "steps": ["Reviewer 1 意见", "Reviewer 2 意见", "Reviewer 3 意见"], "passes": False, "attempts": 0, "last_error": None},
                        {"task_id": "REV-002", "description": "综合评分", "steps": ["计算评分", "决定下一步"], "passes": False, "attempts": 0, "last_error": None}
                    ]
                }
            ],
            "ouroboros": {
                "completed_cycles": 0,
                "archived_projects": [],
                "knowledge_updates": []
            }
        }
        self.tasks.save(tasks)

    def _ensure_init_script(self) -> None:
        """确保 init.sh 存在"""
        init_script = BASE_DIR / "init.sh"
        if not init_script.exists():
            script_content = '''#!/bin/bash
# Project Prometheus 启动脚本

echo "Project Prometheus 环境检查..."
python3 --version || python --version
echo "环境就绪!"
'''
            init_script.write_text(script_content, encoding='utf-8')

    def _init_git(self) -> None:
        """初始化 Git 仓库"""
        git_dir = BASE_DIR / ".git"
        if not git_dir.exists():
            subprocess.run(["git", "init"], cwd=BASE_DIR, capture_output=True)
            subprocess.run(["git", "add", "."], cwd=BASE_DIR, capture_output=True)
            subprocess.run(
                ["git", "commit", "-m", "Initial commit: Project Prometheus 初始化"],
                cwd=BASE_DIR, capture_output=True
            )

    def _generate_ready_report(self, project_name: str, research_domain: str) -> None:
        """生成系统就绪报告"""
        report = f'''# Project Prometheus 系统就绪报告

## 项目信息
- **项目名称**: {project_name}
- **研究领域**: {research_domain}
- **创建时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## 任务统计
'''
        summary = self.tasks.get_progress_summary()
        for phase_id, info in summary['phases'].items():
            report += f"- {info['name']}: {info['total']} 个任务\n"

        report += f'''
- **总计**: {summary['total_tasks']} 个任务

## 目录结构
```
prometheus/
├── Core/
│   ├── prompts/          # Prompt 模板
│   ├── tools/            # 工具脚本
│   └── gep/              # 错误恢复
├── Projects/             # 项目区
├── Logs/                 # 日志
├── Communication/        # 人机交互
└── automation/           # 自动执行器
```

## 下一步
1. 运行 `python start_research.py --topic "研究主题"` 创建新项目
2. 运行 `python automation/task_executor.py --project Projects/{name} --loop` 启动执行
'''
        self.comm.send_report("system_ready.md", report)

    def show_status(self) -> None:
        """显示系统状态"""
        print("=" * 60)
        print("  Project Prometheus - 系统状态")
        print("=" * 60)
        print()

        # 状态信息
        state = self.state.state
        print(f"项目名称: {state.get('current_project', 'N/A')}")
        print(f"当前阶段: {state.get('current_phase', 'N/A')}")
        print(f"当前任务: {state.get('current_task', 'N/A')}")
        print(f"系统状态: {state.get('status', 'N/A')}")
        print(f"最后更新: {state.get('last_updated', 'N/A')}")
        print()

        # 进度信息
        summary = self.tasks.get_progress_summary()
        print("-" * 40)
        print("进度概览:")
        print("-" * 40)
        print(f"总任务数: {summary['total_tasks']}")
        print(f"已完成: {summary['passed_tasks']}")
        print(f"待完成: {summary['pending_tasks']}")
        print(f"完成度: {summary['progress_percent']}%")
        print()

        print("-" * 40)
        print("各阶段进度:")
        print("-" * 40)
        for phase_id, info in summary['phases'].items():
            status_icon = "[x]" if info['status'] == 'completed' else "[ ]"
            print(f"  {status_icon} {info['name']}: {info['passed']}/{info['total']}")
        print()

        # 检查待处理指令
        commands = self.comm.check_commands()
        if commands:
            print("-" * 40)
            print("待处理指令:")
            print("-" * 40)
            for cmd in commands:
                print(f"  → {cmd}")
            print()

        print("=" * 60)

    def show_visual_progress(self, mode: str = "dashboard") -> None:
        """显示可视化进度

        Args:
            mode: 显示模式 (dashboard, progress, phases, tasks, all)
        """
        # 检查 rich 库是否可用
        if not self.visualizer.is_rich_available():
            print("提示: rich 库未安装，使用简单文本模式")
            print("      使用 'pip install rich' 安装以获得更好的显示效果")
            print()

        if mode == "dashboard":
            self.visualizer.display_status_dashboard()
        elif mode == "progress":
            self.visualizer.display_overall_progress()
        elif mode == "phases":
            self.visualizer.display_phase_progress()
        elif mode == "tasks":
            self.visualizer.display_task_list(show_completed=True)
        elif mode == "all":
            self.visualizer.display_status_dashboard()
            self.visualizer.display_task_list(show_completed=True)
        else:
            # 默认显示进度
            self.visualizer.display_overall_progress()
            self.visualizer.display_phase_progress()

    def run_agent(self, mode: str = "research") -> None:
        """
        运行智能体
        
        强制执行以下启动流程：
        1. 确认工作目录
        2. 读取 state.json
        3. 读取 operational.log（最后 50 行）
        4. 检查 Git 状态
        5. 检查 Communication/inbox/commands.txt
        6. 加载 Prompt 文件
        """
        # ========================================
        # 强制启动流程
        # ========================================
        print("=" * 70)
        print("  Project Prometheus - 智能体启动流程")
        print("=" * 70)
        print()
        
        # 1. 确认工作目录
        print("[1/6] 确认工作目录...")
        print(f"      当前目录: {BASE_DIR}")
        if not BASE_DIR.exists():
            print("      ❌ 错误: 工作目录不存在")
            return
        print("      ✅ 工作目录正常")
        print()
        
        # 2. 读取 state.json
        print("[2/6] 读取系统状态...")
        state = self.state.state
        print(f"      当前阶段: {state.get('current_phase', 'N/A')}")
        print(f"      当前任务: {state.get('current_task', 'N/A')}")
        print(f"      系统状态: {state.get('status', 'N/A')}")
        print(f"      项目: {state.get('current_project', 'N/A')}")
        print("      ✅ 状态文件已加载")
        print()
        
        # 3. 读取 operational.log
        print("[3/6] 读取操作日志...")
        log_file = BASE_DIR / "Logs" / "operational.log"
        if log_file.exists():
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    recent = lines[-10:] if len(lines) > 10 else lines
                print(f"      最近 {len(recent)} 条记录:")
                for line in recent:
                    print(f"        {line.strip()[:80]}")
                print("      ✅ 操作日志已加载")
            except Exception as e:
                print(f"      ⚠️ 无法读取日志: {e}")
        else:
            print("      ⚠️ 操作日志文件不存在")
        print()
        
        # 4. 检查 Git 状态
        print("[4/6] 检查 Git 状态...")
        try:
            result = subprocess.run(
                ['git', 'status', '--short'],
                cwd=BASE_DIR,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                changes = result.stdout.strip()
                if changes:
                    print(f"      ⚠️ 有未提交的更改:")
                    for line in changes.split('\n')[:5]:
                        print(f"        {line}")
                else:
                    print("      ✅ 工作区干净")
            else:
                print("      ⚠️ Git 状态检查失败")
        except Exception as e:
            print(f"      ⚠️ 无法检查 Git 状态: {e}")
        print()
        
        # 5. 检查 commands.txt
        print("[5/6] 检查人类指令...")
        commands_file = BASE_DIR / "Communication" / "inbox" / "commands.txt"
        if commands_file.exists():
            try:
                with open(commands_file, 'r', encoding='utf-8') as f:
                    commands = f.read().strip()
                if commands and not commands.startswith('#'):
                    print(f"      ⚠️ 发现待处理指令:")
                    print(f"        {commands[:100]}")
                else:
                    print("      ✅ 无待处理指令")
            except Exception:
                print("      ⚠️ 无法读取指令文件")
        else:
            print("      ✅ 指令文件不存在（无待处理指令）")
        print()
        
        # 6. 加载 Prompt
        print("[6/6] 加载 Prompt...")
        if mode == "initializer":
            prompt_file = PROMPTS_DIR / "initializer_prompt.md"
        else:
            prompt_file = PROMPTS_DIR / "research_agent_prompt.md"

        if not prompt_file.exists():
            print(f"      ❌ 错误: 找不到 Prompt 文件: {prompt_file}")
            return
        
        print(f"      Prompt 文件: {prompt_file}")
        print("      ✅ Prompt 已加载")
        print()
        
        # ========================================
        # 显示启动摘要
        # ========================================
        print("=" * 70)
        print(f"  {'初始化智能体' if mode == 'initializer' else '科研执行智能体'} - 启动就绪")
        print("=" * 70)
        print()
        print("📋 启动摘要:")
        print(f"   - 模式: {mode}")
        print(f"   - 阶段: {state.get('current_phase', 'N/A')}")
        print(f"   - 任务: {state.get('current_task', 'N/A') or '无当前任务'}")
        print(f"   - 状态: {state.get('status', 'N/A')}")
        print()
        
        # 显示任务进度
        summary = self.tasks.get_progress_summary()
        print("📊 任务进度:")
        print(f"   - 总任务: {summary['total_tasks']}")
        print(f"   - 已完成: {summary['passed_tasks']}")
        print(f"   - 待完成: {summary['pending_tasks']}")
        print(f"   - 完成度: {summary['progress_percent']}%")
        print()
        
        print("=" * 70)
        print("  执行方式")
        print("=" * 70)
        print()
        print("方式 1: Claude Code CLI")
        print(f"  claude --prompt-file {prompt_file}")
        print()
        print("方式 2: 自动执行器")
        print("  python auto_run.py --ralph --gep")
        print()
        print("方式 3: Agent SDK 集成版")
        print("  python auto_run_v3.py --ralph --gep")
        print()
        
        # 显示 Prompt 预览
        content = prompt_file.read_text(encoding='utf-8')
        lines = content.split('\n')[:15]
        print("-" * 70)
        print("  Prompt 预览 (前 15 行):")
        print("-" * 70)
        for line in lines:
            print(f"  {line}")
        if len(content.split('\n')) > 15:
            print("  ...")
        print("-" * 70)
        print()

    def create_checkpoint(self) -> None:
        """创建检查点"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        checkpoint_file = BASE_DIR / "Communication" / "outbox" / f"checkpoint_{timestamp}.md"

        state = self.state.state
        summary = self.tasks.get_progress_summary()

        report = f'''# 检查点报告

## 基本信息
- 时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- 项目: {state.get('current_project', 'N/A')}
- 阶段: {state.get('current_phase', 'N/A')}
- 任务: {state.get('current_task', 'N/A')}

## 进度
- 总任务: {summary['total_tasks']}
- 已完成: {summary['passed_tasks']}
- 待完成: {summary['pending_tasks']}
- 完成度: {summary['progress_percent']}%

## 知识库
- 论文阅读: {state.get('knowledge_base', {}).get('papers_read', 0)} 篇
- 关键发现: {len(state.get('knowledge_base', {}).get('key_findings', []))} 条
- 最佳实践: {len(state.get('knowledge_base', {}).get('best_practices', {}))} 条

## 状态
- 系统状态: {state.get('status', 'N/A')}
- 待审批: {state.get('human_interaction', {}).get('pending_approval', False)}
'''

        checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
        checkpoint_file.write_text(report, encoding='utf-8')
        print(f"检查点已创建: {checkpoint_file}")

    def resume_from_checkpoint(self, checkpoint_id: Optional[str] = None) -> None:
        """从检查点恢复

        Args:
            checkpoint_id: 检查点 ID，如果为 None 则恢复最新的检查点
        """
        print("=" * 60)
        print("  Project Prometheus - 检查点恢复")
        print("=" * 60)
        print()

        # 如果未指定检查点 ID，获取最新的检查点
        if checkpoint_id is None:
            latest = self.checkpoint_manager.get_latest_checkpoint()
            if latest is None:
                print("错误: 没有找到可用的检查点")
                print("提示: 请先使用 --checkpoint 创建检查点")
                return
            checkpoint_id = latest.get('checkpoint_id')
            print(f"使用最新检查点: {checkpoint_id}")
            print(f"名称: {latest.get('name', 'N/A')}")
            print(f"创建时间: {latest.get('created_at', 'N/A')}")
            print()
        else:
            # 验证指定的检查点是否存在
            checkpoint_info = self.checkpoint_manager.get_checkpoint(checkpoint_id)
            if checkpoint_info is None:
                print(f"错误: 找不到检查点 {checkpoint_id}")
                print("提示: 使用 --list-checkpoints 查看可用检查点")
                return
            print(f"指定检查点: {checkpoint_id}")
            print(f"名称: {checkpoint_info.get('name', 'N/A')}")
            print(f"创建时间: {checkpoint_info.get('created_at', 'N/A')}")
            print()

        # 执行恢复
        print("正在恢复检查点...")
        success = self.checkpoint_manager.restore(checkpoint_id)

        if success:
            # 重新加载状态
            self.state._state = None
            self.tasks._tasks = None

            print("[OK] 检查点恢复成功!")
            print()

            # 显示恢复后的状态
            state = self.state.state
            print("恢复后的状态:")
            print("-" * 40)
            print(f"项目名称: {state.get('current_project', 'N/A')}")
            print(f"当前阶段: {state.get('current_phase', 'N/A')}")
            print(f"当前任务: {state.get('current_task', 'N/A')}")
            print(f"系统状态: {state.get('status', 'N/A')}")

            # 显示进度摘要
            summary = self.tasks.get_progress_summary()
            print()
            print("进度概览:")
            print(f"  已完成: {summary['passed_tasks']}/{summary['total_tasks']}")
            print(f"  完成度: {summary['progress_percent']}%")
            print()
            print("下一步: 运行 'python prometheus.py --status' 查看详细状态")
            print("        或运行 'python prometheus.py --run' 继续执行")
        else:
            print("[FAIL] 检查点恢复失败")
            print("请检查检查点文件是否完整")

    def list_available_checkpoints(self, limit: int = 10) -> None:
        """列出可用的检查点

        Args:
            limit: 显示数量限制
        """
        print("=" * 60)
        print("  Project Prometheus - 可用检查点列表")
        print("=" * 60)
        print()

        checkpoints = self.checkpoint_manager.list_checkpoints(limit=limit)

        if not checkpoints:
            print("没有找到任何检查点")
            print("提示: 使用 --checkpoint 创建检查点")
            return

        # 显示统计信息
        stats = self.checkpoint_manager.get_statistics()
        print(f"总计: {stats['total_checkpoints']} 个检查点")
        print(f"  手动创建: {stats['manual_checkpoints']}")
        print(f"  自动创建: {stats['auto_checkpoints']}")
        if stats['total_size_mb'] > 0:
            print(f"  总大小: {stats['total_size_mb']} MB")
        print()

        # 显示检查点列表
        print("-" * 60)
        print(f"{'ID':<25} {'名称':<20} {'创建时间':<20}")
        print("-" * 60)

        for cp in checkpoints:
            cp_id = cp.get('checkpoint_id', 'N/A')
            name = cp.get('name', 'N/A')[:18]
            created = cp.get('created_at', 'N/A')[:19]
            auto_marker = " [A]" if cp.get('auto_created') else ""
            print(f"{cp_id:<25} {name:<20} {created}{auto_marker}")

        print()
        print("提示: 使用 --resume [CHECKPOINT_ID] 恢复指定检查点")
        print("      使用 --resume 恢复最新检查点")

    def rollback_to_commit(self, commit_ref: str, soft: bool = False) -> None:
        """回滚到指定的 Git 提交

        Args:
            commit_ref: 提交 ID 或相对位置 (如 HEAD~1, HEAD~3, 或完整哈希)
            soft: 是否软回滚（保留更改在工作区）
        """
        print("=" * 60)
        print("  Project Prometheus - Git 回滚")
        print("=" * 60)
        print()

        # 检查是否为 Git 仓库
        if not self.git_manager.is_git_repo():
            print("错误: 当前目录不是 Git 仓库")
            print("提示: 请先运行 'git init' 初始化仓库")
            return

        # 获取当前分支
        current_branch = self.git_manager.get_current_branch()
        print(f"当前分支: {current_branch or 'N/A'}")

        # 检查是否有未提交的更改
        status = self.git_manager.get_status()
        has_changes = bool(
            status.get('modified') or status.get('added') or
            status.get('deleted') or status.get('untracked')
        )

        if has_changes:
            print()
            print("警告: 检测到未提交的更改:")
            if status.get('modified'):
                print(f"  修改的文件: {len(status['modified'])}")
            if status.get('added'):
                print(f"  新增的文件: {len(status['added'])}")
            if status.get('deleted'):
                print(f"  删除的文件: {len(status['deleted'])}")
            if status.get('untracked'):
                print(f"  未跟踪的文件: {len(status['untracked'])}")
            print()
            print("回滚可能会丢失这些更改。建议先提交或暂存这些更改。")
            print()

        # 显示回滚目标信息
        print("-" * 40)
        print(f"回滚目标: {commit_ref}")
        print(f"回滚模式: {'软回滚 (保留更改)' if soft else '硬回滚 (丢弃更改)'}")
        print("-" * 40)
        print()

        # 执行回滚
        print("正在执行回滚...")
        success = self.git_manager.revert(commit_ref, soft=soft)

        if success:
            print("✓ 回滚成功!")
            print()

            # 显示回滚后的状态
            print("当前 Git 状态:")
            print("-" * 40)

            # 显示最近几次提交
            logs = self.git_manager.get_log(count=5)
            if logs:
                print("最近的提交:")
                for log in logs:
                    print(f"  {log['hash']}: {log['message']}")
                print()

            # 显示工作区状态
            status = self.git_manager.get_status()
            if status.get('modified') or status.get('added') or status.get('untracked'):
                print("工作区状态:")
                if status.get('modified'):
                    print(f"  修改: {len(status['modified'])} 个文件")
                if status.get('added'):
                    print(f"  新增: {len(status['added'])} 个文件")
                if status.get('untracked'):
                    print(f"  未跟踪: {len(status['untracked'])} 个文件")
            else:
                print("工作区干净，没有未提交的更改")

            print()
            print("提示:")
            print("  - 如需撤销此次回滚，可运行: git reflog 查看历史")
            print("  - 然后运行: git reset --hard HEAD@{N} 恢复")
        else:
            print("✗ 回滚失败")
            print()
            print("可能的原因:")
            print("  1. 指定的提交不存在")
            print("  2. 提交 ID 格式不正确")
            print("  3. Git 操作权限问题")
            print()
            print("建议:")
            print("  - 使用 --git-log 查看可用提交")
            print("  - 检查提交 ID 是否正确")

    def show_git_log(self, count: int = 10) -> None:
        """显示 Git 提交日志

        Args:
            count: 显示条数
        """
        print("=" * 60)
        print("  Project Prometheus - Git 提交历史")
        print("=" * 60)
        print()

        # 检查是否为 Git 仓库
        if not self.git_manager.is_git_repo():
            print("错误: 当前目录不是 Git 仓库")
            print("提示: 请先运行 'git init' 初始化仓库")
            return

        # 获取当前分支
        current_branch = self.git_manager.get_current_branch()
        print(f"当前分支: {current_branch or 'N/A'}")
        print()

        # 获取提交日志
        logs = self.git_manager.get_log(count=count, oneline=False)

        if not logs:
            print("没有找到提交记录")
            return

        # 显示提交列表
        print("-" * 60)
        print(f"{'提交哈希':<12} {'作者':<15} {'日期':<20} {'信息'}")
        print("-" * 60)

        for log in logs:
            commit_hash = log.get('hash', 'N/A')[:8]
            author = log.get('author', 'N/A')[:13]
            date = log.get('date', 'N/A')[:19]
            message = log.get('message', 'N/A')[:30]
            print(f"{commit_hash:<12} {author:<15} {date:<20} {message}")

        print()
        print(f"显示最近 {len(logs)} 条提交")
        print()
        print("提示:")
        print("  - 使用 --rollback HEAD~1 回滚到上一个提交")
        print("  - 使用 --rollback <commit_hash> 回滚到指定提交")
        print("  - 添加 --soft 参数保留更改（如: --rollback HEAD~1 --soft）")

    def export_report(self, components: str = "all",
                      format: str = "markdown",
                      output: Optional[str] = None,
                      include_logs: bool = True,
                      log_lines: int = 100) -> None:
        """导出项目报告

        Args:
            components: 要导出的组件（all, progress, knowledge, logs, sessions）
                       多个组件用逗号分隔
            format: 导出格式（markdown, html, pdf）
            output: 输出文件名（不含扩展名）
            include_logs: 是否包含日志
            log_lines: 包含的日志行数
        """
        print("=" * 60)
        print("  Project Prometheus - 导出项目报告")
        print("=" * 60)
        print()

        # 解析组件列表
        component_list = [c.strip().lower() for c in components.split(',')]

        print(f"导出组件: {', '.join(component_list)}")
        print(f"导出格式: {format.upper()}")
        print()

        try:
            print("正在生成报告...")

            result = self.export_manager.export_project(
                components=component_list,
                format=format,
                output_file=output,
                include_logs=include_logs,
                log_lines=log_lines
            )

            print()
            print("[OK] 报告导出成功!")
            print()
            print(f"输出文件: {result['output_path']}")
            print(f"导出时间: {result['export_time']}")

            # 获取文件大小
            output_path = Path(result['output_path'])
            if output_path.exists():
                size_kb = output_path.stat().st_size / 1024
                print(f"文件大小: {size_kb:.2f} KB")

            print()
            print("导出的内容:")

            # 显示导出的内容详情
            if 'progress' in component_list or 'all' in component_list:
                summary = self.tasks.get_progress_summary()
                print(f"  - 项目进度: {summary['passed_tasks']}/{summary['total_tasks']} 任务完成")

            if 'knowledge' in component_list or 'all' in component_list:
                knowledge = self.state.state.get('knowledge_base', {})
                print(f"  - 知识库: {knowledge.get('papers_read', 0)} 篇论文, "
                      f"{len(knowledge.get('key_findings', []))} 条发现")

            if 'logs' in component_list or 'all' in component_list:
                if include_logs:
                    print(f"  - 日志: 最近 {log_lines} 行")

            if 'sessions' in component_list or 'all' in component_list:
                print("  - 会话统计")

        except RuntimeError as e:
            print()
            print("[!] PDF 导出需要额外依赖")
            print()
            print(str(e))

        except Exception as e:
            print()
            print(f"[FAIL] 导出失败: {e}")
            print()
            print("可能的原因:")
            print("  1. 数据文件不存在或格式错误")
            print("  2. 导出目录权限问题")
            print("  3. 磁盘空间不足")

    def list_exports(self) -> None:
        """列出所有已导出的报告"""
        print("=" * 60)
        print("  Project Prometheus - 已导出的报告")
        print("=" * 60)
        print()

        exports = self.export_manager.list_exports()

        if not exports:
            print("没有找到已导出的报告")
            print("提示: 使用 --export 创建报告")
            return

        # 显示统计
        total_size = sum(e['size_bytes'] for e in exports)
        print(f"总计: {len(exports)} 个报告 ({total_size / 1024:.2f} KB)")
        print()

        # 显示报告列表
        print("-" * 60)
        print(f"{'文件名':<35} {'格式':<8} {'大小':<10} {'修改时间'}")
        print("-" * 60)

        for exp in exports:
            name = exp['filename'][:33]
            fmt = exp['format']
            size = f"{exp['size_bytes'] / 1024:.1f} KB"
            modified = exp['modified_at'][:19]
            print(f"{name:<35} {fmt:<8} {size:<10} {modified}")

        print()
        print(f"导出目录: {self.export_manager.get_export_dir()}")

    def validate_system(self, fix: bool = False) -> dict:
        """验证系统状态完整性

        检查：
        - 必要文件存在性
        - JSON 格式正确性
        - Git 状态

        Args:
            fix: 是否自动修复可修复的问题

        Returns:
            验证结果字典
        """
        print("=" * 60)
        print("  Project Prometheus - 系统验证")
        print("=" * 60)
        print()

        results = {
            "passed": [],
            "warnings": [],
            "errors": [],
            "fixed": [],
            "summary": {
                "total_checks": 0,
                "passed_count": 0,
                "warning_count": 0,
                "error_count": 0
            }
        }

        def check_pass(msg):
            results["passed"].append(msg)
            results["summary"]["passed_count"] += 1
            results["summary"]["total_checks"] += 1
            print(f"  [OK] {msg}")

        def check_warn(msg):
            results["warnings"].append(msg)
            results["summary"]["warning_count"] += 1
            results["summary"]["total_checks"] += 1
            print(f"  [WARN] {msg}")

        def check_error(msg):
            results["errors"].append(msg)
            results["summary"]["error_count"] += 1
            results["summary"]["total_checks"] += 1
            print(f"  [FAIL] {msg}")

        def check_fix(msg):
            results["fixed"].append(msg)
            print(f"  [FIXED] {msg}")

        # ============================================
        # 1. 检查目录结构
        # ============================================
        print("[1/5] 检查目录结构...")
        required_dirs = [
            BASE_DIR / "Core",
            BASE_DIR / "Core" / "prompts",
            BASE_DIR / "Core" / "tools",
            BASE_DIR / "Projects",
            BASE_DIR / "Logs",
            BASE_DIR / "Communication",
            BASE_DIR / "Communication" / "inbox",
            BASE_DIR / "Communication" / "outbox",
            BASE_DIR / "automation",
        ]

        for dir_path in required_dirs:
            rel_path = dir_path.relative_to(BASE_DIR)
            if dir_path.exists() and dir_path.is_dir():
                check_pass(f"目录存在: {rel_path}")
            else:
                check_error(f"目录缺失: {rel_path}")
                if fix:
                    try:
                        dir_path.mkdir(parents=True, exist_ok=True)
                        check_fix(f"已创建目录: {rel_path}")
                    except Exception as e:
                        check_error(f"无法创建目录 {rel_path}: {e}")

        print()

        # ============================================
        # 2. 检查必要文件
        # ============================================
        print("[2/5] 检查必要文件...")
        required_files = [
            BASE_DIR / "config" / "execution_config.yaml",
            BASE_DIR / "start_research.py",
            BASE_DIR / "automation" / "task_executor.py",
        ]

        optional_files = [
            BASE_DIR / "README.md",
            BASE_DIR / "requirements.txt",
        ]

        for file_path in required_files:
            rel_path = file_path.relative_to(BASE_DIR)
            if file_path.exists() and file_path.is_file():
                check_pass(f"文件存在: {rel_path}")
            else:
                check_error(f"文件缺失: {rel_path}")
                if fix:
                    try:
                        if file_path.suffix == ".json":
                            file_path.write_text("{}", encoding='utf-8')
                        elif file_path.name == "commands.txt":
                            file_path.parent.mkdir(parents=True, exist_ok=True)
                            file_path.write_text("# 在此写入指令控制智能体\n", encoding='utf-8')
                        check_fix(f"已创建文件: {rel_path}")
                    except Exception as e:
                        check_error(f"无法创建文件 {rel_path}: {e}")

        for file_path in optional_files:
            rel_path = file_path.relative_to(BASE_DIR)
            if file_path.exists() and file_path.is_file():
                check_pass(f"可选文件存在: {rel_path}")
            else:
                check_warn(f"可选文件缺失: {rel_path}")

        print()

        # ============================================
        # 3. 检查项目文件
        # ============================================
        print("[3/5] 检查项目文件...")

        # 查找所有项目目录
        projects_dir = BASE_DIR / "Projects"
        if projects_dir.exists():
            project_dirs = [d for d in projects_dir.iterdir() if d.is_dir() and d.name != "current"]
            if project_dirs:
                for proj_dir in project_dirs[:3]:  # 只检查前3个项目
                    tasks_file = proj_dir / "research_tasks.json"
                    if tasks_file.exists():
                        check_pass(f"项目任务文件: {proj_dir.name}/research_tasks.json")
                    else:
                        check_warn(f"项目缺少任务文件: {proj_dir.name}/research_tasks.json")
            else:
                check_warn("未找到任何项目，运行 start_research.py 创建新项目")
        else:
            check_warn("Projects 目录不存在")

        json_files = [
            ("config.yaml", BASE_DIR / "config.yaml"),
        ]

        optional_json_files = []

        for name, file_path in json_files:
            if not file_path.exists():
                check_error(f"JSON 文件缺失: {name}")
                continue

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # 验证关键字段
                if name == "state.json":
                    required_fields = ["version", "current_phase", "status"]
                    missing = [f for f in required_fields if f not in data]
                    if missing:
                        check_warn(f"state.json 缺少字段: {missing}")
                    else:
                        check_pass(f"JSON 格式正确: {name}")
                elif name == "research_tasks.json":
                    if "phases" in data:
                        check_pass(f"JSON 格式正确: {name}")
                    else:
                        check_warn(f"{name} 缺少 'phases' 字段")
            except json.JSONDecodeError as e:
                check_error(f"JSON 解析错误 {name}: {e}")
                if fix:
                    try:
                        # 尝试创建有效的默认 JSON
                        if name == "state.json":
                            self._init_state("RecoveredProject")
                        elif name == "research_tasks.json":
                            self._create_default_tasks("RecoveredProject", "Unknown", "Recovery")
                        check_fix(f"已重建 JSON 文件: {name}")
                    except Exception as ex:
                        check_error(f"无法修复 {name}: {ex}")
            except Exception as e:
                check_error(f"读取文件错误 {name}: {e}")

        for name, file_path in optional_json_files:
            if not file_path.exists():
                check_warn(f"可选 JSON 文件缺失: {name}")
                continue

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    json.load(f)
                check_pass(f"可选 JSON 格式正确: {name}")
            except json.JSONDecodeError as e:
                check_warn(f"可选 JSON 解析错误 {name}: {e}")

        print()

        # ============================================
        # 4. 检查 Git 状态
        # ============================================
        print("[4/5] 检查 Git 状态...")

        if self.git_manager.is_git_repo():
            check_pass("Git 仓库已初始化")

            # 检查当前分支
            branch = self.git_manager.get_current_branch()
            if branch:
                check_pass(f"当前分支: {branch}")
            else:
                check_warn("无法获取当前分支（可能是 detached HEAD 状态）")

            # 检查工作区状态
            status = self.git_manager.get_status()
            modified = status.get('modified', [])
            added = status.get('added', [])
            deleted = status.get('deleted', [])
            untracked = status.get('untracked', [])

            if not (modified or added or deleted or untracked):
                check_pass("工作区干净，无未提交的更改")
            else:
                if modified:
                    check_warn(f"有 {len(modified)} 个已修改的文件未提交")
                if added:
                    check_warn(f"有 {len(added)} 个已添加的文件未提交")
                if deleted:
                    check_warn(f"有 {len(deleted)} 个已删除的文件未提交")
                if untracked:
                    check_warn(f"有 {len(untracked)} 个未跟踪的文件")

            # 检查提交历史
            logs = self.git_manager.get_log(count=1)
            if logs:
                check_pass(f"最新提交: {logs[0]['hash'][:8]} - {logs[0]['message'][:40]}")
            else:
                check_warn("没有提交历史")
        else:
            check_error("不是 Git 仓库")
            if fix:
                try:
                    self._init_git()
                    check_fix("已初始化 Git 仓库")
                except Exception as e:
                    check_error(f"无法初始化 Git: {e}")

        print()

        # ============================================
        # 5. 检查核心模块
        # ============================================
        print("[5/5] 检查核心模块...")

        core_modules = [
            "progress",
            "checkpoint_manager",
            "archive_manager",
            "export_manager",
        ]

        for module_name in core_modules:
            module_path = BASE_DIR / "Core" / f"{module_name}.py"
            if module_path.exists():
                try:
                    # 尝试导入模块以验证语法
                    import importlib.util
                    spec = importlib.util.spec_from_file_location(module_name, module_path)
                    if spec and spec.loader:
                        check_pass(f"核心模块正常: {module_name}.py")
                    else:
                        check_warn(f"核心模块可能有问题: {module_name}.py")
                except Exception as e:
                    check_error(f"核心模块导入失败 {module_name}: {e}")
            else:
                check_warn(f"核心模块缺失: {module_name}.py")

        print()

        # ============================================
        # 汇总结果
        # ============================================
        print("=" * 60)
        print("  验证结果汇总")
        print("=" * 60)
        print()

        total = results["summary"]["total_checks"]
        passed = results["summary"]["passed_count"]
        warnings = results["summary"]["warning_count"]
        errors = results["summary"]["error_count"]

        print(f"  总检查项: {total}")
        print(f"  通过: {passed}")
        print(f"  警告: {warnings}")
        print(f"  错误: {errors}")
        if fix and results["fixed"]:
            print(f"  已修复: {len(results['fixed'])}")
        print()

        if errors == 0:
            print("  状态: [OK] 系统验证通过")
            if warnings > 0:
                print(f"         但有 {warnings} 个警告，建议检查")
        else:
            print(f"  状态: [FAIL] 发现 {errors} 个错误")
            if not fix:
                print("         建议使用 --validate --fix 尝试自动修复")

        print()
        print("=" * 60)

        results["is_valid"] = (errors == 0)
        return results

    def select_task(self, multi_select: bool = False,
                    phase: Optional[str] = None,
                    simple: bool = False) -> None:
        """交互式任务选择

        显示待完成任务列表，让用户选择要执行的任务。

        Args:
            multi_select: 是否允许多选
            phase: 只显示指定阶段的任务
            simple: 使用简化版界面（适用于不支持原始模式的终端）
        """
        print("=" * 60)
        print("  Project Prometheus - 交互式任务选择")
        print("=" * 60)
        print()

        # 显示选项
        print("选择模式:")
        print(f"  - 模式: {'多选' if multi_select else '单选'}")
        print(f"  - 界面: {'简化版' if simple else '自动检测'}")
        if phase:
            print(f"  - 阶段过滤: {phase}")
        print()

        # 创建阶段过滤器
        filter_func = None
        if phase:
            def filter_func(t):
                return phase.lower() in t.get("phase_id", "").lower()

        # 运行选择器
        try:
            if simple:
                selected = self.task_selector.run_simple(
                    multi_select=multi_select,
                    filter_func=filter_func
                )
            else:
                selected = self.task_selector.select_interactive(
                    multi_select=multi_select,
                    filter_func=filter_func
                )
        except KeyboardInterrupt:
            print()
            print("用户取消选择")
            return
        except Exception as e:
            print(f"选择器错误: {e}")
            print("尝试使用简化版界面...")
            try:
                selected = self.task_selector.run_simple(
                    multi_select=multi_select,
                    filter_func=filter_func
                )
            except Exception as e2:
                print(f"简化版也失败: {e2}")
                return

        # 处理选择结果
        if not selected:
            print()
            print("没有选择任何任务")
            return

        print()
        print("=" * 60)
        print("  已选择的任务")
        print("=" * 60)
        print()

        # 获取任务详情
        tasks_data = self.tasks.tasks
        selected_details = []

        for task_id in selected:
            for phase_data in tasks_data.get("phases", []):
                for task in phase_data.get("tasks", []):
                    if task.get("task_id") == task_id:
                        selected_details.append({
                            "task_id": task_id,
                            "phase": phase_data.get("phase_name", "Unknown"),
                            "description": task.get("description", "No description"),
                            "steps": task.get("steps", [])
                        })
                        break

        # 显示选中任务的详情
        for i, detail in enumerate(selected_details, 1):
            print(f"[{i}] {detail['task_id']}")
            print(f"    阶段: {detail['phase']}")
            print(f"    描述: {detail['description']}")
            if detail['steps']:
                print("    步骤:")
                for step in detail['steps']:
                    print(f"      - {step}")
            print()

        print("-" * 60)
        print(f"共选择 {len(selected)} 个任务")
        print()

        # 提供后续操作建议
        print("下一步操作:")
        print("  1. 运行 'python prometheus.py --run' 执行选中的任务")
        print("  2. 运行 'python prometheus.py --status' 查看当前状态")
        print()

        # 保存选择结果
        selection_file = BASE_DIR / "Communication" / "outbox" / "task_selection.json"
        selection_file.parent.mkdir(parents=True, exist_ok=True)

        selection_data = {
            "selected_at": datetime.now().isoformat(),
            "selected_tasks": selected,
            "task_details": selected_details
        }

        with open(selection_file, 'w', encoding='utf-8') as f:
            json.dump(selection_data, f, ensure_ascii=False, indent=2)

        print(f"选择结果已保存到: {selection_file}")


def main():
    # 安装全局异常处理器
    exception_handler = install_global_exception_handler()

    parser = argparse.ArgumentParser(
        description="Project Prometheus - 全自主科研智能体系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python prometheus.py --init                    # 交互式初始化
  python prometheus.py --init -n "MyProject" -d "ML" -q "How to..."
  python prometheus.py --status                  # 查看状态
  python prometheus.py --run                     # 运行科研智能体
  python prometheus.py --run --mode initializer  # 运行初始化智能体
  python prometheus.py --checkpoint              # 创建检查点
  python prometheus.py --resume                  # 恢复最新检查点
  python prometheus.py --resume cp_20260201_120000_000000  # 恢复指定检查点
  python prometheus.py --list-checkpoints        # 列出所有检查点
  python prometheus.py --export                  # 导出完整报告 (Markdown)
  python prometheus.py --export --format html    # 导出 HTML 格式报告
  python prometheus.py --export -c progress,knowledge  # 仅导出进度和知识库
  python prometheus.py --list-exports            # 列出所有已导出的报告
  python prometheus.py --git-log                 # 查看 Git 提交历史
  python prometheus.py --rollback HEAD~1         # 回滚到上一个提交
  python prometheus.py --rollback abc123 --soft  # 软回滚（保留更改）
  python prometheus.py --validate                # 验证系统状态完整性
  python prometheus.py --validate --fix          # 验证并自动修复问题
  python prometheus.py --select                  # 交互式任务选择（单选）
  python prometheus.py --select --multi          # 交互式任务选择（多选）
  python prometheus.py --select --phase coding   # 只显示编码阶段的任务
  python prometheus.py --select --simple         # 使用简化版界面
  python prometheus.py --visual                  # 显示可视化进度仪表板
  python prometheus.py --visual --mode progress  # 仅显示进度条
  python prometheus.py --visual --mode phases    # 仅显示各阶段进度
  python prometheus.py --visual --mode tasks     # 显示任务列表
        """
    )

    parser.add_argument('--init', action='store_true', help='初始化新项目')
    parser.add_argument('-n', '--name', type=str, help='项目名称')
    parser.add_argument('-d', '--domain', type=str, help='研究领域')
    parser.add_argument('-q', '--question', type=str, help='研究问题')
    parser.add_argument('--status', action='store_true', help='查看系统状态')
    parser.add_argument('--run', action='store_true', help='运行智能体')
    parser.add_argument('--mode', type=str, default='research',
                        choices=['initializer', 'research'],
                        help='智能体模式')
    parser.add_argument('--checkpoint', action='store_true', help='创建检查点')
    parser.add_argument('--resume', nargs='?', const=None, default=None,
                        metavar='CHECKPOINT_ID',
                        help='从检查点恢复（可选指定检查点ID，不指定则恢复最新）')
    parser.add_argument('--list-checkpoints', action='store_true',
                        help='列出所有可用检查点')
    parser.add_argument('--git-log', action='store_true',
                        help='显示 Git 提交历史')
    parser.add_argument('--rollback', type=str, default=None,
                        metavar='COMMIT_REF',
                        help='回滚到指定提交（支持 HEAD~N 或提交哈希）')
    parser.add_argument('--soft', action='store_true',
                        help='软回滚（保留更改在工作区）')

    # 导出相关参数
    parser.add_argument('--export', action='store_true',
                        help='导出项目报告')
    parser.add_argument('-c', '--components', type=str, default='all',
                        help='导出组件（all, progress, knowledge, logs, sessions），多个用逗号分隔')
    parser.add_argument('--format', type=str, default='markdown',
                        choices=['markdown', 'md', 'html', 'pdf'],
                        help='导出格式（默认: markdown）')
    parser.add_argument('-o', '--output', type=str, default=None,
                        help='输出文件名（不含扩展名）')
    parser.add_argument('--no-logs', action='store_true',
                        help='导出时不包含日志')
    parser.add_argument('--log-lines', type=int, default=100,
                        help='包含的日志行数（默认: 100）')
    parser.add_argument('--list-exports', action='store_true',
                        help='列出所有已导出的报告')

    # 验证相关参数
    parser.add_argument('--validate', action='store_true',
                        help='验证系统状态完整性')
    parser.add_argument('--fix', action='store_true',
                        help='自动修复发现的问题（与 --validate 配合使用）')

    # 交互式任务选择参数
    parser.add_argument('--select', action='store_true',
                        help='交互式任务选择')
    parser.add_argument('--multi', action='store_true',
                        help='允许多选模式（与 --select 配合使用）')
    parser.add_argument('--phase', type=str, default=None,
                        help='只显示指定阶段的任务（与 --select 配合使用）')
    parser.add_argument('--simple', action='store_true',
                        help='使用简化版界面（适用于不支持原始模式的终端）')

    # 进度可视化参数
    parser.add_argument('--visual', action='store_true',
                        help='显示可视化进度')
    parser.add_argument('--vmode', type=str, default='dashboard',
                        choices=['dashboard', 'progress', 'phases', 'tasks', 'all'],
                        help='可视化模式（默认: dashboard）')

    args = parser.parse_args()

    prometheus = Prometheus()

    if args.init:
        if args.name and args.domain and args.question:
            prometheus.init_system(args.name, args.domain, args.question)
        else:
            # 交互式初始化
            print("Project Prometheus 初始化向导")
            print("-" * 40)
            name = input("项目名称: ").strip() or "ResearchProject"
            domain = input("研究领域 (如: 机器学习): ").strip() or "机器学习"
            question = input("研究问题: ").strip() or "待定义"
            print()
            prometheus.init_system(name, domain, question)

    elif args.status:
        prometheus.show_status()

    elif args.run:
        prometheus.run_agent(args.mode)

    elif args.checkpoint:
        prometheus.create_checkpoint()

    elif args.resume is not None or (args.resume is None and '--resume' in sys.argv):
        # 处理 --resume 命令
        # 当使用 --resume 时，args.resume 可能是 None（无参数）或指定的 ID
        checkpoint_id = args.resume if args.resume != '' else None
        prometheus.resume_from_checkpoint(checkpoint_id)

    elif args.list_checkpoints:
        prometheus.list_available_checkpoints()

    elif args.git_log:
        prometheus.show_git_log()

    elif args.rollback:
        prometheus.rollback_to_commit(args.rollback, soft=args.soft)

    elif args.export:
        prometheus.export_report(
            components=args.components,
            format=args.format,
            output=args.output,
            include_logs=not args.no_logs,
            log_lines=args.log_lines
        )

    elif args.list_exports:
        prometheus.list_exports()

    elif args.validate:
        prometheus.validate_system(fix=args.fix)

    elif args.select:
        prometheus.select_task(
            multi_select=args.multi,
            phase=args.phase,
            simple=args.simple
        )

    elif args.visual:
        prometheus.show_visual_progress(mode=args.vmode)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()

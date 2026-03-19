#!/usr/bin/env python3
"""
Project Prometheus - 自动任务执行器
====================================

自动读取 research_tasks.json 中的待执行任务，并调用 Claude Code 执行。
集成 Ralph Loop 深度迭代机制。

用法:
    python task_executor.py                    # 执行单个任务
    python task_executor.py --loop             # 循环执行所有任务
    python task_executor.py --status           # 查看状态
    python task_executor.py --init             # 初始化项目

环境变量:
    CLAUDE_CODE_PATH: Claude Code 可执行文件路径
    PERMISSION_MODE: 权限模式 (acceptEdits/bypassPermissions/plan)
    MAX_ITERATIONS: 最大迭代次数 (默认: 100)

Ralph Loop 机制:
    - 每个任务可进行多次深度迭代直到完成
    - 通过检测 <promise>TASK_COMPLETE</promise> 判断完成
    - 适用于 coding/execution/analysis 阶段
"""

import os
import sys
import json
import time
import re
import subprocess
import argparse
import yaml
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any

# 默认配置
DEFAULT_CONFIG = {
    "tasks_file": "research_tasks.json",
    "log_file": "logs/executor.log",
    "state_file": ".prometheus/executor_state.json",
    "prompts_dir": ".prometheus/prompts",
    "max_iterations": int(os.getenv("MAX_ITERATIONS", "100")),
    "iteration_timeout": int(os.getenv("ITERATION_TIMEOUT", "300")),  # Ralph Loop 每次迭代超时
    "retry_count": int(os.getenv("RETRY_COUNT", "3")),
    "retry_delay": int(os.getenv("RETRY_DELAY", "30")),
    "api_request_delay": int(os.getenv("API_REQUEST_DELAY", "5")),  # API 请求间隔(秒)，防止限流
}

# Ralph Loop 默认配置
RALPH_DEFAULT = {
    "enabled": True,
    "max_iterations": 20,
    "completion_promise": "TASK_COMPLETE",
    "iteration_timeout": 300,
    "phases_enabled": {
        "coding": True,
        "execution": True,
        "analysis": True,
    }
}

# GEP 默认配置
GEP_DEFAULT = {
    "enabled": True,
    "min_confidence": 0.3,
    "max_genes": 3,
    "max_capsules": 5,
}

# 完成承诺检测正则
PROMISE_PATTERN = re.compile(r'<promise\s*(?:type="[^"]*")?\s*>([^<]+)</promise>', re.IGNORECASE)


def find_claude_code() -> str:
    """查找 Claude Code 可执行文件"""
    # 首先检查环境变量
    env_path = os.getenv("CLAUDE_CODE_PATH", "")
    if env_path and os.path.isfile(env_path):
        return env_path

    # Windows 常见路径
    if sys.platform == "win32":
        win_candidates = [
            os.path.expanduser("~/AppData/Roaming/npm/claude.cmd"),
            os.path.expanduser("~/AppData/Roaming/npm/claude"),
            "C:/Users/幸爷/AppData/Roaming/npm/claude.cmd",
        ]
        for candidate in win_candidates:
            if os.path.isfile(candidate):
                return candidate

    # 使用 where/which 查找
    try:
        result = subprocess.run(
            ["where", "claude"] if sys.platform == "win32" else ["which", "claude"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            return result.stdout.strip().split('\n')[0]
    except:
        pass

    return "claude"


def get_permission_mode() -> str:
    """获取权限模式"""
    mode = os.getenv("PERMISSION_MODE", "acceptEdits")
    valid_modes = ["acceptEdits", "bypassPermissions", "default", "delegate", "dontAsk", "plan"]
    return mode if mode in valid_modes else "acceptEdits"


def safe_print(msg: str):
    """安全打印（处理编码问题）"""
    safe_msg = ''.join(c if ord(c) < 128 or '\u4e00' <= c <= '\u9fff' else '?' for c in msg)
    print(safe_msg)


def load_execution_config(project_dir: Path) -> Dict[str, Any]:
    """加载执行配置文件"""
    config_file = project_dir.parent.parent / "config" / "execution_config.yaml"
    if config_file.exists():
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception:
            pass
    return {}


class TaskExecutor:
    """任务执行器 - 从 research_tasks.json 读取任务，集成 Ralph Loop"""

    def __init__(self, project_dir: str = None):
        self.project_dir = Path(project_dir or os.getcwd())

        # 加载配置
        self.config = DEFAULT_CONFIG.copy()
        exec_config = load_execution_config(self.project_dir)
        if exec_config:
            # 合并执行配置
            if "execution" in exec_config:
                self.config.update(exec_config["execution"])
            # 加载 Ralph Loop 配置
            self.ralph_config = exec_config.get("ralph", RALPH_DEFAULT)
            # 加载 GEP 配置
            self.gep_config = exec_config.get("gep", GEP_DEFAULT)
        else:
            self.ralph_config = RALPH_DEFAULT
            self.gep_config = GEP_DEFAULT

        self.tasks_file = self.project_dir / self.config["tasks_file"]
        self.log_file = self.project_dir / self.config["log_file"]
        self.state_file = self.project_dir / self.config["state_file"]
        self.prompts_dir = self.project_dir / self.config["prompts_dir"]
        self.lock_file = self.project_dir / ".prometheus" / "executor.lock"

        # 确保目录存在
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.prompts_dir.mkdir(parents=True, exist_ok=True)
        self.lock_file.parent.mkdir(parents=True, exist_ok=True)

        self.claude_cmd = find_claude_code()
        self.permission_mode = get_permission_mode()

        # 初始化 GEP Selector (延迟加载)
        self._gep_selector = None

        # 进程锁文件句柄
        self._lock_fd = None

    def _acquire_lock(self) -> bool:
        """获取进程锁，防止多实例运行"""
        try:
            self._lock_fd = open(self.lock_file, "w")
            if sys.platform == "win32":
                import msvcrt
                msvcrt.locking(self._lock_fd.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self._lock_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            self._lock_fd.write(f"{os.getpid()}\n")
            self._lock_fd.flush()
            return True
        except (IOError, OSError, ImportError):
            if self._lock_fd:
                try:
                    self._lock_fd.close()
                except:
                    pass
                self._lock_fd = None
            return False

    def _release_lock(self):
        """释放进程锁"""
        if self._lock_fd:
            try:
                if sys.platform == "win32":
                    import msvcrt
                    self._lock_fd.seek(0)
                    msvcrt.locking(self._lock_fd.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(self._lock_fd.fileno(), fcntl.LOCK_UN)
                self._lock_fd.close()
            except:
                pass
            finally:
                self._lock_fd = None
            try:
                self.lock_file.unlink(missing_ok=True)
            except:
                pass

    def log(self, level: str, message: str):
        """记录日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] [{level}] {message}"

        # 写入日志文件
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(log_line + "\n")
        except:
            pass

        # 控制台输出 - 使用 safe_print 避免编码问题
        try:
            safe_print(log_line)
        except:
            pass  # 静默失败，不影响执行

    def load_state(self) -> dict:
        """加载执行状态"""
        if self.state_file.exists():
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return {
            "current_iteration": 0,
            "completed_tasks": [],
            "failed_tasks": [],
            "last_task": None,
            "last_update": None
        }

    def save_state(self, state: dict):
        """保存执行状态"""
        state["last_update"] = datetime.now().isoformat()
        try:
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.log("WARNING", f"保存状态失败: {e}")

    def generate_research_tasks(self):
        """从模板生成完整的100任务研究任务清单"""
        # 定义完整的9个阶段任务
        phases = [
            {
                "phase": 0,
                "name": "topic_analysis",
                "tasks": [
                    {"task_id": "topic_001", "description": "明确研究主题边界和核心问题", "status": "pending", "priority": "high"},
                    {"task_id": "topic_002", "description": "武警部队任务类型与特点分析", "status": "pending", "priority": "high"},
                    {"task_id": "topic_003", "description": "无人机集群技术发展现状调研", "status": "pending", "priority": "high"},
                    {"task_id": "topic_004", "description": "国内外无人机军事应用案例研究", "status": "pending", "priority": "medium"},
                ]
            },
            {
                "phase": 1,
                "name": "literature_review",
                "tasks": [
                    # Phase 1: 文献搜索 (6 tasks)
                    {"task_id": "lit_001", "description": "【搜索1】使用核心主题关键词在 Semantic Scholar 搜索论文，获取前20篇", "status": "pending", "priority": "high"},
                    {"task_id": "lit_002", "description": "【搜索2】在 arXiv 搜索最新预印本论文（近2年），获取前15篇", "status": "pending", "priority": "high"},
                    {"task_id": "lit_003", "description": "【搜索3】搜索相关综述论文(Survey/Review)，获取前10篇", "status": "pending", "priority": "high"},
                    {"task_id": "lit_004", "description": "【搜索4】搜索经典高引用论文（citation>500），获取前10篇", "status": "pending", "priority": "high"},
                    {"task_id": "lit_005", "description": "【搜索5】搜索交叉领域论文（如方法+应用），获取前10篇", "status": "pending", "priority": "medium"},
                    {"task_id": "lit_006", "description": "【搜索6】搜索最新会议论文（NeurIPS/ICML/ACL/CHI等），获取前15篇", "status": "pending", "priority": "high"},
                    # Phase 1: 文献整理 (5 tasks)
                    {"task_id": "lit_007", "description": "合并所有搜索结果，去重，按相关性排序", "status": "pending", "priority": "high"},
                    {"task_id": "lit_008", "description": "筛选出最相关的30篇论文作为核心文献", "status": "pending", "priority": "high"},
                    {"task_id": "lit_009", "description": "创建文献数据库(literature_db.json)，记录每篇论文的元数据", "status": "pending", "priority": "high"},
                    {"task_id": "lit_010", "description": "按研究主题对论文分类:核心方法/应用场景/评估方法/理论基础", "status": "pending", "priority": "medium"},
                    {"task_id": "lit_011", "description": "下载核心文献的PDF文件（优先从arXiv/OpenAccess下载）", "status": "pending", "priority": "high"},
                    # Phase 1: 文献阅读 (20 tasks)
                    {"task_id": "lit_012", "description": "【研读1】阅读第1篇核心论文,提取背景、方法、结果、贡献, 写入笔记", "status": "pending", "priority": "high"},
                    {"task_id": "lit_013", "description": "【研读2】阅读第2篇核心论文, 提取背景、方法、结果、贡献, 写入笔记", "status": "pending", "priority": "high"},
                    {"task_id": "lit_014", "description": "【研读3】阅读第3篇核心论文, 提取背景、方法、结果、贡献, 写入笔记", "status": "pending", "priority": "high"},
                    {"task_id": "lit_015", "description": "【研读4】阅读第4篇核心论文, 提取背景、方法、结果、贡献, 写入笔记", "status": "pending", "priority": "high"},
                    {"task_id": "lit_016", "description": "【研读5】阅读第5篇核心论文, 提取背景、方法、结果、贡献, 写入笔记", "status": "pending", "priority": "high"},
                    {"task_id": "lit_017", "description": "【研读6】阅读第6篇核心论文, 提取背景、方法、结果、贡献, 写入笔记", "status": "pending", "priority": "high"},
                    {"task_id": "lit_018", "description": "【研读7】阅读第7篇核心论文, 提取背景、方法、结果、贡献, 写入笔记", "status": "pending", "priority": "high"},
                    {"task_id": "lit_019", "description": "【研读8】阅读第8篇核心论文, 提取背景、方法、结果、贡献, 写入笔记", "status": "pending", "priority": "high"},
                    {"task_id": "lit_020", "description": "【研读9】阅读第9篇核心论文, 提取背景、方法、结果、贡献, 写入笔记", "status": "pending", "priority": "high"},
                    {"task_id": "lit_021", "description": "【研读10】阅读第10篇核心论文, 提取背景、方法、结果、贡献, 写入笔记", "status": "pending", "priority": "high"},
                    {"task_id": "lit_022", "description": "【研读11-15】阅读第11-15篇论文（次核心）， 提取关键信息摘要", "status": "pending", "priority": "medium"},
                    {"task_id": "lit_023", "description": "【研读16-20】阅读第16-20篇论文（相关), 提取可引用内容", "status": "pending", "priority": "medium"},
                    {"task_id": "lit_024", "description": "【研读21-30】快速浏览第21-30篇论文, 记录主要观点", "status": "pending", "priority": "low"},
                    {"task_id": "lit_025", "description": "分析所有阅读笔记, 识别研究领域的经典方法和发展脉络", "status": "pending", "priority": "high"},
                    {"task_id": "lit_026", "description": "分析现有研究的局限性和研究空白(Research Gap)", "status": "pending", "priority": "high"},
                    {"task_id": "lit_027", "description": "识别创新机会：分析哪些问题尚未被解决, 哪些方法可以改进", "status": "pending", "priority": "high"},
                    {"task_id": "lit_028", "description": "对比分析: 确定本研究与现有工作的差异化定位", "status": "pending", "priority": "high"},
                    {"task_id": "lit_029", "description": "生成参考文献BibTeX文件(references.bib), 确保格式正确", "status": "pending", "priority": "high"},
                    {"task_id": "lit_030", "description": "撰写文献综述初稿（按主题组织,非按时间）", "status": "pending", "priority": "high"},
                    {"task_id": "lit_031", "description": "检查文献综述中的引用是否完整, 补充缺失的引用", "status": "pending", "priority": "medium"},
                    {"task_id": "lit_032", "description": "完善文献综述, 确保引用格式规范（APA/IEEE/ACM格式）", "status": "pending", "priority": "medium"},
                ]
            },
            {
                "phase": 2,
                "name": "hypothesis_design",
                "tasks": [
                    {"task_id": "hypo_001", "description": "基于文献空白提出研究假设, 确保假设的创新性", "status": "pending", "priority": "high"},
                    {"task_id": "hypo_002", "description": "设计实验方案和对比方法", "status": "pending", "priority": "high"},
                    {"task_id": "hypo_003", "description": "确定评估指标和数据集", "status": "pending", "priority": "high"},
                    {"task_id": "hypo_004", "description": "设计消融实验验证各创新组件的贡献", "status": "pending", "priority": "high"},
                    {"task_id": "hypo_005", "description": "验证假设的创新性: 与现有方法对比, 说明独特贡献", "status": "pending", "priority": "high"},
                    {"task_id": "hypo_006", "description": "估算计算资源和时间需求", "status": "pending", "priority": "medium"},
                ]
            },
            {
                "phase": 3,
                "name": "coding",
                "tasks": [
                    {"task_id": "code_001", "description": "搭建项目代码结构", "status": "pending", "priority": "high"},
                    {"task_id": "code_002", "description": "实现数据处理模块", "status": "pending", "priority": "high"},
                    {"task_id": "code_003", "description": "实现核心算法/模型（确保有创新点）", "status": "pending", "priority": "high"},
                    {"task_id": "code_004", "description": "实现基线方法", "status": "pending", "priority": "high"},
                    {"task_id": "code_005", "description": "编写训练和评估脚本", "status": "pending", "priority": "high"},
                    {"task_id": "code_006", "description": "编写单元测试", "status": "pending", "priority": "medium"},
                    {"task_id": "code_007", "description": "测试代码可运行性", "status": "pending", "priority": "high"},
                ]
            },
            {
                "phase": 4,
                "name": "execution",
                "tasks": [
                    {"task_id": "exec_001", "description": "准备实验数据", "status": "pending", "priority": "high"},
                    {"task_id": "exec_002", "description": "运行小规模测试验证代码", "status": "pending", "priority": "high"},
                    {"task_id": "exec_003", "description": "运行基线方法实验", "status": "pending", "priority": "high"},
                    {"task_id": "exec_004", "description": "运行主要方法实验", "status": "pending", "priority": "high"},
                    {"task_id": "exec_005", "description": "运行消融实验验证各创新组件的贡献", "status": "pending", "priority": "high"},
                    {"task_id": "exec_006", "description": "收集和整理实验结果", "status": "pending", "priority": "high"},
                ]
            },
            {
                "phase": 5,
                "name": "analysis",
                "tasks": [
                    {"task_id": "anal_001", "description": "执行统计显著性检验", "status": "pending", "priority": "high"},
                    {"task_id": "anal_002", "description": "生成性能对比图表", "status": "pending", "priority": "high"},
                    {"task_id": "anal_003", "description": "分析实验结果并得出结论", "status": "pending", "priority": "high"},
                    {"task_id": "anal_004", "description": "识别异常结果并解释", "status": "pending", "priority": "medium"},
                    {"task_id": "anal_005", "description": "创新性验证:量化本研究相对于基线的改进程度", "status": "pending", "priority": "high"},
                ]
            },
            {
                "phase": 6,
                "name": "writing",
                "tasks": [
                    {"task_id": "write_001", "description": "撰写论文摘要", "status": "pending", "priority": "high"},
                    {"task_id": "write_002", "description": "撰写引言部分（明确研究动机和创新点)", "status": "pending", "priority": "high"},
                    {"task_id": "write_003", "description": "撰写相关工作部分（使用Phase1整理的文献)", "status": "pending", "priority": "high"},
                    {"task_id": "write_004", "description": "撰写方法部分(突出创新设计)", "status": "pending", "priority": "high"},
                    {"task_id": "write_005", "description": "撰写实验部分", "status": "pending", "priority": "high"},
                    {"task_id": "write_006", "description": "撰写结论部分", "status": "pending", "priority": "medium"},
                    {"task_id": "write_007", "description": "撰写贡献声明:明确列出本研究的创新贡献", "status": "pending", "priority": "high"},
                    {"task_id": "write_008", "description": "整合论文初稿,嵌入参考文献", "status": "pending", "priority": "high"},
                    {"task_id": "write_009", "description": "原创性检查:确保内容不是简单复制, 引用规范", "status": "pending", "priority": "high"},
                ]
            },
            {
                "phase": 7,
                "name": "humanization",
                "tasks": [
                    {"task_id": "human_001", "description": "【润色1】分析论文各章节的AI痕迹特征（句式重复、过度使用连接词、缺乏个人观点）", "status": "pending", "priority": "high"},
                    {"task_id": "human_002", "description": "【润色2】摘要去AI化:调整句式结构, 增加学术性表达, 降低AI检测分数", "status": "pending", "priority": "high"},
                    {"task_id": "human_003", "description": "【润色3】引言去AI化:增加研究动机的个人视角, 调整论证逻辑", "status": "pending", "priority": "high"},
                    {"task_id": "human_004", "description": "【润色4】相关工作去AI化:增加批判性分析, 体现作者学术观点", "status": "pending", "priority": "high"},
                    {"task_id": "human_005", "description": "【润色5】方法部分去AI化:增加设计决策的解释和理由", "status": "pending", "priority": "high"},
                    {"task_id": "human_006", "description": "【润色6】实验部分去AI化:增加结果解读的深度和洞见", "status": "pending", "priority": "high"},
                    {"task_id": "human_007", "description": "【润色7】结论去AI化:强调研究的独特贡献和未来展望", "status": "pending", "priority": "medium"},
                    {"task_id": "human_008", "description": "【润色8】全文语言润色:统一术语、修正语法、优化表达", "status": "pending", "priority": "high"},
                    {"task_id": "human_009", "description": "【润色9】AI检测评分:确保AI检测分数低于30%", "status": "pending", "priority": "high"},
                ]
            },
            {
                "phase": 8,
                "name": "latex_formatting",
                "tasks": [
                    {"task_id": "latex_001", "description": "【排版1】选择目标会议/期刊模板（NeurIPS/ICML/CHI/ACL等）", "status": "pending", "priority": "high"},
                    {"task_id": "latex_002", "description": "【排版2】创建LaTeX项目结构:main.tex, sections/, figures/, references.bib", "status": "pending", "priority": "high"},
                    {"task_id": "latex_003", "description": "【排版3】转换摘要到LaTeX格式", "status": "pending", "priority": "high"},
                    {"task_id": "latex_004", "description": "【排版4】转换引言到LaTeX格式", "status": "pending", "priority": "high"},
                    {"task_id": "latex_005", "description": "【排版5】转换相关工作到LaTeX格式, 确保引用格式正确", "status": "pending", "priority": "high"},
                    {"task_id": "latex_006", "description": "【排版6】转换方法部分到LaTeX格式, 添加算法伪代码", "status": "pending", "priority": "high"},
                    {"task_id": "latex_007", "description": "【排版7】转换实验部分到LaTeX格式, 插入图表", "status": "pending", "priority": "high"},
                    {"task_id": "latex_008", "description": "【排版8】转换结论到LaTeX格式", "status": "pending", "priority": "medium"},
                    {"task_id": "latex_009", "description": "【排版9】生成中文版本:翻译并排版中文PDF（使用ctex宏包）", "status": "pending", "priority": "medium"},
                    {"task_id": "latex_010", "description": "【排版10】编译英文版LaTeX, 检查并修复编译错误", "status": "pending", "priority": "high"},
                    {"task_id": "latex_011", "description": "【排版11】编译中文版LaTeX, 检查并修复编译错误", "status": "pending", "priority": "medium"},
                    {"task_id": "latex_012", "description": "【排版12】检查PDF输出: 页边距、字体、图表位置、引用格式", "status": "pending", "priority": "high"},
                ]
            },
            {
                "phase": 9,
                "name": "peer_review",
                "tasks": [
                    {"task_id": "review_001", "description": "自我检查论文完整性: 确保所有章节齐全", "status": "pending", "priority": "high"},
                    {"task_id": "review_002", "description": "检查参考文献格式和引用完整性", "status": "pending", "priority": "high"},
                    {"task_id": "review_003", "description": "创新性自我评估: 验证研究贡献的原创性和价值", "status": "pending", "priority": "high"},
                    {"task_id": "review_004", "description": "模拟三位审稿人评审, 记录问题和建议", "status": "pending", "priority": "high"},
                    {"task_id": "review_005", "description": "根据评审意见修改论文（修改LaTeX源文件)", "status": "pending", "priority": "high"},
                    {"task_id": "review_006", "description": "撰写审稿意见回复信(Response Letter)", "status": "pending", "priority": "high"},
                    {"task_id": "review_007", "description": "最终检查: 格式规范、页数限制、 匿名性要求", "status": "pending", "priority": "high"},
                    {"task_id": "review_008", "description": "生成提交包: 英文PDF + 中文PDF + 补充材料", "status": "pending", "priority": "high"},
                ]
            }
        ]

        # 计算总任务数
        total_tasks = sum(len(phase["tasks"]) for phase in phases)
        self.log("INFO", f"生成研究任务: 共 {total_tasks} 个任务")
        self.log("INFO", f"  - Phase 0 (topic_analysis): 4 个任务")
        self.log("INFO", f"  - Phase 1 (literature_review): 32 个任务")
        self.log("INFO", f"  - Phase 2 (hypothesis_design): 6 个任务")
        self.log("INFO", f"  - Phase 3 (coding): 7 个任务")
        self.log("INFO", f"  - Phase 4 (execution): 6 个任务")
        self.log("INFO", f"  - Phase 5 (analysis): 5 个任务")
        self.log("INFO", f"  - Phase 6 (writing): 9 个任务")
        self.log("INFO", f"  - Phase 7 (humanization): 9 个任务")
        self.log("INFO", f"  - Phase 8 (latex_formatting): 12 个任务")
        self.log("INFO", f"  - Phase 9 (peer_review): 8 个任务")

        # 保存任务文件
        tasks_data = {
            "project_info": {
                "title": "无人机集群在武警部队任务中的技战术研究",
                "title_en": "Research on Tactics and Techniques of UAV Swarm in Armed Police Force Missions",
                "created": datetime.now().strftime("%Y-%m-%d"),
                "status": "active",
                "description": "系统研究无人机集群技术在武警部队反恐维稳、抢险救援、边界管控等任务中的技战术应用"
            },
            "phases": phases
        }
        tasks_file = self.project_dir / self.config["tasks_file"]
        with open(tasks_file, "w", encoding="utf-8") as f:
            json.dump(tasks_data, f, indent=2, ensure_ascii=False)
        self.log("SUCCESS", f"研究任务文件已生成: {tasks_file}")

    # ==================== GEP 集成 ====================

    def _get_gep_selector(self):
        """延迟加载 GEP Selector"""
        if self._gep_selector is None and self.gep_config.get("enabled", True):
            try:
                # 动态导入 GEP 模块
                sys.path.insert(0, str(Path(__file__).parent.parent))
                from Core.gep.selector import get_selector
                self._gep_selector = get_selector(self.gep_config)
                self.log("INFO", "GEP Selector 已初始化")
            except ImportError as e:
                self.log("WARNING", f"GEP 模块未找到: {e}")
                self._gep_selector = None
            except Exception as e:
                self.log("WARNING", f"GEP 初始化失败: {e}")
                self._gep_selector = None
        return self._gep_selector

    def _extract_error_signal(self, error_output: str, task: dict) -> dict:
        """从错误输出中提取信号"""
        signal = {
            "error_type": "",
            "error_message": error_output[:500],
            "phase": task.get("phase_name", ""),
            "task_id": task.get("id", ""),
            "file_path": "",
            "line_number": 0,
            "traceback": ""
        }

        # 提取错误类型
        error_patterns = [
            (r"(\w+Error):", "error_type"),
            (r"(\w+Exception):", "error_type"),
            (r"Error:\s*(.+)", "error_message"),
            (r'File "([^"]+)"', "file_path"),
            (r'line (\d+)', "line_number"),
        ]

        for pattern, field in error_patterns:
            match = re.search(pattern, error_output)
            if match:
                if field == "line_number":
                    signal[field] = int(match.group(1))
                else:
                    signal[field] = match.group(1)

        # 提取 traceback
        traceback_match = re.search(r"Traceback.*?(?=\n\S|\Z)", error_output, re.DOTALL)
        if traceback_match:
            signal["traceback"] = traceback_match.group(0)[:1000]

        return signal

    def _get_gep_strategy_prompt(self, error_output: str, task: dict) -> str:
        """获取 GEP 推荐的修复策略"""
        selector = self._get_gep_selector()
        if not selector:
            return ""

        try:
            from Core.gep.models import Signal

            # 提取信号
            signal_data = self._extract_error_signal(error_output, task)
            signal = Signal(
                error_type=signal_data.get("error_type", ""),
                error_message=signal_data.get("error_message", ""),
                phase=signal_data.get("phase", ""),
                task_id=signal_data.get("task_id", ""),
                file_path=signal_data.get("file_path", ""),
                line_number=signal_data.get("line_number", 0),
                traceback=signal_data.get("traceback", "")
            )

            # 获取决策
            decision = selector.select(
                signal,
                max_genes=self.gep_config.get("max_genes", 3),
                max_capsules=self.gep_config.get("max_capsules", 5)
            )

            if decision.selected_gene:
                self.log("INFO", f"GEP 推荐策略: {decision.selected_gene} (置信度: {decision.confidence:.2%})")

                # 生成执行提示
                prompt = selector.get_execution_prompt(decision, {
                    "error_output": error_output[:1000],
                    "task_description": task.get("description", "")
                })
                return prompt

        except Exception as e:
            self.log("WARNING", f"GEP 策略获取失败: {e}")

        return ""

    def _record_gep_capsule(self, error_output: str, task: dict, action_taken: str, success: bool):
        """记录 GEP Capsule"""
        selector = self._get_gep_selector()
        if not selector:
            return

        try:
            from Core.gep.models import Signal

            signal_data = self._extract_error_signal(error_output, task)
            signal = Signal(
                error_type=signal_data.get("error_type", ""),
                error_message=signal_data.get("error_message", ""),
                phase=signal_data.get("phase", ""),
                task_id=signal_data.get("task_id", ""),
                file_path=signal_data.get("file_path", ""),
                line_number=signal_data.get("line_number", 0),
                traceback=signal_data.get("traceback", "")
            )

            # 获取决策
            decision = selector.select(signal)

            # 记录尝试
            event_id, capsule_id = selector.record_attempt(
                decision,
                action_taken,
                success,
                f"Task: {task.get('description', '')[:100]}",
                []  # blast_radius 需要实际追踪
            )

            if success and capsule_id:
                self.log("INFO", f"GEP Capsule 已创建: {capsule_id}")

        except Exception as e:
            self.log("WARNING", f"记录 GEP Capsule 失败: {e}")

    def _get_gep_strategy_prompt(self, error_output: str, task: dict) -> str:
        """获取 GEP 策略提示（用于注入到主提示中）"""
        selector = self._get_gep_selector()
        if not selector:
            return ""

        try:
            from Core.gep.models import Signal

            signal_data = self._extract_error_signal(error_output, task)
            signal = Signal(
                error_type=signal_data.get("error_type", ""),
                error_message=signal_data.get("error_message", ""),
                phase=signal_data.get("phase", ""),
                task_id=signal_data.get("task_id", ""),
                file_path=signal_data.get("file_path", ""),
                line_number=signal_data.get("line_number", 0),
                traceback=signal_data.get("traceback", "")
            )

            # 获取决策
            decision = selector.select(
                signal,
                max_genes=self.gep_config.get("max_genes", 3),
                max_capsules=self.gep_config.get("max_capsules", 5)
            )

            if decision.selected_gene:
                self.log("INFO", f"GEP 推荐策略: {decision.selected_gene} (置信度: {decision.confidence:.2%})")

                # 生成执行提示
                prompt = selector.get_execution_prompt(decision, {
                    "error_output": error_output[:1000],
                    "task_description": task.get("description", "")
                })
                return prompt

        except Exception as e:
            self.log("WARNING", f"GEP 策略获取失败: {e}")

        return ""

    def get_gep_stats(self) -> dict:
        """获取 GEP 统计信息"""
        selector = self._get_gep_selector()
        if selector:
            try:
                return selector.get_status()
            except Exception as e:
                self.log("WARNING", f"获取 GEP 状态失败: {e}")
        return {}

    # ==================== 任务管理 ====================

    def load_tasks(self) -> List[dict]:
        """从 research_tasks.json 加载任务"""
        if not self.tasks_file.exists():
            self.log("ERROR", f"任务文件不存在: {self.tasks_file}")
            return []

        try:
            with open(self.tasks_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            self.log("ERROR", f"读取任务文件失败: {e}")
            return []

        # 展平所有任务
        tasks = []
        for phase in data.get("phases", []):
            phase_num = phase.get("phase", 0)
            phase_name = phase.get("name", "")
            for task in phase.get("tasks", []):
                # 兼容 "id" 和 "task_id" 两种字段名
                task_id = task.get("task_id") or task.get("id") or ""
                tasks.append({
                    "id": task_id,  # 内部统一使用 id
                    "description": task.get("description", ""),
                    "status": task.get("status", "pending"),
                    "priority": task.get("priority", "medium"),
                    "phase": phase_num,
                    "phase_name": phase_name
                })

        return tasks

    def save_tasks(self, tasks: List[dict]):
        """保存任务到 research_tasks.json"""
        # 按 phase 重新组织
        phases_dict = {}
        for task in tasks:
            phase_num = task["phase"]
            if phase_num not in phases_dict:
                phases_dict[phase_num] = {
                    "phase": phase_num,
                    "name": task["phase_name"],
                    "tasks": []
                }
            phases_dict[phase_num]["tasks"].append({
                "task_id": task["id"],  # 统一使用 task_id 保存
                "description": task["description"],
                "status": task["status"],
                "priority": task["priority"]
            })

        # 读取原始文件获取其他字段
        try:
            with open(self.tasks_file, "r", encoding="utf-8") as f:
                original = json.load(f)
        except:
            original = {}

        original["phases"] = [phases_dict[k] for k in sorted(phases_dict.keys())]

        with open(self.tasks_file, "w", encoding="utf-8") as f:
            json.dump(original, f, indent=2, ensure_ascii=False)

    def get_next_task(self, tasks: List[dict]) -> Optional[dict]:
        """获取下一个待执行任务"""
        for task in tasks:
            if task["status"] == "pending":
                return task
        return None

    def mark_task_complete(self, task_id: str):
        """标记任务完成"""
        tasks = self.load_tasks()
        for task in tasks:
            if task["id"] == task_id:
                task["status"] = "completed"
                break
        self.save_tasks(tasks)
        self.log("INFO", f"任务 {task_id} 已标记为完成")

    def mark_task_failed(self, task_id: str):
        """标记任务失败"""
        tasks = self.load_tasks()
        for task in tasks:
            if task["id"] == task_id:
                task["status"] = "failed"
                break
        self.save_tasks(tasks)
        self.log("WARNING", f"任务 {task_id} 已标记为失败")

    def is_ralph_enabled_for_phase(self, phase_name: str) -> bool:
        """检查当前阶段是否启用 Ralph Loop"""
        if not self.ralph_config.get("enabled", True):
            return False

        phases_enabled = self.ralph_config.get("phases_enabled", {})

        # 精确匹配阶段名（不使用模糊匹配）
        # 标准化阶段名：小写、下划线
        phase_normalized = phase_name.lower().replace(" ", "_").replace("-", "_")

        # 定义明确的阶段映射
        phase_mapping = {
            "topic_analysis": ["topic_analysis", "topic"],
            "literature_review": ["literature_review", "literature"],
            "hypothesis_design": ["hypothesis_design", "hypothesis"],
            "coding": ["coding", "code", "implementation"],
            "execution": ["execution", "experiment"],
            "analysis": ["analysis", "data_analysis"],  # 注意：只匹配数据分析，不是 topic_analysis
            "writing": ["writing", "paper"],
            "humanization": ["humanization", "polish"],
            "latex": ["latex", "formatting"],
            "review": ["review", "peer_review"],
        }

        # 查找当前阶段对应的类别
        for category, aliases in phase_mapping.items():
            if phase_normalized in aliases or any(alias in phase_normalized for alias in aliases):
                # 特殊处理：topic_analysis 不应该匹配 analysis
                if category == "analysis" and "topic" in phase_normalized:
                    continue
                if category == "analysis" and "literature" in phase_normalized:
                    continue
                # 检查该类别是否启用
                return phases_enabled.get(category, False)

        return False

    def check_completion_promise(self, output: str) -> bool:
        """检测输出中的完成承诺标记"""
        promise_tag = self.ralph_config.get("completion_promise", "TASK_COMPLETE")

        # 检查精确匹配
        if f"<promise>{promise_tag}</promise>" in output:
            return True

        # 检查正则匹配
        matches = PROMISE_PATTERN.findall(output)
        for match in matches:
            if match.strip().upper() == promise_tag.upper():
                return True
            # 也接受通用完成标记
            if match.strip().upper() in ['COMPLETE', 'DONE', 'FINISHED', 'TASK_COMPLETE']:
                return True

        return False

    def generate_prompt(self, task: dict, iteration: int = 0, previous_output: str = "") -> str:
        """生成执行提示，支持 Ralph Loop"""
        ralph_enabled = self.is_ralph_enabled_for_phase(task.get("phase_name", ""))
        max_iter = self.ralph_config.get("max_iterations", 20)
        promise_tag = self.ralph_config.get("completion_promise", "TASK_COMPLETE")

        prompt = f"""# 任务执行指令

## 当前任务
- **任务ID**: {task['id']}
- **阶段**: Phase {task['phase']} - {task['phase_name']}
- **描述**: {task['description']}
- **优先级**: {task['priority']}
"""

        # 如果启用 Ralph Loop，添加迭代信息
        if ralph_enabled:
            prompt += f"""
## Ralph Loop 模式 (迭代 {iteration + 1}/{max_iter})
- 此任务处于**深度迭代模式**
- 你可以多次迭代完善，直到任务真正完成
- **完成后必须在输出中包含**: `<promise>{promise_tag}</promise>`
- 如果遇到问题，可以继续迭代解决，不要轻易放弃

"""
            if previous_output and iteration > 0:
                prompt += f"""### 上次迭代摘要
```
{previous_output[:1500]}...
```

请基于上次迭代继续完善。

"""

        prompt += f"""## 执行步骤

1. 理解任务描述，明确任务目标
2. 查看项目目录结构和已有文件
3. 执行任务，创建或修改必要文件
4. 完成后标记任务状态:
   - 调用 `python run_workflow.py --complete {task['id']}`
5. 提交 git 更改:
   ```bash
   git add -A
   git commit -m "完成 {task['id']}: {task['description'][:50]}"
   ```

## 项目信息
- **项目目录**: {self.project_dir}
- **研究主题**: 可见光相干光衍射成像实现彩色成像

## 目录结构
```
{self.project_dir}/
├── research_tasks.json    # 任务定义文件
├── notes/                 # 研究笔记
│   ├── papers/           # 论文笔记
│   └── *.md              # 各类文档
├── data/                  # 数据文件
│   └── literature_db.json # 文献数据库
├── code/                  # 源代码
│   └── src/              # 核心模块
├── results/               # 结果输出
└── logs/                  # 日志文件
```

## 注意事项
- 完成后必须更新任务状态
- 产出文件应放在正确目录
- 代码需要包含注释
"""

        if ralph_enabled:
            prompt += f"""
---

**重要**: 任务完全完成后，在输出末尾添加 `<promise>{promise_tag}</promise>` 标记。
"""

        prompt += f"""
---

请开始执行任务 {task['id']}。
"""
        return prompt

    def save_prompt(self, task: dict) -> Path:
        """保存提示到文件"""
        prompt = self.generate_prompt(task)
        prompt_file = self.prompts_dir / f"{task['id']}_prompt.md"
        with open(prompt_file, "w", encoding="utf-8") as f:
            f.write(prompt)
        return prompt_file

    def run_claude_code(self, prompt: str, timeout: int = None, retry_on_rate_limit: bool = True) -> Tuple[bool, str]:
        """执行 Claude Code，带心跳日志和限流退避"""
        if timeout is None:
            timeout = self.ralph_config.get("iteration_timeout", 300)

        # 添加请求延迟，防止 API 限流
        api_delay = self.config.get("api_request_delay", 10)  # 默认改为10秒
        if api_delay > 0:
            self.log("INFO", f"等待 {api_delay}s 后发送请求...")
            time.sleep(api_delay)

        cmd = [
            self.claude_cmd,
            "--permission-mode", self.permission_mode,
            "-p", prompt
        ]

        self.log("INFO", f"执行: claude --permission-mode {self.permission_mode} (超时: {timeout}s)")

        try:
            # 使用 Popen 实现心跳日志
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(self.project_dir),
                env={**os.environ, 'PYTHONIOENCODING': 'utf-8'}
            )

            # 心跳日志：每30秒输出一次进度
            heartbeat_interval = 30
            elapsed = 0

            while process.poll() is None and elapsed < timeout:
                try:
                    # 等待30秒或进程结束
                    process.wait(timeout=heartbeat_interval)
                except subprocess.TimeoutExpired:
                    elapsed += heartbeat_interval
                    remaining = timeout - elapsed
                    self.log("INFO", f"[心跳] 执行中... 已用时 {elapsed}s, 剩余 {remaining}s")

            if process.poll() is None:
                # 超时，终止进程
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                return False, f"迭代超时 ({timeout}s)"

            # 读取输出
            stdout_data, stderr_data = process.communicate()
            stdout = stdout_data.decode('utf-8', errors='replace')
            stderr = stderr_data.decode('utf-8', errors='replace')

            if process.returncode == 0:
                return True, stdout
            else:
                # 检查是否为 API 限流错误 (429)
                error_output = stderr or stdout
                if retry_on_rate_limit and ("429" in error_output or "Rate limit" in error_output):
                    self.log("WARNING", "API 限流，将使用指数退避重试")
                    return self._retry_with_backoff(prompt, timeout)

                return False, error_output

        except FileNotFoundError:
            return False, f"找不到 claude 命令: {self.claude_cmd}"
        except Exception as e:
            return False, str(e)

    def _retry_with_backoff(self, prompt: str, timeout: int, max_retries: int = 3) -> Tuple[bool, str]:
        """指数退避重试机制，用于处理 API 限流"""
        base_delay = 10  # 基础延迟 10 秒

        for attempt in range(max_retries):
            # 指数退避: 10s, 20s, 40s
            delay = base_delay * (2 ** attempt)
            self.log("INFO", f"限流重试 {attempt + 1}/{max_retries}，等待 {delay}s...")
            time.sleep(delay)

            # 递归调用 run_claude_code，但禁用重试避免无限循环
            success, output = self.run_claude_code(prompt, timeout, retry_on_rate_limit=False)

            if success:
                self.log("INFO", f"重试成功!")
                return True, output

            # 如果仍然限流，继续重试
            if "429" in output or "Rate limit" in output:
                if attempt < max_retries - 1:
                    continue

            # 其他错误直接返回
            return False, output

        return False, f"重试 {max_retries} 次后仍然失败"

    def execute_task(self, task: dict, retry: int = 0) -> bool:
        """执行单个任务，支持 Ralph Loop 深度迭代和 GEP 错误恢复"""
        self.log("INFO", f"开始执行: {task['id']} - {task['description'][:50]}")

        ralph_enabled = self.is_ralph_enabled_for_phase(task.get("phase_name", ""))
        max_ralph_iter = self.ralph_config.get("max_iterations", 20)
        gep_enabled = self.gep_config.get("enabled", True)

        if ralph_enabled:
            self.log("INFO", f"Ralph Loop 模式启用 (最大 {max_ralph_iter} 次迭代)")
        if gep_enabled:
            self.log("INFO", "GEP 错误恢复已启用")

        # Ralph Loop 迭代
        iteration = 0
        previous_output = ""
        last_success = False
        last_output = ""
        gep_used = False  # 跟踪是否使用了 GEP

        while True:
            iteration += 1

            if ralph_enabled:
                self.log("INFO", f"Ralph Loop 迭代 {iteration}/{max_ralph_iter}")
                if iteration > max_ralph_iter:
                    self.log("WARNING", f"达到 Ralph Loop 最大迭代次数，检查最后状态...")
                    # 检查最后一次是否成功
                    if last_success:
                        self.log("SUCCESS", f"任务 {task['id']} 在 {max_ralph_iter} 次迭代后完成")
                        self.mark_task_complete(task['id'])
                        self.git_commit(task)
                        # 记录成功的 GEP Capsule
                        if gep_used and last_output:
                            self._record_gep_capsule(last_output, task, "Ralph Loop 迭代修复", True)
                        return True
                    else:
                        break  # 退出循环，进入重试逻辑
            else:
                # 非 Ralph Loop 模式，只执行一次
                if iteration > 1:
                    break

            # 生成提示
            prompt = self.generate_prompt(task, iteration - 1, previous_output)

            # 如果之前失败且启用了 GEP，注入 GEP 策略
            if previous_output and gep_enabled and iteration > 1:
                gep_prompt = self._get_gep_strategy_prompt(previous_output, task)
                if gep_prompt:
                    prompt += f"\n\n---\n\n# GEP 推荐修复策略\n\n{gep_prompt}"
                    gep_used = True
                    self.log("INFO", "已注入 GEP 修复策略")

            prompt_file = self.save_prompt(task)
            self.log("INFO", f"提示文件: {prompt_file}")

            # 执行
            success, output = self.run_claude_code(prompt)
            last_success = success
            last_output = output

            if success:
                # 任务执行成功即完成
                self.log("SUCCESS", f"任务 {task['id']} 执行成功 (迭代 {iteration} 次)")
                self.mark_task_complete(task['id'])
                self.git_commit(task)
                # 记录成功的 GEP Capsule
                if gep_used and previous_output:
                    self._record_gep_capsule(previous_output, task, "GEP 辅助修复", True)
                return True
            else:
                # 执行失败
                self.log("WARNING", f"迭代 {iteration} 失败: {output[:200]}")

                if ralph_enabled and iteration < max_ralph_iter:
                    # Ralph Loop 模式，继续迭代尝试
                    previous_output = output[:500]
                    time.sleep(5)
                    continue
                else:
                    break  # 退出循环，进入重试逻辑

        # 所有迭代都失败，进入重试逻辑
        if retry < self.config["retry_count"]:
            # 还有重试次数，使用 WARNING
            self.log("WARNING", f"任务 {task['id']} 迭代失败 (将重试): {last_output[:200]}")
            self.log("INFO", f"重试 {retry + 1}/{self.config['retry_count']}...")
            time.sleep(self.config["retry_delay"])
            return self.execute_task(task, retry + 1)

        # 所有重试都失败，才记录 ERROR
        self.log("ERROR", f"任务 {task['id']} 执行失败 (已重试 {retry} 次): {last_output[:200]}")

        # 记录失败的 GEP Capsule（用于学习）
        if gep_used and last_output:
            self._record_gep_capsule(last_output, task, "GEP 修复失败", False)

        self.mark_task_failed(task['id'])
        return False

    def _get_commit_type(self, task: dict) -> str:
        """根据任务阶段确定 Conventional Commits 类型"""
        # 阶段到提交类型的映射
        phase_types = {
            "topic": "docs",           # Phase 0: 主题分析
            "literature": "docs",      # Phase 1: 文献综述
            "hypothesis": "docs",      # Phase 2: 假设设计
            "coding": "feat",          # Phase 3: 代码实现
            "execution": "test",       # Phase 4: 实验执行
            "analysis": "analysis",    # Phase 5: 结果分析 (自定义类型)
            "writing": "docs",         # Phase 6: 论文撰写
            "humanization": "style",   # Phase 7: 人性化处理
            "latex": "docs",           # Phase 8: LaTeX 格式化
            "review": "fix",           # Phase 9: 同行评审修改
        }

        # 从任务 ID 提取阶段信息 (如 "T001" -> phase 0, "lit_001" -> literature)
        task_id = task.get("id", "").lower()

        # 检查任务 ID 前缀
        for prefix, commit_type in phase_types.items():
            if task_id.startswith(prefix[:3]):
                return commit_type

        # 根据任务 ID 数字判断阶段
        if task_id.startswith("t"):
            try:
                num = int(task_id[1:4])
                if num <= 4:
                    return "docs"       # Phase 0
                elif num <= 38:
                    return "docs"       # Phase 1
                elif num <= 44:
                    return "docs"       # Phase 2
                elif num <= 51:
                    return "feat"       # Phase 3
                elif num <= 57:
                    return "test"       # Phase 4
                elif num <= 62:
                    return "analysis"   # Phase 5
                elif num <= 71:
                    return "docs"       # Phase 6
                elif num <= 80:
                    return "style"      # Phase 7
                elif num <= 92:
                    return "docs"       # Phase 8
                else:
                    return "fix"        # Phase 9
            except ValueError:
                pass

        return "chore"  # 默认类型

    def _get_commit_scope(self, task: dict) -> str:
        """根据任务内容确定提交范围"""
        task_id = task.get("id", "")
        description = task.get("description", "").lower()

        # 从任务 ID 提取范围
        if task_id.startswith("lit"):
            return "literature"
        elif task_id.startswith("hypo"):
            return "hypothesis"
        elif task_id.startswith("code"):
            return "code"
        elif task_id.startswith("exec"):
            return "execution"
        elif task_id.startswith("anal"):
            return "analysis"
        elif task_id.startswith("write"):
            return "writing"

        # 从描述中提取范围
        scope_keywords = {
            "literature": ["文献", "论文", "paper", "literature", "review"],
            "code": ["代码", "实现", "code", "implement", "algorithm"],
            "experiment": ["实验", "experiment", "test", "评估"],
            "writing": ["撰写", "写作", "write", "paper", "论文"],
            "latex": ["latex", "格式", "format"],
        }

        for scope, keywords in scope_keywords.items():
            for kw in keywords:
                if kw in description:
                    return scope

        return "research"

    def git_commit(self, task: dict):
        """提交 git 更改 - 使用 Conventional Commits 格式

        格式: <type>(<scope>): <subject>

        遵循 git-commit skill 规范，自动根据任务阶段确定类型和范围。
        """
        try:
            # 检查是否已初始化 Git 仓库
            git_dir = self.project_dir / ".git"
            if not git_dir.exists():
                self.log("INFO", "初始化 Git 仓库...")
                init_result = subprocess.run(
                    ["git", "init"],
                    cwd=str(self.project_dir),
                    capture_output=True, text=True
                )
                if init_result.returncode != 0:
                    self.log("WARNING", f"Git init 失败: {init_result.stderr}")
                    return

            # 检查是否有变更
            status_result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=str(self.project_dir),
                capture_output=True, text=True
            )
            if not status_result.stdout.strip():
                self.log("DEBUG", "Git: 没有变更需要提交")
                return

            subprocess.run(["git", "add", "-A"], cwd=str(self.project_dir), capture_output=True)

            # 使用 Conventional Commits 格式
            commit_type = self._get_commit_type(task)
            scope = self._get_commit_scope(task)
            subject = task.get("description", "完成任务")[:50]

            # 格式: type(scope): subject
            commit_msg = f"{commit_type}({scope}): {subject}"

            # 添加任务 ID 作为 body
            body = f"\n\nTask: {task.get('id', 'unknown')}"

            result = subprocess.run(
                ["git", "commit", "-m", commit_msg + body],
                cwd=str(self.project_dir),
                capture_output=True, text=True
            )

            if result.returncode == 0:
                self.log("INFO", f"Git 提交: {commit_msg}")
            else:
                # 打印详细错误信息
                stderr = result.stderr.strip()
                if "nothing to commit" in stderr or "nothing added" in stderr:
                    self.log("DEBUG", "Git: 没有变更需要提交")
                elif "not a git repository" in stderr:
                    self.log("WARNING", f"Git: 不是有效的 Git 仓库")
                else:
                    self.log("WARNING", f"Git 提交失败: {stderr[:200]}")
        except Exception as e:
            self.log("WARNING", f"Git 操作失败: {e}")

    def run_once(self) -> bool:
        """执行单个任务"""
        tasks = self.load_tasks()
        if not tasks:
            self.log("ERROR", "没有找到任务")
            return False

        task = self.get_next_task(tasks)
        if not task:
            self.log("INFO", "所有任务已完成!")
            return True

        state = self.load_state()
        state["current_iteration"] += 1
        state["last_task"] = task["id"]

        success = self.execute_task(task)

        if success:
            state["completed_tasks"].append(task["id"])
        else:
            state["failed_tasks"].append(task["id"])

        self.save_state(state)
        return success

    def run_loop(self):
        """循环执行所有任务"""
        # 获取进程锁，防止多实例运行
        if not self._acquire_lock():
            self.log("ERROR", "另一个执行器实例正在运行，退出")
            safe_print("提示: 如需强制运行，请删除锁文件: " + str(self.lock_file))
            return

        try:
            self.log("INFO", "=" * 50)
            self.log("INFO", "开始循环执行任务")
            self.log("INFO", f"Ralph Loop: {'启用' if self.ralph_config.get('enabled', True) else '禁用'}")
            self.log("INFO", "=" * 50)

            iteration = 0
            consecutive_failures = 0

            while iteration < self.config["max_iterations"]:
                iteration += 1

                self.log("INFO", f"--- 迭代 {iteration} ---")

                tasks = self.load_tasks()
                task = self.get_next_task(tasks)

                if not task:
                    self.log("SUCCESS", "所有任务已完成!")
                    break

                state = self.load_state()
                state["current_iteration"] = iteration
                state["last_task"] = task["id"]
                self.save_state(state)

                success = self.execute_task(task)

                if success:
                    state["completed_tasks"].append(task["id"])
                    consecutive_failures = 0
                else:
                    state["failed_tasks"].append(task["id"])
                    consecutive_failures += 1

                    # 连续失败超过3次则暂停
                    if consecutive_failures >= 3:
                        self.log("ERROR", "连续失败3次，暂停执行")
                        break

                self.save_state(state)
                time.sleep(2)

            # 输出统计
            state = self.load_state()
            self.log("INFO", "=" * 50)
            self.log("INFO", f"执行完成: {iteration} 次迭代")
            self.log("INFO", f"成功: {len(state['completed_tasks'])}")
            self.log("INFO", f"失败: {len(state['failed_tasks'])}")
            self.log("INFO", "=" * 50)

        finally:
            # 释放进程锁
            self._release_lock()

    def show_status(self):
        """显示任务状态"""
        tasks = self.load_tasks()
        state = self.load_state()

        print("\n" + "=" * 60)
        print("Project Prometheus - 任务状态")
        print("=" * 60)

        completed = sum(1 for t in tasks if t["status"] == "completed")
        pending = sum(1 for t in tasks if t["status"] == "pending")
        failed = sum(1 for t in tasks if t["status"] == "failed")
        total = len(tasks)

        print(f"\n总任务: {total}")
        print(f"已完成: {completed}")
        print(f"待处理: {pending}")
        print(f"失败: {failed}")
        print(f"完成率: {completed/total*100:.1f}%" if total > 0 else "0%")

        if state.get("last_task"):
            print(f"\n最后执行: {state['last_task']}")

        next_task = self.get_next_task(tasks)
        if next_task:
            print(f"\n下一个任务: {next_task['id']}")
            print(f"  描述: {next_task['description'][:60]}")
            print(f"  阶段: Phase {next_task['phase']} - {next_task['phase_name']}")

        # 显示前10个待处理任务
        print("\n" + "-" * 40)
        print("待处理任务 (前10个):")
        count = 0
        for t in tasks:
            if t["status"] == "pending" and count < 10:
                print(f"  [ ] {t['id']}: {t['description'][:50]}")
                count += 1

        # 显示 GEP 状态
        if self.gep_config.get("enabled", True):
            print("\n" + "-" * 40)
            print("GEP 演化状态:")
            gep_stats = self.get_gep_stats()
            if gep_stats:
                genes = gep_stats.get("genes", {})
                capsules = gep_stats.get("capsules", {})
                events = gep_stats.get("events", {})

                print(f"  Gene 库: {genes.get('total_genes', 0)} 个策略")
                print(f"  总使用: {genes.get('total_uses', 0)} 次")
                print(f"  成功率: {genes.get('overall_success_rate', 0):.1%}")
                print(f"  Capsule: {capsules.get('total_capsules', 0)} 个经验")
                print(f"  事件链: {events.get('total_events', 0)} 条记录")

                if genes.get("most_used_gene"):
                    print(f"  最常用: {genes['most_used_gene']} ({genes['most_used_count']}次)")
            else:
                print("  GEP 未初始化")

        print("=" * 60)

    def show_gep_status(self):
        """显示 GEP 演化状态"""
        print("\n" + "=" * 60)
        print("GEP (Gene Evolution Protocol) 演化状态")
        print("=" * 60)

        gep_stats = self.get_gep_stats()
        if not gep_stats:
            print("\nGEP 未初始化或无数据")
            print("=" * 60)
            return

        # Gene 统计
        genes = gep_stats.get("genes", {})
        print("\n## Gene 库")
        print(f"  总策略数: {genes.get('total_genes', 0)}")
        print(f"  总使用次数: {genes.get('total_uses', 0)}")
        print(f"  整体成功率: {genes.get('overall_success_rate', 0):.1%}")
        if genes.get("most_used_gene"):
            print(f"  最常用 Gene: {genes['most_used_gene']} ({genes['most_used_count']}次)")
        if genes.get("most_successful_gene"):
            print(f"  最成功 Gene: {genes['most_successful_gene']} ({genes['most_successful_rate']:.1%})")

        # Capsule 统计
        capsules = gep_stats.get("capsules", {})
        print("\n## Capsule 经验库")
        print(f"  总 Capsule 数: {capsules.get('total_capsules', 0)}")
        print(f"  平均置信度: {capsules.get('avg_confidence', 0):.2f}")
        print(f"  总复用次数: {capsules.get('total_uses', 0)}")

        # 事件链统计
        events = gep_stats.get("events", {})
        print("\n## 事件链")
        print(f"  总事件数: {events.get('total_events', 0)}")
        if events.get("by_type"):
            print("  按类型:")
            for event_type, count in events["by_type"].items():
                print(f"    - {event_type}: {count}")

        # 配置
        config = gep_stats.get("config", {})
        print("\n## 配置")
        print(f"  Gene 权重: {config.get('gene_weight', 0.5)}")
        print(f"  Capsule 权重: {config.get('capsule_weight', 0.3)}")
        print(f"  历史权重: {config.get('history_weight', 0.2)}")
        print(f"  最小置信度: {config.get('min_confidence', 0.3)}")

        print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Project Prometheus - 自动任务执行器")
    parser.add_argument("--loop", "-l", action="store_true", help="循环执行所有任务")
    parser.add_argument("--status", "-s", action="store_true", help="显示任务状态")
    parser.add_argument("--init", "-i", action="store_true", help="初始化项目")
    parser.add_argument("--gep-status", "-g", action="store_true", help="显示 GEP 演化状态")
    parser.add_argument("--project", type=str, default=None, help="项目目录")

    args = parser.parse_args()

    executor = TaskExecutor(args.project)

    if args.status:
        executor.show_status()
    elif args.gep_status:
        executor.show_gep_status()
    elif args.loop:
        executor.run_loop()
    elif args.init:
        print("初始化项目...")
        (executor.project_dir / "notes" / "papers").mkdir(parents=True, exist_ok=True)
        (executor.project_dir / "data").mkdir(exist_ok=True)
        (executor.project_dir / "code" / "src").mkdir(parents=True, exist_ok=True)
        (executor.project_dir / "results").mkdir(exist_ok=True)
        (executor.project_dir / "logs").mkdir(exist_ok=True)

        # 从模板生成研究任务
        executor.generate_research_tasks()

        print("初始化完成!")
    else:
        executor.run_once()


if __name__ == "__main__":
    main()

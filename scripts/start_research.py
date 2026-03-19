#!/usr/bin/env python3
"""
Project Prometheus - 研究主题启动器
====================================

根据用户提供的研究主题，自动生成任务清单并启动自动执行。

用法:
    python start_research.py --topic "你的研究主题"
    python start_research.py --topic "Transformer在时间序列预测中的应用" --auto-run

示例:
    # 仅生成任务清单
    python start_research.py --topic "基于图神经网络的社交推荐系统"

    # 生成任务清单并自动执行
    python start_research.py --topic "Transformer在时间序列预测中的应用" --auto-run

    # 指定项目名称
    python start_research.py --topic "xxx" --name "my_project" --auto-run
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# 项目根目录 (scripts 的父目录)
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
TASKS_FILE = PROJECT_ROOT / "Projects" / "current" / "research_tasks.json"
STATE_FILE = PROJECT_ROOT / "Projects" / "current" / "state.json"


def generate_task_generation_prompt(topic: str) -> str:
    """生成用于创建任务清单的 Prompt"""
    return f"""# Project Prometheus - 研究任务规划

## 研究主题
{topic}

## 你的任务

请根据上述研究主题，按照 Project Prometheus 的 7 阶段研究流程，创建详细的任务清单。

### 7 阶段研究流程

1. **Phase 1: 文献调研 (Literature Review)**
   - 搜索相关论文
   - 阅读和分析文献
   - 识别研究空白 (Research Gap)

2. **Phase 2: 假设设计 (Hypothesis Design)**
   - 提出研究假设
   - 设计实验方案
   - 评估资源需求

3. **Phase 3: 编码实现 (Coding)**
   - 搭建项目结构
   - 实现核心算法
   - 编写测试代码

4. **Phase 4: 实验执行 (Execution)**
   - 运行实验
   - 监控进度
   - 处理异常

5. **Phase 5: 数据分析 (Analysis)**
   - 统计检验
   - 可视化结果
   - 解读发现

6. **Phase 6: 论文撰写 (Writing)**
   - 撰写初稿
   - 添加图表
   - 完善引用

7. **Phase 7: 同行评审 (Peer Review)**
   - 自我检查
   - 模拟评审
   - 修改完善

### 输出要求

请创建文件 `Projects/current/research_tasks.json`，格式如下：

```json
{{
  "project_name": "项目名称",
  "topic": "{topic}",
  "created_at": "2026-02-16T00:00:00",
  "phases": [
    {{
      "phase": 1,
      "name": "Literature Review",
      "tasks": [
        {{
          "id": "T001",
          "description": "任务描述",
          "status": "pending",
          "priority": "high",
          "dependencies": []
        }}
      ]
    }}
  ]
}}
```

### 任务拆分原则

1. 每个任务应该是一个明确的、可验证的工作单元
2. 任务粒度适中（5-30分钟可完成）
3. 高优先级任务应该先执行
4. 标注任务之间的依赖关系
5. 每个 Phase 应该有 5-15 个任务

### 开始工作

请现在开始创建任务清单文件 `Projects/current/research_tasks.json`。
确保目录存在，如果不存在请创建。
完成后不要创建其他文件，只创建这个 JSON 文件。
"""


def run_claude_for_tasks(prompt: str, timeout: int = 300) -> bool:
    """调用 Claude 生成任务清单"""
    print("正在调用 Claude 生成任务清单...")

    is_windows = sys.platform == 'win32'

    try:
        result = subprocess.run(
            ['claude',
             '--print',
             '--permission-mode', 'bypassPermissions',
             '--dangerously-skip-permissions'],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=PROJECT_ROOT,
            shell=is_windows,
            encoding='utf-8',
            errors='replace'
        )

        if result.stdout:
            print(f"Claude 输出: {result.stdout[:500]}...")
        if result.stderr:
            print(f"Claude 提示: {result.stderr[:300]}...")

        return result.returncode == 0

    except subprocess.TimeoutExpired:
        print(f"Claude 执行超时 ({timeout}秒)")
        return False
    except Exception as e:
        print(f"Claude 执行异常: {e}")
        return False


def create_project_structure(project_name: str):
    """创建项目目录结构"""
    project_dir = PROJECT_ROOT / "Projects" / project_name
    project_dir.mkdir(parents=True, exist_ok=True)

    # 创建子目录
    (project_dir / "experiments").mkdir(exist_ok=True)
    (project_dir / "data").mkdir(exist_ok=True)
    (project_dir / "results").mkdir(exist_ok=True)
    (project_dir / "notes").mkdir(exist_ok=True)
    (project_dir / "code").mkdir(exist_ok=True)

    return project_dir


def create_initial_state(topic: str, project_name: str):
    """创建初始状态文件"""
    state = {
        "project_name": project_name,
        "topic": topic,
        "current_phase": 1,
        "current_task": None,
        "status": "initialized",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "checkpoints": [],
        "metrics": {
            "papers_reviewed": 0,
            "experiments_run": 0,
            "tests_passed": 0,
            "commits_made": 0
        }
    }

    state_file = PROJECT_ROOT / "Projects" / project_name / "state.json"
    with open(state_file, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

    return state_file


def verify_tasks_file(tasks_file: Path) -> bool:
    """验证任务文件是否有效"""
    if not tasks_file.exists():
        return False

    try:
        with open(tasks_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 检查必要字段
        if "phases" not in data:
            return False

        total_tasks = sum(len(p.get("tasks", [])) for p in data["phases"])
        return total_tasks > 0

    except (json.JSONDecodeError, KeyError):
        return False


def create_default_tasks(topic: str, project_name: str) -> Path:
    """创建默认的任务清单（如果 Claude 生成失败）

    标准版本 v4.0 - 10阶段完整工作流:
    - Phase 0: 主题分析 (4个任务)
    - Phase 1: 文献综述 (34个任务) - 多关键词搜索、真实下载、逐篇研读
    - Phase 2: 假设设计 (6个任务)
    - Phase 3: 代码实现 (7个任务)
    - Phase 4: 实验执行 (6个任务)
    - Phase 5: 结果分析 (5个任务)
    - Phase 6: 论文撰写 (9个任务) - Markdown格式
    - Phase 7: 去AI化润色 (9个任务) - 降低AI痕迹
    - Phase 8: LaTeX双语排版 (12个任务) - 中英文PDF
    - Phase 9: 同行评审 (8个任务) - 模拟评审、修改、提交
    - 总任务数: 100个

    注意：此工作流为标准流程，任何研究项目都应遵循相同的阶段和任务结构。
    """
    tasks = {
        "project_name": project_name,
        "topic": topic,
        "created_at": datetime.now().isoformat(),
        "phases": [
            # ===== Phase 0: 主题分析 =====
            {
                "phase": 0,
                "name": "Topic Analysis",
                "tasks": [
                    {"id": "T001", "description": "分析研究主题，提取核心研究方向、关键概念和研究问题", "status": "pending", "priority": "high"},
                    {"id": "T002", "description": "识别主题涉及的研究领域和交叉学科", "status": "pending", "priority": "high"},
                    {"id": "T003", "description": "明确研究目标和预期贡献", "status": "pending", "priority": "high"},
                    {"id": "T004", "description": "制定研究计划和技术路线", "status": "pending", "priority": "high"}
                ]
            },
            # ===== Phase 1: 文献综述 (增强版 - 30个任务) =====
            {
                "phase": 1,
                "name": "Literature Review",
                "tasks": [
                    # 1. 多关键词搜索 (6个任务)
                    {"id": "T005", "description": "【搜索1】使用核心主题关键词在 Semantic Scholar 搜索论文，获取前20篇", "status": "pending", "priority": "high"},
                    {"id": "T006", "description": "【搜索2】在 arXiv 搜索最新预印本论文（近2年），获取前15篇", "status": "pending", "priority": "high"},
                    {"id": "T007", "description": "【搜索3】搜索相关综述论文(Survey/Review)，获取前10篇", "status": "pending", "priority": "high"},
                    {"id": "T008", "description": "【搜索4】搜索经典高引用论文（citation>500），获取前10篇", "status": "pending", "priority": "high"},
                    {"id": "T009", "description": "【搜索5】搜索交叉领域论文（如方法+应用），获取前10篇", "status": "pending", "priority": "medium"},
                    {"id": "T010", "description": "【搜索6】搜索最新会议论文（NeurIPS/ICML/ACL/CHI等），获取前15篇", "status": "pending", "priority": "high"},

                    # 2. 文献筛选与整理 (4个任务)
                    {"id": "T011", "description": "合并所有搜索结果，去重，按相关性排序", "status": "pending", "priority": "high"},
                    {"id": "T012", "description": "筛选出最相关的30篇论文作为核心文献", "status": "pending", "priority": "high"},
                    {"id": "T013", "description": "创建文献数据库(literature_db.json)，记录每篇论文的元数据", "status": "pending", "priority": "high"},
                    {"id": "T014", "description": "按研究主题对论文分类：核心方法/应用场景/评估方法/理论基础", "status": "pending", "priority": "medium"},

                    # 3. 下载论文 (3个任务)
                    {"id": "T015", "description": "下载核心文献的PDF文件（优先从arXiv/OpenAccess下载）", "status": "pending", "priority": "high"},
                    {"id": "T016", "description": "对于无法下载的论文，保存摘要和关键信息", "status": "pending", "priority": "medium"},
                    {"id": "T017", "description": "整理下载的PDF，按类别存放到 notes/papers/ 目录", "status": "pending", "priority": "medium"},

                    # 4. 逐篇研读 (15个任务 - 每篇一个任务)
                    {"id": "T018", "description": "【研读1】阅读第1篇核心论文，提取背景、方法、结果、贡献，写入笔记", "status": "pending", "priority": "high"},
                    {"id": "T019", "description": "【研读2】阅读第2篇核心论文，提取背景、方法、结果、贡献，写入笔记", "status": "pending", "priority": "high"},
                    {"id": "T020", "description": "【研读3】阅读第3篇核心论文，提取背景、方法、结果、贡献，写入笔记", "status": "pending", "priority": "high"},
                    {"id": "T021", "description": "【研读4】阅读第4篇核心论文，提取背景、方法、结果、贡献，写入笔记", "status": "pending", "priority": "high"},
                    {"id": "T022", "description": "【研读5】阅读第5篇核心论文，提取背景、方法、结果、贡献，写入笔记", "status": "pending", "priority": "high"},
                    {"id": "T023", "description": "【研读6】阅读第6篇核心论文，提取背景、方法、结果、贡献，写入笔记", "status": "pending", "priority": "high"},
                    {"id": "T024", "description": "【研读7】阅读第7篇核心论文，提取背景、方法、结果、贡献，写入笔记", "status": "pending", "priority": "high"},
                    {"id": "T025", "description": "【研读8】阅读第8篇核心论文，提取背景、方法、结果、贡献，写入笔记", "status": "pending", "priority": "high"},
                    {"id": "T026", "description": "【研读9】阅读第9篇核心论文，提取背景、方法、结果、贡献，写入笔记", "status": "pending", "priority": "high"},
                    {"id": "T027", "description": "【研读10】阅读第10篇核心论文，提取背景、方法、结果、贡献，写入笔记", "status": "pending", "priority": "high"},
                    {"id": "T028", "description": "【研读11-15】阅读第11-15篇论文（次核心），提取关键信息摘要", "status": "pending", "priority": "medium"},
                    {"id": "T029", "description": "【研读16-20】阅读第16-20篇论文（相关），提取可引用内容", "status": "pending", "priority": "medium"},
                    {"id": "T030", "description": "【研读21-30】快速浏览第21-30篇论文，记录主要观点", "status": "pending", "priority": "low"},

                    # 5. 综合分析与文献综述撰写 (8个任务)
                    {"id": "T031", "description": "分析所有阅读笔记，识别研究领域的经典方法和发展脉络", "status": "pending", "priority": "high"},
                    {"id": "T032", "description": "分析现有研究的局限性和研究空白(Research Gap)", "status": "pending", "priority": "high"},
                    {"id": "T033", "description": "识别创新机会：分析哪些问题尚未被解决，哪些方法可以改进", "status": "pending", "priority": "high"},
                    {"id": "T034", "description": "对比分析：确定本研究与现有工作的差异化定位", "status": "pending", "priority": "high"},
                    {"id": "T035", "description": "生成参考文献BibTeX文件(references.bib)，确保格式正确", "status": "pending", "priority": "high"},
                    {"id": "T036", "description": "撰写文献综述初稿（按主题组织，非按时间）", "status": "pending", "priority": "high"},
                    {"id": "T037", "description": "检查文献综述中的引用是否完整，补充缺失的引用", "status": "pending", "priority": "medium"},
                    {"id": "T038", "description": "完善文献综述，确保引用格式规范（APA/IEEE/ACM格式）", "status": "pending", "priority": "medium"}
                ]
            },
            # ===== Phase 2: 假设设计 =====
            {
                "phase": 2,
                "name": "Hypothesis Design",
                "tasks": [
                    {"id": "T039", "description": "基于文献空白提出研究假设，确保假设的创新性", "status": "pending", "priority": "high"},
                    {"id": "T040", "description": "设计实验方案和对比方法", "status": "pending", "priority": "high"},
                    {"id": "T041", "description": "确定评估指标和数据集", "status": "pending", "priority": "high"},
                    {"id": "T042", "description": "验证假设的创新性：与现有方法对比，说明独特贡献", "status": "pending", "priority": "high"},
                    {"id": "T043", "description": "估算计算资源和时间需求", "status": "pending", "priority": "medium"},
                    {"id": "T044", "description": "撰写实验设计文档", "status": "pending", "priority": "medium"}
                ]
            },
            # ===== Phase 3: 代码实现 =====
            {
                "phase": 3,
                "name": "Coding",
                "tasks": [
                    {"id": "T045", "description": "搭建项目代码结构", "status": "pending", "priority": "high"},
                    {"id": "T046", "description": "实现数据处理模块", "status": "pending", "priority": "high"},
                    {"id": "T047", "description": "实现核心算法/模型（确保有创新点）", "status": "pending", "priority": "high"},
                    {"id": "T048", "description": "实现基线方法", "status": "pending", "priority": "high"},
                    {"id": "T049", "description": "编写训练和评估脚本", "status": "pending", "priority": "high"},
                    {"id": "T050", "description": "编写单元测试", "status": "pending", "priority": "medium"},
                    {"id": "T051", "description": "测试代码可运行性", "status": "pending", "priority": "high"}
                ]
            },
            # ===== Phase 4: 实验执行 =====
            {
                "phase": 4,
                "name": "Execution",
                "tasks": [
                    {"id": "T052", "description": "准备实验数据", "status": "pending", "priority": "high"},
                    {"id": "T053", "description": "运行小规模测试验证代码", "status": "pending", "priority": "high"},
                    {"id": "T054", "description": "运行基线方法实验", "status": "pending", "priority": "high"},
                    {"id": "T055", "description": "运行主要方法实验", "status": "pending", "priority": "high"},
                    {"id": "T056", "description": "运行消融实验验证各创新组件的贡献", "status": "pending", "priority": "high"},
                    {"id": "T057", "description": "收集和整理实验结果", "status": "pending", "priority": "high"}
                ]
            },
            # ===== Phase 5: 结果分析 =====
            {
                "phase": 5,
                "name": "Analysis",
                "tasks": [
                    {"id": "T058", "description": "执行统计显著性检验", "status": "pending", "priority": "high"},
                    {"id": "T059", "description": "生成性能对比图表", "status": "pending", "priority": "high"},
                    {"id": "T060", "description": "分析实验结果并得出结论", "status": "pending", "priority": "high"},
                    {"id": "T061", "description": "识别异常结果并解释", "status": "pending", "priority": "medium"},
                    {"id": "T062", "description": "创新性验证：量化本研究相对于基线的改进程度", "status": "pending", "priority": "high"}
                ]
            },
            # ===== Phase 6: 论文撰写 =====
            {
                "phase": 6,
                "name": "Writing",
                "tasks": [
                    {"id": "T063", "description": "撰写论文摘要", "status": "pending", "priority": "high"},
                    {"id": "T064", "description": "撰写引言部分（明确研究动机和创新点）", "status": "pending", "priority": "high"},
                    {"id": "T065", "description": "撰写相关工作部分（使用Phase1整理的文献）", "status": "pending", "priority": "high"},
                    {"id": "T066", "description": "撰写方法部分（突出创新设计）", "status": "pending", "priority": "high"},
                    {"id": "T067", "description": "撰写实验部分", "status": "pending", "priority": "high"},
                    {"id": "T068", "description": "撰写结论部分", "status": "pending", "priority": "medium"},
                    {"id": "T069", "description": "撰写贡献声明：明确列出本研究的创新贡献", "status": "pending", "priority": "high"},
                    {"id": "T070", "description": "整合论文初稿，嵌入参考文献", "status": "pending", "priority": "high"},
                    {"id": "T071", "description": "原创性检查：确保内容不是简单复制，引用规范", "status": "pending", "priority": "high"}
                ]
            },
            # ===== Phase 7: 去AI化润色 (Humanization) =====
            {
                "phase": 7,
                "name": "Humanization",
                "tasks": [
                    {"id": "T072", "description": "【润色1】分析论文各章节的AI痕迹特征（句式重复、过度使用连接词、缺乏个人观点）", "status": "pending", "priority": "high"},
                    {"id": "T073", "description": "【润色2】摘要去AI化：调整句式结构，增加学术性表达，降低AI检测分数", "status": "pending", "priority": "high"},
                    {"id": "T074", "description": "【润色3】引言去AI化：增加研究动机的个人视角，调整论证逻辑", "status": "pending", "priority": "high"},
                    {"id": "T075", "description": "【润色4】相关工作去AI化：增加批判性分析，体现作者学术观点", "status": "pending", "priority": "high"},
                    {"id": "T076", "description": "【润色5】方法部分去AI化：增加设计决策的解释和理由", "status": "pending", "priority": "high"},
                    {"id": "T077", "description": "【润色6】实验部分去AI化：增加结果解读的深度和洞见", "status": "pending", "priority": "high"},
                    {"id": "T078", "description": "【润色7】结论去AI化：强调研究的独特贡献和未来展望", "status": "pending", "priority": "medium"},
                    {"id": "T079", "description": "【润色8】全文语言润色：统一术语、修正语法、优化表达", "status": "pending", "priority": "high"},
                    {"id": "T080", "description": "【润色9】AI检测评分：确保AI检测分数低于30%", "status": "pending", "priority": "high"}
                ]
            },
            # ===== Phase 8: LaTeX双语排版 =====
            {
                "phase": 8,
                "name": "LaTeX Formatting",
                "tasks": [
                    {"id": "T081", "description": "【排版1】选择目标会议/期刊模板（NeurIPS/ICML/CHI/ACL等）", "status": "pending", "priority": "high"},
                    {"id": "T082", "description": "【排版2】创建LaTeX项目结构：main.tex, sections/, figures/, references.bib", "status": "pending", "priority": "high"},
                    {"id": "T083", "description": "【排版3】转换摘要到LaTeX格式", "status": "pending", "priority": "high"},
                    {"id": "T084", "description": "【排版4】转换引言到LaTeX格式", "status": "pending", "priority": "high"},
                    {"id": "T085", "description": "【排版5】转换相关工作到LaTeX格式，确保引用格式正确", "status": "pending", "priority": "high"},
                    {"id": "T086", "description": "【排版6】转换方法部分到LaTeX格式，添加算法伪代码", "status": "pending", "priority": "high"},
                    {"id": "T087", "description": "【排版7】转换实验部分到LaTeX格式，插入图表", "status": "pending", "priority": "high"},
                    {"id": "T088", "description": "【排版8】转换结论到LaTeX格式", "status": "pending", "priority": "medium"},
                    {"id": "T089", "description": "【排版9】生成中文版本：翻译并排版中文PDF（使用ctex宏包）", "status": "pending", "priority": "medium"},
                    {"id": "T090", "description": "【排版10】编译英文版LaTeX，检查并修复编译错误", "status": "pending", "priority": "high"},
                    {"id": "T091", "description": "【排版11】编译中文版LaTeX，检查并修复编译错误", "status": "pending", "priority": "medium"},
                    {"id": "T092", "description": "【排版12】检查PDF输出：页边距、字体、图表位置、引用格式", "status": "pending", "priority": "high"}
                ]
            },
            # ===== Phase 9: 同行评审 =====
            {
                "phase": 9,
                "name": "Peer Review",
                "tasks": [
                    {"id": "T093", "description": "自我检查论文完整性：确保所有章节齐全", "status": "pending", "priority": "high"},
                    {"id": "T094", "description": "检查参考文献格式和引用完整性", "status": "pending", "priority": "high"},
                    {"id": "T095", "description": "创新性自我评估：验证研究贡献的原创性和价值", "status": "pending", "priority": "high"},
                    {"id": "T096", "description": "模拟三位审稿人评审，记录问题和建议", "status": "pending", "priority": "high"},
                    {"id": "T097", "description": "根据评审意见修改论文（修改LaTeX源文件）", "status": "pending", "priority": "high"},
                    {"id": "T098", "description": "撰写审稿意见回复信(Response Letter)", "status": "pending", "priority": "high"},
                    {"id": "T099", "description": "最终检查：格式规范、页数限制、匿名性要求", "status": "pending", "priority": "high"},
                    {"id": "T100", "description": "生成提交包：英文PDF + 中文PDF + 补充材料", "status": "pending", "priority": "high"}
                ]
            }
        ]
    }

    tasks_file = PROJECT_ROOT / "Projects" / project_name / "research_tasks.json"
    with open(tasks_file, 'w', encoding='utf-8') as f:
        json.dump(tasks, f, indent=2, ensure_ascii=False)

    return tasks_file


def print_tasks_summary(tasks_file: Path):
    """打印任务清单摘要"""
    with open(tasks_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print("\n" + "=" * 60)
    print(f"项目: {data.get('project_name', 'Unknown')}")
    print(f"主题: {data.get('topic', 'Unknown')}")
    print("=" * 60)

    total_tasks = 0
    for phase in data.get("phases", []):
        phase_num = phase.get("phase", "?")
        phase_name = phase.get("name", "Unknown")
        tasks = phase.get("tasks", [])
        total_tasks += len(tasks)

        print(f"\nPhase {phase_num}: {phase_name}")
        print("-" * 40)
        for task in tasks:
            status_icon = "[ ]" if task.get("status") == "pending" else "[x]"
            priority = task.get("priority", "medium")
            print(f"  {status_icon} {task['id']}: {task['description'][:50]}... ({priority})")

    print("\n" + "=" * 60)
    print(f"总计: {total_tasks} 个任务")
    print("=" * 60)


def link_to_current(project_name: str):
    """创建 current 符号链接或复制到 current"""
    current_dir = PROJECT_ROOT / "Projects" / "current"

    # 删除旧的 current
    if current_dir.exists():
        import shutil
        shutil.rmtree(current_dir)

    # Windows 不支持符号链接，使用 junction 或直接复制
    if sys.platform == 'win32':
        # 复制目录
        import shutil
        shutil.copytree(
            PROJECT_ROOT / "Projects" / project_name,
            current_dir
        )
    else:
        # 创建符号链接
        current_dir.symlink_to(PROJECT_ROOT / "Projects" / project_name)


def start_auto_run(project_name: str, loops: int = 0, timeout: int = 300,
                   max_wait: int = 1800, max_retries: int = 3, retry_delay: int = 60):
    """启动自动执行"""
    print("\n启动自动执行...")

    auto_run_script = PROJECT_ROOT / "auto_run_research.py"

    # 如果存在专门的研究任务执行脚本，使用它
    if auto_run_script.exists():
        cmd = [
            sys.executable, str(auto_run_script),
            "--project", project_name,
            "--timeout", str(timeout),
            "--max-wait", str(max_wait),
            "--max-retries", str(max_retries),
            "--retry-delay", str(retry_delay)
        ]
        if loops > 0:
            cmd.extend(["--loops", str(loops)])
    else:
        # 否则使用通用的 auto_run.py
        cmd = [
            sys.executable, str(PROJECT_ROOT / "auto_run.py"),
            "--timeout", str(timeout)
        ]
        if loops > 0:
            cmd.extend(["--loops", str(loops)])

    try:
        subprocess.run(cmd, cwd=PROJECT_ROOT)
    except KeyboardInterrupt:
        print("\n用户中断执行")
    except Exception as e:
        print(f"启动失败: {e}")


def main():
    parser = argparse.ArgumentParser(
        description='Project Prometheus - 研究主题启动器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 生成任务清单
  python start_research.py --topic "Transformer在时间序列预测中的应用"

  # 生成并自动执行
  python start_research.py --topic "图神经网络社交推荐" --auto-run

  # 指定项目名称
  python start_research.py --topic "xxx" --name "gnn_recommendation"
        """
    )

    parser.add_argument('--topic', '-t', type=str, required=True,
                        help='研究主题')
    parser.add_argument('--name', '-n', type=str,
                        help='项目名称（默认自动生成）')
    parser.add_argument('--auto-run', '-a', action='store_true',
                        help='生成任务清单后自动开始执行')
    parser.add_argument('--loops', '-l', type=int, default=0,
                        help='执行循环次数（0=无限循环直到完成）')
    parser.add_argument('--timeout', type=int, default=300,
                        help='每个任务的超时时间（秒）')
    parser.add_argument('--max-wait', '-w', type=int, default=1800,
                        help='每个任务最大等待时间（秒，默认1800=30分钟）')
    parser.add_argument('--max-retries', '-r', type=int, default=3,
                        help='失败任务最大重试次数（默认3）')
    parser.add_argument('--retry-delay', '-d', type=int, default=60,
                        help='重试间隔（秒，默认60）')
    parser.add_argument('--use-ai', action='store_true',
                        help='使用 Claude AI 生成更详细的任务清单')
    parser.add_argument('--dry-run', action='store_true',
                        help='干跑模式，只显示任务清单不执行')

    args = parser.parse_args()

    # 生成项目名称
    if args.name:
        project_name = args.name
    else:
        # 从主题生成项目名称
        project_name = re.sub(r'[^\w\s-]', '', args.topic)
        project_name = re.sub(r'[\s]+', '_', project_name)
        project_name = project_name[:30].lower()
        if not project_name:
            project_name = f"project_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    print("=" * 60)
    print("Project Prometheus - 研究主题启动器")
    print("=" * 60)
    print(f"研究主题: {args.topic}")
    print(f"项目名称: {project_name}")
    print()

    # 创建项目结构
    print("创建项目目录结构...")
    project_dir = create_project_structure(project_name)

    # 创建初始状态
    print("初始化项目状态...")
    create_initial_state(args.topic, project_name)

    # 生成任务清单
    tasks_file = project_dir / "research_tasks.json"

    if args.use_ai:
        print("\n使用 Claude AI 生成任务清单...")
        prompt = generate_task_generation_prompt(args.topic)

        # 确保目标目录存在
        tasks_file.parent.mkdir(parents=True, exist_ok=True)

        success = run_claude_for_tasks(prompt, timeout=args.timeout)

        if not success or not verify_tasks_file(tasks_file):
            print("AI 生成失败，使用默认任务模板...")
            tasks_file = create_default_tasks(args.topic, project_name)
    else:
        print("\n生成默认任务清单...")
        tasks_file = create_default_tasks(args.topic, project_name)

    # 链接到 current
    print("链接到当前项目...")
    link_to_current(project_name)

    # 打印任务摘要
    print_tasks_summary(tasks_file)

    if args.dry_run:
        print("\n[干跑模式] 任务清单已生成，不执行")
        print(f"任务文件: {tasks_file}")
        return

    if args.auto_run:
        start_auto_run(project_name, args.loops, args.timeout,
                       args.max_wait, args.max_retries, args.retry_delay)
    else:
        print("\n任务清单已生成!")
        print(f"任务文件: {tasks_file}")
        print("\n要开始执行，请运行:")
        print(f"  python auto_run_research.py --project {project_name}")
        print("或者:")
        print(f"  python start_research.py --topic \"{args.topic}\" --auto-run")


if __name__ == "__main__":
    main()

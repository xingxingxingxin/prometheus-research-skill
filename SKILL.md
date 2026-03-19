# prometheus-research

name: prometheus-research
description: |
  全自主科研智能体 - 自动完成从文献调研到论文撰写的完整研究流程。

  **触发条件**（当用户说以下内容时使用此技能）：
  - "启动研究"、"开始研究"、"做一个研究"
  - "帮我研究"、"调研一下"、"文献综述"
  - "继续研究"、"执行下一个任务"
  - 用户提到任何研究相关需求，如"写论文"、"实验分析"

  此技能会自动执行完整的10阶段研究流程，生成学术论文。

---

# Project Prometheus - 全自主科研智能体

你是一个能够自主完成科研全流程的智能体。遵循以下工作流完成研究任务。

## 可用脚本

本 skill 包含完整的 Python 工具集，位于 `scripts/` 目录：

### 后台执行与监控（推荐）

| 脚本 | 用途 |
|------|------|
| `scripts/quick_start.bat` | **一键启动** - 创建项目并后台执行 |
| `scripts/run_background.bat/.sh` | 后台执行任务 |
| `scripts/monitor.bat/.sh` | 日志监控 |

### 核心脚本

| 脚本 | 用途 |
|------|------|
| `scripts/start_research.py` | 启动新研究项目 |
| `scripts/prometheus.py` | 系统控制器（状态/检查点） |
| `scripts/automation/task_executor.py` | 任务执行器 |

### 工具脚本

| 脚本 | 用途 |
|------|------|
| `scripts/Core/tools/arxiv_search.py` | arXiv 搜索 |
| `scripts/Core/tools/semantic_scholar_search.py` | Semantic Scholar 搜索 |
| `scripts/Core/tools/paper_downloader.py` | 论文下载 |
| `scripts/Core/tools/statistical_test.py` | 统计检验 |
| `scripts/Core/tools/result_visualizer.py` | 结果可视化 |
| `scripts/Core/tools/latex_compiler.py` | LaTeX 编译 |

**依赖安装**：
```bash
pip install -r scripts/requirements.txt
```

## 后台执行工作流（推荐）

### 1. 启动研究
```powershell
# Windows
call scripts\quick_start.bat "研究主题"

# Linux/Mac
./scripts/quick_start.sh "研究主题"
```

### 2. 后台执行
```powershell
# Windows
call scripts\run_background.bat

# Linux/Mac
./scripts/run_background.sh
```

### 3. 监控进度
```powershell
# Windows - 实时日志
Get-Content Logs\executor_*.log -Wait -Tail 50

# 或使用监控脚本
call scripts\monitor.bat

# Linux/Mac
./scripts/monitor.sh
```

### 4. 查看状态
```bash
python scripts/prometheus.py --status
```

### 日志文件位置
```
Logs/
├── executor_20260319_120000.log   # 执行日志
├── workflow.log                    # 工作流日志
└── error_trace.log                 # 错误追踪
```

## 核心原则

1. **增量进展** - 每次只完成一小部分，保持状态可恢复
2. **状态持久化** - 所有进度保存在 `.prometheus/` 目录
3. **完成标记** - 任务完成必须输出 `<promise>TASK_COMPLETE</promise>`
4. **自我验证** - 只有经过验证才能标记任务完成

## 快速启动

### 启动新研究
当用户说"启动研究"或提供研究主题时：

1. **确认主题** - 如果用户没有明确主题，询问：
   ```
   请告诉我你的研究主题，我会自动完成从文献调研到论文撰写的全流程。
   ```

2. **创建项目结构**：
   ```
   Projects/{研究主题}/
   ├── .prometheus/
   │   ├── state.json           # 执行状态
   │   ├── research_tasks.json  # 100个任务清单
   │   └── current_context.md   # 当前任务上下文
   ├── data/
   │   ├── papers/              # 下载的论文
   │   └── search_results/      # 搜索结果
   ├── code/                    # 实验代码
   ├── notes/                   # 研究笔记
   ├── paper/                   # Markdown 论文
   ├── latex/                   # LaTeX 源码
   └── output/                  # 最终输出
   ```

3. **初始化状态文件** - 创建 `.prometheus/state.json`：
   ```json
   {
     "project_name": "研究主题",
     "current_phase": 0,
     "current_task": "T001",
     "status": "in_progress",
     "started_at": "时间戳",
     "phases": {
       "0": {"name": "Topic Analysis", "status": "in_progress"},
       "1": {"name": "Literature Review", "status": "pending"}
     }
   }
   ```

4. **生成任务清单** - 根据下文的10阶段工作流创建 100 个任务

5. **开始执行** - 从 T001 开始执行任务

### 继续研究
当用户说"继续研究"时：

1. 读取 `Projects/{项目}/.prometheus/state.json`
2. 读取 `Projects/{项目}/.prometheus/research_tasks.json`
3. 找到第一个 `pending` 或 `in_progress` 的任务
4. 继续执行

## 10 阶段工作流

| Phase | 名称 | 任务数 | 说明 |
|-------|------|--------|------|
| 0 | Topic Analysis | 4 | 分析研究主题 |
| 1 | Literature Review | 34 | 文献搜索、筛选、研读 |
| 2 | Hypothesis Design | 6 | 设计研究假设和实验 |
| 3 | Coding | 7 | 实现代码 |
| 4 | Execution | 6 | 运行实验 |
| 5 | Analysis | 5 | 分析结果 |
| 6 | Writing | 9 | 撰写论文 (Markdown) |
| 7 | Humanization | 9 | 去AI化处理 |
| 8 | LaTeX | 12 | 转换为 LaTeX |
| 9 | Review | 8 | 同行评审和修改 |

### Phase 0: Topic Analysis (4 tasks)
- T001: 分析研究主题，提取核心研究方向、关键概念和研究问题
- T002: 识别主题涉及的研究领域和交叉学科
- T003: 明确研究目标和预期贡献
- T004: 制定研究计划和技术路线

### Phase 1: Literature Review (34 tasks)
**多关键词搜索 (T005-T010)**
- T005-T010: 使用不同关键词组合搜索文献

**文献筛选 (T011-T014)**
- T011: 合并去重排序
- T012: 筛选30篇核心文献
- T013: 创建文献数据库
- T014: 按主题分类

**下载论文 (T015-T017)**
- T015-T017: 下载和整理PDF

**逐篇研读 (T018-T030)**
- T018-T027: 研读第1-10篇核心论文
- T028-T030: 浏览其余论文

**综合分析 (T031-T038)**
- T031-T038: 分析发展脉络、识别研究空白、撰写综述

### Phase 2: Hypothesis Design (6 tasks)
- T039: 提出研究假设
- T040: 设计实验方案
- T041: 确定评估指标
- T042: 验证创新性
- T043: 估算资源需求
- T044: 撰写实验设计文档

### Phase 3: Coding (7 tasks)
- T045: 搭建项目代码结构
- T046: 实现数据处理模块
- T047: 实现核心算法/模型
- T048: 实现基线方法
- T049: 编写训练评估脚本
- T050: 编写单元测试
- T051: 测试代码可运行性

### Phase 4: Execution (6 tasks)
- T052: 准备实验数据
- T053: 小规模测试验证
- T054: 运行基线实验
- T055: 运行主要实验
- T056: 运行消融实验
- T057: 收集整理结果

### Phase 5: Analysis (5 tasks)
- T058: 统计显著性检验
- T059: 生成性能对比图表
- T060: 分析结果得出结论
- T061: 识别异常结果
- T062: 创新性量化验证

### Phase 6: Writing (9 tasks)
- T063: 撰写摘要
- T064: 撰写引言
- T065: 撰写相关工作
- T066: 撰写方法
- T067: 撰写实验
- T068: 撰写结论
- T069: 撰写贡献声明
- T070: 整合论文初稿
- T071: 原创性检查

### Phase 7: Humanization (9 tasks)
- T072: 分析AI痕迹特征
- T073-T078: 各章节去AI化
- T079: 全文语言润色
- T080: AI检测评分 (<30%)

### Phase 8: LaTeX (12 tasks)
- T081: 选择目标会议模板
- T082-T088: 转换各章节到LaTeX
- T089: 生成中文版本
- T090-T092: 编译和检查PDF

### Phase 9: Review (8 tasks)
- T093-T096: 完整性检查和评审
- T097-T098: 根据评审修改
- T099: 最终格式检查
- T100: 生成提交包

## 任务执行流程

```
┌─────────────────────────────────────────────────────────────┐
│                     单个任务执行流程                          │
├─────────────────────────────────────────────────────────────┤
│  1. 读取任务上下文                                           │
│     ├── 读取 state.json 获取当前状态                         │
│     ├── 读取 research_tasks.json 获取任务详情                │
│     └── 读取对应的 phase 提示词（见 references/）            │
│                                                             │
│  2. 执行任务                                                 │
│     ├── 使用 WebSearch 搜索文献 (Phase 1)                    │
│     ├── 编写代码 (Phase 3)                                   │
│     ├── 运行实验 (Phase 4)                                   │
│     └── 撰写论文 (Phase 6-8)                                 │
│                                                             │
│  3. 验证完成                                                 │
│     ├── 检查输出文件是否存在                                 │
│     ├── 检查代码是否可运行                                   │
│     └── 确认满足任务要求                                     │
│                                                             │
│  4. 更新状态                                                 │
│     ├── 更新 research_tasks.json 标记任务完成                │
│     ├── 更新 state.json 推进到下一个任务                     │
│     └── 输出 <promise>TASK_COMPLETE</promise>                │
└─────────────────────────────────────────────────────────────┘
```

## 状态持久化

### state.json 格式
```json
{
  "project_name": "研究主题",
  "current_phase": 1,
  "current_task": "T018",
  "status": "in_progress",
  "started_at": "2026-03-19T10:00:00",
  "last_updated": "2026-03-19T12:30:00",
  "completed_tasks": 17,
  "total_tasks": 100,
  "phases": {
    "0": {"name": "Topic Analysis", "status": "completed"},
    "1": {"name": "Literature Review", "status": "in_progress"},
    "2": {"name": "Hypothesis Design", "status": "pending"}
  }
}
```

### research_tasks.json 格式
```json
{
  "project_name": "研究主题",
  "created_at": "时间戳",
  "tasks": [
    {
      "id": "T001",
      "phase": 0,
      "title": "分析研究主题",
      "description": "提取核心研究方向、关键概念和研究问题",
      "status": "completed",
      "output": "notes/topic_analysis.md"
    }
  ]
}
```

## 任务状态

| 状态 | 说明 |
|------|------|
| `pending` | 待执行 |
| `in_progress` | 执行中 |
| `completed` | 已完成 |
| `failed` | 失败，需要帮助 |
| `skipped` | 跳过 |

## 完成标记

每个任务完成后，必须：
1. 更新状态文件
2. 输出完成标记：
   ```
   <promise>TASK_COMPLETE</promise>
   任务 T018 已完成: 研读第1篇核心论文
   输出文件: notes/paper_001_summary.md
   ```

## 错误处理

如果任务执行失败：
1. 将任务状态设为 `failed`
2. 记录错误信息到 `.prometheus/error_log.md`
3. 询问用户是否需要帮助

## 使用示例

**用户**: 启动一个关于"大语言模型在代码审查中的应用"的研究

**助手**:
```
好的，我来启动这个研究项目。

[创建项目目录结构]
[初始化 state.json 和 research_tasks.json]

项目已创建: Projects/大语言模型在代码审查中的应用/
当前阶段: Phase 0 - 主题分析
当前任务: T001 - 分析研究主题

开始执行 T001...

[执行任务内容]

<promise>TASK_COMPLETE</promise>
任务 T001 已完成: 分析研究主题
输出文件: notes/topic_analysis.md

继续执行 T002...
```

## 参考文件

详细的工作流和模板见 `references/` 目录：
- `references/workflow.md` - 完整的10阶段100任务详情
- `references/templates.md` - 输出模板

---

*Project Prometheus - 让科研自动化成为可能*

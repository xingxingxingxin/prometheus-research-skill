# prometheus-research

name: prometheus-research
description: |
  全自主科研智能体 - 后台执行完整的10阶段100任务研究流程。

  **触发条件**（当用户说以下内容时必须使用此技能）：
  - "启动研究"、"开始研究"、"做一个研究"
  - "帮我研究"、"调研一下"、"文献综述"
  - "继续研究"、"执行下一个任务"
  - 用户提到任何研究相关需求

  **重要**: 此技能使用后台执行模式，用户通过日志监控进度。

---

# Project Prometheus - 全自主科研智能体

> **原创作者**: xingye
> **微信**: xingye4088
> **版权所有 (c) 2026 xingye**

---

## 原创声明

本项目为 **xingye** 独立开发的原创作品。未经作者书面授权，禁止用于商业用途。学术使用请保留作者署名。

---

## 重要：执行模式说明

**此技能必须使用后台执行模式，不可在对话中直接执行任务。**

当用户触发此技能时，你必须按照以下步骤操作：

### 步骤 1：初始化研究项目

运行以下命令创建项目结构和任务清单：

```bash
python scripts/start_research.py --topic "用户的研究主题"
```

这会：
- 创建 `Projects/{project_name}/` 目录
- 生成 `research_tasks.json`（100个任务）
- 生成 `state.json`（初始状态）

### 步骤 2：启动后台执行

**Windows:**
```bash
call scripts\run_background.bat
```

**Linux/Mac:**
```bash
./scripts/run_background.sh
```

这会启动后台进程，自动执行所有任务。

### 步骤 3：告知用户监控方式

执行启动后，**必须**告诉用户：

```
研究已在后台启动！

查看实时进度：
  Get-Content Logs\executor_*.log -Wait -Tail 50   (Windows PowerShell)
  tail -f Logs/executor_*.log                      (Linux/Mac)

查看状态：
  python scripts/prometheus.py --status

监控菜单：
  call scripts\monitor.bat   (Windows)
  ./scripts/monitor.sh       (Linux/Mac)
```

---

## 10 阶段 100 任务工作流

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

### Phase 0: Topic Analysis (4 tasks: T001-T004)
- T001: 分析研究主题，提取核心研究方向、关键概念和研究问题
- T002: 识别主题涉及的研究领域和交叉学科
- T003: 明确研究目标和预期贡献
- T004: 制定研究计划和技术路线

### Phase 1: Literature Review (34 tasks: T005-T038)
**多关键词搜索 (T005-T010)**
- T005: Semantic Scholar 核心关键词搜索 (20篇)
- T006: arXiv 最新预印本搜索 (15篇)
- T007: 综述论文搜索 (10篇)
- T008: 高引用经典论文搜索 (10篇)
- T009: 交叉领域论文搜索 (10篇)
- T010: 最新会议论文搜索 (15篇)

**文献筛选与整理 (T011-T014)**
- T011: 合并去重排序
- T012: 筛选30篇核心文献
- T013: 创建文献数据库
- T014: 按主题分类

**下载论文 (T015-T017)**
- T015: 下载核心文献PDF
- T016: 保存无法下载论文的摘要
- T017: 整理PDF到papers目录

**逐篇研读 (T018-T030)**
- T018-T027: 研读第1-10篇核心论文
- T028: 研读第11-15篇论文
- T029: 研读第16-20篇论文
- T030: 浏览第21-30篇论文

**综合分析 (T031-T038)**
- T031: 分析发展脉络
- T032: 识别研究空白
- T033: 识别创新机会
- T034: 确定差异化定位
- T035: 生成BibTeX文件
- T036: 撰写文献综述初稿
- T037: 检查引用完整性
- T038: 完善引用格式

### Phase 2: Hypothesis Design (6 tasks: T039-T044)
- T039: 提出研究假设
- T040: 设计实验方案
- T041: 确定评估指标
- T042: 验证创新性
- T043: 估算资源需求
- T044: 撰写实验设计文档

### Phase 3: Coding (7 tasks: T045-T051)
- T045: 搭建项目代码结构
- T046: 实现数据处理模块
- T047: 实现核心算法/模型
- T048: 实现基线方法
- T049: 编写训练评估脚本
- T050: 编写单元测试
- T051: 测试代码可运行性

### Phase 4: Execution (6 tasks: T052-T057)
- T052: 准备实验数据
- T053: 小规模测试验证
- T054: 运行基线实验
- T055: 运行主要实验
- T056: 运行消融实验
- T057: 收集整理结果

### Phase 5: Analysis (5 tasks: T058-T062)
- T058: 统计显著性检验
- T059: 生成性能对比图表
- T060: 分析结果得出结论
- T061: 识别异常结果
- T062: 创新性量化验证

### Phase 6: Writing - Markdown (9 tasks: T063-T071)
- T063: 撰写摘要
- T064: 撰写引言
- T065: 撰写相关工作
- T066: 撰写方法
- T067: 撰写实验
- T068: 撰写结论
- T069: 撰写贡献声明
- T070: 整合论文初稿
- T071: 原创性检查

### Phase 7: Humanization - De-AI (9 tasks: T072-T080)
- T072: 分析AI痕迹特征
- T073: 摘要去AI化
- T074: 引言去AI化
- T075: 相关工作去AI化
- T076: 方法部分去AI化
- T077: 实验部分去AI化
- T078: 结论去AI化
- T079: 全文语言润色
- T080: AI检测评分 (<30%)

### Phase 8: LaTeX Bilingual Formatting (12 tasks: T081-T092)
- T081: 选择目标会议模板
- T082: 创建LaTeX项目结构
- T083: 转换摘要
- T084: 转换引言
- T085: 转换相关工作
- T086: 转换方法(含伪代码)
- T087: 转换实验(含图表)
- T088: 转换结论
- T089: 生成中文版本
- T090: 编译英文PDF
- T091: 编译中文PDF
- T092: 检查PDF输出

### Phase 9: Peer Review (8 tasks: T093-T100)
- T093: 论文完整性检查
- T094: 参考文献格式检查
- T095: 创新性自我评估
- T096: 模拟三位审稿人评审
- T097: 根据评审修改论文
- T098: 撰写审稿回复信
- T099: 最终格式检查
- T100: 生成提交包

---

## 项目目录结构

```
Projects/{project_name}/
├── research_tasks.json      # 任务清单 (100个任务)
├── state.json               # 执行状态
├── logs/
│   └── executor.log         # 执行日志
├── data/
│   ├── papers/              # 下载的论文
│   └── search_results/      # 搜索结果
├── code/                    # 实验代码
├── notes/                   # 研究笔记
├── results/                 # 实验结果
├── paper/                   # Markdown论文
├── latex/                   # LaTeX源码
├── output/                  # 最终输出
│   ├── paper_en.pdf
│   └── paper_zh.pdf
└── references.bib           # 参考文献
```

---

## 状态文件格式

### state.json
```json
{
  "project_name": "研究主题",
  "current_phase": 1,
  "current_task": "T018",
  "status": "in_progress",
  "completed_tasks": 17,
  "total_tasks": 100,
  "phases": {
    "0": {"name": "Topic Analysis", "status": "completed"},
    "1": {"name": "Literature Review", "status": "in_progress"},
    ...
  }
}
```

### research_tasks.json
```json
{
  "project_name": "研究主题",
  "phases": [
    {
      "phase": 0,
      "name": "Topic Analysis",
      "tasks": [
        {"id": "T001", "description": "...", "status": "completed", "priority": "high"},
        ...
      ]
    }
  ]
}
```

---

## 任务状态

| 状态 | 说明 |
|------|------|
| `pending` | 待完成 |
| `in_progress` | 进行中 |
| `completed` | 已完成 |
| `failed` | 失败 |
| `skipped` | 跳过 |

---

## 完成标记

每个任务完成后必须输出：
```
<promise>TASK_COMPLETE</promise>
任务 T018 已完成: 研读第1篇核心论文
输出文件: notes/paper_001_summary.md
```

---

## 可用脚本

| 脚本 | 用途 |
|------|------|
| `scripts/start_research.py` | 启动新研究，生成任务清单 |
| `scripts/run_background.bat/.sh` | 后台执行任务 |
| `scripts/monitor.bat/.sh` | 日志监控菜单 |
| `scripts/prometheus.py` | 系统控制器 |

---

## 日志文件

```
Logs/
├── executor_*.log        # 执行日志（主要查看）
├── workflow.log          # 工作流日志
└── error_trace.log       # 错误追踪
```

---

## 依赖安装

```bash
pip install -r scripts/requirements.txt
```

---

*Project Prometheus - 让科研自动化成为可能*

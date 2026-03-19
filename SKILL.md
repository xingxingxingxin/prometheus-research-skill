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

## 核心原则

1. **增量进展** - 每次只完成一小部分，保持状态可恢复
2. **状态持久化** - 所有进度保存在 `.prometheus/` 目录
3. **完成标记** - 任务完成必须输出 `<promise>TASK_COMPLETE</promise>`
4. **自我验证** - 只有经过验证才能标记任务完成

## 执行方式：后台执行 + 日志监控

### 启动研究
```bash
# 1. 启动新研究
python scripts/start_research.py --topic "研究主题"

# 2. 后台执行
call scripts\run_background.bat   # Windows
./scripts/run_background.sh       # Linux/Mac
```

### 监控进度
```bash
# 查看日志
call scripts\monitor.bat          # Windows
./scripts/monitor.sh              # Linux/Mac

# 实时日志
Get-Content Logs\executor_*.log -Wait -Tail 50   # Windows
tail -f Logs/executor_*.log                      # Linux/Mac
```

### 查看状态
```bash
python scripts/prometheus.py --status
```

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

**总任务数: 100**

### Phase 0: Topic Analysis (4 tasks)
- T001: 分析研究主题，提取核心研究方向、关键概念和研究问题
- T002: 识别主题涉及的研究领域和交叉学科
- T003: 明确研究目标和预期贡献
- T004: 制定研究计划和技术路线

### Phase 1: Literature Review (34 tasks)
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

## 项目目录结构

```
Projects/{project_name}/
├── .prometheus/
│   ├── state.json           # 执行状态
│   ├── research_tasks.json  # 任务清单 (100个任务)
│   └── current_context.md   # 当前任务上下文
├── data/
│   ├── papers/              # 下载的论文
│   └── search_results/      # 搜索结果
├── code/                    # 实验代码
├── notes/                   # 研究笔记
├── results/                 # 实验结果
├── paper/                   # Markdown论文
│   ├── abstract.md
│   ├── introduction.md
│   ├── related_work.md
│   ├── methods.md
│   ├── experiments.md
│   └── conclusion.md
├── latex/                   # LaTeX源码
│   ├── main.tex
│   ├── sections/
│   ├── figures/
│   └── references.bib
├── output/                  # 最终输出
│   ├── paper_en.pdf
│   └── paper_zh.pdf
└── references.bib           # 参考文献
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
    "0": {"name": "Topic Analysis", "status": "completed", "completed_at": "..."},
    "1": {"name": "Literature Review", "status": "in_progress"},
    "2": {"name": "Hypothesis Design", "status": "pending"},
    "3": {"name": "Coding", "status": "pending"},
    "4": {"name": "Execution", "status": "pending"},
    "5": {"name": "Analysis", "status": "pending"},
    "6": {"name": "Writing", "status": "pending"},
    "7": {"name": "Humanization", "status": "pending"},
    "8": {"name": "LaTeX", "status": "pending"},
    "9": {"name": "Review", "status": "pending"}
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
    },
    ...
  ]
}
```

## 任务状态

| 状态 | 说明 |
|------|------|
| `pending` | 待完成 |
| `in_progress` | 进行中 |
| `completed` | 已完成 |
| `failed` | 失败 |
| `skipped` | 跳过 |

## 阶段依赖

- Phase N 必须在 Phase N-1 完成后才能开始
- 同一阶段内的任务按顺序执行
- 检查点必须通过才能进入下一阶段

## 检查点

| 检查点 | 阶段后 | 说明 |
|--------|--------|------|
| checkpoint_a | Phase 1 | 文献综述完成，研究方向确认 |
| checkpoint_b | Phase 2 | 实验设计完成，方案可行 |
| checkpoint_c | Phase 4 | 实验完成，结果有效 |
| checkpoint_d | Phase 5 | 分析完成，结论明确 |
| checkpoint_e | Phase 6 | 论文初稿完成 |
| checkpoint_f | Phase 7 | 去AI化完成 |
| checkpoint_g | Phase 8 | LaTeX完成 |

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
3. GEP 错误恢复机制会尝试修复

## 上下文恢复

当执行中断后恢复时：
1. 读取 `state.json` 获取当前状态
2. 读取 `research_tasks.json` 获取任务状态
3. 找到第一个 `pending` 或 `in_progress` 的任务
4. 继续执行

## 可用脚本

| 脚本 | 用途 |
|------|------|
| `scripts/run_background.bat/.sh` | 后台执行 |
| `scripts/monitor.bat/.sh` | 日志监控 |
| `scripts/prometheus.py` | 系统控制器 |
| `scripts/start_research.py` | 启动研究 |

## 日志文件

```
Logs/
├── executor_*.log        # 执行日志
├── workflow.log          # 工作流日志
└── error_trace.log       # 错误追踪
```

## 依赖安装

```bash
pip install -r scripts/requirements.txt
```

---

*Project Prometheus - 让科研自动化成为可能*

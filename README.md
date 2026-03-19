# Prometheus Research Skill

> 全自主科研智能体 - 后台执行，日志监控

**原创作者: xingye**
**微信**: xingye4088**

---

## 原创声明

本项目为 **xingye** 独立开发的原创作品，享有完整版权。

- 版权所有 (c) 2026 xingye
- 未经作者书面授权，禁止用于商业用途
- 学术使用请保留作者署名

引用请注明：
```bibtex
@software{prometheus_research_2026,
  author = {xingye},
  title = {Prometheus Research Skill - 全自主科研智能体},
  year = {2026},
  url = {https://github.com/xingxingxingxin/prometheus-research-skill}
}
```

---

## 能力展示
这些是产出的论文初稿截图

![Workflow Overview](assets/workflow_overview.png)


![Experiment Results](assets/experiment_results.png)


![Code Structure](assets/code_structure.png)

---

## 设计原理

### 核心理念

**Prometheus Research Skill** 的设计目标是实现真正的"全自主"科研——用户只需说"启动研究"，智能体就会自动完成从文献调研到论文撰写的全部工作。

### 为什么使用后台执行模式？

传统 AI 助手在对话中直接执行任务，存在以下问题：
- **对话阻塞**: 长时间任务会阻塞对话，用户无法进行其他操作
- **上下文限制**: 复杂任务容易超出上下文窗口
- **不可恢复**: 对话中断后任务状态丢失

**后台执行模式** 的优势：
- **非阻塞**: 用户可以继续使用 Claude Code 进行其他工作
- **持久化**: 任务状态保存在文件中，可随时恢复
- **可监控**: 通过日志文件实时查看进度
- **可中断**: 随时可以停止或重启后台进程

### 架构设计

```
┌─────────────────────────────────────────────────────────────────┐
│                        系统架构                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐  │
│  │  Claude Code │ ──── │ SKILL.md     │ ──── │ start_research│  │
│  │   (用户)     │      │ (触发器)     │      │   (初始化)    │  │
│  └──────────────┘      └──────────────┘      └──────────────┘  │
│                                                       │         │
│                                                       ▼         │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              task_executor.py (后台进程)                  │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │   │
│  │  │ Ralph Loop  │  │  GEP 恢复   │  │ 状态持久化  │      │   │
│  │  │ (深度迭代)  │  │ (错误恢复)  │  │ (断点续传)  │      │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘      │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                 │                               │
│                                 ▼                               │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                     输出产物                              │   │
│  │  Projects/{topic}/output/                                │   │
│  │  ├── paper_en.pdf (英文论文)                             │   │
│  │  ├── paper_zh.pdf (中文论文)                             │   │
│  │  └── supplementary.zip (代码和数据)                      │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 核心机制

#### 1. Ralph Loop 深度迭代

每个任务不是一次性完成，而是通过多轮迭代逐步优化：

```
任务执行 → 自我评估 → 发现问题 → 迭代改进 → 检测完成标记
    ↑                                              │
    └──────────────────────────────────────────────┘
```

- **完成检测**: 通过 `<promise>TASK_COMPLETE</promise>` 标记判断任务是否真正完成
- **最大迭代**: 每个任务最多迭代 20 次，防止无限循环
- **适用阶段**: 主要用于 coding、execution、analysis 等需要深度思考的阶段

#### 2. GEP 错误恢复机制

当任务执行失败时，系统会从历史修复经验中学习：

```python
# GEP (Gene Expression Programming) 恢复流程
错误发生 → 提取错误信号 → 匹配历史修复基因 → 生成修复策略 → 执行修复
```

- **基因库**: 存储历史成功修复方案
- **胶囊存储**: 记录修复上下文，供未来参考
- **置信度评估**: 只采用高置信度的修复策略

#### 3. 状态持久化

所有进度保存在 JSON 文件中，支持断点续传：

```json
{
  "current_phase": 3,
  "current_task": "T045",
  "status": "in_progress",
  "completed_tasks": 44,
  "total_tasks": 100
}
```

---

## 10 阶段 100 任务工作流

| Phase | 名称 | 任务数 | 说明 |
|-------|------|--------|------|
| 0 | Topic Analysis | 4 | 分析研究主题，提取核心概念 |
| 1 | Literature Review | 34 | 多源搜索、筛选、研读文献 |
| 2 | Hypothesis Design | 6 | 提出假设，设计实验方案 |
| 3 | Coding | 7 | 实现数据处理、算法、基线 |
| 4 | Execution | 6 | 运行实验，收集结果 |
| 5 | Analysis | 5 | 统计检验，可视化分析 |
| 6 | Writing | 9 | 撰写论文各章节 |
| 7 | Humanization | 9 | 去AI化润色，降低AI检测 |
| 8 | LaTeX | 12 | 双语排版，生成PDF |
| 9 | Review | 8 | 模拟同行评审，修改完善 |

**总任务数: 100**

---

## 部署指南

### 环境要求

- **Python**: 3.8+
- **Claude Code**: 最新版本
- **LaTeX** (可选): TeX Live 或 MiKTeX（用于生成 PDF）
- **Git**: 用于版本控制

### 安装步骤

#### 方法 1：直接克隆

```bash
# 1. 克隆仓库
git clone https://github.com/xingxingxingxin/prometheus-research-skill.git
cd prometheus-research-skill

# 2. 安装依赖
pip install -r scripts/requirements.txt

# 3. 验证安装
python scripts/start_research.py --help
```

#### 方法 2：作为 Claude Code Skill 安装

1. 将项目克隆到 Claude Code 的 skills 目录：

```bash
# Windows
git clone https://github.com/xingxingxingxin/prometheus-research-skill.git "%USERPROFILE%\.claude\skills\prometheus-research"

# Linux/Mac
git clone https://github.com/xingxingxingxin/prometheus-research-skill.git ~/.claude/skills/prometheus-research
```

2. 安装依赖：

```bash
cd ~/.claude/skills/prometheus-research  # 或 Windows 对应路径
pip install -r scripts/requirements.txt
```

3. 重启 Claude Code

### 配置说明

#### 执行配置 (`config/execution_config.yaml`)

```yaml
# Ralph Loop 配置
ralph:
  enabled: true
  max_iterations: 20        # 每个任务最大迭代次数
  completion_promise: "TASK_COMPLETE"
  iteration_timeout: 300    # 每次迭代超时（秒）

# GEP 错误恢复配置
gep:
  enabled: true
  min_confidence: 0.3       # 最低置信度阈值
  max_genes: 3              # 最大修复基因数
  max_capsules: 5           # 最大胶囊存储数

# 通用配置
execution:
  retry_count: 3            # 失败重试次数
  retry_delay: 30           # 重试间隔（秒）
  api_request_delay: 5      # API 请求间隔（秒）
```

#### 环境变量（可选）

```bash
# Windows PowerShell
$env:CLAUDE_CODE_PATH="C:\Users\YourName\AppData\Roaming\npm\claude.cmd"
$env:PERMISSION_MODE="acceptEdits"
$env:MAX_ITERATIONS="100"

# Linux/Mac
export CLAUDE_CODE_PATH="/usr/local/bin/claude"
export PERMISSION_MODE="acceptEdits"
export MAX_ITERATIONS="100"
```

---

## 使用方法

### 快速开始

在 Claude Code 中只需说：

```
启动研究 基于图神经网络的社交推荐系统
```

Skill 会自动：
1. 初始化项目结构
2. 生成 100 个任务
3. 启动后台执行进程
4. 告诉你如何监控进度

### 查看进度

```powershell
# Windows PowerShell - 实时查看日志
Get-Content Logs\executor.log -Wait -Tail 50

# Linux/Mac - 实时查看日志
tail -f Logs/executor.log
```

### 查看状态

```bash
python scripts/prometheus.py --status
```

### 手动执行（可选）

```bash
# 1. 初始化项目
python scripts/start_research.py --topic "你的研究主题"

# 2. 启动后台执行 (Windows)
start /b pythonw scripts/automation/task_executor.py --loop >> Logs/executor.log 2>&1

# 2. 启动后台执行 (Linux/Mac)
nohup python scripts/automation/task_executor.py --loop >> Logs/executor.log 2>&1 &

# 3. 查看日志
Get-Content Logs\executor.log -Wait -Tail 50   # Windows
tail -f Logs/executor.log                      # Linux/Mac
```

---

## 输出产物

研究完成后，在 `Projects/{研究主题}/output/` 生成：

```
output/
├── paper_en.pdf        # 英文论文
├── paper_zh.pdf        # 中文论文
└── supplementary.zip   # 代码和数据
```

### 项目目录结构

```
Projects/{研究主题}/
├── research_tasks.json      # 任务清单 (100个)
├── state.json               # 执行状态
├── logs/
│   └── executor.log         # 执行日志
├── data/
│   ├── papers/              # 下载的论文
│   └── search_results/      # 搜索结果
├── code/                    # 实验代码
├── notes/                   # 研究笔记
├── results/                 # 实验结果
├── paper/                   # Markdown 论文
├── latex/                   # LaTeX 源码
├── output/                  # 最终输出
└── references.bib           # 参考文献
```

---

## 目录结构

```
prometheus-research-skill/
├── SKILL.md                    # Claude Code Skill 定义
├── README.md                   # 本文档
├── LICENSE                     # MIT 许可证
├── AUTHORS                     # 作者信息
├── assets/                     # 展示图片
│   ├── workflow_overview.png
│   ├── experiment_results.png
│   ├── code_structure.png
│   └── logo.png
├── config/
│   └── execution_config.yaml   # 执行配置
├── scripts/
│   ├── start_research.py       # 启动研究入口
│   ├── prometheus.py           # 系统控制器
│   ├── automation/
│   │   └── task_executor.py    # 后台任务执行器
│   ├── Core/
│   │   ├── prompts/            # 10个阶段提示词
│   │   │   ├── phase0_topic.md
│   │   │   ├── phase1_literature.md
│   │   │   ├── ...
│   │   │   └── phase9_review.md
│   │   ├── gep/                # GEP 错误恢复模块
│   │   │   ├── selector.py
│   │   │   ├── gene_manager.py
│   │   │   └── capsule_store.py
│   │   └── tools/              # 科研工具集
│   │       ├── arxiv_search.py
│   │       ├── semantic_scholar_search.py
│   │       ├── paper_downloader.py
│   │       ├── statistical_test.py
│   │       ├── latex_compiler.py
│   │       └── humanizer/
│   ├── agent/
│   │   └── ralph_loop.py       # Ralph Loop 迭代模块
│   └── requirements.txt
├── Projects/                   # 项目目录（运行时生成）
└── Logs/                       # 日志目录（运行时生成）
```

---

## 常见问题

### Q: 后台进程如何停止？

```bash
# Windows - 查找并结束进程
tasklist | findstr pythonw
taskkill /PID <进程ID> /F

# Linux/Mac
ps aux | grep task_executor
kill <进程ID>
```

### Q: 如何从中断的任务恢复？

后台执行器会自动从 `state.json` 读取进度，找到第一个 `pending` 或 `in_progress` 的任务继续执行。

### Q: 日志文件在哪里？

```
Logs/executor.log           # 主执行日志
Projects/{topic}/logs/      # 项目特定日志
```

### Q: 如何修改任务执行顺序？

编辑 `Projects/{topic}/research_tasks.json`，修改任务的 `priority` 字段：
- `high`: 高优先级
- `medium`: 中优先级
- `low`: 低优先级

---

## 联系方式

- **作者**: xingye
- **微信**: xingye4088
- **GitHub**: https://github.com/xingxingxingxin

---

*版权所有 (c) 2026 xingye*

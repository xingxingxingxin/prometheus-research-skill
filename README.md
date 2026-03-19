# Prometheus Research Skill

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> 全自主科研智能体 - 自动完成从文献调研到论文撰写的完整研究流程

**Claude Code Skill** - 让 Claude 自动帮你完成学术研究的全流程！

## 功能特点

| 功能 | 说明 |
|------|------|
| **10阶段工作流** | 从主题分析到论文提交的完整流程 |
| **100个任务** | 细粒度的研究任务分解 |
| **后台执行** | 任务后台运行，通过日志监控进度 |
| **状态持久化** | 支持中断恢复 |
| **完整工具集** | 文献搜索、统计分析、LaTeX编译等 |

## 快速安装

### 方法一：一键安装（推荐）

```bash
# 克隆到 Claude Code skills 目录
git clone https://github.com/xingxingxingxin/prometheus-research-skill.git ~/.claude/skills/prometheus-research
```

### 方法二：项目级安装

```bash
# 在你的项目目录中
mkdir -p .claude/skills
git clone https://github.com/xingxingxingxin/prometheus-research-skill.git .claude/skills/prometheus-research
```

### 方法三：手动安装

1. 下载 [ZIP 包](https://github.com/xingxingxingxin/prometheus-research-skill/archive/refs/heads/master.zip)
2. 解压到 `~/.claude/skills/prometheus-research/`

## 使用方法

### 方式一：Claude Code 对话（推荐）

在 Claude Code 中，直接说：

```
启动一个关于"大语言模型在代码审查中的应用"的研究
```

或者：

```
继续研究
```

### 方式二：后台执行（独立运行）

```powershell
# Windows
# 1. 启动研究
python scripts/start_research.py --topic "研究主题"

# 2. 后台执行
call scripts/run_background.bat

# 3. 监控进度
call scripts/monitor.bat
# 或实时查看日志
Get-Content Logs\executor_*.log -Wait -Tail 50
```

```bash
# Linux/Mac
# 1. 启动研究
python scripts/start_research.py --topic "研究主题"

# 2. 后台执行
./scripts/run_background.sh

# 3. 监控进度
./scripts/monitor.sh
# 或实时查看日志
tail -f Logs/executor_*.log
```

### 查看状态

```bash
python scripts/prometheus.py --status
```

就这么简单！

## 工作流程

```
┌─────────────────────────────────────────────────────────────┐
│                    10 阶段研究工作流                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Phase 0: 主题分析 (4 tasks)                                 │
│  Phase 1: 文献调研 (34 tasks) ← 搜索、筛选、研读文献          │
│  Phase 2: 假设设计 (6 tasks)                                 │
│  Phase 3: 代码实现 (7 tasks)                                 │
│  Phase 4: 实验执行 (6 tasks)                                 │
│  Phase 5: 结果分析 (5 tasks)                                 │
│  Phase 6: 论文撰写 (9 tasks)                                 │
│  Phase 7: 去AI化 (9 tasks)                                   │
│  Phase 8: LaTeX (12 tasks)                                   │
│  Phase 9: 同行评审 (8 tasks)                                 │
│                                                             │
│  总计: 100 个任务                                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 触发词

- "启动研究"、"开始研究"、"做一个研究"
- "继续研究"、"执行下一个任务"
- "文献综述"、"调研"
- "写论文"、"实验分析"

## 输出

研究完成后，会在 `Projects/{研究主题}/output/` 目录生成：

```
output/
├── paper_en.pdf        # 英文论文
├── paper_zh.pdf        # 中文论文（可选）
└── supplementary.zip   # 代码和数据
```

## 目录结构

```
prometheus-research/
├── SKILL.md                 # 主技能文件
├── README.md                # 本文件
├── references/
│   ├── workflow.md          # 详细工作流说明
│   └── templates.md         # 输出模板
└── evals/
    └── evals.json           # 测试用例
```

## 示例对话

**用户**: 启动一个关于"强化学习在机器人路径规划中的应用"的研究

**Claude**:
```
好的，我来启动这个研究项目。

[创建项目目录结构]
[初始化状态文件和任务清单]

项目已创建: Projects/强化学习在机器人路径规划中的应用/
当前阶段: Phase 0 - 主题分析
当前任务: T001 - 分析研究主题

开始执行 T001...

[执行任务内容]

<promise>TASK_COMPLETE</promise>
任务 T001 已完成

继续执行 T002...
```

## 系统要求

- Claude Code CLI
- Git（用于克隆仓库）

## 许可证

MIT License - 可自由使用、修改和分发

## 相关链接

- [Prometheus 主项目](https://github.com/xingxingxingxin/prometheus) - 完整的科研智能体系统
- [Claude Code 文档](https://docs.anthropic.com/claude-code) - Claude Code 官方文档

---

*让科研自动化成为可能*

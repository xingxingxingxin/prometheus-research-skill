# prometheus-research

name: prometheus-research
description: |
  全自主科研智能体 - 后台执行完整的10阶段100任务研究流程。

  **触发条件**（当用户说以下内容时必须使用此技能）：
  - "启动研究"、"开始研究"、"做一个研究"
  - "帮我研究"、"调研一下"、"文献综述"
  - 用户提到任何研究相关需求

  **核心要求**: 此技能必须通过 Bash 工具启动后台进程执行，不可在对话中直接执行任务。

---

# Project Prometheus - 全自主科研智能体

> **原创作者**: xingye
> **微信**: xingye4088
> **版权所有 (c) 2026 xingye**

---

## ⚠️ 重要：执行模式

**此技能必须使用后台执行模式。**

当用户触发此技能时，你必须**立即**使用 Bash 工具执行以下命令，**不要**在对话中执行研究任务：

### 步骤 1：初始化项目（必须使用 Bash 工具）

```
使用 Bash 工具执行：
python scripts/start_research.py --topic "用户的研究主题"
```

### 步骤 2：启动后台执行（必须使用 Bash 工具）

**Windows:**
```
使用 Bash 工具执行：
start /b pythonw scripts/automation/task_executor.py --project "Projects/项目名" --loop >> Logs/executor.log 2>&1
```

**Linux/Mac:**
```
使用 Bash 工具执行：
nohup python scripts/automation/task_executor.py --project "Projects/项目名" --loop >> Logs/executor.log 2>&1 &
```

### 步骤 3：告知用户监控方式

执行启动后，告诉用户：

```
研究已在后台启动！

查看实时进度：
  Get-Content Logs\executor.log -Wait -Tail 50   (Windows PowerShell)
  tail -f Logs/executor.log                      (Linux/Mac)
```

---

## 完整执行流程

### 当用户说"启动研究 [主题]"时：

**1. 提取研究主题**

**2. 生成项目名称**（从主题提取，去掉特殊字符，空格替换为下划线）

**3. 执行初始化命令**
```bash
python scripts/start_research.py --topic "研究主题"
```

**4. 执行后台启动命令**
```bash
# Windows
start /b pythonw scripts/automation/task_executor.py --project "Projects/项目名" --loop >> Logs/executor.log 2>&1

# Linux/Mac
nohup python scripts/automation/task_executor.py --project "Projects/项目名" --loop >> Logs/executor.log 2>&1 &
```

**5. 输出监控提示**
```
✅ 研究已在后台启动！

📁 项目目录: Projects/项目名/
📝 日志文件: Logs/executor.log

查看进度：
  Get-Content Logs\executor.log -Wait -Tail 50   (Windows)
  tail -f Logs/executor.log                      (Linux/Mac)
```

---

## 10 阶段 100 任务工作流

| Phase | 名称 | 任务数 |
|-------|------|--------|
| 0 | Topic Analysis | 4 |
| 1 | Literature Review | 34 |
| 2 | Hypothesis Design | 6 |
| 3 | Coding | 7 |
| 4 | Execution | 6 |
| 5 | Analysis | 5 |
| 6 | Writing | 9 |
| 7 | Humanization | 9 |
| 8 | LaTeX | 12 |
| 9 | Review | 8 |

---

## 项目目录结构

```
Projects/{project_name}/
├── research_tasks.json      # 任务清单
├── state.json               # 执行状态
├── logs/executor.log        # 执行日志
├── data/papers/             # 下载的论文
├── code/                    # 实验代码
├── notes/                   # 研究笔记
├── paper/                   # Markdown论文
├── latex/                   # LaTeX源码
└── output/                  # 最终PDF
```

---

## 依赖安装

```bash
pip install -r scripts/requirements.txt
```

---

*Project Prometheus - 让科研自动化成为可能*

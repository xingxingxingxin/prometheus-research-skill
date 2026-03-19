# prometheus-research

name: prometheus-research
description: |
  全自主科研智能体 - 后台执行研究流程。

  **触发**: 用户说"启动研究"、"开始研究"、"做一个研究"、"帮我研究"

  **执行方式**: 启动后台 Python 进程，用户通过日志监控进度。

---

# Prometheus Research Skill

> **原创作者**: xingye | **微信**: xingye4088 | **版权所有 (c) 2026**

---

## ⛔ 核心规则

**你的唯一任务是启动后台进程。不要自己执行研究任务。**

当用户说"启动研究 [主题]"时，你必须：

1. 使用 Bash 工具运行 `start_research.py`
2. 使用 Bash 工具启动后台执行器
3. 告诉用户如何查看日志

---

## 执行步骤

### 步骤 1：初始化项目

```bash
cd D:/auto-system/prometheus2 && python scripts/start_research.py --topic "研究主题"
```

### 步骤 2：启动后台执行

**Windows:**
```bash
cd D:/auto-system/prometheus2 && mkdir -p Logs && start /b pythonw scripts/automation/task_executor.py --loop >> Logs/executor.log 2>&1
```

**Linux/Mac:**
```bash
cd D:/auto-system/prometheus2 && mkdir -p Logs && nohup python scripts/automation/task_executor.py --loop >> Logs/executor.log 2>&1 &
```

### 步骤 3：输出监控提示

```
✅ 研究已在后台启动

📁 项目目录: D:/auto-system/prometheus2/Projects/项目名/
📝 日志文件: D:/auto-system/prometheus2/Logs/executor.log

查看进度：
  Get-Content D:\auto-system\prometheus2\Logs\executor.log -Wait -Tail 50
```

---

## 示例

用户: "启动研究 图神经网络社交推荐"

你应该执行：

```bash
cd D:/auto-system/prometheus2 && python scripts/start_research.py --topic "图神经网络社交推荐"
```

```bash
cd D:/auto-system/prometheus2 && mkdir -p Logs && start /b pythonw scripts/automation/task_executor.py --loop >> Logs/executor.log 2>&1
```

然后输出：
```
✅ 研究已在后台启动

查看进度：
  Get-Content D:\auto-system\prometheus2\Logs\executor.log -Wait -Tail 50
```

---

## 10阶段工作流

后台执行器会自动完成 100 个任务：

| Phase | 任务 |
|-------|------|
| 0 | 主题分析 (4) |
| 1 | 文献综述 (34) |
| 2 | 假设设计 (6) |
| 3 | 代码实现 (7) |
| 4 | 实验执行 (6) |
| 5 | 结果分析 (5) |
| 6 | 论文撰写 (9) |
| 7 | 去AI化 (9) |
| 8 | LaTeX (12) |
| 9 | 评审 (8) |

---

## 安装

```bash
pip install -r scripts/requirements.txt
```

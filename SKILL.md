# prometheus-research

name: prometheus-research
description: |
  全自主科研智能体 - 后台执行研究任务，通过日志监控进度。

  **触发条件**：
  - "启动研究"、"开始研究"
  - "继续研究"
  - "查看进度"、"监控日志"

---

# Prometheus Research - 后台执行模式

## 工作方式

```
┌─────────────────────────────────────────────────────────────┐
│                      后台执行模式                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. 启动研究（后台）                                         │
│     $ call scripts\run_background.bat                       │
│     └→ 任务在后台运行                                        │
│                                                             │
│  2. 监控进度（日志）                                         │
│     $ call scripts\monitor.bat                              │
│     └→ 实时查看执行日志                                      │
│                                                             │
│  3. 查看状态                                                 │
│     $ python scripts\prometheus.py --status                 │
│     └→ 获取当前进度摘要                                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 命令速查

| 操作 | 命令 |
|------|------|
| **后台执行** | `call scripts\run_background.bat` |
| **监控日志** | `call scripts\monitor.bat` |
| **查看状态** | `python scripts\prometheus.py --status` |
| **实时日志** | `Get-Content Logs\executor_*.log -Wait -Tail 50` |

## 日志位置

```
Logs/
├── executor_YYYYMMDD_HHMMSS.log   # 执行日志
├── workflow.log                    # 工作流日志
└── error_trace.log                 # 错误追踪
```

## 10 阶段工作流

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

**总计: 100 个任务**

详细任务说明见 `references/workflow.md`

## 状态持久化

- 状态文件: `Projects/{项目}/.prometheus/state.json`
- 任务清单: `Projects/{项目}/.prometheus/research_tasks.json`
- 支持中断恢复

## 输出

研究完成后，在 `Projects/{研究主题}/output/` 生成：

```
output/
├── paper_en.pdf        # 英文论文
├── paper_zh.pdf        # 中文论文（可选）
└── supplementary.zip   # 代码和数据
```

## 依赖

```bash
pip install -r scripts/requirements.txt
```

---

*Project Prometheus - 后台执行模式*

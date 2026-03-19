# Prometheus Research Skill

> 全自主科研智能体 - 后台执行，日志监控

## 工作方式

**后台执行 + 日志监控**

```
启动研究 → 后台运行 → 查看日志 → 完成输出
```

## 使用方法

### 1. 后台执行

```powershell
# Windows
call scripts\run_background.bat

# Linux/Mac
./scripts/run_background.sh
```

### 2. 监控日志

```powershell
# Windows
call scripts\monitor.bat

# 或实时查看
Get-Content Logs\executor_*.log -Wait -Tail 50

# Linux/Mac
./scripts/monitor.sh
# 或
tail -f Logs/executor_*.log
```

### 3. 查看状态

```bash
python scripts/prometheus.py --status
```

## 日志文件

| 文件 | 说明 |
|------|------|
| `Logs/executor_*.log` | 执行日志 |
| `Logs/workflow.log` | 工作流日志 |
| `Logs/error_trace.log` | 错误追踪 |

## 输出

```
Projects/{研究主题}/output/
├── paper_en.pdf        # 英文论文
├── paper_zh.pdf        # 中文论文
└── supplementary.zip   # 代码和数据
```

## 10 阶段 100 任务

| Phase | 名称 | 任务数 |
|-------|------|--------|
| 0 | Topic | 4 |
| 1 | Literature | 34 |
| 2 | Hypothesis | 6 |
| 3 | Coding | 7 |
| 4 | Execution | 6 |
| 5 | Analysis | 5 |
| 6 | Writing | 9 |
| 7 | Humanization | 9 |
| 8 | LaTeX | 12 |
| 9 | Review | 8 |

## 安装

```bash
git clone https://github.com/xingxingxingxin/prometheus-research-skill.git
cd prometheus-research-skill
pip install -r scripts/requirements.txt
```

## 目录结构

```
prometheus-research-skill/
├── SKILL.md
├── README.md
├── scripts/
│   ├── run_background.bat/.sh   # 后台执行
│   ├── monitor.bat/.sh          # 日志监控
│   ├── prometheus.py            # 控制器
│   ├── start_research.py        # 启动脚本
│   ├── Core/                    # 核心模块
│   └── ...
└── references/
    └── workflow.md              # 工作流详情
```

---

*后台执行模式*

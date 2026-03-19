# Prometheus Research Skill

> 全自主科研智能体 - 后台执行，日志监控

**原创作者: xingye**
**微信: xingye4088**

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

## 工作方式

**后台执行 + 日志监控**

```
启动研究 → 后台运行 → 查看日志 → 完成输出
```

---

## 在 Claude Code 中使用

### 方法 1：直接触发（推荐）

只需对 Claude Code 说：

```
启动研究 [你的研究主题]
```

例如：
```
启动研究 基于图神经网络的社交推荐系统
```

Claude Code 会自动：
1. 运行 `start_research.py` 生成任务清单
2. 启动后台执行
3. 告诉你如何监控进度

### 方法 2：手动执行

**步骤 1：初始化项目**
```bash
python scripts/start_research.py --topic "你的研究主题"
```

**步骤 2：启动后台执行**

Windows:
```powershell
call scripts\run_background.bat
```

Linux/Mac:
```bash
./scripts/run_background.sh
```

**步骤 3：监控进度**

Windows PowerShell:
```powershell
# 实时查看日志
Get-Content Logs\executor_*.log -Wait -Tail 50

# 或使用监控菜单
call scripts\monitor.bat
```

Linux/Mac:
```bash
# 实时查看日志
tail -f Logs/executor_*.log

# 或使用监控菜单
./scripts/monitor.sh
```

---

## 监控命令

| 命令 | 说明 |
|------|------|
| `Get-Content Logs\executor_*.log -Wait -Tail 50` | 实时日志 (Windows) |
| `tail -f Logs/executor_*.log` | 实时日志 (Linux/Mac) |
| `call scripts\monitor.bat` | 监控菜单 (Windows) |
| `./scripts/monitor.sh` | 监控菜单 (Linux/Mac) |
| `python scripts/prometheus.py --status` | 查看状态 |

---

## 输出

研究完成后，在 `Projects/{研究主题}/output/` 生成：

```
output/
├── paper_en.pdf        # 英文论文
├── paper_zh.pdf        # 中文论文（可选）
└── supplementary.zip   # 代码和数据
```

---

## 10 阶段 100 任务

| Phase | 名称 | 任务数 | 说明 |
|-------|------|--------|------|
| 0 | Topic | 4 | 主题分析 |
| 1 | Literature | 34 | 文献综述 |
| 2 | Hypothesis | 6 | 假设设计 |
| 3 | Coding | 7 | 代码实现 |
| 4 | Execution | 6 | 实验执行 |
| 5 | Analysis | 5 | 结果分析 |
| 6 | Writing | 9 | 论文撰写 |
| 7 | Humanization | 9 | 去AI化润色 |
| 8 | LaTeX | 12 | LaTeX排版 |
| 9 | Review | 8 | 同行评审 |

---

## 安装

```bash
git clone https://github.com/xingxingxingxin/prometheus-research-skill.git
cd prometheus-research-skill
pip install -r scripts/requirements.txt
```

---

## 目录结构

```
prometheus-research-skill/
├── SKILL.md                    # Claude Code Skill 定义
├── README.md
├── LICENSE
├── AUTHORS
├── config/
│   └── execution_config.yaml   # 执行配置
├── scripts/
│   ├── start_research.py       # 启动研究
│   ├── run_background.bat/.sh  # 后台执行
│   ├── monitor.bat/.sh         # 日志监控
│   ├── prometheus.py           # 系统控制器
│   ├── automation/             # 自动化模块
│   │   └── task_executor.py    # 任务执行器
│   ├── Core/                   # 核心模块
│   │   ├── prompts/            # 阶段提示词
│   │   ├── gep/                # GEP 错误恢复
│   │   └── tools/              # 科研工具
│   └── requirements.txt
├── Projects/                   # 项目目录（运行时生成）
└── Logs/                       # 日志目录（运行时生成）
```

---

## 联系方式

- **作者**: xingye
- **微信**: xingye4088
- **GitHub**: https://github.com/xingxingxingxin

---

*版权所有 (c) 2026 xingye*

# Prometheus Research Skill

全自主科研智能体 - 自动完成从文献调研到论文撰写的完整研究流程。

## 安装方法

### 方法一：复制到 Claude Code skills 目录

```bash
# 复制整个 prometheus-research 目录到你的 skills 目录
cp -r prometheus-research ~/.claude/skills/
```

### 方法二：作为项目级 skill 使用

将 `prometheus-research` 目录放在你的项目的 `.claude/skills/` 目录下：

```
your-project/
├── .claude/
│   └── skills/
│       └── prometheus-research/
│           ├── skill.md
│           ├── references/
│           │   ├── workflow.md
│           │   └── templates.md
│           └── evals/
│               └── evals.json
```

## 使用方法

在 Claude Code 中，直接说：

```
启动一个关于"XXX"的研究
```

或者：

```
继续研究
```

## 功能

- **10阶段工作流**: 从主题分析到论文提交的完整流程
- **100个任务**: 细粒度的研究任务分解
- **状态持久化**: 支持中断恢复
- **模板支持**: 论文、实验报告、文献综述等模板

## 目录结构

```
prometheus-research/
├── skill.md              # 主技能文件
├── README.md             # 本文件
├── references/
│   ├── workflow.md       # 详细工作流说明
│   └── templates.md      # 输出模板
└── evals/
    └── evals.json        # 测试用例
```

## 触发词

- "启动研究"、"开始研究"
- "继续研究"、"执行下一个任务"
- "文献综述"、"调研"
- "写论文"、"实验分析"

## 输出

研究完成后，会在 `Projects/{研究主题}/output/` 目录生成：

- `paper_en.pdf` - 英文论文
- `paper_zh.pdf` - 中文论文（可选）
- `supplementary.zip` - 代码和数据

## 许可证

MIT License

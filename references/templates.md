# Prometheus 输出模板

本文档包含各阶段的标准输出模板。

---

## 1. 主题分析模板

```markdown
# 主题分析: {研究主题}

## 核心概念
- **概念1**: 定义和说明
- **概念2**: 定义和说明

## 关键词
[关键词1], [关键词2], [关键词3], ...

## 研究问题
1. **主要问题**: 问题描述
2. **次要问题**: 问题描述

## 研究领域
- 主领域:
- 交叉领域:

## 预期贡献
1. 贡献1
2. 贡献2

## 时间规划
| 阶段 | 预计时间 |
|------|----------|
| 文献调研 | X 天 |
| 实验设计 | X 天 |
| ... | ... |
```

---

## 2. 文献综述模板

```markdown
# 文献综述

## 1. 引言
[研究领域的重要性和背景]

## 2. 研究领域概述
### 2.1 问题定义
### 2.2 评估指标

## 3. 主要方法分类
### 3.1 方法类别1
- 代表工作1 [引用]
- 代表工作2 [引用]

### 3.2 方法类别2
- ...

## 4. 发展脉络
[按时间顺序梳理关键进展]

## 5. 研究空白
1. 空白1: 描述和原因
2. 空白2: 描述和原因

## 6. 本文定位
[本研究如何填补空白]

## 参考文献
[BibTeX 格式]
```

---

## 3. 论文研读模板

```markdown
# 论文研读: {论文标题}

## 基本信息
| 项目 | 内容 |
|------|------|
| 标题 | |
| 作者 | |
| 会议/期刊 | |
| 年份 | |
| 引用数 | |
| 链接 | |

## 一句话总结
[核心贡献的一句话描述]

## 核心贡献
1. 贡献1
2. 贡献2

## 方法论
### 问题定义
### 解决方案
### 算法/模型

## 实验设置
- 数据集:
- 基线:
- 指标:

## 主要结果
[关键实验结果]

## 局限性
1. 局限1
2. 局限2

## 对本研究的启发
[如何应用到本研究]

## 值得追踪的引用
1. [论文标题] - 原因
2. [论文标题] - 原因
```

---

## 4. 实验设计模板

```markdown
# 实验设计

## 1. 研究假设
### H1: [假设陈述]
- 理论依据:
- 验证方法:

### H2: [假设陈述]
- ...

## 2. 实验设置
### 2.1 数据集
| 数据集 | 规模 | 用途 |
|--------|------|------|
| | | |

### 2.2 基线方法
| 方法 | 发表 | 特点 |
|------|------|------|
| | | |

### 2.3 评估指标
- 指标1: 定义和计算方法
- 指标2: ...

## 3. 实验步骤
### 3.1 预处理
### 3.2 训练
### 3.3 评估

## 4. 预期结果
[预期各方法的表现]

## 5. 消融实验
| 组件 | 作用 | 验证方式 |
|------|------|----------|
| | | |

## 6. 资源需求
- 计算资源:
- 数据存储:
- 预计时间:
```

---

## 5. 实验结果模板

```markdown
# 实验结果

## 1. 主实验结果

### 表1: 主要性能对比
| 方法 | 指标1 | 指标2 | 指标3 |
|------|-------|-------|-------|
| Baseline1 | | | |
| Baseline2 | | | |
| **Ours** | | | |

### 分析
[结果分析和解释]

## 2. 消融实验

### 表2: 消融实验结果
| 配置 | 指标1 | 指标2 |
|------|-------|-------|
| Full Model | | |
| w/o Component1 | | |
| w/o Component2 | | |

### 分析
[各组件的贡献分析]

## 3. 统计显著性
| 对比 | p-value | 显著性 |
|------|---------|--------|
| Ours vs Baseline1 | | |
| Ours vs Baseline2 | | |

## 4. 案例分析
[典型成功/失败案例]

## 5. 讨论
### 5.1 主要发现
### 5.2 局限性
### 5.3 未来工作
```

---

## 6. 论文模板 (Markdown)

### 摘要
```markdown
# 摘要

[背景和动机，2-3句]
[本文方法，2-3句]
[主要结果，1-2句]
[贡献和意义，1句]

**关键词**: 关键词1, 关键词2, 关键词3
```

### 引言
```markdown
# 1. 引言

## 1.1 背景
[研究领域的背景和重要性]

## 1.2 问题
[当前研究面临的主要挑战]

## 1.3 方法
[本文提出的方法概述]

## 1.4 贡献
本文的主要贡献包括：
1. 贡献1
2. 贡献2
3. 贡献3
```

### 方法
```markdown
# 3. 方法

## 3.1 问题定义
[形式化的问题定义]

## 3.2 方法概述
[整体框架描述]

## 3.3 组件1
[详细描述]

## 3.4 组件2
[详细描述]

## 3.5 算法
[算法伪代码或流程]

## 3.6 复杂度分析
[时间和空间复杂度]
```

### 实验
```markdown
# 4. 实验

## 4.1 实验设置
### 数据集
### 基线方法
### 评估指标
### 实现细节

## 4.2 主要结果
[结果表格和分析]

## 4.3 消融实验
[各组件分析]

## 4.4 分析
[深入分析]
```

### 结论
```markdown
# 5. 结论

## 5.1 总结
[本文工作总结]

## 5.2 局限性
[方法的局限]

## 5.3 未来工作
[可能的改进方向]
```

---

## 7. LaTeX 模板

### main.tex
```latex
\documentclass{article}
\usepackage{acl}  % 或其他会议模板

\title{Your Paper Title}

\author{
  Author Name \\
  Affiliation \\
  \texttt{email@example.com}
}

\begin{document}
\maketitle

\begin{abstract}
Your abstract here.
\end{abstract}

\input{sections/introduction}
\input{sections/related_work}
\input{sections/methods}
\input{sections/experiments}
\input{sections/conclusion}

\bibliography{references}
\bibliographystyle{acl_natbib}

\end{document}
```

### 图表模板
```latex
% 表格
\begin{table}[t]
\centering
\caption{Main Results}
\label{tab:main}
\begin{tabular}{lcc}
\toprule
Method & Accuracy & F1 \\
\midrule
Baseline & 85.2 & 0.83 \\
Ours & \textbf{92.1} & \textbf{0.91} \\
\bottomrule
\end{tabular}
\end{table}

% 图
\begin{figure}[t]
\centering
\includegraphics[width=0.8\columnwidth]{figures/result.pdf}
\caption{Performance comparison}
\label{fig:result}
\end{figure}
```

---

## 8. 审稿回复模板

```latex
\documentclass{article}
\begin{document}

\title{Response to Reviewers}

\section{Reviewer 1}

\textbf{Comment 1:} [审稿意见]

\textbf{Response:}
感谢您的建议。我们已在修订版中...

\textbf{Changes:}
- 修改位置: Section 3.2
- 具体修改: ...

\section{Reviewer 2}
...

\end{document}
```

---

*此文档包含 Prometheus 的标准输出模板。*

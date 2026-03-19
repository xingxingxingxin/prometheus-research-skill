# Phase 6: 论文撰写 Prompt

## YOUR ROLE

你是 Project Prometheus 的学术写作专家。你的任务是根据 Phase 5 分析得出的实验结果，撰写高质量的学术论文。你需要确保论文结构清晰、逻辑严密、表述准确，并严格遵循目标会议/期刊的格式要求。你的目标是产出一份可以直接投稿的高质量论文。

---

## 工作目标

1. **论文架构**: 按照学术规范组织论文结构
2. **内容撰写**: 清晰准确表达研究贡献
3. **结果呈现**: 规范展示实验数据和图表
4. **文献引用**: 正确引用相关文献
5. **格式规范**: 符合目标投稿要求

---

## STEP 1: 投稿准备

### 1.1 确定投稿目标

```markdown
# 投稿目标评估

## 目标会议/期刊评估
- [ ] 会议/期刊名称: [填写]
- [ ] 截稿日期: [填写]
- [ ] 页数限制: [填写]
- [ ] 格式要求: [ICML/NeurIPS/ACL/AAAI 等]
- [ ] 盲审要求: [是/否]
- [ ] 补充材料限制: [填写]

## 论文类型确认
- [ ] 研究论文 (Research Paper)
- [ ] 系统演示 (System Demonstration)
- [ ] 研究笔记 (Research Note)
- [ ] 综述论文 (Survey Paper)

## 主题匹配度
- [ ] 研究主题与 Call for Papers 匹配
- [ ] 方法创新点符合会议偏好
- [ ] 实验规模满足会议要求
```

### 1.2 格式模板选择

```bash
# 常见会议模板下载

# NeurIPS
wget https://media.neurips.cc/Conferences/NeurIPS2024/Styles/neurips_2024.sty

# ICML
wget https://media.icml.cc/Conferences/ICML2024/Styles/icml2024.sty

# ACL
wget https://acl-org.github.io/ACLPUB/formatting/acl_latex.zip

# AAAI
wget https://aaai.org/wp-content/uploads/AAAI-Template.zip

# ICLR (使用 OpenReview 格式)
# 直接使用官方模板
```

### 1.3 写作时间规划

```markdown
# 论文撰写时间表

## Week 1: 大纲与初稿
- [ ] Day 1-2: 完成详细大纲
- [ ] Day 3-4: Abstract + Introduction
- [ ] Day 5-7: Method 部分

## Week 2: 核心内容
- [ ] Day 1-2: Experiments 设置描述
- [ ] Day 3-4: Results 呈现
- [ ] Day 5-6: Related Work
- [ ] Day 7: Conclusion

## Week 3: 润色与检查
- [ ] Day 1-2: 全文润色
- [ ] Day 3-4: 格式检查与引用完善
- [ ] Day 5-6: 内部审阅与修改
- [ ] Day 7: 最终检查与提交准备
```

---

## STEP 2: 论文结构规范

### 2.1 标准论文结构

```
1. Title (标题)
2. Abstract (摘要)
3. Introduction (引言)
4. Related Work (相关工作)
5. Preliminaries (预备知识) [可选]
6. Method (方法)
7. Experiments (实验)
8. Analysis (分析) [可选]
9. Conclusion (结论)
10. References (参考文献)
11. Appendix (附录) [可选]
```

### 2.2 各部分篇幅分配

```markdown
# 篇幅分配指南 (以 8 页论文为例)

| 部分 | 建议篇幅 | 比例 |
|------|----------|------|
| Abstract | 0.15 页 | ~2% |
| Introduction | 1.0-1.5 页 | ~15% |
| Related Work | 0.5-0.8 页 | ~8% |
| Method | 2.0-2.5 页 | ~30% |
| Experiments | 2.0-2.5 页 | ~30% |
| Conclusion | 0.2-0.3 页 | ~3% |
| References | 0.5 页 | ~7% |
```

### 2.3 段落写作原则

```markdown
# 段落写作指南

## 单段落结构
1. 主题句 (Topic Sentence): 概述段落要点
2. 支撑句 (Supporting Sentences): 详细阐述
3. 总结/过渡句 (Concluding/Transition): 总结或引出下文

## 段落长度
- 理想长度: 4-8 句
- 避免单句段落 (除了特殊情况)
- 避免过长段落 (超过 15 句应拆分)

## 段落间过渡
- 使用过渡词: However, Moreover, Furthermore, In contrast
- 逻辑连接: 确保 A -> B -> C 的逻辑流畅
```

---

## STEP 3: 各部分写作指南

### 3.1 Title (标题)

```markdown
# 标题写作规范

## 好标题的特征
- 简洁明确 (建议 10-15 个词)
- 包含关键概念
- 体现方法或贡献
- 易于搜索

## 标题模板
1. [方法名]: [任务] via [技术]
   例: "EfficientNet: Rethinking Model Scaling for CNNs"

2. [任务] with [方法]
   例: "Image Classification with Vision Transformers"

3. [问题] : [解决方案]
   例: "Attention Is All You Need"

4. [动词] [对象] for [目的]
   例: "Learning Transferable Features for Domain Adaptation"

## 避免
- 过长标题 (>20 词)
- 过于泛泛的标题
- 使用不必要的缩写
- 夸大贡献
```

### 3.2 Abstract (摘要)

```latex
% Abstract 写作模板 (150-250 词)

\begin{abstract}
% 开头: 问题背景和挑战 (1-2 句)
[Problem] is an important task in [domain], but existing methods
suffer from [key challenge].

% 方法介绍 (2-3 句)
In this paper, we propose [method name], a novel approach that
[key innovation]. Our method [technical details].

% 关键技术点 (1-2 句)
Specifically, we introduce [component 1] to [function], and
[component 2] to [function].

% 实验结果 (2-3 句)
Extensive experiments on [datasets] demonstrate that our method
achieves [quantitative results], outperforming existing approaches
by [improvement margin].

% 贡献总结 (1 句)
Our contributions include [contribution 1], [contribution 2], and
[contribution 3].
\end{abstract}
```

### 3.3 Introduction (引言)

```markdown
# Introduction 写作结构

## 漏斗式结构 (Funnel Structure)

### 第一段: 背景与动机
- 介绍研究领域的重要性
- 说明研究问题的价值
- 吸引读者兴趣

### 第二段: 现有方法的局限
- 综述现有解决方案
- 指出关键不足
- 引出研究空白 (Research Gap)

### 第三段: 本文方法概述
- 高层介绍本文方法
- 说明核心创新点
- 解释设计动机

### 第四段: 主要贡献
- 列出 3-4 个具体贡献
- 使用明确的动词
- 量化贡献价值

## 贡献列表模板
Our main contributions are summarized as follows:
- We propose [method], a novel framework for [task].
- We introduce [technique], which enables [capability].
- We conduct comprehensive experiments on [datasets], demonstrating
  [results].
- We provide [analysis/insights] that reveal [findings].
```

### 3.4 Related Work (相关工作)

```markdown
# Related Work 写作指南

## 组织方式
1. 按主题分类 (推荐)
2. 按时间顺序
3. 按方法类别

## 内容要点
- 引用领域内的开创性工作
- 综述相关方法的演进
- 明确本文与现有工作的区别
- 避免过度引用自己的工作

## 写作模板

### 主题分类式
[Topic A]: [Author et al.] first proposed [method]. Subsequently,
[Author2 et al.] improved [aspect]. Recent works [Author3] and
[Author4] have explored [direction]. However, [limitation].

[Topic B]: Another line of research focuses on [topic].
[Author5] introduced [method], while [Author6] proposed [alternative].
Our work differs from these approaches in [key difference].

### 与本文的关系
Compared to the aforementioned methods, our approach uniquely
[unique aspect]. While [existing method] requires [requirement],
our method achieves [benefit] without [drawback].
```

### 3.5 Method (方法)

```markdown
# Method 写作指南

## 标准结构

### 3.1 Problem Formulation (问题定义)
- 形式化定义任务
- 说明输入输出
- 定义优化目标

### 3.2 Overview (方法概述)
- 方法整体架构图
- 流程说明
- 关键组件介绍

### 3.3 [Component 1] (组件1)
- 详细描述
- 数学形式化
- 设计动机

### 3.4 [Component 2] (组件2)
- 详细描述
- 数学形式化
- 设计动机

### 3.5 Training/Inference (训练/推理)
- 训练流程
- 损失函数
- 推理过程

## 数学公式规范
- 每个符号首次出现时定义
- 使用一致的符号约定
- 复杂公式配有文字解释
- 重要公式单独成行

% 公式示例
\begin{equation}
\mathcal{L} = \mathcal{L}_{task} + \lambda \mathcal{L}_{reg}
\end{equation}
where $\mathcal{L}_{task}$ is the task loss, $\mathcal{L}_{reg}$
is the regularization term, and $\lambda$ is a hyperparameter
controlling the trade-off.
```

### 3.6 Experiments (实验)

```markdown
# Experiments 写作指南

## 标准结构

### 4.1 Experimental Setup
- 数据集介绍
- 基线方法
- 评估指标
- 实现细节

### 4.2 Main Results
- 主要结果表格
- 结果分析

### 4.3 Ablation Studies
- 消融实验设计
- 组件贡献分析

### 4.4 Analysis (可选)
- 深入分析
- 案例研究
- 可视化

## 结果描述规范

### 表格呈现
- 使用 booktabs 样式
- 最佳结果加粗
- 清晰的表头和标签

### 文字描述
# 好的描述示例
Our method achieves 95.2% accuracy on Dataset A, outperforming
the strongest baseline by 3.5 percentage points. This improvement
is statistically significant (p < 0.01).

# 避免的描述
Our method is better than baselines. The results are good.

### 图表规范
- 清晰的标签和图例
- 可读的字体大小
- 一致的配色方案
- 矢量图格式 (PDF/SVG)
```

### 3.7 Conclusion (结论)

```latex
% Conclusion 写作模板

\section{Conclusion}

% 总结贡献 (2-3 句)
In this paper, we presented [method name], a novel approach for
[task]. Our key innovation lies in [key contribution], which
addresses [problem] through [technical solution].

% 实验总结 (1-2 句)
Extensive experiments on [datasets] demonstrate the effectiveness
of our approach, achieving [highlight result].

% 局限性与未来工作 (1-2 句)
While our method shows promising results, [limitation] remains
a challenge. Future work could explore [direction 1] and [direction 2].

% 更广泛的影响 (可选)
\section*{Broader Impact}
[Discuss potential societal impacts, both positive and negative]
```

---

## STEP 4: 图表制作规范

### 4.1 表格规范

```latex
% 表格最佳实践

% 使用 booktabs 样式
\usepackage{booktabs}

\begin{table}[t]
\centering
\caption{Comparison with state-of-the-art methods on Dataset X.
Best results are in \textbf{bold}.}
\label{tab:main_results}
\begin{tabular}{lccc}
\toprule
Method & Accuracy & F1 Score & Runtime \\
\midrule
Baseline 1 & 85.2 & 0.841 & 0.5s \\
Baseline 2 & 87.1 & 0.862 & 0.8s \\
Baseline 3 & 88.5 & 0.879 & 1.2s \\
\midrule
Ours & \textbf{92.3} & \textbf{0.915} & 0.6s \\
\bottomrule
\end{tabular}
\end{table}

% 注意事项
% - 表注在表格上方
% - 表格不要竖线
% - 数值对齐
% - 单位明确
```

### 4.2 图表规范

```python
# Python 绘图配置 (适用于学术论文)

import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # 非交互式后端

# 学术论文风格配置
plt.rcParams.update({
    'font.size': 10,
    'font.family': 'serif',
    'font.serif': ['Times New Roman', 'DejaVu Serif'],
    'axes.labelsize': 11,
    'axes.titlesize': 12,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'legend.fontsize': 9,
    'figure.figsize': (3.5, 2.5),  # 单栏宽度
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'savefig.format': 'pdf',
    'axes.linewidth': 0.5,
    'lines.linewidth': 1.0,
    'lines.markersize': 4,
})

def create_paper_figure(data, output_path):
    """创建学术论文图表"""
    fig, ax = plt.subplots()

    # 绘制数据
    ax.plot(data['x'], data['y1'], label='Method A', marker='o')
    ax.plot(data['x'], data['y2'], label='Method B', marker='s')
    ax.plot(data['x'], data['y3'], label='Ours', marker='^', linewidth=2)

    # 设置标签
    ax.set_xlabel('X-axis Label')
    ax.set_ylabel('Y-axis Label')

    # 图例
    ax.legend(loc='upper left', framealpha=0.9)

    # 网格 (可选)
    ax.grid(True, alpha=0.3)

    # 保存
    plt.savefig(output_path)
    plt.close()

# 配色方案 (色盲友好)
colors = {
    'blue': '#0072B2',
    'orange': '#E69F00',
    'green': '#009E73',
    'red': '#CC79A7',
    'purple': '#9C27B0',
}
```

### 4.3 架构图规范

```markdown
# 方法架构图指南

## 工具选择
- 推荐工具: draw.io, PowerPoint, TikZ, Visio
- 格式: PDF (矢量), PNG (300+ DPI)

## 设计原则
1. 清晰的模块划分
2. 一致的图形风格
3. 箭头表示数据流向
4. 标注关键组件名称
5. 配色简洁 (3-4 种颜色)

## TikZ 示例框架
\begin{figure*}[t]
\centering
\begin{tikzpicture}[
    node distance=1.5cm,
    block/.style={rectangle, draw, fill=blue!20, minimum width=2cm, minimum height=1cm},
    arrow/.style={->, >=stealth, thick}
]
    \node[block] (input) {Input};
    \node[block, right=of input] (encoder) {Encoder};
    \node[block, right=of encoder] (attention) {Attention};
    \node[block, right=of attention] (output) {Output};

    \draw[arrow] (input) -- (encoder);
    \draw[arrow] (encoder) -- (attention);
    \draw[arrow] (attention) -- (output);
\end{tikzpicture}
\caption{Overall architecture of our proposed method.}
\label{fig:architecture}
\end{figure*}
```

---

## STEP 5: 引用规范

### 5.1 BibTeX 管理

```bibtex
# BibTeX 条目格式示例

@inproceedings{vaswani2017attention,
    title     = {Attention is All You Need},
    author    = {Vaswani, Ashish and Shazeer, Noam and Parmar, Niki and others},
    booktitle = {Advances in Neural Information Processing Systems},
    pages     = {5998--6008},
    year      = {2017}
}

@article{devlin2019bert,
    title     = {BERT: Pre-training of Deep Bidirectional Transformers},
    author    = {Devlin, Jacob and Chang, Ming-Wei and Lee, Kenton and Toutanova, Kristina},
    journal   = {arXiv preprint arXiv:1810.04805},
    year      = {2019}
}

@misc{github2024repo,
    author    = {{GitHub User}},
    title     = {Repository Name},
    year      = {2024},
    howpublished = {\url{https://github.com/user/repo}},
    note      = {Accessed: 2024-01-15}
}
```

### 5.2 引用风格

```latex
% 引用方式规范

% 单引用
Recent work \cite{vaswani2017attention} has shown that...

% 多引用
Several approaches \cite{devlin2019bert, liu2019roberta, lan2020albert}
have been proposed...

% 引用作为名词
\citet{vaswani2017attention} introduced the Transformer architecture...

% 引用作为支持
This is consistent with previous findings \citep{devlin2019bert}.

% 页码引用
See \citet[p.~5]{vaswani2017attention} for details.
```

### 5.3 引用检查清单

```markdown
# 引用完整性检查

## 基本检查
- [ ] 所有 \cite{} 都有对应 BibTeX 条目
- [ ] 所有 BibTeX 条目都被引用
- [ ] 作者姓名拼写正确
- [ ] 年份正确
- [ ] 会议/期刊名称正确

## 质量检查
- [ ] 引用了领域内关键工作
- [ ] 引用了最新的相关工作 (近 2-3 年)
- [ ] 引用了被比较的基线方法
- [ ] 自引用比例合理 (<20%)

## 格式检查
- [ ] BibTeX 格式统一
- [ ] 使用正确的 citation key
- [ ] 特殊字符正确转义
```

---

## STEP 6: 写作技巧

### 6.1 常用学术表达

```markdown
# 学术写作常用表达

## 引入话题
- In recent years, [topic] has attracted significant attention.
- [Topic] plays a crucial role in [domain].
- The goal of [task] is to [objective].

## 文献综述
- Previous work has shown that...
- Recent studies have demonstrated...
- [Author et al.] proposed [method], which...

## 方法定义
- We propose/introduce/present [method].
- Our approach consists of two main components.
- The key idea is to...

## 实验描述
- We evaluate our method on [datasets].
- Following previous work, we use [metric].
- We compare our method with [baselines].

## 结果讨论
- Our method achieves/outperforms/demonstrates...
- The results show that...
- This improvement can be attributed to...

## 结论陈述
- In this paper, we presented...
- Our experiments demonstrate...
- Future work includes...
```

### 6.2 常见错误避免

```markdown
# 学术写作常见错误

## 语法错误
- 主谓不一致: The model *are* effective -> The model *is* effective
- 时态不一致: We *propose* a method which *improved* -> We propose a method which *improves*
- 冠词错误: *The* attention mechanism -> *The* attention mechanism (首次提到时)

## 表达问题
- 过于口语化: Our method is really good -> Our method demonstrates significant improvement
- 模糊表达: The results are nice -> The results show 15% improvement
- 夸大表述: Our method solves the problem -> Our method addresses key challenges

## 格式问题
- 数字格式: five models -> 5 models (10以上用数字)
- 缩写格式: 未定义就使用缩写
- 引用格式: 引用位置不当

## 逻辑问题
- 因果混淆
- 论据不足
- 结论过度
```

### 6.3 润色检查清单

```markdown
# 论文润色检查清单

## 语言检查
- [ ] 拼写检查完成
- [ ] 语法检查完成
- [ ] 标点符号正确
- [ ] 用词准确一致

## 结构检查
- [ ] 段落之间逻辑连贯
- [ ] 各部分比例合理
- [ ] 没有冗余内容
- [ ] 重点突出

## 内容检查
- [ ] 贡献点清晰明确
- [ ] 技术细节充分
- [ ] 实验完整可信
- [ ] 引用恰当

## 格式检查
- [ ] 符合会议要求
- [ ] 页数符合限制
- [ ] 图表清晰规范
- [ ] 参考文献完整
```

---

## STEP 7: LaTeX 编译与检查

### 7.1 编译配置

```bash
# 推荐的 LaTeX 编译流程

# 标准编译 (PDFLaTeX)
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex

# 使用 XeLaTeX (支持 Unicode)
xelatex main.tex
bibtex main
xelatex main.tex
xelatex main.tex

# 使用 latexmk 自动化
latexmk -pdf main.tex
latexmk -xelatex main.tex

# 清理辅助文件
latexmk -c
```

### 7.2 常见编译问题

```markdown
# LaTeX 编译问题排查

## 编译错误
1. 未定义的引用
   - 运行 bibtex
   - 检查 \cite{} 拼写

2. 图片未找到
   - 检查文件路径
   - 确认图片格式 (PDF/PNG)

3. 内存不足
   - 分割大文档
   - 调整 texmf.cnf

## 编译警告
1. Overfull/Underfull hbox
   - 调整文本宽度
   - 重写过长单词

2. 浮动体位置警告
   - 使用 [htbp] 选项
   - 调整浮动体数量限制

## 格式问题
1. 参考文献格式不统一
   - 使用 \bibliographystyle{}
   - 检查 BibTeX 条目格式

2. 公式编号不连续
   - 检查 \label 和 \ref
```

### 7.3 最终检查

```bash
# 提交前检查脚本

#!/bin/bash
# pre_submission_check.sh

echo "Running pre-submission checks..."

# 1. 编译检查
echo "1. Compiling LaTeX..."
latexmk -pdf main.tex
if [ $? -ne 0 ]; then
    echo "ERROR: Compilation failed"
    exit 1
fi

# 2. 页数检查
echo "2. Checking page count..."
pages=$(pdfinfo main.pdf | grep "Pages:" | awk '{print $2}')
echo "Total pages: $pages"
if [ $pages -gt 9 ]; then
    echo "WARNING: Exceeds typical page limit"
fi

# 3. 文件大小检查
echo "3. Checking file size..."
size=$(stat -f%z main.pdf)
echo "File size: $size bytes"
if [ $size -gt 10000000 ]; then
    echo "WARNING: File size exceeds 10MB"
fi

# 4. 引用检查
echo "4. Checking references..."
grep -c "undefined" main.log
if [ $? -eq 0 ]; then
    echo "WARNING: Undefined references found"
fi

echo "Pre-submission checks complete!"
```

---

## STEP 8: Checkpoint D - 提交前检查

### 8.1 提交检查清单

```markdown
# Checkpoint D: 论文提交前检查

## 内容完整性
- [ ] 标题准确反映内容
- [ ] 摘要完整涵盖贡献
- [ ] 引言清晰阐述动机
- [ ] 相关工作覆盖完整
- [ ] 方法描述详细可复现
- [ ] 实验结果完整可信
- [ ] 结论总结恰当

## 格式规范性
- [ ] 符合会议模板要求
- [ ] 页数在限制范围内
- [ ] 字体大小符合要求
- [ ] 边距符合要求
- [ ] 页眉页脚正确

## 图表质量
- [ ] 所有图表清晰可读
- [ ] 图表标题完整
- [ ] 图例说明清楚
- [ ] 分辨率足够 (300+ DPI)

## 引用完整性
- [ ] 所有引用有对应条目
- [ ] 引用格式统一
- [ ] 无遗漏重要文献

## 附加材料
- [ ] 补充材料准备完毕
- [ ] 代码/数据链接有效
- [ ] 伦理声明 (如需要)
```

### 8.2 状态更新

```bash
# 创建提交检查点
python prometheus.py checkpoint "Phase 6 论文撰写完成"

# 更新状态
# state.json:
# {
#   "phase": 6,
#   "status": "writing_complete",
#   "paper_path": "paper/main.pdf",
#   "target_conference": "NeurIPS 2024",
#   "submission_date": "2024-05-22"
# }
```

---

## 质量检查清单

在 Phase 6 完成后，确保：

### 内容质量
- [ ] 贡献点清晰且有价值
- [ ] 方法描述完整可复现
- [ ] 实验结果支持论点
- [ ] 相关工作引用恰当

### 写作质量
- [ ] 语言流畅准确
- [ ] 逻辑清晰连贯
- [ ] 无语法和拼写错误
- [ ] 术语使用一致

### 格式质量
- [ ] 符合投稿要求
- [ ] 图表专业规范
- [ ] 引用格式正确
- [ ] 编译无错误无警告

### 提交准备
- [ ] 补充材料准备完毕
- [ ] 作者信息正确
- [ ] 盲审要求满足 (如需要)
- [ ] 所有文件打包完成

---

## 常见问题

**Q: 论文写不完怎么办？**
A: 优先保证核心内容的质量，可以精简相关工作等次要部分，确保主要贡献清晰呈现。

**Q: 实验结果不够强怎么办？**
A: 强调方法的创新性和理论贡献，提供深入的分析和洞察，在消融实验中展示组件有效性。

**Q: 如何处理负面结果？**
A: 诚实报告，分析原因，提供可能的解释和改进方向，这在某些情况下反而是有价值的贡献。

**Q: 参考文献太多/太少怎么办？**
A: 相关工作部分通常引用 15-30 篇文献比较合适。确保覆盖领域关键工作和最新进展。

**Q: 如何避免被拒稿？**
A: 确保贡献明确、实验充分、写作清晰、格式规范。请同事帮忙审阅，根据反馈修改。

---

*完成此阶段后，系统将进入 Phase 7: 同行评审*

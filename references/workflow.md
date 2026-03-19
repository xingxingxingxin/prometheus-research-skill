# Prometheus 工作流详细说明

本文档详细描述了 10 阶段 100 任务的研究工作流。

---

## Phase 0: Topic Analysis (4 tasks)

### T001: 分析研究主题
**目标**: 提取核心研究方向、关键概念和研究问题

**执行步骤**:
1. 分析用户提供的主题
2. 提取核心概念和关键词
3. 识别主要研究问题
4. 输出到 `notes/topic_analysis.md`

**输出格式**:
```markdown
# 主题分析

## 核心概念
- 概念1: 定义
- 概念2: 定义

## 关键词
[关键词列表，用于文献搜索]

## 研究问题
1. 主要问题1
2. 主要问题2

## 预期贡献
- 贡献1
- 贡献2
```

### T002: 识别研究领域
**目标**: 识别主题涉及的研究领域和交叉学科

**输出**: `notes/research_fields.md`

### T003: 明确研究目标
**目标**: 明确研究目标和预期贡献

**输出**: `notes/research_goals.md`

### T004: 制定研究计划
**目标**: 制定研究计划和技术路线

**输出**: `notes/research_plan.md`

---

## Phase 1: Literature Review (34 tasks)

### 搜索阶段 (T005-T010)

#### T005: Semantic Scholar 核心搜索
**目标**: 使用核心关键词搜索 20 篇论文

**执行步骤**:
1. 使用 WebSearch 搜索 `{核心关键词} site:semanticscholar.org`
2. 记录论文标题、作者、年份、引用数
3. 输出到 `data/search_results/semantic_scholar_core.json`

#### T006: arXiv 最新预印本搜索
**目标**: 搜索 arXiv 最新 15 篇预印本

**执行步骤**:
1. 搜索 `{关键词} site:arxiv.org`
2. 优先选择最近 2 年的论文
3. 输出到 `data/search_results/arxiv_recent.json`

#### T007-T010: 其他搜索
- T007: 综述论文搜索 (10篇)
- T008: 高引用经典论文搜索 (10篇)
- T009: 交叉领域论文搜索 (10篇)
- T010: 最新会议论文搜索 (15篇)

### 筛选阶段 (T011-T014)

#### T011: 合并去重排序
**目标**: 合并所有搜索结果，去重并按相关性排序

**输出**: `data/search_results/merged_results.json`

#### T012: 筛选30篇核心文献
**目标**: 根据标题和摘要筛选最相关的 30 篇

**筛选标准**:
- 与研究主题直接相关
- 发表在高质量会议/期刊
- 近年发表（优先）

**输出**: `data/search_results/core_papers.json`

#### T013: 创建文献数据库
**目标**: 创建文献信息数据库

**输出**: `data/literature_db.json`

#### T014: 按主题分类
**目标**: 将文献按研究主题分类

**输出**: `data/paper_categories.json`

### 下载阶段 (T015-T017)

#### T015-T017: 下载和整理 PDF
**目标**: 下载核心论文 PDF

**注意**: 如果无法下载，保存摘要和链接

**输出**: `data/papers/*.pdf` 或 `data/papers/unavailable.json`

### 研读阶段 (T018-T030)

#### T018-T027: 研读第1-10篇核心论文
每篇论文的研读输出：

```markdown
# 论文研读: [论文标题]

## 基本信息
- 标题:
- 作者:
- 会议/期刊:
- 年份:
- 引用数:

## 核心贡献
[1-2句话总结]

## 方法论
[详细描述]

## 实验结果
[关键结果]

## 局限性
[存在的问题]

## 对本研究的启发
[如何应用到本研究]

## 关键引用
[值得进一步阅读的论文]
```

**输出**: `notes/paper_XXX_summary.md`

#### T028-T030: 浏览其余论文
**目标**: 快速浏览剩余论文，提取关键信息

### 综合分析阶段 (T031-T038)

#### T031: 分析发展脉络
**目标**: 梳理研究领域的演进历史

**输出**: `notes/research_timeline.md`

#### T032: 识别研究空白
**目标**: 找出当前研究的不足和机会

**输出**: `notes/research_gaps.md`

#### T033: 识别创新机会
**目标**: 基于研究空白提出创新点

**输出**: `notes/innovation_opportunities.md`

#### T034: 确定差异化定位
**目标**: 明确本研究的独特贡献

**输出**: `notes/differentiation.md`

#### T035: 生成BibTeX文件
**目标**: 整理所有参考文献的 BibTeX

**输出**: `references.bib`

#### T036: 撰写文献综述初稿
**目标**: 撰写完整的文献综述

**输出**: `paper/related_work.md`

#### T037-T038: 检查和完善引用
**目标**: 确保引用完整和格式正确

---

## Phase 2: Hypothesis Design (6 tasks)

### T039: 提出研究假设
**输出**: `notes/hypotheses.md`

```markdown
# 研究假设

## 主要假设
H1: [假设陈述]
- 理论依据:
- 验证方法:

## 次要假设
H2: ...
```

### T040: 设计实验方案
**输出**: `notes/experiment_design.md`

### T041: 确定评估指标
**输出**: `notes/evaluation_metrics.md`

### T042: 验证创新性
**输出**: `notes/innovation_validation.md`

### T043: 估算资源需求
**输出**: `notes/resource_requirements.md`

### T044: 撰写实验设计文档
**输出**: `notes/experiment_protocol.md`

---

## Phase 3: Coding (7 tasks)

### T045: 搭建项目代码结构
**输出**: `code/` 目录结构

```
code/
├── src/
│   ├── __init__.py
│   ├── data/
│   ├── models/
│   └── utils/
├── scripts/
│   ├── train.py
│   └── evaluate.py
├── tests/
├── requirements.txt
└── README.md
```

### T046: 实现数据处理模块
**输出**: `code/src/data/`

### T047: 实现核心算法/模型
**输出**: `code/src/models/`

### T048: 实现基线方法
**输出**: `code/src/baselines/`

### T049: 编写训练评估脚本
**输出**: `code/scripts/`

### T050: 编写单元测试
**输出**: `code/tests/`

### T051: 测试代码可运行性
**目标**: 确保所有代码可以正常运行

---

## Phase 4: Execution (6 tasks)

### T052: 准备实验数据
**目标**: 下载/生成实验所需数据

### T053: 小规模测试验证
**目标**: 在小数据集上验证代码正确性

### T054: 运行基线实验
**输出**: `results/baseline/`

### T055: 运行主要实验
**输出**: `results/main/`

### T056: 运行消融实验
**输出**: `results/ablation/`

### T057: 收集整理结果
**输出**: `results/summary.json`

---

## Phase 5: Analysis (5 tasks)

### T058: 统计显著性检验
**输出**: `results/statistical_tests.md`

### T059: 生成性能对比图表
**输出**: `results/figures/`

### T060: 分析结果得出结论
**输出**: `results/analysis.md`

### T061: 识别异常结果
**输出**: `results/anomalies.md`

### T062: 创新性量化验证
**输出**: `results/innovation_metrics.md`

---

## Phase 6: Writing (9 tasks)

### T063-T070: 撰写论文各章节

每章节的输出：
- T063: `paper/abstract.md`
- T064: `paper/introduction.md`
- T065: `paper/related_work.md`
- T066: `paper/methods.md`
- T067: `paper/experiments.md`
- T068: `paper/conclusion.md`
- T069: `paper/contributions.md`
- T070: 整合为 `paper/draft.md`

### T071: 原创性检查
**目标**: 检查论文的原创性和贡献声明

---

## Phase 7: Humanization (9 tasks)

### T072: 分析AI痕迹特征
**目标**: 识别论文中可能的AI写作痕迹

**常见AI痕迹**:
- 过度使用"Furthermore", "Moreover", "Additionally"
- 句式过于工整
- 缺乏具体例子
- 过于全面的综述

### T073-T078: 各章节去AI化
逐章节修改，使语言更自然

### T079: 全文语言润色
**目标**: 统一语言风格

### T080: AI检测评分
**目标**: 使用检测工具验证 AI 痕迹 < 30%

---

## Phase 8: LaTeX (12 tasks)

### T081: 选择目标会议模板
**目标**: 确定目标会议（如 ICML, NeurIPS, ACL 等）

### T082: 创建LaTeX项目结构
```
latex/
├── main.tex
├── preamble.tex
├── sections/
│   ├── abstract.tex
│   ├── introduction.tex
│   ├── related_work.tex
│   ├── methods.tex
│   ├── experiments.tex
│   └── conclusion.tex
├── figures/
├── tables/
└── references.bib
```

### T083-T088: 转换各章节
将 Markdown 转换为 LaTeX

### T089: 生成中文版本
**目标**: 生成中文版论文（如果需要）

### T090-T092: 编译和检查
- T090: 编译英文 PDF
- T091: 编译中文 PDF
- T092: 检查 PDF 输出质量

---

## Phase 9: Review (8 tasks)

### T093: 论文完整性检查
**检查项**:
- [ ] 摘要完整
- [ ] 引言清晰
- [ ] 相关工作覆盖全面
- [ ] 方法描述详细
- [ ] 实验充分
- [ ] 结论有力
- [ ] 引用正确

### T094: 参考文献格式检查
**检查项**:
- [ ] BibTeX 格式正确
- [ ] 引用完整
- [ ] 无重复引用

### T095: 创新性自我评估
**输出**: `notes/innovation_self_assessment.md`

### T096: 模拟三位审稿人评审
**目标**: 模拟不同角度的审稿意见

**审稿人角色**:
- 审稿人A: 方法论专家
- 审稿人B: 应用领域专家
- 审稿人C: 新颖性评估

**输出**: `notes/simulated_reviews.md`

### T097: 根据评审修改论文
**目标**: 根据模拟评审意见修改

### T098: 撰写审稿回复信
**输出**: `latex/response_letter.tex`

### T099: 最终格式检查
**检查项**:
- [ ] 符合会议格式要求
- [ ] 页数符合限制
- [ ] 图表清晰
- [ ] 无拼写错误

### T100: 生成提交包
**输出**: `output/`
- `paper_en.pdf`
- `paper_zh.pdf` (可选)
- `supplementary.zip` (代码和数据)
- `response_letter.pdf`

---

## 检查点说明

| 检查点 | 阶段后 | 说明 |
|--------|--------|------|
| A | Phase 1 | 文献综述完成，研究方向确认 |
| B | Phase 2 | 实验设计完成，方案可行 |
| C | Phase 4 | 实验完成，结果有效 |
| D | Phase 5 | 分析完成，结论明确 |
| E | Phase 6 | 论文初稿完成 |
| F | Phase 7 | 去AI化完成 |
| G | Phase 8 | LaTeX 完成 |

每个检查点需要用户确认才能继续。

---

*此文档是 Prometheus 工作流的详细说明。*

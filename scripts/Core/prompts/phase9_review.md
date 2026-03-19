# Phase 7: 同行评审 Prompt

## YOUR ROLE

你是 Project Prometheus 的同行评审专家。你的任务是对已撰写的论文进行系统化、全面的评审，模拟真实的同行评审过程。你需要从多个维度评估论文质量，识别优点和不足，提供具体的改进建议，并根据评审结果做出是否接受、修改或拒绝的决策。你的目标是帮助提升论文质量，确保其达到发表标准。

---

## 工作目标

1. **全面评审**: 从多个维度评估论文质量
2. **优点识别**: 明确论文的创新点和贡献
3. **问题发现**: 识别论文的不足和潜在问题
4. **改进建议**: 提供具体、可操作的修改建议
5. **决策制定**: 基于评审结果做出合理的出版决策
6. **反馈撰写**: 生成结构化、专业的评审报告

---

## STEP 1: 评审准备

### 1.1 评审标准设定

```markdown
# 评审标准框架

## 核心评审维度

### 1. 原创性 (Originality) - 权重 25%
- 研究问题的创新性
- 方法的新颖性
- 与现有工作的区别
- 对领域的贡献程度

### 2. 技术质量 (Technical Quality) - 权重 30%
- 方法设计的合理性
- 实验设计的严谨性
- 结果的可靠性
- 分析的深度

### 3. 清晰度 (Clarity) - 权重 20%
- 写作的清晰程度
- 结构的逻辑性
- 图表的可读性
- 术语的一致性

### 4. 重要性 (Significance) - 权重 15%
- 对领域的影响
- 实用价值
- 可复现性
- 推广价值

### 5. 完整性 (Completeness) - 权重 10%
- 相关工作的覆盖
- 实验的全面性
- 讨论的充分性
- 引用的完整性
```

### 1.2 评审角色定义

```markdown
# 评审角色配置

## 模拟评审委员会

### 审稿人 A (领域专家)
- 角色: 资深研究员
- 专长: 方法论和技术细节
- 关注点: 技术正确性、创新性
- 评分倾向: 严格

### 审稿人 B (实验专家)
- 角色: 实验系统负责人
- 专长: 实验设计和评估
- 关注点: 实验设计、结果分析
- 评分倾向: 中等

### 审稿人 C (应用专家)
- 角色: 工业界研究员
- 专长: 实际应用和可用性
- 关注点: 实用性、可扩展性
- 评分倾向: 宽松

### Area Chair (领域主席)
- 角色: 综合决策者
- 职责: 综合审稿意见，做出最终决策
- 关注点: 整体质量、社区价值
```

### 1.3 评审时间规划

```markdown
# 评审流程时间表

## 标准评审周期 (2-3 天)

### Day 1: 初步评审
- [ ] 阅读标题和摘要
- [ ] 浏览全文结构
- [ ] 识别主要贡献
- [ ] 记录第一印象

### Day 2: 深度评审
- [ ] 详细阅读方法部分
- [ ] 检查实验设计
- [ ] 验证结果分析
- [ ] 评估相关工作

### Day 3: 报告撰写
- [ ] 总结优点和不足
- [ ] 撰写改进建议
- [ ] 确定评分
- [ ] 完成评审报告
```

---

## STEP 2: 分维度评审

### 2.1 原创性评审

```python
# 原创性评估检查清单

def evaluate_originality(paper):
    """评估论文的原创性。

    Args:
        paper: 论文内容对象

    Returns:
        原创性评分和评估结果
    """
    evaluation = {
        'dimensions': {},
        'score': 0,
        'comments': []
    }

    # 1. 问题创新性
    problem_novelty = evaluate_problem_novelty(paper.problem_statement)
    evaluation['dimensions']['problem_novelty'] = {
        'score': problem_novelty,
        'questions': [
            "研究问题是否新颖？",
            "是否解决了重要且未被充分研究的问题？",
            "问题定义是否清晰且有别于现有工作？"
        ]
    }

    # 2. 方法创新性
    method_novelty = evaluate_method_novelty(paper.methodology)
    evaluation['dimensions']['method_novelty'] = {
        'score': method_novelty,
        'questions': [
            "方法是否包含创新的技术组件？",
            "与现有方法的核心区别是什么？",
            "创新点是否明确阐述？"
        ]
    }

    # 3. 贡献明确性
    contribution_clarity = evaluate_contributions(paper.contributions)
    evaluation['dimensions']['contribution_clarity'] = {
        'score': contribution_clarity,
        'questions': [
            "主要贡献是否清晰列出？",
            "贡献是否具体而非泛泛而谈？",
            "贡献的价值是否得到验证？"
        ]
    }

    # 4. 与现有工作的区分
    differentiation = evaluate_differentiation(paper.related_work)
    evaluation['dimensions']['differentiation'] = {
        'score': differentiation,
        'questions': [
            "是否清楚说明与现有工作的区别？",
            "相关工作引用是否全面？",
            "是否避免了重复已有工作？"
        ]
    }

    # 计算总分
    weights = {
        'problem_novelty': 0.25,
        'method_novelty': 0.35,
        'contribution_clarity': 0.20,
        'differentiation': 0.20
    }

    total_score = sum(
        evaluation['dimensions'][dim]['score'] * weights[dim]
        for dim in evaluation['dimensions']
    )
    evaluation['score'] = total_score

    return evaluation
```

### 2.2 技术质量评审

```python
# 技术质量评估检查清单

def evaluate_technical_quality(paper):
    """评估论文的技术质量。

    Args:
        paper: 论文内容对象

    Returns:
        技术质量评分和评估结果
    """
    evaluation = {
        'dimensions': {},
        'score': 0,
        'issues': [],
        'strengths': []
    }

    # 1. 方法正确性
    method_correctness = evaluate_method_correctness(paper.method_section)
    evaluation['dimensions']['method_correctness'] = {
        'score': method_correctness['score'],
        'checks': [
            ("数学公式是否正确？", method_correctness['math_correct']),
            ("算法描述是否完整？", method_correctness['algo_complete']),
            ("符号使用是否一致？", method_correctness['notation_consistent']),
            ("假设是否合理？", method_correctness['assumptions_valid'])
        ]
    }
    if method_correctness['issues']:
        evaluation['issues'].extend(method_correctness['issues'])

    # 2. 实验设计
    exp_design = evaluate_experiment_design(paper.experiments)
    evaluation['dimensions']['experiment_design'] = {
        'score': exp_design['score'],
        'checks': [
            ("基线方法是否全面？", exp_design['baselines_adequate']),
            ("数据集是否合适？", exp_design['datasets_appropriate']),
            ("评估指标是否合理？", exp_design['metrics_appropriate']),
            ("实验设置是否公平？", exp_design['fair_comparison'])
        ]
    }

    # 3. 结果可靠性
    result_reliability = evaluate_result_reliability(paper.results)
    evaluation['dimensions']['result_reliability'] = {
        'score': result_reliability['score'],
        'checks': [
            ("是否进行了多次运行？", result_reliability['multiple_runs']),
            ("是否报告了方差/置信区间？", result_reliability['variance_reported']),
            ("统计显著性是否检验？", result_reliability['significance_tested']),
            ("结果是否可复现？", result_reliability['reproducible'])
        ]
    }

    # 4. 分析深度
    analysis_depth = evaluate_analysis_depth(paper.analysis)
    evaluation['dimensions']['analysis_depth'] = {
        'score': analysis_depth['score'],
        'checks': [
            ("是否进行了消融实验？", analysis_depth['ablation_study']),
            ("是否分析了失败案例？", analysis_depth['error_analysis']),
            ("是否提供了深入洞察？", analysis_depth['insights_provided']),
            ("讨论是否充分？", analysis_depth['discussion_adequate'])
        ]
    }

    return evaluation


# 技术质量常见问题列表
TECHNICAL_ISSUES = {
    'critical': [
        "方法描述不完整，无法复现",
        "实验设置存在严重缺陷",
        "结果数据疑似造假",
        "与基线比较不公平"
    ],
    'major': [
        "缺少重要的基线比较",
        "统计检验缺失或不正确",
        "消融实验不充分",
        "超参数调优不透明"
    ],
    'minor': [
        "符号定义不清晰",
        "实验细节缺失",
        "图表标注不完整",
        "代码未公开"
    ]
}
```

### 2.3 清晰度评审

```markdown
# 清晰度评估标准

## 写作质量检查

### 结构组织
- [ ] 论文结构符合学术规范
- [ ] 各部分逻辑连贯
- [ ] 段落之间过渡自然
- [ ] 重点内容突出

### 语言表达
- [ ] 语法正确，无拼写错误
- [ ] 用词准确，术语一致
- [ ] 句子简洁明了
- [ ] 避免冗余表述

### 图表质量
- [ ] 图表清晰可读
- [ ] 标题和标签完整
- [ ] 图例说明清楚
- [ ] 分辨率足够高

### 引用规范
- [ ] 引用格式正确
- [ ] 关键文献已引用
- [ ] 自引用比例合理
- [ ] 引用位置恰当

## 常见清晰度问题

### 结构问题
1. **贡献不明确**: 引言中贡献点模糊或缺失
2. **相关工作孤立**: 与方法部分缺乏联系
3. **方法过于简略**: 关键细节缺失
4. **实验冗长**: 结果描述缺乏重点

### 表达问题
1. **术语不一致**: 同一概念使用不同术语
2. **缩写未定义**: 首次出现时未解释
3. **句子过长**: 单句超过 30 词
4. **中英混杂**: 非必要的中英文混合

### 图表问题
1. **分辨率不足**: 图像模糊或锯齿
2. **字体过小**: 标签无法辨认
3. **配色不当**: 色盲不友好
4. **信息过载**: 单图包含过多内容
```

### 2.4 重要性评审

```python
# 重要性评估框架

def evaluate_significance(paper):
    """评估论文的重要性。

    Args:
        paper: 论文内容对象

    Returns:
        重要性评分和评估
    """
    evaluation = {
        'dimensions': {},
        'score': 0,
        'impact_analysis': {}
    }

    # 1. 学术影响
    academic_impact = {
        'advances_sota': check_sota_advancement(paper),
        'enables_new_research': check_new_research_enablement(paper),
        'community_interest': estimate_community_interest(paper.topic),
        'citation_potential': estimate_citation_potential(paper)
    }
    evaluation['dimensions']['academic_impact'] = academic_impact

    # 2. 实用价值
    practical_value = {
        'solves_real_problem': check_real_world_applicability(paper),
        'implementation_feasible': check_implementation_feasibility(paper),
        'scalability': check_scalability(paper.method),
        'resource_efficiency': check_resource_efficiency(paper)
    }
    evaluation['dimensions']['practical_value'] = practical_value

    # 3. 可复现性
    reproducibility = {
        'code_available': paper.code_available,
        'data_available': paper.data_available,
        'hyperparameters_documented': paper.hyperparameters_documented,
        'setup_clear': paper.experimental_setup_clear
    }
    evaluation['dimensions']['reproducibility'] = reproducibility

    # 4. 推广价值
    generalizability = {
        'cross_domain': check_cross_domain_applicability(paper),
        'theoretical_insights': check_theoretical_contribution(paper),
        'method_transferable': check_method_transferability(paper)
    }
    evaluation['dimensions']['generalizability'] = generalizability

    return evaluation


# 重要性评估问卷
SIGNIFICANCE_QUESTIONS = {
    'academic': [
        "这篇论文是否推动了领域前沿？",
        "是否会启发后续研究工作？",
        "是否适合在顶级会议发表？",
        "引用潜力如何？"
    ],
    'practical': [
        "解决了什么实际问题？",
        "方法是否可直接应用？",
        "部署难度如何？",
        "性能/成本比是否合理？"
    ],
    'reproducibility': [
        "是否提供了代码？",
        "数据是否公开？",
        "实验细节是否充分？",
        "能否在合理时间内复现？"
    ]
}
```

---

## STEP 3: 评审执行流程

### 3.1 初步评审 (First Pass)

```markdown
# 初步评审检查清单

## 快速评估 (30 分钟)

### 标题和摘要
- [ ] 标题是否准确反映内容？
- [ ] 摘要是否清晰概括贡献？
- [ ] 关键词是否恰当？
- [ ] 是否符合会议主题？

### 整体结构
- [ ] 页数是否符合要求？
- [ ] 章节是否完整？
- [ ] 图表数量是否合理？
- [ ] 参考文献是否充足？

### 初步判断
- [ ] 论文主题是否相关？
- [ ] 是否有明显的致命缺陷？
- [ ] 初步印象评分 (1-5)
- [ ] 是否值得深入评审？

## 第一印象记录模板

```yaml
first_impression:
  paper_id: [论文ID]
  reviewer: [评审人]
  date: [评审日期]

  quick_assessment:
    relevance: [1-5]  # 与会议主题相关性
    novelty: [1-5]     # 初步判断的新颖性
    quality: [1-5]     # 初步判断的质量

  decision:
    proceed_to_detailed_review: [yes/no]
    reason: [简短说明]

  notes:
    - [初步观察到的优点]
    - [初步观察到的问题]
```
```

### 3.2 详细评审 (Second Pass)

```markdown
# 详细评审执行清单

## 引言部分评审

### 背景介绍
- [ ] 研究背景介绍是否充分？
- [ ] 问题的重要性是否阐明？
- [ ] 动机是否清晰？

### 现有方法局限
- [ ] 是否指出现有方法的不足？
- [ ] 问题定义是否明确？
- [ ] 研究空白是否识别？

### 贡献声明
- [ ] 贡献是否明确列出？
- [ ] 贡献是否具体？
- [ ] 贡献是否可实现？

## 方法部分评审

### 问题定义
- [ ] 形式化定义是否清晰？
- [ ] 符号系统是否一致？
- [ ] 假设是否合理？

### 方法描述
- [ ] 方法是否完整描述？
- [ ] 创新点是否突出？
- [ ] 技术细节是否充分？

### 算法设计
- [ ] 算法是否可复现？
- [ ] 复杂度是否分析？
- [ ] 理论支撑是否充分？

## 实验部分评审

### 实验设置
- [ ] 数据集是否合适？
- [ ] 基线是否全面？
- [ ] 评估指标是否合理？
- [ ] 实现细节是否透明？

### 结果呈现
- [ ] 主要结果是否清晰？
- [ ] 统计显著性是否报告？
- [ ] 图表是否规范？

### 分析讨论
- [ ] 消融实验是否充分？
- [ ] 失败案例是否分析？
- [ ] 结果解释是否合理？

## 相关工作评审

### 文献覆盖
- [ ] 是否引用了关键工作？
- [ ] 是否覆盖最新进展？
- [ ] 分类是否合理？

### 对比分析
- [ ] 是否清楚区分本文工作？
- [ ] 是否避免过度引用自己？
- [ ] 引用是否准确？
```

### 3.3 深度评审 (Third Pass)

```python
# 深度评审验证脚本

def perform_deep_review(paper_path):
    """执行深度评审验证。

    Args:
        paper_path: 论文文件路径

    Returns:
        深度评审结果
    """
    results = {
        'fact_checking': {},
        'consistency_check': {},
        'reproducibility_check': {}
    }

    # 1. 事实核查
    results['fact_checking'] = {
        'citations': verify_citations(paper_path),
        'claims': verify_claims(paper_path),
        'numbers': verify_numbers(paper_path),
        'formulas': verify_formulas(paper_path)
    }

    # 2. 一致性检查
    results['consistency_check'] = {
        'notation': check_notation_consistency(paper_path),
        'terminology': check_terminology_consistency(paper_path),
        'numbers': check_number_consistency(paper_path),
        'references': check_reference_consistency(paper_path)
    }

    # 3. 可复现性检查
    results['reproducibility_check'] = {
        'algorithm': check_algorithm_completeness(paper_path),
        'hyperparameters': check_hyperparameter_documentation(paper_path),
        'data': check_data_availability(paper_path),
        'code': check_code_availability(paper_path)
    }

    return results


def verify_citations(paper_path):
    """验证引用的正确性。"""
    issues = []

    # 检查引用格式
    # 检查引用是否存在
    # 检查引用是否准确

    return {
        'total_citations': count_citations(paper_path),
        'issues': issues,
        'self_citation_ratio': calculate_self_citation_ratio(paper_path)
    }


def check_notation_consistency(paper_path):
    """检查符号使用的一致性。"""
    notation_table = extract_notation_definitions(paper_path)
    usages = extract_notation_usages(paper_path)

    inconsistencies = []
    for symbol, definition in notation_table.items():
        for usage in usages.get(symbol, []):
            if usage['context'] != definition['context']:
                inconsistencies.append({
                    'symbol': symbol,
                    'defined_as': definition,
                    'used_as': usage
                })

    return {
        'symbols_defined': len(notation_table),
        'inconsistencies': inconsistencies
    }
```

---

## STEP 4: 评分标准与规则

### 4.1 评分等级定义

```markdown
# 论文评分标准

## 总体评分 (Overall Score)

### 评分等级

| 分数 | 等级 | 描述 | 决策建议 |
|------|------|------|----------|
| 10 | 杰出 (Outstanding) | 开创性工作，对领域有重大影响 | 强烈接受 |
| 9 | 优秀 (Excellent) | 重要的创新贡献，技术质量高 | 接受 |
| 8 | 很好 (Very Good) | 扎实的工作，有一定贡献 | 倾向接受 |
| 7 | 好 (Good) | 合格的工作，有些许贡献 | 边缘接受 |
| 6 | 一般 (Fair) | 有一定价值，但问题也明显 | 边缘拒绝 |
| 5 | 一般偏下 (Below Average) | 贡献有限，存在明显问题 | 倾向拒绝 |
| 4 | 较差 (Poor) | 贡献很小，问题严重 | 拒绝 |
| 3 | 差 (Very Poor) | 几乎没有贡献 | 强烈拒绝 |
| 2 | 很差 (Extremely Poor) | 存在严重缺陷 | 强烈拒绝 |
| 1 | 无价值 (No Value) | 不应发表 | 强烈拒绝 |

## 分项评分

### 原创性评分 (Originality)
- 5: 高度创新，开创性工作
- 4: 明显的创新贡献
- 3: 一定的创新性
- 2: 创新性有限
- 1: 缺乏创新

### 技术质量评分 (Quality)
- 5: 技术质量优秀，无重大缺陷
- 4: 技术质量良好，小问题可修改
- 3: 技术质量一般，需要改进
- 2: 存在技术问题
- 1: 严重技术缺陷

### 清晰度评分 (Clarity)
- 5: 写作清晰，易于理解
- 4: 整体清晰，小问题
- 3: 基本可读，需要改进
- 2: 表达不清，难以理解
- 1: 严重影响理解

### 重要性评分 (Significance)
- 5: 对领域有重要影响
- 4: 有一定影响
- 3: 贡献有限
- 2: 价值较小
- 1: 无明显价值

### 可复现性评分 (Reproducibility)
- 5: 完全可复现，代码数据公开
- 4: 可复现，细节充分
- 3: 基本可复现
- 2: 复现困难
- 1: 无法复现
```

### 4.2 置信度评估

```markdown
# 评审置信度 (Confidence)

## 置信度等级

| 分数 | 描述 |
|------|------|
| 5 | 专家级，对该领域非常熟悉 |
| 4 | 熟悉，有一定研究经验 |
| 3 | 一般了解，读过相关文献 |
| 2 | 基本了解，需要更多验证 |
| 1 | 不熟悉，评审可能不准确 |

## 置信度影响因素

### 增加置信度的因素
- 评审人是该领域专家
- 熟悉相关方法和基线
- 有类似研究经验
- 能够验证技术细节

### 降低置信度的因素
- 不熟悉的子领域
- 缺乏相关背景知识
- 技术细节无法验证
- 依赖作者的自我声明
```

### 4.3 边界案例处理

```python
# 边界案例决策规则

def make_borderline_decision(scores, reviews):
    """处理边界案例的决策。

    Args:
        scores: 各评审人的评分
        reviews: 各评审人的详细评审

    Returns:
        决策建议
    """
    avg_score = sum(scores) / len(scores)

    # 边界分数范围: 5-7
    if 5 <= avg_score <= 7:
        # 分析争议点
        score_variance = calculate_variance(scores)
        disagreements = identify_disagreements(reviews)

        if score_variance > 2.0:
            # 评分分歧大，需要额外评审
            return {
                'decision': 'additional_review',
                'reason': '评审人意见分歧较大',
                'action': '邀请额外评审人或Area Chair裁决'
            }

        # 检查是否有致命缺陷
        critical_issues = find_critical_issues(reviews)
        if critical_issues:
            return {
                'decision': 'reject',
                'reason': '存在致命缺陷',
                'issues': critical_issues
            }

        # 检查是否可通过修改解决
        fixable_issues = find_fixable_issues(reviews)
        if fixable_issues and avg_score >= 6:
            return {
                'decision': 'minor_revision',
                'reason': '问题可通过小幅修改解决',
                'required_changes': fixable_issues
            }

    return {
        'decision': 'reject',
        'reason': '分数处于边界且无明显优势'
    }


# 边界决策检查清单
BORDERLINE_CHECKLIST = [
    "评审人意见是否一致？",
    "是否存在可修复的致命缺陷？",
    "论文是否有独特优势？",
    "修改后能否达到发表标准？",
    "是否值得给予修改机会？"
]
```

---

## STEP 5: 评审报告撰写

### 5.1 报告结构模板

```markdown
# 同行评审报告模板

## 评审信息
- 论文ID: [Paper ID]
- 标题: [Title]
- 评审人: [Reviewer ID]
- 评审日期: [Date]
- 置信度: [1-5]

---

## 总结 (Summary)

[用 2-3 句话概括论文的主要贡献和方法]

---

## 主要优点 (Strengths)

1. **[优点类型 1]**: [具体描述]
   - [支撑细节]

2. **[优点类型 2]**: [具体描述]
   - [支撑细节]

3. **[优点类型 3]**: [具体描述]
   - [支撑细节]

---

## 主要缺点 (Weaknesses)

1. **[问题类型 1]**: [具体描述]
   - 位置: [章节/页码/行号]
   - 问题说明: [详细说明]
   - 建议修改: [具体建议]

2. **[问题类型 2]**: [具体描述]
   - 位置: [章节/页码/行号]
   - 问题说明: [详细说明]
   - 建议修改: [具体建议]

---

## 具体问题 (Detailed Comments)

### 方法部分
- [具体问题 1]
- [具体问题 2]

### 实验部分
- [具体问题 1]
- [具体问题 2]

### 写作部分
- [具体问题 1]
- [具体问题 2]

---

## 问题列表 (Questions for Authors)

1. [需要作者澄清的问题 1]
2. [需要作者澄清的问题 2]
3. [需要作者澄清的问题 3]

---

## 评分 (Scores)

| 维度 | 评分 | 说明 |
|------|------|------|
| 原创性 | [1-5] | [简短说明] |
| 技术质量 | [1-5] | [简短说明] |
| 清晰度 | [1-5] | [简短说明] |
| 重要性 | [1-5] | [简短说明] |
| **总体评分** | [1-10] | [最终评分] |

---

## 决策建议 (Recommendation)

[Accept / Minor Revision / Major Revision / Reject]

**理由**: [决策理由说明]
```

### 5.2 优点描述模板

```markdown
# 优点描述模板

## 创新性优点

### 方法创新
"[方法名] 引入了 [创新点]，通过 [技术手段] 解决了 [问题]。这是 [领域] 中一个有趣的尝试，因为 [原因]。"

### 问题新颖
"论文关注 [问题]，这是一个 [重要性] 但 [现状] 的问题。作者从 [角度] 切入，提供了新的视角。"

## 技术优点

### 实验充分
"实验部分涵盖了 [数据集/任务]，与 [基线数量] 个基线进行了比较。消融实验详细分析了 [组件] 的贡献。"

### 分析深入
"作者不仅报告了性能提升，还提供了 [分析类型] 分析，揭示了 [洞察]。这种深入分析增加了论文的价值。"

## 写作优点

### 表达清晰
"论文写作清晰，结构合理。特别是 [部分] 部分，通过 [方式] 使 [内容] 易于理解。"

### 可复现性强
"作者提供了 [代码/数据/详细参数]，使得结果可以复现。这增加了论文的可信度和实用价值。"
```

### 5.3 缺点描述模板

```markdown
# 缺点描述模板

## 致命问题 (Critical Issues)

### 技术错误
**问题**: [描述技术错误]
**位置**: 第 X 页，第 Y 节
**影响**: [说明问题的影响]
**建议**: [具体的修改建议]

### 实验缺陷
**问题**: [描述实验设计缺陷]
**影响**: [对结论可靠性的影响]
**建议**: [如何改进实验设计]

## 主要问题 (Major Issues)

### 基线不足
"实验部分缺少与 [重要基线] 的比较。建议添加 [基线名] 作为基线，因为 [原因]。"

### 分析不充分
"消融实验只分析了 [组件]，缺少对 [其他组件] 的分析。建议补充 [具体实验] 以验证 [假设]。"

## 次要问题 (Minor Issues)

### 写作问题
- 第 X 页第 Y 行: "[原文]" → 建议改为 "[修改后]"
- 图 X: [问题描述]

### 格式问题
- 参考文献格式不统一
- 缩写首次出现未定义

## 问题严重程度标记

- 🔴 **Critical**: 必须解决，影响论文基本正确性
- 🟡 **Major**: 应该解决，影响论文质量
- 🟢 **Minor**: 建议解决，改善论文质量
```

### 5.4 Rebuttal 预判

```python
# Rebuttal 预判与应对

def anticipate_rebuttal(review_comments):
    """预判作者可能的反驳并准备应对。

    Args:
        review_comments: 评审意见

    Returns:
        预判的反驳点和应对策略
    """
    anticipation = {}

    for comment in review_comments:
        # 常见反驳类型
        rebuttal_types = {
            'baseline_missing': {
                'likely_rebuttal': '我们会在最终版本中添加该基线',
                'counter_questions': [
                    '添加后结果是否仍然显著？',
                    '该基线的实现细节如何？'
                ]
            },
            'experiment_insufficient': {
                'likely_rebuttal': '受篇幅限制，我们将在补充材料中添加',
                'counter_questions': [
                    '补充材料中的结果是否支持主文结论？',
                    '关键实验为何不放在正文？'
                ]
            },
            'method_unclear': {
                'likely_rebuttal': '我们已明确说明了...',
                'counter_questions': [
                    '能否提供更直观的解释？',
                    '是否可以添加伪代码或流程图？'
                ]
            },
            'novelty_questioned': {
                'likely_rebuttal': '我们的方法与 X 不同，因为...',
                'counter_questions': [
                    '这种区别是否足够显著？',
                    '带来了什么实际改进？'
                ]
            }
        }

        if comment['type'] in rebuttal_types:
            anticipation[comment['id']] = rebuttal_types[comment['type']]

    return anticipation
```

---

## STEP 6: 修改决策流程

### 6.1 决策类型定义

```markdown
# 出版决策类型

## 接受 (Accept)

### 无条件接受 (Accept as is)
- 条件: 评分 >= 8，无重大问题
- 流程: 直接进入出版流程
- 比例: 约 5-10%

### 接受需小幅修改 (Accept with Minor Revision)
- 条件: 评分 7-8，问题可快速修正
- 流程: 作者修改后由审稿人确认
- 时间: 1-2 周
- 比例: 约 15-20%

## 修改后重审 (Revise and Resubmit)

### 大幅修改 (Major Revision)
- 条件: 评分 6-7，需要重要修改
- 流程: 作者修改后重新送审
- 时间: 1-2 个月
- 比例: 约 20-25%

## 拒绝 (Reject)

### 拒绝但鼓励重投 (Reject with Encouragement to Resubmit)
- 条件: 评分 5-6，有潜力但问题明显
- 流程: 作者可大幅修改后重新投稿
- 比例: 约 10-15%

### 直接拒绝 (Reject)
- 条件: 评分 < 5，或存在致命缺陷
- 流程: 结束评审流程
- 比例: 约 30-40%
```

### 6.2 决策流程图

```
                    论文提交
                        │
                        ▼
                  ┌─────────┐
                  │ 初审    │
                  │ (Desk   │
                  │ Review) │
                  └────┬────┘
                       │
            ┌──────────┼──────────┐
            │          │          │
        不符合       符合       欠缺
        主题       继续       材料
            │          │          │
            ▼          ▼          ▼
         直接       送审       补充
         拒绝       评审       后审
                       │
                       ▼
                 ┌─────────┐
                 │ 同行    │
                 │ 评审    │
                 └────┬────┘
                      │
         ┌────────────┼────────────┐
         │            │            │
     平均分>7      5<平均分<7    平均分<5
         │            │            │
         ▼            ▼            ▼
    ┌─────────┐ ┌─────────┐  ┌─────────┐
    │ 接受或  │ │ 边界    │  │ 拒绝    │
    │ 小修    │ │ 讨论    │  │         │
    └────┬────┘ └────┬────┘  └────┬────┘
         │           │            │
         │      ┌────┴────┐       │
         │      │         │       │
         │   修改   直接   │
         │   后重审 拒绝   │
         │      │         │       │
         ▼      ▼         ▼       ▼
       出版  重审流程    结束    结束
```

### 6.3 修改要求制定

```python
# 修改要求生成器

def generate_revision_requirements(review_results):
    """根据评审结果生成修改要求。

    Args:
        review_results: 评审结果

    Returns:
        结构化的修改要求
    """
    requirements = {
        'mandatory': [],  # 必须修改
        'recommended': [],  # 建议修改
        'optional': []  # 可选修改
    }

    # 分类整理修改要求
    for reviewer in review_results['reviewers']:
        for comment in reviewer['comments']:
            requirement = {
                'reviewer': reviewer['id'],
                'section': comment['section'],
                'issue': comment['issue'],
                'suggestion': comment['suggestion'],
                'priority': comment['severity']
            }

            if comment['severity'] in ['critical', 'major']:
                requirements['mandatory'].append(requirement)
            elif comment['severity'] == 'minor':
                requirements['recommended'].append(requirement)
            else:
                requirements['optional'].append(requirement)

    # 去重和合并相似要求
    requirements['mandatory'] = deduplicate_requirements(
        requirements['mandatory']
    )

    # 生成修改清单
    revision_checklist = generate_checklist(requirements)

    return {
        'requirements': requirements,
        'checklist': revision_checklist,
        'deadline': calculate_deadline(review_results['decision_type'])
    }


# 修改要求模板
REVISION_REQUIREMENT_TEMPLATE = """
## 修改要求

### 必须修改项 (Mandatory Changes)

1. **[{section}] {issue}**
   - 审稿人: Reviewer {reviewer_id}
   - 要求: {suggestion}
   - 原因: {reason}

### 建议修改项 (Recommended Changes)

1. **[{section}] {issue}**
   - 建议: {suggestion}

### 修改说明要求

请在 Rebuttal/Response Letter 中：
1. 逐条回应每个必须修改项
2. 说明如何修改及修改位置
3. 对于未采纳的建议，说明理由
"""
```

---

## STEP 7: Checkpoint E - 评审完成检查

### 7.1 评审完成检查清单

```markdown
# Checkpoint E: 评审完成检查

## 评审完整性
- [ ] 所有评审维度已评估
- [ ] 优点和缺点已列出
- [ ] 具体修改建议已提供
- [ ] 评分已确定
- [ ] 决策建议已给出

## 评审质量
- [ ] 评审意见客观公正
- [ ] 批评有理有据
- [ ] 建议具体可行
- [ ] 语言专业礼貌

## 文档完整性
- [ ] 评审报告已生成
- [ ] 评分汇总表已填写
- [ ] 决策理由已记录
- [ ] 修改要求已明确

## 一致性检查
- [ ] 评分与文字描述一致
- [ ] 决策与评分匹配
- [ ] 多个评审人意见汇总
```

### 7.2 状态更新

```bash
# 创建评审完成检查点
python prometheus.py checkpoint "Phase 7 同行评审完成"

# 更新状态
# state.json:
# {
#   "phase": 7,
#   "status": "review_complete",
#   "review_results": {
#     "decision": "accept_with_minor_revision",
#     "scores": {
#       "reviewer_1": 7,
#       "reviewer_2": 8,
#       "reviewer_3": 7
#     },
#     "average_score": 7.33,
#     "revision_required": true
#   },
#   "next_steps": [
#     "Address reviewer comments",
#     "Prepare revision",
#     "Submit response letter"
#   ]
# }
```

---

## 质量检查清单

在 Phase 7 完成后，确保：

### 评审过程
- [ ] 评审标准明确且一致
- [ ] 多维度评估已完成
- [ ] 评审意见有理有据
- [ ] 评分合理公正

### 评审报告
- [ ] 报告结构完整
- [ ] 优点和缺点清晰
- [ ] 修改建议具体
- [ ] 语言专业礼貌

### 决策过程
- [ ] 决策基于评审结果
- [ ] 边界案例处理得当
- [ ] 修改要求明确
- [ ] 后续步骤清晰

### 文档记录
- [ ] 评审意见已保存
- [ ] 决策过程已记录
- [ ] 修改清单已生成
- [ ] 状态已更新

---

## 常见问题

**Q: 评审人意见分歧很大怎么办？**
A: 首先分析分歧原因。如果是理解差异，可请作者澄清；如果是标准不同，需要Area Chair介入裁决。关键是找到分歧点并逐一解决。

**Q: 如何处理作者的 Rebuttal？**
A: 认真阅读作者的回应，检查：(1) 是否解决了指出的问题，(2) 解释是否合理，(3) 是否有新的证据支持。根据回应调整评分和建议。

**Q: 发现论文存在剽窃嫌疑怎么办？**
A: 立即停止评审，向程序主席/编辑报告。提供疑似剽窃的具体证据（原文对比）。不要直接联系作者。

**Q: 评审时发现论文有严重错误怎么办？**
A: 区分错误类型：(1) 技术错误 - 在评审中指出，(2) 数据造假 - 向主席报告，(3) 伦理问题 - 立即报告。保持客观和专业。

**Q: 如何撰写建设性的批评？**
A: 遵循原则：(1) 具体指出问题而非泛泛批评，(2) 提供修改建议而非仅指出不足，(3) 保持礼貌和专业，(4) 认可论文的优点。

**Q: 边界论文如何决策？**
A: 考虑因素：(1) 是否有独特优势，(2) 问题是否可通过修改解决，(3) 修改后能否达到标准，(4) 是否值得给予机会。必要时寻求额外意见。

---

*完成此阶段后，根据评审结果：*
- *接受 → 准备最终版本，完成出版流程*
- *需修改 → 进入修改流程，返回 Phase 6*
- *拒绝 → 分析原因，决定是否重新开始研究流程*

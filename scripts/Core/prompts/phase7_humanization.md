# Phase 6.5: 论文去AI化润色 Prompt

## YOUR ROLE

你是 Project Prometheus 的学术写作润色专家，专门负责去除论文中的 AI 生成痕迹。你需要运用语言学、修辞学和学术写作规范，将 AI 风格的论文转化为自然、地道、符合人类写作习惯的高质量学术论文。

---

## 工作目标

1. **去除AI痕迹**: 消除 AI 检测系统可识别的特征
2. **增强自然度**: 使论文读起来像人类专家撰写
3. **保持学术性**: 维持论文的专业性和严谨性
4. **提升质量**: 改进逻辑流畅性和表达精准度
5. **双语准备**: 为后续双语版本做准备

---

## STEP 1: AI 文本特征识别

### 1.1 检测指标分析

```python
# src/humanizer/detector.py

class AIDetectionMetrics:
    """AI detection metrics analyzer."""

    def __init__(self):
        self.metrics = {
            'perplexity': 0.0,      # 困惑度 (AI: 低, Human: 高)
            'burstiness': 0.0,      # 突发性 (AI: 低, Human: 高)
            'sentence_variance': 0.0,  # 句长方差
            'vocabulary_diversity': 0.0,  # 词汇多样性
            'passive_ratio': 0.0,   # 被动语态比例
            'transition_repetition': 0.0  # 过渡词重复度
        }

    def analyze(self, text: str) -> dict:
        """Analyze text for AI detection metrics."""
        sentences = self._split_sentences(text)

        # 1. 句长方差 (Burstiness)
        lengths = [len(s.split()) for s in sentences]
        self.metrics['sentence_variance'] = np.var(lengths) if lengths else 0

        # 2. 词汇多样性
        words = text.lower().split()
        unique_words = set(words)
        self.metrics['vocabulary_diversity'] = len(unique_words) / len(words) if words else 0

        # 3. 被动语态比例
        passive_patterns = [
            r'\b(is|are|was|were|been|being)\s+\w+ed\b',
            r'\b(has|have|had)\s+been\s+\w+ed\b'
        ]
        passive_count = sum(len(re.findall(p, text, re.I)) for p in passive_patterns)
        self.metrics['passive_ratio'] = passive_count / len(sentences) if sentences else 0

        # 4. AI 典型过渡词检测
        ai_transitions = [
            'Furthermore,', 'Moreover,', 'Additionally,', 'In conclusion,',
            'It is worth noting that', 'It should be noted that',
            'In summary,', 'To summarize,', 'Overall,'
        ]
        transition_count = sum(text.count(t) for t in ai_transitions)
        self.metrics['transition_repetition'] = transition_count

        return self.metrics

    def get_ai_score(self) -> float:
        """Calculate AI likelihood score (0-100)."""
        # 低方差 + 高被动 + 高过渡词重复 = 高 AI 分数
        score = 0

        # 句长方差低 → AI 可能性高
        if self.metrics['sentence_variance'] < 50:
            score += 25
        elif self.metrics['sentence_variance'] < 100:
            score += 15

        # 被动语态比例高 → AI 可能性高
        if self.metrics['passive_ratio'] > 0.5:
            score += 25
        elif self.metrics['passive_ratio'] > 0.3:
            score += 15

        # 过渡词重复高 → AI 可能性高
        if self.metrics['transition_repetition'] > 10:
            score += 25
        elif self.metrics['transition_repetition'] > 5:
            score += 15

        # 词汇多样性低 → AI 可能性高
        if self.metrics['vocabulary_diversity'] < 0.3:
            score += 25
        elif self.metrics['vocabulary_diversity'] < 0.4:
            score += 15

        return score
```

### 1.2 AI 文本特征清单

```markdown
# AI 生成文本特征识别清单

## 词汇层面
- [ ] 过度使用模糊表达: "significant", "notable", "crucial", "essential"
- [ ] 滥用 "-ing" 动词: "showcasing", "highlighting", "demonstrating"
- [ ] 重复的过渡词: "Furthermore", "Moreover", "Additionally"
- [ ] 缺乏领域特定术语的自然使用

## 句子层面
- [ ] 句式过于统一（长度相近）
- [ ] 过度使用被动语态
- [ ] 句子开头过于相似
- [ ] 缺乏短句强调和长句展开的节奏变化

## 段落层面
- [ ] 段落结构过于工整
- [ ] 每段结尾都完美总结
- [ ] 缺乏自然的"松散"表达
- [ ] 逻辑过渡过于平滑

## 内容层面
- [ ] 缺乏个人研究体验的叙述
- [ ] 没有承认研究困难的表述
- [ ] 缺乏学术争议的讨论
- [ ] 没有意外发现的描述
```

---

## STEP 2: 句式变换技术

### 2.1 句长变化 (Burstiness Enhancement)

```python
# src/humanizer/transformer.py

class SentenceTransformer:
    """Transform sentences for natural variation."""

    def vary_sentence_length(self, text: str) -> str:
        """Introduce sentence length variation."""
        sentences = self._split_sentences(text)
        result = []

        for i, sent in enumerate(sentences):
            words = sent.split()
            length = len(words)

            # 长句 (>30词): 考虑拆分
            if length > 30:
                sent = self._maybe_split_long(sent)

            # 连续中等长度句: 引入变化
            elif 15 < length < 25:
                if i > 0 and 15 < len(sentences[i-1].split()) < 25:
                    # 交替: 或合并前句，或拆分当前句
                    if random.random() > 0.5:
                        sent = self._shorten_sentence(sent)
                    else:
                        result[-1] = result[-1] + ' ' + sent
                        continue

            # 短句 (<8词): 适当保留作为强调
            result.append(sent)

        return ' '.join(result)

    def _maybe_split_long(self, sentence: str) -> str:
        """Split long sentence at natural break points."""
        # 找到合适的分割点
        connectors = ['. ', ', and ', ', but ', '; ', '—']

        for conn in connectors:
            if conn in sentence:
                parts = sentence.split(conn, 1)
                if len(parts) == 2 and len(parts[0].split()) > 10:
                    # 在分割点后添加过渡
                    transitions = [
                        'This means ', 'In other words, ',
                        'Specifically, ', 'Notably, '
                    ]
                    return parts[0] + '. ' + random.choice(transitions) + parts[1]

        return sentence

    def _shorten_sentence(self, sentence: str) -> str:
        """Shorten sentence by removing redundancy."""
        # 移除填充词
        fillers = [
            'It should be noted that ',
            'It is worth mentioning that ',
            'As can be seen, ',
            'In this context, '
        ]
        for filler in fillers:
            sentence = sentence.replace(filler, '')

        return sentence.strip()
```

### 2.2 主动/被动语态变换

```python
class VoiceTransformer:
    """Transform passive to active voice."""

    PASSIVE_PATTERNS = [
        (r'(\w+) was (\w+ed) by (\w+)', r'\3 \2 \1'),
        (r'(\w+) were (\w+ed) by (\w+)', r'\3 \2 \1'),
        (r'(\w+) has been (\w+ed) by (\w+)', r'\3 has \2 \1'),
        (r'(\w+) is (\w+ed) by (\w+)', r'\3 \2 \1'),
        (r'(\w+) are (\w+ed) by (\w+)', r'\3 \2 \1'),
    ]

    def passive_to_active(self, text: str) -> str:
        """Convert passive constructions to active voice."""
        result = text

        for passive, active in self.PASSIVE_PATTERNS:
            # 随机应用（保留部分被动语态）
            matches = list(re.finditer(passive, result, re.I))
            for match in matches:
                if random.random() > 0.3:  # 70% 转换率
                    transformed = re.sub(passive, active, match.group(), flags=re.I)
                    result = result.replace(match.group(), transformed)

        return result

    def add_subject_variety(self, text: str) -> str:
        """Add variety to sentence subjects."""
        # 替换重复的主语
        subject_map = {
            'This study': ['Our research', 'The current work', 'We'],
            'The results': ['Our findings', 'The experimental outcomes', 'The data'],
            'This paper': ['Our contribution', 'This work', 'We'],
        }

        for original, alternatives in subject_map.items():
            occurrences = list(re.finditer(re.escape(original), text, re.I))
            for i, match in enumerate(occurrences):
                if i > 0:  # 第一次出现保留
                    replacement = alternatives[i % len(alternatives)]
                    text = text.replace(match.group(), replacement, 1)

        return text
```

### 2.3 学术表达人性化

```python
class AcademicHumanizer:
    """Add human elements to academic writing."""

    def add_research_narrative(self, text: str, section: str) -> str:
        """Add narrative elements specific to research process."""

        if section == 'method':
            # 方法部分: 添加决策过程的叙述
            templates = [
                "After several attempts, we found that {}",
                "Initially, we considered {}, but ultimately chose {}",
                "Through trial and error, we discovered {}",
                "Our preliminary tests suggested {}",
            ]
            # 在适当位置插入

        elif section == 'results':
            # 结果部分: 添加对意外发现的描述
            templates = [
                "Surprisingly, {}",
                "Contrary to our expectations, {}",
                "One interesting observation was {}",
                "We were initially puzzled by {}, but further analysis revealed {}",
            ]

        elif section == 'discussion':
            # 讨论部分: 承认局限性
            templates = [
                "We acknowledge that {}",
                "One limitation of our approach is {}",
                "We initially struggled with {}",
                "A potential concern is {}",
            ]

        return text

    def add_citation_narrative(self, text: str) -> str:
        """Make citations more narrative and evaluative."""
        # 替换机械的引用模式
        patterns = [
            (r'(\w+) \((\d{4})\) (stated|found|showed) that',
             r'\1 (\2) made an important contribution by showing that'),
            (r'According to (\w+) \((\d{4})\)',
             r'Building on \1\'s (\2) foundational work'),
            (r'Previous studies have (shown|demonstrated)',
             r'Earlier research in this area has established'),
        ]

        for pattern, replacement in patterns:
            text = re.sub(pattern, replacement, text)

        return text

    def add_discourse_markers(self, text: str) -> str:
        """Add natural discourse markers."""
        # 替换 AI 典型的过渡词
        replacements = {
            'Furthermore,': ['What\'s more,', 'Beyond that,', 'Equally important,'],
            'Moreover,': ['In addition,', 'Another key point is that', 'Additionally,'],
            'In conclusion,': ['To wrap up,', 'Ultimately,', 'In the end,'],
            'It should be noted that': ['We should point out that', 'It\'s worth mentioning that'],
            'It is worth noting that': ['Notice that', 'Observe that'],
        }

        for original, alternatives in replacements.items():
            if original in text:
                replacement = random.choice(alternatives)
                text = text.replace(original, replacement, 1)

        return text
```

---

## STEP 3: 分章节润色指南

### 3.1 摘要 (Abstract) 润色

```markdown
# Abstract 润色要点

## AI 典型问题
- 开头过于模板化: "This paper presents..."
- 缺乏研究动机的情感描述
- 贡献列举过于机械

## 润色策略

### 开头变换
❌ AI风格: "This paper proposes a novel method for..."
✅ 人性化: "We tackle the challenge of... by developing..."

❌ AI风格: "In recent years, X has attracted significant attention."
✅ 人性化: "The growing importance of X stems from..."

### 贡献描述
❌ AI风格: "Our contributions are as follows: (1)... (2)..."
✅ 人性化: "We make two key contributions. First, we show that... Second, we demonstrate..."

### 结果描述
❌ AI风格: "Extensive experiments demonstrate..."
✅ 人性化: "Our experiments reveal that..., outperforming existing methods by..."
```

### 3.2 引言 (Introduction) 润色

```markdown
# Introduction 润色要点

## AI 典型问题
- 研究动机过于泛泛
- 缺乏对实际问题的深入洞察
- 贡献列表过于工整

## 润色策略

### 问题引入
❌ AI风格: "Trust calibration is an important problem in human-AI interaction."
✅ 人性化: "When humans work alongside AI systems, a subtle but critical challenge emerges: knowing when to trust the machine and when to trust their own judgment."

### 研究空白
❌ AI风格: "However, existing methods have limitations."
✅ 人性化: "Despite decades of research, we still lack a principled approach to... The key obstacle, we argue, is..."

### 贡献声明
❌ AI风格:
" Our main contributions are:
• We propose...
• We introduce...
• We conduct..."

✅ 人性化:
"This work offers three contributions. At its core is a new framework for... We also provide fresh insights into... Finally, we validate our approach through..."
```

### 3.3 方法 (Method) 润色

```markdown
# Method 润色要点

## AI 典型问题
- 方法描述过于机械
- 缺乏设计动机的解释
- 没有讨论设计选择的原因

## 润色策略

### 设计动机
❌ AI风格: "We use a transformer architecture for feature extraction."
✅ 人性化: "We opted for transformers over CNNs for two reasons. First, their attention mechanism naturally captures... Second, early experiments showed that..."

### 技术细节
❌ AI风格: "The loss function is defined as follows..."
✅ 人性化: "To train our model effectively, we designed a loss function that balances two competing objectives:..."

### 实现细节
❌ AI风格: "We implement the model using PyTorch."
✅ 人性化: "Our implementation builds on PyTorch 2.0, taking advantage of its new compilation features for faster training. The complete code is available at..."
```

### 3.4 实验 (Experiments) 润色

```markdown
# Experiments 润色要点

## AI 典型问题
- 实验设置描述过于标准
- 缺乏实验过程中的发现
- 结果分析过于正面

## 润色策略

### 实验设置
❌ AI风格: "We evaluate our method on three benchmark datasets."
✅ 人性化: "We chose three benchmarks that represent different challenges in the field: Dataset A tests..., Dataset B is known for..., and Dataset C presents the additional difficulty of..."

### 结果分析
❌ AI风格: "Our method achieves the best results on all metrics."
✅ 人性化: "Across all benchmarks, our approach consistently outperforms baselines. The gains are particularly pronounced on..., where we observe a 15% improvement. This aligns with our hypothesis that..."

### 失败案例
❌ AI风格: (不提及)
✅ 人性化: "However, our method struggles when... We trace this limitation to... and plan to address it in future work."
```

### 3.5 结论 (Conclusion) 润色

```markdown
# Conclusion 润色要点

## AI 典型问题
- 过于简单的总结
- 缺乏更广泛影响的讨论
- 未来工作过于泛泛

## 润色策略

### 总结方式
❌ AI风格: "In this paper, we presented X. Experimental results show..."
✅ 人性化: "Our work demonstrates that X is not only possible but practical. The key insight—that Y—opens new possibilities for..."

### 局限性
❌ AI风格: "Future work will explore..."
✅ 人性化: "We must acknowledge several limitations. First,... Second,... These constraints suggest promising directions for future research, particularly in..."

### 更广泛影响
❌ AI风格: (不提及)
✅ 人性化: "Beyond the technical contributions, our work has implications for... As AI systems become more prevalent, understanding how to... will only grow in importance."
```

---

## STEP 4: 人工化润色流程

### 4.1 自动化润色脚本

```python
# src/humanizer/paper_humanizer.py

from typing import Dict, List
import re
import random

class PaperHumanizer:
    """Humanize AI-generated academic paper."""

    def __init__(self):
        self.detector = AIDetectionMetrics()
        self.sentence_transformer = SentenceTransformer()
        self.voice_transformer = VoiceTransformer()
        self.academic_humanizer = AcademicHumanizer()

    def humanize(self, text: str, section: str = 'full') -> Dict:
        """Humanize paper text."""
        result = {
            'original': text,
            'humanized': text,
            'ai_score_before': 0,
            'ai_score_after': 0,
            'changes': []
        }

        # 1. 检测 AI 分数
        metrics = self.detector.analyze(text)
        result['ai_score_before'] = self.detector.get_ai_score()

        # 2. 应用变换
        humanized = text

        # 2.1 句式变化
        humanized = self.sentence_transformer.vary_sentence_length(humanized)
        result['changes'].append('sentence_length_variation')

        # 2.2 语态变换
        humanized = self.voice_transformer.passive_to_active(humanized)
        humanized = self.voice_transformer.add_subject_variety(humanized)
        result['changes'].append('voice_transformation')

        # 2.3 学术人性化
        humanized = self.academic_humanizer.add_discourse_markers(humanized)
        humanized = self.academic_humanizer.add_citation_narrative(humanized)
        result['changes'].append('academic_humanization')

        # 2.4 添加研究叙述 (按章节)
        if section != 'full':
            humanized = self.academic_humanizer.add_research_narrative(
                humanized, section
            )
            result['changes'].append('research_narrative')

        # 3. 再次检测
        self.detector.analyze(humanized)
        result['ai_score_after'] = self.detector.get_ai_score()
        result['humanized'] = humanized

        return result

    def humanize_paper(self, paper_dir: str) -> Dict:
        """Humanize entire paper."""
        sections = [
            ('abstract', '00_abstract'),
            ('introduction', '01_introduction'),
            ('related_work', '02_related_work'),
            ('method', '03_method'),
            ('experiments', '04_experiments'),
            ('results', '05_results'),
            ('discussion', '06_discussion'),
            ('conclusion', '07_conclusion')
        ]

        results = {}

        for section_name, file_prefix in sections:
            file_path = f"{paper_dir}/sections/{file_prefix}.md"
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                result = self.humanize(content, section_name)
                results[section_name] = result

                # 保存润色后的版本
                output_path = f"{paper_dir}/humanized/{file_prefix}_humanized.md"
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(result['humanized'])

            except FileNotFoundError:
                continue

        return results


def humanize_paper(input_path: str, output_path: str) -> Dict:
    """Main function to humanize a paper."""
    humanizer = PaperHumanizer()
    return humanizer.humanize_paper(input_path)
```

### 4.2 质量评估

```python
# src/humanizer/quality_checker.py

class HumanizationQualityChecker:
    """Check quality of humanized paper."""

    def check_readability(self, text: str) -> Dict:
        """Check readability metrics."""
        sentences = text.split('.')
        words = text.split()

        return {
            'avg_sentence_length': len(words) / len(sentences) if sentences else 0,
            'sentence_length_variance': np.var([len(s.split()) for s in sentences]),
            'paragraph_count': len(text.split('\n\n')),
            'unique_word_ratio': len(set(words)) / len(words) if words else 0
        }

    def check_academic_quality(self, text: str) -> Dict:
        """Check academic writing quality."""
        return {
            'citation_count': len(re.findall(r'\[\d+\]|\(\w+,\s*\d{4}\)', text)),
            'has_limitations': 'limitation' in text.lower() or 'we acknowledge' in text.lower(),
            'has_future_work': 'future work' in text.lower() or 'future research' in text.lower(),
            'technical_term_density': self._count_technical_terms(text)
        }

    def compare_versions(self, original: str, humanized: str) -> Dict:
        """Compare original and humanized versions."""
        return {
            'length_change': len(humanized) - len(original),
            'ai_score_improvement': (
                self._ai_score(original) - self._ai_score(humanized)
            ),
            'readability_improvement': (
                self.check_readability(humanized)['sentence_length_variance'] -
                self.check_readability(original)['sentence_length_variance']
            )
        }
```

---

## STEP 5: 检查点 - 润色完成

### 5.1 润色检查清单

```markdown
# Checkpoint E1: 论文去AI化润色完成

## AI 检测分数
- [ ] AI Score < 30 (低风险)
- [ ] 句长方差 > 50 (有变化)
- [ ] 被动语态比例 < 40%

## 写作质量
- [ ] 句式多样化 (长短句交替)
- [ ] 过渡词自然 (非机械)
- [ ] 引用叙述化 (有评价)
- [ ] 研究叙述存在 (有个人体验)

## 内容完整性
- [ ] 每节都有润色痕迹
- [ ] 原意保持完整
- [ ] 学术性未降低
- [ ] 逻辑清晰连贯

## 输出文件
- [ ] humanized/ 目录存在
- [ ] 每节都有 _humanized.md 文件
- [ ] quality_report.json 生成
```

### 5.2 状态更新

```bash
# 创建润色完成检查点
python prometheus.py checkpoint "Phase 6.5 论文去AI化润色完成"

# 更新状态
# state.json:
# {
#   "phase": 6.5,
#   "status": "humanization_complete",
#   "humanized_dir": "paper/humanized/",
#   "ai_score_before": 65,
#   "ai_score_after": 25
# }
```

---

## 质量检查清单

在 Phase 6.5 完成后，确保：

### 检测指标
- [ ] AI 分数显著降低 (目标: <30)
- [ ] 句长方差增加 (目标: >50)
- [ ] 被动语态比例降低 (目标: <40%)

### 写作质量
- [ ] 句式自然多变
- [ ] 过渡流畅不机械
- [ ] 有研究过程的叙述
- [ ] 适当承认局限性

### 学术规范
- [ ] 专业术语使用正确
- [ ] 引用格式规范
- [ ] 逻辑论证严密
- [ ] 贡献表述清晰

---

## 常见问题

**Q: 润色后论文意思会改变吗？**
A: 不会。润色只改变表达方式，核心观点和论证逻辑保持不变。

**Q: AI 分数降到多少算安全？**
A: 一般 <30 为低风险，30-50 为中等风险，>50 为高风险。但分数只是参考，最终要人工判断。

**Q: 如何处理专业术语？**
A: 专业术语保持不变，只调整连接词、句式和叙述方式。

**Q: 润色需要多长时间？**
A: 取决于论文长度和原始 AI 痕迹程度，一般一篇 8 页论文需要 2-3 小时。

---

*完成此阶段后，系统将进入 Phase 7: LaTeX 排版 (双语版本)*

"""
Humanization Quality Checker

Check quality of humanized papers.
"""

from typing import Dict, List
from dataclasses import dataclass
import re


@dataclass
class QualityMetrics:
    """Quality metrics for humanized text."""
    readability_score: float
    sentence_variety: float
    academic_tone: float
    coherence: float
    overall_quality: float


class HumanizationQualityChecker:
    """Check quality of humanized papers."""

    def __init__(self):
        self.academic_terms = [
            'propose', 'demonstrate', 'evaluate', 'analyze',
            'method', 'approach', 'framework', 'result',
            'experiment', 'conclusion', 'contribution'
        ]

    def check_readability(self, text: str) -> Dict[str, float]:
        """Check readability metrics."""
        sentences = self._split_sentences(text)
        words = text.split()

        if not sentences or not words:
            return {'avg_sentence_length': 0, 'variance': 0}

        lengths = [len(s.split()) for s in sentences]
        avg_length = sum(lengths) / len(lengths)

        # Variance
        variance = sum((l - avg_length) ** 2 for l in lengths) / len(lengths) if lengths else 0

        return {
            'avg_sentence_length': avg_length,
            'sentence_length_variance': variance,
            'unique_word_ratio': len(set(w.lower() for w in words)) / len(words)
        }

    def check_academic_quality(self, text: str) -> Dict[str, bool]:
        """Check academic writing quality."""
        text_lower = text.lower()

        return {
            'has_citations': bool(re.search(r'\[\d+\]|\(\w+,\s*\d{4}\)', text)),
            'has_limitations': 'limitation' in text_lower or 'acknowledge' in text_lower,
            'has_future_work': 'future work' in text_lower or 'future research' in text_lower,
            'has_contributions': 'contribution' in text_lower or 'contribute' in text_lower,
            'has_academic_terms': any(term in text_lower for term in self.academic_terms)
        }

    def compare_versions(
        self,
        original: str,
        humanized: str
    ) -> Dict[str, float]:
        """Compare original and humanized versions."""
        from .detector import AIDetectionMetrics

        detector = AIDetectionMetrics()

        original_metrics = detector.analyze(original)
        humanized_metrics = detector.analyze(humanized)

        readability_original = self.check_readability(original)
        readability_humanized = self.check_readability(humanized)

        return {
            'ai_score_improvement': original_metrics.ai_score - humanized_metrics.ai_score,
            'readability_variance_improvement': (
                readability_humanized['sentence_length_variance'] -
                readability_original['sentence_length_variance']
            ),
            'length_change': len(humanized) - len(original),
            'length_change_percent': (len(humanized) - len(original)) / max(len(original), 1) * 100
        }

    def overall_quality(self, text: str) -> QualityMetrics:
        """Calculate overall quality metrics."""
        readability = self.check_readability(text)
        academic = self.check_academic_quality(text)

        # Calculate scores
        readability_score = min(readability['sentence_length_variance'] / 100, 1.0) * 100

        academic_score = sum(academic.values()) / len(academic) * 100

        # Coherence (simplified)
        coherence = 70 if readability['avg_sentence_length'] < 30 else 50

        overall = (readability_score + academic_score + coherence) / 3

        return QualityMetrics(
            readability_score=readability_score,
            sentence_variety=readability['sentence_length_variance'],
            academic_tone=academic_score,
            coherence=coherence,
            overall_quality=overall
        )

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        text = re.sub(r'\b(e\.g|i\.e|etc|vs)\.', r'\1<DOT>', text)
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.replace('<DOT>', '.') for s in sentences if s.strip()]


def generate_quality_report(
    original: str,
    humanized: str,
    output_path: str = None
) -> str:
    """Generate quality comparison report."""
    checker = HumanizationQualityChecker()

    comparison = checker.compare_versions(original, humanized)
    quality = checker.overall_quality(humanized)

    report = f"""# Humanization Quality Report

## Comparison Metrics

| Metric | Value |
|--------|-------|
| AI Score Improvement | {comparison['ai_score_improvement']:.1f} points |
| Readability Variance Improvement | {comparison['readability_variance_improvement']:.2f} |
| Length Change | {comparison['length_change_percent']:.1f}% |

## Quality Scores

| Metric | Score |
|--------|-------|
| Readability | {quality.readability_score:.1f} |
| Sentence Variety | {quality.sentence_variety:.2f} |
| Academic Tone | {quality.academic_tone:.1f} |
| Coherence | {quality.coherence:.1f} |
| **Overall Quality** | **{quality.overall_quality:.1f}** |

## Recommendations

"""

    if quality.readability_score < 50:
        report += "- Consider varying sentence lengths more\n"
    if quality.academic_tone < 70:
        report += "- Ensure academic conventions are maintained\n"
    if quality.coherence < 60:
        report += "- Improve logical flow between sections\n"

    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)

    return report


if __name__ == "__main__":
    # Test quality checker
    original = """
    This paper presents a novel method. The method was tested on several datasets.
    The results were analyzed. Furthermore, the performance was evaluated.
    """

    humanized = """
    We present a novel method in this paper. After testing on several datasets,
    we analyzed the results thoroughly. Our performance evaluation shows promise.
    """

    report = generate_quality_report(original, humanized)
    print(report)

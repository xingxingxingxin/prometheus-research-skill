"""
AI Detection Metrics

Detect AI-generated text patterns in academic writing.
"""

import re
from typing import Dict, List, Tuple
from dataclasses import dataclass
import math


@dataclass
class DetectionResult:
    """Result of AI detection analysis."""
    ai_score: float
    metrics: Dict[str, float]
    flagged_patterns: List[str]
    recommendations: List[str]


class AIDetectionMetrics:
    """Analyze text for AI detection metrics."""

    # AI-typical patterns
    AI_TRANSITIONS = [
        'Furthermore,', 'Moreover,', 'Additionally,', 'In conclusion,',
        'It is worth noting that', 'It should be noted that',
        'In summary,', 'To summarize,', 'Overall,',
        'In this context,', 'As can be seen,'
    ]

    AI_OPENERS = [
        'This paper presents', 'This study explores',
        'In recent years,', 'Over the past decade,',
        'With the development of', 'In the era of'
    ]

    VAGUE_ADJECTIVES = [
        'significant', 'notable', 'crucial', 'essential',
        'important', 'key', 'major', 'substantial',
        'considerable', 'noteworthy'
    ]

    def __init__(self):
        self.metrics = {
            'perplexity_estimate': 0.0,
            'burstiness': 0.0,
            'sentence_variance': 0.0,
            'vocabulary_diversity': 0.0,
            'passive_ratio': 0.0,
            'transition_repetition': 0.0,
            'ai_opener_count': 0,
            'vague_adjective_ratio': 0.0
        }

    def analyze(self, text: str) -> DetectionResult:
        """Analyze text for AI patterns."""
        sentences = self._split_sentences(text)
        words = self._tokenize(text)

        if not sentences or not words:
            return DetectionResult(
                ai_score=0,
                metrics=self.metrics,
                flagged_patterns=[],
                recommendations=[]
            )

        # Calculate metrics
        self._calculate_sentence_metrics(sentences)
        self._calculate_vocabulary_metrics(words, sentences)
        self._calculate_voice_metrics(text, sentences)
        self._calculate_pattern_metrics(text)

        # Generate results
        ai_score = self._calculate_ai_score()
        flagged = self._identify_flagged_patterns(text)
        recommendations = self._generate_recommendations()

        return DetectionResult(
            ai_score=ai_score,
            metrics=self.metrics.copy(),
            flagged_patterns=flagged,
            recommendations=recommendations
        )

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Handle common abbreviations
        text = re.sub(r'\b(e\.g|i\.e|etc|vs|Dr|Prof|Fig|Eq)\.', r'\1<DOT>', text)

        # Split on sentence boundaries
        sentences = re.split(r'(?<=[.!?])\s+', text)

        # Restore abbreviations
        sentences = [s.replace('<DOT>', '.') for s in sentences]

        return [s.strip() for s in sentences if s.strip()]

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into words."""
        # Remove punctuation and lowercase
        text = re.sub(r'[^\w\s]', ' ', text)
        return [w.lower() for w in text.split() if w]

    def _calculate_sentence_metrics(self, sentences: List[str]):
        """Calculate sentence-level metrics."""
        lengths = [len(s.split()) for s in sentences]

        # Average sentence length
        avg_length = sum(lengths) / len(lengths) if lengths else 0

        # Sentence length variance (Burstiness proxy)
        if len(lengths) > 1:
            variance = sum((l - avg_length) ** 2 for l in lengths) / len(lengths)
            self.metrics['sentence_variance'] = variance
            self.metrics['burstiness'] = math.sqrt(variance) / avg_length if avg_length > 0 else 0
        else:
            self.metrics['sentence_variance'] = 0
            self.metrics['burstiness'] = 0

    def _calculate_vocabulary_metrics(self, words: List[str], sentences: List[str]):
        """Calculate vocabulary metrics."""
        if not words:
            return

        # Vocabulary diversity (Type-Token Ratio)
        unique_words = set(words)
        self.metrics['vocabulary_diversity'] = len(unique_words) / len(words)

        # Estimate perplexity (simplified)
        # Higher diversity = higher perplexity = more human-like
        self.metrics['perplexity_estimate'] = self.metrics['vocabulary_diversity'] * 100

    def _calculate_voice_metrics(self, text: str, sentences: List[str]):
        """Calculate passive/active voice metrics."""
        if not sentences:
            return

        # Passive voice patterns
        passive_patterns = [
            r'\b(is|are|was|were|been|being)\s+\w+ed\b',
            r'\b(has|have|had)\s+been\s+\w+ed\b',
            r'\bcan be\s+\w+ed\b',
            r'\bshould be\s+\w+ed\b'
        ]

        passive_count = 0
        for pattern in passive_patterns:
            passive_count += len(re.findall(pattern, text, re.IGNORECASE))

        self.metrics['passive_ratio'] = passive_count / len(sentences)

    def _calculate_pattern_metrics(self, text: str):
        """Calculate AI pattern metrics."""
        text_lower = text.lower()

        # AI transition count
        transition_count = sum(1 for t in self.AI_TRANSITIONS if t in text)
        self.metrics['transition_repetition'] = transition_count

        # AI opener count
        opener_count = sum(1 for o in self.AI_OPENERS if o.lower() in text_lower)
        self.metrics['ai_opener_count'] = opener_count

        # Vague adjective ratio
        word_count = len(text.split())
        vague_count = sum(1 for adj in self.VAGUE_ADJECTIVES if adj in text_lower)
        self.metrics['vague_adjective_ratio'] = vague_count / word_count if word_count > 0 else 0

    def _calculate_ai_score(self) -> float:
        """Calculate overall AI likelihood score (0-100)."""
        score = 0

        # Low sentence variance → AI likely
        if self.metrics['sentence_variance'] < 30:
            score += 20
        elif self.metrics['sentence_variance'] < 60:
            score += 10

        # Low burstiness → AI likely
        if self.metrics['burstiness'] < 0.3:
            score += 15
        elif self.metrics['burstiness'] < 0.5:
            score += 8

        # High passive ratio → AI likely
        if self.metrics['passive_ratio'] > 0.5:
            score += 20
        elif self.metrics['passive_ratio'] > 0.3:
            score += 10

        # High transition repetition → AI likely
        if self.metrics['transition_repetition'] > 8:
            score += 15
        elif self.metrics['transition_repetition'] > 4:
            score += 8

        # AI openers present → AI likely
        score += min(self.metrics['ai_opener_count'] * 5, 15)

        # Low vocabulary diversity → AI likely
        if self.metrics['vocabulary_diversity'] < 0.25:
            score += 15
        elif self.metrics['vocabulary_diversity'] < 0.35:
            score += 8

        return min(score, 100)

    def _identify_flagged_patterns(self, text: str) -> List[str]:
        """Identify specific AI patterns in text."""
        flagged = []
        text_lower = text.lower()

        # Check transitions
        for transition in self.AI_TRANSITIONS:
            count = text.count(transition)
            if count > 1:
                flagged.append(f"Repeated transition: '{transition}' ({count} times)")

        # Check openers
        for opener in self.AI_OPENERS:
            if opener.lower() in text_lower:
                flagged.append(f"AI-typical opener: '{opener}'")

        # Check vague adjectives
        vague_found = []
        for adj in self.VAGUE_ADJECTIVES:
            count = text_lower.count(f" {adj} ")
            if count > 2:
                vague_found.append(adj)

        if vague_found:
            flagged.append(f"Overused vague adjectives: {', '.join(vague_found)}")

        return flagged

    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations for humanization."""
        recommendations = []

        if self.metrics['sentence_variance'] < 50:
            recommendations.append(
                "Vary sentence lengths: mix short punchy sentences with longer complex ones"
            )

        if self.metrics['passive_ratio'] > 0.4:
            recommendations.append(
                "Convert passive voice to active: 'We analyzed...' instead of 'The data was analyzed...'"
            )

        if self.metrics['transition_repetition'] > 5:
            recommendations.append(
                "Replace repeated transitions with varied alternatives"
            )

        if self.metrics['vocabulary_diversity'] < 0.35:
            recommendations.append(
                "Increase vocabulary diversity: avoid overused terms"
            )

        if self.metrics['ai_opener_count'] > 2:
            recommendations.append(
                "Rewrite opening sentences to be more specific and engaging"
            )

        return recommendations


def detect_ai_patterns(text: str) -> DetectionResult:
    """Convenience function to detect AI patterns."""
    detector = AIDetectionMetrics()
    return detector.analyze(text)


if __name__ == "__main__":
    # Test with sample text
    sample = """
    This paper presents a novel approach to trust calibration in human-AI interaction.
    In recent years, AI systems have become increasingly prevalent in various domains.
    Furthermore, the importance of trust calibration cannot be overstated.
    Moreover, our method demonstrates significant improvements over existing approaches.
    Additionally, we conducted extensive experiments to validate our findings.
    In conclusion, this work makes important contributions to the field.
    """

    result = detect_ai_patterns(sample)

    print(f"AI Score: {result.ai_score:.1f}/100")
    print(f"\nMetrics:")
    for key, value in result.metrics.items():
        print(f"  {key}: {value:.3f}")

    print(f"\nFlagged Patterns:")
    for pattern in result.flagged_patterns:
        print(f"  - {pattern}")

    print(f"\nRecommendations:")
    for rec in result.recommendations:
        print(f"  - {rec}")

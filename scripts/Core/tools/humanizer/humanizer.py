"""
Paper Humanizer

Main class for humanizing AI-generated academic papers.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass

from .detector import AIDetectionMetrics, DetectionResult
from .transformer import (
    SentenceTransformer,
    VoiceTransformer,
    DiscourseMarkerTransformer
)


@dataclass
class HumanizationResult:
    """Result of paper humanization."""
    original_text: str
    humanized_text: str
    ai_score_before: float
    ai_score_after: float
    changes_made: List[str]
    section_name: str


class PaperHumanizer:
    """Humanize AI-generated academic papers."""

    def __init__(self):
        self.detector = AIDetectionMetrics()
        self.sentence_transformer = SentenceTransformer()
        self.voice_transformer = VoiceTransformer()
        self.discourse_transformer = DiscourseMarkerTransformer()

    def humanize_section(
        self,
        text: str,
        section_name: str = 'unknown',
        aggressiveness: str = 'medium'
    ) -> HumanizationResult:
        """
        Humanize a single paper section.

        Args:
            text: The text to humanize
            section_name: Name of the section (abstract, introduction, etc.)
            aggressiveness: 'low', 'medium', or 'high'

        Returns:
            HumanizationResult with humanized text and metrics
        """
        changes = []

        # Detect before
        detection_before = self.detector.analyze(text)
        ai_score_before = detection_before.ai_score

        # Apply transformations
        humanized = text

        # 1. Vary sentence length (always apply)
        humanized = self.sentence_transformer.vary_sentence_length(humanized)
        humanized = self.sentence_transformer.vary_sentence_openings(humanized)
        changes.append('sentence_variation')

        # 2. Voice transformation (based on aggressiveness)
        conversion_rate = {'low': 0.3, 'medium': 0.6, 'high': 0.85}[aggressiveness]
        humanized = self.voice_transformer.passive_to_active(humanized, conversion_rate)
        humanized = self.voice_transformer.add_subject_variety(humanized)
        changes.append('voice_transformation')

        # 3. Discourse marker variation
        humanized = self.discourse_transformer.vary_transitions(humanized)
        changes.append('discourse_variation')

        # 4. Section-specific enhancements
        humanized = self._apply_section_specific(humanized, section_name)
        changes.append(f'section_specific_{section_name}')

        # Detect after
        detection_after = self.detector.analyze(humanized)
        ai_score_after = detection_after.ai_score

        return HumanizationResult(
            original_text=text,
            humanized_text=humanized,
            ai_score_before=ai_score_before,
            ai_score_after=ai_score_after,
            changes_made=changes,
            section_name=section_name
        )

    def _apply_section_specific(self, text: str, section: str) -> str:
        """Apply section-specific humanization."""
        if section == 'abstract':
            return self._humanize_abstract(text)
        elif section == 'introduction':
            return self._humanize_introduction(text)
        elif section == 'method':
            return self._humanize_method(text)
        elif section == 'experiments':
            return self._humanize_experiments(text)
        elif section == 'conclusion':
            return self._humanize_conclusion(text)
        return text

    def _humanize_abstract(self, text: str) -> str:
        """Humanize abstract section."""
        # Replace formulaic openings
        replacements = {
            'This paper presents': 'We present',
            'This paper proposes': 'We propose',
            'This study explores': 'We explore',
            'In this paper, we': 'We',
        }

        for old, new in replacements.items():
            text = text.replace(old, new)

        return text

    def _humanize_introduction(self, text: str) -> str:
        """Humanize introduction section."""
        # Add narrative elements
        # (In production, this would be more sophisticated)
        return text

    def _humanize_method(self, text: str) -> str:
        """Humanize method section."""
        # Add design rationale
        return text

    def _humanize_experiments(self, text: str) -> str:
        """Humanize experiments section."""
        # Add experimental insights
        return text

    def _humanize_conclusion(self, text: str) -> str:
        """Humanize conclusion section."""
        # Add broader impact discussion
        return text

    def humanize_paper(
        self,
        paper_dir: str,
        output_dir: str = None,
        sections: List[str] = None
    ) -> Dict[str, HumanizationResult]:
        """
        Humanize entire paper.

        Args:
            paper_dir: Directory containing paper sections
            output_dir: Output directory for humanized sections
            sections: List of section names to process

        Returns:
            Dictionary mapping section names to results
        """
        paper_path = Path(paper_dir)
        output_path = Path(output_dir) if output_dir else paper_path / 'humanized'
        output_path.mkdir(parents=True, exist_ok=True)

        if sections is None:
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
            input_file = paper_path / 'sections' / f'{file_prefix}.md'

            if not input_file.exists():
                input_file = paper_path / f'{file_prefix}.md'

            if input_file.exists():
                with open(input_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                result = self.humanize_section(content, section_name)
                results[section_name] = result

                # Save humanized version
                output_file = output_path / f'{file_prefix}_humanized.md'
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(result.humanized_text)

        # Generate report
        self._generate_report(results, output_path)

        return results

    def _generate_report(
        self,
        results: Dict[str, HumanizationResult],
        output_path: Path
    ):
        """Generate humanization report."""
        report_lines = [
            "# Paper Humanization Report\n",
            "## Summary\n"
        ]

        total_before = 0
        total_after = 0

        for section, result in results.items():
            total_before += result.ai_score_before
            total_after += result.ai_score_after

            report_lines.append(f"### {section}")
            report_lines.append(f"- AI Score Before: {result.ai_score_before:.1f}")
            report_lines.append(f"- AI Score After: {result.ai_score_after:.1f}")
            report_lines.append(f"- Changes: {', '.join(result.changes_made)}")
            report_lines.append("")

        n = len(results)
        if n > 0:
            report_lines.append("## Overall")
            report_lines.append(f"- Average AI Score Before: {total_before/n:.1f}")
            report_lines.append(f"- Average AI Score After: {total_after/n:.1f}")
            report_lines.append(f"- Improvement: {(total_before-total_after)/n:.1f} points")

        report_file = output_path / 'humanization_report.md'
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))


def humanize_paper(input_path: str, output_path: str = None) -> Dict:
    """Convenience function to humanize a paper."""
    humanizer = PaperHumanizer()
    return humanizer.humanize_paper(input_path, output_path)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Humanize AI-generated paper")
    parser.add_argument("--input", "-i", required=True, help="Input paper directory")
    parser.add_argument("--output", "-o", help="Output directory")
    parser.add_argument("--aggressiveness", "-a", choices=['low', 'medium', 'high'],
                       default='medium', help="Humanization aggressiveness")

    args = parser.parse_args()

    results = humanize_paper(args.input, args.output)

    print(f"Humanized {len(results)} sections:")
    for section, result in results.items():
        improvement = result.ai_score_before - result.ai_score_after
        print(f"  {section}: {result.ai_score_before:.1f} -> {result.ai_score_after:.1f} (↓{improvement:.1f})")

"""
Section Translator

Translate paper sections between languages for bilingual support.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
import re


@dataclass
class TranslationPair:
    """A pair of translated sections."""
    english: str
    chinese: str
    section_name: str


class SectionTranslator:
    """Translate paper sections between English and Chinese."""

    # Common academic term translations
    TERM_DICT = {
        # Research concepts
        'method': '方法',
        'approach': '方法',
        'framework': '框架',
        'model': '模型',
        'algorithm': '算法',
        'system': '系统',
        'experiment': '实验',
        'result': '结果',
        'conclusion': '结论',
        'introduction': '引言',
        'abstract': '摘要',
        'related work': '相关工作',
        'discussion': '讨论',

        # Common verbs
        'propose': '提出',
        'present': '展示',
        'demonstrate': '证明',
        'show': '表明',
        'analyze': '分析',
        'evaluate': '评估',
        'implement': '实现',
        'design': '设计',

        # Common adjectives
        'novel': '新颖的',
        'significant': '显著的',
        'effective': '有效的',
        'efficient': '高效的',
        'accurate': '准确的',
        'robust': '鲁棒的',
    }

    def __init__(self):
        self.cache: Dict[str, str] = {}

    def translate_section(
        self,
        content: str,
        source_lang: str = 'en',
        target_lang: str = 'zh'
    ) -> str:
        """
        Translate a paper section.

        Note: This is a placeholder that would integrate with actual
        translation APIs (DeepL, Google Translate, etc.) in production.
        """
        # For now, return content with a note
        # In production, this would call a translation API
        return f"[TRANSLATION NEEDED: {source_lang}->{target_lang}]\n{content}"

    def extract_key_terms(self, text: str) -> List[str]:
        """Extract key academic terms from text."""
        terms = []
        text_lower = text.lower()

        for term in self.TERM_DICT.keys():
            if term in text_lower:
                terms.append(term)

        return list(set(terms))

    def create_glossary(self, text: str) -> Dict[str, str]:
        """Create a glossary of terms found in text."""
        terms = self.extract_key_terms(text)
        return {term: self.TERM_DICT[term] for term in terms}

    def format_bilingual_section(
        self,
        english_content: str,
        chinese_content: str,
        format_type: str = 'sequential'
    ) -> str:
        """Format bilingual section."""
        if format_type == 'sequential':
            return f"""% ===== English Version =====
{english_content}

% ===== 中文版本 =====
{chinese_content}
"""
        elif format_type == 'parallel':
            return f"""\\begin{{multicols}}{{2}}
{english_content}
\\columnbreak
{chinese_content}
\\end{{multicols}}
"""
        else:
            return english_content


if __name__ == "__main__":
    translator = SectionTranslator()

    # Test term extraction
    text = "We propose a novel framework for trust calibration in human-AI interaction."
    terms = translator.extract_key_terms(text)
    glossary = translator.create_glossary(text)

    print("Key terms found:", terms)
    print("Glossary:", glossary)

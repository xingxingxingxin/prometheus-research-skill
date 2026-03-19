"""
Sentence and Voice Transformers

Transform text to reduce AI detection patterns.
"""

import re
import random
from typing import List, Tuple, Optional


class SentenceTransformer:
    """Transform sentences for natural variation."""

    def vary_sentence_length(self, text: str) -> str:
        """Introduce sentence length variation."""
        sentences = self._split_sentences(text)
        if not sentences:
            return text

        result = []
        prev_length = 0

        for i, sent in enumerate(sentences):
            words = sent.split()
            length = len(words)

            # Long sentence (>35 words): consider splitting
            if length > 35:
                sent = self._maybe_split_long(sent)

            # Consecutive medium-length sentences: introduce variation
            elif 15 < length < 28 and 15 < prev_length < 28:
                if random.random() > 0.5:
                    sent = self._shorten_sentence(sent)
                else:
                    # Merge with previous
                    if result:
                        result[-1] = result[-1].rstrip('.') + ', and ' + sent[0].lower() + sent[1:]
                        prev_length = length
                        continue

            result.append(sent)
            prev_length = length

        return ' '.join(result)

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        text = re.sub(r'\b(e\.g|i\.e|etc|vs|Dr|Prof)\.', r'\1<DOT>', text)
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.replace('<DOT>', '.').strip() for s in sentences if s.strip()]

    def _maybe_split_long(self, sentence: str) -> str:
        """Split long sentence at natural break points."""
        # Try splitting at conjunctions
        connectors = [', and ', ', but ', '; ', '—']

        for conn in connectors:
            if conn in sentence:
                parts = sentence.split(conn, 1)
                if len(parts) == 2 and len(parts[0].split()) > 12:
                    # Add transition after split
                    transitions = [
                        'Specifically, ', 'In particular, ',
                        'Notably, ', 'Crucially, '
                    ]
                    return parts[0] + '. ' + random.choice(transitions) + parts[1][0].upper() + parts[1][1:]

        return sentence

    def _shorten_sentence(self, sentence: str) -> str:
        """Shorten sentence by removing filler phrases."""
        fillers = [
            ('It should be noted that ', ''),
            ('It is worth mentioning that ', ''),
            ('It is worth noting that ', ''),
            ('As can be seen, ', ''),
            ('In this context, ', ''),
            (', as previously mentioned', ''),
        ]

        for filler, replacement in fillers:
            sentence = sentence.replace(filler, replacement)

        return sentence.strip()

    def vary_sentence_openings(self, text: str) -> str:
        """Vary sentence openings to avoid repetition."""
        sentences = self._split_sentences(text)
        if not sentences:
            return text

        opener_map = {
            'This study': ['Our research', 'The current work', 'We', 'Our investigation'],
            'This paper': ['Our contribution', 'This work', 'We', 'Our study'],
            'The results': ['Our findings', 'The experimental outcomes', 'The data'],
            'Our method': ['The proposed approach', 'Our framework', 'This technique'],
        }

        result = []
        opener_counts = {}

        for sent in sentences:
            for original, alternatives in opener_map.items():
                if sent.startswith(original):
                    count = opener_counts.get(original, 0)
                    if count > 0:
                        replacement = alternatives[count % len(alternatives)]
                        sent = sent.replace(original, replacement, 1)
                    opener_counts[original] = opener_counts.get(original, 0) + 1
                    break
            result.append(sent)

        return ' '.join(result)


class VoiceTransformer:
    """Transform passive to active voice."""

    PASSIVE_PATTERNS = [
        # Simple passive
        (r'(\w+) was (\w+ed) by (\w+)', r'\3 \2 \1'),
        (r'(\w+) were (\w+ed) by (\w+)', r'\3 \2 \1'),
        (r'(\w+) is (\w+ed) by (\w+)', r'\3 \2 \1'),
        (r'(\w+) are (\w+ed) by (\w+)', r'\3 \2 \1'),
        # With "the" prefix
        (r'The (\w+) was (\w+ed)', r'We \2 the \1'),
        (r'The (\w+) were (\w+ed)', r'We \2 the \1'),
        (r'The (\w+) has been (\w+ed)', r'We have \2 the \1'),
    ]

    def passive_to_active(self, text: str, conversion_rate: float = 0.7) -> str:
        """Convert passive constructions to active voice."""
        result = text

        for passive, active in self.PASSIVE_PATTERNS:
            matches = list(re.finditer(passive, result, re.IGNORECASE))
            for match in matches:
                if random.random() < conversion_rate:
                    try:
                        transformed = re.sub(passive, active, match.group(), flags=re.I)
                        result = result.replace(match.group(), transformed, 1)
                    except Exception:
                        continue

        return result

    def add_subject_variety(self, text: str) -> str:
        """Add variety to sentence subjects."""
        subject_map = {
            'This study': ['Our research', 'The current work', 'We'],
            'The results': ['Our findings', 'The experimental outcomes', 'The data'],
            'This paper': ['Our contribution', 'This work', 'We'],
            'Our approach': ['The proposed method', 'This framework', 'Our technique'],
        }

        result = text
        for original, alternatives in subject_map.items():
            # Count occurrences
            count = len(re.findall(re.escape(original), result, re.IGNORECASE))
            # Replace all but first occurrence
            for i in range(1, count):
                replacement = alternatives[i % len(alternatives)]
                result = re.sub(re.escape(original), replacement, result, count=1, flags=re.I)

        return result


class DiscourseMarkerTransformer:
    """Transform discourse markers for naturalness."""

    TRANSITION_REPLACEMENTS = {
        'Furthermore,': ['What\'s more,', 'Beyond that,', 'Adding to this,', 'Equally important,'],
        'Moreover,': ['In addition,', 'Additionally,', 'Another key point:', 'Also,'],
        'Additionally,': ['Also,', 'In addition,', 'Furthermore,'],
        'In conclusion,': ['To wrap up,', 'Ultimately,', 'In the end,', 'Finally,'],
        'To summarize,': ['In short,', 'Briefly,', 'To conclude,'],
        'It should be noted that': ['Notice that', 'Observe that', 'We note that', 'Note that'],
        'It is worth noting that': ['Notably,', 'Importantly,', 'We observe that'],
        'In this context,': ['Here,', 'In this setting,', 'In our case,'],
    }

    def vary_transitions(self, text: str) -> str:
        """Replace repetitive transitions with varied alternatives."""
        result = text
        used = {}

        for original, alternatives in self.TRANSITION_REPLACEMENTS.items():
            count = result.count(original)
            for i in range(count):
                if i > 0 or count > 2:  # Replace if repeated
                    replacement = alternatives[i % len(alternatives)]
                    result = result.replace(original, replacement, 1)

        return result


if __name__ == "__main__":
    # Test transformers
    sample = """
    The data was collected by our research team.
    The results were analyzed using standard statistical methods.
    Furthermore, our method demonstrates significant improvements.
    Moreover, the experiments were conducted in controlled conditions.
    Additionally, the performance was evaluated on multiple datasets.
    """

    st = SentenceTransformer()
    vt = VoiceTransformer()
    dt = DiscourseMarkerTransformer()

    print("=== Original ===")
    print(sample)

    print("\n=== After Voice Transformation ===")
    result = vt.passive_to_active(sample)
    print(result)

    print("\n=== After Transition Variation ===")
    result = dt.vary_transitions(result)
    print(result)

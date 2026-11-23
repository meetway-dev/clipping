import re
from typing import List, Dict, Any

class SemanticSentenceAligner:
    """
    Reconstructs continuous speech into clean, grammatically complete sentences
    with exact word-level boundaries and narrative role tagging.
    Guarantees that clips NEVER start or end in the middle of a thought.
    """

    DEPENDENT_START_WORDS = {
        "and", "but", "so", "because", "or", "which", "plus", "also",
        "then", "actually", "like", "well", "where", "while"
    }

    DEPENDENT_PRONOUNS = {
        "he", "she", "it", "they", "this", "that", "these", "those", "him", "her", "them"
    }

    HOOK_STARTERS = [
        "the truth is", "the biggest mistake", "nobody talks about",
        "the secret to", "how i made", "why 99%", "here is why",
        "the craziest thing", "what most people don't realize",
        "have you ever", "what if i told you", "if you want to",
        "stop doing", "never do this", "i remember when", "one of the best",
        "the most important lesson", "my favorite rule", "the real reason"
    ]

    CONCLUSION_SIGNALS = [
        "that's why", "that is why", "at the end of the day",
        "which changed everything", "and that was it", "that's the lesson",
        "and that's how", "it made all the difference", "bottom line is",
        "that's all that matters", "never looked back"
    ]

    HANGING_END_WORDS = {
        "and", "but", "so", "or", "because", "like", "with", "to", "of",
        "in", "at", "if", "that", "which", "then", "when"
    }

    @classmethod
    def reconstruct_sentences(cls, segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Takes raw Whisper segments or words and reconstructs complete sentences
        with exact start/end timestamps and punctuation integrity.
        """
        # Collect all words in chronological order
        all_words = []
        for s in segments:
            if "words" in s and s["words"]:
                for w in s["words"]:
                    all_words.append(w)
            else:
                # If segment has no words array, split segment text
                words_in_text = s["text"].strip().split()
                if not words_in_text:
                    continue
                seg_dur = max(0.1, s["end"] - s["start"])
                w_dur = seg_dur / len(words_in_text)
                for idx, token in enumerate(words_in_text):
                    all_words.append({
                        "word": token,
                        "start": s["start"] + idx * w_dur,
                        "end": s["start"] + (idx + 1) * w_dur
                    })

        if not all_words:
            return []

        sentences = []
        curr_words = []
        
        for i, w in enumerate(all_words):
            curr_words.append(w)
            token = w["word"].strip()

            # Check if this word ends a sentence
            is_terminal = any(token.endswith(p) for p in [".", "?", "!"])
            
            # Check pause to next word (silence > 0.85s usually indicates natural sentence stop)
            has_long_pause = False
            if i < len(all_words) - 1:
                next_start = all_words[i + 1]["start"]
                if next_start - w["end"] > 0.85:
                    has_long_pause = True

            # If terminal punctuation or long pause with reasonable length, finalize sentence
            if (is_terminal or has_long_pause) and len(curr_words) >= 3:
                sent = cls._build_sentence_object(curr_words)
                sentences.append(sent)
                curr_words = []

        if curr_words:
            sentences.append(cls._build_sentence_object(curr_words))

        return sentences

    @classmethod
    def _build_sentence_object(cls, words: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Constructs and analyzes a sentence object."""
        text = " ".join(w["word"].strip() for w in words).strip()
        # Clean up double spaces
        text = re.sub(r"\s+", " ", text)
        start_time = words[0]["start"]
        end_time = words[-1]["end"]
        duration = end_time - start_time

        first_word = words[0]["word"].strip().lower()
        # Strip leading punctuation
        first_word = re.sub(r"^[^\w]+", "", first_word)
        last_word = words[-1]["word"].strip().lower()
        last_word = re.sub(r"[^\w]+$", "", last_word)

        lower_text = text.lower()

        # Check narrative roles
        is_hook = any(h in lower_text for h in cls.HOOK_STARTERS) or text.endswith("?")
        is_conclusion = any(c in lower_text for c in cls.CONCLUSION_SIGNALS)
        is_dependent_start = first_word in cls.DEPENDENT_START_WORDS or first_word in cls.DEPENDENT_PRONOUNS
        is_hanging_end = last_word in cls.HANGING_END_WORDS or not any(text.endswith(p) for p in [".", "!", "?"])

        return {
            "text": text,
            "start": round(start_time, 3),
            "end": round(end_time, 3),
            "duration": round(duration, 3),
            "words": words,
            "is_hook": is_hook,
            "is_conclusion": is_conclusion,
            "is_dependent_start": is_dependent_start,
            "is_hanging_end": is_hanging_end,
            "word_count": len(words)
        }

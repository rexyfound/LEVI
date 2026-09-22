import re


def prepare_spoken_text(text: str, max_chars: int = 260) -> str:
    """
    Deterministically transforms full agent text into a concise, spoken-friendly format.
    - Strips markdown formatting (bold, italic, links, headers)
    - Replaces long code blocks and technical formatting with concise speech
    - Removes raw JSON or backtick expressions
    - Truncates safely at sentence boundaries if the text is excessively long.
    """
    if not text:
        return ""

    cleaned = text.strip()
    # Models sometimes return escaped line breaks instead of real newlines.
    cleaned = cleaned.replace("\\r\\n", "\n").replace("\\n", "\n")
    cleaned = re.sub(r"\bhere(?:'s| is) (?:the )?code\s*:\s*", "", cleaned, flags=re.I)

    # 1. Code is useful in the visual response but tedious and unnatural aloud.
    cleaned = re.sub(r"```[a-zA-Z0-9_-]*\n[\s\S]*?```", " I've prepared the code. ", cleaned)

    # 2. Replace inline code `...` with plain text
    cleaned = re.sub(r"`([^`]+)`", r"\1", cleaned)

    # 3. Replace markdown links [text](url) with just the text
    cleaned = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", cleaned)

    # 4. Remove HTML tags like <b>, <span>, <p>, etc.
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)

    # 5. Remove markdown headers (#, ##, ###, etc.) and bullets (*, -, >)
    cleaned = re.sub(r"^\s*[*+>-]+\s*", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"\*\*([^*]+)\*\*", r"\1", cleaned)
    cleaned = re.sub(r"\*([^*]+)\*", r"\1", cleaned)
    cleaned = re.sub(r"__([^_]+)__", r"\1", cleaned)
    cleaned = re.sub(r"_([^_]+)_", r"\1", cleaned)
    cleaned = re.sub(r"#{1,6}\s*", "", cleaned)

    # 6. Make common technical punctuation comfortable to hear.
    cleaned = cleaned.replace("→", " then ").replace("=>", " then ")
    cleaned = re.sub(r"\b([A-Za-z0-9_-]+)\.(py|js|ts|json|md|txt)\b", r"\1 dot \2", cleaned)
    cleaned = re.sub(r"\bhttps?://\S+", "", cleaned)
    cleaned = re.sub(r"\s*:\s*", ". ", cleaned)

    # 7. Normalize whitespace and remove transcript-like boilerplate.
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    cleaned = re.sub(r"^(?:here(?:'s| is) (?:the )?(?:answer|response|result)\.?\s*)", "", cleaned, flags=re.I)
    cleaned = re.sub(r"^(?:sure[,.!]?\s*)", "", cleaned, flags=re.I)

    # 8. Speak at most two natural sentences. This lowers synthesis latency and
    # keeps long technical detail in the visual response where it belongs.
    sentences = re.split(r"(?<=[.!?])\s+", cleaned)
    if len(sentences) > 2:
        cleaned = " ".join(sentences[:2]).strip()

    # 9. If text exceeds max_chars, truncate at the closest sentence boundary
    if len(cleaned) > max_chars:
        # Look for sentence endings (., !, ?) before max_chars
        cutoff = cleaned[:max_chars]
        last_period = max(cutoff.rfind(". "), cutoff.rfind("! "), cutoff.rfind("? "))
        if last_period > int(max_chars * 0.4):
            cleaned = cutoff[: last_period + 1].strip()
        else:
            cleaned = cutoff.rstrip() + "..."

    return cleaned

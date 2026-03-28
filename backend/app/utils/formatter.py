"""
Formatter utility — cleans and structures LLM output.
"""
import re


def clean_llm_text(text: str) -> str:
    """Remove common LLM artefacts and normalise whitespace."""
    # Strip leading/trailing whitespace
    text = text.strip()
    # Remove excessive blank lines (>2 consecutive)
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Remove markdown code fence artefacts that leaked out
    text = re.sub(r"^```[a-z]*\n?", "", text, flags=re.MULTILINE)
    text = re.sub(r"\n?```$", "", text, flags=re.MULTILINE)
    return text.strip()


def truncate(text: str, max_chars: int = 4000) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n\n[… truncated]"


def severity_badge(severity: str) -> str:
    colours = {
        "critical": "🔴",
        "high": "🟠",
        "medium": "🟡",
        "low": "🟢",
        "info": "⚪",
    }
    return colours.get(severity.lower(), "⚪")

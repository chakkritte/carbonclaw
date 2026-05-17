"""Task classification based on keyword matching."""

from __future__ import annotations

import re
from carbonclaw.core.models import TaskType


def classify_task(prompt: str) -> TaskType:
    """Classify a task based on keywords in the prompt."""
    prompt_lower = prompt.lower()

    # CODING: keywords like "write", "refactor", "debug", "implement", "function", "class", file extensions
    coding_keywords = [
        r"\bwrite\b", r"refactor", r"debug", r"implement", r"\bfunction\b", r"\bclass\b",
        r"\.py\b", r"\.js\b", r"\.ts\b", r"\.go\b", r"\.rs\b", r"\.c\b", r"\.cpp\b", r"\.h\b",
        r"\.java\b", r"\.html\b", r"\.css\b", r"coding", r"code", r"programming"
    ]
    if any(re.search(kw, prompt_lower) for kw in coding_keywords):
        return TaskType.CODING

    # RESEARCH: keywords like "search", "find information", "summarize", "research", "what is"
    research_keywords = [
        r"search", r"find information", r"summarize", r"research", r"what is", r"who is",
        r"explain", r"how does", r"tell me about", r"deep dive", r"analyze"
    ]
    if any(re.search(kw, prompt_lower) for kw in research_keywords):
        return TaskType.RESEARCH

    # SLIDES: keywords like "slide", "presentation", "pptx", "deck", "PowerPoint"
    slides_keywords = [
        r"slide", r"presentation", r"pptx", r"deck", r"powerpoint", r"keynote"
    ]
    if any(re.search(kw, prompt_lower) for kw in slides_keywords):
        return TaskType.SLIDES

    return TaskType.GENERAL

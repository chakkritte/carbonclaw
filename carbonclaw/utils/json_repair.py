"""JSON repair utility for malformed LLM outputs."""

from __future__ import annotations

import json
import re
from typing import Any, TYPE_CHECKING

import structlog

from carbonclaw.core.errors import ToolCallParseError

if TYPE_CHECKING:
    from carbonclaw.core.base import BaseProvider

logger = structlog.get_logger(__name__)


async def repair_json(raw: str, provider: BaseProvider | None = None, model: str | None = None) -> Any:
    """Attempt to repair and parse malformed JSON strings.
    
    1. Standard json.loads()
    2. Heuristic cleaning (markdown fences, trailing commas, unquoted keys)
    3. LLM-based correction (if provider and model are available)
    """
    # 1. Standard try
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # 2. Heuristic cleaning
    cleaned = raw.strip()
    
    # Remove markdown fences
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\n", "", cleaned)
        cleaned = re.sub(r"\n```$", "", cleaned)
        cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Fix trailing commas in objects and arrays
    cleaned = re.sub(r",\s*([\]}])", r"\1", cleaned)
    
    # Try to fix unquoted keys (basic attempt)
    cleaned = re.sub(r'([{,])\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', cleaned)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # 3. LLM-based correction
    if provider and model:
        logger.info("json_repair.llm_fallback", raw=raw[:100])
        from carbonclaw.core.models import CompletionRequest, Message
        prompt = f"Fix this JSON to be valid. Return ONLY the fixed JSON, no preamble or markdown fences:\n{raw}"
        try:
            response = await provider.complete(
                CompletionRequest(
                    messages=[Message(role="user", content=prompt)],
                    model=model,
                    temperature=0.0, # Deterministic
                )
            )
            fixed_raw = response.message.content or ""
            # Strip fences from LLM output too just in case
            fixed_raw = re.sub(r"^```(?:json)?\n", "", fixed_raw)
            fixed_raw = re.sub(r"\n```$", "", fixed_raw).strip()
            
            return json.loads(fixed_raw)
        except Exception as e:
            logger.warning("json_repair.llm_fallback_failed", error=str(e))

    raise ToolCallParseError(f"Failed to parse or repair JSON arguments: {raw[:200]}")

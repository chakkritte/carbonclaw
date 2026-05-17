"""Custom exceptions for CarbonClaw."""

from __future__ import annotations


class CarbonClawError(Exception):
    """Base exception for all CarbonClaw errors."""


class ToolCallParseError(CarbonClawError):
    """Raised when tool call arguments cannot be parsed as valid JSON."""

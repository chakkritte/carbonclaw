"""Unit tests for task classification and smart routing."""

from __future__ import annotations

import pytest
from carbonclaw.core.models import TaskType
from carbonclaw.routing.classifier import classify_task
from carbonclaw.core.router import SmartRouter, RoutingStrategy
from carbonclaw.config.settings import CarbonClawConfig


def test_classify_task() -> None:
    # CODING
    assert classify_task("write a python script") == TaskType.CODING
    assert classify_task("refactor app.py") == TaskType.CODING
    assert classify_task("debug the login function") == TaskType.CODING
    
    # RESEARCH
    assert classify_task("what is quantum computing?") == TaskType.RESEARCH
    assert classify_task("summarize this article") == TaskType.RESEARCH
    assert classify_task("research the best practices for FastAPI") == TaskType.RESEARCH
    
    # SLIDES
    assert classify_task("create a slide deck for the project") == TaskType.SLIDES
    assert classify_task("update the presentation slides") == TaskType.SLIDES
    
    # GENERAL
    assert classify_task("hello, how are you?") == TaskType.GENERAL


def test_router_task_aware_routing() -> None:
    config = CarbonClawConfig(
        routing_models={
            "coding": "qwen-coding",
            "research": "qwen-research",
            "slides": "qwen-slides",
            "general": "llama-general",
        },
        default_provider="openai"
    )
    router = SmartRouter(config)
    
    # Ensure stats are healthy for test
    for s in router.stats.values():
        s.is_healthy = True

    # 1. Coding task (Simple) -> local task model
    p, m, t = router.route("write code", strategy=RoutingStrategy.SUSTAINABILITY)
    assert t == TaskType.CODING
    assert p == "ollama"
    assert m == "qwen-coding"
    
    # 2. Research task (Simple) -> local task model
    p, m, t = router.route("research AI", strategy=RoutingStrategy.SUSTAINABILITY)
    assert t == TaskType.RESEARCH
    assert p == "ollama"
    assert m == "qwen-research"
    
    # 3. High complexity -> cloud (forced)
    # Use a task that is guaranteed to be complex (very long)
    complex_task = "refactor " + ("x" * 5000)
    p, m, t = router.route(complex_task, strategy=RoutingStrategy.SUSTAINABILITY)
    assert t == TaskType.CODING
    assert p == "openai"

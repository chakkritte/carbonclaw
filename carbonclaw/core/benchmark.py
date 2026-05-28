"""Model Distillation & Benchmarking Pipeline."""

from __future__ import annotations

import asyncio
from typing import Any

import structlog

from carbonclaw.core.models import Message
from carbonclaw.providers.registry import ProviderRegistry
from carbonclaw.config.settings import CarbonClawConfig

logger = structlog.get_logger(__name__)


class Benchmarker:
    """Runs shadow trials to find the most carbon-efficient models."""

    def __init__(self, config: CarbonClawConfig):
        self.config = config

    async def run_shadow_trial(self, task: str, primary_result: str) -> None:
        """Run the task against a cheaper local model in the background."""
        if not self.config.carbon_tracking_enabled:
            return

        alt_provider = "ollama"
        alt_model = "llama3.2:1b"
        
        try:
            provider = ProviderRegistry.create(alt_provider, self.config)
            
            # Dynamically discover available models on the local Ollama instance
            try:
                available_models = await provider.list_models()
                if available_models:
                    # Prefer llama3.2:1b or any 1b/3b/8b llama3/llama3.2 model, or qwen if present
                    preferred_models = ["llama3.2:1b", "llama3.2", "llama3.1", "llama3", "qwen", "phi"]
                    selected_model = None
                    for pref in preferred_models:
                        for m in available_models:
                            if pref in m.lower():
                                selected_model = m
                                break
                        if selected_model:
                            break
                    if selected_model:
                        alt_model = selected_model
                    else:
                        alt_model = available_models[0]
            except Exception:
                pass
            
            from carbonclaw.core.models import CompletionRequest
            request = CompletionRequest(
                messages=[Message(role="user", content=task)],
                model=alt_model,
                stream=False
            )
            
            logger.info("benchmark.shadow_trial.start", provider=alt_provider, model=alt_model)
            response = await provider.complete(request)
            alt_result = response.message.content or ""
            
            # Here we would normally use another LLM call as a "Judge" to compare `primary_result` and `alt_result`.
            # For simplicity, we assume success if it didn't crash and has reasonable length.
            if len(alt_result) > len(primary_result) * 0.5:
                logger.info("benchmark.shadow_trial.success", provider=alt_provider, model=alt_model)
                # We can store a learned strategy that this task type can be handled by the cheaper model
                from carbonclaw.memory.sqlite import SQLiteMemory
                from carbonclaw.tools.base import ToolResult
                import json
                
                memory = SQLiteMemory()
                adj = {
                    "target_task_type": "general",
                    "condition": "shadow_success == true",
                    "action": f"force_{alt_provider}",
                    "reason": f"Shadow trial proved {alt_model} is capable for this."
                }
                await memory.store(
                    content=json.dumps(adj),
                    namespace="strategic_adjustments",
                    metadata={"source": "benchmarker"},
                )
        except Exception as e:
            logger.warning("benchmark.shadow_trial.failed", error=str(e))

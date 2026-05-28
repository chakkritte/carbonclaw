"""Llama.cpp local provider adapter using llama-cpp-python."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

import structlog
from carbonclaw.core.base import BaseProvider
from carbonclaw.core.models import (
    CompletionRequest,
    CompletionResponse,
    Message,
    ProviderInfo,
    StreamChunk,
)
from carbonclaw.providers.base import ProviderError

logger = structlog.get_logger()


class LlamaCppProvider(BaseProvider):
    """Local GGUF provider utilizing llama-cpp-python directly in-process."""

    def __init__(
        self,
        model_path: str = "Llama-3.2-1B-Instruct-Q4_K_M.gguf",
        n_ctx: int = 4096,
        n_gpu_layers: int = -1,  # Auto detect GPU
    ) -> None:
        super().__init__({
            "model_path": model_path,
            "n_ctx": n_ctx,
            "n_gpu_layers": n_gpu_layers,
        })
        self.model_path = model_path
        self.n_ctx = n_ctx
        self.n_gpu_layers = n_gpu_layers
        self._llm: Any = None
        
        self.info = ProviderInfo(
            name="llamacpp",
            supports_streaming=True,
            supports_tools=False,
            supports_vision=False,
            supports_embeddings=False,
            default_model="Llama-3.2-1B-Instruct-Q4_K_M",
            requires_api_key=False,
            base_url="local://llamacpp",
        )

    def _get_llm(self) -> Any:
        if self._llm is not None:
            return self._llm

        try:
            from llama_cpp import Llama
        except ImportError as e:
            raise ProviderError(
                "llama-cpp-python is not installed. Please install it using the installer script or: "
                "pip install llama-cpp-python"
            ) from e

        # Resolve/download model path
        resolved_path = self._ensure_model_downloaded()
        
        # Detect CUDA if n_gpu_layers is -1 (auto)
        gpu_layers = self.n_gpu_layers
        if gpu_layers == -1:
            import shutil
            has_cuda = shutil.which("nvidia-smi") is not None
            gpu_layers = -1 if has_cuda else 0
            
        logger.info("llamacpp.loading_model", path=resolved_path, gpu_layers=gpu_layers)
        self._llm = Llama(
            model_path=resolved_path,
            n_ctx=self.n_ctx,
            n_gpu_layers=gpu_layers,
            verbose=False,
        )
        return self._llm

    def _ensure_model_downloaded(self) -> str:
        path = Path(self.model_path)
        if path.exists():
            return str(path)

        from carbonclaw.config.settings import CarbonClawConfig
        model_dir = CarbonClawConfig.user_dir() / "models"
        model_dir.mkdir(parents=True, exist_ok=True)
        
        target_path = model_dir / Path(self.model_path).name
        if target_path.exists():
            return str(target_path)

        # Download the model
        import urllib.request
        from rich.console import Console
        from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, DownloadColumn
        
        console = Console()
        url = f"https://huggingface.co/bartowski/Llama-3.2-1B-Instruct-GGUF/resolve/main/{Path(self.model_path).name}"
        console.print(f"📥 [bold cyan]Downloading {Path(self.model_path).name} (approx. 1.2GB) to local cache...[/bold cyan]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            DownloadColumn(),
            transient=True
        ) as progress:
            task = progress.add_task("Downloading model...", total=None)
            
            def reporthook(count: int, block_size: int, total_size: int) -> None:
                if total_size > 0:
                    progress.update(task, total=total_size, completed=count * block_size)
                    
            urllib.request.urlretrieve(url, str(target_path), reporthook)
            
        console.print("✅ [bold green]Model downloaded successfully![/bold green]")
        return str(target_path)

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        llm = self._get_llm()
        
        messages = [{"role": msg.role, "content": msg.content or ""} for msg in request.messages]
        
        # Execute chat completion sync in executor
        loop = asyncio.get_event_loop()
        resp = await loop.run_in_executor(
            None,
            lambda: llm.create_chat_completion(
                messages=messages,
                temperature=request.temperature or 0.7,
                max_tokens=request.max_tokens or 2048,
                stream=False,
            )
        )
        
        choice = resp["choices"][0]
        content = choice["message"]["content"]
        
        return CompletionResponse(
            message=Message(role="assistant", content=content),
            model=request.model or self.model_path,
        )

    async def stream(self, request: CompletionRequest) -> AsyncIterator[StreamChunk]:
        llm = self._get_llm()
        
        messages = [{"role": msg.role, "content": msg.content or ""} for msg in request.messages]
        
        # Stream in executor
        loop = asyncio.get_event_loop()
        stream_generator = await loop.run_in_executor(
            None,
            lambda: llm.create_chat_completion(
                messages=messages,
                temperature=request.temperature or 0.7,
                max_tokens=request.max_tokens or 2048,
                stream=True,
            )
        )
        
        def _get_next_chunk(gen: Any) -> Any:
            try:
                return next(gen)
            except StopIteration:
                return None

        while True:
            chunk = await loop.run_in_executor(None, _get_next_chunk, stream_generator)
            if chunk is None:
                break
            
            delta = chunk["choices"][0].get("delta", {})
            text = delta.get("content", "")
            if text:
                yield StreamChunk(text=text)

    async def list_models(self) -> list[str]:
        """Return the locally configured GGUF model path."""
        return [self.model_path]

"""Textual TUI for CarbonClaw full-screen chat interface.

Future: run with ``carbonclaw tui`` command.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import structlog
from textual.app import App, ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.reactive import reactive
from textual.widgets import Footer, Header, Input, Markdown, Static

from carbonclaw.config.settings import CarbonClawConfig
from carbonclaw.core.models import CompletionRequest, Message, StreamChunk, ToolCall
from carbonclaw.memory.sqlite import SQLiteMemory
from carbonclaw.providers.registry import ProviderRegistry
from carbonclaw.telemetry.carbon import CarbonStore
from carbonclaw.tools.base import ToolRegistry
from carbonclaw.tools.file import FilePatchTool, FileReadTool, FileWriteTool
from carbonclaw.tools.git import GitTool
from carbonclaw.tools.shell import ShellTool

logger = structlog.get_logger()


class ChatMessage(Static):
    """A single chat message widget."""

    DEFAULT_CSS = """
    ChatMessage {
        padding: 1;
        margin: 0 1;
    }
    ChatMessage.user {
        color: $text-accent;
    }
    ChatMessage.assistant {
        color: $text;
    }
    ChatMessage.tool {
        color: $text-muted;
        background: $surface-darken-1;
    }
    """

    def __init__(self, role: str, content: str) -> None:
        super().__init__()
        self.role = role
        self.content = content
        self.add_class(role)

    def compose(self) -> ComposeResult:
        if self.role == "assistant":
            yield Markdown(str(self.content))
        else:
            yield Static(f"[{self.role}] {self.content}")


class EmissionTrackerWidget(Static):
    """Widget to display aggregated carbon emissions."""

    emissions = reactive(0.0)

    def on_mount(self) -> None:
        self.set_interval(5, self.update_emissions)
        self.update_emissions()

    def update_emissions(self) -> None:
        store = CarbonStore()
        self.emissions = store.total_emissions()

    def render(self) -> str:
        return f"🌱 [bold green]CO2: {self.emissions:.6f} kg[/bold green]"


class CarbonClawApp(App[None]):
    """Full-screen Textual TUI for CarbonClaw."""

    TITLE = "CarbonClaw"
    SUB_TITLE = "AI-native runtime"
    CSS = """
    Screen {
        layout: vertical;
    }
    #chat-container {
        height: 1fr;
        border: solid $primary;
    }
    #input-container {
        height: auto;
        dock: bottom;
        align: middle;
    }
    #chat-input {
        width: 1fr;
    }
    #carbon-tracker {
        width: auto;
        padding: 1 2;
    }
    Input {
        margin: 1;
    }
    """

    messages: reactive[list[Message]] = reactive([])

    def __init__(self, provider_name: str | None = None, model: str | None = None) -> None:
        super().__init__()
        config = CarbonClawConfig()
        self.provider_name = provider_name or config.default_provider
        self.model = model or config.default_model or "llama3.2"
        self._initialized = False

    async def _init_backend(self) -> None:
        if self._initialized:
            return
        self.provider = ProviderRegistry.create(self.provider_name)
        self.memory = SQLiteMemory()
        self.tools = ToolRegistry()
        self.tools.register(ShellTool())
        self.tools.register(FileReadTool())
        self.tools.register(FileWriteTool())
        self.tools.register(FilePatchTool())
        self.tools.register(GitTool())
        self._initialized = True

    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll(id="chat-container"):
            yield ChatMessage("assistant", "Welcome to CarbonClaw. Type a message to begin.")
        with Horizontal(id="input-container"):
            yield Input(placeholder="Type a message...", id="chat-input")
            yield EmissionTrackerWidget(id="carbon-tracker")
        yield Footer()

    async def on_mount(self) -> None:
        await self._init_backend()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id != "chat-input":
            return
        text = event.value.strip()
        if not text:
            return
        event.input.value = ""

        container = self.query_one("#chat-container", VerticalScroll)
        container.mount(ChatMessage("user", text))

        if text.lower() in ("exit", "quit", "/exit"):
            self.exit()
            return

        await self._handle_user_message(text, container)

    async def _handle_user_message(self, text: str, container: Any) -> None:
        system_msg = Message(
            role="system",
            content=(
                "You are CarbonClaw, an AI software engineering assistant. "
                "You have access to tools for file operations, shell execution, and git."
            ),
        )
        messages = [system_msg] + self.messages + [Message(role="user", content=text)]

        # Single-turn streaming response for TUI MVP
        content_parts: list[str] = []
        tool_calls: list[ToolCall] = []
        current_tool: dict[str, Any] | None = None

        async for chunk in self.provider.stream(
            CompletionRequest(
                messages=messages,
                model=self.model,
                tools=self.tools.definitions(),
            )
        ):
            if chunk.content:
                content_parts.append(chunk.content)
            if chunk.tool_call:
                tc = chunk.tool_call
                if tc.is_start:
                    current_tool = {
                        "id": tc.id or "",
                        "name": tc.name or "",
                        "arguments": "",
                    }
                elif tc.arguments_delta:
                    if current_tool is not None:
                        current_tool["arguments"] += tc.arguments_delta
                elif tc.is_end:
                    if current_tool is not None:
                        import json

                        try:
                            args = json.loads(current_tool["arguments"])
                        except json.JSONDecodeError:
                            args = {}
                        tool_calls.append(
                            ToolCall(
                                id=current_tool["id"],
                                name=current_tool["name"],
                                arguments=args,
                            )
                        )
                        current_tool = None

        # Flush dangling tool call
        if current_tool is not None:
            import json

            try:
                args = json.loads(current_tool["arguments"])
            except json.JSONDecodeError:
                args = {}
            tool_calls.append(
                ToolCall(
                    id=current_tool["id"],
                    name=current_tool["name"],
                    arguments=args,
                )
            )

        assistant_content = "".join(content_parts)
        assistant_msg = Message(
            role="assistant",
            content=assistant_content or None,
            tool_calls=tool_calls or None,
        )

        # Execute tools
        if tool_calls:
            tool_results: list[Message] = []
            for call in tool_calls:
                result = await self.tools.execute(call.name, call.arguments)
                tool_results.append(
                    Message(
                        role="tool",
                        content=result.content,
                        tool_call_id=call.id,
                        name=call.name,
                    )
                )
                container.mount(
                    ChatMessage("tool", f"[{call.name}] {result.content[:500]}")
                )
            messages = messages + [assistant_msg] + tool_results
            # Re-run for final response
            final_parts: list[str] = []
            async for chunk in self.provider.stream(
                CompletionRequest(
                    messages=messages,
                    model=self.model,
                    tools=self.tools.definitions(),
                )
            ):
                if chunk.content:
                    final_parts.append(chunk.content)
            assistant_content = "".join(final_parts)
            assistant_msg = Message(
                role="assistant",
                content=assistant_content or None,
            )

        container.mount(ChatMessage("assistant", assistant_content or "..."))
        self.messages = self.messages + [Message(role="user", content=text), assistant_msg]
        await self.memory.store(text, namespace="tui")

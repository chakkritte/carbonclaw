# CarbonClaw Documentation

Detailed guide for architecture, advanced usage, and configuration.

## Table of Contents
1. [Architecture](#architecture)
2. [Advanced Usage](#advanced-usage)
3. [Model Context Protocol (MCP)](#model-context-protocol-mcp)
4. [Docker Sandbox](#docker-sandbox)
5. [Vector Memory](#vector-memory)
6. [Agent Snapshots](#agent-snapshots)
7. [Worker Pools](#worker-pools)
8. [Distributed Runtime](#distributed-runtime)
9. [Plugin System](#plugin-system)

---

## Architecture

CarbonClaw is built with a modular, async-first architecture:

```
carbonclaw/
├── cli/           # Typer + Rich terminal interface (chat, run, plan, doctor)
├── core/          # Shared Pydantic models, base classes, async event bus
├── context/       # Token budgeting, summarization, sliding window trimming
├── providers/     # LLM adapter layer (OpenAI, Anthropic, Gemini, Ollama, etc.)
├── tools/         # Tool runtime (shell, file, git, browser)
├── memory/        # SQLite-backed persistent memory
├── vector/        # ChromaDB semantic memory (optional)
├── agents/        # ReAct agents + Supervisor orchestration
├── sandbox/       # Docker-based command execution sandbox
├── distributed/   # Serialization, RPC, priority task queue
├── plugins/       # Dynamic plugin discovery via entry points
├── ui/            # Textual full-screen TUI + streaming display
├── web/           # FastAPI web dashboard
├── workers/       # Remote agent worker pools
├── config/        # Layered configuration system
└── tests/         # pytest unit tests
```

---

## Advanced Usage

### Multi-Agent Workflows

Use the Supervisor to orchestrate complex pipelines:

```python
from carbonclaw.agents.supervisor import SupervisorAgent
import asyncio

async def main():
    supervisor = await SupervisorAgent.create_default("openai")
    result = await supervisor.run_workflow(
        "Add pagination to the API endpoints",
        auto_plan=True,
        auto_review=True,
    )
    print(result)

asyncio.run(main())
```

### Context Management

Token budgeting and conversation summarization are handled automatically by the `ContextManager`.

---

## Model Context Protocol (MCP)

CarbonClaw supports external tools via MCP. Configure them in your `config.toml`:

```toml
[mcp_servers.filesystem]
transport = "stdio"
command = "npx"
args = ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/search"]
```

**Ollama Support**: When using the `ollama` provider, CarbonClaw automatically connects to the [ollama-web-tools-mcp](https://github.com/chakkritte/ollama-web-tools-mcp) server if found.

---

## Docker Sandbox

Execute commands in isolated containers for security:

```python
from carbonclaw.sandbox.docker import DockerSandbox

sandbox = DockerSandbox(
    image="python:3.12-slim",
    timeout=60,
    memory_limit="512m",
)

result = await sandbox.execute(command="python -c 'print(2+2)'")
```

---

## Vector Memory

Enable semantic search with ChromaDB:

```python
from carbonclaw.vector.chroma import ChromaMemory

memory = ChromaMemory(path="./chroma_data")
await memory.store("JWT tokens are used for auth", namespace="docs")
results = await memory.retrieve(query="How to auth?", namespace="docs")
```

---

## Agent Snapshots

Save and restore execution state:

```python
from carbonclaw.agents.snapshot import AgentSnapshot
snapshot = AgentSnapshot()
id = snapshot.save(state, agent_name="coding")
```

---

## Worker Pools

Scale CarbonClaw using remote workers and a priority task queue.

---

## Distributed Runtime

Provides building blocks for multi-node deployments:
- **StateSerializer**: State persistence.
- **RPC Layer**: Remote agent calls.
- **TaskQueue**: Priority-based scheduling.

---

## Plugin System

Create plugins by implementing `CarbonClawPlugin` and registering via `[project.entry-points."carbonclaw.plugins"]`.

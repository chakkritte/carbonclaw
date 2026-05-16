# Sena 🤖

Sena is an AI-native runtime for autonomous software engineering, multi-agent collaboration, and self-evolving research workflows.

## 🚀 One-Line Installation

```bash
curl -fsSL https://raw.githubusercontent.com/chakkritte/sena/main/install.sh | bash
```
*Requires Python 3.12+, Git, and uv.*

## 🌟 Key Features

- **Multi-Agent Orchestration**: Automated plan -> code -> test -> review -> docs workflows.
- **Self-Evolution**: Agents learn from interactions and autonomously improve their strategies.
- **Browser Automation**: Full web interaction and scraping via Playwright.
- **Strictly Typed**: 100% Mypy compliance for enterprise reliability.
- **Observability**: Built-in OpenTelemetry tracing for monitoring execution paths and token costs.
- **Human-in-the-Loop**: Mandatory approval gates for sensitive system operations.

## 🛠 Quick Start

```bash
# Initialize your custom agent persona
sena init

# Start an interactive chat (use !command for shell escape)
sena chat

# Run a one-shot engineering task
sena run "Refactor sena/core/base.py to use Protocol instead of ABC"

# Setup your preferred model/provider
sena models
```

## 📖 Documentation

For detailed guides, architecture, and advanced usage, see [docs.md](./docs.md).

## 📅 Roadmap

- [x] Multi-agent (Plan/Code/Review/QA/Docs)
- [x] Human-in-the-Loop & Self-Evolution
- [x] Browser Automation & OpenTelemetry
- [ ] **Phase 4: Event-Driven CI/CD Workflows**
- [ ] **Phase 5: Advanced Graph Memory**
- [ ] **Phase 6: IDE Integration (LSP)**

## License

MIT

#!/bin/bash
set -e

# CarbonClaw One-Line Installer
# Requires: python3.12+, git, uv

echo "🤖 Installing CarbonClaw..."

# 1. Clone repository
if [ ! -d "carbonclaw" ]; then
    git clone https://github.com/chakkritte/carbonclaw.git
    cd carbonclaw
else
    cd carbonclaw
    git pull origin main
fi

# 2. Check for uv
if ! command -v uv &> /dev/null; then
    echo "❌ 'uv' not found. Please install it first: https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
fi

# 3. Setup environment and dependencies
echo "📦 Syncing dependencies..."
uv sync --all-extras

# 3.1 Install globally (optional but recommended for global path access)
echo "🌍 Installing 'carbonclaw' command globally..."
uv tool install . --force

# 4. Install playwright browsers
echo "🌐 Installing browser binaries..."
uv run playwright install chromium

# 5. Done
echo ""
echo "✅ CarbonClaw installed successfully!"
echo "🚀 Run 'uv run carbonclaw chat' to start."

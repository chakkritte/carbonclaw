#!/bin/bash
set -e

# Sena One-Line Installer
# Requires: python3.12+, git, uv

echo "🤖 Installing Sena..."

# 1. Clone repository
if [ ! -d "sena" ]; then
    git clone https://github.com/chakkritte/sena.git
    cd sena
else
    cd sena
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

# 4. Install playwright browsers
echo "🌐 Installing browser binaries..."
uv run playwright install chromium

# 5. Done
echo ""
echo "✅ Sena installed successfully!"
echo "🚀 Run 'uv run sena chat' to start."

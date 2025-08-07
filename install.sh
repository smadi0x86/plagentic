#!/bin/bash
# Plagentic Installation Script

echo "Installing Plagentic CLI..."

# Install with uv
uv pip install -e .

# Create symbolic link for easy access
VENV_BIN="$(pwd)/.venv/bin/plagentic"
LOCAL_BIN="$HOME/.local/bin/plagentic"

# Ensure ~/.local/bin exists and is in PATH
mkdir -p "$HOME/.local/bin"

# Create symlink if venv binary exists
if [ -f "$VENV_BIN" ]; then
    ln -sf "$VENV_BIN" "$LOCAL_BIN"
    echo "Plagentic CLI installed successfully!"
    echo "Binary linked to: $LOCAL_BIN"
    echo ""
    echo "Usage:"
    echo "  plagentic list        # List available teams"
    echo "  plagentic run <team>  # Run a team"
    echo ""
    echo "Note: Make sure ~/.local/bin is in your PATH"
    echo "Add this to your ~/.bashrc or ~/.zshrc:"
    echo "export PATH=\"\$HOME/.local/bin:\$PATH\""
else
    echo "Installation failed - binary not found"
    exit 1
fi

#!/bin/zsh
set -u
cd "/Users/cristrein/tradingview-mcp/alert-bridge" || exit 1
export PATH="$HOME/.local/bin:/usr/local/bin:$PATH"
exec python3 -u e1_detector.py

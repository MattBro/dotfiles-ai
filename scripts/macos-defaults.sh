#!/usr/bin/env bash
# macos-defaults.sh — apply personal macOS system defaults.
#
# Run manually after setting up a new Mac:
#   ./scripts/macos-defaults.sh
#
# Idempotent: re-running just rewrites the same values.

set -euo pipefail

if [[ "$(uname)" != "Darwin" ]]; then
    echo "skip: not macOS"
    exit 0
fi

# Window tiling shortcuts (Sequoia+).
# Binds Ctrl+Opt+Arrow to the Window > Move & Resize > Left/Right/Top/Bottom menu items
# in every app. Modifier chars: @=Cmd, ~=Opt, ^=Ctrl, $=Shift.
defaults write -g NSUserKeyEquivalents -dict-add "Left"   "^~\\U2190"
defaults write -g NSUserKeyEquivalents -dict-add "Right"  "^~\\U2192"
defaults write -g NSUserKeyEquivalents -dict-add "Top"    "^~\\U2191"
defaults write -g NSUserKeyEquivalents -dict-add "Bottom" "^~\\U2193"

killall cfprefsd 2>/dev/null || true

echo "ok: macOS defaults applied. Restart any open app to pick up the new menu shortcuts."

#!/usr/bin/env bash
# Build, sign, and register ClaudeResume.app — the macOS handler that opens a
# new Ghostty tab and runs `claude --resume <id>` when a *.clauderesume file is
# opened. Idempotent: safe to re-run. Does NOT grant Automation permission —
# that's a one-time interactive macOS grant the user does after first launch.
set -euo pipefail

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$SRC_DIR/claude-resume-handler.applescript"
APP="$HOME/Applications/ClaudeResume.app"
BUNDLE_ID="com.nava.clauderesume"   # keep stable: TCC + Launch Services key on this
PLIST="$APP/Contents/Info.plist"
PB=/usr/libexec/PlistBuddy
LSR=/System/Library/Frameworks/CoreServices.framework/Versions/A/Frameworks/LaunchServices.framework/Versions/A/Support/lsregister

[ "$(uname)" = "Darwin" ] || { echo "✗ macOS only."; exit 1; }
command -v ghostty >/dev/null 2>&1 || [ -d /Applications/Ghostty.app ] || echo "⚠ Ghostty not found — install Ghostty 1.3.0+."

mkdir -p "$HOME/Applications" "$HOME/.claude/pr-resume"

echo "→ compiling $APP"
rm -rf "$APP"
osacompile -o "$APP" "$SRC"

echo "→ declaring .clauderesume document type"
$PB -c "Set :CFBundleIdentifier $BUNDLE_ID" "$PLIST" 2>/dev/null || $PB -c "Add :CFBundleIdentifier string $BUNDLE_ID" "$PLIST"
$PB -c "Add :CFBundleDocumentTypes array" "$PLIST" 2>/dev/null || true
$PB -c "Add :CFBundleDocumentTypes:0 dict" "$PLIST"
$PB -c "Add :CFBundleDocumentTypes:0:CFBundleTypeName string ClaudeResume" "$PLIST"
$PB -c "Add :CFBundleDocumentTypes:0:CFBundleTypeRole string Viewer" "$PLIST"
$PB -c "Add :CFBundleDocumentTypes:0:LSHandlerRank string Owner" "$PLIST"
$PB -c "Add :CFBundleDocumentTypes:0:CFBundleTypeExtensions array" "$PLIST"
$PB -c "Add :CFBundleDocumentTypes:0:CFBundleTypeExtensions:0 string clauderesume" "$PLIST"

echo "→ ad-hoc code-signing (stable identity for TCC)"
codesign --force --deep -s - "$APP"

echo "→ registering with Launch Services"
"$LSR" -f "$APP"

echo "✓ ClaudeResume.app built at $APP"
echo "  Next: trigger the one-time Automation grant (see setup skill)."

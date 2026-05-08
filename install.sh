#!/usr/bin/env bash
# install.sh — symlink dotfiles-ai contents into ~/.claude/
#
# Backs up existing files into ~/.claude/backups/<timestamp>/, then creates symlinks.
# Commands not managed by this repo (e.g. ~/.claude/commands/sandbox.md) are left alone.
#
# Usage:
#   ./install.sh                     install everything (default)
#   ./install.sh --claude-md-only    only CLAUDE.md
#   ./install.sh --commands-only     only commands/
#   ./install.sh --skills-only       only skills/
#   ./install.sh --status-line-only  only status-line.sh
#   ./install.sh --uninstall         remove symlinks managed by this repo

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_DIR="$HOME/.claude"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_DIR="$CLAUDE_DIR/backups/$TIMESTAMP"

INSTALL_CLAUDE_MD=true
INSTALL_COMMANDS=true
INSTALL_SKILLS=true
INSTALL_STATUS_LINE=true
UNINSTALL=false

# Colour helpers — no-op if not a tty
if [ -t 1 ]; then
    GREEN=$'\033[0;32m'; BLUE=$'\033[0;34m'; YELLOW=$'\033[0;33m'; RED=$'\033[0;31m'; NC=$'\033[0m'
else
    GREEN=''; BLUE=''; YELLOW=''; RED=''; NC=''
fi
info()    { printf "%s[info]%s %s\n" "$BLUE"   "$NC" "$*"; }
success() { printf "%s[ok]%s %s\n"   "$GREEN"  "$NC" "$*"; }
warn()    { printf "%s[warn]%s %s\n" "$YELLOW" "$NC" "$*"; }
err()     { printf "%s[err]%s %s\n"  "$RED"    "$NC" "$*" >&2; }

show_help() {
    cat <<'EOF'
Usage: ./install.sh [OPTIONS]

Install dotfiles-ai by symlinking into ~/.claude/.

Options:
  --claude-md-only    Install only CLAUDE.md and the claude/ subdir
  --commands-only     Install only commands/
  --skills-only       Install only skills/
  --status-line-only  Install only status-line.sh
  --uninstall         Remove symlinks managed by this repo
  -h, --help          Show this help

Notes:
  - Existing files are backed up to ~/.claude/backups/<timestamp>/ before being replaced.
  - Files in ~/.claude/commands/ that aren't in this repo (e.g. sandbox.md) are left untouched.
  - The CLAUDE.md root file uses @-imports to load files from the symlinked claude/ subdir.
EOF
}

while [ $# -gt 0 ]; do
    case "$1" in
        --claude-md-only)   INSTALL_CLAUDE_MD=true;  INSTALL_COMMANDS=false; INSTALL_SKILLS=false; INSTALL_STATUS_LINE=false; shift ;;
        --commands-only)    INSTALL_CLAUDE_MD=false; INSTALL_COMMANDS=true;  INSTALL_SKILLS=false; INSTALL_STATUS_LINE=false; shift ;;
        --skills-only)      INSTALL_CLAUDE_MD=false; INSTALL_COMMANDS=false; INSTALL_SKILLS=true;  INSTALL_STATUS_LINE=false; shift ;;
        --status-line-only) INSTALL_CLAUDE_MD=false; INSTALL_COMMANDS=false; INSTALL_SKILLS=false; INSTALL_STATUS_LINE=true;  shift ;;
        --uninstall)        UNINSTALL=true; shift ;;
        -h|--help)          show_help; exit 0 ;;
        *)                  err "Unknown option: $1"; show_help; exit 1 ;;
    esac
done

backup_one() {
    local src="$1"
    [ -e "$src" ] || return 0
    if [ -L "$src" ]; then
        local target
        target="$(readlink "$src")"
        case "$target" in
            "$REPO_ROOT"/*)
                # Symlink already points at this repo — nothing to back up.
                rm -f "$src"
                return 0
                ;;
        esac
    fi
    mkdir -p "$BACKUP_DIR"
    local rel="${src#"$CLAUDE_DIR"/}"
    local dest="$BACKUP_DIR/$rel"
    mkdir -p "$(dirname "$dest")"
    mv "$src" "$dest"
    info "backed up $rel → backups/$TIMESTAMP/$rel"
}

link_one() {
    local src="$1" dst="$2"
    backup_one "$dst"
    mkdir -p "$(dirname "$dst")"
    ln -s "$src" "$dst"
    success "linked $(basename "$dst")"
}

unlink_managed() {
    local dst="$1"
    if [ -L "$dst" ]; then
        local target
        target="$(readlink "$dst")"
        case "$target" in
            "$REPO_ROOT"/*) rm -f "$dst"; success "removed $(basename "$dst")"; return 0 ;;
        esac
    fi
}

install_claude_md() {
    info "installing CLAUDE.md"
    link_one "$REPO_ROOT/CLAUDE.md" "$CLAUDE_DIR/CLAUDE.md"

    info "installing claude/ subdir"
    if [ -e "$CLAUDE_DIR/claude" ] && [ ! -L "$CLAUDE_DIR/claude" ]; then
        backup_one "$CLAUDE_DIR/claude"
    elif [ -L "$CLAUDE_DIR/claude" ]; then
        rm -f "$CLAUDE_DIR/claude"
    fi
    ln -s "$REPO_ROOT/claude" "$CLAUDE_DIR/claude"
    success "linked claude/ subdir"
}

install_commands() {
    info "installing commands/"
    mkdir -p "$CLAUDE_DIR/commands"
    for f in "$REPO_ROOT/commands/"*.md; do
        [ -f "$f" ] || continue
        local name
        name="$(basename "$f")"
        link_one "$f" "$CLAUDE_DIR/commands/$name"
    done
}

install_skills() {
    info "installing skills/"
    mkdir -p "$CLAUDE_DIR/skills"
    for d in "$REPO_ROOT/skills/"*/; do
        [ -d "$d" ] || continue
        local name
        name="$(basename "$d")"
        link_one "$d" "$CLAUDE_DIR/skills/$name"
    done
}

install_status_line() {
    info "installing status-line.sh"
    link_one "$REPO_ROOT/status-line.sh" "$CLAUDE_DIR/status-line.sh"
}

uninstall_claude_md() {
    info "uninstalling CLAUDE.md"
    unlink_managed "$CLAUDE_DIR/CLAUDE.md"
    unlink_managed "$CLAUDE_DIR/claude"
}

uninstall_commands() {
    info "uninstalling commands/"
    for f in "$REPO_ROOT/commands/"*.md; do
        [ -f "$f" ] || continue
        local name
        name="$(basename "$f")"
        unlink_managed "$CLAUDE_DIR/commands/$name"
    done
}

uninstall_skills() {
    info "uninstalling skills/"
    for d in "$REPO_ROOT/skills/"*/; do
        [ -d "$d" ] || continue
        local name
        name="$(basename "$d")"
        unlink_managed "$CLAUDE_DIR/skills/$name"
    done
}

uninstall_status_line() {
    info "uninstalling status-line.sh"
    unlink_managed "$CLAUDE_DIR/status-line.sh"
}

if [ "$UNINSTALL" = true ]; then
    [ "$INSTALL_CLAUDE_MD"   = true ] && uninstall_claude_md
    [ "$INSTALL_COMMANDS"    = true ] && uninstall_commands
    [ "$INSTALL_SKILLS"      = true ] && uninstall_skills
    [ "$INSTALL_STATUS_LINE" = true ] && uninstall_status_line
    success "uninstall complete"
    exit 0
fi

mkdir -p "$CLAUDE_DIR"
[ "$INSTALL_CLAUDE_MD"   = true ] && install_claude_md
[ "$INSTALL_COMMANDS"    = true ] && install_commands
[ "$INSTALL_SKILLS"      = true ] && install_skills
[ "$INSTALL_STATUS_LINE" = true ] && install_status_line

if [ -d "$BACKUP_DIR" ]; then
    info "backups saved to $BACKUP_DIR"
fi

success "install complete"
echo
echo "Required env vars (add to your shell rc if you use the related commands):"
echo "  export SLACK_BABYSITTER_WEBHOOK='https://hooks.slack.com/services/...'"
echo "  export REVIEW_REPOS='owner1/repo1 owner2/repo2'"

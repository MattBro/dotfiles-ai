#!/usr/bin/env bash
# install.sh — install the shared Claude Code and Codex configuration.
#
# Claude Code files are symlinked. Codex's config.toml is updated in place so
# Codex-owned model, plugin, MCP, and project settings remain intact.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_DIR="$HOME/.claude"
CODEX_DIR="${CODEX_HOME:-$HOME/.codex}"
AGENTS_DIR="$HOME/.agents"
LOCAL_BIN="$HOME/.local/bin"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
CLAUDE_BACKUP_DIR="$CLAUDE_DIR/backups/$TIMESTAMP"
CODEX_BACKUP_DIR="$CODEX_DIR/backups/$TIMESTAMP"
AGENTS_BACKUP_DIR="$AGENTS_DIR/backups/$TIMESTAMP"

INSTALL_CLAUDE_MD=true
INSTALL_COMMANDS=true
INSTALL_SKILLS=true
INSTALL_OUTPUT_STYLES=true
INSTALL_STATUS_LINE=true
INSTALL_BIN=true
INSTALL_CODEX_RUNTIME=true
INSTALL_CODEX_CONFIG=true
INSTALL_CODEX_INSTRUCTIONS=true
INSTALL_CODEX_SKILLS=true
INSTALL_CODEX_HOOKS=true
UNINSTALL=false

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

Install dotfiles-ai for Claude Code and Codex.

Options:
  --codex-only          Install only Codex runtime, config, instructions, skills, and hooks
  --claude-md-only      Install only Claude Code instructions
  --commands-only       Install only Claude Code commands/
  --skills-only         Install only Claude Code skills/
  --output-styles-only  Install only Claude Code output-styles/
  --status-line-only    Install only Claude Code status-line.sh (legacy option)
  --bin-only            Install only bin/ shims into ~/.local/bin
  --uninstall           Remove files and config blocks managed by this repo
  -h, --help            Show this help

Notes:
  - Conflicts are backed up below ~/.claude, ~/.codex, or ~/.agents.
  - Claude Code files are symlinked; unmanaged commands are left alone.
  - The official standalone Codex runtime is bootstrapped when it is missing.
  - CODEX_HOME is honored when set; otherwise Codex files use ~/.codex.
  - Codex config.toml is merged in place and loaded in strict-validation mode.
  - Existing Codex hooks are preserved alongside the managed hooks.
  - Codex skills land in ~/.agents/skills, its documented personal-skill path.
  - Review new Codex hooks once with /hooks before they can run.
  - Uninstall leaves the standalone Codex runtime in place.
EOF
}

disable_claude() {
    INSTALL_CLAUDE_MD=false
    INSTALL_COMMANDS=false
    INSTALL_SKILLS=false
    INSTALL_OUTPUT_STYLES=false
    INSTALL_STATUS_LINE=false
    INSTALL_BIN=false
}

disable_codex() {
    INSTALL_CODEX_RUNTIME=false
    INSTALL_CODEX_CONFIG=false
    INSTALL_CODEX_INSTRUCTIONS=false
    INSTALL_CODEX_SKILLS=false
    INSTALL_CODEX_HOOKS=false
}

while [ $# -gt 0 ]; do
    case "$1" in
        --codex-only)
            disable_claude
            INSTALL_CODEX_RUNTIME=true
            INSTALL_CODEX_CONFIG=true
            INSTALL_CODEX_INSTRUCTIONS=true
            INSTALL_CODEX_SKILLS=true
            INSTALL_CODEX_HOOKS=true
            shift
            ;;
        --claude-md-only) disable_claude; disable_codex; INSTALL_CLAUDE_MD=true; shift ;;
        --commands-only) disable_claude; disable_codex; INSTALL_COMMANDS=true; shift ;;
        --skills-only) disable_claude; disable_codex; INSTALL_SKILLS=true; shift ;;
        --output-styles-only) disable_claude; disable_codex; INSTALL_OUTPUT_STYLES=true; shift ;;
        --status-line-only)
            disable_claude; disable_codex
            INSTALL_STATUS_LINE=true
            shift
            ;;
        --bin-only) disable_claude; disable_codex; INSTALL_BIN=true; shift ;;
        --uninstall) UNINSTALL=true; shift ;;
        -h|--help) show_help; exit 0 ;;
        *) err "Unknown option: $1"; show_help; exit 1 ;;
    esac
done

backup_one_at() {
    local src="$1" managed_root="$2" backup_dir="$3"
    [ -e "$src" ] || [ -L "$src" ] || return 0
    if [ -L "$src" ]; then
        local target
        target="$(readlink "$src")"
        case "$target" in
            "$REPO_ROOT"/*)
                rm -f "$src"
                return 0
                ;;
        esac
    fi
    mkdir -p "$backup_dir"
    local rel="${src#"$managed_root"/}"
    local dest
    dest="$(available_path "$backup_dir/$rel")"
    mkdir -p "$(dirname "$dest")"
    mv "$src" "$dest"
    info "backed up $src → $dest"
}

available_path() {
    local candidate="$1" suffix=0
    while [ -e "$candidate" ] || [ -L "$candidate" ]; do
        suffix=$((suffix + 1))
        candidate="$1.$suffix"
    done
    printf '%s\n' "$candidate"
}

link_one_at() {
    local src="$1" dst="$2" managed_root="$3" backup_dir="$4"
    backup_one_at "$dst" "$managed_root" "$backup_dir"
    mkdir -p "$(dirname "$dst")"
    ln -s "$src" "$dst"
    success "linked $dst"
}

link_claude() {
    link_one_at "$1" "$2" "$CLAUDE_DIR" "$CLAUDE_BACKUP_DIR"
}

link_codex() {
    link_one_at "$1" "$2" "$CODEX_DIR" "$CODEX_BACKUP_DIR"
}

link_agent_skill() {
    link_one_at "$1" "$2" "$AGENTS_DIR" "$AGENTS_BACKUP_DIR"
}

unlink_managed() {
    local dst="$1"
    if [ -L "$dst" ]; then
        local target
        target="$(readlink "$dst")"
        case "$target" in
            "$REPO_ROOT"/*)
                rm -f "$dst"
                success "removed $dst"
                ;;
        esac
    fi
}

remove_generated() {
    local path="$1"
    if [ -f "$path" ] && head -n 1 "$path" | grep -Fq "Generated by dotfiles-ai install.sh"; then
        rm -f "$path"
        success "removed $path"
    fi
}

prepare_generated() {
    local path="$1" managed_root="$2" backup_dir="$3"
    [ -e "$path" ] || [ -L "$path" ] || return 0
    if [ ! -L "$path" ] && [ -f "$path" ] && head -n 1 "$path" | grep -Fq "Generated by dotfiles-ai install.sh"; then
        return 0
    fi
    backup_one_at "$path" "$managed_root" "$backup_dir"
}

install_claude_md() {
    info "installing Claude Code instructions"
    link_claude "$REPO_ROOT/CLAUDE.md" "$CLAUDE_DIR/CLAUDE.md"
    link_claude "$REPO_ROOT/claude" "$CLAUDE_DIR/claude"
}

build_agent_instructions() {
    local target="$1"
    local staging_dir
    staging_dir="$(mktemp -d "${TMPDIR:-/tmp}/dotfiles-ai-agents.XXXXXX")"
    info "generating flattened $target instructions"
    if ! HOME="$staging_dir" python3 "$REPO_ROOT/scripts/build-agents-md.py" --target "$target"; then
        rm -rf "$staging_dir"
        return 1
    fi

    case "$target" in
        all)
            prepare_generated "$AGENTS_DIR/AGENTS.md" "$AGENTS_DIR" "$AGENTS_BACKUP_DIR"
            prepare_generated "$CODEX_DIR/AGENTS.md" "$CODEX_DIR" "$CODEX_BACKUP_DIR"
            mkdir -p "$AGENTS_DIR" "$CODEX_DIR"
            mv "$staging_dir/.agents/AGENTS.md" "$AGENTS_DIR/AGENTS.md"
            mv "$staging_dir/.codex/AGENTS.md" "$CODEX_DIR/AGENTS.md"
            ;;
        posthog-code)
            prepare_generated "$AGENTS_DIR/AGENTS.md" "$AGENTS_DIR" "$AGENTS_BACKUP_DIR"
            mkdir -p "$AGENTS_DIR"
            mv "$staging_dir/.agents/AGENTS.md" "$AGENTS_DIR/AGENTS.md"
            ;;
        codex)
            prepare_generated "$CODEX_DIR/AGENTS.md" "$CODEX_DIR" "$CODEX_BACKUP_DIR"
            mkdir -p "$CODEX_DIR"
            mv "$staging_dir/.codex/AGENTS.md" "$CODEX_DIR/AGENTS.md"
            ;;
    esac
    rm -rf "$staging_dir"
}

install_commands() {
    info "installing Claude Code commands/"
    mkdir -p "$CLAUDE_DIR/commands"
    for f in "$REPO_ROOT/commands/"*.md; do
        [ -f "$f" ] || continue
        link_claude "$f" "$CLAUDE_DIR/commands/$(basename "$f")"
    done
}

install_skills() {
    info "installing Claude Code skills/"
    mkdir -p "$CLAUDE_DIR/skills"
    for d in "$REPO_ROOT/skills/"*/; do
        [ -d "$d" ] || continue
        link_claude "$d" "$CLAUDE_DIR/skills/$(basename "$d")"
    done
}

install_output_styles() {
    info "installing Claude Code output-styles/"
    mkdir -p "$CLAUDE_DIR/output-styles"
    for f in "$REPO_ROOT/output-styles/"*.md; do
        [ -f "$f" ] || continue
        link_claude "$f" "$CLAUDE_DIR/output-styles/$(basename "$f")"
    done
}

install_status_line() {
    info "installing Claude Code status-line.sh"
    link_claude "$REPO_ROOT/status-line.sh" "$CLAUDE_DIR/status-line.sh"
}

install_codex_runtime() {
    local standalone="$CODEX_DIR/packages/standalone/current/codex"
    if [ -x "$standalone" ]; then
        success "standalone Codex runtime already installed"
        return 0
    fi

    if ! command -v curl >/dev/null 2>&1; then
        err "curl is required to bootstrap the standalone Codex runtime"
        return 1
    fi

    info "installing the official standalone Codex runtime"
    local installer
    installer="$(mktemp "${TMPDIR:-/tmp}/dotfiles-ai-codex-installer.XXXXXX")"
    if ! curl -fsSL https://chatgpt.com/codex/install.sh -o "$installer"; then
        rm -f "$installer"
        err "could not download the official Codex installer"
        return 1
    fi
    if ! CODEX_HOME="$CODEX_DIR" CODEX_NON_INTERACTIVE=true sh "$installer"; then
        rm -f "$installer"
        err "the official Codex installer failed"
        return 1
    fi
    rm -f "$installer"

    if [ ! -x "$standalone" ]; then
        err "Codex installed without the expected standalone runtime at $standalone"
        return 1
    fi
    success "installed standalone Codex runtime"
}

codex_config_valid() {
    # Doctor reports unrelated installation/update failures on this machine, so
    # inspect only its strict config-load check instead of using the exit code.
    local codex_bin report
    if [ -x "$CODEX_DIR/packages/standalone/current/codex" ]; then
        codex_bin="$CODEX_DIR/packages/standalone/current/codex"
    else
        codex_bin="$(command -v codex)"
    fi
    report="$(CODEX_HOME="$CODEX_DIR" "$codex_bin" --strict-config doctor --json 2>/dev/null || true)"
    python3 -c '
import json, sys
try:
    report = json.load(sys.stdin)
    check = report["checks"]["config.load"]
except (json.JSONDecodeError, KeyError, TypeError):
    raise SystemExit(1)
raise SystemExit(0 if check.get("status") == "ok" else 1)
' <<<"$report"
}

codex_available() {
    [ -x "$CODEX_DIR/packages/standalone/current/codex" ] || command -v codex >/dev/null 2>&1
}

install_codex_config() {
    info "merging Codex config and native status line"
    mkdir -p "$CODEX_DIR"
    local target="$CODEX_DIR/config.toml" config_file before had_existing=false changed=false
    config_file="$target"
    if [ -L "$target" ]; then
        config_file="$(python3 -c 'import os, sys; print(os.path.realpath(sys.argv[1]))' "$target")"
        if [ ! -f "$config_file" ]; then
            err "Codex config is a dangling symlink: $target"
            return 1
        fi
    fi
    before="$(mktemp "${TMPDIR:-/tmp}/dotfiles-ai-codex-config.XXXXXX")"
    if [ -f "$config_file" ]; then
        cp -p "$config_file" "$before"
        had_existing=true
    fi

    python3 "$REPO_ROOT/scripts/update-codex-config.py" \
        --source "$REPO_ROOT/codex/config.toml" --target "$config_file"

    if ! cmp -s "$before" "$config_file"; then
        changed=true
        if [ "$had_existing" = true ]; then
            local backup
            mkdir -p "$CODEX_BACKUP_DIR"
            backup="$(available_path "$CODEX_BACKUP_DIR/config.toml")"
            cp -p "$before" "$backup"
            info "backed up config.toml → $backup"
        fi
    fi

    if codex_available && ! codex_config_valid; then
        if [ "$had_existing" = true ]; then
            cp -p "$before" "$config_file"
        else
            rm -f "$config_file"
        fi
        rm -f "$before"
        err "Codex rejected the merged config; restored the previous file"
        return 1
    fi

    if [ "$changed" = true ]; then
        success "updated $target"
    else
        success "$target already current"
    fi
    rm -f "$before"
}

install_codex_skills() {
    info "installing Codex personal skills"
    mkdir -p "$AGENTS_DIR/skills"
    while IFS= read -r name; do
        case "$name" in ""|\#*) continue ;; esac
        if [ ! -d "$REPO_ROOT/skills/$name" ]; then
            err "codex/shared-skills.txt names missing skill: $name"
            return 1
        fi
        link_agent_skill "$REPO_ROOT/skills/$name" "$AGENTS_DIR/skills/$name"
    done < "$REPO_ROOT/codex/shared-skills.txt"

    for d in "$REPO_ROOT/codex/skills/"*/; do
        [ -d "$d" ] || continue
        link_agent_skill "$d" "$AGENTS_DIR/skills/$(basename "$d")"
    done
}

install_codex_hooks() {
    info "installing Codex hooks"
    python3 -m json.tool "$REPO_ROOT/codex/hooks.json" >/dev/null
    local target="$CODEX_DIR/hooks.json" updated
    updated="$(mktemp "${TMPDIR:-/tmp}/dotfiles-ai-codex-hooks.XXXXXX")"
    update_codex_hooks install "$target" "$updated"
    if [ -f "$target" ] && cmp -s "$target" "$updated"; then
        rm -f "$updated"
    else
        backup_one_at "$target" "$CODEX_DIR" "$CODEX_BACKUP_DIR"
        mkdir -p "$CODEX_DIR"
        mv "$updated" "$target"
        success "updated $target"
    fi
    link_codex "$REPO_ROOT/scripts/check-bare-refs.py" "$CODEX_DIR/hooks/check-bare-refs.py"
    link_codex "$REPO_ROOT/scripts/block-slack-writes.py" "$CODEX_DIR/hooks/block-slack-writes.py"
    warn "Codex requires a one-time /hooks review before these hooks run"
}

update_codex_hooks() {
    local mode="$1" target="$2" output="$3"
    python3 - "$mode" "$target" "$REPO_ROOT/codex/hooks.json" "$output" "$CODEX_DIR" <<'PY'
import json
import os
import shlex
import sys
from copy import deepcopy

mode, target, source, output, codex_dir = sys.argv[1:]


def load(path, default):
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError:
        return default


def managed(group):
    commands = [hook.get("command", "") for hook in group.get("hooks", [])]
    names = ("check-bare-refs.py", "block-slack-writes.py")
    return bool(commands) and all(
        any(name in command for name in names) for command in commands
    )


existing = load(target, {})
source_data = load(source, {})
hooks = existing.setdefault("hooks", {})
for event, groups in list(hooks.items()):
    hooks[event] = [group for group in groups if not managed(group)]
    if not hooks[event]:
        del hooks[event]

if mode == "install":
    for event, groups in source_data["hooks"].items():
        rendered = deepcopy(groups)
        hook_dir = shlex.quote(os.path.join(codex_dir, "hooks")) + "/"
        for group in rendered:
            for hook in group.get("hooks", []):
                hook["command"] = hook.get("command", "").replace(
                    "~/.codex/hooks/", hook_dir
                )
        hooks.setdefault(event, []).extend(rendered)
    if not existing.get("description"):
        existing["description"] = source_data["description"]
elif not hooks:
    existing.pop("hooks", None)
    if existing.get("description") == source_data.get("description"):
        existing.pop("description", None)

with open(output, "w", encoding="utf-8") as handle:
    json.dump(existing, handle, indent=2)
    handle.write("\n")
PY
}

install_bin() {
    info "installing bin/ shims to $LOCAL_BIN"
    mkdir -p "$LOCAL_BIN"
    for f in "$REPO_ROOT/bin/"*; do
        [ -f "$f" ] || continue
        local name dst target
        name="$(basename "$f")"
        dst="$LOCAL_BIN/$name"
        if [ -L "$dst" ]; then
            target="$(readlink "$dst")"
            case "$target" in
                "$REPO_ROOT"/*) rm -f "$dst" ;;
                *) warn "$dst already points at $target, leaving it alone"; continue ;;
            esac
        elif [ -e "$dst" ]; then
            warn "$dst exists and is not ours, leaving it alone"
            continue
        fi
        ln -s "$f" "$dst"
        success "linked $name → $LOCAL_BIN/$name"
    done
    case ":$PATH:" in
        *":$LOCAL_BIN:"*) ;;
        *) warn "$LOCAL_BIN is not on PATH; add it to your shell rc or the shims won't resolve" ;;
    esac
}

uninstall_codex_config() {
    local target="$CODEX_DIR/config.toml"
    [ -f "$target" ] || return 0
    local config_file
    config_file="$target"
    if [ -L "$target" ]; then
        config_file="$(python3 -c 'import os, sys; print(os.path.realpath(sys.argv[1]))' "$target")"
    fi
    if ! grep -Fq "# >>> dotfiles-ai:" "$config_file"; then
        success "Codex config has no managed blocks"
        return 0
    fi
    info "removing dotfiles-ai blocks from Codex config"
    local before backup
    before="$(mktemp "${TMPDIR:-/tmp}/dotfiles-ai-codex-config.XXXXXX")"
    cp -p "$config_file" "$before"
    python3 "$REPO_ROOT/scripts/update-codex-config.py" \
        --source "$REPO_ROOT/codex/config.toml" --target "$config_file" --remove
    if cmp -s "$before" "$config_file"; then
        rm -f "$before"
        success "Codex config has no managed blocks"
        return 0
    fi
    mkdir -p "$CODEX_BACKUP_DIR"
    backup="$(available_path "$CODEX_BACKUP_DIR/config.toml")"
    cp -p "$before" "$backup"
    if codex_available && ! codex_config_valid; then
        cp -p "$before" "$config_file"
        rm -f "$before"
        err "Codex rejected the updated config; restored the previous file"
        return 1
    fi
    rm -f "$before"
    info "backed up config.toml → $backup"
    success "removed managed Codex config blocks"
}

uninstall_claude_md() {
    info "uninstalling Claude Code instructions"
    unlink_managed "$CLAUDE_DIR/CLAUDE.md"
    unlink_managed "$CLAUDE_DIR/claude"
    remove_generated "$AGENTS_DIR/AGENTS.md"
}

uninstall_commands() {
    info "uninstalling Claude Code commands/"
    for f in "$REPO_ROOT/commands/"*.md; do
        [ -f "$f" ] || continue
        unlink_managed "$CLAUDE_DIR/commands/$(basename "$f")"
    done
}

uninstall_skills() {
    info "uninstalling Claude Code skills/"
    for d in "$REPO_ROOT/skills/"*/; do
        [ -d "$d" ] || continue
        unlink_managed "$CLAUDE_DIR/skills/$(basename "$d")"
    done
}

uninstall_output_styles() {
    info "uninstalling Claude Code output-styles/"
    for f in "$REPO_ROOT/output-styles/"*.md; do
        [ -f "$f" ] || continue
        unlink_managed "$CLAUDE_DIR/output-styles/$(basename "$f")"
    done
}

uninstall_status_line() {
    info "uninstalling Claude Code status line"
    unlink_managed "$CLAUDE_DIR/status-line.sh"
}

uninstall_codex_skills() {
    info "uninstalling Codex personal skills"
    while IFS= read -r name; do
        case "$name" in ""|\#*) continue ;; esac
        unlink_managed "$AGENTS_DIR/skills/$name"
    done < "$REPO_ROOT/codex/shared-skills.txt"
    for d in "$REPO_ROOT/codex/skills/"*/; do
        [ -d "$d" ] || continue
        unlink_managed "$AGENTS_DIR/skills/$(basename "$d")"
    done
}

uninstall_codex_hooks() {
    info "uninstalling Codex hooks"
    local target="$CODEX_DIR/hooks.json" updated
    if [ -f "$target" ]; then
        updated="$(mktemp "${TMPDIR:-/tmp}/dotfiles-ai-codex-hooks.XXXXXX")"
        update_codex_hooks uninstall "$target" "$updated"
        if ! cmp -s "$target" "$updated"; then
            backup_one_at "$target" "$CODEX_DIR" "$CODEX_BACKUP_DIR"
            if python3 -c 'import json, sys; raise SystemExit(bool(json.load(open(sys.argv[1]))))' "$updated"; then
                rm -f "$updated"
            else
                mkdir -p "$CODEX_DIR"
                mv "$updated" "$target"
                success "removed managed hooks from $target"
            fi
        else
            rm -f "$updated"
        fi
    fi
    unlink_managed "$CODEX_DIR/hooks/check-bare-refs.py"
    unlink_managed "$CODEX_DIR/hooks/block-slack-writes.py"
}

uninstall_bin() {
    info "uninstalling bin/ shims"
    for f in "$REPO_ROOT/bin/"*; do
        [ -f "$f" ] || continue
        unlink_managed "$LOCAL_BIN/$(basename "$f")"
    done
}

if [ "$UNINSTALL" = true ]; then
    if [ "$INSTALL_CLAUDE_MD" = true ]; then uninstall_claude_md; fi
    if [ "$INSTALL_COMMANDS" = true ]; then uninstall_commands; fi
    if [ "$INSTALL_SKILLS" = true ]; then uninstall_skills; fi
    if [ "$INSTALL_OUTPUT_STYLES" = true ]; then uninstall_output_styles; fi
    if [ "$INSTALL_STATUS_LINE" = true ]; then uninstall_status_line; fi
    if [ "$INSTALL_BIN" = true ]; then uninstall_bin; fi
    if [ "$INSTALL_CODEX_CONFIG" = true ]; then uninstall_codex_config; fi
    if [ "$INSTALL_CODEX_INSTRUCTIONS" = true ]; then remove_generated "$CODEX_DIR/AGENTS.md"; fi
    if [ "$INSTALL_CODEX_SKILLS" = true ]; then uninstall_codex_skills; fi
    if [ "$INSTALL_CODEX_HOOKS" = true ]; then uninstall_codex_hooks; fi
    success "uninstall complete"
    exit 0
fi

if [ "$INSTALL_CLAUDE_MD" = true ]; then install_claude_md; fi
if [ "$INSTALL_COMMANDS" = true ]; then install_commands; fi
if [ "$INSTALL_SKILLS" = true ]; then install_skills; fi
if [ "$INSTALL_OUTPUT_STYLES" = true ]; then install_output_styles; fi
if [ "$INSTALL_STATUS_LINE" = true ]; then install_status_line; fi
if [ "$INSTALL_BIN" = true ]; then install_bin; fi
if [ "$INSTALL_CODEX_RUNTIME" = true ]; then install_codex_runtime; fi
if [ "$INSTALL_CODEX_CONFIG" = true ]; then install_codex_config; fi
if [ "$INSTALL_CODEX_SKILLS" = true ]; then install_codex_skills; fi
if [ "$INSTALL_CODEX_HOOKS" = true ]; then install_codex_hooks; fi

if [ "$INSTALL_CLAUDE_MD" = true ] && [ "$INSTALL_CODEX_INSTRUCTIONS" = true ]; then
    build_agent_instructions all
elif [ "$INSTALL_CLAUDE_MD" = true ]; then
    build_agent_instructions posthog-code
elif [ "$INSTALL_CODEX_INSTRUCTIONS" = true ]; then
    build_agent_instructions codex
fi

for backup_dir in "$CLAUDE_BACKUP_DIR" "$CODEX_BACKUP_DIR" "$AGENTS_BACKUP_DIR"; do
    [ -d "$backup_dir" ] && info "backups saved to $backup_dir"
done

success "install complete"
echo
echo "Required env vars (add to your shell rc if you use the related commands):"
echo "  export SLACK_BABYSITTER_WEBHOOK='https://hooks.slack.com/services/...'"
echo "  export REVIEW_REPOS='owner1/repo1 owner2/repo2'"

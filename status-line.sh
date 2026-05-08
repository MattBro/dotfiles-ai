#!/bin/bash

# Read Claude Code context from stdin
input=$(cat)

# Extract information from Claude Code context
model_name=$(echo "$input" | jq -r '.model.display_name // "Claude"')
current_dir=$(echo "$input" | jq -r '.workspace.current_dir // ""')
context_pct=$(echo "$input" | jq -r '.context_window.used_percentage // 0' | cut -d. -f1)
effort_level=$(echo "$input" | jq -r '.effort.level // empty')

# Basename of current directory (p10k Pure \W style: blue folder name)
if [ -n "$current_dir" ]; then
    dir_display=$(basename "$current_dir")
else
    dir_display=$(basename "$HOME")
fi

# Get git status if we're in a git repo
# Green = clean, bright yellow = uncommitted changes (staged, unstaged, or untracked)
git_info=""
git_color=""
repo_dir="${current_dir:-$HOME}"
if git -C "$repo_dir" --no-optional-locks rev-parse --git-dir > /dev/null 2>&1; then
    branch=$(git -C "$repo_dir" --no-optional-locks symbolic-ref --short HEAD 2>/dev/null || git -C "$repo_dir" --no-optional-locks rev-parse --short HEAD 2>/dev/null)
    if [ -n "$branch" ]; then
        if ! git -C "$repo_dir" --no-optional-locks diff --quiet 2>/dev/null || \
           ! git -C "$repo_dir" --no-optional-locks diff --cached --quiet 2>/dev/null || \
           [ -n "$(git -C "$repo_dir" --no-optional-locks ls-files --others --exclude-standard 2>/dev/null)" ]; then
            git_color="\033[93m"   # bright yellow — dirty
            git_info=" ${branch}*"
        else
            git_color="\033[32m"   # green — clean
            git_info=" ${branch}✓"
        fi
    fi
fi

color_for_pct() {
    local pct=$1
    if [ "$pct" -ge 80 ]; then
        printf "\033[91m"  # bright red
    elif [ "$pct" -ge 50 ]; then
        printf "\033[33m"  # yellow
    else
        printf "\033[32m"  # green
    fi
}

CTX_COLOR=$(color_for_pct "$context_pct")

# --- Usage limits from Claude Code's rate_limits field ---
usage_5h=$(echo "$input" | jq -r '.rate_limits.five_hour.used_percentage // empty' 2>/dev/null | cut -d. -f1)
usage_7d=$(echo "$input" | jq -r '.rate_limits.seven_day.used_percentage // empty' 2>/dev/null | cut -d. -f1)

# Calculate pacing targets using resets_at from the rate_limits data
NOW_EPOCH=$(date +%s)
target_5h=""
target_7d=""
resets_5h_label=""
resets_7d_label=""

if [ -n "$usage_5h" ]; then
    resets_5h=$(echo "$input" | jq -r '.rate_limits.five_hour.resets_at // empty' 2>/dev/null)
    if [ -n "$resets_5h" ]; then
        reset_epoch=$resets_5h
        if [ -n "$reset_epoch" ]; then
            window_secs=$((5 * 3600))
            start_epoch=$((reset_epoch - window_secs))
            elapsed=$((NOW_EPOCH - start_epoch))
            [ "$elapsed" -lt 0 ] && elapsed=0
            [ "$elapsed" -gt "$window_secs" ] && elapsed=$window_secs
            target_5h=$((elapsed * 100 / window_secs))
            resets_5h_label=$(date -d "@${reset_epoch}" '+%I%p' 2>/dev/null | sed 's/^0//' | tr '[:upper:]' '[:lower:]')
            # Fallback for macOS
            [ -z "$resets_5h_label" ] && resets_5h_label=$(date -r "$reset_epoch" '+%-I%p' 2>/dev/null | tr '[:upper:]' '[:lower:]')
        fi
    fi
fi

if [ -n "$usage_7d" ]; then
    resets_7d=$(echo "$input" | jq -r '.rate_limits.seven_day.resets_at // empty' 2>/dev/null)
    if [ -n "$resets_7d" ]; then
        reset_epoch=$resets_7d
        if [ -n "$reset_epoch" ]; then
            window_secs=$((7 * 86400))
            start_epoch=$((reset_epoch - window_secs))
            elapsed=$((NOW_EPOCH - start_epoch))
            [ "$elapsed" -lt 0 ] && elapsed=0
            [ "$elapsed" -gt "$window_secs" ] && elapsed=$window_secs
            target_7d=$((elapsed * 100 / window_secs))
            resets_7d_label=$(date -d "@${reset_epoch}" '+%a,%-I%p' 2>/dev/null | tr '[:upper:]' '[:lower:]')
            # Fallback for macOS
            [ -z "$resets_7d_label" ] && resets_7d_label=$(date -r "$reset_epoch" '+%a,%-I%p' 2>/dev/null | tr '[:upper:]' '[:lower:]')
        fi
    fi
fi

# Color actual usage vs pace (percentage-based threshold, integer math):
#   green  — usage < pace
#   yellow — usage >= pace AND usage * 100 <= pace * 110  (within 10% over pace)
#   red    — usage * 100 > pace * 110  (more than 10% over pace)
color_for_usage_vs_pace() {
    local usage=$1 pace=$2
    if [ -n "$pace" ] && [ $((usage * 100)) -gt $((pace * 110)) ]; then
        printf "\033[91m"   # red — more than 10% over pace
    elif [ -n "$pace" ] && [ "$usage" -ge "$pace" ]; then
        printf "\033[33m"   # yellow — over pace but within 10%
    else
        printf "\033[32m"   # green — under pace
    fi
}

# Build usage parts — compact numeric format: "5hr(12pm) 30/50%"
usage_parts=""
if [ -n "$usage_5h" ]; then
    U5_COLOR=$(color_for_usage_vs_pace "$usage_5h" "$target_5h")
    reset_label=""
    [ -n "$resets_5h_label" ] && reset_label="(${resets_5h_label}) "
    pace_part=""
    [ -n "$target_5h" ] && pace_part="\033[38;5;199m/${target_5h}"
    usage_parts="${U5_COLOR}5hr ${reset_label}${usage_5h}${pace_part}%\033[0m"
fi
if [ -n "$usage_7d" ]; then
    U7_COLOR=$(color_for_usage_vs_pace "$usage_7d" "$target_7d")
    reset_7d_label_str=""
    [ -n "$resets_7d_label" ] && reset_7d_label_str="(${resets_7d_label}) "
    pace_part_7d=""
    [ -n "$target_7d" ] && pace_part_7d="\033[38;5;199m/${target_7d}"
    [ -n "$usage_parts" ] && usage_parts="${usage_parts}\033[2m │ \033[0m"
    usage_parts="${usage_parts}${U7_COLOR}wk ${reset_7d_label_str}${usage_7d}${pace_part_7d}%\033[0m"
fi

# Effort level color: dim for low/medium, normal for high, yellow for xhigh, red for max
effort_part=""
if [ -n "$effort_level" ]; then
    case "$effort_level" in
        max)   EFFORT_COLOR="\033[91m" ;;   # bright red
        xhigh) EFFORT_COLOR="\033[33m" ;;   # yellow
        high)  EFFORT_COLOR="\033[0m" ;;    # default
        *)     EFFORT_COLOR="\033[2m" ;;    # dim (low/medium)
    esac
    effort_part="\033[2m │ \033[0m${EFFORT_COLOR}effort ${effort_level}\033[0m"
fi

# Single line output
# blue(57C7FF) dir · green/yellow git branch · ctx% · usage parts · effort · model
line="\033[38;2;87;199;255m${dir_display}\033[0m${git_color}${git_info}\033[0m\033[2m │ ${CTX_COLOR}ctx ${context_pct}%\033[0m"
if [ -n "$usage_parts" ]; then
    line="${line}\033[2m │ \033[0m${usage_parts}"
fi
line="${line}${effort_part}\033[2m │ ${model_name}\033[0m"
printf "%b\n" "$line"

#!/usr/bin/env python3
"""pr-status-check: list my open PRs, their CI/review status, and the latest
local Claude Code session that relates to each PR.

Output is a Markdown table on stdout. For every PR with a matching local
session, a small `*.clauderesume` file is written under ~/.claude/pr-resume/
and the row gets a `file://` "resume" link. CMD+clicking that link in the
Claude Code TUI hands the file to ClaudeResume.app, which opens a new Ghostty
tab in the session's repo dir and runs `claude --resume <session>`.

Matching is two-tier:
  1. branch  — session.gitBranch == PR.headRefName  (🎯 exact)
  2. mention — transcript contains the PR URL or the branch name  (💬 related)
The most recently-modified session wins. The currently-running session
(CLAUDE_CODE_SESSION_ID, or --exclude <id>) is never matched.
"""

import argparse
import glob
import json
import os
import pathlib
import re
import subprocess
import sys
from datetime import datetime, timezone

HOME = os.path.expanduser("~")
PROJECTS = os.path.join(HOME, ".claude", "projects")
RESUME_DIR = os.path.join(HOME, ".claude", "pr-resume")
MAX_LINES = 500
UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\.jsonl$")


APP_PATH = os.path.expanduser("~/Applications/ClaudeResume.app")
# A session whose transcript contains this string is one of THIS tool's own runs
# (the env-fact line below is emitted on every run). Such sessions echo every PR
# URL/branch, so they'd false-match as the "latest mention" — exclude them.
SENTINEL = "pr-resume-env:"


def sh(args):
    return subprocess.run(args, capture_output=True, text=True)


def env_facts():
    """Report raw environment facts for the agent to reason about — no advice,
    no platform assumptions baked in. The installed Claude instance adapts; this
    just surfaces what it can't easily see. Printed as one machine-readable line."""
    return {
        "os": sys.platform,                               # darwin / linux / win32
        "term": os.environ.get("TERM_PROGRAM", ""),       # ghostty / iTerm.app / ...
        "handler_installed": os.path.isdir(APP_PATH),     # ClaudeResume.app present
    }


def ago(iso):
    try:
        t = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return "?"
    secs = (datetime.now(timezone.utc) - t).total_seconds()
    if secs < 3600:
        return f"{int(secs // 60)}m"
    if secs < 86400:
        return f"{int(secs // 3600)}h"
    return f"{int(secs // 86400)}d"


def ago_epoch(mtime):
    """Human age from an epoch timestamp (file mtime)."""
    secs = datetime.now(timezone.utc).timestamp() - mtime
    if secs < 3600:
        return f"{int(secs // 60)}m"
    if secs < 86400:
        return f"{int(secs // 3600)}h"
    return f"{int(secs // 86400)}d"


def is_toplevel_session(path):
    """projects/<dir>/<uuid>.jsonl — excludes subagents/tool-results/workflows."""
    rel = os.path.relpath(path, PROJECTS)
    parts = rel.split(os.sep)
    return len(parts) == 2 and bool(UUID_RE.match(parts[1]))


def parse_meta(path):
    """Pull cwd / first branch / title / earliest user prompt from a session."""
    cwd = branch = aititle = firstprompt = None
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            for i, line in enumerate(fh):
                if i > MAX_LINES:
                    break
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                except json.JSONDecodeError:
                    continue
                cwd = cwd or d.get("cwd")
                branch = branch or d.get("gitBranch")
                aititle = aititle or d.get("aiTitle")
                if firstprompt is None and d.get("lastPrompt"):
                    firstprompt = d["lastPrompt"]
                if cwd and branch and aititle:
                    break
    except OSError:
        return None
    return {
        "sid": os.path.basename(path)[:-6],
        "cwd": cwd,
        "branch": branch,
        "title": (aititle or firstprompt or "").strip(),
        "mtime": os.path.getmtime(path),
        "path": path,
    }


def all_sessions(exclude_sid):
    out = []
    for path in glob.glob(os.path.join(PROJECTS, "*", "*.jsonl")):
        if not is_toplevel_session(path):
            continue
        if os.path.basename(path)[:-6] == exclude_sid:
            continue
        m = parse_meta(path)
        if m:
            out.append(m)
    return out


def grep_sessions(query, exclude_sid):
    """Top-level session paths whose transcript contains the fixed string."""
    r = sh(["grep", "-rlF", "--include=*.jsonl", query, PROJECTS])
    hits = []
    for line in r.stdout.splitlines():
        if is_toplevel_session(line) and os.path.basename(line)[:-6] != exclude_sid:
            hits.append(line)
    return hits


def polluted_sessions():
    """Top-level sessions that are this tool's own prior runs (contain SENTINEL).
    They mention every PR, so they must not count as content matches."""
    r = sh(["grep", "-rlF", "--include=*.jsonl", SENTINEL, PROJECTS])
    return {line for line in r.stdout.splitlines() if is_toplevel_session(line)}


def ci_summary(rollup):
    if not rollup:
        return "—"
    passed = failed = pending = 0
    for c in rollup:
        state = (c.get("conclusion") or c.get("state") or c.get("status") or "").upper()
        if state in ("SUCCESS", "NEUTRAL", "SKIPPED", "COMPLETED"):
            passed += 1
        elif state in ("FAILURE", "ERROR", "CANCELLED", "TIMED_OUT", "ACTION_REQUIRED", "STARTUP_FAILURE"):
            failed += 1
        else:
            pending += 1
    total = passed + failed + pending
    if failed:
        return f"✗ {failed} fail / {total}"
    if pending:
        return f"● {pending} run / {total}"
    return f"✓ {passed}/{total}"


REVIEW = {
    "APPROVED": "✓ approved",
    "CHANGES_REQUESTED": "✗ changes",
    "REVIEW_REQUIRED": "· needs review",
    "": "·",
    None: "·",
}


def candidates_for(pr, repo_name, branch, strong_index, exclude_sid, polluted, limit=4):
    """Return up to `limit` ranked candidate sessions for a PR.

    Each is a heuristic guess, not a verdict — the agent makes the final call
    with the dates, titles, and signals provided here. Signals:
      branch-exact  session's gitBranch == PR head branch (strongest)
      url           transcript mentions the PR URL
      branch-name   transcript mentions the branch name
      same-repo     session cwd belongs to the PR's repo
    Sessions in `polluted` (this tool's own prior runs) are excluded.
    """
    cands = {}  # sid -> meta + signals/score

    def add(meta, sig, pts):
        if not meta:
            return
        c = cands.get(meta["sid"])
        if c is None:
            c = {**meta, "signals": set(), "score": 0}
            cands[meta["sid"]] = c
        c["signals"].add(sig)
        c["score"] += pts

    if branch and branch in strong_index:
        add(strong_index[branch], "branch-exact", 100)
    for path in grep_sessions(pr["url"], exclude_sid):
        if path not in polluted:
            add(parse_meta(path), "url", 20)
    if branch:
        for path in grep_sessions(branch, exclude_sid):
            if path not in polluted:
                add(parse_meta(path), "branch-name", 8)
    for c in cands.values():
        if repo_name and c.get("cwd") and ("/" + repo_name) in (c["cwd"] + "/"):
            c["signals"].add("same-repo")
            c["score"] += 15

    ranked = sorted(cands.values(), key=lambda c: (c["score"], c["mtime"]), reverse=True)
    return ranked[:limit]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exclude", default=os.environ.get("CLAUDE_CODE_SESSION_ID", ""))
    args = ap.parse_args()
    exclude_sid = args.exclude

    os.makedirs(RESUME_DIR, exist_ok=True)
    r = sh([
        "gh", "search", "prs", "--author=@me", "--state=open",
        "--json", "repository,number,title,url,updatedAt,isDraft", "--limit", "50",
    ])
    if r.returncode != 0:
        print(f"\n**Could not list PRs:** `{r.stderr.strip()}`\nTry `gh auth status`.")
        return
    prs = json.loads(r.stdout or "[]")
    if not prs:
        print("No open PRs authored by you. 🎉")
        return

    # strong index: gitBranch -> most-recent session
    strong_index = {}
    for m in all_sessions(exclude_sid):
        if not m["branch"] or m["branch"] in ("HEAD", "main", "master"):
            continue
        cur = strong_index.get(m["branch"])
        if cur is None or m["mtime"] > cur["mtime"]:
            strong_index[m["branch"]] = m

    polluted = polluted_sessions()  # this tool's own prior runs — never match these

    # fresh start: clear stale candidate files from previous runs
    for old in glob.glob(os.path.join(RESUME_DIR, "*.clauderesume")):
        try:
            os.remove(old)
        except OSError:
            pass

    prs.sort(key=lambda p: p.get("updatedAt", ""), reverse=True)

    out_prs = []
    for p in prs:
        repo = p["repository"]["nameWithOwner"]
        name = p["repository"]["name"]
        num = p["number"]
        v = sh([
            "gh", "pr", "view", str(num), "--repo", repo,
            "--json", "headRefName,statusCheckRollup,reviewDecision",
        ])
        head = ci = review = None
        if v.returncode == 0:
            try:
                d = json.loads(v.stdout)
                head = d.get("headRefName")
                ci = ci_summary(d.get("statusCheckRollup"))
                review = REVIEW.get(d.get("reviewDecision"), d.get("reviewDecision") or "·")
            except json.JSONDecodeError:
                pass

        cand_out = []
        for c in candidates_for(p, name, head, strong_index, exclude_sid, polluted):
            fname = os.path.join(RESUME_DIR, f"{name}-{num}__{c['sid']}.clauderesume")
            with open(fname, "w", encoding="utf-8") as fh:
                fh.write(f"{c['cwd']}\n{c['sid']}\n")
            cand_out.append({
                "title": (c["title"] or "").replace("\n", " ").strip(),
                "dir": c["cwd"],
                "age": ago_epoch(c["mtime"]),
                "date": datetime.fromtimestamp(c["mtime"], timezone.utc).strftime("%Y-%m-%d %H:%M"),
                "signals": sorted(c["signals"]),
                "score": c["score"],
                "resume_link": pathlib.Path(fname).as_uri(),
            })

        out_prs.append({
            "pr": f"{name}#{num}",
            "repo": name,
            "number": num,
            "title": p["title"],
            "url": p["url"],
            "draft": bool(p.get("isDraft")),
            "ci": ci or "?",
            "review": review or "?",
            "updated": ago(p["updatedAt"]),
            "head_branch": head,
            "candidates": cand_out,
        })

    print(json.dumps({"env": env_facts(), "prs": out_prs}, indent=2))


if __name__ == "__main__":
    main()

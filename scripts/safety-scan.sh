#!/usr/bin/env bash
# safety-scan.sh — quick grep for common secret patterns before committing.
#
# This is a guardrail, not proof of safety. Always review the diff manually too.
# Uses gitleaks if available, otherwise falls back to ripgrep.

set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if command -v gitleaks >/dev/null 2>&1; then
    gitleaks detect --no-banner --redact --source "$ROOT"
    exit $?
fi

if ! command -v rg >/dev/null 2>&1; then
    echo "Need either 'gitleaks' or 'rg' (ripgrep) installed." >&2
    exit 2
fi

PATTERNS=(
    'phx_[A-Za-z0-9]{20,}'                         # PostHog personal API key
    'sk_live_[A-Za-z0-9]{20,}'                     # Stripe live secret
    'sk_test_[A-Za-z0-9]{20,}'                     # Stripe test secret
    'pk_live_[A-Za-z0-9]{20,}'                     # Stripe live publishable
    'whsec_[A-Za-z0-9]{20,}'                       # Stripe webhook secret
    'rk_live_[A-Za-z0-9]{20,}'                     # Stripe restricted
    'ghp_[A-Za-z0-9_]{20,}'                        # GitHub PAT (classic)
    'github_pat_[A-Za-z0-9_]+'                     # GitHub fine-grained PAT
    'glpat-[A-Za-z0-9_-]{20,}'                     # GitLab PAT
    'xox[baprs]-[A-Za-z0-9-]+'                     # Slack tokens
    'hooks\.slack\.com/services/T[A-Z0-9]+/B[A-Z0-9]+/[A-Za-z0-9]{20,}'  # Slack webhooks
    'AKIA[0-9A-Z]{16}'                             # AWS access key
    'AIza[0-9A-Za-z_-]{35}'                        # Google API key
    '-----BEGIN [A-Z ]*PRIVATE KEY-----'           # PEM-encoded private key
    'client_secret\s*[:=]\s*["'"'"']?[A-Za-z0-9_-]{16,}'  # OAuth client secret literal
)

PATTERN=$(IFS='|'; echo "${PATTERNS[*]}")

# shellcheck disable=SC2086
hits=$(rg -n --hidden \
    --glob '!.git/**' \
    --glob '!scripts/safety-scan.sh' \
    -e "$PATTERN" \
    . 2>/dev/null) || true

if [ -n "$hits" ]; then
    echo "Possible secret matches:"
    echo "$hits"
    exit 1
fi

echo "No matches against common secret patterns."
exit 0

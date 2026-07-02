#!/usr/bin/env bash
# Preserve the audit script exit code. `isaaclab.sh -p` is not used here because
# this guard is part of validation and must fail closed on non-zero Python exits.
#
# Also fires validate.sh layer 7 (planning-surface consistency) at state-surface
# edit time: this V9 wrapper is the design's layer-7 firing wiring (§3層B — "存在≠防止"
# は layer 5 D1 で実証済 → 編集前後に必ず実行される V9 に配線)。A layer-7 FAIL
# (GEN drift / UPDATE-block freeze) fails this guard; layer-7 WARNs do not.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY="$REPO_ROOT/env_isaaclab/bin/python"

rc=0
"$PY" "$REPO_ROOT/scripts/audit_thread_vault_current_state.py" "$@" || rc=$?

l7=0
"$REPO_ROOT/scripts/validate.sh" --layer 7 || l7=$?

# Fail closed: freshness-audit failure takes precedence, then layer-7 failure.
if [ "$rc" -ne 0 ]; then
    exit "$rc"
fi
exit "$l7"

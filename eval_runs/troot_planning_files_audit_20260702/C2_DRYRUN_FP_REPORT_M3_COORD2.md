# C2 dangling-ref dry-run FP report (M3 / CP-C, %10 COORD2, 2026-07-02)

**Purpose:** per DESIGN §3層B (C2 = WARN 出発 → dry-run 0-FP 実測後に FAIL 昇格) + %12 CP-C 要求. Assess C2's false-positive rate on real planning surfaces to inform whether the node-id / sha legs can be promoted from WARN to FAIL.

**Method:** run each C2 leg against the live surfaces (map live, manifest non-GEN, LEDGER, index; SOMA separately) with the committed nest-snapshot node set + `planning_dangling_allowlist.txt` (3 entries). Node set = 238 nodes (incl synthesized stubs).

## Node-id leg (backtick `T-...` anchor → nest-snapshot node-set membership, minus allowlist)
- candidate refs (map + manifest-nonGEN + LEDGER + index): **2**
- dangling after nodeset + allowlist: **0**
- SOMA-only dangling (permanent WARN, 04-Specs = Rs 専権): **0**
- => **0 false positives, 0 true dangling.** The backtick anchor + membership + 3-entry allowlist is clean on current data.
- **Verdict: node-id leg is FAIL-promotable** (0-FP实测 achieved). Recommendation: %12 may promote the node-id leg C2 from WARN→FAIL, OR keep WARN conservatively (either is defensible; 0-FP means promotion won't cause spurious blocks). **Left as WARN in the committed checker** pending %12's promotion decision (design default = WARN-first).

## Sha-token leg (7-10 hex, ≥1 [a-f] → git cat-file -t)
- sha-like tokens found (surfaces incl SOMA): **34**
- valid git objects: **13** | invalid (would-flag): **21** (62%)
- invalid samples: `1b8f2739` (task_config hash in prose), `1d07449d`, `39f09a1c`, `3c06fad5`, `3cd6ff83`, `509ad193`, `54db6ef3`, `5fcfdf03`, … — mostly **false positives** (config/asset hashes, non-commit hex written as plain text without a `commit`/sha word or backtick anchor).
- => **~21 FP** at 62% → **NOT promotable**; a bare 7-10-hex scan floods. The design's mitigation (require `commit`/sha-word adjacency OR backtick context before git cat-file) is necessary before this leg is usable.
- **Verdict: sha leg stays WARN/deferred and is NOT wired live in the committed checker** (only assessed here in dry-run). Follow-up: add the commit/backtick-context anchor filter, re-run this FP dry-run, then decide promotion.

## Summary for %12
| leg | candidates | FP | verdict |
|---|---|---|---|
| node-id | 2 | 0 | FAIL-promotable (0-FP verified); left WARN pending %12 |
| sha | 34 | ~21 (62%) | keep deferred; not wired live; needs context-anchor filter |

Live C2 in `check_planning_consistency.sh` = node-id leg WARN (0 fired on clean baseline) + INFO note pointing here. No sha-leg live WARN (correct — would be 21 FP).

---
**ERRATA (2026-07-02 %12):** 本 report の「Left as WARN … pending %12」は同日 commit 70fa91619c (node-id leg WARN→FAIL 昇格、0-FP 条件成立 + %12 承認) により supersede 済み。corpus 注記: 0-FP の抽出候補は 2 件 (coverage 狭)。

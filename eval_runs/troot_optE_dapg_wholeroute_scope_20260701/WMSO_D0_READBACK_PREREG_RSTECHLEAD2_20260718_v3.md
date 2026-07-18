# [RS-TECH-LEAD2 → OPS-SUP-CODEX] WMSO D0 pre-registered scope — **v3** (fixes pN re-readback R1–R3)

- supersedes: v2 `…_v2.md` (sha256 `a46b0e9c…`), v1 `…_20260718.md` (sha256 `9e6ad050…`)
- node `T-ROOT-RS-TECH-LEAD2` → child `T-WMSO`; author `w2:pQ`; verifier `w2:pN`; custody `w2:p6`
- prepared_at: 2026-07-18 13:37 JST · status: **read-only, pre-execution (nothing built; no content extraction)**
- pN verdicts addressed: HOLD#1 (12:57, B1–B4) folded in v2; **HOLD#2 (13:12, R1 CRITICAL / R2 HIGH / R3 MED) fixed here**.
- pN-PASSed and retained unchanged: commit existence + hash concordance, as-read unchanged-from-freeze,
  owner/factual-vs-design/scope-fence, charter §5 six-schema mapping, §6 10-row trace **structure**,
  and v1 §A readback + §B boundaries.
- companion: **v3 frozen manifest** `WMSO_D0_FROZEN_SOURCE_MANIFEST_20260718_v3.tsv`
  (file sha256 `6abb176ec90160e05a78e75f1d87f682f6184a4922cae08838841d7d1556475f`,
  **aggregate `5d8d22163aba7d12cf8359f0fdbb7b5c698c1e22547645f8c0ab32e25e119467`**,
  freeze_repo_HEAD `a225376a6bdc93ea13a91dbe31a87902b4a6ae24`).

---

## R1 (CRITICAL) — well-formed manifest, correct taxonomy, honest HEAD

**Root cause of the v2 malformed rows (diagnosed empirically, not guessed):** for the 5 sources not in
HEAD, `git rev-parse "HEAD:<path>"` **echoes its argument to stdout on failure**, and the v2 generator's
`|| echo UNTRACKED` **appended** a second line → the `tracked` field carried a newline → `printf` split
each into 2 lines (NF=4 then NF=2). Separately, `thread_isaac_lab/tests/` is **entirely gitignored**
(`git status --porcelain` empty), which v2 mislabeled `clean`.

**Fixes applied in the v3 generator:**
- existence in HEAD tested with `git cat-file -e "HEAD:<path>"` (no stdout leak); `NOT_IN_HEAD` otherwise.
- gitignore tested first with `git check-ignore -q`; all fields newline/tab-sanitized.
- status taxonomy = `clean | modified | untracked | gitignored | ABSENT_IN_DECLARED_CLOSURE`.
- **self-assert `NF==5` on every non-comment row → EMPTY violation set** (verified before bank).

**Corrected numbers (v3 manifest):** **46 sources / 46 distinct paths**; status = **20 modified, 20 clean,
4 untracked, 1 gitignored, 1 ABSENT**. (The v2 "21/47" and pN's "19" were both artifacts of the malformed
rows; the true modified count is **20**.)

**HEAD honesty (R1b):** the shared tree **moves during work** — peer panes committed `d7a69be984`
(DDR#18 p5 lever) and `a225376a6b` (DDR#18 L3-Debate FAIL) around my window; my v2 bank `6b8691f4d0`
parent = `d7a69be984`, so v2's body "HEAD 437ab293e7" was stale. v3 records the **actual**
`freeze_repo_HEAD = a225376a6b` in the manifest header and treats it as *advisory*: the **`as_read_sha256`
(working-tree content) is the integrity pin**, guarded by the pre/post bracket. `tracked_blob` is
HEAD-relative-at-freeze, recorded for reference only.

**Change-during-inventory bracket** unchanged from v2: post-inventory re-hash of the closure vs this
frozen manifest; expected `changed_during_inventory=[]`; any delta → flag, re-freeze, re-quote.

---

## R2 (HIGH) — closure completion + two-stage fail-closed procedure

**Added to the frozen closure (were cited-but-outside in v2; all now hashed in the v3 manifest):**
- `thread_isaac_lab/envs/wrappers/vision_obs_assembler.py` — **vision-grounding assembler** (item 2 belief input).
- `thread_isaac_lab/mcp/safety_guard.py` — existing safety implementation (items 3/5).
- `thread_isaac_lab/thread-vault/07-Design/RL-Routing-Design.md` — substitute DAPG design authority.
- `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/TRAINER_NODE_DEFINE_RSTECHLEAD_20260712.md` — trainer node define + substitute authority.

**Two-stage closure (active checkpoint) — fail-closed procedure, registered:**
1. item-1 reads `policy_route_runner.py` / trainer config **only to discover** which checkpoint(s) the
   current path loads (path + sidecar/metadata). No policy content read yet.
2. **Before** reading any discovered checkpoint/metadata content, generate an **extension manifest**
   (`…_v3_ext.tsv`) freezing `as_read_sha256` + aggregate for the discovered set, and present its hash.
3. Only after the extension freeze is recorded may the discovered content be read.
This keeps discovery and content-read separated and every read pinned. Until stage 1 runs, active-policy
selection is `UNVERIFIED` (40 candidate files enumerated in v2 §B2, not silently omitted).

---

## R3 (MED) — taxonomy self-consistency in the §6 trace

v2's §6 used `ABSENT@D0` / `likely ABSENT` **before execution**, violating this doc's own B4 (absence may
only be `ABSENT_IN_DECLARED_CLOSURE` **after** a registered negative query; otherwise `UNVERIFIED`).
Corrected §6 trace (pre-execution states; **D0 registers contracts, claims NO gate PASS**):

| # | gate | pre-execution state | D0 contract field (to be filled by inventory) | downstream evidence owner / gate |
|---|---|---|---|---|
| 1 | algorithm independence | UNVERIFIED | typed lifecycle contract fields | D1 contract tests |
| 2 | vision grounding | UNVERIFIED (vision_obs_assembler in closure) | belief-input provenance flag (vision vs privileged) | D2/M0 |
| 3 | model calibration | UNVERIFIED (no Skill Dynamics Model yet) | calibration schema stub | M0 held-out/OOD |
| 4 | unknown-state abstention | UNVERIFIED | abstention route field | M0/S0 |
| 5 | safe interruption | UNVERIFIED (checkpoints not yet read) | checkpoint + compat-set schema | S0/V0 |
| 6 | anti-thrashing | UNVERIFIED | dwell/hysteresis field | O0/S0 |
| 7 | real-time | UNVERIFIED (no measured latency) | deadline schema (§4) | RT0 deadline tests |
| 8 | safety independence | UNVERIFIED (safety_guard/safety_envelope/fallback_guard in closure) | independent-safety contract | S0/V0 safety gate |
| 9 | comparative value | UNVERIFIED (D0 has no runs) | baseline set declaration | O0 offline compare |
| 10 | no premature claim | **non-claim contract registered; evidence pending** (NOT asserted as a passed gate) | explicit non-claim banner | S0/V0 two-key |

B4 taxonomy + read-only scope fence from v2 stand unchanged. Only `docs/DAPG_DESIGN.md` is
`ABSENT_IN_DECLARED_CLOSURE` (registered queries: `find … -iname '*dapg*'`, `grep -rIl 'DAPG_DESIGN' …`);
everything not-yet-read is `UNVERIFIED`.

---

## Disposition

v3 + well-formed v3 manifest banked (explicit-path atomic, no push); artifact sha + commit presented to
pN; **STOP** until pN re-readback **PASS**. No 6-item content extraction until PASS. (p6's 13:08 PASS was
the `437ab` assignment/tree-custody readback — a separate axis from this D0 evidence verdict.) v1 §A
readback + §B boundaries + production/training/inference/closed-loop UNAUTHORIZED remain in force.

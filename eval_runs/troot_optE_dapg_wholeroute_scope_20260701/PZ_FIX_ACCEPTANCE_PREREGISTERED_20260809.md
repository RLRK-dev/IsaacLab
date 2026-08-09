# pZ — pre-registered acceptance for the ruled `:2388` fix, written **before the fix exists**

**Author** pZ / IMPL-VERIFIER (`w2:pZ`), role brief `VERIFIER_ROLE_BRIEF_pZ_20260721.md` @ `4714493e64`
**Written** 2026-08-09 16:26 JST · lane tip at writing `03159efcaf2011117a33fa080dab315c552775bd`
**Status** written by pZ; **not committed by pZ** — see §6.

## Why this file exists

Every row below has been sent as a pane message and banked by a custodian as ledger summary. **That is not the same as my own artifact being queryable.** Tonight this desk filed four verdicts late precisely because they lived only in messages, and today a compression at another desk turned *"p5's leg discharged"* into *"dep-1 discharged"* — one dropped word, one changed subject. An acceptance table that p0 codes against, and that I will later judge by, should exist in my words, not only in someone's summary of them.

## 0. What is being accepted

Rs ruled 2026-08-09 ~16:0x JST (custody `20a4d2620d`, verbatim at `:1730` of that blob): 「腕を姿勢へ書き込むことは不可 すべてコントローラの司令で実現できるはず。」 The fix removes the live arm-pose write and reaches the home pose by servo command + real PD motion.

⛔ **This table judges the fix's *structure*. It does not judge whether the arms arrive, whether the pose is right, or anything about physical validity — Rs's court, role brief `:28`.**

## 1. Baselines, measured today by an AST walk (not by regex)

Method: `ast.parse` of the blob; every `Assign` / `AugAssign` / `AnnAssign` whose target resolves to a MuJoCo state attribute, receiver classified; plus every `Call` to `setattr` / `exec` / `eval` / `copyto` / `mj_copyData`.

| | `HEAD` (3839 lines) | tip `2fba2dfd67` (2912 lines) |
|---|---|---|
| live `d.qpos` writes | **1** — `:2388` | **1** — `:1653` |
| live `d.ctrl` writes | **7** — `1031, 2390, 2517, 2568, 2576, 3475, 3479` | **6** — `991, 1655, 1678, 1687, 2556, 2560` |
| live non-`ctrl` state writes other than `qpos` | 0 | 0 |
| dynamic write paths (`setattr`/`exec`/`eval`/`copyto`/`mj_copyData`) | **0** | **0** |
| control — the walk is alive | 1549 `Call` nodes parsed | 1205 |
| scratch receivers (unconstrained) | `sc` 24, `_ap` 3, `_sc2` 3, `_sci` 2, `_sv` 2, `_sc` 1 qpos | `sc` 16 … |

⚠ **Direction matters and is handled structurally, not by intent**: the walk classifies by the *assignment target's* receiver. `d.qpos ← scratch` is a write **to** `d` and counts; `scratch.qpos ← d.qpos` is a write to scratch and does not, whatever it reads. The 6+ evaluative read-outs fall outside the constrained set by construction.

## 2. The six rows

| # | row | requirement |
|---|---|---|
| 1 | live `d.qpos` | **1 → 0** — the fix's signature |
| 2 | live non-`ctrl` state writes (`qvel`/`qacc`/`act`/`mocap_*`/`xfrc_applied`) | **stay 0** |
| 3 | dynamic write paths | **stay 0** |
| 4 | live `d.ctrl` | **must not decrease relative to the fix commit's own parent** |
| 5 | scratch receivers | **unconstrained** — writing scratch is not the ruled act |
| 6 | **ordering** | between the `d.ctrl[arm] = HOME_POSE` block and the `START` read-out there must be **≥1 `mj_step` on the live struct** and a reference to the **existing** `SETTLE_S` / `SETTLE_TOL` |

⛔ **Row 4 was `≥ 7` and that was wrong.** 7 is `HEAD`'s number; the tip's is 6. A correct fix authored from the tip would have read 6 and **false-failed a fixed integer**. The parent-relative form cannot go stale — the same rule that says the base for *"what did this commit change"* is its own parent, never a moving tip.
⚠ Row 4's original rationale (*"if `qpos` goes to 0 and `ctrl` does not rise, the arms are commanded by nothing"*) is **dead by measurement**: p11 showed the servo target already exists at tip `:1655`, two lines below the write. ⇒ Row 4 is now **only a regression guard** — nobody deletes the existing command — and I claim nothing more from it. **Row 6 is the real discriminator.**

## 3. Row 6's control, taken while it still exists

A predicate that has never been seen to fire is not a check, and the fix deletes the only place this one can fire.

| | ctrl-write | `START` read | span | `mj_step` in span | `SETTLE_*` in span | predicate |
|---|---|---|---|---|---|---|
| tip `2fba2dfd67` | `:1655` | `:1658` | 2 lines | **0** | **0** | **FIRES** — defect present |
| `HEAD` | `:2390` | `:2393` | 2 lines | **0** | **0** | **FIRES** |
| synthetic fixed span (`ctrl` → `while err > SETTLE_TOL` → `mj_step` → `START`) | | | | 1 | 1 | **silent** — accepts a correct fix |

Verified by me at the tip, `:1651`–`:1662`: `:1653` the ruled write · `:1655` `d.ctrl = HOME_POSE` — **the servo target is already there** · `:1656` `mj_forward` · `:1658` `START = {…d.qpos…}` reads the written pose back · `:1659`–`:1662` seeds `solve_ik(near=START[t])` three rounds. ⇒ **Deleting the write alone makes `:1658` read the build pose, and every later IK converges elsewhere with no error.** The fix adds motion and moves a line; it does not add the command.

## 4. Corrections to my own published numbers, so nobody inherits them

| I published | truth | cause |
|---|---|---|
| `d.ctrl` = 4 | **7** | my regex required the assignment to start the line |
| scratch writes = 27 over 3 receivers | **35 over 6** (`_ap`, `_sc2`, `_sci` unlisted) | same line-initial assumption |
| row 4 `≥ 7` | parent-relative | 7 was one revision's number |
| (4) call-mechanism predicates "9/9" | true of nine fixtures, **not of the mechanism** | `[^)]*` cannot cross nested parens; and the obvious repair `.{0,300}?` silently loses multi-line, because a negated class crosses newlines and a dot does not. Correct form `[\s\S]{0,300}?`, now carrying three hostile fixtures as permanent controls |

⭐ Four of the five are one family: **a delimiter class encodes an assumption about nesting and about newlines, and both fail silently toward zero.** Where a structural walk is possible it is the corrective — rows 1–3 and 6 are AST or anchored-span, not shape-matching.

## 5. What this table does **not** close

- **Static, one file.** A write performed inside a helper in another module that receives `d` as an argument is outside it.
- The act-level closure needs a run of the driver, which **dep-3 now forbids**. ⇒ the fix will be reported **structurally clean in this file, with the act-level leg gated, not passed** — those are different sentences and I will not let the second borrow the first's word.
- A driver name assembled from pieces defeats any text scan; for the separate KINONLY instrument, D-4's runtime audit record is the primary evidence, not my regex.
- Nothing here is a statement about physical validity, about whether the arms arrive at HOME, or about mode A (commanded vs followed) — that blindness is accepted in writing elsewhere and is not repaired by this table.

## 6. Provenance and authority

All figures computed by pZ from `git show <rev>:<path>` and `ast.parse`; **zero modifications to tracked content by pZ**; ⚠ this file is itself a new untracked path in the shared tree. Env pin `/home/rlrk/env_isaaclab7/bin/python` (3.12.3; stdlib `ast` only).

⛔ **pZ has no measured grant to commit** — re-measured today at `HEAD`: `thread-vault/02-Workflow/Vault Write Permissions.md`, 63 lines, last touched 2026-07-02 22:27 (`55dae1a15a`); `pZ|IMPL-VERIFIER` → 0 **and the control `p4|RS-TECH-LEAD` → 0**, so that zero is not discriminating; `eval_runs/` → 0 with the control (other directory tokens) → 2; generic *CC (Agent)* column → 1. ⇒ This file is **written, not banked**; banking is requested of a custodian.

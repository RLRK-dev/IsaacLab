# pZ — verdict on `bc0bfe5b88`, the ruled `:2388` fix (nominated revision)

**Author** pZ / IMPL-VERIFIER (`w2:pZ`), role brief `VERIFIER_ROLE_BRIEF_pZ_20260721.md` @ `4714493e64`
**Judged against** the pre-registered table `PZ_FIX_ACCEPTANCE_PREREGISTERED_20260809.md` @ `934469208e`, sha256 `ed8445ee…6c77` — **written before the fix existed**
**Measured** 2026-08-09 16:42–16:46 JST · **filed** 16:46 JST
**Status** written by pZ; **not committed by pZ** — see §7.

## 0. Ordering, stated first because a receipt cannot repair it

`bc0bfe5b88` was authored **16:39:15** and `d14ffac4e2` **16:41:08**; both were **already on the lane** when I judged them (`merge-base --is-ancestor bc0bfe5b88 HEAD` → yes). The sequence in the fix chain put my table **before** landing. The nomination reached me at 16:43. ⇒ **This verdict is a confirmation from the lane, not a gate that preceded it.** No row failed, and that fact does not change what the order was.

## 1. The artifact

| | |
|---|---|
| nominated commit | `bc0bfe5b88` — *"Reach the start pose by servo command instead of writing it"* |
| its own parent | `fcac16f1e3` (every comparison below uses this, never a moving tip) |
| scope | **16 / 5**, one file |
| successor also checked | `d14ffac4e2` — *"Have the settle report the clearance it traverses"*, **17 / 0** |
| `ur15_steps_wired.py` content sha256 | **`12f9d034a6568ac7…`** — ⚠ the long-standing `6ca7247513ca117c…` is **retired**; any report still carrying it is stale |

## 2. The six pre-registered rows — **PASS**, both commits, each against its own parent

| # | row | `bc0bfe5b88` | `d14ffac4e2` |
|---|---|---|---|
| 1 | live `d.qpos` == 0 | **0** (was 1, `:2388`) | 0 |
| 2 | live non-`ctrl` state writes == 0 | 0 | 0 |
| 3 | dynamic write paths == 0 | 0 | 0 |
| 4 | live `d.ctrl` ≥ parent | **7 vs 7** — no line added, none removed | 7 vs 7 |
| 5 | scratch receivers | unconstrained, by design | — |
| 6 | settle exists **and** is ordered | **PASS** — interior span `:2393`–`:2403`, live `mj_step` 1, `SETTLE_*` 2 | PASS, interior `:2393`–`:2420` |

⚠ **Span convention, so a difference is not read as a discrepancy**: p0 reports row 6 as `:2392 → :2404` (the two anchors); I report `:2393`–`:2403` (the lines strictly between them). Same region, same conclusion.

Method: `ast.parse` of the blob — every `Assign`/`AugAssign`/`AnnAssign` whose target resolves to a MuJoCo state attribute, classified by the **assignment target's receiver**, so the direction split (`d.qpos ← scratch` counts, `scratch.qpos ← d.qpos` does not) is structural rather than a judgement of intent; plus every `Call` to `setattr`/`exec`/`eval`/`copyto`/`mj_copyData`.

## 3. The five deleted lines are exactly the right ones

Read from the diff, not inferred: the two *"start from home / zero is arms crossed"* comments, the `for _k4, _a4 in enumerate(QADR[_t4]): d.qpos[_a4] = HOME_POSE[_k4]` loop, and the old print. **The servo target at `:2392` is untouched.** ⇒ the fix removed a write and added motion — it did not add the command, which was already there.

## 4. p11's three requirements, checked one at a time

1. **Servo only** — no `d.qpos` assignment survives; no scratch-to-`d` copy appeared.
2. **Existing thresholds, none invented** — the loop bounds on `SETTLE_S / m.opt.timestep` and breaks on `max|d.qpos − HOME_POSE| < SETTLE_TOL`. **No new constant.**
3. **`START` read after the settle** — `:2421`, with the reason written above it in the file: *"START must be the pose the arms REALIZED, never the one commanded."*

## 5. One finding — on the **voluntary** by-product, so it fails nothing

`d14ffac4e2` records the traverse minima using `arm_pair_min` (arm↔arm) and `column_gap` (`:1277`, *"closest … to the yoke mast"*). **`furniture_gap` (`:400`, the table and saddles) is called zero times inside the settle span `:2398`–`:2417`.**

⇒ The recorder watches **arm↔arm (+491.3 mm at the endpoint) and arm↔column**, and **not arm↔table — the +19.8 mm pair, which is the tight one.** ⛔ The label is honest: `:2416` prints *"arm↔column"* and claims nothing about the table, so the print misleads nobody; the risk is a reader taking *"settle traverse worst"* as the traverse's worst when it is the worst over **two of three pairs**. One call beside the other two closes it, at p0's discretion. I pre-committed that I would not fail a fix that omits this by-product entirely, and I do not.

✅ And the density is published on the line that carries the number — `:2417` *"sampled every 10 steps over the traverse, endpoints included"*. Transients between samples remain unrecorded, **stated by the instrument rather than discovered later**.

## 6. Verdict, in the three clauses pre-committed before the fix existed

> **The fix is structurally clean at the commits I checked · the settle exists and is ordered correctly · whether the arms pass clear on the way is unmeasured and gated.**

⛔ **Not claimed**, and the first clause does not carry any of these:

- anything about **physical validity** — Rs's court, role brief `:28`;
- that the arms **actually arrive** at HOME (that is the settle's dynamic outcome, and no static reading produces it);
- that no **helper in another module** receiving `d` writes it — this is static and one file;
- anything about **the day after**: `check_control_method.sh:38` scans `thread_isaac_lab/envs` only, so this directory is still outside Layer 8's population and no standing guard would notice a regression here. Its predicate *would* have matched the ruled line — I evaluated it (`(phys_jq|joint_q|qpos)\[[^=]*\][[:space:]]*=[^=]` matches `d.qpos[_a4] = HOME_POSE[_k4]`, control: a read does not) — so what failed was never what the guard looks for; it was where it was pointed.

## 7. Provenance and authority

All figures computed by pZ from `git show <rev>:<path>` and `ast.parse`; nothing was executed — no driver, no instrument, no guard. **Modifications to tracked content by pZ: 0**; ⚠ this file is itself a new untracked path in the shared tree. Env pin `/home/rlrk/env_isaaclab7/bin/python` 3.12.3 (stdlib `ast` only; the pin is convention here, not a dependency).

⛔ **pZ has no measured grant to commit** — re-measured 2026-08-09 at `HEAD`: `thread-vault/02-Workflow/Vault Write Permissions.md`, 63 lines, last touched 2026-07-02 (`55dae1a15a`); `pZ|IMPL-VERIFIER` → 0 **and the control `p4|RS-TECH-LEAD` → 0**, so that zero is not discriminating; `eval_runs/` → 0 with the control (other directory tokens) → 2. ⇒ **written, not banked**; banking is requested of a custodian.

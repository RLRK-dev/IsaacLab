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

---

# ⛔ ADDENDUM 2026-08-09 16:55 JST — commits three and four, and **one live crash the table cannot see** (ruling A: nothing above rewritten)

This discharges the forward condition I stated when the verdict was filed: *"if a third commit lands on that file, my verdict does not cover it… I will re-run the table against that commit's own parent unprompted."* Two landed; both are covered here.

## A1. Hash namespace, named on every figure from here on

⚠ Two hash functions were in play across desks and the difference read as a moving object when nothing had moved. **Every hash in this file — above and below — is `sha256` of the file's bytes.** For the final state I give both, each with its function named:

| | |
|---|---|
| `ur15_steps_wired.py` **content sha256** | `4981b37a8cc65d41ff6db8c97ed8025400e80c88409b7c829a6b0ee8c918c166` |
| the same object's **git blob SHA-1** | `7830f79dd59f069cf34a44d15341bd543234f46a` |

⇒ **retired, and named as retired**: `6ca7247513ca117c…` (pre-fix) and `12f9d034a6568ac7…` (§1 of this verdict, correct for the first two commits). A report still carrying either is stale. ⭐ **A hash becomes a pin only with its function's name attached** — the hash-shaped form of the line-number law this chain already adopted.

## A2. The table, on both new commits, each against its **own parent**

| commit | scope | parent | rows 1–5 | row 6 (ordering) |
|---|---|---|---|---|
| `01b2149ad3` *"Watch the tight pair too"* | **9 / 4** | `4158f7a777` | qpos 0 · non-ctrl 0 · dynamic 0 · ctrl **7 vs 7** | **PASS** — interior `:2393`–`:2425`, live `mj_step` 1, `SETTLE_*` 2 |
| `d35d3e8973` *"Guard the traverse recorder against an absent reading"* | **2 / 1** | `e16a1ea4fc` | same | **PASS** — interior `:2393`–`:2426` |

⇒ **six rows PASS across all four commits.**

✅ **My §5 finding is closed at the right grain.** `01b2149ad3` puts `furniture_gap` into the settle loop beside `column_gap` — **and the label moved with the coverage** (`:2416` now reads `arm<->column/furniture`). A coverage change that left the label alone would have been the mirror defect: a print claiming less than it measures is survivable, one claiming more is not.

## A3. ⛔ A live crash, outside every row, found while verifying

```
:2403        _v, _w = arm_pair_min(d, want_who=True)     ← no None guard
:2404        if _v < _traverse_arm:                       ← compares directly
:2414                if _v6 is not None and _v6 < _traverse_env:   ← the env pair IS guarded
```

- `arm_pair_min` **returns `None`** when nothing is within range — its own comment says so: *"⛔ None, not the cutoff, when nothing is within range"*.
- `ARM_PAIR_CUTOFF = 4.0 * GRIP_HALF_SPAN` = 4.0 × 0.044 = **0.176 m = 176 mm**.
- The diagnostic's own endpoints: arm↔arm **491.3 mm** at `qpos=0` and **194.2 mm** at HOME — **both outside that cutoff**, at 2.8× and 1.1×.
- `None < 1e9` → `TypeError: '<' not supported between instances of 'NoneType' and 'float'` (control: `0.05 < 1e9` fine).
- The first sample is `_s4 = 0`, because `0 % 10 == 0`.

⇒ **`d35d3e8973` guarded the env pair and left the arm pair unguarded one line above it — the class was fixed at the instance.** And the two are not symmetric in likelihood: the env cutoff comfortably contains +19.8 mm, while the arm pair's only measured distances are **1.1× and 2.8× its own cutoff**, so the unguarded one is the one certain to return `None`.

⚠ **Grade, honestly**: this is a source reading plus arithmetic on published endpoint numbers plus a one-line interpreter check of the comparison. It is **not** a run — dep-3 gates wired — so I can name the defect but not assert it fires at exactly step 0 in the real cell: the settle now starts from the **build pose**, which nobody has measured. Both configurations that *have* been measured are outside the cutoff.

⛔ **This is not a row failure.** My six rows measure state writes and ordering; a runtime `TypeError` is invisible to every one of them, exactly as *"whether the arms pass clear"* is. It is a defect found while verifying, reported as its own thing — and it is the second time in this chain that the risk rode on the **by-product**, not on the fix.

## A4. Verdict, restated over four commits

> **The fix is structurally clean at all four commits I checked · the settle exists and is ordered correctly · whether the arms pass clear on the way is unmeasured and gated · and the traverse recorder that would answer that third clause raises on its first sample unless the arms begin within 176 mm of each other.**

The fourth clause is new and it is **not** about the fix: it is about the instrument bolted to it. One guard on `:2404`, in the form already present at `:2414`, removes it.

---

# ⛔ SECOND ADDENDUM 2026-08-09 17:10 JST — commits five and six, the KEEP word, and one finding that is **new** (ruling A: nothing above rewritten)

## B1. My own A1 is stale, and I am not exempt from the rule I have been applying all night

A1 named `4981b37a…` as the final content sha256. It was correct **for four commits**. Two more landed. Every hash below is named with its function:

| | |
|---|---|
| `ur15_steps_wired.py` **content sha256**, current | `8fae5334e85e6af5cf1efffdd8dcdca76c3b999006a8e5374012d93466da5bbf` |
| the same object's **git blob SHA-1** | `ae8aa42d49dd2bb817f927dfe84a148f8e269a6a` |

⇒ **retired, named as retired**: `6ca7247513ca117c…` (pre-fix) · `12f9d034a6568ac7…` (§1, two commits) · `4981b37a8cc65d41…` (A1, four commits) · `b63400555573585f…` (five commits).

## B2. The table on the fifth and sixth commits — **PASS**, each against its own parent

| commit | scope | parent | rows |
|---|---|---|---|
| `755eae7ddd` *"Guard the arm pair too, which is the one that needs it"* | **5 / 1** | `2e11b6651f` | six rows PASS; ordering interior `:2393`–`:2430` |
| `2a3b5825b7` *"Say nothing was in range instead of printing the sentinel"* | **13 / 2** | `bd1c12e19b` | six rows PASS; ordering interior `:2393`–`:2441` |

⇒ **six rows PASS across all six commits.** The guard is `if _v is not None and _v < _traverse_arm:` — the form already at `:2414`. The print routes both readings through `_traverse_say`, which takes the file's own phrasing from `:2361`/`:3777`.

## B3. Clause four is discharged, and it discharged in two hops

crash → sentinel-printed-as-data → closed. ⭐ **A crash is loud; a sentinel wears the face of data** — the guard that removed the crash is what made the sentinel reachable, so the second hop existed only because the first was fixed.

## B4. ⛔ A correction of my own, caught by one grep

I had half-drafted a finding that `_traverse_say` was *"a second private absence-spelling, a thirteenth site of what `gap_mm` centralizes, with a different magic number."* **Measurement dissolved it.** There are **two absence kinds** in this file, both pre-existing, and the new print uses the right one for its kind:

- `gap_mm:1891` — `return absent if x is None else f"{x * 1000.0:+.1f} mm"` — keys on `None`: **a reading that was absent**. 12 call sites.
- `_traverse_say:2430` — `if v > 1e8` — keys on the **sentinel**: an accumulator that was never assigned. And `init 1e9 / test 1e8` is the file's own idiom, in use before tonight at `:3791` and `:3853`.

⇒ `gap_mm` **cannot** be a drop-in here: the guard converts `None` into *skip*, so what reaches the print is a float sentinel, never `None`. ⭐ The `:1880` history ("individual guards were not working") is real and it is about the **reading** kind, where the centralization exists and holds. It is not evidence about these four lines. **The difference between my two drafts was one grep.**

## B5. ⛔ NEW FINDING — the declared search radius does not describe the query that produced most of the numbers

The env line prints one radius for a value drawn from **two** queries:

```
:2436  _traverse_say(_traverse_env, …, 'arm<->column/furniture', ARM_DECIDE_CUTOFF * 1000)
```

- `furniture_gap:402` — `cut = ARM_DECIDE_CUTOFF if cutoff is None else cutoff` ⇒ **16 mm** (`ARM_DECIDE_CUTOFF = 2·ARM_CLEARANCE = 4·CABLE_R = 4 × 0.004`). Declared radius correct for this half.
- `column_gap:1295` — the prefilter is `if cutoff is not None and …`, and the settle calls it **with no cutoff** ⇒ **the prefilter is skipped entirely**; the range is `mj_geomDistance`'s `distmax = 1.0` at `:1299`, i.e. **1000 mm**. Its `:1307 if best > 1e8` can then never fire, so this half never returns `None` either.

⇒ **A column reading of +80.1 mm — the diagnostic's own HOME endpoint — would print as a value beside a declared search radius of 16 mm.** A number larger than its own stated radius is self-contradictory on its face, and the absence sentence *"nothing within the 16 mm search radius"* is unreachable for a pair one of whose queries searches to a metre.

⚠ **This is the fourth finding in the four voluntary lines, and it is a reporting defect** — not a crash, not in the fix, and it fails no row. ⭐ It also sharpens the citation rule: *cite the value and its derivation* is not enough — **the radius must be the one the query that produced the number actually used.** The derivation here is right and attached to the wrong query.

## B6. My word on keep-versus-revert: **KEEP**, with the grounds and the two conditions that would have reversed it

- **No write path to state** — AST over the settle span (`:2398`–`:2441`): every assignment target is a plain local name (`_traverse_arm`, `_traverse_arm_who`, `_traverse_env`, `_traverse_env_who`, `_v`, `_w`); attribute targets **0**, subscript targets **0**. ⚠ that query covers assignment statements; for-loop targets are names by inspection. ⇒ the recorder's whole range is **crash or wrong number — never a moved arm**.
- **Every finding came from reading** — the tight pair, the env `None`, the arm `None`, the sentinel print, and B5. **Not one needed a run**, so the discovery mode never depended on the gated resource.
- **It is the only instrument that can discharge clause three of this verdict**, and reverting leaves that clause open at the price of a future Rs authorization.
- ⛔ **I would have said REVERT if either held, and neither does**: a write path to state (measured: none), or a defect surfacing **after** a run rather than before (all surfaced before).
- ⛔ **What I do not claim**: that these lines carry no unknown shape. Nobody can, and I will not manufacture grounds for a "no". The claim is bounded — *if* one exists, its range is crash-or-wrong-number, and it is findable by reading.

## B7. Verdict over six commits

> **The fix is structurally clean at all six commits · the settle exists and is ordered correctly · whether the arms pass clear on the way is unmeasured and gated · and the recorder that will answer that third clause on the authorized day declares, for its environment pair, a search radius that only one of its two queries uses.**

The fix itself is unchanged and has been correct since `bc0bfe5b88`.


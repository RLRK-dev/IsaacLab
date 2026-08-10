# pZ — arm-level leg RESULT: audit + independent re-derivation, and the UR15-B formalization

**Author** pZ / IMPL-VERIFIER (`w2:pZ`) · **Written** 2026-08-10 10:04 JST. Naming per m-p18-256: **Rs1 = the human; Rs2 = p4/CC**. UR15-B is Rs1's name (ruling 09:4x, custody `e00a990c45`).
**Rows** = `PZ_ARM_MIRROR_LEG_PREREG_20260810.md` @ `388f9892a9` (sha `ef1d78465f…`), banked before this leg ran.
**Objects**: the 07-29 acceptance `UR15_MIRROR_ACCEPTANCE_20260729.txt` + `ur15_mirror_acceptance.py` @ `38678f5946`; the arm assets; Rs1's reference `~/Downloads/ur15-dual-arm-cell/ur15-dual-arm-cell.json`; and the formalization commit **`c737f6974e`** judged against its own parent `3ad43a3914`.
⛔ Nothing ran that was wired; no run authorization exists, is held, or is sought. Physical validity remains Rs1's court.

## A — audit of the existing instrument

| # | row | result |
|---|---|---|
| **A1** | denominators | **24 poses**, confirmed twice independently: the reference JSON's own `poses` map has **len 24**, and the record's control leg has 24 rows. × 2 position quantities (tool0, grip) = **48 pairs per leg**, four legs. The relayed "8 poses" was **3× small** and is corrected at source (p18 owned it; the asset header now carries 24). |
| **A2** | does each leg discriminate? | **control: PROVEN, first time** — at today's C-2 mounting it reads **0/48, worst 241.1 mm**; at 0.22/45 it reads 48/48. A control that has only ever passed is a declaration; this one has now been seen to fail. **negative: fires** (0/48, worst 1357.5 mm). **limit leg: blind, and the record says so** — I verified the declaration rather than inherit it: measured through the loader, all six stock ranges are symmetric about zero, so `[-hi,-lo] == [lo,hi]` and the row **cannot** fail on these assets; the mirrored ranges do satisfy the rule (`True`). |
| **A3** | can the grip-offset solve absorb pose error? | **No.** Frame-free check of my own over all 48 arm-poses: `|grip − tool0|` ∈ [0.189990, 0.190005] m against the reference's stated 0.19 m, worst deviation **0.0099 mm**. ⚠ This is a **different quantity** from the record's 0.0052 mm (theirs = per-pose deviation of the solved tool-frame vector from its own mean; mine = scalar distance against the nominal constant, so it also carries the solve's own offset). Both bound the same conclusion; neither contradicts the other. |
| **A4** | dead queries | One found, in **my** instrument, not theirs: my XML-text path could not read `ur15_base_mirrored.xml` at all (§F5) — re-run through the loader and the file level instead. Every predicate re-measured at its own site. |

## B — independent re-derivation (my numbers, none through p0's code)

| # | row | result |
|---|---|---|
| **B1** | the reference, read by me | ⭐ **The reference cell is itself exactly mirrored** — `|M·tool0_L − tool0_R| = 0.0000 mm` on **all 24 poses**, same for the grip point. **Nobody had checked the ground the whole acceptance stands on**; it holds exactly. ⭐⭐ And its right-arm joint values are **not** a pure sign flip: `R = −L` for shoulder / forearm / wrist_2 / wrist_3, but **`R = −L + π` for upper_arm and wrist_1**, constant to 1e−6. Identical L/R joint values: **0 of 24**. |
| **B2** | forward kinematics, mine | I built FK from the **reference JSON's own published chain** (`joint_origins_xyz_rpy`, `joint_axis`, `base_rotation_rpy`, `flange_from_wrist_3_rpy`, `tool0_from_flange_rpy`, `arm_base_pose_*`) — no MJCF, no MuJoCo, no p0 code — and reproduced the published tool0 for **both** arms: worst **0.0079 mm** (left) / **0.0074 mm** (right), 24/24 within the 1.0 mm bar. **A second, fully independent path lands inside the record's own error band.** Control: raising the base 10 mm gives 0/24 within the bar (**fires**).
⚠ **That band re-measured by me, because the quoted one was a subset**: parsing every row of the record, the three passing legs span **0.0013–0.0076 mm** (144 values; control 0.0013–0.0076, test 0.0013–0.0076, formula 0.0017–0.0076) and the negative leg spans **357.68–1357.55 mm**. The widely-relayed floor "0.0023" is an artifact of a partial view, as is the negative's "628–1018". The durable form is the file's own summary lines (`:37/:65/:93/:121`), not row quotes — including mine. |
| **B3** | the asset mirror relation | **File level**: symmetric Hausdorff(A·V_L, V_R) = **0.000e+00** on all **7** arm meshes, and the identity control fires on **7 of 7** (unlike the hand, where 3 of 8 were x-symmetric) — winding preserved both sides. **Loader level**: `pos → A p` exact, `quat → A R A` worst 6.7e−16, `axis → −A a` exact with **6/6** axes discriminating. ⚠ Two meshes read non-zero **at loader level** (42.4 mm, 18.0 mm) — that is MuJoCo's per-mesh principal-axis re-framing, exactly the effect p0's gripper acceptance documented, and the file-level zero is what interprets it. A leg that stopped at the loader would have reported a defect that is not there. |
| **B4** | what the position test cannot see | joint **limits** (blind by A2), collision geometry, inertias, and everything dynamic. Restated here, not inherited. |

## C — the UR15-B formalization, `c737f6974e` against parent `3ad43a3914`

| # | row | result |
|---|---|---|
| **C1** | parent-relative | 2 files: `ur15_base_mirrored.xml` (+14/−1: model name `ur15_mirrored` → **`UR15-B`**, provenance header, sim-only warning) and `ur15_steps_wired.py` (+13/−3: docstring + one identity print). |
| **C2** | identity is naming, not geometry — **machine-proven** | I compiled the model **before and after** and compared field by field: `body_pos`, `body_quat`, `jnt_axis`, `jnt_range`, `jnt_pos`, `geom_pos`, `geom_quat`, `geom_size`, `body_mass`, `body_inertia`, **and `mesh_vert`** — **all bit-identical**. ⇒ **No number changed**; the rename does not re-open A/B, and the 07-29 evidence transfers to the UR15-B identity. |
| **C3** | the caveat travels | The header carries it verbatim at `:14`: *"no position-vs-reference evidence exists or can exist at the C-2 mounting"*, alongside the corrected 24 poses × 2 = 48/48 at `:10` and the record's own `:37/:65/:93`. The superseded "eight poses" appears once — **named as superseded**, which is the right way for a retired number to survive. |
| **C4** | no run | Nothing executed; the conditional authorization ② remains unfired and is not mine to fire. |

## F — findings (both already routed; recorded here for the object)

- **F4 — the evidence is anchored to a mounting the cell no longer has.** The instrument imports the mounting live from `ur15_cell_spec:47` while Rs1's reference publishes positions only at the built mounting. Re-run by me in an isolated copy: at today's C-2 defaults **all four legs 0/48 including the control**; with the C-2 row-7 overrides it reproduces the banked record **byte-identically**. The FAIL is the cell having moved, not the mirror having broken. Two by-products: the control became a **proven** discriminator, and **the C-2 row-7 override precedence I verified this morning is what keeps this evidence reproducible at all**.
- **F5 — the header broke standards XML for 5 minutes.** `--` inside an XML comment (XML 1.0 §2.5) made `ur15_base_mirrored.xml` unreadable to expat/ElementTree while MuJoCo's lenient parser loaded it identically (nbody 7). Found because **my own B3 row died on it**. Fixed at `6a542f45dd` (em dashes); **verified at HEAD: well-formed again**. The sentence that broke it was the one honestly naming my corrected denominator — the cost of that honesty was two hyphens, and the content was right to keep.

## Verdict

**The arm mirror holds, and it now holds on two independent paths.** p0's 07-29 acceptance is sound as an instrument (denominator re-derived, control proven to fire, negative fires, blind leg blind exactly where it says), its object has not drifted (0 commits since), and its central claim is reproduced by a re-derivation that shares no code with it — my own FK from Rs1's reference chain lands both arms inside 0.008 mm. The UR15-B formalization is naming only, machine-proven. What remains unmeasured is stated, not implied: no position-vs-reference evidence at the C-2 mounting (impossible by construction), joint limits, collisions, inertias, dynamics — and the whole-cell composition, which no desk has measured and this one cannot without importing the driver.

## Provenance

`git show`/`rev-parse`/`numstat`; `sha256sum`; my own binary STL reader + `scipy.spatial.cKDTree`; my own FK from the reference JSON via `scipy.spatial.transform`; MuJoCo model loads for field-by-field comparison; one isolated `cp -r` re-run of p0's instrument at two mountings (their tracked record never touched). Zero tracked-content modifications by pZ. **Written, not banked; banking requested of a custodian.**

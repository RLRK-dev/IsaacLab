# pZ — pre-registered reading rules for the KINONLY "+0.0" class, and a measured constant the completed cell carries

**Author** pZ / IMPL-VERIFIER (`w2:pZ`), role brief `VERIFIER_ROLE_BRIEF_pZ_20260721.md` @ `4714493e64`
**Written** 2026-08-09 22:55 JST. Naming per the ruling relayed in m-p18-256: **Rs1 = the human; Rs2 = p4/CC** — first use in this artifact, adopted throughout.
**Trigger** = m-p18-259's evidence note to me ("SD1-7 '+0.0' cells are attribution-unknown"). A note my future leg will rely on is not accepted on relay — it is grounded from the lane. This file records the grounding, the reading rules it produces (pre-registered BEFORE any nominated table exists), and one new measured fact found on the way.

## 1. The relay's pins, reproduced at this desk

| pin as relayed | reproduced here |
|---|---|
| artifact §8.43 @ `82a99c8dda`, sha `af2a8ecee7…` (truncated in relay) | `P0_SCRATCH_PATH_SCOPE_…20260808.md`, heading at `:1989`, blob sha256 **`af2a8ecee73267a19156c6ec8ca6dc8b51990c5e411f5dec4dfba3890d987715`** — full form computed here; a partial hash is a collation note, not a pin |
| ledger §1362 @ `0d2b91c496` | read from the blob: +14 lines, content matches the relay (checkpoint, three finds, pZ note) |
| probe committed in the same commit | `p4_ur15_sim_20260727/probe_geomdistance_exact_zero.py`, +81 lines @ `82a99c8dda`; read in full — read-only kinematics (`mj_kinematics` + `mj_geomDistance`), never steps |
| instrument lineage SD5-7 | `921ca08fa6` → `5ec54aff1b` → `49c72643a5` all exist; SD7 = `49c72643a5` (22:27) |

## 2. Freshness: the relay's "next iteration" items are ALREADY AT HEAD

`bbc500b636` (22:44:58, "Complete the cell and replace the jitter guard with proof") landed **after §8.43 was banked (22:42) and before m-p18-259 was sent (22:46)**. No fault anywhere — but a reader of m-p18-259 alone would plan around work that is already done:

- **find (b) fixed**: mast trio (stem corrected to the spec's 0.37→1.53 form, foot, crown capsule), three saddles at REST_X, clips from `spec.CLIP_PARTS`, table thickness from `TABLE_HZ`.
- **guard v2 landed, stronger than announced**: the jitter requery is REMOVED; every reading that is exactly 0.0 **or witness-inconsistent** (`abs(|fromto| − |dist|) > 1e-6 + 0.01·|dist|`) resolves against a **provable lower bound** (bounding radii + exact point-to-primitive for sphere/box/cylinder/capsule). Positive bound → substituted as a conservative stand-in, pair name tagged `" >=bound"`. No positive bound → kept as contact. Counters `_GUARD = [suspect, bound-substituted, kept-as-contact]` published in the audit block. Read from the diff at this desk.

Worktree == HEAD (`0d2b91c496`) for both instrument files (checked by `git status` + sha256: worktree `7153162f94…`, ≠ SD7 blob `5ea55880ff…`).

## 3. Pre-registered reading rules for my leg (written before any nominated table exists)

- **R1 — SD1-7-era "+0.0" cells**: attribution-unknown = (true contact | stable sentinel), never read as a contact by my leg. Discharged only by a guard-v2-era re-measurement or a per-pair proof. This adopts m-p18-259's note, now grounded.
- **R2 — guard-v2-era readings**: a `" >=bound"`-tagged value is a **conservative stand-in**, admissible as "provably ≥ bound", never as the distance itself. A bare 0.0 at guard-v2 era means "no positive bound available" — admissible as TOUCHING for gating (conservative), never as evidence of true geometry.
- **R3 — witness consistency is a discriminator my pair-per-row control gains**: a row whose |fromto| disagrees with its claimed distance by >1%+1µm is self-refuting (the measured case: 301.9 mm centre distance, claimed 0.0, ~520 mm witness). My leg spot-checks witness consistency on sampled rows from the bank.
- **R4 — bank consumption**: `_gen/kinonly_solutions.json` is **untracked** (`git ls-files` empty for `_gen/`; measured) — a mutable path overwritten by every run. Its `meta` self-identifies parameters, stack, and cell provenance but **not the producing instrument revision**. My leg pins any consumed bank by **content sha256 at read time** and records the instrument revision the re-measurement runs under. Today's bank: sha256 `788fe8748fd5acbd0909b8fdf1de73e521544f01d7ef571d6b520d5653ff1fa9` as-read 22:49:46 JST, 25 rows, every row carrying q_L/q_R + its own witness columns (`env_pair`/`arms_pair`/`along_*`); `meta.purpose` verbatim: "winner joint vectors per row so a verifier can PLACE and re-measure every reading without re-running the search".
- **R5 — verdicts do not cross worlds**: a bank row's verdict belongs to the cell build it was measured in (demonstrated in §4-5: same q, env reading +2.87 mm in SD7's world, −79.22 mm in the completed world). My leg never mixes bank verdicts across cell revisions.

## 4. The committed probe, run at this desk (read-only)

Command: `/home/rlrk/env_isaaclab7/bin/python probe_geomdistance_exact_zero.py` from its own directory; instrument = worktree == HEAD; bank = SD7's (pin above). The probe never steps — this is the static-instrument class, no run authorization involved.

- Probe row = bank row STEP 2 (single). Three placements (original bits / ulp-shifted / original again) printed **identical** minima; `exact-zero minima seen: 0 — none at these poses` (the probe's own honest wording). ⇒ The flip mode did **not** re-witness in the completed world at these poses. **This does not contradict p0's measurement**: the flip is a narrowphase artifact of specific mesh pairs at specific relative poses, and `bbc500b636` changed the world (geometry and geom ids). The artifact class stays proven by §8.43 + the probe's committed record; my run adds only "not at these poses in this world".
- **Control that transferred exactly**: arm-arm minimum 36.4927 mm, pair geom 17 (`Lg_right_coupler`) ↔ 52 (`Rg_base`) — byte-equal to the bank's recorded `arms_mm` 36.49273762 / `Lg_right_coupler#15 <-> Rg_base#50`. Robot-only geometry is unchanged across the cell completion; only the cell moved. This is the discriminating pair for §5.

## 5. ⭐ New measured fact: the completed cell carries a constant crown↔base overlap of −79.2182 mm

- Bank row STEP 2 recorded (SD7 world): `env_mm = +2.8675`, pair `L_wrist_2_link#7 <-> stem` — the stem was the only mast part that existed.
- Same q placed in the completed world: L-env = R-env = **−79.2182 mm**, pairs geom 4/43 ↔ 3 = **`L_base_link_inertia` / `R_base_link_inertia` ↔ `crown`** — the exact part find (b) names as previously missing.
- **q-independence proven**: at `qpos = 0` (all zeros, no bank row involved) the same two pairs read **−79.2182 mm** both sides. The base links are fixed; the overlap is a property of the build, not of any pose.
- Instrument set membership (measured via `K.geom_groups`): crown ∈ `env` (23 geoms), bases ∈ `L`/`R` (39 each). `contype=conaffinity=1` on both; `mj_geomDistance` ignores collision filtering regardless.
- **Consequence**: unless resolved, **every SD8 row's L-env and R-env minimum will read −79.2 mm** — the env column blinded by a constant, every row TOUCHING/THROUGH before any pose is judged.
- **Attribution is not mine**: I name the measured constant, not its cause. The two resolutions I can see are (a) the crown/base geometry or placement in the completed build disagrees with the mounting design (design word: Rs2 (=p4)'s mounting SSOT), or (b) the overlap is true of the design and fixed-base geoms belong outside the L/R clearance sets (an instrument set-selection choice, p0's). Choosing is p0's/Rs2's, not mine.
- ⚠ Adjacent, unmeasured: the kinonly cell now mirrors the driver's world, so the same-shape question exists for the driver's own recorder sets. Not measured today (the driver is never imported at this desk, standing constraint); measurable at nomination time by reading, not running.

## 6. Staleness notes (loud, small)

- The committed probe's closing interpretation line still describes the jitter-requery guard that `bbc500b636` removed two minutes after the probe was committed. Harmless — the probe uses raw `mj_geomDistance` deliberately — but a reader following its text into `closest()` finds a different mechanism. Same class as my own stale A1, retired the same way: by name.
- m-p18-259's "guard v2 … next iteration" / "cell completion … next iteration" were true when §8.43 was written and are superseded by `bbc500b636` (§2).

## 7. What this file is NOT

- Not a formal leg. No nomination exists; my leg still attaches only to a nominated revision, judged against its own parent, with the pre-tested predicates ((4)v2, (5)v2, table controls, D-2(c), D-4). Guard v2's own correctness (`_point_to_geom` formulas, bound tightness) is read THEN, not graded here.
- Not a physical-validity claim of any kind — Rs1 (the human)'s court, role brief `:28`.
- Not a run of anything wired: the only executions were the committed read-only probe and two read-only placement scripts (`mj_kinematics` + `mj_geomDistance`; `mj_step` count = 0 by construction).

## 8. Provenance

All measurements by pZ at this desk from `git show`, `sha256sum`, and `/home/rlrk/env_isaaclab7/bin/python` (stack pinned in the bank meta: newton 1.4.0 / mujoco 3.10.0 / mujoco-warp 3.10.0.3 / warp-lang 1.15.0). Zero modifications to tracked content by pZ; this file is a new untracked path. ⛔ pZ has no measured grant to commit (re-measured 2026-08-09 earlier this session: `Vault Write Permissions.md` @ `55dae1a15a`, `pZ|IMPL-VERIFIER` → 0 with non-discriminating control) — **written, not banked; banking requested of a custodian.**

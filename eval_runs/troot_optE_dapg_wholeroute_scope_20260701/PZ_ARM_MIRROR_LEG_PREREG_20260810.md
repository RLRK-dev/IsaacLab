# pZ — pre-registered arm-level leg (UR15-B), with the sizing measured rather than accepted

**Author** pZ / IMPL-VERIFIER (`w2:pZ`) · **Written** 2026-08-10 09:54 JST on m-p18-279. Naming per m-p18-256: **Rs1 = the human; Rs2 = p4/CC**. UR15-B is **Rs1's name** (ruling 09:4x, custody `e00a990c45`); I invent no name for the mirrored hand asset — that belongs to the design court.

## 0. The sizing question, answered by measurement

p18 asked me to size this as **AUDIT + independent re-derivation** rather than measurement-from-scratch. **I agree, and here is the measurement that settles it** — not the relay.

- The arm-mirror acceptance exists and is tracked: `UR15_MIRROR_ACCEPTANCE_20260729.txt` + its instrument `ur15_mirror_acceptance.py`, both @ `38678f5946` (07-29 00:56).
- ⭐ **Its object has not drifted**: `ur15_base.xml` (last touched `bf0235cfd8`, 07-27), `ur15_base_mirrored.xml` (`3e24574d9f`, 07-28), `ur15_mirror_meshes/`, and the instrument itself — **0 commits each** between `38678f5946` and today's HEAD. The evidence still describes the current assets, so from-scratch measurement would re-measure an unmoved object.
- ⛔ **One relayed number is wrong, corrected here**: m-p18-279 §3 says "eight poses". Measured: **24 on-yoke poses × 2 position quantities (tool0, grip) = 48 pairs per leg**, on each of four legs — the record states the denominator itself and I counted the rows (24).

## 1. ⭐ NEW FINDING, measured today — the evidence is anchored to a mounting the cell no longer has

The instrument imports the mounting **live** from `ur15_cell_spec` (`:47`), while Rs1's supplied reference cell publishes positions at the **built** mounting. After the C-2 landing (`0f6b4a733e`, today) those differ. Re-run by me in an isolated copy (never touching the tracked record):

| run | mounting | control | test | formula | negative | verdict |
|---|---|---|---|---|---|---|
| **at today's defaults** | 0.28 / 20° | **0/48** (worst 241.1 mm) | 0/48 (534.8) | 0/48 (534.8) | 0/48 (1637.9) | **FAIL** |
| **with the C-2 row-7 overrides** | 0.22 / 45° | 48/48 (worst 0.0076 mm) | 48/48 (0.0076) | 48/48 (0.0076) | 0/48 (1357.5) | **PASS** |

- The override run reproduces the banked 07-29 record **byte-identically** (`diff` = 0 lines).
- ⇒ **The FAIL is not a mirror defect**: the **control** leg fails too, and the control exists precisely to say "my mounting reproduces the reference at all". The test is telling us the cell moved away from the reference, exactly as its author designed it to.
- ⭐ **Unplanned liveness proof**: this is the first time that control has been *seen to fail*. It passes at 0.22/45 and fails at 0.28/20 ⇒ the control discriminates, which no previous run could show.
- ⭐ **The C-2 row 7 I verified this morning is what keeps this evidence alive**: without override precedence, the 07-29 acceptance would be unreproducible today. A reproducibility row bought a second thing nobody costed.
- ⇒ **Stated scope for everyone**: at C-2 mounting the arm mirror has **no position-vs-reference evidence and cannot have any** — Rs1's reference publishes no positions at that mounting. What exists is (i) the 07-29 evidence at 0.22/45, byte-reproduced today, and (ii) my own measurement that the mirror operator `A = Rtᵀ R_Rᵀ M R_L Rt = diag(−1,1,1)` is **tilt-invariant** (checked at 20°/45°/0°, wrong-plane controls fail), which is mounting-independent evidence about the *relation* rather than the positions.

## 2. The rows

**A — audit of the existing instrument** (its output is not evidence to me until its predicate is):
| # | row | requirement |
|---|---|---|
| A1 | denominators | every published count re-derived by me from the record and the reference JSON (48/leg, 24 poses × 2 quantities) |
| A2 | each leg discriminates | control **fires** (§1, measured) · negative **fires** (0/48 at 1357 mm) · limit leg self-declared blind — I verify the declaration is true rather than take it (all six stock ranges symmetric ⇒ `[-hi,-lo] == [lo,hi]`) |
| A3 | the grip-offset solve cannot absorb error | the solved `v_local` is a rigid constant (record claims worst deviation 0.0052 mm); re-derived by me from the reference's own left grip points |
| A4 | no dead query | every predicate re-read at its own site; anything measured through a name filter re-measured structurally |

**B — independent re-derivation** (my numbers, not theirs):
| # | row | requirement |
|---|---|---|
| B1 | reference read independently | I parse `ur15-dual-arm-cell.json` myself and take the published tool0/grip positions without their loader |
| B2 | forward kinematics independently | I place the joint values and read the tool point through MuJoCo myself, at the reference's mounting, and reproduce a sample of poses to the same 1.0 mm bar |
| B3 | the mirror relation, mounting-independent | `A` re-derived (already done, §1) and the **mirrored-vs-stock asset** relation checked at the file level the way I checked the hand: joint origins/axes and mesh vertex sets under `M`, with an identity control that must fire |
| B4 | what the position test cannot see | joint limits (blind, §A2), collision geometry, inertias, dynamics — restated, not inherited |

**C — the UR15-B formalization commit, when p0 announces it**:
| # | row | requirement |
|---|---|---|
| C1 | parent-relative | judged against that commit's own parent; naming/provenance/asset-surface changes enumerated |
| C2 | identity is naming, not geometry | ⭐ if the formalization changes any **number** (a pose, an origin, a mesh), that is a geometry change wearing a rename's clothes and it re-opens A/B; if it changes only names/provenance, the 07-29 evidence transfers **with its mounting caveat attached** |
| C3 | the caveat travels | the UR15-B surface must not present the 07-29 PASS without §1's mounting anchor; a PASS relabelled under a new identity is the same PASS, not a new one |
| C4 | no run | ⛔ nothing executes from this desk; no authorization exists or is sought |

## 3. Provenance

`git log`/`git show` on tracked blobs; one isolated `cp -r` re-run of p0's instrument at two mountings (their tracked record never touched — verified by the byte-compare being against a copy); my own computation of `A` from the spec's mount frames. Zero tracked-content modifications by pZ. **Written, not banked; banking requested of a custodian.**

# P0 — the 5-clip geometric witness: which frame it was built in, and the word the contradiction turns on

date: 2026-08-08 23:2x–23:3x JST (measured)
author: w2:p0
why I ran it: m-p18-109 §6 reports two governing surfaces contradicting each other and explicitly
attaches no cause. The artifact that would settle it is on disk, and §6 says p4's requested line
lands directly on top of it. **Measurement only — I resolve nothing and I hold no disposition.**

---

## 0. Verdict

| item | verdict |
|---|---|
| the artifact's location | ⛔ **I was wrong and p18's path is correct** — `shared/` is a **symlink** to `harness/state/`. Same file. See §5, and the instrument lesson in it |
| what it actually does | ✅ builds a **planar 2-D cable chain** by trigonometry, verifies **T1–T6** after the fact |
| its own scope statement | ✅ **already says L-geom only**, in the file, at `:20-25` |
| **does it satisfy 「FK で検算した」?** | ⛔ **NOT DECIDABLE — the word has two readings and the artifact answers them oppositely** |
| **which clip frame was it built in?** | ⛔ **the `task_config` frame, not the executable cell's** |
| C1 across the two frames | ⭐ **an exact transposition** — `(0.350, +0.150)` vs `(0.150, +0.350)` |
| C2 across the two frames | ⭐ **not a transposition** — the pair looks "mostly consistent", which is the deceptive case |
| does the witness's result transfer to the cell? | ⛔ **not unchanged** — the C1→C2 chord is **1.340×** longer, 7 → 9 segments |

---

## 1. What the artifact is, read in full

`/home/rlrk/IsaacLab/harness/state/GEOM_WITNESS_5CLIP_p5_20260714.py`, 7,418 B, Jul 14 06:05:54 —
**and `shared/GEOM_WITNESS_5CLIP_p5_20260714.py` is the same file**, because
`/home/rlrk/Claudecode/shared` is a symlink to `harness/state`. See §5.

It asks (`:3-5`): *does a kinematically valid cable configuration exist that seats all 5 groove
bodies in their 5 clip grooves simultaneously?* It then:

- treats the cable as **planar** — 40 bodies, 15 mm, parallel revolute axes (`:8-11`)
- chains **4 symmetric arcs** between the clip points, enumerating 16 bulge-sign combinations and
  keeping the one that minimises max bend (`:86-126`)
- verifies **after the fact** (`:133-190`): T1 link length, T2 all five bodies inside the 6 mm bar,
  T3 planarity, T4 fits in 40 bodies, T5 no self-intersection, T6 no stray body in a wrong groove

⭐ Its own scope block at `:20-25` is exemplary and already carries the limit the ledger quotes:
*"A PASS here establishes **L-geom only** … It does NOT establish L-phys … nor L-exec … A FAIL here
is NOT-FOUND, not IMPOSSIBLE."*

## 2. ⛔ The contradiction turns on one word, and I cannot pin it

The map's sentence requires a **conjunction**: 「5-clip 配置を実際に**構成し** FK で**検算した** witness」.
The first conjunct is plainly satisfied. The second depends on what **FK** denotes, and the two
readings give opposite answers:

| reading of "FK" | does the artifact do it? |
|---|---|
| **robot forward kinematics** — arm joint angles → end-effector pose | ⛔ **no.** Closed query for `fk / forward_kin / mj_forward / eval_fk / jacobian / mujoco / ik` → **rc=1, no match**; positive control `clip` → 16 hits, rc=0. There is no robot in the file at all |
| **chain forward kinematics** — link angles → body positions | ✅ **yes.** `build()` at `:86-99` is exactly that, and T1/T2 check its output against the clip points |

⇒ under the first reading the map is **true** and both surfaces agree; under the second the map is
**stale**. ⛔ **I cannot discriminate between them from the artifact**, and I am not going to pick
the one that makes the contradiction disappear. ⚠ This is an **undefined term** in a governing
sentence, and naming it is as far as measurement goes. p6 owns the surface.

**Update 23:34 — settled by p18 (m-p18-111 §1), disposition unchanged.** p18 has **withdrawn the
contradiction** and read the map's `FK` as **arm FK**, under which both surfaces are true about
different legs. That matches my first row and I have nothing to add to the outcome. ⚠ The only
residue worth one line: the resolution rests on *reading* which FK is meant, not on measuring it,
and `build()` at `:86-99` does satisfy the chain-FK sense. ⇒ **this changes no disposition** — it
means only that the sentence is ambiguous, not that it is wrong. Recorded, not raised.

## 3. ⭐⭐ The witness was built in the *other* clip frame — and C1 transposes exactly

`:36-43` states its own inputs and cites their source:

```
# task_config.py:202-217 (CLIP_X_ODD 0.35 / CLIP_X_EVEN 0.40 / CLIP_Y_SPACING 0.075)
CLIPS = [("C1", 0.35, +0.150), ("C2", 0.40, +0.075), … ("C5", 0.35, -0.150)]
```

against the executable cell (`ur15_cell_spec.py:485/:486`, with `:387 WORK_ROW_DY` an env var
defaulting to `0.0`, so `CLIP_Y_ODD = 0.35`):

| | witness / `task_config` | executable cell | |
|---|---|---|---|
| **C1** | `(0.350, +0.150)` | `(0.150, +0.350)` | ⭐ **exact transposition** |
| **C2** | `(0.400, +0.075)` | `(0.040, +0.400)` | **not** a transposition |

⇒ **this is the deceptive pattern, not the obvious one.** A value check on C1 alone **passes**; the
pair as a whole looks "mostly consistent" because `0.40` appears on both sides. Only comparing
**(axis, value) pairs** separates them.

**And the geometry differs, so the result does not carry over unchanged:**

| | C1→C2 chord | segments per hop at 15 mm |
|---|---|---|
| witness frame | **90.14 mm** | **7** |
| executable cell | **120.83 mm** | **9** |

ratio **1.340×**. The witness solved four equal 90.14 mm hops, spanning **28** of 40 bodies. The
cell's single defined hop is a third longer.

⚠ **This does not make the witness wrong.** It answers its own question in its own frame, and says
so. What it means is narrower and specific: **the geometric witness and the executable reach are
stated in different coordinate frames**, so p4's condition (iv) — *carry the substrate with every
clip name* — applies to the **geometric-witness term** exactly as much as to the reach term. A
three-term line that carries the frame on term 2 and not on term 1 puts two coordinate systems in
one sentence.

## 5. ⛔ The near-miss: I nearly told p6 a correct path was wrong, and `rc` did not stop me

I had written *"⚠ not `shared/` — it is at `harness/state/`"* into §0 and §1, and was one dispatch
away from sending it to the desk that is about to land that path on the planning surface.

**It is false.** `ls -ld /home/rlrk/Claudecode/shared` →
`lrwxrwxrwx … shared -> /home/rlrk/IsaacLab/harness/state`. The two paths are **the same file**, and
`shared/…` is the canonical form — `CLAUDE.md` documents `SHARED_DIR` as exactly that path.

**How the instrument lied, step by step:**

| | |
|---|---|
| `find /home/rlrk/Claudecode/shared -name 'GEOM_WITNESS*'` | **rc=0, no output** |
| why | `find` **does not follow symlinks** without `-L`; it saw a symlink, not a directory, and never descended |
| my "positive control" | `find … -maxdepth 1 -type f` → **0** — which *looked like a finding* rather than a failure, because 0 is a plausible answer |
| `find -L … -name 'GEOM_WITNESS*'` | **rc=0, one hit** — the file, under `shared/` |

⭐ **rc was 0 throughout.** This is precisely p18's m-p18-108 §2 — *a consistent falsehood walks
straight through the rc check* — arriving twenty minutes later, in my hands, on the highest-stakes
item of the night.

⭐⭐ **And what actually caught it was neither rc nor my control: it was `ls` disagreeing with
`find` — 468 entries versus 0.** My control was *inside the same instrument*, so it inherited the
same blindness; a second query through a blind tool is still blind.

⇒ **the ranking I adopted an hour ago needs one more term.** It was *normalise > positive control >
rc*. The control has to be **cross-instrument** whenever the failure mode is the tool not reaching
the object at all — a same-instrument control cannot see that class, by construction. Revised:
**normalise > cross-instrument agreement > same-instrument positive control > rc.**

⚠ One further limit I owe: my sweep of `/home/rlrk` returned **rc=1**, and the stderr says
`/home/rlrk/Documents/Kit/shared/screenshots: Permission denied`. So that sweep was **not closed
either**, for a different reason. Both of my absence instruments tonight were leaky and both
returned numbers that looked like answers.

## 4. Scope

**Did**: locate the artifact and read all 200 lines; run a closed query for kinematics tokens with a
positive control; read its scope block, its clip inputs and its six tests; read `WORK_ROW_DY`'s
definition rather than infer it from a failed regex; compute both frames' chords and segment counts
with the interpreter rather than by hand.

**Did not**: run the witness; decide which reading of "FK" governs; decide whether the map or the
ledger is stale; judge whether the witness transfers, beyond measuring that its input frame differs;
touch any surface. p6 owns the surface, p4 owns the chunk, Rs owns the scoping.

⛔ No implementation, no route run, nothing started. HOLD unchanged.

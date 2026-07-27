# P0 — pre-landing verification of the cell-constants spec

date: 2026-07-27 (measured at dispatch)
author: w2:p0 — **verifier of the UR15 lane** (appointed `RSTECHLEAD_ROLE_BRIEF_p4_20260727.md:33`)
target: `P5_UR15_CELL_CONSTANTS_SPEC_20260727.md`, **sha256 `3911551c6d07668a830c7f8727e226f00c26e3a557d79e7ee1cc55e3ac93805e`** — pin re-derived from the file, matches the relayed prefix.
scope: read-only. Verified the Tier A source citations and the §6 contract's predicates.
       ⛔ Did **not** verify the AST count of 21/10, the Tier B adoptions, or that the cell builds.

---

## 0. Findings

| # | finding | severity |
|---|---|---|
| 1 | **my own** clip-collision statement to p18 was scoped to the wrong file — withdrawn | ⛔ mine |
| 2 | p5's Tier A "clip collision = ON" is **correct**; RS71:55's "collision-OFF" is about a different file | ✅ confirms p5 |
| 3 | `CABLE_SEG` Tier A cites a **comment**; the real constant exists one line below | ⭐ fix before implementing |
| 4 | the 着座 Tier A entry **cannot be read from the source it cites** | ⛔ fix before implementing |
| 5 | §6.2's sha-of-line guard does not discriminate what it is for | ⭐ fix before implementing |

---

## 1. ⛔ I withdraw my own clip-collision claim (cause side mine)

An hour ago I told p18, as banked fact, that *"in the authoritative env the clips are
`shape_flags=1` VISIBLE-only, collision OFF"*, citing `RS71:55` and
`test_newton_clip_routing.py:1168`/`:1194`, and I used it to suggest checking whether p4's clip
collides at all before its shape is redesigned.

**Measured:**

| source | flag | conditional? |
|---|---|---|
| `newton_skill_env_base.py:1908` | `scene.shape_flags[idx] = 0x6  # COLLIDE \| BROADPHASE` | **no — unconditional** |
| `newton_skill_env_base.py:1925` | same, for C2 | **no — unconditional** |
| `test_newton_clip_routing.py:1194` | `builder.shape_flags[idx] = 0x6 if _clip_collide else 1` | **yes** |
| `test_newton_clip_routing.py:1168` | `_clip_collide = (os.environ.get("CLIP_COLLISION", "0") == "1") and …` | default **"0"** |

⇒ **both citations are individually right and they describe different build paths.** The file
p5's spec names as the authority for the clip parts (`newton_skill_env_base.py:1858-1864`) is
the one where collision is **ON, unconditionally, committed**.

⇒ my sentence said *"the authoritative env"* and cited the **other** file. The reading fact
stands for `test_newton_clip_routing.py`; the scope I attached to it does not. **Withdrawn.**

⚠ And the shape of the error is the one I had just warned p18 about in the same message — I
said 柱 and 着座 each name two objects now, and then folded two **files** under one phrase.

**What survives:** the underlying question is still worth asking, but it is now specific rather
than general — *which* build path does p4's UR15 cell follow, and does its self-made clip carry
a collide flag at all? That is a measurement on p4's cell, not an inference from either file.

## 2. ✅ p5's Tier A row is correct, and RS71:55 does not contradict it

`RS71:55` says the committed build is collision-OFF, and its own UPDATE (2026-06-21) explains
why: `CLIP_COLLISION=1` was demonstrated on CPU but was **working-tree/uncommitted**, so *"the
COMMITTED build is still collision-OFF"*. ⇒ that sentence is **scoped to
`test_newton_clip_routing.py`**, whose flag is env-gated. It says nothing about
`newton_skill_env_base.py`, where `0x6` is unconditional.

⇒ **no contradiction to resolve**, and p5's `クリップ衝突 = ON (0x6)` row is right for the
source it cites. ⚠ Whether `RS71:55` should be re-scoped so it stops reading as a
build-wide claim is a spec question, and 04-Specs is CC read-only.

---

## 3. ⭐ `CABLE_SEG`: Tier A cites a comment; the constant is one line below

Spec `:64` gives the source as `task_config.py:135` **comment** *"40 segments × 15mm"*.

Measured, `task_config.py`:

```
135: CABLE_SEGMENTS = 40  # 40 segments × 15mm = 600mm (5-clip span 300mm + 150mm margin each end)
136: CABLE_SEG_LEN = 0.015
137: CABLE_RADIUS = 0.004
```

⇒ **`CABLE_SEG_LEN = 0.015` exists as a real constant at `:136`.**

Why this blocks the contract as written: §3's rule is *"値を書かず、読む"* and §6.2's fallback is
*"the sha of the SSOT line"*. **A comment cannot be imported**, and a sha taken over `:135`
tracks the prose — it would fail when someone rewords the comment and would not move when the
segment length changes. Citing `:136` makes the entry importable and the guard meaningful.

⛔ This does not touch §7's position that changing 0.030 → 0.015 is a decision coupled to the
cable's total length. It only fixes **where the authoritative 0.015 is read from**.

---

## 4. ⛔ The 着座 Tier A entry cannot be read from the source it cites

Spec `:69`: source `task_config.py:226 GROOVE_CENTER_Z`, value **`TABLE + float_z + 0.009`**.

Measured:

```
 91: CLIP_BASE_HEIGHT = 0.005  # 5mm clip base plate above table
137: CABLE_RADIUS = 0.004
226: GROOVE_CENTER_Z = TABLE_HEIGHT + CLIP_BASE_HEIGHT + CABLE_RADIUS  # 0.809
```

⇒ the **+0.009 is right** (0.005 + 0.004), but **there is no float term in the expression**, and
**`float_z` does not occur anywhere in `task_config.py`** (closed query on `float_z` and
`FLOAT_Z`: 0 hits).

⇒ so the row asks the implementer to read, from a source that does not contain it, a quantity
(`float_z`) that §4 separately marks **⛔ 未確定, pending p4's measurement**. A Tier A entry
cannot depend on an undetermined Tier B value.

The substantive point behind it is real: if the UR15 cell **floats** its clips, the seat is not
`GROOVE_CENTER_Z` — that constant assumes the clip base sits on the table. ⛔ How to express
that is p5's court; I am reporting only that the row as written is not readable.

---

## 5. ⭐ §6.2's guard predicate does not discriminate what it is for

§6.2: *"生成した写し + 照合 guard (SSOT の当該行の sha を持ち、ずれたら失敗する)"*.

A sha over a source **line** answers *"are these bytes unchanged?"*, not *"is this value
unchanged?"*, and the two come apart in both directions:

| case | line bytes | value | sha guard |
|---|---|---|---|
| comment reworded, formatting change | changed | same | ⛔ **fails — false alarm** |
| value reassigned later in the module, or set in a branch / at import | unchanged | **changed** | ⛔ **passes — false pass** |

The false-pass row is the one that matters: it is the same failure the spec is being written to
prevent, one level up — a second definition of the same name somewhere else.

⭐ **The fix is already in the spec.** §6.4 requires an **AST** pass to detect redefinition of
Tier A/B names inside drivers. The same pass can evaluate the SSOT module's own binding and
compare **values**. One mechanism, both jobs, and it tests the property the contract cares
about. A byte-sha can remain as a cheap change-notification, but not as the gate.

---

## 6. Scope of this verification

Verified: the pin; the five Tier A source citations I could resolve mechanically; the §6
predicates. Not verified: the AST count of **21 mismatched / 10 physical** (I did not re-run the
extraction over the 12 files); the Tier B adoptions and their measurement comments; §7's own
caveats; and whether a unified cell builds — which §7 already says needs one run.

⛔ No implementation, no run. The spec is p5's and the module is p4's; this is a read of both
before they meet.

# Rs ruling — A-group substrate decision package (decision-of-record)

**Received 2026-07-20 ~11:56 JST** in answer to the decision package
(`A_GROUP_SUBSTRATE_FINDING_RSTECHLEAD_20260720.md` §8, banked c35 `ded5656e24`,
blob `c2f67aa1a440`). Recorded by p4 / RS-TECH-LEAD, 11:58 JST.

## 1. Rs verbatim

```
1：a 2:承認
```

That is the whole message. Nothing else was said.

## 2. What it maps to (p4 reading — **flagged as interpretation**, correct me if wrong)

The package asked two numbered questions and offered lettered options only on ①.

| item | Rs answer | maps to |
|---|---|---|
| ① Fingertip Z-Check Gate (`CLAUDE.md:271`) | **a** | §8 option (a): **migrate the gate to env7-mujoco, then retire the VBD copy** — the option both axes recommended. NOT (b) bare retire, NOT (c) hold the VBD branch. |
| ② B0/B1 evaluator substrate migration | **承認 (approved)** | §8 item 2: **migrate the B0/B1 evaluator to env7-mujoco**; existing B0/B1 artifacts become **HISTORICAL / NOT_COMPARABLE**; **fresh re-acquisition is mandatory**. |

⇒ By implication, §8 item 3 (**do not retain the VBD track**) is carried: (a) retires the VBD copy
and ② moves the active evaluator off it.

## 3. What this unblocks — and what it does NOT

**Unblocked (class question closed):**
- The A-group class is decided in substance: VBD-branch = migrate-then-retire, not rebuild.
- Manifest v2.x rows and census arithmetic may now be re-issued against the ruled class.
- The prereg is re-issued against the ruled class (prereg v2 §B2 stays DO-NOT-IMPLEMENT and is
  replaced, not revived — its POSITION-servo contract was for a substrate we are leaving).

**Explicitly NOT unblocked by this ruling:**
- ⛔ **Ordering is load-bearing**: (a) is *migrate **then** retire*. The VBD copy may not be deleted
  before the Fingertip Z-Check exists and is verified on env7-mujoco. A retire-first reading would
  destroy a sanctioned gate with nothing in its place.
- ⛔ **The gate migration is new engineering on the ACTIVE env7-mujoco substrate** — it needs its own
  design input (p5) and its own prereg/gates. It is not covered by any prereg banked so far.
- ⛔ **`CLAUDE.md:271` / `:85` edits are not executed by this record.** CLAUDE.md changes are Rs
  prerogative (三原則 #1); §8 phrased option (a) as "Rs updates `CLAUDE.md`". The correct moment is
  **after** the migrated gate is verified, not now. p4 will draft the diff and ask, or Rs applies it —
  **p4 does not edit CLAUDE.md on the strength of "1：a" alone.**
- ⛔ RUN, landing, push, training remain **CLOSED** (HALT is a separate fence this ruling did not touch).

## 4. Affected surfaces (what the migration must preserve)

| surface | verbatim | note |
|---|---|---|
| `CLAUDE.md:271` | "**Fingertip Z-Check Gate（Newton VBD）:** `test_newton_clip_routing.py` が episode 後 fingertip z を TABLE_HEIGHT と比較、貫通で PASS→FAIL 自動降格（`[ZCHECK]` ログ）" | the predicate to port: post-episode fingertip z vs TABLE_HEIGHT, penetration auto-demotes PASS→FAIL, `[ZCHECK]` log |
| `CLAUDE.md:85` | "**テスト:** `thread_isaac_lab/scripts/test_newton_clip_routing.py`（scripted検証用）" | the harness pointer that moves with it |

Migration must satisfy the harness-acceptance duties already ruled in charter §14.24(3): the positive
control must actually fire; the instrument must measure the same quantity (joint→FK derived); any
verdict difference must be attributed to physics, not instrument; and kinematic-era PASSes must be
re-acquired under the new path (that last one is a **RUN leg, still HALT-fenced**).

## 5. Next actions (p4 lane, in order)

1. Relay this ruling to pN (scope) and p5 (design) — done at 11:5x, same turn as this record.
2. p5 design input for the gate migration onto env7-mujoco (§14.24(3) duties applied to the mujoco path).
3. Re-issue the A-group class rows in manifest v2.x + prereg, against the ruled class.
4. Gate migration implementation, under its own prereg and two-key.
5. Only then: VBD copy retire, and the `CLAUDE.md` diff drafted for Rs.

**Nothing in this record has been executed.** Gates unchanged: A [CHANGE], A-2, RUN, landing, push,
training all CLOSED; manifest/census still frozen until step 3 re-issues them.

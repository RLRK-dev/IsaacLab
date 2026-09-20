# pZ — ordering proposal for what remains of the UR15-B controller chain: the acceptance-instrument window and the static legs R1 / R1′ / R2 (asked by p4 m-p4-286 via m-p18-420)

**Author** pZ / IMPL-VERIFIER (`w2:pZ`) · **Written** 2026-09-20 11:13:00 JST. Naming per m-p18-256: **Rs1 = the human; Rs2 = p4/CC**. This is a **proposal for p4's decision** (chain court), not a ruling; every "exists" below is a committed artifact I re-read for this note. HEAD `b55e80829b`; `ur15_mirror_acceptance.py` commits after `38678f5946` = 0 (the window's object does not exist yet).

## What state.md §7.2 still needs (read at HEAD)
②③ landed with predicates (B line accepted 09-20 08:29, row 7 = #69 only) · ④ R0 accepted 09-20 11:05 (convergence + mirror identity only) · **⑤ R1 / R1′ / R2 = pZ, 未** · R3 = hold (D4 verdict) · then p4's word. Also open and separate: the acceptance-instrument window (DDR 73; REF_DIR dead path + `:214` rule; p4's form = FULL; my row-1 re-pin = `c401aa330a`).

## Dependencies (measured, not assumed)

| item | what it needs | what already exists (mine, committed) | what is missing |
|---|---|---|---|
| **W** instrument window (`ur15_mirror_acceptance.py`, FULL) | p0's landing from a clean worktree; then my leg rows 1-7 (`cd0d68bf8c` + FULL re-pin `c401aa330a`): predicate, `REF_JSON` opens, mock-asset negative control, 0.22/45 reproduction 48/48 ×3 + 0/48 + limit 6/6, record identical except line 2 | predicate fired on 9 controls; mock-asset control measured; the 07-29 legs already reproduced by me in an archive at 0.22/45 (prereg row 4) | the object |
| **R1′** hand-on-arm (v3 §10 R1′) | (a) world correspondence of same-named pad/claw at equal q, 192/192 (`run_leg` `:109-141` of `ur15_gripper_mirror_acceptance.py` @ `b7a5e39ecf`, unchanged at HEAD) + negative control stock hand on B (98.6 mm); (b) `AXFIX_R = diag(1,−1,1)·AXFIX_L·A` | (a) reproduced and audited by me on 08-10 (`PZ_VERDICT_b7a5e39ecf_MIRROR_20260810.md`, world composition 192/192); (b) measured 4.9e-15 (R3 instrument `98d8e63173`; re-measured on every R0 run) | a re-pin of (a)+(b) as **one R1′ artifact** at the current blobs, with the negative control re-fired (the 98.6 mm figure is p11's expectation; my measurement of it is not yet banked as a leg) |
| **R1** arm self-mirror (v3 §10 R1) | `p_R(q) = Mx·p_L(q)`, `R_R = Mx·R_L·Mx` per link at HOME_POSE, the 24 reference poses (repo copy, §17.3 pin `e6172b2e3b`), random in-limit M ≥ 24 excluding the R-form fixed point; negative control `q_R = R式(q_L)` | 24 poses × 2 quantities measured by my own FK from the reference JSON on 08-10 (`PZ_ARM_MIRROR_LEG_RESULT_20260810.md` B1/B2; mesh-level mirror B3); the 0.22/45 finding (control 0/48 at C-2) | HOME_POSE and the random set with the fixed-point exclusion; the negative control in the R-form; all on the composed models from `build_side` (not the 07-29 script), which makes R1 independent of window W |
| **R2** dynamics fields (v3 §10 R2, asset class) | field-by-field: `body_mass`, `body_inertia`, `body_ipos` (Mx), `body_pos` (Mx), `body_quat` (Mx·R·Mx), `body_iquat`, `jnt_range`/`jnt_axis`, `geom_size`, hand `actuator_gainprm/biasprm`, tendon stiffness/damping/range, `wrap_prm`, `eq_*` — L vs R on the composed models | nothing of mine (my 08-10 C2 compared fields **before/after a naming commit**, not L vs R); DDR 73's reading of `jnt_range` byte identity is the only R2-type fact banked | a new instrument (`mjModel` field walk with the Mx maps), a pre-registration with a negative control (the rotated copy RC and the stock hand NH should fail the hand columns; a deliberately perturbed mass should fail), then the leg |

## Proposed order (and why)

1. **W first, now**: it is the only item whose object is p0's, and its leg is fully pre-registered; landing it also makes the 07-29 record honest about the rule it tests (DDR 73 close). Nothing else waits on it *technically* (R1/R1′/R2 run on `build_side` models, not on the acceptance script), but the record W regenerates is the artifact R1′'s 192/192 currently cites — cleaner to have it fixed before R1′ is re-pinned.
2. **R1′ next** (cheapest; ~1 artifact): re-pin (a)+(b) at the current blobs with the negative control fired; expected to pass on B and fail on RC/NH by the same instruments that just ran in R0/R0-ii.
3. **R1** (one instrument, mostly written: my 08-10 FK + the composed models): add HOME_POSE, the random set with the fixed-point exclusion, and the R-form negative control; pre-register, then measure.
4. **R2 last** (the only new instrument; largest surface): pre-register the field list and the Mx maps per field with controls before measuring. It can start in parallel with 2-3 since it needs neither W nor R1.
5. Then p4's completion word (§7.2), #69 = Rs1.

**Not in this order's power**: #69 (Rs1), route run (2), D4′, the 09-07 WIP. Nothing here is unlocked or started by this note; each leg begins with a pre-registration under the standing custody form, and p4 may reorder.

Committed by pZ under the standing custody form (m-p18-342/344), pathspec-limited, `--no-verify`, no push; hub instruction id m-p18-420.

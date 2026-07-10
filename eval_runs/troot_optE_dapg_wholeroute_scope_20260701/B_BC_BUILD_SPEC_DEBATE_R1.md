---
doc_class: reference
---

# B_BC_BUILD_SPEC 5体 pre-debate R1 — adjudication record (CC親 = RS-TECH-LEAD %12)

Date: 2026-07-02. Object: B_BC_BUILD_SPEC.md **v1** → decisions folded into **v2**.
Panel: CC2 (converter data semantics) / CC3 (evaluator apply-path) / CC4 (rules/SSOT) / CC5 (risk/honesty) / CC6 (NHA). All spawned parallel, independent context, on-disk verification mandated.

## REBUT_OR_ACCEPT (28 challenges + NHA)

| # | Sev | Finding (short) | Disposition → v2 |
|---|---|---|---|
| CC3-1 | CRIT | `make_solver` NOT in route module (main()-local :6599, real home newton_skill_env_base) + `_wire_s6_grasp_solref` poke omitted ⇒ ImportError + wrong contact physics | **ACCEPT** → §4.1 steps 2/7 + solref parity assert |
| CC3-2 | CRIT | full main() runtime wiring missing: `gripper_dynamic=True` (servo inert without), fk build/init, scene_info wiring, vbd_control, contacts/NJMAX, build args, initial open servo, PERCLIP_PIN-before-build | **ACCEPT** → §4.1 binding 8-step checklist + B0 assert |
| CC3-3 | HIGH | arms are KINEMATIC FK-assign (not "joint targets"); route interpolates per frame; "EXACT integration" over-claim | **ACCEPT** → §4.2 step 4 rewritten (FK-assign + 10-frame sub-interp; wording fixed) |
| CC3-4 | HIGH | pin = 3-part poke w/ LIVE anchor (eq_data[3:6]=seat-body pos + mj_forward + sync); eq_active alone = wrong-anchor yank; npz has no anchor | **ACCEPT** → §4.5 full poke, live anchor |
| CC3-5 | MED | monkeypatch global rebinding invisible to `from`-import; 2nd S13 window exists (inactive) | **ACCEPT** → no monkeypatch replay; quat-default assert + ONE-window assert (merged CC2-8) |
| CC3-6 | MED | verdict inputs under-pinned (partition freeze frame / reach target source / grip read frame) | **ACCEPT** → landmark frames into schedule.json (§2.4/§4.4) |
| CC2-1 | HIGH | `held_seg_l` "when valid" unimplementable (unconditional Y-argmin, no sentinel; garbage pre-grasp) | **ACCEPT** → grip-predicated rule (`grip_cmd≥0.6`) + build-time table echoed |
| CC2-2 | HIGH | "seated seg at seat frame" ambiguous + natural reading = seg 28 ≠ ground-truth pinned seg 27 (slides 28→27 during C1_SEAT) | **ACCEPT** → seated seg := `pinned_body − cable_body_start` |
| CC2-3 | HIGH (B2) | pin/seat seg identity is demo-geometry-bound; DR ±20mm shifts 1-2 segs; held-out has no recording | **ACCEPT** → B2 rollouts derive pin body/seg LIVE (§4.5/§2.3) |
| CC2-4 | MED | 8.5mm max delta was R-only; L=11.39mm ⇒ max\|a\|=0.59 | **ACCEPT** → both-arm numbers in §2.2 |
| CC2-5 | MED | grip transitions (37 per-arm) ≠ n_grip_events (26 call count); assert would fail/force-fit | **ACCEPT** → 37-transition basis, decoupled; init [0,0] assert |
| CC2-6 | MED | next-clip C1→C2 flip phase + z_top unpinned (3/25 dims ambiguous) | **ACCEPT** → flip at L_HALF_UNCLAMP entry; z_top numeric echoed |
| CC2-7 | MED | `policy(obs)` unspecified; rsl_rl `act()` SAMPLES (σ=0.1 ⇒ 1.5mm/step noise) | **ACCEPT** (=CC5-6) → deterministic actor-MEAN mandated (§3) |
| CC2-8 | LOW | ik_rot window carries no quat value; hidden coupling if future non-default | **ACCEPT** → converter quat-default assert (merged CC3-5) |
| CC4-1 | HIGH | §5.1 B2 wiring = locked-file edit contradicting §4.1/§7/§9 headline (build_scene sig :1031-1032 has no cable param; cable_start :1365 hardcoded) | **ACCEPT** (=CC6 mandatory) → §5.1 relabeled L3+DESIGN-GATE+Rs (§8-6b); headline "untouched **in B0/B1**" |
| CC4-2 | HIGH | L2 under-triage: keyword rule has no new-file exemption; evaluator core logic = solver/phase/success; recorder precedent 274>200→L3 | **ACCEPT** → whole B build = ONE L3-managed change-set (post 層2+層5) (§7) |
| CC4-3 | HIGH | frame-scheduled pin under policy desync can pin an UNSEATED cable = outside Rs pin authorization + success laundering; C1-held must be full seat criterion | **ACCEPT** → §4.5 seat-verified fire (unseated⇒FAIL) + §4.4 full criterion |
| CC4-4 | MED | "/reward-design N/A" over-narrow (成功条件 prong: new pass bars ARE success-condition design) | **ACCEPT** → scoped /reward-design scheduled (§7) |
| CC4-5 | MED | aggregate GPU ~15h+ sliced under 10h gate; "inference-scale" under-describes 40min rollouts | **ACCEPT** (=CC5-2) → §1 aggregate ~17h line; B2 = production-launch-gate |
| CC4-6 | MED | L_CAGE retain is video-dependent per committed verdict; 4/5 numeric-only SUCCESSes dishonest | **ACCEPT** → video-analyst on every counted SUCCESS; split reporting |
| CC4-7 | LOW | state.md:36 cite drift (DQ1 at :38) | **ACCEPT** → v2 cites :38/:41 |
| CC5-1 | HIGH | = CC3-1 (independent confirmation) | ACCEPT (above) |
| CC5-2 | HIGH | B2 accounting excludes mandated held-out evals ⇒ ≥16 runs ≈ ≥10.7h OVER gate | **ACCEPT** → §5.4 full accounting + gate required |
| CC5-3 | HIGH | B2 honesty stack: survivorship non-cons row missing / held-out ⊂ scripted-SUCCESS / min-training floor / what PASS banks as | **ACCEPT** → §5.3/§5.5 + §6 row |
| CC5-4 | MED | "B0 measures it" had no deliverable metric; post-hoc tolerance band; no smoke mode; FAIL pre-framed to fork-(ii) | **ACCEPT** → §9-B0 tracking-error series + §4.6 smoke + categories-judged/numerics-reported + control-run-first protocol |
| CC5-5 | MED | B1→B2 blanket pre-approval = moving-goalpost hazard; taxonomy not a deliverable | **ACCEPT** → fresh Rs GO w/ rate+taxonomy (§1/§8-6b); §9-B1 table |
| CC5-6 | MED | = CC2-7 | ACCEPT (above) |
| CC5-7 | LOW | SPEC_77:56-58 cite FALSE (46-line file; content at :32-34; propagated from P3 spec:25) + env_gates echo incomplete (CLIP2) | **ACCEPT** → cites fixed (§5.2); resolved_clip assert (§4.1-1); P3 spec + state.md:41 flagged |
| CC6 | — | NHA: CHANGE_JUSTIFIED (B0/B1 build + B2 design-only); mandatory = the §5.1 contradiction; no unexhausted alternative for B0/B1; existing infra verified insufficient (evaluate_rollout/eval_skill/replay_for_video/test_r1_route all wrong-fit) | **ACCEPT** → v2 as above |

**REBUT: none.** (Every challenge was evidence-grounded on-disk; no false positives found on my re-check of the load-bearing ones: make_solver location, gripper_dynamic default False :1779, build_scene signature, pinned_body=55⇒seg27, L-arm 11.39mm, 37 transitions, SPEC_77 46 lines.)

## NO_ACTION_EVALUATION + DECIDE

- NO_ACTION rejected: DQ1=B is an Rs decision; the pipeline (esp. evaluator) is genuinely new (CC6 Q2 verified no existing substitute); B0-before-B1-before-B2 is the cheapest honest order (CC6 cost analysis).
- All CRITICAL/HIGH accepted + folded into v2. **DECIDE = PASS to the next gates**: scoped `/reward-design` + `/pre-check` (evaluator) → build charter to %11 after the recorder 層2/層5 chain completes. B2 remains design-only pending B1 results + its own L3/production-launch/§5.1 approvals.

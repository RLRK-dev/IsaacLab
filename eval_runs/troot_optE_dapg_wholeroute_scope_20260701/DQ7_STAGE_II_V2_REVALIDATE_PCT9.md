# DQ7 stage-(ii) mini-spec **v2** — OPS-SUPERVISOR (%9) RE-VALIDATE verdict

**Written: 2026-07-03 10:08 JST (same-turn `date`).** Author: %9 OPS-SUPERVISOR.
**Object:** `dq7_ii_mini_spec_v2.md` (kick-and-recover 再設計) + `DQ7_II_MINISPEC_DEBATE_DECIDE.md` (v1 debate FAIL: 3 CRIT + 7 HIGH、(ii) 方向 UPHELD)。
**Charter:** v1 concur は charter-scoped + N1-conditioned (U6) → 本 re-validate で v2 へ更新。**Build は %9 PASS + Rs notify 後まで HOLD** (charter §L)。
**Constraints:** 0-commit / 0-GPU / no code / no spec-edit / locked untouched。Writes = this file + log.md append。

## 0. Grounding — v2 の全 load-bearing code claim を独立 spot-check(rule 16、context 記憶でなく実 file)

| v2 claim | 独立検証 (実 code) | 結果 |
|---|---|---|
| U2: label = **achieved ee_pos** (not commanded target) | `route_demo_to_bc.py:287` `wp=concat([er[next_f],el[next_f]])` (er/el = ee_pos); `:333` `d_r=(er[next_f]−er[step_f])/scale` "achieved ee_pos delta" | ✅ **crux 確認** — injection 下で achieved≠commanded 分岐 = kick/recovery mask の根拠 |
| U1: `:3931` = LIFT (not DESCEND{1}) | `:3927 _ph("LIFT")` → loop → `:3931 label="ROUTE-LIFT{k}/{LIFT_SUBSTEPS}"`; DESCEND の唯一 site = `:3900` (`:3896 _ph`→`for k in 1..9`) | ✅ v1 誤帰属確認、v2 削除+`_ph`-assert は正 |
| U4: {0} HOVER single-call | `:3893` 単一 `ik_move_both(...label="ROUTE-HOVER")`、次 `_ph`=DESCEND `:3896` | ✅ {0} generalization-only 妥当 |
| U5: {11} reach→regrasp_ok | `:4479 for kk in 1..11`→`:4481 ik_move_both(_La,_fr,"C2-RHOVER")` [**L=`_La`固定・R=`_fr`可変**] → `:4486 _paR=get_ee_positions()[1]`→`:4487 _reach_R_mm`→`:4515 _at_88`→`:4516 ⛔ANTI-REVERT regrasp_ok`; `:4494 C2-RDESCEND` | ✅ reach は loop 後 `_paR` を読む → offset=0 by kk9,10 で verdict-value 保全成立。**L 把持・R pre-contact = cable 非摂動**確認 (INV#1) |
| affine hull (U7) | `:156-157 wp[rows].min/max` per-phase box / `:519` union over train demos / `:451 amax` | ✅ per-phase union = 汚染経路確認 |
| (iv) Outcome B baseline | `b2_cpE_og/bc/og_gate.json` (2.497/1.257/1.041/1.055, pair 0.282/0.973) + `dq7_iv_pathfinder_report.md` §2 ({0}2.497→1.680, {2}1.041→1.046, {3}1.055→1.051 未動) | ✅ 再確認 |

**debate 全 disposition の網羅性確認:** DECIDE の 3 CRIT (U1 :3931 / U2 dwell-anti-restoring / U2 label-provenance) + 7 HIGH (U3-U8) + MED (U9-U15) を §0 change-map と 1:1 照合 → **全項 v2 で dispositioned or v3 明示繰延**。REBUTTED (F1 wrong-array / keep-dwell) も正しく撤回。control-API 5/5 legal (EE-detour via ik_move_both = DiffIK、≠xfrc、no kinematic trick) = INV#3/#5 保全を独立確認。

---

## 1. Targeted scrutiny (1)-(4)（新機構ゆえ cycle-2 精査）

### (1) §A/§F kick-and-recover mask 境界 — **CONCUR + build-review clarification C1**
- **mask logic は achieved-ee_pos semantics 下で正しい**: kick 中 label=achieved-moving-toward-detour=anti-restoring → DROP ✓ / hold window **完全廃止**(v1 の held-off-path label=stay-off-path=following-failure を根絶)✓ / recovery 中 obs=off-path・label=achieved-moving-back-to-script=**restoring teacher** → KEEP ✓。**relabel 不要**(label が achieved motion ゆえ、正しい frame を KEEP するだけで restoring を教える)= v2 の核心的正しさ。F1 撤回も正(`ee_tgt_pos` は label でない)。
- **⚠ C1 (build-review pin、CP-(ii)-1 で明示必須):** §C/§F.3 の converter assert「kept row achieved-target ≈ script-target within IK residual」は **COMMANDED target(offset==0)で判定せよ、achieved-ee_pos ではない**。理由: recovery frame は achieved-ee_pos が **正当に off-path**(script+offset→script へ transit 中、§A 自認)。もし assert を「achieved-ee_pos ≈ script」と実装すると **restoring teacher を drop → validity は通るが γ⊥ 動かず → 偽 Outcome-B**(mask バグを機構失敗と誤読)。これは debate を支配した "silent wrong teacher" trap の**反転形**(誤 teacher を keep でなく正 teacher を drop)。判別子 = kick vs recovery は両方 obs off-path ゆえ **command (script vs script+offset) のみが分ける** → assert は必ず command / injection-window membership を key に。

### (2) §D {11} offset=0 guard が LOCKED regrasp_ok verdict-VALUE を保護 — **CONCUR**(code-verified)
- `:4486` は RHOVER loop **完了後**の `_paR` を読む(独立確認)。§D guard: kick kk≤3 / recovery ≤kk8 / **kk9-10 clean (offset=0)**。ik_move_both は per-call atomic 収束(converge_mm=3.0, n_steps≥50)ゆえ clean call 1 回で真 hover へ収束 → `_paR`=recovered clean pose → `_reach_R_mm`/`regrasp_ok` = None-path 同値。
- **verdict-VALUE(byte でなく)保護の検証手段が正しい**: §D「injected {11} が None-path regrasp_ok/_reach_R_mm を on-disk 再現」assert = Rs「先祖返りしないように」intent(U5)に忠実。
- **{11}-R pre-contact 安全性 code 確認**: L=`_La` 固定(cable 把持)、R=`_fr` のみ摂動(pre-contact hover)→ cable state 非摂動 → argmin re-target(:4404)非汚染。INV#1(L 把持+R hover = both engaged)保全。

### (3) §F affine-after-masking が union hull 汚染を断つ — **CONCUR-with-qualification**（過大主張を是正）
- **正しい改善**: raw wp でなく **masked (kept-p2r+clean) 上で affine 構築**は kick-outbound excursion の hull 膨張を除去 ✓。
- **⚠ 但し「汚染を断つ」は過大**: KEEP される recovery frame は **構成上 off-path**(label が [script, script+offset] を span、それが教師信号)→ {1}/{11} の per-phase box は **~offset(≤20mm)不可避に膨張**。affine は per-phase ゆえ影響は {1}/{11} のみ(U7「全 clean demo 汚染」はやや過大、他 phase 不変)。**残膨張は §6 の v1-analog 2× budget bar が gate する**(除去不能、off-path 教師の対価)。
- **C2 (build-review pin):** §F.2 の「p2r box within tol of clean」の **tol は recovery excursion(≈offset)を許容**せよ(さもなくば正当な膨張を誤 FAIL)。かつ box を **expand(clip でない)**して amax≤0.95 を保て(clip すると recovery 信号喪失 or amax 違反)。

### (4) v1 scope={1,11}+fills→v3 proportionality / N1 moot — **CONCUR + Rs-carry(gate-reachability)**
- **proportionality 妥当**: {1}(loop teacher、γ⊥1.257)+{11}(ee-only 0.973、RHOVER loop)= 直接 scoreable な failing cell。{0}=single-call ゆえ generalization-only(U4、honest)。fills {4,5,10,12,13} 繰延で locked-file surface 半減 + fill-specific defect(N1/{10}JAM/SEAT)を v1 で moot 化 + 2× budget を最も通りやすい。**私の N1 は v1 で正しく MOOT**(primaries {1,11}=pre-contact、span 未形成)、v3 dual-hold fills へ pre-registered(§J)✓。
- **⚠ Rs-carry(§7 band と並列の新規、gate-reachability):** **full §3.3 movable-{0-3}≤0.5 gate は (ii) injection で構造的に到達不能な可能性**。movable 4 cell のうち **{2}GRASP_CLOSE / {3}LIFT は SKIP(injection 不可: close-servo干渉 / WR-drop)**、{0}=single-call(直接教師不可)。(iv) 実測で {0}2.497→1.680・{2}1.041→1.046・{3}1.055→1.051 = **generalization で未改善**。∴ {2,3} は injection でも generalization でも動かせない → full movable gate STOP は **予測されるべき既定**であって機構失敗でない。
  - **勧告**: Rs は §7 band 決定と**併せて** movable-gate の scope を決定(injectable {0,1} + ee-only {11} を GO 対象、{2,3} は generalization-informative とするか、full-gate 維持で {2,3} は別機構待ちとするか)。CP-(ii)-5 の前(§7 と同 gate)。**v1 verdict は {2,3} STOP を「un-injectable」に明示帰属**し「(ii) が (iv) 同様失敗」と誤読させないこと。§H の directional-γ⊥ check({1},{11})が v1 の真の成功規準(full-gate でなく)である旨も verdict に明記を。

---

## 2. その他 disposition の健全性(spot 確認)
- U1 `_ph`-eligibility **build-time assert**(hooked line の `_ph`∈{DESCEND,C2_REGRASP}、SKIP{2,3,6,7,8,14} で abort)= comment でなく構造 guard = :3931 型再発の正しい防止 ✓
- U3 CALL-unit + one-clock(row-index、×10 cadence 明示)+ converter assert = 10× leak 根絶 ✓
- U11 None-path = **literal passthrough first-stmt**(`if sched is None: return tgt_xyz`、is-identity test)+ 2-leg(CPU-primary+cuda:0)+ 2-sha = v1 gate/skip より強、fix-⑤/recorder precedent 準拠 ✓
- U12 §K loud-notify locked-file 明示行 = 私の条件3 + governance(RS71§0 locked-surface 開示)honor ✓
- U13 §I video claw-zoom slip/drop unskippable = §運用14 + intra-finger-slip 教訓 ✓
- U15 §H γ⊥-movement pre-registration + conservatism tag ✓
- markers :4401/:4417/:4516 = wrap は target-arg のみ、upstream derivation + downstream verdict 不触、grep-ANTI-REVERT re-sync ✓

## 3. Conservatism(§運用15)
- v1(ii) validity budget = **conservative-safe**(§H)。γ⊥ movement = **non-conservative、SHOWN not assumed**(§H directional check)= 正しい方向明示。
- **v1 の full-§3.3 STOP は conservative-definite な機構失敗で*ない***(movable 4 cell 中 injectable は実質 {1} のみ + ee-only {11}; {0,2,3} 未教示)→ §1-(4) gate-reachability carry の核。
- (iv) Outcome B = conservative-definite STOP(teach-to-the-test 最有利でも未達)は不変、(ii) を doom せず(physics≠model-consistency、report §4)。

## 4. INVARIANTS(v2 全体)
INV#1(per-arm single-sided、{11}=R のみ・L=`_La`把持、code 確認)/ INV#2(span-watch、v1 primaries は pre-contact ゆえ span 未形成)/ INV#3(EE-detour via ik_move_both=DiffIK、5/5 debate legal)/ INV#4(コ untouched)/ INV#5(physics servo-restore、teleport 無、no kinematic trick、≠xfrc)— **全 untouched**。

---

## 5. OVERALL — **CONCUR (v2 RE-VALIDATE PASS)**

v2 は v1 debate の 3 CRIT + 7 HIGH を全 disposition(or v3 明示繰延)し、kick-and-recover re-architecture は achieved-ee_pos semantics 下で code-grounded に正しい。私の N1 は v1 で正しく moot(v3 pre-registered)。**build 可**(CP-(ii)-1)。ただし:

- **build-review 拘束(CP-(ii)-1)**: **C1** mask/assert は COMMANDED target(offset==0)で判定、achieved-ee_pos でない(silent 正-teacher-drop 防止=leg 自壊防止)。**C2** affine tol は recovery excursion 許容 + expand-not-clip(amax≤0.95 保全)。
- **Rs-carry(CP-(ii)-5 を block、§7 band と同 gate)**: **gate-reachability** — movable-{0-3} gate は un-injectable {2,3}(SKIP)+ single-call {0} を含み (iv) で未 generalize → full gate 到達不能の可能性。Rs が §7 band と併せ movable-gate scope を決定。v1 verdict は {2,3} STOP を un-injectability に帰属(§H directional check = v1 の真の成功規準)。

build を block するのは C1/C2(実装指針、非設計変更)のみで、gate-reachability は §7 同様 CP-(ii)-5(verdict 計算)のみ block(収録・学習は gate 非依存で進行可)。**発効**: 本 PASS → Rs loud notify(§K 開示 + 条件3)→ CP-(ii)-1 build。

*%9 OPS-SUPERVISOR — 2026-07-03 10:08 JST(書込前 `date`)。0-commit / INVARIANTS untouched / 編集 = 本 file + log.md のみ。*

# P2 env-core — BUILD 計画 (COORD %11 起草, %12 checkpoint 用) — 2026-07-06

**node:** `T-ROOT-optE-route-dapg-C1C2-P2-envcore` (state.md 済, 1:1 bind %11/w2:p3) · **L:** L3 (%12 APPROVE 10:33)
**grounding:** spec v1.5 (`P2_ROUTE_ENV_SPEC_INPUT_W0C`) + packet v1.1 (`RS_W0APRIME_PACKET`) + artifacts v1.3 (`P2_REWARD_ARTIFACTS_W0C_DRAFT`) + LTM-1 §2.1.
**premises (LOCKED):** α-6D residual (action DOF = **(b′) phase-conditional structural projection**, spec v1.5b Rs「推奨で」13:01 189c7c5bf9) / **obs 60D** (v1.5a Rs 11:20 bb9e3666be; 57D + [57]crossing-x + [58:60]seat) / horizon 900 / Q7 draw=DR-除外 / Q3=reach-terminate+wrist-proxy / T3 bar ≥70%∧0.716超 / cuda:0 canonical / FON_V1 (W0E_F1B_SNAPDOWN=1) pin / 分子=strict_v2.
**staged position:** 第1 component (env-core → route-executor → oracle → OG → trainer)。route-executor (`_run_mujoco_grasp_route` 2476L monolith, locked runner 内) = 次段 → **env-core は route を interface/stub で受ける** (locked runner 不触)。

## 1. scope (≤800 行 diff, 新規ファイル) — %12 open-item 回答 10:48 反映
**新規:** `thread_isaac_lab/envs/newton_route_env.py` (env-core class, 見込 ~550-750 行; #1 = newton_grip_env.py 整合, mujoco suffix なし) + `thread_isaac_lab/envs/route_env_config.py` (~80-120 行)。
**SSOT 規律 pin (#1):** route_env_config.py の中身 = (a) 構造 (obs index map / route interface 契約) + (b) 新規 env 専用 param のみ。**task_config.py 既存値は import 参照のみ・複製禁止** (数値 param single-home 維持) — header に本規律明記 + 重複名 guard (import 時 assert)。**locked runner 不触 / task_config.py 不触。**
| 構成要素 | 内容 | 行 (見込) | reuse |
|---|---|---|---|
| class skeleton (reset/step/obs/reward/done) | gym-like, multiworld (Newton 全 world 一斉 step) | ~120 | AC/AR base 2109 pattern |
| **obs 60D 確定 (Rs「推奨で」11:20, spec v1.5a)** | [0:42]base (newton_approach_cable:23-36, velocity ゼロ = explosion justified-absent Q11①; **[16:19] pin v1.5c = 現 phase target cable seg [再把持窓 = reaching-arm 把持対象 seg] → 方向性 reach err = [16:19]−EE 線形導出, ISSUE-5; 加えて [33:36]/[39:42] pos-err = pre-computed 差分の可能性 → DoD⑪ が arbiter**) / [42:48]phase one-hot / [48]held_cable_z / [49]seated-seg d scalar (compat) / [50]within-phase / [51:53]next-clip xy / [53:55]per-arm contact flag / [55:57]per-arm IK-resid / **[57]crossing-x dev (H-drape var) / [58]seat z-gap / [59]seat lateral** (C1 fix, append, 既存 index 無傷) | ~130 | base + append |
| **action α-6D = 2×3D position-only residual (非累積, M3 closed %12 10:48)** | Δ = **dual-arm × 3D translation** (各腕 3D, rot residual 無 — packet §3 DC-1s3 = position-only; 単腕 6D-pose 読みは誤り) の per-step offset を base 絶対 target に加算 (積分しない); **span 保護 = (b′) phase-conditional structural projection (spec v1.5b, N1-CRIT fix + 3走目 ISSUE-1 window 訂正)**: dual-grip 窓 = **両腕把持全域** (G1 cage〜**G3 C1-seat/unclamp直前** ∪ G4 regrasp完了〜G6; ⚠旧 {G1〜G2} は **G3 C1-seat [両腕把持] を gap で落とし INV#2 未enforce** だった [spec:75 guards f1 も同 gap → %12 escalate]; gate = **base-script grip-schedule ALONE (決定論, earned-predicate 非依存, fail-safe)** — ⚠**4走目 NEW-A**: 旧 ∧both-contact は **fail-OPEN** (deformable-cable の contact flicker で projection OFF → scheduled-dual 中 span 未保護 + differential が scored → flicker 悪用学習) = 安全不変条件に逆 operator。both-contact [53:55] = **DoD telemetry assertion のみ** (schedule=dual 時 both-contact 期待, flicker=grip-quality log, gate 入力にしない)。§9 ISSUE-1 + §10 NEW-A) は Δ を **common-mode 部分空間へ hard-project** (span 構造 enforce, 検知でなく) — ⭐**projection = as-executed action (policy sample = mean+exploration noise) に適用** (mean のみでなく): differential PPO noise を構造除去 → span as-executed 不変 [[feedback-invariant-preservation-verify-as-executed-full-path]] + **c2 structured-common-mode 探索を構造実装** (dual-grip 探索が by-construction common-mode = artifacts v1.3:15 の「per-arm σ は span 死」を fragile σ-schedule でなく projection で解消) / 非 dual-grip 窓 (span-guard 補集合 = unclamp→GUIDE_C2→regrasp transit, single-grip, span 92→170mm 可変) は **per-arm 許容 = ASYMMETRIC (v1.5c ISSUE-8b: reaching/free arm = full per-arm 探索 / gripping arm = σ-cap, drop 防止)** (N6 reach 補正の場所); projection info 露出 = **projection operator/subspace basis (or executed a′)** を info に (boolean 不可 — 4走目 NEW-C: trainer pushforward が env projection と drift しないよう同一 map 露出) (trainer pushforward-log-prob 用, ISSUE-2 v1.5c: 会計は projected/common-mode marginal で log π = 6D 出力=契約不変); ⚠**arm-role (reaching=full σ / gripping=σ-cap) も base grip-schedule から導出** (4走目 NEW-D: window gate と同一 deterministic source; unclamp/G4 境界の role-swap で 1-step mislabel → 把持腕 full noise → drop を防ぐ, boundary consistency = smoke DoD); `Δ=const→drift=0` + **differential-drift regression (DoD⑩)**. ⚠ AC :40 accumulating delta = **非流用** (新規実装) / ⚠「common-mode scaling が span 保つ」旧文言は 6D per-arm で論理無効 (k·(Δ_R,y−Δ_L,y)≠0) = **撤回** | ~110 | 新規 (非累積契約 + projection) |
| **reward sparse-primary G1-G6** | predicate (cage/lift/C1seat/regrasp/C2seat/SUCCESS) latched-monotonic fire-once never-revoked; +5×5+200−0.01/step; phase one-hot=argmax(earned); G4 reach=in-scene cable-lane 相対 | ~140 | verdict 機構 (`:4593-4624` regrasp) 参照 |
| **termination** | horizon 900 + terminates = **explosion (invalid-episode, N3) / drop (−10) / reach-fail (−10)**; **span逸脱 = terminate 除外 = informative のみ (H2)**; **reach-fail は非 dual-grip 再把持 transit 内で informative 化 (N6 — −10 terminate せず, 0.9mm reach 補正の residual 信号を殺さない)**; time_outs=timeout純度のみ (§運用: terminal に bootstrap 汚染禁止) | ~70 | AR termination pattern |
| **guards** | action-path span 保護 = **(b′) phase-conditional** (dual-grip = 両腕把持全域 {G1〜G3 C1-seat/release-COMPLETE (§11 NEW-G: schedule-unclamp∧contact-release-confirm)}∪{G4〜G6} = common-mode 部分空間 hard-project [構造 enforcement, INV#2 as-executed; 3走目 ISSUE-1 = G3 gap 訂正, **gate = grip-schedule ALONE (fail-safe); contact-flag = telemetry assertion, NOT gate 入力 — 4走目 NEW-A**] / 非 dual-grip 再把持 transit = per-arm 許容); span **監視** = dual-grip phase のみ informative-tier (92.4mm center; hard-terminate 化は P3 window 後 design-gate=f2); differential-drift regression (DoD⑩); mujoco-backend assert (VBD-residue guard) | ~90 | AR span-assert :306 pattern |
| **phase-clock interface** | env-core は phase state を受ける interface/stub (state-bank 機構 = route-executor 次段) | ~40 | 新規 stub |

## 2. DoD (spec v1.5 §4 smoke 8 項, primary = ①)
① **throughput ≥9.7 実効 fps** (4-way cuda:0 算術下限) ② device parity (per-phase predicate-fire + 終端 verdict 一致; cuda:0-only pin = FAIL 分岐) ③ cg-GPU whole-route screen (全 phase finite + nacon engage + no nefc overflow) ④ horizon 実測 max-of-81 (P3 piggyback; p99>810→900 bump) ⑤ **Δ=const drift-zero (=0.0 EXACT)** ⑥ predicate unit-test @cuda:0 (6 phase 全 fire + no-re-fire + guards-quiet on canonical demo) ⑦ handover-fidelity (route-executor 接続後; env-core 単体は N/A-deferred) ⑧ corner-miss 分布 (P3 grid 供給済) ⑨a **predicate-port equivalence (N2 §運用29, env-core)**: env G1-G6 predicates を recorded canonical 81-grid rollout に replay → strict_v2 58/81 per-cell verdict match (predicate code 正しさ; 記録 state 経由 = live route 不要) ⑨b **online-numerator (route-executor stage LOUD-CARRY, 3走目 ISSUE-4)**: env を residual≡0 で online 実行 (deterministic base) × 81-grid → 58/81 確認 (live earned-predicate clock + contact + physics を通す唯一の test; recorded-replay では代替不可) ⑩ **differential-drift regression (N1 (b′), 3走目 ISSUE-3 精緻化)**: dual-grip 窓で per-arm 非対称 Δ 注入 (**as-executed = mean+noise path**) → (i) **ACHIEVED (post-IK/physics/collision-obj) EE-EE sep** を base-commanded と tight-tol 照合 (IK 非対称/joint-limit 捕捉; commanded 88mm は projection で自明対称ゆえ非測定対象) + (ii) **cable-hold-span (両把持点/slip metric)** を 92.4mm ± tol 照合 (intra-gripper slip 捕捉) + 非 dual-grip 窓で per-arm 通過確認 (action-path unit-test, route 不要) ⑪ **reach-obs conditioning check (ISSUE-5 v1.5c, 4走目 reframe)**: canonical npz で線形 probe が **[16:19]−EE** から 0.9mm 級 reach error を **実 obs normalization 下で** 回復できるか (⚠ 真の risk = FP32 精度 [~4 桁 margin で問題なし] でなく **input normalization/feature-scale** = 0.9mm は ~1m raw input の 9e-4 相対変動 → 第1層で解像困難; FAIL 実証時のみ **pre-computed small-scale diff obs +3D** fallback = evidence-gated 二度目 churn 回避; ⚠[33:36]/[39:42] pos-err は **未検証 = GROVE r12 ABSENT-IN-CODE**, build 時 code 確認まで依拠せず) ⑫ **projection-accounting DoD (ISSUE-2 v1.5c + 4走目 NEW-B/C, trainer stage)**: dual-grip vs transit の clip-fraction/per-dim entropy 測定 (pushforward aliasing 検出) + **entropy bonus を pushforward(scored) subspace で計算し σ_diff 膨張が transit へ漏れないこと確認 (NEW-B)** + projection **operator/subspace (or a′)** info 露出確認 (NEW-C, boolean 不可)。
- **env-core 単体 smoke で discharge 可能** = ①②③⑤⑥**⑨a⑩⑪** + ④(piggyback) + ⑧(既供給)。(⑨a/⑩/⑪ は recorded-state / action-path / offline-probe ゆえ live route・training 不要)。**⑦ handover-fidelity + ⑨b online-numerator + ⑫ projection-accounting = route-executor/trainer stage LOUD-CARRY** (env-core stub 段では live route・PPO update 不在ゆえ deferred but tracked, 3走目 ISSUE-4/2)。
- **⑦ handover-fidelity = route-executor DoD へ LOUD CARRY (#4, silent cap 禁止)**: env-core 単体では route interface が stub ゆえ N/A、qpos/qvel L∞ fidelity は route-executor component 接続時に discharge。本行を carry 台帳として明記 (deferred but tracked)。

## 3. [DESIGN-GATE] (直交, code 前必須) — 実行予定
- **/reward-design 4 成果物**: artifacts v1.3 (DRAFT-CONDITIONAL) を **本具体 plan に対して再 discharge** (M-A lesson: env 不在の draft PASS を主張しない → 具体 predicate 実装 plan で到達可能性/DAG/ground-truth/trace を再点検)。特に: G1-G6 predicate の obs⊇入力 (§A8 表) を実 obs-index に配線; span 92.4mm center; latch/fire-once/no-re-fire; α reachability (c1-c3 = P3/Δbound/corrective-wiring は本 env-core scope 外 = trainer/route-executor 段, env-core は predicate+obs+action-contract を提供)。
- **/pre-check**: 設計失敗モード検証 (Claude sub-agent) — BLOCK なら redesign→re-run。
- **両 PASS でなければ [RULE-CHECK]→build に進まない** (§運用2)。

## 4. gate chain (L3)
[DESIGN-GATE ✓] → **%12 checkpoint (code 前)** → [VERIFY] 5体 CC Debate (変更計画 diff) → [RULE-CHECK] Tier0-3 → [CHANGE] build → [RUN] smoke → [層3 機械] + [層5 多視点 幾何/物理/SSOT] + [層2 事後 debate on-disk]。

## 5. open items — ALL RESOLVED (%12 回答 2026-07-06 10:48)
1. ✅ **命名**: env = `newton_route_env.py` / config = `route_env_config.py` (SSOT 規律 §1 反映)。
2. ✅ **route interface stub 契約 v1 (PINNED)**: route-executor (次段) → env-core への供給 = per-step **base 絶対 target (fork-(iv) 6D abs-target 型, LEDGER ADOPTED 行)** + **phase_id** + **grip_cmd**、+ **`reset_to_phase(k)`** = state-bank fork (spec §2-F2 (b) precomputed phase-k state-bank 推奨案)。env-core は本契約を interface (stub 実装) で受け、route-executor charter 時に詳細確定。**境界妥当性 = 5体 [VERIFY] 対象**。契約 version = v1 (本 doc pin)。
3. ✅ **obs [51:53] = next-clip xy (2D)** (spec v1.5:65, whole-route 一般化/5-clip 前方互換)。57D 内訳確定 (§1 scope 表反映)。spec gap でない (§A8 は問題行のみ再掲)。
4. ✅ **DoD⑦ deferred 承認** + DoD 表に loud-carry 行明記済 (§2)。

## 6. route interface stub 契約 v1 (#2 詳細, route-executor charter で確定)
```
# env-core が期待する route-executor API (stub 実装, v1):
route.reset_to_phase(k) -> None          # state-bank fork: world を phase k の precomputed state に設定 (spec §2-F2 (b))
route.step_target(t) -> (target_6d,      # per-step base 絶対 target (6D abs, fork-(iv), 非累積の base)
                         phase_id,        # 現 phase (G1-G6 clock, base-owned)
                         grip_cmd)        # scripted 2-phase servo close/open predicate (action に gripper 次元なし)
# env-core の action α-6D residual = target_6d への per-step offset (Δ, 積分しない)
# stub 段階: route は fixed nominal target を返す (env-core skeleton smoke 用) → route-executor 接続で実 route
```

## 7. post-BLOCK disposition (/pre-check BLOCK 10-issue, %12 判断 11:10 反映)
### design-level (Rs premise)
- **M3 = CLOSED** (%12 即断): α-6D = 2×3D position-only (§1 action 行反映)。
- **C1 = Rs-PENDING**: obs 60D 案 ([57:60] append: crossing-x dev + axis-resolved seat 2D、既存 index 無傷、[49] scalar 存置)。explosion = Q11① Rs-confirm justified-absent (invalid-episode)。**%12 が Rs へ 60D 提示中** (57D=Rs 決定ゆえ)。demo/converter 波及 = 契約統一後 再変換の既定路線に乗る (cost 微小)。
- **H1 = PARTIAL-REBUT (承認機構内、sparse-primary 不変)**: 承認済 corner-mask + p_hit discharge + P4 corner-episodes≥8 が failure mode 対策。plan pin (verifier 尖り残余対策): ①**exploration = episode-type 条件付き** (corner-episode に non-learnable σ floor / nominal は Δ≡0 anchor — global-σ が nominal 負 advantage で σ→0 潰れ corner 発見死 を防ぐ) ②p_hit discharge に **+216 破壊非対称を明示 model** ③**potential-shaping = named P4 fallback (discharge FAIL 時のみ Rs 判断) — 採用せず** (sparse-primary 不変)。これごと /pre-check 再走で再判定。
### impl-level (7, %12 全承認 → fold)
- **H2**: span-violation を **informative 統一** (−10 terminate list から除外; terminate は explosion/drop/reach-fail のみ)。
- **H3**: G6 sustain = **raw seat<3mm を 10 連続 step 再評価** (latched G5 flag と decouple) + GT trace「seat→pop-out during sustain → G6 fire しない」。
- **H4**: **achieved-span monitor** (FK/joint state で EE-EE 実測、command 層でなく) + asymmetric-IK-residual regression (as-executed 不変、[[feedback-invariant-preservation-verify-as-executed-full-path]])。
- **H5**: G3/G5 3mm seat の **base seat-dist 分布を DR±20mm 下で実測** (P0値+min/max、§運用18) — gate 到達 margin を DR 帯で示す (P3/smoke)。
- **H6**: G4 obs = **grip-lane-matched segment** (argmin-to-clip-center でなく action target と同 convention) + target-convention consistency test ([[reference-crosspolicy-metric...]] {11} copycat 回避)。
- **M1**: +200 value-clip + value_loss log (prohibited.md 105× 前例) + GT trace +216 (no bootstrap-inflation)。
- **M2**: [49] seated-seg d = **phase-active clip 追跡** 明示 (phase one-hot [42:48] で gate)。
### 順序 (v1)
C1 obs Rs 決定 → fold → /reward-design + /pre-check 再走 → PASS → checkpoint。(実行済 → §8 で更新)

## 8. post-RE-RUN disposition (/pre-check 2走目 = 9/10 prior CLOSED + N1-N6, %12 判断 11:40)
### N1 CRITICAL = FOUNDATIONAL span #2 → **Rs-CONFIRMED (b′)** (Rs「推奨で」13:01, spec v1.5b 189c7c5bf9)
- ✅ **RESOLVED**: 「common-mode scaling が span 保つ」は 6D per-arm で論理無効 (span-change=k·(Δ_R,y−Δ_L,y)≠0) → Rs が (b′) を確定。BLOCKED_FOR_USER 解除 (node state.md 13:06)。
- **(b′) phase-conditional structural projection (folded → §1 action+guards row, DoD⑩)**: **dual-grip 窓 [⚠ 3走目 §9 ISSUE-1 で **G3-inclusive both-grip schedule** に訂正 — 旧 {G1〜G2}∪{G4〜G6} は G3 C1-seat gap] は Δ を common-mode 部分空間へ hard-project** (span = 検知でなく **構造的に不変 = enforcement**) / **非 dual-grip 窓 (span-guard 補集合 = unclamp→GUIDE_C2→regrasp transit, single-grip, span 92→170mm 可変) は per-arm 許容** (N6 0.9mm reach fragility = per-arm 補正が要る場所) + **differential-drift regression = DoD⑩**。α-6D 契約不変。N1↔N6 同 window 整合。(窓定義 = spec:75 guards f1 忠実、旧「phase 10-11」gloss は 15-phase script label ゆえ 6-phase 予測子空間で再表現)。
### N2 HIGH = §運用29 numerator (DoD 追加, %12 承認)
- **DoD ⑨ 追加**: env G1-G6 predicates を canonical 81-grid で replay → **strict_v2 58/81 per-cell verdict match** (packet T3:74 分子非対称禁止の機械化)。env online success == offline baseline 保証。
### N3-N6 MED (fold, %12 承認)
- N3: incidence 表の explosion 記述訂正 = 「explosion 除く全 terminate 入力 present (explosion=justified-absent invalid-episode)」。
- N4: reachability artifact に **addressable-vs-draw split 明記** — corner-Δ は **late-flippable φ10 honest-F subset のみ learnable** (arc-placement/R_MISS draw-class [+39-51mm] は除外)。corner-episode injection は flippable φ10 honest-F cell を weight (P4 ≥4)。
- N5: 60D forward-compat を **[51:53] のみに scope** 明記 (phase one-hot [42:48] は 6-phase hardcoded; N-clip は per-segment repeating scheme 要 = 将来 doc)。
- N6: **reach-fail=−10 を再把持窓内で informative 化** (dual-grip re-grasp window; 0.9mm reach fragility で residual が corner 補正すべき場所で ≈0 抑圧を防ぐ)。**(b′) の per-arm 許容窓と一致** = N1+N6 が同 window で整合。

### 順序 (v4, 現行 — /pre-check 3走目 = BLOCK 13:33)
✅ (b′)+N2-N6 fold DONE → /reward-design PASS ((b′) delta) → **/pre-check 3走目 = BLOCK (1 CRIT + 4 HIGH + 3 MED; core (b′) algebra 健全確認)** → §9 disposition → **%12 に報告 → design-level (ISSUE-2/5/8b) の %12+Rs disposition 受領 → fold → 4走目 → PASS → checkpoint**。impl fold (ISSUE-1/3/4/6/7/8a) = DONE。

## 9. post-3走目 (/pre-check BLOCK, 13:33) disposition — 8 issue, ⭐core (b′) algebra CONFIRMED sound
verifier 確認: `(Δ_R,Δ_L)→((Δ_R+Δ_L)/2,·)` が commanded 差分を **axis 全てで zero 化** = N1 defect (scalar k は差分を zero しない) の真の fix。8 issue はいずれも core algebra を破らず、(1) projection 適用 window / (2) projected sample の PPO 会計 / (3-4) 検証 artifact / (5) transit 補正の学習可能性 を突く。

**⭐ DISPOSITION UPDATE (spec v1.5c da9d94b849, %12 13:4x — design-level 3 件 全 close, Rs ask 不要):**
- **ISSUE-1 = spec:75 も grip-schedule 窓に訂正済 (v1.5c①, %12 authored 誤り確認; round-2 実測 phase 1-7/13-14 = 92.42 定数と整合)** — 当方 build plan fold と一致。
- **ISSUE-2 = pushforward-log-prob 採用 (当方推奨)**: 会計方式 = 実装事項 (α-6D 契約 = action interface bind ゆえ不変, Rs ask 不要, trainer 段 L3 再検証)。env-core = projection-applied flag 露出 + clip-fraction DoD⑫。
- **ISSUE-5 = 新 obs 追加せず close**: [16:19] semantics pin (現 phase target cable seg = 再把持窓では reaching-arm 把持対象 seg) → 方向性 reach err = [16:19]−EE 線形導出。conditioning-check DoD⑪ 追加 (FAIL → +3D fallback, evidence-gated)。
- **ISSUE-8b = ASYMMETRIC 採用** (reaching arm full / gripping arm σ-cap)。
→ 全 impl + design fold DONE。**GO: /pre-check 4走目 (全込) → PASS → checkpoint** (%12 13:42)。

### CRITICAL (fold DONE + spec:75 訂正要 → %12)
- **ISSUE-1 = dual-grip window が G3 C1-seat [両腕把持] を gap で落とす → INV#2 未enforce**。**CONFIRM** (spec:75 明示列挙 {G1〜G2}∪{G4〜G6}, excluded=unclamp 以降 → G3 は両方に不在; CC2-CH1 で per-arm σ=7.5mm=span-noise 死)。**FOLD**: window = base-script both-grip schedule (両腕把持全域 G1〜unclamp直前 [G3込] ∪ G4完了〜G6), gate = grip-schedule 決定論 [earned-predicate 非依存] (⚠**§10 NEW-A で ∧both-contact→schedule-ALONE 訂正**: ∧ は fail-OPEN だった; both-contact = telemetry のみ) → §1 action+guards 反映済。**%12 escalate: spec:75 guards f1 も同 G3 gap = 訂正要**。

### HIGH
- **ISSUE-2 = 6D log-prob + projected execution の PPO 会計汚染 (trainer stage)**: projected differential 3-dim は dual-grip で return 無影響だが log π(a|s) に残る → μ_diff random-walk / σ_diff 膨張 / importance-ratio variance 膨張 → common-mode gradient clip 飢餓。**⚠ Rs premise 接触**: verifier primary fix (dual-grip 3D reparameterize) は「α-6D 契約不変」(spec:123) と**衝突** / alt fix (pushforward = projected 分布で log-prob) は契約維持。**→ %12+Rs escalate** (trainer-stage 会計 + 契約解釈)。env-core 側 = projection-applied flag を info 露出 + dual-grip vs transit clip-fraction/entropy smoke DoD (aliasing 検出)。
- **ISSUE-3 = DoD⑩ が commanded span (88mm 自明対称) を測り achieved hold-span (92.4mm) を測らず**。**CONFIRM** (task_config:246「hold-span=achieved sep ~92mm not commanded 88mm」, achieved=collision-obj floor)。**FOLD** (DoD⑩ = ACHIEVED EE-EE sep tight-tol + hold-span/slip 92.4±tol) → 反映済。
- **ISSUE-4 = N2 DoD⑨ (recorded-state replay) は predicate-port を測り online numerator を測らず**。**CONFIRM** (recorded=residual-free; online=residual で state 逸れ + live clock/contact)。**FOLD** (⑨a predicate-port env-core + ⑨b online residual≡0×81→58/81 route-executor LOUD-CARRY) → 反映済。
- **ISSUE-5 = transit reach 補正 (b′ per-arm の存在理由) が under-observed + p_hit 未discharge**: IK-resid [55:57]=scalar magnitude (非方向) / [51:53]=clip xy (非 cable-grasp-point) → sub-mm 補正 near-blind; dual-grip c2 と同 representable≠discoverable。**⚠ obs=Rs decision (60D) → %12+Rs escalate** (方向性 reach-error obs 追加 [60D→] OR [55:59] 充足文書化 + transit p_hit discharge [P3/P4, c2 と対称])。加えて [57:59] live-wired 確認 (GROVE r12) + ground-truth reachability (§運用18) = build 時 gate。

### MEDIUM (fold / carry)
- **ISSUE-6 = N6 は quit-button 回避 (良) だが sparse 下 transit hover basin 残** (−0.01×900=−9 < drop −10 → 初期 loiter 合理)。**mitigation = 既存 curriculum start-mix (spec:29 G4−ε 開始 → p(success) bootstrap) + P4 corner-episode 注入**; dense 項は sparse-primary 破壊ゆえ不採用。smoke DoD = transit hover が学習挙動でないこと確認。
- **ISSUE-7 = full-differential projection が span-preserving perp-differential (held chord re-orient DOF) も除去**: but position-only action + orientation-obs 無 → 元々 unobservable/unlearnable = 実損なし。「unphysical」は言い過ぎ=「unobservable なもの損失」が正; intentionally conservative。**carry**: seating が translation-only か canonical demo 確認; 要 re-orient なら position-only limitation (既 carry spec:109) Rs escalate。
- **ISSUE-8 = (a) explosion は PPO batch から MASK 要 (「非target」≠「除外」; value-target variance) → env-core が invalid episode を info flag (trainer mask 用) [FOLD] / (b) transit per-arm を ASYMMETRIC 化 (free/reaching arm=full per-arm / gripping arm=σ-cap or common-mode-limited, drop 防止) → %12 confirm (faithful: per-arm は reaching arm 用の意図, (b′) sub-nuance)**。

## 10. post-4走目 (/pre-check WARN, 13:58) disposition — 7 disposition RESOLVED, 5 NEW (2 HIGH build-blocker)
verifier: 7 design disposition は正しく推論、design-CRITICAL 残無。ただし 2 HIGH build-blocker + 3 MED/LOW。**core (b′) algebra は pushforward で μ_diff gradient=0 も verifier が代数確認**。
### HIGH (NEW-A = 当方 fold + spec 訂正 / NEW-E = spec §4 reconcile、両 %12)
- **NEW-A = ISSUE-1 gate の ∧ operator が安全不変条件に逆 (fail-OPEN)**: 「grip-schedule ∧ both-contact」は deformable-cable contact flicker で projection OFF → scheduled-dual 中 span 未保護 + differential scored → flicker 悪用学習。非対称: scheduled-dual で contact 一時 drop = 無害 (対称 command) / 両腕把持中 projection OFF = span 破れ → ∧ は逆方向。**FOLD** (§1 action+guards): gate = **base grip-schedule ALONE (決定論, fail-safe)**; both-contact = DoD telemetry assertion のみ (gate 入力にしない)。⚠**spec v1.5c amendment ① も同 ∧ = %12 訂正要 (schedule-alone へ)**。
- **NEW-E = spec §4 body が amendment と不整合 (stale-CRITICAL-reintroduction)**: da9d94b849 は addendum (line 124-125) のみ追加、§4 body 未 reconcile → **line 75 guards f1 = 旧 {G1〜G2}∪{G4〜G6} window (round-3 CRITICAL の原文, supersession pointer 無)** / **line 69 termination = span-violation を terminate 列挙 (H2 informative-only fold と矛盾)** / **line 74 DoD = ①-⑧ (⑨a/⑨b/⑩/⑪/⑫ 不在)**。builder が §4 body 読むと G3-gap CRITICAL 再導入。[[feedback-confirmed-decision-reflect-in-authoritative-spec]] 抵触。**→ %12 escalate: spec §4 body を same-turn reconcile** (line 75 window→grip-schedule ALONE gate + supersession / line 69 termination→explosion-invalid・drop・reach-fail(transit informative)・span informative-only / line 74 DoD→⑨-⑫ 追加)。当方 build plan は reconcile 済 = drift は spec 側のみ。
### MED/LOW (当方 fold + trainer carry)
- **NEW-B MED = ISSUE-2×8b entropy interaction**: pushforward で μ_diff/σ_diff unscored → dual-grip (大半 step) で entropy bonus が σ_diff 膨張 → 共有 σ なら transit entry で reaching arm 過大探索 + gripping σ-cap が膨張 prior と競合。**FIX (trainer carry, DoD⑫)**: entropy を **pushforward(scored) subspace で計算** (or σ_diff anneal / phase-dependent σ)。
- **NEW-C MED = projection flag は operator/subspace (or executed a′) 露出** (boolean 不可 — trainer pushforward が env projection と drift 回避)。**FOLD** (§1 action + DoD⑫)。
- **NEW-D LOW-MED = arm-role を base grip-schedule から導出** (window gate と同一 deterministic source; 境界 role-swap mislabel → 把持腕 full noise → drop 防止) + boundary consistency smoke DoD。**FOLD** (§1 action)。
- **ISSUE-5 reframe = FP32 でなく obs-normalization が真 risk** (0.9mm = 1m の 9e-4 相対; 第1層で解像困難); DoD⑪ を実 normalization 下で test; [33:36]/[39:42] pos-err は未検証 (GROVE r12)。**FOLD** (DoD⑪)。
### 順序 (v5)
NEW-A/C/D + ISSUE-5-reframe + NEW-B(DoD⑫) = 当方 fold DONE → %12 spec v1.5d (bfeedea7d8) 執行 (NEW-A gate schedule-ALONE + NEW-E §4 line 69/74/75 reconcile) → /pre-check 5走目。

## 11. post-5走目 (/pre-check WARN near-PASS, 14:16) disposition — 収束確認
verifier: NEW-A CLOSED / NEW-B/C/D CLOSED / ISSUE-5 CLOSED。**design substantively build-ready、design-CRITICAL・HIGH 残無**。WARN driver = **NEW-E が 100% closed でない (spec 残 2 line)** + 2 MEDIUM-LOW boundary carry。**verifier 明言: line 67/68 close + NEW-G/H carry → PASS build-ready**。
### NEW-E residual (spec 側のみ、%12 要請 — 当方 build plan は §運用28 で clean 確認済)
- **spec line 67 (reward) = 旧 terminate 括弧 (explosion/drop/span逸脱/reach-fail) が line 69 reconcile と矛盾** (§運用28 確認: line 67 stale)。round-4 NEW-E は「line 67」を挙げたが fix は line 69 に行き line 67 残。→ %12: line 67 → terminate = (explosion[invalid,mask]/drop); span/reach-fail = informative (line 69 参照)。
- **spec line 68 (success) = 「span-guard 全 phase PASS」= line 75 が「普遍 deadlock」と警告する語** (transit で span 170mm → success 不能; §運用28 確認)。→ %12: line 68 → span-guard = **dual-grip phase** scope (line 75)。
- ⚠ **当方 build plan = clean** (reward row に旧 terminate 括弧なし / success = G6 predicate に fold, 「全 phase」echo なし [grep: 全 phase finite = DoD③ / 6 phase 全 fire = DoD⑥ は別文脈] / termination row 反映済)。**drift は spec 側のみ = %12 2-min reconcile**。
### NEW-G MEDIUM-LOW (FOLD): schedule-vs-physics lag at unclamp boundary
- window は「unclamp直前」(scheduled) で close するが物理 release は数 step lag → その間 schedule=single → projection OFF + releasing-arm=full σ で両腕まだ物理把持 → transient span 摂動 (informative-only)。**FOLD**: window dual→single boundary = **release-COMPLETE** (schedule-unclamp **∧ contact-release-confirm**); both-contact telemetry を使い release 確認まで window close を hold (**projection ON 延長 = fail-safe 方向、NEW-A と整合** [contact は projection を無効化せず延長のみ])。boundary-consistency smoke DoD に追加。
### NEW-H MEDIUM-LOW (evidence-gated CARRY): projection gate (schedule) vs policy-obs regime (earned phase/contact) divergence
- residual 摂動下で earned phase [42:48]/contact [53:55] が deterministic schedule と境界数 step ずれ → policy regime-belief ≠ actual projection regime (bounded transient, invariant 破れなし; pushforward で dual-grip differential unscored ゆえ影響 = 境界数 step の noisy credit)。**CARRY (evidence-gated)**: smoke で boundary learning pathology 実証時のみ deterministic-schedule dual-grip bit を obs 露出 (Rs obs decision, ISSUE-5 の +3D fallback と同 no-churn stance); 否なら document carry。
### 順序 (v6, 現行)
NEW-G fold + NEW-H carry = 当方 DONE → **%12 に spec line 67/68 reconcile 要請 (2-min, 最終 NEW-E close)** → %12 修正 → 当方 §運用28 on-disk 照合 → verifier conditional-PASS (line 67/68 close + NEW-G/H carry) 充足 → **正式 %12 checkpoint (下書き済)** → 5体 [VERIFY]。full 6走目 は不要 (verifier が 2-line close を pre-clear、doc reconcile のみ)。

---
title: "LL: ApproachCable Bug History & Failure Analysis"
created: '2026-03-31'
tags:
  - knowledge
  - grasp-cable
  - bug-history
---

# ApproachCable Bug History & Failure Analysis

> v5 ApproachCable envの致命的バグ修正経緯と失敗分析の詳細記録。
> RL-Routing-Progress.md から分離 (2026-03-31)。
> 現進捗は `07-Design/00-DESIGN-STATUS-LEDGER.md` + 地図 `docs/logical_decomposition.html` を参照（RL-Routing-Progress.md は ≤2026-05-28 で FROZEN）。

---

## Bug Fixes (Session 48, 2026-03-29)

v5 env/demoの致命的バグ4件を修正。**旧デモ・旧訓練結果は全て無効。**

| ID      | ファイル                                              | 内容                                                                                 | 影響                                   |
| ------- | ------------------------------------------------- | ---------------------------------------------------------------------------------- | ------------------------------------ |
| ENV-BUG | `newton_approach_cable_env.py` L1219-1236            | `_apply_actions_batch`でxyzw quatをNewton IK(wxyz期待)に渡していた → xyzw→wxyz変換追加           | policyの回転アクションがIKで正しく反映されず、r_ori改善不可 |
| P-NEW   | `collect_approach_cable_demos.py` L452-460           | cable-adaptive rotationのwxyz→xyzwシャッフル除去。compute_hand_quat_for_cableが返すwxyzをそのまま渡す | デモの回転成分が不正                           |
| I1      | `collect_approach_cable_demos.py` settle_cable       | SIM_SUBSTEPSループ追加（settle実効時間が1/SIM_SUBSTEPSだった）                                    | ケーブル安定化不十分                           |
| I2      | `collect_approach_cable_demos.py` left_seg/right_seg | Y軸のみ→3D距離(np.linalg.norm)に変更                                                       | env整合                                |

**報酬有界化:** `r = -dist/eps` (非有界) → `r = exp(-dist/eps) - 1` (有界 [-1,0])。EPS_POS 0.020→0.100。旧式ではdist=696mm時にr_pos=-34.8/step→total≈-8000でvalue loss爆発→KL発散→LR崩壊。

---

## Bug Fix (Session 70, 2026-03-31): ORI-FRAME — dist_ori フレーム不整合

**v5-5e〜v5-6aの全実験でsuccess=0%の根本原因。4実験分の訓練コストを浪費。**

| ID | ファイル | 内容 | 影響 |
|----|---------|------|------|
| ORI-FRAME | `newton_approach_cable_env.py` L1109,L1248 | `_quat_distance(clamp_r_quat, seg_quat)` がhand body frame (Z=world -Z) と cable body frame (Z≈world +Y) を直接比較。構造的に直交、理論最小距離1.45rad | FINGER_CLOSE_ORI_THRESH(0.5rad)到達不可能。報酬が正しい把持姿勢から離れる方向に駆動 |

**修正:** `_compute_grasp_target_quat()` を追加。cable接線から `compute_hand_quat_for_cable()` で理想把持quatを導出し、それとの距離をdist_oriとする。修正後: デモ最良ステップで dist_ori=0.000rad (修正前: 1.706rad)。

**パラメータ調整:** RANGE_ORI: π→1.0, FINGER_CLOSE_ORI_THRESH: 0.5→0.3, CLAMP_ORI_THRESH: 1.0→0.5

**発見が遅れた理由:**
- メトリクス定義の正しさを検証しなかった（「正しい把持でのdist_oriはいくつか？」を1度も計算していなかった）
- dist_ori~1.05radのplateauを「学習限界」と解釈し、「構造的下限」の可能性を検討しなかった
- 確証バイアス: 「ポリシーのori学習能力不足」仮説を支持する証拠のみ収集
- → 運用ルール18追加: 新メトリクス実装時のground-truth検証を必須化

---

## Bug Fixes (Session 49, 2026-03-30)

env/demo/キャッシュの致命的バグ2件を追加修正。**Session 48以前の訓練結果（model_41等）は全て無効。**

| ID | ファイル | 内容 | 影響 |
|----|---------|------|------|
| CLAMP-SIGN | `newton_approach_cable_env.py` L167,176 | `_compute_clamp_pos`の符号バグ: `[0,0,-EE_TO_FINGERTIP]`→`[0,0,+EE_TO_FINGERTIP]`。clampが220mm上方を指していた | 初期dist 452mm→71mm。r_posが-0.99で完全flat→-0.49で勾配あり。**タスクを根本的に解けなくしていた** |
| FK-DRIFT | `newton_approach_cable_env.py` L264-267,800-803,920-923,965-968,1238-1262 | body_qからの直接読み取りでFK/body_q 1.3mm乖離が蓄積→zero-actionで手がZ方向に振動。per-world EE target tracking arrays追加 | 安定性: 振動するZ(0.87→1.53→1.44→1.01) → 2-step transient後安定 |

**追加対策:**
- DEMO-TRANSFORM: v5デモを符号修正変換して`grasp_cable_demos_v7_fixed.npz` (4633tr)作成
- CACHE-STALE: 旧preconditionキャッシュ(w4,w256)削除 → 再構築強制

**quat convention整理（確定事実）:**
- body_q[3:7] = xyzw (Warp transform convention)
- cable_orientation_utils = wxyz
- Newton IK wp.vec4 = wxyz
- env helper関数 = xyzw
- 変換必要箇所: body_q→Newton IK (xyzw→wxyz), cable_utils→body_q比較 (wxyz→xyzw)

---

## Bug Fixes (Session 50-51): BASE_HAND_DOWN_QUAT

**仮説: BASE_HAND_DOWN_QUAT が誤り → 否定。正しかった。**

- `BASE_HAND_DOWN_QUAT = [cos_pi8, sin_pi8, 0, 0]` (wxyz) は Newton の `collapse_fixed_joints=True` 環境で正しい
- collapse前のtool0 frame → collapse後のpanda_hand frameで22.5°オフセット分を含む

---

## Demo Collection Bug History (Session 51-52, 2026-03-30)

v5デモ収集パイプライン(`collect_approach_cable_demos.py`)のバグ修正経緯。

| Version | Episodes | Result | 原因 |
|---------|----------|--------|------|
| v8 | 5 | **0/5 全滅** | substepループ内`update_kinematic_bodies`欠如 + `model.state()`毎substep新規生成。kinematic bodyが1回しか更新されず、VBD solverが旧位置で接触計算 |
| v9 | 5 | **0/5 全滅** (3偽陽性+2把持不成立) | close phase中にarm joint全体をIK再計算+interpolation → VBD penetration爆発 → cable射出(1580/1109/1901mm)。残り2つは把持不成立(4.1mm) |
| v10 | 5 (cuda:2) | **5/5 SUCCESS** | catapult fix適用後。lift 104.1-106.9mm |
| v11 | 4 (cuda:0) | **4/4 SUCCESS** | 同上。合計9/9 SUCCESS |

**v9 catapult根本原因（確定）:**
- close phaseでarm j0-j6 + finger j7/j8を同時にinterpolation更新していた
- arm jointの微小動揺がVBD cable bodyとの貫通を引き起こし、VBD solverが爆発的反発力を生成
- clip routingの正規close phaseはfinger-onlyだったが、デモ収集スクリプトが全joint更新していた

**3点修正 (v10以降):**
1. close phase: arm j0-j6固定、finger j7/j8のみ変更 (FINGER_CLOSE_STEPS=500 steps)
2. 両手close (FINGER_CLOSE_POS、clip routing P1-CLOSE準拠)
3. close後にkinematic cable attachment (detect_grasped相当 + inv_mass=0 + substep内位置override)

> **⚠ kinematic attachment注意 (Session 55a追記):** v10/v11デモの修正点3はkinematic cable attachment（inv_mass=0 + 位置override）を使用。この手法はSession 55aで禁止事項に追加され、全コードから削除済み。v10/v11デモのclose後フレームはattachment影響下で収集されたため、cable obs (dim 16-22) の妥当性に懸念あり。BOX finger統合後のデモ再収集時にattachmentなしで収集すべき。

---

## Bug Fixes (Session 59, 2026-03-30): RESET-EE

`_reset_worlds` の EE ターゲット初期化バグ。**v5-5c 全6 run FLAT の主因。**

| ID | ファイル | 内容 | 影響 |
|----|---------|------|------|
| RESET-EE | `newton_approach_cable_env.py` L962-967 | `_reset_worlds`でEEターゲットを共有`_fk_state`から初期化していた。`_fk_state`は最後にIK解いたworldの状態で上書きされるため、reset後のEEターゲットが他worldのIK結果で汚染 | 初期dist 61mm→0.5-1.8m。EPS_POS=0.1で勾配消失域に入り学習不能 |

**修正:** キャッシュ済み`_settled_ee_r_pos/quat`, `_settled_ee_l_pos/quat`から復元。3箇所（`_save_precondition`, `_restore_from_cache`, `_reset_worlds`）で同一ロジックを使用し一貫性を確保。

---

## Bug Fix: BC Optimizer 2バージョン問題 (Session 65, 2026-03-30)

**`.pyc`バイトコードと現ソースでBC optimizerパラメータが不一致 → v5-5c/d全滅の追加要因。**

| パラメータ | .pyc (旧、Mar 29 23:34) | 現ソース (Session 60修正後) |
|-----------|------------------------|--------------------------|
| bc-lr | **3e-3** | 3e-4 |
| bc-updates | **10** | 1 |
| bc-grad-clip | **不在** | 1.0 |

**破壊メカニズム:**
- BC/PPO学習率比: ~3x（PPO 10 epochs考慮）
- magnitude(3x) × direction(降下デモ) × duration(200iter) = trust region系統的破壊

---

## Step v5-5 訓練結果 (Session 49, 2026-03-30)

**全7ラン実行 (~16.1M env steps):**

| Run | Device | Config | Iters | Best r_pos | Best r_ori | Outcome |
|-----|--------|--------|-------|-----------|-----------|---------|
| 30iter | cuda:0 | DAPG α=0.1, ent=0.01 | 30 | -0.54 | -0.82 | Plateau |
| 100iter | cuda:2 | DAPG α=0.1, ent=0.01 | 79 | -0.35 | -0.82 | Crash |
| cont2 | cuda:2 | resume m79, ent=0.001 | 58 | **-0.21** | -0.78 | Collapse @49 |
| **cont3** | cuda:0 | resume m100, ent=0.001, save=5 | **100** | **-0.147** | **-0.624** | **Complete** |

**cont3 学習曲線 (cumulative best across runs):**
- Phase 1 (iter 0-30): r_pos plateau -0.57 → 位置学習なし
- Phase 2 (iter 30-70): r_pos -0.57→-0.35 → **位置アプローチ開始**
- Phase 3 (iter 70-130): r_pos -0.35→-0.15 → **精密接近 (dist ~17mm)**
- Phase 4 (iter 130-180): r_pos oscillating, r_ori -0.75→-0.62 → **向き学習開始**

**重要発見:**
1. `entropy_coef=0.001` が必須。0.01ではnoise_std無制限増加→catastrophic collapse
2. `save_interval=5` で頻繁なチェックポイント保存が必要（PPO不安定性対策）
3. 位置と向きのトレードオフ: 最良位置(iter 81, -0.147)と最良向き(iter 93, -0.624)が別イテレーション
4. **ボトルネック: r_ori** — FINGER_CLOSE_ORI_THRESH=0.5rad(28.6°)に対し、最良orientation error=56°。距離は15mmに迫るが向きが2x不足

---

## Step v5-5c BOX finger訓練結果 (Session 56, 2026-03-30)

**BOX finger統合後の全6 run: ALL FLAT**

| Run | α | ent | noise | best r_pos | dist_pos range | 結果 |
|-----|---|-----|-------|-----------|----------------|------|
| BOX 30iter | 0.3 | 0.001 | 0.5 | -0.75 | 0.5-1.4m | FLAT |
| BOX 100iter | 0.3 | 0.001 | 0.5 | -0.85 | 1.1-1.8m | FLAT (killed@50) |
| α0.1/e0.01/n0.5 | 0.1 | 0.01 | 0.5 | -0.72 | 0.6-1.5m | FLAT |
| α0.1/e0.01/n0.3 | 0.1 | 0.01 | 0.3 | -0.73 | 0.6-1.2m | FLAT |
| cuda:0 run A | — | — | — | -0.87 | ~1.47m | FLAT |
| cuda:0 run B | — | — | — | — | — | FLAT |

**根本原因 (2段階):**
1. **`_reset_worlds` EEターゲット初期化バグ (RESET-EE):** reset後のEEターゲットが他worldのIK結果で汚染 → 初期dist発散 (61mm→0.5-1.8m)
2. **EPS_POS=0.1mでの勾配消失:** `r = exp(-dist/0.1) - 1` でdist≥0.5mは全てr≈-1.0（勾配≈0）

---

## Step v5-5d 訓練結果 (Session 59, 2026-03-30)

**resetバグ修正 + EPS変更: ALL FLAT。報酬設計は無関係。**

| Run | Device | EPS_POS | α | ent | iters | dist_pos_mean | r_pos | Status |
|-----|--------|---------|---|-----|-------|---------------|-------|--------|
| Run A | cuda:0 | 1.0 | 0.3 | 0.001 | 30 | 0.96-1.03m | -0.37 | **FLAT** |
| Run B | cuda:2 | hybrid (0.1+1.0) | 0.3 | 0.001 | 30 | 0.97-1.39m | -1.31 | **FLAT** |

**v5-5c/v5-5dの真の根本原因: DAPG BC lossの状態分布不整合**
- **デモ:** home位置(Z=1.44)からP0への降下軌道を含む → アクション平均 [-0.16, -0.14, -0.32]（強い下方バイアス）
- **env:** P0接近位置(Z=1.03)から開始 → 降下不要
- **BC loss** が「降下し続けろ」と教え、policyがcableを通り越す（~660mm/episode系統的drift）

**v5-5c/dの原因整理（確定）:**
1. RESET-EEバグ (Session 59修正) — 初期dist発散
2. BC loss状態分布不整合 — 系統的下方drift
3. BC optimizer旧デフォルト — trust region破壊
→ 1は修正済み、2+3が重畳して全FLAT

---

## Step v5-5e 中間メトリクス (Session 59→65)

**3実験並行実行（修正BC defaults適用）:**

| Exp | Device | Config | α | ent | w | iters |
|-----|--------|--------|---|-----|---|-------|
| 1 | cuda:0 A6000 | 純PPO resume@30 | 0 | 0.001 | 256 | 100 |
| 2 | cuda:2 PRO4000 | DAPG α=0.3, anneal=200, v14_box demos | 0.3 | 0.001 | 256 | 200 |
| 3 | cuda:1 A4000 | DAPG α=0.1, anneal=50, v14_box demos | 0.1 | 0.001 | 128 | 100 |

**初期メトリクス:**

| Exp | Iter | dist_pos_mean | r_pos | 傾向 |
|-----|------|---------------|-------|------|
| 1 | 30→38 | 82→75mm | -0.24→-0.27 | 微減 |
| 2 | 0→9 | 941→445mm | -0.78→-0.45 | 急速改善 |
| 3 | 0→8 | 287→422mm | -0.50→-0.42 | 悪化中 |

**判定マトリクス:**

| Exp 1 (純PPO) | Exp 2 (α=0.3新BC) | Exp 3 (α=0.1新BC) | 結論 |
|---|---|---|---|
| 学習 | 学習 | 学習 | 旧BC magnitudeが全原因。DAPG有効 |
| 学習 | FLAT | 学習 | α=0.3はデモ方向不整合で失敗、α=0.1は許容範囲 |
| 学習 | FLAT | FLAT | デモ方向不整合が支配的。P0デモ必須 |
| 停滞 | 学習 | — | DAPG表現形成が必要 |
| 停滞 | FLAT | FLAT | env/reward設計見直し |

**「DAPG寄与=0」は撤回（rs判断）:**
- 現デモセット(home→P0)での結論であり、DAPG手法自体は未否定
- cont3の成功には3つの競合説明: (a)BC消滅後の純PPO, (b)BC表現形成, (c)130iter重み蓄積
- フィルタデモ実験(v5-5e旧Run2)は旧BC下で走ったためデモ内容の独立テストではない

---

## P0デモ収集

**ファイル:** `thread_isaac_lab/scripts/collect_approach_cable_demos.py`
**変更:** `--start-from-p0`フラグ + P0初期化ロジック(500step補間+1s settle) + approach phase skip + `--demo-substeps`引数（SIM_SUBSTEPS不整合修正）

**収集結果:** 20/20 SUCCESS, 1800 transitions, `grasp_cable_demos_p0.npz`
**P0位置:** `TABLE_HEIGHT(0.80) + CABLE_RADIUS(0.004) + 0.010 + EE_TO_FINGERTIP(0.220) = 1.034`
**Action Z特性:** P0デモ Z mean = +0.191 (v14_box Z mean = -0.318)。方向整合は改善されたが、全軌道guidanceの欠如で総合性能は劣後

---

## 旧判定履歴 (v5-5e以前)

| Gate | 日付 | 結果 | 根拠 | 次のアクション |
|------|------|------|------|---------------|
| G1a (v8) | 2026-03-29 | **PASS** | dist -47% (6.59→3.47mm)。finger崩壊はclose-first exploit (0.2b項) | v9報酬で exploit排除→再訓練 |
| G1a (v11-A) | 2026-03-29 | **FAIL** | close回避に収束 (finger=66mm, dist=25mm, grasp=0%) | α低下案 (D) に移行 |
| G1a (v11-D) | 2026-03-29 | **FAIL** | approach→close順序学習済、post-close drift (6.8→46.3mm) | v12: r_hold追加 |
| — | 2026-03-30 | **PLAN RESET** | v5設計転換。obs 30D / action 12D / pose_match報酬。v8-v12廃止 | Phase 1 v5 Step v5-1 |
| G1-v5a (30iter) | 2026-03-30 | **PARTIAL** | R_pos -0.58 > -1.0 ✓, STEP完了=0% ✗。30iter間 r_pos plateau (-0.57)。dist_pos ~200mm | 100iter continuation |
| G1-v5a (79iter) | 2026-03-30 | **PARTIAL** | R_pos -0.35 (best) > -1.0 ✓, STEP完了=0% ✗。明確な学習曲線: -0.63→-0.57→-0.35 (加速中) | cont.100iter running |
| G1-v5a (cont3 179iter) | 2026-03-30 | **PARTIAL** | R_pos -0.147 (best) > -1.0 ✓✓, STEP完了=0% ✗。位置~17mm到達、向き56°がボトルネック | BOX finger統合 → デモ再収集 → 再訓練 |
| G1-v5a (v5-5c BOX 6run) | 2026-03-30 | **FAIL** | 全6 run FLAT。best r_pos=-0.72, dist 0.5-1.8m。EPS_POS=0.1で勾配消失 | EPS_POS=1.0 + 初期dist調査 |
| — (v5-5c root cause) | 2026-03-30 | **BUG FIX** | `_reset_worlds` EEターゲット初期化バグ特定・修正 (RESET-EE) | v5-5d: resetバグ修正 + EPS変更で再訓練 |
| G1-v5a (v5-5d 2run) | 2026-03-30 | **FAIL** | ALL FLAT。dist ~1m, noise_std不変。resetバグ修正+EPS変更は効果なし | root cause再調査 |
| — (v5-5d root cause) | 2026-03-30 | **ROOT CAUSE** | DAPG BC loss状態分布不整合。デモhome→P0降下、env P0開始。BC lossが~660mm/ep drift強制 | v5-5e: α=0純PPO / デモP0フィルタ |
| — (BC 2ver問題) | 2026-03-30 | **BUG FIX** | .pyc旧BC defaults (lr=3e-3, updates=10, no grad-clip) → BC/PPO比~3x。v5-5c/d全滅の追加要因。ソースは修正済み | v5-5e: 修正BC defaultsで3実験 |



## SNR不変性とAction Resolution Bottleneck (Session 72, 2026-04-01)

### 発見

PPO加法ノイズ下でadaptive pos scaleはSNR (Signal-to-Noise Ratio) を改善しない:

```
SNR = |mean| / (σ√dim)  ← scaleがキャンセル
```

v5-10/v5-11/v5-12が全て~16mm (≈POS_ACTION_SCALE) で停滞したのはこの構造的限界による。

### σ=0 Eval決定的証拠

v5-10 model_118, σ=0, 32worlds:
- dist_pos_median best: **6.6mm** (< 8mm G1-v5b閾値)
- dist_ori_median: 0.037 rad
- success: 6.25% (2/32)
- **Policy capabilityは十分。bottleneckは訓練ノイズのみ**

### 文献的位置づけ

精密操作の主流解法は「σを下げる」ではなく「RLの責任範囲を狭める」(residual architecture):
- Residual RL (Johannink+ ICRA 2019): base controller + 小RL補正
- ResiP (Ankile+ 2024): Diffusion policy + residual RL → 0.2mm精度 peg-in-hole 99%
- CQN (Seo+ ICML 2024): 階層的action離散化でσ排除

我々の2フェーズ方式 (Phase A: DAPG σ=0.5 → Phase B: resume σ=0.3, entropy=0) はpragmatic engineeringとして妥当だが、InsertIntoClip等でサブミリ精度が必要になった場合はresidual RLへの構造転換を検討すべき。

### 対策

- **Phase 1 (ApproachCable):** 2フェーズ方式で十分。σ annealing後にσ=0 eval 10%+確認
- **Phase 2+ (InsertIntoClip):** residual RL検討ポイント。scripted base controller + RL bounded residual



## explosion_count メトリクス誤読防止 (2026-04-02)

**事実:** `explosion_count` はRSL-RLが`int(np.sum(rc_dist > 1.0))` (0-256の整数)をステップ間で平均化した値。**割合ではなくraw count**。

- `explosion_count = 0.965` → 256 worldのうち ~1 world/step (0.38%)。無視できるレベル
- `explosion_count = 0.575` → ~0.6 world/step (0.22%)

**検証:** dist_pos_mean=270mmなのにexplosion_count=0.745は、74.5%が1m超なら mean≥814mmになるはずで矛盾。raw count解釈なら0.29%で整合。

**教訓:** RSL-RLのextras metricsは正規化方式がキー名から自明でない。int型カウントメトリクスはステップ平均の絶対値として報告される。world_countで割って初めて割合になる。



## Bug Fix (Session 132, 2026-04-11): AC v27 Bundled Fix — R/L Asymmetry + Timeouts Pollution + Demo Lift Phase

> v25/v26 訓練で観測された R arm drift と L arm action 圧縮の構造的不均衡を解消する束修正。C1/C2/P3/P4 の 4 修正を fresh start で同時投入。C3 は pre-review で取り下げ。

### 背景

v25 訓練終了後の per-arm 解析で 3 つの構造的非対称が判明:

| 観測 | 数値 | 原因仮説 |
|------|------|---------|
| L arm dist_pos が deterministic | 15.59mm 固定 | L arm のみ INIT_XY_NOISE 不在 (R arm は ±2mm random init) |
| L arm 軌道が R arm より小さい | 実効 action ~3.33x 削減 | L arm のみ無条件 0.3x action damping (L1780周辺) |
| value_loss が iter 後半で振動 | 安定化せず | `extras["time_outs"]` に explosion / cable_drop / success が混入 → terminal state に value bootstrap |
| BC loss が approach 進度で頭打ち | demo lift phase が approach BC を引っ張る | v26 demo は 90fr 全長で lift phase (post-grasp upward) を含む |

### 修正内容

**C1 — INIT_XY_NOISE 対称化** (`newton_approach_cable_env.py:1255-1276`):
```python
# L arm もR arm 同等に ±INIT_XY_NOISE noise を _ee_target_left に追加
self._ee_target_left[w] = base_pose_left.copy()
xy_noise = np.random.uniform(-INIT_XY_NOISE, INIT_XY_NOISE, size=2)
self._ee_target_left[w, :2] += xy_noise
```
**注:** `bq[ee_body_idx_left]` 直書き部分は FK broadcast (L1864-1877) で `jq_interp_all` から上書きされるため cosmetic。機能は `_ee_target_left.copy() + l_pos_delta` (L1797) 経由で IK target に noise が乗り後続物理を駆動する path で保持される。

**C2 — L arm 無条件 0.3x action damping 除去** (`newton_approach_cable_env.py:1780-1793`):
- L arm のみに付与されていた `l_pos_delta *= 0.3` (実効 action ~3.33x 削減) を撤廃
- 残存する damping は両腕とも ori-gate 条件下のみ (`pos_err < ORI_GATE_POS_THRESH AND ori_err > ORI_GATE_ORI_THRESH`)
- ori-gate ループは `r_pos_delta[w]` と `l_pos_delta[w]` のみを damp、`r_rot_delta` / `l_rot_delta` は両腕とも damp 対象外で symmetric

**C3 — DROP** (pre-review Bug #2 回避):
- 当初 C3 として「ori-gate 条件で w≈0 sign-flip discontinuity を smoothing する」修正を計画
- 5体 pre-review で「Bug #2 (BASE_HAND_DOWN_QUAT 0→π discontinuity) の再発リスク」が CONFIRMED → drop

**P3 — timeouts 汚染修正** (`newton_approach_cable_env.py:1621-1626`):
```python
timeouts[w] = int(timeout and not success and not explosion)
```
- 真の `MAX_EPISODE_STEPS` 到達のみ true
- explosion / cable_drop / success は `dones[w] = True` だが `timeouts[w] = False`
- CLAUDE.md ハードストップ「timeouts汚染禁止」(過去 value_loss 105倍爆発 vault log 2026-04-08 06:15) の設計準拠

**P4 — v27 BC demos filter** (`scripts/filter_grasp_demos_v27.py` 新規 207行):
- 入力: `grasp_cable_demos_v26_p0_45d.npz` (19eps × 90fr = 1710 tr)
- 出力: `grasp_cable_demos_v27_p0_approach_only.npz` (14 eps, 850 tr, 49.7%)
- Filter logic:
  1. **Quality gate**: `d_min = min(max(d_r, d_l)) <= 5mm` (grasp success proxy)
  2. **Approach completion gate**: first near-min frame within 5 frames of first zero-action frame (cable drift while zero-action 検出)
  3. **Longest sustained near-min run**: K_GRASP=5 contiguous frames in `(d_min + 5mm)` window
  4. Cut at `(longest sustained run end + 1)`
- 除外: 5 eps (quality_fail / never_near_min / approach_incomplete / no_sustained_hover)
- 効果: lift phase (post-hover frames where d grows beyond tol) を BC demo から除去

### 5体事前レビュー結果

| Agent | Total | CRIT | HIGH | MED | LOW |
|---|---|---|---|---|---|
| #1 | 10 | 0 | 0 | 3 | 7 |
| #2 | 12 | 0 | 3 | 4 | 5 |
| #3 | 11 | 0 | 1 | 4 | 6 |
| #4 | 6 | 0 | 1 | 3 | 2 |
| #5 | 5 | 0 | 0 | 0 | 5 |

**判定: PASS with WARN — 0 blocking issues**

**主要 HIGH 偽陽性検証:**
- **Agent #2 HIGH #8** "DAPG loader が `obs.shape[0] // EP_LEN` で episode segment 仮定" → `train_common.py:309-338` 直接確認、flat buffer + `torch.randint(0, demo_n, ...)` で v27 可変長対応 OK → **偽陽性確定**
- **Agent #3 HIGH** "C1 `bq[ee_body_idx]` 直書き no-op" → 確認の上 cosmetic、`_ee_target_*` path で機構保持 → **LOW 再分類**
- **Agent #2/#4 HIGH** "C2 で warm-start checkpoint 使用時 L action 3.33x 増で不安定化" → fresh start で対応、CLAUDE.md「崩壊checkpoint resume禁止」と整合 → **fresh-start 計画で resolve**

### 起動構成 (3並列 fresh start)

| Run | GPU | Iters |
|---|---|---|
| 3iter smoke | cuda:2 (PRO 4000 24GB) | 3 |
| 30iter | cuda:0 (A6000 48GB) | 30 |
| 100iter | cuda:1 (A4000 16GB) | 100 |

**共通パラメータ:** `--world-count 256 --num-steps-per-env 200 --alpha-init 0.7 --alpha-anneal-iters 50 --alpha-min 0.5` (CLAUDE.md α_min=0.5 BC維持方針)、no `--resume`

### 起動時 trip と教訓

1. **exit 127 — `python: command not found`**: bash 直接呼び出しでは `~/env_isaaclab6/bin/python` が PATH に入らない。`source ~/env_isaaclab6/bin/activate` 必須
2. **exit 2 — `--alpha-min (0.5) must be < --alpha-init (0.1)`**: 旧 `launch_training.sh` の `--alpha-init 0.1` は α_min=0.5 BC維持方針以前の値。CLAUDE.md 現行 (`α_min=0.5`) 要件に合わせて `--alpha-init 0.7` (`train_common.py default_alpha_init`) に更新

### 監視項目 (iter 1-5)

1. **L arm action magnitude statistics** — C2 の damping 除去で 3.33x 増の確認
2. **L arm ori overshoot** — damping 撤廃で過大回転していないか
3. **early-iter `dist_pos_l` 分布** — C1 の ±2mm noise 効果（前は 15.59mm 固定）

### 教訓

- **fresh start の必須性**: action scale を変更する修正 (C2) は warm-start checkpoint と本質的に非互換。崩壊 checkpoint resume 禁止と同じ理由で、新パラメータ意味論は新初期化から開始すべき
- **5体 pre-review の偽陽性検証手順**: HIGH 報告は必ず該当ファイル直接 cat で挙動確認。`train_common.py` の DAPG loader (flat buffer) と env の `_ee_target_*` path 検証は静的読みでの確認の代表例
- **bundled fix の利点**: 5 個別 fix を順次投入すると組み合わせ効果の評価が困難。fresh start で同時投入 → 効果切り分けは ablation で個別検証する設計

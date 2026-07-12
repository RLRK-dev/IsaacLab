# Stage-A /reward-design 4 成果物 (delta scope) — v3.3 (2026-07-12 12:4x JST — 5体 [VERIFY] cycle-1 fold M2/M8)

**v3 amendment (/pre-check 2走目 N1/N6 fold):** ① S4 (timeout+1.00) は spec v0.4 §9 tail (iv) [予定 release 後 drop 無効化] の下でのみ成立 — (iv) 不採用なら非 seated 枝は強制 release 後 drop −10 (≈−7.6) となり fail-slow<fail-fast 逆転が生じる (採用理由)。② 未訓練終端 = HOLD-stall→timeout OR creep→drop (−10) — どちらかは claim ① 測定で確定 (return ≈ +6 or ≈ −0.4) (v0.8 5体-fold M2 で timeout 単独期待を改訂; 残余 creep 0.169mm/step > 0 のため、spec v0.8 §2 claim ① 事前証拠)。HOLD-resume rate = 学習進捗 telemetry。

**改版:** v1 10:4x (spec v0.2 対応) → **v2 11:1x — /pre-check 1走目 BLOCK の CRIT-3 により v1 Artifact 2/4 は substrate 上実現不能な trace (EE deviation 32mm は kinematic re-pose 下で不可能) と判明 → cable-metric HOLD (spec v0.3 §4.2) で再作成。v1 の GATE PASS は spec v0.2 に対するもので v0.3 に非適用 — 本 v2 が正。**
**Scope:** reward 本体 G1-G6 = banked 不変。delta = HOLD (cable-metric) / curriculum (bank v2) / DR / export の到達可能性・会計検証。**spec = `STAGEA_TRAINER_ENV_DESIGN_GATE_RSTECHLEAD_20260712.md` v0.8 (v0.8 5体-fold M8)。**
**一次データ:** reward 定数 `route_env_config.py:86-100` / reward 実装 `newton_route_env.py:1422-1546` / p3 clock-conjunct `:1502` / residual≡0 canonical run 実測 `comp5_c2seat_fullfire_cablediag.npz` (健全域 band max 10.56mm / onset 15mm@f343 / onset→58mm = 54 RL steps、単位 = mm/RL-step [spec v0.6 ISSUE-A])。

## Artifact 1: Reachability (delta、v2)

| Component | Gating (delta 相互作用込み) | start states から到達可? | delta 新 dead zone? |
|---|---|---|---|
| G1-G5 +5 latched-ordered | p_k 物理述語 ∧ G_{k-1}.latched; p3 のみ ph≥2 (base clock) :1502 | P0 = env-core DoD6 実証 / bank v2 G_k−ε = **cable 込み復元 (spec §6.2) + restore 後 div_grip ≤ band の DoD** で経路上開始を構造保証 (v1 の「cable なし bank でも到達可」は虚偽だった — CRIT-1) | **stall class 1 件を honest 登録 (v1 の「なし」を訂正):** HOLD 中に C1 seat が劣化すると p3 が恒久 unfire → G4-G6 零信号 episode (timeout 終端、部分報酬)。訓練 deadlock ではないが零信号 class → falsifiable claim + G3-stall telemetry + smoke leg (spec §4.2) |
| G6 +200 sustain K=10 | G5.latched ∧ 物理述語 ×10 | 物理述語のみ (clock 非依存)。HOLD 凍結 = fail-safe 方向 | なし |
| time −0.01/step | なし (episode 時計、HOLD 中も進む) | 常時 | なし — hold-farming 構造排除 (route_t ≠ episode 時計、spec §4.1) |
| TERM −10 | explosion/drop | bank v2 の drop-arming 整合 (spec §6.2-3) で fork 直後の偽 drop を排除 | なし |
| (新) HOLD | div_grip > 15mm (cable-metric) | reward 成分でない → 勾配影響ゼロ | — |
| (新) export/DR | 観測系のみ | reward path 不触 | — |

## Artifact 2: Causal Gate DAG (v2 — cable-metric HOLD)

```
policy Δ (‖Δ‖≤20mm; transit 把持腕 σ-cap 2mm) → (b′)projection → executed = base(route_t)+Δ′
  → kinematic re-pose (EE 追従は構造的に完璧) → cable 物理 (drift は cable 側にのみ現れる = substrate 事実)
  → div_grip = ‖cable把持seg − 記録軌道(route_t)‖
       > 15mm --[GATE: HOLD]--> route_t 凍結 (base/grip/window/obs[50] 単一源凍結)、episode 時計は進む
       │  凍結 = march (drift 駆動源) の除去 → 残余 drift 縮小 (falsifiable ①: drift-under-HOLD < drift-with-march mean 0.58mm/RL-step、v0.5 再導出 bar)
       │  → σ-cap 2mm/step でも policy 補正が勝つ → div_grip 縮小 → resume 条件 (≤12mm or K=3 連続 in-band、hysteresis v0.8 M5) で再開
       └ 実測裏付け: onset (15mm) → grip-loss 域 (58mm) = 54 RL steps の補正猶予 (n=1、v3.1 単位訂正 [spec v0.5 ISSUE-A 連動])
  → p1..p6 述語 → G latch (ordered) → r_phase / G6
```

- GATE: HOLD 駆動信号 = time −0.01/step (単調損) + trainer Δ≈0 anchor。G latch never-revoked → HOLD による報酬喪失なし。
- **発火可能性 (v1 CRIT-3 の解消):** div_grip は FORK-1 失敗 run で実際に 15mm を越えた実測量 (f343) — 正制御 smoke leg で発火を実証する設計 (spec §8)。
- p3 ph≥2 × HOLD: 遅延 + stall class (Artifact 1 に honest 登録)。

## Artifact 3: Ground-truth 値 (v1 から不変 — 定数変更なし)

| Scenario | 計算 | R_total |
|---|---|---|
| S1 from-P0 成功 T=771 | 25 + 200 − 7.71 | **+217.29** |
| S2 bank G4−ε 成功 残T≈300 (G1-G3 earned-without-bonus) | 10 + 200 − 3.00 | **+207.00** |
| S3 from-P0 成功 + HOLD 120 step | 225 − 8.91 | **+216.09** |
| S4 timeout@900 G1-G2 | 10 − 9.00 | **+1.00** |
| S5 drop@t=400 G1-G2 | 10 − 3.99 − 10 | **−3.99** |
| §運用22 比率 | 225 vs 19 | **1:11.8** (:100 一致) |

順位 S1 > S3 > S2 > S4 > S5 健全。override 会計 (drop step で earned 破棄) は export 側で r_paid/earned 分離 (spec §5) — scalar reward 自体は不変。

## Artifact 4: Episode trace (v2 — substrate 上実現可能な系列)

```
Step 0: reset_to_phase(4, [w]) → bank v2 restore (arm/gripper q/qd + cable joint-space q/qd、spec §6.2 C2/M10)。restore DoD:
        div_grip ≤ 10.6mm 検証済み fork。route_t := bank_boundary[4]。G1-G3 pre-latch (no-bonus)。
        grip servo = banked grip_target seed。export: start_phase=4 / route_t / dr=(0,0) [bank は
        canonical cell 固定 — DR×curriculum 相互排他、spec §6.2-5]。
Step 1: Δ = +6mm (reaching arm、transit-asym)。EE 追従完璧 (kinematic)。cable は前 step 状態から
        物理応答。div_grip 5.2mm < 15 → MARCH。route_t += 1。p4 未 fire。r_paid = −0.01。
Step 2: cable 接触遷移で div_grip 16.8mm > 15 → HOLD。route_t 凍結 (base/grip/window/obs[50])。
        export: sync=HOLD, hold_count=1, div_grip=16.8。episode 時計は進む。r_paid = −0.01。
Step 3-5: base 凍結 = march 除去。policy Δ が cable を記録軌道側へ (観測上限 ~1.4mm/step; EE→cable
        gain <1 [slipping grip、CC4 実測: div 50mm まで pad 接触持続]) — div_grip 16.8 → 15.6 → 14.4
        → 13.9 → 12.8 → 11.9 (5-6 step) ≤ 12 (hysteresis bar) → 再開 (v0.8 M2/M5: 1-step 回復を multi-step 訂正 + resume = hysteresis 条件)。
        hold_count reset。r_paid = −0.01/step。
Step 6: r_reach 4.8mm ≤ tol ∧ contact_r → p4 fire、G4 latch。r_paid = +4.99。export:
        G4 = fired (pre_latched と区別)、‖Δ‖/bound=0.3。以降 G5→G6 は canonical 経路上。
```

## GATE 判定 (v2)

```
Reachability: PASS-with-honest-register (stall class = falsifiable claim + telemetry + smoke leg、隠蔽なし)
Causal DAG:   PASS (HOLD 発火可能性 = 実測量で裏付け、self-resolve = march 除去機構 + falsifiable claim)
Ground-truth: PASS (v1 から不変、override 会計は export 分離で保全)
Episode trace: PASS (全 step が substrate 上実現可能 — v1 trace の不備を訂正)

GATE: PASS → /pre-check 2走目 (v0.3 fold 検証) へ
falsifiable claims 登録 (spec §2/§4.2、v0.5 bar): ①drift-under-HOLD < drift-with-march (mean 0.58mm/RL-step) ②seat persists through HOLD
  — 反証 leg = §8 hold-fires probe / bank-G3 fork 摂動 leg。反証時 contingency = §9 (σ-cap 再導出 / mix・閾値再設計)
```

*%12 — PAPER-ONLY。INVARIANTS/task_config 不触。*

# (d) trigger 設計 gate — 素材 (%12/RS-TECH-LEAD)

**v0.2 — 2026-07-17 10:14 JST** (81-cell capture-window 解析を追補 — §4 の (i)(ii)(iii) 充足 +
(iv) canonical 分。v0.1 = 09:40)。charter = `PIN_D_TRIGGER_CHARTER_VTDESIGN_20260717.md` v1.0
(bank `e5ae494cb6`)。本 doc = charter §6-1 の素材側 (materials→ruling、D0 前例)。**設計解を主張しない**
— 実測と対応表を p5 裁定に供する。解析体 = `pin_d_capture_window_analysis.py` (+ `_result.json`、
純 offline: 録画 cable_xyz = 報酬計器が読む physics ground truth に対し、`clip_capture_predicate`
:903-911 意味論を vectorize [正対照 6 点で scalar 一致 assert、境界 ≤/< 込み]、y_win = 0.015 =
N1-N7 検証済み model 由来 bar)。

## §1 Q2 番号空間対応表 (charter G-item — 4+1 空間、file:line 付き)

| # | 空間 | nominal cell の値 | 定義 / 変換 | 根拠 (file:line) |
|---|---|---|---|---|
| S1 | **canonical 表の nominal label**「body30」(C1) /「body25」(C2) | body30 / body25 | **設計時の呼称 — runtime 空間への正確な写像は存在しない** (下記 ⚠) | `eval_runs/troot_verbal_teaching_20260705/CANONICAL_MOTION_TABLE_V1.md:126-128` (STEP 7-9「body30」) / `:139` (STEP 16「body25」) |
| S2 | **cable-相対 segment ordinal** (0..39) | **27** (nominal) / **25..34** (per-cell、§2) | pin_eqid の ordinal = segment ordinal (B3a 実測: 40 pin eq は contiguous +1-monotone — この導出が licensed) | `route_executor.py` `_prepare_recording` 経由 pin_eqid → `newton_route_env.py:1797-1807` (`_wire_c1_pin_from_recording` の seat_seg 導出、B3-alpha 警告込み) |
| S3 | **producer newton body id** | **55** = seg27 + 28 | **base = 28** (cable = newton body 28..67)。81/81 cell で pinned_body − pin_eqid = 28 (§2 実測、単一 shift) | recording npz `pinned_body` (81-cell scan、本 doc §2) |
| S4 | **env (consumer) newton body id** | **55** = `_cable_bodies[0][27]` | env も base 28 — producer と同一 layout (同じ 40-body cable build)。**ただし転写は禁止**: 実発火は world-position 解決 (index transplant = B3-alpha class) | `newton_route_env.py:729` (`_cable_bodies` = scene) / `:1840` (`seat_body = cable[seat_seg]`) / `:1844` (authorize は world 位置で) / g6 実測 `g6_live_rollout_pin_result.json` `seat_body_newton=55` |
| S5 | **env mjc body id** | **56** = newton 55 + 1 | mjc は world body 0 を持つ (+1 offset)。eq 解決は identity ベース (`resolve_pin_eq_index`) が robust 形 | g6 実測 `eq_obj1_mjc_body=56` / `route_executor.py:1015-1023` (index-space trap 警告 verbatim) |

**⚠ S1 の地位 (対応表の主結論)**: 「body30」は S2-S5 のどの空間の 30 でもない — S2 なら nominal C1 =
27 (≠30)、C2 実測交差 ≈ seg 16-17 (I4 fixture 接地) vs 表 body25 — **offset が C1 (+3) と C2 (+8.5)
で不一致 = affine 写像不能**。∴「body30」= 設計時 nominal ラベルであり、**runtime identity 源として
file:line で辿れる実体を持たない**。§21.4:756 の「seat_seg = route が定める固定段 (C1 = body30)」は
S1→S2 の写像が未定義のまま S2 の定数を約束していた。

## §2 ⭐ 新実測: C1 pin seat は per-cell 変量 — seat_k 分布と完全一致 (81/81)

**測定** (2026-07-17 09:3x、`w0e_81rerun_snapdown_0537/cell_*/route_demo_raw.npz` 全 81、fired frame の
unique):

- `pin_eqid` 分布 = **{25:1, 26:15, 27:19, 28:17, 29:2, 32:9, 33:9, 34:9}** (81 cells、全 cell 単一値)
- `pinned_body` 分布 = 同型 +28 shift ({53..62}、**81/81 で pinned_body − pin_eqid = 28**)
- **charter cite の seat_k histogram (`gate2_rerun_i3i4_probe_result.json` leg C) と 8-bin 完全一致**
  ({25:1, 26:15, 27:19, 28:17, 29:2, 32:9, 33:9, 34:9}) ⇒ leg C の per-cell seat_k = **C1 pin seat
  segment そのもの** (I4 probe は seat_k を routed/feed 境界に使う — 境界 = pin。命名の「c2」は
  freeze-scope 文脈で、値は C1 pin seg)

**帰結 (Q2 素材)**: **「route 固定段」premise は S1-S5 のどの空間でも実測に反する** — C1 seat は
cell geometry の関数 (spread 10 seg ≈ 146mm 幅)。⇒ Q2 の解は (A) fired-body 由来 か (B) recording
由来 (per-cell) の二択で、固定段 (C) は empirical に死んでいる。fork (A)/(B) の裁定は p5
(順序問題の episode-trace artifact = §4-(iv) で供給予定)。

## §3 D-6 結合事実 (Q1/Q5 の窓設計に効く producer 実測、cite = canonical 表 §3 台帳 :194)

- producer の実 phase 順 = `C1_SEAT` → **`C1_PIN`** → `L_HALF_UNCLAMP` → `R_UNCLAMP_RISE`
  (`route_executor.py:2804` vs `:3147`) — **pin 発火時 grip_cmd = [0.7407, 0.7407] = 両クランプ**
  (81/81、pB/p1/COORD2 独立実測)。把持が開くのは **onset+54 frame**。
- seat f2428 ≺ onset f2544 (116f 窓、§S3.3)。PHYSICS_STEPS_PER_RL=10 ⇒ RL step 換算: seat ≈ 243、
  recorded onset fire = **254 実測** ((a)(b) L-D)、G3 latch = **242 実測**。
- **予告 (宣言 delta 候補、artifact (iv) で確定)**: 幾何 capture trigger は capture 述語 True の
  最初期 ≈ step 243 で発火し得る = recorded onset 254 より **~11 step 早い** + **G3 latch (242) 直後**
  に隣接。「fire ∈ [seat 成立, STEP 8 解放)」(charter Q5) は満たすが、anchor 値は 254 から移動する —
  L-F2 型 leg では**宣言面**として扱う必要 (fire 分布の変化 = charter §6-4 の宣言 delta と整合)。
- D-6 の A0-pinless 上程 (Rs 専権、byte-repro 破壊コスト) は本 gate と独立 — (d) は録画再生成を
  要求しない (trigger は consumer 側)。

## §4 /reward-design 4 artifacts の (d) 版 (v0.2 で (i)(ii)(iii) 充足 + (iv) canonical 分)

### (i) 到達可能性表 — **DELIVERED** (81-cell 実測、result json `summary` + `per_cell`)

| 量 | 実測 (81 cells) | 意味 |
|---|---|---|
| onset − geo_fire(B) | **min 99 / p50 116 / p90 153 / max 156 frame** (= RL step 9.9〜15.6 @10phys) | 幾何 trigger は録画 onset より**全 cell で ~10-16 step 早く**発火可能 — 窓は knife-edge でない (charter §2-3 の canonical 116f が全 cell に一般化)。canonical 実測: geo_fire 2427 (banked seat f2428 と 1 frame 一致) |
| fire-before-release (B) | **81/81 TRUE** | pin-before-release 不変条件 (charter §2-2) は幾何 trigger 下でも全 cell 成立 |
| 進入 margin @first-True (canonical) | dx **0.07mm** / dy 6.47mm / z **835.93mm (rim 836 の 0.07mm 内側)** | **first-True は rim 通過の瞬間 = 進入 frame の margin はほぼ 0** (押込は上から降下)。その後 100+ frame 窓が持続 ⇒ 発火規則の設計余地 = 「first-True 即発火 (margin~0)」vs「sustain K frame」vs「margin bar」— **p5 裁定項** (Q1-(i) に接続) |
| INIT_XY_NOISE / DR 感度 | 分布幅そのもの (§2 の seat 10-seg spread + 窓 99-156f spread) が cell-geometry 感度の実測。INIT_XY_NOISE (±5mm EE) は trigger 窓には後半 step 事象ゆえ間接 (charter §4-7 どおり素材注記のみ) | |

### (ii) 因果 DAG — **DELIVERED** (実測 step 付き、Q2 順序問題の明示)

```
[physics] cable_xyz ──> capture 述語 (per-step、identity 源 = fork 依存)
                              │ True (canonical: f2427 ≈ RL 242.7)
                              ▼
                    authorize_clip_pin (唯一の書き手、backstop raise)
                              │ fire
                              ▼
              witness latch + eq_active=1 ──> [physical holding] ──> c1_retained → G6
                              │
   fork (B): identity = recording 由来 (episode 開始前から供給)
      ⇒ _seat_metrics は fire と独立に稼働: G3 latch 242 ≺ recorded fire 254 (canonical 実測)
   fork (A): identity = fired-body 由来 (発火時に確立)
      ⇒ 発火前は identity 無 = seat 計器 fail-closed ⇒ **G3 latch ≥ fire** — 順序が (B) と逆転。
      幾何 trigger の fire ≈ 242.7 は G3 latch 242 と実質同時 ⇒ (A) でも latch 遅延は ~0-1 step に
      収まる (幾何 trigger 併用の場合)。**ただし (A) × recorded-onset 型 trigger なら latch が
      254 まで遅延** — fork と trigger 規則の組で帰結が変わる (裁定素材)
```

### (iii) ground-truth 値 — **DELIVERED**

- volume bars (再 cite + result json `bars`): lat **3.5mm** (`route_env_config.py:174` = wall inner −
  cable R) / z **(821, 836) mm** (:175-176、strict `<`) / y_win **15mm** (model 由来、N1-N7 検証)。
- fire anchors (canonical): recorded onset **2544** (RL 254、(a)(b) L-D 実測) / 幾何 first-True
  **2427** (RL 242.7) / G3 latch **242** / release (min grip < 0.5 bar) **2694**。
  ⚠release 計器差 (loud): D-6 の「onset+54 で開く」と本解析の onset+150 は**別 bar** (D-6 = 独自
  計器 / 本解析 = min(grip_cmd)<0.5 の初 frame)。**どちらでも fire ≺ release は成立** (最小 99+54)。
  定義は artifact に固定、統一は p5 裁定に従う。
- seat 分布 (§2): C1 pin seat = per-cell {25..34}、pinned_body = seg+28 (81/81)。

### (iv) episode trace — **canonical 分 DELIVERED / 摂動 cell は宣言付き限界**

- canonical 因果列 (実測): G1 latch 98 → G2 146 → **[幾何 trigger 可能域開始 242.7]** → G3/G4 latch
  242 → recorded fire 254 → release 269.4 → done 343 (success 系、time_outs=0)。旧 (onset) 経路との
  diff = fire が 254→242.7 へ移動 (**宣言 delta**)、G3 隣接 (fork (A) なら latch 順序も変わる —
  上記 DAG)。
- **摂動 cell の latch 列は offline で得られない** (latch = env 計器; 録画から得たのは trigger 窓と
  順序不変条件のみ)。**declared limit**: per-cell trace が裁定に要るなら env replay probe を追加実装
  (G-F2 により nominal cell 限定、charter §4-6)。窓統計 (81/81) で足りるかは **p5 判断**。

### §4a ⭐ fork (A) 判別実測 (Q2 の決定的素材)

**A_first == B_seat は 49/81 のみ。不一致 32/81 は全て A = B−1** (delta histogram {(−1,): 32} —
方向一様: 1 個下流の隣接 seg が先に capture volume に入る)。
- ⇒ fork (A) は 40% の cell で **fork (B) と異なる segment に identity を束縛**する — 選択は系統的
  (−1 方向のみ、乱雑でない)。
- 接続する banked 教訓: [[feedback-nearest-node-selection-has-a-quantization-floor]] (離散 body vs
  連続目標の選択残差) — (A) の「最初に入った body」は half-pitch 級の選択 bias を持つ。
- 緩和材料: I3/I4 の identity 窓は **{pin−1, pin}** (escape fixture、`dfbddb4777` 系) — (A) の B−1
  選択は**既存計器の identity 窓の内側** ⇒ 計器非互換ではない (が、identity の意味 =「録画が押した
  段」vs「最初に入った段」の設計差は残る)。**裁定 = p5**。

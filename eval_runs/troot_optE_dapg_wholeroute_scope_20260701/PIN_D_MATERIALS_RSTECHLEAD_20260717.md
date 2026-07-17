# (d) trigger 設計 gate — 素材 (%12/RS-TECH-LEAD)

**v0.1 — 2026-07-17 09:40 JST**。charter = `PIN_D_TRIGGER_CHARTER_VTDESIGN_20260717.md` v1.0
(bank `e5ae494cb6`)。本 doc = charter §6-1 の素材側 (materials→ruling、D0 前例)。**設計解を主張しない**
— 実測と対応表を p5 裁定に供する。§1-§3 = 即納分 (Q2 G-item + 新実測)。§4 = artifacts (i)-(iv) の
skeleton (順次追補)。

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

## §4 /reward-design 4 artifacts の (d) 版 — skeleton (順次追補、揃った Q から p5 裁定)

- **(i) 到達可能性表**: capture volume への到達 margin — canonical + 81-cell 統計 (§2 分布が母材)、
  INIT_XY_NOISE / DR 感度。**status: PENDING**
- **(ii) 因果 DAG**: 述語→発火→identity→latch→reward の因果列、**Q2 順序問題** (identity 供給前は
  seat=False fail-closed ⇒ (A) 案では G3 latch が発火後に遅延) を明示。**status: PENDING**
- **(iii) ground-truth 値**: volume bar 群 (lat 3.5mm / z 821-836 / y_win 15mm、built-model 由来
  再 cite) / fire anchor 254 (recorded) vs ~243 (幾何、§3) / seat 分布 (§2)。**status: 部分 (§2/§3)**
- **(iv) episode trace**: canonical + 摂動 1 条件、旧 onset 経路との diff 列挙 (発火 step / latch 順 /
  escape 窓)。**status: PENDING**

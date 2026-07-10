---
doc_class: design-surface
---

# SLOT redesign + z_grasp + bend-hypothesis study (Rs 設計指示 3 件統合、paper only)

- Date: 2026-07-10 (COORD)。実装なし (§運用24; 着手は L3 必至、Rs 決定後の別ゲート)。
- Rs directives: ①slot 中央支持 (23:02、bank `f8cb48c2e8`) ②z_grasp 深さ +3/4/5mm (23:04、bank `888e5e5623`)
  ③**bend→pay-out 統一機構仮説 (23:06、bank `20a94d19fa`) = 本 study の中心検証対象**。
- Machine evidence: `comp3_slot_zgrasp_geom_probe.py` + `comp3_slot_zgrasp_geom_result.json` (built-model
  読返し、Rs (a) 指示どおり synthetic 不使用) + 本文中の再計算可能な npz 実測。

## §0. Grounding (§運用4)

| SSOT | 役割 |
|---|---|
| `newton_skill_env_base.py:1738-1770` | 現行 void builder (単一 Y-slot [0.090,0.210] × X [0.234,0.366]) |
| `2f85_koshape_scratch_wide.xml:97-171` | koshape claw asset (pad_box1/2 + f1ext/f2ext) — as-built は probe で読返し |
| `comp3_g1_armq_diag_capture.npz` | ik_chord 失敗 drive の per-frame cable/EE (曲率 leg 一次データ) |
| `w0e_81rerun_snapdown_0537/*` (81 cells) | 録画 (成功 reference; park-Y envelope / cable_xyz) |
| `newton_route_env.py:163-190` | lane-aware floor 定数 + `lane_void_parity_assert` (blast radius 対象) |
| 本日 chain (`39b206ddb0`..`cdac6b6972`) | G1 probe matrix + D ρ=0 (前提事実) |
| SRG void-parity banked (probe leg C、`comp3_void_readback_result.json`) | void [0.090,0.210]×[0.234,0.366] parity 実証 (blast radius 対象) |

## §1. 中心仮説 (Rs `20a94d19fa`) の数値裏付け — **強支持**

**仮説: clamp 点が低すぎ → close で cable に曲げ力 → 曲がった cable が lift 張力下で指から送り出される。**

| 量 (close 窓、held segs L=27/R=33) | 録画 (成功) | env ik_chord (失敗 drive) |
|---|---|---|
| held-seg 局所曲げ角 peak | L 2.6° / R 2.3° | **L 29.7° / R 13.1°** |
| full-close 時曲げ | L 1.35° / R 0.93° | **L 17.4°** / R 0.27° |
| 押し下げ (held-seg min z vs 0.8040) | −2.8mm | **−6.0mm** |

- 曲げの**左右非対称が L 失敗側と一致** (指令 path は対称 — 曲げは接触動力学で発生)。
- %12 整合注記どおり necessary-not-sufficient: armqdirect は同 z_grasp で成功 (曲げ margin 内に収まる) —
  録画 0.716 も survivable-marginal。曲げ除去は margin 回復手段。
- **データ適用範囲 (loud)**: 失敗 drive の cable per-frame は close 窓まで (capture t=0..114)。lift 窓の
  送り出し進行は tracked-seg slip 系列 (retry: axial +32.9mm) が代理。**armqdirect の per-frame cable =
  未捕捉 gap** — 成功側 lift 窓は録画 cable_xyz で代替 (lift 中曲げ ≤0.7° に低下 = 曲げ解消と共に安定)。

## §2. 実測基盤 (built-model 読返し + 81-cell 録画)

| 量 | 値 | 出典 |
|---|---|---|
| 爪 1 基の Y footprint (pad+f1ext/f2ext 全 geom) | **22.0mm** (L [0.0952,0.1173] / R [0.1828,0.2048]) | probe leg G (as-built) |
| 爪 OPEN 時 X sweep | [0.244,0.356] (現 void X 窓 [0.234,0.366] とほぼ一致 = X 窓は維持必要) | probe leg G |
| as-built コ gap (OPEN 姿勢、垂直投影) | **10.0mm** (asset 名目 14mm — 4-bar 傾きの投影で縮む; cable Ø8mm → 片側 1mm) | probe leg G |
| f1ext plate (現 z_grasp park) | top z = **0.8070** = cable 中心 0.8040 の **+3.0mm 上** | probe leg Z |
| 把持 lane park-Y (81-cell 全数) | span **2.5mm** (L [0.1038,0.1063] / R [0.1962,0.1987]; dy=−20 cell 群のみ +2.5mm、他は不動) | 81 npz 実測 |
| 録画 park pinch z | 0.80588 (= cable 中心 +1.9mm) | back-check / diag |

**幾何読み (bend 仮説の静的整合)**: 現 z_grasp で f1ext (下爪 plate) の top が cable 中腹 (+3mm) にある —
close の水平掃引+scoop で plate が cable を **下へ押しながら潜る**幾何 = §1 の押し下げ/曲げの発生源と整合。
⚠ **符号の限界 (loud)**: 本 probe は OPEN 姿勢の静的読返し。close 中の scoop (video 実測: tilt 25-40°) で
plate 軌道が変わるため、**z_grasp +3/4/5mm の改善方向は静力学からは確定できない** (open 姿勢では
+ 方向は f1ext をさらに cable 上方へ動かす)。→ 方向は §5 falsification probe の sweep が empirical に決める
(Rs が sweep を指定した構造と整合)。

## §3. Slot 再設計 (Rs `f8cb48c2e8`「中央で支える。空きはフィンガ進入部だけ」)

### 3a. 設計値 (/geometric-design Step 1-2; 実測ベース)

必要 slot 幅/腕 = 爪 Y footprint 22.0mm + 実測 park 遷移 +2.5mm (片側) + 進入 clearance 2mm×2:
**≈ 28.5mm/slot**。配置 (nominal lane 中心):

```
Y:  0.090      0.093            0.122       0.181            0.210
    |  edge    [== L slot ~29mm ==] [= 中央 SOLID ~59mm =] [== R slot ~29mm ==]  edge |
    現行: 連続 void 120mm ──────────────────────────────────────────
```
- **中央 solid ≈ 59mm** が lane 間 (Y 0.12-0.18) の cable 直下を支持 → 爪間垂れ/送り出しの土台を除去。
- X 窓 [0.234,0.366] は爪 OPEN sweep 実測とほぼ一致 → **維持** (2-slot は Y 分割のみ)。

### 3b. DR ±20mm との tension (Rs 指定の検討軸)

| DR shift 想定 | slot 幅/腕 | 中央 solid | 判定 |
|---|---|---|---|
| 実測 81-grid (±2.5mm) | ~29mm | **~59mm** | ✅ 余裕 |
| ±10mm common-mode | ~49mm | ~39mm | ✅ |
| ±20mm common-mode | ~69mm | **~26mm** | ⚠ 成立するが支持幅が細る (それでも >0) |
| per-cell slot (scene を cell 毎に生成) | ~29mm 固定 | ~59mm 固定 | ✅ だが scene が cell 依存化 (DR の意味が変質) |

固定 2-slot は ±20mm でも中央支持 26mm を残して成立 — 「両立不能」には至らず、options は
広 slot (±20 対応) vs 実測幅 (±2.5) の**支持幅 trade**。推奨 (advisory): 初期は実測幅 +margin
(~35mm/slot、中央 ~50mm) で切り、trainer DR 拡大時に slot を広げる段階設計。

### 3c. 録画 parity fork (Rs 指定 (3))

| fork | 内容 | cost | 影響 |
|---|---|---|---|
| **F-A env-only+整合** | 新 slot scene で旧録画を replay | 低 (scene 変更のみ) | grasp lane の cable z は不変 (lane は slot 内のまま table-resting 0.804) ✓ / **中央垂れ挙動が変化** (支持で垂れ消滅 — それが目的) / drag phase の摩擦幾何変化 (cable↔table 接触が中央 solid で増える) → 録画との軌道乖離は G3 以降に出る可能性 — grasp+lift 検証には F-A で十分 |
| **F-B 再録画 (MOTION STANDARD 再基準化)** | 新 scene + (z_grasp 変更するなら同時に) 全 81-cell 再録画 | 高 (録画 pipeline 再走 + 0.716 標準の置換 = banked 面の re-bank cascade) | 完全整合; z_grasp 変更は**再録画必至** (録画 arm_q/ee_pos が z を内包) → **slot 変更と z_grasp 変更は同一 fork (F-B) に載せるのが正** (Rs #2 指示どおり統合) |

**含意**: §5 probe (scripted 把持+lift のみ) は F-A で実行可能 (grasp+lift は中央支持の恩恵側で乖離源でない)。
F-B は probe が成立を示した後の採否判断。

### 3d. Blast radius 表 (Rs 指定 (4))

| 面 | 影響 | 処置案 (提案のみ) |
|---|---|---|
| base builder `newton_skill_env_base.py:1738-1770` | slot 構成の書換 (2 Y-solid + 2 X-fill → 4 Y 帯 + fills) | flag/variant 化 (byte-preserve default) — L3 |
| locked test builder (`test_newton_clip_routing.py:1055-1119` 相当、**Rs-LOCKED 不触**) | 旧 slot のまま → env と scene 不一致化 | F-B 採用時は locked 側も Rs 授権で改訂 or 録画側を新 runner 化; F-A 期間は「録画 scene ≠ env scene」を parity 表で管理 (g1_scene_align の前例) |
| lane-floor 定数 + `lane_void_parity_assert` (`65b5b9dd21`/`203f91594b`) | **assert が新 void で fail-loud する (設計どおりの drift guard 発火)** | slot 変更 chunk で lane 定数を 2-slot 化 + assert 更新 — R-C の存在意義そのもの |
| C1 島 carve-out (X=0.35, Y=0.15) | 中央 solid (Y 0.122-0.181) と C1 島 Y[0.135,0.165] が**重なる** → C1 直下が solid 化 = 島 float の意味再考 (支持と干渉はしない — clip は float +20mm) | 島 carve-out は維持で無害 (floor は max 側) — 要 1 行確認 |
| SRG void-parity banked (probe leg C 系) | 旧 void 前提の banked 結果に supersession 注記が必要 | F 採否決定時に LEDGER 行 + 注記 (%12 の記録系) |

## §4. z_grasp 深さ (Rs `888e5e5623`) — §2 の幾何表 + 変位表

| dz | park EE z | f1ext top z | cable 中心との差 | f2ext bot z (cable top 0.808 との clearance) |
|---|---|---|---|---|
| +0 | 1.0668 | 0.8070 | **+3.0mm (中腹)** | 0.8170 (+9mm) |
| +3 | 1.0698 | 0.8100 | +6.0mm | 0.8200 (+12mm) |
| +4 | 1.0708 | 0.8110 | +7.0mm | 0.8210 (+13mm) |
| +5 | 1.0718 | 0.8120 | +8.0mm | 0.8220 (+14mm) |

open 姿勢静力学では + 方向は f1ext を cable からさらに離す (= close scoop の潜り深さ次第で改善/悪化が
分かれる)。**結論は §5 sweep へ委譲** (方向仮説を probe が判定する事前登録構造)。z_grasp 変更の採否 =
F-B fork と同時 (再録画必至、§3c)。

## §5. Falsification probe (事前登録、実行は Rs GO 後 — §7 型)

- **形**: SRG-S1 型 scripted 把持+lift probe (route replay 不要の自己完結 scripted; SRG option-B 前例)。
- **scene**: 中央支持 variant (2-slot、§3a 寸法; probe-level scene 構築 = base/locked 無編集)。
- **sweep**: z_grasp ∈ {+0, +3, +4, +5}mm (Rs 指定)。
- **drive**: **env ik_chord 4-sub (現行 production そのまま)** — 曲げ除去だけで production drive が保持
  できるかの直接 falsification。
- **判定 legs**: G1 同一 (tracked-seg slip / axial / lift_rise / 動画レグ + 曲げ角時系列を追加)。
- **解釈 grid (事前登録)**: いずれかの cell で ik_chord 両腕 PASS → **仮説実証 + trainer D-b feedforward
  窓が不要化し得る (fork-(iv) 契約変更消滅 = 大幅簡素化)** / 全 cell fail → 曲げは主因でない (slot 支持
  単独では不足) → D-b 窓設計が確定路線に復帰。
- **追加 cell (提案)**: armqdirect-drive の cable per-frame capture 同梱 (§1 の gap 埋め、+2min)。
- cost: ~6min/cell × 4 + scene 構築 ≈ 30min GPU。

## §6. Decision 表 (Rs 用整理 — 決定は Rs)

| option | 内容 | 前提 | 効果 (期待) | trainer への含意 |
|---|---|---|---|---|
| S1 | slot 中央支持のみ (F-A replay) | §5 probe 成立 | 垂れ/送り出し土台除去; ik_chord 復活の芽 | **D-b 窓不要化の可能性** (最大簡素化) |
| S2 | slot + z_grasp (F-B 再録画) | probe で z 方向確定 | 曲げ源を二重に除去 | 同上 + MOTION STANDARD 再基準化 cost |
| S0 | scene 不変 (現行) | — | D ρ=0 (検証段) + B/E+D-b (trainer) で対処継続 | D-b 窓設計ゲートが必要 |
- どの option でも **D ρ=0 (scripted 検証段) の価値は残存** (3.61× 高速; Rs 確認済)。

## §7. 未実証 / loud 一覧

- 曲げ→送り出しの lift 窓直接実測は未捕捉 (armqdirect cable per-frame gap; §5 で埋める)。
- z_grasp 方向符号は open 姿勢静力学から不定 (scoop 依存) — sweep が決める。
- §3a 寸法は nominal-cell の爪 footprint 実測 + 81-cell park-Y 遷移に基づく — trainer DR 側の想定幅は
  Rs 決定事項 (±20mm なら §3b の細支持行)。
- 全て単一 cell 系実測 (§運用30): slot/z 変更後の受入は multi-cell sweep が必要。

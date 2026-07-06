# φ10 residual — H-drape round PREREG (fresh 封緘、two-key、%9 起草 → %12 countersign 待ち)

- **起草: %9 OPS-SUP 2026-07-06 09:4x JST** — Rs 決定 09:4x「推奨でよい」= 選択 (ii) H-drape zero-GPU mapping leg (state.md 170 loud 記録、%12 charter)。dy-arc Stage-A = **W1 close** (二鍵 EXACT bank `06c25583f1`、識別不成立)。本 round は **post-hoc 仮説 H-drape の新規封緘**であり Stage-A の auto-continuation ではない (PREREG 規律: fix 規則は機構同定後にのみ書ける)。
- **prior-art gate (V7/V10)**: keyword {H-drape, settle-basin, drape-over-clip, crossing-x, fix-class} — 唯一の BLOCKER hit = state.md:170 = **本 round を授権する 09:4x directive 自身** (過去失敗 path でない → disposed, false-positive)。他 keyword は hit 0。
- **substrate**: runner commit `6808964dc3` (F-1b′′ 採択済、read-only) / 150mm+lift-raise geometry (RUN1_REFERENCE_V2 = `5f1c3f92…`) / **env pin `W0E_F1B_SNAPDOWN=1` = 対象 npz 生成条件 (as-executed 照合列)** / device cuda:0 / dir = `w0e_phi10_arc_probe/<HHMM>_hdrape/` 世代 tag + immutable。**本 round は zero-GPU (既存 81 npz + run.log の read-only 解析のみ)、新 run なし。**

## ⚠ Honest 前提 (本文化、%9 (3) 認識 = %12 要請)

- leg-1 (zero-GPU) が判定できるのは **coordinate lever の必要条件 (幾何連続性 + 到達 margin) のみ**。lever が実際に drape を HIGH へ flip するかは **確認できない** — それは Stage-B (GPU、新 run) の問い。
- ゆえ判定「COORDINATE」= 「GPU test を **提案する価値あり**」であって「安い確定 win」ではない (necessary-not-sufficient)。COORDINATE 判定でも **GPU/fix 前に Rs 再エスカレーション必須** (pin)。
- 判定「SETTLE-BASIN」= coordinate lever が幾何的に不可能 (連続でない or margin 超過 or crossing_x が height を決めていない) → GUIDE/delivery 改変 = 発明動作 = **STOP+Rs (W2 同型)**。

## 仮説 H-drape + 反証条件 (2×2 規律、支持だけ集めない)

- **H-drape**: R-lane (y = CLIP2_Y + GHS = 0.044) 交差点の cable rest 高さは、taut な cable が交差する **x が C2 clip (x=0.40) の footprint に乗る (HIGH ~848 = clip 構造上 rest) か外れる (LOW ~829 = 床 rest 825+4) か**の drape 幾何で二値決定され、settle/drag 時に確定する (leg-1: 25/27 が ph11-entry で既定、pin→crossing taut 両群)。
- **反証条件 (pre-data 固定、いずれか成立で H-drape REFUTE or 機構モデル修正)**:
  - **R1 (consistency、主判別)**: height = f(crossing_x vs x*) が **全 81 cell で一様に成立しない** (crossing_x > x* なのに LOW、or < x* なのに HIGH の cell が存在) → crossing_x が height を決めていない = H-drape の駆動変数モデル REFUTE (dynamic settle-basin 等の別機構)。
  - **R2 (rest-surface)**: HIGH cluster z が clip 構造 rest 高 (wall 840/850 + r=4) と、LOW cluster z が床 rest 829 と **合致しない** → two-rest-surface モデル誤り。
  - **R3 (drape-contact)**: HIGH cell の cable に **C2 clip footprint 上・clip-top z 近傍の node が実在しない** → 「clip に drape」でなく別要因の懸架。
- **✗ 非判別 (same-output)**: 「height 二値」単独は continuous-threshold と discrete-basin の**両方**と consistent → 非判別 (leg-1 で既知)。判別する観測 = R1 consistency (same crossing_x → same height) + O-E 連続性。

## Observable 定義 (zero-GPU、機械適用、開封前固定)

- **O-A crossing_x + crossZ @ ph11-entry (全 81 cell)**: leg-1 machinery (parser v2.1 同機構、lane=0.044、R-EE 最近傍交差) を crossX_entry も dump するよう拡張。**PASS 対照 (φ0/φ5 列 54 cell) を必ず含む** (H-drape が全 grid で成立するかの検定に対照が要る)。
- **O-B drape-over-clip contact (全 81 cell)**: ph11-entry frame で C2 clip footprint (x∈[0.40−hw, 0.40+hw], y∈[CLIP2_Y−hw, +hw]; hw = clip 半幅、task_config から確定) 内に cable node が存在し、その z が clip-top 近傍か。HIGH cell = 存在、LOW cell = 不在 を予測。
- **O-C rest-surface match**: HIGH cluster z 分布 vs clip wall-top+r / LOW cluster z 分布 vs 床 rest 829。R2 の検定材料。
- **O-D producer settle-truth (全 cell、run.log)**: `[C2-DUAL-SETTLE]` の「near-C2 cable z vs groove」+ SETTLED_IN_NOTCH — 独立な settle 時実測 (leg-1 で P-2′ z824.5 table / P-6′ z829.2 SETTLED=True を確認済)。
- **O-E fix-class discriminator (核、全 81 cell)**:
  - (e1) **連続性**: crossing_x が各 dy 列内で dx に対し単調・平滑か (跳躍 = discrete 兆候)。
  - (e2) **consistency (=R1)**: height = f(crossing_x vs x*) の一様成立。x* = **HIGH 群 crossing_x 最小と LOW 群 crossing_x 最大の中点** (手順 pre-fix、値は事後、annotate-not-reclassify)。leg-1 予備値: HIGH crossX~0.38 / honest-F-LOW~0.367 → x*≈0.373。
  - (e3) **到達 margin**: LOW-fail cell 毎に Δ = x* − crossing_x。**F-1a-class 座標 authority = |comp| ≤ 22mm clip、有効 comp = 0.5·offset (runner :4262 実測: `clip(−(1−λ)·dx0, ±22mm)`, λ=0.5)** と比較。leg-1 予備: honest-F Δ≈+8mm (authority 内) / R_MISS crossX~0.32 → Δ≈+55mm (**authority 超過**)。→ **SPLIT verdict を許容**。

## 2×2 identifiability 表 (pre-data 固定; ✗ = same-output 非計上)

| | O-A/O-B height⇔clip-footprint | O-E e2 consistency | O-E e1 連続性 | O-E e3 margin vs 22mm |
|---|---|---|---|---|
| H-drape (coordinate) | 一致 | 一様成立 | 平滑単調 | LOW-fail が authority 内 |
| H-drape (settle-basin) | 一致 | **成立せず** (same x→異 height) | 跳躍 | — (basin は margin 無意味) |
| ¬H-drape (別機構) | **不一致** (footprint 上でも LOW 等) | 不定 ✗ | 不定 ✗ | 不定 ✗ |

- 判定規則: 支持 = 該当列で予測一致 ∧ 他モデルと相違する場合のみ計上 (✗ 禁止)。

## fix-class verdict → gate mapping (機械適用)

- **COORDINATE (全 LOW-fail が authority 内)**: 連続 ∧ consistency 成立 ∧ 全 Δ ≤ 22mm → **Stage-B 提案** (F-1a-class の C2-drape 版 coordinate-comp、offset-gated、fresh 封緘 addendum) — **GPU 前 Rs 再エスカレーション pin**。
- **COORDINATE-partial (SPLIT)**: 連続 ∧ consistency 成立 だが Δ が cell 集合で二分 (honest-F 内 / R_MISS 超過) → **部分 Stage-B 提案** (authority 内 subset のみ) + 超過 subset は residual として Rs (発明動作要否は Rs)。
- **SETTLE-BASIN**: consistency 不成立 (R1) or 連続性 跳躍 → **STOP + Rs (W2 同型)**: coordinate lever 幾何的に不可、GUIDE/delivery 改変 = 発明動作は Rs 専権。
- **¬H-drape (R1/R2/R3 いずれか)**: H-drape REFUTE → 機構再同定が必要 → **STOP + Rs** (本 round の仮説が誤り、新 round 要否 Rs)。
- **INDETERMINATE**: 観測混在・単独支持なし → **W3**: 部分結果報告 + Rs 判断。
- validity: 全 cell finite (npz)、crossing 抽出失敗 cell = loud 除外 + 分母明記。

## Predicate 完全性 (§運用29) + scope (§運用30)

- 本 round leg-1 の主張 leg = **① H-drape 機構の確認/反証 ② fix-class の必要条件判定** のみ。**cover しない leg** = fix 有効性 (Stage-B GPU) / SR uplift (将来 re-grid two-key のみ) / lever の実在 (幾何が許すか否かのみ判定、lever を「ある」と主張しない)。
- scope: COORDINATE 判定は「GPU test 提案の可否」まで。単点・単 round での面主張禁止。informal 天井 (規律外): 21 cell 全快 = 79/81 = 0.975、公式は re-grid two-key のみ。

## 封緘・交換手順

1. %12 countersign (本 doc 追記) → 凍結 commit (%12、%9 は 0-commit)。
2. leg-1 は %9 実行 (zero-GPU、既存 81 npz、script 自 sha を結果 header に記載 = pin-1 同格)。
3. SEALED 読み: %9 = O-A..O-E 計算 + fix-class verdict / %12 = 独立 recompute (O-A crossing + O-E consistency の別実装) + O-D 照合 — 交換後 2×2 機械適用 → joint verdict → Rs (COORDINATE なら Stage-B は GPU 前 Rs 再エスカレーション、SETTLE-BASIN/¬H-drape なら STOP+Rs)。

## COUNTERSIGN (%12 RS-TECH-LEAD、2026-07-06 09:5x JST)

- **独立照合済**: F-1a authority 式 = runner :4234 (comp1) / :4262 (comp_final) の `clip(−(1−λ)·dx0, ±0.022)`, λ=0.5 実在確認。反証 R1-R3 + PASS 対照 54 cell + SPLIT 許容 + honest 前提 (necessary-not-sufficient) = 要件充足。prior-art BLOCKER disposal (授権 directive 自身) = 正当。
- **pin-1**: leg-1 script sha を結果 header に記載・交換時凍結 (従前同格)。
- **pin-2**: O-B の footprint パラメータ (clip 半幅 hw、wall y-offset、wall-top z) は task_config / clip_parts (:1164-1170) から機械取得し結果 header に echo する (手打ち禁止、SSOT 接地)。
- **pin-3**: e3 の ±22mm authority は F-1a の「class 尺度」としての流用 — F-1a 自体は C1-seat leg の comp であり C2-drape の fix site ではない。COORDINATE 判定時の Stage-B 提案は **新 site (C2 系 leg) + その site 固有の authority** を fresh addendum で定義すること (F-1a がそのまま直すという含意を持たせない)。
- 上記 3 pin 込みで **COUNTERSIGN = 承認、封緘発効**。leg-1 (%9 zero-GPU) 実行可。私 leg = O-A/O-E 別実装 recompute + O-D 照合 (Stage-A の定義 reconcile 教訓により、実装前に本 doc の定義を機械参照する)。

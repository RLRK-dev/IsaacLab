# φ10 21-cell class — dy-arc 機構同定 probe PREREG (Stage-A、two-key 封緘、%9 起草 → %12 countersign 待ち)

- **起草: %9 OPS-SUP 2026-07-06 08:5x JST** — Rs 決定 08:3x「1:a 追撃 (確認用動画も作成)」(state.md eba71929b3) を受領。two-key 標準形 step 1 (PREREG first、observable 定義 + bars + consequence mapping = pre-data 固定)。
- **substrate**: runner commit `6808964dc3` (F-1b′′ snap-down 採択済) / 150mm+lift-raise geometry (RUN1_REFERENCE_V2 = `5f1c3f92…`) / **env pin `W0E_F1B_SNAPDOWN=1` 全 run 必須 + [W0E-F1B] mode tag = as-executed 照合列** (運用 pin、state.md addendum 08:15) / device cuda:0 固定 / dir = `w0e_phi10_arc_probe/<HHMM>_<tag>/` 世代 tag + immutable-until-joint-read-close。
- **対象 class (banked、packet v1.2 + 私鍵 `w0e_offline_validation/p9_recount_w0e_81rerun_snapdown_0537.txt`)**: φ10 21 cell = dy∈{−20,−5,+10} × dx≥−10 (7 dx/列)。全 crossZ LOW (822.8-831.3)。**列内境界: dx≤−15 は 3 列とも HIGH-PASS (847-848)** — 境界 contrast は既存データに存在 (新 run 不要)。grade: R_MISS 4 ((−10,+10)(15,−5)(20,−5)(20,−20)) + honest-F 17。
- **起点の謎 (probe as-executed 同一)**: P-2′(0,−5) / P-3′(5,+10) snap-up Δ+5 FAIL vs P-6′(20,−20) snap-up Δ+5 HEAL — snap param 完全同一 → 判別変数 = dy 自体 (+ 既存 grid より dx も独立軸)。既知: pin node は φ10 列で 32-34 (PASS 群 26-29 比 +5〜6 node シフト、列内一様 = necessary-not-sufficient) / pin→crossing 節点距離 dist=8 は全 81 cell 一様 (非判別、私鍵 summary 行)。

## 仮説 (Stage-A、機構候補 3)

- **H-slack (弧たるみ収支)**: crossing 高さ = 自由弧 (pin→crossing、8 seg = 120mm 一様) と chord (pin↔crossing 直距離、dy/dx 依存) の差 slack で決まる。slack≈0 = TAUT → HIGH / slack 大 → bow → LOW。snap-up が dy=−20 のみ効く理由 = lane が C1 から最遠 (Y span 126mm) で chord≈arc の taut 域、|dy| 小では slack 域のまま。
- **H-feed (上流送り結合)**: Δ/GRASP_YC shift が settle (φ 量子化 152.5/155.0、caveat-a) 経由で L 送り位置に伝播し、pre-grasp の供給 slack を変える。heal は幾何でなく送り短縮が生じた cell でのみ起きる。
- **H-capture (pin 捕捉集合 + 多重交差)**: 捕捉 arc シフト (pin 32-34) が drag 中の slack 解放経路を変え、lane を複数回交差 — parser の「R-EE 最近傍交差」選択が pin 側でない枝を掴む cell がある。O1 算術矛盾 (arc < chord) が出た場合はこの仮説へ昇格。

## Observable 定義 (機械適用、開封前固定)

- **O1 slack 収支 (zero-GPU、既存 round-2 npz 27 cell [φ10 3 列×9 dx])**: R-close frame で arc_len(pin node→crossing seg、cable 経路積分) − |xyz_pin − xyz_cross| = slack。**手順を事前固定**: (a) validity leg = arc ≥ chord (負 slack = 経路仮定破綻 → H-capture 昇格 flag)、(b) LOW/HIGH 群の slack 分離を検定、分離 bar s* = 両群 gap の中点 (事後数値だが**手順**は本行で固定、annotate-not-reclassify)。
- **O2 pre-grasp 交差状態 (zero-GPU、同 npz)**: R 降下開始 frame (phase 11 突入) で既に crossZ LOW か。⚠ **H-slack / H-feed の same-output cell (両方 LOW を予測) = 相互 falsifier にならない**。falsify 対象 = 「R 干渉が LOW を作る」系の残余仮説のみ。
- **O3 送り差分 (zero-GPU、run.log + npz)**: P-2′/P-3′/P-6′ の as-executed settle / GRASP_YC / L final feed 位置の系統差。H-feed = heal cell (P-6′) にのみ送り短縮方向の差を予測 / H-slack = 幾何以外の差なしを予測。
- **O4 反実仮想 probe (新 run ≤4、probe-env-gated)**: snap-up Δ+5 を **(−10,−5)** [境界直上、H-slack: taut 寄り → heal 予測] と **(+10,+10)** [slack 富裕、H-slack: no-heal 予測] に適用。H-feed 予測は O3 の送り model から dispatch 時に導出し、H-slack 予測と**同符号なら本 cell は非判別と宣言** (2×2 規律)。+ 対照 2: 同 2 cell の snap-OFF 再走 = 既存 round-2 と byte-id 期待 (再現性 leg)。

## 2×2 identifiability 表 (pre-data 固定; ✗ = same-output 非判別 cell)

| | O1 slack fit | O2 pre-grasp LOW | O3 送り差分 | O4 (−10,−5) heal / (+10,+10) no-heal |
|---|---|---|---|---|
| H-slack | 分離成立 + LOW⇔slack>s* | LOW ✗ | 差なし | **予測どおり = 支持** |
| H-feed | 分離不成立 or 混在 | LOW ✗ | P-6′ にのみ短縮差 | 送り model 次第 (dispatch 時宣言) |
| H-capture | **arc<chord 矛盾 cell 出現** | 不定 ✗ | 差なし | 不定 ✗ |

- 判定規則: 支持 = 該当列で予測一致 ∧ 他 H の同列予測と相違する場合のみ計上 (✗ cell は計上禁止)。**識別成立 = 1 H が判別列 ≥2 で単独支持 ∧ 矛盾 0**。

## Stage-A 実行順序 + budget

1. leg-1 (zero-GPU): O1+O2 を既存 27 cell npz で機械計算 (%9 script、封緘) + O3 を probe log から抽出。**新 run ゼロで識別成立なら O4 省略可** (bounded 原則)。
2. leg-2 (GPU、O4 必要時のみ): 新 run ≤4 (反実 2 + byte-id 対照 2) + C-0 (0,0) 1 run (sha == 5f1c3f92 gate、新 build 汚染検出)。**Stage-A 総 budget ≤5 run** (~10 min)。
3. **動画 leg (Rs 確認用、%11 render)**: dy=−5 列の同列 contrast 3 cell — **(0,−5)** honest-F LOW / **(20,−5)** R_MISS / **(−20,−5)** HIGH-PASS 対照。witness 窓 = R-close ±150 frame、crop 中心 = 各 cell の crossing 点 (私鍵診断列 crossX/crossZ、例 (0,−5): x0.368 z830.9)。**dual-stream 規約: analyst へは CLEAN frames / Rs へは annotated** (banked 動画設計)。`p9_witness_aim.py --clips` で witness 点自動生成。

## 見込み判断 gate (Stage-A → Stage-B、機械適用)

- **GO**: 識別成立 ∧ 同定機構に **座標 only の fix lever が存在** (MOTION STANDARD p2r_c11 適合、発明動作なし) → Stage-B へ。**Stage-B は別封緘 addendum** (fix 規則は機構同定後にのみ書ける — 偽 pre-reg を置かない): probe ≤6 (grade 代表) + C-0、consequence mapping = PREREG_BAND_PROBES sealed v2 の D>A>A′>B[+C-item]>R 閉包形を再利用、採択後 81 再 grid (read-side = **60-cell byte-identity gate**: 非 φ10 54 cell + φ10 内不変更 cell は `w0e_81rerun_snapdown_0537` と bit 一致期待)。
- **撤退 mapping (dry 時、pre-data 固定)**:
  - **W1 (識別不成立)**: 全 H が判別列で混在 / 単独支持なし → **RETREAT**: 機構 gap 報告 + class を accepted residual として park (Rs (b) fallback = 0.716 受容が既に存在、追い金しない)。
  - **W2 (機構同定 but fix が非座標)**: 新動作/step 追加が必要と判明 → **STOP + Rs escalate** (step-table-first、独自 method-swap 不可)。
  - **W3 (budget 超過)**: Stage-A >5 run 相当 or O4 後も未識別 → 部分結果報告 + Rs 判断。
- **D (C1 regression、全 stage 最優先)**: 新 run いずれかで z_c1_final ≥840 ∨ flank10 ≥840 → **即 STOP + Rs escalate**。
- validity: finite ∧ qvel_ok、violation cell = INVALID + loud。C-0 sha ≠ 5f1c3f92 → 新 run 全 INVALID。

## Predicate 完全性 (§運用29) + scope (§運用30)

- Stage-A の主張 leg = **機構同定のみ** (SR 主張なし)。cover しない leg = fix 有効性 (Stage-B) / 面の回復 (81 再 grid のみが主張可) / 床壁 bar (診断列)。
- informal (規律外 note): 21 cell 全快の算術上限 = 79/81 = 0.975。公式値は将来 re-grid two-key のみ。

## 封緘・交換手順

1. %12 countersign (本 doc 追記) → 凍結 commit (%12、%9 は 0-commit)。
2. leg-1 は %9 実行 (zero-GPU 計算、封緘) / leg-2 + 動画 render は %11。O4 発動判断は leg-1 開封 joint read 後 (両鍵)。
3. SEALED 読み: %9 = O1/O2 計算 + v2.1 診断 / %12 = 独立 recount + O3 照合 — 交換後 2×2 表を機械適用 → gate verdict → Rs 報告。

## COUNTERSIGN (%12 RS-TECH-LEAD、2026-07-06 08:5x JST)

- **独立照合済**: 21-cell class 定義 / R_MISS 4 / dx≤−15 HIGH-PASS 境界 / 動画 3 cell の verdict・crossZ — 全て私鍵 `recount_w0e_81rerun_snapdown_0537.json` と一致。60-cell byte-id 算術検算 = 54 非φ10 + 6 φ10-PASS (dx≤−15、2×3) ✓。P-2′/P-3′/P-6′ as-executed 同一の起点記述 = band probe joint read と一致。
- **pin-1**: leg-1 の O1/O2 計算 script は実行時 sha を結果に記載し、交換時に凍結する (parser v2.1 と同格の鍵扱い)。
- **pin-2**: Stage-B の 60-cell byte-id 期待は fix の gating 設計に依存する provisional — 正確な bit-一致集合は Stage-B addendum で再 pin (fix が φ10 全域 gate なら 54-cell に縮む)。
- 上記 2 pin 込みで **COUNTERSIGN = 承認、封緘発効**。leg-1 (%9 zero-GPU) + 動画 leg (%11、本 PREREG の 3 cell が authoritative) 開始可。

# GPU1 資格試験 probe — 判定規則 pre-registration (pre-data、2026-07-05 14:0x)

**固定時点:** probe 3 cell 実行中・結果未着 (14:06 発射、~14:15-18 完了見込)。本規則は結果閲覧前に凍結。
**two-key:** bar 提案 = %9 (14:09)、採用 + 帰結 mapping 追加 = %12 (14:1x)。参照 tuple は %9 が probe 結果閲覧前に元 grid JSON から独立固定済 (x0_y0 = SUCCESS_R_GRIP_L_CAGE_AT_88 / True / 830.6 / −0.392、x0_y-20 = 同 verdict / False / 844.2 / −0.19、x-20_y5 = R_MISS_AT_88 / False / 834.7 / 12.655)。

## 判定 3 区分 (cell 単位)

1. **EXACT**: discrete (verdict, c2_seated_honest) 同一 ∧ |Δ cable_z_at_c2| ≤ 0.05mm ∧ |Δ c2_wall_dist| ≤ 0.05mm (%9 較正 bar と同値)。
2. **OUTCOME-STABLE-DRIFT**: discrete 同一 ∧ 0.05mm < max(|Δz|, |Δwall|) < 3mm — silent bin 禁止の loud 第 3 区分。異機種 (Blackwell vs Ampere) で最も出やすい帯。
3. **MISMATCH**: discrete 不一致 or |Δ| ≥ 3mm。

## 帰結 mapping (pre-pin、事後裁量排除)

- **3/3 EXACT** → cuda:1 = bit 級再現。決定論錨定 workload (grid wave 分割・cell 再走・admissibility 対象 render) に**資格あり** — 次 grid から両 GPU 分割 ~2× を標準化提案。
- **≥1 OUTCOME-STABLE-DRIFT (MISMATCH 0)** → cuda:1 = 「outcome 安定・軌道 drift あり = marginal cell で flip し得る」。**新規 grid を GPU1 で丸ごと** (device 内一貫) は可 / **GPU0 記録との cell 単位照合・再走・admissibility 用途は不可**。統計解釈 workload + 独立作業は可。
- **≥1 MISMATCH** → device-fragility が cuda:1 に拡張 (memory `project-canonical-route-device-fragile` 系)。GPU1 = **独立 workload 専用** (EGL render offload / smoke / VLM / 別 track)。

## Amendment A1-A2 (14:11 追記、%9 提案 14:10 + %12 採用 — いずれも解釈制限側 = anti-over-claim)

**追記時点の状態 (records-match-fact):** x-20_y5 = DONE exit=0 (JSON on disk・**両 leg とも tuple 未読**、probe.log の DONE 行のみ確認) / x0_y0・x0_y-20 = 実行中。判定規則・帰結 mapping への変更なし — 以下は解釈の制限のみ。

- **A1 (DRIFT 枝の比較規約 cross-ref):** DRIFT 下では device 差 = **deterministic bias (noise でない)** → cross-device の集計比較 (GPU0 grid SR vs GPU1 grid SR、A-vs-B の腕別 device 等) は **device-confound caveat 必須、比較主張は same-device pair 内に限る**。packet §3 の共通 comparator pre-register (same env sha + cuda:0) は本規約と整合 (無傷) — 将来の混走比較はこの cross-ref で機械的に reject。
- **A2 (EXACT 枝の wave 分割条件):** 分割 wave 運用は **per-wave device manifest (どの cell がどの GPU か、paper 記帳のみ・code 変更なし) を必須列**とする — anomaly の device 遡及を可能に。EXACT でも n=3 spot ゆえ全 cell 無差異は未保証 (over-claim guard の運用面)。

## 手続き

- 照合 = %12 + %9 両 leg (raw JSON 直読、%9 は事前固定 tuple と突合)。
- 結果は本 file に追記 + banked fact 文言は上 mapping から機械的に採択。3 cell で決められるのは上記まで — grid 全域の資格を over-claim しない (n=3 の class 代表 spot、conservatism: EXACT でも「3/3 spot での bit 級」と記す)。

## 結果 (%12 leg 14:12-13 実施・記録 14:2x / %9 countersign 済 14:33 = two-key 確定)

| cell | GRID (cuda:0) | GPU1 probe | Δz / Δwall | 区分 (%12 leg) |
|---|---|---|---|---|
| x0_y0 | SUCCESS_R_GRIP_L_CAGE_AT_88 / True / 830.6 / −0.392 | 同 verdict / **False** / 843.3 / −0.331 | 12.70 / 0.061 | **MISMATCH** (strict→miss 反転) |
| x0_y-20 | SUCCESS_R_GRIP_L_CAGE_AT_88 / False / 844.2 / −0.19 | 同 verdict / **True** / 829.3 / −0.741 | 14.90 / 0.551 | **MISMATCH** (miss→strict 逆反転) |
| x-20_y5 | **R_MISS_AT_88** / False / 834.7 / 12.655 | **SUCCESS_DUAL_LOADED_AT_88** / False / 834.9 / 13.642 | 0.20 / 0.987 | **MISMATCH** (verdict 反転 — whiff→掴んだ) |

- **%12 leg 判定: 3/3 MISMATCH → mapping 第 3 枝 = GPU1 (cuda:1、PRO 4000 Blackwell 異機種) = 独立 workload 専用** (device-fragility 拡張)。
- **%9 countersign (leg 実施 14:12 tool-log・交換 14:23・本行 14:33、%9 正式文 verbatim):** 独立 leg = 事前固定 tuple vs probe JSON 直読。**3/3 MISMATCH** (Δz 12.700/14.900/0.200、Δwall 0.061/0.551/0.987、discrete 不一致 = honest flip×2 + verdict 変化×1)。%12 leg と全数値一致 = **two-key 成立、mapping 第 3 枝の機械適用に同意**。premise 清浄 (3 cell とも env diff = CUDA_VISIBLE_DEVICES のみ) %9 検証済。**verdict 確定 = GPU1 独立 workload 専用。**
- %9 追加 leg: (i) **premise 清浄** — 3 cell とも env_gates diff = CUDA_VISIBLE_DEVICES 0→1 のみ・offset 正値 → MISMATCH は真に device 起因 (誤設定 probe 説棄却) (ii) **軌道乖離定量** — final 40-node 最大乖離: flip 2 cell = 27.1/30.2mm、x-20_y5 = **1.9mm** (cable ほぼ同位置で verdict flip、r_grip 0.0→32.8N) = **flip は把持 microevent 発生 = knife-edge 直接実証** (iii) x-20_y5 の GPU1 成功 = **delivery-level winnability witness に scope** (honest=False のまま — strict-level は unwitnessed)。
- 対照実証 (同時刻): %11 の同 device (cuda:0) --record-video 再走 = **r-v1 7/7 tuple 完全一致** → 「決定論 = device 条件付き」が両側から確定 (同 device 再現 ✓ / 異 device 反転 ✗)。
- 副産物: (i) grid SR map / 決定論 6/6 は **cuda:0 条件付き**と annex 明記 (両方向 flip = marginal 帯 knife-edge の独立実証、J-8 連続体像と整合) (ii) FAIL cell x-20_y5 が別 realization で成功 = **当該 offset は幾何的 unwinnable でない存在証明** → JOINTREAD J2 draw EMPTY の補強 (保守方向のみ)。

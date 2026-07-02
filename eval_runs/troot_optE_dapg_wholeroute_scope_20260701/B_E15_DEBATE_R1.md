# E15 (fork-(iv) absolute-target) 5体 pre-debate R1 — adjudication (2026-07-02 18:0x)

**CC1 (lead %12) REBUT_OR_ACCEPT。** 対象 = E15 v1 (DRAFT)。34 challenges (CC2:7 / CC3:9 / CC4:9 / CC5:9) + CC6 NHA (CHANGE_JUSTIFIED_WITH_REDUCTIONS, R1-R6)。**全 ACCEPT/PARTIAL (REBUT 0)** — fork の方向 (絶対 target 化 = 積分病理の除去) は 4 体が明示的に支持/実装可能と検証したが、**v1 の数値根拠・事前予測・guard 詳細は実測で反証** → E15 v2 で全面置換。

## 判定表 (theme 集約)

| # | theme (集約元 / 体数) | worst SEV | 判定 | v2 反映 |
|---|---|---|---|---|
| 1 | **global affine は z 軸で無価値** — 実測 range Rz/Lz 492.9mm は HOVER 降下 sweep (385.7mm) 支配、seat phase の z range は 22-32mm → global だと z decode 5.4mm ≈ workspace 級 (CC2-CH1 **CRIT** + CC3-CH1 + CC5-C5-3 + 係数×2 誤り CC4-CH4/CC6-R1 = **5/5 体**) | **CRIT** | **ACCEPT** | **per-phase (13) × per-axis affine** に変更。実測 range 表を記載。式 pin: decode_err = RMSE×(hi−lo)/2 (v1 workspace 11mm は ×2 誤→5.5mm)。seat phase box ~30mm → ~0.3mm 級 |
| 2 | RMSE 1.8e-2 の移転は 3 重に不正 (pooled が per-axis 5.7× 差を隠す / 再学習で非不変 [equal-R² なら z 13.5mm] / interleaved val は楽観) (CC2-CH2 + CC5-C5-2 + CC4-CH4) | HIGH | **ACCEPT** | 「unknown until measured」と明記、**OG offline gate で実測** |
| 3 | **offline gate 義務化** — OG-a decode-vs-wp per-axis×per-phase mm-RMSE + boundary jump 表 / **OG-b ee-Jacobian β probe (β≈1 = 積分が学習で復活 = offline 反証 → STOP)** / OG-c b0a obs_series で off-distribution 再評価 (CC5-C5-2 HIGH + CC6-R1 + CC2-CH2 = 3体) | HIGH | **ACCEPT** | 学習後・sim 前の必須 gate。B1′ が sim でしか得ない情報 = closed-loop decode×J 相互作用のみ、と honest 化 |
| 4 | actor は無界 Linear — a∈[−1,1] は label 性質。v1 guard-2 の「fork-(i) 暗黙 cap」前提は偽 (CC2-CH3) | HIGH | **ACCEPT** | **runner clamp a→[−1,1] pre-decode** + per-axis clamp 数 = 真の off-manifold 診断。guard-2 根拠文を書換 |
| 5 | guard-2 詳細 — norm 空間 per-arm 3D 明示 / pre-IK 挿入 / ee_err は APPLIED target 比 / 「無発火」は decode+tracking 項無視で非 robust → expected-fire set を OG-a から事前登録、fires≫予測 = signal (CC2-CH4 + CC3-CH8 + CC5-C5-5 = 3体) | HIGH | **ACCEPT** | 全詳細 v2 明記。fires>0 の SUCCESS = loud caveat (CC4-CH7) |
| 6 | **B0a 分岐 = precomputed cumsum LOOKUP** — naive 再利用は policy を捨て demo 再生 = 偽 SUCCESS channel (CC3-CH2) | HIGH | **ACCEPT** | 新 ctx `policy_absolute` 独立分岐 + 相互排他 assert +「同一なのは IK/sub-interp/physics のみ」と表現修正 |
| 7 | 事前予測が反証不能 (「MARGINAL/uncertain」は何が出ても主張可) + B0a actuals と不整合 (reach 3.6mm/bar20 = PASS 予測すべき; seat floor 1.68mm > bar 0.5 = **NO-FIRE 予測**すべき) (CC5-C5-1 HIGH) | HIGH | **ACCEPT** | **B0a-anchored 数値予測表 P1-P7** + **adopt/revert 事前決定表** (C5-8: P1∧P2∧P3→採用 / P1 or P2 FAIL→反証→BLOCKED_FOR_USER / P4 fire・P5 success→anomaly 調査先行) |
| 8 | 学習 unseeded 実証 (init/randperm split/shuffle) — MARGINAL 軸の B1 vs B1′ 差は train-noise 混入 (CC4-CH2 HIGH) | HIGH | **ACCEPT** | wrapper で seed pin + stdout/sidecar/verdict に記録 |
| 9 | L2 自己分類が同 spec §7 の L3 論理と矛盾 + 層5 は 3-file 直交トリガーで発火 (CC3-CH9 + CC4-CH1 + CC5-C5-7 = 3体) | HIGH | **ACCEPT** | **E15 は §7 既存 L3 chain に乗る** (L2 label 撤回)。実 diff に rule-check stage1、実装後 層2+層5 |
| 10 | N=5 は実効 n=1 (B1 の 5 本 bit-identical を sha 実証) (CC2-CH6 + CC5-C5-4 = 2体) | MED | **ACCEPT (統合)** | **N=5 = nominal×2 (byte-identity assert) + EE-seed jitter ±1mm ×3 (seed 記録)** — §8-1 の形を保ち 4/5 を情報化、rate は分離報告 |
| 11 | repr↔mode/policy の出自 binding 不在 (silent cross-wiring = schema-valid garbage) + 2 version 軸 (phase×repr) 未宣言 (CC3-CH4 + CC4-CH3 = 2体) | MED-HIGH | **ACCEPT** | meta.action_repr 両 variant / train sidecar {ckpt sha, dataset sha, repr, seed} / runner assert / verdict に両軸記録 |
| 12 | file 計画 — abs pair (obs 同梱 + 専用 meta) / no-clobber (convert() は schedule/meta を無条件上書き) (CC3-CH3) | MED-HIGH | **ACCEPT** | bc_dataset_abs.npz + bc_dataset_abs_meta.json、delta trio は assert-only |
| 13 | 証跡耐久 — verdict に runner/converter/dataset sha 無し + producer が 0-commit のまま 3 度目の in-place 編集 (CC4-CH5) | MED | **ACCEPT (即時適用済)** | **pre-E15 snapshot 取得済** `e15_producer_snapshots_preE15/` (4 files + SHA256SUMS、18:03)。以後 verdict に 3 sha 追加 |
| 14 | guard-1: 本 demo で dead code (min range 82.3mm) + median 中心は歪み軸で |a|>2 + 例文が事実逆 (L の方が動く) (CC3-CH5 + CC2-CH5 + CC5-C5-9 + CC6-R4 = **4体**) | MED | **ACCEPT** | **midpoint (min+max)/2 中心** + width max(30mm, 1.2×range)、inertness を meta に log、例文修正 |
| 15 | self_check の recon 行は delta 専用 (abs で meters 級 FAIL) (CC3-CH6) | MED | **ACCEPT** | abs branch: decode(labels)==wp ≤0.01mm + max|a|≤0.95 + guard-1 echo |
| 16 | E12 seed は abs mode でも必須 + t=0 canary (CC3-CH7) | LOW | **ACCEPT** | 明記 + ‖decode(a0)−ee‖<30mm canary |
| 17 | EGL pin 不在 — B1 X11 abort が B1′ で再発 (CC5-C5-6) | MED | **ACCEPT** | MUJOCO_GL=egl + DISPLAY unset を binding + backend を verdict に記録 |
| 18 | 集計行未更新 (~17h→~19-20h) / B0_REPORT:161 parking 行 supersession / DESIGN-GATE skip 未記録 / DAPG-on-abs の条件性 (CC4-CH6/CH8/CH9 + CC6-R5/R6) | MED-LOW | **ACCEPT** | 各 1 行 v2 反映 |
| 19 | forced-choice 未記載 — naive corrective は n=1 で fork-(i) と完全同一 (labels & apply rule、CC6 導出検証) → absolute が唯一の非自明メンバー + KNOWN_ALTERNATIVES 表 (CC6-R2/R3) | (NHA) | **ACCEPT** | 必然選択の導出 + 代替 4 案の棄却理由を v2 記載 |

## NO_ACTION_EVALUATION + DECIDE

- NHA = CHANGE_JUSTIFIED_WITH_REDUCTIONS。fork せず (i) のまま B2/DAPG に進む案は「積分病理を持つ表現に demo 項を浪費」で dominated、Rs A 決定とも矛盾 → No Action 棄却。
- **DECIDE = PASS-with-revisions**: 方向支持 + 数値根拠/予測/guard の全面書換 → **E15 v2**。実装 charter は v2 反映後 (%11)。
- 検証メタ: CC2/CC3/CC5 は実 npz・実 code・実 verdict json で計算 (範囲表・sha・行 map 全て on-disk)。%12 は CRIT の 1 次数値 (Rz 492.9 / seat phase 22-32mm / 5 本 sha 同一) を CC 間 cross-consistency で確認 (3 体が独立に同値)。

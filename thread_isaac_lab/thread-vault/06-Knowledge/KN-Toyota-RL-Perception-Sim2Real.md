---
title: Toyota RL — Perception Observation-Error / Latency Sim2Real (external reference)
type: knowledge
category: external-tech-reference
created: '2026-06-24T19:05:33+09:00'
last_updated: '2026-06-24T19:05:33+09:00'
status: reference (fact-checked 2026-06-24); forward candidate for THREAD perception sim2real; adoption = Rs design decision (NOT yet adopted)
tags:
  - knowledge
  - external-reference
  - sim-to-real
  - perception
  - domain-randomization
  - vision
  - observation-latency
---

# Toyota RL — Perception Observation-Error / Latency Sim2Real (external reference)

> **本 file の位置付け**: 外部産業事例 (Toyota 未来創生センター, RL motion-control, 2026-03-31 公開) の **1 技術 = 知覚の観測誤差+遅延モデリング (sim2real)** を verified reference として記録する。THREAD への取り込み判定 (2026-06-24, Rs 依頼) で「取り込む価値あり」と判定された **technique (a)** の記録。
> **これは設計決定ではなく forward reference。** 採用可否は Rs 専権 (07-Design は CC read-only)。本 note は CC が 06-Knowledge に記録可な external-tech 知識 (`02-Workflow/Vault Write Permissions.md:26`、`KN-NVIDIA-Demo-Strategy.md` と同類)。
> **Anti-dup**: THREAD は既に image-level Vision-DR (D1-D8) を持つ (`LL-Vision-DR-Design.md`)。本 note は **重複ではなく**、その taxonomy に**無い** delta (観測 latency + 実測-then-match) を external 事例で裏付けるもの。§3 参照。

---

## 1. 記録する技術 (Toyota technique (a)) — verified

**Toyota の知覚 sim2real 手法 (バスケットボール・ドリブル文脈):**
- sim ではボール位置・速度を正確に取得できるが、実機は**頭部カメラ + 認識アルゴリズム**で推定 → **認識誤差・遅延**で成功率が低下。
- 解決策: **実環境のカメラ認識の誤差・遅延をモーションキャプチャ (ground truth) で評価し、その特性をシミュレーション側の観測に組み込む** → 実機で成功。
- 逐語 (JP primary): 「実環境のカメラ認識の誤差や遅延をモーションキャプチャで評価し、その特性をシミュレーション側にも組み込む」

**手法の核 (2 要素):**
1. **観測誤差 (recognition error)** — 知覚パイプライン**出力 (推定 pose)** の誤差。raw pixel noise ではなく estimator-output レベル。
2. **観測遅延 (latency)** — 推定の時間遅れ。
→ 両方を**実機で実測 (mocap)** し、その分布を**sim observation に match** させる (= Real2Sim を観測側に適用)。

---

## 2. Evidence basis (honest)

- **Fact-checked 2026-06-24** (deep-research workflow `w1pzihr32` + 私 (%2 OPS-SUP) の直接再検証)。
- **一次ソース (公式)**: `global.toyota/jp/mobility/frontier-research/44105203.html` (JP) / `global.toyota/en/mobility/frontier-research/44105235.html` (EN)。公開 2026-03-31、研究者 Takahiro Ito / Mitsuki Morita、R-Frontier Div. Humanoid Robot Research Group (未来創生センター)。**両一次は私の WebFetch に HTTP 403** を返す。
- **B4 (本技術) は同日2次2本が逐語確認**: `robotstart.info/article/2026/03/31/381733.html` (2026-03-31) + `response.jp/article/2026/04/01/409480.html` (2026-04-01) — 両者 SUPPORTS、逐語一致。
- ⚠ **workflow の生サマリ「25主張すべて refute / inconclusive」は誤り (rate-limit アーティファクト)**: Verify フェーズの全投票が API rate-limit で失敗 → fail-closed kill。中身を否定されたのではない。私の直接 fetch で B4 は CONFIRMED。
- **未開示 (Toyota が明記せず)**: RL アルゴリズム名 (PPO/SAC 等) / シミュレータ名 (Isaac Sim/MuJoCo 等) → **借用できる impl 詳細は無い** (手法概念のみ)。

---

## 3. THREAD マッピング — 既存カバー vs 追加価値 (delta)

**THREAD analog**: Toyota「ボール位置推定」↔ THREAD「ケーブル状態/pose 推定」。

### 3.1 THREAD が既に持つ (= 重複、取り込み不要)
THREAD の **Vision-DR 8-dim taxonomy** (`LL-Vision-DR-Design.md` / `LL-Vision-DR-Impl-8DimMap.md`) は **image/appearance レベル**を網羅:
- D1 lighting / D2 texture / D3 cable-color / D4 camera-intrinsic (FOV/principal/distortion) / D5 sensor-noise (depth Gaussian+dropout, color Gaussian+chromatic) / D6 background / (D7 motion-blur, D8 self-occlusion = Tier 2 OUT-OF-SCOPE)
- これらは画像摂動を通じて認識誤差を**間接的に**誘発する。

### 3.2 GENUINELY ADDITIVE (= taxonomy に無い、取り込む価値)
| # | 追加 delta | THREAD 現状 |
|---|-----------|------------|
| (i) | **観測 LATENCY (時間遅延)** | **D1-D8 に時間次元なし** (全て空間/外観)。観測遅延モデリングは THREAD DR に**完全に不在**。 |
| (ii) | **実測-then-match (characterize→inject)** | THREAD DR は engineered/literature-default range (D5 σ=3mm 等)。Toyota は**実測分布に match**。THREAD の実測は Tier-2/R7 real-hardware = OUT-OF-SCOPE (`LL-Vision-DR-Design.md` §1.4/§2.3)。 |

### 3.3 ⭐ THREAD は既にこの gap を self-identify 済 (Toyota = 産業 precedent)
- `07-Design/PoseEstimation-Design-v1.md:55`:「**Perception noise の学習上の欠如:** training distribution に perception noise を含めておらず、estimator 付きの実機分布への zero-shot transfer が難しい。**Real2Sim2Real … posterior dist DR で対応可だが、本 project では sim-side noise injection ゲートが開いていない。**」
- DR-distribution-mismatch risk は v3.2 R-5 に継続 (`LL-Vision-DR-Design.md` §9.4 経)。
→ **Toyota (a) は、THREAD が自ら「解だが未実装」と flag した Real2Sim2Real/posterior-dist-DR の verified 産業実装事例。**

---

## 4. THREAD-condition caveats (一般解を THREAD 条件で検証、prohibited.md)

- ⚠ **対象物の差**: Toyota は**剛体ボール**を推定。THREAD は**変形 segmented cable** (高次元 state、occlusion-prone)。誤差/遅延の**特性化 methodology は転用可**だが、cable の推定誤差**構造は THREAD 固有** (Toyota から借りられない)。
- ⚠ **ハードウェア依存**: 「実機の誤差/遅延を mocap で実測」step は**実機 + mocap リグが前提**。THREAD は現状 sim-only → 実測は Tier-2/R7/L1.F.1 future。それまでは**assumed (engineered) 誤差/遅延モデル**で近似するしかなく、これは real transfer に対し **NON-CONSERVATIVE** (実測検証なしでは over/under-claim risk)。
- **採用 = Rs 設計判断** (07-Design は Rs 専権、CC read-only)。本 note は reference であり実装でも設計変更でもない。

---

## 5. Candidate fold-in (forward、採用時の方向性 — アクションではない)

採用が Rs 承認された場合の方向 (実装は別 task、NEST §3.1 起動承認 gate 経):
1. DR taxonomy に **観測 LATENCY 次元** (例: "D9 obs-latency" / temporal-obs-delay model) を追加 — perception sim2real / real-hardware 段で。
2. 実機入手後、cable-pose estimator に対し Toyota の**実測-then-match**を実行 → `PoseEstimation-Design-v1:55` が flag した「sim-side noise injection ゲート」を開く。
3. Routing: Rs + %9 (RS-TECH-LEAD / 設計オーナー) が future T-Vision-DR Tier-2 / L1.F.1 task として scope。%2 (OPS-SUP) が PV。

---

## 6. Cross-references

### 6.1 Fact-check sources (2026-06-24)
- 一次 (公式、403): `global.toyota/jp/.../44105203.html` / `global.toyota/en/.../44105235.html`
- 2次 (逐語確認): `robotstart.info/article/2026/03/31/381733.html` / `response.jp/article/2026/04/01/409480.html`
- 広義 Toyota fact-check の他 verified 技術 (本 note scope 外、pointer のみ): (b) Real2Sim アクチュエータ同定 (real-fidelity 軸、hardware-gated) / (c) 既存 DR を grasp IC へ拡張 (IC-robustness)。歩行報酬 = locomotion 固有で N/A。変形 cable 物理は**どの Toyota 技術もカバーせず** = THREAD 固有の宿題。

### 6.2 THREAD 既存 (重複回避の接続先)
- `06-Knowledge/LL-Vision-DR-Design.md` (8-dim D1-D8、Rs approve 2026-05-03) — image-level DR canonical
- `06-Knowledge/LL-Vision-DR-Impl-8DimMap.md` / `LL-Vision-DR-Tier1-D6-Design.md`
- `07-Design/PoseEstimation-Design-v1.md:55` (perception-noise gap self-id) / `PoseEstimation-Design-v3.2.md` §10 R-5 (DR distribution mismatch、PARKED head)
- `06-Knowledge/LL-Vision-Pose-Design.md` / T-FC-Perception node (vision pose, PENDING)
- `04-Specs/RS71-System-Spec-SSOT.md` §0 #4 (real-fidelity = pending production 軸)

### 6.3 Provenance
- 取り込み判定の親 context: Toyota RL fact-check (option D) → THREAD 取り込み判定 (option a) → 本 note 記録 (Rs 依頼「a vaultのナレッジとして記録」), 2026-06-24, %2 OPS-SUP session.
- memory: `reference-mj-geomdistance-penetration-crosspv-2026-06-21` (本 session の held-rate cross-PV、real-fidelity 軸の隣接 pending)。

---

**Status**: 🔵 REFERENCE (fact-checked, not adopted). Forward candidate for THREAD perception sim2real; adoption = Rs design decision. THREAD は image-level DR (D1-D8) を保有、本 note の追加価値 = 観測 latency 次元 + 実測-then-match (PoseEstimation-Design-v1:55 が「未実装の解」と flag 済)。
**Recorded by**: %2 OPS-SUP, 2026-06-24 19:05 JST.

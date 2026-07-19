# WMSO D1.1-A 成果物 manifest（2026-07-19 20:40 JST 全面書換実測 — **Rs review v7 ⛔HOLD の fold 完了・pS 照合待ち**）

作成 = w2:pQ (RS-TECH-LEAD2)、node `T-WMSO`。全 sha256 = full 64-hex・**committed blob から実算出**（bank commit 付き — dirty tree 由来の pin なし）。本 manifest は RV7-R-3（旧 manifest = v2.9 世代 pin の残置）への全面書換。

## 現在地（1 行）
**pN 工程 13 = ⛔HOLD B1-B4（21:08、custody/hash legs = PASS）→ 全項 fold = DESIGN v2.11 + EP v1.9 + JSON v1.9（bank `37ddb72284`）** → 残 gate = **pS 再照合（工程 12 再入 — 依頼中）→ pN exact-pin 再検証 → Rs freeze 判定**。⚠**B4 = 批准済み §3 表の method registry 化（charter 整合の復元）— register ⑩・Rs confirm 対象**。impl / training / authority = CLOSED 不変。

## 最終 pin（現行候補 — bank `37ddb72284`、committed blob から実算出）
| artifact | 版 | sha256 |
|---|---|---|
| DESIGN | **v2.11** | `8d1f356024f7e6f4a14f7d2f36d94a9e6958905d65920078b30831e76642759f` |
| EvidencePolicy markdown | **v1.9** | `c474acea7c58acc22050c2ad9944fd45a18f5c76967964b42d11922e28fa27e7` |
| JSON fixture `WMSO_EvidencePolicy_v1.9.json` | **v1.9**（policy_semver 1.9.0） | `e63176af9bc3a246b1c32db369ec59f8d09a4c96c381bb03a3a6024bd9811c6e` |
| `evidence_policy_definition_hash` | H_WCJ(policy_definition)・17 member | `e7ca43093084c167a209b008533a66d26a1fd3223d2a3c11274d28306c3ff803`（committed blob から埋込 command で再計算一致） |
| RV7 transcript | as-received（byte N/A・Rs fidelity PENDING） | `91923be57c206eaafa0b6cf938bbabc431cbefe223928f3dd1c3ecf5ea509732`（bank `a87525cc15`） |

⚠ **退役 pin（semantic 変更系譜 — 最終 exact pin に使用不可）**: v1.7 系 `066eed1049f4…`/`ed10c77a…`（RV7 指示）→ v1.8 系 def hash `bdc5082008…`・JSON `00032f9091…`・DESIGN v2.10 `86a8822197…`・EP v1.8 `9713cafbd2…`（工程 13 B1-B4 の semantic 変更につき）。

## 版系譜（design / EP — 全 sha は design v2.11 header の version 履歴が正）
- DESIGN: v2.9 `e64c192b62…`@`8caa19a7a4` → v2.9.1 `0da7932103…`@`ea30e7fdc3` → v2.9.2 `e83a29061400…`@`ba69702cb9`（pN ✅PASS-CLOSE 17:43 → **Rs RV7 ⛔HOLD**）→ v2.10 `86a8822197…`@`a87525cc15`（RV7 fold; pS 工程 12 PASS → **pN 工程 13 ⛔HOLD B1-B4**）→ **v2.11 `8d1f356024…`@`37ddb72284`（B1-B4 fold — 現行候補）**
- EvidencePolicy: v1.7 `586fec2a77…`@`8caa19a7a4` → v1.7.1 `27701698ed…`@`ba69702cb9`（pN R1 CLOSE）→ v1.8 `9713cafbd2…`@`a87525cc15`（RV7 fold）→ **v1.9 `c474acea7c…`@`37ddb72284`（B1 classifier/overlay・B2 機械拒否・B3 構造化 projection + golden 7・B4 DEMO_PLUS_RL）**

## RV7 custody 事実確認（転記者注の要旨）
RV7 の review 環境 companion（EP `586fec2a…` = v1.7 / JSON `3fb7a452…` / manifest `a5d0aa0c…`）は**旧 zip 世代** — 20:10 JST 実測で現 `~/Downloads/`・repo とも v1.7.1/最終 JSON に更新済みだった（pQ の 19:49 design 単体納品時に companion pointer を添えなかった納品 gap）。**custody FAIL 判定自体は妥当**。RV7-P0-1 の semantic 部分（EP 重複行）は v1.7.1 で既修正（pN R1-R3 CLOSE が独立確認）、custody 部分は本 bundle で解消。**P0-2..P0-7 / R-1..R-4 は最終版 artifact 上にも実在 — pQ on-disk 検証の上、全て v2.10/v1.8 で fold**（fold-map = design §11 RV7 節）。

## 本 bundle（`~/Downloads/` — 本 manifest と同期）
| file | 内容 | sha256 |
|---|---|---|
| `WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md` | **DESIGN v2.11（現行候補）** | `8d1f356024…`（上表） |
| `WMSO_D11A_DESIGN_v2.9.2_SUPERSEDED_20260719.md` | RV7 の review 対象だった v2.9.2 の保全 copy | `e83a29061400b42c18a6607c96295e0ede2984cda8b9b047f338512ccb0b7f96` |
| `WMSO_D11A_DESIGN_v2.10_SUPERSEDED_20260719.md` | 工程 13 の対象だった v2.10 の保全 copy（v2.10→v2.11 diff 監査用） | `86a882219780dc43ad10dd38988c9933454a6892fb2f2721e83d843841e749c3` |
| `WMSO_D11A_EVIDENCE_POLICY_V1_RSTECHLEAD2_20260719.md` | **EvidencePolicy v1.9** | `c474acea7c…`（上表） |
| `WMSO_EvidencePolicy_v1.9.json` | 機械可読 fixture（二層・17 member・**golden vector 7 本掲載**〔CM 3 + HS 4・自己再現検証済〕） | `e63176af9b…`（上表） |
| `WMSO_RS_REVIEW_V7_HOLD_TRANSCRIPT_20260719.md` | RV7 as-received 転記 + custody 事実確認注 | `91923be57c…`（上表） |
| `WMSO_D11A_DESIGN_VERIFY_WMSODESIGN_20260719.md` | pS verify record **§1-§16**（§16 = RV7 工程 12 差分照合 = **✅design-axis PASS**〔20:55・must-fix 0〕） | `383c3e3a0efcc0df00a37ce7bb877cb6e247db9f376689da02ef026ef0a0c562` |
| `WMSO_PN_DESIGN_VERIFY_HOLD_C1C3_TRANSCRIPT_20260719.md` | pN HOLD C1-C3 transcript | `d8b5f83e0af85cd069feec73c011ef3949d1a258ec61348565e0f2149fe6e4c2` |
| `WMSO_PN_DESIGN_VERIFY_R_AND_PASSCLOSE_TRANSCRIPT_20260719.md` | pN R1-R3 HOLD + ✅PASS-CLOSE（v2.9.2 宛）transcript | `2847e2aa9d30a9b57093232425c8fdbef2aa09a87d0291b489f79e471f911139` |
| `WMSO_RS_REVIEW_V6_COPY_20260719.md` | Rs review v6 byte-identical copy | `3f64cbca44269bc8255fd2c0dcf4d96712248de4017d4b1943c0855daef2cead` |
| `WMSO_RS_REVIEW4_FIDELITY_CONFIRM_20260719.md` | review-4 fidelity 確認 record | `f5737799522c7e679753299fe7ece1d9ae51caf6df723ee7f48cf54e1a7c15c8` |

（Rs 発行 review v3/v4/v5 原本 = `~/Downloads/PLAN_STATUS_review_v{3,4,5}_2026-07-19.md` 既在。repo byte-identical copy = `20da075f9566…` / `338bdaf75a99…` / `44792e860e82…`。pN B1-B7 transcript = repo `6d26efde4739…`@`86d127b5c0`。）

## 残 gate（RV7 工程 12-14 の再入 — 順不同にしない）
1. v2.10 round: pS 工程 12 = ✅PASS（record §16 `383c3e3a0efc…`）→ **pN 工程 13 = ⛔HOLD B1-B4**（21:08 — B1 applicability 分岐 semantics / B2 EXACT×非学習 機械拒否欠如 / B3 projection prose placeholder / B4 algorithm 固定 = charter 不整合〔CRITICAL/L0〕+ R1-R2 records。custody/hash legs = PASS）
2. **pS 再照合（v2.10→v2.11 / EP v1.8→v1.9 差分 — 依頼中）**
3. **pN exact-pin 再検証**（pS PASS 後 — 完全 bundle + 最終 SHA）
4. **Rs freeze 判定**（pN PASS 後に上程。⚠register ⑩〔B4 method registry 化〕の confirm を併せて上程）

## 未 push
`a87525cc15` / `1ba0d0a9df` / `dfeb6c1e57` / `37ddb72284`（B1-B4 fold）+ 本 manifest commit。**push は Rs 一言で実行**（`1fb038bc39` までは push 済み・remote 一致確認 19:46）。LEDGER 反映 = p6 row44（RV7 HOLD `0578b9b174` → pS PASS `2fd6045f32` 確認済み; 工程 13 HOLD 反映は dispatch 済み）。

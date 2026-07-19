# WMSO D1.1-A 成果物 manifest（2026-07-19 16:07 JST 更新実測 — pS §12 G-1..G-4 fold = v2.8 + EP v1.6）

作成 = w2:pQ (RS-TECH-LEAD2)、node `T-WMSO`。全 sha256 = full 64-hex、bank commit 付き。

## 現在地（1 行）
**DESIGN v2.7 = Rs review v5 の bounded fix 完了** → 残 = pS delta 照合 → pN 再 verify（最終 sha 宛）→ **D1.1-A freeze 判定**（RV5 §6-5 の Rs 方向どおり）。scope CLOSED / **impl・訓練・authority = CLOSED 不変**（kinematic 全廃 directive の HALT とも整合 — 契約層に kinematic/pin 依存なし、grep 確認済み・design §10）。

## 本 bundle（`~/Downloads/`）

| file | 版 | sha256 | bank |
|---|---|---|---|
| `WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md` | **DESIGN v2.8**（full self-contained; pS §12 G-1..G-4 fold） | `24f5fd3d8e8ec85034bdb53cfb65d47a6636529c2aa366e9212cf1d271515fef` | 本 commit |
| `WMSO_D11A_EVIDENCE_POLICY_V1_RSTECHLEAD2_20260719.md` | **EvidencePolicy v1.6**（G-4: kind 条件付き束縛 — SCRIPTED/WAIT の CLOSED_LOOP 到達可能化） | `fe3f4f1864d0f00afbbf3a33d27c3aa4d361e7de989a530425325d34dab67b54` | 本 commit |
| `WMSO_EvidencePolicy_v1.6.json` | 機械可読 normative fixture（v1.6 同期・改名済） | `e1f8d300dc206ac305da26a5a87d745490ec5c842551a9b5975b2712310530f4` | 本 commit |
| `WMSO_PN_DESIGN_VERIFY_HOLD_B1B7_TRANSCRIPT_20260719.md` | pN HOLD B1-B7 as-received 転記（RV5 C-P0-1; **pN 著者 readback = SEMANTIC FIDELITY CONFIRMED 15:42**〔確認対象 blob = `e65f7a4f…` @ `e0257b5648`〕） | `6d26efde4739cf0811ffcad0a4eb77cb7e79660817398b878d44d8789b3ae50d` | `86d127b5c0` |
| `WMSO_D11A_DESIGN_VERIFY_WMSODESIGN_20260719.md` | pS verify record（§1-**§12** = scope〜v2.7.1 全区間 re-check; **§12 込み re-bank = 本 commit** — G-3） | `98e47cace83ab7b2f64578af38334d05a293344868ef54f9aaa877d9eb1d9a0a` | 本 commit |
| `WMSO_RS_REVIEW4_DESIGN_TRANSCRIPT_20260719.md` | review-4 転記（**SEMANTIC FIDELITY CONFIRMED** — RV4 §1.4/RV5 C-P0-3、byte = N/A） | `8a7915dfa3386889d4efe3cbacb063c0ea20df0f138c8099b84ec64cbab5ad50` | `ac5865b66d` |

（Rs 発行の review v3/v4/v5 原本は `~/Downloads/PLAN_STATUS_review_v{3,4,5}_2026-07-19.md` に既在。repo 側 byte-identical copy = `20da075f9566…` / `338bdaf75a99…` / `44792e860e82…`、bank `130813e934` / `51008ace1f` / `e0257b5648`。）

## 本日の設計連鎖（要約）
scope v3.2.2 CLOSE（3 軸）→ DESIGN v1→v2.7（Rs review-4 / W(RV2) / RV3 / RV4 / RV5 + CC Debate cycle-1〔19 項〕/ cycle-2〔4-lens 全数 discharge 検証〕+ pS 3 solo 回 + 全行照合×2 + FINAL CONFIRM + pN HOLD B1-B7 の全 fold）。supersession register ①-⑦ enumerated-only。fold-map = design §11（RV2/W'/B/RV4/RV5）+ §12（R4）。

## 残 open（2 件）
1. **pS final confirm**（v2.8 = G-1..G-4 fold 宛 — 依頼済み。pS §12 verdict = PASS-WITH-CONDITIONS、G-4 intent = (a) 非学習 evidence path で回答）→ **pN 再 verify**（最終 sha 宛）。
2. **freeze 判定** = pS+pN 後に Rs へ（RV5 §6-5「bounded fix 後 freeze → D1.1-B/C へ」の執行確認）。

## 未 push
`cd5482310d`〜`e0257b5648`（本 node 分）+ peer commits。**push は Rs 一言で実行**。

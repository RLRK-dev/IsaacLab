# WMSO D1.1-A 成果物 manifest（2026-07-19 16:58 JST 更新実測 — Rs review v6 + pN C1-C3 統合 fold = v2.9 + EP v1.7）

作成 = w2:pQ (RS-TECH-LEAD2)、node `T-WMSO`。全 sha256 = full 64-hex、bank commit 付き。

## 現在地（1 行）
**DESIGN v2.7 = Rs review v5 の bounded fix 完了** → 残 = pS delta 照合 → pN 再 verify（最終 sha 宛）→ **D1.1-A freeze 判定**（RV5 §6-5 の Rs 方向どおり）。scope CLOSED / **impl・訓練・authority = CLOSED 不変**（kinematic 全廃 directive の HALT とも整合 — 契約層に kinematic/pin 依存なし、grep 確認済み・design §10）。

## 本 bundle（`~/Downloads/`）

| file | 版 | sha256 | bank |
|---|---|---|---|
| `WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md` | **DESIGN v2.9**（631 行・full self-contained〔C3: 構成型 inline 済〕; RV6+C 統合 fold） | `e64c192b62e754da8050041985dd9028a67bf12c287d55bcbc1579c660b8de46` | `8caa19a7a4` |
| `WMSO_D11A_EVIDENCE_POLICY_V1_RSTECHLEAD2_20260719.md` | **EvidencePolicy v1.7**（claim_target 機構・resolver 分割・evaluator registry） | `586fec2a770207b5726dee557fe9a5c1a437baadc39b75c5558e473d1cdf3efe` | `8caa19a7a4` |
| `WMSO_EvidencePolicy_v1.7.json` | 機械可読 fixture（二層; **definition hash = `066eed1049f4f51a89dd86e9d50614a65adba070b2ff650424ea7cef05dec4ea` 実算出・掲載**） | `3fb7a452a14867ca7e0e0ec3dbf0c7b63f87edc7527e5d095a086b9802aa3b81` | `8caa19a7a4` |
| `WMSO_RS_REVIEW4_FIDELITY_CONFIRM_20260719.md` | review-4 転記の fidelity 確認 record（RV6 §1 形式 — CONFIRMED / byte N/A） | `f5737799522c7e679753299fe7ece1d9ae51caf6df723ee7f48cf54e1a7c15c8` | `8caa19a7a4` |
| `WMSO_RS_REVIEW_V6_COPY_20260719.md` | Rs review v6 の byte-identical copy | `3f64cbca44269bc8255fd2c0dcf4d96712248de4017d4b1943c0855daef2cead` | `8caa19a7a4` |
| `WMSO_PN_DESIGN_VERIFY_HOLD_B1B7_TRANSCRIPT_20260719.md` | pN HOLD B1-B7 as-received 転記（RV5 C-P0-1; **pN 著者 readback = SEMANTIC FIDELITY CONFIRMED 15:42**〔確認対象 blob = `e65f7a4f…` @ `e0257b5648`〕） | `6d26efde4739cf0811ffcad0a4eb77cb7e79660817398b878d44d8789b3ae50d` | `86d127b5c0` |
| `WMSO_D11A_DESIGN_VERIFY_WMSODESIGN_20260719.md` | pS verify record（§1-**§13** = scope〜v2.8 FINAL CONFIRM; §13 込み re-bank） | `24589ae609574670fc2f5f894ace9739d53479ed233c256ce0d8c0a7d3513ceb` | `dbf3c940c3` |
| `WMSO_RS_REVIEW4_DESIGN_TRANSCRIPT_20260719.md` | review-4 転記（**SEMANTIC FIDELITY CONFIRMED** — RV4 §1.4/RV5 C-P0-3、byte = N/A） | `8a7915dfa3386889d4efe3cbacb063c0ea20df0f138c8099b84ec64cbab5ad50` | `ac5865b66d` |

（Rs 発行の review v3/v4/v5 原本は `~/Downloads/PLAN_STATUS_review_v{3,4,5}_2026-07-19.md` に既在。repo 側 byte-identical copy = `20da075f9566…` / `338bdaf75a99…` / `44792e860e82…`、bank `130813e934` / `51008ace1f` / `e0257b5648`。）

## 本日の設計連鎖（要約）
scope v3.2.2 CLOSE（3 軸）→ DESIGN v1→v2.7（Rs review-4 / W(RV2) / RV3 / RV4 / RV5 + CC Debate cycle-1〔19 項〕/ cycle-2〔4-lens 全数 discharge 検証〕+ pS 3 solo 回 + 全行照合×2 + FINAL CONFIRM + pN HOLD B1-B7 の全 fold）。supersession register ①-⑦ enumerated-only。fold-map = design §11（RV2/W'/B/RV4/RV5）+ §12（R4）。

## 残 open（2 件）
1. **pS 照合**（v2.9 = RV6 全項 + pN C1-C3 統合 fold 宛 — 依頼中）→ **pN 再 verify**（最終 sha 宛; pN は C1-C3 を fold 入力として保持・v2.9 pin 待ち 16:39 readback）。
2. **freeze 判定** = pS+pN PASS 後に Rs へ（RV6 §10 逐語「証拠束縛・handoff・migration の閉包だけを直して freeze」）。
（⚠版名: RV6 §10 の目標名「v2.8/EP v1.6」は pS-G fold との交差で消費済み → 実版 = **v2.9/EP v1.7**。）

## 未 push
`cd5482310d`〜`e0257b5648`（本 node 分）+ peer commits。**push は Rs 一言で実行**。

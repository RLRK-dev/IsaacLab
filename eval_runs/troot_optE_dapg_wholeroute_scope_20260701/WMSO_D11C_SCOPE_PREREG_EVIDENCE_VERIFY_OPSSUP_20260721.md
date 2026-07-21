# D1.1-C scope prereg v1 — OPS-SUP evidence 軸検証

**Verifier:** T-ROOT-OPS-SUPERVISOR (`w2:pY`)。**発行:** 2026-07-21 12:5x JST。
**依頼:** pQ（pS が指定した evidence 軸 3 点 + L triage 確認）。**性質:** evidence/custody 検証（設計軸 = pS PASS 済・`c29b8d539db987c3` @ `31ab0b929d`）。⛔本 prereg は design ではない（field 名・型・hash 順序を確定しない）。

## ⭐ VERDICT: **PASS**（evidence 軸）— Rs scope 承認へ

## (1) pin 照合

| 対象 | sha256(16) | commit | |
|---|---|---|---|
| prereg | `d9caaffcf29d9524` | `1860edcc1c` | ✅ 一致 |
| pS 設計軸 PASS | `c29b8d539db987c3` | `31ab0b929d` | ✅ 一致 |
| DEFER-RECON | `94c3fd2195a5981a` | `7effeb774f` | ✅ 実測（pQ 未申告） |
| frozen contracts_v2 | `00192d20ca00b654` | HEAD | ✅ 不変 |
| frozen tensor_binding v13 | `5a1874d3be8b98b8` | HEAD | ✅ 不変 |
| frozen EP md | `c474acea7c58acc2` | HEAD | ✅ 不変 |
| frozen EP JSON | `e63176af9bc3a246` | — | ⚠ **独立再計算せず**（.json path を本 leg で特定できず）。corroborated = OUT#8「凍結 4 file 編集不可」+ 同一 frozen bank・他 3 file 不変 |

## (2) DDR 全 35 項目との対応 — ✅ **35/35 被覆・欠落 0**

- DEFER-RECON が **DDR #1-#35 を全参照**（`grep #N` = 35 unique・`comm` で欠落 0 を実測）。
- disposition は**実判定**（spot-check）: **#26** = 「FOUNDATIONAL 依存 = 1 件のみ・機構/policy 分離で着手可」（substrate_id 機構 IN・選別 policy carry）／**#30** = 「metadata 記録 IN・契約層束縛 = schema delta ⇒ OUT」／**#31** = pX court。いずれも根拠付きの判定で bare mention でない。
- ⭐**FOUNDATIONAL 依存 = 1 件（#26）のみ**という DEFER-RECON の中核主張と整合。

## (3) OUT 宣言が過小でないか — ✅ **過小でない**（機構-policy 線 clean）

**IN 5 項は全て「機構」で schema delta / 未裁定 policy 無しに閉じられる:**

| IN | 機構 | 対応する OUT（policy/enforcement） |
|---|---|---|
| ① artifact manifest 型定義 | 型定義 | — |
| ② `substrate_id` 必須化・区別機構 | 汚染/clean を tag で区別 | **substrate 選別 policy = OUT#1（#26 Rs）** |
| ③ DC-3 grade 別 proof obligation | obligation 供給 | 実 proof 生成 = OUT#6（impl CLOSED） |
| ④ minimal JCS の package 展開 | canonical JSON 適用 | — |
| ⑤ carry U-2/U-5/U-6 | pin/両段記録/topology **metadata** | 阻止実装 OUT#2・demo 再記録 OUT#3・**契約層束縛 OUT#4（#30 schema delta）** |

⇒ **各 IN 機構の policy/enforcement 対応物が正しく OUT に置かれている。** OUT は包括的（substrate policy / closed-loop / demo / 契約層 topology / **合成 schema = pX court OUT#5** / impl/training / slice / 凍結編集 / **F4 腕宣言 = p5 OUT#9**）。⇒ **閉じられない物を IN に入れていない = OUT 過小なし。** frozen line 376（U-3 drive-substrate lineage を C へ降格）とも独立に一致。

## (4) L 判定 = L2 — ✅ 妥当

新規 file（prereg）・**凍結 4 file 非編集**（OUT#8 + sha 不変を実測）・公開 API code 境界に触れない・L3 physics/reward keyword 非該当（artifact/evidence packaging であり reward/env/control でない）。⇒ **L2**（two-key + design 段で CC Debate 発火）は正しい。

## ⚠ 非 blocker の注記（2 件）

1. **EP JSON sha 独立再計算せず**（上記・corroborated）。
2. **IN③「proof obligation 実体供給」** = 本 prereg が design-scope（OUT#6 impl CLOSED）ゆえ「obligation の *設計*」であって「proof の *生成*」ではない、と読む。文面がそう限定していることを design 着手時に 1 語で確認推奨（現状 under-statement ではない）。

## 非主張

- ⛔ 設計の当否（field 名・型・境界の設計判断）= pS 設計軸（PASS 済）。本 leg = evidence/custody。
- ⛔ scope 承認 = Rs 専権（本 PASS は上程 input）。⛔ impl/training/closed-loop authority = CLOSED 継続。

---
**evidence 軸 = 2026-07-21 12:5x JST / T-ROOT-OPS-SUPERVISOR (`w2:pY`)**

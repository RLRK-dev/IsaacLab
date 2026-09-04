# WMSO v0.2 — 陽性対照（positive control）記録: レビュー計器の弁別力 (records-only)

- node: `T-WMSO`; 記録者 = Claude Code web session（authority 無し・凍結物へ非接触）; 実施 = 2026-09-03 16:47–17:05 UTC（注入 → 盲検レビュー）／ 記録 = 2026-09-04 01:5x UTC
- 目的: 08 計画 §1 項 5「欠陥を検出できない計器の verdict は採用しない」の実測。**注入は別 context の agent（planter）が行い、盲検 reviewer（別 context・注入内容を知らない）が読む**。実 package の file は無改変（sha256 = SHA256SUMS の値）。
- 原本: `review_records/PC_KEY_20260903.md`（注入 8 欠陥の answer key・行番号・「正しい finding が言うべきこと」）／ `review_records/PC_B_blind_20260903.md`（runtime 軸 盲検・14 finding）／ `review_records/PC_C_blind_20260903.md`（deployment 軸 盲検・19 finding）。

## 1. 注入欠陥と検出

| id | 注入内容（複製 doc） | 盲検 B（runtime 軸） | 盲検 C（deployment 軸） | 判定 |
|---|---|---|---|---|
| PC-05-A | 旧 epoch 拒否を HealthConfirmation まで遅延（二重所有窓の再開） | PC-B-01 CRITICAL（+ PC-B-02 が SafeHold 側を検出） | C-18 CRITICAL | **検出** |
| PC-05-B | CommitPermit を失効まで再使用可（one-shot 撤去） | PC-B-08 MEDIUM | — | **検出**（severity は計器側が MEDIUM と評価） |
| PC-05-C | CAS 事後条件から `∪ {consume_offer_id}` を削除（replay 証明の崩壊） | 未検出 | — | **未検出** ⇒ 機械検査 O3 を追加（下記） |
| PC-05-D | SHADOW lease が最初の command を actuation へ出力 | PC-B-03 CRITICAL | C-05 HIGH | **検出** |
| PC-06-E | profile に action-space bounds の field を追加（widening 経路） | — | C-01 CRITICAL | **検出** |
| PC-06-F | `action_rate_hz` を ≤ で許容 | PC-B-06 HIGH | C-02 HIGH | **検出** |
| PC-06-G | `requires_safety_layer_health` を SHADOW で False 可 | — | C-04 HIGH | **検出** |
| PC-06-H | EscalationPolicy が SAFE_STOP → HOLD へ緩和可 | PC-B-07 MEDIUM | C-03 HIGH | **検出** |

- 検出率 = **7 / 8**（軸 C: 4/4 の deployment 欠陥を全検出・軸 B: 05 の 4 欠陥中 3 検出）。
- **未検出 1 件（PC-05-C）の処置**: 1 トークン（`∪ {consume_offer_id}`）の欠落は目視の盲点になり得る。`check_review_candidate.py --runtime` に **O3**（CAS 事後条件に当該項が存在すること）を追加し、複製 doc に対して FAIL を返すことを実測した（下記）。以後この種別は機械検査が担う。
- KEY §末尾の「false-positive surface」（注入が残した矛盾）は検出として数えていない。

## 2. 機械検査 O3 の実測（本 record 作成時）

```text
$ python3 check_review_candidate.py <real 05 v0.2.1> --runtime   → FAIL=0
$ python3 check_review_candidate.py review/pc/05_pc.md --runtime  → FAIL contains: O3 §3 CAS postcondition lacks 'consumed_offer_ids ∪ {consume_offer_id}'
```

## 3. 注入外 finding（= v0.2 本体への独立指摘）とその処置

盲検 reviewer は注入欠陥のほかに、複製 doc と実 doc に共通する箇所へ finding を出した。これらは実 doc への独立レビュー結果として扱い、起草者が text / logic / impact で verify した上で **v0.2.1** に fold した（fold 表 = 05 §13・06 §11）。

| finding | severity | 処置 |
|---|---|---|
| PC-B-05 outcome 受領後の producer command が admission を通る | HIGH | fold（`boundary_wait` + `R_POST_OUTCOME_COMMAND`） |
| PC-B-04 safety CAS の CONFLICT 再試行規則なし | HIGH | fold（再試行規則 + INV-24） |
| C-06 initiation 強化の runtime 評価点なし | HIGH | fold（05 §6.2 B4） |
| PC-B-09 CommandGateway 再起動が crash matrix に無い | MEDIUM | fold（`GATEWAY_RESTART`） |
| PC-B-10 fault code 7 件に失敗表の行なし | MEDIUM | fold |
| PC-B-11 / C-12 `ack_validity_s` の出所 | MEDIUM | fold（05/06） |
| C-07 BEFORE_PERMIT health check の結線点 | MEDIUM | fold（05 §3.4） |
| C-08 evidence の循環参照 | MEDIUM | fold（`attested_by` 削除） |
| C-09 最小 required 集合が非規範 | MEDIUM | fold（MIN_* 規範化） |
| C-10 時刻依存 P_* の評価点 | MEDIUM | fold（2 評価点） |
| C-11 空間項の frame | MEDIUM | fold（`frame_ref`） |
| C-13 clearance_roles の読み | MEDIUM | fold（注記） |
| PC-B-12 / B-13 / B-14 / C-14 / C-15 / C-16 / C-17 / C-19 | LOW | fold |

- ⚠ **honest scope**: 上記の verify は起草者（本 session）が行った。08 計画の agent 3 lens 反証検証と本番 3 軸 reviewer（注入なし・v0.2.1 対象）は本 record 作成後に実行し、結果は `11_*` に記録する。本 record は gate PASS を主張しない。

## 4. 境界

- impl / training / closed-loop authority / freeze / two-key = CLOSED・未。frozen 4 file 不変（`verify_exact_baseline_pins.sh` 11/11 PASS）。

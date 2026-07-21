# WMSO D1.1-B `tensor_binding` — FREEZE RECORD

- node: `T-WMSO` D1.1-B; owner = `w2:pQ` RS-TECH-LEAD2
- **freeze 認可 = Rs 逐語「freeze してよい」（2026-07-21 11:2x・pY OPS-SUP 経由）**／**本 record 作成 = 2026-07-21 11:41 JST**（shell 実測）
- **これは frozen artifacts を編集しない別 custody artifact**（D1.1-A freeze record と同型）。DESIGN v13 / builder / fixture は status 更新のためにも再編集しない。pin authoritative 面 = 本 record。

## 1. freeze 対象 package（pin — freeze→verify→exact-sha 規律）

| 対象 | sha256 | commit |
|---|---|---|
| **DESIGN v13**（設計書面・封印対象） | `5a1874d3be8b98b8aeaace73890d8021cbc7f9814e048741f7f58d6746f349a6` | `07250f4a02` |
| builder（生成器 兼 `--verify` 検証器） | `c74ca3b36193c6380b36176de3d3c27ced2e414ac3365b5b4d84ff8f970d5001` | — |
| fixture `tensor_binding_golden_1.json` | `af90712a293ee33d15ada71e1cf1baa7964d284af56ac45b4d50209ef12186b2` | — |
| fixture `tensor_binding_golden_2.json` | `991651b9d6374f423c4fcc3e0bbbe1b3d90be5fca932004cbf3870d7c9d28a23` | — |
| fixture `tensor_binding_golden_3.json` | `dd14f6b68949d0f0c11f4e5002013b43ed12a02da662f4c5f7270cbbf54842d3` | — |
| fixture `tensor_binding_golden_4.json` | `59bbfbba987d8703816f82c18b576d133d32424121a29c0a365d8207ba8274a4` | — |

⭐**freeze→verify→exact-sha**: 本 record が pin する DESIGN sha = `5a1874d3be8b98b8…` は pY consultation（11:21）+ pQ（11:41 直前）の独立照合値と一致し、07250f4a02 以降 byte 不変。pY が freeze 後に `frozen_sha == 5a1874d3be8b98b8` を独立照合（verify_sha == banked_sha gate）。builder + fixture 4 は v6 以降不変。

## 2. 検証系譜（3 軸 CLOSE + consultation）

| 軸 | evidence |
|---|---|
| **機構** | pS §33 = `f4a2f440bcb260715ced65979cfc4aede78a7b1727c1008372814341ed1e0063` @ `37ffb8f653`（契約層は `ControlMode` で駆動/保持を区別・pQ の原主張撤回を pS が検証） |
| **pin** | pN v13 exact-pin **PASS-WITH-DECLARED-OPEN** transcript = `3432de3c3462336d741f95314c189f75eb233aefc0d8872b6a1ada5c17ef0b81` @ `7ce2a520c9` |
| **authority** | Rs ratify 2026-07-20 21:44（B1 = D-1「`EvidenceRecord.source_ref` 束縛」を CC1 設計判断として委譲・veto 不行使）・custody = `WMSO_RS_B1_DELEGATION_RECORD_20260720.md` §5・DDR#27 CLOSED |
| **consultation** | pY OPS-SUP GO = `WMSO_D11B_FREEZE_CONSULTATION_OPSSUP_20260721.md` `424b8bfb1ff95ea85603d5976158f9ff4a390754a8a3d5aab02fbd82ba8e5dfb`（declared-open 4 件の risk 記述 = 4 件とも正確と判定） |

## 3. declared-open 4 件（**「open として」封印** — open=0 を宣言しない §規律）

1. **`stats_key` 一意性**: length 不一致での共有 = fail-closed（`E_BINDING_NORMALIZER_VALUE`）／同一 length での共有 = **検出 code 不在ゆえ一意必須読みで silent-pass**（certificate は通る）。`§1.2` で規則を定めれば閉じる。
2. **§7 到達性負例**: `E_BINDING_HASH_MISMATCH` が非 canonical bytes で実発火することの実証 = **impl leg**。
3. **§5 閾値系**: 判定式・class 台帳・窓幅 = **slice 詳細 prereg + Rs 裁定**。
4. **U-2 / U-5 / U-6**: producer artifact 阻止 / demo 移行 / topology ledger 束縛 = **D1.1-C prereg の必須入力**（DDR 登録済）。

## 4. 境界（freeze が主張しないこと）

- freeze = **設計書面の確定のみ**。⛔**implementation / training / closed-loop authority = CLOSED 継続**。
- **arity（`ParallelRegion` 枝数）SUSPENDED は本 freeze を block しない**: tensor_binding は arity 非依存（DESIGN 全文で arity/ParallelRegion への依存 = 0 hit・pY 独立確認）。arity supersede（Rs「B」vs「A 推奨」）+ DUAL-ARM 適合は Rs 専権 OPEN のまま、本 freeze と独立。
- **凍結 D1.1-A `contracts_v2` 3 file は不変**: DESIGN `00192d20ca00b654…` / EP md `c474acea7c58…` / EP JSON `e63176af9bc3…`（本 D1.1-B は schema delta を導入せず）。
- **push は Rs 一言待ち**: 本 freeze = **FROZEN-LOCAL / CUSTODY-PENDING**。Rs は「freeze」のみ言及（D1.1-A の「freeze + push」と異なる）。branch = `rlrk/optE-s2-substrate-swap`。権限ある exact push + remote readback で custody CLOSE。
- 後続順序: **D1.1-B FROZEN → D1.1-C（artifact manifest）→ boundary-only vertical slice**（着手は Rs 指示・self-start しない）。

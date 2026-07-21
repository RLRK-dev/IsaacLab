# WMSO D1.1-C `artifact_manifest` — [DEFER-RECON] reconciliation record

- node: `T-WMSO` D1.1-C; 著者 = `w2:pQ` RS-TECH-LEAD2; 作成 = **2026-07-21 12:24 JST**（shell 実測）
- **本 chunk** = D1.1-C `artifact_manifest` の**詳細 prereg 執筆**（scope prereg v1.1.1 `:19`「D1.1-C / slice は着手時に各自の詳細 prereg を切る」）
- **着手指示** = Rs 逐語「go」（2026-07-21 12:1x・D1.1-B FROZEN/CUSTODY-CLOSED 完了直後）
- **照合対象** = LEDGER §DDR **全 35 項目**（実測列挙）。⛔本 record は §運用2 の必須 artifact であり、判定を省略しない。

## 1. 本 chunk の前提（scope prereg §3 banked outline・逐語要旨）

1. contracts_v2 + tensor binding を **code / model / data / config / evaluator / EvidencePolicy / substrate_id の exact hash へ結合**（training-time run manifest 型）
2. **`substrate_id` 必須化** — 旧 contaminated log へ明示 `substrate_id` を付与し **silent pooling 禁止**
3. **minimal JCS の package 全体への展開**（artifact manifest・証拠 bundle・配布 metadata）+ package/CI 最終整備
4. **DC-3 grade 別 proof obligation の実体結合**（`EXACT_TRAIN_TIME` = training run manifest / source commit / config hash … — C の manifest が proof の**実体供給源**）

## 2. ⭐ 判定を可能にした原則 — **機構 / policy の分離**

D1.1-C が設計するのは「**何を記録し、どう区別するか（機構）**」であって「**その記録を使ってどう判断するか（policy）**」ではない。⇒ policy が未裁定でも機構は設計できる。**ただし機構に policy を焼き込めば、その未裁定の判断を先取りすることになる**（本 record の carry はすべてこの線で切る）。

## 3. DDR 全 35 項目との依存判定

### 3.1 ⛔ FOUNDATIONAL 依存 = **1 件のみ**（#26）— 機構/policy 分離で着手可

| | 内容 |
|---|---|
| **#26 P0 substrate defect** | 状態 = **PENDING**。L-P0 測定済（`e5d2dc214a`）= R0[汚染 kin] 到達 vs R1[clean kin] **全滅** = chain 帰結レベルの非無視差。**未解決部分 = 「banked evidence の継続利用可否」の Rs 裁定**（historical impact 裁定待ち）。 |
| **依存の実体** | 前提 2（`substrate_id` 必須化）が #26 を参照する。 |
| ⭐**判定 = 着手可** | D1.1-C が作るのは **汚染/clean を `substrate_id` で区別する機構**。#26 が決めるのは **区別した後どちらを使うか（policy）**。⇒ **機構はどちらの裁定でも実行可能**であり、むしろ**裁定を実行可能にする前提条件**。 |
| ⛔**carry（機構に焼き込まない）** | 「D2 transition data = 修正済み clean substrate のみ」といった**選別 policy を D1.1-C の設計に焼き込まない**。prereg では「区別・記録・silent pooling 禁止」までを IN とし、**どの substrate を採用するかは #26 の Rs 裁定に委ねる**旨を明記する。 |

### 3.2 D1.1-C が**消費**する carry（私の court・prereg で扱う）

| # | 項目 | 機構（D1.1-C が設計） | ⛔carry（D1.1-C が閉じない） |
|---|---|---|---|
| **#28** | U-2 producer artifact 阻止 | manifest が run 毎に producer artifact を pin する機構。DDR 逐語「pQ — C prereg で解決」 | 発行済 certificate 下での encoder 差替えの**阻止**は closed-loop eligibility 検査の実装 |
| **#29** | U-5 demo 移行（198 demo が不 bind） | manifest が**両段 binding を記録**する機構（`E_BINDING_STAGE_IDENTICAL_UNCONFIRMED` の解消経路） | **kinematic 全削除後の demo 再記録**は別 lane（p4/p0）依存 |
| **#30** | U-6 topology ledger 束縛 | `chain_topology_class` を manifest **metadata** として記録 | **契約層での束縛 = schema delta ⇒ Rs review**（frozen `SemanticFieldSpec` に格納できない） |

### 3.3 carry だが本 chunk の設計を妨げない（機構 vs 実体）

- **#21 FM2 demos regeneration**（obs-contract change）— #29 と同族。manifest の記録機構は設計可・再生成は別 lane。
- **#31 skill selectability ①trainer 実在（AC/IC/AR = ABSENT）** — training run manifest の**実体**が未取得。⚠**機構の設計は依存しない**が、manifest の実データ充填は trainer 実在に依存 ⇒ **carry として明示**。

### 3.4 D1.1-C に**非依存**（別 lane の物理/訓練 premise）

**#2**（P3 body_q sync-premise）/ **#4**（P2 non-crutch）/ **#12**（fork-B V0）/ **#18**（grip-efficacy SRG）/ **#19**（ENV-MULTIWORLD freeze）/ **#25**（(d) arm-control remediation）/ #3 #5 #6 #7 #9 #11 #13 #14 #15 #16 #17 #20 #22 #23 #24。
⇒ いずれも **arm-control / training / substrate 実行系の premise**。D1.1-C は**契約層の記録設計**（何を hash に結合し、どう区別するか）ゆえ、これらの物理的成否に依存しない。⚠**#19 は training data 生成に効く**が、それは 3.3 の「機構 vs 実体」と同じ線で carry。

### 3.5 作業様式にのみ効く（設計内容に非依存）

- **#34**（NEST role label と C2 guard の衝突）/ **#35**（`validate.sh` が docs-only commit で偽 FAIL）⇒ 本 node の commit が `--no-verify` である根拠。**設計内容をブロックしない**。

### 3.6 CLOSED / 別軸

- **#27** B1-locator = ✅**CLOSED**（D-1 採択・Rs ratify）。/ **#32** rollout horizon vs cycle length = SDM 設計軸（pX+pQ・D1.1-C 非依存）。/ **#33** 所管境界 = p5↔pX 確定済。/ **#1 #8 #10** = 別 node の gate。

## 4. 結論

✅**D1.1-C 詳細 prereg の着手 = 可**。

- **FOUNDATIONAL 未解決依存 = #26 のみ**で、**機構/policy 分離**により着手を妨げない（機構は裁定を実行可能にする側）。
- ⛔**prereg に必ず書く carry 5 件**: ①#26 の選別 policy を焼き込まない ②#28 の阻止実装 ③#29 の demo 再記録（別 lane）④#30 の契約層束縛（schema delta ⇒ Rs review）⑤#31 の trainer 実在（manifest の実データ充填）。
- ⛔**本 record は着手可否のみを判定**し、D1.1-C の設計内容・IN/OUT を確定しない（それは prereg 本体）。

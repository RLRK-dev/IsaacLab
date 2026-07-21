# P-D1 PREREG v1.4 — W-b 目的への再凍結（DRAFT・p11 ARM-CONTROL-DESIGN, 2026-07-21）

**Author:** ARM-CONTROL-DESIGN (`w2:p11`)。**Status:** **DRAFT / proposal** — 凍結は p4 landing 時。
**所管:** C-1/C-2 prereg = p11 court（p4 確定 2026-07-21 13:15 JST。control-method が p11 へ移った時点で本 prereg も移動・「元 %12/p4 系」は歴史的経緯）。
**対象:** `ARM_CONTROL_PD1_PROBE_PREREG_RSTECHLEAD_20260719.md` **v1.3 FROZEN `b3ddfbab1c`**（+ header fix `535304198d`・worktree == HEAD を実測 / blob sha256 先頭 `3f65b06fdb10d5b5`）。
⛔ **実 re-run は本書で認可されない** — `production-launch-gate` + Rs（p4 指示）。本書は**設計軸の再凍結案**のみ。

---

## 0. なぜ再凍結が要るか（1 行）

**v1.3 の目的節が現状と合わない。** v1.3 は「**記録された振付を PD が bar 内で追従するか**」を問うが、**その振付は Rs 裁定 B（振付＝再工事 W-b）で作り直す対象**になった。⇒ 追従の可否でなく「**新しい振付をどの速度域まで設計してよいか**」を測る probe に変わる。

| | v1.3（現行・凍結中） | **v1.4（本案）** |
|---|---|---|
| 問い | 記録軌道を bar 内で追従できるか | **どの指令速度まで bar 内に収まるか（設計包絡）** |
| 記録 npz の役割 | **acceptance の参照**（合否の基準） | ⭐**励振signalのみ**（現実的な速度を出させるための入力） |
| 出力 | probe PASS/FAIL | ⭐**ω_max（joint 毎）と T_LAG_BAR の材料** = 新振付の設計制約 |
| C-1/C-2 の位置 | S-1 bar 設計 input | 同左（**変更なし**）+ 上記包絡の実測 |

⚠ **v1.2 の R-1 FAIL verdict は不変**（§13 R-2「本 probe 救済でない」）。本再凍結は **verdict の救済ではなく、問いの差替**。

---

## 1. ⭐ v1.3 から**退役**する項目（追加より先に書く）

| 項目 | v1.3 での位置 | v1.4 | 理由 |
|---|---|---|---|
| **L-P2′ parity vs R0b**（清潔基盤 kinematic playback との一致） | acceptance leg | ⛔ **退役** | ①参照 R0b は **kinematic 走行**であり、Rs 07-19「kinematic 基線 run = 廃止」は裁定 B（pin のみ復活）でも**戻っていない** ②W-b で**旧 chain との一致自体が目標でなくなった**（合わせる相手を作り直す） |
| **R0 / R1**（kinematic 走行） | run matrix | ⛔ **本 prereg では走らせない** | 同上。⭐**v1.4 は kinematic 走行を 1 本も要求しない**（P-1 / 裁定 B 適合）。L-P0 の既存 evidence は banked `e5d2dc214a` を参照するのみ |
| **L-P4 no-haul**（route-start teleport 後の追従） | R1 で採点 | 🔶 **保留**（C-1/C-2 では採点しない） | route-start re-pose は分類 B（reset 系）で残るが、**W-b で route-start の pose 自体が再定義される**ため、旧 frame-0 値に対する採点は意味を持たない |
| **decision tree の probe PASS→S-1 rollout** | §5 | 🔶 **切離し** | S-1 rollout は W-b 振付と design-gate 後。本 probe は**包絡の測定**であって rollout の許可条件でない |

⇒ **v1.4 は v1.3 より小さい。** 新規に足すのは §3 の観測量 2 件のみ。

---

## 2. 変更しないもの（明示）

- **C-1 / C-2 の run 定義そのもの**: `--arm-pd --kd-scale 0.25` / `--arm-pd --kd-scale 0.25 --ke-scale 2.0`（R2-class single、同 substrate / 同 recording / 同 seed、probe v0.8 `bc1f7f2d48`）。
- ⛔ **effort cap 不変** = ±150 / ±28 N·m（実機 spec・census assert が ke/kd のみ scaled を確認）。**引上げ禁止**（fidelity 非保守方向・design §9）。
- **lag-law leg / ringing leg / L-P3 saturation / census**（v1.3 §6 の宣言観測量）。
- **bar 値そのもの**（L-P1 2/5 mrad・EE 1.5/3 mm・L-P3 WARN 1% / FAIL 5%・M-6 N_DIV=48）。⇒ **bar は動かさない**。動かすのは**採点対象でなく用途**（合否 → 包絡の切り出し）。
- **video leg**（設計 §5・必須）と **物理妥当性 = Rs human-GT**。

---

## 3. ⭐ 追加する宣言観測量（2 件のみ・凍結時に固定）

### O-1 指令速度の被覆（ω coverage）
per-joint に、励振signalが実際に出した指令角速度 ω の分布（p50 / p95 / max、`ω > 0.5 rad/s` の frame 比）を報告する。
⛔ **理由（必須）**: 包絡は**実際に励振された ω 範囲でしか主張できない**。ω が薄い joint について「その速度まで大丈夫」と外挿しない。**被覆外は「未測定」と書く**（PASS でも FAIL でもない）。

### O-2 包絡の切り出し（envelope）
実測 lag 則 `T_lag = err/ω` から、per-joint に

> **ω_max(joint) = （適用 bar）/ T_lag(joint, p95)**

を算出して報告する。⇒ **新振付の設計制約**（「この joint はこの角速度を超えないこと」）として S-1 / W-b へ渡る材料。
⚠ **bar の選択を宣言**: 準静的窓は 2 mrad、過渡窓は 5 mrad（v1.3 §2 の phase split 定義をそのまま使う）。
⚠ **hypothesis tag**: 線形 lag 則の外挿は仮説。**O-1 の被覆内でのみ有効**と明記して報告する（measured governs）。

### ⭐ R-ROBUST との結合（宣言・本 probe では採点しない）
Rs 裁定 B の摂動耐性要件（≥ trainer residual / DR scale）は**振付の受入条件**であって本 probe の合否ではない。ただし**包絡には効く**:
trainer の residual は**指令の上に角速度を上乗せする**ため、新振付が使ってよい速度は **ω_max − ω_residual** に縮む。
⇒ **O-2 の報告には「residual 分の余裕を残した値である」ことを併記**し、ω_residual の実値は別途実測（未測定ゆえ本書では数値を置かない）。

---

## 4. 合否（v1.4）

**本 probe に「PASS / FAIL」を置かない。** 出力は**測定値**（T_lag / ω 被覆 / ω_max / ringing / saturation / census）。

- ⛔ **instrument INVALID 条件は維持**: census FAIL（nu / imported ABSENT / cap 不変）・ringing leg 欠測・`|ctrl − intended| ≤ 1e-9` の wiring assert 破れ ⇒ その run は**無効**（結果を使わない）。
- **saturation が WARN/FAIL bar を超えた場合** = 包絡の上端がそこで切れる、として報告（re-trajectory は別チャンク・design §5 分岐）。
- **sustained ringing** = LOUD 報告（その gain 候補は包絡算出に使わない）。

⇒ **「別様に出得ない test」ではない**: C-1/C-2 は ringing / saturation / 被覆不足で**実際に使えない結果を返し得る**。

---

## 5. 適合確認（本案が触れる規則）

| 規則 | 適合 |
|---|---|
| **P-1 物理結果を捨てない**（Rs「すてるなよ」） | ✅ C-1/C-2 は PD 駆動のみ。**kinematic 走行 0 本**（§1 で R0/R1 を退役） |
| **裁定 B**（kinematic 例外 = clip-retention pin のみ） | ✅ 本 probe は pin を `route_c1_pin=True` で使うが**実装は pin arc court**。⚠ pin 実装が equality 形へ変わる場合、本 probe の substrate pin も追随が要る（**下記 §6 の flag**） |
| **§0#3 IK-only / #4 コ字 LOCK / #1 dual-arm** | ✅ 非接触（gains のみ） |
| effort cap 実機 spec | ✅ 不変・census assert |
| 記録面 | ✅ eval_runs 配下・CLAUDE.md / prohibited.md 非接触 |

---

## 6. ⚠ entangle flag（p4 指示により明示）

1. **pin arc (d-a)/(d-b) と結合**: v1.3 §1 の substrate は `route_c1_pin=True`（real pin）。Rs 指示で pin が **equality 拘束形**へ移る場合、**本 probe の pin もその形で走らないと substrate が一致しない**。⇒ **C-1/C-2 の実走は pin 形の確定後**が整合的（p4 court）。
2. **trainer と結合**: §3 の ω_residual は trainer の residual scale に依存（DDR #18 / trainer node = %12/pQ court）。⇒ **数値は借りる側**であり、本書では確定しない。
3. **実行 driver（DDR #31）とは非結合**: C-1/C-2 は既存 probe harness 単走ゆえ `RoutingOrchestrator` 不在の影響を受けない。

---

## 7. 非主張 / gate

- **凍結していない**（DRAFT。凍結 = p4 landing）。**走らせていない**。**bar を動かしていない**。
- ω_max の数値を主張していない（**未測定** — C-1/C-2 実走後）。
- v1.2 の R-1 FAIL verdict は**不変**。
- 実 re-run = `production-launch-gate` + Rs。**本書は認可でない。**

## 8. L 自己申告

**L1**（新規 file 1・prereg 案・コード 0・数値凍結 0・landing なし）。
⚠ 凍結時（p4 landing）は **prereg 本体の版表更新を伴う**ため、その時点で L2+ 相当の記録操作になる。commit = explicit pathspec + `--no-verify`（DDR #35）。

# fingertip / H-4 — p4 **records correction v2**

**訂正者:** RS-TECH-LEAD (`w2:p4`)。**起草（`date` 実測）:** 2026-07-26 20:10:13 JST（date-THEN-write）。
**応答する RETURN:** `MSG-PN-P4-FINGERTIP-H4-NOREMEASURE-RETURN-20260726-001`（cause-side records RETURN）。
**bank 状態:** **§6 参照**（起草時は PROCESS HOLD 下で未 commit、その後 Rs 裁定により bank）。
**⛔ 履歴 rewrite なし** — 旧 commit は immutable。amend も改変もしない。

---

## 0. 訂正対象（exact pin・私が独立に再計算して一致）

| 項目 | 値 |
|---|---|
| **path** | `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/P4_RS_RULINGS_20260726_PIN_AND_FINGERTIP.md` |
| **commit** | `5d87b3a1fbdf72bfb7718784c4b630b12c4a365f` |
| **sha256（全 64 桁）** | `66638471171e9a9e32de0e4a28ba45b2a976af6f3715c56b6cf535398dd98d72` |
| **行数** | 49 |
| **該当行** | `:36` |

**`:36` 逐語（旧・保全する）:**

> - **非 blocking:** p11 は H-4 を **3 参照点**（`0.220` / pad / `0.2757`）で出力する設計にしており、**どちらに決まっても再測定は不要**。⇒ 誰も待たない。

---

## 1. RETRACT — 撤回するのは `:36` の 2 節のみ

⛔ **撤回 (i):** 「**どちらに決まっても再測定は不要**」
⛔ **撤回 (ii):** 「**⇒ 誰も待たない**」

⭐ **撤回しない（同じ行のうち事実部分）:** 「p11 は H-4 を **3 参照点**（`0.220` / pad / `0.2757`）で出力する設計にしており」。

---

## 2. 正確形 — p11 の current evidence に接地

**接地（私が独立に読み・sha256 を再計算して一致）:**

| 項目 | 値 |
|---|---|
| **path** | `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/P11_ARM_TARGET_CONSUMER_REVIEW_20260726.md` |
| **commit** | `81779f2a3ec58c0f472ce6e0e9abf1065d6d03e9`（author time `2026-07-26 19:49:30 +0900`） |
| **sha256（全 64 桁）** | `62e6580d0c5298353a3c3188a24360e20343f798d67d7ba5abdd51cc1551f69d` |
| **行数** | 415 |
| **該当行** | `:328`（B15）／`:330`（B9）／`:338`（B4） |

⚠ p11 の後続版は **records-only で本 semantic は不変**と申告されている（pN 経由）。⇒ 私は**自分が読んだ exact commit を pin する**。

### 2.1 正確形（3 点とも p11 の line に接地）

1. ⭐ **proxy は測定済**（`:328` / `:330`）— 現行 H-4 の 3 点の値は存在する（bank `908ac4674576c3b936fe66866254d17691b6cc8e`「Measure the grasp Jacobian at three points, and mark what is not swept」）。⚠ ただしその中身は **各列を最大絶対成分に縮約 ＋ 1 姿勢**。⛔ **「未測」と言ってはならない**（p11 逐語「**『未測』ではない・消さない**」）。
2. ⛔ **未測なのは evidence-grade**（`:328` / `:330`）= **方向つきの完全な 3 成分 Jacobian ＋ 認可された envelope**。
3. ⛔ **proxy から bar は導けない**（`:330`）⇒ **H-4 全体は HOLD 継続**。

### 2.2 ⛔ 同一視しない（RETURN の明示要求）

**taxonomy 分類の進行可否** と **H-4 evidence-grade 測定の充足** は**論理的に別軸**である。⇒ **一方から他方は導けない。** 旧 `:36` はこの 2 つを 1 文に潰していた。

⛔ **私は taxonomy の進行可否を決めない**（本書は進行可も進行不可も主張しない）。⚠ **operative state（governing）= `p17` relay は exact-pin PASS まで CLOSED** — `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/P11_ROUTING_SUBMISSION_MATERIALS_V4_20260726.md:124` @ `81779f2a3ec58c0f472ce6e0e9abf1065d6d03e9`（sha256 `94f992db120898e6a6a1c2e0defb4e9f7f116f6385c2a24f1424594348f41089`・133 行）。

### 2.3 ⛔ 本書が選ばないもの

- **必要な測定の方式**（何をどの面で測るか）を選ばない。
- **GO を出さない**。**H-4 全体 HOLD を保持**する。

---

## 3. 私の欠陥の機構（provenance の記録 — ⚠ 帰属の移転ではない）

⚠⚠ **provenance の evidence-grade（fence）:** 以下の「文言の初出」は **私の session-context に基づく**（私の session transcript 内の受信 message）。⛔ **stable message ID も durable な artifact pin も無い＝非 durable**。⇒ **他者は再現できない。本書はこれを独立 evidence として用いない。** 私の欠陥の**機構の説明**としてのみ置く。

**文言の初出（session-context・非 durable）:** `w2:p5` からの pane message（私の session 内の受信・**2026-07-21 21:52 JST** と表示）に、「p11 が 3 点で判断非依存化済ゆえ誰も待たない」旨の一文があった。

⛔ **私の欠陥:** 私は **p11 の artifact を自分で読まずに**、その主張を**自分の banked record に active voice で書いた**。
**違反した規則:** `CLAUDE.md` §27「⛔ **他 pane の message の数値で裁定しない**（artifact を自分で見てから裁定する）」。
⚠ **責任は私にある。** 上記 provenance は**機構の記録**であり、**cause の移転ではない**（`:36` を書いたのは私）。

---

## 4. 別 court に残る live surface（⛔ 代理編集しない・**RETURN 依頼**）

同じ semantic が **p5 の banked record に live で残存**している（私の実測）。⛔ **私は編集も disposition の決定もしない。**

| 項目 | 値 |
|---|---|
| **path** | `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/P5_ESCALATION_fingertip_offset_franka_legacy_20260721.md` |
| **commit（当該 file を最後に触れた）** | `fe80839219b913518f3d2afa84323f9cbbd02df4` |
| **sha256（全 64 桁）** | `30225018d9fe9dc3d649804a2c3ef60175993ed79146bc53c2534072abd6835a` |
| **行数** | 49 |

| 行 | 逐語（抜粋） |
|---|---|
| `:32` | 見出し「controller-driven 再設計への含意（p11 の対処は正しい・**判断非依存**）」 |
| `:33` | 「… sizing は「閾値と同じ面」= 0.220）は **正しい**。2mm 予算は 0.220 点に課される。**判断に依存せず進めてよい。**」 |
| `:42` | 「… **p11 は判断非依存で sizing 継続可**ゆえ本件は**誰も block しない**（p11 の 3 参照点 bank `53b8997ed4`）」 |

⚠ `:42` は p5 自身が 2026-07-26 に**別の leg**（「Rs 専権」）を撤回した後の**現行文**であり、**「判断非依存」部分は撤回されていない**。
**依頼（pN へ）:** 上記 3 行を **p5 へ RETURN** してください。判断の根拠は p11 `:330`（B9）＝「**面の選択それ自体は新たな measurement-design point を増やさない**」の撤回。⛔ **p5 の disposition は p5 の court**。私は決めない。

---

## 5. 不変（本書は触れない）

- **Rs 逐語**（custody の byte 形どおり — §1「1 クリップのケーブル固定ではkinematicを残す。それ以外ではkinematic禁止」／§2「2　は私が判断することではない」／§3「3　削る」）
- **`:31`-`:35` の court routing**（Rs は判断しない ⇒ 設計 lane の court ／ 私の framing 撤回 ／ **p5 へ RETURN** ／ 私は内容を決めない）
- **§3 handoff 追記の記録**、その他の p4 記録
- **H-3.1 GO なし ／ H-4 全体 HOLD ／ class B は別 leg で HOLD ／ source・`[CHANGE]`・実装・RUN・verify・status・gate flip なし**

---

## 6. bank 状態（経緯を残す）

| 時刻（JST） | 状態 |
|---|---|
| 2026-07-26 20:10:13 | 起草。**未 commit** — pN `MSG-PN-P4-PRECOMMIT-GATE-20260726-002`（PROCESS HOLD）に従う |
| 2026-07-26 20:51:53 | pN RETURN `…-003` の 3 件（B1/B2/B3）を修正。なお未 commit |
| 2026-07-26 20:53:06 | pN `…-004` = **draft PASS-CLOSE**。ただし bank は **all-files gate または人間/Rs 別裁定まで HOLD** |
| 2026-07-26 20:56:37 | 私が clean parent `81779f2a3e` で all-files を独立実測（**RC = 1**・5 hook が計 **1019 file** を書換・codespell は banked artifact 内も指摘）⇒ Rs へ選択肢 A〜D を上程 |
| 2026-07-26 21:23:26 | **Rs 逐語「推奨で良い」= A 採用** ⇒ HOLD は解除条件（人間/Rs 別裁定）により解除。custody = `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/P4_RS_RULING_20260726_RECORDS_COMMIT_GATE.md` @ `e7048174ed8c1f23665eff2fa48c24b6ddfb8b67` |

⇒ **本書は bank された。** ⇒ **旧 `:36` の 2 節（`§1` の (i)(ii)）は撤回が発効**し、それを根拠にした下流の主張は**成立しない**。
⚠ **§4 の p5 court 側 3 行は未処理のまま**（p5 の disposition 待ち）。⛔ 私は代理編集しない。

---
**p4 records correction v2（未 bank）= 起草 2026-07-26 20:10:13 JST / RS-TECH-LEAD (`w2:p4`)**

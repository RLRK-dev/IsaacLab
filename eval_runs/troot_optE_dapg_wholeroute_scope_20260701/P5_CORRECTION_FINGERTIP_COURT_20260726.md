# 訂正版 — fingertip 定数の disposition（p5 が自分の主張を RETRACT し再提出）

**stable ID:** `P5-CORRECTION-FINGERTIP-COURT-20260726-001`
**著者:** SKILL-DETAIL-DESIGN (`w2:p5`) = **原因側**。**発行:** 2026-07-26 16:42:50 JST（date-THEN-write）。
**契機:** p4 → p5 RETURN（pN 経由・VERIFIED）`MSG-P4-P5-FINGERTIP-COURT-RETURN-20260726-001`。
**上位 custody（p5 独立照合済）:** `P4_RS_RULINGS_20260726_PIN_AND_FINGERTIP.md` @ `5d87b3a1fbdf72bfb7718784c4b630b12c4a365f` / sha256 `66638471171e9a9e32de0e4a28ba45b2a976af6f3715c56b6cf535398dd98d72`（**p5 が git object 上で再算出し exact 一致**）。
**Rs 逐語:** 「**2　は私が判断することではない**」／**受領文脈** = p4 の列挙 2 = `EE_TO_FINGERTIP=0.220`(Franka legacy) vs コ実測 `0.2757`（custody §2 で確認・p4 は直接 witness）。
⛔ **本書は内容値を選ばない**（0.220 か 0.2757 かは決めない — RETURN の指示）。⛔ source / 実装 / RUN / verify / status flip は行わない。

---

## 1. RETRACT（私の原因部分・逐語で特定）

**旧 artifact:** `P5_ESCALATION_fingertip_offset_franka_legacy_20260721.md` @ `454db0f866b300ea51fa4b6743829cb24fa66042` / sha256 `0aa784c9a7b6b94897d9eb81c0422aa744e0f41699631521ad61fe1dc2426dd4`（p5 独立再算出で exact 一致）。

**撤回する主張（当該 artifact の逐語・行番号は当該 commit 上）:**

| 行 | 撤回する逐語 | 判定 |
|---|---|---|
| `:32` | 「## 5. ⛔ Rs escalation（invariant #4 + env/success 設計 = **Rs court**・p5 は裁定しない）」 | **RETRACTED** |
| `:36` | 「⚠ これは **PREMISE 隣接**（#4 locked geometry）+ env/success 設計（/reward-design gate）ゆえ **Rs 専権**」 | **RETRACTED** |
| `:5` | 「**Rs court** = 不変前提 #4（コ geometry LOCK）+ env/success 設計の変更」 | **RETRACTED** |
| `:42` | 「（env/reward 設計 = **Rs** + /reward-design gate・#4 locked geometry）」 | **Rs 帰属部分のみ RETRACTED**（gate 要求は有効） |

⭐ **撤回しない部分（正しい主張は帳尻合わせで変えない）**: 同 artifact の `:33`（問いの定義）/ `:34`（事実 3 点）/ `:35`（トレードオフ）/ `:38-39`（§6 = 閾値表「指先」の訂正）/ `:1-4` の事実群は **いずれも有効**。`:2` §2「相殺は無い」（success は 0.220 点 ↔ 物理 cable で測るため offset 差が残る）も **有効**。

## 2. なぜ誤りだったか — Rs 逐語に依存しない独立の理由（2 件）

**(a) 「#4 に属す＝PREMISE 隣接」は誤り。** #4 が LOCK するのは **geometry（asset）**であり、`EE_TO_FINGERTIP` は geometry ではなく **記録側の派生定数**。しかも #4 自身が「記録を locked geometry に一致させる」先例を本文に持つ — `04-Specs/RS71-System-Spec-SSOT.md:40` 逐語「✅ **records-vs-code RESOLVED 2026-06-23**（commit `85315bbec6`）: the committed asset is now `2f85_koshape.xml`（コ）」。コ実測 `0.2757` は **locked geometry の測定**（`task_config.py:321`・re-derived 2026-06-22・artifact `eval_runs/troot_optE_rs71_koshape_ee_tip_rederive_20260622/`）。
⇒ **定数を geometry に一致させることも、0.220 を維持することも、premise の変更ではない**（どちらも records 側の選択）。#4 が要求する source-GO は *geometry を変える* 場合の要件であり、本件は geometry を変えない。

**(b) 「`GRASP_Z` が load-bearing ⇒ Rs 専権」は non-sequitur。** load-bearing（`task_config.py:93` `GRASP_Z = TABLE_HEIGHT + CLIP_BASE_HEIGHT + EE_TO_FINGERTIP` / `:95` `PUSH_Z` 同）が要求するのは **設計ゲート**（`/geometric-design`・`/reward-design`）と **L3 triage**（`task_config.py` = L3 自動昇格 path）であって、**Rs の個人判断ではない**。設計ゲートは設計 lane 内で執行される。

⛔ **失敗の型 = 「帰結が重い + gate が要る」を「Rs 専権」と同一視した。** これは #4 本文から **独立に検出可能**だった ⇒ Rs 逐語は誤りを *露呈* させたが、作ったのではない。同族の既記録教訓: [[feedback-same-constant-is-not-same-measurement-surface-2026-07-18]] / [[feedback-the-boundary-question-and-the-identity-question-are-different-2026-07-15]]。
⚠ **副次の自己申告**: 私は「gate が要る」ことを正しく見抜きながら、その gate を **自分の lane で回す**のでなく human へ渡した。これは §運用26 の逆用（BLOCKED_FOR_USER の乱用）に相当する。

## 3. 訂正版 disposition — 設計 lane 内の court / gate（内容値は選ばない）

対象を **消費先ごとに分解**して court を付ける（1 個の「Rs 判断」に丸めない）:

| # | 対象 | court | 必須 gate |
|---|---|---|---|
| **(A)** | **success 述語の測定面** = 2mm / 12mm / 10° を **どの点**で評価するか（skill の成功条件） | ⭐**p5（本 pane）** = 各 SKILL の中身の詳細設計 | **`/reward-design`**（成功条件 = 直交 forced gate・4 artifact 必須）＋ GPU 消費前に **`/pre-check`** |
| **(B)** | **positioning 定数** `GRASP_Z` / `PUSH_Z`（腕の指令先・`EE_TO_FINGERTIP` を消費） | ⚠**UNCONFIRMED**（下記） | **`/geometric-design`**（位置・形状パラメータ変更の forced gate・6 ステップ出力）＋ `task_config.py` ゆえ **L3 自動昇格**（L2 + 直交ゲート + 多視点並行検証） |
| **(C)** | **定数 `EE_TO_FINGERTIP` 自体**（`task_config.py:78`） | (B) と同一 | 同上（**新規測定は不要** — locked geometry の測定は `:320/:321` に既に banked） |
| **(D)** | **そもそも re-derive が必要かの証拠**（0.220-nominal は internally consistent かつ Rs 動画 GT で grasp working。controller-driven 下でその証拠が保つか） | 証拠軸 = **pN / pZ** | (A)(B) への入力 |

⚠ **(B)(C) の owner = UNCONFIRMED ゆえ HOLD する（帰属を捏造しない）。** 理由 = `GRASP_Z`/`PUSH_Z`/`EE_TO_FINGERTIP` は **複数 skill が共有する SSOT 定数**であり、2026-07-20 の絞り込み「p5 = 各 SKILL の**中身**の詳細設計」に収まるか未裁定（共有定数の court は既知の未裁定境界）。候補 = p5 / p17 SKILL-DESIGN（分解・単位・語彙）/ p11 ARM-CONTROL-DESIGN（腕の指令先）/ p16 MWSO-DESIGN。⇒ **pN 経由で境界照会**し、確定まで (B)(C) を進めない。**(A) は私の court として明確ゆえ、境界確定を待たずに gate を回せる。**

**非 blocking（確認済）**: p11 は H-4 を **3 参照点**（`0.220` / pad / `0.2757`）で出力する設計を bank 済（`53b8997ed4`「Ingest p5's thresholds and measure the Jacobian at three points」・2026-07-21 21:44:30）⇒ **どちらに決まっても再測定不要・誰も待たない**。

## 4. correction chain（影響先・履歴 rewrite なし）

| # | 影響先 | 状態 |
|---|---|---|
| 1 | 旧 artifact @ `454db0f866`（sha256 `0aa784c9…`） | **本書が訂正**。⭐ 旧 artifact 側にも in-place の RETRACTED 注記＋本書への back-pointer を付す（**原文は消さず可視のまま**＝ rewrite でない） |
| 2 | 閾値表 `P5_EE_REACH_THRESHOLDS_for_p11_20260721.md` @ `49a6f66323`（sha256 `e93ee3d799f0bb0d…`） | 「指先」無限定は旧 artifact §6 で訂正済 ⇒ **本書で chain 化**。⚠ 内容値は不変（測定面の *名前* の限定のみ） |
| 3 | p11 ingest @ `53b8997ed4`（設計 5.4.1） | **内容影響なし**（3 参照点で判断非依存）。disposition の読み替えのみ |
| 4 | p4 の framing（本件を Rs の plate に載せた） | **p4 が custody §2 で自ら撤回済**（私は代理編集しない） |
| 5 | 私の handoff `02-Workflow/HANDOFF_p5_vtdesign.md`（git 管理外） | 旧記載「disposition = Rs escalate / 現 open ③ = Rs 判断待ち」を **本書へ差し替え**（自分の record ゆえ自分で直す） |

## 5. 時刻の訂正（RETURN 指示 = 旧 artifact `:3`）

旧 artifact `:3`「**2026-07-21 21:5x JST**」は **丸めではなく falsified**。
- exact evidence = 当該 bank commit `454db0f866` の author date = **2026-07-21 21:49:31 +0900**（`git show -s --format='%ai'` 実測）。
- 「21:5x」は **21:50–21:59** を主張するため、実測 21:49:31 を **含まない**。⇒ 丸めの粗さでなく**範囲の誤り**。
- ⇒ 旧 artifact `:3` を exact 値へ接地し（原文は可視のまま RETRACTED 注記）、以後 `Hh:Mx` 形式の時刻を artifact header に書かない。

## 6. 非主張

- ⛔ **内容値（0.220 / 0.2757）を選ばない。** (A) の gate を回して初めて決まる。
- ⛔ source / 実装 / `task_config.py` 編集 / RUN / verify / status flip / LEDGER・DDR 更新（= p6 court）を行わない。
- ⛔ 他 pane の record を編集しない（発見側の p4 / pN も同様に私の record を編集していない）。
- ⛔ 07-Design / 04-Specs は CC read-only ゆえ触らない。

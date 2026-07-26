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

⭐ **撤回しない部分（正しい主張は帳尻合わせで変えない）**: 同 artifact の `:33`（問いの定義）/ `:34`（事実 3 点）/ `:35`（トレードオフ）/ `:38-39`（§6 = 閾値表「指先」の訂正）/ `:1-4` の事実群は **いずれも有効**。~~`:2` §2「相殺は無い」（success は 0.220 点 ↔ 物理 cable で測るため offset 差が残る）も **有効**。~~ ⛔ **2026-07-26 に N9 で narrow（§7.7）**: 有効なのは **algebraic な非打ち消し**（banked expression に `0.2757` 項もそれを打ち消す項も見えず、`0.220` query 点と cable body 位置を比較する）まで。⛔ **「物理 cable で測るため offset 差が残る」は UNVERIFIED**（接触面 = UNMEASURED / runtime = UNVERIFIED）。

## 2. なぜ誤りだったか — Rs 逐語に依存しない独立の理由（2 件）

**(a) 「#4 に属す＝PREMISE 隣接」は誤り。** #4 が LOCK するのは **geometry（asset）**であり、`EE_TO_FINGERTIP` は geometry ではなく **記録側の派生定数**。しかも #4 自身が「記録を locked geometry に一致させる」先例を本文に持つ — `04-Specs/RS71-System-Spec-SSOT.md:40` 逐語「✅ **records-vs-code RESOLVED 2026-06-23**（commit `85315bbec6787a9cfcb3cb147c87fb78beb3b5ca`）: the committed asset is now `2f85_koshape.xml`（コ）」。コ実測 `0.2757` は **locked geometry の測定**（`task_config.py:321`・re-derived 2026-06-22・artifact `eval_runs/troot_optE_rs71_koshape_ee_tip_rederive_20260622/`）。
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
| **(C)** | **定数 `EE_TO_FINGERTIP` 自体**（`task_config.py:78`） | (B) と同一 | 同上（~~**新規測定は不要** — locked geometry の測定は `:320/:321` に既に banked~~ ⚠**2026-07-26 限定（§7）**: 本欄が述べるのは **geometry の実測値が既に banked** であること（**immutable pin**〔pN `-006` B4〕= `thread_isaac_lab/configs/task_config.py` @ `de786148a7b956f04683db4ab2f35723d6be0f20` / blob `d86380dbe186af003d97465376690c9eba00e9ed` / sha256 `1a0851db9cfc2c740c98821c73c84f5405d1cc96df5fe22a71f66906bb1762bc` の `:78`（`EE_TO_FINGERTIP = 0.220`）・`:320`（`EE_TO_PINCH_CLOSED`）・`:321`（`EE_TO_PINCH_TIP_CLOSED`）— **p5 が blob-id と sha256 を再算出し exact 一致**。⚠ WT 再読は corroboration のみで根拠にしない〔旧記述の read-time 挟み込みは撤回〕）**のみ**。⛔ **腕側（H-4）の Jacobian / 認可 envelope の測定については何も述べない** — そちらは evidence-grade **未測・HOLD**） |
| **(D)** | **そもそも re-derive が必要かの証拠**（0.220-nominal は internally consistent。Rs 動画 GT は **historical witness** =「ケーブルが C1 の溝に入っている・見た目上 ok」まで ⚠**contact geometry の証拠には使わない**〔pN `MSG-PN-P5-FINGERTIP-H4-DRAFT-RETURN-20260726-008` B10〕。controller-driven 下でその証拠が保つか） | 証拠軸 = **pN / pZ** | (A)(B) への入力 |

⚠ **(B)(C) の owner = UNCONFIRMED ゆえ HOLD する（帰属を捏造しない）。** 理由 = `GRASP_Z`/`PUSH_Z`/`EE_TO_FINGERTIP` は **複数 skill が共有する SSOT 定数**であり、2026-07-20 の絞り込み「p5 = 各 SKILL の**中身**の詳細設計」に収まるか未裁定（共有定数の court は既知の未裁定境界）。候補 = p5 / p17 SKILL-DESIGN（分解・単位・語彙）/ p11 ARM-CONTROL-DESIGN（腕の指令先）/ p16 MWSO-DESIGN。⇒ **pN 経由で境界照会**し、確定まで (B)(C) を進めない。**(A) は私の court として明確ゆえ、境界確定を待たずに gate を回せる。**

~~**非 blocking（確認済）**: p11 は H-4 を **3 参照点**（`0.220` / pad / `0.2757`）で出力する設計を bank 済（`53b8997ed479ad94cc42f93e9429574dfe86c5cb`「Ingest p5's thresholds and measure the Jacobian at three points」・2026-07-21 21:44:30）⇒ **どちらに決まっても再測定不要・誰も待たない**。~~

⛔⛔ **RETRACTED 2026-07-26（原因側 = p5・訂正 = §7）。** 撤回するのは **3 節のみ** = 「**非 blocking（確認済）**」／「**再測定不要**」／「**誰も待たない**」。
⭐ **保持（帳尻合わせで消さない・2 節とも真）**: (i) p11 が H-4 を 3 参照点（`0.220` / pad / `0.2757`）で出力する設計を bank 済であること — **full pin `53b8997ed479ad94cc42f93e9429574dfe86c5cb`**・author **2026-07-21 21:44:30 +0900**（p5 が `git rev-parse` / `git log` で再算出）。(ii) **その 3 点の値が proxy として測定済**であること — p11 自身が「proxy（縮約 ＋ 1 姿勢）は測定済・**未測ではない・消さない**」と明記（`81779f2a3ec58c0f472ce6e0e9abf1065d6d03e9` `:330`）。
⛔ **narrow（pN `-006` B5）**: 私が示していないのは「**この参照点の決定それ自体が追加の blocker を生む**」ことまで。⭐ **H-4 全体 HOLD は保持**（§7.4・p11 `:330`）⇒ 「H-4 は不足していない」とは **言わない**。

## 4. correction chain（影響先・履歴 rewrite なし）

| # | 影響先 | 状態 |
|---|---|---|
| 1 | 旧 artifact @ `454db0f866b300ea51fa4b6743829cb24fa66042`（sha256 `0aa784c9a7b6b94897d9eb81c0422aa744e0f41699631521ad61fe1dc2426dd4`） | **本書が訂正**。⭐ 旧 artifact 側にも in-place の RETRACTED 注記＋本書への back-pointer を付す（**原文は消さず可視のまま**＝ rewrite でない） |
| 2 | 閾値表 `P5_EE_REACH_THRESHOLDS_for_p11_20260721.md` @ `49a6f66323cba3ea97f08a8a15c4930dfc1cf8f7`（sha256 `e93ee3d799f0bb0df0450b784cf40844e3abc7f939e38a05a99748ebd822dbbf`） | 「指先」無限定は旧 artifact §6 で訂正済 ⇒ **本書で chain 化**。⚠ 内容値は不変（測定面の *名前* の限定のみ） |
| 3 | p11 ingest @ `53b8997ed479ad94cc42f93e9429574dfe86c5cb`（設計 5.4.1） | ~~**内容影響なし**（3 参照点で判断非依存）。disposition の読み替えのみ~~ ⛔ **RETRACTED 2026-07-26（§7）** ⇒ 影響は **UNVERIFIED**（「判断非依存」を私は示していない）。⭐ p11 は同型の主張を **自ら撤回済**（`81779f2a3ec58c0f472ce6e0e9abf1065d6d03e9` の `:338` = B4 v2「どれに決まっても再測定不要」撤回 / `:330` = B9 撤回）— **p11 の record ゆえ私は編集せず引用のみ** |
| 4 | p4 の framing（本件を Rs の plate に載せた） | **p4 が custody §2 で自ら撤回済**（私は代理編集しない） |
| 5 | 私の handoff `thread_isaac_lab/thread-vault/02-Workflow/HANDOFF_p5_vtdesign.md`（⚠ **repo 内 untracked** — `git status` = `??`・tracked でない・ignore もされていない。**旧表記「git 管理外」は誤り**: repo *外* ではない。pN `MSG-PN-P5-FINGERTIP-H4-DRAFT-RETURN-20260726-010` S1） | 旧記載「disposition = Rs escalate / 現 open ③ = Rs 判断待ち」を **本書へ差し替え**（自分の record ゆえ自分で直す） |

## 5. 時刻の訂正（RETURN 指示 = 旧 artifact `:3`）

旧 artifact `:3`「**2026-07-21 21:5x JST**」は **丸めではなく falsified**。
- exact evidence = 当該 bank commit `454db0f866b300ea51fa4b6743829cb24fa66042` の author date = **2026-07-21 21:49:31 +0900**（`git show -s --format='%ai'` 実測）。
- 「21:5x」は **21:50–21:59** を主張するため、実測 21:49:31 を **含まない**。⇒ 丸めの粗さでなく**範囲の誤り**。
- ⇒ 旧 artifact `:3` を exact 値へ接地し（原文は可視のまま RETRACTED 注記）、以後 `Hh:Mx` 形式の時刻を artifact header に書かない。

## 6. 非主張

- ⛔ **内容値（0.220 / 0.2757）を選ばない。** (A) の gate を回して初めて決まる。
- ⛔ source / 実装 / `task_config.py` 編集 / RUN / verify / status flip / LEDGER・DDR 更新（= p6 court）を行わない。
- ⛔ 他 pane の record を編集しない（発見側の p4 / pN も同様に私の record を編集していない）。
- ⛔ 07-Design / 04-Specs は CC read-only ゆえ触らない。

---

## 7. 第 2 次 RETRACT — 「再測定不要 / 誰も待たない / 内容影響なし」（原因側 = p5）

**stable ID:** `P5-CORRECTION-FINGERTIP-NOREMEASURE-20260726-002`
**著者 / 原因側:** SKILL-DETAIL-DESIGN (`w2:p5`)。**本節の執筆時刻:** 2026-07-26 20:17:26 JST（`date` 実測）。⭐ **initial bank = commit `b59228cfbc305e52b3df8b93b7e4f7f0399489a4`**（parent `bea32cd761305af4d51001475f9fe5133cea89f3` / **author 2026-07-26 21:35:59 +0900**・pathspec 限定で本書＋旧 artifact の 2 path のみ）。〔⚠ **HISTORICAL**: 旧記述「本節は uncommitted ゆえ bank 時刻は存在しない — landing 後に author date を追記する」は **A の landing で解消**。約束どおり実測 author date を追記した。〕
**契機:** pN → p5 RETURN **5 通**（stamp は pN 逐語転記。⚠ **本行の列挙は下記 5 件のみ**）= `MSG-PN-P5-FINGERTIP-H4-NOREMEASURE-RETURN-20260726-004`（**20:10:43 JST**・N1-N7）／`MSG-PN-P5-FINGERTIP-H4-DRAFT-RETURN-20260726-005`（**20:47:12 JST**・C1 = N8 fold / C2 = memory scope）／`MSG-PN-P5-FINGERTIP-H4-DRAFT-RETURN-20260726-006`（**20:50:24 JST**・B1-B5。⭐ pN は同通で `-005` の「現 WT `:34`」を **stale table 継承ゆえ自ら RETRACT**）／`MSG-PN-P5-FINGERTIP-H4-DRAFT-RETURN-20260726-007`（**20:56:16 JST**・B6-B9）／`MSG-PN-P5-FINGERTIP-H4-DRAFT-RETURN-20260726-008`（**21:11:25 JST**・B10 = N9。他は PASS）。
**⚠ 通数の訂正（記録）**: 上記は当初「**4 通**」と書いていたが列挙は 5 件で不一致だった ⇒ **5 通**へ訂正（pN `MSG-PN-P5-FINGERTIP-H4-DRAFT-RETURN-20260726-009` R1）。⛔ **`-009` は本節を訂正させた RETURN であり、上の 5 件の列挙には含めない**（同一行に混ぜて「5 通に ID 6 個」を作った自分の誤りも本行で訂正）。
**⚠ 略記の legend（本書・旧 artifact 共通）**: 本文中の `-004` = `MSG-PN-P5-FINGERTIP-H4-NOREMEASURE-RETURN-20260726-004`、`-005` / `-006` / `-007` = `MSG-PN-P5-FINGERTIP-H4-DRAFT-RETURN-20260726-005` / `-006` / `-007`。**hash 系の pin は全桁のみ使用**（partial + ellipsis の residual = 0・pN `-007` B9）。

### 7.1 撤回する主張（逐語・2 つの行番号面を分けて特定）

⚠ **行番号は面ごとに違い、注記を足すたびに下へずれる。** 旧 artifact の offset は `fe80839219b913518f3d2afa84323f9cbbd02df4` の注記版で **原版 +4**、`-005` 提出時の WT で **原版 +5**、以後も動く。⇒ 下表は **immutable な 2 面（原版 `454db0f866b300ea51fa4b6743829cb24fa66042` / 注記版 `fe80839219b913518f3d2afa84323f9cbbd02df4`）を正**とし、**WT 列は snapshot（固定しない）**。**同一性の識別子は行番号ではなく逐語**。
〔訂正 2026-07-26（原因側 = p5）: 旧 banner の「注記追加で **4 行**ずれた」は **+4 だった時点の記述**。私の `-005` 提出時の WT 列（`:32`/`:33`/`:34`/`:42`）は **+1 stale** であり、pN `-005` の「現 WT `:34`」もこの stale な表を継承した。⇒ 下表で 3 面に分けて訂正（pN `-006` B2）。**pN 側の行番号は pN が自ら RETRACT 済**。〕

| # | 対象 file | 原版 @`454db0f866b300ea51fa4b6743829cb24fa66042` | 注記版 @`fe80839219b913518f3d2afa84323f9cbbd02df4` | WT（⛔ **固定しない** = pN `-006` B2） | 撤回する逐語（= **同一性の識別子**） | 判定 |
|---|---|---|---|---|---|---|
| N1 | 本書（訂正版） | — | `:50` | 逐語で特定 | 「**非 blocking（確認済）**」／「**再測定不要**」／「**誰も待たない**」 | **RETRACTED** |
| N2 | 同上 | — | `:58` | 逐語で特定 | 「**内容影響なし**（3 参照点で判断非依存）」 | **RETRACTED** |
| N3 | 同上 | — | `:45` | 逐語で特定 | 「**新規測定は不要**」（無限定） | **限定に置換**（geometry 実測値のみ・腕側 H-4 に及ばない） |
| N4 | 旧 artifact | `:28` | `:32` | 逐語で特定 | 見出し「（p11 の対処は正しい・**判断非依存**）」 | **「判断非依存」のみ RETRACTED** |
| N5 | 同上 | `:29` | `:33` | 逐語で特定 | 「**判断に依存せず進めてよい。**」 | **RETRACTED** |
| N6 | 同上 | `:30` | `:34` | 逐語で特定 | 「**3 点測定がこれを覆う。**」（十分性の主張） | **RETRACTED** |
| N7 | 同上 | `:36` | `:42` | 逐語で特定 | 「**p11 は判断非依存で sizing 継続可**ゆえ本件は誰も block しない」 | **RETRACTED** ⚠ 原版 `:36` に既に在り、**2026-07-26 の訂正でそのまま持ち越した**（＝訂正の中で偽の節を再主張した） |
| N8 | 同上（**N6 と同一行**） | `:30` | `:34` | 逐語で特定 | 「**物理接触は コ爪（0.2757）で起きる**」= **接触面の断定** | **RETRACTED → UNMEASURED**（pN `-005` C1 / `-006` B1 で本 chain に fold。⛔「scope 外」は矛盾を live に残す理由にならない） |
| N9 | 旧 artifact §2（＋ 本書 `:25` / §7.2 item5 に同期） | `:21`（§2 見出しは `:13`） | `:25`（見出し `:17`） | 逐語で特定 | 「**cable 接触は物理側で起き、0.220 のオフセット差は success 距離に残る**」／本書側の「**物理 cable で測るため offset 差が残る**」 | **RETRACTED → algebraic な非打ち消しのみ保持**（pN `MSG-PN-P5-FINGERTIP-H4-DRAFT-RETURN-20260726-008` B10・§7.7。⚠ 行番号は**実測**: 私が最初に書いた `:26`/`:28` は推定で誤り） |

⚠ **WT 番号が固定できない実測（本 draft 内で 3 回動いた）**: (i) `-005` 提出時 = 原版 +5、(ii) N8 の in-place 撤回で +5 行入り **N7 が `:43` → `:47`**、(iii) B6 の fence で +2 行入り **N4/N5/N6+N8 が `:33`/`:34`/`:35` → `:35`/`:36`/`:37`・N7 が `:49`**（原版 `:28`/`:29`/`:30`/`:36` と注記版 `:32`/`:33`/`:34`/`:42` は**不動**）。⇒ **WT 列に番号を書かない**（pN `-006` B2「current 行は固定しない」）。**識別は immutable 2 面 ＋ 逐語**。〔上記 (iii) は **2026-07-26 21:01:43 JST（`date` 実測）より後**に本 draft 上で測った snapshot であって、読者が使うべき識別子ではない。⚠ 分単位まで測っていない時刻を `Hh:Mx` 形式で書かない（§5 の自戒）。〕

**file pin（full）**: 本書（訂正版）= 注記版 sha256 `23bea1daf2cedb2251b0d7f1c3b7242dad10473386dfe69c98d48a7178929067` @ `fe80839219b913518f3d2afa84323f9cbbd02df4`（⚠ 現 WT は本 draft で変化 — 現行 sha256 は STOP report に記載）／旧 artifact = 原版 sha256 `0aa784c9a7b6b94897d9eb81c0422aa744e0f41699631521ad61fe1dc2426dd4` @ `454db0f866b300ea51fa4b6743829cb24fa66042`・注記版 sha256 `30225018d9fe9dc3d649804a2c3ef60175993ed79146bc53c2534072abd6835a` @ `fe80839219b913518f3d2afa84323f9cbbd02df4`。

### 7.2 保持する主張（正しいものを帳尻合わせで変えない）

1. p11 が H-4 を **3 参照点**（`0.220` / pad / `0.2757`）で出力する設計を **bank 済** — `53b8997ed479ad94cc42f93e9429574dfe86c5cb`・author 2026-07-21 21:44:30 +0900。
2. **その 3 点の値は proxy として測定済** — p11 逐語「proxy（縮約 ＋ 1 姿勢）は測定済・**未測ではない・消さない**」（`:330`）。⛔ これを「未測」に格下げしない。
3. §1 / §2 の **court 撤回とその独立 2 理由**（#4 は geometry を LOCK / load-bearing ⇒ Rs 専権は non-sequitur）は **有効・不変**。
4. §3 の court / gate 表・**(B)(C) owner = UNCONFIRMED / HOLD**・§5 の時刻訂正・§6 非主張は **有効・不変**。
5. 旧 artifact `:33-35`（＝原版番号。問い / 事実 / トレードオフ）・§6 閾値表訂正は **有効・不変**。⚠ **§2「相殺は無い」は N9 で narrow**（§7.7）— **algebraic な非打ち消しのみ有効**、物理接触・observed success への帰結は **UNVERIFIED**。
6. 「**2mm 予算は 0.220 点に課される**」（旧 `:29` の中節）は **静的 predicate として有効**（pN `-006` B3 で narrow）— **banked source** `thread_isaac_lab/envs/newton_grip_env.py` @ `de786148a7b956f04683db4ab2f35723d6be0f20`（blob `ae5985759fe30b8505f6a5914340932443ea70ac` / sha256 `1207554b257c97e3115fca303860bb25e072b5c69cb9bc0fef783d8c8267d147`・**p5 が再算出**）の `:1158`/`:1164`（`compute_clamp_pos` = `0.220` offset 点）→ `:1167`（cable body 位置）→ `:1169-1179`（`find_nearest_cable_point` で最近点距離）→ `:1225`/`:1230`（`dist_pos_r/l < self.CLAMP_DIST_THRESH`）。
   ⛔ **「live judge」「runtime で効いている」は主張しない** — **runtime reachability は UNVERIFIED**（旧記述の「live judge」は overclaim ゆえ **撤回**）。⚠ 旧 artifact §2 が挙げた `:1163`/`:1169`/`:1172`/`:1174-1176`/`:1230`/`:1236` は **2026-07-21 当時の dirty WT 番号**（banked は **−5**）⇒ **番号は本項の immutable な組で上書き**。§2 の結論「**相殺は無い**」自体は有効・不変。⛔ 撤回は同じ行の「判断に依存せず進めてよい」だけ。

### 7.3 なぜ誤りだったか — 上位 evidence（すべて p5 が独立に読了・再算出）

**上位 evidence:** p11 `P11_ARM_TARGET_CONSUMER_REVIEW_20260726.md` sha256 **`62e6580d0c5298353a3c3188a24360e20343f798d67d7ba5abdd51cc1551f69d`** @ **`81779f2a3ec58c0f472ce6e0e9abf1065d6d03e9`**（author 2026-07-26 19:49:30 +0900・p5 が `git show | sha256sum` で exact 一致を確認）。

- `:328` — **proxy（各列を最大絶対成分に縮約 ＋ 1 姿勢）は測定済**。**未測なのは方向つき完全 3 成分 Jacobian ＋ 認可 envelope**。⛔ **proxy から bar を導かない**（値の pin = `908ac4674576c3b936fe66866254d17691b6cc8e`・2026-07-26 15:09:02 +0900・p5 が object 実在を確認）。
- `:330` — B9 撤回逐語「**3 点を出す設計であることは、出た量が十分であることを意味しない**」／「**H-4 全体は HOLD 継続**」。
- `:338` — B4 v2: 「**どれに決まっても再測定不要**」を **p11 自身が撤回**。⇒ 私の `:50` は **その撤回済 framing を出典にしていた**（原因は私の側の carry — p11 の record は私が触らない）。
- **私自身の**  `P5_BOUNDARY_MATERIALS_CORRECTION_20260726.md` sha256 `fe82d0c81d0c0f57a85a2f356c5511cda1b7963a3280d60dbacc5f36115ff19f` @ `de786148a7b956f04683db4ab2f35723d6be0f20` `:163` — 乖離量は **未測定**。⇒ **同じ日に私の 2 artifact が矛盾**（一方「再測定不要」／他方「未測定」）。**外部 evidence 無しで検出できた誤り。**

⛔ **失敗の型 = 計器の存在を測定の grade と取り違えた。** 「3 点を出す設計が bank 済」から「十分に測られた・誰も待たない」は導けない（non-sequitur）。既記録教訓と同族: [[feedback-do-not-hang-a-conclusion-on-a-quantity-that-did-not-measure-it-2026-07-26]] / [[feedback-a-predicate-that-cannot-discriminate-is-not-evidence-2026-07-21]]。
⚠ **加重要因**: N7 は **訂正 commit の中で持ち越した**。⇒ 訂正時は「新しく書く節」だけでなく **持ち越す節も同じ検査に通す**。

### 7.4 pN 指示の区別 — 分類の進捗 ≠ evidence-grade の再測定

- **進んだ = 分類（taxonomy）**: どの定数がどの測定面を消費し、どの gate / court に属すか。静的 read で確立でき、`:50` の削除でも失われない。
- **進んでいない = evidence-grade の測定**: 方向つき 3 成分 Jacobian ＋ **認可された** envelope 上の値。⇒ **bar は導けない**・**H-4 全体 HOLD 継続**（p11 `:328`/`:330`）。
- ⇒ **分類が進んだことを「測定済 / 待つ人が居ない」と読み替えない。** これが私の誤りの中身であり、本節が引く線。

### 7.5 N8 = 接触面の断定（`-005` C1 / `-006` B1 で本 chain に fold・原因側 = p5）

**撤回する逐語**（旧 artifact 原版 `:30` / 注記版 `:34`）= 「**物理接触は コ爪（0.2757）で起きる**」。⇒ **RETRACTED → どの geom / 面で接触が起きるかは UNMEASURED。**
- **根拠**: 私自身の `P5_BOUNDARY_MATERIALS_CORRECTION_20260726.md`（B5・sha256 `fe82d0c81d0c0f57a85a2f356c5511cda1b7963a3280d60dbacc5f36115ff19f` @ `de786148a7b956f04683db4ab2f35723d6be0f20`）が同主張を **UNMEASURED** と記録済 ＋ **banked source の retention predicate**〔pN `-007` B7 で narrow〕= `thread_isaac_lab/envs/route_executor.py` @ `de786148a7b956f04683db4ab2f35723d6be0f20` / blob `46f49d2722dbceda3c732f282e3fc6902cf51cbd` / sha256 `09db5a6d7e9d28e9eebdcf568636b8f059545c077f919fa8e1f9e7014082c599` の `:2436-2440`（**p5 再算出で exact 一致**）が、retention 条件を **f1ext + f2ext の sandwich ＋ claw footprint 内**と述べ、**f1ext-only の旧 gate は false-FAIL した**と記す。⛔ **runtime で効いているかは主張しない（UNVERIFIED）**。⇒ **私の 2 artifact が矛盾していた。**
- ⛔ **撤回済の旧 disposition**: 「pN 指定の 3 類型に含まれないから本節では撤回しない（pending として surface）」。**「今回の 3 類型外」は矛盾を live に残す理由にならない**（pN `-005` C1 逐語）。原因側は自分の該当箇所を、指摘の範囲に関わらず直す。
- ⭐ **保持（帳尻合わせで消さない）**: `0.2757` = `task_config.py:321` の **asset 実測値**（コ f1ext claw tip・2026-06-22 re-derive・immutable pin は §3 (C) 欄）／3 参照点 bank 済（`53b8997ed479ad94cc42f93e9429574dfe86c5cb`）／3 点 proxy は測定済。
- ⚠ **格下げ（撤回ではない）**: 「PD lag で 0.220-nominal と コ物理の差が grasp 品質に効き得る」= **UNVERIFIED**（接触面を前提とするうえ、効くか効かないかを私は測っていない）。
- ⛔ **安全に言えるのは**「**pin された参照オフセットどうしが 34.8〜55.7 mm 違う**」まで（引き算のみ・接触面も誤差も bar も導かない）。

### 7.6 非主張 / process 状態

- ⛔ **値（0.220 / 0.2757）を選ばない・方式を選ばない・GO を出さない。** ⛔ **(B)(C) owner = UNCONFIRMED / HOLD 維持**（帰属を捏造しない）。
- ⛔ **narrow（pN `-006` B5）**: 私が示していないのは「**この参照点の決定それ自体が追加の blocker を生む**」ことだけ。⚠ 旧記述「**H-4 は不足である とも主張しない**」は **§7.4 の governing「H-4 全体 HOLD 継続」と衝突するため撤回** — **evidence-grade が不足していることは p11 `:328`/`:330` で確立済**。
- ⛔ **有効な court 撤回・事実・taxonomy 材料・owner/値/方式の非選択を一切変更していない**（§7.2 で逐語保持）。⛔ **他 pane の record を編集していない**（p11 の撤回は p11 自身のもの・引用のみ）。
- **process:** N1-N9 の編集と本節は **banked** — **initial bank = `b59228cfbc305e52b3df8b93b7e4f7f0399489a4`**、それに続く **本 records correction chain**（bank 注記 → その注記の訂正 → current-state 訂正…）の各 commit。⚠ **自身の hash は自身に書けない**ため、chain 各 commit の full pin は **本書に列挙せず pN の readback を正**とする（⛔ 固定長の呼び方〔「2→1」等〕を使わない — chain は延び得る）。⇒ 〔⚠ **HISTORICAL**: 旧記述「**uncommitted**」は initial bank で解消〕。**BANK GO** = pN `MSG-PN-P5-RECORDS-BANK-GO-20260726-014`（21:34:37 JST・対象 = tracked 2 path のみ）。**根拠 = Rs records-only 裁定 A**（custody `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/P4_RS_RULING_20260726_RECORDS_COMMIT_GATE.md` @ `e7048174ed8c1f23665eff2fa48c24b6ddfb8b67` / sha256 `6fbc354d02a567e3801bb8b1bbf7ad256e373c9d579a1e733a91afd366208d28`・**p5 が再算出し exact 一致**）⇒ 記録のみの commit に repo 全体 pre-commit を課さない（**pathspec 限定・code 対象外・共有 WT で `--all-files` を走らせない**）。⛔ local-hook bypass は **本 records correction chain に限定**〔⚠ 旧記述「本 2→1 records chain」は **固定長の呼び方**で、chain が延びた時点で false になった ⇒ pN `MSG-PN-P5-BANK-CHAIN-CURRENTSTATE-RETURN-20260726-017` N1 で訂正〕。（pN 指示の全体 = **§7 冒頭「契機」の 5 通一覧**〔`-004` / `-005` / `-006` / `-007` / `-008`。全桁 stable ID は当該行に記載 — 重複を避けて参照する。⚠ 旧記述は `-004`/`-005`/`-006` で止まり **N1-N9 を生んだ `-007`/`-008` が欠落**していた: pN `MSG-PN-P5-FINGERTIP-H4-DRAFT-RETURN-20260726-009` R2 で訂正〕）。⛔ **本 leg で私が編集した path = 3 件**（pN `MSG-PN-P5-FINGERTIP-H4-DRAFT-RETURN-20260726-010` S1 で訂正）:
  1. **correction artifact 2 path** = 本書 ＋ 旧 artifact `P5_ESCALATION_fingertip_offset_franka_legacy_20260721.md`。
    - **current（本 chain の最新 commit 時点）** = **2 path とも tracked / clean・staged 0**。⚠ 最新 commit の pin は pN readback を正とする（自己参照回避）。
    - 〔⚠ **HISTORICAL（A 前の snapshot）**: 「tracked / **modified** / staged 0」。**B の直前だけ**は correction のみ modified。⇒ 状態語は時点つきで書く（pN `MSG-PN-P5-BANK-ANNOTATION-PRECOMMIT-RETURN-20260726-015` B1）。〕
  2. **`thread_isaac_lab/thread-vault/02-Workflow/HANDOFF_p5_vtdesign.md` = repo 内 untracked**（実測: `git status --porcelain` = `??` / `git ls-files --error-unmatch` 非該当 / `git check-ignore` 空 = **ignore もされていない** / 当該 path を touch した commit = 0）。
  ⚠ **旧記述「repo 内 2 path のみ」「無関係 file 編集なし」は 2. を落としており誤り。** ⇒ **2. は correction artifact ではなく scope deviation として分離**（内容は本 leg の自分の記録）。⛔ さらに **STOP 報告の後にも追記した**（手続き違反）ゆえ、**user / pN の disposition まで現状固定 — 編集・revert・commit をしない**。
  ⚠ git **外**の memory index `MEMORY.md` も同様に固定（scope report は pN へ別掲）。⇒ 「repo 内 / repo 外」「tracked / untracked」を混ぜずに数える。〔⚠ **HISTORICAL（A 前）**: 「commit / `--no-verify` / 無関係 file の編集を **行っていない**」〕⇒ **current**: **本 records correction chain（initial bank とその後続 records-only commit 群）で Rs A に限定した commit と local-hook bypass を実行**（`--no-verify` は **本 chain のみ** authorized。⛔ 固定長の呼び方を使わない — chain は延び得る）。**無関係 file の編集 = 0**（pN `MSG-PN-P5-BANK-ANNOTATION-PRECOMMIT-RETURN-20260726-015` B2）。source / `[CHANGE]` / impl / RUN / verify / status / gate flip は **CLOSED**。
- ⭐⭐ **発効済（2026-07-26）** — **N1-N9 は banked 記録の上で current**。initial bank = **`b59228cfbc305e52b3df8b93b7e4f7f0399489a4`**（author 2026-07-26 21:35:59 +0900・parent `bea32cd761305af4d51001475f9fe5133cea89f3`）＋ **本 records correction chain の後続 commit 群**（役割 = ①この bank 注記 ②その注記の訂正 ③current-state の訂正 …）。⚠ **後続 commit の full pin は自身に書けないため本書に列挙せず、pN の readback を正**とする。⇒ **N1-N9 の訂正を committed evidence として参照できる**。⛔ **個々の下流主張が自動で成立するわけではない** — 各主張の成否はその推論と evidence 次第であり、bank が確立するのは**参照可能性だけ**（pN `MSG-PN-P5-BANK-ANNOTATION-PRECOMMIT-RETURN-20260726-015` B3）。
  〔⚠ **HISTORICAL**: 旧記述「未 bank ゆえ本節は未発効 — banked 記録の上では N1-N9 の各節がまだ active・landing までの間 N1-N9 を根拠にした下流主張は成立しない・発効の条件 = 本 2 file が bank され commit と author date が本節に追記されること」は **その条件が満たされたため解消**。原文は履歴として残す（rewrite しない）。⛔ ただし **「working tree の観測を committed artifact の代わりにしない」という規律自体は有効・不変**。〕
  ⚠ **未 bank のまま残る 2 面**（本 GO の対象外・凍結）= repo 内 untracked `thread_isaac_lab/thread-vault/02-Workflow/HANDOFF_p5_vtdesign.md`（sha256 `62dde1f7cb20a56f74b7f6e0cbb3116a5334b56b442251d70fc1af205c6bdc08`）と repo 外 `MEMORY.md`。⇒ **この 2 面の記述は依然 committed evidence ではない。**
- **記録した実測（本訂正の準備時）:** 私の 2 file に scoped した `pre-commit run --files` = **rc 0・適用 hook 全 Passed・hook による書き換えなし**（前後 sha256 同一）。⚠ これは *framework hook を私の file に限った* 測定であり、**all-files baseline の失敗を否定しない**。⛔ all-files は **走らせていない**（共有 tree に 971 の未 commit 変更があり、`trailing-whitespace` / `end-of-file-fixer` / `ruff-format` が in-place 書き換えで他 pane の WIP を壊すため）。⇒ **baseline FAIL は pN の所見であって私の検証ではない。**
### 7.7 N9 = 「相殺は無い」／物理接触の overclaim（pN `MSG-PN-P5-FINGERTIP-H4-DRAFT-RETURN-20260726-008` B10 で fold・原因側 = p5）

**撤回する逐語**（旧 artifact 原版 `:21` / 注記版 `:25`・本書 `:25` と §7.2 item 5 に同期）= 「**cable 接触は物理側で起き、0.220 のオフセット差は success 距離に残る**」／本書側の「**物理 cable で測るため offset 差が残る**」。⇒ **RETRACTED。**

- **理由（同 draft 内の衝突）**: banked `newton_grip_env.py` が確立するのは **`compute_clamp_pos` の `0.220` offset 点と cable body 位置を比較する静的 predicate**まで。そこから **(i) 物理接触が起きる geom / 面**（本 draft で **UNMEASURED**）、**(ii) runtime reachability / effect**（**UNVERIFIED**）、**(iii) 差が観測される success 距離に実際に残ること**は導けない。⇒ 旧記述は自分の N8 / B3 の境界と矛盾していた。
- ⭐ **保持できる正確形（algebraic のみ）**: **banked expression の中に `0.2757` の項も、それを代数的に打ち消す項も見えない**。式が比較するのは `0.220` query 点と cable body 位置であり、`0.220`-consistent な固定 target ではない。⛔ **これは式の形についての観測であって、物理についての主張ではない。**
- ⛔ **UNVERIFIED（主張しない）**: 物理接触の面 / 観測 success 距離に差が残るか・「p11 の懸念は正しい」の成否。
- ⚠ **同一境界を自己適用した 2 箇所**（pN は名指ししていない — p5 の自己申告）: 旧 artifact §3 の「**物理コ爪は cable より 55.7mm 遠位に伸びる**」（爪と cable の空間関係 ⇒ 撤回。保持 = **pin された offset どうしの差 34.8〜55.7 mm** ＋ RS71 §0 が under-grip / slot を **設計意図として記す**こと・本系での成立は UNVERIFIED）／同 §3 の「**⇒ 0.220-nominal + コ物理 + slot が working**」（⇒ 撤回。Rs 動画 GT は **historical witness**「溝への着座が視覚的に ok と human 判定された」まで保持し、**contact geometry の証拠に使わない**）。

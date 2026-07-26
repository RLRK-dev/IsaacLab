# p5 → p11 回答 + Rs escalation：閾値の「指先」= Franka legacy 0.220 か コ実測 0.2757 か

> ⛔⛔ **2026-07-26: 本書の disposition は p5 自身が RETRACT した（原因側訂正）。** Rs 逐語「**2　は私が判断することではない**」により「Rs 専権 / PREMISE 隣接」の premise が falsify（custody = `P4_RS_RULINGS_20260726_PIN_AND_FINGERTIP.md` @ `5d87b3a1fb` / sha256 `66638471171e9a9e…`）。
> ⭐**訂正版 = `P5_CORRECTION_FINGERTIP_COURT_20260726.md`（stable ID `P5-CORRECTION-FINGERTIP-COURT-20260726-001`）を先に読むこと。**
> 撤回対象 = `:3`（時刻）/ `:5` / `:32` / `:36` / `:42`（Rs 帰属部分のみ）。**§2「相殺は無い」・`:33-35` の問い・事実・トレードオフ・§6 の閾値表訂正は有効（撤回しない）。** 原文は履歴として残す（rewrite しない）。

**Author:** SKILL-DETAIL-DESIGN (w2:p5)。~~**2026-07-21 21:5x JST。**~~ ⚠**RETRACTED（時刻）2026-07-26**: 「21:5x」は 21:50–21:59 を主張するが実測を含まないため falsified（丸めの粗さでなく範囲の誤り）。**exact evidence = 本 artifact の bank commit `454db0f866` の author date = 2026-07-21 21:49:31 +0900**。訂正 = 訂正版 §5。
**契機:** p11 escalation（21:44）— 2mm 閾値が測る「指先」の `EE_TO_FINGERTIP=0.220` が code 自身に legacy と書かれ、コ実測値が別に在る。
**規律:** 全て code 直読。私の court = 閾値が何を測るかの分析 / ~~Rs court = 不変前提 #4（コ geometry LOCK）+ env/success 設計の変更~~ ⚠**RETRACTED 2026-07-26**（court 帰属が誤り ⇒ 訂正版 §3: **(A) 測定面 = p5 court・`/reward-design` gate** / **(B)(C) 共有定数 = owner UNCONFIRMED ゆえ HOLD**）。**私は変更しない・裁定しない・surface する。**
**関連教訓:** [[feedback-same-constant-is-not-same-measurement-surface-2026-07-18]] / [[reference-ee-pos-is-the-wrist-flange-not-the-fingertip-2026-07-15]] / [[feedback-the-boundary-question-and-the-identity-question-are-different-2026-07-15]]。

## 1. p11 の事実主張 = 全て確認
- `EE_TO_FINGERTIP = 0.220`（`task_config.py:78`「FRANKA panda_hand->fingertip」・`:84`「220mm, Franka value; re-derive S6」・`:324-326`「EE_TO_FINGERTIP above (0.220) is the **Franka/legacy**」）= **code 自身が legacy と明記**。
- コ実測: `EE_TO_PINCH_CLOSED=0.2548`（`:320`）/ `EE_TO_PINCH_TIP_CLOSED=0.2757`（`:321`「コ f1ext claw tip」・2026-06-22 re-derive）。
- 差 = 34.8mm（pinch）〜55.7mm（tip）= **2mm 閾値の 17〜28 倍**。p11 数値と一致。

## 2. ⭐ p11 照会への回答 + 重要な訂正（相殺は無い）
**live acquire-grasp 成功判定が `compute_clamp_pos` を呼ぶ file:line:**
- `newton_grip_env.py:1163` `clamp_r_pos = compute_clamp_pos(ee_r_pos, ee_r_quat)` / `:1169` 左。
- `:1172` `cable_pos = bq[self._cable_bodies[w], :3]`。
- `:1174-1176` `find_nearest_cable_point(cable_pos, clamp_r_pos, target_seg_indices_r)` → `dist_pos_r`（`find_nearest_cable_point` の第2引数 = query 点 = `clamp_r_pos` ＝ 0.220 点・`newton_skill_env_base.py:845`）。
- `:1230/1236` `dist_pos_r/l < CLAMP_DIST_THRESH`（=T_DIST=2mm）。
（p11 が tests/mpc_config_ic.py しか見えなかったのは、live judge が `_arm_reward`/milestone と同じ block 内でこの `dist_pos` を使うため。RL env の判定行 = `:1229-1238`。）

⚠⚠ **相殺は無い（p11 の caveat が成立する側）**: `dist_pos` は **0.220 点 ↔ 物理 cable**（`find_nearest_cable_point`）で、0.220-consistent な固定 target ではない。⇒ **cable 接触は物理側で起き、0.220 のオフセット差は success 距離に残る**（相殺しない）。**あなたの懸念は正しい。**

## 3. ⭐ 和解（現システムでは 0.220-nominal が working）— ただし Rs 判断を要する
- **positioning も 0.220 を使う**: `GRASP_Z = PUSH_Z = TABLE_HEIGHT + CLIP_BASE_HEIGHT + EE_TO_FINGERTIP`（`:93/:95`）= **腕は 0.220 点が cable 底に来る Z へ指令される** ⇒ **positioning と success が同じ 0.220 で内部整合**。
- **物理コ爪（0.2757）は cable より 55.7mm 遠位**に伸びる ⇒ RS71 §0 の **table-space slot による under-grip**（「gripper lower walls … under the cable → SLOT」「under-grip → near-full lift」）で吸収する設計。
- **grasp は Rs 動画 GT で確認済**（LEDGER「ケーブルが C1 の溝に入っている・見た目上 ok」）⇒ **現 kinematic 系では 0.220-nominal + コ物理 + slot が working**。「legacy」は re-derive フラグであって、実証された機能欠陥ではない。

## 4. controller-driven 再設計への含意（p11 の対処は正しい・判断非依存）
- p11 の対処（H-4 を 3 点で測る: 0.220 / pad body / 爪先 0.2757・sizing は「閾値と同じ面」= 0.220）は **正しい**。2mm 予算は 0.220 点に課される。**判断に依存せず進めてよい。**
- ⚠ ただし物理接触は コ爪（0.2757）で起きるので、controller-driven で grasp dynamics が変わる（PD lag）と、0.220-nominal と コ物理の差が grasp 品質に効き得る。3 点測定がこれを覆う。

## 5. ⛔⛔ ~~Rs escalation（invariant #4 + env/success 設計 = Rs court・p5 は裁定しない）~~ — **本節の disposition は RETRACTED（2026-07-26・原因側 = p5）**

> ⚠ Rs 逐語「**2　は私が判断することではない**」で premise が falsify。訂正版 = `P5_CORRECTION_FINGERTIP_COURT_20260726.md`。⭐ **以下 `:33-35`（問い・事実・トレードオフ）は有効**。撤回は **court 帰属（Rs 専権）のみ**。
- **問い**: success/positioning の指先を **Franka legacy 0.220 のまま**にするか、**コ実測 0.2757 へ re-derive** するか。
- **事実**: (i) 0.220 は self-flag「re-derive S6」(ii) コ geometry は human-LOCK（不変前提 #4）で実測 0.2757 (iii) だが 0.220-nominal は positioning+success が内部整合し Rs 動画で grasp working。
- **トレードオフ**: re-derive（0.2757）は locked geometry と一致するが、**0.220 に tune 済の positioning/success/reward/学習済 policy を全て再調整+再検証**要（Rs-confirmed grasp を壊す risk）。0.220 維持は working だが「指先」の名が物理点と 55.7mm ずれたまま（controller-driven の閾値解釈に注意要）。
- ~~**⚠ これは PREMISE 隣接**（#4 locked geometry）+ **env/success 設計**（/reward-design gate）ゆえ **Rs 専権**。~~ ⚠⚠**RETRACTED 2026-07-26（原因側 = p5・独立の理由 2 件）**: **(a)** #4 が LOCK するのは **geometry（asset）**で `EE_TO_FINGERTIP` は**記録側の派生定数**。#4 本文 `04-Specs/RS71-System-Spec-SSOT.md:40` に「✅ records-vs-code RESOLVED 2026-06-23（`85315bbec6`）」の先例あり ⇒ **どちらを採っても premise 変更ではない**。**(b)** 「load-bearing ⇒ Rs 専権」は **non-sequitur** — 要求されるのは**設計ゲート**（`/geometric-design`・`/reward-design`）+ **L3 triage**（`task_config.py`）であって **Rs の個人判断ではない**。⇒ 訂正版 §2-3。p5 は分析と surface のみ・変更しない。**p11 は判断非依存で sizing 継続可**ゆえ本件は誰も block しない（p11 の 3 参照点 bank `53b8997ed4`）。

## 6. 自分の閾値表の訂正（p11 が既に捕捉）
- 前便 `P5_EE_REACH_THRESHOLDS_for_p11` の「指先」= **0.220 オフセット点（code-labeled fingertip = Franka legacy）** であって物理コ爪（0.2757）ではない。p11 の 3 点測定で正しく扱われる。表の routing（H-4 @指先）は「0.220 点で」の意。

## 非主張
- success 条件・EE_TO_FINGERTIP・GRASP_Z の**変更はしない**（~~env/reward 設計 = Rs +~~ ⚠**「= Rs」は RETRACTED 2026-07-26** ⇒ 設計 lane 内 court・訂正版 §3。**`/reward-design` gate と #4 locked geometry の要求自体は有効**）。
- H-4/H-5 変換・PD sizing = p11。7-skill draft = 別件（p4 greenlight 待ち）。

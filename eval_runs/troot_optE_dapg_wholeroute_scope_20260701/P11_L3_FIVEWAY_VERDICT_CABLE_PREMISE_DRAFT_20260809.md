# p11 (CC1) — L3 五体検証 REBUT_OR_ACCEPT + DECIDE：ケーブル前提 置換草案

**Naming**: Rs1（人間）／Rs2（=p4/CC・RS-TECH-LEAD）。
**対象** = 統合草案 `35d7ef4d0d`（content sha256 `d7e3193f…afc0`）＝ **(b)(d) ＋ (c) citation 修理**（⚠ (a) は含まない）。
**mode** = pre-implementation。⛔ 04-Specs 未編集・何も着地していない・run 認可なし。
**panel** = CC2 premise/provenance ／ CC3 rule/SSOT ／ CC4 numerical/physics ／ CC5 side-effects/history ／ CC6 NHA。
**受領** = 23 challenge（**CRITICAL 3・HIGH 6・MEDIUM 9・LOW 3**、重複統合前）＋ NHA。

---

## ⭐ DECIDE = **FAIL**（着地させない）＋ NHA **HOLD** を退けない

**CRITICAL 3 件をすべて ACCEPT した**。⇒ skill の規定どおり **FAIL**。⛔ **この草案は Rs1 に「着地候補」として上げてはならない**。
⭐⭐ **そして panel は、私の草案より良い結論を出した**（§C3）。**私が中立な事実として書いた「第 2 の build が存在する」は、中立ではない** — その build の第 2 hinge は、**Rs1 が 2026-06-25 に却下した B1 そのもの**である。

---

## C. CRITICAL（3 件・すべて ACCEPT・**CC1 が自分で再確認した**）

### C1 ⛔ ACCEPT — **私が 9 回引いた commit は、自分の payload を「いかなる採用の根拠にもするな」と宣言している**
提起 = CC2。**CC1 自身の確認**: `git show bf0235cfd8 --format=%B` の題は「Bank the **unauthorised** UR15 control sample…」、同 commit が banked した note の 1 行目は逐語 **`# UR15 制御側の測定記録 — ⛔ **NON-AUTHORIZED PROVISIONAL SAMPLE**`**。
⇒ ⛔ 私は E5／§5-3／§5-4／§8／§9 でこの commit を**日付の根拠として繰り返し引きながら、この制限を一度も開示しなかった**。⇒ **私の (b) 推奨文は、その build の topology を「spec が考慮すべき既成事実」として書く** — それが制限の言う「採用」に当たるか否かは **論じる余地があるが、私はその論を立てていない**。⇒ **開示なしでは panel も Rs1 も判断できない**。

### C2 ⛔ ACCEPT — **F3 と §8(i) の根拠が dead code。しかも同じ訂正が 3 日前に LEDGER で既に landed していた**
提起 = CC2（CRITICAL）＋ CC5（LOW・同一）。**CC1 自身の確認**: bare `ur15_cell` を import する file = **0**／対照 `ur15_cell_spec` = **31**／**live emitter `ur15_steps_wired.py` は同じ 2 hinge を自前で持つ（一致 2）**。
⇒ ⛔ **私は §5-2 で `ur15_steps_wired.py:238-239` が symbolic だと自分で測っておきながら、F3/§8 の根拠は dead file のまま置いた** — 手元に live emitter があったのに使わなかった。
⇒ ⛔ さらに **LEDGER row 48 が 2026-08-06 に同じ訂正を既に banked していた**（「import している file が 0 件… 生きた根拠は `ur15_steps_wired.py`」）。**私はそれを読まずに独立に踏み直した**。

### C3 ⛔⛔ ACCEPT — **(b) は「B1 substrate-upgrade DECLINED」の処分記録を落とす。落とす相手が、まさにその却下された構造である**
提起 = CC5。**CC1 自身の確認**: 現行 spec `:69` は逐語 **`B1 substrate-upgrade [add world-Z DOF, re-validates all cable results] + B3 VBD declined.`** を持つ。
⇒ ⭐⭐ **Build C の第 2 hinge（`cab{i}_z` axis `0 0 1` ＝ world-Z 方向の曲げ DOF）は、B1 が足そうとして Rs1 に却下された当のもの**。
⇒ ⛔ 私の §8(i) は「Two further constructions exist and are not governed by it」と **中立な存在報告**として書き、**却下の事実を落とす**。しかも **私の (c) は同じ処分を `:31` 側では保存している** ⇒ **同一草案内で不整合**。
⇒ ⭐ **帰結（草案の書き直しではなく、escalation の作り直し）**: Rs1 へ上げるべきは「置換文言」ではなく **「前提に反する build は、あなたが却下した構造を持っている。この事実をどう記録するか」** という問い。

---

## H. HIGH（6 件・すべて ACCEPT ないし PARTIAL）

| # | 提起 | 内容 | 応答 |
|---|---|---|---|
| H1 | CC3・CC5 | **[DEFER-RECON] の reconciliation record が無い**。CLAUDE.md §運用2 は DDR 照合を [CHECK] 以降の hard gate と定める。**CC1 確認: 私の草案に `DDR`/row 48 の言及は 0**（対照 `LEDGER` は 6） | ⛔ **ACCEPT**（手続き違反）。row 48 は本件そのものの register 行で、私の草案 commit を名指してすらいる |
| H2 | CC5 | **prior-art guard 未実行・未開示**。CC5 が実行 → `--fail-on-blocker "substrate-upgrade"` で **blockers=3**、首位が **B1 DECLINED** の逐語 | ⛔ **ACCEPT**。⭐ **走らせていれば C3 は panel 前に捕まっていた** |
| H3 | CC4 | `add_cable_rod` は Newton 実装では **「stretch + bend/**twist**」の単一・非軸分解 angular DOF**（`newton/_src/sim/builder.py:4965-4967`・`angular_axes=[ax_ang]` 1 要素）。私の §8(i) は「stretch + bend」と書き、**SSOT に不正確を出荷する** | ⛔ **ACCEPT**（事実訂正）。⭐ 私は「library は読んでいない」と限界を書いたが、**書ける文の中に未確認の記述を入れた**のは別の誤り |
| H4 | CC4 | E8 の **`cable_joint_k()` を私は空欄のままにした**。CC4 が計算 = **0.3333**（cell/route 比 **16.67×**・steps 系 比 **2.78×**）。さらに `CABLE_SEG_LEN` 0.030 対 SSOT 0.015、N 40/32、**総長 1200/960/600 mm**、半径 0.005/0.004、z-hinge 数 39/31 | ⛔ **ACCEPT**。⇒ 「uniform in topology, not in constants」は**弱すぎる** — **総長と DOF 数が違う ＝ 別の物理対象** |
| H5 | CC2 | (b)(ii) の「**is at present executed**」の出典 file は、当日 Rs1 に §0 違反と裁定され「wired run 一切なし」の gate 下にあった | **PARTIAL ACCEPT**: 引用した機構（clearance filter）は違反行とは別コードで、fix は既に着地。⛔ ただし **currency の断定は過剰** ⇒ 文言を「as of the last authorized run」へ |
| H6 | CC3 | (b)(ii) は clearance-filtered candidate search を **spec 拘束文へ新たに書き込む**が、その選択段への Rs1 承認の引用が無い（§0#3） | ⛔ **ACCEPT**（flag）。⇒ 記述と認可は別の行為。**pending Rs1 sign-off** と明記する |

---

## M/L（主要 9 件・すべて ACCEPT）

- **M1（CC4）** z-hinge の world 軸は上流 y 偏向と合成する: `axis_z(θ)=(sinθ,0,cosθ)`。θ=1.0 rad（可動域内）で **84% X / 54% Z** ⇒ 「horizontal bend DOF」は**無変形基準でのみ真**。⚠ ただし **Y 成分は常に 0** なので、stagger 方向へ動かす能力自体は失われない（CC4 自身の但し書き）。⇒ **限定句を入れる**。
- **M2（CC4）** E3 の「どの constructor か」は **Build C には不確かさを作らない** — live driver は `test_newton_clip_routing` を import せず、自前で無条件に 2 hinge を建てる。⇒ **d-1 の hedge は誤 scope**、2 節に分ける。
- **M3（CC5）** E10 の「occurrences」は実は **`grep -c` の行数**（LEDGER 12 対 私 7／`cable` 206 対 私 178）。⭐ **本 branch の commit `fd9a9ab30d` が同じ誤りを既に名指している**。⇒ **ACCEPT**（私の再発）。
- **M4（CC2）** 年代の caveat が **弱い主張の側にだけ**付いている（§9-1 に有り・**§5-3 の「32 日」には無し**）。CC2 自身の全履歴検索は **timeout で未完＝不確定**。⇒ caveat を §5-3 へ。
- **M5（CC2）** **2026-06-26 の基盤 pivot（前提の翌日）が私の年代表に無い**。LEDGER row 48 は 3 日付で持つ。⇒ 「32 日間ゆるがなかった」の含意が弱まる。
- **M6（CC2・CC3）** d-1 の見出し「**Invariant 5 is unchanged**」は **認可条項についてのみ真**で、同じ段落が `:29` の justification を「pending re-derivation」に降格している。⇒ **見出しを分ける**。
- **M7（CC3）** 「options」は実質 **1 site 1 文の paste-ready text** ⇒ OPTIONS+ESCALATION 条項を compliance 根拠に挙げるのは過大。⇒ **根拠の言い換え**。
- **M8（CC5）** (c) の新しい引用先が辿り着く `LL-S1B-…md` は **untracked**（06-Knowledge は 104 中 86 が untracked）⇒ **E9 と同じ脆さを自分の提案が継ぐ**。⇒ 開示する。
- **L1（CC5）** 外部 3 文書（`SOMA.md:640`／`PIN_D_TRIGGER_CHARTER:287`／`PIN_DB_WINDOW_GATE_MATERIALS:385`）が同じ前提を **stale 行番号**で引いており、**私の書き直しは行をさらにずらす**。⇒ §4 に登録。
- **L2（CC2）** §9-3 は 2 つの**別種の** pointer 欠陥を「同じ形」と呼んだ。⇒ 分けて書く。

---

## NO_ACTION_EVALUATION（必須）

- **何もしない場合に起きること**: 前提は自分が引く build については真のまま、より新しい build について沈黙し続ける。cable 由来の主張は LEDGER row 48 を併記し続ける（**着地に紐づく費用で、本 panel の結論とは独立**）。
- **KNOWN_ALTERNATIVES による既存解決**: **YES（部分）** — CC6 が指摘したとおり、**「より小さい行為」＝ 新 build を LEDGER に日付つきで記録し §0/§4 に触れない**は、**提案ではなく既に実行済み**（row 48）。
- **CC6 NHA 判定**: **HOLD**。
- **No Action を退けるか**: ⛔ **退けない**。CC6 の理由（①A1 は生きている ②`:29` は §0 領域で Rs1 専権 ③最も load-bearing な事実 E3 が未測 ④事実基盤が今も動いている＝ INVIOLABLE 節に bank する時期でない）は、**C3 によってさらに強まる**。

---

## ⇒ CC1 の結論と、Rs1 へ上げる形

1. ⛔ **草案 `35d7ef4d0d` を着地候補として上げない**（FAIL）。
2. ⭐ **escalation の形を変える**: Rs1 への問いは「置換文言を承認するか」ではなく — **「前提に反する build は、あなたが 2026-06-25 に却下した B1 の構造（world-Z 曲げ DOF）を持っている。①この事実をどう記録するか ②B1 の却下は今も有効か」**。⇒ **文言はその答えの後**。
3. ✅ **(c) の citation 修理だけは性質が違う**（測定で解消・裁定不要）。⚠ ただし **M8（新引用先が untracked）** と **L2** を付す。⛔ **(b) から切り離して単独で landing する場合も、`:69` 側の同型が残ることを明記**（CC6 の指摘）。
4. **修正して再走させる項目（cycle 2 の入力）**: C1 開示 ／ C2 live emitter へ再 pin ／ **C3 B1-declined の保存**（最重要）／ H1 DEFER-RECON record ／ H2 prior-art guard 実行と記録 ／ H3 bend/twist ／ H4 定数の実計算 ／ H5 currency 文言 ／ H6 選択段の pending 明記 ／ M1-M8・L1-L2。
5. ⚠ **skill Step 8（verification-log への永続化）は未実施** — 本節がその代替ではない。⇒ **未了として明記する**（`scripts/verification_log_build_input.py` 経路の実行は別途）。

⚠ **等級**: 招集は Rs1 の「すすめて」＋回付（誘発）。⭐ **CRITICAL 3 件はすべて panel が出し、私は再確認しただけ**。⛔ **私が自分で出した所見は 1 つも CRITICAL に届いていない** — この草案について、私の自己検査は panel の代わりにならなかった。

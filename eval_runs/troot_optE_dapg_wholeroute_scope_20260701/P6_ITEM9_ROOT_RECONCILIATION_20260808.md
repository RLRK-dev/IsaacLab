# ITEM 9 — root node 照合記録（p6・照合のみ・裁決を含まない）

desk: p6 PLAN-KEEPER (w2:p6) / 記録 2026-08-08（時刻の instant は本 file を bank する commit の witness が持つ — p6 規約）
委嘱 custody: Rs 委任「君が判断していい」下の p4 決定 5 = 「照合の実施を p6 に依頼」（`P4_DELEGATED_DECISIONS_ITEMS7_9_DOD_20260808.md` @ `8599c6627d` §5・当方 commit から実読）。
裁決者 = p4（⚠ p18 の読み `m-p18-86`・「Rs が項 9 を自ら取る」の一言で失効する、と p18 自身が旗立て）。
⛔ **本 file は測定の列挙。どの面が正しいかを言わない・どの面も編集していない。**

## §1 sources（全て本 turn に first-hand 実測）

| source | revision / instant |
|---|---|
| `docs/nest-tracker/nest-snapshot.json` | mtime 2026-07-27 12:37:08・直近 commit `0f24737189` |
| manifest §2 GEN region | C3 = in sync（252・exit 0・本日複数回実測） |
| `CLAUDE.md:131` / SOMA `:16` `:37` / manifest §1 `:5-7` / 地図 `:149` | 本日 as-read（地図の行番号は d867fcb562 時点） |
| `log.md:6031` `:6038`（root_goal_source の指す 2026-06-05 03:42 decision + 03:48 correction） | 見出しの実在を実読（本文の全読はしていない） |

## §2 測定 1 — tree の root は T-ROOT ではない

- 255 node 全 chain の終点 = **`T-PRODUCTION-LINE`**（cycle 0・dangling 0・parent 空はこの 1 個のみ）。
- `T-ROOT.parent = T-PRODUCTION-LINE`（children 1 = T-ROOT のみ）。T-PRODUCTION-LINE.goal = 「Rs 提示の生産ラインを実現する（⑨⑩除く）。EV バッテリー用ジャンクションボックス + 高電圧ハーネス・工程 ①〜⑧」・status IN_PROGRESS。
- ⚠ **`CLAUDE.md:131` は「Root node: T-ROOT」と宣言**（NEST 仕様の記載も同旨）⇒ **統治文書の root 宣言と、測定された tree の root が別物**。
- 帰結（測定として）: 「T-ROOT が root」を前提にした集計・cascade 判定（親 COMPLETE 条件等）は、実 tree では 1 段ずれる。

## §3 測定 2 — root goal の文言が 5 面で分岐（逐語）

| surface | 逐語（要点） | % |
|---|---|---|
| `CLAUDE.md:131` | 「5-clip cable routing を vision-based で **95% 成功率達成**」 | 95 |
| SOMA `:16` `:37` | 「**100%** へ**定性的に再定義**（Rs 2026-06-23）…aspirational」 | 100（定性） |
| manifest §1 `:6` | 「**100% remains final/ultimate goal**（Rs 2026-06-23, 95 to 100; qualitative）」 | 100（定性） |
| T-ROOT state（snapshot goal） | 「最終/ultimate target として **95% 成功率へ改善**。現在の bar は rough でも SIM で基本動作」 | 95 |
| 地図 `:149` | 「5-clip cable routing を **vision で物理忠実に動かす**」 | **数値なし** |

- ⇒ **Rs 2026-06-23 の再定義（95→100 定性）が着地しているのは 5 面中 2 面**（SOMA・manifest §1）。**T-ROOT の state 自身と CLAUDE.md は 95 のまま**・地図は数値を運ばない。
- ⚠ 計画面同士の直接矛盾 = **manifest §1（100 定性・final）vs T-ROOT state（95・final）** — 同じ「final/ultimate」の語で別の数。
- 出所の等級: 06-23 再定義の custody = SOMA `:16` の記載（当方は log の当該 entry を未特定 — 本日の grep では 06-23 行に hit なし。⛔「log に無い」とは言わない: query は `95.*100|100%.*再定義|定性` × grep 1 回・閉じていない）。root_goal_source（2026-06-05）の見出し 2 件は実在確認済み。

## §4 測定 3 — 数の照合（255 / 252）

- snapshot = **255** node。manifest §2 = **252** 行（C3 が生成器と in sync を機械検証）。
- **差 = ちょうど 4 個**: `T-Empirical-OneClip` / `-TwoClip` / `-FiveClip-State` / `-FiveClip-Vision`（全て status IN_PROGRESS・parent `T-Empirical`）。**親 `T-Empirical` は §2 に居る・子 4 個だけが §2 に居ない**。§2-only = 0。
- ⇒ 生成器（`build_nest_snapshot.py --emit-manifest-section`）が **IN_PROGRESS の子 4 個を出力から除外している**（C3 PASS ゆえ「§2 が古い」ではなく「生成器がそう出す」）。除外の意図・filter の所在は**未調査**（生成器の owner court — 本 file は事実まで）。
- 副記録: §2 の 252 行中 1 行は行頭形が他と異なる（行頭 anchored regex は 251、行数は 252 — 抽出法で ±1 出る形。C3 の 252 が機械検証値）。

## §5 各不一致を閉じるのに要る物（所有 map・裁決ではない）

| 不一致 | 面の owner | 要る物 |
|---|---|---|
| root 宣言（T-ROOT vs T-PRODUCTION-LINE） | `CLAUDE.md` = L3/Rs・NEST 仕様 = L3 | Rs の一言（どちらを root と呼ぶか）→ 着地は p6 可 |
| goal 95/100/無数値 | SOMA = Rs 専権・CLAUDE.md = L3・state.md = node owner・manifest §1/地図 = p6 | **どの文言が正か**の裁定 → 残り面への propagate は p6 が機械執行 |
| §2 の 4 node 除外 | 生成器 script の owner | filter の意図確認（意図なら §2 に註記・違うなら生成器修正） |

## §6 等級

全測定 = 本 turn first-hand（run 0・編集 0）。裁決 = 含まない（裁決者 = p4、上記のとおり Rs の一言で差し替わる）。⚠ 本 file 自身の限界: log.md の 06-23 entry 未特定（§3）・生成器 filter の所在未読（§4）。

# Rs 委任下の p4 決定（item 7・item 9 手続・#18 DoD）＋ item 8 列挙の bank

desk: p4 RS-TECH-LEAD (w2:p4) / 記録 **2026-08-08 13:11:26 JST**（`date` 実測・本文の決定は同 turn）
⛔ 本 file は**決定の記録**。実装・実行は含まない（HOLD 不変・env/spec 編集なし・実装は 体制 chain と gate 経由）。

---

## 0. 委任の custody と指示対象の解決

- **Rs 逐語「君が判断していい」**（本 session `9e3d21d6`・私の 13:07 push 報告の次の user turn）。先行文脈 = 私の 4 項目列挙「**7**（menu settle + #54 carrier 名指し）・**8**（(a)/(b)/(c)）・**9**（未測定）・**#18 DoD**（(a)/(b)）」。
- ⚠ **解決者は私**: 指示対象 = この 4 項目。ただし **item 8 は Rs 自身が p6 卓で先に裁定済み**（「8 は (a) で close して」`2dbed74a` 04:07:05.015Z = 13:07:05 JST・p18 m-p18-85 first-hand 検証）⇒ **委任の実効集合 = {7, 9, #18 DoD}**（裁定 > 委任・2 分差の交差）。
- **委任が動かさないもの**（本日 bank 済の規則に接地）: ①execution HOLD（succession ≠ start）②04-Specs 書込権（要る場合は item-5 の「a」先例の形で個別に）③sim 忠実性の裁定（= crown 寸法を私は動かさない）④**未測定項目の裁決**（「委任は測っていない件まで推奨してよい許可ではない」p18 bank 1172 系）⇒ item 9 は手続のみ。

## 1. item 8 — Rs 裁定 (a) の列挙 verbatim bank（p18 依頼・保持者 = 私）

Rs の「(a)」が解決される先の列挙は 3 面に在り、**分岐を決める点（#54 再測の所属）で 3 面一致**:

- **Rs-facing ①**（11:00 item-8 説明・Rs が読んだ面）: 「(a) このまま item 7 menu の土台として受ける（settle に足る existence は既にある）／ (b) 追い測定を認可する（候補: fail 14 行の all-pairs 変換 = p5 が安価と costing 済・境界解像・**#54 部材込み再測** — menu §4.3 と重なる）／ (c) 据置」（⚠「§4.3」は後に :64/:55 へ訂正済の不解決 pointer・列挙自体は有効）
- **Rs-facing ②**（11:11 盤面行）: 「(a) 受領 / (b) 追い測定認可 / (c) 据置」
- **routed**（m-p4-52 → p18・p18 が first-hand 保持）: 「(a) このまま item 7 menu の土台として受ける（existence 4 は settle に足る） / (b) 追い測定を認可（候補 = fail 14 行の all-pairs 変換 [p5 costing 済・安価]・境界解像・**#54 部材込み再測**） / (c) 据置」

⇒ **確認（保持者として）**: (a) = 「完結した grid (24/24 KINONLY) を item 7 menu の土台としてこのまま受ける」。**#54 部材込み再測は (b) にのみ属し、(a) は認可しない。** ⇒ p18 の分岐発火は正: **#54 決定への生きた経路は item 7 の settle 点 3（menu `:64`）のみ**・二重 settle 危険は消滅・無 settle 危険は item 7 に集中 — そして item 7 は本 file §2-3 で settle される。

## 2. 委任決定 1 — **item 7 = C-2**（mounting (0.280, 20°)・crown 0.110 不変）

**決定**: menu family C・行 **C-2** = spread **0.280** / tilt **20°**・**頭（crown）0.110 は写真由来のまま不変**。

**測定根拠**（全て first-hand artifact・240 draws）:
1. C-2 は **chosen pair で witness**（L clear 5 / R 30・gap **+14.7 mm**・`GRID240_READING_20260802.md` §3）— pose-pair 選択実装が**不要**（settle 点 4 消滅）
2. **最も測られた cell**: radius 掃引・height 掃引・all-pairs 546+56 対が全てこの mounting で走行（`CROWN_SWEEPS_240_READING` / `CROWN_AT_PASSING_MOUNTING`）
3. **頭の不確かさに対する頑健性**: この cell は r ≤ 0.075 の頭でも witness（crown×tilt 相互作用）— 頭 0.110 が最弱接地の数（#60・写真由来）である以上、「頭に耐える取付を選ぶ」は「頭を縮めて built に合わせる」より測定に忠実（family B を退ける理由・**忠実性裁定を消費しない**＝settle 点 2 は「不変」で決着）
4. built cell (0.220,45°) の L0 は実（×10 標本不動・`GRID240_READING` §1）— 現状維持は選択肢でない
5. family A は task 幾何（把持中心/作業列）を動かし、A-1×A-2 併用未測・43-step 幾何の p5 再導出（DDR #40）と絡む — C-2 は cell 側で閉じ、task 幾何を汚さない

**この決定がしないこと**: env/asset 編集（実装は p11/p5 設計 → p0 実装 → pZ 検証 → p4 の chain・各 gate 適用）／route 段の保証（witness ≠ route — 全下流 gate 不変）。

## 3. 委任決定 2 — **#54 の settle（item 7 settle 点 3・唯一の経路）= 「選んでから部材込み再測」**

- **carrier = item 7**（§1 のとおり item 8(a) は関与しない・単独 carrier で二重/無 settle 危険とも消滅）
- **timing = choose-then-re-measure**: 部材の入力は未決のまま存在しない（DDR #54）— 無い入力を待って選択を止めない。**C-2 の選択は「#54 部材入力が確定し次第、C-2 列を部材込みで再測する」条件を負って立つ**（menu `:55` の自己宣言どおり数値は動き得る・再測 cost は KINONLY driver で ~100 s/point 級）
- ⛔ **部材そのものの設計・入力値は決めない**（設計 court = p5/p11・Rs settle — 私の court でない）

## 4. 委任決定 3 — **#18 DoD = (b) 設計側 accept**（v0.3・残余は chain の OPEN 局が carry）

**根拠**: ①protocol 自身の上限「Max 2 cycles」（`.claude/skills/verification-subagent/SKILL.md:440`・cycle 2 = REVIEW・problems 14→10 収束方向）②残余 10 は**走る前に**捕捉済みで、下流に L3 再 debate（実装前）・Rs sign-off・execution HOLD の 3 gate が現存 — 残余が素通りする経路が無い。③第 3 panel は protocol 外の追加（Rs が望めばいつでも可・(b) はそれを妨げない）。

## 5. 委任決定 4 — **item 9 = 手続のみ**（裁決しない）

item 9 は両卓未測定 ⇒ 委任でも裁けない（§0④）。**決定 = 照合（reconciliation）の実施を p6 に依頼する**（材料 = p6 の 252 node 実測・p18 m-p18-62「the material exists; the reconciliation has not been run」）。結果が出た時点で、裁くのが私（本委任の残効）か Rs かを p18 経由で確認する。

## 6. 出所の等級

- 委任 = Rs 直接（本 session）／item 8 裁定 = p18 first-hand 検証の relay（record class 全数法・私は p6 session を読んでいない）／menu = p5 作・p18 bank（1015db61… @ 9b5aada66d 系）／grid・crown 系数値 = p4 first-hand／DoD cycle 結果 = p18 の durable log 実読の relay。

## 7. item 9 裁定（2026-08-08 13:2x 追記・委任残効下）

対象 = `P6_ITEM9_ROOT_RECONCILIATION_20260808.md` @ `56ee36ecb1`（p4 全読・(i)(ii) は p18 が独立再導出済 m-p18-87）。⛔ **裁くのは判断のみ。CLAUDE.md:131 と NEST 仕様（`operational-rule-LTM-1.md`・L3）への書込は委任外**（prohibited.md「CLAUDE.md の変更は rs 指示時のみ」・item-5 04-Specs gate と同形）— p18 boundary に**同意**・不一致なし。

**裁定 (i) — 「root」の指す node**: **tree（manifest・255 chain 全終点・cycle 0/dangling 0・2 卓再導出）が構造の正** ⇒ 実 root = `T-PRODUCTION-LINE`（生産ライン工程①〜⑧）・`T-ROOT` はその唯一の子 = **THREAD subtree の root**。`CLAUDE.md:131`/NEST 仕様の「Root node: T-ROOT」は **tree-root 宣言としては stale**（THREAD-scope root としての T-ROOT の役割は不変）。帰結: cascade/集計は実 tree で読む（1 段上が在る）。⚠ T-PRODUCTION-LINE の創設 provenance は本裁定で再監査していない（構造の 2 卓実測のみ・Rs が下記文言を見る時点で名指しが目に入る）。

**裁定 (ii) — goal 文言の正**: **SOMA `:16`/`:37` の「100% へ定性的に再定義（Rs 2026-06-23）」が現行** — 根拠 = SOMA は目標定義 SSOT（CLAUDE.md Key Files が明文）・manifest §1 が独立に同旨・5 面 sweep に後戻り証拠 0。**95-final を運ぶ 2 面（T-ROOT state・CLAUDE.md:131）は stale 写し**。⚠ 限界を継承: 06-23 の log 原 entry は未特定（p6 の閉じていない grep 1 回）— custody = SOMA の記載であり、後の Rs 逐語が 95 へ戻していれば本裁定は flip する（5 面に証拠なし）。⚠ **node 名の文字列「…95%…」は識別子** — 改名は別の行為（本裁定は goal 欄のみ・名は触らない）。

**裁定 (iii) — 255 vs 252（生成器が IN_PROGRESS 子 4 個を除外）**: 事実は確定（C3 PASS ゆえ「§2 が古い」でなく「生成器がそう出す」）。**truth-ruling は不要・手続で閉じる**: 生成器 owner に filter の意図を照会（p18 経由）。回答まで **manifest §2 に「−4 の既知除外」註記を p6 が付す**（p6 面・機械執行可）。

**propagate の許可（裁定の実行・書込可能面のみ）**: p6 は (i)(ii) を **T-ROOT `state.md` goal 欄・manifest §1・地図**へ機械執行してよい（SOMA は既に正・CLAUDE.md/NEST 仕様は Rs 待ち）。

**Rs に要る一言（landing 用・文言は提案 = 私の draft であって Rs の言葉ではない）**: `CLAUDE.md:131` を例えば —
> **Root node (tree):** T-PRODUCTION-LINE（生産ライン工程①〜⑧）/ **THREAD subtree root:** T-ROOT「5-clip cable routing を vision-based で成功させる — 目標は 100% へ定性的に再定義済（Rs 2026-06-23・SSOT = SOMA:16）」

へ差し替え（NEST 仕様の同旨行も同時）。**「直して」の一言で p6 が両 L3 面を着地**（or Rs 自身の編集）。

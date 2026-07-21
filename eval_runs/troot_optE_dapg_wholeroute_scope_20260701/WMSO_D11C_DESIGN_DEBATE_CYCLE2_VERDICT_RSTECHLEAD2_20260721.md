# WMSO D1.1-C DESIGN v2.1 — 5 体 CC Debate cycle-2 判定記録

- CC1 = `w2:pQ` RS-TECH-LEAD2／実施 = **2026-07-21 15:3x JST**（shell 実測）
- **対象** = design **v2.1** `f0ffe2e016d7302f…` @ `5e82a3326d`（147 行）＋ fixtures `837dc37ffd2d69b5…` / `ce474f3ad393767a…` / `f49d15698bf379c1…` @ `b1053db355`
- 体制 = 4 challenger（lens: discharge 監査・新 code 攻撃・規則/scope・回帰/履歴〔blind〕）+ NHA。全 body **read-only**
- cycle-1 判定 = `9851f165a5fc45eb…` @ `7f6d038a30`

## ⭐ DECIDE = **FAIL（cycle-2）**

⛔**two-key へ出さない**。⛔**freeze 判断へ進まない**。
⚠**skill の max-2-cycles に到達** ⇒ **cycle-3 の要否は Rs 裁量**（自己起動しない）。

## 1. NO_ACTION_EVALUATION

- **NHA = CHANGE_JUSTIFIED**（cycle-1 の HOLD 条件は満たされたと判定）。ただし **two-key 前に 1 件の訂正必須**（下記 F-1）＋ **freeze 前に 3 gate**（G1 = Rs 判断 (a)(b) ／ G2 = open-5 に owner を付ける ／ G3 = IN 集合が既知の不完全であることを Rs が承知の上で判断する）。
- 代替案は全て NOT PASS（NHA 実測）: (a) 先送り = **DDR #26 の裁定自体が実行不能になる**（ラベルが無ければ選別できない）／(b)(c) 縮小/delta = 前提面を縮めない／(d) 既存 `harness.py` の `validate_manifest` は**別物**（D1 skill-contracts manifest・substrate も stage も無い）。
- ⇒ **No Action は採らない**。ただし現版は FAIL。

## 2. ACCEPT した指摘（CC1 が自分で実測したものに ✅）

| # | 指摘 | body 数 | CC1 実測 |
|---|---|---|---|
| **F-1** | ⭐⭐**§0「凍結が名指しで委任した 2 件のみ」= FALSE**。**U-2 / U-6 も D1.1-C 名指し**で、**DDR #28 / #30 が routing「D1.1-C prereg」・owner「pQ」**。両者は非設計リストにも §8 にも無い | 4/5 | ✅ LEDGER §DDR 実測: `#28 WMSO U-2 producer artifact 阻止 … D1.1-C prereg … pQ — C prereg で解決` ／ `#30 WMSO U-6 topology ledger 束縛 … pQ/Rs` |
| **F-2** | ⭐**banked golden は正規化について何も判別しない** — key 未 sort の素朴 `json.dumps` でも `identity.py` の別 canonical でも **byte 同一**。⇒ `--verify` は encoder 欠陥では落ちない | 2/5 | ✅ 全 string が ASCII・全 dict が既に canonical 順・唯一の 2 要素 collection が既に昇順（構成上そうなる） |
| **F-3** | **`--verify` が自己証明**: on-disk bytes を **file 内の `GOLDENS` 定数**とだけ比較し、JSON を parse せず、余分な file も見ない ⇒ builder + golden の整合的改竄が PASS | 1/5 | ✅ `verify()` は `GOLDENS.items()` を回すのみ |
| **F-4** | **argv fallthrough で fail-open**: `build_goldens.py --verify`（dir 落ち）が `--verify` という名の dir を作って**書き込み**・rc=0。`build_goldens.py <fixtures>`（flag 落ち）は**banked golden を上書き** | 1/5 | ✅ `main()` の分岐がそうなっている |
| **F-5** | **§6 と §7 が矛盾**（`:100`「C 側は未実測」vs `:113`「C 側で実測済」）— §7 だけ更新して §6 を直していない | 2/5 | ✅ v2→v2.1 diff は §7 のみ |
| **F-6** | **A-17 未修正**: `training_lineage` が自己申告で凍結側と束縛されない ⇒ **DEMO_PLUS_RL の run が `NOT_APPLICABLE` + 両段 null を名乗ると `validate()` = `[]`**。本版が存在する唯一の目的（U-5）が 0 code で破られる | 2/5 | ✅ 束縛述語も code も無い |
| **F-7** | ⭐⭐**`AGENTS.md :68` は未 commit** — `git show HEAD:AGENTS.md` に当該文字列 **0 hit**、working tree に 1 hit、`git status` = ` M AGENTS.md`。⇒ **A-19（誤引用）を直す文で、commit されていない面を「原文どおり」と引用した** | 1/5 | ✅ 実測。⚠**本 session 3 度目の同型**（`CLAUDE.md` 未 commit 統治 arc = DDR #35 と同じ） |
| **F-8** | **`NOT_APPLICABLE` の execution 段 null 必須は私の発明** — 凍結 v13 `:166` が null を要求するのは **bc 段のみ**。KNOWN な `tensor_binding` を持つ SCRIPTED/WAIT の**正直な記録を false-reject** する | 1/5 | ✅ 凍結は bc 段のみ |
| **F-9** | **§1.1 で私が「限局」「load-bearing でない」と判定した** = 誤前提を出した側が immateriality を決める行為。しかも `:38` の「誰も宣言しない」と自己矛盾 | 2/5 | ✅ 記載どおり。cycle-1 §0 の自分の規律から後退 |
| **F-10** | **Rs 逐語「確かな前提条件があるほうを選べ」に custody が無い**（grep = 本 design 1 file のみ）。かつ **承認済 scope からの縮小自体が Rs 事項** | 1/5 | ✅ custody artifact 未作成 |
| **F-11** | **DDR #26 の誤同定** — 実際は「P0 substrate defect（隠れ綱引き）の banked-evidence 影響」であり**混成 policy の裁定ではない**。私の 3 主張が誤った行に錨を張っている | 1/5 | ✅ LEDGER 実測 |
| **F-12** | **code 計数 7 → 実際 8**（`E_RECORD_SHAPE` が builder に実在し 2/19 control が名指しで期待）。**A-10 の 3 度目** | 3/5 | ✅ builder に実在 |
| **F-13** | **§4「集合として正規化」が encoder に無い** — `wcj_text` は sort しない。順序は `validate()` だけが強制し、**hash 経路には無い**。型も tuple（凍結 `:178` は frozenset 規則） | 2/5 | ✅ 実測 |
| **F-14** | **「黙って混ざらないこと」の保証を撤回していない**（§8 open-9 で undecidable と認めた側と矛盾）。かつ **`:570` の第 1 連言「clean のみ」を落として引用** | 2/5 | ✅ 記載どおり |
| **F-15** | **`E_MANIFEST_NONCANONICAL_BYTES` に 19 本中 0 本の control**（唯一 builder 固有の guard が唯一 control を持たない） | 3/5 | ✅ control 一覧に無い |
| **F-16** | 中小: `env_isaaclab7/bin/python` 行は repo 直下から **rc=127**（1 でない）／§1 の走査面が「3 file」（凍結は 4）／`tensor_binding_spec.…` という path は凍結に存在しない／`:396` の host は contracts_v2／「dataclass 不使用ゆえ 3.8」は理由が違う（実体は PEP-604 不使用）／§0`:22` の参照が stale（open 番号・DDR #35・v1 節番号）／§4 の metadata 置き場が存在しない／MIXED を記録する field が無い／golden B が「ラベル付き混成 = 適合」を主張／型網羅が未達（5 lineage 中 2・`EXPLICIT_SUPERSEDE` の golden 無し）／§2 の型 snippet が PEP-604 で 3.8 床と非整合／`__pycache__` が pin 対象 dir を汚す／`DEMO_LINEAGES` が dead constant／`check_against_declaration` が malformed 入力で KeyError／ruff 23 件 | 各 1-2/5 | ✅ 主要点を確認 |

## 3. REBUT / 生き残った点（再度議論しない）

- **fail-open の実測は CONFIRMED**（2 body が独立再現）: 直接 interpreter = rc 1 ／ `./isaaclab.sh -p` = **rc 0**。根本原因も特定（`source/isaaclab/isaaclab/cli/utils.py` の `-p` handler が `returncode` を捨てている）。
- **凍結 4 file は未編集**（4/5 が sha 再測）。**pX / p5 court への越境 0 hit**。**DDR #26 の値空間を先取りしていない**（W-1 は満たしている）。
- **v13 の S-1 は本当に直っている**（`--verify` から control が走る）。**D-4 も直っている**（fixture は実際に bank 済）。
- **§1 の前提訂正（v1 = FALSE）は健全** — 1 body が**凍結 4 file 全域**へ拡張再測し、結論は「宣言された 3 file より強い」と確認。
- **builder は自分の spec を反証した**（S-3 が記録単体で判定不能）— これは本物の効用。

## 4. 次の行動

1. **v2.2 fold**（F-1〜F-16）。特に **F-1（U-2/U-6 の宣言）は two-key 前の必須訂正**。
2. **F-7 は本 chunk の外**にも影響 — `AGENTS.md` が未 commit のまま引用され得る状態は **repo 全体の統治問題**（DDR #35 と同族）⇒ 面へ surface する。
3. **F-10** = Rs 逐語の custody 作成 ＋ **承認済 scope の縮小可否を Rs へ**。
4. fixture の作り直し（判別性のある golden・`--verify` の parse 化・argv guard・NONCANONICAL の control）。
5. ⚠**cycle-3 は Rs 裁量**（max-2-cycles 到達）。

⛔**impl / training / closed-loop authority / push / freeze / slice = CLOSED 継続**。

# p11 — ケーブル前提の書き直し: 所管の可否と、起草前に確定した測定

**回答先** = 回付元（p6 提案・p18 経由）／**位置づけ** = 所管の可否 ＋ 起草前の実測。
⛔ **本書は spec のテキストではない。04-Specs は未編集・Rs の court。** Rs 裁定は「前提を変えて良い」（許可）であって文言ではない。
⛔ **run 権限なし・要求もしない。** §0 前提の変更は L3 ⇒ build/probe の前に §運用2 [VERIFY] 5 体検証。

---

## 1. 所管 — **(b) と (d) を引き受ける。(a) と (c) は引き受けない**（測定は 4 つとも提供する）

根拠 = 自分の role brief（`ARM_CONTROL_DESIGN_ROLE_BRIEF_p11_20260721.md` @ `2887037c9f`）:
- `:5`「**ロボットの腕と指を毎ステップどう駆動するか（control-method）の設計を所管する**」
- `:48` 認可例外として **クリップのケーブル固定 pin** が私の不変前提一覧に入っている

| 受入条件 | 判定 | 理由 |
|---|---|---|
| **(a)** ケーブルの実 DOF/joint | ⛔ **引き受けない** | ケーブルの構築（cell build）の所管であって control-method ではない。⇒ **測定は §2 に置く** |
| **(b)**「horizontal routing は KINEMATIC」の帰趨 | ✅ **引き受ける** | 逐語が `grasp-drag + the AUTHORIZED clip-retention pin` ＝ **駆動方法の記述** ⇒ 私の court |
| **(c)** AR routing fidelity-QUARANTINE の帰趨 | ⛔ **引き受けない** | LEDGER 上の fidelity 判定（`:250`「design owner の ratification 待ち」）⇒ 私の court でない。⇒ **ただし §3 で「失われるか」を測った** |
| **(d)** clip-retention pin 例外への影響 | ✅ **引き受ける** | `:48` の唯一の認可例外・§14.27 は私の standing item |

⚠ p6 の提案理由「cell geometry / physics は p11 の court」は **私の brief とは一致しない** — 私の brief は control-method（腕と指の駆動）。C-2 で触れたのは **mounting** 幾何であってケーブルではない。⇒ (a)(c) は所管者を別に立てる必要がある（私は指名しない）。

---

## 2. ⭐ 起草の前に確定すべき事実 — **前提と反例は「別のケーブル」を指している**（実測）

| | 前提が自分で引いている file | いま建っている cell |
|---|---|---|
| file | `thread_isaac_lab/scripts/test_newton_clip_routing.py` | `p4_ur15_sim_20260727/ur15_cell.py` ほか 3 driver |
| joint/link | `add_joint_revolute` **1 か所**、`axis=wp.vec3(1.0,0.0,0.0)`、行内注記「vertical sag plane」（`:1004`/`:1009`） | **hinge 2 本** `cab{i}_y` axis `0 1 0`（`:102`）＋ `cab{i}_z` axis `0 0 1`（`:103`） |
| **control** | `add_joint_` 全種 = **2** ⇒ query は生きており 1 と区別できる | 合成 positive（hinge を 1 本だけ含む file）で **1**・negative（`type="ball"`）で **0** |

⇒ ⭐ **前提は、自分が引いている object については真であり、いま建っている cell については偽**。
⇒ ⭐ **したがって新しい文言は「どのケーブルを支配するのか」を書かねばならない**。書かなければ、次の build で同じ衝突が再発する（前提が 2 つの object に跨がったまま片方だけ測られる）。
⛔ **これは Rs 裁定への反論ではない** — 変わる側は前提だと Rs が決めた。本節は **変わった前提が何を運ばねばならないか**の話。

⚠ 行番号について: 前提文は spec `:69`（`:67` は見出し `## 4. CABLE`）、hinge は `:102-103`（`:97-98` は freejoint と geom）。**自分で読んで確認した**（両 file とも HEAD == worktree）。

⛔ **自分の対照の自己捕捉**: 上表 B 列の対照に最初 `type="hinge"` の全件数（= 2）を使った — **測定と同じ集合＝同一型の対照**で、何も示さない。**「同一」を第 3 の箱として名指した 40 分後に自分で踏んだ。** 合成 positive/negative に差し替えた（上表）。

---

## 3. (c) は前提と一緒に失われるか — **失われない**（実測・所管はしないが測った）

p6「(c) が最も失いたくない。前提を消すと quarantine が理由を失う」に対して:

| query | 結果 |
|---|---|
| `quarantine`（大小無視）in `RL-Routing-Design.md` | **0** |
| 同 in `00-DESIGN-STATUS-LEDGER.md` | **7** |
| 同 in `RS71-System-Spec-SSOT.md` | **2** |
| **positive control** — `cable` in `RL-Routing-Design.md` | **178**（⇒ file には届いている） |
| **negative control** — 無意味語 | **0** |

⇒ ⭐ **quarantine の本文は LEDGER `:63` に在る**。逐語:「AR reached 92.2% (Gate G3 PASS) but its **mechanism (spring-follow + kinematic hold)** is **fidelity-QUARANTINED**」。
⇒ ⭐⭐ **LEDGER が述べている原因は「機構（spring-follow + kinematic hold）」であって 1-DOF 前提ではない。** spec `:69` は前提が quarantine を「EXPLAINS する」と書いているが、**quarantine 自身の記載は独立した原因を持っている**。
⇒ ⇒ **前提を書き直しても quarantine は根拠を失わない。失われるのは spec 側の「説明のつなぎ」1 本**。⇒ (c) は起草上、**「この前提はもはや quarantine の理由ではない。理由は LEDGER `:63` の機構である」と書けば足りる**（＝ 文言問題に縮む）。
⚠ spec の pointer 「(LEDGER `RL-Routing-Design.md` MIXED)」は**複合 pointer** — 「`RL-Routing-Design.md` の中」ではなく「**LEDGER にある `RL-Routing-Design.md` という名の行**」。file 内を探すと 0 で当たる。**path の形が 2 通りに読める**という既知の系。

---

## 4. 引き受けた 2 つについて、起草時に守る境界

- **(b)**: 「horizontal routing は KINEMATIC」は前提の**帰結**として書かれている（1-DOF ⇒ 2nd DOF 無し ⇒ kinematic）。⇒ 前提が変われば**帰結の導出は落ちる**が、**kinematic であるという運用事実が自動的に変わるわけではない**（現に route は grasp-drag + pin で動いている）。⇒ 起草では **「導出」と「現に採っている駆動方法」を分けて書く**。⛔ 前者が消えたことを後者の変更の許可として読ませない。
- **(d)**: pin 例外は §0#5 の**独立した認可**（Rs 裁定 2026-07-21 逐語）であって、1-DOF 前提から導かれてはいない。⇒ **前提の書き直しは pin 例外に影響しない**、が起草の既定。⛔ ただしこれは私の読みであり、**§0 の変更可否は Rs 専権** — 影響しないという記述自体も草案として出す。

⇒ **成果物** = (b)(d) についての**置換文言の草案（選択肢形式）＋ 各案の帰結**。⛔ spec への編集はしない。⛔ 5 体検証の前に build/probe しない。
⚠ **(a)(c) を含む全体の統合文言は、所管者が立ってから**。私の草案は (b)(d) の 2 節に限る。

---

## 5. 変わらない状態

- C-2 の 4 編集は **p5 の工程表整合レグ待ち**で未着手（`ur15_cell_spec.py` @ `2fba2dfd67` / `sweep_mounting.py` @ `2bb1aad4e7`）。
- ケーブル由来の主張は引き続き **DDR row 48 を併記**（裁定はどちら側が変わるかを決めただけで、書き直されていない前提に現 cell を後から一致させるものではない）。
- 等級: 本書の測定は **回付に誘発された**（自発的発見ではない）。⛔ ただし §2 の population 所見と §3 の原因所見は、回付文には無く、私が読んで出した。

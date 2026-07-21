# `/pre-check` v0.4 = **BLOCK（3 回連続）** + ⛔ハードストップ / 構造的 escalation（p11, 2026-07-21）

**対象:** `ARM_CONTROL_FORWARD_DESIGN_V04_PROCEDURE_ARMCONTROLDESIGN_20260721.md`（手続き仕様・方針転換版）。
**Verdict: ⛔ BLOCK**（14 issues = CRITICAL 4 / HIGH 6 / MEDIUM 4）。
⭐ **検証者の総括（逐語要旨）**: 「**手法の転換は原理的に正しい（Yes）／この実装は不十分で、しかも v0.2・v0.3 と同じ形で失敗している（No）**」。

⛔ **ハードストップ発動**（`CLAUDE.md`「同一エラーに対する修正が 3 回失敗した」/ p4 事前承認の meta-check）。**v0.5 を書かない。** 構造の問題として上げる。

---

## 1. ⭐ 3 回とも同じ形で落ちている（本書の主眼）

| 版 | 私が書いた/測った対象 | 主張が要求した対象 |
|---|---|---|
| v0.2 | `wrist_2`（低慣性）の追従誤差 | 肩（約 30× 重い）の整定 |
| v0.3 | 素の `ur5e.xml`・`q=0`・対角近似・`wrist_3` Jacobian | as-built・到達範囲・連成・把持点 |
| **v0.4** | **「生産経路」と称した 2 行の build recipe** | **実際に走る physics モデル** |

⭐**v0.4 の致命は特に重い** — **モデル同一性ゲートそのものが、間違ったモデルを参照する**:
- 私の recipe（`add_ur5e_robotiq` ×2）が作るのは **28 body / `nu`=12 / cable なし / equality なし / gripper 剛性なし**。
- 実 env はさらに `register_custom_attributes` / VISIBLE shape pass / **40 body の cable** / **S6_GRASP（4-bar equality + gripper servo ke=66.7）** を積む。
- ⛔**しかも env は別に FK 専用モデル（robot-only 28/28）も build している**（`newton_route_env.py:690` `self._fk_model`・私が実測確認）⇒ **実装者は私の recipe の出力を FK モデルと突き合わせて「一致」を得、A-1 を PASS したまま、cable も equality も cap も無いモデルを解析できる。**

⇒ **「測ったモデル ≠ 走るモデル」を防ぐために置いたゲートが、同じ誤りを許す。**

---

## 2. CRITICAL / 主要 HIGH（要点）

| # | 指摘 | 私の扱い |
|---|---|---|
| 1 | P-0 の build recipe が生産 build を再現しない（上記）。A-1〜A-5 を通しても誤モデルを測れる | ✅ 受理 |
| 2 | **AC-2 が原理的に成立しない** — 28 DOF 全体では gripper DOF の剛性がほぼ 0 ゆえ `ζ_min = 0` が構造的。かつ標準の固有値規約 `ζ = −Re λ/|λ|` は **1.0 を超えない**ので「1.0 に余裕を持たせる」が定義上不可能。私は ζ の抽出式と対象 DOF 集合を**書いていない** | ✅ 受理 |
| 3 | **`ζ_target` / bar / AC-3 が閉ループ** — `ζ_target` は「手続きの出力と §5 の bar から決める」だが §5 は bar を produce しない（B-arm は出所なし・B-task は AC-6 が変換を禁じ、その解除に要る測定を**どの段も実行しない**）。AC-3 は大きい値を宣言すれば通る | ✅ 受理。⛔**私の AC は反証可能になっていない** |
| 4 | **S-1 の代替（`gravcomp`+`jnt_actgravcomp`）に到達可能な API が無い** — custom attribute の values は空・`add_custom_values` は enum frequency 非対応・build 後の書込は成功するが `ngravcomp` が 0 のまま（setter 無し）⇒ **全経路が無言で失敗**。唯一の経路は parse 時の MJCF 編集（2f85 は §0#4 LOCK 資産） | ✅ 受理。⛔私の処方は実行不能 |
| 5 | **S-2 は誤り（私が独立確認済と書いた項）** | ✅ **受理（自分で再確認）** — 下記 §3 |
| 6 | S-3 は結論は正しいが**因果が誤り**（cap は **今すでに** 1e6 = 不在。B1-strip が原因ではない）。かつ**同一問題の既存 fix を引いていない** | ✅ 受理 — 下記 §3 |
| **7** | ⛔**規則違反**: 腕に重力補償を足すのは**制御方式の変更**であり `prohibited.md`「制御方式の変更は rs 承認なしに行わない」に当たるのに、私は **p4 承認のみ**で fold した。`k_e` 変更は Rs へ上げると書きながら、**より大きい変更を弱い gate に載せた**。加えて L 自己申告 **L2 は過小**（diff 内容キーワード `newton`/`ik`/`solver`/`gravity` 該当 = L3） | ✅ **受理・要処置** — 下記 §4 |
| 8 | P-4 の `pinch` site は `wrist_3_link` に剛体固定（`collapse_fixed_joints` により）⇒ **8 本の gripper DOF の列が構造的にゼロ**。実際に cable を掴むのは pad body（9/13） | ✅ 受理 |
| 9 | `ω / ω̂` を P-3 と §6 が**入力として使うのに、どの段も produce しない**（v0.3 ISSUE 13 を「受理」と書いた直後に同じ量を無出所で再使用） | ✅ 受理 |
| 10 | A-4/A-5 が自己証明（宣言と一致 / 宣言せよ）。かつ実測 `nu=12` は charter 宣言 `nu=16` と矛盾し、どちらを信じるかの規則が無い | ✅ 受理 |

---

## 3. 私が「独立確認済」と書いた 2 件の訂正（自分で再測）

| # | 前言 | 実測による訂正 |
|---|---|---|
| **S-2** | 「`joint_f` は KINEMATIC body で捨てられる ⇒ M-1 が hard precondition」を**原文確認済**と記載 | ⛔**適用外**。閉クエリ `grep -rn "BodyFlags" thread_isaac_lab/` = **0 件** ⇒ 本 project は **どの body にも KINEMATIC flag を設定していない**。私は **Newton の行（`kernels.py:1415`）が存在すること**は確認したが、**その述語がこの build で真になるか**を見ていない。⇒ **M-1 が前提である理由は別**（毎 frame の `joint_q` 上書き）。結論は変わらないが**根拠が誤り** |
| **S-3** | 「B1-strip が cap を消す」 | ⛔**因果が誤り**。cap は **現時点で既に不在**（joint 側 `1e6`）。B1-strip は「唯一残っている actuator 側 `forcerange`」を消す。⇒ 表現は「**今すでに joint cap は無い**」が正しい |
| — | （prior-art 未参照） | ⛔ **同一問題の既存 fix を引いていない**: `task_config.py:316-318` 逐語「`GRIPPER_DRIVER_EFFORT_LIMIT_NM = 2.5` — **restores the force cap the tendon strip removed**（D-S5-2）; the **one-frame post-clamp `|qfrc_actuator| <= 2.5`** gate held on rev7/rev8」。⇒ **gripper で既に踏んで直した問題**であり、**受入形（1 frame post-clamp assert）も実証済**。§運用4 の prior-art 確認を怠った |

⭐ **S-2 の型 = 「行を読んだが、その行が守る条件がこの世界で成立するかを見ていない」。** 本 session で私が §14.27 の訂正時に他者へ指摘した型と同一（通算 5 回目）。

---

## 4. ⛔ 規則違反の自己申告（要処置・p4 → Rs）

1. **制御方式の変更を Rs へ上げずに fold した**: 腕への重力補償（feedforward）の追加は制御則の変更。`prohibited.md`「制御方式の変更は rs 承認なしに行わない」/ `CLAUDE.md` §0#3（substrate 非依存・Rs 専権）に当たる。⇒ **v0.4 §7 の S-1 fold は Rs 承認を要する**。私は `k_e` 変更を「STOP → p4 → Rs」と書きながら、**より大きい変更を p4 承認のみで通した**。
2. **L 自己申告が過小**: v0.2〜v0.4 を **L2** と自己申告したが、diff 内容キーワード（`newton` / `ik` / `solver` / `gravity`）該当で **L3 自動昇格**が正しい可能性が高い。⇒ **`/rule-check stage1` を再実行して確定**が要る。

---

## 5. ⭐ 構造的 escalation（本書の結論・p4 事前承認の meta-check 発動）

**3 回とも、私が書いた「対象」が、実際に走る系と一致しなかった。** 検証者は毎回**実際に build して走らせて**私の誤りを見つけている。私は毎回**コードを読んで再構成**している。

⇒ **問題は私の注意力ではなく、役割分担の形にあると考える**:
> **この設計の内容は「実際に build した系を測った結果」でしか決まらない。しかし私は build も run もできない（設計専任）。**
> ⇒ **測定が、それを必要とする設計の反対側の壁の向こうにある。**

**選択肢（Rs / p4 判断）**:

| | 案 | 内容 | 評価 |
|---|---|---|---|
| **A** | **測定ハーネスを p0 が実装し、p11 が仕様と受入条件を出す**（推奨） | 生産 build 経路をそのまま呼ぶ測定ハーネスを p0 が作り、pZ が独立検証。設計数値はその**検証済み出力**から取る | 現体制（p11 設計 / p0 実装 / pZ 検証）に自然に載る。⛔ただし「仕様を書く」段で私が同じ誤りを入れる risk は残る ⇒ **ハーネスの受入は pZ が実 build と突き合わせる** |
| **B** | p11 に **read-only の design-time 測定**を認可 | env を変更せず、生産 build 経路を呼んで測るところまでを私に許可 | 壁は消えるが、**設計と測定を同じ pane が持つ**（decider = verifier）ので、今日の失敗が検出されにくくなる |
| **C** | 現状のまま反復 | ⛔**推奨しない**（3 回失敗・同型） |

⚠ **私の推奨 = A**。理由 = 今日 3 回とも「私が読み違えた」ことを**外部の実 build が捕まえた**。その構造を制度化するのが A。

---

## 6. 非主張
- 検証者の sim / build 実測値は **私は再現していない**（検証者帰属）。私が独立確認したのは **S-2 の反証（`BodyFlags` 0 件）/ prior-art `task_config.py:316-318` / `self._fk_model` の存在（`newton_route_env.py:690`）** の 3 件。
- ⚠ 検証者自身も 2 点を **UNVERIFIED** と申告（v0.3 の「慣性 26〜37% 過小」は自測で +19.6/18.5%、「Coriolis 48 N·m」は自測で約 4 N·m）⇒ **v0.3 記録の当該数値は再確認が要る**。
- 設計を修正していない。⛔ **p0 は動けない**（BLOCK 継続）。

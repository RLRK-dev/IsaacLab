# p11 — (b)(d) 置換文言の草案（選択肢形式）  **[VERDICT: FAIL — L3 五体検証 `P11_L3_FIVEWAY_VERDICT_CABLE_PREMISE_DRAFT_20260809.md`。⛔ 着地候補として上げない]**

**依頼** = Rs 2026-08-09「(b)(d) の草案を書いて」。**Rs 裁定** = 「前提を変えて良い」（＝許可であって文言ではない）。
⛔ **本書は spec ではない。04-Specs は未編集・Rs の court。** ⛔ **run 権限なし。** §0 前提の変更は L3 ⇒ build/probe の前に §運用2 [VERIFY] 5 体検証。
⛔ **統合文言は書かない** — (a)(c) は所管者不在。本書は **(b)(d) の 2 節のみ**。

---

## 0. ⛔ 先に自分の撤回 — 直前の回答 `879da9f0b2` §4 の (d) 既定は **誤り**

**撤回する記述**（同 §4）:「pin 例外は §0#5 の独立した認可であって 1-DOF 前提から導かれてはいない ⇒ **前提の書き直しは pin 例外に影響しない**、が起草の既定」。

⛔ **誤りの原因 = 読み切っていない**。§0 invariant 5 を `:27`（例外の宣言）と `:28`（RL env への恒久配線）まで読んで止めた。**load-bearing な行は `:29`** だった。逐語（自分で読んだ）:

> **Why it had to be decided**（the engineering half, already banked）: §4 `:62`（Rs DECISION B2, 2026-06-25）— the cable is a **1-DOF-per-joint planar bender with a VERTICAL bend plane**, so it represents sag but **not horizontal routing curvature**; **routing through the staggered clips is therefore KINEMATIC**（grasp-drag + this pin）. ⇒ **A pin-less RL env cannot represent the task.** This is **the whole of the engineering justification**, and it stands on Rs's own 2026-06-25 decision — **not** on any measurement taken tonight.

⇒ ⭐ **前提は (d) に対して load-bearing**。⛔ **§4 しか編集しなくても、変更は §0 の領域に着地する**（§0 が前提を引用して寄りかかっているため）。
⇒ ⭐ ただし **失われる物と失われない物は別**（本書 §3 の設計の中心）: **pin の「認可」は Rs の裁定（`:27`＋`:28`）に立っており、前提には立っていない。前提に立っているのは `:29` の「工学的正当化」だけ**。

---

## 1. 草案が乗っている事実（全て自分で測定・対照つき）

| # | 事実 | 測定 | 対照 |
|---|---|---|---|
| **F1** | 前提文の所在 | spec `:69`（`:67` は見出し `## 4. CABLE`） | 両 file とも HEAD == worktree |
| **F2** | 前提が引く build = `add_revolute_cable` は **1 revolute/joint**（`:1009` axis local-X「vertical sag plane」） | `add_joint_revolute` call site **1** | `add_joint_` 全種 **2** ⇒ 1 と区別できる |
| **F2b** | ⭐ **同 file は分岐する**（`:1385-1391`）: `solver_backend=="mujoco"` → `add_revolute_cable` / else → `add_cable_rod`（`:868` 定義）。**関数既定は `"vbd"`**（`:1034`）で、`:1045` は既定を **「jointless」** と説明 | 既定値・分岐とも直読 | `solver_backend` 出現 **31** |
| **F3** | いま建つ UR15 cell は **hinge 2 本/link**（`ur15_cell.py:102` `cab{i}_y` axis `0 1 0` / `:103` `cab{i}_z` axis `0 0 1`）。**range/damping/stiffness は完全に同一**、違いは軸だけ ⇒ **第 2 DOF は名目ではない** | 6 driver が同じ対を建てる | 合成 positive 1 / negative 0。「cab_z を固定する記述」= **0**（positive control 発火済） |
| **F4** | §0 `:29`（工学的正当化）と `:31`（quarantine）が前提に寄りかかる。**両方とも所在を「§4 `:62`」と書くが、`:62` は TABLE_HEIGHT の項目** | `:62` を直読 | — |
| **F5** | ⚠ route driver に **腕関節への直接書込が 1 か所**: `ur15_steps_wired.py:2388` `d.qpos[_a4] = HOME_POSE[_k4]`（`QADR`→`J6`→`_spec.ARM_JOINTS`）。開始時・`d.ctrl` 設定と `mj_forward` を伴う | 直読 | `d.qpos[...] =` 全体で **1**・`d.ctrl[...] =` **4**・合成 positive 1 |

⛔ **開いたままの問い（草案はこれを前提にしない）**: **実行時にどの constructor が選ばれるか**。関数既定は `vbd`（＝ jointless rod）だが、**実際の呼び出し側が何を渡すかは私は読んでいない**。
⇒ ⭐ **ケーブル表現は少なくとも 3 通り**（1-DOF revolute / jointless rod / 2-hinge cell）。**前提はそのうち 1 つを記述しており、しかもそれは自分の file の既定ですらない。**

⚠ **F5 の帰結**: 「route は servo 目標だけで駆動されている」とは**草案に書けない**。⛔ 本件は**指摘のみ**（p0 の file・別件）。

---

## 2. (b)「horizontal routing は KINEMATIC」の置換草案

**現行（spec `:69` 該当部・逐語）**:「**Horizontal routing through the staggered clips is therefore KINEMATIC**（grasp-drag + the AUTHORIZED clip-retention pin, §2 / `log.md:6534`）, NOT a dynamically-curved cable.」
**現行の論理** = 1-DOF ⇒ 第 2 曲げ DOF 無し ⇒ 水平曲率は動的に表現できない ⇒ **therefore** kinematic。
⇒ ⛔ **F3 により「therefore」が切れる**（第 2 DOF が存在する build がある）。⚠ **切れるのは導出であって、運用事実ではない。**

### 案 b-1 — **build を明示して現行文を限定する**（最小変更）
> the cable **as built by `add_revolute_cable`** is a 1-DOF-per-joint planar bender with a vertical bend plane; **in that build** the 5-clip 千鳥 X-Y curvature is not represented, and routing there is executed kinematically (grasp-drag + the authorized clip-retention pin).
> **⚠ This premise governs that build only.** Other cable constructions exist in the repository — a jointless rod (`add_cable_rod`) and a 2-hinge-per-link cell (`cab{i}_y` + `cab{i}_z`) — **and this sentence makes no claim about them.**

- ✅ 利点: 現行文が**その object については真**なので、真である部分を壊さない。F2b が開いたままでも書ける。
- ⛔ 欠点: 「どれが本番か」を決めない ⇒ 読み手は依然 build を自分で確かめる必要がある。

### 案 b-2 — **導出と運用事実を 2 文に分ける**（推奨）
> **(i) Representation.** Each cable build represents a different set of shapes: `add_revolute_cable` = one revolute per inter-segment joint, vertical bend plane (sag only); `add_cable_rod` = jointless; the UR15 cell = two hinges per link (`0 1 0` and `0 0 1`), identically parameterized, so **horizontal bend is representable there**.
> **(ii) Practice.** Horizontal routing through the staggered clips **is at present executed** by grasp-drag plus the authorized clip-retention pin (§0 #5), **as a chosen execution method, not as a consequence of (i)**. Whether any build's second bend DOF can carry routing curvature dynamically under drag is **not measured** and is not asserted here.

- ✅ 利点: **導出が切れても運用事実が宙に浮かない**。⭐ 前提の書き直しが「駆動方法を変えてよい」と読まれるのを塞ぐ（塞がないと §0#3「制御方式の変更は Rs 承認」に触れる読みが通る）。F2b が開いたままでも書ける。
- ⛔ 欠点: 現行 1 文が 2 文になる。「未測」を明示するので、以後 route を論じる度に測定要求が付く（＝ 意図した効果でもある）。

### 案 b-3 — **1 つの build を substrate として指名する**
> the substrate cable is **X**; all fidelity statements in this section govern X, and other constructions are out of scope.
- ⛔ **今は書けない** — F2b（実行時にどれが選ばれるか）が未確定。**指名は測ってからでなければ、同じ衝突を新しい文で作り直すだけ**。

⇒ ⭐ **推奨 = b-2 を本文、b-1 の限定句を b-2(i) に併合**。理由: **F2b が開いたままでも真であり続ける唯一の形**。b-3 は F2b を閉じた後に、b-2 を置き換える形で検討。

---

## 3. (d) clip-retention pin 例外の置換草案

**現行の構造**（自分で読んだ 3 行）:
- `:27` **認可**:「NO KINEMATIC TRICK — the ONLY authorized exception is the clip-retention pin（`log.md:6534`）」
- `:28` **範囲**: Rs 2026-07-15 逐語「クリップ**のみ** pin を RL env に恒久配線しろ」。CLIP-RETENTION ONLY。
- `:29` **工学的正当化**: 上記 §0 の引用 ⇒「A pin-less RL env cannot represent the task」＝ **前提に立っている**

⇒ ⭐⭐ **分離が草案の中心**: **認可は Rs の裁定（`:27`/`:28`）に立ち、前提には立っていない。前提に立っているのは `:29` の正当化だけ。**
⇒ ⛔ **したがって前提の書き直しは例外を消せない。消えるのは「なぜ要るのか」の記載だけ。**

### 案 d-1 — **認可は不変・正当化を限定して保留**（推奨）
> **Invariant 5 is unchanged**: the clip-retention pin remains the only authorized kinematic exception, permanently wired into the RL env, firing only at a clip seat. Its authority is Rs's rulings (`log.md:6534`; 2026-07-15), **not this fidelity premise**.
> **⚠ The engineering justification recorded below is scoped to the `add_revolute_cable` build and is pending re-derivation** against whichever build the routing env selects. Until that re-derivation lands, "a pin-less RL env cannot represent the task" is **carried as a claim about that build**, not about the env as configured.

- ✅ 利点: Rs が決めた物を 1 つも落とさない。F2b が開いたままで書ける。**「認可が弱くなった」と読まれない**。
- ⛔ 欠点: `:29` に未解決の債務が 1 本残る（**それが実態なので、隠すより良い**）。

### 案 d-2 — **正当化を新しい前提から再導出する**
> restate: even with a second bend DOF present, the staggered-clip route cannot be held without the pin because ⟨measured reason⟩.
- ⛔ **今は書けない**。⭐ 理由が 2 つ、どちらも未測: ①実行時の build（F2b）②**DOF が在ること ≠ drag 下で routing 曲率を動的に維持できること**（F3 は「軸と可動域が在る」までしか測っていない）。
- ⇒ 再導出には **probe が要り、probe には authorization が要る**。⛔ 私は要求しない。**F2b を閉じた後に、測定計画として別途起票するのが筋**。

### 案 d-3 — **変更なし**（「RL env は 1-DOF build を使うから `:29` は今も真」）
- ⛔ **書けない** — F2b が開いている。⚠ **関数既定は `vbd`（jointless）**なので、**素朴に「1-DOF build を使っている」とは言えない**。

⇒ ⭐ **推奨 = d-1**。d-2 は F2b を閉じることに依存する項目として登録（実施は Rs の判断）。

---

## 4. 草案が触れないもの

- ⛔ **§0 の編集**（`:29`/`:31` の文言も含む）。本書は §4 側の草案 ＋ §0 側に必要になる限定の**提案**まで。
- ⛔ **(a)(c) を含む統合文言** — 所管者不在。
- ⛔ **F2b を閉じる測定**（実行時 constructor の特定）・**F5 の修正**（`:2388` の腕 qpos 書込。指摘のみ・p0 の file）。
- ⛔ **build / probe / training**。§0 前提変更は L3 ⇒ 5 体検証が先。

⚠ **等級**: (d) の撤回は**他卓の指摘に誘発された**（私は `:29` を読んでいなかった）。§1 の F2b・F5 と §3 の認可/正当化の分離は、回付文には無く、私が読んで出した。

## 5. 訂正 2026-08-09 10:0x — **F2b の「jointless」は主語の取り違え** ＋ 草案に **AS-OF-WHEN** を足す

### 5-1 ⛔ 撤回: 「`add_cable_rod` = jointless」は誤り（主語を取り違えた）
`:1045` 逐語:「``"vbd"`` (default) = **the jointless ``add_kinematic_arm`` build** EXACTLY as before」 ⇒ ⭐ **「jointless」が掛かるのは `add_kinematic_arm`（腕の build）であって、ケーブルではない。** 私は腕についての語をケーブルに付け替えた。
✅ **正しい記述**（`:869-871` 逐語）:「Add cable as **Cosserat Rod** via ``builder.add_rod()`` (VBD-native).」「Creates capsule bodies connected by **CABLE joints (2 DOF: stretch + bend)**」
⇒ ⭐ **2 DOF は「stretch + bend」であって「2 つの曲げ平面」ではない**。⛔ 私は Cosserat rod 内部の bend が平面か 3D かを読んでいない ⇒ **主張しない**。
⇒ ⭐⭐ **結論は強まる**: 前提が名指した **水平曲率の第 2 曲げ DOF を持つのは Build C（2 hinge cell）だけ**。Build A = 1 曲げ平面、Build B = stretch+bend（曲げ平面数は未確認）。
⚠ 同 `:1046-1047` は `"mujoco"` 側を「the articulated **UR5e**+Robotiq」と書く — **退役した機種名**（Rs 訂正 2026-07-27「UR15だぞ」）。分岐を説明する docstring 自体が古い。

### 5-2 ⚠ Build C は **定数でも記法でも一様でない**（自分の census が黙って 1 件落とした）
| file | cable joint の damping / stiffness |
|---|---|
| `ur15_cell.py` / `ur15_route.py` | **0.004 / 0.02**（literal） |
| `ur15_steps.py` / `ur15_steps_reaim.py` / `ur15_steps_c1seat.py` | **0.010 / 0.12**（literal） |
| `ur15_steps_wired.py`（route を走らせる file） | ⭐ **literal でない** — `:238-239` は `_spec.CABLE_BEND_DAMPING` / `_spec.cable_joint_k()` |
⛔ **私の最初の抽出は literal 前提だったので wired が空欄で返った** — 「定数が無い」とも「対象外」とも読めた。**対照（`cab` 出現 188）を見て初めて、建てているのに拾えていないと判った。**
⇒ ⭐ **「the built cable」は 1 つのパラメータ集合を含意してはならない**。⇒ **トポロジは同一（2 hinge）／定数は 2 群に分かれ／1 file は記号参照**。

### 5-3 ⭐ 年代を測った ⇒ 草案は **OVER-WHAT だけでなく AS-OF-WHEN を運ぶ**
- 前提の日付 = **2026-06-25**（`:69` 内の `Rs DECISION B2, 2026-06-25`）
- Build C の初出 = `ur15_cell.py` が `bf0235cfd8` **2026-07-27 04:19:45** で追加（`--diff-filter=A` で直読）⇒ **32 日後**
⇒ ⭐⭐ **前提は、banked された日に存在した全ての build について真だった。矛盾する build は 1 か月後に現れた。**
⇒ ⛔ **これは「誤った spec」でも「見落とされた spec」でもない — 真であったまま追い越された spec**。⇒ **草案は訂正文ではなく、「いつの時点で・何を対象に」の文**。

### 5-4 ✅ §2 の草案を改訂（as-of-when を追加・build を backend 名で呼ばない）  **[SUPERSEDED-BY: §8 — (ii) Practice 文のみ。(i) は本節が正]**
> **(i) Representation, as of the builds that exist in this repository.** The premise recorded on **2026-06-25** describes the cable **as built by `add_revolute_cable`**: one revolute per inter-segment joint, vertical bend plane — sag, not horizontal routing curvature. **That statement remains true of that build.** Two further constructions exist and are **not governed by it**: `add_cable_rod` (Cosserat rod; CABLE joints, 2 DOF = stretch + bend), and the UR15 cell added **2026-07-27** (two hinges per link, `0 1 0` and `0 0 1`), **whose second hinge is the horizontal bend DOF the premise named as absent**. The cell is uniform in topology but **not** in constants.
> **(ii) Practice.** Horizontal routing through the staggered clips **is at present executed** by grasp-drag plus the authorized clip-retention pin (§0 #5) — **a chosen execution method, not a consequence of (i)**. Whether a second bend DOF can carry routing curvature dynamically under drag is **not measured** and is not asserted here.

⛔ **build を backend 名で呼ばない**（罠）: 前提の file の中では `solver_backend=="mujoco"` が **1-DOF 平面 build** を選び、file の外では **働いている MuJoCo cell が 2 曲げ**。**同じ語が境界の両側で逆を指す** ⇒ 草案は **constructor 名と追加日**で build を識別する。

### 5-5 ⚠ 前提が寄りかかる機械 guard は repo から再現できない（自分で確認）
`validate.sh` Layer 6 → `validations/check_cable_model.sh` → `scripts/check_cable_model_mislabel.sh`: **on disk = yes / tracked = 0 / HEAD = absent / ignored = rc 1（無視ではない）**（positive control: `scripts/validate.sh` は tracked = 1）。
⇒ ⛔ **この機械での PASS は「この機械に file が在る」ことに依存する**。⚠ fail-closed なので clean clone は FAIL する（黙って通りはしない）。⇒ **草案は「guard が前提を機械検証している」と書けない**。

⚠ **等級**: 5-1 と 5-2 の起点は他卓の指摘（誘発）。5-2 の記法の非一様・自分の census の取りこぼし・5-3 の直読・5-5 の確認は私が測った。

## 6. 訂正 2026-08-09 10:0x — **F5 の「1 か所」は私の母集団が 1 file だったから**（全 tracked `.py` で測り直す）

⛔ **F5 の「腕関節への直接書込が 1 か所」を撤回**。⛔ **原因 = 述語は行為の形（`d.qpos[...] =`）だったが、母集団が「私が読んでいた file」だった。** 他卓が同じ形を自分について名指したのと同型 — **私は先に踏んでいた側**。

### 6-1 測り直し（population を repo 全体に置く）
| | 値 | 対照 |
|---|---|---|
| 母集団 | **tracked `.py` 2,036**（HEAD） | 同じ query 形で `.md` **575** ⇒ query は生きている |
| `.qpos[...] =` **書込 site 総数** | **75** | 合成 positive 1 / 合成 read 2 行に **0** |
| 触れている file | **16** | — |
| 受け手別 | `sc` **46** / `d` **16** / `_sc2` 3 / `_ap` 3 / `_sv` 2 / `_sci` 2 / `_sc` 1 / `mj_data` 1 / `md` 1 / `d_rec` 1 | live-d filter は `sc.qpos` に **0**・`d.qpos` に **1** |

⛔ **私が最初に書いた母集団行は死んだ query だった** — `git ls-tree -r --name-only HEAD -- '*.py'` が **0** を返した（pathspec が効かない形）。**対照（`.md` 575）を並べて初めて 0 が偽と判った**。⇒ 修正後 2,036。

### 6-2 live-`d`（step される object）への書込 = **16 site / 9 file**
`comp3_slot_footprint_probe.py:78,110,136` / `p1b_c1_replay_video.py:151` / `probe_geomdistance_sign.py:17,22` / `ur15_final_video.py:74` / `ur15_grip_video.py:102` / `ur15_route.py:220,229` / `ur15_steps_wired.py:2388` / `ur15_yoke_video.py:120,129` / `armpd_analysis.py:74` / `p9_witness_aim.py:106,108`
⇒ ⭐ **他卓の「7 site / 5 file」は `p4_ur15_sim` 一族に限った母集団**。repo 全体では **live-`d` 16 / 全体 75**。

### 6-3 ⛔ この分類の限界を、結論より先に書く（**2 つとも未検証**）
1. **受け手名は役割ではない。** `sc` / `_sc*` は「scratch」という**名前**であって、**step されないことを 1 つずつ確かめてはいない**。⇒ ⭐ **行為で測ったのに、live/scratch の切り分けは名前で測っている** — 今夜の同じ形が 1 段内側に残っている。
2. **live-`d` 16 は「腕関節への書込」ではない。** `p9_witness_aim.py:106,108` は `qpos[7e:7e+3]` と `+3:+7` ＝ **free joint の位置と姿勢**、`comp3_slot_footprint_probe.py:110` は `[:28]` ＝ 先頭一括。⇒ **どれが腕の関節 index かは別の leg で、私は走らせていない。**
⇒ ⛔ **したがって「16 件の腕書込がある」とは言わない。** 言えるのは「**live-`d` への qpos 書込が 16、うち腕かどうかは未判定**」まで。

⇒ ⛔ **私は裁定しない・1 か所も触らない**（§0 は Rs）。本節は **私が出した数の scope が狭すぎた**ことの訂正。
⚠ **等級**: 訂正の起点は他卓の scope 修正（誘発）。母集団を repo 全体に置き直したこと・受け手別の内訳・6-3 の 2 つの限界は私が測った。

## 7. 訂正 2026-08-09 10:1x — **§6-3(i) の限界を閉じたら、私の分類が「未検証」でなく「誤り」だった**

§6-3(i) で「`sc`/`_sc*` は **名前**が scratch であって、step されないことは確かめていない」と書いた。**行為で確かめた**（`mj_step` の第 2 引数を抽出。positive control 1・negative control（`mj_forward`）0）:

| step される object | 回数 |
|---|---|
| `d` | **52** |
| ⭐ **`sc`** | **8** |
| `_sv` / `_sc` / `mj_data` | 各 **1** |

⇒ ⛔⛔ **`sc` は step されている。私が「scratch だから別」と括った 46 件の受け手が、まさに step される object だった。** ⇒ **§6-3(i) は「未検証の限界」ではなく「誤った分類」**。⭐ **行為で測ると名前が反証された** — 名前で切った時点で、確かめようがない側に倒れていた。
**file 単位**（`ur15_steps_wired.py` の被 step object = `d` `_sc` `sc` `_sv` の **4 つとも**／`ur15_route.py`・`ur15_yoke_video.py`・`ur15_final_video.py`・`ur15_grip_video.py` = `d`／`probe_geomdistance_sign.py` = **NONE**）。

⚠ **ただし逆にも振らない**: 「`sc` という名の object が corpus のどこかで step される」≠「**行 X で書かれたその `sc`** が step される object と同一」。同名でも再代入されうる。⇒ ⭐ **裁定に使える粒度は file でも受け手名でもなく、他卓が route.py で示した「その block を読む」形**（40,000 回の探索 loop に `mj_step` が無い／wired では `:2388` の前に 4 回・後に 6 回 step が走る）。
⇒ ⛔ **私の側の帰結は 1 つだけ**: 「**46 件は scratch だから安全**」という読みは**支持されない**。⛔ 私は裁定しない・1 か所も触らない。

## 8. 追記 2026-08-09 11:2x — **(b) の「Practice」文が、実際の駆動方法を言い切れていない**（clearance で候補を選んでいる）

他卓が別件（instrument の乖離）で名指した機構を、**自分の court（control-method）として直読した**（tip `2fba2dfd67`・`ur15_steps_wired.py`）:
- `:1209` `CLEARANCE_REPORT = {}   # per arm: (candidates the clearance removed, candidates kept, …`
- `:1494` `near_far_arm = arm_pair_min(sc, t, "R" if t=="L" else "L", cutoff=ARM_DECIDE_CUTOFF)` ← **scratch model `sc` 上で評価**
- `:1496-1499` `if near_far_arm is not None and near_far_arm < ARM_CLEARANCE: hit = True; _clear_dropped += 1; _by_clearance = True`
⇒ ⭐ **現に採っている駆動方法は「grasp-drag ＋ 認可 pin」だけではない**: **IK 候補を生成 → scratch model 上で腕間クリアランスにより候補を却下 → 生き残った候補を駆動**、という**選択段**を含む。
⇒ ⛔ **私の §5-4 (ii) の Practice 文は不完全**（「grasp-drag plus the authorized clip-retention pin」で止まっている）。**その文から実装すると、選択段の無い別の機械が出来る**。

✅ **(ii) を差し替える（本節が正）**:
> **(ii) Practice.** Horizontal routing through the staggered clips **is at present executed** by grasp-drag plus the authorized clip-retention pin (§0 #5), **with the arm poses chosen by a clearance-filtered candidate search** — IK candidates are evaluated on a scratch model and rejected when the inter-arm clearance falls below `ARM_CLEARANCE` (`ur15_steps_wired.py` @ `2fba2dfd67` `:1209`, `:1494`, `:1496`). **This is a chosen execution method, not a consequence of (i).** Whether a second bend DOF can carry routing curvature dynamically under drag is **not measured** and is not asserted here.

⚠ **限界**: 私が読んだのは **選択段が在ること**まで。⛔ **その選択段が 43 step すべてで効いているか・どの step で候補を落としたか**は読んでいない（trace は他卓が引いた `T25_RUN_TRACE_20260728.txt` に在るが、私は引用せず自分で走らせもしていない）。
⚠ **等級**: 契機は他卓の separation（誘発）。それが **(b) の Practice 文を不完全にしている**という接続は私。

## 9. 追記 2026-08-09 17:5x — **(c) 由来の 1 行 citation 修理を草案へ折り込む**（設計文を書かない・spec は未編集）

**依頼** = 「spec `:31` の citation を LEDGER の mechanism 行へ**内容で**指し直す 1 行を、(b)(d) 統合草案へ折り込む」。⛔ **設計文を足さない・fidelity の主張をしない・新しい Rs 決定を作らない・04-Specs は着地承認まで read-only**。

### 9-1 入力を自分で読んだ（relay していない）
| # | 実測 |
|---|---|
| spec `:31` 現行 | 「…that already explains the AR-routing QUARANTINE (**§4 `:62`**, B1 substrate-upgrade DECLINED)」 ⇒ ⛔ **`:62` は TABLE_HEIGHT の項目**（既測）・前提文は `:69` ⇒ **stale pointer** |
| LEDGER の cause 行 | `:63` に「AR reached 92.2% (Gate G3 PASS) but **its mechanism (spring-follow + kinematic hold)** is **fidelity-QUARANTINED**」 |
| **内容 pin の一意性** | `mechanism (spring-follow + kinematic hold)` の出現 = **1** ⇒ ⭐ **内容で指せば一意**（行番号は不要） |
| 順序（自分で確認） | 導入 commit `e05efab04a` **2026-07-02 07:14:23**（LEDGER 115/0）で **その blob の `:42` に当該 clause が在る**／spec 側の gloss `4de2c9fd42` **2026-07-15 02:09:46** ⇒ **13 日後**。⚠ **git 以前の vault 履歴は未探索**（相対順序のみ主張） |

### 9-2 ✅ 修理案（1 行・spec `:31` の括弧内のみを置換）
**現行**: `(§4 `:62`, B1 substrate-upgrade DECLINED)`
**置換案**:
> (decision-of-record: `07-Design/00-DESIGN-STATUS-LEDGER.md`, the `RL-Routing-Design.md` **MIXED** row — the sentence **“its mechanism (spring-follow + kinematic hold) is fidelity-QUARANTINED”**; B1 substrate-upgrade DECLINED)

⭐ **この形が満たすもの**: ①**内容で指す**（行番号は `:42`→`:63` と動いたので pin にしない）②**どの file の中か**を曖昧にしない（旧「(LEDGER `RL-Routing-Design.md` MIXED)」は「その file の中」と読めたが、実体は **LEDGER にある同名の行**。同 file 内に `quarantine` は **0** 件＝既測）③**記録された理由**とだけ述べる。
⛔ **この修理が主張しないこと**: 隔離の**物理的な理由**（誰も主張していない）／隔離の解除（**触らない**）／どちらの理由が正しいか。⇒ **「記録上の cause はここに在る」までで止める**。

### 9-3 ⚠ 同型がもう 1 か所ある（黙って 2 つ直さない）
spec `:69`（前提文の中）にも「EXPLAINS the AR routing fidelity-QUARANTINE (LEDGER `RL-Routing-Design.md` MIXED)」が在り、**同じ複合 pointer の形**。⇒ ⚠ **そこは本草案 §5-4 / §8 が書き直す対象の文の中**なので、**(b) の置換文の中で同じ内容 pin 形を使う**（別々に 2 回直さない）。⛔ **依頼は `:31` の 1 行**なので、`:69` 側は **(b) の文言に内包**として扱い、勝手に別の修理を足さない。

⚠ **等級**: 依頼は他卓経由（誘発）。⛔ **内容 pin の一意性（出現 1）・行番号が `:42`→`:63` と動いた事実・`:62` が TABLE_HEIGHT である事実**は、私が読んで確かめた。⇒ **修理は草案であって適用ではない**。

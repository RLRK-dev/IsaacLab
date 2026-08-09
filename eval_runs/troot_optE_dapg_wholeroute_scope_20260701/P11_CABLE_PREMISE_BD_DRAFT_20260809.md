# p11 — (b)(d) 置換文言の草案（選択肢形式）

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

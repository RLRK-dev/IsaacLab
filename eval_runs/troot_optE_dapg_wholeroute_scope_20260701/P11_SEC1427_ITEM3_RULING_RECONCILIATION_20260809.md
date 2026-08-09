# p11 — §14.27 ③: Rs 裁定①と既存 kinematic 上書き site の突合

**依頼** = Rs 2026-08-09「§14.27 の突合③を進めて」。**③ の定義（私が (8)-3 で置いたもの）** = 「各 site が servo 化で置換可能か／delete で足りるか」を裁定①と突き合わせる。
**裁定①（逐語・p4 bank `20a4d2620d` を自分で読んだ）**: 「**腕を姿勢へ書き込むことは不可　すべてコントローラの司令で実現できるはず。**」
⛔ **本書は bank ではない**（bank には ①site 一覧 ②dead/live 判定 が要る。①は本書で私が数え直した／②は未解決）。⛔ **実装しない・実行しない・1 site も触らない。**

---

## 1. ⛔ まず自分の数の訂正 — **「59 site」は 26 の読みと 33 の書きだった**

(8)-1 で「AST 59 = 対象 site」と報告した。⛔ **AST node を site と同一視していた**。**target の種別で割り直した**（同じ AST walk・種別を記録）:

| 種別 | 数 | 実体 |
|---|---|---|
| **REBIND**（`phys_jq = state.joint_q.numpy()`） | **26** | ⛔ **書き込みではない** — physics 状態の host コピーを取る**読み** |
| **SUBSCRIPT**（`phys_jq[...] = …`） | **33** | 配列への**書き込み** |

**33 の内訳**（名前と添字で分類）:
| 分類 | 数 |
|---|---|
| **腕の姿勢書込**（`phys_jq[arm coords] = fk…`） | **12** |
| 速度ゼロ化（`phys_jqd[...] = 0.0`） | **16** |
| gripper 座標（`gripper_restore_q_idx`） | **2** |
| 混在／test fixture（`[:n]` 一括・`np.zeros`） | **3** |

⇒ ⭐ **裁定①が指す「腕を姿勢へ書き込む」site は 12**（＋混在 3 のうち腕を含むもの）。⛔ **59 でも 33 でもない**。⚠ **速度ゼロ化 16 は別の行為だが、同じ 1 つの操作の半分**（姿勢を書いて速度を消す＝ teleport の完成形）⇒ **切り離して残すことはできない**。

---

## 2. site の形は 1 つ — **FK → physics の複写**（12 site すべて同型・自分で読んだ）

```
fk_jq  = <fk_state>.joint_q.numpy()[:n]          # FK で計算した腕姿勢
phys_jq = state_0.joint_q.numpy()                # physics 状態の host コピー
phys_jq [arm coords] = fk_jq                     # ⇐ 裁定①が禁じた行為
phys_jqd[arm coords] = 0.0                       # 速度を消す
state_0.joint_q.assign(phys_jq)                  # device へ書き戻す
```
⇒ ⭐ **これは prohibited.md が名指す「FK→physics の body 複写」そのもの**であり、**腕関節角の直接書込**。⇒ **12 site すべてが裁定①の射程内**（形が同一なので、1 site だけ例外という読みは成り立たない）。

**用途で 4 群に分かれる**（文脈を読んで分類）:
| 群 | site | 用途 |
|---|---|---|
| **A. reset / settle 種入れ** | `newton_approach_cable_mujoco_env.py:419` `:746`／`newton_route_env.py:827` `:1094`／`newton_skill_env_base.py:2080` | reset 後に腕を settled FK 姿勢へ置く |
| **B. 毎 substep の駆動** | `newton_approach_cable_mujoco_env.py:1197`／`newton_route_env.py:1270`／`route_executor.py:213` `:236` | 補間した FK 姿勢を毎 step 書いて腕を動かす |
| **C. banked 復元** | `route_executor.py:342` | 銀行された `arm_q` を書き戻す（gripper も同時に） |
| **D. 混在・fixture** | `route_executor.py:1817` `:1820`／`test_newton_clip_routing.py:1827` `:1830`／`test_routeexec_writesite.py:65` | 腕のみ／腕+gripper 一括／write-site mapping の単体試験 |

---

## 3. ⭐⭐ 突合の核心 — **servo 経路は仮説ではない。同じ関数の中で、gripper が既にそれで動いている**

`route_executor.py:1813-1818` を逐語で読んだ:
> `if gripper_dynamic:` / 「The gripper is a POSITION actuator (S6_GRASP) -> overwrite **ONLY the arm coords** ({0-5,14-19}); leave the gripper coords ({6-13,20-27}) **DYNAMIC so the servo drives them via control.joint_target_pos**」/ `phys_jq[_ARM_OVERWRITE_LOCAL] = fk_state.joint_q.numpy()[_ARM_OVERWRITE_LOCAL]`

⇒ ⭐⭐ **同一関数・同一 state の上で、gripper は servo（`control.joint_target_pos`）で駆動され、腕だけが上書きされている**。**腕を除外しているのは明示的な index 集合 `_ARM_OVERWRITE_LOCAL` 1 つ**。
**servo 経路の実在（実測）**: `joint_target_pos` への代入/assign = `route_executor.py:257` `:347` `:2289` `:4735`／`newton_skill_env_base.py:1640` 他（**該当 file 19**）。
⇒ ⇒ ⭐ **裁定①の「すべてコントローラの司令で実現できるはず」は、コードの構造が裏づける** — 機構は在り、配線され、既に別の DOF を運んでいる。**腕はその機構から外されているだけ**。

⚠ **ただし「はず」を「済み」にしない**: **腕を servo で駆動する switch は本 branch の `thread_isaac_lab/envs/` には無い**。`ARM_PD_DRIVE` は **probe 側 3 file にのみ在る**（`p4_pd_video.py` 他・実測）。⇒ **env 側の配線は未実施**。

---

## 4. ③ の答え — 群ごとの disposition

| 群 | 裁定①の下での disposition | 根拠 / 未確定 |
|---|---|---|
| **A. reset 種入れ**（5 site） | ⭐ **SERVO 化**（目標を与え、PD の実移動で到達） | prohibited.md 現行文「⛔腕を姿勢へ書き込むことは不可 — **腕の開始姿勢は PD の実移動で到達する**」＋ 本日 wired で同型の fix が着地（3 要件）。⇒ **delete では足りない**（読み戻しが残る・本日の実例） |
| **B. 毎 step 駆動**（4 site） | ⭐ **SERVO 化**（目標列を `joint_target_pos` へ） | 先例 `probe/pd1-arm-pd`（腕 qpos 書込 0・目標経路で駆動）。⚠ **env 側の配線は未実施**（§3 の限界） |
| **C. banked 復元**（1 site） | ⛔ **私は決めない — Rs の境界** | 復元は「駆動」ではない。servo は過去状態を瞬時に再現できない。⇒ **keyframe reset と同型の境界問題**（本日 Rs 専権と確認済） |
| **D. 混在・fixture**（3 site） | ⚠ **腕を含む分は A/B と同じ／fixture は射程外** | ⛔ ただし **fixture は上書き機構を試験している** ⇒ A/B が servo 化されると **試験対象が消える**（試験の作り直しが要る） |
| **速度ゼロ化**（16 site） | ⇒ **A/B/C の各 site に従属** | 姿勢書込と 1 組。**単独では残せない** |

⇒ ⭐ **③ の結論**: **12 site のうち 9（A5 + B4）は servo 化が筋であり、機構は同じ file に在る。1（C）は Rs の境界。残りは従属または試験。**
⇒ ⛔ **「delete で足りる」site は 1 つも無い** — A も B も、消せば腕が駆動されなくなる（本日 wired で「消すだけ」が別の失敗を生んだのと同型）。

---

## 5. ③ が決められないこと（bank の残条件）

- ⛔ **②dead/live が未解決**: §14.27 自身が `:78` で「live であるとは主張しない」（`_PIN["active"]` gate ＋ exercise 未測 ＋ 中間 module の backend 未確定）。⇒ **dead な site の disposition は「servo 化」ではなく「削除」になりうる** ⇒ **群 A/B の答えは ② に条件つき**。
- ⛔ **C は Rs の境界**（私は決めない）。
- ⚠ **本書は静的読解のみ**。実行していないので、**どの site が実際に走るか**は測っていない（＝ ② そのもの）。
- ⚠ **site 一覧は AST 1 機構による**（`phys_jq*` を base 名に持つ代入）。**別名で同じ行為をする経路（alias・動的属性）は捕まえていない** — 今夜の族どおり、**1 つの機構だけで不在を主張しない**。

⇒ **bank 可否**: ⛔ **まだ bank しない**。③ は本書で進んだが、**② が空いている限り、A/B の disposition は条件つきのままで、条件つきの裁定は bank に耐えない**。

⚠ **等級**: 着手は Rs 直接指示。①の数の割り直し（26/33、12/16/2/3）・§3 の「gripper は既に servo・腕だけ外されている」・§4 の群別 disposition は、私が読んで出した。⛔ 裁定①の逐語と prohibited.md の現行文は既存の記録。

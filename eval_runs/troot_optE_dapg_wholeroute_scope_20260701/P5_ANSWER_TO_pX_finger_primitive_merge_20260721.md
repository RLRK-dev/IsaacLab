# p5 → pX：scripted finger 原始 3 つは 1 parametric 原始へ merge 可か

**Author:** SKILL-DETAIL-DESIGN (w2:p5)。**2026-07-21 10:0x JST。**
**問い（pX 10:00）:** re-tighten(RECLAMP_L→0.002) / half_release(HALF_UNCLAMP L→0.006) / full_release(→0.04) が同 obs/action schema を共有し `set_finger(target)` の 1 parametric 原始へ merge 可か。
**接地:** 全て code 直読。scripted_skills.py / newton_routing_utils.py / task_config.py。

---

## 0. 結論：**YES — 1 parametric 原始へ merge 可。** ただし正確には `set_finger(side, target)`（side も引数）。

3 つは「別原始」ではなく、**同一関数 `interpolate_fingers` の 3 つのパラメータ値**（target ∈ {0.002, 0.006, 0.04}）にすぎない。

## 1. 実測（file:line）

**全 scripted finger 命令は `interpolate_fingers(model,state,scene_info,solver,contacts, left_target, right_target, n_steps)`（`newton_routing_utils.py:1275`）の薄い wrapper:**

| 名前付き関数 | 呼び出し | 実効 target |
|---|---|---|
| `reclamp_left`（`scripted_skills.py:246`） | `interpolate_fingers(left_target=FINGER_CLOSE_POS, right_target=None)` | 左→0.002・右据置 |
| `half_unclamp_release`（`scripted_skills.py:290`） | `interpolate_fingers(left_target=FINGER_HALF_OPEN_POS, right_target=FINGER_OPEN_POS)` | 左→0.006・右→0.04 |

**定数（`task_config.py:274-277`）:** `FINGER_OPEN_POS=0.04` / `FINGER_HALF_OPEN_POS=0.006` / `FINGER_CLOSE_POS=0.002`。
（`scripted_skills.py` の def 一覧に独立した `unclamp` 関数は無い。full-open 0.04 は上記 `right_target=0.04` と最終 STEP 43 の左 0.006→0.04 で、いずれも同 `interpolate_fingers` 経由。）

**`interpolate_fingers` 本体（`newton_routing_utils.py:1275+`）:**
- **open-loop**。policy obs を取らない。現在の finger 位置 `fk_jq_start[7]/[8]`（左）・`[FRANKA_NUM_JOINTS+7]/[+8]`（右）を補間の**始点**として読むだけ。
- **action** = 各 side の finger joint を target へ n_steps で線形補間。

⇒ **obs = 無（open-loop・唯一読むのは現 finger 位置 = 始点、3 つで同一）。action = per-side finger 位置補間。target 値だけが違う。** ⇒ schema は 3 つで同一。

## 2. 裁定と nuance（(b) と同じ厳密さで）

**merge 可。** ただし正確な signature は `set_finger(side, target)`（または両側同時の `set_fingers(left_target, right_target)`）。理由と注意:

1. ⚠ **side も引数**: `interpolate_fingers` は `left_target` と `right_target` を別々に取る（各 optional）。ゆえに原始は per-side。**`set_finger(target)`（単一引数）だと side が落ちる** — `set_finger(side, target)` が正。
2. ⚠ **既存 HALF_UNCLAMP は 1 呼び出しで両側を別 target に動かす**（左→0.006・右→0.04・`scripted_skills.py:296-297`）。⇒ merge 後この step は **2 回の `set_finger` 呼び出し**（左, 0.006）(右, 0.04)、または 1 回の `set_fingers(0.006, 0.04)`。原始化自体は妨げない。
3. **scope**: これは **scripted 原始だけ**の merge。**learned grasp（1a acquire-grasp=CLAMP の auto-close）は吸収しない**（auto-close は policy 内部で、`set_finger` 呼び出しでない）。⇒ grip 分割と整合: **1b re-tighten + half_release + full_release がこの 1 つの scripted `set_finger(side,target)` に畳まれる**。基底が 1 つ減る。
4. ⚠ **schema ≠ realization**: これは schema(vocab)の言明。finger target を**物理 sim にどう効かせるか**（制御 API 経路）は control-method の court（07-20 に p5 から外れた）。`interpolate_fingers` は `fk_state.joint_q`（target 計算用の FK scratch）を書くので、sim 側 finger 制御の compliance は別軸・p4 lane。私はここでは制御方式を裁定しない。

## 3. side 座標（pX §4 見立て）への schema 事実の照合

pX 見立て:「基底が own-frame side-agnostic なら side は合成グラフ側の座標で足り obs 入力不要」。**schema 事実と一致する:**
- **scripted finger 原始**: side は明示的な**呼び出し引数**（left_target vs right_target）で obs でない ⇒ side = グラフ座標。✓
- **learned CLAMP**: side は own-frame 暗黙（per-arm）・side-agnostic ⇒ side は obs 入力でない。✓
- ⇒ **両者とも side を obs 入力にする必要はない。** pX の見立ては code と整合。（唯一 side が schema に入るのは、pS が明示 side スカラを要求する場合のみ = §4 の pS 判断。）

## 4. 非主張
- 私は schema 一致（=merge 可）と正しい signature（side も引数）を返しただけ。原始の語彙化・命名は pX+pS。
- realization（制御 API 経路）は control-method の court ゆえ裁定しない。
- 新実装・env 変更・訓練は着手しない。

# §14.27 bank 可否 — 裁定（p11 ARM-CONTROL-DESIGN, 2026-07-21）

**Author:** ARM-CONTROL-DESIGN (`w2:p11`)。**Status:** RULING v1.0 — **proposal**（landing = p4 経由）。
**対象:** `P5_CONTROL_METHOD_ANSWER_PRESERVED_20260721/sec_14_27.md`（保存版 sha256 先頭 `0cee3583cc6f04a3`、著者 p5、未 bank）。
**任務根拠:** role brief §任務2（`ARM_CONTROL_DESIGN_ROLE_BRIEF_p11_20260721.md` @ `2887037c9f`）+ p4 承認（2026-07-21 13:15 JST「§14.27 は `_pp` 実測後の裁定で可」）。

⛔ 本書は**設計軸の裁定のみ**。実装しない・走らせない・削除しない。disposition の実行は所管 arc + p4/Rs。

---

## 0. 裁定（3 行）

1. **論証本体と一般規則は BANK 可**（単一 class DRIVE / bind = 全 consumer / F-α / F-β / [R-E] / [H-1] / 訂正 #27 / citation 訂正）。所管移動によって無効化される種類の議論ではない。
2. ⛔**ただし §14.27 (4) は as-written では bank 不可** — escalation の根拠 2 本が**両方とも失効**している（premise 失効 + 事実誤り）。
3. ⭐**escalation 自体は別根拠で存続する。** 実測で `_pp` は **ケーブル全 DOF を凍結**しており、これは裁定 B の認可例外「clip 側がケーブルを保持する機構」**より広い**。（⚠ ただし腕関節角にも指にも触れていない。）

---

## 1. 実測（全て閉クエリ・producing commit 直読 or as-read 明示）

### 1.1 `_pp` の実体（`r_fc0_c2_smoke_77.py`、committed blob @ `7ab1cc313f`、blob sha256 先頭 `53ed88a73df9f7f9`）

```python
def _pp(model, state, solver, contacts, si):          # :72
    st = _ops(model, state, solver, contacts, si)
    if _PIN["active"]:
        jq = st.joint_q.numpy();  jq[ARM_Q:] = _PIN["jq"];  st.joint_q.assign(jq)    # :75
        qd = st.joint_qd.numpy(); qd[ARM_Q:] = 0.0;         st.joint_qd.assign(qd)   # :76
        md = solver.mj_data                    # RENDER source — freeze it too
        md.qpos[ARM_Q:] = _PIN["mjq"]; md.qvel[ARM_Q:] = 0.0                         # :78
        mujoco.mj_forward(solver.mj_model, md)
    return st
T.physics_step = _pp                                   # :83 ← module top level
```
活性化 = `:256-258`（`joint_q[ARM_Q:]` と `mj_data.qpos[ARM_Q:]` を snapshot して `active=True`）。

### 1.2 ⭐ `[ARM_Q:]` が指すもの（SSOT 実測）

- `ARM_Q = 2 * T.JOINTS_PER_ARM`（`:57`）
- `JOINTS_PER_ARM = ROBOT_NUM_JOINTS` = **14**（`task_config.py:42` 逐語「14: per-arm stride for joint_q arrays」）
- ⇒ **`ARM_Q = 28`**
- 両ロボットの座標 = arm `{0-5, 14-19}` / gripper `{6-13, 20-27}`（`test_newton_clip_routing.py:1771-1776`）⇒ **全て < 28**

⇒ **`[28:]` = 両ロボットの後 = ケーブル側 DOF。** §14.27 の読み（「両腕を除いた cable 側」）は **正しい**。

### 1.3 tracked 状態（§14.27 の主張と食い違う点）

| file | tracked | HEAD | `7ab1cc313f` | **c52 `46a59e7831`**（§14.27 の測定元） | provenance |
|---|---|---|---|---|---|
| `r_fc0_c2_smoke_77.py` | ✅ **Y** | Y | Y | ✅ **Y** | producing commit で pin 可 |
| `r_s71_bothhook_c1_76.py` | ⛔ N | N | N | — | **as-read のみ**（sha256 `4a6cfa74a7bf6652`・mtime 2026-06-21 22:16:33） |
| `r_s71_clip_dropin_72.py` | ⛔ N | N | N | — | **as-read のみ**（sha256 `707a266709fdfd2b`・mtime 2026-06-21 18:47:51） |

`git check-ignore` = 該当なし（ignored ではない）。初出 commit = `d2563368d5`。

### 1.4 F-α sink census（閉クエリ `physics_step\s*=`、worktree 除外）

**`T.physics_step = _pp` は 3 file が同一パターンで保持**（いずれも `:83`・`_pp` は `:72`・freeze 行は `:75/:76/:78` で行番号まで一致）:
`r_fc0_c2_smoke_77.py` / `r_s71_bothhook_c1_76.py` / `r_s71_clip_dropin_72.py`

別系統（restore 付き記録 wrapper・cable freeze なし）= `s5_p1_probe{,_rev4..rev8}.py` / `s5b_entry_probe{,_rev2}.py` の `T.physics_step = R4.recording_step` ⇔ `= R4._orig_step`。

⭐ **rebind は module 最上位 = import 時に起きる**（`__main__` 配下でない）⇒ **import しただけで共有 symbol が差し替わる**。
production import は **0**（閉クエリ）— 唯一の参照は sibling の**コメント** `r_fc0_c2_pen_crosspv_opssup.py:92`「forked from r_fc0_c2_smoke_77, render stripped」。3 file とも `if __name__ == "__main__": sys.exit(main())` の standalone script。

---

## 2. 裁定の内訳

### 2.1 ✅ BANK 可（無条件）

| 項目 | 判定 | 理由 |
|---|---|---|
| class = 単一 `DRIVE` / `MIGRATION_PENDING`・consumer 別分割 却下 | ✅ ADOPT | 述語（「この行は robot joint state を kinematic に書くか」）が 6 行全てで真。`gripper_dynamic` は extent を変え kind を変えない。extent 差で割ると remediation 義務が同一な 2 class ができ per-consumer 免除の入口になる — 論証が自足 |
| bind = 全 consumer（B0/B1 部分 bind 不可） | ✅ ADOPT | 「B0/B1 closure ⊊ symbol closure」の実測（外部 5 callsite 中 1・同 module 54 callsite が非 B0/B1） |
| 訂正 #27 = [R-E] 静的 retire 条件への差替 | ✅ ADOPT | 「live consumer 無なら retire」は否定の全称命題で静的には satisfy も refute も不能。**RUN が CLOSED の場面で RUN レグを要求する解除条件を書いていた**という自己訂正は正しい。一般則「解除条件は偽を示せる形で書く」も採る |
| citation 訂正 `policy_route_runner:506` → `:483` | ✅ ADOPT | 事実は真・行番号のみ |
| **F-α**（rebind sink を guard 契約に追加） | ✅ **ADOPT・さらに強化**（§2.3） | 静的 closure は rebind に健全でない。**実測で裏づけ増**（下記） |
| **F-β**（untracked consumer を 3 択で disposition） | ✅ **ADOPT・規則は CONFIRM**（⚠ 事例は差替、§2.2） | 規則自体は正しく、**むしろ実測で正当性が上がった** |
| [H-1] Z-Check 移管条件（`gripper_dynamic=True` path 限定 + 入口 fail-closed assert） | ✅ ADOPT | 移管先が 6 FAIL 行の consumer になると貫通述語が FK 指令の関数になり **gate が識別しなくなる**。fail-OPEN / `found` 短絡の 2 欠陥を逐語移植しない注意も妥当 |

### 2.2 ⛔ BANK 不可（as-written）— §14.27 (4) escalation

**根拠 2 本が両方とも失効:**

1. **premise 失効** — (4) は「**Rs 2026-07-19『kinematic 完全削除（pin 含む）』directive の射程内**」を escalation 根拠に置く。この directive は **裁定 B（`LEDGER:35`）で superseded**。
2. **事実誤り** — (4) の見出しは「**untracked** pin wrapper」。⛔ **`r_fc0_c2_smoke_77.py` は tracked**（§1.3。§14.27 自身の測定元 c52 `46a59e7831` でも tracked）。F-β の理由づけ「誰も pin できず、誰も再検証できない」は**この file には当たらない** — 実際に 4 commit で pin した。

⭐ **ただし escalation は破棄しない — 別根拠で存続する（下記 2.4）。**

⚠ **失敗の型（記録）**: §14.27 は事例集合を**審査対象の材料（c52）から作った**ため、(a) 名指しした 1 件を誤分類し (b) 同一パターンの 2 件を取り落とした。
= `feedback-never-source-the-verification-set-from-the-claim-under-review-2026-07-21`。**私の census は独立の閉クエリから構成した。**

### 2.3 ⭐ F-α / F-β は事例を差し替えて**強化**される

- **F-β の真の対象 = `r_s71_bothhook_c1_76.py` / `r_s71_clip_dropin_72.py`**（§1.3）。両者は producing commit を持たず **provenance が mtime のみ** ⇒ §14.27 が書いた「pin closure の外・exact-sha 契約が及ばない・第三状態」が**文字どおり成立するのはこの 2 件**。
- **F-α の census = 1 でなく 3**、しかも **import 時 rebind**（§1.4）。guard が「呼び出し側 sink のみ」を見る限り 3 件とも見えない。⇒ §14.27 の guard 契約追加要求は**過小でなく妥当、対象数だけ上方修正**。

### 2.4 ⭐ 新規 — `_pp` は裁定 B の認可例外より広い（設計軸の実質論点）

裁定 B canonical =「kinematic の唯一の認可例外 = **clip-retention pin**（＝ **clip 側がケーブルを保持する機構**）」。

`_pp` の実測（§1.1/§1.2）:

| 述語 | 実測 | 裁定 B 上の位置 |
|---|---|---|
| 腕関節角を直接書くか | ⛔ **否**（`[28:]` は arm `{0-5,14-19}` を含まない） | 不許可事項に**当たらない** |
| 指を kinematic close するか | ⛔ **否**（gripper `{6-13,20-27}` を含まない） | 同上 |
| `update_kinematic_bodies` / weld / attachment か | ⛔ 否 | 同上 |
| **clip の所でケーブルを保持するか** | ⛔ **否 — ケーブル全 DOF を凍結**（`joint_q` 全置換 + `joint_qd` 全零化 + render state 凍結 + `mj_forward`） | ⚠ **認可例外の範囲外**（広すぎる） |

⇒ **「腕・指に触れないから不許可事項ではない」が「だから認可例外である」とは言えない。** 認可されたのは *clip 側の保持機構* であって *ケーブル全体の凍結* ではない。
⇒ **escalation は存続する** — ただし根拠は「07-19 directive の射程」ではなく「**裁定 B の例外 scope を超える機構が、tracked 1 + untracked 2 の計 3 file に存在する**」。

⚠ **非主張**: これらが **live（実際に exercise される）とは主張しない**（p5 の非主張を継承）。production import = 0 は測ったが、直接実行の履歴は測っていない。⛔ 削除・改修を勧告しない（disposition = 所管 arc + p4/Rs）。

---

## 3. 勧告（proposal・実行しない）

1. **§14.27 を bank する** — ただし (4) を §2.2 + §2.4 で置換し、F-α census を 3、F-β 事例を untracked 2 件へ差し替えたうえで。著者 p5 は所管外ゆえ、**訂正版の起草は私（p11）が担う**のが筋と考える（p5 は「指示あれば訂正文案は起草する」と表明済・`P5_ANSWER_TO_P4_20260721.md:31`）。
2. **裁定 B の scope 照会を 1 件 surface** — 「ケーブル全 DOF 凍結」は認可例外に含まれるか。私の読みでは**含まれない**（例外は clip 側の保持機構）。⚠ これは **§0 不変前提の解釈**ゆえ、私は裁定せず **p4 → Rs へ上げる**（guardrail 遵守）。
3. **F-β disposition** は 3 択（track / 削除・隔離 / 実行不能証拠つきで closure 外登録）のうち、standalone script かつ production import 0 という実測から **(iii) が自然**と考えるが、**決めるのは所管 arc + p4/Rs**。

## 4. 非主張

- class を動かしていない・census 35 を動かしていない・bar を動かしていない。
- `_pp` が live とも dead とも言っていない。
- 削除・改修を実行していない・勧告していない。
- 物理妥当性の判定をしていない。

## 5. L 自己申告

**L1**（新規 file 1 本・記録 + 設計軸裁定・コード 0・rule file 非接触・landing なし）。
⚠ §2.4 は **§0 不変前提の解釈に触れる論点**ゆえ、裁定せず surface に留めた（触れたら STOP → p4 → Rs の guardrail 適用）。
commit = explicit pathspec + `--no-verify`（DDR #35）。

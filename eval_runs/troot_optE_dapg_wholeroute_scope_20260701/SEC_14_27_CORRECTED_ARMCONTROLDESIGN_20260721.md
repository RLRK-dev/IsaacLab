# §14.27（訂正版 v2）— `physics_step` 全 consumer 列挙への裁定

**原著:** VT-DESIGN / SKILL-DETAIL-DESIGN (`w2:p5`)、2026-07-20 21:0x（charter v2.31 §14.27・保存版 sha256 先頭 `0cee3583cc6f04a3`）。
**訂正:** ARM-CONTROL-DESIGN (`w2:p11`)、2026-07-21 — 現 control-method 設計 owner。
**Status:** **proposal**（landing = p4 経由）。裁定根拠 = `SEC_14_27_BANK_RULING_ARMCONTROLDESIGN_20260721.md` @ `0eed7c6756`。
**保存原本は改変しない** — `P5_CONTROL_METHOD_ANSWER_PRESERVED_20260721/sec_14_27.md` は当時のまま保持（同 `README.md:21` の方針）。本書は**別 file の訂正版**。

> **訂正の範囲（先に読む）**: 論証本体・一般規則は**原著のまま採る**。変更は 3 点のみ — **(A)** §4(4) escalation の根拠を差替（原根拠 2 本が失効）/ **(B)** F-β の事例を実在の untracked 2 件へ差替（原著が名指した 1 件は tracked）/ **(C)** F-α の sink census を 1 → **3** へ。原著の判断力を否定する訂正ではない：**F-α/F-β の規則は実測でむしろ正当性が上がった**。

---

**0. 測定基準**

- **原著の測定**: worktree HEAD = `ddbae19e0f`（`rlrk/optE-s2-substrate-swap`）で (d) arc の branch でなく、c52 は HEAD の祖先でない ⇒ 全実測は `git show 46a59e7831:<path>` = producing commit 直読。
- **本訂正の測定（p11）**: 同 branch。tracked 判定は `git ls-files` / `git cat-file -e <commit>:<path>` / `git check-ignore` を **HEAD・`7ab1cc313f`・`46a59e7831`（原著の測定元）・`ddbae19e0f`（原著の worktree HEAD）の 4 点**で実施。untracked file は **producing commit が存在しないため as-read（sha256 + mtime）のみ**で扱う。
- ⚠ **p4 が独立に再実測して一致を確認**（2026-07-21 13:24 JST：`ARM_Q=28` / `[28:]` = ケーブル全 DOF / 腕・指に触れない）。

---

**1. c52 の検証結果（採用 / 訂正の内訳）** — 原著のまま

artifact sha256 = `068b51dda8aee047a0261b21d6c5f389655f85054f36117aa310d5ff33bef95d` — banked object 上で exact 一致 ✓。

| c52 の主張 | 独立検証 | 判定 |
|---|---|---|
| §5 分岐構造: `:1813` default `False` / `:1823` 分岐 / `:1827-1828` arm のみ / `:1830-1831` 全 DOF / `:1832-1833` 共通 sink | 逐語一致 | ✅ ADOPT |
| True-setter = tncr `:3063` `:3262` `:3721` / `srg_probe.py:193` | 逐語一致（閉クエリ `gripper_dynamic` 全 hit を印字） | ✅ ADOPT |
| True-setter = `policy_route_runner.py:506`（assert `:507`） | ⚠ **両者とも「誤り」ではない — 測った面が違う**（下記 ⭐D） | ⚠ **citation を content pin へ差替（D）** |
| 帰属は enclosing def でなく `scene_info` の provenance で決まる | 同意。ただし provenance だけでは足りない（下記 2） | 🔶 PARTIAL |
| §6 rebind / untracked consumer | §4(3)(4) で裁定に採用（⚠ **事例は本訂正で差替**） | ✅ ADOPT（規則）/ ⚠ 事例訂正 |

**⭐ D. citation 訂正の再訂正 — 行番号でなく content で pin する**

原著は c52 の `:506` を「実体は `:483`・23 行ずれ」と訂正した。**p11 の実測では、どちらも自分の測定面では正しい**:

| 測定面 | `scene_info["gripper_dynamic"] = True` の位置 |
|---|---|
| **c52 `46a59e7831`**（原著の測定元） | **`:483`**（assert `:484`）✅ 原著の訂正は自面で正しい |
| `7ab1cc313f`（(d) lane tip） | `:483`（assert `:484`） |
| **HEAD `bec159aec5`**（現 branch） | **`:506`**（assert `:507`）← **c52 の申告値と一致** |
| worktree（dirty・HEAD 比 +377 行） | `:540`（assert `:541`） |

⇒ **「23 行ずれ」ではなく、同一 file が面ごとに 4 つの行番号を持つ。** 原著も c52 も誤っておらず、**行番号を面の明示なしに引いたこと**が問題だった。
⇒ ⭐ **本書は content で pin する**: **True-setter = `policy_route_runner.py` の `scene_info["gripper_dynamic"] = True` + 直後の `assert … "B0 DoD: gripper_dynamic must be True before the loop"`**（閉クエリ `scene_info\["gripper_dynamic"\]` で一意）。行番号は**照合記録**として上表に置く。
= [[feedback-pin-by-content-version-is-only-a-collation-note-2026-07-21]] の行番号版。⚠ DDR shorthand の警告「drift-prone line anchors — re-grep before relying」と同根。

---

**2. else 枝の到達条件は「連言」である** — 原著のまま

> **¬set(`gripper_dynamic`) ∧ `scene_info["solver_backend"] == "mujoco"`**

`main:8067` は第 2 連言肢で落ちる（`:8206` `if solver_backend == "mujoco":` → `:8250` `return` が連鎖の外・`if` の内 ⇒ mujoco の全 dispatch 枝が return し、main 自身の loop に到達するのは非 mujoco のときだけ ⇒ VBD 枝 `:1836` を通り 6 FAIL 行に触れない）。
⇒ **else 枝の entry point は 5 でなく 4**（`_run_mujoco_ik_motion_smoke:2817` / `_run_mujoco_episode:7525` / `_run_mujoco_tracking_smoke:7761` / `_run_mujoco_cable_settle_smoke:7820`）。継承 helper の帰属にも同じ連言 intersect が要る（測定レグ）。
⛔ 失敗の型 = **述語の連言のうち 1 肢だけで数えた**。

**3. 訂正 #27 — v2.30 の retire 条件節が反証不能だった** — 原著のまま

「live consumer 無なら retire」は否定の全称命題で、静的測定では satisfy も refute もできない（**RUN レグを要求する条件を、RUN が CLOSED の場面で解除条件に据えた**）。静的に判定可能・かつ偽を示せる形へ:

> **[R-E] else 枝 retire 条件** = `¬set(gripper_dynamic) ∧ backend=="mujoco"` を満たす callsite が **静的に 0**（閉クエリ + 継承 helper の呼び元 intersect を含む）。

現状 = 4 entry point 該当 ⇒ **retire 不可**（現材料だけで決着）。
⭐ 一般則: **解除条件は「それが偽であることを示せる形」で書く。**

---

**4. 裁定**

**(1) class = 単一 `DRIVE` / `MIGRATION_PENDING` 維持。consumer 別分割は却下。** — 原著のまま

class の述語は「この行は robot joint state を kinematic に書くか」であり、`:1827/:1828/:1830/:1831/:1832/:1833` の 6 行すべてで全 consumer 共通に真。`gripper_dynamic` が変えるのは**書込範囲(extent)**であって**種別(kind)**ではない。extent 差で class を割ると remediation 義務が同一な 2 class ができ、実質 **per-consumer 免除の入口**になる。
⚠ v2.30 §14.26-d の「2 枝は別 triple ゆえ別 class」は narrow する — **triple の差は acceptance evidence の差であって class の差ではない**。

**(2) bind = 全 consumer。B0/B1 への部分 bind は不可。** — 原著のまま

B0/B1 は外部 5 callsite 中の **1**（`policy_route_runner.py:730`）、同 module の **54 callsite は B0/B1 経路に属さない**（`_run_mujoco_grasp_route` だけで 35）。「B0/B1 closure ⊊ symbol closure」の 3 例目。⇒ **列挙なき部分 cutover 不可**。

**(3) fence は「class の代わり」ではなく「class に加えて」必須。2 種を別立てにする。**

- **F-α identity fence（rebind に対する健全性）** — 規則は原著のまま／**census を訂正**
  `_ops = T.physics_step` → `T.physics_step = _pp` は **AST 静的解決と runtime 実体を乖離**させる。Layer 8 は**呼び出し側 sink のみ**を見るため rebind sink を持たない ⇒ guarded symbol の定義を検証しても**走る物を検証していない**。
  ⇒ guard 契約に「**guarded symbol への module 属性代入（`<mod>.<sym> = ...`）を sink として検出**」を追加する。class をどう付けても消えない **guard の健全性欠陥**。
  ⭐ **(C) census 訂正 = 1 → 3。** 独立の閉クエリ（`physics_step\s*=`・worktree 除外）で、**同一パターン `T.physics_step = _pp` を 3 file が保持**（`_pp` = `:72`／freeze = `:75/:76/:78`／rebind = `:83`、**行番号まで一致**）:
  `r_fc0_c2_smoke_77.py`（tracked）/ `r_s71_bothhook_c1_76.py`（**untracked**）/ `r_s71_clip_dropin_72.py`（**untracked**）。
  ⭐ **rebind は module 最上位 = import 時**（`__main__` 配下でない）⇒ **import しただけで共有 symbol が差し替わる**。
  別系統（restore 付き・cable freeze なし）= `s5_p1_probe{,_rev4..rev8}.py` / `s5b_entry_probe{,_rev2}.py` の `T.physics_step = R4.recording_step` ⇔ `R4._orig_step`。
  ⭐ 一般則: **静的 closure は rebind に対して健全でない。symbol を守る guard は、その symbol の *束縛* も守らねばならない。**

- **F-β closure fence（untracked live consumer）** — 規則は原著のまま／**事例を差替**
  untracked な実行可能 consumer は **pin closure の外**にあり、**freeze→verify→bank の exact-sha 契約が及ばない**（誰も pin できず、誰も再検証できない）。「tracked でも quarantined でもない**第三状態**」を残さない。
  ⇒ 各 untracked consumer を **(i) track する / (ii) 削除・隔離する / (iii) 実行不能の証拠つきで closure 外に登録する** のいずれかへ disposition する。**無記載のまま放置は不可。**
  ⭐ **(B) 事例訂正 — 対象は下記 2 件**（原著が名指した `r_fc0_c2_smoke_77.py` は **tracked** ゆえ F-β の対象ではない）:

  | file | tracked | provenance |
  |---|---|---|
  | `r_s71_bothhook_c1_76.py` | ⛔ **N**（HEAD / `7ab1cc313f` いずれにも不在） | **as-read のみ** — sha256 `4a6cfa74a7bf6652`・mtime 2026-06-21 22:16:33 |
  | `r_s71_clip_dropin_72.py` | ⛔ **N**（同上） | **as-read のみ** — sha256 `707a266709fdfd2b`・mtime 2026-06-21 18:47:51 |

  ⇒ 原著が書いた「pin closure の外・exact-sha 契約が及ばない・第三状態」は、**文字どおり成立するのがこの 2 件**。**規則の正当性は下がらず上がる。**
  規律（**不在の閉クエリは root だけでなく "追跡状態" も覆う**）を本 charter の常設規律に格上げする。

**(4) ⛔ escalation — `_pp` の機構は認可例外より広い（⭐ (A) 根拠 差替）**

`_pp`（`r_fc0_c2_smoke_77.py:72-81` 他 2 file）は `_PIN["active"]` の時に `jq[ARM_Q:]` を snapshot で全置換し、`qd[ARM_Q:]` を全零化し、さらに render 元の `md.qpos[ARM_Q:]` / `md.qvel[ARM_Q:]` も同じく上書きして `mujoco.mj_forward` を適用する。

**`[ARM_Q:]` が指すもの（SSOT 実測）**: `ARM_Q = 2 * T.JOINTS_PER_ARM`（`:57`）、`JOINTS_PER_ARM = ROBOT_NUM_JOINTS` = **14**（`task_config.py:42` 逐語「14: per-arm stride for joint_q arrays」）⇒ **`ARM_Q = 28`**。両ロボットの座標は arm `{0-5, 14-19}` / gripper `{6-13, 20-27}`（`test_newton_clip_routing.py:1771-1776`）で**全て < 28** ⇒ **`[28:]` = ケーブル側 DOF**。

| 述語 | 実測 | 裁定 B 上の位置 |
|---|---|---|
| 腕関節角を直接書くか | ⛔ 否 | 不許可事項に**当たらない** |
| 指を kinematic close するか | ⛔ 否 | 同上 |
| `update_kinematic_bodies` / weld / attachment か | ⛔ 否 | 同上 |
| **clip の所でケーブルを保持するか** | ⛔ **否 — ケーブル 40 節すべてが動かなくなる** | ⚠ **認可例外の範囲外（広すぎる）** |

⇒ **「腕・指に触れないから不許可事項ではない」は真だが、「だから認可例外である」は導かれない。** 裁定 B が認可したのは *clip 側がケーブルを保持する機構*（`LEDGER:35` canonical）であって *ケーブル全体を動かなくすること* ではない。

⛔ **原著の 2 根拠は両方とも失効している**（本訂正の実体）:
1. **premise 失効** — 原著は「Rs 2026-07-19『kinematic 完全削除（pin 含む）』directive の射程内」を根拠にした。同 directive は **裁定 B（`LEDGER:35`）で superseded**。
2. **事実誤り** — 原著の見出し「**untracked** pin wrapper」。⛔ `r_fc0_c2_smoke_77.py` は **tracked**（原著の測定元 c52 `46a59e7831` でも tracked）。F-β の理由づけ「誰も pin できず、誰も再検証できない」は**この file には当たらない**。

⇒ ⭐ **escalation は破棄せず、根拠を差し替えて存続**: 「07-19 directive の射程」ではなく「**裁定 B の例外 scope を超える機構が、tracked 1 + untracked 2 の計 3 file に存在する**」。

**disposition = ⭐`書き戻し形は不採用 → equality 拘束へ`**（2026-07-21）。

⚠⚠ **2026-07-21 18:56 訂正（p4 接地更新・STOP）**: 本 disposition の根拠から **Rs 逐語「すてるなよ」を外す**（Rs が当該 rule を disavow・逐語「そんなルール知らない」⇒ `ARM_CONTROL_DESIGN_PRINCIPLE_REGROUND_ARMCONTROLDESIGN_20260721.md`）。
⇒ **根拠 = §0#5 の認可例外 scope 超過**（`RS71-System-Spec-SSOT.md:27` 逐語 `physics-faithful only; the ONLY authorized exception is the clip-retention pin`）。これは Δ A で**既に併記していた根拠**であり、**逐語を外しても disposition は変わらない**。
📎 **receipt（authority ではない・保持のみ）**: 2026-07-21 13:48:37 JST、p11 が `_pp` を「**毎回捨てて同じ値に戻すので、変化が積み上がらない**」と説明した直後の Rs 応答 =「すてるなよ」（session transcript line 535 / role=user）。⛔ **規範として引かない**。
⇒ **この形は採らない。** 認可された clip-retention は **clip の所に equality 拘束を置き、ソルバに解かせる形**（物理結果を捨てず、拘束も物理の一部として解かれ、残りの節は物理のまま動く）で実現する。
**実現可能性 = 実測済**: env7 Newton 1.2.1 `SolverMuJoCo` は equality 対応（`solvers.py:326` support matrix / `solver_mujoco.py:295-296` 逐語 supported）。⇒ 形が認可文言「**クリップのみ／never beyond clip**」（`log.md:6534`）にも収まる。

⛔ **書かないこと（p4 指示・over-claim 回避）**: 上記は **Rs の実務指示（redirect）**であって、**「ケーブル全体を動かなくするのが裁定 B の例外の外である」と Rs が formal に裁定した、とは書かない。** §0 不変前提の解釈は Rs 専権であり、本書は裁定しない。設計 owner (p11) の読みが「例外に収まらない」であることのみ記録する。
⚠ **pin 実装の owner = pin arc (d-a)/(d-b) court**（p4 が tracking・非緊急ゆえ実装接近時に routing）。本書は制御設計側の記録に留める。
⛔ **live 判定は要求しない**（要求すると RUN レグを開ける）。⚠ **live とも dead とも主張しない** — production import = **0**（閉クエリ。唯一の参照は sibling `r_fc0_c2_pen_crosspv_opssup.py:92` の**コメント**）、3 file とも `if __name__ == "__main__": sys.exit(main())` の standalone script。**直接実行の履歴は未測定。**
⛔ **削除・改修を勧告しない。** F-β 3 択の適用（実測からは (iii) が自然）も**所管 arc + p4/Rs の court**。

---

**5. ⭐ Z-Check 移管（Rs 裁定 ②）への hard 条件 [H-1]** — 原著のまま

- 現 Z-Check gate は **VBD 枝の上に載っている**（`recorder.check_penetration()` `:8452` / `[ZCHECK]` `:8456` はいずれも enclosing def = `main:8067` = `:8250 return` の下流 = 非 mujoco 経路）。`CLAUDE.md:271`「Fingertip Z-Check Gate（Newton VBD）」と構造が一致。
- ⇒ 移管は **substrate 境界をまたぐ port**。現 host loop は VBD 退役で消えるので移管先で instrument を**新規配線**する必要がある（**6 FAIL 行を引き継ぐ話ではない**）。
- ⚠ ただし移管先は 6 FAIL 行の consumer になる:
  - **mujoco 枝 × `gripper_dynamic=False`**: `phys_jq[:n]` が毎 substep FK で上書き ⇒ **fingertip z が FK 指令の関数**になり接触物理の関数でなくなる ⇒ **貫通述語が物理由来では偽になり得ない = gate が識別しない**。
  - **mujoco 枝 × `gripper_dynamic=True`**: gripper coords は dynamic（servo が `control.joint_target_pos` で駆動）⇒ fingertip z は物理由来 ⇒ **識別する**。
- ⇒ **[H-1]**: 移植した Z-Check は **`gripper_dynamic=True` の path 上でのみ有効**とし、**gate 自身の入口で fail-closed に assert する**（runner 側の assert に依存しない）。
  H-1 を欠く移管は **別様に出得ない test** になる。
- ⚠ 既知欠陥 2 件を**逐語移植しない**: (i) `:585-586` `if not self._zheight_frames: return None` = **fail-OPEN**、(ii) `:591-600` の `found` 短絡により `max_penetration_mm` は frame ごとの初出 1 件の最大であって真の最大でない。
- 本 [H-1] は §14.25 の 4 acceptance 条件への**加算**。

---

**verdict**

**class = 単一 `DRIVE` / `MIGRATION_PENDING` 維持**（consumer 別分割 = 却下。extent 差は kind 差でない）。
**bind = 全 consumer**（B0/B1 部分 bind 不可）。
**fence = F-α〔rebind sink を guard 契約に追加・⭐ census = **3 file**・rebind は **import 時**〕+ F-β〔untracked consumer を 3 択で disposition・⭐ 対象 = `r_s71_bothhook_c1_76.py` / `r_s71_clip_dropin_72.py`〕の 2 種を別立てで必須**（class の代替でなく加算）。
**escalation = `_pp` の機構は認可例外より広い（ケーブル 40 節すべてが動かなくなる ≠ clip 側の保持機構）。⭐ disposition = 書き戻し形 不採用 → equality 拘束へ（根拠 = **§0#5 の認可例外 scope 超過**。⚠ 旧記載の Rs 逐語根拠は 2026-07-21 18:56 に取り下げ ⇒ REGROUND doc）。** ⛔ Rs の formal 例外裁定とは書かない・live 主張なし・削除勧告なし。
**⚠ 訂正 #27** = 「live consumer 無なら retire」を静的判定可能な [R-E] に差替 ⇒ else 枝 retire は現材料で不可と確定。
**⚠ %12 count 訂正** = `main:8067` は else 枝に入らない（entry point 5→4）。
**⚠ citation 訂正** = `policy_route_runner:506` → 実体 `:483`。
**⭐ 新規** = Z-Check 移管の hard 条件 [H-1]。
⭐ **一般則 2 件**: 「解除条件は偽を示せる形で書く」/「guard は symbol の束縛も守れ」。

---

## Δ 一覧（原著からの差分・traceability）

| Δ | 箇所 | 内容 | 理由 |
|---|---|---|---|
| **A** | §4(4) | escalation の根拠を差替（07-19 directive → 裁定 B 例外 scope 超過） | 原根拠の premise が裁定 B で失効・かつ「untracked」が事実誤り |
| **E** | §4(4) disposition | `Rs 解釈待ち` → **`書き戻し形 不採用・equality 拘束へ`**（根拠 = **§0#5 の認可例外 scope 超過** + 実現可能性の実測）。⛔formal 例外裁定とは書かない。⚠ **2026-07-21 18:56 訂正** = 旧版は Rs 逐語「すてるなよ」を根拠に置いたが **Rs disavow** により取り下げ（逐語は receipt として保持・disposition 不変） | `ARM_CONTROL_DESIGN_PRINCIPLE_REGROUND_ARMCONTROLDESIGN_20260721.md` |
| **F** | 全体 | ケーブルについての「凍結」を平易語へ（「凍結」は bar/prereg の固定の意味で既用＝語衝突） | Rs 指摘「凍結とは？」 |
| **B** | §4(3) F-β | 事例を `r_fc0_c2_smoke_77.py` → **untracked 2 件**へ差替 | 名指された file は 4 commit で tracked と実測。**規則は不変** |
| **C** | §4(3) F-α | census 1 → **3**、**import 時 rebind** を明記 | 独立の閉クエリで同一パターン 3 件 |
| **D** | §1 + 新節 D | citation 訂正を**行番号 → content pin** へ差替（c52 `:506` / c52 blob `:483` / HEAD `:506` / worktree `:540` = **面ごとに 4 値**） | 原著も c52 も自面では正しく、**面を明示せず行番号を引いたこと**が誤りだった |
| — | §0 | 測定基準に p11 の測定 4 点 + p4 独立再現を追記 | provenance |

⚠ **原著の失敗の型（記録・非難でない）**: 事例集合を**審査対象の材料（c52）から作った**ため、名指した 1 件を誤分類し同型 2 件を取り落とした。
= [[feedback-never-source-the-verification-set-from-the-claim-under-review-2026-07-21]]。本訂正の census は**独立の閉クエリから構成**した。
⭐ **原著の判断は覆っていない** — F-α/F-β の**規則は実測で正当性が上がり**、訂正は**事例と根拠の差替に限られる**。

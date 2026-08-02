## 前セッション完了: 2026-08-02 23:57 JST (p4 / UR15 sim・route 不動の根因除去)

⛔ 全 sha・全 log path・全経緯は **p4 正本**（上記）と、repo の
`eval_runs/troot_optE_dapg_wholeroute_scope_20260701/p4_ur15_sim_20260727/WHY_THE_ROUTE_NEVER_MOVED_20260802.md`
が正。以下は次セッションが最初の 5 分で必要とするものだけ。

### 何が起きていたか
route は **1 歩も進んでいなかった**（全 step「0.0%・全 tick 保留」）。追従門は各腕が自分の命令から
**5.18 mrad 以内**であることを要求し、実測の静止誤差は **L 18.14 / R 929.31 mrad**、**両腕は接触**していた。
⇒ 原因 = **経路の表し方**。`solve_ik` は答えを主値域へ丸め、ramp はその値へ直線補間するので、基部関節が
±π 付近だと**ほぼ一周逆向き**（274°/244°）に回り、途中で両腕が噛む。

### 何を直したか（全て既定 off の env flag・commit 済）
- `UNWRAP_SOLVE=1` — **unwrap を解きの中（経路検査の前）へ**。⚠ 解いた後の unwrap は効かない
  （丸めた経路で落ちた候補は既に捨てられている）。実測: **右腕 clear 0→8・静止誤差 L/R とも 0.00 mrad・両腕が正確に到達**
- `ARM_PATH=1` — もう一方の腕への**経路**検査（従来は姿勢のみ）
- `FURNITURE=1` — 鞍柱・テーブル（従来は**検査そのものが無かった**）
- `STEREO_HEAD=1` — 参照 cell に在り sim に無かった 240×85×75 mm の実体。⭐ 入れても結果は**完全同一**

### 次にやること（1 が最初）
1. **aim 解きの詰まりを測る**（走らせたが log が出ず未取得）:
   `cd ~/IsaacLab/eval_runs/troot_optE_dapg_wholeroute_scope_20260701/p4_ur15_sim_20260727 && UNWRAP_SOLVE=1 ARM_PATH=1 GRASP_CENTRE_X=-0.200 START_TRIES=240 /home/rlrk/env_isaaclab7/bin/python -u ur15_steps_wired.py > /tmp/aim.log 2>&1 &`
   → `grep "fell back) rejected against" /tmp/aim.log`
   ⭐ aim 解きは候補が **1〜2 個**しかない（`pose_only` で姿勢固定）。私が足した経路検査が乗ると
   「1 つの窮屈な選択肢」が「ゼロ」に変わり得る — 理由行がそれを言うはず
2. 6 中心を `UNWRAP_SOLVE=1` で掃く（−0.110 … −0.250、−0.200 以外）
3. push（**未 push 94 commit**・共有 branch なので Rs の一言待ち）

### 状態
- **走行中プロセス: なし**（23:55 実測）／未 commit = `MUJOCO_LOG.TXT` のみ
- ⚠ **MEMORY.md は 4 卓凍結中**（hook「圧縮せよ」vs Rs standing「圧縮するな」= Rs gate 第 4 項）
- ⛔ 設計判断（取付点・把持中心・冠寸法）は **p5 → Rs の court**。私は測定と計器修正のみ
- ⛔ pane 間 message は全て **`w2:p18` 経由**

### ⭐ Rs 指摘（本日）
**「問で停滞している」** — 測るたびに問いを増やし、本題の走行が止まっていた。**議論より実行**。
実際、止めて走らせたその日のうちに根因に届いた。

### ⭐ 本日一貫していた形
**「腕が到達しない姿勢は、clear であることでは安全にならない」**（driver 自身の docstring）。
マスト（07-28 に修正済）→ もう一方の腕 → 家具 → 経路の表し方、と **4 回**同じ文が出た。
私の誤りも 1 形だった: **label を読んで実体を見ない**（上限定数の文面 / gap の列 / file 名の draw 数 /
印の語 / 自分の parser の「0 件」）。

---

## 前セッション完了: 2026-07-21 01:40 JST (p4 RS-TECH-LEAD / w2:p4)

⚠ 本 file = LAST-WRITER 共有面。**p4 正本 = `handoff_cc_p4_rstechlead_control_method_20260719.md`（全 sha・全 verdict・全 arc はそちらが正）**。他 pane は各 per-pane file（MEMORY.md「Current Handoff」節）。

### Context
- **タスク（Rs 裁定 A・2026-07-21 01:0x）**:「**43 ステップ表の動作をロボットアームとコントローラで実現すること**」
- **DoD（Rs 指定）**:「**ロボットアーム、ハンド、フィンガを描画した動画**」。数値のみの報告は受入にならない
- **Phase**: **[CHECK] 完了**（基線 c67-c69 bank・pY PASS）。⛔`[CHANGE]` / `RUN` は**未開錠**
- **robot 確定**: **UR5e ×2 + Robotiq 2F-85**（Rs 明示）
- 参照 SSOT: `RS71-System-Spec-SSOT.md` §0 / LEDGER §35 + DDR#25/#31/#32 / `task_config.py` / p5 charter v2.30

### Vault SSOT checked（banked design 接地）
- **banked design SSOT** = `RS71-System-Spec-SSOT.md` §0 — **banked mechanism = DiffIK-only / no-kinematic-trick、唯一の例外 = clip-retention pin**
- ⭐**`RS71:28` に 2026-07-15 Rs 逐語が banked**:「クリップのみ pin を RL env に恒久配線しろ」「**CLIP-RETENTION ONLY — this authorizes no other kinematic exception**」（pY 発見）
- ⇒ 次セッションは **handoff narrative でなくこの banked design を ground truth にする**

### 完了タスク（本セッション）
1. SKILL admissibility 棚卸 **c54-c56**（pN PASS ×3 / pQ 引用 2/2 / p6 反映 + **DDR#31** 起票）
2. SKILL 分解能 材料 **c57-c66**（pN/pY PASS / pQ 精緻化 2 件 受入 / **DDR#32** 登録）
3. SKILL 所管の routing 訂正 **c60**（Rs 裁定「SKILL は pX が決める」）
4. 43 step controller 実現の基線 **c67-c69**（pY PASS）
5. `02-Workflow/HANDOFF.md` の旧前提 3 箇所を裁定 B へ訂正（p6 要請）

### 未完了・中断タスク
- **腕の actuator/DiffIK 駆動** — 未着手。理由 = **ブロッカー: p5 の `physics_step` class 裁定**が書換対象行そのものを扱う。難易度 **complex**
- **指の servo 化** — 未着手。理由 = 待ち。⚠**忠実 actuation が未実装**と判明し単純載せ替えでは済まない。難易度 **moderate**
- **Franka 由来の完全削除**（Rs 指示）— census 途中。理由 = 時間切れ + 設計判断待ち（`EE_TO_FINGERTIP` consumer 約 40・割付は `/geometric-design` 強制ゲート）。難易度 **complex**
- **`02-Workflow/HANDOFF.md` の commit** — 保留。理由 = 判断待ち（Findings 参照）

### Findings
- ⭐**43 step 経路は腕も指も kinematic**。`wet_run_full_sequence.py` は `gripper_dynamic` 未設定（閉クエリ 0 hit）⇒ 既定 `False` ⇒ `physics_step` else 枝 `phys_jq[:n]` で**全 DOF 毎 substep 上書き**。Rs 観察「フィンガは kinematic で実現していた」は**実測 TRUE**
- ⭐⭐**MJCF gripper actuator は死んでいる**。`2f85_koshape.xml:191-193` 逐語「orphaned `<actuator ... tendon="split">` is **SILENTLY skipped at parse**（verified live newton 1.0.0）」／4-bar `<equality>` も drop ／「**NOT a faithful gripper**」。`task_config.py:337`「**faithful actuated close is deferred**」⇒ **「指 servo は実証済み」は over-claim・撤回済**（5 箇所訂正）。型 = §運用15 第3 bucket **ABSENT-IN-CODE / wire-then-validate**
- ⭐**腕は asset に 6 position actuator を持つが build で意図的に無効**。`ur5e.xml:124-130`（size3 = kp2000/kd400/±150N·m、size1 = kp500/kd100/±28N·m）。しかし `newton_route_env.py:280-282` 逐語「every `negative_dofs`（**non-driver: arm**）carries **NO servo ke** — **A blanket-wired build fails here**」⇒ **腕を wire すると既存テストが FAIL**。テストの扱いも設計判断
- ⭐**Franka 由来の残存**: `franka|panda` 参照 約 170 file（大半 PhysX 期 legacy）。**code 自身が stale と申告する 7 件**が要注意。特に `EE_TO_FINGERTIP=0.220`（**Franka 値**）が `GRASP_Z`/`PUSH_Z` を決め、`newton_approach_cable_mujoco_env.py:195` 逐語「**stale Franka GRASP_Z=1.025** で指先が机に 40mm めり込む」。正 = `EE_TO_PINCH_CLOSED=0.2548` / `TIP_CLOSED=0.2757` / `OPEN=0.2609`（差 約 56mm）
- ⚠**census の構造的な穴**: Franka 由来は **grep で見つかるのはラベルのある分だけ**。由来コメントを失った値は文字列検索で原理的に不可視 ⇒ **実測による再導出**が要る
- ⚠**`02-Workflow/HANDOFF.md` に未 commit の全面書換**（2026-07-20 08:09 起点）。HEAD 115 行 vs 作業ツリー 56 行 = **+50/−109** ⇒ **commit すると 59 行の正味削除も landing する**
- ⚠**vault guard = FAIL 3**（dangling node-id `T-ROOT-OPS-SUPERVISOR` / `-CODEX` / `T-ROOT-RS-TECH-LEAD`）。出所は `log.md` の 2026-05-24 履歴で**私の編集とは無関係**

### 変更したファイル（このセッション）
- `eval_runs/.../SKILL_ADMISSIBILITY_INVENTORY_RSTECHLEAD_20260720.md` — 9 skill の admissibility 棚卸。意図 = (d) 残作業を「どの skill が selectable になるか」で表現
- `eval_runs/.../SKILL_GRANULARITY_MATERIALS_RSTECHLEAD_20260720.md` — 分解能の材料 v1.9。意図 = 設計を導出せず測れる量だけ提供
- `eval_runs/.../STEP43_CONTROLLER_REALIZATION_BASELINE_RSTECHLEAD_20260721.md` — 裁定 A の基線 + DoD + 裁定 B。意図 = 着手前の現在地固定
- `thread-vault/02-Workflow/HANDOFF.md` — 旧前提 3 箇所を裁定 B へ。意図 = **歴史記述を消さず読み替え注記**（書換は記録を嘘にする）
- memory: `project-sim-is-reality-no-kinematic-20260719`（pin 例外復活）/ `project-p4-purpose-build-the-skills-wmso-selects-2026-07-20`（新規）/ `project-skill-unit-vector-composition-direction-2026-07-20`（新規）/ `feedback-absence-claims-need-closed-query-…-2026-07-18`（追補）

### State Snapshot
- probe `pd1-arm-pd` HEAD = **`183c1bb5dc`（c69）**・**tree clean**
- **未 push = 31 commit**（`412f37ec10..HEAD`）。**source 変更 0**（`eval_runs/` docs のみ）。push 先 = **`fork`**（⛔`origin` は公開上流ゆえ不使用）
- **Layer 8 census = `LAYER8_FAIL=35` / `WARN=0`**（不変）
- 実行中プロセス **なし**。ハーネス **未起動**

### 次にやるべきこと
1. ⛔**self-start しない。** 待ちが 4 本:
   - **p5** — `physics_step` class 裁定（**腕の実装をブロック**）
   - **pX SKILL-DESIGN** — 分解能・単位ベクトル（SKILL は pX 所管）
   - **Rs** — (a) `[CHANGE]`/`RUN` 開錠 (b) 所管境界 p5/pS/pQ×pX (c) 単位ベクトル化の詳細 (d) `HANDOFF.md` commit 可否
   - **pY** — 裁定 B 逐語の 1 行確認を Rs へ照会中（**非 blocking**）
2. 開錠後の順序 = **指の servo 化 → 動画 → 腕の actuator/DiffIK**（腕は p5 裁定が前提）
3. Franka 削除は **census（ラベル分）＋ 実測再導出（ラベル無し分）の 2 本立て**。`task_config.py` は L3 かつ `/geometric-design` 強制ゲート

### 重要な文脈
- ⭐**裁定 B は新規の逸脱でなく banked spec への復帰**（`RS71:28` の 2026-07-15 逐語と一致・07-19 の側が outlier）。pY 発見
- ⭐**SKILL の決定権は pX**。私は「その動作を実現する制御側」のみ。43 step 表そのもの（分割・step 内容）は触らない
- ⭐**cross-lane 引用は path + sha256 + commit を必ず併記**（本 lane の artifact は `probe/pd1-arm-pd` にのみ在る）
- ⚠**本セッションで自分の over-claim を 2 回捕捉**（servo 実証済み / D0 draft を現行として引用）。いずれも **comment を読んで wired を確認しなかった**型。**指摘は欠陥クラスの標本 ⇒ bank 前に doc 全体へ機械 sweep**
- pane 構成が動いた: **`w2:pY` = T-ROOT-OPS-SUPERVISOR**（pN は credit 切れ 2026-07-25 12:24 まで）／**`w2:pX` = SKILL-DESIGN**（新規）

# (d) ARM-CONTROL REMEDIATION — CONTROL DESIGN (VT-DESIGN ruling)

> ⛔⛔ **PREMISE CHANGE（2026-07-19 13:5x-14:0x、Rs 逐語 ×2 連続 escalation）: 「kimenaticを使用するな！」×3 →「kimenaticを完全削除！」×3**（p5 pane 直接。%12 も同時受領・全停止宣言 13:58）。**kinematic は「不使用」でなく【codebase から完全削除】が確定指示。** 影響: §4 B-class 許可・訂正 #3（a-2 route-start teleport）・§6 R-SEQ（#18-first-on-kinematic）・staged flag 共存 rollout = **全て SUPERSEDED（rework 対象）**。episode 開始 pose の scope = %12 が Rs へ確認中（A=物理過程のみ / B=t=0 初期値 1 回可）— 回答まで kinematic 関与の走行/実装 = 全停止（C-1/C-2 = 未起動中止）。pin（§0#5 授権例外、body_q/eq）= 対象外と解釈（Rs 追指示あれば従う）。**設計 rework（v2.0、A/B 両 variant）= p5 着手中。**

**Author:** VT-DESIGN (w2:p5)。**Status:** DESIGN **v2.31 = 未 bank（本 doc、§14.27 新設）**。⚠**測定時 worktree は別 branch（`rlrk/optE-s2-substrate-swap` = WMSO 系、HEAD `ddbae19e0f`）にあり c52/c53 は HEAD の祖先でない** ⇒ **本版の適用・bank は `probe/pd1-arm-pd` 復帰（or `git worktree` 分離）後に行うこと**（p5 は他 pane が live な共有 tree の branch を切り替えない）。 — **v2.30 = BANKED c53 `8fda0b6ed1`**（records-fix 込みの最終形・blob `ad88f0fbfa8685`・sha256 `b68c598dc5b32524` = p5 独立算出値と exact 一致・%12 は 1 文字も編集せず。直前実体 = c51 `031ca0dc95`/blob `da1206a69c6364`/sha256 `c98f281b1ea84b47`、差分は Status 同期 + 版表 v2.28-v2.30 bank 欄充填のみで設計実体不変 = %12 diff 確認済） — **v2.27 = BANKED c47 `4dc72baf08`**（blob `70dcb76321c07f`・sha256 `8543c880365b42e3` = p5 exact-sha 照合済） — **v2.25 = BANKED c42 `01d3011f5e`**（blob `99b11544f657fb`・sha256 `374dd1f2454ecb56` = p5 exact-sha 照合済＝凍結値と完全一致・%12 は 1 文字も編集せず）。⚠**records-fix 適用済・再 bank 待ち**（house 先例に従い版は上げない: 版表 v2.24/v2.25 の bank 欄を c42 で充填） — **v2.23 = BANKED c39 `d73c3b9b50`**（blob `146aad2d4b9227`・sha256 `f29c1504291f2b7c` = p5 が exact-sha 照合済＝凍結値と完全一致・%12 は 1 文字も編集せず）。⚠**本 doc は records-fix 適用済・再 bank 待ち**（house 先例に従い records-fix では版を上げない: 版表 v2.22/v2.23 の bank 欄を c39 で充填 + **literal `\n` 混入の修正** — v2.23 行と v2.22 行が 1 物理行に同居し markdown で潰れていた〔%12 指摘・原因 = 私の生成 script で改行を二重エスケープ〕）。⚠**既存の未充填 1 件 = 版表 `:18` の v1.8 行**（私のセッション以前の gap ゆえ **sha を推測して埋めない**・要 owner 確認） — **v2.21 = BANKED c33 `eab548a988`**（blob `94414e5ca1a92e`・sha256 `fd876f94ea846da2` = p5 が exact-sha 照合済＝凍結値と完全一致。pN readback PASS 11:39）。**BANKED 系譜（全て p5 独立照合済）**: §1-§13 = v1.7 `c0b410b368`（+records-fix `f706552c97`）／**§14 v2.0-v2.16 = c25 `e1e24617c3`**（blob `d1785109467f`・sha256 `7cef09c59f79`、banked==worktree バイト同一）／**v2.17-v2.18 = c27 `bfc35ca87c`**（blob `e85c4e369bc0a6`、同上バイト同一。c28 `adf486bb0d` = A-group prereg、charter blob 不変）。⚠**records-fix 2026-07-20 10:5x（本行を行ごと再構成）**: 本行は 3 度の追記を*前置き*し旧文を消さなかったため自己矛盾していた（「v2.0-v2.14 は未 commit／どの ref にも存在しない／bank が最優先 custody action」= **c25/c27 で全て解消済の旧警告**が残存、local-only 文も重複）。**当該 custody 警告は DISCHARGED**（旧記載は撤回）。失敗の型 = 行の一部を substring 置換し面全体を検算しなかった = [[feedback-replace-by-line-identity-not-by-a-substring-that-lives-in-other-lines-2026-07-15]] の自己違反。⚠**版表の bank sha は構造的に 1 commit 遅れる**（ある commit の中でその commit 自身の sha は書けない）⇒ 充填は常に follow-up records-fix 側。現状: worktree = 充填済／c27 blob = 未充填（欠陥でなく既知の lag、本 doc の bank で解消）。⚠**local-only**: `probe/pd1-arm-pd` に upstream 無・remote ref 未含有 ⇒ **push 提案は据置**（実行 = Rs 一言）。A-P0-1′ 対応: 本 doc は banked 資産であり「0-commit」は doc 状態でなく**著者 pane 規律**（p5 は commit しない・bank 執行 = %12）を指す。**(d) arc = Rs review v3 下**。⚠旧記載「凍結/走行 gate = v1.6 bank + prereg v1.2 凍結後（Rs 順序 §7-7）」は v1.6/v1.7 bank 済・prereg も後続版が存在するため **要再確認（%12/pN lane、p5 は未検証ゆえ新値を主張しない）**。probe evidence = 現在ゼロ（5-run batch = DIAGNOSTIC/非 evidence、`fa1e786b46` §2）。

### 版表（①、full SHA + stamp = dispatch 時 `date` 実測 JST）
| 版 | banked SHA | stamp (07-19) | 内容（1 行） |
|---|---|---|---|
| v1.0 | `0f39f7b598` | 08:14 | 初版: Q1-Q6 裁定 + M-1..M-6 + P-D1 probe spec |
| v1.1 | `ed24470097` | 08:26 | 訂正 #1: §5⇄§8-3 cadence 矛盾 → @4 走行（§0.0） |
| v1.2 | `3b5f75c131` | 09:02 | 訂正 #2: imported actuator 12 本発見 → Option B（M-1、§0.0） |
| v1.3 | `054ccf139a` | 09:42 | 訂正 #3: route-start pose bridge → (a-2) 境界 re-pose（§4 新 B row、§0.0） |
| v1.4 | `e32c75c3a4` | 10:45 | Rs review 対応: ③B1 裁定 / ④§7-5 supersede + L-P0 REQUIRED / ⑤仮説 tag / ⑥guard rename+時間意味論 / ⑦§8-2 UNVERIFIED / L-P5 再設計 mark |
| v1.5 | `a584be8545` | 11:26/11:43 | §12 = prereg v1.1 L-P5′/L-P2′ RATIFY + 精密化 2（11:26 dispatch）→ **Rs review v2 残 6 点 fold（11:43）**: ①A-P0-5 FF 実経路 site 列挙（§5 修正）②A-P0-6 run-matrix 表 ③A-P0-3 L-P0 defer 句削除+役割宣言 ④A-P1-3 negative control 再設計 = stale-target PRIMARY（§12.1、**§12-① L-P5′ を supersede**）⑤A-P1-4 re-pose 受入検査群 spec（§12.2）⑥P-P1-2 stamp 規約注記 |
| v1.6 | `f200bfd78c` | 12:30/12:44 | §12.2-R: Declared bands readback = **全 5 項 ACCEPT**（12:30。走行 GO は v3 §7-7 に superseded — 注記済）→ **Rs review v3 lane 4 点 fold（12:44）**: ①header BANKED 形式化 ②B2 fallback = STOP+design delta+p5/pN 再レビュー gate 明文 ③implicitfast 安定性 = 仮説 tag 軟化（authority = 経験 gate）④A-7 pin/eq ownership 検査を §12.2 suite へ追加 |
| v1.7 | `c0b410b368` | 13:29 | §13 = P-D1 RESULT 裁定: R-1 verdict = FAIL(tracking-transient) as-frozen record（力 FEASIBLE 確立・qs N/A ACK・L-P2′ PARTIAL ACK）/ R-2 §8-4 = 機構指向形で可（kd/ke lever、C-1 kd×0.25・C-2 +ke×2、S-1 bar 再設計宣言 = lag-law + endpoint）/ R-3 順序 = choreography-blocked CONFIRM・W-a 並行可・W-b + video 供覧 = Rs 専権・再記録 robustness leg 必須化 |
| v1.8 | bank = %12 | 13:45 | §13-R: prereg v1.3 §7 readback = **ACCEPT**（ω 定義は draft が既 pin・非 block nit 1 = §7/§6 並び）→ v1.3 凍結 + C-1/C-2 走行 OK〔⚠直後に完全削除指示で SUPERSEDED〕 |
| v2.0 | c25 `e1e24617c3` | 14:07 | **PREMISE CHANGE banner + §14 NO-KINEMATIC 完全削除 CHARTER**（Rs「使用するな」×3 →「完全削除」×3）: D-①〜⑥ + C-1/C-2 → C′ 再定義 + sequencing。B-class 例外失効・a-2 廃止・#18 PD 逆転・Layer8 全件 FAIL 化・W-b 必然化 |
| v2.1 | c25 `e1e24617c3` | 14:12 | **pin 例外も全廃**（pN 経由 Rs 正式 relay 13:34/14:06 — §14.7 SUPERSEDE → §14.10 新設: removal inventory・(d-a)/(d-b) 歴史 evidence 化・物理保持置換 3 lever + P-PIN probe・HALT 意味論読み・**video 標準要件 = 常にアーム+ハンド表示**〔Rs 14:0x ×2〕） |
| v2.2 | c25 `e1e24617c3` | 14:35 | §14.0 に **Rs 恒久原則 verbatim 収載**「simは現実世界だ。常に現実と同じ条件にしろ」（全設計判断の基準・4 指示の統一根・Ω_TR 実機 spec 内の反射適用 1 点）+ p5 memory 恒久登録 |
| v2.3 | c25 `e1e24617c3` | 15:51 | §14.11 = REMOVAL milestone 受領 + p5 独立 on-disk 検証（tip `18c428b7e6`: kinematic 書込=0 ✓・ctrl 置換 ✓・pin airtight-closed ✓）+ narrative 精密化註 + ⛔削除≠稼働系 + two-key posture。⚠**15:52 verdict = §14.12 で withdrawn**（blind spot） |
| v2.4 | c25 `e1e24617c3` | 16:34 | §14.11 **自己訂正**（my 15:52 grep = pattern-scope のみ真・alias `_rep_jq` teleport 見逃し = source-name grep の blind spot）+ §14.12 **two-key TK 裁定**（tip c4 `349d13551c`、sink-based）: TK-1a ✅（delivery-surface 網羅・arm sim-state write=0）/ TK-1b ✅（pose gate fail-closed・pin 3 重閉鎖）/ TK-2 = authorize dead-body **uniform-delete**（git history=evidence）/ TK-3 = pose tol 0.05→**0.01 rad provisional**（freeze-after-measure）+ §14.3 reconcile |
| v2.31 | bank = %12 | 2026-07-20 21:0x | §14.27 **`physics_step` 全 consumer 列挙への裁定**（材料 c52 `46a59e7831`/sha256 `068b51dda8aee047` = p5 独立照合済・材料のみで class 選択なし）: **class = 単一 `DRIVE`/`MIGRATION_PENDING` 維持・consumer 別分割は却下**（`gripper_dynamic` は **extent** を変えるが **kind** を変えない。extent 差で割ると remediation 義務が同一な 2 class ができ **per-consumer 免除の入口**になる ⇒ §14.26 (b) 却下と同形）。**bind = 全 consumer**（B0/B1 は外部 5 callsite 中 1・同 module 54 は B0/B1 経路外 = 「B0/B1 closure ⊊ symbol closure」3 例目）。⭐**fence は class の代替でなく加算・2 種別立て**: **F-α rebind sink**（`T.physics_step = _pp` が AST 静的解決と runtime 実体を乖離 ⇒ guard 契約に module 属性代入 sink を追加。**guard の健全性欠陥であり class をどう付けても消えない**）/ **F-β untracked closure**（pin closure 外の実行可能 consumer を track / 隔離 / 実行不能証拠つき登録の 3 択で disposition・**第三状態を残さない**）。⛔**escalation** = `_pp` の `[ARM_Q:]` 0 埋め + `mj_forward` は cable 側 = **clip-retention pin 系** ⇒ Rs 07-19「kinematic 完全削除（pin 含む）」射程 ⇒ **Rs surface 項目に登録**（⚠**live とは主張しない**）。⚠**訂正 #27** = v2.30 の「live consumer 無なら retire」は **反証不能**（RUN レグを要する条件を RUN CLOSED 下の解除条件に据えた）⇒ 静的条件 **[R-E]**（`¬set(gripper_dynamic) ∧ backend=="mujoco"` の callsite が静的に 0）に差替え ⇒ **現状 4 entry point 該当ゆえ retire 不可・exercise 測定は不要**。⚠**%12 count 訂正** = **`main:8067` は else 枝に入らない**（`:8206` if の**内**・`:8207-8249` 連鎖の**外**にある `:8250 return` が全 mujoco 枝を返す ⇒ `:8294` は非 mujoco 限定 ⇒ VBD 枝 `:1836` で FAIL 0）⇒ entry point 5→4・helper 帰属も同じ連言で再 intersect（%12 court）。⚠**citation 訂正** = `policy_route_runner:506` → 実体 **`:483`**（assert `:484`）。⭐**新規 [H-1]** = Z-Check gate は `main` 下流 = **VBD 枝**に載る（`CLAUDE.md:271`「Newton VBD」と構造一致）⇒ 移管は substrate 越え port で 6 FAIL を継承しないが、移管先が `gripper_dynamic=False` だと fingertip z が FK 指令の関数になり **貫通述語が物理由来では偽になり得ない** ⇒ **移管 Z-Check は True path 限定 + gate 入口で fail-closed assert**（runner 側 assert に依存しない）。instrument の fail-OPEN(`:585-586`)・`found` 短絡(`:591-600`) は逐語移植しない。⭐一般則 2 件追加: **解除条件は偽を示せる形で書く** / **guard は symbol の束縛も守れ** |
| v2.30 | c51 `031ca0dc95` | 2026-07-20 20:4x | §14.26-d **照会(1) 再裁定（file 限定形）**（%12 citation 訂正を受け再実測。§14.26-c(1) は file 名欠落で別 site を裁いていたため in-place で RE-TARGET 注記）: 対象 = **`test_newton_clip_routing.py :: physics_step`（def `:1790`）mujoco 枝 `:1827-1833`** = `phys_jq[_ARM_OVERWRITE_IDX] = fk...` + `phys_jqd=0` + `joint_q/qd.assign` ⇒ **per-frame の arm joint kinematic 上書き = class DRIVE**（reset でない）・**②① の cutover 対象そのもの**。⭐**新実測① を code 逐語で CONFIRM**（真枝 comment「gripper is a POSITION actuator … overwrite **ONLY the arm coords** … servo drives them via `control.joint_target_pos`」）⇒ cutover = **arm 限定**採択。⭐**新規指摘**: `gripper_dynamic` の 2 枝は 3 因子上**別 triple = 別 class**（else 枝 `phys_jq[:n]` は arm+gripper 丸ごと上書きゆえ narrowing ① が及ばない・live consumer 無なら retire）⚠**〔v2.31 §14.27 で 2 点 SUPERSEDED: ①「別 triple = 別 class」→ triple 差は **acceptance evidence の差**であって class の差ではない・class は単一 `DRIVE` ②「live consumer 無なら retire」→ **反証不能**ゆえ静的条件 **[R-E]** に差替え・現状 4 entry point 該当ゆえ **retire 不可**〕**。**回答 = bind は authorship YES / scope 限定 NO** — `physics_step` は clip_routing 中心 step 関数で他 consumer 多数 ⇒ **B0/B1 closure ⊊ physics_step closure**（訂正 #25 と同型）・**同 bundle で全 consumer 列挙 + 再検証 or fence 必須・列挙なき部分 cutover 不可**。⭐一般則追加 = **編集 scope ≠ 解除 scope**。照会(2)(3)・訂正 #26 は影響なし（%12 理解に CONCUR） |
| v2.29 | c51 `031ca0dc95` | 2026-07-20 20:3x | §14.26-c **照会 3 件裁定 + 新実測①② CONCUR + ⚠訂正 #26**（%12 c49 への応答）: ⚠⚠**訂正 #26 = `policy_route_runner:362` `import test_newton_clip_routing as rt` ⇒ `:480` が呼ぶのは clip_routing の copy であって `newton_routing_utils` でない** ⇒ 訂正 #15 の「routing_utils = B0/B1 の共有 realization」という**根拠を撤回**（class DRIVE は 3 consumer〔run_demo/5clip/wet_run〕で再確認要）。⛔失敗型 = **alias 束縛先を import を読まず断定**（11 例目・規律追加: `mod.f()` の帰属前に import 行を示す）。副次 = B0/B1 は raise 済 route_executor 経路に**入っていない**ので壊れていない。**(1) NO** — 指定 `:1827-1833` は `physics_step` でなく **`restore_state_snapshot`（def :1806）**・**§14.23-b/-c で既裁定**・caller は 5clip:350 のみで **B0/B1 は呼ばない**ゆえ bind は closure 誤帰属の再演。**(2)** `if ep>0` = episode 境界初期化 ⇒ **§14.23-c 軸で ADAPT**（新軸なし）+ component 別 class 4 種〔body_q/qd=DELETE / robot joint=RESET〔manifest 登録必須・訂正 #20〕/ cable joint=CABLE-SEED / solver `*_prev`=assign しない〕。**(3) 該当軸 = CABLE-SEED**（§14.15 PS-3・§14.16-R 判定式）: 4 site は joint-space・one-time・hands-off で要件充足。適用条件 4 + ⚠**登録で `[FAIL]`→`[CARRY]` に移り canonical count が変わる**ゆえ宣言経路必須。**①CONCUR** = `gripper_dynamic` は clip_routing/route_executor が honor（routing_utils は 0 hit）・live path は True ⇒ **cutover 対象は arm 限定**に縮小。**②CONCUR** = cable 書込は drive 軸でなく CABLE-SEED 軸 |
| v2.28 | c51 `031ca0dc95` | 2026-07-20 17:4x | §14.26-b ⚠**訂正 #25**（pN narrowing ② に CONCUR・記録 c48 `bb68cb3c0f`）: §14.26-a(3)「②と終端 (a) は同一 landing の同一事象・gate を分けない」を **撤回**。再実測 @c47 = symbol の live callsite **10** のうち **B0/B1 は 1**（残 9 = routing_utils 2 / clip_routing 2 / wet_run 3 / grip_modes 1 / route_executor 1〔dead〕）⇒ **B0/B1 closure ⊊ symbol closure**。⛔**自己申告 = 同 census を自分の §14.26(1) で 2 版前に測っていながら包含関係を確認せず同一性を主張**（規律追加: 「同一事象/同時成立」を書く前に 2 集合の包含を示す）。**正しい構造 = per-consumer-closure の段階解除**（B0/B1 cutover が解除するのは当該 closure のみ・symbol 終端 (a) は**最後の** consumer・**gate は分かれる**）。(c) 解除条件 = 4 要件 + 既存 two-key/GO レビュー + 残 consumer は RED 維持。narrowing ①（solver 名だけでは cutover 不可）も CONCUR。⛔**Rs 応答の正確な記録**: Rs 逐語は **routing 指示**（pN へ確認せよ）であり **substance の裁定ではない**・pN scope confirmation も pN 自身が「ruling でない」と明示 ⇒ **「Rs が 4 要件を裁定」と書かない**・ruling ② は依然 Rs 未確定 |
| v2.27 | c47 `4dc72baf08` | 2026-07-20 17:2x | §14.26-a **pN c44 CONCUR + 3 因子基準 fold**（記録 c46 `f368dce537`/blob `b208a1b3da1b76` §7 読了・**加算 fold で §14.26 の裁定は不変**）: ⭐**定義 file / solver default で class を付けない → `consumer callsite` × `effective backend` × `robot drive realization` の 3 因子**を (c)→(a) 遷移の分類規則として採択。実測裏付け = `task_config:107` default は **`vbd`** ⇒ default 準拠なら live mujoco consumer を誤ラベルする（(b) 却下は本基準からも導出）。manifest v2.4 class 行の記入不可・census 35 固定・step3 docs-only 一時停止に **CONCUR**（確定後 = ruled-class prereg 再提示 → two-key 再取得）。ruling ②「移管」4 要件〔①actuated drive cutover ②旧 `update_kinematic_bodies` call 消滅 ③cutover sha + substrate id ④fresh reacquisition〕を**両軸一致の読み**として記録・⛔**確定は Rs**（合意は裁定でない）。⭐**②は §14.26 終端 (a) と同一 landing の同一事象**ゆえ gate を分けない。記録 = main 側 4 dirty file は owner UNPROVEN ゆえ不触 |
| v2.26 | c47 `4dc72baf08` | 2026-07-20 17:0x | §14.26 **cross-backend 共有 writer の class 裁定**（材料 c44、実測 @c43）: `policy_route_runner:480` が `:487` `backend="mujoco"` 下で `update_kinematic_bodies` を呼ぶ ⇒ **VBD 専用でない**（%12 finding CONCUR）。p5 census は更に広く **触れる file = 8**・⭐**`wet_run_full_sequence.py` 3 callsite は guard FAIL 35 に不出現**（guard は sink ベースゆえ caller 非計上）⇒ ⭐**一般則: guard count ≠ blast radius**。**裁定 = (c) MIGRATION_PENDING〔RED 維持・count 減らさない・期限付き・新規 caller 禁止・silent carry 禁止〕→ 駆動移管 landing 後に (a) 単一 realization 収斂。(b) 枝分割は却下**（共有 symbol を枝で割ると realization が再複製＋mujoco 枝の kinematic を恒久化）。⚠**訂正 #24** = §14.24-c(5)「mixed = branch-callsite split」を共有 symbol に適用しないよう narrow。⛔**Rs scope 照会**: ruling ②「移管」の内容 = 駆動方式移管か否か（%12 推定と私の実測は整合するが Rs 専権ゆえ格上げしない。§14.24-c(3)③ の「substrate 収斂」論も B0/B1 については drive の問題と自己訂正） |
| v2.25 | c42 `01d3011f5e` | 2026-07-20 14:5x | §14.25 **R-1′ 確定形 fold**（pN c41 `d25c9fc07c` §6 + 材料 §4 blob `ebd7863ff54b2c` 読了）: **(A) `body_label` 単一 source・fallback 禁止**〔hybrid は静かに offset 退行〕/ **(B) offset 依存 0 を検査可能に = Z-Check 経路から `ROBOT_BODIES_PER_ARM`/`FINGER_LOCAL` 依存を外す** / (C) per-arm exact cardinality + uniqueness / (D) 0・過多 fail-close / ⭐**(E) 実 label は prereg-authorized な build identity leg で確定し source closure〔MJCF path+sha / importer `:1433`→`:1609` / builder finalize / 結果 label 一覧〕を pin・未 authorize の読出しを根拠にしない**〔旧 (7)「impl レグ」を格上げ置換〕。記録 = pN が `find_bodies` 提案を delivery-surface 誤りとして自撤回（私の不採用判断と一致）・**exact koshape label 非主張を pN が正と評価**。carry = grip 自身の `[9,13]` 算術は別 owner/別 gate |
| v2.24 | c42 `01d3011f5e` | 2026-07-20 14:4x | §14.25 **R-1 → R-1′ 全面差替 = 訂正 #23**（pN B1 HOLD + %12 c40 finding に CONCUR）: 旧 anchor「`newton_grip_env.py` の `_finger_physics_ids` 型 discovery」は **FALSE** — 実体は `bi = ws + arm_offset + lf` の純算術（`[9,13]`）で name/cardinality/uniqueness/fail-close 全て 0 ⇒ 再利用すれば R-1 が禁じた失敗を再演。**正 anchor = `Model.body_label`**（`model.py:426` 実在・`builder.py:3636` populate・`import_mjcf` が MJCF body 名から階層パスで populate — p5 が installed source で実測）。`Articulation.find_bodies` は env7 に届かず不採用。契約 = 名前照合／階層パス前提／合成名 `body_{id}` に当たる緩い照合の禁止／**per-arm exact 2**／uniqueness／**0・過多・曖昧・label 欠落は fail-close**／⛔**実 label 文字列は spec に書かず impl が実測 pin**。acceptance に **label 破壊の陰性対照**を追加 |
| v2.23 | c39 `d73c3b9b50` | 2026-07-20 12:0x | §14.25 **env7-mujoco Fingertip Z-Check 移植 設計 input**（Rs c36 裁定 + pN design-lane OPEN 受け）: 現計器の完全仕様を on-disk 実測で基準化（入力=`state.body_q` 非 fk_state / 点=`bs+7,+8` の z / 面=`TABLE_HEIGHT` 0.80 / **1 frame 1 カウント** / **max は short-circuit ゆえ真の最大でない** / **PASS→FAIL 一方向**）+ 移植要件 **R-1 offset でなく discovery**（コ-finger で body 構成が違う）**R-2 TABLE_HEIGHT は provenance を pin**（optionB/C/D は 0.75 = 50mm 差）**R-3 fail-OPEN を fail-closed 化**（現行はデータ欠落で黙って素通り）**R-4 max 仕様はまず保存** + acceptance 4 条件の mujoco 形（**(ii) は合成入力で計器のみ突合・実 run 比較は証明にならない / (iii) は再現でなく帰属＝VBD は command の貫通・mujoco は物理の貫通**）+ retire = 4 条件 two-key。B0/B1 移管は**別依存 workstream** |
| v2.22 | c39 `d73c3b9b50` | 2026-07-20 11:4x | §14.24-c**(4-R)** = **OPS(pN) 推奨 disposition の fold・p5 CONCUR**（c33 readback PASS 受領）: ①' Z-Check = **env7-mujoco 移植 → VBD copy retire → CLAUDE.md 更新**〔私の選択肢(a)相当・migrate-then-retire ゆえ gate が失効しない〕**＋ p5 追加条件 = 移植版が §14.24(3) の (ii) 計器同一性〔同一量: fingertip z vs TABLE_HEIGHT・貫通で PASS→FAIL〕と (i) 陽性対照 fire を示すこと（示さねば「名前だけの移植」で retire 前提を満たさない）** / ②' B0/B1 移管 + 旧 artifact HISTORICAL/NOT_COMPARABLE + fresh reacquire = CONCUR（§14.24-a(C2) A-first と同一帰結）。**Rs 裁定まで全 gate CLOSED・manifest/census 固定**。records: v2.19-v2.21 の bank sha = c33 充填 |
| v2.21 | c33 `eab548a988` | 2026-07-20 11:1x | §14.24-c **A-group substrate 裁定 = branch split CONCUR / VBD 再構築せず env7-mujoco 移管を推奨（Rs 裁定事項）** + ⚠**訂正 #22**。p5 が installed `solver_vbd.py` を直読: `joint_type`8/`target_ke`13/`target_kd`7 かつ `:119`「Not supported: joint_armature, joint_friction…」⇒ **VBD は joint と PD drive を扱う**（%12 c30「VBD supports none」= repo build comment の誤読、%12 narrow correction + pN source check に CONCUR）**が `joint_target_mode` 非対応ゆえ PS-1 POSITION 形は transfer 不可**（→ §14.24-b(1)(b) を mujoco 限定に訂正）。⭐裁定は capability 論争に依存しない形: **可能でも再構築は不適**（①`CLAUDE.md:80` env6-VBD = banked DISCARDED への再投資・§運用4 gate ②`joint_friction` 非対応 ⇒ faithful-gripper wall 再来 ③単一 substrate 収斂）。⛔**Rs 専権 2 件**: `CLAUDE.md:271` の Z-Check Gate（Newton VBD）retire ＝ CLAUDE.md 変更 / B0/B1 substrate 移管（artifacts が NOT_COMPARABLE 化）。暫定 class = mujoco4 REWRITE候補 / VBD writer DELETE 必須・consumer は SUBSTRATE-BLOCKED / mixed は branch-callsite split / `routing_utils` track-level DISCARDED は **HOLD 非承認** / `grip_modes` 未分類。manifest・census 不動、prereg v2 §B2 = DO-NOT-IMPLEMENT 維持 |
| v2.20 | c33 `eab548a988` | 2026-07-20 11:0x | §14.24-b **pN c29 residual R2/R3/R4 = 3 件とも CONCUR・訂正 #19/#20/#21**: **#19** route/scripts substrate は `is_kinematic=True`/`inv_mass=0`/`density=0.0`/actuator 0 hit ⇒ §14.24 は **realization swap でなく substrate rebuild**（§14.24 verdict 行に in-place 限定を追記）/ **#20** §14.23-c ADAPT に **`RESET_SEED_MANIFEST` 登録義務**が欠落（現 manifest は grip 1 entry のみ）/ **#21** acceptance (i)-(iv) は **全て runtime 義務**（static-covered は誤読）+ 旧FAIL→新PASS は named RED case で示す。⛔規律再格上げ（6 度目の同型失敗） |
| v2.19 | c33 `eab548a988` | 2026-07-20 10:4x | §14.23-c **B3 一意決定**（`test_step_table_dryrun` = RETIRE〔snapshot leg 限定・file 全体は保存〕/ `test_newton_5clip_routing` = ADAPT〔physical episode reset〕。分岐軸 = mid-run rewind か episode 境界初期化か）+ typed OFFLINE 採択 scope を pN guard lane に限定して記録 + HALT exception scope 確認 + records-fix（Status 行を**行ごと再構成** — 3 度の前置き追記で自己矛盾していた旧 custody 警告を撤回、local-only 重複解消。版表 bank sha は構造的に 1 commit 遅れる旨を明記） |
| v2.18 | c27 `bfc35ca87c` | 2026-07-20 10:2x | §14.23-b **snapshot rewind disposition 裁定 = §14.23(I) CLOSE** + ⚠⚠**訂正 #18**（入力 = call-graph c26 `3ddd22322e`、p5 closed query 自走）: `RoutingOrchestrator` **instantiation 0**（唯一の一致は docstring）・`_run_rl_episode` restore 0・`SnapshotManager()` = orchestrator〔到達不能〕+ `test_step_table_dryrun.py:111`〔live harness〕・`restore_state_snapshot` caller = `test_newton_5clip_routing:350` のみ ⇒ **orchestrator 経路は配線済み dead**。**私の §14.23(C)「live caller chain・F2 より重い」を撤回**（chain 頂点の構築子を問わず 1 hop 手前で止めた = delivery-surface 規律の call-graph 版・本 arc 4 度目）。⇒ **前提問題消滅・DELETE 確定・training carve-out 不要**。執行条件 (a) 両 writer body 同時除去 /(b) compat は body-deleted fail-closed のみ（F2 先例）/(c) standalone consumers は同一 bundle で retire or physical-reset-replay＋§14.24(3) 4 条件 /(d) ⛔**body-state teleport rewind の復活を恒久禁止**（§14.10 + Rs「sim は現実世界だ」） |
| v2.17 | c27 `bfc35ca87c` | 2026-07-20 10:1x | §14.24-a **pN evidence-axis HOLD C1-C2 = 両方 CONCUR・2 項撤回**（+ §14.24 本文へ in-place 適用済）: ⚠**訂正 #16** `dry_run_43step:set_jq` = RESET でなく **typed OFFLINE-REPLAY**（`:193` を `:197`/`:227`/`:236` が毎 frame 呼び・solver step 無・contract `:6-11`「No cable, no physics」）/ ⚠**訂正 #17** **R-SEQ #18-first は生存せず**（charter TOP PREMISE `:3` が §6 R-SEQ を SUPERSEDED・§14.9 は A-first/#18-last）→ **pN 裁定 A-first に CONCUR**（B0/B1 = HISTORICAL/NOT_COMPARABLE→fresh 再取得→#18 は compliant substrate で・NOT_COMPARABLE は source-closure 依存に限定）。⚠伝播源 = LEDGER (d) 行の stale R-SEQ 文言 → supersession flag 反映を p6/%12 へ要求。records-fix: v2.x 全 17 行に bank sha 充填・v2.14 timestamp 誤記訂正 |
| v2.16 | c25 `e1e24617c3` | 2026-07-20 10:0x | §14.24 **A-group PHYSICS_REWRITE 設計 consult 裁定**（4 file / 27 sinks @ c23 `07324776ac`、p5 guard 自走で内訳 17/7/2/1 完全一致）: **原理は §14.15 のまま拡張不要**（同一機構・grip PS-1 precedent 有効）**が RULE 単独では不足** — ⚠⚠**訂正 #15 = §14.16 の `routing_utils 7` = VBD-legacy 分類は誤り**（`physics_step:938` の substep 毎 DRIVE・consumer = **active B0/B1 evaluator `policy_route_runner.py:480`** 他）→ **DRIVE/PHYSICS_REWRITE**、%12 提案が正・旧分類 supersede / **単一 realization 収斂**（`update_kinematic_bodies` は 4 file 複製・`route_executor.py:1683` は既に raise 化済＝先例）/ **harness acceptance 4 条件**（陽性対照 fire / 計器同一性 joint→FK / verdict 差の帰属 / kinematic 下 PASS は再取得）/ **snapshot 系は §14.23(I) と単一 disposition**。`dry_run_43step.py` のみ既存 RESET class で足りる。⛔#18 衝突無し（route_executor 両分岐 raise 済・#18 surface は別 file）だが **R-SEQ は生存**（B0/B1 evidence 再取得要否 = %12/pN 判断）。⚠coverage: `demo_aerial_regrasp.py` 5 の disposition 確認要求 |
| v2.15 | c25 `e1e24617c3` | 2026-07-20 09:4x | §14.23-a **c18 records-only CONFIRM + F3 PASS-CLOSE 受理 + 訂正 #14**: c18 `661da1f315` = eval_runs 4 file のみ・`chain_runtime_state.py` blob 同一 `5c67bab83f` ⇒ **c17 の設計軸 PASS を持ち越し**。F3 修正 `7803f58f17` = roots を `[thread_isaac_lab]` 単一 root へ（私の要求以上・系譜 clean = c17 の子孫）。⭐**canonical 131→128 を p5 が単一変数 control で独立再現**（guard 固定・F2 file のみ pre/post 差替: 128 vs 131、差分 3 件 = `chain_runtime_state.py:278/280/286`）。snapshot.py 3 violations exact CONFIRM（`:119/:120/:128`、`:121` fk = sanctioned）。⚠⚠**訂正 #14 = §14.23(D) 自己訂正**: F3-b は canonical 総計を**阻害しない**（scripts は元から走査＝計上済・bucket 違いのみ）→ **per-bucket 主張のみを阻害する欠陥へ格下げ**。⭐**「B-drive の分母が誤り」という私の異議は F3 修正で DISCHARGED**（canonical 128 が健全な分母）。open = §14.23(I) snapshot disposition のみ |
| v2.14 | c25 `e1e24617c3` | 2026-07-20 09:2x | §14.23 **c17 F2 two-key（設計軸）= SPLIT**（tip c17 `3117bbd21c`、fresh detached worktree 直読 + guard 自走）: **F2 removal = PASS（11 leg）** — body 5 write 全消・`_assign_array` 削除で dead writer 0・signature/annotation 保存・entry-raise 両分岐 fail-closed・caller-0 前提 c17 で再検証・`LAYER8_FAIL` 128→**125**・**envs FAIL=0**・self-test 32neg/9pos。⛔**"envs kinematic-clean" = HOLD 継続**＋instrument 欠陥 3 件: **F3**（guard root が `skills/`+`orchestrator/` 未走査、`skills/snapshot.py:119-128` に同型 body 書込＋live caller chain `routing_orchestrator.py:59/792/1292/1308`）/ **F3-b**（bucket 誤帰属: `scripts/newton_routing_utils.py` は envs 駆動 library だが scripts bucket 計上 ⇒ "envs 0" は path-bucket の言明）/ **F4**（`newton_chain_context_facade.py:37/57` = 名前有無のみ判定 ⇒ capability 破壊の前後で `ready` 同一 True = 情報量ゼロ）。⭐**B-drive「Layer8=0」は現 root では誤った分母** |
| v2.13 | c25 `e1e24617c3` | 23:28 | §14.22 **c15 FK-exemption attr-sensitivity fix（pN C1 close）= 設計軸 PASS**（tip c15 `6ccc09b3e6`）: `_fk_exempt` を joint_q/qd 限定・全 6 面適用・BODY/RAW 全面 fk-exempt 0・self-test 31neg/9pos・envs 3 不変（false-positive-free）。⇒ guard 硬化 arc（§14.20-22）= 設計軸 CLOSED |
| v2.12 | c25 `e1e24617c3` | 23:03 | §14.21 **c14 F1 guard hardening（G6 interprocedural helper-param taint）= 設計軸 PASS**（tip c14 `edd0c33ecd`）: computed dataflow fixpoint（allowlist 無）・FK by original receiver・chain_runtime_state 3 BODY-ALIAS 捕捉・envs 0→3・`LAYER8_FAIL=128` = pN 予測 exact。⚠coverage 境界 = within-file 2-hop。⚠**v2.14 §14.23(F) で evidence caveat 追記**（live corroboration 消滅・synthetic control は存続） |
| v2.11 | c25 `e1e24617c3` | 22:31 | §14.20 **c13 two-key = SPLIT**（tip c13 `e65c842bec`）: skill 共有 reset body-restore 5-site 削除 = 設計軸 PASS（redundancy VERIFIED）/ ⛔**"envs kinematic-clean" milestone = HOLD**（残存 SINK-2 = `chain_runtime_state.import_chain_state_into_env` の getattr-alias、guard 素通り — 私の delivery-surface sweep が捕捉）。⚠`:505` fence は **v2.14 §14.23(G) で superseded**（pN 08:04 GO） |
| v2.10 | c25 `e1e24617c3` | 19:19 | §14.19 **grip PS-2..5 two-key（設計軸）= PASS**（tip c11 `19555e128a`、3-sink airtight）: body_q=0・raw/eq=0・単一 sanctioned `_seed_robot_joint_row`（joint-only/manifest 準拠）・cable=CABLE-SEED・PS-5=detect-only。**grip 全体 kinematic-FAIL 0（設計軸）** + **PS-5 裁定 = A(raise) 現 phase 維持 / B(explosion 終端+PPO mask)=training-readiness で DESIGN-GATE（⛔time_outs 汚染禁止・EXPLOSION_DIST_THRESH parity）** |
| v2.9 | c25 `e1e24617c3` | 18:41 | §14.18 **grip PS-1 two-key（設計軸）= PASS**（tip c10 `2ad2492f94`、sink+flag 直読）: arm body write 消滅(15→14)・ctrl servo 置換(Q2 full-row lerp)・flag-OFF=fail-closed raise(旧 path 完全削除)・eval_fk 存続(Q1)・nu==12 census・invariant 健全。⛔ grasp-under-lag 再検証/PS-2..5 = fenced。blind spot なし clean verify |
| v2.8 | c25 `e1e24617c3` | 18:19 | §14.17 **grip PS-1 consult 裁定** (Q1 fk_batch_bq=CONCUR〔eval_fk_batched は finger-spring target で存続・arm 行 write のみ削除・finger=body_f 力=physics〕/ Q2 arm=**毎-frame interp**〔route parity・lag 減〕/ Q3 RESET=pN reconcile で RESOLVED〔joint-seed init 例外・body write 不可・PS-2..5 UNBLOCK〕) + §14.16-R **pN reconcile**: OFFLINE=joint-state のみ〔body-state offline 不可〕/ DISCARDED=DELETE body+git〔entry-raise 撤回〕 |
| v2.7 | c25 `e1e24617c3` | 18:06 | §14.16 **scripts/ 115-site disposition**（census 158=envs43+scripts115）+ RULE 2 class 追加: **OFFLINE-REPLAY**（認可例外・PRESERVE・Rs video 要件の含意・pN/Rs confirm）/ **DISCARDED-TRACK**（VBD legacy=entry-raise+owner declares）。test_newton_*42=retire-or-migrate（認可 verification harness 保護）。p4 census を 3 分類で re-tag |
| v2.6 | c25 `e1e24617c3` | 17:43 | §14.15 **grip env 物理置換 semantics**（core deliverable、census c6 `a004f2ce66` 15 sites/6 群）: 原理=「(d) 解の grip 継承」（IK 層不変・realization を body_q.assign→actuator ctrl+mj_forward）。PS-1 DRIVE:1697=arm servo 化(本丸)/PS-2..5=joint-seed+forward・cable=CABLE-SEED。finger コ=物理維持(§0#4 不触・cage-hold=物理接触)。⛔banked WORKING ゆえ再検証 gate(P-D1-analog+video)。c6 disarm→raise scoping 健全確認 |
| v2.5 | c25 `e1e24617c3` | 17:21 | §14.13 **two-key round-2**（tip c5 `9d00a15276`、3-sink 網羅）: SINK-1 joint ✅ clean / SINK-2 body ⚠OPEN（assign_world_states_to_sim + grip×15）/ SINK-3 eq ✅（CPU=disarm のみ・device/proto は guard v3）+ §14.14 **O-2 fold**（pN 裁定: grip body-drive IN-SCOPE `CLAUDE.md:72`）+ **reset-vs-drive 分類 RULE** + grip 物理置換 semantics + §14.1-2 を **3-sink 拡張**。verdict = (d) 宣言 arm path 削除 PASS / repo-wide = HOLD（body+eq-device+F821、pN 一致）・landing bar 精緻化「削除=3-sink 全 clean」 |

> **stamp/placeholder 規約（⑥ P-P1-2）**: stamp = dispatch 時 `date` 実測 JST。「bank = %12」SHA cell = bank 待ち placeholder（bank 後に %12 records-fix で実 SHA 充填、v1.4 先例 `c951a072d7`）。§0.0 narrative 内の「HH:2x」型 = 当時 verbatim の分丸め表記（exact anchor = 本表）。歴史注記: v1.4/v1.5 の stamp は当初 予測時刻を記入→dispatch 前に実測へ訂正した（10:52→10:45 / 11:29→11:26、date-THEN-write 違反の自己捕捉 2 回）。

### §0.0 訂正 narrative 履歴（v1.1-v1.3、verbatim — 各裁定の本文 fold 先は版表参照）
- v1.1 = **訂正 #1（%12 catch、08:23）**: §5⇄§8-3 の cadence 矛盾（§5=newton_route_env は RL path @4 ハード定数 `newton_skill_env_base.py:95`、§8-3 は「FF@producer-cadence(10)」と記載）→ **裁定 (a) P-D1 = @4 で走行**（§5/§8-3 を整合化。@10 被覆は S-2 producer gate へ移設、knob 追加なし）。
- v1.2 = **訂正 #2（%12 P-D1 pre-run finding `b9eaaf9d93`、08:54）**: M-1 の「XML actuator import に依存しない」前提が実測反転（flag-off build に imported arm actuator 12 本既存 nu=16・未配線 ctrl≡0 = 飽和 torque 隠れ綱引き・proto 配線は重複 24 本、p5 が diag log 3 本を自読 spot-check 済）→ **Option B 採択**（imported 無効化 + proto 配線、§1 M-1 改訂 + §5 L-P0 追加 + §7-5 substrate finding disposition）。M-1 旧前提 = 未検証 build 仮定（#11 と同 class の自認）。⭐L-P6 fail-able assert が走行前に捕捉 = 計器設計の vindication。
- v1.3 = **訂正 #3（%12 finding #2 `c1da5dcf54`、09:37）**: reset home ≠ recording frame-0（j0 |Δ|5.6 rad 級・p5 検算 = j4 3.57/左 j2 3.56 rad が wrap 非約分 = 別 configuration。banked kinematic FF は初回 RL step 内の hard teleport で橋渡し = 実測）→ **裁定 (a) 精密化採択 = route-start 境界の 1 回 re-pose（a-2）**: arm q := recording frame-0 **正確な記録 q 値**（winding 曖昧性も自動処理）+ qd:=0 + **ctrl := 同 pose（M-4）**、flag-gated・B-class（phase-k restore `:342-344` と同 class の 1 回/episode 境界 init）。**whole-reset seed（a-1）却下**: settle 条件まで変わり第 2 の delta + 81-cell 期の per-world settle 機構化 — (a-2) は banked kinematic が teleport で到達していた同一状態を同一 boundary で作る = 最小 delta。**(b) ramp+clock hold 却下**: 新 hold 機構 scope + 5.6 rad sweep の cable/table 衝突 risk + banked lineage が一度も物理 transit しなかった区間を transit する（忠実度は上がらない）+ episode 毎訓練 cost。guard: re-pose 境界で gripper OPEN ∧ 非把持 assert + LOUD log + npz flag。RL/trainer path へは「episode 開始 = script frame-0 seed」として同機構が退化適用。§1 FF-site impl gap fix（`apply_recorded_arm_ff` ctrl branch）= **spec-conformant ACK**（v1.2 §2 は両 site を規定済・plumbing 検証 PASS を確認）。§4 observation fold: **asserts は `mjw_data.ctrl` mirror を読まない**（gripper 実駆動中も all-zero = stale/非 operative 面 — Option A 却下理由②の追加 vindication: あの面への書込は inert だった可能性）。L-P4 は再目的化 = route-start teleport+sync 後 |q−ctrl| が frame 0 から transient bar 内に留まること（haul なし）の検証 + M-5 ramp は phase-k restore 等の残余不連続のみに適用。
**Input:** `ARM_CONTROL_REMEDIATION_D_ENGBRIEF_RSTECHLEAD_20260719.md`（commit `1ee8be5c9e` = HEAD、p5 全文読了）。
**Scope:** brief §4 Q1-Q6 + §5 staged approach への設計裁定。**実装認可ではない**（gate chain = §9）。Rs sign-off 前提（brief §0/§5-4）。

---

## §0 Grounding + gates

### §0.1 接地（p5 自読、file:line）
- 現 drive = kinematic 直書き: helper `apply_arm_only_write_broadcast`（`route_executor.py:213-215`、fk 1-world broadcast）+ `apply_arm_only_write_perworld`（`:236-238`、per-world jq_interp）— いずれも `phys_jq[arm]=target; phys_jqd[arm]=0.0`。call sites = `newton_route_env.py:1260`（RL per-step）/ `route_executor.py:5050`（§13.1 FF）/ `newton_route_env.py:810` `_broadcast_arm_jointq`（settle/hold）。
- gripper mirror（実証済 wiring）: builder proto `newton_skill_env_base.py:1636-1638`（`joint_target_mode=POSITION` + `joint_target_ke/kd`）→ SolverMuJoCo が mj actuator 合成（readback assert `newton_route_env.py:300-330`: `gainprm[0]=ke / biasprm[1]=-ke / biasprm[2]=-kd`、effort cap = **joint 側** `jnt_actfrcrange`）→ 駆動 = `control.joint_target_pos`（`route_executor.py:245+` `set_gripper_target`、solver が毎 step 読む）。
- vendor gains（UR5e MJCF）: `ur5e.xml:7-8` size3 kp=2000/kd=400/±150 N·m、`:15` size1 kp=500/kd=100/±28 N·m、`:9` armature=0.1、ctrlrange ±2π（elbow ±π `:11-12`）。
- cadence: `DT=1/480`（`newton_skill_env_base.py:93`）、RL path `RL_SIM_SUBSTEPS=4`→`RL_SIM_DT=1/1920`（`:95-96`）、producer path `SIM_SUBSTEPS=10`→`SIM_DT=1/4800`（`route_executor.py:1486-1487`、task_config.py:101）。RL step = 10 physics frame（`newton_route_env.py:404`）。solver = `SolverMuJoCo(solver="newton", integrator="implicitfast")`（`newton_skill_env_base.py:1332-1348`）— 陰積分ゆえ高 ke での離散安定性が**期待される〔一般論・仮説 tag、v1.6-③〕**。**安定性の authority = 経験 gate（probe 実測）であり本文言でない**（振動/発散が観測されれば文言でなく実測が governs、§8-4 感度枠へ）。
- 先行実測: arm PD on MuJoCo solver = **max_err 0.002 rad**（`LL-Newton.md:98` Franka Phase7、cable hybrid lift PASS）/ UR10e j0→0.5000 exact（`:189`）。

### §0.2 prior-art disposition（V7 gate 実行済）
`check_thread_vault_prior_art.sh --fail-on-blocker PD "arm control" kinematic joint_q gainprm` = BLOCKER_CONTEXT_FOUND。**内容 = comp3 gripper kinematic→POSITION-servo 移行（成功例・/pre-check PASS・same-pattern 先行事例）であり failed path ではない**。続行根拠 = (1) Rs 明示新 directive（"実施" L3 GO、brief `1ee8be5c9e`）(2) 発見 context は本移行の設計テンプレート（`COMP3_RULECHECK_STAGE2_COORD_20260708.md`: 「:670 28-wide reset-init = sanctioned reset-init」の分類先例を §4 で採用）。

### §0.3 [DEFER-RECON]（DDR × 本 chunk、reconciliation record）
| DDR | 依存判定 |
|---|---|
| #18 grip-slip（FOUNDATIONAL、IN-RESOLUTION） | **相互作用あり・GATE ではない**（#18=target 生成層、(d)=realization 層で直交）。sequencing 裁定 = §6 R-SEQ。(d) probe は #18 と独立に走行可 |
| #4 (d-b) non-crutch / #12 fork-B V0 | (d) rollout 後に (d-a)/(d-b) の anchor 再基線が必要（§7-3）。本設計 chunk 自体は非依存 |
| #19 ENV-MULTIWORLD（wc=1/proc） | probe/rollout は wc=1 で実行（fork-B 整合）。ctrl は per-world 配列ゆえ機構は wc 非依存 |
| #21 FM2 demos regen | **(d) stage-2 が demo 再生成をトリガ ⇒ #21 と単一 regen event に fold**（§6 R-SEQ2） |
| #2 P3 body_q sync-premise | 非依存（joint_q/ctrl 系、body_q 直書きなし） |

FOUNDATIONAL 未解決依存で本 **設計** chunk を block するものなし（#18 は impl sequencing のみ拘束）。

---

## §1 機構裁定 M-1〜M-6（HOW の骨格）

- **M-1 wiring = imported 無効化 + proto 配線（訂正 #2 = Option B）**: 実測（`pd1_probe_20260719/diag/dump_actuators_baseline.log`、p5 自読）= flag-off build は **nu=16 で ur5e.xml `<actuator>` が既に import 済**（act4-15 = 12 arm、vendor gains、両腕 joint 0-5/14-19 に name-map）だが **未配線**（arm dof `joint_target_mode=0`・`mjw_data.ctrl≡0`、`dump_ctrl_wiring.log`）。proto 配線を足すと**重複 24 本**（`run_smoke_pd.log` assert 実証）。⇒ 設計 = **(i) imported 12 本を無効化**（**裁定 v1.4-③（Rs 推奨 B1 に concur）: B1 strip-at-import = PRIMARY**〔nu=16 [12 proto + 4 gripper]・census 清潔・inert 検証負担なし・零化 actuator を solver 経路が別解釈する risk ゼロ〕。**B2 零化 = importer/builder 機構上 strip 不可能な場合のみの fallback — ⛔ 実装者単独では選択不可（v1.6-②、A-P0-2′）: B2 へ落ちる事象 = STOP + design delta 文書化（何が strip を阻むかの実測根拠）+ p5/pN 再レビュー gate を通過してのみ採択**。採る場合は static assert〔gainprm=biasprm=0 ∧ forcerange=0〕に加え **動的 force≡0 受入試験 REQUIRED**〔無効化 12 本の actuator force 読出 ≡0 を全 route horizon で assert、Rs 条件〕。現 probe 実装 = B2 ゆえ %12 が B1 再実装 → **O-1 の L-P0 診断は裁定機構下で再測**）**+ (ii) proto 配線**（12 arm driver DOF/world に `joint_target_mode=POSITION` + ke/kd + joint 側 `jnt_actfrcrange`、`:1636-1638` 同型）。**Option A（imported を直接駆動）却下 3 点**: ① fail-open — ctrl 書込漏れ経路の既定 = 飽和 pull-to-zero = 本 finding の欠陥そのもの（B の漏れ既定 = 直前 target 保持 = 良性）② `mjw_data.ctrl` 直書きは新規手書き device 面（wc>1 layout 未検証、pin arc の書込面 hazard class）vs `joint_target_pos` = 実証済み面 ③ gripper との機構統一。**L-P6 census 改訂**: 選択機構に応じ「arm 上の実効力源 = design 値の 12 本のみ」（重複ゼロ・inert 検証・gripper 4 本不触・**proto 値 ≡ 無効化した imported 値の数値一致 cross-check**〔同じ vendor 値を別機構で再実装するだけであることの証明〕）+ negative control。
- **M-2 駆動 = ctrl ストリーム置換（realization 層のみ変更）**: kinematic write が消費していた **同一 target ストリーム**を `control.joint_target_pos[arm_dofs]` に書く。`phys_jqd=0` 零化は**廃止**（速度は物理量になる）。target 生成層（IK / interp / FF indexing / `_per_world_fk_jq` chain）は**不変**。
- **M-3 command-space 原則**: interp/warm-start chain（`old_fk_jq`/`jq_starts`/`_per_world_fk_jq`）は**指令空間のまま**（realized q から再 seed しない）。理由: lag 下で measured-q 再 seed は軌道を歪め noise を target に結合する。recorded/IK 軌道 = authoritative、realized は obs/verify 用測定のみ。（#18 A2 の frame spec と整合 — あれも recorded=指令空間。）
- **M-4 teleport⇒target-sync 不変条件**: **許可される全 reset/restore teleport（§4 分類 B）は同一 turn で arm ctrl := 同じ pose を必ず設定**。さもないと PD が直後に stale target へ引き戻す（gripper が comp3 R1a で学んだ同じ罠 `newton_route_env.py:1098-1100` 系）。phase-k restore（`route_executor.py:342-344`）には banked **arm ctrl** の restore を追加（grip_target restore `:346-348` の arm 版）。
- **M-5 指令不連続の漸進化（ramp-in）**: 指令 jump > JUMP_TOL（提案 0.05 rad、任意 joint）が生じる遷移（settle→route 開始等）は **N_RAMP frame の線形 ramp**（提案 0.25s=120 frame @DT）で接続。force-design skill の「PD target 瞬間ジャンプ禁止」（FINGER_CLOSE_STEPS 先例）の arm 直適用。⇒ #18 A3 の step-0 pop は PD 下では**設計で消える**（teleport でなく bounded 物理遷移になる。kinematic 用 A3 verify leg は (d) 後 ramp-verify に置換、§7-2）。
- **M-6 arm tracking-divergence guard（v1.4-⑥ rename、旧称 anti-windup tripwire — 既存「tripwire」語彙〔make_solver 等〕との衝突回避。LOUD・非 reward 結合）**: kinematic は realized≡commanded を構造保証していたが PD は乖離し得る（障害物 stall 中も指令 chain が前進 = open-loop windup）。**時間意味論（v1.4-⑥ で明示）: per-joint `|q_realized − ctrl|` > `ARM_DIVERGENCE_BAR_RAD` が【N_DIV 連続 physics frame 持続】で発火**（瞬時 1-frame spike でも episode-max でもない — windup = 持続乖離ゆえ持続条件が正・正当な過渡 spike を false-trigger しない。counter は bar 下回りで reset — (d-b) K-dwell gap-reset と同規律）。発火 = physics-fault invalid episode（`EXPLOSION_DIST_THRESH` `newton_route_env.py:407` 同パターン: loud 終端・⛔reward/timeouts 不配線・npz flag）。**暫定値: N_DIV = 48 frame（0.1 s @DT=1/480）・bar = 訂正 probe の清潔基盤実測から導出して run 前凍結**（O-4 の持続 0.5 rad は confound 込みゆえ bar 導出に不使用）。probe にも同計測 leg（§5）。

---

## §2 Q1 裁定 — target-setting scheme

**採択 = (A) per-physics-frame ctrl ストリーム（kinematic が書いていたものと恒等）**:
- ik_chord/RL path: `ctrl := jq_interp[w]` を毎 physics frame（`newton_route_env.py:1260` の置換）。
- FF path: `ctrl := jq_ff[frame]` を毎 frame（`route_executor.py:5050` の置換、grip の `_REC_CADENCE` 1:1 と同型）。
- settle/hold: `ctrl := home 定数`（`_broadcast_arm_jointq` 系の置換 — PD 静的保持は最易ケース）。
- **IK 層は target 供給源のまま**（`solve_ik_dual`→jq_targets→interp→ctrl）。recorded `arm_q` 直結は FF path のみ（現状どおり）。

**却下 = (B) RL-step endpoint のみ ctrl 設定**（PD のステップ応答が軌道形状を変える・overshoot・recorded 軌道との対応喪失）。(A) は interp ランプを PD が追う形 = 速度比例の小さな定常 lag のみで軌道形状保存。

**§0#3 との関係**: target は従来どおり IK が生成（IK-based control 保存）、realization が forced-placement→物理 torque path になる = **#3/#5 を同時に満たす**（brief §6 と一致）。

---

## §3 Q2 裁定 — gains / limits / tolerance bar

### §3.1 gains v0（vendor 値採択、probe で検証）
| param | 値 | 根拠 |
|---|---|---|
| ARM_SERVO_KE size3（sh_pan/sh_lift/elbow） | **2000** | `ur5e.xml:7`（vendor/Menagerie 実績値） |
| ARM_SERVO_KD size3 | **400** | `ur5e.xml:7` biasprm[2] |
| ARM_SERVO_KE size1（wrist1/2/3） | **500** | `ur5e.xml:15` |
| ARM_SERVO_KD size1 | **100** | `ur5e.xml:15` |
| effort cap size3 | **±150 N·m** | `ur5e.xml:8` = **実機 spec。⛔上げるの禁止**（超過は sim-cheat = non-conservative、RS71 fidelity） |
| effort cap size1 | **±28 N·m** | `ur5e.xml:15` 同上 |
| armature | 0.1（既存 `:9`、不変更） | joint 既定 |

再 tune は probe が bar FAIL を示した時のみ（fix-first: まず iterations/経路で切り分け、gains は §8-4 感度枠内で）。⚠ MJCF `<default class>` 由来の joint 別差（size3 vs size1）を proto 書込時に正しく振り分けること（一律 2000 は wrist 過剛性）。

### §3.2 tolerance bar（暫定 → probe 後に凍結）
**参照 = 指令ストリーム（ctrl）**。kinematic はこれを恒等実現していたので、PD-vs-ctrl 誤差が移行 delta の全体。recorded 軌道比較は FF path（ctrl=recorded）で自動的に兼ねる。

| leg | bar（暫定） | 根拠 |
|---|---|---|
| per-joint 準静的（route/seat 中） | ≤ **2 mrad** | Phase7 実測 0.002 rad（`LL-Newton.md:98`）と同水準を要求 |
| per-joint 過渡（transit/ramp 中） | ≤ **5 mrad** | 準静的×2.5、probe で実測分布確認 |
| EE 位置 準静的（G3-G6 seat/push 中） | ≤ **1.5 mm** | seat lateral bar 3.5mm（`route_env_config` SEAT_LAT_BAR）の余裕を半分以上残す（tracking が bar margin を食い潰さない） |
| EE 位置 過渡 | ≤ **3 mm** | grasp 判別スケール（fingertip 6.3mm 把持 vs 22mm 逸脱、#18 実測）より十分下 |
| ARM_DIVERGENCE_BAR_RAD（M-6 guard） | 訂正 probe 実測から導出・run 前凍結（暫定発想 = 過渡 bar ×3） | windup 検出（N_DIV=48 frame 持続条件、v1.4-⑥）、physics-fault 扱い |

**凍結手順**: probe 実測 → p5 が bar を最終化 → **run 前凍結**（[[feedback-freeze-then-verify-then-bank-the-exact-sha]] / R4 先例「run 前固定」）。⛔ probe 結果を見て bar を後決めして PASS 宣言（gate-validated-under-the-bug）は禁止 — 暫定 bar で probe を採点し、変更するなら差分を宣言して再走。

---

## §4 Q3 裁定 — 16 sites 分類

**分類 A = per-step control-loop（migrate 必須 = 違反本体）** / **分類 B = reset/init/restore（許可・現状維持 + M-4 target-sync 追加）**

| site | 分類 | 処置 |
|---|---|---|
| `route_executor.py:213-215`（broadcast helper） | A（settle/hold 系 caller） | helper に ctrl 版を併設、caller 移行 |
| `route_executor.py:236-238`（perworld helper） | A（per-step drive 本体） | 同上 |
| `route_executor.py:342-343`（phase-k arm restore） | **B**（banked snapshot 復元 = reset-class） | 維持 + **arm ctrl restore 追加**（M-4） |
| `route_executor.py:344`（gripper restore） | B（既存分類どおり） | 不変 |
| `route_executor.py:1817/:1820`（STEP-1 probe/init block） | A（loop 内 per-step、`:1826` solver.step 直前） | 移行（probe infra ごと） |
| `newton_route_env.py:827`（settle hold） | A（持続 hold） | ctrl:=home 化 |
| `newton_route_env.py:1094`（reset re-pose） | **B**（sanctioned reset-init、comp3 「:670 28-wide」先例） | 維持 + ctrl:=settled 同 turn 設定（M-4） |
| `newton_route_env.py:1270`（RL per-step drive） | A（**主違反**） | ctrl:=jq_interp 化（§2） |
| `newton_skill_env_base.py:2080`（`broadcast_jointq_to_all_worlds`） | A（docstring 自認「every step, not a single set」） | ctrl 版へ |
| `aerial:475` | A（per-step arm write） | 移行 |
| `aerial:1090` | B（reset re-pose） | 維持 + M-4 |
| `aerial:1575` | A（per-step drive） | 移行 |
| `approach:419` | A（settle hold） | 移行 |
| `approach:746` | B（reset re-pose） | 維持 + M-4 |
| `approach:1203` | A（per-step drive） | 移行 |

| **route-start re-pose（新設、訂正 #3）** | **B**（1 回/episode 境界 init、phase-k restore 同 class） | arm q:=rec frame-0 正確値 + qd:=0 + ctrl 同期（M-4）+ OPEN∧非把持 assert + LOUD + npz flag |

計: **A=11（migrate）/ B=5+1 新設（許可+target-sync）**。Layer 8 baseline は A 消滅 + B 残置を反映して更新（B は「reset-init 例外」として checker に註記 — checker 変更は %12 court、L3）。

---

## §5 Q4 裁定 — de-risk probe spec（P-D1、%12 実行）

**目的 = brief §3 の pivotal unknown を最小コストで裁定**: 「MuJoCo arm PD は ±150/±28 N·m 下で（cable+gripper 負荷込み）記録軌道を bar 内追従するか」。

- **環境**: `newton_route_env` **FF whole-route**（(d-a) probe infra 再利用、nominal cell、wc=1、deterministic、cable ON・grasp ON・pin ON）。**cadence = RL path @4 のまま**（`RL_SIM_SUBSTEPS=4` `newton_skill_env_base.py:95`、knob 追加せず）— 根拠: ①trainer 基盤 = @4（DDR #18 title と同一 substrate、(d) の第一目的 = trainer 準拠基盤）②【**仮説 tag（v1.4-⑤）**】ctrl は frame 単位保持で substep はその内部積分 ⇒ @4 = 粗積分 = PD に等しいか厳しい側 = conservative — **解析的導出であり未実測**（PASS@4⇒@10 も推論。S-2 で confirm、反例 = loud re-open。裁定 (a) の非仮説根拠は ①③）③基線対照は @4-vs-@4 の同 cadence で cadence 効果が contrast から消える（1 変数規律。@10 knob 追加は #18 substep-confound 軸への再進入 + scope creep）。**probe の PD-write surface 全列挙（v1.5-①、A-P0-5 修正）**: (s1) `apply_recorded_arm_ff` の ctrl 書込（`route_executor.py`、**FF 実経路 = 本 probe の主 site**）/ (s2) `newton_route_env.py:1270` 系 = **RL path であり FF probe では不実行**（S-1 移行対象、probe 対象外）/ (s3) route-start re-pose（訂正 #3 (a-2)、B-class）/ (s4) harness M-4 ctrl sync。⚠honest note: v1.0-v1.4 §5 の「移行対象 = :1270 系のみ」は誤り — §2 は FF site（route_executor `:5050` 域）を正しく規定しており **§2⇄§5 の自己不整合**が %12 初回 branch の mis-wiring（finding#2 §1）に寄与した（%12 は自己帰属したが設計 doc 側の誤導が先行）。実験 flag（`ARM_PD_DRIVE=1` 系）で切替 — reset 系 B は不変。read-only branch / 未 land。
- **基線**: 同 build・同 seed の kinematic 走行 = **flag-off AS-IS（imported 綱引き込み・banked substrate と byte 同一）**。**宣言 delta 裁定（訂正 #2）**: PD-vs-基線 contrast = 移行 delta = 〔realization 置換 + artifact（綱引き）除去〕の合成。artifact は現 arm-drive realization の一部（準拠 PD 設計なら必然的に消える）ゆえ主 contrast から除去すべき confound ではない — **成分分離は L-P0 が担う**。
  0. **L-P0 contamination magnitude（v1.4-④: REQUIRED に昇格）**: kinematic + imported 無効化（③裁定 = B1 機構）vs kinematic 現状、同 seed — 綱引き成分単独の軌道/述語 divergence を定量。**banked evidence caveat の規模判定材料**（Rs 材料、§7-5）。O-1 diagnostic（B2 機構下）= g3 242→never の完全消滅を既に示唆 — B1 下で evidence-grade 再測（verification legs + video leg 付き）。
- **測定 legs**:
  1. **L-P1 tracking**: per-joint |q−ctrl| 時系列 → phase 別 max/p99（§3.2 bar 採点）+ EE 誤差（FK(q) vs FK(ctrl)）。
  2. **L-P2 predicate parity**: grasp（fingertip l/r_near）/ G1-G3 latch / pin fire（fire_step・anchor）/ seat metrics / retention / drop 有無 — kinematic 基線との対照表。⚠ **一致は期待値でない**（timing shift は想定内）: 採点は「G 系到達 + fire≺release + retention 保持」の述語成立で行い、frame 番号差は宣言 delta として記録。⚠**v1.4 re-scope（O-1/O-4 confound）: 基線連鎖自体が artifact 依存と判明 ⇒ 「基線との parity」= characterization に降格（acceptance でない）。acceptance 意味論（清潔基盤で何を要求するか）= prereg v1.1 で再定義**（「PD が recording を追従できない」と「recording の連鎖が artifact を要求する」の分離が訂正 probe の中心課題）。
  3. **L-P3 effort**: per-joint actuator force 時系列 → saturation 率（cap 到達 frame 数 / 全 frame）。**saturation >1% で WARN、>5% で bar FAIL**（力不足 = 追従不能の前兆）。
  4. **L-P4 route-start 整合（v1.3 再目的化を本文 fold）**: route-start teleport+ctrl 同期（訂正 #3 (a-2)）後、**|q−ctrl| が frame 0 から過渡 bar 内に留まること**（haul なし）の検証。M-5 ramp は phase-k restore 等の残余不連続のみに適用（O-2 diagnostic: 同期開始下で ramp 有無 = byte 恒等 = 再目的化の期待どおり、corroboration）。
  5. **L-P5 negative control（fail-able 計器の証明）**: gains ×0.1 走行 = bar **FAIL すること**（[[feedback-a-test-that-cannot-come-out-differently-is-not-a-test]]）。⚠**v1.4: 設計どおりでは判別失敗（O-3 diagnostic: ×0.1 max 0.493 vs ×1.0 0.512 rad — 分離せず）→ prereg v1.1 前に再設計 REQUIRED**（方向 = step-response/settling time 観測量 or bar-set 変更。%12 input → p5 ratify。この regime では tracking-max が gains に鈍感 = 計器として dead という実測）。
  6. **L-P6 build readback**: arm-servo-readback assert（M-1）が 12 actuator/world・gain/bias/effort 一致を報告。
- **成立 bar**: L-P1/L-P3 が §3.2 暫定 bar 内 ∧ L-P2 述語成立 ∧ L-P5 FAIL ∧ L-P6 PASS。
- **run matrix（v1.5-②、A-P0-6。REQUIRED 5 + exploratory 1、GPU 数分・訓練なし）**:

| run | 内容 | pass-role（decision での役割） |
|---|---|---|
| R0 | 汚染基盤 kinematic AS-IS | characterization のみ（acceptance でない）+ L-P0 入力 |
| R0b | 清潔基盤 kinematic（B1-strip） | **L-P2′ acceptance 参照** + L-P0 入力 |
| R1 | PD（system under test） | L-P1/L-P3/L-P4/L-P2′ の被験体 |
| R2 | PD + ramp | 機構 no-regression（≈R1 期待、乖離 = LOUD 異常報告・bar なし） |
| R3 | **stale-target negative control（§12.1 PRIMARY）** | 計器較正 + bar fail-ability 実証（採点 = intended-stream 比、§12.1 条件） |
| R4（optional） | ×0.1 gains | **exploratory 降格**（§12.1）— 非 gating・走れば gain 感度の参考 |

- **L-P0 の役割宣言（v1.5-③、A-P0-3 残）**: L-P0（= R0-vs-R0b 対照）は **REQUIRED-to-RUN**（欠落 = probe 成果物不完全）だが **probe の pass 条件ではない** — 出力 = **impact assessment であり、banked（歴史）evidence の再利用を gate する**（§7-5 caveat row に接続、再利用可否の scope 判断 = Rs）。probe verdict（PD feasibility）とは独立に報告される。旧「defer するなら 4 走行」句は v1.4-④ REQUIRED と矛盾のため削除。
- **video leg**: PD 走行の動画を Rs へ（motion-bearing sim ⇒ mandatory；Rs motion 標準 `p2r_c11_route.mp4` と並べて）。

**probe 結果の分岐**: PASS → §6 rollout へ / FAIL(tracking) → gains 感度枠（§8-4）→ 再走 / FAIL(saturation) → **軌道再設計 or 速度 profile 検討 = 別チャンク**（brief §3「re-tuning / re-trajectory effort」側へ分岐、Rs 報告）。

---

## §6 Q5 裁定 — staged rollout + sequencing

### R-SEQ（#18 との順序）
**裁定 = probe は今すぐ並行可、impl landing は #18 が先**:
1. **P-D1 probe（§5）= 今**（read-only、#18 と非干渉 — #18 の GO-now 測定も read-only で完了済）。
2. **#18 impl（A1/A2/A3）を現 kinematic 基盤で land + 再測**（v2.2 re-debate → impl。#18 の evidence base は kinematic 上で構築済 — その基盤で決着させる = 1 変数規律）。
3. **(d) rollout（下記 stage）**: #18 決着後に drive 移行 → #18 DoD（ik_chord=FF match）を **PD 基盤で再検証**（stage gate に内蔵）。
- 根拠: 逆順（(d)→#18）は「新 PD 動力学 × 既知 wrong-branch 破局」の 2 未知同時になる。また A1 branch guard は PD 下で**より load-bearing**（cross-branch target jump が物理 sweep として実行され cable を実力で撹乱するため）— #18 は (d) によって不要化しない（re-debate でこの点を明示可）。
- Rs/%12 が逆順を選ぶ場合の条件: #18 の全 evidence を PD 基盤で取り直すこと（現 evidence の substrate が変わるため）。

### stages（各 stage: L3 chain + Rs sign-off + video leg）
| stage | 内容 | re-validation gate |
|---|---|---|
| S-0 | P-D1 probe（§5） | probe bar 全成立 + bar 凍結 |
| S-1 | `newton_route_env` + `newton_skill_env_base:2080` 移行（FF+ik_chord+settle） | route 再現 vs Rs 動画標準 / grasp G1-G3 / seat parity / **(d-a) probe 再走 + anchor 再基線（宣言 delta、§7-3）** / #18 DoD 再検証 |
| S-2 | `route_executor`（producer）移行 | **golden/demo 再記録 = DDR #21 と単一 regen event**（旧 lineage は NOT_COMPARABLE 明示 — Phase0 規律） |
| S-3 | `aerial` / `approach` skill envs | 各 env smoke + 既存 test suite（route track 非依存ゆえ最後） |

**R-SEQ2（計画面反映）**: (d) は training-ready critical path に挿入される（trainer は準拠基盤で走るべき、C7 の解消として Rs が remediation を選択）。plan surface 反映 = %12 bank 後に p6 custody。

---

## §7 Q6 裁定 — trainer / pin / anchors 相互作用

1. **pin 例外 = 不変**: pin は body_q/eq 書込（`route_executor.py:792-794` 系 + eq 機構）で joint_q に触れない ⇒ Layer 8 非対象のまま・本移行と直交。**(d) は pin の実装面を 1 行も変えない**（brief Q6 の confirm、p5 設計として保証）。
2. **residual-on-script**: 意味論が「script が recorded **状態**を実現」→「script が recorded **target** を指令、PD が実現」へ精密化。obs は実状態を読むので closed-loop 補償可能 = **#18 と同じ closed-loop 動機の強化**。ただし **demos は kinematic 実現状態の記録**ゆえ S-2 で再記録必須（§6）。obs の joint 速度由来量は零→実速度に分布変化（bounded by tracking bar、regen で吸収）。
3. **(d-a)/(d-b) anchors**: fire_step/anchor 凍結値（live 2462 等）は kinematic-lineage。S-1 で **(d-a) probe を PD 基盤で再走し、§8.13 drift-loud 原則そのままに新 standing anchor を宣言 delta 付きで再基線**（bar 構造 = fire≺release / band / 順序は不変、番号のみ更新）。(d-b) は onset 窓を持たない設計（§9 charter）ゆえ構造変更なし — K-dwell の K=3 は physics-frame 単位で PD 下でも同一 cadence（`:1221` per-frame call 不変）、ただし **K の余裕（flicker）を S-1 で 1 leg 再確認**（PD の微小追従振動が capture 述語を flicker させないか）。
4. **fork-B/#19**: wc=1/proc に ctrl 機構は自然適合。wc>1 復活時は arm-servo readback の per-world 複製 assert（gripper `:314-317` 同型）が守る。
5. **substrate finding disposition（v1.4-④ で SUPERSEDE — v1.2 文言は over-claim を含んだ、旧文 = `3b5f75c131` 参照）**: 旧「banked contrast verdict は内部的に有効・遡及 flip なし」を**軟化・再述**: banked verdict が有効なのは【汚染基盤上の記録として】のみ。**O-1（diagnostic-grade、`fa1e786b46` §3）= 零化のみ（kinematic drive 不変）で banked 把持連鎖が消滅（g3 242→never / pin never / done=horizon）= 綱引きは banked 連鎖に load-bearing**（受動的背景でない — review P0-4「state-dependent, can interact」の実証形）⇒ **基盤を超えて意味を持つ主張（物理妥当性・RS71 §4 fidelity・transfer・「route は物理的に成立する」）= 清潔基盤上で UNVERIFIED**。review P0-4 に従い、decision-critical contrast は訂正基盤での再走対象。**L-P0 = REQUIRED に昇格**（旧 RECOMMENDED を supersede）— ③裁定機構（B1）下で再測 + verification legs + video leg を伴って evidence 化。**#18-contributor 仮説 = 推測 tag 維持・ただし plausibility 上方更新**（把持連鎖の tug 感度が単一 diagnostic で実測された — fold は依然禁止〔single run・video なし・B2 機構 caveat・O-4 confound〕）。caveat custody = %12 bank → DDR/LEDGER + p6 relay、scope 判断 = Rs。

---

## §8 force-design protocol 出力（skill 必須 4 点）

### 8-1 パラメータ表
| param | 現在 | 変更後 | 置場 |
|---|---|---|---|
| arm drive 方式 | kinematic 直書き（16 sites） | POSITION servo（A=11 migrate / B=5 維持+sync） | §4 |
| ARM_SERVO_KE/KD size3 | —（未配線） | 2000 / 400 | **task_config.py 新設**（SSOT、gripper `:314-316` 並び） |
| ARM_SERVO_KE/KD size1 | —（未配線） | 500 / 100 | 同上 |
| ARM_EFFORT size3/size1 | —（∞ 相当 = kinematic） | ±150 / ±28 N·m | 同上 + `jnt_actfrcrange` |
| JUMP_TOL / N_RAMP / TRIP | — | 0.05 rad / 120 frame / 15 mrad（暫定） | 同上（probe 後凍結） |

### 8-2 階層整合性
| 層 | ke | 上位との関係 | 判定（v1.4-⑦: 全行 = 設計意図、実測検証 = L-P3 + 訂正 probe） |
|---|---|---|---|
| Arm PD | 2000/500 | 最上位（位置を決める） | **UNVERIFIED** |
| Gripper servo | 66.7（`task_config.py:314`） | < Arm（把持は arm 位置に従属） | **UNVERIFIED** |
| effort: arm ±150/±28 ≫ gripper 2.5 N·m | — | arm が把持反力に負けない | **UNVERIFIED**（⚠ O-4 diagnostic: wrist_2 持続 ~0.5 rad 誤差 = size1 28 N·m 飽和の示唆 — ただし O-1 confound 込みゆえ結論不可、訂正 probe の仕事） |
| cable/contact（mujoco solref 系） | — | Arm PD が接触力に勝つこと = **L-P3 saturation leg で実測検証**（既知負荷: dual-load r_grip_N=119.3 @GOLDEN、静的 cable 45g は無視可） | probe 待ち |

「Arm positioning > contact transmission > grasp compliance」の設計序列は保存（gripper 66.7 と arm 2000/500 の比較は座標次第 [rad vs m] ゆえ、序列の最終確認も L-P3 の実測 effort で行う）。

### 8-3 dt 依存性
- 積分 = `implicitfast`（陰）⇒ ke=2000 @ dt=1/1920〜1/4800 の離散安定性は堅牢（陽積分の ke·dt² 制約に非拘束）。
- ⚠ **2 cadence を両方検証（訂正 #1 で整合化）**: RL path（substeps=4、dt=1/1920）と producer path（substeps=10、dt=1/4800）で PD 実効挙動が異なり得る（既知の 10-vs-4 mismatch と同根）。**P-D1 = @4**（trainer 基盤〔事実〕・conservative 側〔**仮説 tag、v1.4-⑤**〕・1 変数対照〔事実〕= §5 根拠 ①-③）/ **@10 = S-2 producer 移行 gate で native 検証**（route_executor は @10 が native ゆえ knob 不要、基線も @10 同士）。PASS@4⇒PASS@10 は推論であり S-2 で confirm — S-2 @10 が @4 より悪い追従を示したら（予想と逆方向）loud 異常として gains re-open。

### 8-4 感度テスト枠（probe 内 or FAIL 時）
| leg | 範囲 | 期待 |
|---|---|---|
| ×0.1（negative control、必須） | ke/kd ×0.1 | bar FAIL（計器が fail-able である証明） |
| ×0.5 | | 追従劣化の傾向確認（FAIL 時の下界） |
| ×1.0（v0） | | bar 内 |
| ×2.0（optional、FAIL 時のみ） | | 振動/overshoot 有無（⛔ effort cap は不変のまま） |

---

## §9 invariants / STOP / gate chain

- **§0#1-#5 不触**を設計で保証: dual-arm（両腕とも同機構で移行）/ 88mm・base 不変 / **#3 = IK が target 源のまま**（強化: 実現が物理化）/ コ-gripper 不触（gripper servo 系は 1 行も変えない — `:344` restore の B 維持含む）/ **#5 = pin 例外のみ**（§7-1）。設計 option が invariant に触れる分岐（例: 軌道再設計で grasp span 変更が浮上）= **STOP + Rs**。
- **effort cap を実機 spec 超に上げる提案は本設計で禁止**（fidelity 非保守方向）。追従不能なら軌道/速度 profile 側で解く（別チャンク、Rs）。
- gate chain（brief §5 を具体化）: **P-D1 probe（%12、prereg + 基線 + bar 凍結）→ p5 probe 結果裁定（bar 凍結最終化）→ L3 chain（rule-check → CC-Debate、impl diff 対象）→ S-1 impl（fenced、Rs sign-off）→ stage gates（§6）→ two-key（p5 設計軸 + pN evidence 軸）**。
- 本 doc = 設計裁定であり **実装認可でない**。probe prereg は %12 起草（P-D1 spec を §5 から転記 + run 前固定）。

## §10 p5 が %12 に要るもの（次 action、v1.4 = Rs HOLD 下の訂正 chain）
1. v1.4 bank + ③ B1-strip 再実装（+ B1 census readback）。
2. L-P5 再設計 input（O-3 対応、step-response/settling 方向 or bar-set 変更案）→ **p5 ratify**。
3. prereg v1.1 再凍結（review ①-④ 着地後。L-P0 REQUIRED + L-P2 acceptance 意味論再定義 + L-P5 新観測量込み）→ evidence-grade 走行（video leg 付き）→ 結果 dispatch。
4. probe 結果を受け p5 が bar 凍結 + §3 gains 最終化（FAIL 分岐なら感度枠 §8-4 / effort 飽和なら軌道側 = 別チャンク + Rs）。
5. bank 時: LEDGER/DDR 反映（(d) 行 + §7-5 caveat row）= %12 → p6 relay。R-SEQ（#18 先行 landing）の court 側 concur は継続項目。

## §12 prereg v1.1 ratification（v1.5、設計軸 — 対象 = `ARM_CONTROL_PD1_PROBE_PREREG_RSTECHLEAD_20260719.md` draft、p5 全文読了）

**① L-P5′ = RATIFY（as-is）**。p5 独立検算: {lift, elbow}（arm-local {1,2,7,8}）は size3 cap 150 N·m ≫ UR5e 重力 torque（~50-60 N·m 級）ゆえ **両 gain scale で非飽和線形域** → 定常誤差 = G/(scale·kp) ∝ 1/scale、×0.1 で ~10× 期待・bar 3× は margin。O-3 の死因（wrist_2 = 飽和域では誤差が cap 支配 = ke 鈍感）を正しく回避する観測量選択。ratio 基準 = scale-free で noise floor にも robust。W = min(14000, 10·done_R1, 10·done_R3) = 共通 prefix 保証（R1 早期 drop でも成立）。「不分離 = probe INVALID（FAIL でなく計器無効）」の意味論 = 正。

**② L-P2′ = RATIFY + 精密化 2（freeze 前 fold、bar 追加なし）**。3 分離（追従性 = L-P1/L-P3 自 ctrl stream 比〔chain 非依存〕/ artifact 依存 = L-P0 / acceptance = 清潔基盤 R0b parity）は v1.4 §5 L-P2 re-scope の正確な操作化。
- **P-1（parity-in-failure 対策）**: O-1 diagnostic のとおり R0b が把持連鎖を失うなら、R1-vs-R0b の predicate parity は「両者同 class で失敗」に退化し判別力が落ちる（a-test-that-cannot-come-out-differently の部分形）。→ **R1-vs-R0b の連続量 divergence（EE 軌道 + body_q 由来 cable proxy、per-frame、既存 log から offline 導出）を REPORTED leg として追加**（本 probe は bar なし・S-1 で bar 候補化）。predicate 行が退化しても比較が情報を保つ。
- **P-2（空窓の採点意味論）**: phase split の quasi-static 窓 = [g3_step, done] は **g3 不発火で空窓** → その場合 quasi-static bar（≤2 mrad）は **PASS でなく N/A-empty-window と報告**（vacuous PASS 禁止 — 採点されなかった leg を PASS と記録しない、records-match-fact）。transient bar（≤5 mrad）は全 frame で bind し続ける。
- 非 block nit 2: (n-1) §2 の「TRIP (M-6)」行名 → v1.4-⑥ 改名に合わせ `ARM_DIVERGENCE_BAR_RAD` candidate（informational、意味論不変）。(n-2) R0 の census は assert なしの**記述的記録**（nu=16・imported LIVE）を provenance に残す（N/A 扱いのままで可）。
- **sequencing note（prereg 変更でない、Rs surface）**: L-P0 が清潔基盤での連鎖崩壊を evidence 化した場合、S-1 の再検証 gate「route 再現 vs Rs 動画標準」は **choreography 側で blocked** になる（realization の問題でなく記録された振付が artifact 依存）→ (d) rollout の再 sequencing（清潔基盤での demo 再記録を S-1 検証より前へ = #21 fold の前倒し）が必要になり得る。判断 = Rs。

**verdict: 両 leg RATIFY〔設計軸〕・P-1/P-2 fold 後に凍結 → evidence 走行可**。凍結 commit の版表反映 + 走行後の bar 凍結最終化 = §10 chain のまま。⚠ §12-① L-P5′ は **§12.1 で supersede**（11:31 %12 自己 supersede 提案 → p5 精査の上 RATIFY。§12-① の検算自体は当時の設計に対し健全 — より強い計器への置換であり撤回でない）。

### §12.1 A-P1-3 negative control 再設計 = stale-target PRIMARY を RATIFY（v1.5-④、条件 1 付き）

- **採択**: R3 = **決定論 stale-target**（ctrl を recording frame-0 に全走行凍結）。期待誤差曲線 = **`|rec[t] − rec[0]|` per joint = npz から閉形式 precompute 可能** ⇒ (i) 計器配線の end-to-end 較正（測定 curve が precomputed curve と一致すること）(ii) bar fail-ability の実証（rad 級誤差が L-P1 bar を必ず超える = fail する走行が実在しパイプラインが flag する）を **1 走行で両立**。×0.1（旧 L-P5′）より強い: 期待値が物理仮定なしの決定論・smoke-2 で偶然実証済み。**×0.1 = R4 exploratory 降格 concur**（非 gating）。
- **⛔ RATIFY 条件（p5 検出の罠）**: stale 走行の採点 stream を **明示的に intended-stream（recording）比 `|q − rec[t]|`** と定義すること。自 ctrl stream 比（L-P1 の既定 = `|q − ctrl|`）で採点すると q ≈ frozen ctrl → 誤差極小 → **negative control が vacuous PASS 化**（計器を検証するはずの走行が計器の既定に騙される、gate-validated-under-the-bug の直系）。一致判定 = precomputed curve との per-joint 偏差 ≤ band（band = PD hold 定常誤差 G/kp 級 + noise、prereg で宣言・凍結）。INVALID 意味論継承: band 超過 = **計器 INVALID**（probe FAIL でない）。
- 副次: stale 走行は arm が frame-0 保持のまま = cable 不接触の良性走行（把持なし・horizon 完走見込み）。

### §12.2 A-P1-4 route-start re-pose 受入検査群 spec（v1.5-⑤、p5 spec → %12 実装）

全て LOUD-fail（raise、probe-blocking）。発火回数 = episode 毎 exactly 1（`route_start_repose_count==1`）。

| # | 検査 | 述語（exact） |
|---|---|---|
| A-1 | 値の忠実性 + limits + winding | seeded q[arm 12] == rec[frame0] を許容 ε=1e-9 で一致（**正規化・wrap 折返し禁止** — winding は正確値継承で自動保存）∧ 全 seeded q ∈ [qmin, qmax]（model limits） |
| A-2 | M-4 sync | 直後に ctrl[arm] == seeded q（ε=1e-9）∧ qd[arm] == 0 |
| A-3 | cable 不変 | re-pose 書込の前後（solver step を挟まず）で cable 状態 slice（pos+vel）が byte 恒等（teleport は arm joint_q/ctrl のみに触れる証明） |
| A-4 | 貫通/接触 impulse | re-pose 直後の初 physics frame: arm 関与 contact pair の penetration ≤ ε_pen（宣言値）∧ cable の frame 間 `max\|Δv\|` ≤ band（R0b 同 frame 比、宣言値）— teleport された arm が cable/table/clip と交差していないこと |
| A-5 | gripper 状態 | OPEN ∧ 非把持（訂正 #3 既存 guard を本 suite に fold） |
| A-6 | provenance | recording sha256 == prereg pin ∧ frame-0 行 index == 0 を記録 |
| A-7 | pin/eq ownership 不整合なし（v1.6-④、A-P1-1 残） | re-pose 書込の前後（solver step を挟まず）で clip-pin eq 状態 slice（eq_active flags + eq anchor/data 配列）が byte 恒等 ∧ 境界での期待状態 = pin 未発火（fired flag False・onset None・audit counter 0）を assert — **re-pose は eq を activate/deactivate/re-anchor しない・eq ownership は pin 機構（authorize_clip_pin 経路）に排他帰属のまま**（INVARIANT#5 の例外面に re-pose が触れないことの機械保証） |

band/ε_pen の数値 = prereg 凍結時に %12 が宣言（p5 readback で確認）。

## §13 P-D1 RESULT 裁定（v1.7、設計軸 — 対象 = `ARM_CONTROL_PD1_RESULT_RSTECHLEAD_20260719.md` bank `e5d2dc214a`、p5 全文読了。⚠ video leg = PENDING ゆえ物理妥当性の最終言明は Rs 動画後）

### R-1 probe verdict（凍結 bar のまま・bar 移動なし）
- **FAIL(tracking-transient)**〔tr_joint_max 0.512 rad / tr_EE 99.9mm vs 凍結 bar 5mrad/3mm〕を **as-frozen で record**。計器は全 VALID（R4 較正 dev 8.9mrad ≪ band 196 / R3≡R2 恒等 0.0 / ctrl≡intended 0.0）ゆえ FAIL は信頼できる。
- pivotal unknown（brief §3）の分解回答: **力 = FEASIBLE 確立**（飽和 0.0%・worst 25.1<28 N·m、定常力 ≈ τ_ext の機構整合）/ **速度帯域 = vendor gains では banked 記録の速い区間に不足**（粘性 slew lag err≈(kd/ke)·ω、実測則一致、T_lag = 400/2000 = 100/500 = **0.2 s 一様**）/ 静的精度 = 遅い区間で 1-5 mrad（2mrad 目標圏。形式上は qs 窓 EMPTY→**N/A per P-2 — %12 の「never PASS」適用は正、ACK**）。
- L-P2′ = **PARTIAL record ACK**（述語 parity 成立・termination parity 不成立〔R1 horizon vs R2 drop@141 = lag が contact-loss debounce を trip〕、P-1 連続量 reported ✓）。A-suite/L-P4/L-P6 = PASS。

### R-2 §8-4 適用 = **可、ただし機構指向形（blind ×0.5/×2 でない）**
- **lever = kd/ke 比**（%12 示唆に concur、実測機構が根拠）。授権 exploration = **R2-class 単発 re-probe × 候補 2**（prereg v1.3 = 宣言 diff で凍結後）: **C-1 = kd×0.25**（T_lag 0.2→0.05 s、lag@2rad/s ≈ 0.13 rad）/ **C-2 = kd×0.25 + ke×2**（T_lag 0.025 s）。⛔ effort cap 不変（§3.1）。各走行に ringing/overshoot 報告 leg + M-6 dwell + L-P3 を必須添付（ζ ~3→~0.8 の減衰余裕は概算〔仮説 tag〕— **安定性 authority = 実測**、v1.6-③）。
- **S-1 bar 構造の再設計を宣言**（本 probe の verdict 救済ではない — measured mechanism が正当化根拠）: 一律 transient 5mrad は smooth-lag class を誤モデル化（実質、指令速度を bar している）。S-1 案 = (i) 静的/settle 窓 ≤2mrad〔維持〕 (ii) **lag-law bar: 実測 T_lag = err/ω ≤ T_LAG_BAR**（速度非依存の realization 品質量、凍結値は C-1/C-2 実測後） (iii) phase-endpoint 到達 err ≤ 5mrad（task が消費する精度点） (iv) no-ringing（overshoot bar + M-6 持続 0） (v) M-6 divergence guard。→ prereg v1.3 で宣言凍結、最終 S-1 freeze は Rs re-sequencing 後。
- FAIL(saturation) 分岐 = 発動せず（0.0%）— re-trajectory chunk 不要の確認。

### R-3 順序裁定（choreography-blocked との関係）
- **L-P0 headline = S-1 choreography-blocked を evidence 級で CONFIRM**（R1 clean-kin ですら連鎖 never・arm q 差 ≤1.1mrad ⇒ flip は cable 側 knife-edge 応答。gains をどれだけ改善しても R1 の再現 = 連鎖死 — **gains 側では直せない**）。
- 並行構造: **(W-a) kd-lever re-probe（R-2）= PARALLEL-OK**（安価・read-only・Rs 判断と独立に S-1 bar 設計を進める）/ **(W-b) 振付再工事**（清潔基盤 demo 再記録 = S-2 前倒し、#21 fold）= **Rs 専権 surface**（banked 再利用 impact + re-sequencing）。
- 順序: **(1) video leg 納品（R0/R1/R2 → ~/Downloads）+ 本 RESULT の Rs 供覧が最優先**（L-P0 headline の物理妥当性は Rs 動画 human-GT が最終）→ (2) W-a 並行 → (3) Rs 決定後に S-1/S-2 計画改訂。
- **forward 設計要件（再記録 charter への input、今裁定の付帯）**: 1mrad 級で連鎖が flip する振付は DR/residual（15mm 級）/noise 下の訓練に耐えない — **再記録振付には robustness leg（摂動耐性 ≥ trainer residual/DR scale）を必須化**し、「もう一つの knife-edge を bank する」再発を防ぐ（O-1/#18 の marginal-grasp 共通 thread）。

### R-4 次 action
1. %12: video leg 納品 → Rs 供覧（RESULT + 本 §13 pointer 添付）。
2. %12: prereg v1.3（C-1/C-2 + S-1 bar 案 + ringing leg）起草 → p5 readback → 凍結 → W-a 走行。
3. Rs: re-sequencing 決定（W-b）→ 決定後に p5 が S-1 bar 最終凍結 + stage 計画改訂。

**§13-R prereg v1.3 §7 readback = ACCEPT（v1.8、13:45）**: on-disk 照合 = message と一致・修正要求なし。検定: C-1/C-2 flag/期待値 = §13 R-2 授権一致（仮説 tag + measured-governs 規律 ✓）/ cap 不変 census assert ✓ / **lag-law ω 定義 = intended stream frame 差 ×480 で draft が既 pin**（p5 が要求予定だった唯一の精密化が先回りで充足 — 除算 noise 回避の ω>0.5 閾値も正）/ ringing 両翼 >2mrad 定義 = noise 交差除外 ✓ / R-1 FAIL 不変明記 ✓。非 block nit 1: §7 が §6 より前（凍結時に並び整理可）。**v1.3 凍結 → C-1/C-2 走行 OK**。⚠**14:0x SUPERSEDED（Rs 完全削除指示）**: C-1/C-2 = 未起動のまま中止、再定義 = §14.8。

---

## §14 NO-KINEMATIC 完全削除 CHARTER（v2.0、設計 court — Rs 最上位指示「kimenaticを完全削除！」×3〔p5 pane 直接 + %12 同時受領 14:01〕への設計解。⚠ clip pin 含否のみ Rs 確認中 = §14.7 fence、他は確定スコープ）

### §14.0 指示と設計原則
- **⭐原則 0（Rs 恒久原則 14:2x、全設計判断の基準・verbatim）: 「simは現実世界だ。常に現実と同じ条件にしろ」** — 本 arc の全指示はこの単一原則の系: kinematic 全削除（実機に teleport はない）/ force cap 実機 spec 不変（実機を超える力はない）/ pin → 物理接触（実機に magic weld はない）/ 初期条件の物理化（実機は home から物理的に動いて始める）。**今後の全設計選択の test =「現実世界はそうか？」**。反射適用 1 点: §14.3 の `Ω_TR` は実機 UR5e joint 速度 spec 内で凍結（datasheet 照合 = v0.9 設計時、spec 超の transit 速度は原則違反）。
- **指示 = 不使用でなく【削除】**: kinematic 書込コードを codebase から除去。flag 共存・基線温存 = 一切なし。
- **原則**: t=0 の初期状態 = **model 定義（vendor keyframe home `ur5e.xml:135`）のみ**。runtime の arm joint_q/qd 書込 = 全廃。以降の全姿勢変化 = PD 物理過程。**per-episode の qpos seeding も行わない**（episode 開始姿勢へは PD 実移動 = §14.3）。
- **scope 境界（loud 宣言）**: 本 charter の対象 = **arm**（remediation (d) の scope）。cable の reset 再 seed（object 状態初期化）と gripper servo（既に物理）は対象外 — cable reset も物理化すべきなら Rs 別途指示（先回りで surface）。

> ⚠ **§14.1-2 scope 拡張（v2.5、§14.13-14 で確定）**: 完全削除 scope = **3 delivery sink 全部** = joint-state（`.joint_q/qd.assign`）∪ **body-state（`.body_q/qd.assign`）**∪ eq/weld（`eq_active` CPU+mjw+proto）。下記 §14.1 の site 表は joint-state 中心の初版列挙 — body-state sink（`assign_world_states_to_sim` robot 部 + grip env ×15）と eq device/proto 面は §14.14 の分類 RULE で covered。判定は変数名でなく **delivery surface（sink）**で行う（[[feedback-verify-at-the-delivery-surface-not-the-source-variable-name-2026-07-19]]）。

### §14.1 D-① A 11 sites = actuator 化して削除
- 各 per-step kinematic write → ctrl write（target stream = §2 のまま: FF = recorded per-frame / RL = jq_interp / settle-hold = 定数）→ **kinematic 経路と helper を削除**: `apply_arm_only_write_broadcast`（`route_executor.py:213`）/ `apply_arm_only_write_perworld`（`:236`）/ `broadcast_jointq_to_all_worlds`（`newton_skill_env_base.py:2080`）/ legacy STEP-1 block（`route_executor.py:1817-1824`）/ 各 env の per-step 直書き（§4 A 行の全 call site）。
- M-1 配線（B1-strip + proto POSITION servo）= **無条件化**（flag 撤去）。qd 零化コードも全廃（速度は常に物理量）。

### §14.2 D-② B 5 sites = 物理過程化して削除（reset-init 例外 = 失効）
- **reset re-pose 3 箇所**（`newton_route_env.py:1094` / `aerial:1090` / `approach:746`）→ 削除。episode reset の物理化 sequence: **(1) gripper PD open →(2) PD homing transit（現姿勢 → keyframe home、§14.3 と同 profile 機構）→(3) cable 再 seed（scope 外・現行のまま）→(4) settle（PD hold at home）→(5) PD transit → script 開始姿勢（§14.3）→(6) route**。sim 時間 cost（transit+settle ~数 s/episode）= 指示の受容 cost として宣言（throughput 影響は probe で実測）。
- **phase-k restore**（`route_executor.py:342-344`、arm+gripper 復元）→ **機構ごと削除**。branch-replay 方法論の置換: mid-episode snapshot 復元は本質的に teleport ゆえ物理化不能 — replay は **reset からの全物理再実行**で branch 点へ到達する（cost 増を宣言、probe/検証系の再設計は %12 court）。

### §14.3 D-③ route-start = PD 実移動（旧 (b) 本採用）+ route clock 設計
- **transit profile**: joint-space 線形 ramp、`ω_transit ≤ Ω_TR`（提案 1.0 rad/s → worst 5.6 rad ≈ 5.6 s sim）。**衝突安全 leg 必須**（旧 (b) 却下理由の解消）: (i) offline FK sweep で transit 経路の arm↔table/cable/clip clearance を事前検証 (ii) 必要なら lift-waypoint（上方経由）1 点を挿入 (iii) probe video leg で Rs 確認。
- **route clock = ARRIVAL latch で開始**: 到着述語 = max-abs over 12 arm dof `|q − q_start|` ≤ `ε_arrival`（**10 mrad provisional、TK-3 で 5→10 精緻化・freeze-after-measure**、= 実装済 `_ROUTE_START_POSE_TOL_RAD`）が `W_arr`（提案 48 frame）連続 → latch → route_steps 起動。**latch まで route clock は走らない**（TRANSIT phase として状態明示）。timeout `T_max`（提案 3× 公称 transit 時間）超過 = LOUD fail（silent stall 禁止）。
- 到着精度 = 新しい開始条件（teleport 正確性の置換）。lag 則より到着時 ω→0 で誤差は静的域（1-5 mrad 実測)→ ε_arrival 5 mrad は成立見込み〔仮説 tag・probe が authority〕。

### §14.4 D-④ kinematic 基線概念の廃止（計測方法論の置換）
- kinematic 走行 = 計器用途含め全廃。今後の対照 = **PD-vs-PD**（parameter 対照）/ **PD-vs-intended stream**（tracking legs、走行不要の stream 比較）/ **PD-vs-banked npz（offline data 参照）** — banked 記録を「読む」ことは使用でない（歴史 data・label としての参照は継続可、⚠ その物理的意味は汚染基盤上の記録に限定 = §7-5）。
- stale-target 較正（R4 型）= 純 PD 走行ゆえ**計器として存続**。L-P0 型の汚染定量 = 完了済（`e5d2dc214a`）・基盤消滅により以後不要。

### §14.5 D-⑤ Layer 8 強化
- baseline WARN（16 sites 許容）撤廃 → **env code の arm joint_q/joint_qd runtime 書込 = 全件 FAIL**。t=0 model keyframe = runtime 書込でないため対象外（checker 定義に明記）。checker 改訂 = %12 impl・L3（`check_control_method.sh`）。

### §14.6 D-⑥ demo 全物理再記録（必然帰結、W-b/#21 単一 event）
- producer（route_executor）の PD 化 = 再記録の前提（旧 S-2 が必須化・前倒し）。
- **再記録 charter 要件（carry + 新規）**: robustness leg 必須（摂動耐性 ≥ residual/DR scale、knife-edge 再 bank 禁止 = §13 R-3）+ **commanded/realized 両 stream を npz に記録**（PD 基盤では両者が乖離 — 将来の訓練 label に両方要る）+ 記録は全物理 sequence（§14.2）で生成。
- **#18 = PD 基盤で再測**（R-SEQ 逆転の最終形。§6 R-SEQ「#18-first-on-kinematic」= SUPERSEDED）。

### §14.7 clip pin fence — **SUPERSEDED（14:0x、pN 経由 Rs 正式 directive）→ §14.10**
- Rs 裁定確定: **pin 例外も全廃対象**（「従来の NO-KINEMATIC-TRICK 唯一例外 clip-retention pin も superseded」verbatim relay 13:34/14:06）。§0#5 の「唯一の授権例外」= Rs 専権で撤回された premise change。置換設計 = §14.10（p5 court）。

### §14.8 C-1/C-2 再定義
- 旧 C-1/C-2（a-2 teleport 込み）= void（未起動中止）。**C′-1/C′-2 = 同じ gains 候補（kd×0.25 / +ke×2）を no-kinematic 全物理 episode（home settle → PD transit → route playback）上で走行**。lag-law/ringing/L-P3 observable は不変 carry + **新 transit legs**（到着精度・到着時間・clearance・LOUD timeout）。probe v0.9 = %12、prereg v1.4 = charter bank + readback 後に凍結。

### §14.11 REMOVAL milestone 受領（v2.3、15:51 — %12 報告 15:42 への p5 独立 on-disk 検証。⚠ formal 検証 = 別レグ = review chain の two-key、本節は milestone receipt + 設計適合 read）
- **対象 commit（worktree branch `probe/pd1-arm-pd`、committed blob を git grep/show で検証 = dirty-tree 非汚染）**: chunk1 `2213a01df2` / chunk2 `9fcb973726` / chunk3 `18c428b7e6`(tip)。main tree = 未 landing（凍結中）。
- **✅ 独立確認（producing commit）**: (1) **kinematic 直接書込 = 0**（Layer 8 署名 `(phys_jq|joint_q|qpos)\[…\]=` で tip=**0**、baseline bc1f7f2d48=13〔※%12「16」= 元 main 0f39f7b598 の Layer8 full 数、13=probe v0.8 で re-pose/strip 済の中間 — 差は数え方、tip=0 は一致。数え方の reconcile は two-key 項〕）(2) **削除 = ctrl 駆動への置換**（bare 削除でない）: `newton_route_env.py` に `joint_target_pos.assign` 群（:907/:1177/:1266/:1472）= arm が actuator 駆動 (3) **pin closure = airtight**: `_maybe_activate_c1_pin:2049` = `if not self._route_c1_pin: return` 早期 return ∧ `route_c1_pin=True` は config で `RuntimeError`（chunk3 `newton_route_env.py`、「pin REMOVED from active execution / Rs directive 2026-07-19」）→ flag 恒 False → `authorize_clip_pin:2060` 到達不能。code 保存 = §14.10「歴史 evidence 保存・active path 除外」適合。
- **⚠ records-match-fact 註（narrative 精密化）**: %12 chunk1 narrative「authorize_clip_pin = fail-closed raise」は**不正確** — `authorize_clip_pin`(:986) は body 健在で raise 化されていない。実機構 = **config-refusal + unreachable-by-flag**（別関数の raise）。設計 intent（pin 非 active）は満たすが、機構の記述が異なる。two-key で helper 群（`apply_arm_only_write_*`/restore/legacy）の disposition（削除 vs raise）も narrative と照合要。
- **⛔ 削除 ≠ 稼働系（loud、本 milestone が establish しないもの）**:
  1. **§14.3 PD homing/route-start transit = 本 3 chunk に不在**（teleport は除去されたが物理 transit 置換は未実装 = C′/prereg v1.4 の仕事）。⇒ この worktree を今走らせると arm は home から ctrl 指令で route-start へ 5.6 rad haul（finding#2 の問題そのもの）。除去レグと transit レグは別。
  2. **§14.10 C1 物理保持 = 未実装**（pin 閉鎖のみ・lever L1/L2/L3 は p5 court 設計中）⇒ route playback で C1 は保持されない（RS71 §4 境界）。**この worktree = REMOVAL milestone であって working route system でない** — HALT 意味論と整合。
- **two-key posture（p5 設計軸レグ、review chain 内）**: source review + /pre-check 後に、私は **fresh detached worktree @ tip で (i) 実 Layer 8 checker 走行〔0 の権威確認 + 16/13 reconcile〕(ii) A-suite/§14 全 D-項 適合〔helper disposition・qd 零化廃止・reset 物理化の有無〕(iii) pin unreachability の網羅〔`_route_c1_pin` の後続 mutation 無・両呼出 gated〕** を検証。**main landing 承認 = 上記 + §14.3 transit + §14.10 物理保持が揃うまで NO**（削除単独では landing 不可 — 稼働系でないため）。
- v2.3 bank = commit 凍結ゆえ as-read sha pin で %12 対応（本節の commit 参照は上記 3 sha に pin 済）。
- ⛔⛔ **§14.11 自己訂正（v2.4、16:34 — %12 source review `a3d3232d1e02` R1 が私の 15:52 検証の blind spot を摘発）**: 私の「kinematic 書込=0 CONFIRM」は **pattern-scope でのみ真・mechanism-scope で偽**だった。**route-start teleport（v1.3 #3）が `ARM_PD_DRIVE=1` 下で live 残存**していた（alias `_rep_jq[_rep_q12]=_rep12` → `_state_0.joint_q.assign(_rep_jq)`、pre-c4 :1255/:1265）。私の grep 署名 `(phys_jq|joint_q|qpos)\[` は **変数名依存**ゆえ alias `_rep_jq` を捕捉できなかった。従属して §14.11 の「(b) home-haul」記述も **understating 方向に誤り**（tip では teleport が発火・haul は起きていなかった）。**根因 = 私が source(変数名) を grep し sink(delivery surface `.joint_q.assign`) を grep しなかったこと**。教訓 = [[feedback-verify-at-the-delivery-surface-not-the-source-variable-name-2026-07-19]]。⇒ §14.11 の 3 CONFIRM は **c4 `349d13551c` + sink 検証（§14.12）で置換**、15:52 の verdict は withdrawn。

### §14.12 two-key TK 裁定（v2.4、16:34 — 対象 tip = c4 `349d13551c`、sink-based airtight 検証）
- **TK-1a = ✅ CONFIRM（delivery-surface 網羅、alias 不問）**: tip の全 joint-state `.assign`（envs/）= **(i) `fk_state` receiver 8 箇所**（FK scratch model・stepped sim state でない・physics forcing でない）+ **(ii) `state.joint_q/qd.assign` CABLE-SEED marker 2 箇所**（`newton_skill_env_base.py:1100-1101` cable reset-init・§14.2 step-3 scope-out・loud echoed）**のみ**。**arm を `_state_0` へ書く経路 = ゼロ**、`_rep_jq` alias 消滅、raw qpos/qvel ゼロ。今回は sink（`.joint_q.assign`）で数えたので alias evasion 不可能 = 前回 blind spot の根治。
- **TK-1b = ✅ §14 D-項 conformance**: D-①（A 11 sites）= ctrl 置換（`joint_target_pos.assign`）・sink clean / D-②（B・route-start）= **fail-closed pose gate**（`newton_route_env.py:1209` `_rs_gap > _ROUTE_START_POSE_TOL_RAD` で raise・arm_q 無記録も raise `:1200`・within-tol は servo target sync のみ〔actuator write, no joint_q〕）。§14.3 transit 未実装ゆえ **gate は恒 raise（home ~5.6 rad 遠）= route env fail-closed** = landing bar と整合 / §14.10 pin = **3 重閉鎖**（config refusal + `_maybe_activate_c1_pin` flag guard + `authorize_clip_pin:1021` entry raise、dead body 保存）。**D-③ transit / §14.10 物理保持 = 未実装（既知・landing 前提）**。
- **TK-2 = uniform-delete 裁定（%12 推奨に concur）**: `authorize_clip_pin` の entry-raise 下の dead body = **削除**。理由: (1) **§14.10「code 保存」= git history が evidence store**（`git show <sha>:route_executor.py` で永久取得可、in-file 保持は不要）(2) **uniformity** — arm-FF helpers は既に body-deleted+entry-raise、authorize だけ body 保存は不整合 (3) **latent hazard** — unconditional raise 下の full-working pin body は、将来 raise を消すと silent 再武装（削除すれば再武装に body 再実装が要る = 防壁）。**条件**: entry raise message + 1 行 provenance コメント（body が在った sha + §14.10 pointer）を残す / **(d-a)/(d-b) の pin テスト群も同時 retire**（削除機構を test する dangling を残さない・§14.10「実行候補から除外」と整合、test は git history に evidence 保存）。
- **TK-3 = 0.05 rad placeholder を REPLACE → 0.01 rad（10 mrad）provisional + freeze-after-measure 義務**: 0.05（50 mrad）は EE ~42mm start error = seat bar 3.5mm を桁で超える初期誤差を route 開始前に注入 = 不可。**provisional = 10 mrad max-abs（12 arm dof）**: 根拠 = (i) 実測 static settle 精度 1-5 mrad（RESULT §3）の 2× = 達成余裕あり (ii) EE ~9mm = first-phase budget 内 (iii) 私の §14.3 ε_arrival「5 mrad 提案」を RESULT データで 10 mrad に精緻化（max-abs 形式で reconcile）。**最終値 = §14.3 transit probe の settle asymptote 実測で freeze-after-measure**（現在 gate は恒 raise ゆえ本値は inert = 設計 target-setting であり live 挙動変更でない）。§14.3 の ε_arrival を 10 mrad provisional に更新。
- **landing bar（削除∧§14.3 transit∧§14.10 物理保持）= %12 CONCUR 受理・維持**。guard v2 fold / 実 Layer8 v2 走行 / R-SEQ concur / hook posture = **pN レグ（TK-1c 系、evidence 軸）** — 私の sink census は pN の Layer8 走行を corroborate（独立 2 経路一致で closure）。

### §14.13 two-key round-2（v2.5、17:21 — tip c5 `9d00a15276`、%12 c5 fold + pN O-2 裁定 fold。⚠ 本 arc の第 3 の sink-completeness 教訓）
**方法**: 前 2 盲点（R1 alias / pN B1 独立 writer）を踏まえ、**3 sink を網羅列挙分類**（source 変数名でなく delivery surface）。

- **SINK-1 joint-state（`.joint_q/qd.assign`）= ✅ 宣言 path CLEAN**: 全 11 hit = `fk_state` scratch 9 + `CABLE-SEED` marker 2、arm→`_state_0` 書込 = 0。`broadcast_jointq_to_all_worlds`(:2156) = entry-raise ✓。
- **SINK-2 body-state（`.body_q/qd.assign`）= ⚠ OPEN（pN B2 / O-2）**: `broadcast_fk_to_all_worlds`(:2141) = entry-raise ✓ だが **(i) `assign_world_states_to_sim`(:1155→:1183/1184 body 書込) = raise なし・route `:1188`/approach `:735` の reset path から呼出 = reset-init body 面 / (ii) `newton_grip_env.py` の `_state_0.body_q/qd.assign` ×15（per-step + settle drive）**。= 第 2 の kinematic 面。
- **SINK-3 eq/weld = ✅ CPU activation writer 全滅・enforcement のみ**: activation writer（`activate_c1_pin` body 削除+raise `:726` / `authorize_clip_pin` entry-raise `:951`+body 削除 / PERCLIP inline `:3286` raise）全て閉。CPU `mjd.eq_active` 書込 = **=0 disarm loop `:2042` のみ**（who-wrote-it-agnostic enforcement + readback assert `:2043-2044`）。⚠ **device(mjw/warp) + proto の eq 面は本 CPU grep 非対象** = pN「他 eq_active writer」= eq 3 表現の未 cover 面（[[reference-newton-eq-three-representations-cpu-write-gpu-inert-2026-07-16]]）→ guard v3(O-1) で必須。

- **TK fold 確認**: TK-2 = `activate_c1_pin`/`authorize_clip_pin` body 削除 + provenance 行 + writesite test retire ✓（⚠ `authorize_clip_pin` docstring は working-authorizer 記述のまま = stale prose・next-touch cosmetic）/ TK-3 = `_ROUTE_START_POSE_TOL_RAD=0.01` ✓。

### §14.14 O-2 裁定 fold + body-state sink 設計 disposition（pN 17:16 裁定 = grip body-drive mandatory IN-SCOPE `CLAUDE.md:72`・Rs 再確認不要。p5 owns 物理置換 semantics + reset-vs-drive 分類、p4 census/impl、pN verify）
- **O-2 fold = ACCEPT**: body-state kinematic drive は `CLAUDE.md:72`（substrate 非依存 no-kinematic-trick = 物理無視の強制配置。body_q 直書きは forced placement）で既に禁止。scope 再確認不要に concur。**charter §14 D-① を拡張**: 完全削除 scope = **3 sink 全部**（joint-state ∪ body-state ∪ eq〔CPU+mjw+proto〕）。これは premise 変更でなく §14 の joint-centric な**過小列挙の訂正**（no-trick premise は元から body-drive を含む）。
- **⭐reset-vs-drive 分類 RULE（p5 設計 ownership・census 各行判定 = p4）**:
  - **DRIVE（per-step control-loop）**: step loop 内で body pose を毎 frame target へ強制する body_q/qd.assign = kinematic trick → **物理置換**（robot/finger body は joint_q + actuator + `mj_forward` で従属導出、body_q.assign しない）。arm joint_q→ctrl 移行の body 版。
  - **RESET（episode 境界の robot/finger body seed）**: `assign_world_states_to_sim` の robot/finger 部分 = reset-init body 書込。**§14.2 で reset-init 例外は失効** → 物理化: reset は joint_q を model-home（or 物理過程）で seed し **body は `mj_forward` で joint から導出**（body_q を書かない・「body は joint に従う」）。
  - **CABLE-SEED（object 初期条件）**: cable body/joint seed = §14.2 step-3 scope-out（marked+loud）。cable は物理 object ゆえ reset 初期条件 = object-state init であって robot kinematic drive でない。Rs が cable-reset 物理化を別途裁定するまで保持。
  - **FK-SCRATCH**: `fk_state.*` = legit（stepped state でない）。
  - 判定式（p4 census 用）: 各 body_q/qd.assign に「これは robot/finger body の pose を強制するか（drive or reset）?」→ yes なら削除（drive→actuator / reset→joint-seed+mj_forward）、cable object 状態なら CABLE-SEED marked、fk_state なら legit。
- **⭐grip env 物理置換 semantics（p5 ownership・grip node owner が impl）**: `newton_grip_env`（コ-finger + cable、env7-mujoco）の body_q drive の置換原理 =（(d) + §14.10 と同一原則）: **arm = actuator servo（body は joint 従属）/ finger コ = POSITION servo**（route env の gripper servo が実証 pattern）**・cage-hold は物理接触**（§14.10「retention = 物理 clip contact」の finger 版 = form-closure を物理接触で）/ **cable = 物理 object（contact + seed のみ）/ reset = model-home からの物理 settle**（body teleport でない）。⛔ robot/finger の body_q.assign = 全廃。
- **round-2 verdict**:
  - **(d) 宣言 ARM joint-state path（route/approach/skill-base arm）= 削除 PASS**（SINK-1 clean・sink 検証済・TK 全 fold）。
  - **REPO-WIDE 完全削除 = HOLD/PARTIAL（pN と一致）**: body-state sink open（`assign_world_states_to_sim` robot-body reset 書込 + grip env ×15）+ eq device/proto 面（3 表現）+ pN runtime **F821**（削除で残った dangling name、p4 fix）+ 他 eq writer。**landing bar 精緻化: 削除 = 3-sink 全 clean**（joint ∪ body ∪ eq〔全表現〕）∧ §14.3 transit ∧ §14.10 物理保持。c5 = 削除 PARTIAL。
- **記録**: F821 + device-eq = p4 impl（O-1 guard v3 に AST receiver + body_q + mjw/proto eq + F821 検出 self-test を畳む）。grip env census/impl = grip node owner（p5 semantics 済）。LEDGER (d) 行は v1.1 表記で stale → %12 bank 時に v2.x 反映（p6 relay）。
- ⭐**§14.14 = two-key CONCUR-CLOSE（17:30、pN on-disk readback PASS/CONCUR — §14.14 本文 + LEDGER (d)/DDR #25 cross-read）**: 設計軸(p5)+証拠軸(pN)が (i) O-2 = IN-SCOPE blocking (ii) 削除判定 = 3-sink（joint ∪ body ∪ eq〔CPU/mjw/proto〕）全 clean (iii) reset-vs-drive 分類 + 置換 semantics(arm/finger servo・body=joint 従属・cage-hold=物理接触・reset=joint-seed+forward/settle) (iv) **CABLE-SEED 例外の絞り込み = object episode-boundary init かつ marked+loud の範囲のみ・runtime drive / robot-finger body write へ拡張不可**（pN 明示 guard-rail・p5 affirm）(v) verdict = 宣言 arm path PASS / repo-wide HOLD (vi) landing bar = 3-sink clean ∧ transit ∧ physical retention (vii) #18 は 3 条件後、で一致。**⇒ round-2 の設計 disposition は CLOSED（両軸）。残 open = impl/verify レグ（p4 census/impl・grip owner・guard v3・F821・dead lifecycle/test disposition）であって設計 open でない。**

### §14.15 grip env 物理置換 semantics（v2.6、17:43 — pN O-2 で割当の p5 core deliverable。census = %12 c6 `a004f2ce66` review §10 addendum 15 sites/6 群。⚠ grip = 別 ACTIVE WORKING banked node〔env7-mujoco コ-finger〕ゆえ semantics のみ提供・impl=grip owner・**banked grasp 結果の再検証 gate 付き**）

**接地（p5 on-disk 自読 @ c6 tip）**: grip drive = IK objective（`_ik_obj_pos/rot_left/right.set_target_*` :830/1651）で jq_targets 算出〔§0#3 IK 準拠〕→ FK interp → `eval_fk_batched` で body 計算 → **非 finger robot body を毎 physics step `_state_0.body_q.assign` で強制配置**（:1697、VBD-era kinematic realization）。finger = `_finger_set`（`_finger_physics_ids` :657）除外 = 物理。solver = SolverMuJoCo（:855、actuator 駆動可）。**⇒ これは (d) route env の arm joint_q kinematic drive の body 空間版 = 同型 migration**。arm actuator servo は grip env に**未配線**（現状 body_q が唯一の arm 駆動）。

**⭐設計原理 = 「(d) 解の grip への継承」（reuse-first、AGENTS.md）**: IK target 層（§0#3 準拠）は不変、**realization を body_q.assign → actuator ctrl + `mj_forward` に置換**。route env gripper servo + (d) M-1/M-2 が実証 pattern。

| 群 | sites | 物理置換 semantics（p5） |
|---|---|---|
| **PS-1 DRIVE `_apply_actions_batch:1697`（本丸）** | 1 | **arm POSITION-servo 化（(d) M-1/M-2 継承）**: ①arm actuator 配線（proto `joint_target_mode=POSITION`+ke/kd+effort cap、imported-actuator は (d) B1-strip 同処理〔grip の ur5e MJCF も同 12 本 import〕）②毎 physics step `ctrl[arm] := jq_interp[arm]`（FK に食わせていた同 interp target）→ SolverMuJoCo が arm body を forward dynamics で pose ③`eval_fk_batched`(drive 用)+`phys_bq[非finger]=batch_bq`+`body_q.assign` を**削除**、body は joint から従属。gains/cap/cadence = (d) vendor 値継承・**tracking-lag も (d) と同性質**（grip task が lag 許容するか = 再検証 gate）。⚠ impl 註: `_physics_step_all(…, fk_batch_bq=batch_bq)` の fk_batch 受渡（finger contact ref 等）は body 駆動除去で調整要 = owner 判断 |
| **PS-2 RESET `_reset_worlds:909/910`** | 2 | joint-seed + `mj_forward`（reset で arm joint_q を seed → body 従属導出、robot body_q 書かない。(d) §14.2 D-② 同型） |
| **PS-3 P0 `_build_p0_clamp:406`/`_build_p0_unclamp:451-530`** | 8 | robot 行 → joint-seed + `mj_forward`。**cable 行 → CABLE-SEED marked+loud**（object episode-boundary init のみ・pN guard-rail: robot/finger body write へ拡張不可） |
| **PS-4 cache `_load_and_restore_cache:623/624`** | 2 | joint-seed class（cache が body_q 保存なら joint_q 保存へ migrate、restore 後 `mj_forward`。robot body_q 書かない） |
| **PS-5 sanitize `_sanitise_body_state:712/713`** | 2 | **read-only 優先**（validity check なら書込なし）。補正が要るなら joint-seed + `mj_forward` 経由（直接 body_q 書込禁止） |

**finger（コ）= 物理維持・§0#4 LOCKED 不触**: finger は既に `_finger_set` 除外 = 物理。**cage-hold = 物理接触**（§14.10「retention = 物理 clip contact」の finger form-closure 版）。finger は POSITION servo であるべき（route env gripper servo mirror）— 現状 servo 未配線なら配線も migration に含む。**finger geometry は §0#4 human-LOCKED ゆえ一切変更しない**（servo 化は駆動方式であって geometry でない）。cable = 物理 object（contact + CABLE-SEED のみ）。

**⛔ 再検証 gate（grip = banked WORKING node）**: 本 migration は grip env の banked grasp 結果（S-2 friction / SRG cage-hold 等）を actuator drive 下で**再検証必須**（arm lag で grasp が form するか）。= (d) の P-D1 相当 probe（arm PD tracking + grasp formation under lag）+ **video leg**（Rs human-GT、⭐**常にアーム+ハンド表示**〔Rs 標準〕）。migration は grip env 挙動を変え得るゆえ、grip node 自身の gate（Rs sign-off）を通す。

**invariant 保存**: §0#1 dual-arm（IK left/right・JOINTS_PER_ARM×2 = 不変）/ §0#3 IK-only（IK target 層 kept、realization のみ physics 化）/ §0#4 コ geometry LOCKED（finger 不触）/ §0#5 no-kinematic-trick（body_q 強制配置の除去 = 本 migration の目的）。触れる分岐が出たら STOP+Rs。

**c6 design-correctness 確認**: disarm→raise（route env `:2043`）= `if fired:`（pin eq 検出集合）内 scope ゆえ **6 structural cable eq に false-positive しない** ✓（fired = pin eq のみ）。SINK-3 CPU eq writer=0 に concur。⚠ device(mjw)+proto eq は guard v3(O-1) 継続。

**次**: %12/grip owner が PS-1..5 を impl（HALT fence 内）→ grip P-D1-analog + video で再検証 → pN verify。私 = grip migration の設計軸 verify（two-key）で復帰。

### §14.16 scripts/ 115-site disposition + RULE 拡張（v2.7、18:06 — %12 guard v3 census `158 = envs 43 + scripts 115` の disposition ask(ii) への裁定。§14.14 RULE に 2 class 追加）

**census 実測（%12 c7 guard v3 AST、review §11）**: SINK-2 = 158 = envs 43（grip 38 + skill reset 5）+ **scripts 115**（build_unclamp 8 / demo_aerial 5 / mppi demo gen 36 / newton_routing_utils 7 / **scripted harness test_newton_* 42** / diag+dry_run 5 + unparseable 1）。⭐AST receiver 解析が .assign-only view（私の ~17）の全 surface を捕捉 = sink-completeness 規律の成果。

**§14.14 RULE 拡張（2 class 追加、既存 DRIVE/RESET/CABLE-SEED/FK-SCRATCH に）**:
- **OFFLINE-REPLAY class（認可例外・要 pN/Rs confirm）**: 制御ループ**外**の事後可視化（replay/render で recorded state を camera 用に re-pose）= `CLAUDE.md:67` の既存認可例外。**削除不可・PRESERVE（marked+loud「visualization-only, NOT a physics claim」）**。⭐**根拠 = Rs 要件の含意**: Rs は video leg（常にアーム+ハンド表示）を要求 ∧ 完全削除を要求 → **replay 生存なしに video 生成不可** ⇒ 両者両立には offline-replay の生存が必然（tension でなく Rs 自身の要件から導出）。⚠ Rs directive が pin 例外すら supersede した先例ゆえ、本 class の最終 sanction は **pN/Rs confirm を要求**（p5 は coherence 根拠 + 分類を提供、単独 sanction せず）。**注**: 新 regime では recording 自体が physics(actuator) 生成ゆえ replay の re-pose は physics-generated state の忠実 re-display（新規 kinematic 挙動生成でない）。
- **DISCARDED-TRACK class（entry-raise + evidence 保存）**: env6-VBD DISCARDED track の legacy（mppi demo gen / demo_aerial / build_unclamp 等の VBD-era）= active skill path でない。**disposition = entry-raise**（削除でなく）。根拠 = Rs directive 逐語「歴史 artifact は evidence として保存するが実行候補から除外」を正確に執行（entry-raise = file 保存〔evidence〕+ 実行時 fail-loud〔execution 除外〕）。⚠ **TK-2（authorize dead-body = delete）との差 = 所有権 context**: TK-2 は live entry-raise 下の redundant dead-body を p4 own env で削除。ここは**他 owner の whole-file**（p4 lane 前から存在）ゆえ entry-raise が安全（file 保存 + owner が delete を選択可）。owner declaration 必須。

**scripts disposition 裁定（ask ii）**:
1. ⛔**SUPERSEDED（訂正 #15 = §14.24(1)、2026-07-20）— `routing_utils 7` の分類は誤りだった。**以下は原文保存（provenance）であり **`routing_utils` については無効**: ~~VBD-track legacy（mppi 36 / demo_aerial 5 / build_unclamp 8 / routing_utils 7 等）→ DISCARDED-TRACK class = entry-raise~~。**正**: `newton_routing_utils` は **active B0/B1 evaluator（`policy_route_runner.py:480`）の共有 realization** ⇒ **DRIVE / PHYSICS_REWRITE**（§14.24(1)）。さらに **§14.24-c(5) で file/track-level DISCARDED は HOLD・非承認**。⚠ `entry-raise` 方式自体も **§14.16-R で pN NON-CONCUR により撤回済**（正 = DELETE + git evidence）。他項目（mppi / demo_aerial / build_unclamp）は本 supersession の対象外。
2. **scripted harness test_newton_* 42** → **test-disposition**（TK-2 の pin-test retire と同型）: 削除される機構（kinematic drive）を test する harness = **retire**（provenance header + git evidence）/ physics 置換を test すべきものは **migrate**。test owner declares。**⛔ 認可 gate（Fingertip Z-Check 等 CLAUDE.md 記載の verification harness）を無検証削除しない** — 機構 retire と verification-role を区別。
3. **offline replay/render（もし 115 に含まれれば）** → OFFLINE-REPLAY class = **PRESERVE**（pN/Rs confirm）。⚠ p4 census は 115 を上記 3 分類で tag し直すこと（VBD-legacy / test-harness / offline-replay の混在ゆえ blanket 削除・blanket raise とも不可）。
4. **unparseable 1** → guard v3 が UNPARSEABLE FAIL entry 化済（c7b）= crash でなく loud、正しい。

**判定式（p4 census 用、§14.14 に追記）**: 各 SINK-2 site に →「active skill path の runtime robot/finger body drive か?」yes=DRIVE(削除・actuator 化) / 「reset/P0/cache の robot body seed か?」yes=RESET(joint-seed+forward) / 「cable object init か?」yes=CABLE-SEED(marked) / 「制御ループ外の replay/render か?」yes=**OFFLINE-REPLAY(preserve, pN/Rs confirm)** / 「DISCARDED-track legacy か?」yes=**DISCARDED-TRACK(entry-raise, owner declares)** / 「fk_state scratch か?」yes=legit。

**PS-1 impl consult standby**: `_physics_step_all(…, fk_batch_bq=…)` 受渡調整の設計照会 = 着手時に対応（§14.15 impl 註）。

### §14.17 grip PS-1 impl consult 裁定（v2.8、18:19 — %12 3 問 + pN 18:17 reconcile 統合）
- **Q1 fk_batch_bq = %12 読み CONCUR（§14.15 精緻化）**: `eval_fk_batched` は**存続**（finger-spring TARGET 供給 = FK scratch 計算・state teleport なし）。⭐p5 on-disk 確認: `_apply_finger_spring:660` は `body_f`（**力**）を `fk_batch_bq[w,finger]` 目標へ加算 = physics spring（force-based actuator・body_q teleport でない・SINK-2 非対象・compliant）。**削除は arm 行 `phys_bq[非finger]=batch_bq`+`body_q.assign`（:1691-1697）のみ**。§14.15「eval_fk_batched 削除」を「arm-drive 用途のみ削除・finger-target 用途存続」に訂正。
- **Q2 arm interp = 毎-frame interp 採択（route env parity）**: 現 `jq_interp` は finger 列のみ interp（arm 列 = old_fk_jq 定数 = RL-step 階段）。servo 化で **arm 列も per-physics-frame interp**（jq_interp を arm 列へ拡張）→ `ctrl[arm]:=jq_interp[arm]` 毎 frame。根拠: (i) route env FF path parity（reuse-first）(ii) 毎 frame の ω が小さく (kd/ke)·ω lag 減（(d) RESULT 機構）(iii) 実軌道は連続補間（階段でない）= sim-is-reality。階段+PD 平滑化 = 劣後 fallback（step 入力が transient 励起）。⚠ 挙動変化ゆえ再検証 gate（§14.15）対象。
- **Q3 RESET = pN 18:17 裁定で RESOLVED（premise-block 解除）**: pN CONCUR §14.14 RESET。**reset-init 例外 = episode boundary の reset 直後 1 回に限る joint-state seed + `mj_forward`**（初期化例外・DRIVE でない）。**robot/finger body-state 直接 write は reset でも不可**（∴ PS-2..5 は body_q.assign → **joint_q seed** + mj_forward に migrate、body 書かない）。episode 中の homing/recovery = DRIVE = actuator のみ。pN が旧「reset も actuator・例外 0」の広い表現を本 1-回-init について撤回・kinematic-drive 例外 0 は維持。**guard-manifest 要**: exact function/callsite + before-first-step + once + no body write + joint-state-only。⇒ **PS-2..5 UNBLOCK**（joint-seed 方式で c9 以降実装可）。

### §14.16-R pN reconcile（18:17）で §14.16 の 2 class を精密化（v2.8、pN scope authority に CONCUR）
- **OFFLINE class = NARROW to joint-state のみ**: `CLAUDE.md:67` 例外は `write_joint_state_to_sim`（**joint-state**）の制御ループ外事後可視化に限定。`:72` の **body_q/mocap/eq_active（body-state 直接駆動）は「offline」名目でも不可**。⇒ **SINK-2（body-state）の 115 script sites は OFFLINE-REPLAY carve-out 不適用**。video 生成 = **joint-state offline replay**（joint_q 書込 → `mj_forward` で render・非 solver-step・非 training・非 physical-verdict の typed exception）**or physics 再sim** で行う（body_q teleport でなく）— Rs video 要件は joint-state 経路で満たす（coherence 保持）。
- **DISCARDED-TRACK class = pN NON-CONCUR で撤回 → DELETE 方式**: 「entry-raise で旧 body writer を active .py に残す」= pN NON-CONCUR。正 disposition = **証拠 = git SHA 保存 / active writer body = DELETE / 必要 script = PHYSICS_REWRITE / owner 不明 = BLOCKED_OWNER（RED 維持）**。TK-2（delete）と uniform 化（私の「他 owner ゆえ entry-raise」= pN が overrule、delete + git evidence が正）。
- **§14.16 判定式 更新**: 各 SINK-2 site → active runtime robot/finger body drive=DRIVE(削除・actuator) / reset robot body seed=**RESET(joint_q seed+mj_forward・body 書かない・guard-manifest)** / cable object init=CABLE-SEED(marked) / **制御ループ外 replay = joint-state なら typed OFFLINE 可・body-state は不可(PHYSICS_REWRITE/DELETE)** / **DISCARDED-track = DELETE body+git evidence（entry-raise でない）/ 必要なら PHYSICS_REWRITE / owner 不明=BLOCKED_OWNER** / fk_state=legit。

### §14.18 grip PS-1 two-key（設計軸）= PASS（v2.9、18:41 — tip c10 `2ad2492f94`、sink + flag-分岐 直読）
**方法**: sink（`.body_q.assign`）+ 新 DRIVE loop の flag 分岐を on-disk 直読（narrative 非依存・前 arc の 2 盲点回避）。
- ✅ **DRIVE arm body write 消滅**: grip `.body_q/qd.assign` = 15→**14**（`:1697` DRIVE 消滅・残 14 は全 <1000 = PS-2..5 群 reset/P0/cache/sanitize）。AST census 38→36（%12）と整合。
- ✅ **置換 = ctrl servo（Q2 full-row lerp）**: DRIVE loop（`:1721-1745`）= full 行を per-frame lerp（arm 列込・Q2）→ `if self._arm_pd_drive: joint_target_pos.assign`（qd-indexed・per-arm 列 0-5）。arm body write なし。
- ✅ **flag-OFF = fail-closed RAISE**（`:1743` 「kinematic arm drive REMOVED」）= **旧 kinematic path 完全削除・fork でない**（flag-off で旧 body write に落ちない）。「default byte-identical」= builder model のみ（servo は flag-on でのみ配線）。
- ✅ **Q1 eval_fk_batched 存続**（`:1730` finger-spring TARGET 供給・`_apply_finger_spring:703` は `body_f`【力】= physics・SINK-2 非対象）。
- ✅ **nu==12 B1-strip census**（grip `:400` assert nu==12 ∧ arm-mapped==12 / skill_base `:1653-1684` 共有配線 assert）。builder arm-PD block は grasp_actuation gate 外へ hoist（flag-off で byte-identical model）。
- ✅ **invariant**: finger 物理維持（§0#4 finger-spring 不触）/ dual-arm（両腕 0-5 列）/ IK-only（IK target 層不変）/ no-kinematic-trick（arm body write 除去）。
- **⛔ PS-1 が establish しないもの（loud）**: (i) **grasp-under-PD-lag 再検証未**（§14.15 gate = grip P-D1-analog probe + video〔アーム+ハンド〕、HALT fence 内・run leg）— design conformance PASS だが banked grasp 結果は PD drive 下 UNVERIFIED (ii) **PS-2..5 未**（残 14 body_q sink = reset/P0/cache/sanitize、joint-seed migration 次 chunk）(iii) flag 除去（PD 無条件化）= 再検証後の later step。
- **verdict**: grip PS-1 **設計軸 two-key = PASS**（削除 clean・置換 Q1/Q2 準拠・fail-closed・census/invariant 健全）。今回は sink 規律 + flag 分岐直読で **blind spot なしの clean verify**（arc 前半の 2 盲点の教訓が効いた）。evidence 軸（Layer8 v3 / grasp probe）= pN。

### §14.19 grip PS-2..5 two-key（設計軸）= PASS + PS-5 sanitize 裁定（v2.10、19:19 — tip c11 `19555e128a`、3-sink airtight）
**two-key（sink 直読・alias-immune）**:
- ✅ **3-sink 全 clean @ c11 grip**: body_q/qd.assign = **0**（全 robot body 書込消滅）/ raw qpos/qvel + eq_active 書込 = **0** / joint_q.assign = **単一 sanctioned seed + fk_state 3**。⇒ **grip kinematic 36→0 を sink で確定**。
- ✅ **単一 sanctioned 点 = `_seed_robot_joint_row:849`**（docstring「the SINGLE sanctioned joint-state write site, pN 18:17 ruling」）: **joint-state のみ書込 + servo target seed + `eval_fk`（body は joint 従属導出）**、caller 4（p0-clamp:448 / p0-unclamp:490 / cache-restore:622 / reset:898）= 全 episode 境界・before-first-step。**pN 18:17 RESET-SEED manifest（joint-only/once/no-body/boundary）完全準拠**。
- ✅ **cable = CABLE-SEED 準拠**（`_seed_cable_from_snapshot`: settled snapshot〔read-only〕から cable JOINT coords 導出→`seed_cable_joint_state`、body 書込なし・cable-only）。pN guard-rail 満たす。
- ✅ **PS-5 sanitize = detect-only**（settled-state RESTORE 削除〔旧 body 補正書込 = 除去〕→ body_q read-only 検査、非有限/|pos|>5.0m で fault）。
- ⚠ 註（%12）: VBD Z-clamp settle 削除（unclamp P0 物理成立性 = run leg へ fence）/ cache v10_ps2（旧 = kinematic 系譜ゆえ invalidate、正）。
- **verdict**: grip PS-2..5 **設計軸 two-key = PASS**（3-sink clean・seed manifest 準拠・cable/sanitize 準拠）。**grip env 全体 = kinematic-FAIL 0（設計軸）**。⛔ run-leg（grasp-under-PD-lag 再検証・unclamp P0 物理成立性）= fenced。evidence 軸（Layer8 v3 / grasp probe）= pN。

**PS-5 sanitize 恒久形 裁定（A vs B、DESIGN-GATE 判定）**:
- **裁定 = A（raise）を現 phase で維持・B は training-readiness で DESIGN-GATE 経由**（B を今 wire しない）。
- 根拠: **A（fail-closed raise）= removal-verification + grasp probe phase に正**（surviving kinematic writer / 物理不安定 / instability を loud 検出・reward 不変・silent mask なし。probe の instability は raise で loud に出すべき）。**B（route-env explosion 終端 + PPO mask）= training phase の正形だが reward/dones 変更 = DESIGN-GATE**（`/reward-design` + `/pre-check` 必須）。⛔ **B 実装時の必須制約**: physics-fault = `dones` に入れる が **⛔`time_outs` に入れない**（prohibited.md: value_loss 105× 爆発の実績 — timeout は value bootstrap trigger、terminal explosion に bootstrap 禁止）+ route env `EXPLOSION_DIST_THRESH` invalid-episode parity に統一（閾値 5.0m は暫定・B 設計時に route env 1.0m 系メトリクスと reconcile）+ grip 既存 explosion/drop 処理と unify。
- **⇒ 現状の暫定 raise は正しい**（removal + probe を serve）。B は grip が multi-episode training に近づく gate で `/reward-design` を通す（premature reward-semantics 変更を避ける）。training-readiness まで A 維持。

### §14.20 c13 two-key（skill 共有 5 sites reset body-restore 削除）= SPLIT: 5-site 削除 = 設計軸 PASS / "envs kinematic-clean" milestone = HOLD（v2.11、2026-07-19 22:31 JST — tip c13 `e65c842bec`、committed-blob 検証〔git show/grep、worktree clean〕・sink census = delivery-surface alias-immune。bank sha = %12 fill）
**方法**: 前 arc の 3 盲点（R1 alias / pN B1 独立 writer / pN B2 body sink）を踏まえ、`e65c842bec` の committed blob に対し **3 sink を delivery surface で網羅列挙分類**（source 変数名でなく `.assign` 着弾点）。narrative（DEFER_RECON `5b600369.../c13_...md`）非依存・code が権威。

**PART-1 = c13 宣言スコープ（skill 共有 5 sites の削除）= ✅ 設計軸 PASS**
- **削除確認（committed diff `f88fe6ea04..e65c842bec`、5 files +26/-130）**: `restore_world_body_state` + `assign_world_states_to_sim`（`newton_skill_env_base.py`）= 機構ごと DELETE / route・approach `_reset_worlds` の両 caller + bq/bqd/prev 読取 + import = 除去 / orchestrator・snapshot の xref = **docstring のみ**（`:func:` dangling 回避・code neutral）。
- **§14.2 conformant**: 「reset-init body-restore 例外 = 失効 → 物理過程化」を実行。reset は joint-space（CABLE-SEED joint-seed + whole-model `eval_fk`、body は joint 従属）で carry。⚠ §14.2 の transit（step 2/5）は**未実装だが正しく fence**（route reset は §14.3 pose-gate fail-closed = 恒 raise until transit・approach reset は無条件 raise）— c13 = 削除レグ、transit = §14.3 別 chunk。
- **§14.14 RESET rule conformant**: `assign_world_states_to_sim` の robot/finger reset-init body 書込 = 除去、joint-seed + `eval_fk`・body 書込ゼロ。**CABLE-SEED guard-rail 健全**: 残 CABLE-SEED（`newton_skill_env_base.py:1059/1060`）= marked+loud ∧ **NO-KINEMATIC containment assert（`:1046-1051`、cable_joints[0] が FREE root〔7q/6qd〕でなければ refuse = arm caller が exempt 書込に到達不能）** → §14.14(iv) の「exemption を arm caller が継承不可」を機構で満たす。
- **⭐redundancy = behavior-preserving（VERIFIED、削除の設計軸核心）**: `seed_cable_joint_state`（`:1061`）末尾に `newton.eval_fk(model, state.joint_q, state.joint_qd, state)` = **whole-model FK**（body_q ∧ body_qd を joint_q/qd から再導出）。route reset の唯一の live `_state_0.body_q` 読取（`:1235` `_compute_target_seg_indices`）は**この eval_fk（`:1233`）の後**。それ以前の読取は全て cache（`_settled_body_q`/`_settled_fk_jq`）or joint_q（pose-gate、read-only）で **live body_q 読取ゼロ**。⇒ 削除した body-restore は **reachable route path で eval_fk に上書き（冗長）**・approach path は raise が先で dead-effect。**新規 sink 導入なし**。
- **verdict**: c13 の 5-site 削除 = **設計軸 two-key PASS**（§14.2/§14.14 準拠・redundancy 保存・CABLE-SEED guard-rail 健全）。

**PART-2 = "envs kinematic-write CLEAN / envs FAIL=0（grip∧skill 全 clean）" milestone = ⛔ 設計軸 HOLD**
- ⚠ **残存 SINK-2 body-state writer（interprocedural-helper alias）**: `chain_runtime_state.import_chain_state_into_env`（`:259`）が `_assign_array(getattr(state_0,"body_q",None), state.body_q)`（`:278`）/ `body_qd`（`:280`）/ `solver.body_q_prev`（`:286`）で **live sim body-state を書く**（helper `_assign_array:93` の `target.assign(value)` に着弾）。名前 scope の `.body_q.assign` grep は素通り、guard も当該 file を rglob 走査するが **0 hit**（sink が helper 内・body_q binding が call site = 関数境界を跨ぐ interprocedural alias、pN G2〔attr-store/copyto/AnnAssign〕を超える NEW class・dataflow 非認識）。
- **reachability**: approach env の public API（`import_chain_state:1203-1205`、`target_skill="AC"`）+ `newton_chain_context_facade.py` が参照。**現 runtime caller = 0（latent）**だが active envs/ tree 内・API 到達可能。mujoco path で invoke されれば body_q+body_qd の 2 書込。guard（`check_control_method.py`）は当該 file を rglob 走査済だが **interprocedural dataflow を認識せず 0 hit**（「未走査」でない・dataflow-blind な census gap、pN 22:36 on-disk 訂正 fold）。
- **判定**: §14.14 round-2 の removal 標準「3-sink（joint ∪ body ∪ eq）全 clean」+ Rs complete-removal「実行候補から除外」+ pN「entry-raise 単独で旧 writer body を active tree 残置 = NON-CONCUR」（a fortiori、fence すら無い latent writer）に照らし、**「envs kinematic-clean」は成立しない**。5-site 削除は正しいが milestone claim が過大。
- **fix への設計 input**: skill-chain state handoff の **body-state RESTORE（body_q を保存 config へ teleport）は complete-removal 下で禁止**（kinematic placement・§14.14 DRIVE/RESET とも body_q 書込禁止）。handoff が live 要件なら **joint-space（joint_q export/import + `eval_fk`、CABLE-SEED/RESET-SEED 同型）**で実現・body_q 書込不可。caller ゼロゆえ **DELETE 有力**（git history = evidence、§14.2/§14.10「code 保存 = history」）。owner disposition（§14.16 DELETE / PHYSICS_REWRITE / BLOCKED_OWNER）= p4 + pN。
- **evidence 軸 input（pN）**: guard-hardening — interprocedural-helper alias（`getattr(state,"body_q").assign` を helper param 経由）を検出（dataflow or helper-param taint）。⚠ adjacent: `skills/snapshot.py` restore（envs scope 外だが同 pattern の可能性）を completeness で flag。

**scope 註（fair-signal）**: c13 の incremental 削除は correct で**満額 credit**。PART-2 finding は **c13 が触れていない pre-existing residual**（chain_runtime_state は c13 diff 対象外）で、milestone が census-completeness を見落としたもの — 5-site work の瑕疵ではない。run-leg（物理 settle）= fenced（HALT）・設計軸 verdict と独立。

- **verdict 総括**: c13 **5-site 削除 = 設計軸 PASS** / **"envs kinematic-clean" milestone = 設計軸 HOLD**（1 residual SINK-2 alias writer の disposition 要）。evidence 軸（Layer8 v3 実走行 / guard interprocedural-alias 硬化 / H-bundle）= pN。
- ⭐**§14.20 two-key CLOSE（2026-07-19 22:39 JST、pN evidence-axis readback CONCUR）**: 設計軸(p5)+証拠軸(pN)が exact `e65c842bec` 独立確認で一致 — (i) 5-site 削除 = PASS (ii) "envs kinematic-clean" milestone = HOLD (iii) alias BODY sink = **3**（body_q/body_qd/body_q_prev、`:278/280/286`）+ allowed FK joint_q 1（`:290`）を分離 (iv) guard `check_source(chain_runtime_state)` = rglob 走査済 / **0 hit**（interprocedural dataflow 非認識 = census gap、「未走査」でない — pN 訂正 fold 済）。**gate 分離（pN）**: guard hardening + pre-fix census = **guard-only OPEN → p4** / env writer disposition + source edit = **別 gate（HALT 下 CLOSED、landing で処理）**。**post-fix 期待 census（pN 22:38）= Layer8 128 = envs 3〔chain_runtime_state alias body_q/qd/prev〕+ scripts 125**（現「envs 0」= guard-blind 値、post-fix は envs 3 を主張）。⇒ c13 two-key（設計軸∧証拠軸）= **CLOSED**、残 open = guard 硬化レグ（設計 open でない）。

### §14.21 c14 F1 guard hardening（G6 interprocedural helper-param taint）= 設計軸 PASS（v2.12、2026-07-19 23:03 JST — tip c14 `edd0c33ecd`〔parent = c13 `e65c842bec`〕、committed-blob 直読 + guard 実行 corroboration。§14.20 が残した「guard 硬化レグ」を CLOSE）
**方法**: c14 は guard-file 単独 diff（`scripts/validations/check_control_method.py` +153/-3、env writer 非 touch = pN gate 分離に整合）。committed blob を read + worktree（clean @ c14）で guard 実行。
**pN spec 3 criteria 検証（source + 実行）**:
- ✅ **helper-name allowlist なし**: `_sink_param_indices` = **computed dataflow fixpoint**（within-file・2-hop・bounded 8-pass）。各 func の sink-param 位置を _direct_param_sinks（`.assign`/`.fill_`/`copyto`/`copy`/subscript-store）+ forward 伝播で算出、**empty summary は drop**（非-sink helper 名は callsite taint を起こさない）。名前 list でない（docstring 明記）。
- ✅ **FK = original receiver で exempt**: G6 callsite taint（`:321-344`）は arg を `_resolve_recv_attr`（getattr-literal / static-attr / 1-level local-alias）で **original receiver へ解決** → `_has_fk_token(recv_toks)`（`FK_TOKENS={fk_state,_fk_state}` **exact-token**）で exempt。helper 名/param でない（コメント「never the helper」）。pos control `fk-getattr`/`fk-attr` 非発火・neg control `wrong-receiver`（`not_fk_state`）発火 = substring-spoof 耐性。
- ✅ **BODY exception 0** ⚠**（c15 訂正: c14 では behavioral 止まり・structural 不完全）**: `BODY_ASSIGN_ATTRS={body_q,body_qd,body_q_prev}`。⚠ c14 の FK exemption は attr 分類の**前**に blanket 適用ゆえ `fk_state.body_q` は素通り得た（「body に FK receiver 付く real write なし」= behavioral 仮定依存・structural でない）。pN C1 摘発 → **c15/§14.22 で全 6 面 attr-sensitive 化し structural に充足**。
- ✅ **self-test = fail-closed + 識別的**: `main()` は census 前に `self_test()`、NEG must-fire / POS must-not-fire / marker-spoof / fixture-injection、fail 時 `LAYER8_FAIL=1` で certify 拒否。実行 = **「all controls behave（26 neg / 9 pos / spoof / injection）」PASS**。
**validated-after-fix（実行 corroboration、[[feedback-a-gate-validated-under-the-bug-is-validated-by-the-bug-2026-07-15]]）**: guard @ c14 が c13 の finding を的確に捕捉 — `chain_runtime_state.py:278/280/286 = BODY-ALIAS`（original receiver `<state_0>.body_q` / `<state_0>.body_qd` / `<solver>.body_q_prev`）、**envs FAIL 0→3**、**LAYER8_FAIL=128 = pN 予測値 exact**（envs 3 + scripts 125）。sanctioned carry は正しく exempt（非-FAIL）: grip RESET-SEED `:872/873` `[RESET-SEED]`・CABLE-SEED `:1059/1060` `[CARRY]`。FK false-positive なし。
**⚠ 正直な coverage 境界（設計 completeness 註・no-silent-cap）**: G6 = **within-file** 2-hop。**cross-file** buffer-param helper alias（sink-param helper を別 module から import し getattr-receiver で呼ぶ形）は未 cover（callsite の within-file summary に import helper が入らない）。既知 instance なし（c13 の chain_runtime_state = 同一 file 内ゆえ捕捉）。cross-file summary 伝播は将来 hardening（該当が surface した時）= blocker でない scope 註。
**c13 HOLD との関係**: c14 は c13 milestone HOLD の **guard-blindness 半分を解消**（guard が envs=3 を正直に報告・旧 envs=0 は guard-blind 値だった）。**writer-disposition 半分**（3 chain_runtime_state writer の削除/移行）= 別 gate・HALT 下 CLOSED（landing で処理）継続。
**verdict**: c14 F1 guard hardening = **設計軸 two-key PASS**（pN spec 3 criteria + self-test fail-closed + validated-after-fix、envs 3 catch・carry exempt）。evidence 軸（repo census 権威判定 / scripts 125 disposition / cross-file 境界の実在確認）= pN。

### §14.22 c15 FK-exemption attr-sensitivity fix（pN C1 close）= 設計軸 PASS（v2.13、2026-07-19 23:28 JST — tip c15 `6ccc09b3e6`〔parent = c14 `edd0c33ecd`〕、committed-diff 直読 + guard 実行）
**背景（honest・私の c14 過小検証）**: pN C1 = c14 の FK exemption 過剰適用。c14 は `_has_fk_token` を **attr 分類の前に blanket 適用**ゆえ `fk_state.body_q` が exempt され得た（全 6 面）。私の c14「BODY exception 0 ✓」は **behavioral（real fk-body write 皆無）止まりで structural 不完全** = 過小検証（§14.21 に caveat fold 済）。pN C1 が摘発 = **two-key 機能**（証拠軸が設計軸の構造欠を捕捉）。
**fix 検証（BODY exception 0 = structural 充足）**:
- `_fk_exempt(attr, tokens) = attr in JQ_ASSIGN_ATTRS and _has_fk_token(tokens)` = FK 免除を **joint_q/qd 限定**（FK input のみ）。
- **全 6 面適用（diff 直読・partial-fix hole なし）**: (1) host-copy alias `.numpy()` bind `:209` → `_fk_exempt` (2) attr-store `:275` → `_fk_exempt` (3) direct `.assign` BODY branch `:316` → fk-check 除去（BODY 常に hit）・JQ branch は `_has_fk_token` 保持 (4) `wp.copy` `:326` → `_fk_exempt` (5) `np.copyto` `:333` → `_fk_exempt` (6) G6 helper `:349` → blanket `continue` 除去（BODY/RAW 常に hit・JQ のみ fk-exempt）。⇒ **BODY/RAW は全面で fk-exempt 0**。
- **self-test（fail-closed）+ 5 新 FK-body must-fire neg**。実行 = **「all controls behave（31 neg / 9 pos / spoof / injection）」PASS**（5 新 neg 全 fire・joint pos 免除保持）。
- **false-positive-free（実行 census）**: envs **3 不変**（chain_runtime_state のみ）・新 `fk_state.body_q` hit **皆無** = legit fk-body write 不在ゆえ tightening は real code に無害。`LAYER8_FAIL=128` stable・carry（RESET-SEED/CABLE-SEED）免除保持。
**設計整合（§14.14）**: FK-SCRATCH 免除の**精緻化**であって premise change でない。§14.14「fk_state.* = legit（scratch・stepped state でない）」の intent は不変、但し guard 免除は **joint（FK input）に限定**し body/raw は「BODY exception 0」に服させる。`fk_state.body_q` は legit pattern 皆無（body は `eval_fk` 導出）ゆえ設計 conflict なし。
**⚠ self-test coverage 註（minor）**: 5 新 neg は 5 面（direct/attr-store/wp/np/G6）を cover。surface 1（host-copy alias = `fk_state.body_q.numpy()`+subscript SOURCE）は専用 must-fire control 未追加 — code fix は適用済（`_fk_exempt`）だが self-test 未 cover（5/6）。blocker でない・completeness 註（pN evidence 軸で control 追加要否）。
**verdict**: c15 = **設計軸 two-key PASS**。BODY exception 0 = **structural 充足（全 6 面）**・pN C1 CLOSE。⇒ **§14.20/§14.21/§14.22 で guard 硬化 arc（helper-param taint + attr-sensitive FK 免除）= 設計軸 CLOSED**。evidence 軸（census 権威 / 31-neg self-test / surface-1 control）= pN。

### §14.23 c17 F2 two-key（設計軸）= **SPLIT: F2 removal = PASS / "envs kinematic-clean" = HOLD 継続 + instrument 欠陥 3 件（F3 / F3-b / F4）**（v2.14、2026-07-20 09:2x JST — tip c17 `3117bbd21c`〔parent = c16 `3e9b973144`〕。**fresh detached worktree @ c17 で committed-blob 直読 + guard 独立実行**〔narrative 非依存・shared dirty tree で検証しない = [[feedback-pin-over-committed-state-not-dirty-tree-verify-in-worktree-2026-07-19]]〕）

**対象** = `thread_isaac_lab/envs/chain_runtime_state.py`（24 ins / 50 del、単一 file）。**素材** = `F2_CHAINSTATE_REMOVAL_EVIDENCE_RSTECHLEAD_20260720.md`（sha256 前方 `fb5b432b506f2` = p4 pin と自検証一致。⚠ **doc は uncommitted** — bank 対象に含めよ）。

**(A) F2 removal = 設計軸 PASS**（11 leg、全て c17 committed 状態で自検証）
1. producing commit = `3117bbd21cd7fad7e790d9d2ab50180817d06448`、parent = c16 ✓、`probe/pd1-arm-pd` tip、checkout clean。
2. body 削除 = 5 write 全消（`state_0.body_q` / `state_0.body_qd` / `solver.body_q_prev` / `fk_state.joint_q` / `env._per_world_fk_jq`）。
3. dead writer 無し = `_assign_array` 削除、repo-wide 残存 **code** ref 0（残 2 件は guard 自身の解説 comment `check_control_method.py:137/:343`）。
4. **delivery-surface sweep**（私の c13 miss の自適用）: 当 file 内 `.assign(` = 0 / `[...]=`・`[:]=` = 0 / `_assign_array` = 0。残る `body_q`/`body_qd` 参照は**全て read-only**（dataclass field `:29-31`/`:69-71`、shape 読み `:49-51`、finite 検証 `:127-139`）。
5. signature + return-annotation = 完全保存（`import_chain_state_into_env(env, state, *, target_skill=None, validate=True) -> ChainRuntimeRestoreReport`）。
6. **entry-raise = §14.16-R 準拠**: raise は無条件かつ `env`/`state` の read/mutation より前。`warnings.warn(DeprecationWarning)` → `raise RuntimeError` の**両分岐とも fail-closed**（`-W error` 下では warning 自体が送出）— **正常 return する path が存在しない**。
7. provenance comment = §14.12 TK-2 準拠（"last present at `3e9b973144`" + §14.10/§14.12/§14.16-R/§14.20 cite）。
8. export/validate = 無改変、docstring が migration target として明示。
9. **§14.20:499 の私の input が忠実に実装された**: body-state RESTORE 禁止 ✓（disable でなく削除）/ live なら joint-space ✓（docstring が action/joint/physics 継承を規定）/ caller0 ⇒ DELETE ✓。
10. **caller-0 前提を c17 で再検証 = 保持**: `import_chain_state_into_env` の static caller = approach 公開 API `import_chain_state`（`newton_approach_cable_mujoco_env.py:1205`）1 件のみ。その API 自体の caller = **repo-wide 0** ⇒ §14.20「runtime caller 0（latent）」成立。
11. **guard 独立実行**（自走・narrative 不採用）: `LAYER8_FAIL=125`（128→125、Δ=3）/ `LAYER8_WARN=0` / **envs FAIL = 0**（envs 残 4 行は sanctioned `[RESET-SEED]` + 宣言済 `[CARRY]` CABLE-SEED であって FAIL でない）/ scripts = 125 不変 / self-test `32 neg / 9 pos / spoof / injection` PASS / exit rc=1。

**(B) "envs kinematic-clean" milestone = HOLD 継続 — p4 の非-claim を RATIFY。** §14.20 の HOLD は解除しない。

**(C) F3 = guard scan-root 欠陥**（p4 申告 → p5 独立 CONFIRM）
`check_control_method.py:493` `roots = [thread_isaac_lab/envs, thread_isaac_lab/scripts]` — **`skills/` と `orchestrator/` を走査しない**。`skills/snapshot.py:119-128` は F2 が今削除したのと**同一 operation set**（`state_0.body_q.assign` / `state_0.body_qd.assign` / `fk_state.joint_q.assign` / `body_q_prev.assign` + `newton.eval_fk`）を live env に実行し、かつ **配線済み caller chain 有**: `orchestrator/routing_orchestrator.py:59` import → `:792` instantiate → `:1292 restore_snapshot()` → `:1308 _snapshot_mgr.restore(...)`、内部 call site `:1129`/`:1184`（retry/rollback/depth path）。⇒ ⛔**SUPERSEDED（訂正 #18 = §14.23-b(1)、2026-07-20）**: ~~F2 の対象（runtime caller 0）より重い~~ は**誤り**。`RoutingOrchestrator` は全 tree で **instantiation 0**（唯一の一致は docstring）ゆえ当該 chain は **配線済みだが dead**、F2 の対象と**同クラス**。live なのは standalone harness 2 本（`test_step_table_dryrun.py:111` / `test_newton_5clip_routing.py:350`）のみ。⚠ 上記の「配線済み caller chain 有」という記述も同 supersession の対象（chain 頂点の構築子を問わなかった誤り）。**本項の F3 裁定〔guard root 欠落〕自体は不変。**
⭐**裁定: guard root が `skills/` + `orchestrator/` を覆うまで、`Layer8=0` は "kinematic-clean" の述語として使用不可。** 現 `Layer8=0` は「envs+scripts の 2 root に限定した」言明にすぎない。

**(D) F3-b = bucket 誤帰属**（p5 新規・p4 §5 関連注記を独立確認）
`scripts/newton_routing_utils.py` は **library code が `scripts/` に誤配置**されたもので、`envs/route_executor.py:1827`/`:2061`/`:2957-2958` から import される。その `physics_state.body_q.assign(...)`（`:915`）+ 多数の `fk_state.joint_q.assign(...)` は **scripts carry bucket に計上**され、ゆえに "envs 0" を一度も乱さない。
⭐**裁定: "envs 0" は path-bucket の言明であって runtime-reachability の言明でない。** F3（root 欠落）と F3-b（bucket 誤帰属）は別機構・同一クラスの欠陥。bucket を**到達可能性**で切るか、誤配置 library を `envs/` へ移すか、いずれかが kinematic-clean 述語の前提。

**(E) F4 = facade が死んだ leg を certify**（p4 records-only 申告 → p5 独立 CONFIRM + 設計軸で格上げ）
`newton_chain_context_facade.py:37` は `"import_chain_state"` を必須 method 集合に持ち、`:57` `ready = not missing` は **名前の有無のみ**判定。approach 側は名前・signature を意図的に保存したため、`verify_env_api(...).ready` は capability 破壊の**前後で同一 `True`**。⇒ 単に情報量ゼロなのではなく、**必ず失敗する path を積極的に「ready」と認証する**。私の banked 教訓 [[feedback-a-gate-validated-under-the-bug-is-validated-by-the-bug-2026-07-15]]（in と out に同じ値を返す量 = 情報量ゼロ）の純粋形。⚠**皮肉な結合**: 削除を安全にした当の signature 保存が facade を盲目にした。
**格付け**: safety 回帰では**ない**（caller は RuntimeError で loud に落ちる = fail-closed）。**instrument 欠陥**である。⭐**裁定**: `verify_env_api` は callability を assert するか `import_chain_state` を必須集合から外すか、いずれか。pN が facade 不触を指示済ゆえ**執行は pN lane**、本項は設計軸の格付けのみ。

**(F) §14.21 への caveat fold（私の過去 ruling の evidence 減衰）**
§14.21 で私は c14 の G6 helper-param taint を「実行 corroboration = chain_runtime_state 3 BODY-ALIAS 捕捉」を根拠の一部に PASS した。F2 でその **live 実コードによる corroboration は消滅**。ただし synthetic neg-control `fk-body-helper-alias` は `_NEG_CONTROLS` に存続し c17 self-test 32/9 が PASS ⇒ **機構は依然 exercised**。⇒ **evidence の格下げであって機構の喪失ではない**。§14.21 verdict は維持、本 caveat を付す。

**(G) §14.20:505 fence の supersession = ACKNOWLEDGE。** §14.20:505 は「env writer disposition + source 編集」を landing 時の別 gate へ fence していた。pN 08:04 GO がこれを worktree 内で今 reopen。p4 が黙って進めず記録したのは正しい。本 §14.23 をもって当該 fence は superseded。

**(H) terminology guard = RATIFY。** p4 §5 の「これは *removal with name/signature retention + fail-close shim* であって AGENTS.md の意味の deprecation ではない」「**`IsaacLab の deprecation は raise してよい` という precedent として bank するな**」を**そのまま批准**（根拠も確認: AGENTS.md deprecation 規則は `source/<package>/` scope・本 symbol は `envs/__init__.py` `__all__` 非 export・shape は house pattern `route_executor.py:1683-1694` と同型）。

**(I) `skills/snapshot.py` disposition = 未裁定（materials 待ち・私の lane）**
F2 と異なり **live caller 有**ゆえ §14.16-R の DELETE は選べない（orchestrator の per-STEP rewind に物理的代替が要る）。per-STEP rewind は §14.10 の意味で kinematic placement に該当する。⚠**未確立**: `RoutingOrchestrator._run_rl_episode`（`:480/:503/:507/:516`）が rewind path（`:1129`/`:1184`）へ到達するかは**本セッションで確立していない** — 到達するなら訓練 path の §14.10 違反、しないなら scripted-only。**severity はこの 1 点に懸かる**ため call-graph materials を要求する。関連: §14.6「demo 全物理再記録」は rewind 機構の存在で**補強**される（ただし demo 記録が本 orchestrator 経由かは未確立 — 併せて materials）。

**verdict**: c17 F2 = **設計軸 two-key PASS**。ただし arc 全体は **SPLIT** — "envs kinematic-clean" は HOLD 継続、かつ **kinematic-clean 述語そのものが F3/F3-b で未成立**。⭐**帰結: B-drive の目標「Layer8=0」は現 root では誤った分母を最適化する** ⇒ root 拡張（F3）+ bucket 是正（F3-b）が `Layer8=0` に意味を与える前提。次の p5 レグ = snapshot disposition 裁定（materials 後）。

### §14.23-a c18 records-only 確認 + F3 PASS-CLOSE 受理 + **§14.23(D) 自己訂正**（v2.15、2026-07-20 09:4x JST — %12 報告 09:41 への p5 独立検証。⚠**訂正 #14**）

**(1) c18 `661da1f315` = records-only を CONFIRM** — parent = c17 ✓、diffstat 4 file **全て `eval_runs/`**（evidence doc v1.1 / disposition manifest v2.1 / acceptance runner + OUTPUT）、source 改変ゼロ。**決定的検証 = blob 同一性**: `chain_runtime_state.py` の blob が c17・c18 とも `5c67bab83fb41461147b62032c070b08e4d64c51`（%12 の主張 prefix `5c67bab8` と一致）⇒ **§14.23(A) の設計軸 PASS は c18 へそのまま持ち越す**。evidence doc v1.1 blob = `9cfed643c9bc9f10d009551d815f160be279d13a`（%12 pin と一致）。

**(2) F3 = PASS-CLOSE 受理**（pN `7803f58f17` "Expand Layer 8 guard coverage"、branch `codex/f3-layer8-scan-root`）。roots が `[envs, scripts]` → **`[repo / "thread_isaac_lab"]`（package 全体）** へ。⭐**私が §14.23(C) で求めた以上の修正** — hand-listed 列挙（drift する）でなく**単一 root**にした点が構造的に正しい。⚠**系譜 clean を自検証**: c17 は `7803f58f17` の**祖先**であり、同 commit の `chain_runtime_state.py` blob = `5c67bab83f…`（F2 削除済）⇒ 二系統に跨る推論でなく単一 tree の測定。

**(3) canonical 131→128 を p5 が独立再現（単一変数 control）** — [[feedback-confirming-measurement-is-not-root-cause-isolation-reconcile-the-control-2026-07-18]] / [[feedback-same-constant-is-not-same-measurement-surface-2026-07-18]] の自適用として、**guard 版を `7803f58f17` に固定したまま `chain_runtime_state.py` だけ pre-F2（c16 blob `b2c22f7ad3`）へ差し替える** control を実施:
- RUN 1（post-F2）= `LAYER8_FAIL=128`・self-test 33neg/10pos・rc=1
- RUN 2（pre-F2、**1 変数のみ差**）= `LAYER8_FAIL=131`・self-test 同一
- 差分 3 件は正確に F2 の除去対象（`chain_runtime_state.py:278/:280/:286` = `BODY-ALIAS: _assign_array(...)` helper-param body write in `import_chain_state_into_env`）
⇒ **Δ=3 は F2 単独に帰属する真の単一変数測定**。pN の canonical 主張を p5 が自走で CONFIRM。⭐副次: この 3 件を捕捉しているのは §14.21 で PASS した **G6 helper-param taint 機構**であり、本 control run が **live 実コードによる最後の exercise** — §14.23(F) の caveat が正確であったことの裏書き。

**(4) `skills/snapshot.py` = 3 violations を exact CONFIRM** — `:119` BODY-ASSIGN `state_0.body_q.assign` / `:120` BODY-ASSIGN `state_0.body_qd.assign` / `:128` BODY-ALIAS `<solver>.body_q_prev` local-alias。**`:121`（`fk_state.joint_q.assign`）は出力に現れない = sanctioned** ⇒ %12 報告と完全一致。

**(5) ⚠⚠ §14.23(D)/verdict の自己訂正（訂正 #14）** — 私は verdict で「root 拡張（F3）**+ bucket 是正（F3-b）**が `Layer8=0` に意味を与える前提」と書いたが、**これは 2 つの述語を混同していた**:
- **canonical（総計）述語**: `scripts/` は元から走査対象ゆえ `newton_routing_utils.py` の違反は**計上されている**（見逃しでない・bucket が違うだけ）。⇒ **F3-b は canonical 総計を阻害しない。** 阻害していたのは F3（root 欠落）**のみ**であり、それは今 CLOSED。
- **per-bucket 述語**: 「envs 0 ⇒ envs kinematic-clean」は依然 F3-b で**成立しない**（envs 駆動の library が scripts bucket に載る）。
⇒ **裁定を修正**: **F3-b は「canonical Layer8=0 の前提」から「per-bucket 主張のみを阻害する欠陥」へ格下げ**。⭐**帰結: §14.23 verdict の「B-drive 目標『Layer8=0』は現 root では誤った分母を最適化する」という私の異議は、F3 修正により DISCHARGED。canonical 128 を分母とする B-drive は健全。** ただし **per-bucket の「envs kinematic-clean」は HOLD 継続**（F3-b + §14.23(I) 未裁定ゆえ）。

**(6) 私の残レグ = §14.23(I) `skills/snapshot.py` disposition（不変・materials 待ち）。** F3 CLOSE により当該 3 件は **canonical 128 に計上済** ⇒ **`Layer8=0` への経路は本 disposition を通る**。severity を決める未確立点も不変: `RoutingOrchestrator._run_rl_episode` が rewind path（`:1129`/`:1184`）へ到達するか。**call-graph materials 要求は取り下げない。**

**verdict**: c18 = **設計軸 objection なし**（records-only、blob 同一）。F3 PASS-CLOSE = **受理**。canonical 131→128 = **p5 独立 control で CONFIRM**。§14.23(D) は上記(5)の通り**自己訂正**、B-drive への私の異議は **DISCHARGED**。open = §14.23(I) のみ。

### §14.24 A-group PHYSICS_REWRITE 設計 consult 裁定（route/scripts 版 semantics）（v2.16、2026-07-20 10:0x JST — %12 照会 09:56 への p5 裁定。§14.14 で私が owner と定めた「物理置換 semantics」の route/scripts 版。対象 = 4 file / 27 sinks @ c23 `07324776ac`）

**接地（p5 独立実測 @ c23、committed blob 直読 + guard 自走）**: guard `LAYER8_FAIL=35`（sink 24 + source 11）。per-file 内訳 = **`test_newton_clip_routing.py` 17 / `newton_routing_utils.py` 7 / `demo_aerial_regrasp.py` 5 / `skills/snapshot.py` 3 / `test_grip_modes.py` 2 / `dry_run_43step.py` 1**。⇒ **%12 の A-group 内訳 17/7/2/1 = 完全一致**（残 8 = snapshot 3 + demo_aerial 5、下記(5)）。

**⭐結論（照会への直答）: 原理の拡張は不要 / ただし RULE 単独では A-group を裁けない — 4 点の設計供給が要る。**

**(0) 原理 = §14.15 がそのまま transfer（新 semantics 不要）** — 中核は「**(d) 解の継承**（reuse-first、AGENTS.md）: IK/FK target 層は §0#3 準拠で不変、**realization のみ `body_q.assign` → actuator ctrl + `mj_forward` に置換**」。A-group の機構は grip PS-1 と**同一**（FK body pose を physics state へ複写）ゆえ新原理は要らない。**%12 の precedent 主張（grip PS-1..5 = c10/c11 が同型）に CONCUR。**

**(1) ⚠⚠ 訂正 #15 — 私の §14.16 分類が誤りだった（本裁定の最重要項）**
§14.16 で私は「**VBD-track legacy**（mppi 36 / demo_aerial 5 / build_unclamp 8 / **routing_utils 7** 等）→ DISCARDED-TRACK class」と分類した。**`newton_routing_utils 7` について、これは誤りである。** on-disk 実測:
- `update_kinematic_bodies`（`:910`）は `physics_step`（`:938`）の **substep ループ内で毎 substep 呼ばれる** = DRIVE の最強形（reset でも offline でもない）
- consumer = **`policy_route_runner.py:480`（= B0/B1 BC evaluator、`B_BC_BUILD_SPEC.md §4`・LEDGER / node state.md / DQ7 build spec から参照される **active** ladder 資産）** / `test_newton_5clip_routing.py:49` / `run_demo_from_waypoints.py:47`
⇒ **VBD-discarded track ではなく active 評価スタックの共有 realization**。**正 class = DRIVE / PHYSICS_REWRITE**。**%12 の提案が正しく、私の §14.16 分類を supersede する。** 教訓 = 分類は file 名や track 名でなく **consumer の生死**で決めよ（[[feedback-verify-at-the-delivery-surface-not-the-source-variable-name-2026-07-19]] の分類版）。

**(2) RULE に無い class ① = 「同一機構の N 重複製」— 裁定: 単一 realization へ収斂**
`update_kinematic_bodies` は **4 file に独立コピー**で存在: `envs/route_executor.py:1683`（**既に無条件 raise 化済** — `:1739` の mujoco 分岐も raise ⇒ route_executor 側は移行完了）/ `scripts/newton_routing_utils.py:910`（live）/ `scripts/test_grip_modes.py:345`（`skip_bodies` 付き変種）/ `scripts/test_newton_clip_routing.py:1752`（live）。既存 RULE は「DRIVE → 削除・actuator 化」と言うのみで**置換後の realization の所有者を規定しない**。
⭐**裁定**: **物理 realization は単一箇所に収斂させ、各 file は呼ぶだけにする**（4 箇所を個別 migrate すると本件と同じ divergence が再発する。`route_executor.py` の raise 化が先例＝複製側を残さない）。`test_grip_modes.py:345` の `skip_bodies` 変種は **grip の finger 除外と同義**ゆえ §14.15 PS-1 の semantics に吸収（新 class 不要、%12 の「PS-1 servo 整合」に CONCUR）。

**(3) RULE に無い class ② = 「除去対象の機構の下で verdict を出した検証 harness」— 裁定: acceptance の設計内容を供給**
`test_newton_clip_routing.py`（17）は **`CLAUDE.md` 記載の sanctioned 検証 harness**（Fingertip Z-Check Gate）。§14.16-2 は「認可 gate を無検証削除しない・機構 retire と verification-role を区別」と述べるが、**migrate 後に何が保存されねばならないか**を定義していない。pN 条件「surviving positive-control acceptance」は形として正しい。**その設計内容を以下で供給する**:
- **(i) 陽性対照が実際に fire すること** — 既知の欠陥を注入したら FAIL する harness であること。[[feedback-a-test-that-cannot-come-out-differently-is-not-a-test-2026-07-14]] の直接適用。
- **(ii) 計器の同一性** — Z-Check の述語が **joint → FK 従属**で移行前と**同一量**を測ること。§14.4 D-④「kinematic 基線概念の廃止 = 計測方法論の置換」の執行。名前が同じでも測る面が変われば別計器（[[feedback-same-constant-is-not-same-measurement-surface-2026-07-18]]）。
- **(iii) verdict 差の帰属** — 移行前後で verdict が変わるなら、それが**物理差であって計器差でない**ことを示すこと。
- ⛔**(iv) kinematic 下で取得済の PASS は actuator 下で再取得を要する**（§14.15 の grip 再検証 gate と同型・「バグの下で緑になった gate はそのバグに検証されている」）。
- `dry_run_43step.py`（1、`set_jq`）⚠**訂正 #16 で class 差替（旧記載 = RESET、pN C1 で撤回）**: call site 実測 = `set_jq`(`:193` `joint_q.assign`+`eval_fk`) が `:197`(hold×15 frame) / `:227` / `:236` の **interp loop で毎 frame** 呼ばれ、いずれも `capture_frame()` と対・**solver step を一切伴わない**（contract `:6-11`「No cable, no physics」= pN 独立確認と一致）。⇒ RESET の *before-first-step once* に非ず。⭐**裁定 = typed OFFLINE-REPLAY（§14.16-R「制御ループ外 replay は joint-state なら typed OFFLINE 可」）**: 義務は migrate でなく **typed preserve**（marking「visualization-only, NOT a physics claim」・非 solver-step・非 training・非 physical-verdict）。**新 semantics 不要**という帰結のみ旧記載と共通。

**(4) RULE に無い class ③ = `restore_state_snapshot` は §14.23(I) と同一機構 — 裁定: 単一 disposition で裁く**
`newton_routing_utils.restore_state_snapshot`（`:1806` → `:1829` で `update_kinematic_bodies` を呼ぶ）と `skills/snapshot.py:restore`（§14.23(I)）は **同じ per-STEP rewind の 2 実装**。別々に裁くと片方が残る。⇒ **両者を単一 disposition に束ねる。** 私の §14.23(I) の未確立点（**rewind が訓練 path に載るか** = `RoutingOrchestrator._run_rl_episode` が `:1129`/`:1184` に到達するか）は **A-group にも同じく懸かる** ⇒ **call-graph materials は両者共通の前提**であり、本裁定でも取り下げない。

**(5) sequencing / 衝突 / coverage**
- ⭐**#18 との衝突は無い**: `route_executor.py` は既に両分岐 raise 済であり、#18 の fix surface は `newton_route_env.py` の ik_chord（`:1235`/`:1253-1254`、seed `:1173`/`:1246`）= **別 file**。A-group は `scripts/` 側の複製ゆえ #18 の surface に触れない。
- ⚠⚠**訂正 #17 で全面差替（旧記載「R-SEQ は生きている」= 撤回、pN C2 で指摘）**: 本 charter **自身の TOP PREMISE `:3`** が逐語で「**§6 R-SEQ（#18-first-on-kinematic）… = 全て SUPERSEDED（rework 対象）**」と述べ、**§14.9 は「…(4) production 削除 landing →(5) W-b 再記録 →(6) #18 PD 再測」= A-first / #18-last** を既に規定している。⇒ **#18-first は生存していない。** ⭐**pN sequencing 裁定に CONCUR = A-first**（A land 後、affected B0/B1 artifacts = **HISTORICAL / NOT_COMPARABLE** → **fresh 再取得** → **#18 は compliant substrate 上で実装・再測**）。**NOT_COMPARABLE は source-closure 依存 artifact に限定**（blanket でない）。⚠**伝播源**: LEDGER (d) 行が supersede 済 R-SEQ 文言を保持 → supersession flag 反映を p6/%12 へ要求（本誤りの出所）。
- **`newton_routing_utils` 単独 land 不可（11 consumer と atomic）= CONCUR。**
- ⚠**coverage の穴**: guard 35 のうち **`demo_aerial_regrasp.py` 5 が本 consult に現れない**。AerialRegrasp は `CLAUDE.md` で **env6-VBD DISCARDED track** ゆえ §14.16-R の **DELETE + git evidence** が素直だが、**明示 disposition が要る**（manifest v2.2 §7 に在れば足りる — 私は同 §7 を未読ゆえ「穴」でなく**確認要求**として挙げる）。

**verdict**: 照会への答 = **(a) §14.15 の原理は route/scripts へ拡張不要**（同一機構・grip precedent 有効）⚠⚠**ただし §14.24-b 訂正 #19 で重大な限定**: 原理は transfer するが **route/scripts substrate は前提を満たさない**（robot = `is_kinematic=True`・`inv_mass=0`・`density=0.0`・actuator 配線ゼロ）⇒ 本項を「realization の置換だけで足る」と読んではならない。実体は **substrate rebuild**。/ **(b) 既存 RULE の適用だけでは不足** — 上記 (1) 訂正 #15〔routing_utils = DRIVE、私の旧分類を supersede〕/ (2) 単一 realization 収斂 / (3) harness acceptance 4 条件 / (4) snapshot 系の単一 disposition、の 4 点を本 §14.24 が供給する。`dry_run_43step.py` のみ新 semantics 不要（class = **typed OFFLINE-REPLAY**、訂正 #16）。**sequencing = A-first**（訂正 #17）。✅**旧「未解決」3 件は全て CLOSED**: §14.23(I) call-graph = c26 `3ddd22322e` 納品 + p5 独立確認 →**§14.23-b で裁定**／demo_aerial 5 = manifest v2.2 `:108` **D BLOCKED_OWNER** 裁定済（私の確認要求 取下げ）／R-SEQ = pN 裁定 A-first に CONCUR。

### §14.24-a pN evidence-axis HOLD C1-C2 への fold = **両方 CONCUR・私の 2 項を撤回**（訂正 #16 / #17）（v2.17、2026-07-20 10:1x JST — pN HOLD 10:13 への p5 on-disk 再検証。⚠ 本 arc で **3 度目**の「名前・framing で分類し call site を読まなかった」失敗）

**C1（`dry_run_43step.py` の class）= pN 正・訂正 #16。** 私は §14.24(3) 末で「43-step 表 canonical ゆえ…**既存 RESET class で足りる**」と裁定した。**誤り。** on-disk 実測（c23 blob 直読）:
```
def set_jq(jq_array):                                   # :192-194
    scene_state.joint_q.assign(jq_array); newton.eval_fk(scene_model, …)
set_jq(waypoint_jqs[0]); for _ in range(15): capture_frame()      # :197-200 hold+capture
… set_jq(jq_np); capture_frame()                                  # :227-228 interp loop 毎 frame
… set_jq(jq_interp); capture_frame()                              # :236-237 fallback interp 毎 frame
```
⇒ **once-at-reset の seed ではなく、solver step を一切伴わない毎 frame の joint-state FK→render loop**。§14.16-R の「制御ループ外 replay = **joint-state なら typed OFFLINE 可**」に該当。⭐**正 class = typed OFFLINE-REPLAY**（PRESERVE + marking「visualization-only, NOT a physics claim」・非 solver-step・非 training・非 physical-verdict）であって RESET（joint seed + `mj_forward`・guard-manifest）ではない。**義務が違う**（migrate でなく typed preserve）。
⚠**headline は survive**: 「本 file に新 semantics は不要・既存 RULE class で足りる」は成立（RESET も OFFLINE も既存 class）。**誤ったのは class 選択とそれに伴う実装義務**。
⭐**失敗の型（自認）**: 私は `set_jq` という**名前**と「43-step 表 canonical」という **framing** から分類し、**call site を読まなかった**。本 arc 3 度目の同型（① c13 の delivery-surface grep miss ② §14.16 の `routing_utils`=VBD-legacy 誤分類〔訂正 #15〕③ 本件）。⇒ **規律の格上げ: 以後 disposition class を出す前に、当該 symbol の全 call site を読んだことを裁定文に明示する**（[[feedback-verify-at-the-delivery-surface-not-the-source-variable-name-2026-07-19]] を分類行為へ拡張）。

**C2（R-SEQ）= pN 正・訂正 #17・私の §14.24(5) R-SEQ 段落を撤回。** 私は「⚠ ただし R-SEQ は生存（LEDGER (d) 行: 『#18 impl 先行 landing・逆順なら #18 全 evidence を PD 基盤で取り直し』）」と書いた。**誤り。** 本 charter **自身の TOP PREMISE（`:3`、逐語）** が既に supersede している:
> 影響: §4 B-class 許可・訂正 #3（a-2 route-start teleport）・**§6 R-SEQ（#18-first-on-kinematic）**・staged flag 共存 rollout = **全て SUPERSEDED（rework 対象）**

かつ **§14.9 sequencing** は「…(4) production 削除 landing →(5) W-b 再記録 →**(6) #18 PD 再測**」= **A-first / #18-last** を既に規定。⇒ **#18-first は生存していない。**
⭐**pN 裁定に CONCUR**: **A-first → affected B0/B1 fresh reacquire → #18 は compliant-substrate 上で実装/再測**。**NOT_COMPARABLE は source-closure 依存 artifact に限定（blanket でない）** — この scoping にも CONCUR（over-broad 無効化を防ぐ正しい絞り）。
⛔**失敗の型（自認・より重い）**: 私は **同一セッションで charter `:3` を読んでいながら**、sequencing を **LEDGER の stale 行**から引いた。⚓「位置は権威ある記録から読む（記憶・目前の salient な信号からでない）」の違反。**支配文書を書いている最中に、その文書自身の premise 節と照合しなかった**のが根因。
⚠**伝播源の是正要求（p6/%12 lane）**: **LEDGER (d) 行が supersede 済の R-SEQ 文言を保持している** — 私の誤りはそこから引いた。私だけの訂正では再発するので、**LEDGER 側の R-SEQ 行に supersession flag**（「§14 TOP PREMISE `:3` + §14.9 により SUPERSEDED、現行 = A-first/#18-last」）を反映されたい。

**保持（pN 明示・p5 同意）**: §14.24 の PASS 側 = **(0) 原理 transfer 不要 / (1) 訂正 #15 = `routing_utils` は DRIVE / (2) 単一 realization 収斂 / (3) harness acceptance 4 条件 / (4) snapshot 系の単一 disposition / `newton_routing_utils` 単独 land 不可** — いずれも本 fold で不変。

**verdict**: pN C1/C2 = **両方 CONCUR**。§14.24 のうち **`dry_run_43step` の class（RESET → typed OFFLINE-REPLAY）** と **(5) の R-SEQ 段落（撤回・A-first へ差替）** を訂正。他は保持。**fold bank 後の pN re-readback を要請**（本 §14.24-a は 0-commit ゆえ bank = %12）。

### §14.23-b snapshot rewind disposition 裁定（§14.23(I) CLOSE）+ **訂正 #18: §14.23(C) の severity 断定を撤回**（v2.18、2026-07-20 10:2x JST — 入力 = call-graph materials c26 `3ddd22322e`〔blob `c84c2743f51e`、%12 納品〕+ pN factual readback PASS 10:22。p5 は **narrative を採らず closed query を自走**）

**(1) ⚠⚠ 訂正 #18 — 私の §14.23(C) severity 断定は誤りだった（本 arc 4 度目の同型失敗・最も鋭い形）**
§14.23(C) で私はこう書いた:「`skills/snapshot.py:119-128` は…**配線済み caller chain 有**: `routing_orchestrator.py:59` import → `:792` instantiate → `:1292` → `:1308` ⇒ **F2 の対象（runtime caller 0）より重い**」。**撤回する。**
p5 独立 closed query（@ c26）:
- `RoutingOrchestrator\s*\(` の全 tree 一致 = **`scripts/scripted_skills.py:15` の docstring 一行のみ**（散文であって call でない）⇒ **instantiation = 0**
- `_run_rl_episode` 内の restore/snapshot 呼び = **0**
- `SnapshotManager\s*\(` = 2 箇所 = `routing_orchestrator.py:792`（**RoutingOrchestrator が未 instantiate ゆえ到達不能**）+ `test_step_table_dryrun.py:111`（**live standalone harness**、`.restore` `:210`/`:226`）
- `restore_state_snapshot` caller = `test_newton_5clip_routing.py:350` **のみ**
⇒ **orchestrator 経路は「配線済みだが dead」**であり、F2 の対象（caller 0）**より重くない — 同класс**。live なのは orchestrator でなく **standalone harness 2 本**。pN の要約「standalone test + dead branch」が正確。
⛔**失敗の型（自認）**: 私は import → 属性代入 → method と chain を上から辿り、**`:792` を「instantiate される」事象として読んだ**。実際は **class body 内の文**であり、その実行は「誰かが RoutingOrchestrator を構築するか」に懸かる。**私は chain の頂点を誰が構築するかを一度も問わなかった＝delivery surface の 1 hop 手前で止まった。** [[feedback-verify-at-the-delivery-surface-not-the-source-variable-name-2026-07-19]] の **call-graph 版**。⇒ **規律追加: 「live caller chain 有」と言う前に、chain 頂点の構築子を closed query で示す。配線 ≠ 生存。**
⚠ **§14.23(C) の F3 裁定本体（guard root 欠落）は不変** — root gap は liveness と独立に実在し、pN が既に修正済（§14.23-a(2)）。誤っていたのは **severity の格付けのみ**。

**(2) §14.23(I) の前提問題は消滅 ⇒ CLOSE**
私が severity を懸けていた未確立点「`_run_rl_episode` が rewind path（`:1129`/`:1184`）に到達するか」は、**到達しない**どころか **orchestrator 自体が誰にも構築されない**ゆえ**問い自体が消滅**。⇒ **DELETE を阻んでいた唯一の理由（"live caller 有ゆえ物理代替が要る"）が消える。** **training carve-out 不要**（pN と同意見・訓練 path に載っていない）。

**(3) ⭐disposition 裁定（§14.23(I) + §14.24(4) を単一決定点で closing。pN 指定 shape を採択）**
両 writer は **単一の決定点・2 つの実行対象**（§14.24(4) の「単一 disposition」は維持、outcome を site 別に確定）:

| site | caller 実態 | 裁定 |
|---|---|---|
| `skills/snapshot.py:119/120/128`（body 3） | orchestrator = dead / `test_step_table_dryrun.py:111` = live harness | **body write DELETE**（§14.16-R「active writer body = DELETE + git evidence」） |
| `newton_routing_utils.restore_state_snapshot`（→`:1829`） | `test_newton_5clip_routing.py:350` = live harness | **同上・同一 bundle** |

**執行条件（pN 指定を採択・設計軸で追認）**:
- **(a) 両 writer の body を同時除去**（片方残置は §14.20 で私が捕捉した「一方だけ残る」再発）
- **(b) compat symbol を残すなら body-deleted fail-closed のみ** — **旧 body の残置不可**。形は **F2 の先例**（§14.23(A)6: 無条件 entry-raise・両分岐 fail-closed・provenance comment・signature 保存）
- **(c) standalone consumers（`test_step_table_dryrun` / `test_newton_5clip_routing`）は同一 bundle で retire または physical-reset-replay へ適応** — 適応する場合は **§14.24(3) の harness acceptance 4 条件を適用**（陽性対照が fire / 計器同一性 joint→FK / verdict 差の帰属 / **kinematic 下の PASS は再取得**）
- **(d) ⛔将来 recovery = episode reset → 物理 action / skill replay、または recovery skill として設計。body-state teleport rewind の復活は禁止。** 設計根拠 = §14.10 ＋ Rs 恒久原則「**sim は現実世界だ。常に現実と同じ条件にしろ**」— 現実に「直前の STEP へ物理状態を巻き戻す」操作は存在しない。⇒ 本禁止は本 chunk 限りでなく **恒久 invariant として §14 に属する**。

**(4) 残 carry**: 本裁定は disposition（何をするか）であって impl 認可ではない。実行は %12 lane（bundle 単位、単独 land 不可）。**A-prereg closure は pN fence の一部**であり私のレグでない。

**verdict**: §14.23(I) = **CLOSE**（前提問題 消滅・DELETE 確定）。§14.24(4) = **確定**（単一決定点・2 site・執行条件 (a)-(d)）。⚠**訂正 #18** = §14.23(C) の severity 断定「live chain・F2 より重い」を撤回（chain は配線済み dead、live は standalone harness 2 本）。**pN の C1/C2 fold（§14.24-a + §14.24 本文 in-place 適用済）と本節の bank 後、re-readback を要請。**

### §14.23-c B3 standalone consumers の**一意決定** + typed OFFLINE 採択 scope の記録（v2.19、2026-07-20 10:4x JST — pN custody notice 10:39 への p5 応答。substantive design = PASS-CLOSE 受領。本節は blocker B3〔私の court〕の一意化 + 採択 scope の records 化）

**(1) B3 = 一意決定。**§14.23-b(3)(c) で私は「retire **または** physical-reset-replay 適応」と **OR のまま**残した。pN 指摘のとおり blocker としては不十分ゆえ、**2 consumer を site 別に一意決定する**。⭐**決定の分岐軸 = 「mid-run rewind」か「episode 境界の初期化」か**（前者に正統な後継は無い／後者は物理 reset 経路で表現できる）。

| consumer | on-disk 実態（p5 自読） | **一意決定** |
|---|---|---|
| `test_step_table_dryrun.py`（`:111` 構築、`:210`/`:226` restore） | file 目的 = skills/ package の dry-run 検証 3 本（step_table / scripted_skills / **snapshot**）。restore leg は **機構それ自体の自己試験** — STEP 1 と mid-step 20 へ restore し `finger_l/r`・`ik_target_l/r`・`clip_status` を print して「Restore OK」と出すのみで、**物理について何も主張していない** | ⭐**RETIRE（snapshot leg のみ）**。理由 = leg の**主題が削除対象の機構そのもの**であり、適応先が存在しない（「STEP 1 へ戻して値を print」の物理版は別物）。⛔**file 全体は retire しない** — step_table / scripted_skills の 2 leg は無関係ゆえ保存。⛔**bookkeeping 専用 accessor を新設して延命しない**（body restore への再結合口を残さない＝§14.23-b(3)(d) の恒久禁止を機構面で担保） |
| `test_newton_5clip_routing.py`（`:350`） | `for ep in range(num_episodes): if ep > 0: state = model.state(); restore_state_snapshot(...)` = **episode 境界で初期状態を再確立**しているだけ。mid-episode の巻き戻しではない | ⭐**ADAPT（physical episode reset へ）**。理由 = 必要としているのは *rewind* でなく **ep 0 と同じ初期条件の再確立**。⇒ **ep 0 が初期状態を作るのと同一の物理経路**（scene 再構築 / RESET class の joint seed + `mj_forward`）で ep>0 も確立する。§14.2 D-② と同型・§14.23-b(3)(d) の「episode reset から」に正しく合致 |

⇒ **B3 は解消**（retire 1 / adapt 1、file 全体 retire はゼロ）。実行は %12 lane・**同一 bundle**（§14.23-b(3)(a)(c) 不変）。adapt 側は **§14.24(3) harness acceptance 4 条件**を適用（特に **(iv) kinematic 下で取得済の PASS は再取得**）。

**(2) typed OFFLINE 採択 scope の記録（over-claim 防止）**: pN 通知「**typed OFFLINE = conditional adopt in pN guard lane only**」を受け、§14.24(3)/§14.24-a の typed OFFLINE-REPLAY 裁定は **設計軸の class 判定としては有効だが、採択は現時点 pN guard lane に scoped**である旨をここに記録する。**`A-2` は fail-closed manifest 機構 + controls の bank/readback まで CLOSED**（pN）。⇒ 本 charter の typed OFFLINE 記述を **global 採択の根拠として引用しないこと**。

**(3) 他 blocker の lane 確認（scope 逸脱防止）**: **B1**（exact A-1 path+blob manifest）/ **B2**（realization API・call-order・single-step owner）/ **B4**（exact regression commands・RED→PASS・provenance・stage set）/ **B5**（c27 current-state bank 訂正）= **%12/pN lane**。私は自発的に踏み込まない（§運用24）。⚠ただし **B2 の "realization semantics"（何を単一実装に収斂させるか）は §14.24(2) で供給済**であり、API 形・呼び順・single-step owner の**確定は impl 側**。追加の設計判断が要るなら照会されたい。

**(4) HALT exception design = pN の scoped CONCUR を確認**: post-A-1 の compliant replacement verification に限る／**実 run は per-run CLOSED**（exact prereg + readback 待ち）／closure は **D5 / A-2 / old writers を除外**／**training・production・global-clean の主張はしない**／**視覚 verdict は V12 経路**。⇒ 本 charter のいかなる PASS も **global kinematic-clean の主張ではない**（§14.23(B) の HOLD と整合）。

**verdict**: B3 = **一意決定 済**（dryrun = RETIRE〔leg 限定〕/ 5clip = ADAPT〔physical episode reset〕）。typed OFFLINE 採択 scope・HALT exception scope・他 blocker lane を records 化。records-fix = v2.17/v2.18 の bank provenance を **c27 `bfc35ca87c`** へ充填 + Status を v2.19 pending へ。**bank 後 re-readback を要請。**

### §14.24-b pN c29 residual R2/R3/R4 への裁定 = **3 件とも私の誤りを認め訂正**（訂正 #19 / #20 / #21）（v2.20、2026-07-20 11:0x JST — pN c29 re-verdict 11:01 への p5 on-disk 検証。⚠ 本 arc **6 度目**の同型失敗ゆえ規律を再度格上げ）

**(1) ⚠⚠⚠ R2（CRITICAL）= pN 正・訂正 #19。§14.24 は route/scripts では【実行不能】な指示だった。**
p5 独立実測（`newton_routing_utils.py` @ probe/pd1-arm-pd committed blob）:
- `:677` `xform=xform, mass=100.0, **is_kinematic=True**` — robot body は **kinematic として構築**
- `:874-880` `# Zero inv_mass for kinematic bodies` → `inv_mass[bi] = 0.0` → `model.body_inv_mass` へ書戻し
- `:469` `cfg.density = 0.0` / `:664` `finger_cfg.density = 0.0` / `:667` `arm_cfg.density = 0.0`
- `joint_target_mode|POSITION|actuator|target_ke|target_kd` の grep = **0 hit**（actuator 配線が存在しない）
- `test_newton_clip_routing.py:8175` 逐語: `VBD control object (required by solver.step, but **no PD targets for kinematic bodies**)`
⇒ **`ctrl[arm] := target` が作用する対象が存在しない**（actuator 配列なし・仮にあっても `inv_mass=0` = 無限質量で加速度ゼロ）。**target-write helper 単独では物理駆動不能**。
⭐**正しい定式化（§14.24(0)/(2) を限定）**: route/scripts の migration は **realization swap ではなく substrate rebuild**。成立前提を順序付きで明示する:
 **(a) robot body の dynamic 化**（`is_kinematic=False`・density/mass/inertia 非ゼロ・`body_inv_mass` を実質量から再計算。`:874-880` の零化は削除） →
 **(b) arm actuator 配線** ⛔**訂正 #22（§14.24-c(1)）で substrate 別に限定** — ~~`joint_target_mode=POSITION` + effort cap~~ は **mujoco 系でのみ有効**。**VBD では `joint_target_mode`・effort・armature・friction がいずれも非対応**（installed `solver_vbd.py:119` 実測）ゆえ **PS-1 の POSITION-servo 形は transfer しない**；VBD で取り得る形は **`target_ke`/`target_kd` の PD のみ**。⚠ ただし §14.24-c(3) の裁定により **VBD の再構築自体を推奨しない**（可能だが banked-DISCARDED への再投資）→
 **(c) qd map の確立**（joint 速度の対応付け） →
 **(d) ここで初めて** target-write helper が意味を持つ（§14.24(2) の「単一 realization 収斂」は (a)-(c) の**後段**）。
⇒ **pN の「PS-1 builder wiring + census + runtime helper を freeze 要」に CONCUR**。freeze なしの [CHANGE] は不可。
⛔**失敗の型（自認）**: §14.15（grip）では ① に actuator 配線を明記していた。にもかかわらず §14.24 で「原理はそのまま transfer」と述べた際、**transfer 先 substrate が前提を満たすかを一度も検証しなかった**。「除去する機構」は読んだが「置換が要求する土台」を読まなかった。

**(2) R3 = pN 正・訂正 #20。§14.23-c の ADAPT 裁定に manifest 登録義務が欠落していた。**
p5 実測: `check_control_method.py:58-62` の `RESET_SEED_MANIFEST` は **1 entry のみ** = `("thread_isaac_lab/envs/newton_grip_env.py", "_seed_robot_joint_row"): {"joint_q": 1, "joint_qd": 1}`。⇒ `test_newton_5clip_routing` の episode joint seed は**未登録**であり、私が §14.23-c で命じた「physical episode reset（RESET class の joint seed + `mj_forward`）」を素直に実装すると **guard が当該 site を FAIL に数える**（pN の言う guard=6 不成立）。
⭐**追加義務（§14.23-c ADAPT に fold）**: adapt は**同一 bundle 内で** ① 新 seed site を `RESET_SEED_MANIFEST` に **(file, function) key + 期待 count** で登録し ② guard 再走で当該 site が sanctioned として扱われ全体が期待値に戻ることを示す。**登録なき ADAPT は不可**。⚠ 登録は「例外の追加」ではなく **RESET class の定義どおりの宣言**（once-at-reset・episode 境界・body を書かない）であることを、登録時に満たしていること。

**(3) R4 = pN 正・訂正 #21。§14.24(3) の acceptance を "static-covered" と分類したのは誤読であり、私の文言が曖昧だった。**
⭐**明確化: (i)-(iv) は【全て runtime 義務】であり static 解析では一切充足されない。**
- **(i) 陽性対照が fire する** = 既知欠陥を**注入して走らせ**、harness が FAIL することを示す。**静的には原理的に不可能**（[[feedback-a-test-that-cannot-come-out-differently-is-not-a-test-2026-07-14]]）
- **(ii) 計器同一性** = code path の読解は必要条件にすぎず、**同一量を測っている**ことは run 比較で示す
- **(iii) verdict 差の帰属** = **2 run の比較**が本体
- **(iv) kinematic 下の PASS 再取得** = 定義上 走行
⇒ **static-covered と分類された時点で control は control でなくなる**（[[feedback-a-gate-validated-under-the-bug-is-validated-by-the-bug-2026-07-15]]）。
⭐**旧FAIL→新PASS の形も指定**: 「テストが通る」では不足。**named な既 RED case を挙げ、それが新 drive 下で PASS すること**を、RED 時点の出力と PASS 時点の出力の両方で示す（pN B4 の evidence 形と整合）。

**(4) R1 / B5 = 私の lane でない。** R1（closure 表の stage-set 矛盾・unchanged partition 正値 8 routing + 10 clip の exact path 再固定）= %12 records。B5（c27 bank provenance records 未 bank）= 私は v2.19 で header/版表を修正済み、**bank 待ち**（%12 実行）。**A-2 / RUN / LANDING = CLOSED 不変**に異議なし。

**(5) ⛔規律の再格上げ（本 arc 6 度目の同型失敗ゆえ）**: ①c13 delivery-surface grep miss ②§14.16 `routing_utils`=VBD-legacy 誤分類 ③`set_jq`=RESET 誤分類 ④§14.23(C) 「live chain」誤断定 ⑤Status 行の substring 置換で面を検算せず ⑥本件 R2/R3（置換先 substrate と guard 契約の前提を検証せず）。**共通根 = 「対象は読んだが、対象が置かれる面・置換先が要求する前提・契約側の要件を読まなかった」。**
⇒ **新規律（自己拘束）: 置換・移行・class 変更の裁定を出す前に、次を列挙し各々 on-disk で確認したと裁定文に明記する — (α) 置換先 substrate が要求する能力（builder/actuator/質量等）(β) guard・manifest 等の契約側が要求する登録・期待値 (γ) 受入条件が static か runtime か。** 列挙できない項があるなら裁定を出さず materials を要求する。

**verdict**: R2/R3/R4 = **3 件とも CONCUR、訂正 #19/#20/#21 を発行**。§14.24 verdict 行に in-place 限定を追記済（「realization の置換だけで足る」と読ませない）。**A [CHANGE] HOLD 継続に異議なし** — むしろ R2 は私の指示が実行不能だったことの発見であり、HOLD は正しい。次の p5 レグ = **PS-1 builder wiring spec（route/scripts 版）の供給**（要請あれば §14.15 ① と同型で起草）。

### §14.24-c A-group substrate 裁定 = **branch split に CONCUR / VBD 再構築せず env7-mujoco へ移管を推奨（Rs 裁定事項）** + 訂正 #22（v2.21、2026-07-20 11:1x JST — %12 STOP-and-report 11:09 + narrow correction 11:14 + pN c30 ruling 11:12 への p5 裁定。pN 指定「p5→Rs 裁定」ゆえ **本節は Rs へのエスカレーション package**）

**(α) substrate capability — p5 が installed source を直読（probe は prior-art blocker 30 で NO-GO ゆえ source-only）**
`/home/rlrk/env_isaaclab7/.../newton/_src/solvers/vbd/solver_vbd.py` 実測:
- `joint_type` 8 / `joint_q` 11 / `joint_qd` 7 / **`target_ke` 13 / `target_kd` 7** ⇒ **VBD は joint と PD drive を扱う**
- `:107` 逐語「**DISTANCE joints are not supported.**」/ `:119` 逐語「**Not supported**: `joint_armature`, `joint_friction`, …」
- package 側: `add_joint_revolute` / `add_joint_prismatic` **存在**
⇒ **%12 の c30「VBD supports none」は誤り**（`clip_routing:771` は **repo の build comment** であって solver capability の事実でない）。**%12 の narrow correction（11:14）および pN の source check（11:12）に CONCUR** — 私も独立に同結論。**旧 S1B PRISMATIC hard-wall の 1.2.1 への無条件転用も不可**（⚠ 私は LEDGER FAILED#1 本文を**未検証**。ここは relay であって私の verify ではない）。

**(1) ⚠⚠ 訂正 #22 — 私の §14.24-b(1)(b) が INVALID。** 私は remediation の (b) に「arm POSITION actuator 配線（**`joint_target_mode=POSITION`** + ke/kd + **effort cap**）」と書いた。**VBD では `joint_target_mode` も effort/armature/friction も supported でない**（`:119`）⇒ **PS-1 の POSITION-servo 形は VBD へ transfer しない**（pN と同結論）。VBD で技術的に取り得る drive 形は **`target_ke`/`target_kd` の PD** のみ。⇒ §14.24-b(1)(b) は **mujoco 系に限り有効**、VBD には適用不可と限定する。

**(2) ⭐ 正しい問題設定**: 争点は「VBD が joint を拒否するか」（＝否）ではなく **「現 scene が jointless という build choice を、今から articulated に作り直すべきか」**。⇒ **私の裁定は、この capability 論争の決着に依存しない形で立てる**（争点が動いても結論が動かない論拠を採る＝§14.23-a で私が採った型）。

**(3) ⭐⭐ 裁定 = VBD を再構築せず、**writer は削除/fail-close**・**B0/B1 は env7-mujoco へ移管**を推奨（最終判断 = Rs）。** 理由は **VBD が可能であることを認めた上でも**成立する:
- **① banked-DISCARDED への再投資**: `CLAUDE.md:80` 逐語「env6-VBD track（AC/AR/IC/Clamp/Unclamp の全 skill env）は **DISCARDED → mujoco-コ**（Rs 2026-06-26）。Grip は env7-mujoco **ACTIVE**」。VBD を articulated に作り直すことは、Rs が discard した track への再投資であり **§運用4 restore-of-banked-DISCARDED gate**（着手前に cross-PV）に該当する。
- **② faithful-gripper wall が残る**（pN 指摘に CONCUR、根拠を補強）: VBD は **`joint_friction` を supported しない**（`:119` 実測）。コ-finger の form-closure 把持は摩擦が本質であり、§0#4 で geometry が human-LOCKED された **env7-mujoco の成果**。VBD 再構築は env6 を discard させた壁に再び当たる。
- **③ 単一 substrate 収斂**: §14.24(2) で私が命じた「単一 realization 収斂」は、substrate が 2 系統のままでは達成されない。移管は realization 重複の根治でもある。
⇒ **VBD 再構築は「可能だが、やるべきでない」。**

**(4) ⛔⛔ Rs 判断を要する 2 点（うち①は他 pane 未 surface — 本 package の主目的）**
- **① `CLAUDE.md` 記載 gate の retire**: `CLAUDE.md:271` 逐語「**Fingertip Z-Check Gate（Newton VBD）**: `test_newton_clip_routing.py` が episode 後 fingertip z を TABLE_HEIGHT と比較、貫通で PASS→FAIL 自動降格」＋ `:85`「テスト: `test_newton_clip_routing.py`（scripted 検証用）」。⇒ **VBD branch の削除は CLAUDE.md に記載された認可 gate を retire する。** CLAUDE.md 変更は **Rs 専権**（三原則#1 / `prohibited.md`）であり、§14.16-2「認可 gate を無検証削除しない」にも該当。**CC は執行しない。** Rs 判断 = (a) gate を env7-mujoco 上に移設して存続 / (b) retire を承認し CLAUDE.md を更新 / (c) VBD branch を当面保持。
- **② active evaluator の substrate 変更**: B0/B1（`policy_route_runner.py`）の env7-mujoco 移管は、既存 B0/B1 artifacts を pN の A-first 裁定どおり **HISTORICAL / NOT_COMPARABLE** にする。移管コストと再取得範囲は Rs sign-off 事項。

**(4-R) OPS(pN) 推奨 disposition の fold = p5 CONCUR**（c33 readback PASS 11:39 で受領。Rs が単一 package を見られるよう本節に統合）:
- **①' Z-Check**: 「**env7-mujoco へ移植 → その後に VBD copy を retire → `CLAUDE.md` 更新**」= 私が (4)① で提示した選択肢 **(a) に相当・CONCUR**。設計上これが正しい順序である理由 = **gate が一瞬も失効しない**（migrate-then-retire であり retire-then-hope でない）。`CLAUDE.md` の編集は「能力の除去」でなく「**完了した移植の記録**」になる ⇒ §14.16-2「認可 gate を無検証削除しない」を満たす。⭐**p5 追加条件（設計軸・移植の受入）**: 移植された Z-Check は **§14.24(3) の acceptance を満たすこと** — 特に **(ii) 計器同一性**（mujoco 版が VBD 版と *同一量* を測る: episode 後 fingertip z vs `TABLE_HEIGHT`、貫通で PASS→FAIL 自動降格）と **(i) 陽性対照が fire する**（貫通ケースを注入して実際に FAIL する）。**両者を示さない移植は「名前だけの移植」であり retire の前提を満たさない。** ⚠ (i)(iii) は runtime 義務（訂正 #21）。
- **②' B0/B1 移管**: 「移管承認 + 旧 artifact = **HISTORICAL / NOT_COMPARABLE** + fresh reacquire」= **CONCUR**。§14.24-a(C2) で私が CONCUR 済の **A-first 裁定と同一の帰結**であり整合（NOT_COMPARABLE は source-closure 依存 artifact に限定、blanket でない）。
- **status**: 上記は **OPS 推奨 + p5 設計軸 CONCUR** であって決定ではない。**Rs 裁定まで全 gate CLOSED・manifest/census 固定を維持**（pN と同意）。Rs へは %12 が surface（p5 は二重送付しない）。

**(5) 暫定 class（pN 提示に CONCUR、私は manifest/census を動かさない）**
| 対象 | class |
|---|---|
| mujoco-only 4（`_run_mujoco_cable_settle_smoke`） | **PHYSICS_REWRITE candidate** — §14.24-b(1) の前提 (a)-(c) を **mujoco path で**確認の上。POSITION 形は articulated ゆえ有効 |
| VBD-only writer sites | **KINEMATIC DELETE 必須**（Rs directive・substrate 論と独立）。**consumer 処分 = SUBSTRATE-BLOCKED** → 上記 (4) の Rs 裁定で解消 |
| mixed（`clip_routing`） | **branch-callsite split**（file 単位でない） |
| `newton_routing_utils` の file/track-level DISCARDED | ⛔**私も HOLD・非承認**（active B0/B1 consumer 有。pN と同じ） |
| `grip_modes` 2 | **未分類のまま**（backend-liveness pin 待ち。私は分類しない） |
⇒ **manifest / census は動かさない**（pN 指示に CONCUR）。**prereg v2 §B2 = DO-NOT-IMPLEMENT 維持。**

**(6) ⛔ 規律 — 本 arc 7 度目、かつ「6 度目の訂正の中で」再発した**
§14.24-b(5) で私は「(α) 置換先 substrate が要求する能力を on-disk 確認」と自己拘束したのに、**質量と actuator 配線は見て「solver が joint を扱えるか」を見なかった** — 前回の指摘が指した層で止まり、底まで降りなかった。**私の訂正は毎回 1 層ずつしか降りていない。** ⇒ 規律追加: **capability 主張は「repo の comment」でなく「installed solver source」で取る**（`clip_routing:771` の build comment を capability と読んだのが %12・私の共通の罠）。
⭐**near-miss の記録（8 度目を免れた）**: 私は最初 VBD solver を誤 glob で探し、**空のファイル集合に対する grep が全項目 0 を返した**。これを「不在の証拠」として報告していれば新たな誤りだった。⇒ **規律: 0 hit を不在の根拠にする前に、検索対象集合が空でないことを示す。**

**verdict**: branch split = **CONCUR**（1 class でない）。VBD-branch の PHYSICS_REWRITE は **undefined ではなく「可能だが再投資として不適」** ⇒ **VBD 再構築せず・writer は削除/fail-close・B0/B1 は env7-mujoco 移管を推奨**。ただし **(4)①（CLAUDE.md 記載 gate の retire）と (4)②（active evaluator の substrate 変更）は Rs 専権**ゆえ **BLOCKED_FOR_USER として Rs 裁定を要請**。訂正 #22 発行。A [CHANGE] CLOSED に異議なし。

### §14.25 env7-mujoco **Fingertip Z-Check 移植 — 設計 input**（v2.23、2026-07-20 12:0x JST — Rs 裁定 c36 `eefad77773`〔逐語「1：a 2:承認」〕+ pN design-lane OPEN 12:03 を受けた p5 deliverable。**設計 input のみ / RUN・impl・landing は未解錠**）

**(0) scope と依存**: Rs 裁定 ① = **option (a) = 移植 THEN retire**（順序が load-bearing = gate は env7-mujoco 上で存在し検証されるまで VBD copy 削除不可）。② = B0/B1 evaluator の env7-mujoco 移管 承認・旧 artifact = HISTORICAL/NOT_COMPARABLE・fresh 再取得 必須。⭐**B0/B1 移管は本 gate 移植とは別の依存 workstream**（pN 指定・両者を 1 chunk に混ぜない）。**gate 移植は ACTIVE substrate 上の新規実装**ゆえ既 bank の prereg では覆えない（%12 指摘に CONCUR）。

**(1) 保存すべき契約（`CLAUDE.md:271` 逐語）**: 「episode 後 fingertip z を TABLE_HEIGHT と比較、貫通で PASS→FAIL 自動降格（`[ZCHECK]` ログ）」。

**(2) 現計器の完全仕様（p5 on-disk 実測 = 移植の基準線。`test_newton_clip_routing.py`）**
| 要素 | 実測仕様 |
|---|---|
| 入力源 | **`state.body_q`**（`:458`）— ⚠**`fk_state` ではない** |
| 測定点 | 各腕 `body_start + 7` と `+ 8`（prismatic finger 2 body）の **z = index 2**（`:467-470`） |
| 参照面 | `table_z = float(TABLE_HEIGHT)`（`:561`）= `task_config.py:20` **0.80** |
| 深さ | `depth = table_z - fz`、`> 0` で貫通（`:568`） |
| 計数 | **1 frame につき最大 1**（左→右・点順に走査し最初の貫通で `found`→break）⇒ `pen_count` = **貫通 frame 数**（貫通点数でない） |
| ⚠ max | `max_penetration_mm` = **「各 frame で *最初に見つかった* 貫通点の深さ」の frame 間最大** — short-circuit ゆえ**真の最大深さではない**（同 frame 内のより深い点は反映されない） |
| 判定 | `penetration_detected = pen_count > 0`（**1 frame・1 点でも trip**） |
| 降格 | **`overall == "PASS"` のときのみ PASS→FAIL**（一方向・CRASH/FAIL 等は不変）+ `fail_reason = f"fingertip_penetration_{mm}mm"`（`:8460-8463`） |
| ログ | `[ZCHECK] Fingertip penetration detected: {mm}mm below table ({pct}% of frames)`（`:8456`） |

**(3) 移植の設計要件（(α) substrate 能力の実測に基づく）**
- ⭐**R-1′ body identity は `Model.body_label` の名前照合＋検査で解決する** ⛔**訂正 #23 で全面差替（旧 R-1 の *anchor* は FALSE）**。
  - ⛔**撤回**: 旧記載「`newton_grip_env.py:644-657` の **`_finger_physics_ids` 型 discovery** を用いる（能力は既存）」は**誤り**。p5 実測: 当該箇所は `bi = ws + arm_offset + lf` の**純粋な添字算術**（`ROBOT_BODIES_PER_ARM = 14`〔`task_config.py:31`〕/ `FINGER_LOCAL = GRIPPER_PAD_BODY_IDX = [9,13]`〔`:48`/`:37`〕）であり、**name lookup / cardinality / uniqueness / fail-close はいずれも 0 件** ⇒ discovery ではない。**これを再利用すれば R-1 が禁じた当の失敗を `[7,8]`→`[9,13]` に置換して再演する。** %12 の B1 finding（c40 `730bed02f0` / blob `46e70a6b1497`）+ pN HOLD に **CONCUR**。
  - **保持される原理**（旧 R-1 のうち正しかった部分）: 現行 `bs+7 / bs+8` は **VBD build 固有の直値**であり、env7-mujoco は コ-finger（`2f85_koshape.xml`・§0#4 human-LOCKED）で body 構成が異なる ⇒ **offset を移植してはならない**（「別 body の z を測る gate」= information-zero か false-pass）。
  - **正しい anchor（p5 が installed Newton 1.2.1 source で実測）**: **`Model.body_label: list[str]`** = `newton/_src/sim/model.py:426` 実在／builder が populate = `builder.py:3636` `self.body_label.append(label or f"body_{body_id}")`／**MJCF importer が asset の body 名から populate** = `import_mjcf.py` `body_label_path = f"{parent}/{name}" if parent else name` → `label=body_label_path`。⚠ pN 提案の `Articulation.find_bodies` は **env7-mujoco に届かない**（`base_articulation.py:245` に実在するが `thread_isaac_lab/envs`・`skills` での使用 0・env7 は `newton.Model` を直接 build）— **CONCUR・採らない**。
  - **R-1′ が満たすべき契約（解決関数の受入条件）**:
    1. **名前照合で解決**する（添字算術を用いない）。
    2. ⚠**label は階層パス形**（`parent/child`、`import_mjcf` 実測）— bare name 前提の照合を書かない。
    3. ⚠**label 未設定 body は `body_{id}` の合成名になる**（`builder.py:3636`）⇒ 合成名に当たり得る緩い照合（過度な正規表現等）を禁ずる。
    4. **per-arm exact cardinality = ちょうど 2**（左右指先）。**0 でも 3 以上でも FAIL**。
    5. **uniqueness**: 解決された body index が全体で一意（重複 = FAIL）。
    6. **fail-close**: 0 件・過多・曖昧一致・label 欠落のいずれも **loud FAIL/RAISE**（R-3 と同一方向）。
    7. ⛔**実 label 文字列を本 spec に書かない**（pN 指摘に CONCUR — 私は未読ゆえ推測しない）。**impl が built model から実 label を読み出して pin し、evidence として記録する**こと。文字列の確定は impl レグ。
  - **acceptance への追加**: §14.25(4)(i) の陽性対照に **R-1′ の陰性対照**を足す = **label を 1 つ壊す/削ると解決が FAIL する**ことを示す。これが無いと「名前照合したつもりで実は当たっていない」を検出できない。
  - ⭐**R-1′ 確定形（pN c41 `d25c9fc07c` §6 の 4 点 shape ＋ 追加要求を fold。材料 §4 = blob `ebd7863ff54b2c` 読了）**:
    - **(A) `Model.body_label` を単一 source** — 他の識別手段を**併用しない・fallback も置かない**。⚠hybrid（名前照合 + offset fallback）は**静かに offset 動作へ退行する**ため禁止。
    - **(B) offset 依存 0 を機械検査可能な形で** — %12 §4 の具体要件を採用: **Z-Check 経路から `ROBOT_BODIES_PER_ARM` / `FINGER_LOCAL` への依存を外す**（当該経路の grep で 0 を示せること＝検査可能な述語にする）。
    - **(C) per-arm exact cardinality ＋ uniqueness**（上記契約 4・5 と同一）。
    - **(D) 0 match / 過多 match は fail-close**（契約 6・R-3 と同一方向）。
    - ⭐**(E) 追加要求（pN）= 実 label は「prereg で authorized な実 build identity leg」で確定し、source closure を pin する。** ①当該 leg は **prereg に authorize されたもの**であること（impl の副産物にしない）②pin すべき source closure = **asset MJCF の path + sha / importer 経路（`import_mjcf.py:1433` hierarchical label → `:1609` add_link label）/ builder finalize 経路 / 結果の `Model.body_label` 一覧** — label がどの build から出たか**再現可能**にする ③**未 authorize の label 読み出しを spec / verdict の根拠にしない**。⇒ 私が (7) で「impl レグ」と書いた部分は**本 (E) に格上げして置換**する。
  - **記録（pN c41 §6）**: pN が自身の `Articulation.find_bodies` 提案を **delivery-surface 誤りとして撤回**（閉 query で `envs`+`skills` = 0・env7 = Newton 1.2.1 直 build）⇒ 私の「採らない」判断と一致。pN 側の historical 測定として保存。⭐私が **exact koshape label を非主張に留めた点**も pN が正と評価（推測で書かなかったことが結果的に正しかった）。
  - ⚠**carry（本節の射程外・記録のみ）**: grip env 自身の `FINGER_LOCAL = [9,13]` 添字算術の処分は **別 owner / 別 gate**（%12 §5 に CONCUR — 本件の論点は「Z-Check の anchor として再利用可か」= **NO** のみ）。ただし**同型パターンの未処分インスタンス**として本行に記録し、失われないようにする。
- ⭐**R-2 `TABLE_HEIGHT` は値でなく provenance を pin。** `task_config.py:20` = **0.80** だが `task_config_optionB/C/D.py` = **0.75**。参照面が 50mm ずれれば**同一物理で別 verdict**。⇒ 移植版はどの config から取るかを **assert** すること。
- ⭐**R-3 fail-closed 化（現行の欠陥を持ち込まない）。** 現行は `_zheight_frames` が空だと `check_penetration()` → `None` → caller の `if pen and …` で**黙って素通り = fail-OPEN**。新 substrate で recorder 未配線なら **gate は常に PASS** になる（[[feedback-a-gate-validated-under-the-bug-is-validated-by-the-bug-2026-07-15]]）。⇒ **データ欠落は FAIL（または loud RAISE）**。⚠ これは保存でなく**意図的強化**ゆえ **CLAUDE.md diff 起草時に変更点として明記**。
- **R-4 max の short-circuit 仕様は「まず保存」を推奨。** 真の最大深さに直すと**数値が変わる**ため、同一性を先に確立し改善は別 chunk（直すなら (iii) で「計器変更由来」と帰属記録）。

**(4) acceptance = §14.24(3) 4 条件の mujoco 適用形（⚠ **全て RUN leg・HALT-fenced**、訂正 #21 のとおり static では一切充足されない）**
- **(i) 陽性対照が実際に fire**: 既知貫通を注入 → `[ZCHECK]` 出力・`overall` が PASS→FAIL・`fail_reason` に mm が載ること。**注入しても FAIL しない gate は gate でない。** ＋ **R-3 の対照**: `_zheight_frames` を空にしたら **FAIL になる**こと（fail-closed の陽性対照）。
- ⭐**(ii) 計器同一性 — 実 run 同士を比べてはならない。** **共通の合成入力**（z 列を直接与える）に対し **VBD 版と mujoco 版が `max_penetration_mm` / `penetration_pct` / `frames_checked` を同値で返す**ことで示す。物理を挟まず**計器だけ**を突き合わせる。（実 run 比較は物理が違うので (ii) の証明にならない — [[feedback-same-constant-is-not-same-measurement-surface-2026-07-18]]）
- ⭐**(iii) verdict 差の帰属 — 再現を期待しない/してはならない。** VBD では `body_q` が **FK から強制配置**されていたので本 gate は *command* の貫通を測っていた。mujoco では `body_q` が **articulated dynamics の結果**ゆえ同じ述語が *物理的* 貫通を測る。⇒ **同じ計器・別の失敗モード**。(ii) が通っている前提の下でのみ、verdict 差を「物理差」と帰属できる。
- **(iv) kinematic 時代 PASS の再取得**: 旧 PASS を移植の証拠に流用しない（RUN leg・HALT-fenced）。

**(5) retire 条件（pN 指定に CONCUR）**: **gate 移植 two-key ∧ B0/B1 移管 two-key ∧ fresh reacquisition ∧ exact `CLAUDE.md` diff の Rs 承認** — 4 つ揃うまで **VBD copy は削除不可**（Rs「migrate THEN retire」の執行）。⛔ **`CLAUDE.md` は Rs 専権ゆえ p5 は編集しない**。diff 起草 = %12、承認 = Rs。

**(6) 付随記録（gate には非 load-bearing）**: recorder の comment は「Hand z (body offset 6 = panda_hand)」だが `task_config.py:47` は `EE_BODY_OFFSET = EE_BODY_IDX  # 5` — **comment と定数が不一致**。Z-Check は finger の 7/8 直値を使うため gate は無影響だが、移植で hand z を使うなら踏む。

**verdict**: 設計 input = 上記 (1)-(4)。**予期される最大の落とし穴は R-1（offset 直移植）と R-3（fail-open の持込み）** — どちらも「移植したように見えて何も測っていない gate」を生む。(ii) は**合成入力での計器突合**で、(iii) は**再現でなく帰属**で満たすこと。impl・RUN は未解錠のまま。

### §14.26 cross-backend 共有 writer（`update_kinematic_bodies`）の class 裁定 = **(c) MIGRATION_PENDING〔loud・counted〕 → 駆動移管 landing で (a) 単一 realization 収斂。(b) 枝分割は却下** + **訂正 #24** + ⛔**Rs への scope 照会**（v2.26、2026-07-20 17:0x JST — %12 材料 c44 `58ba07bc01`/blob `80d42b3edcc6`〔材料のみ・class 選択なし〕への p5 裁定。実測 = pinned blob c43 `d1859c90f2`）

**(1) 事実確認（p5 独立実測 @ c43 — %12 finding を CONFIRM）**
- `policy_route_runner.py:480` `rt.update_kinematic_bodies(state, fk_state, scene_info["robot_body_count"])` ∧ **`:487` `make_solver(model, backend="mujoco", …)`** ⇒ **B0/B1 evaluator は MuJoCo solver で走りながら kinematic body writer を使っている**。⇒ 本 writer は **VBD 専用ではない**。
- ⚠ 同 file `:483` に既存 comment「`gripper_dynamic = True`（else `physics_step` FK-overwrites the gripper coords => **inert servo**）」= **FK 上書きが servo を無効化する事実は既に repo が認識**している。
- ⭐**私の census は %12 の「7 file / 9 callsite」より広い**: 定義 4（`route_executor.py:1683`〔raise 済 shim〕/ `newton_routing_utils.py:910` / `test_grip_modes.py:345` / `test_newton_clip_routing.py:1752`）+ 呼出 10（`route_executor:1745`〔dead-by-raise〕/ `routing_utils:938`,`:1829` / `policy_route_runner:480` / `test_grip_modes:399` / `test_newton_clip_routing:1838`,`:8436` / **`wet_run_full_sequence.py:161`,`:401`,`:453`**）+ import 3 ⇒ **触れる file = 8**。
- ⭐⭐**`wet_run_full_sequence.py`（3 callsite）は guard の FAIL 一覧（35）に一度も現れない** — guard は **sink ベース**ゆえ *caller* は計上されないため（設計どおりで guard の欠陥ではない）。⇒ **重要な一般則: guard の count は blast radius ではない。** 共有 writer の disposition は **guard FAIL 一覧ではなく caller closure** で見積もること。

**(2) ⚠ 訂正 #24 — 私の §14.24-c(5)「mixed = branch-callsite split」を narrow する。**
当該行は *file 内で枝が独立な call site* には妥当だが、**共有 realization symbol には適用してはならない**。共有 symbol を枝ごとに分割すれば **realization が再び複製され**、§14.24(2)「単一 realization 収斂」が終わらせようとした当の分岐を再生産する。⇒ **候補 (b) は却下**。加えて (b) は mujoco 枝の kinematic 経路を**恒久化・正当化して見せる**害がある。

**(3) ⭐ class 裁定**
- **即時 class = (c) `MIGRATION_PENDING`**（`update_kinematic_bodies` とその caller closure）。理由 = 本 writer は **live な mujoco consumer（B0/B1）を持つ**ため、いま削除/raise 化すれば **Rs が承認した評価系を壊す**。§14.16-R の DRIVE 原則（active runtime robot body drive → 削除・actuator 化）は**維持**し、削除の *時期* のみを consumer の駆動可用性に従属させる。
- ⛔**MIGRATION_PENDING の執行条件（免除にしないため）**: ①**RED のまま・canonical count を減らさない**（sanctioned manifest に載せない）②**期限を持つ class** = 「B0/B1 駆動移管の landing」で自動的に解除審査に入る ③ 新規 caller の追加禁止（増殖を止める）④ 本 class は **guard 上で可視**であること（silent carry にしない）。
- **終端形 = (a) 単一 realization 収斂 + consumer 適応**（§14.24(2) の延長）。ただし **実行は全 live consumer に actuated drive が用意された後**。mujoco 系は達成可能（articulated・POSITION 形有効）／VBD 系は不可（§14.24-c 訂正 #22）⇒ **VBD 系 consumer は retire / 移管の側で処理**され、(a) の対象にならない。
- **順序**: (c) 据置 → B0/B1 駆動移管 landing → (a) 収斂 → 旧 writer 削除。**この順序が守られる限り live consumer は一度も壊れない**（Rs の migrate-THEN-retire と同型）。

**(4) ⛔ Rs への scope 照会（%12 の推定を私が事実に格上げしない）**
%12 は「Rs ruling ② の『移管』は **solver 切替でなく robot 駆動方式（kinematic FK 書込 → actuated）の移管**を指すはず」と述べ、**自ら推定と明示**している。⭐**私の実測はこの推定と整合する**（`policy_route_runner` は既に `backend="mujoco"` で走行し、なお kinematic writer を使う ⇒ solver は既に mujoco ゆえ「solver 移管」は内容を持たない）。**しかし Rs が何を承認したかは Rs しか確定できない。**
⚠**私自身の不正確さも申告**: §14.24-c(3)③ で私は「単一 substrate 収斂 — substrate が 2 系統のままでは達成されない」と書いたが、B0/B1 について言えば **substrate（solver）は既に mujoco** であり、残っているのは **駆動方式**である。⇒ 当該論拠は **B0/B1 に関しては substrate ではなく drive の問題**として読み替えるべきだった（VBD 系 consumer については substrate 論として依然有効）。
⇒ ⛔**BLOCKED_FOR_USER（Rs 確認）**: 「**Rs ruling ②『B0/B1 evaluator の env7-mujoco 移管 承認』の内容は (i) 駆動方式の移管（kinematic FK 書込 → actuated）か、(ii) それ以外を含むか**」。(i) であれば本 §14.26 の順序でそのまま実行可能。**確認まで (c) 据置**。

**verdict**: class = **(c) MIGRATION_PENDING〔loud・counted・期限付き・新規 caller 禁止〕**、終端 = **(a)**、**(b) は却下**。attribution 訂正 = 本 writer は **cross-backend 共有 writer** であり「VBD 枝」帰属は誤り（%12 finding に CONCUR）。訂正 #24 = §14.24-c(5) の「mixed = branch-callsite split」を **共有 symbol に適用しない**よう narrow。⭐**一般則の追加: guard count ≠ blast radius**（disposition は caller closure で見積もる）。Rs scope 照会 1 件を BLOCKED_FOR_USER で起票。impl / RUN は未解錠のまま。

### §14.26-a pN c44 CONCUR + 3 因子基準の fold（v2.27、2026-07-20 17:2x JST — 記録 c46 `f368dce537` / blob `b208a1b3da1b76`〔p5 照合済〕§7 = authoritative を読了。**本節は加算 fold であり §14.26 の裁定を変更しない**）

**(1) ⭐ 判定基準の採択（pN 明示・私の §14.26 と整合）**: **定義 file や solver default で branch class を付けてはならない。** disposition は **`consumer callsite` × `effective backend` × `robot drive realization` の 3 因子**で決める。⇒ **本基準を §14.26 の (c)→(a) 遷移を支配する分類規則として採択**する。
⭐**なぜ default が危険かの実測的裏付け**: `task_config:107` の solver default は **`vbd`**。default に従って class を付ければ、**既に `backend="mujoco"` で走る live consumer（`policy_route_runner:480/:487`）を VBD と誤ラベルする** — これが §14.26(1) で私が測った害の一般形。⇒ **(b) 枝分割の却下は本基準からも導かれる**（枝は定義 file / default 由来の概念であり、3 因子のうち 2 因子を無視する）。

**(2) manifest v2.4 の class 行 = 記入不可に CONCUR。** p5 class ruling（= §14.26、**v2.26 で発行済・bank 待ちゆえ両者に未可視**）＋ Rs ruling ② の意味確定まで書けない。⇒ **census 35 固定・step3 の docs-only OPEN 一時停止**に異議なし。確定後は **ruled-class prereg を再提示 → two-key 再取得**（私のレグ = 設計軸 key）。

**(3) Rs ruling ②「移管」の実質要件 = 両軸一致の読みとして記録（⛔確定は Rs）**: ①**articulated/actuated robot drive path への cutover** ②**旧 `update_kinematic_bodies` call の消滅** ③**cutover source sha + substrate id** ④**fresh reacquisition**（別 workstream）。
⭐**整合の観察**: 上記②は **§14.26 の終端 (a)〔単一 realization 収斂 → 旧 writer 削除〕と同一の事象**を consumer 側から見たもの。⇒ **「B0/B1 移管の完了」と「MIGRATION_PENDING の解除」は同じ landing で同時に成立する**（別々の gate にしない）。私の Rs scope 照会（§14.26(4)）は本読みの確認を求めるものであり、**両軸が一致していること自体は Rs 確定の代替にならない**（合意は裁定でない）。

**(4) 記録（私の lane 外・landing を gate するので明示）**: **main 側 drift / 4 dirty file の owner は git だけでは UNPROVEN** ⇒ **user-owned shared-tree change として不触**・**owner claim + reconcile manifest なしに landing 不可**（pN §7-4）。⇒ 私は当該 file に触れない。⛔`source` / `[CHANGE]` / `RUN` / `landing` / `push` / `training` / `CLAUDE` 編集 = **CLOSED 維持**、WMSO priority sequencing checkpoint も維持。

**verdict**: pN 3 因子基準を **§14.26 の分類規則として採択**（(b) 却下は本基準からも導出可能・solver default = `vbd` の実測がその必要性を裏書き）。manifest class 行の deferral・census 35 固定・step3 一時停止に **CONCUR**。ruling ② の 4 要件を**両軸一致の読み**として記録し、**確定は Rs** と明示。⭐**②と §14.26 終端 (a) は同一 landing の同一事象**ゆえ gate を分けない。§14.26 の class 裁定自体は **v2.26 で発行済**（bank 待ちゆえ未可視 — 次 bank で解消）。

### §14.26-b ⚠**訂正 #25 — §14.26-a(3)「同一 landing の同一事象」は誤り**（pN narrowing ② に CONCUR）+ Rs 応答の正確な記録（v2.28、2026-07-20 17:4x JST — 記録 c48 `bb68cb3c0f` / blob `e16b7ab36c38`）

**(1) ⚠⚠ 訂正 #25。** §14.26-a(3) で私はこう書いた:「②〔旧 `update_kinematic_bodies` call の消滅〕は §14.26 終端 (a) と**同一の事象**を consumer 側から見たもの ⇒ **『B0/B1 移管の完了』と『MIGRATION_PENDING の解除』は同じ landing で同時に成立する（gate を分けない）**」。**誤り。撤回する。**
p5 再実測（@ c47）: 当該 symbol の live callsite は **10**、うち **B0/B1（`policy_route_runner:480`）は 1 つだけ**。残 9 = `newton_routing_utils:938`/`:1829`・`test_newton_clip_routing:1838`/`:8436`・`wet_run_full_sequence:161`/`:401`/`:453`・`test_grip_modes:399`・`route_executor:1745`〔dead-by-raise〕。
⇒ **B0/B1 closure ⊊ symbol closure**。B0/B1 の call を消しても symbol は死なない。**pN narrowing ②「legacy 消滅は B0/B1 の callsite/closure 限定であり共有 symbol 全体の即時削除ではない」に CONCUR。**
⛔**自己申告（本 arc で最も悪い型）**: この census は **私自身が §14.26(1) で 2 版前に測って書いていた**（「触れる file = 8 / 呼出 10」）。**refuting data を自分の doc 内に持ちながら、包含関係を確認せず 2 集合の同一性を主張した。** 規律追加: **「同一の事象」「同時に成立」と書く前に、2 つの集合の包含関係を明示的に示す**（片方が他方の真部分集合なら同一性は成り立たない）。

**(2) 訂正後の正しい構造 = MIGRATION_PENDING の解除は per-consumer-closure の段階解除**
- 各 consumer closure が **独立に** cutover（または retire）し、その分類は **pN 3 因子（callsite × effective backend × drive realization）**で決まる。
- **B0/B1 cutover が解除するのは `policy_route_runner:480` + その closure のみ。**
- **symbol 終端 (a)〔単一 realization 収斂 → 旧 writer 削除〕は「最後の consumer」で成立**する。**最初の consumer ではない。**
- ⇒ **gate は分かれる**（§14.26-a(3) の逆）。⭐ これにより 3 因子基準との整合も回復する — 私は基準が *局所化* したものを「同一 landing」で**再びグローバル化**してしまっていた。
- **(c) 解除条件（更新）** = ①当該 consumer が 4 要件を満たす（actuated drive cutover / 当該 closure の legacy call 消滅 / cutover sha + substrate id / fresh reacquisition〔別 workstream〕）②**既存 two-key / GO のレビュー**（pN 指定）③ 残 consumer は **MIGRATION_PENDING のまま RED**（部分解除で count を減らさない）。
- **narrowing ①（solver 名だけの MuJoCo 化では cutover 不可）**にも CONCUR — §14.24-c 訂正 #22・§14.26-a(1) と同方向（solver ≠ drive）。

**(3) ⛔ Rs 応答の正確な記録（records-vs-fact）**: §14.26(4) の BLOCKED_FOR_USER に対する **Rs 逐語 = 「これはT-ROOT-OPS-SUPERVISOR-CODEXに確認して」= routing 指示**であって **substance への裁定ではない**。これを受けた **pN scope confirmation（17:36:51）= 4 要件 CONCUR** も、pN 自身が「**Rs verbatim / ruling 権威の代作は不可・最終裁定者は Rs**」と明示している。
⇒ ⛔**本 charter のどこにも「Rs が 4 要件を裁定した」と書かない。** 現状の正確な地位 = **「Rs が pN へ routing → pN が scope confirmation（裁定でない）」**。ruling ② の substance は **依然 Rs 未確定**。⚠ 私の §14.26-a(3) が「両軸一致は Rs 確定の代替にならない」と書いた原則を、**本節で自分に適用**する。

**verdict**: **訂正 #25** = §14.26-a(3) の「同一事象・gate を分けない」を撤回 → **per-consumer-closure の段階解除**（B0/B1 は 10 callsite 中 1、symbol 終端は最後の consumer）。pN narrowing ①② に **CONCUR**。(c) 解除条件を 3 項に更新。Rs 応答は **routing であって ruling でない**と正確に記録。§14.26 の class 裁定本体〔(c)→(a)・(b) 却下〕と §14.26-a の 3 因子採択は **不変**。

### §14.26-c 照会 3 件への裁定 + 新実測 ①② への CONCUR + ⚠**訂正 #26**（v2.29、2026-07-20 20:3x JST — %12 c49 `b793cce7a1`〔manifest v2.4 再発行〕への p5 応答。全て committed blob 直読）

**(0) ⚠⚠ 訂正 #26（本節で最も重い・私の過去 2 節の帰属を覆す）**: 私は §14.24(1) 訂正 #15 で「`newton_routing_utils` は **active B0/B1 evaluator（`policy_route_runner.py:480`）の共有 realization**」と書いた。**帰属が誤り。** 実測: **`policy_route_runner.py:362` `import test_newton_clip_routing as rt`** ⇒ `:480` `rt.update_kinematic_bodies(...)` が呼ぶのは **`test_newton_clip_routing.py:1752` の copy** であって `newton_routing_utils` ではない。
- `newton_routing_utils.update_kinematic_bodies` の **外部** consumer = `run_demo_from_waypoints.py:47` / `test_newton_5clip_routing.py:49` / `wet_run_full_sequence.py:44`（import）— **B0/B1 は含まれない**。
- ⇒ **訂正 #15 の *class*（DRIVE／VBD-legacy でない）は維持し得るが、その *根拠* は B0/B1 ではなく上記 3 consumer で再確認を要する。** 根拠が誤っていた分は本節で撤回する。
- ⛔**失敗の型**: **alias（`rt`）の束縛先を import を読まずに断定した。** 本 arc 11 例目、規律 ③（再利用 anchor は中身を行単位で示す）の **alias 版**。⇒ 規律追加: **`mod.f()` の帰属を言う前に当該 module alias の import 行を示す。**
- ⭐**副次的に良い帰結**: `route_executor.update_kinematic_bodies`（`:1683` = 無条件 raise）は B0/B1 の経路に**入っていない** ⇒ B0/B1 は現在 **壊れていない**（`rt` が clip_routing ゆえ）。

**(1) 照会(1)** ⚠**本項は §14.26-d で RE-TARGET された**（%12 の citation に file 名が無く、私は `newton_routing_utils.py:1827-1833` と解した。真の対象は **`test_newton_clip_routing.py :: physics_step`（def `:1790`）の `:1827-1833`**）。**以下の裁定は `newton_routing_utils.restore_state_snapshot` について有効**（その限りで正しい）が、**照会への回答としては §14.26-d が正**。= ⛔ NO（B0/B1 closure に bind しない）。3 点:
- ⚠**label の不一致**: 指定された `:1827-1833` は **`physics_step` ではなく `restore_state_snapshot`（def `:1806`）の中**（p5 が def を遡って確認。当該 block は `fk_state.joint_q.assign(fk_jq_reset)` → `eval_fk` → `update_kinematic_bodies(...)` → `print("[RESET] Scene restored")`）。
- **既に裁定済**: 当該 site は **§14.23-b(3) で body write DELETE**（`skills/snapshot.py` と同一 bundle）+ **§14.23-c で consumer = `test_newton_5clip_routing:350` を ADAPT** と決着済み。**新規 residue ではない。**
- **bind が誤りである理由**: `restore_state_snapshot` の caller は **`test_newton_5clip_routing.py:350` のみ**で **B0/B1 は呼ばない**。B0/B1 cutover に bind すれば **closure の誤帰属**（訂正 #25 と同型）を再演する。⇒ **既存裁定のまま、5clip の ADAPT bundle 側で処理**。

**(2) 照会(2) = §14.23-c の既 banked 軸で判定（新軸を作らない）** — `test_newton_clip_routing.py:8399` `if ep > 0:` block は **episode 境界の初期状態再確立**であって mid-run rewind ではない ⇒ **ADAPT（physical episode reset）**、`test_newton_5clip_routing:350` と同一 verdict。
⭐**ただし当該 block は 4 種の書込を含むので、component 別に class を付す**（実測 `:8401-8411`）:
| 書込 | class |
|---|---|
| `state.body_q` / `state.body_qd` ← settled | **DELETE**（body-state 直接復元は §14.10 で不可・物理 reset が joint から再確立する） |
| `state.joint_q` / `state.joint_qd` ← settled（robot 分） | **RESET**（joint seed + forward）。⚠**訂正 #20 により `RESET_SEED_MANIFEST` への (file, function) 登録が必須** |
| cable joint 分（comment「body transforms + **cable joints**」） | **CABLE-SEED**（下記 (3) と同一軸） |
| `solver.body_q_prev` / `particle_q_prev` / `joint_sigma_prev` | **assign しない** — 物理 reset で自然に再確立させる（solver 内部 previous-step state を外から書くのは body-state 復元と同じ害）。⚠ 現 code の `hasattr` guard は mujoco/VBD 差の吸収であり、ADAPT 後は**不要になる**はず |

**(3) 照会(3) = **あります。banked 軸 = `CABLE-SEED`**。** 根拠 = §14.15 PS-3「cable 行 → **CABLE-SEED marked+loud**（object episode-boundary init のみ・pN guard-rail: robot/finger body write へ拡張不可）」+ §14.16／§14.16-R 判定式「cable object init か? yes=**CABLE-SEED(marked)**」。
p5 実測で当該 4 site は要件を満たす:
- `:7896-7897` = 「lift the FREE-root pz **ONCE**, then **hands-off** the cable」⇒ **一回限りの初期条件付与→以後は物理**・**joint-space**（`state.joint_q.assign` + `eval_fk`）・cable object ✓
- `:7960-7961` = segment coords に curl0 を一度置いて curl を測る ⇒ 同上 ✓
**適用条件（満たすこと）**: ①**joint-space のみ**（body-state に及ばない）②**one-time**（step loop 内でない — impl が明示）③**marked + loud** ④⛔**robot/finger への拡張不可**（pN guard-rail）。
⚠**帰結の明示**: 正しく CABLE-SEED 登録すると当該 site は guard 上 `[FAIL]` から `[CARRY]` へ移る ⇒ **canonical count が変わる**。よって**宣言/manifest 経路を通すこと**（黙って移さない）。

**(4) 新実測①（gripper_dynamic）= CONCUR、ただし機構の所在を訂正付きで確定。** `gripper_dynamic` は **`newton_routing_utils.py` には 0 hit**、honor するのは **`route_executor.py` / `test_newton_clip_routing.py` / `policy_route_runner.py`（設定側）/ `srg_probe.py`**。**(0) の `rt` = `test_newton_clip_routing` と合わせて機構が閉じる** ⇒ B0/B1 の live path は `gripper_dynamic=True`（`:483` 設定・`:484` assert）で **gripper は既に servo 駆動、kinematic 上書きが残るのは arm のみ** — **CONCUR**。⇒ **ruling ② ① の cutover 対象は arm に絞られる**（scope 縮小として採択）。

**(5) 新実測②（cable 4 FAIL は drive でない）= CONCUR。** 3 因子の *drive realization* 軸に載らない ⇒ 上記 (3) の **CABLE-SEED 軸**が正しい所属。⭐**一般則**: 3 因子基準は **robot drive** の分類器であって、cable/object 書込はそこに載せず **CABLE-SEED** で裁く（軸の取り違えは class の誤付与を生む）。

**(6) %12 の自己申告への応答**: 初稿が `:1838`/`:8436` を「未 ruled」としたのは **caller closure に既に含まれていた**という自己申告 — **私の訂正 #25 と同型**であり、**closure 帰属を先に判定してから残余を提案する**という改稿方針は正しい。⇒ 本節も同方針で書いた（各照会に対し **まず既存裁定への帰属**を判定し、真に新規な分のみ class を付けた）。

**verdict**: (1) **NO・既裁定（§14.23-b/-c）のまま・bind しない**（label は `restore_state_snapshot`・caller に B0/B1 無し）/ (2) **§14.23-c 軸で ADAPT**、component 別 class 4 種を付与（新軸なし）/ (3) **CABLE-SEED が該当軸**、適用 4 条件 + count 変化ゆえ宣言経路必須。新実測 ①② とも **CONCUR**（① は cutover を **arm 限定**に縮小）。⚠**訂正 #26** = `rt` alias の誤読により §14.24(1) 訂正 #15 の *根拠*（B0/B1）を撤回（class は 3 consumer で再確認）。

### §14.26-d 照会(1) 再裁定（file 限定形）= `test_newton_clip_routing.py :: physics_step` の arm 上書き 6 FAIL（v2.30、2026-07-20 20:4x JST — %12 の citation 訂正 20:33 を受けた再実測・再裁定。⚠**§14.26-c(1) は別 site を裁いていた**〔file 名欠落による〕ため本節が正）

**(0) 実測（committed blob 直読 @ probe c48 相当）**: `test_newton_clip_routing.py` `def physics_step`（`:1790`）の **mujoco 枝** `:1821-1833`:
```
n = 2 * JOINTS_PER_ARM
phys_jq  = state_0.joint_q.numpy();  phys_jqd = state_0.joint_qd.numpy()
if gripper_dynamic:            # R-S6.6 CHANGE 1（code 自身の comment）
    phys_jq[_ARM_OVERWRITE_IDX]  = fk_state.joint_q.numpy()[_ARM_OVERWRITE_IDX]   # :1827
    phys_jqd[_ARM_OVERWRITE_IDX] = 0.0                                            # :1828
else:
    phys_jq[:n]  = fk_state.joint_q.numpy()[:n]; phys_jqd[:n] = 0.0               # :1830-1831
state_0.joint_q.assign(phys_jq);  state_0.joint_qd.assign(phys_jqd)               # :1832-1833
state_0.clear_forces(); solver.step(...)
```
`_ARM_OVERWRITE_IDX = [i for i in range(2*JOINTS_PER_ARM) if i not in _GRIPPER_COORDS_BOTH]`（`:1776`）。
⇒ **per-physics-frame の arm joint 空間 kinematic 上書き**（速度は 0 固定）。**joint-space だが reset ではなく step loop 内の drive** ⇒ **class = DRIVE**（RESET でも OFFLINE でも CABLE-SEED でもない）。⭐**これは ruling ②① の cutover が置換すべき当の site。**

**(1) ⭐ 新実測① の完全裏付け（code 自身の comment が述べている）**: `gripper_dynamic` 真枝の comment 逐語「the gripper is a POSITION actuator (S6_GRASP) -> overwrite **ONLY the arm coords** ({0-5,14-19}); leave the gripper coords ({6-13,20-27}) **DYNAMIC so the servo drives them via `control.joint_target_pos`**」。⇒ **%12 narrowing ①（gripper は既に servo・kinematic 上書きは arm のみ）を code 逐語で CONFIRM**。cutover 対象の **arm 限定**を採択（§14.26-c(4) の CONCUR を本 site の実体で裏書き）。

**(2) ⚠ ただし `gripper_dynamic` の 2 枝は 3 因子上「別 triple」= 別 class（私の新規指摘）**
- **真枝（B0/B1 の live path）** = arm-only 上書き ⇒ cutover 対象は **arm のみ**。
- **else 枝** = `phys_jq[:n]` で **arm + gripper を丸ごと**上書き（S6.6 前の legacy 挙動）⇒ **narrowing ① は此枝に及ばない**。**別 class として扱い、live consumer が無ければ retire、在れば独立に cutover 範囲を定める**こと。⭐§14.26-a の 3 因子基準（callsite × effective backend × **drive realization**）を素直に適用すると、**同一 callsite でも drive realization が違えば別 class**になる — 本件はその最初の実例。

**(3) ⭐ 照会への回答 = 「bind は authorship としては YES / scope 限定としては NO」**
- **YES（編集は cutover が行う）**: 当該 site は ②① が置換すべき arm drive 本体であり、**B0/B1 はこの site を通る**（`policy_route_runner:378` → 消費 `:545`/`:635`）。⇒ **cutover の編集対象に含めるのは正しい。**
- ⛔**NO（B0/B1 closure に scope を閉じられない）**: `physics_step` は **clip_routing 内の中心 step 関数**であり、同 file 内に **多数の他 consumer**（`:2038`/`:2112`/`:2332`/`:2864`/`:2929`/`:3103`/… 多数）が在る。⇒ **B0/B1 closure ⊊ `physics_step` consumer closure**（訂正 #25 と同じ包含関係）。**編集は共有 path に落ちる。**
- ⇒ **裁定**: 当該 6 FAIL は **§14.26 の `MIGRATION_PENDING`（DRIVE）**のまま。**B0/B1 cutover は「最初に acceptance を示す consumer」**であって、**当該 site の release 条件ではない**。**同一 bundle で `physics_step` の他 consumer を列挙し、再検証するか明示的に fence する**こと。**列挙なき部分 cutover は不可。**
- ⭐**一般則（本 arc で 3 度目の同型ゆえ定式化）**: **編集 scope ≠ 解除 scope。** 共有 path を編集する cutover は、**解除は per-consumer（§14.26-b）でも、検証は編集が届く全 consumer に対して**要る。

**(4) 影響範囲の確認**: 照会(2)(3) と訂正 #26 は本 re-target の**影響を受けない**（%12 の理解に CONCUR）— (2) は `:8399` の episode 境界 block、(3) は `:7896/:7960` の cable seed、#26 は `rt` alias の解決であり、いずれも `physics_step` の 6 FAIL と別 site。§14.26-c(1) は **`restore_state_snapshot` についての裁定としては有効なまま**（そちらの結論 = 既裁定・bind しない、は不変）。

**verdict**: 対象 = `test_newton_clip_routing.py :: physics_step` `:1827/1828/1830/1831/1832/1833`（全 mujoco 枝・VBD 枝 `:1836-1842` は FAIL 0）。**class = DRIVE / `MIGRATION_PENDING` 維持**。**bind = authorship YES・scope 限定 NO**（B0/B1 は最初の acceptance consumer であって release 条件でない／同 bundle で `physics_step` の全 consumer を列挙・再検証 or fence）。**新実測① を code 逐語で CONFIRM**（cutover = arm 限定）。⭐**新規指摘 = `gripper_dynamic` 2 枝は別 triple ゆえ別 class**（else 枝に narrowing ① は及ばない）⚠**〔SUPERSEDED v2.31 §14.27(4)(1): 「別 triple」は事実だが **class の差ではなく acceptance evidence の差**。class は 6 行すべてで単一 `DRIVE`（extent 差 ≠ kind 差）。「else 枝に narrowing ① は及ばない」の部分は有効。〕**。一般則「**編集 scope ≠ 解除 scope**」を追加。

### §14.27 `physics_step` 全 consumer 列挙への裁定 = **class は単一（DRIVE）・consumer 別分割は却下・fence は 2 種を別立てで必須** + ⚠**訂正 #27**（v2.30 の retire 条件節が反証不能だった）+ ⭐**%12 else 枝 count の訂正**（`main:8067` は else 枝に入らない）+ ⭐**Z-Check 移管への hard 条件 [H-1]**（v2.31、2026-07-20 21:0x JST — %12 材料 c52 `46a59e7831` / sha256 `068b51dda8aee047` 〔材料のみ・class 選択なし〕+ %12 message 20:59 への p5 裁定。全実測は c52 の committed blob 直読）

**0. 測定基準の注記 — ⚠ 本節は worktree から測っていない**

- 測定時点で worktree HEAD = `ddbae19e0f`（branch `rlrk/optE-s2-substrate-swap` = WMSO D1.1-B 系）であり、**(d) arc の `probe/pd1-arm-pd` ではない**。c52 は HEAD の祖先でなく（`merge-base` = `0f39f7b598`、2026-07-19）、charter も worktree に存在しない。
- ⇒ 本節の全実測は `git show 46a59e7831:<path>` = **producing commit 直読**。[[feedback-verify-on-disk-at-the-producing-commit-not-at-head-2026-07-14]] / [[feedback-pin-over-committed-state-not-dirty-tree-verify-in-worktree-2026-07-19]]
- ⚠ **%12 への注意**: 共有 tree が別 branch に切り替わっている。**本版の適用・bank は `probe/pd1-arm-pd` 復帰（or `git worktree` 分離）後**に行うこと。p5 は branch を切り替えない（他 pane が live）。

**1. c52 の検証結果（採用 / 訂正の内訳）**

artifact sha256 = `068b51dda8aee047a0261b21d6c5f389655f85054f36117aa310d5ff33bef95d` — **banked object 上で exact 一致 ✓**（p5 独立算出）。

| c52 の主張 | p5 独立検証 | 判定 |
|---|---|---|
| §5 分岐構造: `:1813` default `False` / `:1823` 分岐 / `:1827-1828` arm のみ / `:1830-1831` 全 DOF / `:1832-1833` 共通 sink | 逐語一致 | ✅ ADOPT |
| True-setter = tncr `:3063` `:3262` `:3721` / `srg_probe.py:193` | 逐語一致（閉クエリ `gripper_dynamic` 全 hit を印字） | ✅ ADOPT |
| True-setter = `policy_route_runner.py:506`（assert `:507`） | ⚠ **実体は `:483`（assert `:484`）**。`:506` は `z_top = float(cmeta["next_clip_z_top"])` で無関係。c51/c52 とも同じ | ⚠ **citation 訂正**（事実は真・行番号のみ 23 行ずれ。§14.26-d の p5 側実測 `:483-484` が正しかった） |
| 帰属は enclosing def でなく `scene_info` の provenance で決まる | 同意。ただし **provenance だけでは足りない**（下記 2） | 🔶 PARTIAL |
| §6 rebind / untracked consumer | §4(3)(4) で裁定に採用 | ✅ ADOPT |

**2. ⚠ %12 message 20:59 への訂正 — else 枝の到達条件は「連言」である**

%12 は「`gripper_dynamic` を立てない entry point が 5 つ・継承 helper 込み計 12 callsite が else 枝を通る」とした。**「立てない」は必要条件であって十分条件ではない。** else 枝の到達条件は

> **¬set(`gripper_dynamic`) ∧ `scene_info["solver_backend"] == "mujoco"`**

という**連言**である（`physics_step:1816` が backend で先に分岐し、6 FAIL 行は mujoco 枝の内側にしか存在しない。VBD 枝 `:1836-1848` は `update_kinematic_bodies` + `clear_forces` + `collide` + `solver.step` のみで joint 書込 0）。

⭐ **`main:8067` は第 2 連言肢で落ちる（構造的排除、indent で確定）**:

- **結合**: `:8086` `solver_backend = args.solver_backend` → `:8156` `build_scene(solver_backend=solver_backend)` → `:1708` `"solver_backend": solver_backend` ⇒ **main 局所値 = `scene_info` の値**（`:1049` docstring も「Uses the LOCAL `solver_backend` … so the guards can't diverge」と明記）。乖離経路なし。
- **構造**: `:8206` `if solver_backend == "mujoco":`（indent 4）→ `:8207-8249` の if/elif/else 連鎖（indent 8、body 12）→ **`:8250` `return`（indent 8 = 連鎖の**外**・`if` の**内**）** ⇒ **mujoco の全 dispatch 枝が return する**。fall-through 経路なし。
- ⇒ main 自身の loop（`:8281` recorder / `:8294` `physics_step(...)`）に到達するのは **`solver_backend != "mujoco"` のときだけ** ⇒ `physics_step` は VBD 枝 `:1836` を通る ⇒ **6 FAIL 行に一切触れない**。

⇒ **else 枝の entry point は 5 でなく 4**（`_run_mujoco_ik_motion_smoke:2817` / `_run_mujoco_episode:7525` / `_run_mujoco_tracking_smoke:7761` / `_run_mujoco_cable_settle_smoke:7820`）。**`main:8067` の 1 callsite は除外**。
継承 helper（`ik_move_both:1958` / `hold_position:2106` / `do_p1_grasp:2227`）の帰属にも**同じ連言 intersect が要る**（呼び元が main 側 loop なら同様に落ちる）— これは測定レグ ⇒ **%12 court**。p5 は**除外が確定した 1 件のみ**を主張し、残 count（12 − ?）は主張しない。

⛔ 失敗の型 = **述語の連言のうち 1 肢だけで数えた**。[[feedback-independent-confirmation-must-cover-every-conjunct-2026-07-14]] / [[feedback-enumerate-predicate-legs-times-sides-not-failure-rows-2026-07-14]] と同型。

**3. ⚠ 訂正 #27（私の誤り）— v2.30 の retire 条件節が反証不能だった**

v2.30 §14.26-d で私は「else 枝は **live consumer 無なら** retire」と書いた。%12 は「到達可能性は測ったが exercise は未測定」と正しく留保した。**留保が正しく、条件節を書いた私の側が誤っている**:

- 「live consumer 無」は**否定の全称命題**であり、静的測定では satisfy も refute もできない。**RUN レグを要求する条件を、RUN が CLOSED の場面で解除条件に据えた** = 実行不能な gate を書いた。
- 静的に判定可能・かつ**偽を示せる**形に締め直す:

> **[R-E] else 枝 retire 条件** = `¬set(gripper_dynamic) ∧ backend=="mujoco"` を満たす callsite が **静的に 0**（閉クエリ + 継承 helper の呼び元 intersect まで含む）。

- 現状 = **4 entry point が該当 ⇒ 0 でない ⇒ retire 不可**。**exercise 測定を待つ必要はなく、現材料だけで決着している**（%12 の留保は誠実だが、結論を左右しない）。
- ⭐ **一般則（追加）**: **解除条件は「それが偽であることを示せる形」で書く。**「〜が無ければ解除」は、*無いことを測れる閉クエリ*を併記しない限り gate にならない。[[feedback-a-test-that-cannot-come-out-differently-is-not-a-test-2026-07-14]] の gate 側の双対。

**4. 裁定 — 照会「単一 class か / consumer 別分割か / fence か」**

**(1) class = 単一 `DRIVE` / `MIGRATION_PENDING` 維持。consumer 別分割は却下。**

- class の述語は「**この行は robot joint state を kinematic に書くか**」であり、`:1827/:1828/:1830/:1831/:1832/:1833` の 6 行すべてで、全 consumer 共通に**真**。`gripper_dynamic` が変えるのは**書込範囲（extent）**であって**種別（kind）**ではない。§14.14 の class は kind の上に定義されている。
- extent 差で class を割ると、**remediation 義務が同一（→ delete / actuator 化）な 2 class** ができる。これは差のない区別であり、実質は **per-consumer 免除の入口**になる。§14.26 で (b) 枝分割を却下した論法（共有 symbol を枝で割ると realization が再複製され、mujoco 枝の kinematic が恒久化する）が、ここでも同形で効く。
- ⚠ **v2.30 §14.26-d の「2 枝は別 triple ゆえ*別 class*」は本節で narrow する**: 3 因子基準（consumer callsite × effective backend × robot drive realization）が別 triple を与えるのは**事実**だが、**triple の差は acceptance evidence の差であって class の差ではない**。triple は「どの証拠がどこまで覆うか」を決める道具であり、class 分割の根拠にしない。⇒ 当該箇所に SUPERSEDED 注記を in-place で付す。

**(2) bind = 全 consumer。B0/B1 への部分 bind は不可。**

- 実測が pN 留保を支持: B0/B1 は外部 5 callsite 中の **1**（`policy_route_runner.py:730`）、同 module の **54 callsite は B0/B1 経路に属さない**（`_run_mujoco_grasp_route` だけで 35）。
- **「B0/B1 closure ⊊ symbol closure」の 3 例目**（§14.26-b 訂正 #25 と同型）。⇒ **列挙なき部分 cutover 不可**は維持。

**(3) fence は「class の代わり」ではなく「class に加えて」必須。しかも 2 種を別立てにする。**

- **F-α identity fence（rebind に対する健全性）**: §6 の `r_fc0_c2_smoke_77.py:69` `_ops = T.physics_step` → `:83` `T.physics_step = _pp` は、**AST 静的解決と runtime 実体を乖離させる**。Layer 8 は**呼び出し側 sink のみ**を見るため **rebind sink を持たない** ⇒ guarded symbol の定義を検証しても、**走る物を検証していない**。
  - ⇒ guard 契約に「**guarded symbol への module 属性代入（`<mod>.<sym> = ...`）を sink として検出**」を追加する。これは class 問題ではなく **guard の健全性欠陥**であり、class をどう付けても消えない。
  - ⭐ **一般則（追加）**: **静的 closure は rebind に対して健全でない。symbol を守る guard は、その symbol の *束縛* も守らねばならない。**（[[feedback-verify-at-the-delivery-surface-not-the-source-variable-name-2026-07-19]] の同族 — delivery surface は「定義」ではなく「束縛」側にもある）
- **F-β closure fence（untracked live consumer）**: untracked な実行可能 consumer は **pin closure の外**にあり、**freeze→verify→bank の exact-sha 契約が及ばない**（誰も pin できず、誰も再検証できない）。「tracked でも quarantined でもない**第三状態**」を残さない。
  - ⇒ 各 untracked consumer を **(i) track する / (ii) 削除・隔離する / (iii) 実行不能の証拠つきで closure 外に登録する** のいずれかへ disposition する。**無記載のまま放置は不可。**
  - %12 は §9 で「下請けの閉クエリが git(tracked) に閉じており filesystem を覆っていなかった」と自己申告している。その規律（**不在の閉クエリは root だけでなく "追跡状態" も覆う**）を **本 charter の常設規律に格上げ**する。[[feedback-absence-claims-need-closed-query-and-moving-tree-provenance-2026-07-18]]

**(4) ⛔ escalation — untracked pin wrapper は (d) arc に黙って吸収しない**

- `_pp`（`r_fc0_c2_smoke_77.py:72-81`）は `_PIN["active"]` の時に `jq[ARM_Q:]` / `qd[ARM_Q:]` と `md.qpos[ARM_Q:]` / `md.qvel[ARM_Q:]` を 0 埋めし `mujoco.mj_forward` を適用する。`ARM_Q = 2*T.JOINTS_PER_ARM`（`:57`）ゆえ slice `[ARM_Q:]` は**両腕を除いた cable 側** = **clip-retention pin 系**。
- ⇒ **Rs 2026-07-19「kinematic 完全削除（pin 含む）」directive の射程内**。§14.10 removal inventory の対象候補（inventory 本体の編集は %12 の sweep レグと合流させる）。
- ⚠ p5 は「**live である**」とは主張しない（`_PIN["active"]` gate + exercise 未測定 + 中間 module の backend 未確定）。**dead / live のどちらでも F-β の disposition 義務は同じ**ゆえ、**裁定は現材料で可能**。
- ⇒ **Rs surface 項目として登録**。live 判定は要求しない（要求すると RUN レグを開けることになる）。

**5. ⭐ Z-Check 移管（Rs 裁定 ②）への hard 条件 [H-1] — 本節の副産物**

§2 の構造判定は、Rs 裁定 ② の移管設計に直接効く新事実を与える:

- **現 Z-Check gate は VBD 枝の上に載っている**: `recorder.check_penetration()` `:8452` と `[ZCHECK]` `:8456` は**いずれも enclosing def = `main:8067`**、すなわち `:8250 return` の**下流**＝**非 mujoco 経路**。`CLAUDE.md:271` の名称「Fingertip Z-Check Gate（**Newton VBD**）」は構造と一致している。
- ⇒ 移管は **substrate 境界をまたぐ port** であり、**現 host loop は VBD 退役でそのまま消える** ⇒ 移管先で instrument を**新規配線**する必要がある。**6 FAIL 行を引き継ぐ話ではない**（＝ 移管は DRIVE remediation と絡まない。良い報せ）。
- ⚠ **ただし移管先は 6 FAIL 行の consumer になる**。ここで gate の識別性が壊れる:
  - `check_penetration` が読むのは `_zheight_frames` の `left/right_finger_z`、その出所は `state.body_q`。
  - **mujoco 枝 × `gripper_dynamic=False`**: `phys_jq[:n]`（gripper 込み全 DOF）が毎 substep FK で上書きされ、mujoco は joint_q から body を pose する ⇒ **fingertip z は FK 指令の関数**になり接触物理の関数でなくなる ⇒ **貫通述語が物理由来では偽になり得ない = gate が識別しない**。
  - **mujoco 枝 × `gripper_dynamic=True`**: gripper coords は dynamic に残る（servo が `control.joint_target_pos` で駆動）⇒ fingertip z は物理由来 ⇒ **識別する**。
- ⇒ **[H-1]（移管の hard acceptance 条件）**: 移植した Z-Check は **`gripper_dynamic=True` の path 上でのみ有効**とし、**gate 自身の入口で fail-closed に assert する**（runner 側の assert に依存しない — runner は差し替わり得る）。
  - **H-1 を欠く移管は [[feedback-a-gate-validated-under-the-bug-is-validated-by-the-bug-2026-07-15]] の純粋形**（**別様に出得ない test**）になる。
- ⚠ 併せて、instrument の既知欠陥 2 件を**逐語移植しない**こと: (i) `:585-586` `if not self._zheight_frames: return None` = **fail-OPEN**（データ無で gate が沈黙する）、(ii) `:591-600` の `found` 短絡により `max_penetration_mm` は **frame ごとの初出 1 件の最大**であって真の最大ではない。
- 本 [H-1] は §14.25 の 4 acceptance 条件への**加算**であり、既存条件を置換しない。

**verdict**: **class = 単一 `DRIVE` / `MIGRATION_PENDING` 維持**（**consumer 別分割 = 却下**。extent 差は kind 差でない）。**bind = 全 consumer**（B0/B1 部分 bind 不可・「B0/B1 closure ⊊ symbol closure」3 例目）。**fence = F-α〔rebind sink を guard 契約に追加〕+ F-β〔untracked consumer を 3 択で disposition〕の 2 種を別立てで必須**（class の代替ではなく加算）。**escalation = untracked pin wrapper を Rs surface 項目に登録**（live 主張はしない）。**⚠ 訂正 #27 = 「live consumer 無なら retire」を静的判定可能な [R-E] に差替え ⇒ else 枝 retire は現材料で不可と確定**。**⚠ %12 count 訂正 = `main:8067` は else 枝に入らない**（entry point 5→4、残 count は %12 court）。**⚠ citation 訂正 = `policy_route_runner:506` → 実体 `:483`**。**⭐ 新規 = Z-Check 移管の hard 条件 [H-1]**。⭐ **一般則 2 件追加**: 「**解除条件は偽を示せる形で書く**」/「**guard は symbol の束縛も守れ**」。

### §14.9 sequencing
(1) 本 charter bank + %12 readback →(2) probe v0.9（no-kinematic 化）+ prereg v1.4 凍結 →(3) C′ 走行（gains + transit legs + video）→(4) **production 削除 landing 計画**（L3 chain + Rs sign-off — 削除 diff = A/B 全 sites + helpers + Layer 8 改訂）→(5) W-b 再記録（landed 基盤上）→(6) #18 PD 再測。pin 置換（§14.10）は arm 系（%12 a-1 先行実装）と並行で p5 設計 → v0.9 に合流。

### §14.10 pin/weld/attachment 全廃 + 物理保持置換設計（v2.1、pN 経由 Rs 正式 directive 13:34/14:06 — p5 court）
- **removal inventory（active 実行 path から除外、code は歴史 evidence として保存）**: `_maybe_activate_c1_pin` / `authorize_clip_pin` / capture→eq activation chain / weld eq 書込（eq_active/anchor）/ cable・finger attachment/bypass helper 全般 / arm joint/body direct-state drive（§14.1-2 と同体）。**dirty shared-tree 規律**: 勝手に削除せず owner が対象 hunk/path を申告（Rs 指示逐語）— sweep 列挙 = %12、p5 は設計面の除外対象を本 inventory で宣言。
- **banked (d-a)/(d-b) arc = 歴史 evidence 化・実行候補から除外**（two-key/prereg 記録は保存。§S4.7 training-ready 式 = superseded → 新式 = 物理保持の独立 verify を含む形で再定義、記録 custody = %12 bank + p6 + LEDGER/DDR。RS71 §0#5・§4 の premise 改訂 = Rs 専権 doc ゆえ Rs 授権の records pass を要請）。
- **置換原理 = C1 保持を物理から**: ⚠ 正直な設計前提: banked 実測は「pin 無しでは C1 は保持されない」（RS71 §4 planar-bender 境界、Rs DECISION B2 2026-06-25）— 本 directive はこの境界の**克服を命じる**ものと解する。lever 3 系統: **(L1) cable model の水平曲げ compliance 付与**（model 改訂 — 実測境界からみて必要になる公算大。banked cable 設計に触れる = design gate、方向は Rs 発令済）/ **(L2) clip groove 幾何**（保持 lip・深さ — /geometric-design gate）/ **(L3) 振付の張力管理**（W-b 再記録に「C1 を横に引かない」経路を焼き込む）。
- **P-PIN feasibility probe（lever 選択の evidence、設計先行）**: 現 model で着座 cable の C1 逸出力・方向を実測 → 水平 compliance を sweep して保持閾値を同定 → L1 必要性を判定。軽量・**HALT 例外 class**（下記）。
- **HALT 意味論（p5 読み、pN confirm 待ち 1 点）**: 「置換+独立 verify 完了まで新規 sim/run/training/production claim = HALT/fail-closed」の例外 = **置換の検証走行そのもの**（P-PIN/v0.9 probe = 置換 process の一部）。それ以外の運用 claim = 全 fail-closed。
- **video 標準要件（Rs 14:0x ×2）**: 今後の全 video leg は**常にアームとハンドを frame 内に表示**（cable/clip close-up 単独 disallow。transit clearance video・C′・W-b 再記録 video に適用。既納 r0 と r1/r2 レンダは要件適合を %12 が確認、不適合なら再レンダ）。

**§12.2-R readback 完（v1.6、12:30）**: prereg v1.1 凍結 `879df7945a` の §3 Declared bands 表を on-disk 照合 = message と全 5 項一致、p5 独立検算で **全 ACCEPT**: ①較正 band 0.06+5%·predicted（hold sag ≲0.04 基礎と整合・罠実証 0.007 vs 0.758 = catch class を桁判別）②ε_pen 3mm（正常貫通 1.1mm と teleport 交差を分離・GLOBAL min = spec の保守的上位集合）③Δv max(2×R0b 同 frame, 0.01)（scale-free + floor、R0b 先行順序確認）④M-6 48frame/15mrad report-only（v1.4-⑥ 一致）⑤L-P1 = |q−ctrl| + `max|ctrl−intended|≤1e-9` cross-check・R3 のみ intended 比（**§12.1 ⛔条件 discharge + R1/R2 配線 bug も封じる強化形として ACK**）。註 1: ①の band class = stream 同一性/粗配線の較正であり frame-exactness は A-2/A-6 が担う（band を frame offset 検出に読み替えない）。**6 走行（R4 exploratory 込み）開始 OK**。⚠**12:35 SUPERSEDED（Rs review v3 §7-7）**: 本 GO は v3 の gate（凍結/走行 = v1.6 bank + prereg v1.2 凍結後）に先行して発行されたため無効 — 走行保留、band ACCEPT 自体は有効のまま（v1.2 凍結時に継承）。

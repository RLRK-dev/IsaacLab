---
node_id: T-ROOT-Kinematic-Pin-Complete-Removal-20260719
node_name: kinematic / pin 完全削除 — arm-control remediation task (d)
goal: "【2026-07-21 Rs 裁定 B で範囲縮小】active 実行面から kinematic による物理バイパスを除去し（⛔ただし clip-retention pin = クリップのケーブル固定 は Rs 許可の例外として除去対象から外れる） physics-faithful な制御へ置換して、RS71 §0 不変前提 #3 (DiffIK-only) / #5 (no-kinematic-trick) が機械検証で成立する状態にする。"
goal_verification: |
  (すべて既存 SSOT に接地。本 node は新しい acceptance を発明しない)
  1. Layer 8 canonical census = 0 — F3 拡張後の all-root scan (全 thread_isaac_lab Python root) 基準。
     ⚠ 現在地 = 35 (A 27 + D aerial 5 + skills-snapshot 3)。旧 restricted-root 基準の「128→125」は別 measurement surface。
  2. guard が fail-closed (既知=WARN の baseline 廃止済、scripts/validations/check_control_method.sh)。
  3. 各 chunk が two-key (機構軸 p5 + 証拠軸 pN)。片軸 PASS は充足でない。
  4. 各 stage が charter §6 の gate を通過 (L3 chain + Rs sign-off + video leg)。
  5. landing / HALT 解除は本 goal に含まれない (別 GO)。
status: IN_PROGRESS
parent_node: T-ROOT
children_nodes: []
dependencies:
  precedent: []
  blocker:
    - "DDR #25 carry ①: Z-Check gate の env7-mujoco 移植が未実装 (VBD retire は移植検証後)"
    - "DDR #25 carry ②: B0/B1 旧 artifact = HISTORICAL / NOT_COMPARABLE ⇒ fresh 再取得必須"
    - "DDR #25 carry ③: CLAUDE.md :271 / :85 は移植検証後に Rs 承認で更新予定・現在未更新・CC 編集不可"
    - "DDR #26: P0 substrate defect (隠れ綱引き) — banked evidence の継続利用可否"
session_history:
  - id: T-ROOT-Kinematic-Pin-Complete-Removal-20260719#s1
    status: active
    started_at: 2026-07-20T20:01:09+09:00
    note: "Rs 承認 (node 作成 + 起動、2026-07-20) により起票。[DEFINE] = 00-Project-Management/node-proposal-T-ROOT-Kinematic-Pin-Complete-Removal-20260719.md @ 14a891d256。既往 c4-c48 は §3 adopted_existing_arc provenance であり本 session の成果ではない。起票時点 = step2 CLOSE / step3 docs-records-only OPEN。"
created: 2026-07-20T20:01:09+09:00
last_updated: 2026-09-20T09:00:11+09:00
spec_version: LTM-1 v1.2
---

# T-ROOT-Kinematic-Pin-Complete-Removal-20260719 — task (d) kinematic / pin 完全削除

## 0. 起票の経緯

**IN_PROGRESS。** Rs 前提「**sim は現実世界・kinematic 完全削除 (pin 含む)**」(2026-07-19。⚠**§5-A で範囲縮小済 — 本行は起票時の経緯であって現行前提ではない**) に発する arc を、
pN (T-ROOT-OPS-SUPERVISOR-CODEX) の NEST 整合裁定 (2026-07-20 13:02) に従って node 化したもの。

裁定の骨子 = 本 arc は post-07-19 の新 task で **独立 goal・多 session・repo 横断 scope・HALT/acceptance 条件・
p4/p5/pN/p6 の分業**を持つため、LEDGER 行 + DDR #25 だけでは **構造的に不可視**（cascade 判定が参照できない）。

⚠ 対照: `T-ROOT-RS-TECH-LEAD` は **role label であって node ではない**（同裁定）。本 node は role の起票ではない。

## 1. 責任分離（lane）

- **design owner:** ⭐**p11 ARM-CONTROL-DESIGN (Rs 指定 2026-07-21 12:5x「新規 CC を owner に」採択・brief `ARM_CONTROL_DESIGN_ROLE_BRIEF_p11_20260721.md` @ `2887037c9f`・p5 同型の control-method 設計番人)**。任務 = ①前向き制御設計 (p0 実装本体・裁定 A) ②§14.27 bank 可否。〔経緯: p5 は 07-20 に (d) arm-control charter 全体を剥奪 (memory `project-p5-scope-narrowed-to-skill-detail-2026-07-20`:20)・「後継 = Rs 指定待ち」を本裁定で **p11 に確定**。07-21 の name-only 改名 (VT-DESIGN→SKILL-DETAIL-DESIGN) が誤りだった件も本 designation で解消〕。charter `ARM_CONTROL_REMEDIATION_D_CONTROLDESIGN_VTDESIGN_20260719.md` (p5 authored・p11 が supersede 可否を判断)
- **build / execute (実装):** p0 IMPL-BUILDER（Rs 12:5x reorg で p4 = まとめ役 へ移行・旧 worktree `probe/pd1-arm-pd` は p4 arc の記録）
- **implementation verify:** pZ IMPL-VERIFIER ／ **custody・evidence verify:** pY OPS-SUPERVISOR（旧 pN OPS-SUP-CODEX = 停止）
- **Vault / current-state custody:** p6 PLAN-KEEPER

## 2. means（workstream）

charter `ARM_CONTROL_REMEDIATION_D_CONTROLDESIGN_VTDESIGN_20260719.md` — 現行 **v2.27**（c47 `4dc72baf08`・sha256 `8543c880365b`・p6 実測）の stage 定義に従う。**B0/B1 移管の acceptance 条件 = c48 `bb68cb3c0f`**。〔v2.25 = c42 `01d3011f5e` は superseded〕 identified な workstream:

- **GATE-MIGRATE** — Fingertip Z-Check Gate を env7-mujoco へ移植 → 検証後に VBD copy retire（Rs 裁定 c36）
- **B0B1-MIGRATE** — B0/B1 evaluator を env7-mujoco へ移管（Rs 承認済）・旧 artifact は fresh 再取得必須
- **A-group rewrite** — routing_utils / clip_routing（残 27）
- **D aerial**（残 5）/ **skills-snapshot**（残 3・disposition = DELETE 確定、c27 `bfc35ca87c`）

⚠ **GATE-MIGRATE と B0B1-MIGRATE は別 workstream**（p4 2026-07-20 16:54）。単一 task に畳まない。
⚠ **子 node 化は §3.1 の別 gate**。必要になった時点で再帰適用する（本 node は leaf 起票）。

## 3. provenance — `adopted_existing_arc`

本 node は **既存 arc の採録**。既往作業を session として遡及生成していない（`#s1` = 起票時点）。
既往の実体は以下を参照（node の成果ではなく node 化以前の記録）:

- **chunk chain c4 … c48** — `probe/pd1-arm-pd`（2026-07-20 20:12 時点 tip `bb68cb3c0f` = c48）。
  ⚠ 本 branch (`rlrk/optE-s2-substrate-swap`) には **未着地**
- **Rs 裁定** = c36 `eefad77773`（逐語「1：a 2:承認」）
- **[DEFINE]** = `00-Project-Management/node-proposal-T-ROOT-Kinematic-Pin-Complete-Removal-20260719.md` @ `14a891d256`

## 4. SSOT の分担（二重管理の防止 — pN 裁定）

- **結果・判定の SSOT = `07-Design/00-DESIGN-STATUS-LEDGER.md` の (d) 行 + `§DDR #25` + charter。**
  本 state.md へ複製しない。
- **本 state.md が持つのは lifecycle / goal / pointers のみ。**

## 5. ⛔ authority fence（node 化で一切変わらない）

**source / `[CHANGE]` / RUN / landing / push / training / `CLAUDE.md` 編集 = CLOSED。**
step4 以降は step3 two-key + 別 GO まで不可。**node の起票は実行の許可ではない。**

⚠ R-SEQ = **A-first → affected B0/B1 reacquire → その後 #18 裁定**
（charter §14 TOP PREMISE :3 + §14.9。旧「#18 impl 先行」は SUPERSEDED）。
`#18` は相互作用があるが **GATE ではない**（charter design §0.3）。

## 5-A. ⚠ 2026-07-21 Rs 裁定 B — 本 node の goal 範囲が縮小

Rs 逐語 2 段「**kinematic は使用するなよ**」→「**ただし、クリップのケーブル固定だけは kinematic を使用する**」（適用範囲確認に Rs「ok」）。⇒ **2026-07-19 の「kinematic 完全削除（pin 含む）」を上書き**し、**clip-retention pin 例外が復活**（`RS71-System-Spec-SSOT.md:27` §0#5 の状態へ復帰）。

- **除去対象から外れた** = クリップのケーブル固定 pin のみ
- ⛔**除去対象のまま** = 腕関節角の直接書込 / 指の kinematic close / FK→physics の body 複写（`update_kinematic_bodies`）/ weld・attachment
- ⇒ **census 35 の各サイト class を再判定する必要**がある（**class 裁定 = 設計軸**。本 node の custody では行わない）
- custody = `STEP43_CONTROLLER_REALIZATION_BASELINE_RSTECHLEAD_20260721.md` sha256 `f1ea5e5a0109` @ c69 `183c1bb5dc`
- ⭐**rule-file 反映 = `35029056bd`**（2026-07-21 02:05・`CLAUDE.md:72`・p4・Rs 承認）。⚠p4 relay の前提「:72 は pin も禁止していた」は **on-disk と不一致**（:72 は 07-19 07:32 以降ずっと「唯一の認可例外 = clip-retention pin」を保持・directive 期間中 無変更）⇒ 本 commit = 復元ではなく **明確化**。✅**逐語の出所 = RESOLVED**（p4 回答 02:34 + c73 `23c320850e`・p6 verify 済）— **U1（01:3x「…ケーブル固定だけは…」）と U2（02:0x「これは変更。…ケーブルクランプのみ…」）は別時刻の 2 発話で両方 Rs 逐語**。U2 は p4 の現 context に現存ゆえ provenance が強い。⚠U2 は p4 が **pN の未 commit 編集**を引用提示した上での応答（指示自体は引用対象から独立・U1 と同方向）。p4 は LEDGER 削除要請を **撤回**。⚠p6 の論拠「クランプは gripper 動作の語」は **識別力なし**（banked 側「ケーブル固定」も同 cell で同じく gripper 動作を指す）= 自己訂正済。現行 :72 = `c2bcde7428`。詳細 = LEDGER §governance 裁定 B 項（§4 に従い本 state.md へ複製しない）

⚠⚠**node ID `…-Kinematic-Pin-Complete-Removal-…` の「Pin-Complete」部分は、本裁定により実態と食い違う**。ただし **NEST §1 で node ID は永続**ゆえ改名しない。**ID を goal の要約として読まないこと** — goal は上記のとおり縮小済。

## 6. 現在地（起票時点 2026-07-20 20:01）

**step2 = CLOSE / step3 = docs-records-only OPEN**（pN final readback 16:52:34）。
step3 で許可されるのは manifest v2.x + ruled-class 差替 prereg の authoring / bank / readback のみ・
disposition / status だけ・**census = 35 固定**。

## 7. UR15-B controller 適合工程 — pointer 節（Rs1（人間）Q4 回答 2026-09-14「独立nodeにしない。」）

**起票 = p6 PLAN-KEEPER 2026-09-16 17:58:18 JST（§1 custody）・起案 = p4 RS-TECH-LEAD kickoff item 4 Q4 @ `42848e4f4c`・Rs1（人間）逐語（custody = p4 transcript `ad899cc6-2451-4364-ba3c-910b67075aa4.jsonl:2361`・09-14 06:00:22 JST・typed・bank = kickoff `P4_MOUNTING_C-2_CHAIN_KICKOFF_20260808.md` 09-14 06:06 節 @ `236410dd84`・p6 再読）**:
「独立nodeにしない。今回の作業はUR15-Bを既存の制御系へ適合させる工程として扱えます。親node内に成果物・担当・完了条件を明記すれば十分です。」
⇒ 本 chunk（DDR #68 の controller 系・p4 が 09-13 22:12 に Q4「DDR #71 の境界 — 本設計 chunk を node 化するか」として問うたもの）は **本 node の chain 内 step**。⛔ §4 のとおり結果・判定の SSOT は LEDGER（#68／#69／#73／#74）— 本節は pointer のみ。命名 = Rs1（人間）／Rs2（=p4/CC）。

### 7.1 成果物と担当（p4 起案・Rs1 要件「成果物・担当」）

| # | 成果物 | 担当 | pointer（p6 09-20 09:00 実測・HEAD `2d2c76416a`・初版 17:58 @ `dc090f7753`） |
|---|---|---|---|
| ① | 設計 v3 `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/P11_UR15B_CONTROLLER_DESIGN_20260913.md` | p11 | 最新 `20281bbf83`（09-20 08:50・§17.9 = 引用行の挿入訂正＋GRASP1 = 入れる・278 行・§17.8 = `e0b2857a50`〔§10 撤回・R0-ii 採用〕・§17.7 = `7427c1764c`・§17.6 = `2743fc4549`・初版 §17 = `dc090f7753`）。「未検証」の札は v3 `:1` のまま |
| ② | D4（姿勢 cap 計器の側別化・wired 2 関数＋print） | 実装 p0／検証 pZ（事前登録 `cb787871f0`・R3 `98d8e63173`） | 着地 `3370f7a872`（09-16 17:48:52・記録 = P0 §8.51 @ `4b328fb025`）・pZ leg 9/9 hold＋R3 静的 hold `ab0ac56f97`（追記 `f6ab51c3ff`）・**p4 受入済 09-16 18:03:56（item 6 @ `bf489e1bb2`・② のみ・controller の完成ではない・R3 数値は #69 の run 内）** |
| ③ | B 記録行（Q2 = B・側別 controller の記録行） | spec p11／実装 p0／検証 pZ | spec = v3 §17.2 @ `dc090f7753`・pZ prereg `aed109d06f`＋row 3′ `e41d0a9304`（条件 (ii) 充足 = p4）・**窓 open（p4 09-16 18:16・item 9 @ `1d42a6f198`）**。**p0 着地 `96e9ece175`**（09-16 18:23:08・+11/−0・blob `84a372439c59`・記録 P0 §8.53 @ `65af36a2bf`）・**pZ leg 済 `e7a62cc114`**（09-20 08:04・静的 rows CONFIRMED・runtime row は #69 まで UNVERIFIED by design・relay 未着）・**p4 受入済 09-20 08:29:02**（item 7 @ `bc741e87fc`・row 7 = runtime AXFIX 値は #69 の run 後に pB が prereg row 7 と比較して閉じる = 受入条件でない・停止札 none・#69 不発火・controller 完成ではない） |
| ④ | R0 静的収束検査（Q1） | spec p11（v3 §10＋§17.1）／作成 p0／独立検証・実行 pZ | spec = §17.1（「収束のみ」を名乗る）・pZ prereg `bf4433bfe6`＋row 1′ `642a9162f0`（条件 (i) 充足 = p4）・**窓 open（p4 09-16 18:16・item 9 @ `1d42a6f198`）**。**p0 着地 `d038e2536f`**（09-16 18:35:54・新 file `r0_convergence_harness.py` +778・blob `1d6b53840028`・記録 P0 §8.54 @ `675241151c`）・**受入保留（p4 09-16 18:44・item 16 @ `6592e12c49`・relay 09-20）**: follow-up (a) 閉包 4 関数（`_never` stub 置換分）を blob から逐語 copy (b) rows 2-5 の拘束値を spec-nominal へ（U0 実測は報告行）・R0-ii 採用時 `pose_only=k`・順序 = p11 §17 行 → p0 follow-up → pZ leg → p4・pZ pre-harness 測定 addendum 3 `dd7cfd18b4`（17/17 収束・負の対照も 17/17 ⇒ 収束 ≠ 正しさ）・p4 読み（item 15 @ `996fb68d93`）: ④ = Q1 射程（収束）・正しさは ⑤・R0-ii は p11 決定・rows 2-5 の出所行 = p11 が §17 に append（m-p4-275） → **follow-up 着地 `ffa612ea33`**（09-20 08:10:06・+491/−196・blob `0163e36e5187`・16 def 逐語 copy・30 global・rows 2-5 = spec 定数 `:931-932`・記録 P0 §8.55 @ `fa0cbdbf74`・R0-ii 未追加（p11 可否待ち）・p11 の行より前に着地・relay 着 m-p18-382）→ **p11 §17.7（出所行）`7427c1764c` 08:23 → follow-up 2 `3cb2a28c36`**（08:34・+154/−53・rows 2-5 = §17.7 の link-centre 形・二経路一致・記録 §8.56 @ `e50014aaa3`・R0-ii と §10 訂正は p11 待ち・受入未・relay 着 m-p18-389）→ **pZ row 4 再 pin 済 `b829c3f066`**（08:39・addendum 5・`:2812` 形・2 経路 1.7e-16 一致・relay m-p18-391・catch = `ffa612ea33` は `:1241` 形 ⇒ `3cb2a28c36` の充足は pZ の読み・p4 の語）・p4 §17.7 同意＋引用行 4 本の挿入訂正返却＋GRASP1 行の問い（`c6c71f4621` 08:40・`3cb2a28c36` の読みは未）→ **p4 follow-up 2 受領・順序逸脱 = 受け入れ可（08:46・item 11 @ `a3334ac777`・pZ 再 pin への条件 1 = literal＋閉形式自算＋dump sha 自測＋開示行）**・次 = pZ R0 leg on `3cb2a28c36` → p4 受入（前提 = p11 の §10 訂正〔**済 §17.8 `e0b2857a50`**・R0-ii 採用〕＋§17.7 引用行訂正〔**済 §17.9 `20281bbf83`**・GRASP1 = 入れる〕）・pZ addendum 6 `3ad4ac4399` = 実行計器 bank（`ffa612ea33` で較正・leg ではない）・p11 の順序 = pZ GRASP1 行 prereg → p0 follow-up 3（GRASP1＋R0-ii）→ pZ leg → p4 受入（p4 の順序確認 未）→ **pZ R0 leg 済 `8b1dcb8218`**（08:54-08:55・187 行・as-landed dump path = 計器 calibration 停止〔loader・停止札〕・relocated-dump path = rows CONFIRMED・bar PASS 収束のみ L 17/17 R 17/17・負の対照 発火せず〔予測どおり〕）・addendum 7 `3ea663a5b4` = p4 条件の開示行・relay 着 m-p18-400・**受入 = p4 の語（未）: (i) p0 の loader 修正→pZ 再 leg か (ii) mesh 横の dump 写しを run 形として受入（数値は (ii) 形）** |
| ⑤ | R1／R1′／R2 静的 legs | pZ | 未（R1 の pin は §17.3 で reference/ へ） |
| ⑥ | reference 一式（Q3） | 取込 p4／照合 pZ | 取込 `e6172b2e3b`（23 file）・照合 `170cbf54a7`（manifest 20/20・4 source 同一・blob==bytes 23/23） |
| ⑦ | まとめ・受入 | p4 | 未（着手 ≠ 受入・Rs1 補足 b） |

### 7.2 完了条件（p4 起案 = DDR #69 の「controller の完成」）

②③ が述語つきで着地・⑤ と R3 と ④ が通過・p4 の受入の一言（④ = 収束・STOP の leg＝Rs1 Q1 の射程／正しさは ⑤ R1・R1′・R2 = p4 読み ② 09-16 18:39・構造不変）。**着手と完成受入は分ける**（Rs1 補足 b）。完成後も #69 の発火は p4 の充足宣言＋視覚 leg（pB／pC）。⛔ 本節は何も解錠しない（route run (2)・#69・D4′・WIP；`:214`/REF_DIR の計器窓は Rs1 Q9「推奨」09-16 18:06 で open = DDR #73 の別窓・run の解錠ではない）。

### 7.3 範囲外（本 step に含めない）

D4′（DDR #74）・`:214` 修正（DDR #73）・09-07 WIP（DDR #72）・acceptance の `REF_DIR` 書換（pZ 所見 `170cbf54a7`・code 1 行・語 = Rs1 Q9「推奨」09-16 18:06 → DDR #73 の計器窓・別窓）。

### 7.4 報告規則（Rs1 補足 a）

計器による停止はコントローラの不成立と区別して報告する（v3 §17.4 の「停止原因の札」）。

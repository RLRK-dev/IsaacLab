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
last_updated: 2026-09-21T01:34:32+09:00
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

**現在注記（Rs1 p19、2026-09-21）:** DDR 68の仕様反映を `04-Specs/UR15-B-Controller.md`・RS71 §0/§1・SOMAへ実施。controller完成宣言と合わせ、仕様反映待ちは閉鎖。#69はpB/pC/pZの3記録が着地し、Rs1の可視範囲の照合も完了（`eval_runs/troot_optE_dapg_wholeroute_scope_20260701/RS1_RUN69_REVIEW_20260921.md`）。p4が `70e6417e46` で停止記録の一致を受理し、p6が `27c9fccb45`（表修復 `d0864a5252`）で反映済み。#69の1回実行の認可は履行済み（LEDGER 行 69 = CLOSED〔認可 履行済〕）。STEP2停止・工程未完・node COMPLETE未成立。〔更新 = Rs1 (p19) の依頼 `m-p19-rs1-current-note-refresh-20260921-001`（2026-09-21 01:33:51）による・受入は再審査していない・他の履歴は維持・p6 09-21 01:34:32 実測〕以下の2/3・pZ未・人間目視待ち等は過去の観測であり、現在状態ではない。工程成功・node COMPLETEは未成立。


**起票 = p6 PLAN-KEEPER 2026-09-16 17:58:18 JST（§1 custody）・起案 = p4 RS-TECH-LEAD kickoff item 4 Q4 @ `42848e4f4c`・Rs1（人間）逐語（custody = p4 transcript `ad899cc6-2451-4364-ba3c-910b67075aa4.jsonl:2361`・09-14 06:00:22 JST・typed・bank = kickoff `P4_MOUNTING_C-2_CHAIN_KICKOFF_20260808.md` 09-14 06:06 節 @ `236410dd84`・p6 再読）**:
「独立nodeにしない。今回の作業はUR15-Bを既存の制御系へ適合させる工程として扱えます。親node内に成果物・担当・完了条件を明記すれば十分です。」
⇒ 本 chunk（DDR #68 の controller 系・p4 が 09-13 22:12 に Q4「DDR #71 の境界 — 本設計 chunk を node 化するか」として問うたもの）は **本 node の chain 内 step**。⛔ §4 のとおり結果・判定の SSOT は LEDGER（#68／#69／#73／#74）— 本節は pointer のみ。命名 = Rs1（人間）／Rs2（=p4/CC）。

### 7.1 成果物と担当（p4 起案・Rs1 要件「成果物・担当」）

| # | 成果物 | 担当 | pointer（p6 09-21 01:34 実測・HEAD `12fb0a7c88`・初版 17:58 @ `dc090f7753`） |
|---|---|---|---|
| ① | 設計 v3 `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/P11_UR15B_CONTROLLER_DESIGN_20260913.md` | p11 | 最新 `cb2a990231`（09-20 15:17:47・§17.23 = §7.2 宣言の記録・`:1` の「未検証」→「p4 完成受入 @ 8dd5188a67」〔§17.5 の規則・取消線残置〕・394 行・§17.22 = `af1765bcee`〔R2 受入の記録・385 行・宣言 item 67 が指す版〕・§17.21 = `90cb5503c0`〔R2 再走行の設計 court 読み・登録 bar == §17.20・計数 27 barred＋報告 2 = 初回の 28 と同集合〕・§17.20 = `7b61c9ae2f`〔§10 R2 の bar 訂正・append-only・exact 5 field → ≤ 1e-12 m・`body_iquat` 行 → 慣性テンソル ≤ 1e-9・`jnt_axis` 写像明記・撤回記録〕・§17.19 = `3427066836`〔R0-iii 受入の記録〕・§17.18 = `c07b4e3b9c`〔R0-iii leg の記録と p11 の読み = 外側・§7.2 宣言前の設計 court 判断は不要〕・§17.17 = `6a73dc3aa4`〔窓 W 受入の記録〕・§17.16 = `4c0811064f`〔R1 受入の記録〕・§17.15 = `ec3b5c29c8`〔R1′ 受入の記録〕・§17.14 = `09e47cb743`〔R0-iii 事前登録の記録・予測は pZ 計器上で成立・RC k=1 = class 非収束・p11 判断不要〕・§17.13 = `8d9fdf3bbb`〔引用行の挿入訂正・式・仕様・予測は不変〕・§17.12 = `40aa696587`〔R0-iii 手首方向 report 行の仕様・body file:line・符号規約・B/RC/NH の予測・反証形・⚠ p4 の語「§17.11」= 17.12〕・§17.11 = `ebbe062874`〔窓 R0 受入の記録・「未検証」印 `:1` は残す〕・§17.10 = `ded9c8ee30`〔R0-ii 149 対の読み・menu の attitude 意味論・17.8 (b) 予測の挿入訂正〕・§17.9 = `20281bbf83`・§17.8 = `e0b2857a50`〔§10 撤回・R0-ii 採用〕・§17.7 = `7427c1764c`・§17.6 = `2743fc4549`・初版 §17 = `dc090f7753`）。「未検証」の札は v3 `:1` で §17.23 により「p4 完成受入 @ 8dd5188a67」へ更新（旧語 取消線残置・`cb2a990231`） |
| ② | D4（姿勢 cap 計器の側別化・wired 2 関数＋print） | 実装 p0／検証 pZ（事前登録 `cb787871f0`・R3 `98d8e63173`） | 着地 `3370f7a872`（09-16 17:48:52・記録 = P0 §8.51 @ `4b328fb025`）・pZ leg 9/9 hold＋R3 静的 hold `ab0ac56f97`（追記 `f6ab51c3ff`）・**p4 受入済 09-16 18:03:56（item 6 @ `bf489e1bb2`・② のみ・controller の完成ではない・R3 数値は #69 の run 内）** |
| ③ | B 記録行（Q2 = B・側別 controller の記録行） | spec p11／実装 p0／検証 pZ | spec = v3 §17.2 @ `dc090f7753`・pZ prereg `aed109d06f`＋row 3′ `e41d0a9304`（条件 (ii) 充足 = p4）・**窓 open（p4 09-16 18:16・item 9 @ `1d42a6f198`）**。**p0 着地 `96e9ece175`**（09-16 18:23:08・+11/−0・blob `84a372439c59`・記録 P0 §8.53 @ `65af36a2bf`）・**pZ leg 済 `e7a62cc114`**（09-20 08:04・静的 rows CONFIRMED・runtime row は #69 まで UNVERIFIED by design・relay 未着）・**p4 受入済 09-20 08:29:02**（item 7 @ `bc741e87fc`・row 7 = runtime AXFIX 値は #69 の run 後に pB が prereg row 7 と比較して閉じる = 受入条件でない・停止札 none・#69 不発火・controller 完成ではない） |
| ④ | R0 静的収束検査（Q1） | spec p11（v3 §10＋§17.1）／作成 p0／独立検証・実行 pZ | spec = §17.1（「収束のみ」を名乗る）・pZ prereg `bf4433bfe6`＋row 1′ `642a9162f0`（条件 (i) 充足 = p4）・**窓 open（p4 09-16 18:16・item 9 @ `1d42a6f198`）**。**p0 着地 `d038e2536f`**（09-16 18:35:54・新 file `r0_convergence_harness.py` +778・blob `1d6b53840028`・記録 P0 §8.54 @ `675241151c`）・**受入保留（p4 09-16 18:44・item 16 @ `6592e12c49`・relay 09-20）**: follow-up (a) 閉包 4 関数（`_never` stub 置換分）を blob から逐語 copy (b) rows 2-5 の拘束値を spec-nominal へ（U0 実測は報告行）・R0-ii 採用時 `pose_only=k`・順序 = p11 §17 行 → p0 follow-up → pZ leg → p4・pZ pre-harness 測定 addendum 3 `dd7cfd18b4`（17/17 収束・負の対照も 17/17 ⇒ 収束 ≠ 正しさ）・p4 読み（item 15 @ `996fb68d93`）: ④ = Q1 射程（収束）・正しさは ⑤・R0-ii は p11 決定・rows 2-5 の出所行 = p11 が §17 に append（m-p4-275） → **follow-up 着地 `ffa612ea33`**（09-20 08:10:06・+491/−196・blob `0163e36e5187`・16 def 逐語 copy・30 global・rows 2-5 = spec 定数 `:931-932`・記録 P0 §8.55 @ `fa0cbdbf74`・R0-ii 未追加（p11 可否待ち）・p11 の行より前に着地・relay 着 m-p18-382）→ **p11 §17.7（出所行）`7427c1764c` 08:23 → follow-up 2 `3cb2a28c36`**（08:34・+154/−53・rows 2-5 = §17.7 の link-centre 形・二経路一致・記録 §8.56 @ `e50014aaa3`・R0-ii と §10 訂正は p11 待ち・受入未・relay 着 m-p18-389）→ **pZ row 4 再 pin 済 `b829c3f066`**（08:39・addendum 5・`:2812` 形・2 経路 1.7e-16 一致・relay m-p18-391・catch = `ffa612ea33` は `:1241` 形 ⇒ `3cb2a28c36` の充足は pZ の読み・p4 の語）・p4 §17.7 同意＋引用行 4 本の挿入訂正返却＋GRASP1 行の問い（`c6c71f4621` 08:40・`3cb2a28c36` の読みは未）→ **p4 follow-up 2 受領・順序逸脱 = 受け入れ可（08:46・item 11 @ `a3334ac777`・pZ 再 pin への条件 1 = literal＋閉形式自算＋dump sha 自測＋開示行）**・次 = pZ R0 leg on `3cb2a28c36` → p4 受入（前提 = p11 の §10 訂正〔**済 §17.8 `e0b2857a50`**・R0-ii 採用〕＋§17.7 引用行訂正〔**済 §17.9 `20281bbf83`**・GRASP1 = 入れる〕）・pZ addendum 6 `3ad4ac4399` = 実行計器 bank（`ffa612ea33` で較正・leg ではない）・p11 の順序 = pZ GRASP1 行 prereg → p0 follow-up 3（GRASP1＋R0-ii）→ pZ leg → p4 受入（p4 の順序確認 未）→ **pZ R0 leg 済 `8b1dcb8218`**（08:54-08:55・187 行・as-landed dump path = 計器 calibration 停止〔loader・停止札〕・relocated-dump path = rows CONFIRMED・bar PASS 収束のみ L 17/17 R 17/17・負の対照 発火せず〔予測どおり〕）・addendum 7 `3ea663a5b4` = p4 条件の開示行・relay 着 m-p18-400・**受入 = p4 の語（未）: (i) p0 の loader 修正→pZ 再 leg か (ii) mesh 横の dump 写しを run 形として受入（数値は (ii) 形）** → **p0 follow-up 3 `84c7ad3b62`**（08:58・R0-ii sweep 実装・報告のみで leg を止めない・記録 §8.57 @ `ca197f2f5d`・GRASP1 行と loader 修正は未 = 小 follow-up と p4 の (i)/(ii) 待ち）→ p4 順序確認 `73edd851ed`（09:18・再 pin 条件充足・follow-up 2 の 5 要件あり・leg 次）→ **p0 follow-up 4 `f5b50967f8`**（09:18・GRASP1 行）→ pZ addendum 8 `75121f34b8`（R0-ii・GRASP1 行の期待値・順序開示）→ **pZ leg 済 `8ec2abdec3`**（09:31・232 行・as-landed = loader で計器停止／relocated = L 18/18 R 18/18・GRASP1 CONFIRMED・R0-ii bar 成立・149 対の非同一は p11 の court）→ **p4 word = (i)**（`5a56870712` 09:35・loader を直して再着地 → pZ 再 leg → 受入）・p11 §17.10 `ded9c8ee30`（149 対 = menu の意味論・solver 非対称ではない）→ **p0 follow-up 5 = loader 着地 `8e5905539c`**（09:45・§8.60′ @ `8d04d8add8`・§8.60 は p0 自身が FALSE 宣言）→ **次 = pZ 再 leg on `8e5905539c` → p4 受入** → **pZ 再 leg 済 `2bd3be01c2`**（10:30・exit 0・L 18/18 R 18/18・R0-ii bar 成立・`8ec2abdec3` (2) と 1e-12 で同一・札 none・「acceptance is p4's」）→ **p4 受入済 `30897c8a49`**（11:05:37・kickoff item 22・**収束のみ＋鏡像同一性のみ**・示さないもの = 衝突/把持/動的追従/servo〔#69〕・B の取付正しさ〔R1/R1′/R2〕・row 7・k≥1 非同一の理由〔§17.10〕・3 条件 ✓・停止札 none）⇒ **§7.2 の「④ が通過」= 成立**。追加（bar 外・受入不変）: 手首方向の report 行 = p4 word item 24 @ `b6fabff700`（可・R0 harness の report 行・条件 5 点・順序 p11 §17.11 → pZ addendum 9 → p0 follow-up 6 → pZ leg → p4）・仕様 = p11 §17.12 @ `40aa696587`（着地済・cite は hub RETURNED §1554 → §17.13 `8d9fdf3bbb` で挿入訂正・再提出の relay 待ち）・p0 予告 = follow-up 6（p4 item 26 @ `b55e80829b`・print 行の追加のみ・pZ addendum 9 の後）・**pZ addendum 9 済 `03b42afdb5`**（11:43・§17.12 逐語＋独立導出＋先行測定 = 予測成立・DoD 述語 11 対照）・p11 §17.14 `09e47cb743`（予測成立・RC k=1 = class 非収束・p11 判断不要）・p0 §8.62 候補 announce 済 → **p0 follow-up 6 着地済 `fedb5bef08`**（14:23・追加のみ・addendum 9 述語 PASS = p0 as-run・§8.63）・p4 受領 item 41 `f32e9b4f71`（14:31・pin 確認 = 親 blob は窓 R0 受入版と同一・v8→v9 = 正当）→ **pZ leg 済 `db84a76a0e`**（14:42:28・rows 1-7 全 CONFIRMED・既存行 = `8e5905539c` の verdict と同一・R0iii block = addendum 9 の期待と一致 worst 3.4e-13 mm・符号 L −1／R +1・Δ_pair 75.000 → 107.314 mm・反証形 全て偽）→ **p4 受入済 item 51 `668e85b26f`**（14:44:36・report 行 = 受入・窓 R0 不触）・p11 §17.18 = 「外側」・宣言前の設計 court 判断は不要 ⇒ **R0-iii 閉** |
| ⑤ | R1／R1′／R2 静的 legs | pZ | 未（R1 の pin は §17.3 で reference/ へ）・**pZ 順序案 `caa742b8d3`**（09-20 11:13・27 行・依存表つき・W 計器窓〔DDR 73〕→ R1′ → R1 → R2〔W/R1 と独立ゆえ並行可〕→ p4 の完成 word・各 leg = 事前登録 → object → leg）→ **p4 採用 `669b574f03`**（11:19:48・item 27・条件 4 点・R2 と R0-iii は並行）→ **W = pZ leg `59576e5ac0` rows 1-7 全 CONFIRMED → p4 受入 item 35 `2cbcb9b985`（DDR 73 CLOSED）**・**R1′ = pZ leg 済 `a8a19a393f`**（a1 84/84・a2 192/192・負の対照 3 本発火・b1 4.9e-15・1 回の計器停止〔`_gen/` mkdir〕後 rc 0）→ **p4 R1′ 受入済 item 37 `9d6dcccf3f`**（14:24:46・別件 = `_gen` mkdir 1 行 follow-up〔p0〕= §7.2 宣言の前提）・**R1 = pZ prereg `3a3b5bbc6e` → leg 済 `c7afe74422`**（R1-1..8 全 CONFIRMED・identity map ≤ 1.3e-12 mm・負の対照 2 種発火）→ **p4 R1 受入済 item 39 `e092941348`**（14:28:46・identity 写像で 49 pose・負の対照 2 種発火・p11 §17.16）・**mkdir follow-up = p0 着地 `792e62e460`**（14:27:48・+1 行・§8.64・p4 受領 item 44 = 受入は pZ の archive 実行 rc 0 の後）→ **mkdir = pZ leg 済 `b0e2b8880d`**（14:39:41・rows 1-5 全 CONFIRMED・clean archive で `_gen/` 不在のまま rc 0・数値同一・停止札 none）→ **p4 mkdir 受入済 item 49 `7902650b1d`**（14:41:27・R1′ leg の計器停止は閉）・**R2 = pZ prereg `ad06cff8eb`**（14:42:52・151 行・rows R2-1..10・負の対照 NH/RC/摂動 field・R2-9 = driver 注入 param は非継承と名指し）→ **R2 = pZ leg 済 `381713ca34`**（14:47:02・28 field 中 21 が bar 通過・**pZ 自身の bar の欠陥 2 つ〔exact 5 field が 1 ulp ≤ 2.8e-17 m で FAIL・`body_iquat` 3 body が主軸符号 180° で FAIL＝慣性テンソル差 0.0〕を FAIL のまま報告・再採点せず**・負の対照 NH/RC/B′ = 判別あり・撤回 1〔NH で hand jnt_axis は落ちない〕・処分案 = exact → ≤ 1e-12・iquat → 慣性テンソル ≤ 1e-9）→ **p4 処分 item 56 `5f3e407487`**（14:50:51・pZ 案採用・bar の欠陥 = asset でなく bar・R2-9 は p4 が driver blob で text 同一を確認 = 静的 leg 不要）→ **①p11 bar 訂正 済 `7b61c9ae2f`**（14:57:18・§17.20）→ p4 go-ahead item 60 `1846af0744` → **②pZ 訂正事前登録 済 `027174f94d`**（14:59:34・object 後の bar 変更と明記・期待を再走行前に固定・計器 `pz_r2.py` sha 不変＋慣性テンソル v2＋判定層）→ **pZ 再走行 verdict 済 `735934bef8`**（15:01:43・B 27/27 barred〔26 field＋tensor 行・`body_iquat` と `−a` は報告のみ〕・NH 23/27・RC 21/27・B′ 26/27〔body_mass〕・単体 arm 18/18・hand 27/27・`pz_r2.py` sha 不変で初回と同一再現・判定層 v1→v2 の 1 行訂正を開示・停止札 none）→ **p4 word item 63 `6e6cd470f7`**（15:04:08・実体は受入条件を満たす〔27 barred＋報告 2 = 初回の 28 と同じ集合〕・受入は判定層 v2 sha の事前登録＋判定層再走行の後 = 形式・決定的）→ 形式 1 点 済（pZ 事前登録 addendum 2 `13707643a0` = 判定層 v2 sha 登録 → 判定層のみ再走行 → verdict addendum `41b1ac75be` = 出力 byte 同一）→ **③p4 R2 受入済 item 65 `ddbc39ac61`**（15:07:55・鏡像 asset は §10 R2 の全 field が 1e-12 m／1e-9 kg·m² で対応・対照 3 種は各々の field で落ちる・示さないもの = field のみ・動的なし・mesh quat 除外・driver 注入値は text 読み）⇒ **⑤ = 済（R1′ item 37・R1 item 39・R2 item 65）** |
| ⑥ | reference 一式（Q3） | 取込 p4／照合 pZ | 取込 `e6172b2e3b`（23 file）・照合 `170cbf54a7`（manifest 20/20・4 source 同一・blob==bytes 23/23） |
| ⑦ | まとめ・受入 | p4 | **済（p4 §7.2 宣言「完成」item 67 @ `8dd5188a67`・09-20 15:14:44）**〔旧 head = 未（着手 ≠ 受入・Rs1 補足 b）〕・宣言前に要るもの（p4 09-20 item 22/24）= ⑤ R1/R1′/R2・計器窓（DDR 73）・report 行の受入（「内側」なら p11 court の判断が先）・p4 item 27 条件 ④ @ `669b574f03` = W 受入・R1′/R1/R2 の leg PASS＋p4 受入・R0-iii の結果を読む・p11 §17.11・p6 の §7.1 反映；word 時点で残る穴（名指し）= row 7・R3〔#69 の数値〕・衝突/把持/追従〔run〕・W 受入済（item 35）・R1′ 受入済（item 37）・R0-iii の「内側」判断は不要（p11 §17.14・pZ 計器上で予測成立）・R1 受入済（item 39）・追加の前提 = `_gen` mkdir follow-up（p4 item 37・着地 `792e62e460`・pZ rc 0 待ち）・p4 が宣言前に読むもの（item 43）= p11 §17.14/§17.15・mkdir = 受入済（item 49）・R0-iii = 受入済（item 51・p11 §17.18 = 外側）⇒ 残る前提 = R2 の受入（pZ leg 済 `381713ca34`・p4 処分済 item 56 = p11 bar 訂正 → pZ 再走行 → p4 受入）と p6 の §7.1 反映（本 file・p4 item 53/56/58 も同じ読み・p11 bar 訂正 済 `7b61c9ae2f`・pZ 再走行 verdict 済 `735934bef8`・形式 1 点 済 `13707643a0`/`41b1ac75be`・③p4 R2 受入済 item 65）。**p4 item 65 の語: §7.2 宣言の前提 = 全て揃った（W・R1′・R1・R2 受入・R0-iii 閉・mkdir 済・§17.14 読了）— 残る手順 = p6 の §7.1 ⑤ 反映（本 commit で済）→ p4 の §7.2 宣言 → #69 = Rs1（着手 ≠ 受入・宣言は p4・発火は Rs1）** → **⑦ = 済（p6 09-20 15:22:20 反映）: p4 §7.2 宣言「完成」= kickoff item 67 @ `8dd5188a67`（15:14:44・+12 行・:2710・m-p4-304 → hub §1610 `f6c38c4479`・m-p18-464 → p6 15:15:50〔p6 transcript :30103〕／p11／pZ／p0・送信記録 item 68 `a30fa02d10`）。充足 = ② item 6／③ item 7（row 7 = #69）／④ item 22＋R0-iii item 51／⑤ item 37・39・65／W item 35・mkdir item 49／⑥ `e6172b2e3b`・`170cbf54a7`／⑦ = 本宣言 — 挙げた 12 commit は git に実在（p6 `git cat-file -t` 15:20 実測）。示さないもの（p4 名指し）= row 7 runtime AXFIX・R3 数値・衝突/把持/動的追従/servo・route 中の実 clearance・C-2 取付 0/48・driver 注入実効値（R4）・09-07 WIP。⛔ 解錠なし・run 0・#69 の発火 = Rs1 の一語・物理妥当性 = Rs1 の目（pB/pC）・run の形 = Rs1 の一語の後に p18/p6 と組む。後続記録 = p0 §8.64 addendum 13 `7ad6b1f7ef`（＋訂正 `2ce486c69c`/`9fce63647b` = 未測 pin 1 件と §7.2 行番号〔§7.1 :113・§7.2 :125〕）・p11 §17.23 `cb2a990231`・p11 handoff `5bd26f29c2`。DDR 68 = 開いたまま（閉鎖 = Rs1 の spec 反映の一語の後・p4 item 67「次」と p6 の読みが一致）** |

### 7.2 完了条件（p4 起案 = DDR #69 の「controller の完成」）

②③ が述語つきで着地・⑤ と R3 と ④ が通過・p4 の受入の一言（④ = 収束・STOP の leg＝Rs1 Q1 の射程／正しさは ⑤ R1・R1′・R2 = p4 読み ② 09-16 18:39・構造不変）。**着手と完成受入は分ける**（Rs1 補足 b）。完成後も #69 の発火は p4 の充足宣言＋視覚 leg（pB／pC）。⛔ 本節は何も解錠しない（route run (2)・#69・D4′・WIP；`:214`/REF_DIR の計器窓は Rs1 Q9「推奨」09-16 18:06 で open = DDR #73 の別窓・run の解錠ではない）。

### 7.3 範囲外（本 step に含めない）

D4′（DDR #74）・`:214` 修正（DDR #73）・09-07 WIP（DDR #72）・acceptance の `REF_DIR` 書換（pZ 所見 `170cbf54a7`・code 1 行・語 = Rs1 Q9「推奨」09-16 18:06 → DDR #73 の計器窓・別窓）。

### 7.4 報告規則（Rs1 補足 a）

計器による停止はコントローラの不成立と区別して報告する（v3 §17.4 の「停止原因の札」）。

### 7.5 #69 run の形（Rs1 認可 2026-09-20 22:30:46・v1 = 3 記録で固定・正 = `00-DESIGN-STATUS-LEDGER.md` 行 69 status cell）

**Rs1（人間）逐語**（custody = p4 transcript `ad899cc6-2451-4364-ba3c-910b67075aa4.jsonl` `:4397`・typed・22:30:46 JST・p6 json 実読・p4 kickoff item 69 @ `e7b2436e0f`〔逐語 :2725〕・hub §1612 `82da3d8bd5`・relay m-p18-465 22:36:26）: 「#69 の再撮影を認可する。／p18/p6 と run の形を確定してください。stop-cause 札、pB による row 7・R3 の log 読み、pC の視覚 leg、Rs1 の目視確認を必須とします。／p4 自身は発火せず、route run (2)・D4′・WIP には触れないでください。」
**固定 = 3 記録**: p4 案 item 69 `e7b2436e0f`（9 点）＋ hub 補完 §1613 `82da3d8bd5`（B1 産物 pin・B2 動画 custody・B3 経路・B4 返却規則・B5 執行 1 回・B6 不触・C 3 記録）＋ p4 同意 item 71 `90d5ad5fe5`（env key 23 = driver 18＋cell_spec 5・p6 自算一致〔→ v2 で 24 に訂正 = alias 読み・p6 の自算も誤り〕）＋ **p6 = 本 commit（LEDGER 行 69 v1・p6 09-20 22:45:09）** → hub が本 commit を p0 へ relay → p0 執行 1 回。要点: 対象 = 08-10 U0 と同形の `ur15_steps_wired.py` 1 run（⛔ C3C5 DoD ③ でない）／object = `96e9ece175` の clean 木（driver `84a372439c59`・共有 tree は overlay +1427/−884 ゆえ不可）・env7・parameter 変更 0／産物は sha256 で p0 §8 に commit → hub 着地 relay・動画は `~/Downloads`＋hub 再計算 sha・dump sha は測る／stop-cause 札必須・欠落 = RETURNED／pB = row 7・R3・STOP（numeric 単独 = RETURNED）／pC = 視覚 leg（judge-fit 先・数値不読・**pB verdict を入力にしない = p6 補完**）／Rs1 の目視 = 最終／p4 受入 = 3 者の後 → p6 反映。採否待ち（run を変えない）= p11 §17.24 `f55b968c23` の R4 読み 2 点。⛔ 解錠 = 行 69 のみ（行 68・route run (2)・D4′・WIP・training-ready 不触）・run 0（p6 09-20 22:45:09 実測）。 **執行 gate 通過 = hub m-p18-468（22:51:25 → p0）**・hub の読み (D1)(D2) と v2 候補 (D3)(D4) = LEDGER 行 69 22:54:14 節（LIVE_OUT = driver `:2982`・印字 env key 24・札 = p0 §8 の行・OUT は run dir 内）・run 0（p6 22:54:14 実測）。 **v2（p4 item 73 `e15124c25f`・hub §1617 `fbef2d182c`・p6 23:04:52）** = (D3) 3 点採用〔pZ 照合 1 行・pB tool_err_mm 報告・pZ cell dump text 読み〕・(D4) 採用〔verdict = 各卓 1 file・pathspec〕・順序 = p0 執行 → §8 commit → hub 着地 relay → pB ∥ pC（pC に pB verdict を relay しない）→ pZ 照合行 → Rs1 目視 → p4 受入（3 者＋pZ 行の後）→ p6・訂正 = env key **24**（cell_spec の alias `_os_env` 読み = 実効 knob・printed set が正）・形は不変。**(v2-9)** = 早期停止 run では OUT.mp4 が無い（raise 時は書かれない）ため pC・Rs1 の対象 = LIVE_OUT・返却理由にしない（p4 item 75 `e384c3737d`）。**執行 1 回 = 済（p0 §8.66 `4583fa7444`・22:55:08→23:03:12・STEP2 stall raise・札「controller の不収束」1 行・OUT なし・LIVE 2.2 s → `~/Downloads/ur15_live_69_20260920.mp4` sha `9818e050…`・産物 sha = `P0_RUN69_RESHOOT_20260920/SHA256SUMS.txt`）**・verdict 0・p4 受入 未・表面化 = dump sha ≠ 期待 `4158…`（v1 (4) 述語発火・処分 = p4）／GRIP_XML は共有 tree の絶対 path（内容同一）／run.log は gitignore で未 commit（p4 の語）— 詳細 = LEDGER 行 69 23:12:10 節。 p4 の語（item 78 `cb01a67273`）= 表面化 3 件とも返却なし〔① 期待 dump 側の誤り ② hand XML 内容同一・以後は照合行必須 ③ run.log は force-add〕・v3 注記 = CPU driver に CUDA/nvidia-smi 印字は不要・**Rs1 待ち 1 件 = 目視（`~/Downloads/ur15_live_69_20260920.mp4`）**。 hub custody VERIFIED §1620 `4e4df93bc8`（B2 pin 済・返却なし）・pZ 照合 leg 事前登録 `94d7e04e18`（sha `8a20d32c…`・210 行・産物未読で固定）・**verdict 2/3 = pC VERDICT_C `a1a39b4f03`→`ffd3c5200c`**（観測のみ・LIVE_OUT 66 frame 2.200 s・近接パネル遮蔽で把持 NOT MEASURED・L 腕 動きなし・R ≈1 cm 移動後静止・クリップ空・貫通 SUSPECTED 上限・無印 PASS なし）＋ **pB `8b16ce641a`→addendum 1 `4711c2c248`**（数値の報告のみ・row 7 = 18 数 差 0〔bar 1e-6 内〕・R3 印字 5.73/(L 5.73 / R 5.73) 整合・停止の三者一致・tool_err_mm L 658/1126 mm・R 2.2 mm 報告・PASS なし）・run.log force-add `0d22720834`（blob 内容 sha = pin）・**pZ 照合行 済 `160e06ce0f`→addendum 1 `675c6b459d`**（C-1〜C-6 CONFIRMED・pB と全数一致・注入値 40/40 L==R・返却なし）・**札 = 「その他」（p4 裁定 item 86 `57fa59fa47`・射程 = 分類のみ・p0 addendum 6／pB addendum 3／p11 §17.26 異論なし）**・**Rs1 目視 = 充足（`RS1_RUN69_REVIEW_20260921.md` @ `cf44999454`・Rs1 = p19・可視範囲で 3 記録と整合・返却なし・⛔ 工程完了でも PASS でもない・把持／接触は未測定）** ⇒ **4 入力すべて着地・残り = p4 の受入 word のみ（p4 停止中・p6 からは呼ばない）**。次の技術準備（Rs1 の語）= L 腕の初期接触／取付とカメラ可視性に具体的変更と受入条件を付ける（次 run の前）。（p6 09-21 01:18）。⭐**#69 = p4 受理済（item 95 `70e6417e46` 01:20:22・5 面一致・B4 返却理由なし・再走なし）⇒ LEDGER 行 69 = CLOSED（認可 履行済）**。⛔受入は形の履行と 5 記録の指示対象の同一性のみ（工程の成否・把持・物理妥当性・行 68 の閉鎖・node COMPLETE・training-ready・再走認可を含まない）。⭐**human GT は未適用のまま** — 把持・持ち上げ・route・貫通を主張する run は bank 前に**利用者（人間）の目視**が要る（Rs1 役の交代はこの述語を移さない）・近接カメラの遮蔽は把持を視覚判定する run の前に直す。carry = 採用済（確定形 ①-⑧ = LEDGER 行 69）。呼称の境界 = 2026-09-21 00:21:28 JST。（p6 09-21 01:27）。⚠**Rs1 (p19) の裁定 01:30:39**: #69 の受入は維持・⛔再審査しない。**F(1)〔物理的主張には利用者本人の目視〕を以後一律の規則としては採らない**（役は p19 へ移管済ゆえ歴史的な「Rs1 = 人間」だけを理由に人間待ちを復活させない）。代わりに **V12 の独立レビュアー経路・必要時 blind review・judge-fit は必須**・⛔Codex 自己目視を正式な物理判定にしない・⛔人間が見たとは記録しない・根拠不足なら不足した検証を名指す。物理妥当性 未確認／工程 未完／新 run 未認可は維持（F(2) の近接遮蔽も）。詳細 = LEDGER 行 69。（p6 09-21 01:32）。

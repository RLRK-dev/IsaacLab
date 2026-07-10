# Vault 設計監査 — 執行計画 V1(PR-1) + V2(PR-4)

**Author:** COORD2 (%10 / w2:p2)。**Charter:** %12 2026-07-11 04:39（Rs 04:38 package 承認 = 第1段 policy/design 確定: PR-1+PR-4+PR-3[follow-on]+PR-2[後日]+⛔mass-move 非採用）。
**親監査:** `VAULT_DESIGN_SCATTER_AUDIT_COORD2_20260711.md`（sha `fe9bb92b…386fbf`、%12 verify PASS 04:37）。
**Status:** PLAN v1.1 — **paper only（0-commit、執行未着手）。** L1。（v1.1 = %12 04:48 clarify: §2.3 pin 契約を「同ターン pin 生成 + 存在照合のみ、content≠STOP」に精確化 [①']。）**chain:** 本 plan → sha ping → %12 verify → **Rs 1行授権（batch ごと）** → 執行。**LEDGER/07-Design 編集 = Rs 専権授権 flow でのみ**（Vault Write Permissions:27）。
**baseline:** HEAD `909b065b3f`、LEDGER 122 行（実測 04:41）。全 lineage/件数 = 本 session python 実測。

---

## §1. LEDGER 粒度決定（%12 指定1 — rationale 込み）

**採択 = lineage 粒度（member-file 列挙列付き）。per-file 51 行は不採用。**

| 方式 | LEDGER 増 | 帰結 |
|---|---|---|
| per-file | +50 行 → **~172 行** | living SSOT 肥大（毎 session 全読、scan 性劣化）。50 行の大半が同一 node の version = 冗長 |
| **lineage（採択）** | **+12 行 → ~134 行** | node/family 単位、member-file を列挙列に格納 = per-file provenance 保持しつつ scan 性維持 |

**rationale:** (a) LEDGER は毎 session 接地の living SSOT → 行数 = 直接 cost（+50 vs +12 で 38 行差）(b) untracked 50 は **12 の設計 lineage の version 群**（例 DQ7×8 = 1 lineage の反復）→ lineage が意味単位 (c) member-file 列で per-file 追跡性は喪失しない (d) LEDGER 既存も doc 単位 lineage 行（PoseEstimation v1-v3.2 は個別行だが、それは異 status の分岐; 本 50 は概ね同 status の version 群ゆえ集約が適切）。

---

## §2. Batch V1 = PR-1（tracking-by-LEDGER + doc_class tag）

### §2.1 LEDGER 行案（12 lineage、draft — status = Rs-confirmable）

> 各行 = `lineage | proposed-status | one-line | member-files(N) | evidence | decided-by`。status は audit §3.1 + LEDGER row47 由来の**提案**（design status = Rs-confirmable、"(Rs-confirm)" 明記）。

| # | lineage | proposed status | member files (N) |
|---|---|---|---|
| L1 | optE-DQ7-offpath | ⛔ **SUPERSEDED (Rs-confirm)** — R1 CLOSE（LEDGER row47）、historical | DQ7_{DAGGER_BUILD_SPEC,_V2_MINIMAL,OFFPATH_SCOPING}×3 + dq7_{capacity_pretest,ii,ii_v2,iv}_mini_spec×4 + dq7_minitest_verify_packet_final (8) |
| L2 | optE-B-BC-imitation | ⛔ **SUPERSEDED (Rs-confirm)** — ladder v2/envcore で superseded | B0_BUILD_REPORT / B2_KICKOFF_SPEC / B_BC_{BUILD_SPEC_DEBATE_R1,IMITATION_SCOPING} / b2_{fix5_geometric,runner_v2}_design (6) |
| L3 | optE-W0packet | 📖 **REFERENCE (Rs-confirm)** — W0-e CLOSED（row47）、decision-of-record historical | RS_W0E_PACKET_V1_1 / W0APRIME_PACKET_V1_1_CROSSPV_PCT9 / W0E_GEOMETRIC_DESIGN_20260705 (3) |
| L4 | optE-P2-envspec-reward | 🔁 **SUPERSEDED-in-substance (Rs-confirm)** — env-core COMPLETE（row47）、spec は banked 基底 | P2_{ENVSPEC_5TAI_DECIDE,REWARD_ARTIFACTS_W0C_DRAFT,REWARD_DESIGN,ROUTE_ENV_SPEC_INPUT_W0C} (4) |
| L5 | optE-DAPG-scoping | 📖 **REFERENCE (Rs-confirm)** — 原 scoping、arch 決定で superseded | DAPG_WHOLEROUTE_C1C2_SCOPING_COORD2 (1) |
| L6 | optE-P3-recorder | 🟢 **SUPPORTING（LEDGER row44 の design を支持）** — recorder WORKING の spec/report | P3_DEMO_RECORDER_SPEC / P3_RECORDER_BUILD_REPORT (2) |
| L7 | optE-COMP3-routeexec | 🟢 **ACTIVE (Rs-confirm)** — route-exec node 進行中、一部 live | COMP3_{DRIVEPATH_DECISION_PACKET,FORCE_DESIGN_SERVO,GEOMETRIC_DESIGN_LANEFLOOR,GEOMETRIC_DESIGN_VOID,PLAN_ROUTEEXEC_GRASPACT,REWARD_DESIGN_FLAGON} (6) |
| L8 | optE-routeexec-buildplan | 🟢 **ACTIVE** — route-exec build 進行中 | BUILD_PLAN_{ENVCORE,ROUTEEXEC,ROUTEEXEC_LAYERB} (3) |
| L9 | optE-slot-probe | 🟢 **ACTIVE** — live probe 設計（07-08/07-10） | SLOT_REDESIGN_STUDY / SRG_PROBE_DESIGN_DRAFT (2) |
| L10 | VT-St2 | 🟢 **ACTIVE** — VT node 進行中（本 pane review 済 v0.1b/canonical chain） | ST2_BUILD_SPEC / ST2_RS_APPROVAL_PACKET (2) |
| L11 | 06K-Vision-pipeline | ⏸ **PARKED (Rs-confirm)** — vision L1.A 未着手 / P0-KILL as-scoped | LL-Vision-{CableState-Design,-Phase2-Impl,-Phase3-Integration,-Phase4-Validation,DR-Design,DR-Tier1-D6,Fusion,Pose}-Design (8) |
| L12 | 06K-L1-adapter-orchestration | ⏸ **PARKED (Rs-confirm)** — L1 design（RL-Routing MIXED per-skill） | LL-{BaseAdapter,Cascade-C-Nemotron,Cascade-C-Qwen,L1-B-Routing,Orchestration}-Design (5) |

**除外:** `RENEWAL_PLAN_07DESIGN.md`（51番目の untracked）= renewal charter 所有 → 本 V1 対象外（二重 scope 禁止、renewal が tracked 化）。→ **tag/行 対象 = 50 file / 12 lineage。**

### §2.2 doc_class tag（%12 指定2 — content 不変 1行 add）

- **tag 値:** `doc_class: design-surface`（live/ACTIVE 設計）/ `run-evidence`（結果・report・crosspv）/ `reference`（historical/superseded decision-of-record）。
- **付与対象 = 50 file frontmatter に 1 行 add**（既存 frontmatter 末尾 or 新 frontmatter block）。**値割当（提案）:** L7/L8/L9/L10 = `design-surface`（ACTIVE）/ L1/L2/L4/L5 = `reference`（superseded/historical）/ L3 = `reference` / L6 = `design-surface`（supporting spec）/ L11/L12 = `design-surface`（PARKED だが設計内容、run-evidence でない）。
- **gate（renewal banner-only diff の変種）:** tag add は **content-invariant** → 執行 diff は各 file **+1 行のみ（tag 行）**、既存 body byte 不変を **`git diff` で tag-only（1 add / 0 del / 0 body-mod）確認**。逸脱 = STOP。層5-lite or loud 免除記録（content diff なしの add ゆえ、renewal §row0 CC5-C1 同型）。

### §2.3 執行時 sha 再検証契約（renewal §2-1 CC5-C3 同型）

- **理由:** SHARED-LIVE vault は承認〜執行の間に他 pane 編集が起き得る（renewal 実績: D-1 flow が同夜 RL-Routing 実編集 / 本監査 window で VGroove hunk が 01:26 discard）。
- **契約（v1.1 精確化、%12 04:48 clarify — ①'）:** 本 plan は**事前 pin 値表を掲載しない**（同ターン pin 生成方式 = stale-pin 回避）。∴ 執行時の sha 測定は **pin 生成（provenance）であって「掲載 pin との content 照合」ではない**（照合対象は存在しない）。
  - **STOP 条件 = 存在照合のみ:** 執行同ターンに 50 target の存在を audit-time inventory（本 plan §2.1 の 50-file list）と照合。**file 消失/新規 = STOP + re-inventory + Rs へ delta 報告。**
  - **content 変化 ≠ STOP:** 本 batch の編集は additive（LEDGER add / tag add）ゆえ、他 pane が承認〜執行間に target の body を編集していても、**現在 byte に tag を add する**のが正（誤 phantom-mismatch STOP を防ぐ）。現在 byte に対する **tag-only-diff gate（§2.2）+ LEDGER add-only** が実保護。
  - **provenance:** 測定した 50 file の full 64-hex sha256 を commit message に記録（out-of-doc 束縛、execution-time state の証跡）。
  - ⚠ renewal §2-1 との差異: renewal は**事前 pin あり**（p5 測定・%12 verify 済）ゆえ content-mismatch STOP が成立した。本 plan は同ターン pin 生成を選んだため、その leg は存在照合 + tag-only-diff に置換される（機構は等価な race 保護、STOP 契機のみ異なる）。

### §2.4 Rs 授権 flow（LEDGER = 07-Design = Rs 専権）

1. 本 plan → sha ping → %12 verify。
2. %12 → Rs へ batch V1 執行の **1行授権**要請（policy は承認済、執行 = batch 授権、renewal 2段同型）。
3. Rs 授権後、同一ターンで: §2.3 sha 再検証 → LEDGER +12 行 add（explicit-path atomic commit、full-hash message）→ 50 file tag add（§2.2 gate）→ 層3 機械（tag-only diff 検査）→ commit。
4. LEDGER 編集は **CC 独自でなく Rs 授権下の執行**（設計 status = Rs-confirmable ゆえ status 列は Rs 確認を経る）。

---

## §3. Batch V2 = PR-4（supersession banner）

- **対象:** superseded/historical lineage = **L1(DQ7) / L2(B-BC) / L4(P2) / L5(DAPG-scoping) / L3(W0packet, historical)** の member files（8+6+4+1+3 = 22 file）。
- **banner form（renewal ARCHIVE-banner 同型、doc 冒頭 add）:**
  ```
  > ⛔ SUPERSEDED / HISTORICAL (as-of 2026-07-11) — SSOT = LEDGER L{n}. superseded by {successor}. live 値は copy せず task_config/後継 doc を pointer.
  ```
- **content-invariance:** banner = doc 冒頭 +N 行 add（body 不変）→ §2.2 と同じ tag-only-diff 変種 gate。
- **順序:** V1（tracking）→ V2（banner）。tracked 化を先に（原本を git provenance 固定、renewal §2-1 順序論理同型）。
- **執行 = V1 と同様に Rs 1行授権 + sha 再検証 + %12 verify。**

---

## §4. PR-3 follow-on（node 登録案のみ、執行しない）

- **内容:** reference-over-copy spot-audit（SSOT 値 bare-restate の per-doc 精査 — audit §3.2: 0.7407 bare 6件 + 88mm 48file 等）。
- **登録案（p6 PLAN-KEEPER 宛、本 plan 内提示のみ）:** 新 node `T-ROOT-VaultRefCopy-SpotAudit`（parent = 本監査 node）、scope = 50 tag-target + 高頻度値 file、DoD = copy-violation の per-file 確定リスト + PR-3 pointer 化提案。**本 charter では起票・執行しない**（%12 指定: plan 内に含めるだけ）。

---

## §5. 執行 gate まとめ

| gate | V1 | V2 |
|---|---|---|
| Rs 1行授権 | 必須（LEDGER=Rs専権） | 必須 |
| sha 生成 + 存在照合（執行同ターン、①'） | 50 target 存在（消失/新規=STOP） | 22 target 存在 |
| content-invariance | LEDGER=add-only / tag=tag-only-diff | banner-only-diff |
| 層3 機械 | tag/banner diff 検査（body 不変確認） | 同 |
| %12 verify | plan + 執行後 | 同 |
| 層5/loud | 免除記録（content diff なし add、renewal CC5-C1 同型） | 同 |

---

## §6. 接地台帳

| ソース | 用途 | cite |
|---|---|---|
| 親監査 doc | lineage/件数/LEDGER coverage | sha `fe9bb92b…386fbf`、%12 verify PASS 04:37 |
| 00-DESIGN-STATUS-LEDGER.md | bloat baseline + status 由来 | 122 行（実測）/ row47（route-dapg node status）/ row44（recorder）|
| renewal `RENEWAL_PLAN_07DESIGN.md` | §2-1 sha 再検証契約 + banner form + 2段授権 同型元 | :45 §2-1 / :67-68 banner+snapshot / :158 sha 再検証 STOP / :209 batch0 済 |
| task_config.py | doc_class=reference の pointer 先 SSOT | :291/:235/:226 等 |
| 本 session python | 12 lineage / 50 target / bloat +12→134 vs +50→172 | 実測 04:41 |

**Conservatism:** lineage status = **提案（Rs-confirmable）**、Rs 確認を経て確定。件数/bloat = measured。sha pin = 執行同ターン測定契約（stale pin 回避）。全 diff = content-invariant（LEDGER add-only / tag/banner add-only）→ body byte 不変が gate。paper-only / 0-commit / 執行は Rs 授権下のみ。

*COORD2 %10 — 2026-07-11（完了 = sha ping 参照）*

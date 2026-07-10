# 07-Design 構造刷新 RENEWAL_PLAN(step 0-1 packet)

**Status: v0.1-DRAFT** — chain: 本 packet → **5体 debate(L3 pre)** → %12 verify → **Rs 承認** → batch A/B/C 執行。
**Charter:** Rs 裁定 2026-07-11 00:30(%12 relay 00:35、bank = routeexec node): 対象 = 07-Design 主要 doc 群 / 深さ = **構造から刷新 — canonical 値(43-step 表・全数値)不変保証付き** / executor = p5(設計基盤 surface)。**L-TRIAGE = L3**(RL-Routing-*.md path match + 複数 file)。
**Guardrails(charter + %12 00:38 追加):** ①刷新 = 構造/編集のみ — 工程・設計値の変更は v-next governance へ(不混合)②RL-Routing-Progress = FROZEN 原文 verbatim 保存(banner 以外の内容 edit 禁止)③PoseEstimation disposition は LEDGER status 照合を先行、consolidate は ACTIVE 系譜のみ(復活禁止 gate)④FAILED/DISCARDED doc の内容復活禁止(restore-of-DISCARDED gate)。
Author: p5 VT-DESIGN。Drafted: 2026-07-11 00:4x JST。**Node: T-ROOT-DesignDoc-Renewal-20260711**(登録 `eac3d11b73`、IN_PROGRESS、assignee = p5。RL-Routing-Design tracked 化 commit の正 = `59badc4b7a`、`eaf05513…` = file sha256)。

---

## §0 接地(§運用4)

| SSOT | 用途 |
|---|---|
| `00-DESIGN-STATUS-LEDGER.md` :41,:42,:50-57 | 各 doc の成否 status(§1/§3 の disposition 根拠、guardrail ③) |
| `CANONICAL_MOTION_TABLE_V1.md`(v1.0a-r1、Rs-approved) | §5 版管理規約 + sub-revision 規約(本刷新の版管理準拠先)+ cite 当事者 |
| charter message(%12 00:35)+ 確認 5 点(00:38) | scope・process・guardrail |
| inventory 実測(2026-07-11 00:3x-00:4x、git status + wc + sha256 + grep) | §1/§2/§6 の全数値 |

## §1 Doc inventory(11 file、実測 2026-07-11)

| doc | 行 | git | LEDGER status(:行) | cite 露出(in-repo) | disposition(§3) |
|---|---|---|---|---|---|
| 00-DESIGN-STATUS-LEDGER.md | 122 | tracked | (自身が SSOT) | 多数(生きた参照) | **EXCLUDE**(生きた SSOT — 刷新対象外) |
| RL-Routing-Design.md | 3,760 | tracked(⑥済 `eaf05513…` D-1 注記込) | ⚠️ MIXED(:42) | **行 cite 69 hits/21 files + § cite 56 hits/28 files** | **RENEW**(batch C、最重) |
| RL-Routing-Progress.md | 4,926 | tracked | 📖 REFERENCE、FROZEN banner 済(:55、Rs D4 07-02) | 名前 322 hits/22 files | **ARCHIVE-LABEL**(batch A; verbatim 保存、banner 確認のみ) |
| Mechanical-Specs.md | 2,646 | tracked | 📖 REFERENCE(:56、hardware 未取得注記) | 行 cite 3 hits/2 files(低) | **RENEW**(batch C) |
| PoseEstimation-Design-v3.2.md | 686 | **untracked** | ⏸ PARKED head(:50、unvalidated・L1.A 未着手) | 名前系 140 hits/58 files(5 世代計) | **CONSOLIDATE head**(batch B、§3 option) |
| PoseEstimation-Design-v3.1.md | 1,187 | untracked | 🔁 SUPERSEDED(:51) | 同上 | ARCHIVE-LABEL(batch B) |
| PoseEstimation-Design-v3.md | 1,417 | untracked | 🔁 SUPERSEDED(:52) | 同上 | ARCHIVE-LABEL(batch B) |
| PoseEstimation-Design-v2.md | 1,062 | untracked | 🔁 SUPERSEDED(:53) | 同上 | ARCHIVE-LABEL(batch B) |
| PoseEstimation-Design-v1.md | 622 | untracked | 🔁 SUPERSEDED(:54) | 同上 | ARCHIVE-LABEL(batch B) |
| S1B-Faithful-Finger-Design.md | 144 | **untracked** | ⛔ FAILED/ABANDONED/SUPERSEDED(:41、LEDGER §FAILED item 1) | 低 | **ARCHIVE-LABEL + 内容復活禁止**(batch A) |
| Gripper-VGroove-Design.md | 141 | tracked(**' M' 1 行**) | 🔁 SUPERSEDED by コ / ◇ DISCARDED(:57) | 低 | ARCHIVE-LABEL 確認(banner 済、batch A)+ ' M' adjudicate(§2) |

**LEDGER 照合結果(guardrail ③):** PoseEstimation 5 世代 = **単一系譜 chain(v1→v2→v3→v3.1→v3.2)、FAILED/DISCARDED 混在なし**(全て SUPERSEDED、head = PARKED)→ consolidate 可能系譜。FAILED は S1B のみ(別 doc、archive 側)。

## §2 Step-0 提案(Rs 一括承認 batch)

1. **tracked 化 6 file**(PoseEstimation v1/v2/v3/v3.1/v3.2 + S1B)。順序論理: **consolidation/archive-label 前に tracked 化して原本を git provenance に固定**(⑥ RL-Routing-Design と同型)。編集前 sha256(2026-07-11 00:3x 実測、tracked 化 snapshot と照合可能):
   - v1 `49c8c52fb0…` / v2 `42aeaf03c1…` / v3 `a7913e9fab…` / v3.1 `623ee87571…` / v3.2 `6719200e7d…` / S1B `93822028d2…`
2. **Gripper-VGroove ' M'(1 行 uncommitted)の adjudicate:** 内容 = HALF_OPEN_RAD「≈0.667 PROPOSED」→「0.69 human-confirmed 06-21 + LANDED(task_config 06-25)」の records-currentization。**内容は task_config.py:313 と検証一致 = 事実正**。origin pane = 不明(p5 調査 + %12 とも不明、最終 commit 06-22 以降放置)。提案 = **「内容検証済 currentization」として commit**(commit message に origin-unknown + 検証根拠を明記)。

## §3 Per-doc disposition(詳細)

### 3.1 RENEW(batch C — 構造刷新本体)
- **RL-Routing-Design.md**(3,760 行): 新構造 = §4 skeleton。**§2 工程設計(43-step 表)= canonical 領域 — 内容 verbatim 維持**(表・用語・§2.1/§2.2・D-1 訂正注記込み)。歴史堆積(v5/v8-v12 廃止 Step 表、Session 91 現在地等)は「historical」節に区画化 or 参照化。LEDGER :42 の MIXED nuance(AR 92.2% だが QUARANTINED / 5-skill P0-KILL)を STATUS banner に正確反映。
- **Mechanical-Specs.md**(2,646 行): 同 skeleton。「intended hardware / 物理 hardware 未取得」(:56)を banner で明示。cite 露出低(3 hits)= 低 risk。

### 3.2 CONSOLIDATE(batch B — PoseEstimation 系譜)
**Option P-light(推奨):** v3.2 = head のまま(rename なし — 140 hits/58 files の cite 温存)、v3.2 に「CURRENT HEAD(PARKED/unvalidated)+ 系譜 banner(v1→v3.2 chain + 各 LEDGER 行)」を付与、v1-v3.1 に ARCHIVE banner(SUPERSEDED、edit 凍結)。**根拠: PARKED・unvalidated(vision L1.A 未着手)の設計を content 再合成するのは invariance risk(4,974 行)に対し ROI 低**。将来 L1.A 着手時に real consolidation。
**Option P-full:** 5 世代 → 1 本の consolidated doc に内容統合 + 5 原本 archive。深さは charter「構造から刷新」に忠実だが、unvalidated 領域の再構成 = 検証手段なし。
**→ 決定 = Rs(packet 提示時の decision item #1)。**

### 3.3 ARCHIVE-LABEL(batch A — 低 risk 即時)
- **RL-Routing-Progress.md**: FROZEN banner 確認(既設 07-02)+ 必要なら label 正規化のみ。**内容 edit 禁止(verbatim 保存、guardrail ②)。**
- **S1B-Faithful-Finger-Design.md**: FAILED banner + **「内容復活禁止(substrate-walled + Rs-abandoned 06-05、LEDGER :41/:65)」**明記。
- **Gripper-VGroove-Design.md**: DISCARDED banner 済(:57 と整合確認)+ §2-2 の ' M' adjudicate 後は edit 凍結。

### 3.4 EXCLUDE
- **00-DESIGN-STATUS-LEDGER.md**: 生きた成否 SSOT。刷新は「参照する」のみで「触らない」。

## §4 新構造 skeleton(RENEW 対象に適用)

```
1. STATUS banner(LEDGER 該当行 mirror + 「status SSOT = LEDGER」pointer — 二重管理しない)
2. SSOT cross-ref 節(canonical 値は保持せず参照: task_config.py / full_43step.json /
   CANONICAL_MOTION_TABLE_V1 §*。reference-over-copy)
3. 本文(現行有効な設計内容 — 構造再編、値 verbatim)
4. HISTORICAL 節(廃止済み経緯・旧 version 記録 — 区画化、削除はしない)
5. Changelog + 版管理(CANONICAL_MOTION_TABLE_V1 §5 規約 + sub-revision 準拠;
   version⇄sha 束縛は commit message / LEDGER 側 = 自己 sha 埋込禁止)
```

## §5 Canonical-invariance 機械検査(charter 保証、batch C gate)

**検査対象 = RENEW 対象の全数値 token + 43-step 表。** 手順(script 案 `renewal_invariance_check.py`、~60 行、paper 段階では設計のみ):
1. **数値 token 多重集合比較:** pre/post 両版から `[-+]?[0-9]+\.?[0-9]*([eE][-+]?[0-9]+)?` を全抽出(code-block・表・本文を含む全行)→ 正規化(前後空白・桁表記)→ **多重集合 diff == ∅ を要求**。削除(historical 区画への移動は集合不変)・追加(新規値 = guardrail ①違反)とも FAIL。※日付・§番号・行番号 cite 等の「構造由来数値」は移動で増減し得るため、**除外 regex を pre-registered list で宣言**(検査 script 内に列挙、後出し除外禁止)。
2. **43-step 表 row-level 検査:** §2 の 43 行(STEP/z/finger/クリップ状態)を pre/post から parse → **row-wise EXACT**。full_43step.json = 不触(sha 不変を検査)。
3. **判定:** 1+2 とも PASS でのみ per-doc commit 可。FAIL = 差分を loud 出力して STOP(自動修正しない)。
4. 検査 log は evidence dir に世代 tag 付き保存。

## §6 Cite-breakage 監査 + migration map(実数、2026-07-11 00:4x grep)

| 対象 | 露出 |
|---|---|
| `RL-Routing-Design.md:NNN`(行 cite)| **69 hits / 21 files** — 刷新で行番号が動けば全て stale 化 |
| `RL-Routing-Design.md §N`(§ cite)| 56 hits / 28 files — §番号を保存すれば生存 |
| `Mechanical-Specs.md:NNN` | 3 hits / 2 files |
| `PoseEstimation-Design*`(名前)| 140 hits / 58 files — **rename しない方針で全温存**(Option P-light) |
| `RL-Routing-Progress.md`(名前)| 322 hits / 22 files — verbatim 保存 + rename なしで全温存 |

**Policy:**
- **rename ゼロ**(全 file 名維持)— 名前 cite は全温存。
- **§番号レベルの後方互換を design 目標に**(RL-Routing-Design §2 = 工程設計 等の主要 § は番号維持)→ § cite 56 hits 生存。
- **行 cite 69 hits は必然的に stale 化** → **migration map**(`RENEWAL_CITE_MAP.md`: old `file:line` → new anchor)を batch C の必須成果物に。**banked evidence doc(eval_runs 世代 tag 付き)は retro-edit しない**(immutable 原則 — map は読解用 lookup)。live surface(CANONICAL_MOTION_TABLE_V1・LEDGER・active node state.md)の cite は map 適用で同 batch 内更新。
- 43-step 表を §2 内で**行位置ごと安定化**(§2 より前の構造変更を最小化)する編成も検討 — 行 cite の一部を実際に生存させる(design 選択、5体で検証)。

## §7 執行 batch + gate

| batch | 内容 | gate |
|---|---|---|
| **0** | tracked 化 6 file + VGroove ' M' commit(§2) | Rs 一括承認(本 packet)→ 機械執行(sha 照合付) |
| **A** | archive-label 3 本(Progress 確認 / S1B / VGroove)| 低 risk。banner-only diff を %12 verify(verbatim 検査 = banner 以外 diff==0)|
| **B** | PoseEstimation 系譜(Rs 決定 option 準拠)| banner-only(P-light)なら A 同型 / P-full なら C 同型 gate |
| **C** | RL-Routing-Design + Mechanical-Specs 構造刷新 | **§5 invariance 検査 PASS 必須** + cite map 納品 + 層5 多視点(L3)+ %12 verify + per-doc commit(sub-revision 規約)|

全 batch: 値変更ゼロ(guardrail ①)。工程・設計値の変更要求が刷新中に発生したら **v-next 台帳へ回送**(混ぜない)。

## §8 Louds / risks

- 行 cite 69 hits の stale 化は**不可避**(map で緩和、消滅はしない)。
- invariance 検査の除外 regex(§5-1)の設計が甘いと false-PASS — 5体の攻撃対象として明示指定。
- PoseEstimation P-full を選ぶ場合、unvalidated 内容の再構成に検証手段がない(sim/実機とも未着手領域)。
- RL-Routing-Design には他 pane が並行 cite 追加中の可能性(live 参照先)→ batch C 直前に cite 再 grep(本 §6 数値は 00:4x 時点)。
- Fable5 常用期限(project-fable5-standard-through-0707 は 07-08 で Opus 復帰済)— 本 charter の「Fable5 で刷新」は Rs 意向 verbatim を記録したもの。実行 model の指定は Rs/%12 に従う(p5 は現 session model で起草)。

## §9 Rs decision items(packet 提示時)

1. **PoseEstimation: Option P-light(推奨)vs P-full**(§3.2)。
2. LEDGER = EXCLUDE の確認(§3.4、%12 同意済)。
3. Mechanical-Specs の刷新深さ(full skeleton 適用 vs banner+区画化のみ — hardware 未取得のため軽量案も可)。
4. Step-0 一括承認(tracked 化 6 + VGroove ' M' commit)。

## §10 Changelog

- v0.1-DRAFT(2026-07-11 00:4x JST): 初版。inventory・LEDGER 照合・cite 実数・invariance script 案・batch 設計。次 = 5体 debate(L3 pre)。

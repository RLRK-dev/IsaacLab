# Rs 上程 — ゲート改訂 6 条

**起票: %12 RS-TECH-LEAD (実、fork-resume session `59f43438`)、2026-07-14 07:4x JST**
**Rs 指示 (pK 経由 07:38): 「ゲート改訂 5 条を上程の形にまとめよ。実装するな (`.claude/skills/*` = L3 = Rs 専権)。」**
**⚠ 本文書は *提案* である。%12 は self-start しない。**

---

## 0. 一行要約

> ⭐ **本件は metric bug ではない。「これは測れない」という *証明済みの banked 知見* が実装に届かず、成功条件が壊れたまま採用され、忠実性契約でロックされた。**
> ⭐⭐ **そして — 我々はそれを止めるゲートを *持っていた*。走らせると `PASS` を返す。**
> ⇒ **fix は metric でも env でもなく、*ゲート* に打つ。**

---

## 1. 何が起きたか (3 層)

### L1 — metric: 計器の 3 重失敗 (全て on-disk 実測、%12 独立検証済)

| | 病理 | 根拠 |
|---|---|---|
| **(a) FAIL できない述語** | `c1_retained` (`newton_route_env.py:1479-1483`) = `z<0.840 ∧ flank<0.840` = **天井チェック、X 不参照**。凍結 recount 81 cell で **81/81 no-op**、`strict_v2`(58) == `c2_seated_honest`(58) **厳密一致** ⇒ **C1 の連言はタダ** | %12 code 実読 + p1 実測 |
| **(b) PASS できない述語** | 溝は **Y 押し出し** (`create_clip.py:68`) ⇒ **Y = 自由軸**。G3 (`:1550`) は **XY ノルム**で採点 ⇒ **自由軸 dy を着座誤差として課金**。node 間隔 14.64mm ⇒ **\|dy\| 床 7.32mm > bar 3.0mm** ⇒ **bar は分解能の 2.4 倍細かい = 抽選** ⇒ **G3 は 24/81、G6(+200) は demo 分布の 70% で到達不能。物理は 81/81 で着座。** | %12 が正典 golden (`5f1c3f92…`) から再導出 / p1・p6・%10 独立 CONFIRM |
| **(c) そもそも測れない** | **「lateral groove-capture: NO numeric coverage (contact ≠ capture, **proven**); **Rs-video is the only ground-truth**」** — `harness/state/ANCHOR_STEPTABLE_ALIGNMENT_p4p5_20260712.md:107-108`、**07-12 に proven + banked (%12 共著)**。以後の全計器試作が positive control で死亡 (p1 の \|dx\| 計器は **Rs が目視却下した cell 2037 を PASS**) | p1 発見 / p5 source / p6 negative control |

⭐ **(a) と (b) は互いを隠す**: 鳴らない警報と、「難しい課題」に見える欠落。**どちらも沈黙する。**
⭐ **campaign を回していれば、agent は 70% の cell で成功信号をゼロ受信し「RL が効かない」と誤診されるところだった。数週間の GPU が壊れた計器の上で焼かれる。**

### L2 — 定義: two-key は *実装* の独立性しか持たなかった

| # | 段 |
|---|---|
| 1 | **PREREG spec v0.9 (`1f074169a1`)** が `c1_retained_final` を **天井チェック**として定義 — **欠陥の起源** |
| 2-3 | %12 と p1 が **独立に** 実装 (`recount_strict_v2.py` / `p9_recount_strict_v2.py`) — **two-key check として** |
| 4 | **一致** ⇒ ⛔ **その一致が *妥当性の検証* として読まれた** |
| 5-6 | env が p1 の script を「**the EXACT frozen def**」として名指し、**DoD-9a が parity を契約で強制** — 逐語「**never by loosening tol**」= **直すための逸脱すら禁止** |
| 7 | ⇒ ⛔ **欠陥は忠実性契約でロックインされ、「独立検証」がそれを authorise した 2 本の鍵の 1 本になった** |

⭐⭐ **両方の鍵が *同じ定義* を encode していれば、一致は必然であり何も証明しない。独立性は *実装* でなく *定義* の水準で要る。** ⇒ **「0.716 は two-key で検証済」は *妥当性の* 検証ではない。**

### L3 — governance: ⭐ **ゲートは在り、必須で、そして `PASS` を返す**

**%10 / p3 が必須の prior-art gate (CLAUDE.md §運用4・AGENTS.md で *必須*) を実走:**
```
$ bash scripts/check_thread_vault_prior_art.sh "lateral groove-capture" "contact capture"
findings=0 blockers=0 lessons=0
PASS: no related prior-art hits found in configured roots.
```
⛔ **一方、原典は on-disk に実在** (`harness/state/ANCHOR_STEPTABLE_ALIGNMENT_p4p5_20260712.md`)。
⭐ **原因 (%12 が実測して決着)**: `check_thread_vault_prior_art.py:29-32` の **`DEFAULT_ROOTS = (thread_isaac_lab/thread-vault, docs, eval_runs)`** — ⛔ **`harness/state/` は探索対象に *含まれていない*。**
⚠ **p6 は同 gate で `BLOCKER_CONTEXT_FOUND` を得たが、それは原典ではなく *今夜 07:20 に %12 が spec へ書き込んだ引用* に当たったもの** (`git log -S` で初出 07-14 07:20 を確認)。⇒ ⭐⭐ **07-12 当時、ゲートは PASS を返していた。今 BLOCK するのは、我々が偶然、今夜、finding を探索範囲内に引用したから。** ⇒ ⭐ **ゲートの被覆は *偶然* である。** (p6 own 済)

⭐⭐⭐ **∴ prior-art gate 自身が、今夜の全欠陥と同じ class である: 対象を被覆していない計器が、hit ゼロを「先行事例なし」と読み替えて PASS を返す。出力文言「no hits **in configured roots**」は scope 限界を自白しているのに、verdict は PASS。** ⇒ **「FAIL できない述語」が governance 層に在る。**

---

## 2. ⇒ ゲート改訂 6 条 (Rs 裁定を仰ぐ。**%12 は self-start しない**)

| # | 条 | 出自 |
|---|---|---|
| **1** | `/reward-design` に **Artifact 0 = banked-gap 照合** — 述語を作ろうとしている *量* について、vault に「NO numeric coverage」「cannot measure」「X is the only ground truth」の banked annotation が無いか照合。**在れば numeric 述語は作れない ⇒ escalate。** ⚠ **keyword は人の思いつきでなく、*量の名前・軸・単位から機械的に導出*** (p6)。**+ ゲート実行の *証跡* を DoD の required artifact に** (走ったか否かが後から検証可能になる)。 | p1 + p6 |
| **2** | **Reachability Table は *demo 分布全体* で取る** (単一 nominal cell 禁止)。⚠ **ゲートには reachability レグが *既に在る* — 走らなかったか、1 cell で走った。24/81 は分布上でしか出ない。** | p1 |
| **3** | **強制ゲートは *コードの新規性* でなく *述語の役割* で発火する** — 「reward/成功条件の述語を **定義する / 採用する / 鏡写しする** のか?」→ YES なら発火。**reference を mirror することは免除にならない。** ⇐ **移植者はゲートを呼ばない。自分が設計しているとは思っていないから。** | p5 |
| **4** | **パリティ / 忠実性の契約は、妥当性ゲートを *discharge できない*。忠実性ゲートは妥当性ゲートに *従属* する。** 順序を逆にすると **忠実に壊れたものを増やす。** | p5 |
| **5** | **prior-art gate の探索 root に `harness/state/` 等の banked 面を入れる** — **実証済** (上記 L3)。**+ 「hit ゼロ」で PASS を出さず、*どの root を探索したか* を必ず出力し、既知 SSOT 位置が root に無ければ fail-loud。** | p3 + %10 |
| ⭐**6** | **(一般形) 全ての gate と全ての不在主張は、*分母を宣言し*、それが述語の空間を *覆う* ことを示す。** 機械化: **「述語 P は空間 S に住む。私の分母は S から取った。根拠は ___。」の 1 行が書けないなら、主張は無い。** ⇒ **(5) は (6) の 1 実例。(6) が無ければ、次に作る gate が同じ穴を持つ。** | p5 + pF |

⛔ **(3)(4) が無ければ (1)(2) は *今回と同じく発火しない*。(6) が無ければ (5) を足しても *次の* gate が盲目になる。**

---

## 3. なぜ 6 条が要るか — **今夜の失敗は 1 つの形しかなかった**

**「分母が、主張する述語と *別の空間* から取られていた」**

| 事例 | 述語の空間 | 使われた分母 | 向き |
|---|---|---|---|
| ghost 掃引 ①-④ (pF) | 生きた session / プロセス停止 / branch 上の commit / 全 project 履歴 | 06:34 凍結の一覧 / 書込 mtime / HEAD 系譜のみ / 単一 dir | **過小** |
| commit 掃引 (p5) | *現ブランチ上の* commit | `git log --all` (worktree 含む) | ⭐**過大** |
| prior-art gate (p3/%10) | 既知 finding の全て | root = `thread-vault` のみ | 過小 |
| clip 衝突 (p1) | ***実行時* の値** | **コードの既定値** | 別空間 |
| reachability leg | demo 分布 | 単一 nominal cell | 過小 |
| ⭐ **two-key 独立性** | **定義** の空間 | **実装** の空間 | 別空間 |
| ⭐ **c1_retained** | **溝への捕捉 (X 軸)** | **天井高さ (Z 軸)** | 別空間 |

⭐ **不在主張の誤りは *両方向* にある** (過小は隠し、過大は捏造する)。⭐ **そして gate 自身も、memory 索引自身も、同じ穴を持つ。**

⚠ **pF 実測 (推測と区別して報告)**: **MEMORY.md = 28,416 bytes / 宣言された読込上限 ≈ 24,985 bytes ⇒ 3,431 bytes 超過。** ⇒ **今夜 bank した教訓を載せた索引そのものが、自分の読込上限を超えている。** (truncation は直接観測していない ⇒ **超過 = 事実 / 「recall が壊れている」= 推測**。)

---

## 4. 併記 — 未決の Rs 裁定 3 件 (本上程と独立)

- **(A)** **計器を直してから B3b-B7 を再開** — fix = 折れ線を y=CLIP_Y で補間し **3 連言** (\|dx\| ≤ 3mm ∧ \|z − ROUTE_GROOVE_Z\| ≤ 3mm ∧ **wall-only 接触 ≤ 0.5mm**) / **`obs[49]` も同じ汚染 ⇒ 同時差替え** / **bar は緩めない**。⚠ **env 単独では打てない** (DoD-9a parity) ⇒ **env + offline + PREREG の 3 点同時改訂 = spec 層。**
- **(B)** **p5 に両壁 form-closure 着座指標の設計を授権** — ⭐ **受入条件が確定: 「Rs 却下 cell `2037` を *FAIL* し、真の着座 cell を PASS する」(両方向 control)。** ⚠ `c1_wall_dist_spacer_excluded_mm` は未 emit ⇒ **producer 再走が要る。**
- **(C)** **pin (INVARIANT #5) を RL env へ *恒久* 配線してよいか** — B3-α。**(d2) の最小配線は *測定* の授権であって採択ではない。**

### ⭐ 新規 (%12 実測、07:38) — **(d2) 腕 D を追加した**

| | ke | kd | gap |
|---|---|---|---|
| producer C1 (`test_newton_clip_routing.py:1179-1185`) | **40000** | 400 | 0.002 |
| RL env C2 (`newton_skill_env_base.py:1884-1890`) | **40000** (record-matched) | 400 | 0.002 |
| ⛔ **RL env C1** (`:1855-1862`) | ⛔ **2500** | **100** | **0.001** |

⭐ **RL env の C1 クリップだけが producer の 1/16 の接触剛性。C2 は記録一致。** ⭐ **code 自身が `:1880` で「record-matched, **NOT C1's soft 2500**」と *注記している*** ⇒ **既知・注記済・放置 = 「注記されたが強制されない」の 3 例目。**
⇒ **腕 D = 腕 A と同一、ただし C1 剛性を producer に一致 (flag-gated、default OFF)。問い: 「C1 の接触剛性を記録に合わせるだけで横滑りは消えるか?」** ⚠ **測定であって設計採択ではない。恒久化は Rs 裁定。**
⚠ **先行して pB の probe (Newton `shape_flags=0x6` が MuJoCo 変換後に本当に `contype/conaffinity` になっているか) を走らせる** — **source の存在 ≠ runtime の liveness** (我々の banked 教訓 ERRATUM-F)。

---

## 4-b. ⭐ D-5 — canonical step-table の 5-seg 汚染 (p5、**Rs 裁定待ち**)

**`RL-Routing-Design.md` §2.1 の clip↔groove body 対応 (C1=30 / C2=25 / … = **5 seg = 75mm**) は幾何的に不成立。**
- **千鳥 hop 弦長 = √(50²+75²) = 90.14mm**、非伸長 cable は **arc ≥ chord** ⇒ **正 = ≥7 seg** (⚠ **6 seg = 90.0mm は 0.139mm 不足** = 剃刀の縁)。
- **origin**: config コメント「5-clip span 300mm」が **Y 投影のみ**を見ており、**千鳥の 50mm が計算から脱落** (真の折線長 = 4×90.14 = **360.6mm**)。
- **正値** (p5 の幾何 witness `GEOM_WITNESS_5CLIP_p5_20260714.py`、6/6 PASS。**p6 が SSOT から自前導出で独立検算 → 全項一致**、p1 も独立確認): **C1:33 / C2:26 / C3:19 / C4:12 / C5:5**。

⭐⭐ **p5 の対処が、本上程の第 8 条の *実演* である (commit `0778881d28`)**:
- ✅ **§2 逸脱台帳に D-5 を登録** + **§1.4:109 に ERRATUM を掲示** (「本行の seg 数・body 番号を接地に使うな」)
- ⛔ **body 番号は *一切変えていない*** ⇒ **banked §2.1 の faithful restate を維持**
- ⭐ **理由: canonical の訂正 = 07-Design = Rs 専権。黙って直せば「鏡写しすべき SSOT」から乖離する。**
⇒ ⭐⭐ **∴ 「忠実に restate し、欠陥を loud に掲示し、訂正は権限者に上げる」= 条 8 (ゲートの finding は *既存コードの欠陥項目* を開く。新規コードがそれを避けることで discharge されない) の正しい適用。**
⇒ ⛔ **Rs 裁定待ち = canonical (§2.1) の訂正のみ。表側は記録済・faithful restate 維持。**

---

## 5. ⛔ 撤回した主張 (上程に含めない)

- ❌ **「clip は衝突を持たない ⇒ 何も保持できない ⇒ 全 clip に pin が要る」** (%12 + p1) — **producer も RL env も clip は COLLIDE** (`newton_skill_env_base.py:1876` = `0x6` / `w0e_81rerun_runner.sh:21` = `CLIP_COLLISION=1`)。**コードの既定値を実行時の値と取り違えた。1 コマンドで反証される負債ゆえ外す。**
- ❌ **「0.716 は水増しでない / 危険は前向きであって遡及的でない」** (p1・p6・%10 が伝播、全員撤回) — **救済に使った計器が Rs 却下 cell を PASS させる。** ⇒ ⚓ **「58/58 で溝の中」は未確保 (偽ではない)。「0.716 は無効」も未確立。**
- ❌ **「5-clip は配位空間の外」系の壁 4 説** — **4 説とも崩壊** ((d1) CLOSE)。⚠ **「壁が無い」≠「達成できる」— witness は静的配置であって軌道ではない。**

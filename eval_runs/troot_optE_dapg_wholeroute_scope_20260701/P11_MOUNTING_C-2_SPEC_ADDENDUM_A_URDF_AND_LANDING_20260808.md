# P11 別紙 A — banked spec への 2 件の追補（URDF 由来 / 着地順の読み）

desk: p11 ARM-CONTROL-DESIGN (w2:p11) / 記録 **2026-08-08 22:25:51 JST**（`date` 実測）
対象 = `P11_MOUNTING_C-2_IMPL_DESIGN_SPEC_20260808.md` @ **`3315631007`**（content sha256 `a7c116df…4d3b42c7`・p4 受入 `e39526fe58`）
⛔ **本紙は別紙**。banked spec 本体は**編集しない**（受入済 sha を動かさない・凍結物は別紙で訂正する型 = Rs 07-21 裁定）。⛔ 設計のみ・実行なし。
契機 = p18 m-p18-102 の p11 宛 flag（EFFORT/LIMS の URDF 由来）。**以下は全て本 session の第一手実測**。

---

## A-1. LIMS は動力学定数であるだけでなく、**witness の抽選領域**だった（spec §3.1/§7 の射程に効く）

**実測（`ur15_steps_wired.py`）**:
- `:1130` `LIM = np.array(LIMS)  # the URDF values, read by the spec module`
- ⭐ `:1972` `q = rg.uniform(LIM[:, 0], LIM[:, 1])` — **開始姿勢 IK の種は URDF 関節範囲の一様抽選**。回数 = `START_TRIES`（既定 24・grid と本 spec は 240 = `:2418`/`:2456`）。
- `:1136-1138` ±2π 巻き戻しの可否・`:2002` IK ステップの clip・`:2025` 近傍解の受理も `LIM` が決める。
- 動力学側は別口: `:315` `a.forcerange = ±EFFORT, a.ctrlrange = LIMS`。

⇒ ⭐ **spec の witness（L clear 5 / R clear 30 @ 240 draws）は「URDF の関節範囲を領域として」得られた existence である**。本 spec は witness を「運動学量ゆえ整定非依存」と書いた（§5b-1）— それは真だが、**URDF 非依存という意味ではない**。⇒ **existence 主張の射程に「抽選領域 = `ur15_mj.urdf` の `<limit lower/upper>`」を加える**（従来の 2 条件〔stereo head 不在・#54 部材不在〕に並ぶ 3 つ目）。

## A-2. 出所（provenance）— 失われたのは *作業複製* で、**公式の上流は在り、監査は閉じた**

**実測**:

| 項目 | 実測 | 出所 |
|---|---|---|
| URDF 冒頭の生成元 | `/tmp/…/b952db35-…/scratchpad/urdf_work/ur.urdf.xacro` | `ur15_mj.urdf:3` |
| その dir | **不在**（`No such file or directory`） | `ls` 実測 |
| URDF 自体 | **tracked**・worktree == HEAD blob `2494cab707…`・**content sha256 `b4c60d4d18c1ec2b243b2baa0b0d4d8e9a49504bf1b41bce7e3ea0deb1c6b57d`** | `git ls-files` / `git rev-parse` / `sha256sum` |
| 公式 description | **在る** — `/home/rlrk/src/ur15-line-render/assets/Universal_Robots_ROS2_Description/`（**同名 `urdf/ur.urdf.xacro` + `config/ur15/joint_limits.yaml`**） | `ls`/`find` 実測（既知 = 私の 07-27 disposition `:55`） |

**監査（arm 6 関節の `<limit>` を公式値と突き合わせ・本 session 実施）**:

| joint | 公式 `config/ur15/joint_limits.yaml` | `ur15_mj.urdf` の `<limit>` | 一致 |
|---|---|---|---|
| shoulder_pan | effort 433.0 / ±360° | 433.0 / ±6.283185307179586 rad | ✅ |
| shoulder_lift | 433.0 / ±360° | 433.0 / ±6.283185307179586 | ✅ |
| elbow | 204.0 / ±180° | 204.0 / ±3.141592653589793 | ✅ |
| wrist_1 / _2 / _3 | 各 70.0 / ±360° | 各 70.0 / ±6.283185307179586 | ✅ |

⇒ ⭐⭐ **p18 の「regenerate も source 照合もできない」は 1 点狭められる**: 消えたのは **/tmp の作業複製**であって、**同名の公式 xacro と公式 ur15 関節諸元は on-disk に在り、URDF の腕 `<limit>` 6 行は公式値を厳密に再現している** ⇒ **EFFORT/LIMS についての監査は閉じた（CLEAN）**。
⛔ **閉じない残り（一般化しないこと）**: ①消えた作業複製が公式 xacro と byte 一致だったかは**原理的に確かめられない**（腕 `<limit>` については「差が無い」と示せたが、それは複製の同一性の証明ではない）②**URDF の他の内容（mesh 参照・慣性・link 幾何）は未監査** — 本紙は 6 行についてのみ CLEAN と言う。
⇒ **恒久の錨は content pin**（`b4c60d4d…`）— 出所が辿れなくても **commit から再現できる**（本 project の「pin は content で持て」の型）。

**私の 07-27 裁定は substance 不変**（`P11_UR15_DESIGN_DISPOSITION_20260727.md:5152` 逐語「**EFFORT / LIMS = court 外**（URDF 由来・reader ✅）」・`:5133` fail-closed reader = `<limit>` 欠落で raise）。変わったのは**根拠が 1 段強くなった**こと（公式照合 + content pin）と、**A-1 の射程が付いた**こと。⚠ #39（UR5e 由来の動力学測定は流用不可・廃棄範囲未確定）は**本件と別軸**で不変 — 本紙は τ_bias/Jacobian/damping に触れない。

## A-3. 着地順の読み（spec §6-4 の解釈固定 — p0 が矛盾に挟まれないように）

- banked spec `:201` §6-4 逐語 = 「本 branch (`rlrk/optE-s2-substrate-swap`) 上で行う」。**執筆は p18 の着地順裁定より前**。
- 現在の確定（m-p18-99/-100/-101）= **p0 実装 → pZ 検証 → その後に着地**。加えて p18 推奨（採否 = **p4/p0 の court**）= 実装は **lane 外 branch** へ commit し sha を pZ へ、pZ は **fresh detached worktree** で content pin 検証、着地は lane。
- ⇒ ⭐ **§6-4 が固定しているのは「最終的にどこへ着地するか（= lane）」であって、中間の commit 先でも順序でもない。** 従って **p4 が推奨を採る場合、lane 外 branch を経由することは §6-4 と矛盾しない**（むしろ §6-4 の「lane に着地」を満たす唯一の順序整合な形）。⛔ **§6-4 を「検証前に lane へ直接 commit してよい」と読まない**。
- 変わらないもの: commit 規律（explicit pathspec 限定 + `--no-verify`〔DDR#35〕）は中間 branch でも lane でも同じ（spec §6-3）。

## A-4. 追加する pZ 項目（spec §7 への追補・番号は続き）

13. **URDF の content pin**: 検証記録に `ur15_mj.urdf` の **content sha256 `b4c60d4d…b57d`** を記載する（生成元 xacro の作業複製が消えているため、**content pin が唯一の恒久錨**）。⚠ 併せて existence 主張の射程に「**抽選領域 = 当該 URDF の関節範囲**」を書く（A-1）。⇒ spec §7-12 の cell 条件は **3 条件**になる: stereo head 不在 / #54 部材不在 / **URDF 関節範囲を領域とする抽選**。

## A-6. 追記 22:39 — banked spec §1 の不在主張に**母集団**を付ける（契機 = p18 m-p18-103 §2 の規則改訂）

**対象の主張**（banked spec `:31` 相当）= 「**コード上の導出は `ur15_cell_spec.py:432` の 1 箇所のみ**」。⚠ v1/v2 執筆時に私が実際に走らせたのは **2 file を名指しした grep** であり、「他 file に無い」と書ける母集団を測っていなかった（debate CC3 が語り過ぎを指摘し v2 で文言は直したが、**母集団は依然無記載**だった）。⇒ 閉じた query を 2 経路で走らせ直した。

**結果（本 session 22:38-22:39・rc を毎回確認）**:

| 経路 | 母集団（自分で計測） | `YOKE_SPREAD/2` の `.py` hit | rc |
|---|---|---|---|
| A: `git grep`（tracked） | tracked **5,262** file（うち `.py` **2,036**） | 5 箇所 | 0（走行・hit あり） |
| B: `command grep -r`（ignore 規則なし = tracked + untracked + ignored） | disk 上の `.py` **43,032**（worktree 複製を含む） | **同じ 5 箇所** | 0 |
| B'（worktree 複製のみ・別計測） | `.claude/worktrees` + `.codex/worktrees` = 4 本 | **0** | **1**（= 走って hit 無し。⛔ rc 1 と 127 を混同しない） |

**5 箇所の内訳** = **実行される導出は 1 つだけ**: `ur15_cell_spec.py:432`（`:429` の 4 分岐 chain の最終 else）。残り 4 は文字列 — `ur15_cell_spec.py:426`（注記）/ `sweep_mounting.py:258`（print）/ `:288`（comment）/ `compare_24_vs_240.py:78`（print）。
**`CROWN_R` の代入点**（同 2 経路）= `.py` で **`ur15_cell_spec.py:429` の 1 箇所のみ**。⚠ `ur15_steps_wired.py:174`/`:179` は hit するが **comment と print の文字列**であって代入ではない（実読で判別）。

⇒ ✅ **spec §1 の「編集点は単一」は 2 経路・上記母集団で成立**（v2 の文言も維持）。⛔ **覆っていない範囲を明記**: 非 `.py` の実行面は本 query の外（本 cell は Python で組まれるため既知の面は無いが、「無い」ことを測ってはいない）／worktree 複製は**別立てで測り 0 と確認**（フィルタで隠していない — 表示から除外した集合を測らずに済ませると、それ自体が作られた不在になる）。
⭐ **私が引き取る形**: 名指し file への grep は**その file についての主張しか閉じない**。「他に無い」と書くなら、書く前に母集団を測って併記する（p18 §1195 = cardinality は membership を答えない、の同型 — 私の側は「2 file の counts で全体の membership を語っていた」）。

### A-6b. 追記 23:11 — A-6 の「同じ 5 箇所」を**目視でなく判別力のある検査**で確定（契機 = p18 m-p18-106 §1 membership/path-form）

⚠ A-6 の集合等価は **2 つの印字を目で見比べて**書いていた。両経路は**同じ object を別の文字列で描く** — 実測: route A `eval_runs/…/compare_24_vs_240.py:78` / route B `./eval_runs/…/compare_24_vs_240.py:78`（先頭 `./` の有無）。⇒ 正規化（`sed 's#^\./##'` → `path:line` 抽出 → `sort -u`）して `comm` で測り直した:

- **A-only 0 / B-only 0 / 共通 5 / `diff` rc=0**（`git grep -- '*.py'` rc=0・`command grep -r --include='*.py'` rc=0）⇒ **A-6 の等価主張は成立**（結論不変・根拠が目視から集合演算へ）。
- ⭐ 副次: 今回の route B は **worktree を除外せずに**走らせて同じ 5 ⇒ **worktree 複製の寄与 0** が A-6 の B'（rc=1）と独立に一致。

**母集団の言い切り方も直す**（p18 §3 で採用された形に合わせる）: 本主張は「**現在の作業ツリー（tracked + on-disk）に他の導出は無い**」であって「**project の履歴のどこにも無い**」ではない。⛔ 履歴（過去 rev の range）は**未測・本紙は主張しない**。⇒ p0 が編集するのは現在の file ゆえ、実務上これで閉じる。

## A-7. 追記 23:2x — **本 chunk の DoD を折り畳んでいた**（spec §0 と §9 の当該文を supersede・契機 = p4 の scope 訂正 / p18 m-p18-107 §1 が私の court として回付）

**私の欠陥**: banked spec は §0 と §9 で「**chain DoD = 43-step scripted route 動画（裁定 A）**」と書いた。裁定 A の引用自体は正しいが、それは **p4 の任務定義**であって **本 chunk が C-2 cell で出せる受入 artifact ではない**。2 つの scope を 1 文に折り畳んでいた。

**実測（本 session・controlled predicate と rc つき）**:

| measurement | 実測値 | 出所 |
|---|---|---|
| live cell の clip 定義 | **C1 `(0.150, CLIP_Y_ODD)` / C2 `(0.040, CLIP_Y_EVEN)` の 2 個のみ** | `ur15_cell_spec.py:485`/`:486`（`^C[12] *=` rc=0 = 陽性対照） |
| 同 predicate で C3/C4/C5 | **0**（`^C[345] *=` **rc=1** = 走って hit 無し） | 同 file |
| `\bC[345]\b` を live 2 file 全体で | **0**（rc=1） | `ur15_cell_spec.py` + `ur15_steps_wired.py` |
| 実行される STEP | **STEP 1**（`:2509` 逐語「the arms REACH the start pose by servo motion」）＋ **STEP 表 2-18**（`:2639`）= 表 row **17 本を計数**・最終 row = `(18, "上昇", …)` ⇒ **計 18** | `ur15_steps_wired.py` |
| canonical row 18 | 述語 **{c1_retained ∧ c2_retained}** / verdict source **N** | `eval_runs/troot_verbal_teaching_20260705/CANONICAL_MOTION_TABLE_V1.md:141` |
| canonical row 43 | 述語 **{c1∧c2∧c3∧c4∧c5_retained}**（whole-route 分子）/ verdict source **R（whole-route 最終 = Rs 動画）** | 同 `:160` |

⇒ ⭐ **訂正（本紙が正・spec §0/§9 の当該文を supersede）**:
- **本 chunk（C-2 mounting）の受入 = canonical 1-18 を C-2 cell で走らせた動画**（row 18 述語 = C1・C2 保持 / verdict source N）。
- **裁定 A の 43-step / 5-clip whole route = 任務定義**（row 43・verdict source **R** = Rs 動画）。**live cell に C3-C5 は無い**ので本 chunk の設計では到達できない。**5-clip 化の scoping は Rs の court・別 chunk**（p4 が routing 済）。本 spec はそれを scope していないし、していると読まれてはならない。
- ⚠ **「2 of 5 だから本 chunk は不足」と採点しない**（pZ の pre-commitment を採用）— それは **row 43 を本 chunk に当てる誤った行の測定**。本 chunk が答える行は row 18。
- **evidence-grade cap は不変**: #48/#18 open の間は無印 PASS を出さない・#49 はゲート状態併記・#61 の env pin・cell 条件 3 件（stereo head 不在 / #54 部材不在 / URDF 関節範囲）。

**⚠ 併せて記録する label の罠（p4 発見・当方実測）**: 同じ名前 C1/C2 が **substrate で別の点を指す** — task 側 `task_config.py:212` C1 = (0.35, +0.150) … `:216` C5 = (0.35, −0.150)（5 clip）に対し cell 側 `:485` C1 = (0.150, …) / `:486` C2 = (**0.040**, …)。⛔ **C2 は 0.40 と 0.040 で桁も違う**。⇒ **C1/C2 を引くときは必ず substrate を添える**。本 spec §7-6（「C1/C2 の値が変更前後で同一」）は **同一 file 内の比較**なので成立するが、pZ は**跨いで突き合わせない**こと。

### A-7b. 追記 23:3x — A-7 の label 注記を **2 点訂正**（私の書き方の欠陥 1 + 罠の本体の言い直し 1・契機 = p18 m-p18-109 §8 / p0 発見）

**訂正 1（私の欠陥・形の捏造）**: A-7 は task 側を「`task_config.py:212` **C1 = (0.35, +0.150)**」と**代入の形**で書いた。**値は実読どおりだが形は実在しない**。実測: `git grep -nE '^C[1-5] *='` は `task_config.py` で **rc=1（走って hit 無し）**・同 predicate は cell spec で `:485`/`:486` を返す（**陽性対照**）。⇒ 実体は **`CLIP_POSITIONS` の list 要素に付いた行末コメント**（`:212` `(CLIP_X_ODD, CLIP_Y_CENTER + 2*CLIP_Y_SPACING),  # C1: (0.35, +0.150)` … `:216` `# C5: (0.35, -0.150)`）。⛔ **代入として書くと、次の読み手は `C1 =` を探して見つからず「無い」と読む** — 私が今日 3 度名指した「作られた不在」を、自分の sheet で作りかけた。

**訂正 2（罠の本体は「別の点」より強く、軸の入れ替え）**: 実測 — `task_config.py:203 CLIP_X_ODD = 0.35` / `:204 CLIP_X_EVEN = 0.40`（**X の役**）に対し `ur15_cell_spec.py:483 CLIP_Y_ODD, CLIP_Y_EVEN = 0.35 + WORK_ROW_DY, 0.40 + WORK_ROW_DY`（**同じ大きさが Y の役**）。⇒ ⭐ **値の集合を突き合わせると「0.35 も 0.40 も両側にある」で通ってしまい、転置は値検査を生き延びる** ⇒ **(軸, 値) の対で比べる**。A-7 の「同名が別の点を指す」は真だが弱い言い方だった。
**併せて**: cell 側の clip x（`0.150` / `0.040`）は **cell 内の literal** であって task 側 `CLIP_POSITIONS` から導かれていない。⇒ **clip 座標については executable は task_config に束縛されない**（他の定数 — cable 半径・把持スパン・clip 接触 — は `ur15_cell_spec.py:52`/`:60`/`:66-67` 経由で task_config に束縛される）。⛔ **どちらの SSOT が勝つかは本紙で裁定しない**（#46 / Rs の軸）。⇒ spec §7-6 は**同一 file 内の前後比較**ゆえ成立・**pZ は clip 座標を substrate 跨ぎで突き合わせない**。

## A-8. 追記 23:3x — spec の中心主張「変更は cell 側で閉じる」を**検証可能な述語**にする（pZ 項目 14 新設・契機 = p4 の測定 / p18 m-p18-111 §4）

banked spec §0/§2 H5/§3.4 は「**C-2 は cell 側で閉じ、task 幾何を汚さない**」と主張していたが、**主張のまま**で pZ が測れる形になっていなかった。⇒ 述語化して当方で実測（陽性対照つき）:

| 検査 | 結果 |
|---|---|
| STEP 表領域（`ur15_steps_wired.py` 2639-2760）に mounting 定数（`YOKE_SPREAD` / `CROWN_R` / `CROWN_ZC` / `TILT` / `SHOULDER_HEIGHT` / `COLUMN_R`）が現れるか | **0（rc=1 = 走って hit 無し）** |
| **陽性対照**（同領域・同形式で `GRIP_HALF_SPAN` / `C2[` / `GL[` / `GR[`） | **13 hit（rc=0）** ⇒ 述語はこの領域に当たれる ＝ 上の 0 は判別力のある 0 |
| 目標値の出所（実読） | `:91 Z_SEAT = GROOVE_Z` ／ `:1121-1122 GL/GR = GRASP_CENTRE_X ∓ GRIP_HALF_SPAN`（y,z は実測 cable）／ `:2625-2626` 同（実測 cable）／ `:2642 RX_MID = mean([C1[0], C2[0]])` |

⇒ ✅ **STEP 2-18 の直交座標目標は cable・clip・指令スパンの関数であって、取付の関数ではない** ⇒ **mounting を C-2 へ動かしても route の目標点は動かない**（spec の confinement 主張が、断定から**測れる述語**になった）。
⛔ **これが establish しないこと（over-read 防止・当方で先に塞ぐ）**: 「動きが同じ」ではない。**同じ目標へ別の取付から到達する以上、IK 解と経路は変わる** ⇒ 経路の干渉は依然 carry（spec §3.5c step 2）であり、答えるのは DoD 動画 + pZ + Rs human-GT。

**pZ 項目 14（新設）**: 実装 diff 後に上表の 2 行（mounting 定数 = 0 / 陽性対照 = nonzero）を**同じ形で再実行**し、rc とともに記録する。⇒ confinement は「設計時にそうだった」ではなく「landing 後も成り立つ」形で検査される。

⚠ **witness の取り違え防止（同名 2 個・当方実測・契機 = p18 m-p18-111/-112 が別 witness の substrate 欠落を指摘）**: 今夜「witness」は **2 つの別物**を指している。⑴ **5-clip の L-geom witness**（2026-07-14・6/6 PASS）は **task_config の clip 配置**の上で計算されたもの（0.35/0.40 が **X** の役）。⑵ **本 spec の C-2 witness**（開始姿勢 clear・240 draws）は **cell 配置**の上の測定 — 計器 `sweep_mounting.py` → `ur15_steps_wired.py` は **`ur15_cell_spec` を import**（`:39`/`:55`・rc=0 = 陽性対照）し、**`task_config` を import しない**（`^ *(from|import) .*task_config` = **0 / rc=1**）。⇒ ⛔ **⑴ を本 chunk の幾何的裏づけとして引かない・⑵ を 5-clip の主張に使わない**。本 spec が立っているのは ⑵ のみ。

### A-7c. 追記 23:38 — A-7b の「転置」は **C1 でしか成立しない**（当方で算術を再導出・契機 = p0 測定 / p18 m-p18-113 §4）

A-7b は罠の本体を「**軸の転置**」と名付けたが、**その名前は 2 clip 中 1 個にしか当たらない**。source の構成定数から組み直して再計算（⛔ 行末コメントの数値は使わず `CLIP_X_ODD/EVEN`・`CLIP_Y_CENTER`・`CLIP_Y_SPACING`・`WORK_ROW_DY=0.0` から合成。`env_isaaclab7` の python で実行）:

| clip | task 側 | cell 側 | 厳密な転置か |
|---|---|---|---|
| C1 | (0.350, 0.150) | (0.150, 0.350) | **True** |
| C2 | (0.400, 0.075) | (0.040, 0.400) | **False** |
| **C1→C2 の弦** | **90.14 mm** | **120.83 mm** | **比 1.3405 倍**（15 mm pitch 換算 6.01 対 8.06 節） |

⇒ ⭐ **2 面は「1 つの読み替え（転置）」では関係づかない** — C1 だけが転置で、C2 は違う。⇒ ⛔ **C1 だけで値検査すると通る**（見た目に分かりやすい方でなく、欺く方の並び）。
⇒ ⭐⭐ **より強い言い方（かつ測定済）**: 両面が共に定義する唯一の hop が **cell 側で 1/3 長い**。「carry は未確立」ではなく「**測ってあり、違う**」。⇒ A-7b の (軸, 値) 対で比べる規則は有効なまま・**「転置」という名前だけを撤回**する（1 個の例から関係全体に名前を付けていた）。
⚠ 本 chunk への影響 = **なし**（本 spec は cell 面のみで閉じ、task 面の clip 座標を引かない = A-7b/A-8）。本節は**引用する側**への警告。

## A-9. 追記 23:4x — **pZ 項目 14 の計器を差し替える**（A-8 の項目 14 は本節が supersede・発見 = pZ / 回付 = p18 m-p18-116・決定 = p11）

**pZ が指摘した 2 欠陥（当方で確認・いずれも成立）**:
1. **領域行は主張を運べない**: A-8 自身が引いた目標の出所（`:91` / `:1121-1122` / `:2625-2626`）は **どれも窓 2639-2760 の外**。⇒ 例えば `:2625`（窓の 14 行上）で mounting 定数が目標へ入っても、領域 scan は**見ない**。confinement を支えていたのは領域行ではなく **file 全体での局在**だった。
2. **anchor が使う瞬間に腐る**: 項目 14 は「landing 後に同じ 2 行を再実行」と書いたが、**diff は行を挿入する** ⇒ literal `2639-2760` は別のコードを指し、**0 を返し続けながら別物を測る**。

**差し替える形（当方で実装・実行済。literal 行番号を述語に持たない）**:
- **対象語**は spec の mounting block から**機械導出**（`ur15_cell_spec.py` の柱・冠・ヨーク系 10 語 = `YOKE_SPREAD` `TILT` `CROWN_R` `CROWN_ZC` `CROWN_Z0` `SHOULDER_HEIGHT` `COLUMN_R` `COLUMN_HZ` `COLUMN_STEM_BOTTOM` `COLUMN_STEM_H`）。⚠ 作業列・什器（`REST_*` `TABLE_*` `FLOOR_*` `WORK_ROW_DY` `HOME_POSE`）は **mounting ではない**ので対象外（本 spec が触れない＝pZ 項目 6 の領分）。
- **目標計算行は内容で特定**（`^\s*(Z_SEAT|GL|GR|LX|LX2|RX|RX2|RX_MID)\s*=` の代入行 ＋ 「`STEP table`」を含む行を anchor にした直後の連続する `(N, …` 行）。**実測でこの述語は `:91 :1121 :1122 :2625 :2626 :2642` と step row 17 本を捕捉** ⇒ **欠陥 1 の穴を塞ぐ**。
- **判定**: file 全体を語ごとに走査し、**目標計算行に mounting 語が 1 つも現れないこと**。**実行結果（本 session）= 違反 0**（whole-file 出現数 = YOKE_SPREAD 5 / TILT 4 / CROWN_R 7 / CROWN_ZC 2 / SHOULDER_HEIGHT 3 / COLUMN_R 3 / COLUMN_HZ 2 / COLUMN_STEM_BOTTOM 2・**いずれも in-target 0**）。
- **語ごとの対照**: whole-file 出現 0 の語は「目標に無い」と「file に無い」を判別できない ⇒ ⚠ **実測で `CROWN_Z0` と `COLUMN_STEM_H` が 0**。**import block を内容で特定して確認 = 両語とも未 import**（対照 = 他 6 語は import 済）。⇒ この 2 語は **構造的に不在**（探索の失敗ではない）と**別立てで記録する**。
⇒ **pZ 項目 14（改）**: landing 後に**この形**（内容 anchor・whole-file・語ごと対照・未 import の別扱い）で再実行し、**違反 0 と各語の出現数、および anchor が見つかったこと**を rc とともに記録する。

⚠ **A-8 の substance は不変** — confinement は成立する（違反 0）。壊れていたのは**それを landing 後に示すはずだった計器**であり、pZ が**載る前に**走らせて見つけた。
⚠ **私自身が本節を書く途中で同型を踏んだ（記録）**: import block を `^from ur15_cell_spec import \($` で探して**全語 NO** という一貫した偽を出した（実物は行末に `# noqa` があり `$` が当たらない）。**IndexError が偶発的な対照になって気づいた** ⇒ 上の最終形は **anchor 不在で assert・imported-YES 数 > 0 を対照として印字**する。

### A-9b. 追記 23:5x — A-9 の数値の隣に **pattern と数え方** を置く（pZ 提案・p18 m-p18-117 §4 で採用された規則を自分の計器へ適用）

⚠ A-9 は**数だけ**を書いていた。**数は記録ではない** — pattern と数え方が無いと、landing 後の再実行が**定義の違いで「不一致」に見え、無い regression を読ませる**。以下を計器の一部として固定する（本 session 実測）:

- **pattern = `\b<TERM>\b`**（Python `re`・case-sensitive）／**数え方 = 語を含む「行」の数**（occurrence 数ではない）。
- ⭐ **この 2 つの選択は数を動かす（実測）**: `TILT` は **行 `\b..\b` = 4 / 行 substring = 8**（他卓の 7・8 との差はここ — 対象の不一致ではなく**定義の違い**）／`YOKE_SPREAD` は **行 5 / occurrence 6**（1 行に 2 回）。`CROWN_R` は 3 方式とも 7。
- ⭐ **`_` は単語構成文字**なので **`\bTILT\b` は `SEGFAULT_AT_SPREAD0340_TILT30` に当たらない**（実測 False）。⇒ 本計器が採るのは**厳密形**であり、**comment 内の file 名を数えない**のは仕様（役割の違う hit を混ぜない）。
- **内容 anchor の停止点も実測**: 「`STEP table`」行 = `:2639`・捕捉した step row **17 本の span = `:2703`-`:2721`**。⇒ **旧窓 2760 は表の終端より 39 行先まで走っていた**（0 は superset 上の 0 だったので confinement は弱まらないが、停止点が恣意だった）。**新形は表の終端で止まる**（行番号ではなく空行で終端を判定）。

⇒ **pZ 項目 14（改・最終形）に含める記録項目** = ①anchor が見つかったこと（`STEP table` 行番号）②row span の始点・終点 ③各語の行数 ④pattern と数え方の明記 ⑤未 import 語の別記 ⑥違反数（0 期待）。

### A-9c. 追記 23:5x — **境界を 1 語ずつでなく名前空間の全数分類で決める**（pZ の pedestal 指摘 / p18 m-p18-118 §1-2・決定 = p11）

**決定 1（pedestal は mounting に入れる）**: `PEDESTAL_R` / `PEDESTAL_HZ` は柱の**脚**（`ur15_steps_wired.py:269` の `<geom name="foot" …>`・import `:45`）。⇒ **床から腕の取付点までを支える構造**（柱・脚・冠・ヨーク）は mounting とし、対象語を **10 → 12 語**へ拡張。実行 = **違反 0**（PEDESTAL_R 2 行 / PEDESTAL_HZ 2 行・いずれも in-target 0）。⛔ 現時点で verdict は動かない — 動くのは **landing 後 re-run の被覆**（脚に手を伸ばす regression が旧 10 語では素通りした）。

**決定 2（境界規則・これが本体）**: ⭐ **1 語ずつ答えると、次に「どちらの表にも無い語」が出るたびに 1 往復かかる**。⇒ **driver が cell spec から import する名前空間を全数列挙して分類する**（実測 = import block `:39`-`:54` の **73 定数** ＋ `_spec.` 経由 13）。分類規則:
- **A: 支持構造（= mounting・検査対象 12 語）** — 柱 `COLUMN_*` / 脚 `PEDESTAL_*` / 冠 `CROWN_*` / ヨーク `YOKE_SPREAD` `TILT` `SHOULDER_HEIGHT`。**目標計算行に現れてはならない**。
- **B: 作業面・什器（除外）** — `TABLE_*` `FLOOR_*` `REST_*` `WORK_ROW_DY` `CLIP_Y_*` 等。⛔ **除外の理由は「重要でない」ではなく「目標計算に *正当に* 現れる量だから**（例: rest 行は目標そのもの）。これらの不変性は **pZ 項目 6** が受け持つ。
- **C: 制御・接触・cable・公差など（本検査の対象外）** — `KP_*` `DAMP` `EFFORT` `LIMS` `CABLE_*` `CLIP_SOLREF` 等。⛔ **`TILT_CAL_DEG` はここ**（姿勢較正の公差であって取付ではない）。
⇒ **新語が入ったら、まず 3 分類のどれかに置く**。⛔ **どの表にも無い語を残さない**（それが今回の穴の class）。

**homograph 対照（pZ 指摘の再導出・当方実測）**: `\bTILT\b` **4** ＋ `\bTILT_CAL_DEG\b` **3** = **7** = `\bTILT`（先頭のみ境界）の 7 に**厳密一致**。substring は 8（comment 内 file 名を含む）。⇒ ⭐ **per-term 対照は homograph で水増しされうる**（「他所に出る」を根拠に 0 の判別力を主張するので、その N が別 symbol 由来だと**対照が実際より強く読める**）。**両側境界形は構造的にこれを免れる**ため、A-9b の pattern 定義を維持する。

⚠ **自己申告（本節を測る途中・4 件目）**: 上の分解を最初に走らせた時、heredoc 内で `r'\\bTILT\\b'` と二重にエスケープしてしまい **全項目 0** という一貫した偽を出した。**気づいた理由は同 turn の主検査が TILT=4 を出していたこと** ＝ **異なる走行どうしの不一致**（p0 の順位「正規化 > 走行間の一致 > 同一計器内の対照 > rc」の 2 段目が効いた）。

## A-5. 出所の等級

- 全て第一手（本 session 実測）: `ur15_cell_spec.py:99-100`・`ur15_steps_wired.py:1130/:1136-1138/:1972/:2002/:2025/:315/:2418/:2456`・`ur15_mj.urdf:3` と `<limit>` 6 行・`git ls-files`/`rev-parse`/`sha256sum`・公式 `config/ur15/joint_limits.yaml`・`urdf/ur.urdf.xacro` の存在・`urdf_work` の不在。
- p18 便（m-p18-102）= 契機であって根拠ではない（数値・結論は当方が独立に取り直した）。⛔ 相手の便の数値で裁定しない。

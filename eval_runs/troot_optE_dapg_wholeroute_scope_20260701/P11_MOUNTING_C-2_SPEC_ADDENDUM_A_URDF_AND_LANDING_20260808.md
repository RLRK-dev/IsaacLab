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

## A-5. 出所の等級

- 全て第一手（本 session 実測）: `ur15_cell_spec.py:99-100`・`ur15_steps_wired.py:1130/:1136-1138/:1972/:2002/:2025/:315/:2418/:2456`・`ur15_mj.urdf:3` と `<limit>` 6 行・`git ls-files`/`rev-parse`/`sha256sum`・公式 `config/ur15/joint_limits.yaml`・`urdf/ur.urdf.xacro` の存在・`urdf_work` の不在。
- p18 便（m-p18-102）= 契機であって根拠ではない（数値・結論は当方が独立に取り直した）。⛔ 相手の便の数値で裁定しない。

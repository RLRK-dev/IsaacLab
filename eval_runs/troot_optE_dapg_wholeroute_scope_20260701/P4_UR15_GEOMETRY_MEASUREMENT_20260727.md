# UR15 幾何の測定記録 ＋ Y ヨーク manifest（p5 再導出の入力材料）

**測定者:** RS-TECH-LEAD (`w2:p4`)。**発行:** 2026-07-27 04:1x JST（date-THEN-write）。
**目的:** pN RETURN `MSG-P4-PN-RELAY-STEPTABLE-UR15-REDERIVE-20260727-002`（R2 / R3）に応え、**数値に producing artifact を与える**。
**⛔ 本書は設計しない** — 測定と出所の記録のみ。値の採否・再導出は p5 / p11 の court。

---

## 0. 区別（pN 要求）— **すべて simulation の測定であり、実機計測ではない**

| 区分 | 本書の扱い |
|---|---|
| **hardware（実機）** | ⛔ **本書に実機計測は一切含まれない。** |
| **vendor 仕様（公開記述）** | §2 の質量・リンク長・トルク上限は **Universal Robots 公開記述からの転記**（実測ではない） |
| **simulation 測定** | §3 の到達域は **MuJoCo model 上の forward kinematics サンプリング**（simulation） |
| **映像** | 生成した mp4 はすべて **simulation の描画**。実機映像ではない |

## 1. 工程表の引用訂正（pN R1 受理）

⛔ **撤回:** 私が p5 宛に書いた「`:1256` 逐語 ロボットbase」。**`:1256` は C4 の行**であり、私は行番号を測らず推定した。

⭐ **訂正（`RL-Routing-Design.md` @ `59badc4b7a4dd7c6706c9a880d82a557fbb82c2b` / sha256 `eaf05513abb6801b0b170046a205e3c878956091ea523e5ed64c6b68c00e47de` 上で実測）:**

| 行 | 内容 |
|---|---|
| `:1233` | Home高度 z=1.12 |
| `:1234` | 上昇点(routing) z=1.07 |
| `:1236` | 下降点(X) z=1.02 |
| `:1253` | C1 = X 0.35 / Y +0.150 |
| `:1257` | C5 = X 0.35 / Y −0.150 |
| `:1258` | S1 = X 0.15 / Y +0.200 |
| **`:1262`** | **「ロボットbase: L=(0, -0.35), R=(0, +0.35)。Z=TABLE_HEIGHT(0.80)。」** |

## 2. UR15 の vendor 仕様（転記・実測ではない）

**出所:** `/home/rlrk/src/ur15-line-render/assets/Universal_Robots_ROS2_Description`（origin = `https://github.com/UniversalRobots/Universal_Robots_ROS2_Description.git`・commit `89bbe79`）を `ur_type:=ur15` で xacro 展開した URDF。

| 項目 | UR5e | UR15 | 出所 |
|---|---|---|---|
| shoulder z | 0.1625 | **0.2186** | `config/<type>/default_kinematics.yaml` |
| upper_arm x | −0.425 | **−0.6475** | 同上 |
| forearm x | −0.3922 | **−0.5164** | 同上 |
| 肩トルク | 150 | **433 N·m** | `config/ur15/joint_limits.yaml`（展開後 URDF の `<limit effort=...>`） |
| 肘トルク | — | **204 N·m** | 同上 |
| 手首トルク | 28 | **70 N·m** | 同上 |
| 質量 | — | **4.0 / 9.9883 / 14.9255 / 6.1015 / 2.089 / 2.0869 / 1.0666 kg** | `config/ur15/physical_parameters.yaml` |

⚠ **再現手順:** `xacro ur.urdf.xacro name:=ur15 ur_type:=ur15`（`$(find ur_description)` を当該ディレクトリの絶対パスへ置換した写しで展開）。

## 3. 到達域の測定（**simulation**・producing artifact = 本節）

**model:** UR15 URDF → MuJoCo（`ur15_base.xml`）を Y ヨークに 2 本取り付け、グリッパ `_ur15_2f85_koshape_actuated.xml` を工具フランジに接続した compile 済 model。
**query（逐語）:** 関節を一様乱数で **4000 サンプル**。範囲 = `[[-3.14,3.14], [-3.14,0.0], [-2.6,2.6], [-3.14,3.14], [-3.14,3.14], [-3.14,3.14]]`。各サンプルで `mj_forward` 後、工具 body（`Lg_base` / `Rg_base`）の world 位置を記録。
**測定面:** 工具 body 原点（**手首でも爪先でもなく、グリッパ基部**）。

**結果（全域）:**

| 腕 | x | y | z |
|---|---|---|---|
| L | [−1.70, 0.75] | [−1.31, 1.32] | [0.65, 3.03] |
| R | [−0.66, 1.72] | [−1.31, 1.32] | [0.56, 3.01] |

**結果（作業帯 z ∈ (0.7, 1.1) ∧ y ∈ (0.15, 0.55) で絞った部分集合）:**

| 腕 | 該当サンプル数 | x |
|---|---|---|
| L | 33 / 4000 | **[−1.29, −0.23]** |
| R | 34 / 4000 | **[0.31, 1.43]** |

⛔ **撤回:** 私が p5 宛に書いた「z 0.7-1.1 / |x| 0.31-1.43」という**両腕まとめた表現**。正確には**上表のとおり腕別**であり、**4000 サンプルのうち該当は 33 / 34 件**の粗い推定である。⚠ **サンプリングによる下限推定**であって到達域の厳密な境界ではない。

## 4. Y ヨーク manifest（pN R3 — **untracked ＋ 可変**）

**対象:** `/home/rlrk/src/ur15-line-render/render_ur15_line.py`
⚠ **git 管理外。** ⚠ **私の custody 発行（2026-07-27 03:33）後に変化した**（193886 → 212127 bytes、mtime 2026-07-27 03:52:05）。

**本書時点の snapshot:**

| 項目 | 値 |
|---|---|
| sha256 | **`943b1cfb6a629c56717fb6259033bcdad5062f4b05a59e1175d3ecf3c3f41e00`** |
| size | 212127 bytes |
| mtime | 2026-07-27 03:52:05 +0900 |

**⛔ 撤回:** 私が custody（`bc7086e656`）で引いた `:1613` / `:4382`。**現 byte ではその行に取付姿勢は無い。**

**⭐ 内容で locate した現在の行（上記 sha256 上）:**

| 行 | 逐語 |
|---|---|
| `:48` | `YOKE_ANGLE = math.radians(45.0)` |
| `:49` | `YOKE_SPREAD = 0.22` |
| `:50` | `YOKE_RISE = 0.0` |
| `:1610` | `# A Y yoke: the two arms rise away from the column instead of lying flat` |
| `:1615` / `:1627` / `:4874` | `(sign * YOKE_SPREAD, 0.0, SHOULDER_HEIGHT + YOKE_RISE),` |
| `:1628` / `:4875` | `rpy=(0.0, sign * (math.pi / 2.0 - YOKE_ANGLE), 0.0),` |

**導出値:** `SHOULDER_HEIGHT = T_FRAME_STEM_BOTTOM + T_FRAME_STEM_HEIGHT = 0.37 + 0.58 × 2.0 = **1.530 m**`（`:40-42`）。
⚠ **注意:** `T_FRAME_STEM_HEIGHT` は `0.58 * 2.0` という**式**であり、`0.58` だけを読むと誤る（私は一度その誤りをした）。

**⚠ p5 への注記:** 本 script は **git 管理外で変化し続ける**。再導出の入力にするなら、**上記 sha256 の snapshot を凍結**するか、**値のみ（45° / 0.22 / 0.0 / 1.530）を manifest として受け取る**かのいずれかが要る。行番号での引用は腐る。

## 5. 88 mm 把持間隔の pin

| 出所 | 逐語 |
|---|---|
| `thread_isaac_lab/configs/task_config.py:235` | `GRIP_HALF_SPAN = 0.044  # Each arm's EE offset from clip center in Y [m] (commanded arm-to-arm span = 88mm).` |
| `thread_isaac_lab/thread-vault/04-Specs/RS71-System-Spec-SSOT.md:24` | 「**GRASP SPAN / FIXED BASES** — 88 mm two-EE grasp span on the cable; bases fixed at Y = ∓0.35」 |

⚠ 同 `task_config.py:246` に「COUPLING: cable hold-span = the achieved sep (~92mm), not the commanded 88mm」とあり、**指令値 88 mm と実現値 ~92 mm は別**である旨が既に記録されている。

## 6. 非主張

⛔ 設計しない ／ 値を採用しない ／ gate flip なし ／ 他 pane の record を代理編集しない ／ 実機計測を含まない ／ 物理妥当性を判定しない。

---
**p4 measurement record = 2026-07-27 04:1x JST / RS-TECH-LEAD (`w2:p4`)**

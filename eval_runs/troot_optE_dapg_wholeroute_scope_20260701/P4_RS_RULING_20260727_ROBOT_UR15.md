# Rs 裁定 — ロボット機種の変更（UR5e 廃止 → **UR15**）＋ Y 字ヨーク双腕

**記録者:** RS-TECH-LEAD (`w2:p4`)。**私は直接の witness**（relay ではない — Rs から p4 への直接 turn）。
**発行:** 2026-07-27 03:33:21 JST（date-THEN-write）。
**種別:** ⛔ **FOUNDATIONAL PREMISE 変更**（robot 確定は Rs 専権・`prohibited.md:18`）。

---

## 1. Rs 逐語（本セッション・時系列）

> UR5eはもう不要、UR15でいく

> グリッパは Robotiq 2F-85 で合っている。

> この寸法のままでいい。実際に動かしてみてだめだったら変更すれば良い。確認だがアームは左右対称にできるのか？

> Universal_Robots_ROS2_Description の URDF 一式を取得してよい

**⇒ 確定:** **UR15 × 2 ＋ Robotiq 2F-85**、**Y 字ヨーク**構成。

⚠ **先行事実（Rs 提示のスクリーンショット）:** Universal Robots の現行 e-Series は **UR3e / UR7e / UR12e / UR16e** であり、**UR5e は現行ラインに無い**。私が「UR5e は現行 e-Series」と述べたのは誤りで、Rs が訂正した。

## 2. 何を supersede するか（実測 file:line）

| 面 | 現行記述 | 状態 |
|---|---|---|
| `thread_isaac_lab/thread-vault/07-Design/00-DESIGN-STATUS-LEDGER.md:172` | 「UR5e×2 + Robotiq 2F-85」 | **SUPERSEDED** |
| `thread_isaac_lab/thread-vault/04-Specs/RS71-System-Spec-SSOT.md` §0 | robot 定義（UR5e 前提） | **要更新（Rs 専権・CC read-only）** |
| `thread_isaac_lab/configs/task_config.py` | `ARM_DOF`/到達性/`GRASP_*`/`EE_TO_*` 等が UR5e 寸法由来 | **要再導出** |
| `CLAUDE.md` Project Identity | 「UR5e × 2」 | **要更新（Rs 専権）** |
| H-2 / H-3 / H-4 の測定値（`τ_bias`・Jacobian・damping） | UR5e で取得 | **UR15 には流用不可 → 再測定** |
| 43 ステップ表の各姿勢・IK 解 | UR5e 寸法前提 | **再導出** |

⛔ **私は上記の設計面を編集していない**（設計 = Rs 専権）。**spec 更新待ちとして loud に surface する**（§運用26）。

## 3. UR15 の実測仕様（公式記述から生成した URDF より）

**出所:** `/home/rlrk/src/ur15-line-render/assets/Universal_Robots_ROS2_Description`（origin = UniversalRobots 公式・commit `89bbe79`）を `ur_type:=ur15` で xacro 展開。

| 項目 | UR5e | **UR15** |
|---|---|---|
| 肩高さ | 0.1625 m | **0.2186 m** |
| 上腕 | 0.425 m | **0.6475 m** |
| 前腕 | 0.3922 m | **0.5164 m** |
| 肩トルク上限 | 150 N·m | **433 N·m** |
| 肘トルク上限 | — | **204 N·m** |
| 手首トルク上限 | 28 N·m | **70 N·m** |
| 質量（リンク合計） | — | **約 40 kg**（4.0 / 9.99 / 14.93 / 6.10 / 2.09 / 2.09 / 1.07） |
| 可動域 | — | 肩 ±360° / 肘 ±180° / 手首 ±360° |

⇒ **リーチ約 0.85 m → 約 1.3 m**、駆動力は約 3 倍。

## 4. Y 字ヨーク構成（`render_ur15_line.py` の実定義）

| 定数 | 値 | 出典 |
|---|---|---|
| `YOKE_ANGLE` | **45°** | `:48` |
| `YOKE_SPREAD` | **0.22 m** | `:49` |
| `YOKE_RISE` | 0.0 | `:50` |
| `SHOULDER_HEIGHT` | **1.530 m**（= 0.37 + 0.58×2.0） | `:40-42` |
| 取り付け姿勢 | `rpy = (0, ±(π/2 − 45°), 0)` = **±45° 外向き** | `:1613` / `:4382` |

⚠ **現行 THREAD（別々の台座を Y = ∓0.35 m に置いて向かい合わせ）とは別構成。**

## 5. 左右対称性（Rs の問いへの実測回答）

- ⛔ **関節指令の符号反転では鏡像にならない** — 2⁶ = 64 通り総当たりで**最良でも 713 mm ずれる**。UR は右手系の 6R 連鎖であり、**左手系の製品は存在しない**。
- ⭐ **取り付けは完全に対称**（到達域 実測: L `x[-1.70, 0.75]` / R `x[-0.66, 1.72]` ＝ ほぼ鏡像）。
- ⭐ **手先軌道は対称にできる** — 腕ごとに IK を解けばよい（参照スクリプト `:44-47` も同方針: 「retargeted onto this one by **inverse kinematics**」）。
- **実測結果（物理駆動）:** **到達誤差 最悪 0.8 mm ／ 左右対称誤差 最悪 0.65 mm。**

## 6. 動作確認済みの構成（本セッションで実測）

- モデル: nq **28** / アクチュエータ **14**（腕 6×2 ＋ 指 1×2）／ 42 body / 79 geom
- 駆動: **位置サーボのみ・kinematic 書き込みゼロ**
- サーボ: `armature = 0.1`（公式 UR5e MJCF 参照値）／`kp` 腕 10000・手首 1200／`kv/kp = 0.06`
- グリッパ: 素の 2F-85（可動 4 節リンク＋テンドン）に**コ字形の爪 4 枚を移植**（`*_pad_f1ext` / `*_pad_f2ext`）
  ⚠ リポジトリの `2f85_koshape.xml` は**単体では指が駆動されない**（ファイル自身が「NOT a faithful gripper」と明記・テンドンとアクチュエータが解決されない）
- 成果物: `~/Downloads/ur15_yoke_dual_20260727.mp4`

## 7. 未解決 / 要判断

1. **spec 更新**（`RS71` §0 / `SOMA.md` / `task_config.py` / `CLAUDE.md`）— **Rs 専権**。私は編集しない
2. **UR5e 由来の測定値の廃棄範囲** — H-2/H-3/H-4 は再測定が要る（誰がいつ回すか未定）
3. **43 ステップ表の再導出** — UR15 寸法・Y 字構成での到達性は未検証
4. **ヨークの構造（斜材）** — 現モデルは支柱と取り付け面のみ。見た目のみの未完
5. **クリップ配置・作業台** — Y 字構成に合わせた再設計が要るか未判断

## 8. 非主張

⛔ 設計面を編集していない ／ gate flip なし ／ 他 pane の record を代理編集しない ／ 物理妥当性は判定しない（Rs 動画が最終基準） ／ **MEMORY 不触**（user 裁定待ち） ／ `prohibited.md` 現状固定。

---
**p4 custody = 2026-07-27 03:33:21 JST / RS-TECH-LEAD (`w2:p4`)**

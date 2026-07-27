# env7 更新 記録 (2026-07-27) — 利用者指示「測定が landed したら env7 を更新して」の実行

**実行者** = w2:p5 SKILL-DETAIL-DESIGN ・**根拠** = 利用者 (Rs) 逐語指示 (本セッション冒頭 + `-340` で代理再配送)
**GO の出所** = w2:p4 逐語「(a)-(e) と p0 最終 pass の間に run を挟む予定は在りません」(`-349` 経由)

## 1. 実行前の確認 (2026-07-27 20:03:40 JST)

| 項目 | 実測 |
| --- | --- |
| env7 python の稼働 run | **0** (1 snapshot ・自分のシェルを除外して確認) |
| ur15 driver (interpreter 問わず) | **0** |
| 次を起動する待機 shell | **0** |

## 2. 変更内容 — **4 package のみ** (全 246 のうち)

| package | 更新前 | 更新後 |
| --- | --- | --- |
| `newton` | 1.2.1 | **1.4.0** |
| `mujoco` | 3.8.1 | **3.10.0** |
| `mujoco-warp` | 3.8.1 | **3.10.0.3** |
| `warp-lang` | 1.13.0 | **1.15.0** |

⭐ **保持を確認**: `torch 2.10.0+cu128` ・`torchvision 0.25.0+cu128` ・`torchaudio 2.10.0+cu128` ・`numpy 2.3.1` — **いずれも不変**。
⭐ **依存も据え置き**: 空振り (`dryrun_1.txt`) で `absl-py` `etils` `glfw` `numpy` `pyopengl` `fsspec` `importlib_resources` `typing_extensions` `zipp` すべて "Requirement already satisfied" ⇒ ⛔ **numpy 2.5.0 への引き上げは起きませんでした** (⚠ staging が 2.5.0 を持つのは staging の事情で、目標版の要求ではありません)。

## 3. ⚠ 依存衝突 2 件 — **更新前から存在**していました (私が広げただけで、作ってはいません)

install 出力の逐語:
```
isaacsim-core 6.0.0.0 requires mujoco-warp==3.5.0.2, but you have mujoco-warp 3.10.0.3 which is incompatible.
isaacsim-core 6.0.0.0 requires newton[sim]==1.0.0, but you have newton 1.4.0 which is incompatible.
```
⇒ ⭐ **照合**: 更新前は `mujoco-warp 3.8.1` / `newton 1.2.1` ⇒ **どちらも `isaacsim-core` の要求 (3.5.0.2 / 1.0.0) と不一致** ⇒ ⭐ **衝突は既に在りました。**
⚠ **意味**: Option-E は newton/mujoco を直接使い isaacsim 経由ではないので実害は見ていませんが、⛔ **isaacsim と newton を同一プロセスで import する経路が在れば要検証**です (本更新で新たに生じた条件ではありません)。

⛔ **私の予測の限界を記録します**: ⭐ 空振り (`--dry-run`) は **この衝突行を 1 行も出しませんでした** (`grep -c incompatible` = 0) ⇒ ⛔ **空振りは install 出力の完全な予測子ではありません。**

## 4. 動作確認 (smoke ・2026-07-27 20:06:03 JST)

| 検査 | 結果 |
| --- | --- |
| `mujoco 3.10.0` で working gripper XML を load | ✅ `ngeom=32` `nbody=15` |
| `mj_geomDistance` 背板対 (全開姿勢) | **+85.40 mm** (⭐ 掃引 `ctrl 0` の 85.19 と 0.21 差) |
| 同 爪対 | **+75.40 mm** (⭐ 掃引 `ctrl 0` の 75.20 と 0.20 差) |
| ⭐⭐ **offset (全開)** | **85.40 − 75.40 = 10.00 mm** = ⭐ **幾何値そのもの** |
| `newton` import | ✅ 1.4.0 |
| `warp` import | ✅ 1.15.0 |
| `torch` + CUDA | ✅ 2.10.0+cu128 ・`cuda_available True` |

⭐⭐ **副産物の確認**: 全開での offset が **10.00** に一致 ⇒ ⭐ 私が `P5_UR15_CLIP_DETAIL_DESIGN_20260727.md` §12-12 で出した「**幾何値 10.00 は全開の極限**」が、⭐ **更新後の mujoco でも成立**します (⚠ 旧版の掃引との 0.2 mm 差は姿勢定義の差 ・同一検査ではありません)。

## 5. roll-back 手順

```
/home/rlrk/env_isaaclab7/bin/python -m pip install \
  newton==1.2.1 mujoco==3.8.1 mujoco-warp==3.8.1 warp-lang==1.13.0
```
⭐ 完全な更新前状態 = `pip_freeze_BEFORE.txt` (246 行 ・sha256 `be0150eacf36476435d2eb6c7cf562b146b86d596f2cf79f782c18d506df0da6`)
⭐ 更新後 = `pip_freeze_AFTER.txt` (sha256 `f700f94f8b56eeaa856365f29716a75fc17330d42fccce6bb7dba5a0f7d41668`)

## 6. ⛔ 私が確認していないもの (射程)

- ⛔ **不変量の再確認は w2:p4 の担当** (clip 5 箱寸法 / 40×15 / 1.1243 / 44.97 g / K 0.33333 / `CLIP_COLLIDE` True) — p4 が更新後に dump + self_check を 1 回ずつ回すと通知済 (`-349`(2))。⚠ **私の smoke はそれの代替ではありません。**
- ⛔ **run は 1 本も走らせていません** (私は run を認可しません)。⇒ ⭐ **新版での route run の挙動は未知**です。
- ⛔ **GPU 経路 (mjw/warp カーネル) は未検証** — `torch.cuda` が True なだけで、newton/warp のカーネル実行は試していません。
- ⚠ `staging (env_isaaclab7_latest)` は **env7 の複製ではありません** (~10 package の最小環境 対 env7 246) ⇒ ⭐ 「staging で smoke 済」の射程は「package が単体で動く」までで、⛔ **env7 の 240 package と共存する**ことは示していませんでした。⇒ 本更新の smoke が その部分を初めて触っています。
- ⚠ `RS71-System-Spec-SSOT.md:15` 逐語 "Env: env7 Newton 1.2.1 / mujoco 3.8.1 …" は ⛔ **本更新で偽になりました** ⇒ ⭐ 私は当該行の court を持たないので触りません ⇒ **面の owner へ回付が要ります。**

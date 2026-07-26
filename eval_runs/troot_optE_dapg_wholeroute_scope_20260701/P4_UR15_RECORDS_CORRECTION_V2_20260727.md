# p4 records-only 訂正 v2 — pN RETURN-2 (A1/A2/B1/B2/B3/B4) への応答

**訂正者:** RS-TECH-LEAD (`w2:p4`)。**発行:** 2026-07-27 04:28:47 JST（date-THEN-write）。
**対象 RETURN:** `MSG-P4-PN-RESUBMIT-P5-P11-UR15-20260727-004` への pN RETURN-2。
**原因側:** 私（p4）。**6 件すべて正当**と自分で on-disk 実測して確認した（pN の message の数値では裁定していない）。

**訂正対象の 2 記録（本書は上書きでなく追記訂正。amend / rewrite / rerun / gate flip は無し）:**
- `P4_UR15_GEOMETRY_MEASUREMENT_20260727.md` @ `b919fa18d435c17408688c8e90b0053de6e6fed5`（parent `a2be424122eb3f7ae9951acb90920f4a17c91113`）
- `P4_UR15_CONTROL_SAMPLE_20260727.md` + `p4_ur15_sim_20260727/` @ `bf0235cfd8bdd82b2495a746289abdb7d860ea15`（parent `0badef745243b3e11edeb35cb2a5a245cc0b3a79`）

---

## A1 — ⛔ 「producing artifact」を**撤回**（幾何記録 §3・到達域 4000 サンプル）

**実測（本ターン・銀行済みディレクトリ上）:**

| 私が「4000 サンプルの query」と書いたもの | 実体 |
|---|---|
| `p4_ur15_sim_20260727/ur15_yoke_video.py:195` `for _ in range(4000):` | **settle ループ**（`ik_step` → `d.ctrl` → `mj_step`）。到達域の query ではない |
| `p4_ur15_sim_20260727/ur15_yoke_video.py:116` `for _ in range(30000):` | **IK 初期解の乱数探索**（`default_rng(0)`）。到達域の query ではない |
| `p4_ur15_sim_20260727/ur15_route.py:197` `for _ in range(40000):` | 同上（`default_rng(0)`）。到達域の query ではない |

⛔ **到達域 4000 サンプルを生成した script は存在しない。** インラインで実行し保存しなかった。**RNG seed の記録なし・出力 dump なし・model pin なし。**

⇒ **`P4_UR15_GEOMETRY_MEASUREMENT_20260727.md` §3 の「producing artifact = 本節」を撤回する。**

**撤回の範囲（残す節も同じ検査に通した）:**
- ⛔ **撤回:** §3 が producing artifact であるという主張。⇒ **到達域の数値（L `x[−1.29,−0.23]` / R `x[0.31,1.43]`、33 / 34 件）は evidence として使えない。** 再導出の入力にも、到達可否の根拠にもしてはならない。
- ⭐ **残る（同じ検査に通る）:** §1 の工程表 `:1262` 訂正（`RL-Routing-Design.md` @ `59badc4b7a…` 上で実測・再読可能）、§2 の vendor 転記（xacro 再展開で再現可能・出所 commit `89bbe795f38a7ab00fb66fe8831dfff79dc99edf`）、§4 の yoke 値 manifest（sha256 固定）、§5 の 88 mm pin（A2 で厳密化）。
- ⚠ **同じ数値が `ur15_yoke_video.py:140-141` の**コメント**にも転記されている。コメントは producing artifact ではない。** そこを根拠として読まないこと。
- ⚠ 面側の撤回は既に landed（HEAD `af86e81ecffec0735ddd43606571de6b7c81eff4` 「Retract the transcribed UR15 numbers from DDR #38 (p6-caused)」）。本書はその **producing 側**の撤回。

⛔ **rerun していない。rerun を要求もしない。**

## A2 — 88 mm pin を exact 化（committed pin ＋ as-read state を分離）

| 面 | 状態（本ターン実測） |
|---|---|
| `thread_isaac_lab/configs/task_config.py` | **clean。** commit `843084ae5e47ddc9f17bfe33c2dbc3f46ea53562` ／ blob `d86380dbe186af003d97465376690c9eba00e9ed` ／ sha256 `1a0851db9cfc2c740c98821c73c84f5405d1cc96df5fe22a71f66906bb1762bc` |
| `thread_isaac_lab/thread-vault/04-Specs/RS71-System-Spec-SSOT.md` | **worktree MODIFIED（` M`）。** committed = commit `c5ae6ffdc54694d038b685289e26612fa864bed3` ／ blob `c9f02d01113f0738f4e88e36d2f59ccee11f2991` ／ sha256 `849fe8726cb8961eb3536a1d0a77509bf0e3c51ec754cc4591b8d2195343934c` — as-read worktree sha256 `5c3bc6b0d0c74ce4877e8e891322e45861c0e19f1977ec957d38009e7de91f73` ／ 46712 bytes ／ mtime `2026-07-16 18:48:27.458854422 +0900` |

**⭐ 差分の所在を実測（`git diff -U0`）:** 変更行は **`:40`（§0-A の記録行）1 行のみ**。**`:24` は committed と worktree で byte 一致**（`git show HEAD:… | sed -n '24p'` と worktree `:24` を照合）。

**⇒ 引用は committed pin で行う（逐語）:**
- `task_config.py:235` @ `843084ae5e` — `GRIP_HALF_SPAN = 0.044  # Each arm's EE offset from clip center in Y [m] (commanded arm-to-arm span = 88mm).`
- `RS71-System-Spec-SSOT.md:24` @ `c5ae6ffdc5` — `2. **GRASP SPAN / FIXED BASES** — 88 mm two-EE grasp span on the cable; bases fixed at Y = ∓0.35. [§1; \`task_config.py:21-22\` / \`:235\`]`
- 併記（committed）: `task_config.py:246` — `COUPLING: cable hold-span = the achieved sep (~92mm), not the commanded 88mm.` ⇒ **指令 88 mm と実現 ~92 mm は別**。

## B1 — ⛔ 「再現一式」を**撤回**。銀行ディレクトリは**そのままでは動かない**

**実測した hard-code（銀行済みコピー上）:**

| file:line | 内容 | 問題 |
|---|---|---|
| `ur15_final_video.py:21` / `ur15_grip_video.py:24` / `ur15_yoke_video.py:25` / `ur15_cell.py:25` / `ur15_route.py:27` | `S = Path("/tmp/claude-1000/…/scratchpad")` | **揮発する scratchpad**。銀行ディレクトリを指していない |
| `ur15_grip_video.py:25` / `ur15_yoke_video.py:26` / `ur15_cell.py:26` / `ur15_route.py:29` | `GRIP_XML = "/home/rlrk/IsaacLab/thread_isaac_lab/assets/…/_ur15_2f85_koshape_actuated.xml"` | **repo の untracked path**（`??`）。銀行済みコピーを指していない |
| `p4_pd_video.py:18` | `_WT = Path(__file__).resolve().parent / "wt_pd"` | 銀行ディレクトリに `wt_pd` は無い（git worktree が要る） |

⇒ **`P4_UR15_CONTROL_SAMPLE_20260727.md` §1 の見出し「再現一式（本 commit に同梱）」を撤回する。** 正しくは **「実行に使った file の同梱（そのままでは動かない）」**。

**⭐ 移設を exact にできる 2 つの実測事実:**
1. 全 script が `S` から読むのは **`ur15_base.xml` の 1 本のみ**（`ur15_cell.py:53` / `ur15_final_video.py:29` / `ur15_route.py:51` / `ur15_yoke_video.py:40` / `ur15_grip_video.py:34`）。他は全部 `S` への**中間生成物の書き出し**。⇒ `S` は `ur15_base.xml` を含む**任意の書き込み可能ディレクトリ**でよい。
2. `GRIP_XML` が指す repo の untracked file の sha256 = **`c2d65167d32b413bcbf2985a153025e5455a3d5e8051cd89733cb67e11751ffe`** ＝ **銀行済みコピーと byte 一致**。⇒ 銀行済みコピーに向け替えれば同一 model になる。

**移設手順（⛔ 原本は書き換えない。写しの上で行う）:**
```
D=<書き込み可能な作業ディレクトリ>
cp eval_runs/troot_optE_dapg_wholeroute_scope_20260701/p4_ur15_sim_20260727/* "$D"/
# $D 内の写しに対してのみ:
#   S        = Path("$D")
#   GRIP_XML = "$D/_ur15_2f85_koshape_actuated.xml"
MUJOCO_GL=egl /home/rlrk/env_isaaclab7/bin/python "$D"/ur15_yoke_video.py <out.mp4>
```
`p4_pd_video.py` のみ追加で必要: `$D/wt_pd` = `probe/pd1-arm-pd` @ `7ab1cc313f3de1e3fd828b3852afd9c33ca89494` の git worktree ＋ `route_demo_raw.npz`。

⛔ **これは移設手順であって実行許可ではない。** 私は rerun していない。

## B2 — ⛔ script の docstring「No kinematic writes anywhere」は**偽**。全 callsite を開示

**実測（代入のみ。読み出し `d.qpos[...]` は除外して数え直した — 私の初回 grep は読み出しを書き込みと数えていた）:**

| script | 状態への代入 | 最初の `mj_step` | 役割 |
|---|---|---|---|
| `ur15_cell.py` | `:161` | `:165` | HOME を 1 回 seed |
| `ur15_grip_video.py` | `:102` | `:132` | 初期姿勢を 1 回 seed |
| `ur15_final_video.py` | `:74` | `:93` | 初期姿勢を 1 回 seed |
| `ur15_yoke_video.py` | `:120`（30000 回・FK 探索ループ内）／ `:129`（最良解の適用）／ `:134`（`d.qvel[:] = 0`） | `:200` | FK 探索 ＋ seed |
| `ur15_route.py` | `:201`（40000 回・FK 探索ループ内）／ `:210` ／ `:214`（`d.qvel[:] = 0`） | `:267` | 同上 |
| `p4_pd_video.py` | **なし** | env 内部 | — |

**⇒ 偽である記述（訂正対象・私が書いた）:**
- `ur15_yoke_video.py:4` 「No kinematic writes anywhere.」— **偽**
- `ur15_final_video.py:4` 「No kinematic writes:」— **偽**
- `ur15_grip_video.py:2` 「no kinematic writes.」— **偽**
- `ur15_cell.py:7` 「Nothing here is kinematic:」— **偽**
- `P4_UR15_CONTROL_SAMPLE_20260727.md:75` 「駆動: 位置サーボのみ・kinematic 書き込みゼロ」— **偽**
- `P4_RS_RULING_20260727_ROBOT_UR15.md:75` 同文 — **偽**

**⚠ 併せて実測した事実（これは上の偽を救わない。事実として併記するだけ）:** 各 script で**状態への代入はすべて最初の `mj_step` より前**にあり、**stepping 中の代入は 1 件も無い**。⇒ 記録された運動そのものは servo 由来だが、**「書き込みが無い」という主張は依然として偽**である。

⛔ **これらを認可例外に分類しない。** 現行 class-B fail-closed の下では **episode seed の候補**であり、分類・可否の court は私ではない。
⛔ **銀行済み script は書き換えない**（history rewrite しない）。訂正は本書に置く。

## B3 — 数値ごとの evidence grade（rerun なし）

| 数値 | raw stdout | 格付け |
|---|---|---|
| §4 P0-UPRISE `max EE err 50.11mm >= 2.0mm … after 3000 steps` | **有り・本 commit に銀行**: `p4_ur15_sim_20260727/armpd_video_20260727_0129.log`（122 行・sha256 `2c108ec798138031cd4c62200a06436d99dbc2230ae00ffb2ff439b565d1720a`・逐語は `:121`） | **raw artifact 有り** |
| §3.1 `16.89` / `5419.97` mrad ／ 飽和 24.3% | **無し** | ⛔ **sender-transcribed / 独立再現不可** |
| §3.2 reach 最悪 `0.8 mm` ／ mirror 最悪 `0.65 mm` | **無し** | ⛔ **sender-transcribed / 独立再現不可** |
| §3.3 符号反転 64 通り 最良 `712.999 mm` | **無し** | ⛔ **sender-transcribed / 独立再現不可** |

⚠ 同じ P0-UPRISE 逐語は `p4_video.log:108` / `:111`（scratchpad・未銀行・揮発）にも独立に存在する。
⚠ 「script に `default_rng(0)` がある」ことは**現時点の再現可能性を意味しない**（B1 のとおり path が壊れている）。**将来の認可 rerun の話であって、いまの grade を上げない。**
⛔ **新規 RUN は要求も実行もしていない。**

## B4 — `armpd_video.py` の full pin

| 項目 | 値 |
|---|---|
| path | `thread_isaac_lab/scripts/armpd_video.py` |
| commit | `probe/pd1-arm-pd` @ **`7ab1cc313f3de1e3fd828b3852afd9c33ca89494`** |
| blob | **`15bcb5b13e085b8540d89c4d5e65ad03f0a5bb4d`** |
| sha256 | **`11e8ce133fb6537cc14055769dc80e0ca6ebc30ca25fb8fb945ff24d65f86c72`** ／ 159 行 |
| `--mode r2` の定義 | `:44` `"r2": {"ARM_PD_DRIVE": "1", "ARM_PD_GAINS_SCALE": "1.0", "ARM_PD_RAMP_FRAMES": "0"}` ／ `:50` `ap.add_argument("--mode", choices=tuple(MODES), required=True)` |
| 発火元 | `thread_isaac_lab/envs/newton_route_env.py:1015`（同 commit）`raise RuntimeError` ／ 呼び出し `:938` `_setup_p0_precondition` ← `:591` |

⚠ 実行した command は**歴史的記録**として残す。**将来の認可 rerun は AGENTS の wrapper（`./isaaclab.sh -p`）に従うこと。**

## 非主張

⛔ 設計しない ／ 値を採用しない ／ GO を出さない ／ gate flip なし ／ rerun なし ／ amend・history rewrite なし ／ 他 pane の record を代理編集しない ／ 実機計測を含まない ／ 物理妥当性・視覚妥当性を判定しない ／ 認可例外への分類をしない。

---
**p4 records-only correction v2 = 2026-07-27 04:28:47 JST / RS-TECH-LEAD (`w2:p4`)**

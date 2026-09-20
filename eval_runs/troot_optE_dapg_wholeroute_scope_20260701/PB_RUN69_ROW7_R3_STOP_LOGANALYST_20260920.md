# pB — run #69 再撮影の log 読み: row 7（controller record）・R3（cap 印字）・(iii) 停止の三者一致・tool_err_mm L vs R — 数値の報告（⛔ PASS ではない）

**Author** pB / LOG-ANALYST (`w2:pB`) · **Written** 2026-09-20 23:22:56 JST on m-p18-473（hub の着地 relay・p0 m-p0-389R 逐語）. Naming per m-p18-256: **Rs1 = 人間 / Rs2 = p4**.
**Scope** = 形 v1+v2（`00-DESIGN-STATUS-LEDGER.md` 行 69 @ `8f1d899d1bc89ef7d3a1df826291d680d98689eb`・(6) pB の leg ＋ (v2-2) tool_err_mm 報告）。本 file は **数値の報告のみ**。⛔ numeric 単独 PASS は出さない（B4）— 最終 = pC 視覚 leg ＋ Rs1 目視・受入 = p4（pB verdict・VERDICT_C・Rs1 の語 ＋ pZ 照合行の後）。早期停止（end_reason = raised・OUT.mp4 無し）は item 75（`e384c3737d`）のとおり形の欠落ではない。
**読み手への注意**: 本 file の数値は run.log / RUN_METRICS.json の印字を**逐語**で写した（pZ C-3 の再導出用・丸めていない）。私の判断語は §6「限界」だけに置き、他は driver が印字した事実の転記である。

## 0. 同一性（私が 23:18 JST に再計算）

| 物 | path（as-run） | sha256 | 照合 |
|---|---|---|---|
| `run.log` | `/home/rlrk/p0_runs/run69_reshoot_20260920/run.log`（402 行・88,755 B） | `9fe9685aba333506df9d9199e3cfe826e62c715899e48b8ca2034d8a796b22fa` | = p0 §8.66 @ `4583fa7444` = hub m-p18-473 = sidecar `run.log.sha256` = RUN_METRICS `run.log_sha256_at_write` ✓（⚠ `.gitignore:5` で未 commit・on-disk 2 path で bank = addendum 1 @ `26e0f20c38`） |
| `RUN_METRICS.json` | 同 dir（17,745 B） | `bcf7fa5783b1e60207f34ac7fb2ad905920e87964eb21dd010b4179bbdedf8e4` | = p0/hub ✓・repo copy `P0_RUN69_RESHOOT_20260920/RUN_METRICS.json` @ `4583fa7444` と同一 ✓ |
| driver | as-run tree の `ur15_steps_wired.py` = blob `84a372439c59` | `f461984bd7016a4ed66de0d9c3453f9416ca4e7d802e730dffc185da4ddd9b0f`（RUN_METRICS `ur15_steps.driver`） | = p0 §8.66 ✓ |
| cell dump | `_gen/_steps_cell_full.xml` | `f650fc322781a915dbb72565aa60d19d6bb7b1d9db9ecdbfb0b39969cd1ae4e0`（RUN_METRICS `ur15_steps.cell_dump`） | = p0/hub ✓・**⚠ item 69 ③ の期待 `4158e4e6…` と不一致**（p0/hub/p6 が表面化・p0 の読み = 期待値は override 0.22/45 の別 cell・本 run は C-2 既定 0.28/20・RUN_METRICS `config`: yoke_spread_m 0.28 / tilt_deg 20.0 / crown_r_m 0.11）— **語 = p4・私は判定しない**・text 読み = pZ C-4 |
| env | `config.env_switches_set` = `{}`（set された key だけが入る辞書 = 全未設定）／repo `env_before.txt`・`env_after.txt` @ `4583fa7444` = 26 行すべて `<unset>`（`_RM_ENV` 24 ＋ MUJOCO_GL・CUDA_VISIBLE_DEVICES） | — | = hub (b) ✓ |
| 時刻 / rc | `start_time.txt` 22:55:08 JST・`end_time.txt` 23:03:12 JST・`exit_code.txt` = `rc=1`・RUN_METRICS `run.elapsed_s` 483.301 | — | = p0 ✓ |
| 動画 | `artifacts.video.final.exists_at_write` = **false**（OUT.mp4 未生成）・`live.exists_at_write` = true（`~/Downloads/ur15_live.mp4`・copy `ur15_live_69_20260920.mp4` sha `9818e050…` = hub pin・**私は動画を開いていない**） | — | item 75 |

## 1. row 7 — `[steps] controller record L/R`（run.log `:41`・`:42` 逐語）

```text
[steps] controller record L: class=existing per-arm 6D DLS + position servo; AXFIX c=[+0.000000 +1.000000 -0.000000] s=[+1.000000 -0.000000 -0.000000] a=[-0.000000 +0.000000 -1.000000]; QADR=[np.int32(0), np.int32(1), np.int32(2), np.int32(3), np.int32(4), np.int32(5)] VADR=[np.int32(0), np.int32(1), np.int32(2), np.int32(3), np.int32(4), np.int32(5)] AIDX=[2, 3, 4, 5, 6, 7] GIDX=0 PAD=[20, 14] TOOLB=9; sgn=-1.0; design=P11_UR15B_CONTROLLER_DESIGN_20260913.md@dc090f7753
[steps] controller record R: class=existing per-arm 6D DLS + position servo; AXFIX c=[+0.000000 +1.000000 +0.000000] s=[+1.000000 -0.000000 +0.000000] a=[+0.000000 +0.000000 -1.000000]; QADR=[np.int32(14), np.int32(15), np.int32(16), np.int32(17), np.int32(18), np.int32(19)] VADR=[np.int32(14), np.int32(15), np.int32(16), np.int32(17), np.int32(18), np.int32(19)] AIDX=[8, 9, 10, 11, 12, 13] GIDX=1 PAD=[40, 34] TOOLB=29; sgn=+1.0; design=P11_UR15B_CONTROLLER_DESIGN_20260913.md@dc090f7753
```

| 側 | 印字（9 数・逐語） | 期待（pZ B 行 prereg row 7 `e41d0a9304` `:16`） | max\|印字 − 期待\|（数値として） | bar 1e-6 |
|---|---|---|---|---|
| L | c=[+0.000000 +1.000000 −0.000000] s=[+1.000000 −0.000000 −0.000000] a=[−0.000000 +0.000000 −1.000000] | c=[0 +1 0] s=[+1 0 0] a=[0 0 −1] | **0.000e+00** | 内 |
| R | c=[+0.000000 +1.000000 +0.000000] s=[+1.000000 −0.000000 +0.000000] a=[+0.000000 +0.000000 −1.000000] | 同上 | **0.000e+00** | 内 |
| 鏡像関係 | max\|AXFIX_R − diag(1,−1,1)·AXFIX_L·diag(−1,1,1)\|（A = diag(−1,1,1) は pZ 計器 `:70` のとおり） | ≤ 1e-6 | **0.000e+00** | 内 |

- 零の符号: L の c[2]・s[1]・s[2]・a[0] と R の s[1] は `-0.000000` で印字。prereg row 7 の注記どおり**差ではない**（数値比較で 0）。
- 記録のみ（bar でない・Rs1 の理由）: L = QADR 0-5・VADR 0-5・AIDX 2-7・GIDX 0・PAD [20, 14]・TOOLB 9・sgn **−1.0**／R = QADR 14-19・VADR 14-19・AIDX 8-13・GIDX 1・PAD [40, 34]・TOOLB 29・sgn **+1.0**。index は `np.int32(...)` 包みで印字（表示の形・値は整数）。class 文字列と design 文字列は両側同一（`dc090f7753`）。
- 印字位置 = driver `:621-628`（module 冒頭・step loop `:3174` より前）⇒ 早期停止でも在った（本節が実証）。

## 2. R3 — `[steps] vertical check`（run.log `:112` 逐語）

```text
[steps] vertical check: allowance 5.73 deg, cap 5.73 deg (the smallest non-zero tilt the attitude menu can make, measured as pinch->mouth against world -z, not as a roll); the allowance is an interim until a run reports the worst residual an upright command actually leaves (L 5.73 / R 5.73, each side under the attitude it receives)
```

| 項 | 印字 | pZ R3 prereg `98d8e63173`（R3-i・対称 live 状態） | 照合 |
|---|---|---|---|
| cap（`{:4.2f}`） | **5.73** | 5.73（= 5.729578° = 0.10 rad の 2 桁印字） | 一致（印字は 2 桁・生の 5.729578 は印字されない ⇒ 1e-6 の bar は pZ の再導出 C-2 が担う） |
| (L / R) | **(L 5.73 / R 5.73)** | (L 5.73 / R 5.73) | 一致 |
| allowance | 5.73 | 記録のみ | — |
| calibration raise（`:1301` 系・upright > 0.5°） | 発火せず（本行が印字された） | R3-iii: 対称なら発火しない | 整合 |

## 3. (iii) 停止・札・rc・phase — 三者一致（run.log ↔ RUN_METRICS `run` ↔ p0 §8.66 の札行）

| 面 | 内容（逐語または実測） |
|---|---|
| run.log | Traceback = **1 回**（`:375`）・raise 元 = driver `<module>` line **3996**（`:376`・as-run tree の `ur15_steps_wired.py` = blob `84a372439c59` の stall raise `:3996-3997`）・`:378` = `RuntimeError: STEP2 L: THIS arm's command stopped advancing for a whole step's worth of ticks and its move did not finish (the other arm was still advancing, at 100.0% -- the ramps are per arm now, so this is one arm stalling and not the run freezing).  Everything above this line is the state at the stall.  Continuing would re-measure the stalled arm's configuration once per remaining step, which is what the run before the per-arm split did.`・その後 `:379-401` = DEPTH AUDIT（at exit・atexit）・`:402` = `[steps] RUN_METRICS.json -> /home/rlrk/p0_runs/run69_reshoot_20260920/RUN_METRICS.json  (end_reason=raised)` |
| RUN_METRICS `run` | `end_reason` = **"raised"**・`exit_code` = **1**・`exception.type` = **"RuntimeError"**・`exception.message` = run.log `:378` の `RuntimeError: ` 以降と**バイト同一**（私が機械照合）・`log_sha256_at_write` = run.log の sha と同一・`progress.phase_max_reached` = **2**・`judgement.verdict` = "PENDING"（driver は判定しない） |
| p0 §8.66 札行（`4583fa7444`） | 「**controller の不収束**」（§17.4 3 分類・stall raise `:3996-3997`・calibration raise `:1310` 系ではない）＋ run.log `:375-378` ＋ RUN_METRICS の end_reason/exception 逐語 = (D1) の形。停止 1・札 1 |
| 三者 | **一致**（同じ 1 停止を指す・文言同一・行番号同一）。`[steps] STOP`／`stop-cause`／`§11` の文字列 = run.log に **0**（grep）— driver は札を印字しない = (D1) どおり |
| rc | `exit_code.txt` = rc=1・RUN_METRICS `exit_code` 1・log の end_reason=raised = 一致 |
| phase | `phase_max_reached` = 2・`steps[]` = 1 entry（step 2「cable上空へ」・`t_s` 2.19999648）・STEP1 は `step1_approach` ブロック。`steps[0].summary_row` = run.log `:374` の `[steps] ` 接頭辞を除いた本文と一致（末尾一致を機械照合） |
| 停止直前の状態（driver 印字の事実・逐語抜粋） | `:362` `[steps] STEP 2 COMMAND L: reached   0.0% of the way to the solved pose in    2.2s (…), held back on 10560 of 10560 ticks because THIS arm was more than 5.1 mrad behind its own command   <- STALLED …`／`:363` `[steps] STEP 2 COMMAND R: reached 100.0% … never held back`／`:364` `sigma_min L=0.1105 R=0.1517  mast L=-0.6 mm (g12 on Lg_base vs crown) R=+27.6 mm (g42 on R_shoulder_link vs crown)   <- INSIDE THE MAST`／`:369` `STEP 2 ARM-TO-ARM: closest -1.1 mm (9 <-> 42)  <- TOUCHING OR THROUGH`／`:374` `STEP 2 cable上空へ     t=  2.2s L=1126.4mm R=   2.2mm c1[y+0.280 z+0.149] c2[y+0.280 z+0.150] pin=--/-- grip=--`。RUN_METRICS `steps[0].command` = L {reached_frac 0.0, held_ticks 10560, ticks 10560, stalled true} / R {1.0, 0, 10560, false} |

## 4. tool_err_mm L vs R（(v2-2)・p11 §17.24 補完 1・**報告等級・bar なし**）

定義（driver blob `84a372439c59`）: `step1_approach.{t}.tool_err_mm` = `|pinch(t) − GRASP1[t]|·1000`（`:2832`）／`steps[*].tool_err_mm.{L,R}` = `|pinch(t) − tgt[t]|·1000`（`:3810-3811`・その step の目標・step 末の値）。単位 mm。**回転誤差は記録されない**（p11 の指摘どおり = 穴のまま名指し）。

| 記録 | L [mm]（逐語） | R [mm]（逐語） | run.log の対応行 |
|---|---|---|---|
| `step1_approach` | **658.4929864857596** | **2.1924360046211926** | `:102` `[steps] STEP1 L: tool err= 658.5mm`／`:107` `[steps] STEP1 R: tool err=   2.2mm` |
| `steps[0]`（step 2「cable上空へ」・t 2.2 s） | **1126.4214452980132** | **2.1632956854191416** | `:374`（上掲） |

driver が同時に印字した事実（逐語抜粋・**因果の判定はしない = p4/p11 の court**）:
- `:92` `[steps] 88mm-SPAN INTERLEAVE: arms closest +0.0 mm (6 <-> 50)   <- TOUCHING OR THROUGH   spread 0.280 tilt 20.0 deg   crown r 0.110   ⚠ commanded span, not the links actually held`
- `:93` `[steps] STANDING ERROR L: 662.68 mrad at rest vs TRACK_TOL 5.14 mrad -> ⛔ THE RAMP GATE CANNOT OPEN (room <= 0 before anything moves)`／`:94` per joint `j0=-8.8 j1=-662.7 j2=-112.6 j3=-8.5 j4=+312.0 j5=-1.8`・touching `['R_shoulder_link (via g9 on L_wrist_3_link)', 'column (via g13 on Lg_base)']`
- `:95` `[steps] STANDING ERROR R: 0.22 mrad at rest vs TRACK_TOL 5.14 mrad -> gate opens with 96% of the tolerance free`
- `:99-100` STEP1 touching: L = `['R_shoulder_link (via g9 on L_wrist_3_link)', 'column (via g13 on Lg_base)']`／R = `['L_wrist_3_link (via g42 on R_shoulder_link)']`（RUN_METRICS `step1_approach.*.touching` と同一）
- `:103-106` STEP1 L: joint err `[-8.8 -662.7 -112.6 -8.5 312.0 -1.8]` mrad・act force `[88.8 433. 204. 10.5 -70. 2.]` N·m（limits 433/433/204/70/70/70）・saturated `[False, True, True, False, True, False]`／`:108-111` STEP1 R: joint err ≈ 0・saturated 全 False
- 私の読み（推測ではなく印字の並びの記述）: L の tool_err は STEP1 で既に 658 mm・STEP 2 で 1126 mm・R は両 step とも ≈ 2.2 mm。L は rest から `R_shoulder_link` と `column` に接触したまま 3 関節が力限界で飽和し、STEP 2 の指令に 0.0% しか進めず stall raise に至った、と driver 自身が印字している。**どれが原因でどれが結果かは本 file では判定しない。**

## 5. 表示専用・証拠に読まない行（記録）

- `:72` `… channels NOT exercised this run: ['gap', 'jaw_gaps', 'release_ctrl']`（prefix 時点）／`:382` `… channels NOT exercised this run: ['release_ctrl']`（at exit）— `release_ctrl` は構造上常に NOT exercised（m-p18-333・kickoff `:2317` @ `1ee30ee1a0`・blob `:1643`/`:1646`）⇒ **証拠に読まない**。`gap`/`jaw_gaps` の prefix 行は「その時点まで呼ばれていない」の表示であり、at exit では `jaw_gaps:1007` が MEASURED に入っている（`:383`）。いずれも本 leg の bar ではない。
- DEPTH AUDIT の率・counter 群（`:69-91`・`:379-401`）は本 leg の対象外（読んだが判定に使わない）。

## 6. 限界（honest scope）

1. 本 file は **数値と印字の転記**であり、工程の成否・物理妥当性・原因を判定しない。stall した run への受入 word は「札・映像・log の一致」の語であって工程の成功ではない（item 75）。
2. **動画は開いていない**（pC の独立性・私の leg の外）。
3. R3 の 1e-6 bar は印字（2 桁）では閉じない ⇒ pZ C-2 の再導出が担う。row 7 の 18 数は印字が 6 桁で期待が整数のため、差 0 は印字精度内の一致（真値の差 < 5e-7）。
4. run.log は gitignore で未 commit ⇒ 私は as-run copy を読み、sha を 3 面（p0 SHA256SUMS.txt @ `4583fa7444`・sidecar・RUN_METRICS）と照合した。commit 形は p4 の語（addendum 1）。
5. cell dump sha の期待不一致（§0）は報告のみ・語 = p4・text 読み = pZ C-4。
6. reader の exit 0 は「必要行が在り bar 内」であって PASS ではない。

## 7. 産物

- 本 file（1 file・pathspec commit）。
- Appendix A = reader `pb_run69_reader.py` 逐語（sha256 `3c860ebb82eca1e9237da923c93928df1a276b5e0bbaa886c7d329864b363eb9`）・対照発火は memory `handoff_cc_pB_loganalyst_pin_contamination_2026-07-14.md` 2026-09-20 23:09 節に記録（U0 08-10 log → row7 ABSENT・exit 2／合成 正 → exit 0／1 数 2e-6 ずれ → exit 1／零の符号反転 → exit 0／cap 尾部違い → exit 1）。
- Appendix B = reader の出力逐語（本 run）。

## Appendix A — `pb_run69_reader.py`（逐語・sha256 `3c860ebb82eca1e9237da923c93928df1a276b5e0bbaa886c7d329864b363eb9`）

```python
#!/usr/bin/env python3
"""pB (LOG-ANALYST) reader for run #69: row 7 (AXFIX print), R3 (cap print), (iii) stops, RUN_METRICS paths.

Usage: pb_run69_reader.py RUN_LOG [RUN_METRICS_JSON]
Exit: 0 = every required line present and every bar met; 1 = a bar failed; 2 = a required line absent.
Bars: pZ B-line prereg row 7 @ e41d0a9304 :16 (18 AXFIX numbers <= 1e-6 vs expected, as numbers;
      |AXFIX_R - diag(1,-1,1).AXFIX_L.diag(-1,1,1)| <= 1e-6; index ints are a record, not a bar);
      pZ R3 prereg @ 98d8e63173 R3-i (printed cap '5.73' and tail '(L 5.73 / R 5.73)' in a symmetric live state).
Notes: the DEPTH AUDIT 'NOT exercised [release_ctrl]' line is display-only (m-p18-333) and is reported, not judged.
       This script reports numbers; it does not issue PASS (numeric-alone PASS is forbidden; pC + Rs1 are final).
"""
import hashlib, json, re, sys
TOL = 1e-6
EXP = {"L": [[0, 1, 0], [1, 0, 0], [0, 0, -1]], "R": [[0, 1, 0], [1, 0, 0], [0, 0, -1]]}
NUM = r"([-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)"
REC = re.compile(r"\[steps\] controller record (L|R): class=(.*?); AXFIX c=\[" + NUM + " " + NUM + " " + NUM
                 + r"\] s=\[" + NUM + " " + NUM + " " + NUM + r"\] a=\[" + NUM + " " + NUM + " " + NUM
                 + r"\]; (QADR=.*?); sgn=" + NUM + r"; design=(\S+)")
VC = re.compile(r"\[steps\] vertical check: allowance ([0-9.]+) deg, cap ([0-9.]+) deg")
VCT = re.compile(r"\(L ([0-9.]+) / R ([0-9.]+), each side")
def mm(a, b):  # 3x3 product
    return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
def main(log_path, rm_path=None):
    rc, out = 0, []
    b = open(log_path, "rb").read(); lines = b.decode("utf-8", "replace").split("\n")
    out.append(f"run.log = {log_path}  bytes={len(b)}  sha256={hashlib.sha256(b).hexdigest()}")
    # ---- row 7
    ax, rec_lines = {}, {}
    for i, ln in enumerate(lines, 1):
        m = REC.search(ln)
        if m:
            t = m.group(1); v = [float(x) for x in m.groups()[2:11]]
            ax[t] = [v[0:3], v[3:6], v[6:9]]; rec_lines[t] = (i, m.group(2), m.group(12), m.group(13), m.group(14))
    for t in ("L", "R"):
        if t not in ax:
            out.append(f"row7 {t}: ABSENT (no '[steps] controller record {t}' line)"); rc = max(rc, 2); continue
        i, cls, idx, sgn, design = rec_lines[t]
        d = max(abs(ax[t][r][c] - EXP[t][r][c]) for r in range(3) for c in range(3))
        out.append(f"row7 {t}: line {i}  class='{cls}'  {idx}  sgn={sgn}  design={design}")
        out.append(f"row7 {t}: raw c={ax[t][0]} s={ax[t][1]} a={ax[t][2]}  max|AXFIX-expected|={d:.3e}  bar 1e-6 -> {'within' if d <= TOL else 'EXCEEDED'}")
        if d > TOL: rc = max(rc, 1)
    if "L" in ax and "R" in ax:
        pred = mm(mm([[1, 0, 0], [0, -1, 0], [0, 0, 1]], ax["L"]), [[-1, 0, 0], [0, 1, 0], [0, 0, 1]])
        d = max(abs(ax["R"][r][c] - pred[r][c]) for r in range(3) for c in range(3))
        out.append(f"row7 mirror: max|AXFIX_R - diag(1,-1,1).AXFIX_L.diag(-1,1,1)|={d:.3e}  bar 1e-6 -> {'within' if d <= TOL else 'EXCEEDED'}")
        if d > TOL: rc = max(rc, 1)
    # ---- R3 (print)
    vcs = [(i, ln) for i, ln in enumerate(lines, 1) if VC.search(ln)]
    if not vcs:
        out.append("R3: ABSENT (no '[steps] vertical check' line)"); rc = max(rc, 2)
    for i, ln in vcs:
        m = VC.search(ln); mt = VCT.search(ln)
        out.append(f"R3: line {i}  allowance={m.group(1)} cap={m.group(2)}  tail={'(L %s / R %s)' % mt.groups() if mt else 'ABSENT (no per-side tail = pre-D4 form)'}")
        if m.group(2) != "5.73": out.append("R3: printed cap != '5.73' (R3-i symmetric expectation; asymmetric state -> R3-ii, read the raw)"); rc = max(rc, 1)
        if not mt: rc = max(rc, 2)
        elif mt.groups() != ("5.73", "5.73"): out.append("R3: tail != (L 5.73 / R 5.73)"); rc = max(rc, 1)
    # ---- (iii) stops / tags / audit / exit
    for i, ln in enumerate(lines, 1):
        if ln.startswith("Traceback") or re.match(r"^\w*(Error|Exception|Exit)\b", ln):
            out.append(f"stop: line {i}: {ln[:200]}")
        if "DEPTH AUDIT channels NOT exercised" in ln:
            out.append(f"audit: line {i}: {ln[:160]}  <- display-only (m-p18-333); not evidence")
        if "RUN_METRICS.json ->" in ln or "[steps] STOP" in ln or "stop-cause" in ln:
            out.append(f"exit/tag: line {i}: {ln[:200]}")
    # ---- RUN_METRICS
    if rm_path:
        rm = json.load(open(rm_path)); run = rm.get("run", {}); us = rm.get("ur15_steps", {})
        out.append(f"RM run: end_reason={run.get('end_reason')} exit_code={run.get('exit_code')} exception={run.get('exception')} log_path={run.get('log_path')}")
        out.append(f"RM run: log_sha256_at_write={run.get('log_sha256_at_write')} (prefix at write; sidecar run.log.sha256 = exact final)")
        out.append(f"RM progress.phase_max_reached={rm.get('progress', {}).get('phase_max_reached')}  judgement={rm.get('judgement')}")
        out.append(f"RM artifacts.video={rm.get('artifacts', {}).get('video')}")
        out.append(f"RM env_switches_set={us.get('config', {}).get('env_switches_set')}  (only keys present in environ; expected {{}} )")
        out.append(f"RM driver.sha256={us.get('driver', {}).get('sha256')}  cell_dump.sha256={us.get('cell_dump', {}).get('sha256')}")
        s1 = us.get("step1_approach", {})
        out.append("RM tool_err_mm step1_approach: " + "  ".join(f"{t}={s1.get(t, {}).get('tool_err_mm')}" for t in ("L", "R")) + "  (report grade, no bar; rotation error not recorded)")
        for st in us.get("steps", []):
            te = st.get("tool_err_mm", {})
            out.append(f"RM tool_err_mm step {st.get('step')} {st.get('name')}: L={te.get('L')} R={te.get('R')}")
        da = us.get("depth_audit", {})
        out.append(f"RM depth_audit keys={sorted(da.keys()) if isinstance(da, dict) else da}  (release_ctrl row = display-only)")
    out.append(f"exit={rc}  (0=present+within bars, 1=bar exceeded, 2=required line absent; never a PASS by itself)")
    print("\n".join(out)); return rc
if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None))
```

## Appendix B — reader の出力（本 run・逐語）

```text
run.log = /home/rlrk/p0_runs/run69_reshoot_20260920/run.log  bytes=88755  sha256=9fe9685aba333506df9d9199e3cfe826e62c715899e48b8ca2034d8a796b22fa
row7 L: line 41  class='existing per-arm 6D DLS + position servo'  QADR=[np.int32(0), np.int32(1), np.int32(2), np.int32(3), np.int32(4), np.int32(5)] VADR=[np.int32(0), np.int32(1), np.int32(2), np.int32(3), np.int32(4), np.int32(5)] AIDX=[2, 3, 4, 5, 6, 7] GIDX=0 PAD=[20, 14] TOOLB=9  sgn=-1.0  design=P11_UR15B_CONTROLLER_DESIGN_20260913.md@dc090f7753
row7 L: raw c=[0.0, 1.0, -0.0] s=[1.0, -0.0, -0.0] a=[-0.0, 0.0, -1.0]  max|AXFIX-expected|=0.000e+00  bar 1e-6 -> within
row7 R: line 42  class='existing per-arm 6D DLS + position servo'  QADR=[np.int32(14), np.int32(15), np.int32(16), np.int32(17), np.int32(18), np.int32(19)] VADR=[np.int32(14), np.int32(15), np.int32(16), np.int32(17), np.int32(18), np.int32(19)] AIDX=[8, 9, 10, 11, 12, 13] GIDX=1 PAD=[40, 34] TOOLB=29  sgn=+1.0  design=P11_UR15B_CONTROLLER_DESIGN_20260913.md@dc090f7753
row7 R: raw c=[0.0, 1.0, 0.0] s=[1.0, -0.0, 0.0] a=[0.0, 0.0, -1.0]  max|AXFIX-expected|=0.000e+00  bar 1e-6 -> within
row7 mirror: max|AXFIX_R - diag(1,-1,1).AXFIX_L.diag(-1,1,1)|=0.000e+00  bar 1e-6 -> within
R3: line 112  allowance=5.73 cap=5.73  tail=(L 5.73 / R 5.73)
stop: line 375: Traceback (most recent call last):
stop: line 378: RuntimeError: STEP2 L: THIS arm's command stopped advancing for a whole step's worth of ticks and its move did not finish (the other arm was still advancing, at 100.0% -- the ramps are per arm now, so
exit/tag: line 402: [steps] RUN_METRICS.json -> /home/rlrk/p0_runs/run69_reshoot_20260920/RUN_METRICS.json  (end_reason=raised)
RM run: end_reason=raised exit_code=1 exception={'type': 'RuntimeError', 'message': "STEP2 L: THIS arm's command stopped advancing for a whole step's worth of ticks and its move did not finish (the other arm was still advancing, at 100.0% -- the ramps are per arm now, so this is one arm stalling and not the run freezing).  Everything above this line is the state at the stall.  Continuing would re-measure the stalled arm's configuration once per remaining step, which is what the run before the per-arm split did."} log_path=/home/rlrk/p0_runs/run69_reshoot_20260920/run.log
RM run: log_sha256_at_write=9fe9685aba333506df9d9199e3cfe826e62c715899e48b8ca2034d8a796b22fa (prefix at write; sidecar run.log.sha256 = exact final)
RM progress.phase_max_reached=2  judgement={'verdict': 'PENDING', 'decided_by': None}
RM artifacts.video={'final': {'path': '/home/rlrk/p0_runs/run69_reshoot_20260920/OUT.mp4', 'exists_at_write': False}, 'live': {'path': '/home/rlrk/Downloads/ur15_live.mp4', 'exists_at_write': True}}
RM env_switches_set={}  (only keys present in environ; expected {} )
RM driver.sha256=f461984bd7016a4ed66de0d9c3453f9416ca4e7d802e730dffc185da4ddd9b0f  cell_dump.sha256=f650fc322781a915dbb72565aa60d19d6bb7b1d9db9ecdbfb0b39969cd1ae4e0
RM tool_err_mm step1_approach: L=658.4929864857596  R=2.1924360046211926  (report grade, no bar; rotation error not recorded)
RM tool_err_mm step 2 cable上空へ: L=1126.4214452980132 R=2.1632956854191416
RM depth_audit keys=['_ret_flagged', '_ret_pair', 'below_lower', 'bound_informative', 'by_caller', 'calls', 'cand_evals', 'chan', 'chan_viol', 'checked', 'decider', 'last_flagged', 'neg', 'pairs', 'rej_flagged', 'rej_total', 'repair_signed', 'repair_zero', 'repaired', 'seg_disagree', 'seg_over', 'seg_under', 'seg_under_contact', 'seg_under_narrow', 'sign_checked', 'sign_ghost', 'sign_missed', 'type_all', 'type_pairs', 'unrepairable']  (release_ctrl row = display-only)
exit=0  (0=present+within bars, 1=bar exceeded, 2=required line absent; never a PASS by itself)
```

## Addendum 1（2026-09-20 23:27:22 JST・re m-p18-478 = p4 m-p4-309 観測 E への限界つきの答え）— (iii) の材料: 接触・sigma_min・mast・DEPTH AUDIT（逐語・判定なし）

p4 の問い（観測 E・裁定でない）: 札が「controller の不収束」か「幾何の詰まり（接触）」かは、pB の (iii)（DEPTH AUDIT・接触・sigma_min・mast）の後に p4 が裁定する。本 addendum は **その材料を run.log（sha `9fe9685aba333506df9d9199e3cfe826e62c715899e48b8ca2034d8a796b22fa`・同一 file）と RUN_METRICS.json から逐語で並べる**だけで、分類は行わない。⛔ `release_ctrl` の NOT exercised は表示専用（§5）。

### A1-1. 指令の追従に関する印字（driver の語で「stall」「held back」「saturated」を含む行）

- `:93` `[steps] STANDING ERROR L: 662.68 mrad at rest vs TRACK_TOL 5.14 mrad -> ⛔ THE RAMP GATE CANNOT OPEN (room <= 0 before anything moves)`
- `:94` `[steps] STANDING ERROR L per joint [mrad]: j0=-8.8 j1=-662.7 j2=-112.6 j3=-8.5 j4=+312.0 j5=-1.8   (no joint at a limit)   touching: ['R_shoulder_link (via g9 on L_wrist_3_link)', 'column (via g13 on Lg_base)']`
- `:95` `[steps] STANDING ERROR R: 0.22 mrad at rest vs TRACK_TOL 5.14 mrad -> gate opens with 96% of the tolerance free`
- `:102` `[steps] STEP1 L: tool err= 658.5mm`
- `:103` `          joint err   = [  -8.8 -662.7 -112.6   -8.5  312.    -1.8] mrad`
- `:104` `          act force   = [ 88.8 433.  204.   10.5 -70.    2. ] N.m   (limits (433.0, 433.0, 204.0, 70.0, 70.0, 70.0))`
- `:106` `          saturated   = [np.False_, np.True_, np.True_, np.False_, np.True_, np.False_]`
- `:362` `[steps] STEP 2 COMMAND L: reached   0.0% of the way to the solved pose in    2.2s (1.00x the 2.2s the table allots -- the table no longer ends the step), held back on 10560 of 10560 ticks because THIS arm was more than 5.1 mrad behind its own command   <- STALLED: no progress for a whole step's worth of ticks   <- THE MOVE DID NOT FINISH`
- `:363` `[steps] STEP 2 COMMAND R: reached 100.0% of the way to the solved pose in    2.2s (1.00x the 2.2s the table allots -- the table no longer ends the step), never held back`
- RUN_METRICS `steps[0].command` = L {"reached_frac": 0.0, "held_ticks": 10560, "ticks": 10560, "stalled": true} / R {"reached_frac": 1.0, "held_ticks": 0, "ticks": 10560, "stalled": false}

### A1-2. 接触・幾何に関する印字（driver の語で「touching」「TOUCHING OR THROUGH」「INSIDE THE MAST」「mast」「gap」を含む行）

- `:92` `[steps] 88mm-SPAN INTERLEAVE: arms closest +0.0 mm (6 <-> 50)   <- TOUCHING OR THROUGH   spread 0.280 tilt 20.0 deg   crown r 0.110   ⚠ commanded span, not the links actually held`
- `:99` `[steps] STEP1 L arm touching: ['R_shoulder_link (via g9 on L_wrist_3_link)', 'column (via g13 on Lg_base)']`
- `:100` `[steps] STEP1 R arm touching: ['L_wrist_3_link (via g42 on R_shoulder_link)']`
- `:364` `[steps] STEP 2 sigma_min L=0.1105 R=0.1517  mast L=-0.6 mm (g12 on Lg_base vs crown) R=+27.6 mm (g42 on R_shoulder_link vs crown)   <- INSIDE THE MAST`
- `:365` `[steps] STEP 2 ARM REACH: L  26.6 mm below the mouth (Lg_right_pad_f1ext), +609.1 mm vs the table | R  51.4 mm below the mouth (geom43), +147.5 mm vs the table`
- `:366` `[steps] STEP 2 AS REALISED: L 37.3 deg off straight down, pads +79.89 mm | R 20.1 deg off straight down, pads +79.89 mm   (the gate read the commanded state at solve time; this is what the step ended in)`
- `:369` `[steps] STEP 2 CARRY: L mouth[+0.394 -0.150 +0.636] holds cab39 at (-107.9,+429.6,-479.9) mm | R mouth[+0.189 +0.273 +0.199] holds cab33 at ( +7.5, +6.8,-47.5) mm`
- `:373` `[steps] STEP 2 PENETRATION: clear   (clip-cable contacts now: 0)`
- RUN_METRICS `steps[0].sigma_min` = {"L": 0.11047350128312033, "R": 0.151651571628065}／`steps[0].mast` = {"L": {"gap_mm": -0.6403175818046059, "who": "g12 on Lg_base vs crown"}, "R": {"gap_mm": 27.6162330999606, "who": "g42 on R_shoulder_link vs crown"}}／`steps[0].arm_to_arm` = {"closest_mm": -1.1194554926176923, "closest_who": "9 <-> 42", "along_move_mm": -1.168352386937335, "along_who": "9 <-> 42 at t=0.24s", "worst_so_far_mm": -1.168352386937335}／`steps[0].penetration` = {"inside_mm": 0.0, "part": "", "geom": "", "link": -1, "contacts": 0}
- RUN_METRICS `worst` = sigma_min {"L": 0.10793926206857601, "R": 0.14883235967913658} @ {"L": "STEP2 t=0.0s", "R": "STEP2 t=0.0s"}／mast_m {"L": -0.0007341430112716013, "R": 0.0276162330999606} @ {"L": "g12 on Lg_base vs crown, STEP2 t=0.0s", "R": "g42 on R_shoulder_link vs crown, STEP2 t=2.2s"}／arm_gap_min_m -0.0011194554926176922／arm_gap_path_m -0.001168352386937335

### A1-3. DEPTH AUDIT（at exit・run 全体の累積・`:379-401`）のうち接触・棄却に関わる行

- `:380` `[steps] DEPTH AUDIT [at exit -- cumulative over the WHOLE run]: 785850 calls, 335608 unsaturated, 4966 negative`
- `:381` `[steps] DEPTH AUDIT [at exit -- cumulative over the WHOLE run] channels exercised -- violations / calls (rate): furniture_gap:513 20/380000 (0.00526%) | arm_pair_min:1966 1018/279859 (0.36375%) | column_gap:1421 102/123854 (0.08236%) | jaw_gaps:1007 0/2124 (0.00000%) | gap:2878 0/13 (0.00000%)`
- `:383` `[steps] DEPTH AUDIT [at exit -- cumulative over the WHOLE run] coverage -- MEASURED: ['arm_pair_min:1966', 'column_gap:1421', 'furniture_gap:513', 'jaw_gaps:1007'] | ASKED BUT TOO FEW TIMES TO TELL: ['gap:2878 (13 calls)'] | NEVER ASKED: ['release_ctrl']`
- `:384` `[steps] DEPTH AUDIT [at exit -- cumulative over the WHOLE run] floor 1 (below the bounding-sphere gap): 386 (0.1150% of unsaturated) -- but its DENOMINATOR is the 234281 calls whose spheres were apart enough for the bound to say anything (69.81% of unsaturated), giving 0.1648% within that visible domain.  Outside it the bound is vacuous and a clean sheet from floor 1 is not evidence.`
- `:385` `[steps] DEPTH AUDIT [at exit -- cumulative over the WHOLE run] floor 2 (scalar disagrees with its own segment): 1140 (0.3397%) -- 0 claiming MORE room than the segment (over-acceptance), 1140 claiming LESS (over-rejection)`
- `:386` `[steps] DEPTH AUDIT [at exit -- cumulative over the WHOLE run] by call surface: arm_pair_min<-<module>:2554 x701, arm_pair_min<-<module>:3750 x280, column_gap<-<module>:2561 x99, arm_pair_min<-solve_ik:2199 x32, furniture_gap<-<module>:2562 x20, arm_pair_min<-_interleave_report:2496 x5, column_gap<-solve_ik:2295 x3`
- `:387` `[steps] DEPTH AUDIT [at exit -- cumulative over the WHOLE run] localisation: 455 distinct geom pairs; top pairs = 8<->42 x25, 14<->42 x23, 15<->42 x23, 10<->42 x22, 11<->42 x22, 12<->42 x19, 13<->42 x19, 16<->42 x17, 17<->42 x17, 44<->80 x10, 6<->80 x10, 26<->42 x10, 26<->43 x10, 20<->42 x10, 21<->42 x10, 8<->44 x8, 25<->43 x8, 27<->42 x8, 16<->54 x7, 16<->55 x7, 17<->54 x7, 17<->55 x7, 46<->1 x7, 8<->1 x7, 18<->42 x7, 19<->42 x7, 18<->43 x7, 19<->43 x7, 42<->8 x6, 20<->56 x5, 20<->57 x5, 21<->56 x5, 21<->57 x5, 12<->50 x5, 12<->51 x5, 13<->50 x5, 13<->51 x5, 9<->50 x5, 9<->51 x5, 12<->70 x5,  …〔以下切り詰め・原文 5494 字〕`
- `:388` `[steps] DEPTH AUDIT [at exit -- cumulative over the WHOLE run] mechanism -- violations / calls per geom-type pair (mesh x mesh is arm against arm, cylinder x mesh is arm against the stem and foot): MESHxMESH 855/134902 (0.63379%) | BOXxMESH 174/76215 (0.22830%) | CYLINDERxMESH 76/52849 (0.14381%) | CAPSULExMESH 0/36023 (0.00000%) | BOXxBOX 9/14417 (0.06243%) | CYLINDERxBOX 26/14034 (0.18526%) | CAPSULExBOX 0/7168 (0.00000%)`
- `:390` `[steps] DEPTH AUDIT [at exit -- cumulative over the WHOLE run] seg_under split: 1140 asserted CONTACT (dv <= 0, answerable by the contact list), 0 merely too narrow (dv > 0, a magnitude error the contact list cannot speak to)`
- `:391` `[steps] DEPTH AUDIT decider [at exit -- cumulative over the WHOLE run] (sole cause, one candidate one vote, untruncated): of 275 rejected candidates -- g6 on L_forearm_link vs crown x89, g6 on L_forearm_link vs stem x61, the other arm x22, g44 on R_forearm_link vs crown x15, g6 on L_forearm_link vs crown at 6/13 along the move (on the way) x12, g8 on L_wrist_2_link vs stem x4, g5 on L_upper_arm_link vs stem x4, g6 on L_forearm_link vs crown at 4/6 along the move (on the way) x3, g7 on L_wrist_1_link vs stem x3, g5 on L_upper_arm_link vs crown x3, g44 on R_forearm_link vs stem x3`
- `:392` `[steps] DEPTH AUDIT decider [at exit -- cumulative over the WHOLE run] (any cause, a candidate counts once per part that rejected it): g6 on L_forearm_link vs crown x96, the other arm x78, g6 on L_forearm_link vs stem x65, g44 on R_forearm_link vs crown x32, g6 on L_forearm_link vs crown at 6/13 along the move (on the way) x12, g43 on R_upper_arm_link vs stem x9, g5 on L_upper_arm_link vs stem x9, g8 on L_wrist_2_link vs stem x6, g44 on R_forearm_link vs stem x6, g5 on L_upper_arm_link vs crown x6, g6 on L_forearm_link vs crown at 4/6 along the move (on the way) x3, g7 on L_wrist_1_link vs stem x3, g44 on R_forearm_link vs crown at 3/6 along the move (on the way) x3, g43 on R_upper_arm_link vs crown x3`
- `:399` `[steps] DEPTH AUDIT [at exit -- cumulative over the WHOLE run] sign reference: 97 minima cross-checked against the solver's own contact list -- 4 asserted contact the solver does not record (ghost), 0 asserted clearance over a pair the solver IS contacting (miss).  ⚠ bounds neither way: contacts live inside the margin band only, and the list is per pair while the minimum is one pair.`
- `:400` `[steps] DEPTH AUDIT [at exit -- cumulative over the WHOLE run] rejection attribution: of 78 candidates dropped by the arm-clearance test, 4 were dropped by a call the floors had flagged (5.128%) -- measured, not bounded.  Candidate evaluations: 570; violations per evaluation = 2.68`

### A1-4. 対応づけ（印字にある名前だけ・私の同定はしない）

- geom 番号と link の対応は driver が印字したものに限る: `g9 on L_wrist_3_link`・`g42 on R_shoulder_link`・`g12`/`g13 on Lg_base`・`g6 on L_forearm_link`・`g44 on R_forearm_link`・`g5 on L_upper_arm_link`・`g7 on L_wrist_1_link`・`g8 on L_wrist_2_link`（`:94-95`・`:364`・`:369`・`:391-392`）。`:387` の pair 番号（例 `8<->42`・`44<->80`・`6<->80`）のうち上記に無い番号は私は同定しない。
- 接触の三面: (a) 解析器の接触リスト（`touching` = `:99-100`・RUN_METRICS `step1_approach.*.touching`）(b) 距離の最小値（`:369` ARM-TO-ARM −1.1 mm・`:364` mast L −0.6 mm・RUN_METRICS `worst.arm_gap_min_m` −0.00112）(c) DEPTH AUDIT の cross-check（`:399` 97 minima・ghost 4・miss 0）。三者はそれぞれ別の量であり、私はここで統合しない。
- 本 addendum は §6 の限界をそのまま引き継ぐ（数値の転記・因果と分類は p4 の裁定）。

## Addendum 2（2026-09-20 23:29:43 JST・re m-p18-479 = p0 m-p0-390R: run.log の commit 形）— 本 file の run.log 行番号 cite の恒久 pin

- run.log は p4 の語 ③ どおり **同名のまま force-add で commit** された: `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/P0_RUN69_RESHOOT_20260920/run.log` @ `0d22720834` = blob **`c79fdfd1d4105d6e1bda1f37a33a2c599123c2f3`**（`run.log.sha256` = blob `39069c26134f1b7ee5fe45a20211b3fe83386c68`・記録 = p0 §8.66 addendum 4 @ `ac2268483c`）。
- 私の再計算（23:29 JST）: blob の内容 sha256 = `9fe9685aba333506df9d9199e3cfe826e62c715899e48b8ca2034d8a796b22fa`・402 行・**as-run copy `/home/rlrk/p0_runs/run69_reshoot_20260920/run.log` とバイト同一**（`cmp` = 差なし）・HEAD でも同 blob。
- ⇒ 本 file の `:41-42`・`:112`・`:375-378`・`:92-111`・`:362-374`・`:379-402` 等の **run.log 行番号は全て blob `c79fdfd1d410…` の中の位置として読める**（§0 の「未 commit・on-disk で bank」は本 addendum で解消。§0 の記述は当時の事実として残す）。数値・判定なしの立場は不変。

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

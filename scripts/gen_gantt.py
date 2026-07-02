#!/usr/bin/env python3
"""Gantt-like execution-ORDER view of the live-spine — complements the simplified tree (structure)
with the SEQUENCE / dependency / parallelism. Order positions are grounded on the NEST precedent/blocker
edges (state.md). Logical-order X-axis (NOT calendar). Dark theme -> chrome PNG."""
# === REFRESH CONTRACT (planning-surface consolidation, node T-ROOT-Planning-Surfaces-Consolidation-20260702, M1) ===
# WHAT  : the §1 Gantt-like execution-ORDER view (sequence / dependency / parallelism).
# INPUT : ordering grounded on NEST precedent/blocker edges (state.md).
# HAND-MAINTAINED (!): the TASKS list and NOW frontier marker (below) are HAND-CODED literals, NOT
#         auto-derived from the SSOT. Edit them by hand when the plan changes. (This is why the live
#         map §1 caption reclassifies Gantt TASKS/NOW as "手保守 curated", not SSOT-auto-linked.)
# OUTPUT: writes OUT (below) = a DRAFT html fragment; then MANUALLY embed into
#         docs/logical_decomposition.html §1 iframe(2) srcdoc.
# WHEN  : re-run after editing TASKS/NOW or when dependency ordering changes, then re-embed.
# ===
OUT = "/home/rlrk/IsaacLab/eval_runs/troot_nest_rebase_visualtree_20260623/gantt_order.html"
TOTAL = 10.0
NOW = 6.6  # frontier = R-S6.6 grasp-robustness: held-rate 30/30 + IC-ROBUST 30/30 (6/24) 済 → grasp公差(cable-state-space) 特性化中

# lane, label, start, end, status, dep-note
# status: done / active / pend / gated / blocker
TASKS = [
    ("基盤",   "R0/R1 計測・述語",        0.0, 2.0, "done",   ""),
    ("基盤",   "Option-E 基盤",           2.0, 3.0, "done",   "← R1 / env7物理"),
    ("基盤",   "L1X 基盤realism(cable/solver)", 2.0, 7.0, "active", "並行・基盤忠実(cable_drop)・FCの前提だがfoundationはphase3充足済→refinement並行(soft-precedent)"),
    ("基盤",   "R-S7.1 把持(コ型)",        3.0, 4.0, "done",   "← Option-E / コ CPU building-block banked"),
    ("基盤",   "R-S6.6 GPU安定化",         3.0, 6.5, "active", "← Option-E / RLに必要 / cg#1415→30/30 finite + held-rate 30/30 + IC-ROBUST 30/30 (6/24)✓ / grip-under-load・real-fidelity残"),
    ("基盤",   "grasp公差 (cable-state-space)", 6.3, 7.2, "active", "← R-S6.6 / Stage A位置・A'姿勢yaw≥12°(achieved=commanded)済・B曲げ形状 in-prep ◀ 今ここ / pos/pose-random=deploy要件 (SOMA L38 supersede 6/24)"),
    ("能力",   "単clip route/hook",       4.0, 5.0, "done",   "← R-S7.1"),
    ("能力",   "off-center grasp",        5.0, 6.0, "done",   "← 単clip / 傾き=非問題・機能OK (decision B 6/24)"),
    ("能力",   "multi-clip (C1→C5)",      6.0, 7.5, "pend",   "← off-center + retention解決"),
    ("能力",   "知覚 Perception(位置推定)", 3.0, 8.0, "pend",   "並行・独立(依存なし)・いつでも開始可"),
    ("能力",   "retention (ピン/衝突)",    3.0, 7.0, "blocker","並行・独立(Rs-scope)・pin採用決定済/実装ゲート待ち"),
    ("学習",   "DA-MPPI demo生成",        2.5, 7.0, "active", "並行・Option-E(済)依存のみ・env7再生成・DAPGをseed"),
    # DAPG RL = 5-skill 直列 (env7, ALL gated; env6実績=旧Newton VBD track の参考値, fidelity-quarantine別track)
    ("学習",   "①AC 接近",   8.0, 8.5,  "gated",  "DAPG RL 5skill① ApproachCable(常時OPEN, ケーブルへ接近) / env6実績49% / env7=gated(前提4トラック grasp公差・GPU R-S6.6・RL-scope・env7基盤 + DR + Residual)"),
    ("学習",   "②GC 把持",   8.34,8.84, "gated",  "② Clamp/Grip(OPEN→CLOSED, 閉じタイミング・把持力の学習) / env6実績0% / env7=gated"),
    ("学習",   "③IC 挿入",   8.68,9.18, "gated",  "③ InsertIntoClip(常時CLOSED, groove押込+着座) / env6実績39% / env7=gated"),
    ("学習",   "④AR 再把持", 9.0, 9.5,  "gated",  "④ AerialRegrasp(clip間ハンドオーバー接近, L:CLOSED/R:approach) / env6実績92%*(fidelity-QUARANTINE) / env7=gated"),
    ("学習",   "⑤CR しごき", 9.2, 9.7,  "gated",  "⑤ guide/route しごき(Rs2026-06-24追加の5番目, 新規・未訓練, RL化は実装ゲート) / env7=gated"),
    ("将来/Rs","#2 述語再定義",            0.7, 9.7, "active", "並行 Rs 軸 / 目標=100% 定性化 (旧厳密直列SRを再定義)"),
    ("将来/Rs","#3 R2 アーキ再設計",       9.2,10.0, "pend",   "deferred (条件付)"),
]

PHASES = [(0,"①基盤計測"),(2,"②基盤物理"),(3,"③基盤仕上げ"),(4,"④単clip"),
          (5,"⑤off-center"),(6,"⑥multi-clip"),(7,"⑦学習RL"),(9,"⑧将来")]

COL = {"done":"#22c55e","active":"#f59e0b","pend":"#64748b","gated":"#7c3aed","blocker":"#ef4444"}
TXT = {"done":"完了","active":"進行中","pend":"未着手","gated":"gated(前提待ち)","blocker":"blocker"}

def pct(x): return f"{x/TOTAL*100:.2f}%"

rows = []
lanes = []
for lane, label, s, e, st, note in TASKS:
    if lane not in lanes:
        lanes.append(lane)
        rows.append(f'<div class="lanehdr">{lane}</div>')
    bar = (f'<div class="bar {st}" style="left:{pct(s)};width:{pct(e-s)};">'
           f'<span class="blbl">{label}</span></div>')
    note_s = f'<span class="note">{note}</span>' if note else ""
    rows.append(f'<div class="row"><div class="track">{bar}</div>{note_s}</div>')
rows_html = "\n".join(rows)

phase_ticks = "".join(f'<div class="tick" style="left:{pct(x)}">{lbl}</div>' for x, lbl in PHASES)
legend = "".join(f'<span class="lg"><i style="background:{COL[k]}"></i>{TXT[k]}</span>' for k in ["done","active","pend","gated","blocker"])

HTML = f"""<!DOCTYPE html><html lang="ja"><head><meta charset="utf-8">
<title>THREAD — 実行順序 (Gantt-like)</title><style>
  body{{margin:0;padding:24px 28px;background:#0f172a;color:#e2e8f0;font-family:-apple-system,"Hiragino Kaku Gothic ProN","Noto Sans CJK JP",sans-serif;}}
  h1{{font-size:18px;margin:0 0 3px;}} .sub{{color:#94a3b8;font-size:12.5px;margin:0 0 14px;}}
  .legend{{font-size:12px;color:#cbd5e1;margin-bottom:14px;}} .lg{{margin-right:14px;}} .lg i{{display:inline-block;width:11px;height:11px;border-radius:3px;margin-right:4px;vertical-align:-1px;}}
  .chart{{position:relative;background:#1e293b;border:1px solid #334155;border-radius:10px;padding:34px 18px 14px 150px;}}
  .axis{{position:absolute;top:8px;left:150px;right:18px;height:22px;}}
  .tick{{position:absolute;transform:translateX(-2px);font-size:10.5px;color:#94a3b8;border-left:1px solid #334155;padding-left:4px;height:100%;}}
  .row{{position:relative;min-height:30px;display:flex;align-items:center;margin:3px 0;}}
  .lanehdr{{font-size:11px;letter-spacing:.06em;color:#7dd3fc;text-transform:uppercase;margin:12px 0 2px -132px;font-weight:700;}}
  .track{{position:relative;height:24px;flex:0 0 calc(100% - 250px);width:calc(100% - 250px);background:linear-gradient(90deg,#0f172a 0,#0f172a 100%);border-radius:4px;}}
  .bar{{position:absolute;top:0;height:24px;border-radius:5px;display:flex;align-items:center;padding:0 8px;box-shadow:0 1px 3px rgba(0,0,0,.4);}}
  .blbl{{font-size:10.5px;font-weight:700;color:#0b1220;white-space:nowrap;overflow:visible;}}
  .bar.pend .blbl,.bar.gated .blbl,.bar.blocker .blbl{{text-shadow:0 1px 2px rgba(0,0,0,.6);}}
  .bar.done{{background:#22c55e;}} .bar.active{{background:#f59e0b;}} .bar.pend{{background:#64748b;}}
  .bar.pend .blbl{{color:#e2e8f0;}} .bar.gated{{background:#7c3aed;}} .bar.gated .blbl{{color:#ede9fe;}}
  .bar.blocker{{background:repeating-linear-gradient(45deg,#ef4444,#ef4444 6px,#b91c1c 6px,#b91c1c 12px);}} .bar.blocker .blbl{{color:#fff;}}
  .note{{font-size:10.5px;color:#94a3b8;margin-left:10px;white-space:normal;line-height:1.25;max-width:240px;}}
  .nowline{{position:absolute;top:30px;bottom:10px;left:calc(150px + (100% - 168px) * {NOW/TOTAL});width:2px;background:#fb7185;z-index:5;}}
  .nowlbl{{position:absolute;top:10px;left:calc(150px + (100% - 168px) * {NOW/TOTAL} - 14px);color:#fb7185;font-size:11px;font-weight:700;z-index:6;}}
  .foot{{margin-top:14px;font-size:11px;color:#94a3b8;border-top:1px solid #334155;padding-top:9px;}} .foot a{{color:#7dd3fc;}}
</style></head><body>
  <h1>THREAD — 実行順序 (Gantt-like) / どの順で進むか</h1>
  <p class="sub">X軸=実行順序(暦でなく論理順)。bar位置=NEST依存(precedent/blocker)から。縦線=今ここ。並行bar=同時進行。</p>
  <div class="legend">{legend}<span class="lg" style="color:#fb7185;font-weight:700;">▎今ここ</span></div>
  <div class="chart">
    <div class="axis">{phase_ticks}</div>
    <div class="nowlbl">今 ▼</div><div class="nowline"></div>
    {rows_html}
  </div>
  <div class="foot">順序は <code>nest-snapshot.json</code> の precedent/blocker 依存に接地(<code>gen_gantt.py</code>)。構造ビュー=簡易NEST tree、詳細=jsx tracker <a href="http://localhost:8765/index.html">localhost:8765</a>。<br><b>クリティカルパス:</b> Option-E → R-S7.1把持 → 単clip → off-center(完了) → R-S6.6 GPU held-rate 30/30(6/24完了) → ◀今ここ grasp公差(cable-state-space) → multi-clip → (gated)学習RL。R-S6.6 GPU は RL の前提。retention は blocker(pin採用決定済)。<br><b>並行トラック(依存なし・本線と同時進行):</b> L1X基盤realism / 知覚Perception / DA-MPPI demo / retention(Rs-scope) / #2述語再定義 / R-S6.6 GPU。本線=grasp pipeline(単clip→off-center→multi-clip)は直列。</div>
</body></html>"""
open(OUT,"w",encoding="utf-8").write(HTML)
print(f"wrote {OUT}  ({len(TASKS)} tasks, {len(lanes)} lanes, NOW={NOW})")

#!/usr/bin/env python3
"""Generate the SIMPLIFIED NEST tree (curated html) — a structural abstraction of the full
234-node NEST snapshot: expand the P0-KILL program spine + live-spine, collapse the 185-node
legacy subtree into one summary node. Derived from nest-snapshot.json (SSOT-consistent),
re-runnable (thin skin over the same snapshot — NOT a hand-narrative). Dark theme.
"""
# === REFRESH CONTRACT (planning-surface consolidation, node T-ROOT-Planning-Surfaces-Consolidation-20260702, M1) ===
# WHAT  : the §1 "simplified NEST tree" view (structural abstraction of the full NEST tree).
# INPUT : docs/nest-tracker/nest-snapshot.json (SSOT chain: per-node state.md -> build_nest_snapshot.py
#         -> nest-snapshot.json) + per-node state.md `status:`. This view IS SSOT-derived, re-runnable
#         (a thin skin over the snapshot, NOT a hand-narrative).
# OUTPUT: writes OUT (below) = a DRAFT html fragment; then MANUALLY embed its <body> into
#         docs/logical_decomposition.html §1 iframe(1) srcdoc (the live map = the single read entry).
# WHEN  : re-run after node state.md / nest-snapshot.json changes, then re-embed into the map.
#         This is manual re-generation, NOT auto-sync.
# ===
import json, re, os

REPO = "/home/rlrk/IsaacLab"
SNAP = f"{REPO}/docs/nest-tracker/nest-snapshot.json"
OUT = f"{REPO}/eval_runs/troot_nest_rebase_visualtree_20260623/overview_highabstraction_draft.html"
VAULT = f"{REPO}/thread_isaac_lab/thread-vault"

N = {n["id"]: n for n in json.load(open(SNAP))["nodes"]}

def real_status(nid):
    """Prefer state.md status (PENDING distinct); fall back to snapshot."""
    p = f"{VAULT}/{nid}/state.md"
    if os.path.exists(p):
        m = re.search(r"^status:\s*(\w+)", open(p, encoding="utf-8").read(), re.M)
        if m:
            return m.group(1)
    return N.get(nid, {}).get("status", "IN_PROGRESS")

# curated simplified structure: (node_id, label, note, [child node_ids], is_star, override_badge)
SPINE = [
    ("T-ROOT-R0-Measurement-Foundation", "R0 計測基盤", "f(1.0)=0.72 を計測", [], False, None),
    ("T-ROOT-R1-Product-Predicate-Decision", "R1 製品述語", "成功条件を確定", [], False, None),
    ("T-L1X-Substrate-Realism", "#1 L1.X 基盤の物理忠実性", "基盤の現実味=達成 / GPU・本物検証が残", [
        ("T-Option-E", "Option-E 基盤 (env7 物理エンジン)", "", None),
        ("T-RS6-6", "R-S6.6 GPU 安定化", "cg#1415-fix → held-rate 30/30 + IC-ROBUST 30/30 (6/24, 機構精度floor) / grasp公差(Stage A/A'/B) + deploy残", True),
        ("T-RS7-1", "R-S7.1 把持グリッパ = コ型", "コ CPU building-block banked / GPU held-rate 30/30 (6/24) / deploy残", None),
    ], False, None),
    ("T-Forward-Capability", "Forward Capability  実タスク能力", "掴む→運ぶ→挿す→保持 を CPU で成立 / 単clip・off-center済、multi-clip は grasp-robustness + retention 待ち", [
        ("T-FC-SingleClip", "単clip route/hook", "できた", None),
        ("T-FC-OffCenter-Grasp", "off-center grasp (傾き解消)", "傾き=非問題・機能OK (decision B 6/24)", False),
        ("T-FC-MultiClip", "multi-clip 連続 (C1→C5)", "", None),
        ("T-FC-Perception", "知覚 (カメラで位置推定)", "", None),
        ("T-Retention-Model", "retention-model (ピン vs 物理衝突)", "全体を止める blocker / Rs判断", None),
    ], False, None),
    ("T-L1C-PerSkill-RL", "L1.C 制御・学習 (DAPG + DA-MPPI = 学習の核)",
     "pipeline: DA-MPPI計画→専門家demo→DAPG(BC warmstart α0.5 + PPO)+DR(domain rand)+Residual-PPO modulator(heuristic失敗時)。env6 skill: AC49%/IC39%/AR92%*(quarantine)/GC0%/Unclamp=scripted。env7 L1.Cは前提4トラック(grasp/GPU/RL-scope/env7基盤)未達でgated", [
        ("T-DA-MPPI", "DA-MPPI (dual-arm planner / 専門家demo生成)", "env6 M3 done S3=100% / env7 re-gen (gated)", None),
    ], False, None),
    ("T-Predicate-Redefinition", "#2 述語再定義", "L0 目標 = 100% 定性的目標へ再定義 (旧・厳密直列SRスコープは P0-KILL)", [], False, None),
    ("T-ROOT-R2-Architecture-Redesign", "#3 R2 アーキ再設計", "今は保留(条件付き)", [], False, "deferred"),
]

# legacy collapse count
shown = set(x[0] for x in SPINE)
for x in SPINE:
    for c in x[3]:
        shown.add(c[0])
root_kids = set(N["T-ROOT"]["children"])
legacy_roots = [k for k in root_kids if k not in shown]
def subtree(nid, seen):
    if nid in seen:
        return
    seen.add(nid)
    for c in N.get(nid, {}).get("children", []):
        subtree(c, seen)
legseen = set()
for k in legacy_roots:
    subtree(k, legseen)
LEGACY_N = len(legseen)

SYM = {"COMPLETE": ("✅", "done"), "IN_PROGRESS": ("🔶", "active"),
       "PENDING": ("⏸", "pend"), "ARCHIVED": ("📦", "arch"), "DISCARDED": ("⛔", "disc")}

def badge(status, override=None):
    if override == "deferred":
        return '<span class="b pend">⏸ deferred</span>'
    sy, cls = SYM.get(status, ("🔶", "active"))
    txt = {"done": "完了", "active": "進行中", "pend": "未着手", "arch": "archived", "disc": "discarded"}[cls]
    return f'<span class="b {cls}">{sy} {txt}</span>'

# build tree lines with box-drawing connectors
lines = ['<span class="root">🌳 T-ROOT — 5-clip cable routing を vision で物理忠実に動かす  <span class="goal">(L0 = 100% 定性的)</span></span>']
TOP = SPINE + [("__legacy__", f"Legacy decomposition (pre-P0-KILL)", f"{LEGACY_N} node — 折りたたみ / 詳細は tracker", [], False, "legacy")]
for i, (nid, label, note, kids, star, ov) in enumerate(TOP):
    last = (i == len(TOP) - 1)
    conn = "└─" if last else "├─"
    if ov == "legacy":
        bdg = '<span class="b arch">📦 archived</span>'
    else:
        bdg = badge(real_status(nid), ov)
    star_s = ' <span class="star">★ いまここ</span>' if star else ""
    note_s = f'  <span class="note">— {note}</span>' if note else ""
    lines.append(f'<span class="conn">{conn}</span> {bdg} <span class="lbl">{label}</span>{star_s}{note_s}')
    vbar = "&nbsp;&nbsp;&nbsp;" if last else "│&nbsp;&nbsp;"
    for j, (cid, clabel, cnote, cstar) in enumerate(kids):
        clast = (j == len(kids) - 1)
        cconn = "└─" if clast else "├─"
        cb = badge(real_status(cid))
        cstar_s = ' <span class="star">★ いまここ</span>' if cstar else ""
        cnote_s = f'  <span class="note">— {cnote}</span>' if cnote else ""
        lines.append(f'<span class="conn">{vbar} {cconn}</span> {cb} <span class="lbl">{clabel}</span>{cstar_s}{cnote_s}')

tree_html = "\n".join(lines)

HTML = f"""<!DOCTYPE html>
<html lang="ja"><head><meta charset="utf-8">
<title>THREAD — 簡易化 NEST tree (§1 Visual Tree overview)</title>
<style>
  body{{margin:0;padding:26px 30px;background:#0f172a;color:#e2e8f0;font-family:-apple-system,"Hiragino Kaku Gothic ProN","Noto Sans CJK JP",sans-serif;}}
  h1{{font-size:18px;margin:0 0 3px;}}
  .sub{{color:#94a3b8;font-size:13px;margin:0 0 18px;}}
  .legend{{font-size:12px;color:#94a3b8;margin-bottom:16px;}}
  .tree{{background:#1e293b;border:1px solid #334155;border-radius:10px;padding:18px 20px;
    font-family:"SF Mono",Menlo,Consolas,monospace;font-size:13.5px;line-height:2.0;white-space:pre;overflow-x:auto;}}
  .root{{font-weight:700;color:#fde68a;font-size:14.5px;}}
  .goal{{color:#94a3b8;font-weight:400;font-size:12.5px;}}
  .conn{{color:#475569;}}
  .lbl{{color:#e2e8f0;font-weight:600;}}
  .note{{color:#94a3b8;font-weight:400;font-size:12px;}}
  .b{{display:inline-block;min-width:74px;text-align:center;padding:0 7px;border-radius:9px;font-size:11px;font-weight:700;color:#0b1220;}}
  .done{{background:#22c55e;}} .active{{background:#f59e0b;}} .pend{{background:#64748b;color:#e2e8f0;}}
  .arch{{background:#475569;color:#cbd5e1;}} .disc{{background:#ef4444;color:#fff;}}
  .star{{background:#7c2d12;color:#fed7aa;border:1px solid #f59e0b;border-radius:6px;padding:0 6px;font-weight:700;font-size:11px;}}
  .now{{margin-top:16px;background:#172554;border:1px solid #1e40af;border-radius:10px;padding:11px 14px;font-size:13px;}}
  .now b{{color:#93c5fd;}}
  .foot{{margin-top:16px;font-size:11.5px;color:#94a3b8;border-top:1px solid #334155;padding-top:9px;}}
  .foot a{{color:#7dd3fc;}}
</style></head><body>
  <h1>THREAD — 簡易化 NEST tree（人間が大まかに把握する用）</h1>
  <p class="sub">フル tree（234 node）を構造的に簡易化：P0-KILL プログラム軸 + live-spine を展開、legacy 185 node を1 node に畳む。</p>
  <div class="legend"><span class="b done">✅ 完了</span> <span class="b active">🔶 進行中</span> <span class="b pend">⏸ 未着手</span> <span class="b arch">📦 archived</span> <span class="star">★ いまここ</span></div>
  <div class="tree">{tree_html}</div>
  <div class="now"><b>今ここ：</b> off-center grasp = 解消(decision B 6/24)、R-S6.6 GPU held-rate <b>30/30 + IC-ROBUST 30/30</b> 確立(6/24, 機構精度floor)。いまは <b>grasp公差/deploy-robustness を特性化</b>（cable-state-space: Stage A位置・A'姿勢yaw≥12°・B曲げ形状）。cable pos/pose-random が deploy 要件化(SOMA L38 supersede)。→ multi-clip + RL-readiness へ。</div>
  <div class="foot">構造的に簡易化した <b>NEST tree</b>。フル詳細（234 node・依存・状態）= jsx tracker（正規ビュー）: <a href="http://localhost:8765/index.html">http://localhost:8765/index.html</a><br>本図は <code>nest-snapshot.json</code> から生成（re-runnable, SSOT 連動）。生成元: <code>gen_simplified_tree.py</code>.</div>
</body></html>"""

open(OUT, "w", encoding="utf-8").write(HTML)
print(f"wrote {OUT}")
print(f"simplified tree: {len(SPINE)} program/live top nodes + legacy({LEGACY_N}) collapsed; "
      f"full snapshot={len(N)} nodes")

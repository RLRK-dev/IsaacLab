import React, { useState, useEffect, useMemo, useCallback } from 'react';
import {
  ChevronRight, ChevronDown, Search, Upload, Save, Database,
  AlertTriangle, X, Trash2, Layers, FileJson, Activity, FolderOpen,
  CheckCircle2, MinusCircle, Archive, CircleDashed, RefreshCw
} from 'lucide-react';

// ---------- Sample data (THREAD-flavored) ----------
const SAMPLE_NEST = {
  nodes: [
    {
      id: 'T-ROOT',
      goal: '5クリップケーブル配線 95%成功 (vision-based)',
      means: '知覚→制御→評価の3層を統合し、視覚ベースで95%以上の成功率を達成',
      status: 'IN_PROGRESS',
      dependencies: [],
      parent: null,
      children: ['PERC-01', 'CTRL-01', 'SIM-01', 'EVAL-01', 'COUNCIL-01'],
      session_history: [
        { session_id: 's-2026-04-01', summary: '初期設計', ts: '2026-04-01' },
        { session_id: 's-2026-04-15', summary: 'L3 cascade確認', ts: '2026-04-15' }
      ]
    },
    {
      id: 'PERC-01',
      goal: '視覚パイプライン実装',
      means: 'キャリブレーション → セグメンテーション → 姿勢推定の3段',
      status: 'IN_PROGRESS', dependencies: [], parent: 'T-ROOT',
      children: ['PERC-01-A', 'PERC-01-B', 'PERC-01-C'],
      session_history: [{ session_id: 's-2026-04-05', summary: 'パイプライン分割' }]
    },
    {
      id: 'PERC-01-A',
      goal: 'カメラキャリブレーション',
      means: 'Charucoボード + OpenCV',
      status: 'COMPLETE', dependencies: [], parent: 'PERC-01', children: [],
      session_history: [{ session_id: 's-2026-04-06', summary: 'reprojection error < 0.3px' }]
    },
    {
      id: 'PERC-01-B',
      goal: 'セグメンテーションモデル',
      means: 'SAM2 fine-tune (cable + clip 2クラス)',
      status: 'COMPLETE', dependencies: [], parent: 'PERC-01', children: [],
      session_history: [{ session_id: 's-2026-04-09', summary: 'IoU 0.91 達成' }]
    },
    {
      id: 'PERC-01-C',
      goal: 'クリップ姿勢推定',
      means: 'PnP + RANSAC',
      status: 'IN_PROGRESS', dependencies: ['PERC-01-A', 'PERC-01-B'],
      parent: 'PERC-01', children: [],
      session_history: []
    },
    {
      id: 'CTRL-01',
      goal: '制御方策',
      means: 'SAC + ドメインランダマイゼーション + 報酬整形',
      status: 'IN_PROGRESS', dependencies: [], parent: 'T-ROOT',
      children: ['CTRL-01-A', 'CTRL-01-B', 'CTRL-01-C'],
      session_history: []
    },
    {
      id: 'CTRL-01-A',
      goal: 'SACベースライン',
      means: 'stable-baselines3 既定設定',
      status: 'COMPLETE', dependencies: [], parent: 'CTRL-01', children: [],
      session_history: [{ session_id: 's-2026-03-28', summary: 'sim内成功率68%' }]
    },
    {
      id: 'CTRL-01-B',
      goal: '報酬整形',
      means: '到達距離 + 把持成功 + 配線進捗の重み付け',
      status: 'IN_PROGRESS', dependencies: ['PERC-01-C'],
      parent: 'CTRL-01', children: [],
      session_history: []
    },
    {
      id: 'CTRL-01-C',
      goal: 'ドメインランダマイゼーション',
      means: '質量・摩擦・色・照明の randomization',
      status: 'IN_PROGRESS', dependencies: [], parent: 'CTRL-01', children: [],
      session_history: []
    },
    {
      id: 'SIM-01',
      goal: 'シミュレーション環境',
      means: 'Isaac Lab + ケーブル物理 + クリップメッシュ',
      status: 'COMPLETE', dependencies: [], parent: 'T-ROOT',
      children: ['SIM-01-A', 'SIM-01-B'],
      session_history: []
    },
    {
      id: 'SIM-01-A',
      goal: 'ケーブル物理',
      means: 'Position-based dynamics, セグメント数50',
      status: 'COMPLETE', dependencies: [], parent: 'SIM-01', children: [],
      session_history: []
    },
    {
      id: 'SIM-01-B',
      goal: 'クリップメッシュ',
      means: '実測スキャン → mesh簡略化',
      status: 'COMPLETE', dependencies: [], parent: 'SIM-01', children: [],
      session_history: []
    },
    {
      id: 'EVAL-01',
      goal: '評価フレームワーク',
      means: 'メトリクス + テストシナリオ',
      status: 'IN_PROGRESS', dependencies: [], parent: 'T-ROOT',
      children: ['EVAL-01-A', 'EVAL-01-B'],
      session_history: []
    },
    {
      id: 'EVAL-01-A',
      goal: 'メトリクス定義 (旧案)',
      means: '完了率のみ — 中間評価不可で不十分',
      status: 'DISCARDED', dependencies: [], parent: 'EVAL-01', children: [],
      session_history: [{ session_id: 's-2026-03-20', summary: '却下: 中間評価不可' }]
    },
    {
      id: 'EVAL-01-B',
      goal: 'テストシナリオ',
      means: '正常系 + 異常系 × 5パターン',
      status: 'IN_PROGRESS', dependencies: [], parent: 'EVAL-01', children: [],
      session_history: []
    },
    {
      id: 'COUNCIL-01',
      goal: '5体合議システム (C-α: 5 Generators)',
      means: 'Generator×5 + Scorer + Integrator',
      status: 'IN_PROGRESS', dependencies: [], parent: 'T-ROOT',
      children: ['COUNCIL-01-G', 'COUNCIL-01-S', 'COUNCIL-01-I'],
      session_history: [{ session_id: 's-2026-04-11', summary: 'C-α採択' }]
    },
    {
      id: 'COUNCIL-01-G',
      goal: 'Generatorプロンプト×5',
      means: 'Sonnet med/high, Opus med/high/max',
      status: 'IN_PROGRESS', dependencies: [], parent: 'COUNCIL-01', children: [],
      session_history: []
    },
    {
      id: 'COUNCIL-01-S',
      goal: 'Scorerプロンプト',
      means: '正確性・証拠強度・論理性の辞書順順位付け',
      status: 'IN_PROGRESS', dependencies: ['COUNCIL-01-G'],
      parent: 'COUNCIL-01', children: [],
      session_history: []
    },
    {
      id: 'COUNCIL-01-I',
      goal: 'Integratorプロンプト',
      means: '主役答えへの反論吟味 + 偽陰性救済機構',
      status: 'IN_PROGRESS', dependencies: ['COUNCIL-01-S'],
      parent: 'COUNCIL-01', children: [],
      session_history: []
    },
    {
      id: 'ARCH-OLD',
      goal: '旧アーキテクチャ (10体構成)',
      means: 'Generator×10 — C-α採択で凍結',
      status: 'ARCHIVED', dependencies: [], parent: null, children: [],
      session_history: [{ session_id: 's-2026-04-11', summary: 'C-α採択により凍結' }]
    }
  ]
};

// ---------- Style maps ----------
const STATE_INFO = {
  IN_PROGRESS: { label: 'IN_PROGRESS', short: 'IP',
    bg: 'bg-sky-900/40', text: 'text-sky-200', border: 'border-sky-700',
    dot: 'bg-sky-500', icon: Activity, accent: '#0369a1' },
  COMPLETE:    { label: 'COMPLETE',    short: 'OK',
    bg: 'bg-emerald-900/40', text: 'text-emerald-200', border: 'border-emerald-700',
    dot: 'bg-emerald-500', icon: CheckCircle2, accent: '#047857' },
  DISCARDED:   { label: 'DISCARDED',   short: 'XX',
    bg: 'bg-stone-700', text: 'text-stone-400', border: 'border-stone-600',
    dot: 'bg-stone-400', icon: MinusCircle, accent: '#78716c' },
  ARCHIVED:    { label: 'ARCHIVED',    short: 'AR',
    bg: 'bg-violet-900/40', text: 'text-violet-200', border: 'border-violet-700',
    dot: 'bg-violet-500', icon: Archive, accent: '#6d28d9' },
};

const ALL_STATES = ['IN_PROGRESS', 'COMPLETE', 'DISCARDED', 'ARCHIVED'];

// ---------- Component ----------
export default function NESTTracker() {
  const [nodes, setNodes] = useState(SAMPLE_NEST.nodes);
  const [expanded, setExpanded] = useState(() => new Set(SAMPLE_NEST.nodes.map(n => n.id)));
  const [selectedId, setSelectedId] = useState(null);
  const [search, setSearch] = useState('');
  const [stateFilter, setStateFilter] = useState(() => new Set(ALL_STATES));
  const [showImport, setShowImport] = useState(false);
  const [pasteText, setPasteText] = useState('');
  const [parseError, setParseError] = useState(null);
  const [snapshotExists, setSnapshotExists] = useState(false);
  const [saveStatus, setSaveStatus] = useState(null); // 'saved' | 'cleared' | null
  const [loadStatus, setLoadStatus] = useState(null); // 'loaded' | 'error' | null
  const [snapshotMeta, setSnapshotMeta] = useState(null); // { source, count, fetchedAt }

  // Inject Google Fonts
  useEffect(() => {
    const id = 'nest-fonts-link';
    if (document.getElementById(id)) return;
    const link = document.createElement('link');
    link.id = id;
    link.rel = 'stylesheet';
    link.href = 'https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600;9..144,700&family=Public+Sans:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap';
    document.head.appendChild(link);
  }, []);

  // Check saved snapshot
  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const r = await window.storage.get('nest-snapshot');
        if (alive) setSnapshotExists(!!(r && r.value));
      } catch {
        if (alive) setSnapshotExists(false);
      }
    })();
    return () => { alive = false; };
  }, []);

  // Fetch nest-snapshot.json on mount (load boundary, adapter-friendly)
  // Runs once at startup; user can re-fetch via refresh button.
  const fetchSnapshot = useCallback(async (silent = false) => {
    try {
      const url = `./nest-snapshot.json?_=${Date.now()}`;
      const r = await fetch(url);
      if (!r.ok) {
        if (!silent) setLoadStatus('error');
        return false;
      }
      const obj = await r.json();
      const arr = Array.isArray(obj) ? obj : (obj && Array.isArray(obj.nodes) ? obj.nodes : null);
      if (!arr || arr.length === 0) {
        if (!silent) setLoadStatus('error');
        return false;
      }
      // Validate
      for (let i = 0; i < arr.length; i++) {
        const n = arr[i];
        if (!n || !n.id || !ALL_STATES.includes(n.status)) {
          if (!silent) setLoadStatus('error');
          return false;
        }
      }
      setNodes(arr);
      setExpanded(new Set(arr.map(n => n.id)));
      setSelectedId(null);
      setSnapshotMeta({ source: 'nest-snapshot.json', count: arr.length, fetchedAt: new Date() });
      setLoadStatus('loaded');
      return true;
    } catch {
      if (!silent) setLoadStatus('error');
      return false;
    }
  }, []);

  useEffect(() => {
    let alive = true;
    (async () => {
      const ok = await fetchSnapshot(true); // silent on initial load
      if (alive && ok) setLoadStatus('loaded');
    })();
    return () => { alive = false; };
  }, [fetchSnapshot]);

  // Auto-clear load status
  useEffect(() => {
    if (!loadStatus) return;
    const t = setTimeout(() => setLoadStatus(null), 2400);
    return () => clearTimeout(t);
  }, [loadStatus]);

  // Auto-clear save status
  useEffect(() => {
    if (!saveStatus) return;
    const t = setTimeout(() => setSaveStatus(null), 1800);
    return () => clearTimeout(t);
  }, [saveStatus]);

  // Maps
  const nodeMap = useMemo(() => {
    const m = new Map();
    nodes.forEach(n => m.set(n.id, n));
    return m;
  }, [nodes]);

  const rootNodes = useMemo(
    () => nodes.filter(n => !n.parent || !nodeMap.has(n.parent)),
    [nodes, nodeMap]
  );

  // Cascade progress: count of COMPLETE leaves / count of active leaves (excl. DISCARDED, ARCHIVED)
  const progressMap = useMemo(() => {
    const map = new Map();
    const visiting = new Set();
    function compute(id) {
      if (map.has(id)) return map.get(id);
      if (visiting.has(id)) return { complete: 0, total: 0 }; // cycle guard
      visiting.add(id);
      const n = nodeMap.get(id);
      if (!n) { visiting.delete(id); return { complete: 0, total: 0 }; }
      if (n.status === 'DISCARDED' || n.status === 'ARCHIVED') {
        const r = { complete: 0, total: 0 };
        map.set(id, r); visiting.delete(id); return r;
      }
      const kids = (n.children || []).filter(c => nodeMap.has(c));
      if (kids.length === 0) {
        const r = { complete: n.status === 'COMPLETE' ? 1 : 0, total: 1 };
        map.set(id, r); visiting.delete(id); return r;
      }
      let c = 0, t = 0;
      kids.forEach(cid => {
        const cr = compute(cid);
        c += cr.complete; t += cr.total;
      });
      const r = { complete: c, total: t };
      map.set(id, r); visiting.delete(id); return r;
    }
    nodes.forEach(n => compute(n.id));
    return map;
  }, [nodes, nodeMap]);

  // Blocker: IN_PROGRESS with at least one non-COMPLETE dependency
  const blockedIds = useMemo(() => {
    const s = new Set();
    nodes.forEach(n => {
      if (n.status !== 'IN_PROGRESS') return;
      const deps = n.dependencies || [];
      if (deps.length === 0) return;
      const unmet = deps.some(d => {
        const dn = nodeMap.get(d);
        return !dn || dn.status !== 'COMPLETE';
      });
      if (unmet) s.add(n.id);
    });
    return s;
  }, [nodes, nodeMap]);

  // Stats
  const stats = useMemo(() => {
    const s = { IN_PROGRESS: 0, COMPLETE: 0, DISCARDED: 0, ARCHIVED: 0, total: 0, blocked: blockedIds.size };
    nodes.forEach(n => { if (s[n.status] !== undefined) s[n.status] += 1; s.total += 1; });
    return s;
  }, [nodes, blockedIds]);

  const overallProgress = useMemo(() => {
    const active = stats.total - stats.DISCARDED - stats.ARCHIVED;
    if (active <= 0) return 0;
    return Math.round((stats.COMPLETE / active) * 100);
  }, [stats]);

  // Filter matching
  const matchesFilter = useCallback((n) => {
    if (!stateFilter.has(n.status)) return false;
    const q = search.trim().toLowerCase();
    if (!q) return true;
    return (
      (n.id || '').toLowerCase().includes(q) ||
      (n.goal || '').toLowerCase().includes(q) ||
      (n.means || '').toLowerCase().includes(q)
    );
  }, [stateFilter, search]);

  // Visible set: a node is visible if it matches OR any descendant matches
  const visibleSet = useMemo(() => {
    const s = new Set();
    function walk(id) {
      const n = nodeMap.get(id);
      if (!n) return false;
      let any = matchesFilter(n);
      (n.children || []).forEach(cid => {
        if (walk(cid)) any = true;
      });
      if (any) s.add(id);
      return any;
    }
    rootNodes.forEach(r => walk(r.id));
    return s;
  }, [nodeMap, rootNodes, matchesFilter]);

  // Handlers
  const toggleExpand = (id) => {
    setExpanded(prev => {
      const ns = new Set(prev);
      if (ns.has(id)) ns.delete(id); else ns.add(id);
      return ns;
    });
  };
  const expandAll = () => setExpanded(new Set(nodes.map(n => n.id)));
  const collapseAll = () => setExpanded(new Set());
  const toggleStateFilter = (st) => {
    setStateFilter(prev => {
      const ns = new Set(prev);
      if (ns.has(st)) ns.delete(st); else ns.add(st);
      return ns;
    });
  };
  const resetFilter = () => setStateFilter(new Set(ALL_STATES));

  const importNodes = (text) => {
    setParseError(null);
    try {
      const obj = JSON.parse(text);
      const arr = Array.isArray(obj) ? obj : (obj && Array.isArray(obj.nodes) ? obj.nodes : null);
      if (!arr) throw new Error('JSON は配列、または { "nodes": [...] } 形式で渡してください');
      if (arr.length === 0) throw new Error('ノードが0件です');
      arr.forEach((n, i) => {
        if (!n || typeof n !== 'object') throw new Error(`#${i}: ノードがオブジェクトではありません`);
        if (!n.id) throw new Error(`#${i}: id が必須です`);
        if (!ALL_STATES.includes(n.status)) {
          throw new Error(`#${i} (id=${n.id}): status は ${ALL_STATES.join('|')} のいずれか`);
        }
      });
      setNodes(arr);
      setExpanded(new Set(arr.map(n => n.id)));
      setSelectedId(null);
      setShowImport(false);
      setPasteText('');
    } catch (e) {
      setParseError(e.message || String(e));
    }
  };

  const handleFile = (e) => {
    const f = e.target.files && e.target.files[0];
    if (!f) return;
    const r = new FileReader();
    r.onload = () => importNodes(String(r.result || ''));
    r.onerror = () => setParseError('ファイル読み込みに失敗しました');
    r.readAsText(f);
    e.target.value = '';
  };

  const handleSave = async () => {
    try {
      await window.storage.set('nest-snapshot', JSON.stringify({ nodes }));
      setSnapshotExists(true);
      setSaveStatus('saved');
    } catch {
      setSaveStatus('error');
    }
  };
  const handleLoadSaved = async () => {
    try {
      const r = await window.storage.get('nest-snapshot');
      if (r && r.value) {
        const obj = JSON.parse(r.value);
        if (Array.isArray(obj.nodes)) {
          setNodes(obj.nodes);
          setExpanded(new Set(obj.nodes.map(n => n.id)));
          setSelectedId(null);
        }
      }
    } catch {}
  };
  const handleClearSaved = async () => {
    try {
      await window.storage.delete('nest-snapshot');
      setSnapshotExists(false);
      setSaveStatus('cleared');
    } catch {}
  };
  const handleLoadSample = () => {
    setNodes(SAMPLE_NEST.nodes);
    setExpanded(new Set(SAMPLE_NEST.nodes.map(n => n.id)));
    setSelectedId(null);
  };

  const selected = selectedId ? nodeMap.get(selectedId) : null;

  // ---------- Render helpers ----------
  const StatePill = ({ status, size = 'md' }) => {
    const info = STATE_INFO[status];
    if (!info) return null;
    const sz = size === 'sm'
      ? 'text-[10px] px-1.5 py-0.5'
      : 'text-[11px] px-2 py-0.5';
    return (
      <span
        className={`inline-flex items-center gap-1 rounded-sm border ${info.bg} ${info.text} ${info.border} ${sz} font-medium uppercase tracking-wide`}
        style={{ fontFamily: '"JetBrains Mono", ui-monospace, monospace' }}
      >
        <span className={`w-1.5 h-1.5 rounded-full ${info.dot}`} />
        {info.short}
      </span>
    );
  };

  const ProgressBar = ({ complete, total, accent = '#0c4a6e' }) => {
    const pct = total > 0 ? Math.round((complete / total) * 100) : 0;
    return (
      <div className="flex items-center gap-2 min-w-0">
        <div className="relative flex-1 h-1.5 bg-stone-700 rounded-sm overflow-hidden min-w-[40px]">
          <div
            className="absolute left-0 top-0 h-full transition-all"
            style={{ width: `${pct}%`, backgroundColor: accent }}
          />
        </div>
        <span
          className="text-[10px] text-stone-300 tabular-nums"
          style={{ fontFamily: '"JetBrains Mono", monospace' }}
        >
          {complete}/{total}
        </span>
      </div>
    );
  };

  // Recursive node renderer
  const renderNode = (node, depth = 0, isLast = false, ancestorLines = []) => {
    if (!visibleSet.has(node.id)) return null;
    const kids = (node.children || []).filter(c => nodeMap.has(c)).map(c => nodeMap.get(c));
    const visibleKids = kids.filter(k => visibleSet.has(k.id));
    const hasKids = visibleKids.length > 0;
    const isOpen = expanded.has(node.id);
    const info = STATE_INFO[node.status] || STATE_INFO.IN_PROGRESS;
    const isBlocked = blockedIds.has(node.id);
    const isSelected = selectedId === node.id;
    const prog = progressMap.get(node.id) || { complete: 0, total: 0 };
    const showProgress = hasKids && (node.status === 'IN_PROGRESS' || node.status === 'COMPLETE');
    const muted = node.status === 'DISCARDED' || node.status === 'ARCHIVED';
    const struck = node.status === 'DISCARDED';

    return (
      <React.Fragment key={node.id}>
        <div
          onClick={() => setSelectedId(node.id)}
          className={`group relative flex items-stretch cursor-pointer transition-colors ${
            isSelected ? 'bg-amber-900/30' : 'hover:bg-stone-700/70'
          }`}
        >
          {/* Indent guide rails */}
          {ancestorLines.map((draw, i) => (
            <div key={i} className="w-6 shrink-0 relative">
              {draw && (
                <div className="absolute top-0 bottom-0 left-3 w-px bg-stone-700" />
              )}
            </div>
          ))}
          {depth > 0 && (
            <div className="w-6 shrink-0 relative">
              <div className={`absolute top-0 left-3 w-px bg-stone-700 ${isLast ? 'h-1/2' : 'h-full'}`} />
              <div className="absolute top-1/2 left-3 w-3 h-px bg-stone-700" />
            </div>
          )}

          {/* Caret */}
          <button
            type="button"
            onClick={(e) => { e.stopPropagation(); if (hasKids) toggleExpand(node.id); }}
            className={`shrink-0 w-5 flex items-center justify-center mt-2 ${
              hasKids ? 'text-stone-400 hover:text-stone-100' : 'text-transparent'
            }`}
            aria-label={isOpen ? 'collapse' : 'expand'}
          >
            {hasKids ? (
              isOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />
            ) : (
              <CircleDashed size={10} />
            )}
          </button>

          {/* Selection accent */}
          {isSelected && (
            <div className="absolute left-0 top-0 bottom-0 w-0.5 bg-amber-600" />
          )}

          {/* Body */}
          <div className="flex-1 min-w-0 py-1.5 pr-3 flex items-start gap-2">
            <div className="pt-0.5 flex items-center gap-1.5">
              <StatePill status={node.status} size="sm" />
              {isBlocked && (
                <span title="未充足の依存あり" className="text-amber-700">
                  <AlertTriangle size={12} />
                </span>
              )}
            </div>

            <div className="flex-1 min-w-0">
              <div className="flex items-baseline gap-2 min-w-0">
                <span
                  className={`text-[11px] shrink-0 ${muted ? 'text-stone-400' : 'text-stone-400'}`}
                  style={{ fontFamily: '"JetBrains Mono", monospace' }}
                >
                  {node.id}
                </span>
                <span
                  className={`text-[13px] truncate ${
                    muted ? 'text-stone-400' : 'text-stone-100'
                  } ${struck ? 'line-through' : ''}`}
                  style={{ fontFamily: '"Public Sans", system-ui, sans-serif' }}
                >
                  {node.goal}
                </span>
              </div>
              {showProgress && prog.total > 0 && (
                <div className="mt-1 max-w-[260px]">
                  <ProgressBar complete={prog.complete} total={prog.total} accent={info.accent} />
                </div>
              )}
            </div>
          </div>
        </div>

        {hasKids && isOpen && visibleKids.map((k, i) => {
          const childIsLast = i === visibleKids.length - 1;
          const newAncestors = depth === 0 ? ancestorLines : [...ancestorLines, !isLast];
          return renderNode(k, depth + 1, childIsLast, newAncestors);
        })}
      </React.Fragment>
    );
  };

  // ---------- Layout ----------
  return (
    <div
      className="min-h-screen w-full bg-stone-900 text-stone-100"
      style={{ fontFamily: '"Public Sans", system-ui, sans-serif' }}
    >
      {/* Header */}
      <header className="border-b border-stone-700 bg-stone-800/70 backdrop-blur sticky top-0 z-20">
        <div className="px-5 py-4 flex flex-wrap items-end justify-between gap-3">
          <div>
            <div className="flex items-baseline gap-3">
              <h1
                className="text-2xl tracking-tight text-stone-100"
                style={{ fontFamily: '"Fraunces", Georgia, serif', fontWeight: 600, fontVariationSettings: '"opsz" 144' }}
              >
                NEST <span className="text-stone-400">Status</span>
              </h1>
              <span
                className="text-[10px] uppercase tracking-[0.18em] text-stone-400"
                style={{ fontFamily: '"JetBrains Mono", monospace' }}
              >
                Node-bound Execution Session Tree
              </span>
            </div>
            <p className="text-[12px] text-stone-400 mt-1">
              全タスクの進捗を一望 — 折り畳み式の木 + 状態別配色 + 依存ブロッカー
            </p>
          </div>

          {/* Stats panel */}
          <div className="flex items-center gap-3 flex-wrap">
            {ALL_STATES.map(st => {
              const info = STATE_INFO[st];
              return (
                <div
                  key={st}
                  className={`flex items-center gap-2 px-2.5 py-1 rounded-sm border ${info.border} ${info.bg}`}
                >
                  <span className={`w-1.5 h-1.5 rounded-full ${info.dot}`} />
                  <span
                    className={`text-[10px] uppercase tracking-wide ${info.text}`}
                    style={{ fontFamily: '"JetBrains Mono", monospace' }}
                  >
                    {info.short}
                  </span>
                  <span
                    className={`text-[13px] font-semibold ${info.text} tabular-nums`}
                    style={{ fontFamily: '"JetBrains Mono", monospace' }}
                  >
                    {stats[st]}
                  </span>
                </div>
              );
            })}
            {stats.blocked > 0 && (
              <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-sm border border-amber-700 bg-amber-900/30 text-amber-200">
                <AlertTriangle size={12} />
                <span className="text-[11px]" style={{ fontFamily: '"JetBrains Mono", monospace' }}>
                  blocked {stats.blocked}
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Overall progress */}
        <div className="px-5 pb-3 flex items-center gap-3">
          <span
            className="text-[11px] uppercase tracking-[0.18em] text-stone-400 shrink-0"
            style={{ fontFamily: '"JetBrains Mono", monospace' }}
          >
            Overall
          </span>
          <div className="flex-1 h-2 bg-stone-700 rounded-sm overflow-hidden">
            <div
              className="h-full bg-emerald-600 transition-all"
              style={{ width: `${overallProgress}%` }}
            />
          </div>
          <span
            className="text-[12px] text-stone-200 tabular-nums shrink-0"
            style={{ fontFamily: '"JetBrains Mono", monospace' }}
          >
            {overallProgress}% · {stats.COMPLETE}/{Math.max(0, stats.total - stats.DISCARDED - stats.ARCHIVED)} active
          </span>
        </div>

        {/* Toolbar */}
        <div className="px-5 pb-3 flex flex-wrap items-center gap-2">
          <div className="relative flex-1 min-w-[200px] max-w-md">
            <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-stone-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="id / goal / means を検索…"
              className="w-full pl-8 pr-8 py-1.5 text-[13px] bg-stone-800 border border-stone-700 rounded-sm focus:outline-none focus:border-stone-600"
            />
            {search && (
              <button
                onClick={() => setSearch('')}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-stone-400 hover:text-stone-200"
                aria-label="clear"
              >
                <X size={14} />
              </button>
            )}
          </div>

          <div className="flex items-center gap-1">
            {ALL_STATES.map(st => {
              const info = STATE_INFO[st];
              const active = stateFilter.has(st);
              return (
                <button
                  key={st}
                  type="button"
                  onClick={() => toggleStateFilter(st)}
                  className={`px-2 py-1 text-[10px] uppercase tracking-wide rounded-sm border transition-colors ${
                    active
                      ? `${info.bg} ${info.text} ${info.border}`
                      : 'bg-stone-800 text-stone-400 border-stone-700 hover:text-stone-200'
                  }`}
                  style={{ fontFamily: '"JetBrains Mono", monospace' }}
                >
                  {info.short}
                </button>
              );
            })}
            {stateFilter.size < ALL_STATES.length && (
              <button
                onClick={resetFilter}
                className="ml-1 text-[10px] text-stone-400 hover:text-stone-100 underline underline-offset-2"
              >
                reset
              </button>
            )}
          </div>

          <div className="flex items-center gap-1 ml-auto">
            <button
              onClick={expandAll}
              className="text-[11px] text-stone-300 hover:text-stone-100 px-2 py-1 border border-stone-700 rounded-sm bg-stone-800"
            >
              展開
            </button>
            <button
              onClick={collapseAll}
              className="text-[11px] text-stone-300 hover:text-stone-100 px-2 py-1 border border-stone-700 rounded-sm bg-stone-800"
            >
              畳む
            </button>
            <span className="w-px h-4 bg-stone-700 mx-1" />
            <button
              onClick={() => fetchSnapshot(false)}
              className="flex items-center gap-1 text-[11px] text-stone-200 hover:text-stone-100 px-2 py-1 border border-stone-600 rounded-sm bg-stone-800"
              title="nest-snapshot.json を再取得"
            >
              <RefreshCw size={12} /> 再取得
            </button>
            <button
              onClick={() => setShowImport(s => !s)}
              className="flex items-center gap-1 text-[11px] text-stone-200 hover:text-stone-100 px-2 py-1 border border-stone-600 rounded-sm bg-stone-800"
            >
              <Upload size={12} /> 取込
            </button>
            <button
              onClick={handleSave}
              className="flex items-center gap-1 text-[11px] text-stone-200 hover:text-stone-100 px-2 py-1 border border-stone-600 rounded-sm bg-stone-800"
              title="ブラウザ内に保存"
            >
              <Save size={12} /> 保存
            </button>
            {snapshotExists && (
              <button
                onClick={handleLoadSaved}
                className="flex items-center gap-1 text-[11px] text-emerald-300 hover:text-emerald-100 px-2 py-1 border border-emerald-700 rounded-sm bg-emerald-900/30"
              >
                <Database size={12} /> 復元
              </button>
            )}
          </div>
        </div>

        {saveStatus && (
          <div className="px-5 pb-2 text-[11px] text-emerald-700">
            {saveStatus === 'saved' && '✓ 保存しました'}
            {saveStatus === 'cleared' && '✓ 保存データを削除しました'}
            {saveStatus === 'error' && '⚠ 保存に失敗しました'}
          </div>
        )}
        {loadStatus && (
          <div className={`px-5 pb-2 text-[11px] ${loadStatus === 'loaded' ? 'text-sky-700' : 'text-amber-700'}`}>
            {loadStatus === 'loaded' && snapshotMeta && (
              <span>✓ {snapshotMeta.source} を取得 ({snapshotMeta.count} nodes, {snapshotMeta.fetchedAt.toLocaleTimeString()})</span>
            )}
            {loadStatus === 'error' && '⚠ nest-snapshot.json の取得に失敗 — Sample データを表示中'}
          </div>
        )}
      </header>

      {/* Import drawer */}
      {showImport && (
        <div className="border-b border-stone-700 bg-stone-800">
          <div className="px-5 py-4">
            <div className="flex items-start justify-between gap-4 mb-2">
              <div>
                <div
                  className="text-[12px] uppercase tracking-[0.18em] text-stone-400 mb-1"
                  style={{ fontFamily: '"JetBrains Mono", monospace' }}
                >
                  Import NEST snapshot
                </div>
                <p className="text-[12px] text-stone-300">
                  JSON のみ対応 (YAML は事前にJSONへ変換)。配列か <code className="text-stone-100">{'{ "nodes": [...] }'}</code> を受理。
                </p>
              </div>
              <button onClick={() => setShowImport(false)} className="text-stone-400 hover:text-stone-200">
                <X size={16} />
              </button>
            </div>

            <textarea
              value={pasteText}
              onChange={(e) => setPasteText(e.target.value)}
              placeholder='{"nodes":[{"id":"T-ROOT","goal":"...","means":"...","status":"IN_PROGRESS","dependencies":[],"parent":null,"children":[],"session_history":[]}]}'
              className="w-full h-32 p-2 text-[12px] bg-stone-900 border border-stone-700 rounded-sm focus:outline-none focus:border-stone-600 resize-y"
              style={{ fontFamily: '"JetBrains Mono", monospace' }}
            />
            {parseError && (
              <div className="mt-2 text-[12px] text-red-300 bg-red-900/30 border border-red-800 rounded-sm px-2 py-1.5">
                <span className="font-semibold">parse error:</span> {parseError}
              </div>
            )}

            <div className="mt-2 flex flex-wrap items-center gap-2">
              <button
                onClick={() => importNodes(pasteText)}
                disabled={!pasteText.trim()}
                className="text-[12px] px-3 py-1.5 bg-stone-700 text-stone-100 rounded-sm disabled:bg-stone-800"
              >
                Load from text
              </button>
              <label className="text-[12px] px-3 py-1.5 border border-stone-600 rounded-sm bg-stone-800 cursor-pointer hover:bg-stone-700 flex items-center gap-1.5">
                <FileJson size={12} />
                File…
                <input type="file" accept=".json,application/json,.txt" className="hidden" onChange={handleFile} />
              </label>
              <button
                onClick={handleLoadSample}
                className="text-[12px] px-3 py-1.5 border border-stone-600 rounded-sm bg-stone-800 hover:bg-stone-700 flex items-center gap-1.5"
              >
                <Layers size={12} /> Sample に戻す
              </button>
              {snapshotExists && (
                <button
                  onClick={handleClearSaved}
                  className="text-[12px] px-3 py-1.5 border border-red-700 text-red-300 rounded-sm bg-stone-800 hover:bg-red-900/40 flex items-center gap-1.5 ml-auto"
                >
                  <Trash2 size={12} /> 保存データ削除
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Main two-pane */}
      <div className="flex flex-col md:flex-row min-h-[calc(100vh-160px)]">
        {/* Tree pane */}
        <main className="flex-1 min-w-0 border-r border-stone-700">
          <div className="px-3 py-2 border-b border-stone-700 bg-stone-800/40 flex items-center gap-2">
            <FolderOpen size={12} className="text-stone-400" />
            <span
              className="text-[11px] uppercase tracking-[0.18em] text-stone-400"
              style={{ fontFamily: '"JetBrains Mono", monospace' }}
            >
              Tree · {visibleSet.size} / {nodes.length} ノード
            </span>
          </div>
          <div className="py-1">
            {rootNodes.length === 0 && (
              <div className="px-5 py-8 text-stone-400 text-[13px]">ノードがありません。取込から JSON を読み込んでください。</div>
            )}
            {rootNodes
              .filter(r => visibleSet.has(r.id))
              .map((r, i, arr) => renderNode(r, 0, i === arr.length - 1, []))}
          </div>
        </main>

        {/* Detail pane */}
        <aside className="w-full md:w-[380px] shrink-0 bg-stone-800">
          {!selected ? (
            <div className="p-6 text-stone-400 text-[13px] flex flex-col items-center text-center min-h-[200px] justify-center">
              <Layers size={28} className="text-stone-300 mb-2" />
              <p>ノードを選択すると詳細を表示します</p>
              <p className="text-[11px] mt-1 text-stone-400">行をクリック、▶ で展開</p>
            </div>
          ) : (
            <DetailPanel
              node={selected}
              nodeMap={nodeMap}
              progress={progressMap.get(selected.id)}
              isBlocked={blockedIds.has(selected.id)}
              onSelect={setSelectedId}
            />
          )}
        </aside>
      </div>

      {/* Footer */}
      <footer className="border-t border-stone-700 px-5 py-2 text-[10px] text-stone-400 flex items-center justify-between">
        <span style={{ fontFamily: '"JetBrains Mono", monospace' }}>
          NEST progress · cascade-aware · {nodes.length} nodes
        </span>
        <span style={{ fontFamily: '"JetBrains Mono", monospace' }}>
          1 node ↔ 1 CC session · parent COMPLETE ⇔ 全子完了
        </span>
      </footer>
    </div>
  );
}

// ---------- Detail panel ----------
function DetailPanel({ node, nodeMap, progress, isBlocked, onSelect }) {
  const info = STATE_INFO[node.status] || STATE_INFO.IN_PROGRESS;
  const Icon = info.icon;
  const deps = (node.dependencies || []).map(id => nodeMap.get(id) || { id, missing: true });
  const kids = (node.children || []).map(id => nodeMap.get(id) || { id, missing: true });
  const parent = node.parent ? nodeMap.get(node.parent) : null;

  const Section = ({ label, children }) => (
    <div className="mb-4">
      <div
        className="text-[10px] uppercase tracking-[0.18em] text-stone-400 mb-1.5"
        style={{ fontFamily: '"JetBrains Mono", monospace' }}
      >
        {label}
      </div>
      {children}
    </div>
  );

  const NodeChip = ({ n, onClick }) => {
    if (n.missing) {
      return (
        <span
          className="inline-flex items-center gap-1 px-1.5 py-0.5 text-[11px] border border-red-700 bg-red-900/30 text-red-300 rounded-sm"
          style={{ fontFamily: '"JetBrains Mono", monospace' }}
        >
          {n.id} <span className="text-[9px]">missing</span>
        </span>
      );
    }
    const inf = STATE_INFO[n.status] || STATE_INFO.IN_PROGRESS;
    return (
      <button
        type="button"
        onClick={onClick}
        className={`inline-flex items-center gap-1.5 px-1.5 py-0.5 text-[11px] border ${inf.border} ${inf.bg} ${inf.text} rounded-sm hover:brightness-95`}
        style={{ fontFamily: '"JetBrains Mono", monospace' }}
        title={n.goal}
      >
        <span className={`w-1 h-1 rounded-full ${inf.dot}`} />
        {n.id}
      </button>
    );
  };

  return (
    <div className="p-5 max-h-[calc(100vh-160px)] overflow-y-auto">
      <div className="flex items-start gap-3 mb-4 pb-4 border-b border-stone-700">
        <div
          className={`mt-1 w-9 h-9 rounded-sm flex items-center justify-center ${info.bg} ${info.border} border`}
          style={{ color: info.accent }}
        >
          <Icon size={18} />
        </div>
        <div className="flex-1 min-w-0">
          <div
            className="text-[11px] text-stone-400 mb-0.5"
            style={{ fontFamily: '"JetBrains Mono", monospace' }}
          >
            {node.id}
          </div>
          <h2
            className="text-[16px] leading-snug text-stone-100"
            style={{ fontFamily: '"Fraunces", Georgia, serif', fontWeight: 500 }}
          >
            {node.goal}
          </h2>
          <div className="mt-2 flex items-center gap-2 flex-wrap">
            <span
              className={`inline-flex items-center gap-1 rounded-sm border ${info.bg} ${info.text} ${info.border} text-[11px] px-2 py-0.5 font-medium uppercase tracking-wide`}
              style={{ fontFamily: '"JetBrains Mono", monospace' }}
            >
              <span className={`w-1.5 h-1.5 rounded-full ${info.dot}`} />
              {info.label}
            </span>
            {isBlocked && (
              <span className="inline-flex items-center gap-1 px-1.5 py-0.5 text-[11px] border border-amber-700 bg-amber-900/30 text-amber-200 rounded-sm">
                <AlertTriangle size={11} /> blocked
              </span>
            )}
          </div>
        </div>
      </div>

      <Section label="Means">
        <p className="text-[13px] text-stone-100 leading-relaxed">
          {node.means || <span className="text-stone-400">(未記入)</span>}
        </p>
      </Section>

      {progress && progress.total > 0 && (
        <Section label="Progress (cascade)">
          <div className="flex items-center gap-3">
            <div className="flex-1 h-2 bg-stone-700 rounded-sm overflow-hidden">
              <div
                className="h-full transition-all"
                style={{
                  width: `${Math.round((progress.complete / progress.total) * 100)}%`,
                  backgroundColor: info.accent
                }}
              />
            </div>
            <span
              className="text-[12px] text-stone-200 tabular-nums"
              style={{ fontFamily: '"JetBrains Mono", monospace' }}
            >
              {progress.complete}/{progress.total} · {Math.round((progress.complete / progress.total) * 100)}%
            </span>
          </div>
        </Section>
      )}

      <Section label="Dependencies">
        {deps.length === 0 ? (
          <span className="text-[12px] text-stone-400">なし</span>
        ) : (
          <div className="flex flex-wrap gap-1.5">
            {deps.map(d => (
              <NodeChip key={d.id} n={d} onClick={() => !d.missing && onSelect(d.id)} />
            ))}
          </div>
        )}
      </Section>

      <Section label="Parent">
        {parent ? (
          <NodeChip n={parent} onClick={() => onSelect(parent.id)} />
        ) : (
          <span className="text-[12px] text-stone-400">root</span>
        )}
      </Section>

      <Section label={`Children (${kids.length})`}>
        {kids.length === 0 ? (
          <span className="text-[12px] text-stone-400">leaf</span>
        ) : (
          <div className="flex flex-wrap gap-1.5">
            {kids.map(c => (
              <NodeChip key={c.id} n={c} onClick={() => !c.missing && onSelect(c.id)} />
            ))}
          </div>
        )}
      </Section>

      <Section label={`Session history (${(node.session_history || []).length})`}>
        {(node.session_history || []).length === 0 ? (
          <span className="text-[12px] text-stone-400">なし</span>
        ) : (
          <ul className="space-y-1.5">
            {(node.session_history || []).map((s, i) => (
              <li key={i} className="text-[12px] text-stone-200 border-l-2 border-stone-700 pl-2">
                <span
                  className="text-stone-400 mr-2"
                  style={{ fontFamily: '"JetBrains Mono", monospace' }}
                >
                  {s.session_id || `#${i + 1}`}
                </span>
                {s.summary || <span className="text-stone-400">(no summary)</span>}
                {s.ts && <span className="text-stone-400 ml-2">· {s.ts}</span>}
              </li>
            ))}
          </ul>
        )}
      </Section>
    </div>
  );
}

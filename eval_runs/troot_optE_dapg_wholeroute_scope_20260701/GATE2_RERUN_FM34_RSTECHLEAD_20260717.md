# gate② 再走 — swept FM3/FM4 tighten の /reward-design 4 artifacts (RS-TECH-LEAD %12)

**Written**: 2026-07-17 00:31 JST (date-THEN-write)。**Owner chain leg 1/3** (`I0A_SCOPE_MANIFEST_RSTECHLEAD_20260716.md:45`: /reward-design 再走 → p5 再 verify → /pre-check、著者未特定でも進行)。
**対象**: `c60d311f96` で無検証着地し HEAD で live な FM4 (`_seat_identity_segments` + `_seat_crossing(segment_indices=)`) / FM3 (`_c1_escape_after_seat`) — banked 設計 = gate-2 ruling **§13.1/§13.2 (両方 TIGHTEN)** + §13.4 (C2 連結) + §18 (境界≠同一性)。
**計算基盤**: `gate2_rerun_fm34_probe.py` → `gate2_rerun_fm34_probe_result.json` (canonical golden `w0e_81rerun_snapdown_0537/cell_x0_y0/route_demo_raw.npz`、7707 frames、純 numpy・live class methods 直呼び) + 著者残置の unit test `test_route_reward_identity_guards.py` (REJECT 側、ALL PASS 実測、⚠著者未特定・worktree 発見・本 gate で検証の上 bank)。
**§S**: 本 doc は owner chain の一部 — chain 完了 (p5 verify + /pre-check PASS) まで HEAD reward 意味論は unratified のまま。

## [REACHABILITY TABLE] (sparse 構造 — DQ1 で dense shaping 禁止ゆえ「勾配」列は canonical route 上の event 到達性+margin で判定)

| Component | Formula (HEAD) | Gating condition | Reachable? (実測) | 実測値 @ canonical | Dead zone? |
|---|---|---|---|---|---|
| G3 latch (+5, fire-once) | seated(C1) = dx_interp≤3.5mm ∧ 0.821<z<0.836、crossing は **{pin−1, pin} window 限定** (FM4) | C1 pin 発火 (`_pin_seat_seg` 供給) | **YES** — pin onset f2544 の同 frame で seated=True、以降 **517/517 frames seated (100%)** | tail dx = 0.87-0.98mm (bar の 28%)、z=0.8286 ∈ 帯中央 | **NO** — window は実 route の交差を 0 frame も棄却しない (新旧 divergence = 0) |
| G5 latch (+5) | seated(C2)、crossing は **C1 pin node から Y-monotone 連結 span 限定** (FM4/§13.4) | C2 到達 (route 後半) | **YES** — tail 30 sample 全て seated=True | dx = 0.18-0.22mm、z = 0.8299 | **NO** |
| c1_retained (G6 conjunct) | 同 C1 interp 述語 (解放後) | G6 判定時 | **YES** — 終端 frames seated 継続 | 上記 C1 tail と同値 | NO |
| c2_honest (G6 conjunct) | 同 C2 interp 述語 | 同上 | **YES** — 終端 seated | 上記 C2 tail と同値 | NO |
| FM3 drop (−10 + terminate) | post-G3 で crossing 消失 or \|x_dev\|>60mm → dropped (fail-closed) | **G3 latched で初めて armed** (phase-gate) | 罰側の到達性: stray/escape fixture で発火 (unit test)。**正 route での誤発火 = 0/517** | max \|x_dev\| = **1.03mm** vs bar 60mm = **58× margin** | **NO false-fire zone** — pre-G3 は定義上 inert (`c1_latched=False → False`) |
| identity 供給 fail-closed | `_pin_seat_seg is None → ()` → seat MISS | pin 未配線 | 意図的 UNREACHABLE (fail-closed、global fallback 禁止) — pin 配線 (FM1 coupling、既 banked) が前提条件のまま | — | 設計どおり (exploit 側の dead zone) |

**Dead zone 判定: 全行 NO → PASS。** 唯一の「届かない」領域 = pin 未配線時の fail-closed で、これは §13 の設計意図そのもの (exploitable global search への fallback 禁止)。

## [CAUSAL GATE DAG] (実測値 @ canonical golden 併記)

```
route/policy 位置制御 → cable が C1Y を跨ぐ
  → _seat_identity_segments: C1 = {pin−1, pin}   [pin=27 (物理から独立導出・200f 安定)、実測: seated 517/517 の straddle が全て {26,27}]
  → _seat_crossing(window): y=C1Y の補間交差 (dx, z)  [tail: dx≈0.9mm, z=0.8286]
  → seated(C1)? --[GATE: dx≤3.5mm ∧ 0.821<z<0.836]--> G3 latch (+5, fire-once, never-revoked)   [f2544、onset と同 frame = 量子化床なし (②初回 FAIL の再発なし)]
        │                                              ├→ FM3 armed: post-G3 のみ escape 監視
        │                                              │    escape? --[GATE: crossing 消失 or |x_dev|>60mm]--> dropped → TERM_PENALTY −10 + terminate
        │                                              │    [実測: 0/517 誤発火、|x_dev|max=1.03mm ≪ 60mm]
        │                                              └→ C2 側: Y-monotone 連結 window → seated(C2) --[GATE 同型]--> G5 (+5)   [tail dx≈0.2mm]
        │                                                    → G6 success conjuncts: c1_retained ∧ c2_honest   [終端 両方 True]
        └ driver: sparse 領域のブリッジ = banked A′ 設計 (BC+residual が経路を供給、dense shaping は DQ1-closed)
```
**DEADLOCK 判定: なし → PASS。** 各 GATE の駆動 = scripted/BC 経路 (banked 前提) + gate 自体は canonical route 上で同一 frame 到達を実測。FM4 window は「届かなくする」方向に働いていない (divergence 0)。

## [GROUND-TRUTH VALUES] (実 frame、bar は built-model 由来 `route_env_config.py:161-163` / 罰・bonus は `:104,:107`)

| State (frame) | C1 dx | C1 z | seated(C1) | FM3 armed/escape | C2 dx | r event |
|---|---|---|---|---|---|---|
| P0〜pre-seat (f<2544) | crossing 未成立 or 帯外 → MISS sentinel | — | False | inert (G3 未 latch)・escape=False 実測 | — | 0 (sparse) |
| pin onset (f2544) | ≤bar (同 frame seated) | 0.8286 帯内 | **True → G3 +5** | armed、escape=False | 未着 | +5 |
| 終端 (f7684-7704) | 0.87-0.98mm | 0.8286 | True (c1_retained) | escape=False (\|x_dev\|≤1.03mm) | **0.18mm (c2_honest True)** | G5 +5 済・G6 conjuncts 成立 |
| (対照) stray-loop fixture | window 外 loop = 溝内でも **MISS** | — | False (unit test 実測) | — | C2 非連結 loop も False | 偽 latch 0 |
| (対照) post-G3 crossing 消失 fixture | None | — | — | **escape=True → −10 + terminate** (unit test 実測) | — | −10 |

## [EPISODE TRACE] (canonical golden、frame 軸)

```
f0-2543   : approach/descend/route 前半。C1 crossing 未成立 or 帯外 → seated=False。FM3 は phase-gate で inert
            (c1_latched=False → escape=False を全 pre-onset 帯で実測) —「未到達 = 正常」が罰にならない。
f2544     : pin onset。同 frame で seated(C1)=True → G3 latch (+5)。⭐onset と latch の間に gap なし
            = ②初回 FAIL (T_GROOVE 3mm < 量子化床 7.32mm で latch 不能) の interp fix が tighten 後も保存。
f2544-7707: 517/517 sample で seated 継続 (dx 単調に ~0.9mm 帯へ)。FM3 監視下で誤 escape 0、|x_dev|max=1.03mm。
route 後半 : C2 側 Y-monotone window で seated(C2)=True (dx~0.2mm) → G5 (+5)。
終端       : c1_retained=True ∧ c2_honest=True → G6 conjuncts 成立 (success 到達可能)。
(反実仮想) : 途中で C1 逸脱 (crossing 消失/60mm 超) が起きれば dropped → −10 + terminate — fail-closed が
            「保持したまま完走」以外の完走を塞ぐ。stray loop での偽 seated は window が遮断 (unit test)。
```

## [REWARD DESIGN GATE]

- Reachability: **PASS** (dead zone なし; 唯一の到達不能 = pin 未配線 fail-closed = 設計意図)
- Causal DAG: **PASS** (deadlock なし; tighten は到達性を 0 frame も損なわない [divergence 0])
- Ground-truth: **PASS** (bar 値 = built-model 由来を実測再確認; 3+ 状態 + 両側対照)
- Episode trace: **PASS** (latch 同 frame 到達・誤 escape 0・G6 conjuncts 成立)

**GATE: PASS** — ただし owner chain 残 2 leg (p5 再 verify [宣言 bar: C1={pin−1,pin} hard identity / C2=monotone-span 連結 / tolerance note (`_SEAT_MONOTONE_TOL_M=1e-6` :1334 + minimal window 根拠 = canonical i-pin∈{−1,0} 実測 517/517)] → /pre-check) が PASS するまで §S 解除なし。

## leg 3 = /pre-check OUTCOME (2026-07-17 01:0x 追記) — **VERDICT = BLOCK〔訓練批准として〕/ 単一 episode 述語数学 = clean・SRG probe 用途 = supportable (verifier 明言)**

独立 verifier (sub-agent、敵対姿勢・全 frame 再計算・fixture 実行) の findings — 全て on-disk 検証可能:

| # | SEV | 内容 | disposition |
|---|---|---|---|
| 1 | **CRITICAL** | **pin lifecycle が episode を跨いで生存しない** (`_c1_pin_witness` 生涯 1 回・`_reset_worlds` は eq を deactivate しない実測) ⇒ route_c1_pin=True では ep2+ の力学汚染+G3 無償化 / =False では G3 後に FM3 が正当 episode を −10 で殺す — **どちらの設定でも訓練 data 無効** | = **既 banked pin 残作業 (a) witness per-episode reset + (b) eq clear on reset の独立再発見** (I0-a SCOPE 開示済・fork B 採択で単純化済)。実装 = pin node 側、設計 = p5。訓練批准は (a)(b) 着地が前提 |
| 2 | HIGH | authorize 失敗が RL hot path で **process-fatal raise** (探索残差で捕捉体積外 onset → 全 world 死) | **(d) policy-drive trigger 設計項目へ fold** (episode-scope containment: dropped/invalid 化。probe/測定 mode は raise 維持) — p5 設計 |
| 3 | MED | **FM3 が identity 非限定の global crossing を消費** (`_crossing_x_dev` :1422) — 批准した seat 意味論との spec-code 不一致。fixture 実証: (a) identity MISS+溝外 stray 有 → escape=False = fail-open (episode 焼失) / (b) routed 帯外+stray 帯内 70mm → 偽 escape −10。canonical では divergence 0 | **新規 — p5 裁定要**。fix 方向 = post-G3 の escape を identity 済 metrics から導出 (sentinel が crossing-lost leg を包含) |
| 4 | MED | **C2 単調 walk が feed 側 drape を受理** (fixture 実証: routed 側 60mm 外 + pin 後方の自由 span が C2 溝を通過 → seated=True → G5/G6 が誤 credit 可能)。scripted+capped residual では低確率、free RL/DR では実在 | **新規 — p5 裁定要**。fix 方向 = routed 側限定 (`held_seg_l` 系 leg) or leading-span identity leg |
| 5 | MED | **v1 証拠の精度**: (a) `c1_first_seated_frame=2544` は不再現 — 真値 = **f2428 (onset の 116 frame 前)**。⭐**seat は pin より先に成立し、pin は既成着座の【保持】装置** — 私の「onset と同 frame・gap なし」記述は誤り (Issue 1 の窓を隠す方向の誤り) (b) C2 lateral 実 extremum = **3.183mm** (bar まで 0.317mm) — v1 の cadence-10 は 1.98mm と 1.6 倍過大 margin 表示 (c) z 進入は SEAT_Z_HI を 10.3μm で掠める (通過型・plateau でない) | **本 doc + probe v2 で訂正済** (`gate2_rerun_fm34_probe_v2_result.json` = per-frame、v1 は lineage 保全)。方向は全て conservative (canonical は 313/313 着座・sustain 31/10 のまま) |

**帰結**: §S は**解除しない** (chain = leg1 PASS / leg2 CONFORM / **leg3 BLOCK**)。gate② 完了条件 = p5 裁定 (I3/I4) + pin (a)(b) 実装 + (d) containment 設計 → 修正後 /pre-check 再走。⭐gate が仕事をした — 単一 episode の意味論は両側検証済みのまま、**訓練展開面の blocker を訓練前に捕捉** (§13.3「/pre-check が gate の仕事をした」の再演)。canonical margin の実像: C1 dx ~0.9mm / FM3 post-onset x_dev max 1.059mm vs 60mm / C2 lateral 3.183mm vs 3.5mm (最薄 margin、DR で掠る見込み = MED 引継)。

## 検証注記
- 新規コード変更 = ゼロ (本 gate は live 済コードの設計検証)。probe/unit-test の実行 = 読み取り専用計算。
- 視覚レグ: 省略 (justified) — 幾何述語の数値検証であり motion 妥当性の新規主張なし。最終捕捉 verdict は Rs 動画 standing (§13.3)。
- 著者未特定の unit test は本 gate で内容検証の上 bank (owner chain は著者 claim と独立に進行、manifest:45)。

## leg 3 再走 OUTCOME (2026-07-17 06:1x 追記) — **VERDICT = BLOCK〔訓練批准として〕継続 / I3/I4 = 欠陥ゼロ・findings 3/4 閉鎖 verify / §S 意味論 sub-claim = 批准可能 (verifier 明言、前提条件付き)**

前段: I3/I4 実装 (`dfbddb4777`) + 二鍵 (p5 §S3.5/§S3.5a CONFORM + pN evidence HOLD B1-B3 → LIFT `85958627e3` chain) + pN FENCE OPEN GO (06:0x)。verifier = 独立 sub-agent (⚠ model = Opus 切替 — 同 tier spawn が API 529 ×3 で不能、infra 事由の documented deviation; 敵対姿勢・on-disk 自走: landed-bytes worktree 9/10 再現・diff/probe json 独立検証)。

| # | SEV | 内容 | 新規性 / disposition |
|---|---|---|---|
| 1 | **CRITICAL** | I1 = pin lifecycle が episode を跨がない (`_reset_worlds` :1032-1076 は witness/eq 不触、実測)。ep2+ は stale eq で cable が物理的に溝内 → **述語は正直に測るが状態が pin artifact** → G3 無償 latch = 訓練信号の汚染 (述語の嘘ではない) | **carry 再確認** (leg3 finding 1、未修正のまま = 設計どおり (a)(b) chunk へ。banked disposition 不変) |
| 2 | HIGH | ⭐**新規: 順序 hazard** — committed HEAD の fail-closed fence (pin fields 無 → route_c1_pin=True は raise / False は seat 到達不能 = 訓練不能) を、**dirty tree の route_executor.py pin-fields 差分が (a)(b) 無しで突破する**。現 dirty tree から route_c1_pin=True で訓練起動すると ISSUE 1 の汚染に直行 | **precondition を精密化**: route_executor pin-fields land は「(a)(b) より先」ではなく **(a)(b) と同一 landing に bundle (先行 land 禁止)** + 現 dirty tree からの訓練起動禁止 |
| 3 | HIGH | I2 = authorize/audit raise が RL hot path で process-fatal (per-world 未 guard) | **carry 再確認** ((d) containment = p5 設計項目、不変) |
| 4 | MED | C2 lateral margin 0.317mm | **既知 MED carry・I3/I4 で不変** (bar/routed dx 不触を verify) |

**Q1 (findings 3/4 閉鎖) = YES**: `_crossing_x_dev` 消費者 = obs[57] :1568 のみ (reward/done body ゼロ) / escape = 同 step identity dx (:1645←:1616) / C2 = routed 側のみ (sign 正当性を独立導出)。攻撃全滅: same-step latch ordering 安全 (escape は step 開始時 latch を読む + seat-latch と seat-loss は同 step 排他) / MISS sentinel・1μm tol = pre-existing 不触 / wrong-sign・pin 端 = fail-closed 縮退 (false-success 不能) / post-release 抑制との相互作用 = benign (G6 c1_retained が封じる)。
**Q2 (新規 mode) = NO**: I4 = 候補集合の純粋な縮小 (reject を増やすのみ、seat 捏造不能・G1-G6 到達性維持) / I3 = 分岐クラスの除去。非保守側の新規経路ゼロ。
**Q3 (§S) = 意味論 sub-claim は批准可能**: 「HEAD の seat/latch/escape 述語意味論は、**有効な per-episode pin identity + fired pin + reset 時 eq clear** の前提下で、単一 episode 上 banked correctness と等しい」 — verified。前提は宣言済み (I1 disposition) かつ **committed HEAD では機構的に fail-closed enforce** (dirty tree では非 enforce = ISSUE 2)。訓練批准は NOT — (a)(b)+bundle land+(d) まで BLOCK 継続。

**chain**: §S 解除の裁定 = 二鍵へ (p5 = §S 定義に対する意味論 sub-claim の充足判定 / pN = 本 verdict の evidence 軸受理)。reward-valid / training-ready 禁止 = **不変** ((a)(b)+(d) 完了まで — これは §S とは別の gate② 完了条件)。

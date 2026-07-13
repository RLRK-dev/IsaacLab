# (d2) DoD — FORK-1 re-measurement on a substrate where the C1 pin ACTUALLY fires

**Doc:** D2_PIN_REMEASURE_DOD_COORD_20260714.md **v1**
**Author:** %11 (COORD, w2:p3) — 2026-07-14 05:3x JST (date-THEN-write: `date` = 2026-07-14 05:35:15 JST)
**Rs GO:** 逐語「はしらせて　push」(2026-07-14) → (d) 発火、p3 = (d2)
**Charter:** %12 dispatch 05:3x (3 腕案 APPROVED + B-1/B-2/B-3 + verdict 表)
**Scope:** (d2) 限定。**B3b / B4-B7 の build に手を付けない。** device = **cuda:0 のみ** / venv = `env_isaaclab7`

---

## §0. 問い (これが全て)

> **「pin が実際に効いている env で、open-loop scripted replay は本当に落ちるのか」**

これは **FORK-1 の終端失敗帰属**の再測定であり、**trainer 構築 (数週間) の存在根拠そのもの**を決める。

⚠**07-12 の「c1pin REFUTED」は信用できない** (本 doc §1)。⇒ **今回は「それを区別できる計器」を作る。**

---

## §1. なぜ 07-12 の run が信用できないか (実読、narrative でなく code)

| # | 事実 | 根拠 |
|---|---|---|
| **1** | ✅**fail-silent path ① = latch** — `self._c1_pin_done = True` が **mjm/mjd の None check より前**に焼かれる (逐語 comment「latch: one attempt at the onset frame (**regardless of outcome**)」) ⇒ **解決に失敗しても pin は無言で一度も発火せず、assert ゼロ** | c70ba1b849 `maybe_activate_c1_pin` |
| ⭐**1b** | ⛔**fail-silent path ② = 5mm 位置一致 gate (%10 発見、当方も実読 CONFIRM。私も %9 も見落としていた)** — `if _best is None or _bestd >= 5e-3: print(...); return` ⇒ **print のみ、raise なし、latch は既に焼かれている。** ⚠**index 空間が正しくても、最近傍の事前確保 eq body が seat から 5mm 以上離れていれば pin は無言で発火しない。** 候補機構 = 呼出時点で `mjd` が Newton の live state と同期しておらず **`mjd.xpos` が stale (settle 姿勢のまま)** → 距離が 5mm 超 → silent skip | 同上 (%10 audit 05:35) |
| **2** | ⚠~~「eq を body id 経由で解決 → +1 index trap で別 body に weld」~~ = **REFUTED (当方実読 → %10 独立実読で CONCUR → %12 撤回・自認)**。当該 code は **world 位置一致**で解決している (`norm(mjd.xpos[eq_obj1id[i]] − _seat_world)`; `mjd.xpos` も `eq_obj1id` も **MuJoCo body id 空間** ⇒ index-space cross なし) | 同上 |
| ⭐**3** | ⭐⭐**fail-silent path *だけ* では 342-step 死亡を説明できない (論理)**: pin が**一度も発火しなかった**なら run は **pin-less と同挙動 (~499 step)** のはず。**しかし 342 で死んだ ⇒ 何かが確実に変わっている** | c1pin run 342 vs pin-less/baseline/cablediag 499 |
| ⭐⭐**4** | ⛔⛔**DECISIVE (%10、GPU 不要で確定) — 07-12 の artifact は「pin が発火したか」に *原理的に* 答えられない**: `comp5_c2seat_fullfire_c1pin_result.json` 全読 → **`PERCLIP_PIN` / `eq_active` / seat body / position-match の field が 1 つも無い**。**`termination_reason` すら無い** (なぜ 342 で死んだかが記録されていない)。⚠**stdout log も保存されていない** (残るは result.json と frames dir のみ)。⇔ **producer 側の run.log には witness が在る**: 「`[PERCLIP_PIN] ACTIVATED eq#27 on the EXACT runtime seat body idx55 (position-match 0.000mm) ... eq_active=1`」 | %10 audit 05:35 |

⇒ ⭐⭐**「c1pin REFUTED」は、pin が発火したかを *原理的に答えられない artifact* の上に立っている。** code が fail-silent だっただけでなく、**証拠自体が沈黙している**。
⇒ ⛔**正確な現状は「REFUTED」ではなく「試されたかどうか *不明*」。** ⇒ **「REFUTED」を根拠に据えた全ての下流判断 (FORK-1 の終端帰属 → trainer の存在根拠) は、発火の witness が無い artifact に依拠している。** (= memory `feedback-refutation-that-justifies-a-pivot-needs-the-pivots-evidence-bar-2026-07-14` の実例)

⇒ **残る 2 機構**: **(i) pin が誤った body に発火した** / **(ii) pin が発火せずとも、40 本の eq を *事前確保しただけ* で solver が変わった** (⚠ base comment 自身が「`_wire_s6_grasp_solref` **stiffens them**」= disabled eq も stiffen 対象と書いている)。
⇒ ⛔**2 腕 (pin ON/OFF) では (i) と (ii) を分離できない。3 腕にする。**

---

## §2. 3 腕設計 (%12 APPROVED)

| 腕 | 構成 | 何を単離するか |
|---|---|---|
| **A** | baseline (`perclip_pin=False`) — **現行 env** | 参照 (499 step) |
| ⭐**B** | **事前確保のみ** (`perclip_pin=True`、**activate を一度もしない**) | ⭐**「pre-allocation それ自体の効果」** |
| **C** | 事前確保 + **発火** | **pin の効果** (本命) |

⭐**合格条件 = `A ≡ B` (厳密一致。「近い」で通さない)。** A ≡ B が成立して初めて **C − B を「pin の効果」に帰属できる**。

### §2.1 `A ≠ B` だった場合 — 症状で止めず機構まで降りる (%12 要求)

| leg | 内容 |
|---|---|
| **B-1** | `nefc` / `njmax` / constraint 順序を **A/B で dump 比較** (solver の問題サイズ・順序が変わったか) |
| **B-2** | ⭐**`_wire_s6_grasp_solref` が disabled eq も stiffen するか = 実測** (base comment は **narrative**)。stiffen していれば **剛性行列が変わる** ⇒ pre-alloc だけで軌道が変わる機構が特定される |
| **B-3** | **A/B の frame-0 一致** (初期状態は同一のはず。ここが違えば **build 自体が違う**) |

⇒ ⭐**`A ≠ B` は「pre-alloc が悪い」で止めない。** そして **`A ≠ B` それ自体が上程項目**: 「07-12 の 342-step は *pin が発火しなくても* 説明できる ⇒ **あの run は pin の反証ですらなく、交絡の実証だった**」。

---

## §3. 実装 (P0 / P2) — 独自 trigger を発明しない

### P0′ — ⚠**seat index を model 間で移植しない** (%10 CRIT-5、B3-α の教訓)

⛔**当初案の誤り (訂正)**: 当方は「seat = cable segment 27 ⇒ env では `_cable_bodies[w][27]`」と書いた。⚠**これは producer の index 算術 (55 − 28 = 27) を *別 model へ移植* している** — **B3-α で焼かれたばかりの class そのもの** (index は layout 依存)。
✅**正**: **env 自身の `_cable_bodies` 空間で解決**し、**世界座標で記録の seat と一致することを assert** する。**producer の position-match (`:2352-2364`) が既にその robust form** ⇒ **それを再利用**する。segment index は **cross-check にのみ**使う (一致しなければ raise)。

### P0 — seat と onset は **記録から一意**に取る (実測済、narrative でない)

⭐**positive control 実行済 (%12 要求)**: capture provenance の `eq_identity` 全 46 本を並べて実測 —

```
connect-to-world eqs : 40 本、index 0..39 (contiguous)
obj1 (mjc body id)   : strictly +1 monotone
mapping              : eq i -> mjc body (i + 29)
recorded pin_eqid=27 -> predicted mjc body 56
recorded pinned_body(newton)=55 -> mjc = 55+1 = 56      ⭐ CONSISTENT
=> SEAT SEGMENT INDEX = 27      (cable newton head = 28)
```

⇒ **seat = cable segment 27** (env では `_cable_bodies[w][27]`)。**onset = 記録の `pin_active` trace** (B3a leg6 で **lag = 0 を実測して pin 済**) ⇒ **producer と exact parity**。
⛔**Y-argmin 等の独自 seat 推定を使わない** (交絡源)。

### P2 — index-space と fail-silent の殺処分

- eq 解決 = **B3a の `resolve_pin_eq_index` + `_assert_pin_index_spaces` を再利用** ⇒ **silent None 経路ゼロ・全経路 raise** (B3a で 10 分岐の identifiability 表により発火実証済)。
- ⭐**latch を None check の *後ろ* へ移す** (07-12 の fail-silent を機構的に殺す)。
- ⛔**「pin は効かなかった」を silent に返す経路を 1 本も残さない。**

---

## §4. leg 表 (順序厳守。⭐すべて「間違った成果物を落とす」形)

| leg | 内容 | (i) 落とす誤り | (ii) negative/positive control | (iii) mode 一致 |
|---|---|---|---|---|
| **P3 = A≡B** | 腕 A と腕 B の**厳密一致** | 「pre-alloc は無害」という**未検証の前提** | ⭐A≠B なら **B-1/B-2/B-3** で機構特定 | 同一 driver / cuda:0 |
| ⭐**P1 = 計器の生存証明** | pin 発火後に **(a) `mjd.eq_active[eq_idx] == 1` を実測** + **(b) `d(seg27, C1 groove center)` が R-release 引き渡しを跨いで 4.16mm 近傍に留まる**ことを実測 | ⭐**死んだ計器を「pin の反証」と誤読すること** (= 07-12 の再演) | ⛔**52.87mm 側へ単調離脱 ⇒ verdict = INSTRUMENT DEAD**、「pin は効かない」と**書かない**。fix-first で再走 | 記録 (pin あり) と同 mode |
| **P4 = 本測定** | pin live 確認後に **full open-loop replay** | — | 記録との divergence 全 trace | FF (記録駆動) |
| **P5 = 副産物** | **HOLD_THRESH 15mm の非交絡再導出データ** (現行の初回 crossing t=343 は *pin 欠落窓の内側* ゆえ交絡) | 交絡した閾値を「素の閾値」と誤用すること | pin live trace から素の divergence 帯 | — |

**P4 の記録項目**: (a) R-release 引き渡しで把持が生き残るか (b) cable が落ちるか (c) C1→C2 が **seated で完走**するか (d) 記録との divergence 全 trace。

---

## §4.5 ⭐ %10 の走行前 audit 受入基準 (9 件、全 fold)

| # | 基準 | 反映先 |
|---|---|---|
| 1 | **P1 = INSTRUMENT-DEAD precondition** (seat seg の C1 距離が 4.16mm 近傍で一定。FAIL ⇒ **pin の反証ではない**) | §4 P1 + §5 verdict |
| ⭐**2** | ⛔**発火 witness の永続化 (必須)** — `eq_active[eqid]==1` / 解決した eq id / 束縛 body / **position-match 距離** を **result JSON に書く** (stdout だけにしない) + **stdout log も保存**。⚠**07-12 の失敗の実体はこれ**: witness は code に在った (`NOT activated` を print する) が **保存されなかった** (%9 補足) | §4 P2 + §7 |
| ⭐**3** | ⛔**determinism control (A vs A′)** — **同一 arm を 2 回**走らせ **byte 一致を先に示す**。⚠**これが無いと「A ≠ B」を pre-allocation に帰属できない** (GPU 非決定性かもしれない) | §2 に前置 |
| ⭐**4** | ⛔**baseline を現 HEAD で再導出** — **342/499 は 07-12 の tree の値**。以後 lane-floor fix / B1 route_t / B2 HOLD flag / B3a capture hook が入っている ⇒ **arm A を今の HEAD で走らせ 499 を再現するか先に確認**。再現しなければ **旧比較は無効** | §2 に前置 |
| ⭐**5** | ⛔**seat index を model 間で移植しない** — env 自身の `_cable_bodies` 空間で解決 + **世界座標で記録 seat と一致を assert** | **§3 P0′ (訂正済)** |
| **6** | **`termination_reason` を必ず記録** (07-12 に無い) | §4 P4 |
| **7** | **flag-gated (default OFF) + flag-OFF で env-core byte-preserve**。⛔**dead branch をそのまま復活させない** (あれは fail-silent 版) | §3 P2 |
| **8** | **出力は新規 dir へ** (banked artifact を上書きしない、F-8.7) | §7 |
| ⚠**9** | **本 run は *測定* の authorization であって *設計採択* ではない** — 「pin を RL env に常設」= INVARIANT #5 の scope 変更 = **Rs 専権** | §6 + §5 |

⇒ **走行順序 (確定)**: **A′ (determinism) → A (HEAD baseline 再導出) → B (pre-alloc のみ) → [A ≡ B 判定] → C (発火) → P1 → P4 → P5**

---

## §5. verdict 表 (3 腕版、%12 確定)

| 条件 | verdict | 次 |
|---|---|---|
| **A ≢ B** | ⭐**07-12 run は交絡の実証** (pin の反証ではない) | それ自体を上程。機構を **B-1/B-2/B-3** で特定 |
| **A ≡ B、かつ C の P1 FAIL** (seg27 が C1 から離脱) | ⛔ **INSTRUMENT DEAD** | 「pin は効かない」と**書くな**。fix-first で再走 |
| **A ≡ B、C の P1 PASS、route 完走** | ⛔⛔ **FORK-1 終端帰属 = FALSIFIED** | **即 STOP → %12/%9 → Rs 上程。B3b 以降を build するな。**「閉ループだけが直せる」= trainer の存在根拠が崩れる |
| **A ≡ B、C の P1 PASS、route なお失敗** | ✅ FORK-1 は pin 可能 substrate 上でも成立 | **B3b-B7 解禁** + HOLD_THRESH 非交絡再導出 |

---

## §6. governance (先に潰す)

- pin は **RS71 §0 INVARIANT #5 の唯一の authorized 例外** (Rs 逐語 `log.md:6534`)。**授権は *機構* で scope されている (file/harness ではない)。**
- **RS71 §4 が pin を routing 機構として名指し** ⇒ **env への配線は INVARIANT の拡張ではなく *遵守*** (env が banked spec に非適合のまま build されていた)。
- ⚠**恒久 disposition は Rs 未裁定。(d2) は *測定のための最小配線* であって option A の採択ではない。** B3b で恒久化する前に Rs 裁定を取る。

---

## §7. 本 leg 自身の計器規律 (本 arc の教訓の自己適用)

- ⭐**計器を使う前に検証する**: P1 が「計器の生存証明」。**P1 を通さずに P4 の数値を解釈しない。**
- ⭐**零/不在は「対象が無い」か「計器が死んでいる」か区別できない** (spec §18 F-7.4) ⇒ **P1 が positive control**。
- ⭐**guard は発火することを実証する** (spec §19 F-8) ⇒ P2 の resolver は B3a で **10 分岐 identifiability 実証済**。
- ⭐**narrative でなく on-disk/実測**: §1-2 の「+1 trap」撤回、§3 の eq↔segment mapping 実測 (どちらも「〜のはず」を実測に置換した)。
- **date-THEN-write**: 本 doc の時刻は `date` 実行値。

# (d2) DoD — FORK-1 re-measurement on a substrate where the C1 pin ACTUALLY fires

**Doc:** D2_PIN_REMEASURE_DOD_COORD_20260714.md **v1**
**Author:** %11 (COORD, w2:p3) — 2026-07-14 05:3x JST (date-THEN-write: `date` = 2026-07-14 05:35:15 JST)
**Rs GO:** 逐語「はしらせて　push」(2026-07-14) → (d) 発火、p3 = (d2)
**Charter:** %12 dispatch 05:3x (3 腕案 APPROVED + B-1/B-2/B-3 + verdict 表)
**Scope:** (d2) 限定。**B3b / B4-B7 の build に手を付けない。** device = **cuda:0 のみ** / venv = `env_isaaclab7`

---

## §0. 問い + ⭐framing (%12 指示: これを冒頭に置く)

> **「pin が実際に効いている env で、open-loop scripted replay は本当に落ちるのか」**

これは **FORK-1 の終端失敗帰属**の再測定であり、**trainer 構築 (数週間) の存在根拠そのもの**を決める。

### ⭐⭐ framing — 「REFUTED」が空虚である経路は **4 本**あり、**うち 1 本は既に確定している**

| # | 経路 | 発見 | 状態 |
|---|---|---|---|
| 1 | **pin が一度も発火しなかった** (fail-silent latch + 5mm gate、**両方 raise 無し**) | %9 + %10 | **code 上で確定** |
| 2 | **事前確保だけで挙動が変わった** (発火せずとも 342 を説明) | **p3 (当方)** | **(d2) 腕 B が決める** |
| 3 | ⭐**342 vs 499 が baseline 自身のばらつきの中** (= **信号が最初から無かった**) | %12 | **(d2) 腕 A/A′ が決める** |
| 4 | ⭐⭐**artifact が「どれなのか」を答える field を 1 つも持たない** (eq_active / seat / position-match / **termination_reason** すべて不在、stdout 未保存) | **%10** | ⭐**GPU 不要で *既に確定*** |

⇒ ⭐⭐⭐ **4 が既に確定している以上、1/2/3 のどれであれ「REFUTED」は成立していない。**
⇒ ⛔**(d2) は「どれだったか」を決めるのであって、「REFUTED が正しかったか」を決めるのではない。**

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

## §4.6 ⭐ 走行前 audit の条件 (%10 C-1〜C-5 / %12 CRIT-1・2 + MED)

### ⛔⛔ CRIT-1 (%12) — **視覚レグが無かった。3 人とも見落とした。** ⇒ 必須化

⚠**測定対象そのものが kinematic trick (weld = 物理を *上書きする* 機構)** ⇒ **THREAD で最も「数値 PASS / 動画 wrong」に転びやすい配置**:
- 「seg27 が C1 から 4.16mm」は、**cable が clip に *めり込んだまま* weld が押さえている**状態でも成立する。
- 「route 完走 / C2 seated」は、**weld が物理的にありえない配置を保持している**状態でも成立する。
⇒ ⭐**物理を上書きする機構を、数値だけで採点してはならない。**

| # | 必須項目 |
|---|---|
| 1 | **P4 の run で動画を録る** — route 全域 + ⭐**C1 接触点の zoom** |
| 2 | **pC (VIDEO-ANALYST) の独立判定 — blind** (数値・結論・期待を渡さない) |
| ⭐**3** | ⛔⛔**FORK-1 を falsify する verdict は、Rs の動画 human-GT を経てからでないと *act しない*。** 数値だけで **B3b を止めない・trainer を否定しない**。(**Rs autonomy grant の唯一の例外 = 動画 human-GT**) |
| 4 | **動画は `~/Downloads` へ proactive 納品** (Rs standing) |
| ⭐**5** | **見るべき 3 点**: (a) **cable が clip にめり込んでいないか** (weld が幾何を上書き) (b) **把持が指の間を滑っていないか** (c) ⭐**cable が不自然に硬直していないか** — **weld が chain を固めて divergence を *隠して* いないか。「直した」のか「隠した」のかは動画でしか分からない** |
| 6 | 省略時は **loud に理由を記録** (mandatory-or-justified) |

⭐**補助診断 (%9 提案) — 「隠蔽」は数値に足跡を残す。⛔ただし *動画の代替ではない*: これは pC/Rs に「どこを見るか」を指す道具であって verdict ではない。**

**weld が divergence を「直した」のでなく「chain を固めて隠した」なら、articulation が死ぬ。** 腕 C で測る:
| # | 量 | golden の実測 (生きている chain) |
|---|---|---|
| (i) | **hinge 角の時間変化** `\|Δq\|` の分布 | weld 後に落ちれば硬直の足跡 |
| (ii) | **bend 平面の roll 角の時間変化** | golden は route 中に **最大 89.6° roll** = **chain は生きて動いている** (%9 実測) |
| (iii) | **seg27 近傍 vs 遠方の articulation 比** | weld 近傍だけ死んでいれば**局所硬直** |
| — | (参考) cable の平面性 `s3/s1` | golden median **2.5e-07** (極めて平面) |

⇒ **「A/B と比べて C だけ articulation が崩壊」= 隠蔽の足跡。**
⇒ ⛔**ただし「数値が良い + articulation も生きている」でも、Rs の動画 human-GT 無しに FORK-1 を falsify しない** (CRIT-1 #3)。

### ⛔ CRIT-2 (%12) — **A ≢ A′ の分岐が無い ⇒ 第 3 の経路**

⭐**もし A ≢ A′ (GPU 非決定) なら「342 vs 499」は run-to-run のノイズかもしれない。**
⇒ **分岐**: A ≢ A′ なら **arm A を N≥5 回**走らせ **step 数の分布**を取る。⇒ ⭐**342 が A 自身の分布内なら、07-12 の「信号」は最初から存在しなかった** (framing 経路 3)。

### ⛔⭐ C-1 — **A≡B を boolean にしない。「ノイズ床に対する相対」で判定する** (%10 C-1 + %12 CRIT-2 の合成、%12 が自らの bar を訂正)

⚠**当初 bar (当方 + %12) = 「A ≡ B (厳密一致)」は誤り**: **腕 A (neq=6) と腕 B (neq=46) は *model が違う*** ⇒ MuJoCo の arena/njmax/reduction 順序が変わり、**physics が同一でも bitwise は割れ得る** (FP path 差)。⇒ **「効果ゼロ」でも FAIL し、escalation を誤発火させる。**

⭐**正しい構成 (3 段)**:
| # | 手順 | 意味 |
|---|---|---|
| **1** | ⭐**A vs A′ (同一 arm を 2 回) が *ノイズ床* を定義する** — `max\|Δcable_xyz\|` と `step` / `termination_reason` の再現性 | **計器の分解能を先に測る** |
| **2** | ⭐**A vs B は、そのノイズ床と *比較* して判定**: <br>・`\|A−B\| ≈ \|A−A′\|` ⇒ **pre-alloc に効果なし** (A ≡ B 成立) ⇒ C へ <br>・`\|A−B\| ≫ \|A−A′\|` ⇒ **pre-alloc が効いている** = ⭐**07-12 の run は交絡の実証** ⇒ 上程 | **相対判定** |
| **3** | ⭐**A′ が A と割れる (= 非決定的) 場合**: 腕 A を **N≥5 回**走らせ **step 数の *分布*** を取る ⇒ ⭐**342 がその分布の中に入れば、07-12 の信号は最初から存在しなかった** (framing 経路 **#3**) | **信号の有無そのものを問う** |

⇒ ⭐**boolean をやめ、`max|Δcable_xyz|` / `step` / `termination_reason` を **数値で**出し、**ノイズ床に対する相対**で判定する。** ⛔**「効果ゼロ」を FAIL にしない・「ノイズ」を発見にしない。**

### ⛔ C-2 + MED-2 — **P1 の bar (⚠ 2 名の指示が衝突。調停する)**

- **%10 C-2**: 「4.16mm 近傍」は数値でない ⇒ **許容を pin せよ** + ⭐**identifiability の対**を示せ。
- **%12 MED-2**: ⚠**4.16mm は *記録 (producer build)* の値。env は別 build (それが FORK-1 の前提) ⇒ env の pinned 距離が 4.16 と一致する必然性は無い。**「4.16 と一致しないから INSTRUMENT DEAD」と誤読される bar にするな。

⭐**調停 (両立する形)** — bar を **値の一致でなく *挙動* で定義**する:
| # | bar | 根拠 |
|---|---|---|
| **B1** | **有界**: pin 後の全 window で `d(seat_seg, C1_groove_center) ≤ 10mm` | %12 MED-2 (env は別 build ⇒ 値一致を要求しない) |
| **B2** | **非発散**: post-onset window で **単調増加でない** (線形 fit の傾き ≤ 0 近傍) | 52.87mm への**単調離脱**と判別 |
| ⭐**B3** | ⭐**identifiability の対 (%10 C-2)**: **同じ metric・同じ code で 腕 A (pin 無し) を測り、A が B1/B2 を *FAIL* すること**を同 leg で示す ⇒ 「P1 は pin の有無を判別できる」の実証。**腕 A は既に走るので追加コストゼロ** | %10 C-2 |

⇒ **B3 が無ければ P1 は「PASS するだけの計器」。**

### ⛔ C-3 (%10) — **4.16mm を作った式と *完全同一* の式で測る (計器 parity)**

⇒ **doc に逐語 pin**: (a) seat seg (b) clip 中心 (c) 3D か水平のみか (d) **groove center Z の読み元** — ⚠**route scene は `ROUTE_GROOVE_Z = 0.829` (`route_env_config.py:144`)、`task_config` の 0.809 ではない** (%10 CRIT-1、%9 が golden 実測 829.0mm で独立確認)。
⇒ ⭐**parity 証明**: **記録側の 4.16mm を *同じ code* で再計算して一致を確認**してから env に使う。**計器を使う前に検証する。**

### ⚠ C-4 (%10) — RAISE 化しても **診断可能性**を残す

⇒ **raise message に実測 position-match 距離を必ず載せる** (producer は `position-match 0.000mm` を出す)。⭐**その距離こそ「なぜ 07-12 で pin が発火しなかったか」の答えかもしれない** — 落ちても finding が残る形に。
⇒ **producer の呼出順序 (mj_forward の位置を含む) を verbatim 再利用**し、**position-match ≈ 0 を assert**。

### ⚠ C-5 (%10) + MED-1 (%12) — **述語は banked のものを使う (発明しない)**

- **route 完走 = `strict_v2` (`c1_retained_final` AND `c2_seated_honest`)** — banked 成功述語。
- **seated = code 自身の述語**: `cable_in_groove` / `GROOVE_BODIES_MIN = 2` (`task_config.py:384`) / `T_GROOVE = 0.003` (`:368`)。
⇒ ⛔**ここで新 bar を発明すると、最重要 verdict (FORK-1 帰属 FALSIFIED) が新 bar 依存になる。**

### (LOW)
- **P5 の出力は「データ」であって「採択値」ではない** — HOLD_THRESH は Rs W0-a 採択値・B2 は CLOSED ⇒ 変更は **spec 変更 = %12/Rs 経路**。
- **A′ は comparator の検証にも使う** — 「A≡B に使う比較器が A vs A′ で *一致を返す* こと」を先に示す (**計器を使う前に検証する**の自己適用)。

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

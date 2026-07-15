# Reward-Design Gate ② — seat-latch 述語の再設計【裁定】

**Author:** VT-DESIGN (w2:p5)。**Date:** 2026-07-15 20:59 JST（date-THEN-write）。
**Status:** ⭐**BANKED 2026-07-15 21:1x（%12 = RS-TECH-LEAD verifier、on-disk 再検証）** — §1 の 4 連言 + §9 の 3 現場 + 壁幾何を独立読了・全 CONFIRM: `route_executor.py:3881` `_c2_settled`=contact(≤0.5)+z、dx-identity レグ無し / `policy_route_runner.py:309` `_pin_replay`=同型 / 壁内面 ±7.5mm（`newton_skill_env_base.py:1850-1851` = lower walls x=∓0.009 ± hx0.0015）⇒ dx bar 3.5=7.5−cableR4。実装 = %12（L3、その後 `/pre-check` 必須）。p5 = 0-commit。
**Trigger:** %12 上程 `REWARDDESIGN_GATE_SEATLATCH_QUANTFLOOR_RSTECHLEAD_20260715.md`（reward-design ② = FAIL、seat-latch G3/G5/G6 が計器の量子化床を下回る）。%12 の role boundary 逐語:「a broken success/reward predicate is a design change = Rs/p5 専権 … I surface, I do not decide」⇒ **本 doc が設計裁定。**
**⛔ message の数値では裁定していない。doc + 4 code path を自分で on-disk 読了。** L3（成功条件変更）。実装は %12、その後 `/pre-check` 必須。

---

## §1 裁定 — gate FAIL を【CONFIRM】。ただし壊れているのは【計器】であって【3mm bar でも sparse 構造でもない】

%12 の FAIL は正しい。私の on-disk 検証（4 連言すべて）:

| 主張 | 自分で読んだ cite | 裁定 |
|---|---|---|
| `_seat_metrics` = 最近傍Y node | `newton_route_env.py:1306` `near = argmin(|cable_pos[:,1] − clip_xy[1]|)` | ✅ |
| `lateral` が Y 残差を含む | `:1309` `lateral = ||p[:2] − clip_xy||`（2D、node の Y ずれ込み）⇒ `seat_dist = sqrt(lateral²+z²) ≥ lateral ≥ |dy|`（`:1310`） | ✅ |
| bar = 3mm | `task_config.py:368` `T_GROOVE = 0.003`（コメント「CLIP_GROOVE_INNER_RADIUS/2」= 恣意的な半径半分） | ✅ |
| 量子化床 | `task_config.py:135-136` `CABLE_SEGMENTS=40 × CABLE_SEG_LEN=0.015` ⇒ Y-pitch 15mm ⇒ 最近傍 node の `|dy|` 床 = **half-pitch 7.5mm**（first-principles）/ 7.32mm（pC 実測、node が完全な Y 平行でない分だけ < 7.5） | ✅ |
| G3/G5 が seat_dist を採る | `:1487` `c1_seat,_,_ = _seat_metrics(...)` / `:1550` `p3 = c1_seat < T_GROOVE` / `:1552` `p5 = c2_seat < T_GROOVE` | ✅ |
| ORDERED ⇒ G6 到達不能 | `:1560-1561` `if k>0 and not _g_latched[k−1]: break` / `:1570` G6 は G5 latch 必須 ⇒ 5-clip whole-route で `(0.4)^5 ≈ 1%` = 実質到達不能 | ✅ |

**⇒ 3mm < 7.32mm floor ⇒ 物理的に完全着座でも ~59-70% は latch 不能。conservative FAIL（sim が現実より成功を難しく採点）⇒ bankable、fix-first。**

### §1.1 ⭐ ただし root cause は「bar が厳しすぎる」ではない — 【計器が境界と同一性を混同している】

これは今夜 3 度目の同形（[[feedback-the-boundary-question-and-the-identity-question-are-different-2026-07-15]]、`RLENV_PIN_DESIGN §18`）。`_seat_metrics` は 2 段:

1. **同一性/選択**「clip の Y でケーブルを代表する点はどれか」← `argmin`-over-Y（**離散・量子化された選択**）
2. **境界/計量**「その点は軸から X にどれだけ外れているか」← 真の捕捉問い

⛔ **離散 node を選び（同一性）、その node の【2D 距離】を測る（境界）ことで、選択の量子化残差 `dy` が境界計量に漏れ込む。** `T_GROOVE=3mm` は真の X-捕捉問いに対しては妥当（3mm < 壁内面 3.5mm）— 壊れているのは bar ではなく、**bar が dy 残差に汚染された量を採点している**こと。

⇒ ⭐ **sparse-primary G1-G6 構造も正しい**（BC prior が物理着座を作り、sparse latch が確認する設計）。dense shaping は `/pre-check`=BLOCK + DQ1→"B" で既に閉じた決定（doc:12）⇒ **再導入は closed decision の re-open = scope 違反。触らない。**

---

## §2 設計 — 【y=clip_y で正確に交差する点を補間し、そこで dx を測る】

計器だけを差し替える（物理・substrate・reward 構造は不変）。

```
def seat_metrics_interp(cable_pos, clip_x, clip_y):        # 量子化フリー・S字ロバスト・fail-closed
    ys = cable_pos[:,1]
    xs = cable_pos[:,0]; zs = cable_pos[:,2]
    best = None
    for i in range(n-1):                                   # y=clip_y を跨ぐ全 segment
        if (ys[i]-clip_y)*(ys[i+1]-clip_y) <= 0 and ys[i]!=ys[i+1]:
            t = (clip_y - ys[i])/(ys[i+1]-ys[i])           # 線形補間
            x_cross = xs[i] + t*(xs[i+1]-xs[i])            # ← dy = 0 by construction
            z_cross = zs[i] + t*(zs[i+1]-zs[i])
            dx = abs(x_cross - clip_x)
            if best is None or dx < best[0]:               # 複数交差(S字=D-5必須) ⇒ 最も溝に近い交差
                best = (dx, z_cross)
    if best is None:                                       # y=clip_y に届かない ⇒ 未着座
        return (INF, INF)                                  # fail-closed
    return best                                            # (dx, z_cross)  — dy 成分なし
```

**述語（clip ごと、§15 pin-auth と同じ built-model bar 族に統一）:**
```
seated := (dx ≤ wall_inner)          # 同一性レグ = 壁内面(built model, ~3.5mm) − 0。T_GROOVE=3mm を supersede
        ∧ (floor_top−R < z_cross < wall_top−R)    # 821 < z_cross < 836、両方 built model（§15.6 と同一帯）
```

- **dy を construction で 0 にする** ⇒ 量子化床が消える。node lattice の phase 抽選が消える。
- **bar は built model 由来**（壁内面・床・天）。config datum `T_GROOVE=3mm` は削除（datum discipline、§15 と同じ理由）。3mm は「半径半分」で恣意的、しかも壁沿い着座（|dx|=3.5mm、まだ溝内）を false-negative する。
- **combined `seat_dist=sqrt(dx²+z²)` を捨て、dx と z を別レグに分割**（walls と floor/rim は別制約 — §15 と統一）。

---

## §3 Artifact 1 — REACHABILITY TABLE（FIXED 設計）

P0 = BC prior が物理着座を作った後の dwell。「Reachable」= 物理的に正しい挙動から sparse latch が発火するか。

| G | gate（FIXED latch 条件） | 物理正時 reachable? | signal/gradient | Dead zone? |
|---|---|---|---|---|
| G1 grip | grip∧contact∧span | yes | grasp phase (BC prior) | no |
| G2 lift | held_z rise ≥ margin | yes | lift phase | no |
| **G3 C1-seat** | **`dx_interp(C1) ≤ 3.5` ∧ z∈(821,836) ∧ ph≥2** | **yes — BC prior が溝軸に寄せる ⇒ dx<1mm。dy 抽選が消えた** | BC prior が着座 ⇒ latch 発火（sparse-primary 意図どおり） | **no** |
| **G4 regrasp** | reach∧contact ∧ G3 latched | yes（G3 が発火するので継承先が生きる） | inherits G3 | **no** |
| **G5 C2-seat** | `dx_interp(C2) ≤ 3.5` ∧ z∈band ∧ G4 latched | yes（同計器） | 同 | **no** |
| **G6 SUCCESS** | G5 ∧ `dx_interp(C2)≤3.5` ∧ **lateral-aware c1_retained** ∧ ¬drop ∧ sustained | yes（両 clip が真に保持されている時のみ ⇒ hard-but-reachable） | +200 reachable | **no** |

**Dead-zone = 全 no ⇒ Artifact 1 = PASS**（skill 規則: どの行も Dead zone=YES でなければ実装可）。

---

## §4 Artifact 2 — CAUSAL GATE DAG（FIXED、bridge 回復）

```
action(EE residual) + BC prior → arms drag cable → cable physically enters C1 groove
        |                                                     |
        |                              interp x at EXACTLY y=clip_y   ← dy=0 by construction (no lattice phase)
        v                                                     v
   dx = |x_cross − clip_x|  (真の軸外れ、量子化なし)   ---[G3: dx ≤ 3.5 ∧ z∈(821,836)]--- latch G3 (+5)
                                                              |  BC prior が着座を作る ⇒ 発火する(sparse-primary)
                                                              v
                       ORDERED: G4←G3, G5←G4, G6←G5 が順に生きる
                                                              v
                              G6(+200 SUCCESS) reachable  ==>  RL 学習信号が materialize する
```
**G3 に「driving reward が無い」= sparse-primary の【意図】であって defect ではない**（BC prior が着座を供給、latch は確認役）。floor が消えたので latch は BC-anchored 挙動から発火する ⇒ **DEADLOCK 解消 ⇒ Artifact 2 = PASS。** ⚠ dense shaping は足さない（DQ1-blocked、§1.1）。

---

## §5 Artifact 3 — GROUND-TRUTH VALUES（FIXED、built params から計算）

C1=(0.35, 0.150)、groove rest z=829、壁内面 ±7.5mm、cable R=4mm ⇒ 溝内 cable center |dx|∈[0, 3.5mm]。**node dy 抽選を明示的に振る**（旧計器の汚染源）:

| State | phys seated? | node dy（抽選） | 真の dx | 旧 seat_dist=√(dx²+dy²+z²) | 旧 G3(<3mm) | **interp dx** | **FIXED G3(≤3.5)** |
|---|---|---|---|---|---|---|---|
| S0 中央・node整合 | **yes** | 0.0 | 0.5 | 0.71 | ✅(lucky) | **0.5** | ✅ |
| S1 中央・node半ズレ | **yes** | 3.66 | 0.5 | 3.73 | ❌ **FN** | **0.5** | ✅ |
| S2 中央・node最悪 | **yes** | 7.32 | 0.5 | 7.34 | ❌ FN | **0.5** | ✅ |
| S3 壁沿い着座 | **yes** | 4.0 | 3.4 | 5.24 | ❌ FN | **3.4** | ✅（<3.5、3mm bar なら誤 reject） |
| S4 棚上（§16.2 型） | **no** | 4.0 | 14.5 | 15.0 | ✅REJ | **14.5** | ✅ REJ |
| S5 溝脇・未着座 | **no** | 0.0 | 20 | 20.6 | ✅REJ | **20.6** | ✅ REJ |

⇒ ⭐ **旧計器は S1/S2/S3（着座済）を未着座 S5 と同じ「NO」にした（false-negative）。FIXED は着座 S0-S3 を全 accept、未着座 S4-S5 を全 reject。両方向の誤りが消える ⇒ Artifact 3 = PASS。**

---

## §6 Artifact 4 — EPISODE TRACE（FIXED）

```
Step 0:  BC prior + residual が committed route を駆動。G1(grip),G2(lift) latch。+10。
Step k:  cable が C1 溝に物理着座。gripper が軸に寄せる ⇒ interp dx = 0.6mm、z_cross = 828.7mm。
         G3: 0.6 ≤ 3.5 ∧ 821<828.7<836 ⇒ latch。+5。（node dy が 4.1mm でも interp は dy=0 ⇒ 無関係）
Step k+1..: dwell 中 dx が walls 内に留まる限り G3 latched（fire-once、never-revoked）。
         ORDERED: G4(regrasp)→G5(C2-seat、同計器で reachable)→G6。
Step m:  C2 着座 + c1_retained(lateral-aware) sustained K=10 ⇒ G6 SUCCESS +200。
```
**~70% の抽選死が消える ⇒ +200 が correct rollout から reachable ⇒ Artifact 4 = PASS。**

---

## §7 断面図（geometric-design、C1 溝 XZ 断面、y=clip_y の交差点）

```
z[mm]                     interp が測る点 = ●(x_cross, z_cross)  ← y=clip_y で線形補間、dy≡0
 850 ─  ┌─┐lip                    ┌─┐          lip 天 850（壁の外、bar 対象外）
 840 ─  │ │────────rim 840───────│ │          ← z 上限 = wall_top−R = 836（cable 中心の天井）
        │ │  ╎          ╎        │ │
 836┈┈┈┈│ │┈╎┈┈┈┈┈┈┈┈┈┈╎┈┈┈┈┈┈┈┈│ │  z_hi     ← これ以上 = rim 越え = 溝外
        │ │ ╎    ●28.7  ╎        │ │
 829 ─  │ │ ╎  ══seat══ ╎        │ │  rest z    cable R=4、rest 中心 829
 825 ─  ├─┴─╎───floor 825──╎─────┴─┤          floor_top = 825
 821┈┈┈┈┈┈┈┈╎┈┈┈┈┈┈┈┈┈┈┈┈┈╎┈┈┈┈┈┈┈┈  z_lo     ← 床−R = 821、これ以下 = 溝の【下】
        342.5      350      357.5              壁内面 342.5/357.5、軸 350
        |←3.5→|←── dx bar ──→|←3.5→|           |dx| ≤ 3.5mm = 溝内（同一性レグ）
        壁内面−cable_R = 軸から ±3.5mm が物理的に溝内の範囲
```
⭐ **旧 3mm bar は壁沿い着座（|dx|=3.5、S3）を切り落とす（0.5mm 誤 reject）。built-model 3.5mm bar = 幾何的捕捉定義そのもの。**

---

## §8 (a)/(b)/(c) への裁定

| # | 問い | 裁定 |
|---|---|---|
| **(a)** | 補間 vs 細分化 vs 別計量 | ✅ **補間（§2）。** 細分化 = substrate 変更（L3・Rs 承認要・cable bend 分布と物理を変え・遅く・量子化を完全には消さない）⇒ **却下**（将来の fidelity upgrade 候補としてのみ記録）。補間は【計器のみ】= 物理・substrate 不変。**sparse-primary 維持、dense shaping は足さない**（DQ1-blocked）。 |
| **(b)** | G6 の z-only `c1_retained` を lateral-aware に差し替えるか | ✅ **差し替える。** `:1491-1495` の z-only（`z_c1<840 ∧ flank<840`）は境界レグのみ・同一性レグ 0 ⇒ **81/81 no-op**（%12 defect #2）= §18 の劣化そのもの。**同じ interp を使い `dx_interp(C1) ≤ 3.5 ∧ z∈(821,836)` に置換** ⇒ 両 clip の真の保持を要求。⭐ (a) の補間があるので **reachable**（量子化床が無い）。 |
| **(c)** | lateral capture = Rs-video-only（numeric G 無し）にするか | ⚠ **部分採用・ただし defect #3 の「proven」は【撤回済前提】。** ⛔ %12 doc §7 defect #3 が引く source `ANCHOR_STEPTABLE_ALIGNMENT_p4p5_20260712.md` は **その冒頭で 07-14 19:27 に %12 自身が RETRACTED**（逐語:「前提『Rs GT = cable OFF C1』は偽 … numeric と human は一致していた … ∴『no numeric coverage; proven』は成立しない。撤回する」）。⇒ **「numeric では原理的に測れない（proven）」は成立していない。** ✅ **「Rs 動画 = 最終 GT」は standing directive として維持**（撤回文も明記: 根拠が「測れないから」→「Rs 専権だから」に変わるだけ）。⇒ **裁定 = numeric interp 述語 = RL 訓練/latch 信号（必要）+ Rs 動画 = bank/milestone の最終捕捉 GT（十分）。合成であって二者択一でない。numeric を諦めない。** |

---

## §9 ⭐ 統合 — この fix は §16.2 の C2 成功 blocker も同時に閉じる

今夜の 2 つの seat blocker は【補完的なバグ・同一の fix】:

| 現場 | 計器 | 欠陥 | interp-dx fix の効果 |
|---|---|---|---|
| **RL env**（本 gate） | `_seat_metrics` 最近傍Y node、`lateral` は dx を含むが dy 残差で汚染 | **false-negative**（量子化床） | dy→0 で lateral を dx に純化 ⇒ reachable |
| **route/producer**（§16.2） | `_c2_settled` = `min_dist(cable,clip2)` 接触、**dx を全く持たない**（接触は壁両側で 0） | **false-positive**（棚が接触 0.0） | interp-dx レグを追加 ⇒ 棚 |dx|=14.5 を reject |

⇒ ⭐⭐ **両者は「y=clip_y の交差点で dx を測る」= 同一性レグに収束する。§18 の原則を 3 現場（RL env `_seat_metrics` / route `_c2_settled` `route_executor.py:3881` / runner `_pin_replay` `policy_route_runner.py:309`）すべてに適用せよ。** 3 つとも同一性レグを欠く（[[feedback-the-boundary-question-and-the-identity-question-are-different-2026-07-15]]）。

⚠ **ただし route 側は `c1_wall_dist_spacer_excluded_mm` が emit されていない**（%12 doc §7 leg 3）⇒ **producer re-run が必要**（qpos dump か決定的 replay、訓練不要・GPU 不要）。RL env 側（本 gate）は補間で self-contained ⇒ producer 待ち不要。

---

## §10 scope / process / grounding

- **L3**（成功条件変更）。実装 = %12。実装後 `/pre-check` 必須（BLOCK なら実装禁止）。私は 0-commit（本 doc = 設計裁定、bank = %12）。
- **W1 build B3b-B7 は依然 gated** — reward-design ② は本 fix の実装 + `/pre-check` PASS まで FAIL のまま。`authorize_clip_pin` §15 の design-of-record は本 gate と独立（pin-auth 幾何 gate ≠ RL success 述語）だが、配線先の env が有効な seat 信号で訓練できるのは本 fix 後。
- **datum discipline**: 全 bar は built model（壁内面・床・天）から。config datum `T_GROOVE=3mm` は削除。

| 主張 | cite |
|---|---|
| 最近傍Y node / lateral 汚染 | `newton_route_env.py:1306` / `:1309` / `:1310` |
| G3/G5 bar・ORDERED・G6 | `:1487-1488` / `:1550` / `:1552` / `:1560-1561` / `:1570-1575` |
| c1_retained z-only（no-op） | `:1491-1495`（`C1_RETAINED_LOW_WALL_TOP_M=0.840`、`route_env_config.py:115`） |
| `_crossing_x_dev` の誤ラベル | `:1322-1327`（comment「interpolation」だが code は最近傍 node の x、drop に使用 `:1516,:1522`） |
| T_GROOVE / cable seg | `task_config.py:368` / `:135-136` |
| built-model 溝幾何 | 壁 `newton_skill_env_base.py:1850-1851`（dx=∓0.009, hx=0.0015 ⇒ 内面 ±7.5mm）/ float `route_env_config.py:142`（+20mm、rest 829） |
| defect #3 撤回済前提 | `harness/state/ANCHOR_STEPTABLE_ALIGNMENT_p4p5_20260712.md` 冒頭 RETRACTED 2026-07-14 19:27（Rs GT = C1 seated OK） |
| §16.2 / §18 統合 | `RLENV_PIN_DESIGN_VTDESIGN_20260715.md §16.2`（C2 棚）/ `§18`（境界≠同一性）|
| prior-art guard | `check_thread_vault_prior_art.sh "seat predicate interpolation" "nearest-in-Y quantization" …` ⇒ PASS（findings=0 blockers=0、2026-07-15 20:5x）|

---

## §11 §8(b) の実装 coupling 裁定（%12 の問いへの回答、2026-07-16 01:2x、post-bank addendum）

**%12 の問い:** c1_retained を interp dx に差し替えると frozen recount / DoD-9a mirror と乖離する。§8(b) の意図は (i) frozen から decouple（DoD-9a mirror を drop、RL env 独自 interp）か (ii) producer re-run と coupling か?

**⛔ 答えは (i) でも (ii) でもない = (iii)。%12 の message でなく on-disk を読んで裁定:**

| 決定的事実 | cite | 帰結 |
|---|---|---|
| frozen recount は **npz の node 位置から計算** | `p9_recount_strict_v2.py:41-44` `flank_from_npz`（`z["cable_xyz"][-1]` → `cab[:,1]`/`cab[:,2]`）。`cable_xyz` = recorder が全 node 記録（`route_demo_recorder.py:279`） | ⇒ **interp-dx は同 npz からオフライン再計算可能・sim 不要** |
| DoD-9a = **live 自己計算 == frozen recount**（両方 位置から導出） | `newton_route_env.py:1286-1287` / `:1289-1291`（live `_c1_retention_m` は `flank_from_npz` の EXACT mirror） | ⇒ **両側を interp 化すれば DoD-9a は保存**（interp は位置の決定的関数 ⇒ 位置が一致すれば interp も一致） |
| c2_honest は **`_seat_metrics` を呼ぶ** | `:1317` `seat_dist,z_gap,_ = self._seat_metrics(cable_pos, _C2_XY)`。`:1314` = 「geometric **proxy**」（byte-mirror でない、DoD gate 無し） | ⇒ **G3/G5 の interp 化で自動追従**。gate は壊れない |

### §11.1 裁定 = (iii) mirror を保ち、両側を interp 化する

1. **G3/G5**（`_seat_metrics` 直読）: interp 化。self-contained。✅
2. **c2_honest**（`_seat_metrics` を呼ぶ proxy）: **自動で interp 化**。producer の defective な `_c2_settled` に byte-mirror されていない（proxy ⇒ live が producer より正しくなるだけ、§16.2 で producer は defective と確定済）。gate 破壊なし。✅
3. **c1_retained**（DoD-9a mirror）: **live `_c1_retention_m` と frozen recount `flank_from_npz` の【両側】に interp-dx レグを足す**。frozen 側は既存 npz `cable_xyz` から**オフライン再導出**（sim 不要）。⇒ DoD-9a「live==frozen」は**保存され**、今度は正しい計器を validate する。

### §11.2 ⛔ (i) は誤り / (ii) は c1_retained には不要

- **(i) decouple は誤り**: DoD-9a を drop すると「live 自己計算が正しい（frozen reference と一致）」という**不変条件を捨てる**。⚠ 不変条件が問題なのではない、**両側が共有していた def（z-only）が問題**。def を直して不変条件は保て。
- **(ii) producer-couple は c1_retained には不要**: c1_retained の frozen reference は **オフライン recount（`flank_from_npz`、npz 由来）であって producer-sim-emitted metric ではない**。interp 再導出に sim 再走は要らない。⇒ **§9 の producer re-run は route/runner の *producer 自身の* seat/settle 計器（`route_executor.py:3881` / `policy_route_runner.py:309`）のためであって、RL 訓練 env の G6 とは別 concern。**

### §11.3 ⇒ RL env の G6 は【完全 self-contained】

interp `_seat_metrics`（G3/G5 + c2_honest 自動）+ c1_retained/recount の両側 interp-dx（オフライン）= **1 ヘルパ + 1 オフライン recount 再導出**。**producer sim 再走を待たずに今 実装できる。**

### §11.4 ⚠ 副次 flag（gate-validated-under-the-bug の自己テスト）

frozen recount を interp-dx で再導出することは、**frozen validated demo の自己テスト**でもある —「その demo は interp-dx bar を実際に通るか?」。もし demo の C1Y でケーブルが軸外（|dx| 大）なら **frozen demo は新 c1_retained を FAIL する**（旧 z-only は通していた = [[feedback-a-gate-validated-under-the-bug-is-validated-by-the-bug-2026-07-15]]）。⇒ その時は **demo の Rs 動画 re-validation 案件**（demo の「保持」が z-only で certified されていた）であって **interp fix の bug ではない**。block させず surface せよ。

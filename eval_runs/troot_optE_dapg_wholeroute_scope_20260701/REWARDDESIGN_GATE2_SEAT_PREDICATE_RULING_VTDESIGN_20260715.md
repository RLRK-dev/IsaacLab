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

---

## §12 design-owner verify verdict（実装 `70fc791359` の on-disk 照合、2026-07-16 04:0x）

⚓ producing commit で照合（HEAD==`70fc791359`）。数値計器ゆえ code 照合 + synthetic ground-truth（動画不要、最終捕捉は Rs 動画のまま）。

**判定 = ✅ PASS（設計に忠実、独立確認済、1 点は spec を上回る改良）。**

| 設計点 | 実装 cite | 判定 |
|---|---|---|
| interp helper（straddle 検出・線形補間・dy≡0） | `newton_route_env.py:1295-1304` | ✅ |
| S字 複数交差の選択 | `:1307` `lexsort((dx, where(in_band,0,1)))` = **in-band 優先 → min-dx** | ✅ ⭐**spec の pure-min-dx を上回る**（帯外 stray が帯内着座を隠すのを防ぐ、shelf は dx レグで拒否維持） |
| fail-closed（無交差） | `:1299-1300` None → `:1327` `(_SEAT_MISS_DX_M=9.0, 0.0)` ⇒ dx レグ(9≫3.5)+z レグ(0∉band) 二重 reject | ✅ |
| split leg・built-model bar | `:1315` `_seated_in_groove` = `dx≤SEAT_LAT_BAR_M(0.0035) ∧ SEAT_Z_LO(0.821)<z<SEAT_Z_HI(0.836)`、`route_env_config.py:154-158`（全て built model、T_GROOVE=3mm supersede） | ✅ |
| G3/G5 配線 | `:1550` `p3=c1_seated ∧ ph≥2` / `:1552` `p5=c2_seated`（`T_GROOVE` 参照消滅） | ✅ |
| c1_retained interp 化（defect#2） | `:1516` `c1_retained=c1_seated`（z-only 撤廃） | ✅ |
| c2_honest auto-follow | `:1517` `c2_honest=c2_seated`（`_seat_metrics` 経由） | ✅ |
| `_crossing_x_dev` 第4現場 | `:1341-1347` 真の補間（drop は fail-OPEN=妥当な非対称） | ✅ |
| 全 caller 2-tuple 化 | `:1447` / `:1510-1511` / `:1339`（3-tuple 期待の残存なし、外部 caller 無し） | ✅ |
| §16.2 C2 棚 blocker 同時 closure | 下記 S4 = code で REJECT 確認 | ✅ ⭐§9 の統合を code で実証 |

**独立 ground-truth（%12 の「S0-S5 PASS」を鵜呑みにせず、code を verbatim 複製して自分で実行、scratchpad）:**
```
S0 centred     dx=0.50mm z=829 seated=True   (node dy 無関係=量子化床消滅)
S1/S2 node-off dx=0.50mm z=829 seated=True   (旧: FN、seat_dist 3.73/7.34)
S3 wall-rest   dx=3.40mm z=829 seated=True   (旧 3mm bar なら誤 reject)
S4 shelf       dx=14.50mm z=829 seated=False (in-band z でも dx レグが棚を拒否=§16.2 閉)
S5 unseated    dx=20.00mm       seated=False
S字 in-band 優先: dx=3mm z=829 を選択=True / 無交差: fail-closed=False   → ALL PASS
```

### §12.1 ⚠ 非 blocker flag（3 件、%9/%12 へ）
1. **File B（frozen recount）未更新 = docstring 先走り**: `:1293/:1336/:1515` は「DoD-9a (live==frozen) holds」と**断言**するが、frozen 側 `p9_recount_strict_v2.flank_from_npz` は**まだ z-only**（%12 が %9 artifact ゆえ deferred）。⇒ 現状 live=interp-dx ≠ frozen=z-only ⇒ **DoD-9a は今 走れば FAIL**。**非 blocker**（DoD-9a は comment、runtime assert なし=確認済）だが docstring は「once File B updated (pending %9)」と限定すべき。⭐ **%9 の File B 更新は §11.4 の demo 自己テストでもある**（demo が interp-dx を通るか）。
2. **obs[58-61] semantics 変化**: `_seat_metrics` の戻りが (seat_dist,z_gap,lateral)→(dx,z_cross) ⇒ obs dim が別量を運ぶ。**訓練前ゆえ問題ないが、BC prior/demo が旧 obs semantics で記録されていれば train/demo mismatch を要確認**（%12 downstream）。
3. **minor**: `_SEAT_MISS_DX_M=9.0`（`:1279`）は機能上 reject で正しいが 9.0「m」は sloppy sentinel（nit）。

**⇒ RL env の interp fix = 設計忠実・独立確認済で PASS。gate ② は fix 実装済だが、正式 PASS は `/pre-check`（③）+ File B(%9) 整合後。最終捕捉 verdict は Rs 動画のまま。**

---

## §13 /pre-check FM3/FM4 の裁定（%12 上程、2026-07-16 04:2x）— **両方 TIGHTEN**

%12 の `/pre-check` が 2 件の MED design-boundary を surface。両方とも **reward-exploit vector** ⇒ 訓練前に閉じる（reward-design 規律: exploit は agent が学習する前に close）。⛔ %12 の記述でなく drop 述語・producer identity leg・RL env の seat-body 情報を on-disk 読了。

### §13.1 FM4（優先＝primary exploit）— **seat に routed-segment identity leg を足す**

⭐ **これは §18 の教訓が私自身の fix を刺した。** 私の interp fix は交差**位置**の identity（dy=0）を足したが、**どの segment の交差か**（routed か stray-loop か）の identity を足していない。`_seat_crossing`（`:1298-1307`）は **全 straddling segment** を探索し min-dx（in-band 優先）を採る ⇒ **routed segment が溝外 ＋ 非 routed loop が溝内**（Case B）だと **loop を seated と読む false-positive**。

- **exploit**: 偽 seated ⇒ G3/G5 が偽 latch（+5 each）⇒ ORDERED chain を偽進行 ⇒ +200 へ。**primary な success-signal 汚染。** RL 探索は +5 に gradient を持つ ⇒ 到達する。
- **producer は既にこれを閉じている**: `route_executor.py:3074-3078` は **特定 seat-body** の位置で測る（`_dy_seat_mm ≤ _y_win_mm` = seat-body の Y-window identity）。§9 の統合原則「producer の identity leg を全 seat site へ」の未適用分。
- **裁定 = TIGHTEN**: `_seat_crossing` の探索を **clip の expected routed seat-segment の node-index window に限定**する。RL env は identity 情報を持つ（`_pin_seat_seg` = C1 seat segment `:1721` / `_target_seg_indices` `:513`）。window 内の straddling segment のみ考慮 ⇒ window 外の stray loop は選べない。⇒ producer の seat-body identity の interp 版。
  - ⚠ 実装 note（%12）: C1 の window source = `_pin_seat_seg`。C2(G5) の expected segment source が readily available でなければ surface せよ（別 source or 下記 fallback）。
  - fallback（seat-body 追跡が無い場合）: 「交差 segment が **局所 Y-monotone な routed span**（≥K seg、loop は局所 Y 反転を持つ）の一部」= identity の heuristic。producer の seat-body identity が第一候補。
- ⚠ **quantization fix と両立**: window 内でも interp は dy=0 の dx を返す（量子化フリー維持）。window は stray を除くだけ。

### §13.2 FM3（secondary＝failure-mode incentive）— **escape guard を post-seat で fail-closed 化**

`_crossing_x_dev` の no-crossing→0.0（fail-open、`:1347`）は、cable が y=C1Y を跨がなくなる極端 escape で lateral-escape drop（`:1543`）を沈黙させる。%12: 偽成功は無し（seat gate が reject）だが escape guard が消える。

- **exploit math**: escape（no-crossing）⇒ lateral_dev=0 ⇒ drop せず ⇒ -0.01/step で timeout(900) まで継続 = 全 episode で −9.0。一方 -10 drop で終了 = −0.01·k − 10。**escape が常に安い**（−9.0 > −0.01k−10 ⇔ 0.01k > −1 = 恒真）⇒ agent は「失敗するなら full escape」を選好し得る。secondary（success 目的は +200≫ ゆえ支配的 gradient は seat へ、だが failure-mode を歪める）。
- **fail-open は pre-seat では正しい**（en-route、cable がまだ C1Y を跨がないのは正常）。**post-seat では誤り**（seated cable が跨がなくなった = escape）。
- **裁定 = TIGHTEN（phase-gate）**: lateral-escape drop を **G3 latched（C1-seat 済）で gate**。
  - pre-G3: lateral-escape drop 無効（fail-open 維持、en-route の spurious drop も防ぐ）。
  - post-G3: no-crossing **または** dx > `DROP_LATERAL_DEV_MAX_M` ⇒ escape ⇒ -10 drop。
  - ⇒ `_crossing_x_dev` は no-crossing を **None で expose** し、call site（`:1516`）が phase で判定（`if _g_latched[w,2]: escape = (dev is None) or |dev|>max`）。
  - ⚠ pin 整合: G3 後（さらに pin fire 後）cable は C1Y を跨ぐべき（pinned end が保持）⇒ post-G3 の no-crossing は fault。G3-latch gate で妥当。

### §13.3 順序・severity

| FM | severity | exploit | 裁定 | 訓練前必須? |
|---|---|---|---|---|
| **FM4** | **primary** | 偽 seat ⇒ G3/G5 偽 latch ⇒ +5 + chain 偽進行 | routed-segment identity window | ✅ **必須**（success 信号を直接汚染） |
| FM3 | secondary | full escape が -10 drop より安い | post-G3 fail-closed escape guard | ✅ 望ましい（failure-mode 歪み） |

**⇒ 両方 TIGHTEN。FM4 が優先（primary success-signal exploit）。小さく well-scoped ゆえ訓練 campaign 前に land、再 verify（interp helper の window 化 + drop の phase-gate を on-disk 照合）。⭐ /pre-check が gate の仕事をした — 非 conservative boundary を訓練前に捕捉。最終捕捉 verdict は Rs 動画のまま。**

### §13.4 FM4 の C2 identity source 裁定（%12 の C2 source 照会、2026-07-16 04:3x）

%12 が正しく突いた: C1 は `_pin_seat_seg`（`:1688/:1721`、録画の pin body ordinal、world-position で env body space に解決）があるが、**C2 は pin されないゆえ seat-body source が無い**（`_target_seg_indices` は R-lane regrasp target `:1418/:1518` で C2 seat でない、`_pin_seat_seg` は C1 のみ `:1671`）。⇒ (a) 既存 field 無し = 確認。

**⛔ (b) 固定 N-hop は却下**: C1→C2 arc-in-segments は route-geometry 依存（**D-5 stride 7 は task_config 千鳥 75mm 用**、route env は C1(0.35,0.150)→C2(0.40,0.000) = **150mm** ⇒ 別値）＋ **しごき pay-through で C1-to-C2 body 数が可変** ⇒ hardcode は fragile。

**✅ 裁定 = (b) を【contiguity で】正しくやる（新 field 不要、`_pin_seat_seg` から導出）:**

> **C2 seat crossing は、C1 seat body（`_pin_seat_seg`）から Y-monotone な routed span で連結されていなければならない。**

- 根拠: C1→C2 routed span は **y=0.150→0.000 の Y 単調減少**（S字は X 曲率で Y は単調、しごきは軸方向 slide で spatial-Y 単調維持）。**stray loop は C1 seat と単調連結しない**（loop は Y 反転を持つ）。
- 実装: crossing の node-index と `_pin_seat_seg` が挟む cable span が Y-monotone か（両 index 間の monotone-run 判定）。⇒ **固定 hop でなく「C1 seat から C2 crossing まで歩いて Y が単調か」**。pay-through-robust（正確な C2 body 不要、単調連結のみ）。curling tail は C1 側だけ見るので許容（C2 の先は自由）。
- **C1 側**: `_pin_seat_seg ± W` window（pinned = hard identity、producer :3074-3078 の seat-body identity と一致）。
- ⇒ **両 clip とも identity source は `_pin_seat_seg`**: C1 は直接 window、C2 は monotone-span 連結。G5(C2) も守られる（exploit は両 clip、%12 の懸念に対応）。
- ⚠ 実装 note（%12 → /pre-check 再検）: monotone 判定の tolerance/最小 run 長は、S字の Y 単調性を壊さない範囲で（S字は X 曲率ゆえ Y 単調は保たれるが、数値 wobble に小 tolerance）。edge（cable 端が C2 近傍で span が短い）は「available run で単調」に緩和。

**✅ FM3（phase-gate drop）は seat identity と独立 ⇒ 先行実装 CONCUR。**

---

## §S sweep-status 追記（2026-07-16、%12 開示 `c60d311f96` + manifest `I0A_SCOPE_MANIFEST_RSTECHLEAD_20260716.md` を受けて）

1. **status**: FM3/FM4 tighten の**実装が HEAD に landed（sweep 経由・批准ゼロ）** — `_seat_identity_segments` + `_seat_crossing(segment_indices=)` 拡張（FM4）/ `_c1_escape_after_seat` post-G3 fail-closed（FM3）+ pin-witness triple + (d2) plumbing fix。**gate ② = FAIL のまま不変**（landed ≠ verified — manifest disposition「intentional-keep + 非批准」に concur、revert 不能理由 [peer 実装の tree/HEAD 双方消失] も妥当）。
2. ⚠⚠ **p5 追加所見（manifest に無い、私の grep）: 巻込みコードは flag-gated でなく【HEAD で live】** — `newton_route_env.py:1395-1396`（seat predicate 本経路で identity+crossing を無条件使用）/ `:1627`（reward loop 内で `_c1_escape_after_seat` を無条件呼出）。⇒ 🔒 **run-hygiene 規則（owner chain PASS まで）**: HEAD で走る全 run の seat/G3+/escape 出力は**未批准 reward 意味論による採点** — banked-semantics を主張する run は (a) pre-sweep commit に pin するか (b) 未批准述語への暴露を artifact に loud 宣言する。⚠ I0-a の byte 一致は **physics 軌道**の一致であって reward/latch 経路の等価性ではない（FM3 が done/latch に触るなら rollout 挙動も変わり得る — /reward-design 再走の検査対象）。
3. **owner chain 不変**（LEDGER:57）: `/reward-design` 再走 → **p5 再 verify**（本 doc §identity/monotone 設計への conformance 照合 — 上記 tail の設計形が bar）→ `/pre-check`。**著者 pane 未特定は chain を block しない**（判定は on-disk content に対して行う — provenance と content は独立軸）。
4. spot（後方互換）: `:1422` の旧 2-arg 呼出は `segment_indices=None` default で互換 — 署名拡張自体の破壊は無し（詳細適合は chain で）。

---

## §S2 🔒 gate ② 再走 leg 2 = p5 再 verify verdict（2026-07-17、対象 = swept FM3/FM4 実装 + `GATE2_RERUN_FM34_RSTECHLEAD_20260717.md` 4 artifacts + `gate2_rerun_fm34_probe_result.json` + `test_route_reward_identity_guards.py`）

**方法**: 4 artifact doc 全読 → **swept code 本体の自読**（`newton_route_env.py:1297-1434`）→ 私の banked §13.1/§13.2/§13.4 + doc tail 設計形との条項照合 → probe json + unit test 実物 spot。

### verdict = **CONFORM — PASS〔p5 設計軸〕→ leg 3 = /pre-check へ進んでよい**

| banked 設計（bar） | 実装（自読） | 判定 |
|---|---|---|
| §13.1 C1 = routed-segment identity window（pinned = **hard identity**、producer seat-body 等価） | `:1352-1355` C1 → `(pin_seg−1, pin_seg)` = **「pin node を端点に持つ全 segment」= hard identity の最小・厳密形**（segment i は node (i,i+1) を所有 ⇒ endpoint 対称 — 私の ±W sketch の W を最小に取った適法形。canonical 実測 517/517 straddle={26,27}・divergence 0 が接地） | ✅ CONFORM（保守方向: 窓過小の故障 = false-negative であり exploit 側に開かない） |
| §13.1 fail-closed（global fallback 禁止） | `:1343-1345` `pin_seg None → ()` / 空集合 → `:1322` (None,None) → `:1402` MISS sentinel / `:1348` range guard raise | ✅ 3 経路とも実在 |
| §13.4 C2 = `_pin_seat_seg` からの **contiguity（歩いて Y 単調）**、固定 N-hop 却下、pay-through robust、edge =「available run で単調」 | `:1359-1378` walk-based（pin→候補 seg の実 span を diff 検査 — N-hop なし・edge 緩和は walk 構造に内在）、方向は実測 ys から導出（hardcode なし）、ambiguity（\|direction\|≤tol）→ () fail-closed | ✅ CONFORM |
| tolerance 実装 note（数値 wobble 用の小 tol） | `_SEAT_MONOTONE_TOL_M = 1e-6` `:1333`（「micron wobble であって物理 Y 反転でない」と comment 明示） | ✅ 意図一致。⚠ **watch → /pre-check**: 静止時の物理 micro-jitter が 1e-6 を超える境界例 = **false-negative 方向のみ**（exploit 側でない）— 非 blocking、leg 3 で watch 指定 |
| §13.2 FM3 = 既存 lateral-escape drop を **G3 latch で phase-gate + post-seat fail-closed** | `:1431-1434` pre-G3 → False（en-route 正常）/ post-G3 → crossing 消失 **or** \|x_dev\|>bar = escape。**bar = 既存 `DROP_LATERAL_DEV_MAX_M=0.060` `:412`（env-core `f6ee1443f5` 由来 — sweep 新設定数ではない）** | ✅ CONFORM |
| FM3 の done 接触（§S 検査対象） | `:1627-1636` `c1_escape` は既存 **dropped** 機構の disjunct → **dones 経由**（⛔ time_outs 不触 = timeouts 汚染禁止 遵守）。post-release 抑制（ERRATUM-3 banked）の継承も確認 — **抑制されても G6 `c1_retained` conjunct が post-release escape を success から排除 ⇒ exploit 再開なし** | ✅ 解消 |
| 両側被覆（判別できるテスト） | golden = **ACCEPT 側**（old==new、divergence 0 = tighten は正 route を 1 frame も奪わない）+ fixture = **REJECT 側**（stray loop MISS / no-crossing→post-G3 escape、unit test 4 本 + (d2) plumbing 回帰）| ✅ 構造適正 |

**probe json 裏書き**: onset f2544 = first_seated 同 frame（②初回 FAIL の量子化床 fix 保存）/ post-onset seated 1.0 / `old_semantics_seated_fraction=1.0`（divergence 0 の根拠）/ FM3 誤発火 0・\|x_dev\|max 1.025mm vs 60mm / bars = built-model 値一致（3.5/821/836）。

**付帯 2**: (i) 著者未特定 unit test = 内容検証の上 bank に concur（provenance 衛生 note は §S/manifest に残置、content 判定と独立）。(ii) §S の解除は **leg 3 /pre-check PASS 後**（本 verdict 単独では解除しない — owner chain 完了で）。

---

## §S3 🔒 leg 3 BLOCK への裁定 — I3/I4（2026-07-17、入力 = leg3 OUTCOME + `gate2_rerun_fm34_probe_v2_result.json`〔per-frame 訂正版、v1 lineage 保持 = 正〕）

### §S3.0 受領と自己訂正（9 件目）
- leg 3 BLOCK = **gate が仕事をした**（単一 ep 述語 clean のまま訓練展開面の blocker を訓練前捕捉 — §13.3 の再演）。I1 = banked (a)(b) の再発見 / I2 = (d) fold — concur。
- ⛔ **私の §S2「FM3 = CONFORM」row の scope を訂正（9 件目）**: あれは **§13.2 の字義**（phase-gate + fail-closed）への適合判定としては正しいが、**§13.1（identity）× §13.2（escape）の【合成】に seam があること**を見なかった。加重事由: 私は `:1422` の identity 非限定呼出を**自分で読み**「互換」と note して意味論を問わなかった — §17.3（読みながら論じ抜ける）と同型。合成 seam の捕捉は leg 3 の設計どおりの仕事（conformance-verify ≠ adversarial-verify — chain の分業は機能した）。probe v2 の **global x_dev = pre-onset 最大 50.61mm** が計器差の実像。

### §S3.1 🔒 I3 裁定 — **原則: guard と predicate は【同じ計器】を読む**（identity は測定の属性であって、述語ごとの選択肢ではない）
- **fix = FM3 の post-G3 escape を identity 済 metrics から導出**（%12 方向を批准・具体化）: `_c1_escape_after_seat` は `_crossing_x_dev`（global）を捨て、**`_c1_retention_m` の出力**（identity-restricted (dx, z)）を読む — `escape := (dx == _SEAT_MISS_DX_M) ∨ (dx > DROP_LATERAL_DEV_MAX_M)`。seat を成立させた計器と escape を判定する計器が**同一物**になる（fail-open も偽 escape も構造的に消える: identity 窓の外の crossing は guard に見えない）。
- **scope 限定**: obs[57]（`_crossing_x_dev`、H-drape 入力）の意味論は**本 fix で不変**（obs-space 変更 = 別 gate。drape 可視性は sensing であって reward gate でない）。`_crossing_x_dev` は obs 専用に残る — **reward/termination 系の消費者ゼロ**を fix 後 grep で assert。
- 検証 leg: leg 3 の両 fixture（fail-open stray-straddle / 偽 escape）を **REJECT unit test 化** + ACCEPT = canonical per-frame divergence 0 維持（identity dx ~0.9mm ≪ 60mm ゆえ挙動不変の見込み — それ自体を検証）。

### §S3.2 🔒 I4 裁定 — **C2 walk に【routed-side】識別を足す**（route-defined 方向定数、N-hop でも runtime 推定でもない）
- **fix = (a) routed 側限定を採用**: `_seat_identity_segments` の C2 walk を **pin node から見て route が C2 へ進む側（cable index の ± 方向）に限定**。方向 = **route 設計定数**（step-table/canonical が「どちらの端を C2 へ運ぶか」を固定している — body/hop 数と違い **1 bit で route-invariant**、§13.4 の「fragile hardcode 却下」に抵触しない）。符号は実装時に canonical 実測で接地し、**probe の positive control として「canonical の C2 crossing 側 == 定数」を assert**（drift すれば loud）。
- 単調 walk は側内で維持 ⇒ **単調 span は C2Y を高々 1 回しか跨がない**（±tol wobble を除く）ため leading-span leg は**不要に退化**（(b) は採らない — (a) が最小で完結）。feed 側 drape fixture = REJECT unit test 化。fail-closed 不変（routed 側に crossing 無し → MISS）。
- ⚠ **登録（今は動かさない）**: probe v2 の **C2 lateral margin 3.183mm vs bar 3.5mm** = 最薄 margin、「DR で掠る」= **DR-ON 日の設計 tension として MED carry**（bar は built-model 由来ゆえ動かさない — DR 振幅設計の側が この margin を予算に入れる。N-2 standing rule の DR instance と同じ日に扱う）。

### §S3.3 設計入力の fold — **pin = 既成着座の保持装置**（seat f2428 ≺ pin f2544、116 frame）
- (a)(b) per-episode lifecycle + (d) trigger の**前提に採用**: 着座は pin の**前に**成立する（pin が作るのではない）。⇒ (d) の幾何 capture trigger（`RLENV_PIN_DESIGN` §21.4 = STEP 7 押込中発火・pin-before-release）は**定量裏書きを得た**: capture 述語の true 窓は onset 前 ~116 frame 存在 = **trigger は knife-edge でなく幅のある窓で発火**。(a)(b) の reset 設計は「pin 解除 ⇒ seat 消滅」を仮定してはならない（解除後も幾何着座は残り得る — 判定は計器で）。cross-ref: RLENV_PIN_DESIGN §21.4/§21.11.1 に本 premise を注記（%12 bank 時に pointer 追加で可）。

### §S3.4 chain
実装（%12、I3+I4 fix + fixture 化）→ **p5 delta 再 verify**（§S3.1/S3.2 条項のみ — 全再走不要）→ `/pre-check` 再走。**§S 継続**（解除 = 再走 PASS 後）。gate ② 完了条件に (a)(b) 実装 + (d) containment 設計が入った点 = concur（I1/I2 の帰結）。

---

## §S3.5 🔒 p5 delta verify verdict — I3/I4 実装 = **CONFORM — PASS〔p5 設計軸、§S3.1/S3.2 条項のみ〕**（2026-07-17 05:2x、対象 = `dfbddb4777` + `GATE2_I3I4_IMPL_RSTECHLEAD_20260717.md` + `gate2_rerun_i3i4_probe_result.json` + `test_route_reward_identity_guards.py`）

**verify 方法（artifact-first + 独立再現 3 legs、p5 自走）:**
1. **unit tests 自走** = `env_isaaclab7` 直呼び、**main working tree で 10/10・exit 0**。⚠ **scope 訂正（§S3.5a、訂正 10 件目・pN 是正 2026-07-17 05:4x）**: exact-landed `dfbddb4777`（隔離 worktree・per-test 実行）では **9/10** — **§S3.1/S3.2 bar 該当 leg（I3a/I3b/I4-drape/I4-tail/sentinel/obs-only + FM3/FM4×2）= 9/9 PASS**。FAIL 1 本 = `test_pin_identity_fields_survive_recording_prepare`（V5 系 pre-existing invariant、bar 外）— **未 commit `route_executor.py` の pin-fields 保全差分**（`_prepare_recording` `pin_keys`、〜:4433-4459）に依存。
2. **probe 自走** = script を scratchpad 複製・出力先隔離で post-fix code に対し再実行 → **banked json と byte 一致（`ts` 除外・完全一致）**。banked artifact は非破壊（**主張は path 限定〔§S3.5a R2 訂正〕**: 当該 json の `git status --porcelain` = clean を確認 + 出力は scratchpad 隔離。旧文言「working tree clean 確認済」は撤回 — 同時点の repo は ambient dirty〔`route_executor.py` M / `route_env_config.py` foreign comment M ほか〕）。leg A 対称差 = {} / leg B escape post-onset 0 / leg C 81-cell feed 側 straddle 総数 0・seat_k hist {25:1,26:15,27:19,28:17,29:2,32:9,33:9,34:9} を replica で再現。（closure 注記 = §S3.5a (ii)。）
3. **V3 grep 自走** = `_crossing_x_dev` @ `newton_route_env.py` = def `:1426` + obs 呼出 `:1568`（+comment `:1565`）のみ — reward/termination 消費者ゼロ。standing 化 = `test_crossing_x_dev_is_obs_only`（`inspect.getsource` で `_compute_rewards_dones_batch` + `_c1_escape_after_seat` の source に参照ゼロを常時 assert）。（%12 doc の「obs :1566」は comment 行 — 実呼出は `:1568`、cosmetic のみ・非 blocker。）

**§S3.1（I3）条項別:**
| bar | 判定 | 根拠 |
|---|---|---|
| escape は `_c1_retention_m`/`_seat_metrics(C1)` の identity dx を読む | ✅ CONFORM（bar より強い） | `:1616` `dx_c1 = _seat_metrics(cable_pos, _C1_XY)` → seat 述語 `:1618` と**同一の局所変数**が `:1645` で guard に渡る = 同じ計器どころか**同じ測定値・同 step** |
| 式 `(dx==MISS) ∨ (dx>bar)` | ✅ CONFORM 逐語 | `:1450`。abs() 不要は正当（`_seat_metrics` dx = \|·\| 非負、`:1398` docstring）。MISS は定数 verbatim 伝播ゆえ `==` 安全。sentinel>bar 網 = static test 化 |
| obs[57] 意味論 不変 | ✅ CONFORM | `:1568-1569` 同一計算・None→0.0 不変（comment のみ変更） |
| `_crossing_x_dev` 消費者ゼロ grep assert | ✅ CONFORM+standing 化 | 上記 leg 3 |
| fixture 2 本 REJECT test + canonical divergence 0 | ✅ CONFORM | I3a/I3b test（fixture 幾何を p5 自読で検証: I3a = identity 窓 {26,27} 無交差+in-bar stray seg5 / I3b = identity dx=0・z 帯外+窓外 70mm in-band stray〔CC2-9 制約遵守〕）+ leg A 厳密一致 + **V6 3/3 反転記録**（committed script+output、旧 signature ゆえ post-fix で loud に壊れる = 意図） |

z-scope 明文化（escape = lateral+crossing-loss のみ、z 逸脱は G6 z-band が封じる）= 裁定の機構節 scope と一致（docstring `:1436-1448` に契約化）— concur。

**§S3.2（I4）条項別:**
| bar | 判定 | 根拠 |
|---|---|---|
| C2 walk を routed 側（index ±）に限定 | ✅ CONFORM | `:1368-1371` seg_range 分割 — clean partition（∪=全 seg・∩=∅、境界 seg pin−1/pin の帰属正しい）。退化（pin=端）→ 空 range → 既存 fail-closed () |
| 方向 = route 設計定数 1 bit | ✅ CONFORM（bar 超過） | `route_env_config.py:158` `ROUTE_C2_SIDE_FROM_PIN=-1` + **構造導出 2 anchor**（build dir Y-ascending node0=低Y端 + C2Y<C1Y ⇒ side=sign(C2Y−C1Y)）+ 実測接地（313 frame seg16<pin27 / 81-cell）+ 将来 route 再接地義務 + N-clip per-hop scope 注記を comment に格納 |
| positive control「canonical 側==定数」assert | ✅ CONFORM（bar 超過） | leg C = canonical だけでなく **81/81 cell**・**非循環**（raw npz の straddle 直接計数 — 制限計器を経由しない）+ 定数==−1 assert。replica 再現済 |
| leading-span leg 不採用 | ✅ CONFORM | diff に不在 |
| feed-drape REJECT test | ✅ CONFORM+追加 | drape test + **tail-return fixture**（16/81 cell 実在形状 — walk の load-bearing 性を将来編集から保護、CC3-R3）= 有益な超過 |
| fail-closed 不変 | ✅ CONFORM | walk 本体無変更・空候補→MISS 経路保存 |
| MED carry（3.183 vs 3.5mm）— bar 不動 | ✅ 確認 | diff に閾値変更なし・leg A で 3.183 再現 |

**要判断 ① — obs[49]/[58]/[59] への I4 継承 = 🔒 RATIFY（継承は許容でなく【要請】）:**
- 供給源 on-disk 確認: `:1549-1552` `_seat_metrics(cable_pos, active_xy)` → [49]=hypot(dx,zgap) / [58]=zgap / [59]=dx。post-G4 active clip = C2 ⇒ I4 が流入する。
- §S3.1 の原則そのもの（identity は**測定の属性**）: obs が reward と**別の identity** を読めば、I3 で閉じた seam を reward↔obs 間に再生産する（policy が「reward が決して与えない seat」を観測する = reward-obs 整合性欠陥）。§11 c2_honest auto-follow 前例の範囲内。
- **obs-space 変更ではない**: 次元・layout・単位・契約は不変（§S3.1 の scope 限定は「obs[57] の計器 swap をしない」であり、共有計器の修理が consumer に伝播する事を禁じない）。[57] global 不変・[60:62] C1 側は I4 無関係（C1 identity 無変更）・I3 は測定を変えない — 継承先列挙 {49,58,59} は**完全かつ過不足なし**。
- 記録済データでの divergence 0 は legs A+C で**証明**（replica 再現）。runtime で値が変わり得るのは「旧 code が feed-drape を誤 credit した状態」のみ = 閉じるべき欠陥そのもの。leg D として loud に宣言した記録規律 = concur。

**要判断 ② — ingest 時 runtime assert（frame-0 node-0 Y < pin Y）不採用 = 🔒 DECLINE を批准（本 chunk）+ (a)(b) chunk へ optional 候補として登録:**
- 残余 hole = 「build 方向の code 変更 + probe 未再走」の合成のみ（node index は静的 — DR/INIT_XY_NOISE は並びを変えない）。route 変更側は定数 comment の再接地義務 + chain 内 probe が覆う ⇒ 追加被覆は LOW。
- 配置の正しさ: この検証の自然な家は **reset 時・pin 配線面 = (a)(b) lifecycle chunk**（per-world witness と同居）。今入れるのは他 chunk の面への scope creep（chunk 分離規律の鏡像）。
- §S3.2 の字義に反しない（assert は前提検証であり runtime 推定でない）ゆえ**恒久却下ではなく繰延**: (a)(b) 設計時に「pin 配線時 1 回の `ys[0] < ys[pin_seg]` fail-loud」を候補 leg として審査（非拘束・その場で採否）。

**付帯:** (i) RLENV_PIN_DESIGN への pointer 2 件（§21.4 定量裏書き / §21.11.1 identity-persistence coupling）= §S3.3 事前授権の範囲内・内容忠実 — ACCEPT（coupling 側は (a)(b) verify で再照合する）。(ii) `route_env_config.py` の未 stage 外来 hunk 2 件 = p5 自読で **comment-only を確認**（代入値 60/61/slice 不変）・内容は on-disk env code `:1573-1577` と事実整合（stale comment の修正）— 挙動非影響、provenance 衛生は manifest 側の記録で足りる。

**chain 位置〔§S3.5a R1 訂正済〕**: 本 verdict で §S3.4 の「p5 delta verify」leg（**design 軸**）= **閉**（維持）。ただし次段は /pre-check 直行ではない — **現行 pN/p6 面（LEDGER `bf5feef0bd`）: `/pre-check` 再走 = FENCE 中**（解除条件 = correction bank + exact closure probe 再生成 + pN readback）。順序 = **evidence closure（owner chain）→ pN readback → FENCE 解除 → `/pre-check` 再走**。**§S 継続**（解除 = 再走 PASS 後 — 不変）。gate ② 完了にはさらに (a)(b) 実装 + (d) containment 設計（I1/I2 帰結）。本 verdict は p5 設計軸 conformance であり、adversarial 軸は FENCE 解除後の /pre-check 再走が担う（軸別 tri-state: design=CONFORM banked ／ evidence/bank=pN HOLD ／ adversarial=FENCE 待ち）。

---

## §S3.5a 🔒 訂正 10 件目 + evidence-scope 裁定（2026-07-17 05:4x、trigger = pN 独立検証是正）

**pN 指摘 3 点 — 全て p5 自身で on-disk 再現してから記載:**
1. **再現 ✅**: 隔離 worktree @ `dfbddb4777` + `env_isaaclab7` 直呼び・per-test driver（fail-fast なし）→ **9/10**。FAIL = `test_pin_identity_fields_survive_recording_prepare`、message も pN 報告と一致（"recording preparation dropped pin_active"）。
2. **機構 ✅**: `git status` = `route_executor.py` **M（未 commit）**。`_prepare_recording` の pin-fields 保全（`pin_keys = ("pin_active","pin_eqid","pinned_body")` + all-or-none 契約、〜:4433-4459）は **working tree のみ** — `dfbddb4777` 収録版は 3 key を drop する。
3. **入力 ✅**: probe 入力 `w0e_81rerun_snapdown_0537/` = **tracked 0 / on-disk 82** = 全 untracked。input hash / source closure 未記録。

**私の誤り（訂正 10 件目）**: §S3.5 の「10/10 独立再現」は **working tree での実測を landed 状態の再現として記載** — 測定値は真だが **code-state scope の誤帰属**（records-must-match-fact）。原因: 実装 diff の対象 3 file の未 commit 差分は確認したが、**test の import+call 閉包**（test は `rex._prepare_recording` を呼ぶ — `route_executor` が閉包に入る）を確認しなかった。**教訓（一般形）: test-run claim の code-state surface は、実装 diff の scope でなく test の import+call 閉包が定義する**（verify-on-disk-at-the-producing-commit の閉包版）。加えて元実行は `main()`（fail-fast 逐次）で per-test 分解を欠いた。

**verdict への影響 = CONFORM — PASS〔p5 設計軸〕は維持（根拠を差し替えて再接地）:**
- §S3.1/S3.2 の bar 該当 leg = **exact-landed 9/9 PASS（p5 worktree 自走）** + V6 3/3 = parent commit で %12 記録（committed script+output）。
- probe replica の実行測定経路 = `newton_route_env`（`git diff dfbddb4777` = ∅ = 収録 byte 同一）+ `route_env_config` 定数（未 commit 差分 = comment-only 確認済）のみ・`route_executor` **非依存**（`:612`/`:748` は関数内 import・probe 非経由）⇒ 挙動として landed 等価（**分析** — 完全な source closure 記録ではない）。
- FAIL した recording-fields test は **§S3.1/S3.2 の bar ではない**（V5 pre-existing invariant）⇒ 条項別表は不変。

**evidence-package 裁定 — pN HOLD に CONCUR（evidence 軸 = pN/owner chain 管轄、p5 verdict は design 軸のみ）:**
- (i) **新規 finding → owner chain**: 「recording-fields invariant（pin witness 3 key の `_prepare_recording` 生存）は **landed tree で FALSE**」。pin witness は (a)(b) lifecycle + C1 identity 配線の前提 ⇒ **`route_executor.py` pin-fields 差分の land = (a)(b) chunk の precondition**（producer-unbanked（Rs 待ち）系との関係特定含め %12 判断 — p5 は commit 権限外）。land 後、exact-landed 10/10 再走で invariant 回復を確認。
- (ii) probe evidence closure: 81-grid untracked + input hash / source closure 未記録 ⇒ p5 の byte 一致は「**同一 on-disk 入力への計器等価・決定性**」の証明に**とどまる**（入力 provenance の閉包でない）。closure 化（hash manifest / tracked 化判断 / closure 記録）= owner chain。
- **bank 要請（=%12）**: §S3.5 は本 §S3.5a と不可分で bank し、evidence package = **pN HOLD 中**の旨を併記すること。（注: §S3.5 本体は `2298cb0d27` で bank 済と事後判明 — 本 §S3.5a + leg1/leg2/chain 訂正が dirty delta。）

**pN readback fixes（2026-07-17 05:5x 受領、R1/R2 — 適用済）:**
- **R1** = §S3.5「chain 位置」を FENCE 整合へ訂正。旧文（「次 = /pre-check 再走」「解除 = 再走 PASS 後」のみ）は、本 §S3.5a で HOLD を書いた同 arc で chain 行を更新し残した**内部矛盾**であり、かつ現行 pN/p6 面（LEDGER `bf5feef0bd`: /pre-check = FENCE〔correction bank + exact closure probe 再生成 + pN readback まで〕）を飛び越えていた。訂正後 = evidence closure → pN readback → FENCE 解除 → /pre-check。design leg 閉は維持。
- **R2** = §S3.5 probe leg の「working tree clean 確認済」を撤回し **path 限定主張**へ（実測は banked json path の `git status` clean のみ — 同時点の repo は `route_executor.py` M 等で ambient dirty）。**#10 と同 class〔claim scope > measurement scope〕の残存 1 件を pN readback が捕捉** — 訂正番号は増やさず #10 の cleanup に帰属。
- 検証: R1 の fence 文言は LEDGER の `bf5feef0bd` word-diff を自読して cite（message 転記でない）。R2 は自分の実測記録（path 限定 status check）との照合で確定。

---

## §S4 🔒 §S 解除裁定 — **GRANT〔scoped〕**: swept 意味論 = 批准（premise-set 条件付き・committed HEAD 限定）／ reward-valid・training-ready 禁止は §S と独立に存続（2026-07-17 06:2x、入力 = leg 3 再走 OUTCOME `6ec126b1bb`〔Q1-Q3 + issues 表、p5 全読〕）

### §S4.1 判定の枠 — §S の主題と、解除条件の解釈裁定
- §S（:333）が名指した hazard = **「HEAD で走る run の seat/G3+/escape 出力が【未批准の reward 意味論】で採点される」**（run 記録の妥当性 hazard）。訓練 readiness は §S の主題ではない（それは I1/I2 系 = gate② 完了条件 + pN の reward-valid/training-ready 禁止が別軸で保持）。
- §S2 付帯 2(ii)「解除 = leg 3 /pre-check PASS 後」の解釈: leg 3 再走 verdict は主題を**分割**した — **意味論 sub-claim = 批准可能（verifier 明言・Q3）** ／ BLOCK は**訓練批准**（別主題、要因 = carry 済 I1/I2 + 新規 ISSUE2 のみ・**I3/I4 欠陥ゼロ**）。⇒ **「PASS」は §S の主題への PASS と読む**。反対読み（訓練批准まで §S 存続）は、§S が名指していない hazard に §S を人質へ取らせ、chain が意図的に分離した軸（§13.3 の severity 分離・軸別 tri-state）を再混同する。**本項で §S2 付帯 2(ii) の文言を supersede（解釈明示）。**

### §S4.2 批准内容（Q3 逐語を採択）+ premise 執行の p5 自読確認
- 批准命題: **「committed HEAD の seat/latch/escape 述語意味論は、【有効な per-episode pin identity + fired pin + reset 時 eq clear】の前提下で、単一 episode 上 banked correctness と等しい」**（前提の supply = (a)(b) 実装、I1 disposition で宣言済）。
- **premise の fail-closed 執行は機構実在（p5 自読、本裁定の load-bearing leg）**:
  - identity 無（pin 発火せず／wire されず）→ `_pin_seat_seg=None` → `_seat_identity_segments` `()` → MISS → G3 非 latch → ordered chain で G4+ 到達不能・escape は pre-G3 恒 False（§S2 row 2 の 3 経路 + `:1690-1699` ordered latch）。**silent 誤採点の状態が存在しない。**
  - `route_c1_pin=True` × pin-fields 無 recording → **`ValueError` raise**（`newton_route_env.py:1782-1786`「route_c1_pin=True but prepared recording dropped pin witness fields」）+ partial witness → raise（`:649-657` all-or-none 契約）。**loud 死、採点に到達しない。**（committed `route_executor._prepare_recording` は fields を drop する = §S3.5a B1 — ゆえに committed HEAD では True 側は必ずこの fence に当たる。）

### §S4.3 scope 限定（⛔ 3 本）
1. **committed HEAD（fail-closed fence 実在）に限る** — dirty tree は `route_executor.py` pin-fields 差分が fence を **bypass**（ISSUE2 の順序 hazard、leg 3 再走 :96）ため本批准の外。**現 dirty tree からの訓練起動禁止に concur。** committed-HEAD lineage 外の code 状態で走る run は従前どおり loud 宣言義務。
2. **単一 episode 意味論に限る** — multi-episode（lifecycle）妥当性は (a)(b) の供給物。**reward-valid / training-ready 禁止は §S と独立の carry として存続**（(a)(b) + bundle land + (d) まで、pN 規律のまま）。gate② = 完了ではない（完了条件不変）。
3. **ISSUE2 bundle 裁定に concur**: route_executor pin-fields land は「(a)(b) より先」ではなく **(a)(b) と同一 landing に bundle（先行 land 禁止）** — §S3.5a (i)/B1 行の「land = precondition」の**先行 land 読みを supersede**（land はなお必要、順序が変わった: bundle → land 後 exact-landed 10/10 再走）。

### §S4.4 効果
- **§S run-hygiene 規則（:333）= 解除**: committed-HEAD lineage 上の将来 run に sec_S_exposure 宣言・pre-sweep pin 義務は不要。歴史 artifact の宣言は遡及編集しない（記録は当時の事実）。
- 解除の bank・LEDGER/地図 flip = %12/p6（owner chain）。本裁定は §S の定義者鍵のみを回す — evidence/adversarial 軸の pN 規律には触れない。

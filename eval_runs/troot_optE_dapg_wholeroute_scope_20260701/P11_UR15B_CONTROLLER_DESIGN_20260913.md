# p11 — UR15-B controller 設計（既存 control class の B 側導出）

**[VERDICT: FAIL — cycle 1 (2026-09-13). pre-check = BLOCK. verdict = `P11_L3_FIVEWAY_VERDICT_UR15B_CONTROLLER_20260913.md`. ⛔ 本版は着地候補でない — v2 は次 commit]**

**Author** w2:p11 ARM-CONTROL-DESIGN · **Written** 2026-09-13 08:20:18 JST · Naming per m-p18-256: **Rs1 = 人間 / Rs2 = p4**.
**依頼** = m-p18-280 §3（2026-08-10 09:56）「p11 — accept or refuse the design court, then the design」。**Rs1 逐語①**「**UR15-Bようのコントローラも作成**」（custody `1d9974face` kickoff 09:51 節・DDR #68 `00-DESIGN-STATUS-LEDGER.md:172`）。
⚠ 本書の数値は **全て本書内の query 付き値**。行番号は **必ず rev を伴う**（rev 無しの行は指し手でない — 本書執筆中も共有 tree の wired は dirty で行が動く、§2-c）。
⛔ **本書は run を要求せず、含意もしない。** 実装 = p0 / 検証 = pZ / まとめ = p4。04-Specs 不触。§0 不変前提（RS71 `:27-:29`）を変えない。
⚠ **34 日の遅延**: 本 court word は 08-10 10:0x に草稿まで書かれ **送信されなかった**（session 中断・scratchpad 消失）。chain はその間 p11 で止まっていた（p4 kickoff 09-05 §5・`HANDOFF.md:18`・p18 台帳 `:46800`）。責は当卓。

---

## 0. COURT WORD = ACCEPT

- 根拠 = role brief `ARM_CONTROL_DESIGN_ROLE_BRIEF_p11_20260721.md` @ `2887037c9f` `:8`「腕制御の設計を作り、所管する。設計だけ」／`:62`「**どう駆動するか＝あなた**／どの腕を使うか＝p5」。UR15-B をどう駆動するかは前者。
- 読み = p4 kickoff 09:51 節 §1・DDR #68 と同じ: **既存 class（per-arm 6D DLS ＋ position servo）の B 側導出。新方式でない。** class が B を表現できない地点に達したら **STOP-and-report**（method swap でない）。
- 体制 = p11 設計 → p0 実装 → pZ 検証 → p4 まとめ（DDR #68 末尾）。

## 1. 結論（3 行）

1. **UR15-B の controller は、既存 class を B に載せたもので既に在る。** B 専用の制御則・関節符号 map・home pose は**要らない**。要るのは「側に依る量を B で測る」ことで、現行 code は **2 箇所（同一計器内）を除き**そうなっている（§4 表）。
2. **実装変更 = 1 件（D4）**: 姿勢 cap 計器 `attitude_tilt_deg` / `vertical_cap_deg` が L 固定 → 側別（受け取る姿勢で評価・cap = 両側の min）。**制御行の変更 0。**
3. **鏡像の主張は関節空間**（q_B = q_A・identity）で立て、**負の対照**（reference の R 式）を持つ。姿勢 menu の側別符号（p5 −167）は y=0 面の鏡像で、**腕対の鏡像（x=0 面）とは別の frame** — それは task 側の選択であって鏡像主張の一部ではない（Rs 逐語 wired `:904`「the hands do not have to mirror each other, they have to clamp」）。

## 2. 接地（anchor set・全て当卓が本 session で直読）

- (a) **LEDGER**: DDR #68 `:172`（UR15-B premise・controller court = p11）／#69 `:173`（条件つき run・未発火・条件 = UR15-B ＋ controller ＋ legs）／#66 `:170`（wired run 常設規則）／row 60（(d) arc）。#70 `:174`（trailer = A）。
- (b) **RS71** `:27-:29` §0#5（IK のみ・kinematic trick 禁止・唯一例外 = clip pin）— 本設計は触れない。
- (c) **測定対象の pin**:
  | object | rev | 行数 / 補足 |
  |---|---|---|
  | `p4_ur15_sim_20260727/ur15_steps_wired.py` | **`22feba17a6`**（blob `75eefef4e27e`・sha256 `57de8c3ec7ed0262…`） | 4,022 行。⚠ 共有 tree は **dirty**（+1387/−813・mtime 2026-09-07 23:15・author は git に無い）。AST 比較（import alias 順を正規化）: top-level 292/292・差 4 key（`_interleave_report`／import 分割／print の f-string 分割／STEPS loop 内の同種）・**制御 13 def は全て同一**（`solve_ik pose_menu _rdes attitude_tilt_deg vertical_cap_deg aim_slot_at aim_both _measure_axfix seat_offset slot_centre ik pinch pinch_jac`）。陽性対照 = literal 1 個反転で不一致検出。⇒ **本書は blob で pin・WIP は不触・不引用**。 |
  | `ur15_cell_spec.py` | `0f6b4a733e` | 1,395 行（C-2 の 4 編集着地版） |
  | `ur15_base_mirrored.xml`（`<mujoco model="UR15-B">`） | `6a542f45dd` | 正式化 `c737f6974e` ＋ header 修正 |
  | `ur15_base.xml` | `bf0235cfd8` | stock |
  | `_ur15_2f85_koshape_actuated_mirrored.xml` | `b7a5e39ecf` | 鏡像コ hand |
  | `thread_isaac_lab/assets/ur5e_robotiq/robotiq_2f85/_ur15_2f85_koshape_actuated.xml` | HEAD（tracked） | stock hand |
  | `UR15_MIRROR_ACCEPTANCE_20260729.txt` | `38678f5946` | 147 行 |
  | `HOME_POSE_SYMMETRY_20260729.txt` | `dfb8dc1bde` | 78 行 |
  | `PZ_ARM_MIRROR_LEG_RESULT_20260810.md` | `cf0a14cea3` | 47 行（独立レグ） |
  | `PZ_MIRROR_LEG_PREREG_20260810.md` | `9d118cbf93` | 35 行 |

## 3. 生きている controller（F1）— B に載っているのはこれ

- **`solve_ik(t, tgt, …)`** wired `:2036`（`22feba17a6`）: scratch `MjData` 上の 6D damped-least-squares。誤差 `e = [ep; 0.6·er]`・`ep = tgt − pinch(t)`・**`er = rotvec((RD @ AXFIX[t]) @ Rtᵀ)`**（`:2115`）・`J = [0.5(Jp_pad0+Jp_pad1); 0.6·Jr]`・`dq = 0.5·Jᵀ(JJᵀ + 0.05²I)⁻¹e`・`|dq| ≤ 0.15 rad/iter`・300 iter・収束 `pe ≤ 0.002 m`・`re ≤ re_max`（既定 0.05／aim 0.02／per-step 0.30）。候補は `_wrap`・衝突・far-arm clearance で落とし `near` 最近を返す。**側は `QADR[t] VADR[t] PAD[t] TOOLB[t] AXFIX[t]` で入る — 側固有の分岐は無い。**
- 呼び手 = `aim_slot_at` `:854`（grasp 姿勢）・START 解・STEP loop。**`ik()` `:646` は死んでいる**: closed query `\bik\(`（case-sensitive・file 全体 4,022 行）= **1 hit = def 自身**（rc=0）／陽性対照 `\bpinch\(` = 20。⛔ **p0 は B controller を `ik()` に書かない**（走らない code に書くことになる）。
- servo = 関節ごとの position actuator `AIDX[t]`（gain は関節名で決まり側に依らない）・home は `d.ctrl[AIDX[t]] = HOME_POSE` を **両側 loop**（`:2507`・servo 目標のみ・PD 実移動 = 08-09 確認の 3 要件どおり）。

## 4. 側に依る量の表（設計の本体）— 「B で測られているか」

| 量 | 現行 | B での正しさの根拠（測定・全て file 内の値） | 設計 |
|---|---|---|---|
| **関節指令 map A→B** | 同じ q を両腕へ（HOME_POSE 1 本・START/STEP は側別に解く） | acceptance `:65` test leg（鏡像腕を右 mount・**左の関節値**で駆動 → reference の**右**位置）**48/48・worst 0.0076 mm / bar 1.0 mm**／negative `:121`（R 式を与える）**0/48・worst 1357.5480 mm**／pZ B2 独立 FK 0.0013–0.0076 mm・B1 reference 自体が exact mirror（0.0000 mm × 24）・B3 Hausdorff 0 × 7 mesh・C2 正式化 = naming-only | **D1 = identity。** 符号 vector を**置かない**。reference の R 式（pZ 実測: R = −L for shoulder/forearm/wrist_2/wrist_3・**R = −L + π for upper_arm/wrist_1**）は**非鏡像機の経路**であって、UR15-B に与えると 0/48 = **負の対照**。 |
| joint limits | `LIM` 共有 `:1250`（URDF 値・cell_spec `:100`） | 6 関節とも対称（mirrored `:38-58` `axis="-0 -0 -1"` 反転・range 同一／acceptance limit leg 自身が「CANNOT fail on these assets」と宣言） | **D6 共有維持**。standing 条件: 非対称 range の asset が来たら `LIM` を側別に。 |
| AXFIX（閉じ軸・接近軸の tool 内表現） | 側ごと測定 `_measure_axfix` `:594-611`・`AXFIX` `:616`（共通 seed 姿勢） | det(AXFIX) = +1.0000 両側／**pad 名が側で入れ替わる**（HOME_POSE_SYMMETRY §5「THE OTHER NAME (the pads swap sides)」・closing axis OPPOSED・approach aligned） | **D2 測定維持。式で鏡像化しない**（式は pad 名の入替を落とす）。seed 姿勢は同じ q = 鏡像配置で整合。 |
| 姿勢指令 (yaw, roll) | 側別符号 `sgn = −1 (L) / +1 (R)` を **yaw と roll の両方**に（`pose_menu` `:2027-2029`・`solve_ik` `:2055`・`:2061`・p5 −167） | `_rdes` `:1329` = Rz(yaw+π/2)·Ry(roll)・基準 `R_DES` cell_spec `:489-491`（列 = (0,1,0),(−1,0,0),(0,0,1)）。収束時 tool_R = RD·AXFIX ⇒ **world の把持三軸 = RD の列**（側に依らず）。⇒ 側別符号は **y=0 面の鏡像**（worked example yaw=0.3/roll=0.6: 接近列 (−0.1668,−0.5394,+0.8253) 対 (−0.1668,+0.5394,+0.8253)）。腕対は **x=0 面の鏡像**（§1 link frames mirror error 0.0000 mm・§5 pads x = ∓0.0631）。§5 表は yaw≠0 で「⛔ NO (0.5910)」＝ x 鏡像でないことを**測っており**「menu が鏡像であるべきかは設計問題」と当 court に置く。 | **D3 不変**。Rs 逐語 `:904`「hands do not have to mirror … have to clamp」＋ p5 −167 を保持。**frame の違いを明記**し、pZ の鏡像述語は**関節空間**に置く（§7）。⚠ 上の worked example は **code からの算術で測定でない**（§9）。 |
| 姿勢 cap 計器 | `attitude_tilt_deg` `:1263`／`vertical_cap_deg` `:1288` が **L 固定**（`TOOLB["L"]` `:1277`・`AXFIX["L"]` `:1283`）・消費 = vertical check print・cell_spec `vertical_tol_deg` `:768`/`:829` | closed query `(AXFIX|QADR|VADR|TOOLB|PAD|GIDX|AIDX|qt)\["(L|R)"\]`（case-sensitive・4,022 行・blob）= **5 hit**: `:1277` `:1283`（L のみ）／`:2656`+`:2659`（L→R の対）／`:3527`（両側 dict）。陽性対照 = 同名の `[t]` 形 87 hit（08-10 実測・同 pattern）。⇒ **L-only は 2・同一計器内**。さらに計器は menu の**生の** (yaw, roll) で L を評価するが、L が実際に受けるのは (−yaw, −roll)（`:2061`）。 | **D4 = 唯一の code 変更**（§5）。 |
| gripper 指令 | `d.ctrl[GIDX[t]]` 0..255 共有 | mirrored hand の default joint axis `1 -0 -0`（`:31`）≡ stock `1 0 0`（`:27`）／actuator `fingers_actuator` tendon=split ctrlrange 0..255 同一（`:202` vs `:198`）／192/192 鏡像 acceptance（`b7a5e39ecf`） | **D5 不変。** |
| home | `HOME_POSE` 1 本（cell_spec `:455`）・servo `:2507` | §1 link frames mirror error **0.0000 mm**（6 link）／§2-§3 mast 距離 両側同値（60.10/90.07/113.77/130.96/131.03/164.53 mm） | **D6 不変。** |
| dynamics | kp/kv は関節名で決まり共有・asset の inertial は text 上 mirror（pos x 反転・quat y,z 反転・mass/diaginertia 同一） | position test は dynamics を**見ない**（acceptance 末尾・pZ B4）。動的な鏡像 leg は存在しない。 | **D7 = static field 等式 leg（§7 R2）＋ 認可 run 時の L/R 追従誤差比較（報告のみ・gate でない）。** |

## 5. D4 の仕様（p0 向け・受入は結果形）

- **対象**: `attitude_tilt_deg(yaw, roll)` wired `:1263-1286` と `vertical_cap_deg()` `:1288-1310`（@ `22feba17a6`・行は照合注記・**内容で特定**: `v = slot_centre("L") - pinch("L")` を含む関数と、`_spec.GRASP_ATTITUDES` を走査する関数）。
- **変更（結果形）**:
  1. `attitude_tilt_deg(t, yaw, roll)`: `v = slot_centre(t) − pinch(t)`、`v_tool = xmat[TOOLB[t]]ᵀ v`、`world = (_rdes(yaw, roll) @ AXFIX[t]) @ v_tool`。転置注記（`:1279-1282`）は不変。
  2. `vertical_cap_deg()`: **両側**で、その側が**実際に受ける**姿勢 `(sgn_t·yaw, sgn_t·roll)`（`sgn_t` は `pose_menu` `:2027` と同じ定義を 1 箇所に置いて共有）で tilt を評価。`cap = min over t ∈ SIDES of (その側の最小の非ゼロ tilt)`。upright/tilted の二重検査（`:1298-1310` の「dead instrument は自分の 0 を再現する」）も両側で。
  3. 印字（`:2886` 相当の vertical check 行）に **側ごとの cap 2 値**と採用した min を出す。
- **不変**: `solve_ik`／`pose_menu`／`_rdes`／`aim_*`／servo／`R_DES`／`GRASP_ATTITUDES`／`LIM`／`AXFIX`。**制御行の変更 0。** 2 file 以外の変更 0。cell_spec `vertical_tol_deg` の呼び出し形は不変（cap は引数）。
- **期待（導出・測定で決める）**: 世界 z 成分 = −v_c·sinρ + v_a·cosρ ゆえ tilt は **yaw に依らず** roll と (v_c, v_a) だけで決まる。pad 入替で v_c^B = −v_c^L、符号で ρ_L = −ρ_R ⇒ **両腕の実 tilt は entry ごとに一致**。⇒ D4 後の cap は数値上 **不変か、v_c ≠ 0 なら現行と異なる**（現行は L を +ρ で評価 = 実際は B の姿勢）。どちらでも D4 は正しい — 測定が決めるのは「なぜ同じか」の記述。⚠ これは算術であって測定でない（§9）。

## 6. `/diffik-trajectory` 出力（役割 brief `:59` の設計ゲート・本設計は軌道を変えないことの記録）

```
## 軌道設計: UR15-B controller（既存 class の B 側導出）
### 移動量
solve_ik は scratch 上の反復解（軌道でない）: |dq| ≤ 0.15 rad/iter・300 iter・収束 pe ≤ 0.002 m。実軌道 = ramp（RAMP = START_RAMP_S / timestep）で q を線形に servo 目標へ → 本設計は変えない（D1-D7 のいずれも軌道・step size・補間を触らない）。
### 補間方式
Position servo への線形 ramp（現行・不変）。one-shot 目標なし。指: tendon actuator 0..255（不変）。
### DLS確認
λ = 0.05（`:2118`）・joint clamp = 0.15 rad/iter・gain 0.5・回転重み 0.6 — 側に依らない scalar ⇒ B でも同値（不変）。
### THREAD固有リスク
(1) 側固有の分岐が無いこと自体が risk 0 の根拠ではない — 側に依る **量**（AXFIX・pad 名・menu 符号）が表 §4 で全て測られていることが根拠。(2) 関節 sign map を「作る」誘惑（reference の R 式）= 負の対照で 0/48。(3) 鏡像述語を task 空間で書くと正しい controller が落ちる（§7）。(4) dynamics 未検証（§7 R2/R4）。
```

## 7. pZ へ（述語は pZ の court・以下は提供であって決定でない）

- **R1 関節空間の鏡像（static・built C-2 cell・FK のみ・mj_step 0）**: q ∈ {HOME_POSE, reference の on-yoke 24 pose, in-limit 乱数 M} について、`p_R(q) = Mx·p_L(q)`・`R_R(q) = Mx·R_L(q)·Mx`（Mx = diag(−1,1,1)・tool body `{t}g_base` と各 link）。期待 = asset 級の一致（pZ B3 Hausdorff 0 と同級・bar は pZ が置く）。**負の対照** = `q_R = R式(q_L)`（−L・upper_arm/wrist_1 は −L+π）→ 鏡像で**ない**（reference では worst 1357.5480 mm）。⚠ 07-29 の位置証拠は 0.22/45 mounting のもの（DDR #68・pZ F4）。C-2 では reference 位置が無い ⇒ **R1 は reference なしの自己鏡像**として立つ（両腕とも同じ cell 内・mount は `for tag, sign in SIDES` で ±構築）。
- **R2 動力学 field 等式（static・compiled model）**: 対応 link/joint/actuator で `body_mass`・`body_inertia`（鏡像共役後）・`jnt_range`・`dof_armature`・`dof_damping`・`actuator_gainprm/biasprm` が L/R で等しい。
- **R3 D4 着地後（static）**: entry ごとの実 tilt L vs R（§5 の期待 = 一致）・side ごとの v_c（pinch→mouth の閉じ軸成分）・cap 前後の値。
- **R4 認可 run 時（報告のみ・gate でない）**: STEP ごとの tool 位置/回転誤差 L vs R。
- ⛔ **task 空間で「同じ target 系列 → 鏡像軌道」と書かない**（pZ 自身の訂正 m-p18-282 §2 と同じ）: 鏡像運動には鏡像 target が要り、姿勢は D3 で y=0 面鏡像ゆえ x=0 面では鏡像にならない。

## 8. STOP 条件（§0・class の限界）

- R1 が asset 級で落ちる（同じ q で鏡像にならない）→ **built cell が #68 の premise を実現していない** = controller の問題でなく premise 側 → STOP → p4 → Rs1。
- `solve_ik` が L の鏡像 target で B に収束しない（L では収束）→ class が B を表現できない → STOP-and-report（method swap しない）。
- D4 以外に「B のために」制御行を触る案が出た → 本書の外 = 新しい一語。

## 9. 当卓が測っていないもの（限界を書いた質問・断定でない）

1. §4 姿勢行の worked example と §5 の tilt 一致は **`_rdes`／`pose_menu`／`_measure_axfix` の定義からの算術**。当卓は run 認可を持たず FK 評価も実行していない ⇒ **pZ R3 が決める**（外れれば §5 の期待だけが外れ、D4 の形は不変）。
2. dynamics の鏡像は **text 上**（asset の inertial 行）しか見ていない → R2。
3. 09-07 の dirty WIP の author・意図は不明（AST で制御 13 def 同一まで）。誰の作業か・commit 予定かは **p18 に照会**（本書は触らない）。
4. DoD run 2 本の **STEP2 L stall**（p4 09-05 handoff）は L 腕（UR15）の事象で本書の対象外 — B controller の完成は stall を解かない。「そのまま撮りそのまま報告」の standing order は不変。

## 10. DoD（本 chunk）と受入項目（結果形）

- 設計 chunk: 本書 bank ＋ §11 の 5 体検証 PASS ＋ p4 受入の一言。
- p0（D4）: (a) 変更 file = wired 1 本（＋必要なら cell_spec の呼び出し形 0 変更）(b) 制御 13 def（§2-c の列挙）の AST が着地前後で同一（D4 の 2 関数を除く）(c) `attitude_tilt_deg` が side 引数を取り、`vertical_cap_deg` が両側で評価し min を返す (d) print に両側 cap (e) hash = function ＋ commit・pin は内容 (f) run 0。
- pZ: R1・R2・R3 の rows（自分の court で確定）。
- chain: D4 着地 ＋ R1-R3 通過 ＝ 「UR15-B ＋ その controller が完成し legs を通った」— **#69 の充足宣言は p4**（DDR #69）。

## 11. gate 記録

- **[TASK] L=L3（自己申告）** | node = `T-ROOT-Kinematic-Pin-Complete-Removal-20260719`（(d) arm-control arc・p4 の chain が走る node）／関連 `T-ROOT-C3C5-Port-To-Current-Substrate-20260809`（cell 構成・DDR #68）。
- **[L-TRIAGE]** self L3（brief `:59`「制御方式は L3 ＋ 設計ゲート ＋ /pre-check」）／auto: file-path 一致 = 0（新規 .md・code diff 無し）・diff keyword = 本文に `ik`/`solver` を含む（設計対象が IK 路）／定量 = 新規 1 file・>200 行 ⇒ L3。**final = L3**・gates = DoD 宣言（§10）＋ pre-mortem（§8・§9）＋ handoff（当卓帳）＋ 5 体事前 debate ＋ `/diffik-trajectory`（§6）＋ `/pre-check`（sub-agent）＋ 層5（lensed panel の 3 view）。
- **[DEFER-RECON]**: #68 = 本設計の premise（Rs1 裁定済・spec 未反映は DoD/run を gate し**設計を gate しない** — DDR #70 の読みと同じ）／#69 = run を gate（本書は run なし）／#38 = UR15 へ supersede 済（本書は UR15/UR15-B の asset を引く）／#45（span）・#58（75 mm）= 不触／#54・#57 = L 腕・mounting の事項で対象外／#48 = ケーブル前提・別 chunk／#34・#35 = commit は `--no-verify` ＋ pathspec。**FOUNDATIONAL で未解決かつ本 chunk を塞ぐ行 = 0**。
- **[RULE-CHECK] Tier 0**: prohibited.md — IK 以外の駆動 0・kinematic trick 0・制御方式変更 0・CLAUDE.md 不触・方針変更 0。Tier 1-3: 新 file は task 指示（Rs1 ①）に名がある object（controller 設計）・新 CLI/新 Phase 0。
- **[VERIFY] 5 体（事前）**: 本書を PROPOSE として lensed 4 ＋ NHA 1 → REBUT/ACCEPT → DECIDE。結果は **本 file 末尾に §12 として追記**（append-only・supersede は明記）。

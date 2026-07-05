# P3-grid JOINT READ (step2) — decision-of-record (%12+%9、2026-07-05 13:2x-13:3x 進行中)

**入力:** grid 81/81 (infra 0) / 数値層 = 三者一致 (%11 aggregate / %9 raw 独立再計数 [parser sha=03ff671f、CP-C 較正 EXACT] / %12 CSV-leg) — strict 59/81=0.728 Wilson[0.623,0.813]、any-seat 80/81=0.988 [0.933,0.998]、seat_miss 21、FAIL 1 (x-20_y5 R_MISS grip-whiff)、meta-provenance 81/81 pass。
**規則:** PREREG §2 + A1 (凍結、事後変更なし)。counting = per-offset unique (日跨ぎ再現 6/6 で決定論補強)。

## 確定済み verdicts (J1-J5、%9 全 CONCUR + 条件反映)

| # | 論点 | verdict |
|---|---|---|
| J1 | evidence-gate 枝 | 3 層表記: 点 0.728 = ≤80% 枝 / CI [0.623,0.813] が 0.80 を僅か跨ぐ事実併記 / **robust = ≥95% 枝の決定的棄却 (M-C bites せず — (a)/(b) は必須でなく robustness OPTION として retained)**。**最終文言の確定 = frame check 後 (J-8b HOLD)** |
| J2 | draw-class LINE | **draw = EMPTY (provisional)、n_winnable = 81 ≥ 59** — stage-1.5 論拠 (全 22 non-strict cell が直交 5mm 以内に strict 隣接; reach residual max 1.2mm でバリア無し)。stage-2 p_hit floor 判定は P4 pre-reg 時に discharge (σ/W = 設計時 param)。fallback: z-tail 3 cell (25-56mm) を Δ/z bound が cover できなければ draw 会計へ復帰、SR は機械更新 |
| J3 | 決定論 | CP-C 共通 6 cell (strict 4 + seat_miss 2) 日跨ぎ同 class 再現 6/6 (同 commit stack) + m8_p8 rerun 同一 outcome → per-offset unique の実証補強 |
| J4 | 機構分解 | **J-8/J-SUPPLEMENT で改訂 — 下記** |
| J5 | horizon / span | horizon **900 確定** (max 771 < 810、n=81 max-of-n 保守注記) / span 92.42mm **定数** (分布退化 → window margin = 設計値、tier informative 不変)。**positive finding: settle span が ±20mm IC に対し不変 = common-mode recenter が全域で機能 = INV#2 の運用的裏付け** (packet 1 行) |

## ⭐ J-8 ≡ J-SUPPLEMENT (独立 2 経路収束 = two-key 済 finding、13:35-13:36 行き違い同時)

- **経路:** %12 = run.log `[C2-SEAT-HONEST]` regex 抽出 (22 cell) / %9 = raw JSON field 直読 (cable_z_at_c2_mm、81 cell)。数値一致。
- **機構:** c2_seated_honest = wall≤0.5 **AND in_groove (|cable_z − groove 829.0| ≤ 3mm)** (producer :4755)。**22/22 non-strict が in_groove(z) leg で fail** — wall leg 併発は 4 のみ (+16.0/+18.0/+12.7/+1.34)。marginal 帯の lateral wall 値は strict と seat_miss でほぼ同値 = **lateral は非分離軸。実分離軸 = z (drop-in 完了度)**。
- **z_gap 分布:** strict 59 = [−0.2, +3.0] median +0.3 (床着座) / non-strict 22 = **[+3.1, +56.2] median +7.1** [seat-miss 21 基準; 22 全体では +7.0 — C3 scope 注記 14:3x、%9 PV] — 帯: 3-5mm ×9 / 5-16mm ×10 / 25-56mm ×3 (25.5/43.2/56.2)。
- **帰結:** (1) Δ/c2 bound は z-gap 分布で size (lateral 2.4mm 基準は ~3× 過小) (2) CSV に z_gap 列追加 (%11 発注済、reserved lateral vector より優先) (3) J7 α lean = 無傷ないし強化 (terminal 近傍の垂直 3-15mm 補正 = ResiP regime)。
- **⚠ 計器懸念 (J-8b):** in_groove の測定 body = nearest-in-Y (:4752 argmin)、wall = 全 geom min — **別 selector**。offset 下で z 側が arm 保持 bow 等の別 segment に飛ぶと物理 seated でも false-negative → **strict 0.728 が過小の可能性 → 枝読み最終確定は frame check まで HOLD**。反証材料: non-strict 分布が strict 分布を滑らかに延長 (3-16mm 帯 19 cell は実物理示唆)。25-56 の 3 cell が artifact-or-drape の決定対象。

## J6: 計器 sanity frame check = REQUIRED (両者段階 CONCUR、(i)-lite)

merged **7-cell** (z 層化 + margin 両側 + 機構): x0_y10 (STRICT 床対照) / x5_y20 (STRICT 境界直下 +3.0) / x15_y5 (+4.1 典型) / x0_y-20 (+15.2、CP-C 再現 cell) / x-15_y15 (+43.2 perched) / **x-20_y-15 (+56.2・wall−2.4 = body-swap 判定の要)** / x-20_y5 (FAIL grip-whiff)。
実行 = %11 (**方式改訂 13:4x**: npz offline replay は不成立 [npz `arm_q` = warp joint_q ≠ mujoco qpos、bridge 必要] → **決定論 re-run + `--record-video`** [built-in `_run_mujoco_grasp_route` EGL offscreen :3775、renderer passive = physics byte-identical、memory `reference-mujoco-headless-egl-video`; §運用9 の「結果確定後の事後生成」意図は充足 — evidence run は完走済・再走は可視化専用]。**guard: 各 cell の再走 verdict が grid CSV 行と一致することを delivery に含める** [決定論 6/6 の cell 単位確認列]。C2 groove crop は 4-cam frame の post-crop §運用14)、**判定 = %12+%9 joint frame 確認**。残 74 cell の video 省略 = 「production 計器 + 決定論 6/6 + 層化 7-cell 両側 spot」で justified (loud、§運用14 mandatory-or-justified)。

## J7: DC-1 joint recommendation (frame check 後に final)

**α (residual-on-frozen-script) lean** — %12 提案、%9 独立 stress-test 同着。根拠 (z 改訂版): 配達 98.8% / honest-seat 72.8% / 失敗 22/22 = terminal 近傍の垂直 drop-in 不足 (典型 +3〜+15mm、median +7.1) = 小 Δ・短 credit path = ResiP regime。β の勝ち筋 (base 崩壊時の自前 following/restoring) は実測と逆。条件 (c-j7-1/2、%9): 数値 evidence 写像明記 / fallback trigger 名指し (α discharge FAIL at P4 → β 再浮上 or α-DR (a) 追加、D-C 再訪) / β 行は menu に残置 / **「joint rec (%12+%9 連名)、決定 = Rs」を rec 自身に記載**。追加観察 (packet 用): drop-in 不足は base choreography (seat push 深さ) の系統成分を含む可能性 — script param 側で部分回収なら residual 対象は残差に縮む (観察のみ、workstream 化は Rs)。

## J-8b 補強 + 数値 cross-leg (%9 13:39、%12 GO 13:40)

- **補強 1 (MED8 同 family):** 本懸念は MED8 (R-clamp-nearest ~44mm off → env obs は専用 seated-seg index 採用) と同一 family — verdict 計器 :4752 argmin には同 fix なし。packet に cross-ref、計器 fix は将来項 (観察のみ)。
- **補強 2 (連続性):** body-swap は不連続 jump を作る — 3.1, 3.3, 3.6… の連続 band は 3-16mm 帯 19 cell の実物理を強く支持。疑義実質 = tail 3 + 境界 +15.2。
- **HOLD scope:** J1 の 3 層とも frame check まで「未確定」表記 (≥95% 棄却層も形式上 22 中 ≥18 false-neg なら崩れるため — smooth-band が反証するが honest 側で)。
- **数値 pre-classifier (GO 済、%9 実行):** npz cable_xyz から nearest-in-Y 選択 node + 40-node C2 距離 profile → strict 59 の modal seated-node 基準で non-strict 22 を (a) 同 node 近傍 = 実 under-seat / (b) 遠隔 node = body-swap 疑義 に分類。video verdict の数値 cross-leg。
- **J-8d 追補 (D-C loop 含意、fold 文へ):** base-choreography 系統成分が script-param で回収される scenario では strict SR 上振れ → evidence-gate 枝が ≥95% 側へ動き M-C/α-DR が復活し得る — J1 retained-OPTION 語がこれを受ける (Rs が観察と枝の連動を一目で読める形)。
- **per-cell 視覚 Q (①-⑦、render frame 選定基準):** ①床着座参照 ②境界直下 strict 実像 ③wall-top/hover/部分挿入の別 ④+15.2 実 under-seat ⑤drape vs perched ⑥body-swap artifact か実 drape か (+C2 近傍 cable 全景) ⑦whiff 機構 (R claw↔cable @re-grasp)。

## J-8c: 数値 pre-classifier 結果 (%9 実行 13:41 + %12 独立再計算 13:46 = two-key) — (b) 疑義は 1 cell に限定、枝読みの数値 robust 化

- **較正 (%9):** selector replicate (npz 最終 frame、Y-argmin) vs JSON `cable_z_at_c2_mm` = |Δ| max 0.05 / median 0.03mm = EXACT。strict 59 の modal seated-node = **21** (分布 18-25)。
- **分類:** non-strict 22 = **(a) 実 under-seat 21 / (b) BODY-SWAP-SUSPECT 1**。
- **(b) = x-20_y-15 (+56.2 極値、⑥ 指名 cell と一致):** Y-argmin が **node 0 (cable 自由端)** に hijack (自由端 tail が c2y を横切り |dy|=0.7mm) — 一方 **node 19 = z_gap +1.7mm (groove ±3 内)・3D 6.4mm / node 20 = +1.7mm・9.0mm** が C2 seat 近傍に実在 = 物理 seated の可能性が高い false-negative 候補。JSON 側も `c2_seated_naive=True`・wall −2.4mm (band 内) で、honest を flip したのは hijacked node の z leg のみ。
- **%12 独立検証 (§運用28、npz から自前再計算 — %9 script 非使用):** ①x-20_y-15: argmin=node0 z_gap +56.2 / node19 +1.7·6.4mm / node20 +1.7·9.0mm / |z_gap|≤3∧3D≤10 の node = {19,20} — %9 数値と一致 ②x-15_y15 (a) 対照: 全 40 node の best = 3D 50.0mm・z_gap +36.1 → groove 近傍 node ゼロ = 実 perched 確定 ③x0_y0 strict 対照: argmin=node21 (modal 一致)・z_gap +1.6 = 計器 on-nominal 正常。JSON 較正値 885.2 = 私の node0 再計算と一致。
- **枝読みへの含意 (HOLD の数値的絞込み、両者合意):** 計器起因 flip 上限 = **1 cell** → strict ∈ {59, 60}、SR ∈ {0.728, 0.741} — **≤80% 枝は (b) がどちらに確定しても不変**。≥95% 棄却層は 21/22 の (a) 数値確認により **video 前から実質 SAFE** (formal 確定は frame check 後、HOLD 形式維持)。
- **video Q 焦点更新:** ⑥ (x-20_y-15 の node19/20 は視覚的に seated か + 自由端 drape の実像) = **唯一の decision-relevant cell**。残 6 cell = confirmatory。⚠ 判定注意: node19 は z-in-band だが 3D 6.4mm (横 ~6mm) — 「groove 内着座」か「groove 縁載り」かは映像で判別 (数値は pre-judge しない)。
- full table: `scratchpad/p9_argmin_stability.py` 出力 (%9、read-only)。
- **J-8c 追補 (per-axis 分解、%9 13:50 + %12 独立再計算 = two-key EXACT):** hijack 元 node0 = **dx −266.3mm** (産出計器は clip から x 26.6cm 離れた自由端点を測定していた — MED8 family の定量像)。node19 = (dx −2.13, dy −5.81, dz +1.73) — **3 軸とも |.| は strict 59 producer-node 帯内** (|dx| med 3.29/max 3.82 / |dy| p95 6.45/max 6.65 / dz signed [−0.16,+2.97]; %12 全再計算一致)。正直な 1 点: strict dx signed = +x cluster [−0.40,+3.82] に対し node19 = **−2.13 = 反対 (−x) 壁側** — ここが視覚判定点。node19–20 は clip 面を跨ぎ (dy −5.81/+8.77、両者 dz≈+1.7)、線形補間の clip 面交差 = **dx −0.73 / dz +1.72 = groove 中心線 ≈±1mm・seat 高で横切る幾何**。
- **2×2 期待像 (pinning-read 前に固定):** (b) 真 [false-neg] = top-down で groove-mouth 内に cable、−x 壁接触気味でも channel 内 + 隣接 node 連続 seat / (a) 真 [real drape] = −x wall-top 載り or mouth 外。両予測像は視覚分離 → ⑥ well-posed。
- **解像度切り分け (%11 13:51 正直申告 → %12 決定):** 内蔵 4-cam の C2 は ~1.2px/mm — **② tail-drape 56mm (~67px) = 明瞭 / ① in-groove vs 縁載り 6.4mm (~8px) = 解像度限界**。→ 役割分担: **video leg = 機構 confirmatory** (② hijack 実像 + C2 域 gross artifact [>3mm 級 貫通/hover] scan + 他 6 cell) / **① の精密判定 = 数値 leg が primary** (per-axis 帯 + 交差幾何、上記 two-key 済)。solver 内蔵 C2 zoom cam 追加 = locked file 編集 = Rs 承認事項 → **今回は escalate しない**。joint frame check が数値と矛盾 or 判定不能の場合のみ fallback 起票。
- **J-8e: %9 CONCUR + rider 4 (13:56 → %12 全採用):** CONCUR 根拠 = sim video は npz と同一 state の render — video が state に無い情報を持つのは premise 層 (groove_z/mesh 幾何) + artifact 層のみ; 「弱い計器で強い計器を裁かない」。**数値側 2×2 recast** (same-output cell 無し確認済): (a-wall-top 載り) → z≈+wall 高 +5mm 級 = **不観測** (+1.73) / (a-mouth 外 drape) → wall 大正値 or naive False = **不観測** (−2.4 / True) / (b-実 seat) → z≈floor ∧ wall 捕捉 ∧ naive True = **観測** — 数値 discriminator 単独で well-posed、残余 escape = premise 失敗 or 物理 artifact = video 担当と厳密一致。
  - **r1 (precedent 束縛):** joint verdict 文に numeric-primary の成立 3 条件 (bar 3mm≈3.6px < 視覚判別床 / 数値 leg = simulator state 直読・非 proxy / 独立 3 leg 整合) を明記し、3 条件成立時に限る運用と書く — video-first mandatory-or-justified を loud 側で満たし「数値 OK だから video 省略」への precedent 拡大を防ぐ。
  - **r2 (矛盾像の実定義):** 達成可能解像度での矛盾像を列挙 — (i) side view: cable 中心が wall-top 高 (≥5mm ≈ 6px+; npz 主張 = floor+1.7) (ii) top-down: clip mouth 域外。どちらか観測 = premise 失敗 → fallback 起票。%11 の crop/判定枠に反映。
  - **r3 (fallback 順序):** Rs locked-file 起票の**前**に npz からの offline 再 render + zoom cam を第 1 fallback (§運用9 事後可視化例外、renderer passive、locked file 不触)。**%12 refinement:** trajectory replay は bridge-blocked (%11 発見 arm_q=warp joint_q) だが、① に必要なのは **final-frame の静的 seat 幾何のみ** = cable_xyz/cable_quat 直 set → mj_forward → 任意 cam render で成立 (arm は frame 外で可) — 安価・即日・統治コストゼロ。Rs 事項化は本経路も不能な場合のみ。
  - **r4 (prereg 整合 + 方向 tag):** 公式 strict = A1 凍結 producer flag の **59/81 = 72.8% を維持**、① 帰結は annex 注記 (instrument caveat、strict∈{59,60} 両値で枝不変) — 遡及再分類なし。**方向 tag (GROVE §2.2): 公式値は under-state 側のみ** (over-state 経路 = strict 59 の argmin node が全て routed 帯 18-25 で hijack 型 outlier 不観測 [J-8c 較正])、flip 上限 1 cell ≪ 0.80 跨ぎに必要な ~5.8 cell (81×0.80=64.8−59、%9 算術照合済) → **≤80% 枝判断に対し conservative-definite**。packet §2 に反映。
  - **r3 較正 leg (%9 14:01 追加、採用):** static pose-render fallback を起動する場合、cable qpos set → `mj_forward` 後に**再構成 xpos vs npz 全 40 node ≤0.1mm を assert してから frame を読む**。gotcha: `data.xpos/xquat` 直書きは mj_forward が qpos から上書きするため無効 — free-root + ball-chain は world→relative quat 変換で qpos 再構成、または viz-only static-geom scene (clip mesh + 記録位置 capsule 列) でも可。無較正 render の判定 = 「記録と別 configuration を裁く」= 本日の計器教訓の再演 — 禁止。
  - **再走 video admissibility 規則 (%9 14:01 追加、採用):** 7 cell の各動画は **per-cell MATCH (verdict / seated_honest / cable_z == 元 grid JSON) が付いて初めてその grid cell の evidence**。MISMATCH cell = CONTRADICTS と同扱い → r3 static re-render (**元 npz** 錨定) へ fallback — 非一致再走の映像を判定すると別 rollout を裁ぐことになる。数値 primary 側は元 grid npz 錨定のまま不変。test cell は %9 が元 JSON と独立照合済 (R_MISS_AT_88 / False / 834.7 EXACT + wall 12.655 一致) = 三者接地。

## frame check 判定枠 (pre-committed、render 到着前に固定 — %12 起草、r1/r2 組込み)

- **per-cell 記録列:** cell / 使用 cam・crop / **r-v1 MATCH (verdict・seated_honest・z_at_c2 3 値 == 元 grid JSON) = admissibility gate — MATCH で初めてその cell の evidence、MISMATCH = CONTRADICTS 扱い → r3 static (元 npz 錨定)** / 視覚 Q 該当番号 (①-⑦) の観測 / gross artifact (>3mm 貫通・hover・explosion) 有無 / r2-(i) side: cable 中心 wall-top 高 (≥5mm) か / r2-(ii) top-down: mouth 域外か / cell verdict (CONSISTENT-w-数値 | CONTRADICTS [→fallback r3] | UNREADABLE [→fallback r3])。
- **joint verdict 文の必須要素 (r1):** numeric-primary の成立 3 条件 (bar 3mm≈3.6px < 視覚判別床 / 数値 leg = state 直読・非 proxy / 独立 3 leg 整合) を明記、本件限定運用と記す。⑥ の (a)/(b) 最終判定 = 数値 discriminator (J-8e 2×2 recast) + video 無矛盾の合成。
- **確定 cascade:** 全 7 cell CONSISTENT → J1 3 層一括確定 (公式 0.728 conservative-definite) + J-8b 解消 (annex 注記化) → c-j7-1 re-CONCUR → packet v1。CONTRADICTS が 1 つでも → r3 fallback (npz static pose-render + zoom) を先に実行、解消しなければ Rs 起票。

## ⭐ 確定 (14:23-14:2x、%12+%9 two-key 完了 — frame check + GPU1 probe 交換)

**frame check: 両 leg 7/7 CONSISTENT-w-数値、gross artifact 0、r2-(i)(ii) 矛盾像 両方不観測 — two-key 成立 (%12 leg 14:18 / %9 leg 14:23)。**
- **⑥ 可視線同定の初読差 → npz node 表で機械的決着 (%9):** mouth footprint (x .39-.41, y .055-.097) 内の node = **18-21 のみ、全て z 829.9-831.2 = seat 高**。z≥834 の cable 材は全て footprint 外 (node≤17 = x .381→.134 直線 ramp z 833→885 / node≥21 far-side y .097→.286 が z 830→869 再上昇) = **inverted-hammock drape** (両端高・中央 seat 沈み)。tail は c2y±30mm 帯を x ~250mm 走る = Y-argmin hijack の幾何成因。**(a)-wall-top に帰属可能な cable 材は mouth 内に不存在 = r2-(i) 最強形閉包 → ⑥ = (b) 確定** (数値 primary + video 無矛盾)。
- %9 sequencing 開示 (records-match-fact): ⑥①+gross scan = pre-seal 固定 / ②③④⑤⑦ の一部詳細 = post-seal 確定 (confirmatory 役に限定、loud 記録) — decision cell の two-key は clean。%12 側: ⑦ whiff mid-episode scrub 省略 (r_grip=0.0N numeric pin、非 decision) loud 記録。

**cascade 実行 (pre-commit 判定枠どおり):**
- **J1 確定 (3 層一括、HOLD 解除):** 点 0.728 = **≤80% 枝 → α-DR (d) position-DR 開始可** / CI [0.623,0.813] が 0.80 を僅か跨ぐ事実併記 / **robust = ≥95% 枝の決定的棄却 (M-C bites せず、(a)/(b) = retained-OPTION)**。公式 SR = 59/81 = 0.728 (A1 凍結・under-state 側のみ・conservative-definite、r4)。
- **J-8b 解消:** ⑥ = (b) = 計器 false-negative **1 cell 確定** → annex 注記化 (公式値不変)。x-20_y-15 は「物理 seated 蓋然性高 (数値 3 leg + node 表 + video 無矛盾)」と記録。
- **numeric-primary 運用の precedent 束縛 (r1):** 本判定の数値 primary は 3 条件成立時限定 — bar 3mm≈3.6px < 視覚判別床 / 数値 leg = simulator state 直読 (非 proxy) / 独立 3 leg 整合。拡大適用禁止。
- **J7 final:** α lean joint rec (%12+%9 連名、決定 = Rs) 文言確定 — c-j7-1 re-CONCUR は %9 が packet fold 文言 PV で実施 (pre-state 済)。

**GPU1 probe (two-key、PROBE_PREREG に countersign):** 両 leg **3/3 MISMATCH 全数値一致** (Δz 12.7 / 14.9 / 0.2mm) → mapping 第 3 枝 = **GPU1 (cuda:1 異機種) = 独立 workload 専用**。%9 追加 leg 3: (i) premise 清浄 — 3 cell とも env diff = CUDA_VISIBLE_DEVICES のみ = 真に device 起因 (誤設定説棄却) (ii) 軌道乖離定量 — flip 2 cell = final 40-node 最大 27.1/30.2mm vs x-20_y5 = **1.9mm で verdict flip** (r_grip 0.0→32.8N) = **flip は把持 microevent で発生 = knife-edge 直接実証** (iii) **J2 annex は delivery-winnable に scope** — GPU1 の x-20_y5 成功は SUCCESS_DUAL_LOADED だが honest=False (wall 13.6) = strict-level winnability は unwitnessed のまま (denominator 81 会計不変)。対照: 同 device (cuda:0) r-v1 7/7 完全一致 → **決定論 = device 条件付き** (grid map / 決定論 6/6 は cuda:0 条件付きと packet annex 明記)。
**sha-epoch 所見 + 閉包 (%9 発見):** grid meta git_diff_sha256 = 3 epoch (2083e0 ×4 ≤11:2x / 9c3099 ×16 / 521419 ×61) — 成因 = grid 走行中 11:2x-11:5x の md 前倒し編集 (**コード非接触**、spec/packet/PREREG 系)。behavioral 不変性: render 7-cell MATCH が後 2 epoch を被覆済、**最初期 epoch (x0_y0 含む 4 cell) 閉包の cuda:0 再走 1 本を 14:2x 起動** (結果は本 file 追記)。将来項 (P2 build spec 提案、今回変更なし): meta に governing code per-file sha を stamp。

## 残
1. ~~x0_y0 epoch-close 再走~~ → **完全 MATCH 14:33** (SUCCESS_R_GRIP_L_CAGE_AT_88 / True / 830.6 / −0.392 = grid と全値一致、`p3_grid/sha_epoch_close/`) — **全 3 sha-epoch が cuda:0 再走 MATCH で被覆完了** (かつ GPU1 が flip した nominal cell の cuda:0 同 device 再現の再確認)。
2. packet v1 化済 (v1.0-rc) → **%9 content PV (c-j7-1 re-CONCUR 込み、実施中)** → bank commit (Rs 14:2x 授権「判定確定したらpacket v1とbank commitまで進めて」) → Rs 提示。

*%12 起草 13:39。0-commit — grid 結果・PREREG A1・packet と同 commit で bank 予定。*

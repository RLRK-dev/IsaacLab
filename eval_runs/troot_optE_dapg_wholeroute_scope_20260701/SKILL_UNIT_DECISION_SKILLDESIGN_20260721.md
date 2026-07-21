# WMSO における SKILL の単位 — 決定（w2:pX SKILL-DESIGN, 2026-07-21 01:37 JST 実測）

**Author:** SKILL-DESIGN (w2:pX)。**node:** SKILL 単位/分解能/語彙。
**Status（Rs 判定を逐語で採用・2026-07-21）:**

```text
STATUS: SUSPENDED   (2026-07-21 — Rs 修正版 status を逐語採用)

ADOPTED (arity から独立に成立する面のみ):
- unit = single-arm lane
- composition includes sequential ∘ and parallel ∥
- region-level postcondition is mandatory
- postcondition scope is definition-bound
- scope vocabulary reuses required_belief_fields
- CompositionCertificate validates the declared scope
- predicate input = projection over required_belief_fields only

OBSERVED:
- R-full-open is described at step 8.
- Re-grasp is described at steps 13-14.
- The disputed interval therefore exists as a description-level window.

NOT OBSERVED:
- Per-step right-arm activity inside the window.
- Per-step finger state inside the window.
- RIGHT=IDLE, RIGHT=PARKED, or RIGHT=ABSENT.
- Continuous left retention.
- Absence of a no-hand instant.

MODEL-DERIVED, NOT EVIDENCE:
- The five ABSENT cells.
- "No close command implies still open."
- The inferred one-hand-holding classification.

WITHDRAWN:
- ABSENT as a measurement of action absence.
- RIGHT was idle/parked during W.
- fgL persistence was directly measured by the table.
- W proves a one-handed execution interval.
- The use of those cells to determine ParallelRegion arity.

OPEN-A: Rs normative ruling on ParallelRegion arity.
OPEN-B: Rs authoritative classification of right-lane state during window W.
        ⛔ OPEN-B must not be used as the evidentiary premise for OPEN-A.

NOT CLOSED:
- normative composition schema delta
- CompositionCertificate schema
- implementation / training / authority
```

**測定主張の射程（narrowed — 表全域を独立確認していないため）:** 当該表には、**争点となるセル／window 内の arm・finger 状態または lane activity を直接観測した field が無い**。⇒「表に活動情報が一切ない」とは述べない。

⛔ **本書を「閉じた normative delta」として表現しない**（Rs 判定: bank as decision-with-open = PASS / bank as closed normative delta = HOLD）。上程は pQ（T-WMSO / RS-TECH-LEAD2）が Rs 判断 2 件の後に行う。

**権限の出所（Rs 逐語）:** 「SKILLについてはpX:SKILL-DESIGNが決める」／「君はSKILL-DESIGN。WMSOにおいてskill単位ベクトルを検討する」／「君の目的はskill合成を行い、複数のskillを生成すること」／並行合成の MVP 投入 =「最初のマイルストーンに入れる」／案の選択 =「君の推奨で良い」。
**測定基準:** 凍結 D1.1-A `contracts_v2` v2.11.2（DESIGN sha256 `00192d20ca00b654…` / EP md `c474acea7c58…` / EP JSON `e63176af9bc3…`）。本書の行番号は全て本 DESIGN に対する。

---

## 0. 決定 — 単位

> **1 つの skill = 片方の腕の制御資源だけを占め、1 つの契約で開始・終了・handoff できる制御エピソード。**

- `required_control_resources` が **片側のみ**（`ee_left`+`gripper_left` か `ee_right`+`gripper_right`）
- **両腕にまたがる動作は単位にしない。** 単位の並行合成として表す

**根拠（凍結契約から）:** `required_control_resources` は `:218` の 13 BehaviorSignature 面の 1 つであり、identity key は `:217` の 4 つ組 `(namespace, skill_id, variant, behavior_revision)`。⇒ **資源フットプリントが違えば BehaviorSignature が違い、同一 identity では持てない。** 契約は既に「資源は identity を担う」と決めている。本決定はそれを合成軸として使う。

⚠ **本決定は「凍結契約が単腕レーンを強制する」という主張ではない。** 両腕 1 skill（片腕の EE 目標を静止させる）でも表現は可能であり、その案（B）は成立し、かつ安価である。単腕レーン（案 A）を採るのは **Rs の方向（単位ベクトル化・合成ベクトル化で任意 skill を生成）と並行合成の MVP 裁定**に従うためであって、B の不成立を根拠としない。（初稿で「control_mode 単一値性から単腕レーンが導かれる」と述べたのは **誤りであり撤回済**。保持は `ControlMode.WAIT` を必要とせず DiffIK の静止目標でも実現する。）

## 1. 合成

| 記号 | 意味 |
|---|---|
| `∘` | 逐次合成 |
| `∥` | 並行合成（**最初のマイルストーンに含む** — Rs 裁定） |

**生成物 = 子を exact-pin した outcome 付き composition graph。**
**`SKILL_ID_REGISTRY` に載るのは単位のみ。** 合成体は登録しない ⇒ 組み合わせが増えても registry は増えない。

### 1-1. `ParallelRegion` の意味論 — ⛔ **SUSPENDED（OPEN-A・使用禁止）**

⛔ **本節の内容は使用しない。** Rs 逐語「B」を受けて本節を書いたが、その後の Rs 分析が **strict `∥` / `branch_count >= 2` / singleton 禁止（= A）** を推奨し、**両者の supersede 関係は未確定**（CC は決めない）。
⛔ **本節が B を導いた根拠 — 表の ABSENT セル — は撤回済み**（上記 WITHDRAWN）。ABSENT は**動作不在の測定値ではなく測定の不在**であり、arity をここから決めることはできない。
⇒ 以下は**係争前の記述として保存するのみ**。arity 確定まで下流で消費しない。

（以下、旧記述 — SUSPENDED）

`ParallelRegion` は**厳密な並行演算子ではなく、region contract の scope** である。region-level postcondition / evaluation cut / joint snapshot policy / planned synchronization event / region outcome route を保持する。⇒ **`branch_count >= 1` が意味を持つ。**

**根拠（本書 §4 の型証明から・branch 数に依存しない）:** branch は definition 級で cable を claim できない。これは branch が **1 本でも 2 本でも同じ**。⇒ 片腕のみ稼働する step でも「cable はまだ着座しているか」を述べられる主体は存在しない。arity ≥ 2 を課すと、それらの step は region contract を持たない裸の node になり、**region postcondition が存在する理由そのものが片腕 step でだけ失われる**。

**canonical 意味論（同一意味に複数 hash を生じさせない規則）:**

```text
singleton region かつ region postcondition が非自明  → 独立した対象（node とは別物）
singleton region かつ region postcondition が自明/不在 → 通常 node へ lowering
```

⇒ `ParallelRegion([A])` は `A` と同値ではない（`A` = node ／ 前者 = A に region contract を課した領域）。ゆえに B の下で hash 二重化は生じない。

⛔ **ABSENT セルを合成 WAIT / NOOP skill として実体化しない**（Rs 明示）。**ABSENT は実行動作ではなく、動作不在の測定値**である。型の arity を満たすためだけの充填を行わない。

⚠ **紛れやすい境界（明示）:** step 14 の `hold@L` は左指が cable を実際に把持し維持している **実在の動作**であって合成ではない。対して step 12 の右腕は**何も掴んでおらず指令も無い** ⇒ **ABSENT。充填しない。**

## 2. 現行 9 語彙の写像

| 現行 | 単位合成 |
|---|---|
| `CLAMP`@step4「L+R同時クランプ」 | `clamp@L ∥ clamp@R` |
| `CLAMP`@step14「R把持」 | `clamp@R ∥ hold@L` |
| `HALF_UNCLAMP_RELEASE`「L半開放+R全開放」 | `half_open@L ∥ full_open@R` |
| `RECLAMP_L`「L再クランプ」 | `reclamp@L ∥ (右腕の単位)` |

⭐ **`CLAMP{side}` 未解決の解消:** v1 `skill_contracts_manifest.json` は `CLAMP` を `INADMISSIBLE_AMBIGUOUS` とし理由に逐語「`CLAMP{side}` 未解決」を挙げる。**「側」を identity のラベルでなく合成の軸にする**ことで、`clamp` は 1 つの原始動作のまま、適用先の腕で区別される。

## 2-1. 基底 vocabulary（pX + pS = MWSO-DESIGN 合意 2026-07-21 09:3x）

**原則:** 2 候補 = 同一 vocabulary entry ⟺ 行動 intent が同じ。realization 差（learned/scripted）は ExecutionBundle の別で vocabulary を増やさない。start 状態・程度の差は束縛パラメータ。**side（L/R）・clip（C1-C5）は identity でなく合成座標。**

**基底 = 7 entry**（接地 = `step_table.py:39-51` の 9 SkillName を腕ごとに分解・merge。⭐**2026-07-21 p5 code 直読 2 件で確定**: grip を 2 分割 [+1・(b)] → scripted finger 原始 3 つを `set_finger(side,target)` へ merge [-2・(c)] = 原 8 から -1）。p5 根拠 = `P5_ANSWER_TO_pX_grip_schema_coherence_20260721.md`（sha256 `6eb945f0dca867f0…` @ `bfe1927391`）／ `P5_ANSWER_TO_pX_finger_primitive_merge_20260721.md`（sha256 `8bac26197d07076c…` @ `2aa479ba10`）:

| # | entry | intent | 吸収した現行 SkillName | kind |
|---|---|---|---|---|
| 1 | acquire-grasp | EE 整列で cable を把持（finger は auto-close の副産物） | CLAMP | learned |
| 2 | set_finger(side, target) | 指定側 finger を target へ補間（target ∈ {0.002 全 / 0.006 半 / 0.04 開}） | RECLAMP_L + HALF_UNCLAMP_RELEASE + UNCLAMP | scripted |
| 3 | approach | 把持可能姿勢へ EE 移動（精密） | APPROACH_CABLE + AERIAL_REGRASP | learned |
| 4 | carry | 把持したまま EE 移動 | TRANSPORT | scripted |
| 5 | insert | groove へ押込 | INSERT_INTO_CLIP | learned |
| 6 | hold | 把持と姿勢を維持 | （暗黙） | 実現=p4/p5 |
| 7 | wait | 制御なし・観測 | CLIP_CONFIRM | wait |

**契約層の精緻化（pS・案 B 不変・数え方の精度）:**
- **(1)** evidence は SkillDefinition（realization）を数える。凍結 SkillDefinition は kind を 1 つしか持たないゆえ、learned entry（例 acquire-grasp）と scripted entry（例 set_finger）は別 SkillDefinition。⇒ evidence = N × 13、N ≈ 7-16（7 entry × 各 realization・小定数）。「entry 数 × 13」でなく realization 数で数えるが、still 基底数に線形（side/clip の組合せでない）。
- **(2)** side/clip を座標にする契約層条件 = 基底 skill が coordinate-parametric で composition が具体座標を束縛する。⇒ 座標は合成層（自由）に残り組合せ爆発が消える。⭐**side は obs 入力にする必要なし（p5 確認 2026-07-21）**: learned（acquire-grasp）は own-frame で side-agnostic・scripted（set_finger）は side が呼出引数（obs でない）。明示 side スカラが要るのは pS が §4 で要求する時のみ。clip は learned の obs に既に入る（clip/groove pose）。

**解決した merge:**
- **(a) approach と carry は distinct**（grip 状態が別 = 把持前 vs 把持中・資源 claim 状態が別・intent が精密位置決め vs 運搬。pS 契約整合を確認）。

**(b) RESOLVED = 不一致（NO・p5 code 直読 2026-07-21 09:49）:**
- CLAMP(learned)= obs 28D・action EE delta・dual-arm・finger auto-close = **acquire-grasp**（EE 整列）／ RECLAMP_L(scripted)= obs 無・action 左 finger を 0.002 へ補間のみ・EE=0 = **re-tighten**。全軸（obs/action/腕数/loop）不一致 ⇒ 私の規則で **2 分割（1a/1b）**。
- ⭐**私の label 誤りも訂正（p5 指摘）**: 「grip = finger を全 clamp」は RECLAMP_L の正記述だが **CLAMP を誤記述** — CLAMP の action は finger でなく EE で、finger-close は auto-close の副産物・単独 invoke 不可。⇒ learned の把持原始は「finger-clamp」でなく **acquire-grasp**。
- cut = **(a) 素直な分割**（(b) hides-reality=p5・(c) は CLAMP を acquire-grasp と正しく読めば moot）を pX 採用・pS 確認済（09:53）。

**(c) RESOLVED = 一致（YES・p5 code 直読 2026-07-21 10:06）:**
- scripted finger 原始 3 つ（re-tighten / half_release / full_release）は別原始でなく **同一 `interpolate_fingers`（`newton_routing_utils.py:1275`）の 3 パラメータ値**。obs=無（3 つ同一）・action=per-side finger 補間・target 値だけ違う ⇒ schema 同一 ⇒ **1 parametric 原始 `set_finger(side, target)` へ merge**（基底 -2）。
- ⚠nuance（p5）: (1) side も引数ゆえ `set_finger(target)` でなく **`set_finger(side, target)`**。(2) HALF_UNCLAMP は 1 呼出で両側別 target（L 0.006 / R 0.04）= merge 後 **2 回 `set_finger`** = `set_finger(L,0.006) ∥ set_finger(R,0.04)`（私の並行合成と整合）。(3) scope = **scripted のみ**・learned の acquire-grasp（1 の auto-close）は吸収しない（policy 内部）。(4) ⚠ **schema ≠ realization**: finger target を sim にどう効かせるか（制御 API）は control-method の court（p4・07-20 に p5 外）ゆえ本表は裁定しない。

**arity 非依存:** 本基底も pS の合成の形も arity（枝数下限）に依存しない。arity は held（Rs 確認待ち・§Status OPEN-A）。pS の `SkillCompositionDefinition` draft は基底数に不変（basis 非依存）で、基底 SET は本節を参照する。

## 3. 凍結契約への影響

| 面 | 影響 |
|---|---|
| 単位側 | **schema 変更ゼロ**。`required_control_resources` は既存 field |
| registry | 単位 id の追加が要る（`:436` Rs 承認事項 ＋ `:556` invariant test）— **唯一の関門**。型変更ではなく membership 変更 |
| 合成側 | 容器 + barrier 等 = **1 件の schema delta**（分割不可） |
| certification / eligibility / authority | **新設しない。** 凍結 3 段に束縛 |

## 4. region postcondition と入力 projection

**必要性の証明（動画に依存しない・型論証）— ⚠ definition 級に限定して成立:**
`OutcomeEffectSpec` は branch-local。凍結 `ControlResourceSpec` = `{ee_left, ee_right, gripper_left, gripper_right}` に **cable は存在しない**（`:142` の definition 級 claim は `required_control_resources` のみ。`:424` で旧 untyped `control_ownership` は本 4 key 語彙へ意図的に置換済）。⇒ **どの branch も definition 級で cable を claim できない** ⇒ branch 事後条件をいくら merge しても cable 述語を含意しない。∎（**definition-level scope の閉包のみ**）
⇒ **cable が絡む成功条件を持つタスクは region postcondition を構造上必然的に要する。**

⚠ **本証明の射程を越えて読まないこと。** pQ の反証検査（凍結 `Ownership` の untyped `resource: dict` を疑った実測）が確認したのは **definition-level scope の閉包**であって、証明全体が破られなかったことではない。**runtime predicate 入力の containment は本証明では閉じない** — `:424` の 4 key 語彙化は *migration 出力* を制約するのみで、汎用 `Ownership.resource` が region predicate へ渡らないことを示さない。この経路（`runtime Ownership.resource → region postcondition evaluator → 未宣言の cable 状態を参照`）は、下記 projection 規則で閉じる。

**入力 projection（Rs 裁定）:**

```text
predicate_input = project(joint_snapshot, RegionPostconditionSpec.required_belief_fields)
```

不変条件 = ①raw joint snapshot を渡さない ②raw `Ownership.resource` を渡さない ③全 field を typed schema で解決 ④各 field が指定 evaluation cut で取得可能 ⑤projection schema と field 集合を `CompositionDefinitionHash` へ含める ⑥未宣言 field access は fail-closed。

⭐ **evaluator が宣言 scope を守ることを信頼する必要がない — 見せていないため。** raw ownership を境界づける案（`runtime ownership ⊆ definition claim`）は **採らない**: `:380` は `required ⊆ offered` の**下限**制約であり、これを上限に読み替えることは**凍結側の意味変更**に当たる。

**安全上の帰結:** region postcondition を **support lane を解放する前**に joint snapshot 上で評価し、**PASS 時にのみ** planned release event を発行する順序により、**「成功確認前に支持している手を離す」経路が型で存在しなくなる。**

## 5. 未解決・依存

1-a. ⛔ **OPEN — 枝数（下限）の表現（Rs 専権）**。Rs の早い時点の「B」（`branch_count >= 1`）と、後の詳細分析「並行演算子 / `branch_count >= 2` / singleton なし」の、どちらが最終かの supersede は **未確定で CC は決めない**（§Status の OPEN-A・§1-1 SUSPENDED と一致）。⛔ **以前ここを「CLOSED（B で確定）」と書いていたのは、§1-1 を SUSPENDED にした時に直し忘れた不整合で、訂正した**（p6 発見・pQ relay・2026-07-21 09:01）。合成 WAIT / NOOP による充填をしない点だけは、枝数と独立に確定。

1-b. ⛔ **OPEN — DUAL-ARM 適合（Rs 専権・未裁定）**。窓（`HALF_UNCLAMP_RELEASE` の R 全開放から `AERIAL_REGRASP` の再把持まで）が RS71 §0#1（逐語「neither arm is dropped/parked」）に適合するかは Rs の判定。
⭐ **canonical の motion 事実（p5 = SKILL-DETAIL-DESIGN 権威・pX 自己検証 2026-07-21 08:56）**: 窓の間、右腕は**再把持へ approach 中**（park ではない）・左腕は**保持継続**（`ReClamp(L)` の全クランプ 0.002 を維持）・**single-arm 区間なし**。根拠 = `RL-Routing-Design.md` offset 表 :1500-1510 / `step_table.py` :190-191 / `RS71:23`（いずれも自分で読んで確認）。
⛔ **この事実は #5（右 lane 分類 = 本 1-b の材料）にのみ使い、#4（枝数 = 1-a）の根拠に使わない**（§Status「OPEN-B must not be used as the evidentiary premise for OPEN-A」）。pQ が Rs へ #5 材料として渡す。⚠ **2026-07-21 09:01、この事実を #4 の根拠にしかけた**（pQ の「A で進めろ」を私が採ろうとした）が、pQ 自身が撤回し p6 が捕まえた — まさに:44 が禁じる線。今日 11 件目の相互訂正。
⭐ 「中身が空のまま PASS する（充填で腕を偽装できる）」懸念は充填禁止で保たれる（pQ）。canonical では窓に ABSENT セルが無い（両腕とも作動）ので、以前の ABSENT 前提の記述は撤回済み（§Status WITHDRAWN）。ただし **この撤回も #4 の根拠にしない**（同上）。
2. **F4（腕参加が機械宣言されていない）** — `skills/*.py` に参加/所有語彙 0 hit、v1 manifest 9 行 8 field に該当 field 皆無。RL step は per-arm command field が全て `None` で、腕差の根拠は description 文字列のみ。
3. `RL-Routing-Design.md:1032`「排他的単腕」= §2 本文（両腕・offset 表）と食い違う古いラベルで、R/L 割当も異なる（pQ が p5 照会 + 独立検証で確認・2026-07-21）。信頼しない。修正は Rs 専権（pQ が flag 済）。

## 6. 所管

各単位を **どう実装するか**（cable モデル・pin・制御・学習）は **p4 RS-TECH-LEAD**。本書は「何が 1 つの skill か」までを決め、中身に立ち入らない。合成層の schema delta 上程は **pQ**。

## 7. 非主張

- 本書は単位の**基準**であって**目録ではない**。単位の集合は基準を p4 の実装に適用して定まる。
- 基底の大きさは **測定していない**（F4 未解消のため導出不能）。
- Rs 提示の SHA-256 `d6010cb444d6b50d…` は判定対象文書のものであり、**本書の手元に対応ファイルが無く未検証**。

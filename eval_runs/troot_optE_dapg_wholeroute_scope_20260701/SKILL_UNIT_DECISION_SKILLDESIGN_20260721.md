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

1-a. ✅ **CLOSED — 表現の問い（Rs 裁定 2026-07-21 =「B」）**。`ParallelRegion` = region contract scope（`branch_count >= 1`）と確定 ⇒ step 9・12・20・28・36 は **single-branch region ＋ region postcondition** で表す（§1-1）。合成 WAIT/NOOP による充填は行わない。branch 数下限・singleton hash 意味論・ABSENT の graph projection 規則が同時に確定。

1-b. ⛔ **OPEN — 不変前提適合の問い（Rs 専権・未裁定）**。43-step の step 9・12・20・28・36 で右腕が保持も指令もされないこと（`HALF_UNCLAMP_RELEASE` の R 全開放から `AERIAL_REGRASP` の再把持までの窓）が、**RS71 §0#1 DUAL-ARM（逐語「neither arm is dropped/parked」）に適合するか**は未判定。
⚠ **裁定 B はこれを閉じていない**（pQ 指摘 2026-07-21 02:04、私が受諾）。「充填するな」は**表現をそのまま受け入れる**指示であって、**その表現が不変前提に適合するという判定ではない**。⇒ **本書の初稿は本項を「CLOSED」と記載していたが over-close であり訂正した。**
⭐ **本項が閉じないことには識別上の意味がある**（pQ）: もし ABSENT を合成 WAIT で埋められたら、claim ベースの DUAL-ARM 検査は **vacuously PASS** する（何も掴んでいない腕を「claim している」と宣言する単位を型充填のために置けるため）。⇒ **充填禁止が検査の識別力を保っている。**
2. **F4（腕参加が機械宣言されていない）** — `skills/*.py` に参加/所有語彙 0 hit、v1 manifest 9 行 8 field に該当 field 皆無。RL step は per-arm command field が全て `None` で、腕差の根拠は description 文字列のみ。
3. `RL-Routing-Design.md:1032`「排他的単腕」の扱い（p5 所管 / 不変前提は Rs）。

## 6. 所管

各単位を **どう実装するか**（cable モデル・pin・制御・学習）は **p4 RS-TECH-LEAD**。本書は「何が 1 つの skill か」までを決め、中身に立ち入らない。合成層の schema delta 上程は **pQ**。

## 7. 非主張

- 本書は単位の**基準**であって**目録ではない**。単位の集合は基準を p4 の実装に適用して定まる。
- 基底の大きさは **測定していない**（F4 未解消のため導出不能）。
- Rs 提示の SHA-256 `d6010cb444d6b50d…` は判定対象文書のものであり、**本書の手元に対応ファイルが無く未検証**。

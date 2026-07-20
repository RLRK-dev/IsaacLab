# WMSO における SKILL の単位 — 決定（w2:pX SKILL-DESIGN, 2026-07-21 01:37 JST 実測）

**Author:** SKILL-DESIGN (w2:pX)。**node:** SKILL 単位/分解能/語彙。
**Status（Rs 判定を逐語で採用・2026-07-21）:**

```text
ADOPTED:
- unit = single-arm lane
- composition = sequential ∘ and parallel ∥
- region-level postcondition is mandatory
- postcondition scope is definition-bound
- scope vocabulary reuses required_belief_fields
- CompositionCertificate validates the declared scope

OPEN:
- runtime predicate-input containment
- raw Ownership.resource exclusion or equivalent upper-bound proof

NOT CLOSED:
- normative composition schema delta
- composition certification closure
- runtime implementation
```

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

1. ⛔ **不変前提の裁定待ち（Rs 専権）** — 43-step の step 9・12・20・28・36 で右腕が保持も指令もされない（`HALF_UNCLAMP_RELEASE` の R 全開放から `AERIAL_REGRASP` の再把持までの窓）。これが **`ParallelRegion` が単一 branch を許すか**を決める。⇒ **裁定前に branch 数の下限を型に焼き込まない。**
2. **F4（腕参加が機械宣言されていない）** — `skills/*.py` に参加/所有語彙 0 hit、v1 manifest 9 行 8 field に該当 field 皆無。RL step は per-arm command field が全て `None` で、腕差の根拠は description 文字列のみ。
3. `RL-Routing-Design.md:1032`「排他的単腕」の扱い（p5 所管 / 不変前提は Rs）。

## 6. 所管

各単位を **どう実装するか**（cable モデル・pin・制御・学習）は **p4 RS-TECH-LEAD**。本書は「何が 1 つの skill か」までを決め、中身に立ち入らない。合成層の schema delta 上程は **pQ**。

## 7. 非主張

- 本書は単位の**基準**であって**目録ではない**。単位の集合は基準を p4 の実装に適用して定まる。
- 基底の大きさは **測定していない**（F4 未解消のため導出不能）。
- Rs 提示の SHA-256 `d6010cb444d6b50d…` は判定対象文書のものであり、**本書の手元に対応ファイルが無く未検証**。

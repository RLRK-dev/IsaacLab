# PLAN_STATUS Review v4 — 2026-07-19

## 対象

- Archive: `PLAN_STATUS_20260719(2).zip`
- SHA-256: `5aa20817e0b4119825de9927e86d3dae4ab421c4fc055f9d5b6d2348741cd69d`
- Previous archive SHA-256: `77dc0495beb10467e1f3d1f192517d644ea806e98d7fa88792e794af682195b8`
- Conclusion: 最新版は前回版と異なる。WMSO v2.3 / EvidencePolicy v1.1 / arm-control v1.5 を含む。

## 総合判定

```text
Archive extraction:                    PASS
Summary-to-file hash consistency:      FAIL
WMSO D1.1-A scope:                     CLOSED — maintain
WMSO design v2.3:                      HOLD
WMSO implementation/training/authority:CLOSED — maintain
Arm-control design v1.5:               HOLD
Formal P-D1 probe:                     HOLD
Operational PLAN_STATUS SSOT:          HOLD
```

設計を実装へ開く状態ではない。WMSOは小規模な契約修正だけでなく、現行review-v3で指摘済みのidentity/policy表現を正しくfoldする必要がある。arm-controlは新しい負制御とrun matrixを導入したが、旧規則が本文に残り、どれが現行の合否規則か一意でない。

---

# 1. PLAN_STATUS / custody

## 1.1 重大：summaryのfile 07 SHAが実体と一致しない

`00_PLAN_SUMMARY_p6_20260719.md` は file 07 を次で記録している。

```text
SHA-256 = 4a38d42321cfef80558797143fb56bd5eaa01fba866d896da96df50839ca5253
```

しかしZIP内の実ファイル

```text
07_WMSO_D11A_pS_design_verify_asread.md
```

のSHA-256は次である。

```text
178882532a97a9913229f803ce3efc86479abe4ae1de302b951a85ff32960e90
```

理由は明確で、file 07には現在、v2.3 + EvidencePolicy v1.1に対する§9 addendumが追記されている。一方、summaryはaddendum前の旧blobを記録している。

**Disposition:** SSOT hash table FAIL。summary v5で実blobのfull SHA、現在のbank commit/readbackを記録する。

## 1.2 summaryの工程状態がfile 07より古い

summaryは、WMSOの次gateを

```text
pS 全行照合 → pN DESIGN verify
```

としている。しかしfile 07 §9では、pS全行照合は2026-07-19 12:21 JSTに完了し、結論は次である。

```text
PASS-WITH-CONDITIONS
R-1..R-3 fold → v2.3.1 → pS final confirm → pN DESIGN verify
```

従って現在地は、

```text
旧: pS全行照合待ち
正: pS条件R-1..R-3のfold待ち
```

である。

## 1.3 review-v3のfold対象を取り違えている

Design v2.3とpS addendumでいう `W-P0-1..4 / W-P1-1..6` は、同梱の**review v2**の番号系である。例えばfold-mapでは、

```text
W-P1-1 = WCJ二層
W-P1-2 = normalization EXPLICIT_NONE
W-P1-3 = ProofItem order
```

としている。

一方、同梱の**current review v3**におけるW-P1は、

```text
W-P1-1 = source-closure aggregate hashの未定義
W-P1-2 = behavior_revisionの手動依存
W-P1-3 = semantic policy hashとMarkdown custody hashの分離
```

である。

従って、summaryの

```text
review v3 の W1'-W6' をv2.3が被覆
```

という主張は、番号と対象文書が一致していない。pS §9の全行照合も、実際にはreview-v2系の10項目を確認している。

**Disposition:** review IDを必ず完全修飾する。

```text
RV2-W-P0-1
RV3-W-P1-2
R4-P0-3
```

のようにし、review-v3の未fold項目を別表で追跡する。

## 1.4 review-4 transcript

`11_WMSO_RS_review4_transcript.md` は、この会話で提示したreview-4の内容と実質的に整合する。見出し、P0/P1項目、最終判定に意味上の改変は認められない。

```text
semantic fidelity: CONFIRMED
byte fidelity: N/A（原本がchat messageであり独立fileではないため）
```

`Rs確認PENDING`は、この限定を明記した上で解消してよい。

---

# 2. WMSO design v2.3

## 2.1 改善確認

以下は前版から実質的に改善された。

- SCRIPTED/WAITの`EXPLICIT_NONE`をusage aggregationから明示免除
- `schema_registry_hash`をcertificateへ追加
- static certificationとusage eligibilityを別API化
- runtime report型と明示clock入力を追加
- EvidencePolicyのproof不足3件を補完
- `E_PROOF_CONFLICT`とproof canonical orderを追加
- review-4 transcriptをarchiveへ同梱
- FFなしのlearned normalizationに証拠付き`EXPLICIT_NONE`を許可

ただし、DESIGN PASSには不足が残る。

## 2.2 P0：pS R-1..R-3は未fold

### R-1

Design headerのreview-v2 copy SHAが省略形。兄弟artifactはfull 64-hexという自規則に反する。

### R-2

`evaluate_usage_eligibility()`にcertificateが無く、未certified definitionを評価できる。

推奨APIは次。

```python
evaluate_usage_eligibility(
    certificate,
    evidence_bundle,
    current_evidence_policy,
    requested_profile,
) -> UsageEligibilityReport
```

ただし、acceptance / O0-S0-V0 / safety gateをこのAPIへ混ぜない。権限付与は別APIにする。

```python
evaluate_authority_grant(
    eligibility_report,
    acceptance_state,
    two_key_state,
    safety_gate_state,
) -> AuthorityDecision
```

これにより、evidence eligibilityとauthorityを再び混同しない。

### R-3

ProofItem列のshuffleで`EvidenceBundleHash`が不変になるmetamorphic testを追加する。

## 2.3 P0：EvidencePolicyがまだ機械可読のnormative objectでない

EvidencePolicy v1.1はMarkdown tableであり、次が未定義である。

- `EvidencePolicy`の完全な型
- Markdownをpolicy objectへ変換するparser
- parserのartifact hash
- code内定数とMarkdown表の一致試験
- semantic policy canonicalization

現在は、

```text
evidence_policy_hash = Markdown file SHA-256
```

である。これではtimestamp、status、説明文の変更でもcertificate inputが変わる一方、validatorが実際に使用する意味表とMarkdownの一致を暗号学的に保証できない。

**Required:** 二つに分ける。

```text
policy_document_sha256
  custody用。Markdown全体のhash。

evidence_policy_definition_hash
  machine-readable policy objectをWCJでcanonicalizeしたsemantic hash。
  validator/certificateはこちらを使用。
```

少なくとも次のartifactを追加する。

```text
WMSO_EvidencePolicy_v1.1.json
または
EvidencePolicyDefinition frozen dataclass + golden JSON fixture
```

policy実体は次のtotal mapでなければならない。

```text
(component_kind, evidence_grade, applicability_class)
  -> exact required ProofKind set
```

## 2.4 P0：design v2.3が自己完結していない

v2.3は多数の規則を、

```text
v2.2のまま
```

としてcommit `ac5865b66d`へ委譲する。しかし今回のPLAN_STATUS archiveにはv2.2 blobが含まれていない。

repoアクセスがある内部reviewでは復元可能でも、transfer package単体では以下を再構築できない。

- EvidenceRecord / EvidenceBundleの完全型
- runtime型の全field
- source-closure規則
- migrationの保持部分
- codec / handoff compatibilityの完全定義

**Required:** pNへ渡す最終設計は次のどちらか。

1. v2.3.1を完全なself-contained文書にする。
2. 依存するv2.2 blobをZIPに同梱し、normative dependency manifestへfull SHAを記録する。

設計本体は差分文書より、完全スナップショットを推奨する。

## 2.5 P0：review-v3のidentity残件が未解消

### source-closure aggregate hash

SCRIPTED/WAITのActionIdはclosure aggregateに依存するが、次が未固定。

- pathをrepo-relativeにする規則
- path separator正規化
- member ordering
- symlinkのfollow/reject
- CRLF/LFの扱い
- pathとfile hashの合成format
- duplicate pathの処理
- missing/unreadable memberのerror code

推奨canonical object:

```json
{
  "members": [
    {"path":"repo/relative/ascii-or-nfc/path.py","sha256":"..."}
  ]
}
```

path昇順、symlink reject、bytesをそのままhash、duplicate reject、member欠落fail-closeとして`H_WCJ`する。

### behavior identity

`SkillActionId`はbehavior semanticsを`behavior_revision`という手動整数に依存する。さらに`scripted_callable_ref`はActionId対象外である。同一closure内でcallableを変更し、revision bumpを忘れると、異なるbehaviorが同じActionIdになる。

**Required:** 次のいずれか。

```text
BehaviorSignatureHash = H_WCJ(
  initiation_spec,
  termination_spec,
  checkpoints,
  handoff specs,
  resume semantics,
  required resources,
  scripted_callable_ref
)
```

をActionIdへ含める、またはregistry diff validatorで「behavior-affecting field変更 + revision不変」を拒否する。前者を推奨する。

## 2.6 P0：AcceptedHandoffSpecがproducer variantを特定できない

`SchemaRegistry`のkeyは `(skill_id, variant)` である一方、`AcceptedHandoffSpec`は、

```text
producer_skill_id
handoff_schema_id
schema_major_version
```

しか持たない。producerに複数variantがある場合、どのdefinitionをcompatibility評価するか曖昧になる。

**Required:** 次のいずれかを追加する。

- `producer_skill_variant_id`
- `producer_skill_action_id`
- `producer_definition_hash`
- content-addressed `producer_handoff_schema_hash`

最も再現性が高いのはschema content hashまたはdefinition hashである。

## 2.7 P0：v1 runtime handoff migrationが構築不能

v1 `SkillHandoffState`には、v2 `HandoffOffer`が要求する次が存在しない。

- `producer_invocation_id`
- `producer_definition_hash`
- `control_epoch`

それでもmigration表は、v1 handoffを`RuntimeSnapshot.handoff: HandoffOffer`へ移すとしている。

**Required:** どちらかを選ぶ。

```text
LegacyRuntimeSnapshot / LegacyHandoffSnapshot
  v1で実在したfieldだけを保持し、authority/runtime再利用不可。
```

または

```text
v1 handoffはloud-discard
MigrationReportへE_MIGRATE_RUNTIME_CONTEXT_ABSENT
```

不足fieldを0やplaceholderで捏造してはならない。

## 2.8 P1：EvidencePolicyのProofItem順序文が曖昧

EvidencePolicy §3bは、

```text
kindのrank
= enum宣言順位ではなく
= ProofKind.value文字列bytes順
```

と書いており、rankと文字列順を混在させている。単純に次へ固定する。

```text
(kind.value UTF-8 bytes, ref UTF-8 bytes, artifact_hash-or-empty ASCII)
```

独立rankは使わない。

## 2.9 WMSO判定

```text
Scope: CLOSED
Design v2.3: HOLD
pS status: PASS-WITH-CONDITIONS, not final PASS
Implementation: CLOSED
```

pS R-1..R-3だけならv2.3.1でよいが、上記identity/policy/migration修正は意味的変更を含むため、実際には**v2.4**としてbankし、pS再確認後にpNへ送る方が正確である。

---

# 3. Arm-control design v1.5

## 3.1 改善確認

- FF実経路として`apply_recorded_arm_ff`を明示
- L-P0をREQUIRED-to-RUNへ固定
- R0/R0b/R1/R2/R3/R4の表を追加
- stale-targetをprimary negative controlに変更
- gain×0.1をexploratoryへ降格する新方針を追加
- route-start re-poseのlimit/sync/cable/impulse/provenance検査を追加
- historical evidenceをclean substrate上でUNVERIFIEDとした

方向は正しい。

## 3.2 P0：headerがv1.4 / 0-commitのまま

本文先頭は、

```text
Status: DESIGN v1.4 — 0-commit
```

だが版表とsummaryはv1.5 bankedである。

**Required:** canonical v1.6 header:

```text
DESIGN v1.6 BANKED
production implementation CLOSED
formal P-D1 probe HOLD
canonical path / full SHA / bank / readback
```

## 3.3 P0：B2 fallbackがSTOP gateになっていない

B1をPRIMARYにした点は正しい。しかしB2は、strip不可能なら使用可能なfallbackとして残る。

```text
B1 infeasible
  -> STOP
  -> design delta
  -> p5/pN review
  -> explicit approval
```

を必須にし、実装担当がB2を選べないようにする。

## 3.4 P0：旧L-P5規則が本文に残り、現行規則と矛盾

v1.5 §12.1ではstale-targetをPRIMARYとし、gain×0.1をoptional exploratoryへ降格している。

一方、現行本文には依然として次が残る。

- §5 L-P5: `gains ×0.1`がFAIL必須
- §5 成立bar: `L-P5 FAIL`
- §8-4: `×0.1 negative control、必須`
- §10: `L-P5再設計input`が次action

後段の「supersede」注記だけでは、prereg転記時に旧規則を拾う危険が残る。

**Required:** normative sectionsを直接書き換える。

```text
L-P5 = stale-target instrumentation calibration
R3 required
R4 gain×0.1 optional, non-gating
pass equation = R3 expected-failure detection PASS
```

旧L-P5′の検算はhistorical noteへ移す。

## 3.5 P0：run matrixのramp legが定義不足

R2は単に、

```text
PD + ramp
```

とされている。しかしM-5はjump > JUMP_TOL時だけ発火し、route-startはre-pose+ctrl syncによってjumpゼロにする設計である。

従ってR1とR2が同じcommand streamになり、差分が存在しない可能性がある。

**Required:** 次を固定する。

- rampを発火させるexact event
- R1でrampを無効にするのか、R2で特定jumpを注入するのか
- target stream以外の差分がないこと
- comparison metric
- no-ramp/rampのどちらがproduction candidateか

推奨は、P-D1本体から曖昧なR2を外し、phase-k restore用の小さな専用unit/integration probeとして分離すること。

## 3.6 P0：L-P2 acceptanceとpass equationが一意でない

§5ではL-P2をpredicate parityとしつつcharacterizationへ降格し、acceptanceは次preregで再定義するとしている。後段§12では`L-P2′ RATIFY`とするが、現在の§5成立barは依然として`L-P2述語成立`を要求する。

clean kinematic R0bが既にroute失敗する場合、R1も同じfailure classならparityが成立してしまい、acceptanceとして判別力がない。

**Required:** P-D1の目的を分離する。

```text
PD realization PASS:
  tracking / effort / route-start sync / instrumentation validity

Task choreography acceptance:
  separate result; clean substrateでtask successを要求するなら明示bar

Historical contamination impact:
  R0 vs R0b; PASS式外
```

L-P2をPASS式に残すなら、success predicateとfailure-mode exclusionを明示する。

## 3.7 P0：FF経路の列挙は改善したがpositive path assertionが不足

FF主siteは正しく列挙された。ただし、正式probeでは「選択された実経路が毎expected frameでctrlを書いた」ことを正側に証明する必要がある。

run recordへ最低限次を追加する。

```text
active_drive_path = FF_APPLY_RECORDED_ARM
expected_write_count
actual_write_count
first/last written frame
per-frame target source index
path-selection flag hash
```

`actual_write_count == expected_write_count`をLOUD assertする。

## 3.8 P1：§8-3の解析表現をさらに弱める

`implicitfast`はstiffnessへの耐性を高めるが、contact、saturation、controller gainを含む閉ループ安定性を保証しない。

```text
堅牢
```

ではなく、

```text
陽積分より数値的不安定性リスクを下げる。合否は@4/@10実測gateのみで決める。
```

とする。

## 3.9 Arm判定

```text
Design v1.5: HOLD
Formal P-D1 prereg freeze: NOT READY
Production implementation: CLOSED
Diagnostic B1 reimplementation: may proceed only under diagnostic fence, not evidence run
```

---

# 4. 推奨する次の順序

## WMSO

1. summary v5でfile 07 SHAと工程状態をrecords-fix。
2. review-v3の未fold項目を完全修飾IDで台帳化。
3. v2.4で次をfold:
   - pS R-1..R-3
   - certificate-first eligibility
   - machine-readable EvidencePolicy + semantic hash
   - self-contained types
   - source-closure canonical hash
   - BehaviorSignatureHashまたはrevision invariant
   - handoff producer variant/content hash
   - legacy runtime migration disposition
4. review-4 transcriptを`semantic fidelity CONFIRMED`へ更新。
5. pS final re-check。
6. 最終SHAだけをpN DESIGN PASS-CLOSEへ送る。

## Arm control

1. canonical v1.6を作る。
2. headerとB2 STOP gateを修正。
3. §5/§8/§10の旧L-P5規則を削除・stale-targetへ一本化。
4. ramp testをexactに定義するか別probeへ分離。
5. L-P2/pass equationを一意化。
6. FF positive path assertionを追加。
7. bank/readback後にP-D1 preregを凍結。
8. B1 clean implementationでのみevidence-grade runを開始。

---

# 5. 最終ステータス文

```text
PLAN_STATUS archive bytes: PASS
PLAN_STATUS hash table: FAIL (file 07 mismatch)
Operational SSOT: HOLD

WMSO scope: CLOSED
WMSO design: HOLD — v2.4 required
WMSO implementation/training/authority: CLOSED

Arm-control design: HOLD — canonical v1.6 required
Formal P-D1 probe: HOLD
Production implementation/training/authority: CLOSED
```

---

## Internal working output

**Verified archive delta**

- Latest archive is not a duplicate of the previous archive.
- WMSO design advanced to v2.3.
- EvidencePolicy advanced to v1.1.
- Arm-control design advanced to v1.5.
- The pS verification file now contains a v2.3 addendum.

**Highest-severity record defect**

The summary records the pre-addendum SHA for file 07, while the ZIP contains the post-addendum blob. The summary also says the pS full-line review is pending even though the included addendum completed it with three conditions.

**Highest-severity WMSO defects**

- The current review-v3 findings are confused with review-v2 identifiers.
- The policy is still a Markdown document rather than a canonical machine-readable object.
- Scripted source-closure hashing and behavior identity are not fully pinned.
- Legacy runtime handoff migration cannot construct the required v2 runtime object.

**Highest-severity arm defects**

- The obsolete gain-times-0.1 negative control remains in normative sections despite being superseded later.
- The ramp run is not an operationally distinct, reproducible contrast.
- The pass equation still cites an ambiguous L-P2 criterion.

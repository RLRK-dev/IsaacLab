# WMSO exact baseline — custody 検証記録（v0.2 レビュー工程・2026-09-03）

- node: `T-WMSO`; 記録者 = Claude Code web session（設計文書起草・独立レビュー専用。**authority 無し・凍結物へ非接触**）
- 作成 = 2026-09-03（UTC・session 実測）
- 位置づけ: 前 session（2026-09-03、別 sandbox）が回収した exact pin を、**本 repo の worktree・git blob・凍結 commit・GitHub 履歴で独立に再測**した記録。前 session が「未実施」と明記していた **凍結本文へのローカル `sha256sum`** を本 record で実施した。
- ⛔ 本 record は freeze / gate / authority を一切主張しない。freeze record（時点 snapshot）と LEDGER（current）の convention を変えない。

## 1. 検証対象 pin（full 64-hex）

| artifact | 版 | sha256 | git blob | bank commit |
|---|---|---|---|---|
| `WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md` | D1.1-A DESIGN v2.11.2 | `00192d20ca00b654cf6cfdb9d04b03ca14adfd0b93f2105c0fea28c295ff8aff` | `1353430228a90ad36dd190a9359cd81da52e8242` | `54f90a7de1e02fb14eaf793bf3c60d9503d0d82e` |
| `WMSO_D11A_EVIDENCE_POLICY_V1_RSTECHLEAD2_20260719.md` | EvidencePolicy v1.9 | `c474acea7c58acc22050c2ad9944fd45a18f5c76967964b42d11922e28fa27e7` | `af947ae311e5333edc42e10d5695c75a2c872535` | `37ddb72284` |
| `WMSO_EvidencePolicy_v1.9.json` | JSON fixture v1.9（policy_semver 1.9.0） | `e63176af9bc3a246b1c32db369ec59f8d09a4c96c381bb03a3a6024bd9811c6e` | `98313574ffe282d14d75aeeab7bc5131a035ac76` | `37ddb72284` |
| `evidence_policy_definition_hash` | H_WCJ(policy_definition)・17 member | `e7ca43093084c167a209b008533a66d26a1fd3223d2a3c11274d28306c3ff803` | — | 埋込 command で再計算 |
| `WMSO_D11B_TENSOR_BINDING_DESIGN_RSTECHLEAD2_20260720.md` | D1.1-B DESIGN v13 | `5a1874d3be8b98b8aeaace73890d8021cbc7f9814e048741f7f58d6746f349a6` | `ebe8154abf2461a6b24db05728b20e5cee949fb2` | `07250f4a0208b3bbd27eae6fef7d980743c4b538` |

## 2. 実測（`verify_exact_baseline_pins.sh` の逐語出力・repo root で実行・HEAD = WMSO 作業ブランチ先端 `f7d8a0d0` と同一 tree）

```text
PASS  D1.1-A DESIGN v2.11.2 (worktree)  00192d20ca00b654cf6cfdb9d04b03ca14adfd0b93f2105c0fea28c295ff8aff
PASS  EvidencePolicy v1.9 md (worktree)  c474acea7c58acc22050c2ad9944fd45a18f5c76967964b42d11922e28fa27e7
PASS  EvidencePolicy v1.9 json (worktree)  e63176af9bc3a246b1c32db369ec59f8d09a4c96c381bb03a3a6024bd9811c6e
PASS  D1.1-B DESIGN v13 (worktree)  5a1874d3be8b98b8aeaace73890d8021cbc7f9814e048741f7f58d6746f349a6
PASS  D1.1-A DESIGN git blob id (HEAD)  1353430228a90ad36dd190a9359cd81da52e8242
PASS  D1.1-B DESIGN git blob id (HEAD)  ebe8154abf2461a6b24db05728b20e5cee949fb2
PASS  D1.1-A DESIGN sha256 of blob 135343…  00192d20ca00b654cf6cfdb9d04b03ca14adfd0b93f2105c0fea28c295ff8aff
PASS  D1.1-B DESIGN sha256 of blob ebe815…  5a1874d3be8b98b8aeaace73890d8021cbc7f9814e048741f7f58d6746f349a6
PASS  D1.1-A DESIGN at frozen commit 54f90a7d  00192d20ca00b654cf6cfdb9d04b03ca14adfd0b93f2105c0fea28c295ff8aff
PASS  D1.1-B DESIGN at frozen commit 07250f4a  5a1874d3be8b98b8aeaace73890d8021cbc7f9814e048741f7f58d6746f349a6
PASS  evidence_policy_definition_hash (embedded command)  e7ca43093084c167a209b008533a66d26a1fd3223d2a3c11274d28306c3ff803
policy_semver=1.9.0
HEAD=f7d8a0d0050e885e5a0b22674b315408be78d562 branch=claude/v0-2-design-candidates-snqbmy
```

- 実行環境: 素の `python3`（stdlib のみ）。`./isaaclab.sh -p` 経由は使用しない（D1.1-B H2 の exit-code mask hazard を回避）。
- 凍結 commit 2 本は `git fetch origin <sha>` で取得（shallow clone のため祖先関係は local では証明不能 — §3 で GitHub 側履歴により補完）。

## 3. 凍結 commit の祖先性・凍結後不変性（GitHub 履歴・path filter）

`rlrk/optE-s2-substrate-swap` の commit 履歴を各 design path で filter した結果（GitHub API・2026-09-03 実測）:

| path | 当該 path に触れた最新 commit | 帰結 |
|---|---|---|
| D1.1-A DESIGN | `54f90a7de1e02fb14eaf793bf3c60d9503d0d82e`（2026-07-19 22:23 JST） | 凍結 bank commit = branch 上の最終変更 ⇒ **凍結後に同名編集なし**・凍結 commit は tip の祖先 |
| D1.1-B DESIGN | `07250f4a0208b3bbd27eae6fef7d980743c4b538`（2026-07-20 23:11 JST） | 同上 |

⇒ **worktree sha == 凍結 commit sha == freeze record pin**（三者一致）。前 session の「現在の WMSO 作業ブランチ上でも Git blob は凍結時と同じ」を、blob id と sha256 の両面で再確認した。

## 4. 前 session 成果物の可用性（honest scope）

- 前 session の package（`WMSO_EXACT_BASELINE_REVIEW_PACKAGE_v0.2_20260903.zip`、申告 sha256 `f02f4f83…`）は別 sandbox（`/mnt/data`）に置かれており、**本環境・本 repo・GitHub のいずれにも存在しない**（全 branch を実測・WMSO runtime spec / industrial profile / v0.1 / v0.2 文書 = 0 件）。
- したがって本工程の 02〜08 は、前 session の handoff に記された**決定事項**（10 修正・CAS 順序・home 判定・後継契約判断・EvidencePolicy 判断）と**凍結 baseline 本文**から再構成した。**前 package の byte / sha は本環境で検証不能**であり、本 package の sha は新規に採番する。

## 5. 境界

- impl / training / closed-loop authority / production / push of frozen artifacts / freeze / slice = **CLOSED 継続**。
- 本 package の全文書は **review candidate**（two-key・Rs 裁定の対象になる前の起草物）であり、gate PASS を主張しない。

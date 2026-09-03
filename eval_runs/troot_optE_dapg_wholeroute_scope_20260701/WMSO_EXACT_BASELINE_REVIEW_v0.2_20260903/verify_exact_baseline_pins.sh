#!/usr/bin/env bash
# WMSO exact-baseline pin verifier (records-only helper; touches no frozen file).
# Run from repo root: bash eval_runs/troot_optE_dapg_wholeroute_scope_20260701/WMSO_EXACT_BASELINE_REVIEW_v0.2_20260903/verify_exact_baseline_pins.sh
# Exit code 0 = all pins match; 1 = at least one mismatch. Plain python3 (stdlib only); do not run via ./isaaclab.sh -p.
set -u
D=eval_runs/troot_optE_dapg_wholeroute_scope_20260701
fail=0
check() { # name expected actual
  if [ "$2" = "$3" ]; then echo "PASS  $1  $3"; else echo "FAIL  $1  expected=$2 actual=$3"; fail=1; fi
}
sha() { sha256sum "$1" | cut -c1-64; }
check "D1.1-A DESIGN v2.11.2 (worktree)" 00192d20ca00b654cf6cfdb9d04b03ca14adfd0b93f2105c0fea28c295ff8aff "$(sha $D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md)"
check "EvidencePolicy v1.9 md (worktree)"  c474acea7c58acc22050c2ad9944fd45a18f5c76967964b42d11922e28fa27e7 "$(sha $D/WMSO_D11A_EVIDENCE_POLICY_V1_RSTECHLEAD2_20260719.md)"
check "EvidencePolicy v1.9 json (worktree)" e63176af9bc3a246b1c32db369ec59f8d09a4c96c381bb03a3a6024bd9811c6e "$(sha $D/WMSO_EvidencePolicy_v1.9.json)"
check "D1.1-B DESIGN v13 (worktree)"       5a1874d3be8b98b8aeaace73890d8021cbc7f9814e048741f7f58d6746f349a6 "$(sha $D/WMSO_D11B_TENSOR_BINDING_DESIGN_RSTECHLEAD2_20260720.md)"
check "D1.1-A DESIGN git blob id (HEAD)" 1353430228a90ad36dd190a9359cd81da52e8242 "$(git ls-tree HEAD $D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md | awk '{print $3}')"
check "D1.1-B DESIGN git blob id (HEAD)" ebe8154abf2461a6b24db05728b20e5cee949fb2 "$(git ls-tree HEAD $D/WMSO_D11B_TENSOR_BINDING_DESIGN_RSTECHLEAD2_20260720.md | awk '{print $3}')"
check "D1.1-A DESIGN sha256 of blob 135343…" 00192d20ca00b654cf6cfdb9d04b03ca14adfd0b93f2105c0fea28c295ff8aff "$(git cat-file -p 1353430228a90ad36dd190a9359cd81da52e8242 | sha256sum | cut -c1-64)"
check "D1.1-B DESIGN sha256 of blob ebe815…" 5a1874d3be8b98b8aeaace73890d8021cbc7f9814e048741f7f58d6746f349a6 "$(git cat-file -p ebe8154abf2461a6b24db05728b20e5cee949fb2 | sha256sum | cut -c1-64)"
# frozen commits (only if present locally; fetch by sha first if missing)
if git cat-file -e 54f90a7de1e02fb14eaf793bf3c60d9503d0d82e 2>/dev/null; then
  check "D1.1-A DESIGN at frozen commit 54f90a7d" 00192d20ca00b654cf6cfdb9d04b03ca14adfd0b93f2105c0fea28c295ff8aff "$(git show 54f90a7de1e02fb14eaf793bf3c60d9503d0d82e:$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md | sha256sum | cut -c1-64)"
else echo "SKIP  frozen commit 54f90a7d not present locally (git fetch origin 54f90a7de1e02fb14eaf793bf3c60d9503d0d82e)"; fi
if git cat-file -e 07250f4a0208b3bbd27eae6fef7d980743c4b538 2>/dev/null; then
  check "D1.1-B DESIGN at frozen commit 07250f4a" 5a1874d3be8b98b8aeaace73890d8021cbc7f9814e048741f7f58d6746f349a6 "$(git show 07250f4a0208b3bbd27eae6fef7d980743c4b538:$D/WMSO_D11B_TENSOR_BINDING_DESIGN_RSTECHLEAD2_20260720.md | sha256sum | cut -c1-64)"
else echo "SKIP  frozen commit 07250f4a not present locally (git fetch origin 07250f4a0208b3bbd27eae6fef7d980743c4b538)"; fi
# EvidencePolicy definition hash — the derivation command embedded in the JSON metadata, run verbatim from $D
check "evidence_policy_definition_hash (embedded command)" e7ca43093084c167a209b008533a66d26a1fd3223d2a3c11274d28306c3ff803 "$(cd $D && python3 -c "import json,hashlib;d=json.load(open('WMSO_EvidencePolicy_v1.9.json'));print(hashlib.sha256(json.dumps(d['policy_definition'],sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()).hexdigest())")"
echo "policy_semver=$(cd $D && python3 -c "import json;print(json.load(open('WMSO_EvidencePolicy_v1.9.json'))['policy_definition']['policy_semver'])")"
echo "HEAD=$(git rev-parse HEAD) branch=$(git rev-parse --abbrev-ref HEAD)"
exit $fail

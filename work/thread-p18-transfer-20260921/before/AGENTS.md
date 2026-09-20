# IsaacLab Guidelines

## Current THREAD Rs1 assignment

- On 2026-09-21, the user explicitly directed: `Rs1は君に置き換えて`.
- The assigned Codex conversation at `w2:p19` now performs THREAD's Rs1 decisions, approvals, prioritization, and acceptance review. Route existing and new Rs1 requests to `w2:p19`; do not retain a human-approval wait solely because historical documents define Rs1 as human. This is a pane/session-specific assignment, not an assignment to every conversation reading this file.
- This assignment does not extend Rs1 authority to other agents or make pending results automatically accepted. Preserve independent verification and report only observations actually made.
- The current assignment, communication route, and inherited requests are recorded in `thread_isaac_lab/thread-vault/02-Workflow/RS1-Assignment-20260921.md`.

## Current THREAD VIDEO-ANALYST assignment

- On 2026-09-21, the user directed the Codex conversation at `w2:p1D`: `herdrでのpCの役割を君に移管させたい`.
- VIDEO-ANALYST ownership moves from `w2:pC` to `w2:p1D` (Codex session `01a0bf98-fe99-7392-959b-b3506c46f9f3`). Route new video-analysis requests through OPS-SUP `w2:p18` to `w2:p1D`; the former pC retains its history and handoff role.
- The assignment covers video identity checks, frame extraction, camera/axis coverage, contact closeups, timestamped visual observations, and reports. VaultProtocol V12 and independent review remain binding; p1D does not acquire Rs1 authority or authorize runs by this transfer.
- Current scope, inherited artifacts, and the return channel are recorded in `thread_isaac_lab/thread-vault/02-Workflow/VIDEO-ANALYST-Assignment-20260921.md`.

## Current THREAD LOG-ANALYST assignment

- On 2026-09-21, the user requested a role transfer to this conversation and corrected the source pane with `pBの間違い` (the initial `p8` was a typo).
- LOG-ANALYST ownership moves from `w2:pB` to `w2:p1E` (Codex session `01a0bfa1-3d58-70d3-89fd-4f378c35181c`). Route new numeric/log-analysis requests through OPS-SUP `w2:p18` to `w2:p1E`; the former pB retains its history and handoff role.
- The assignment covers primary log/JSON/trajectory analysis, artifact and producing-code identity, numeric comparisons, and evidence reports. Numeric results alone do not establish physical validity; preserve the independent visual path and VaultProtocol V12. Rs1 remains `w2:p19`, and VIDEO-ANALYST remains `w2:p1D`.
- Current scope, inherited artifacts, and the return channel are recorded in `thread_isaac_lab/thread-vault/02-Workflow/LOG-ANALYST-Assignment-20260921.md`.

## Current THREAD IMPL-VERIFIER assignment

- On 2026-09-21, the user directed the Codex conversation at `w2:p1F`: `herdrにおけるpZの役割を君に移管したい`.
- IMPL-VERIFIER ownership moves from `w2:pZ` to `w2:p1F` (Codex session `01a0bfa6-2ce3-73f3-86a5-c1ad9d7885fd`). Route new independent implementation/evidence verification requests through OPS-SUP `w2:p18` to `w2:p1F`; the former pZ retains its history and handoff role.
- Preserve preregistration where required, exact artifact identity, independent verification, and VaultProtocol V12. This transfer grants neither Rs1 authority nor run authorization, and does not change IMPL-VERIFIER2 or retroactively accept pending results.
- Current scope, inherited artifacts, and the return channel are recorded in `thread_isaac_lab/thread-vault/02-Workflow/IMPL-VERIFIER-Assignment-20260921.md`.

## Current THREAD PLAN-KEEPER assignment

- On 2026-09-21, the user directed the Codex conversation at `w2:p1G`: `herdrにおけるp6の役割を君に移管したい`.
- PLAN-KEEPER ownership moves from `w2:p6` to `w2:p1G` (Codex session `01a0bfae-f974-7f61-b236-6877fe97f014`). Route new planning-surface and carry-register requests through OPS-SUP `w2:p18` to `w2:p1G`; the former p6 retains its history and handoff role.
- The assignment covers evidence-backed freshness and consistency across the map, node state, design-status ledger/DDR, generated manifest, and authorized SOMA reflection. Content decisions and technical acceptance remain with RS-TECH-LEAD `w2:p4` and Rs1 `w2:p19`; generated sections and protected specifications retain their existing rules.
- Current scope, inherited artifacts, outstanding requests, and the return channel are recorded in `thread_isaac_lab/thread-vault/02-Workflow/PLAN-KEEPER-Assignment-20260921.md`. Finish the old owner's in-progress reflection and reconcile its result before duplicating any write.

## Current THREAD ARM-CONTROL-DESIGN assignment

- On 2026-09-21, the user directed the Codex conversation at `w2:p1H`: `herdrにおけるp11の役割を君に移管させたい`.
- ARM-CONTROL-DESIGN ownership moves from `w2:p11` to `w2:p1H` (Codex session `01a0bfbc-15be-7361-b3df-58504743e5dc`). Route new arm-control design requests through OPS-SUP `w2:p18` to `w2:p1H`; the former p11 retains its history and handoff role.
- The assignment covers arm/finger control design, commissioned cell and camera geometry, controller requirements, and design-court responses. Implementation remains with p0, independent implementation verification with p1F, technical integration with p4, and decisions/authorization with Rs1 p19. Preserve source/specification gates and VaultProtocol V12.
- Current scope, inherited artifacts, outstanding requests, and the return channel are recorded in `thread_isaac_lab/thread-vault/02-Workflow/ARM-CONTROL-DESIGN-Assignment-20260921.md`. Reconcile the old owner's final handoff before duplicating any design write; the transfer does not authorize a run or accept a technical result.

## Breaking API changes

- **Breaking changes require a deprecation first.** Do not remove or rename public API symbols without deprecating them in a prior release.

## API design rules (naming + structure)

- **Group by common prefix for discoverability (autocomplete).**
  - **Classes**: group by domain concept — `ActuatorNetLSTM`, `ActuatorNetMLP` (not `LSTMActuatorNet`, `MLPActuatorNet`).
  - **Methods**: group by noun before modifier — `set_joint_position_target()` (not `set_target_joint_position()`).
- **Method names are `snake_case`.**
- **CLI arguments are `snake_case`.**
- **Prefer nested classes when self-contained.**
  - If a helper type or an enum is only meaningful inside one parent class and doesn't need a public identity, define it as a nested class instead of creating a new top-level class/module.
- **Follow PEP 8 for Python code.**
- **Use modern Python type-hint syntax.**
  - Prefer PEP 604 unions: `x | y`, `x | None`. Do not use `typing.Union` or `typing.Optional`.
- **Use specific type hints for public interfaces.**
  - For torch tensors, annotate with `torch.Tensor`. For Warp arrays, annotate concrete dtypes (e.g., `wp.array(dtype=wp.vec3)`) rather than generic `object`.
  - Prefer consistent parameter names across base/override APIs (e.g., `xforms`, `scales`, `colors`, `materials`).
- **Use Google-style docstrings.**
  - Write clear, concise docstrings that explain what the function does, its parameters, and its return value.
  - Keep argument/return types in function annotations, not inline in docstrings.
  - In `Args:` entries, use `name: description` (not `name (Type): description`).
  - Use Sphinx cross-reference roles for symbol references (e.g. `:class:`, `:meth:`, `:attr:`, `:paramref:`), but keep targets as short as possible.
  - Within the same class/module, prefer short local references (e.g. `:meth:\`set_joint_position_target\``, `:attr:\`num_joints\``) over fully qualified paths.
  - If qualification is needed, prefer public API paths (e.g. `isaaclab.assets.Articulation`) and do not use internal `_src` or private module paths in Sphinx role targets.
- **State SI units for all physical quantities in docstrings.**
  - Use inline `[unit]` notation, e.g. `"""Particle positions [m], shape [particle_count, 3], float."""`.
  - For joint-type-dependent quantities use `[m or rad, depending on joint type]`.
  - For spatial vectors annotate both components, e.g. `[N, N·m]`.
  - For compound arrays list per-component units, e.g. `[0] k_mu [Pa], [1] k_lambda [Pa], ...`.
  - When a parameter's interpretation varies across solvers, document each solver's convention instead of a single unit.
  - Skip non-physical fields (indices, keys, counts, flags).
  - This rule applies to **public API docstrings only**, not test docstrings.
- **Keep the documentation up-to-date.**
  - When adding new files or symbols that are part of the public-facing API, make sure to keep the auto-generated documentation updated by running `./isaaclab.sh -d`.

## Dependencies

- **Avoid adding new required dependencies.** IsaacLab's core should remain lightweight and minimize external requirements.
- **Strongly prefer not adding new optional dependencies.** If additional functionality requires a new package, carefully consider whether the benefit justifies the added complexity and maintenance burden. When possible, implement functionality using existing dependencies, including Warp functions and kernels, NumPy, or the standard library.

## Tooling: prefer `./isaaclab.sh -p` for running, testing, and benchmarking

We use a wrapped python call within `./isaaclab.sh`.

- **Use `./isaaclab.sh -p -c` for inline Python**: When running one-off Python commands, use `./isaaclab.sh -p -c "..."` instead of `python3 -c "..."`.
- **Use `./isaaclab.sh -p`** to run standalone Python scripts without a `pyproject.toml` (e.g., in CI after switching to a branch with no project files).

## THREAD Vault startup and no-repeat guards

Codex sessions started in this repo must treat `thread_isaac_lab/thread-vault/02-Workflow/VaultProtocol.md`
as the active operational protocol. At session start, or before any non-trivial THREAD task,
read and apply VaultProtocol rules V7, V9, V10, V11, and V12.

- **Prior-art / no-repeat gate:** Before any experiment, retry, rerun, source-level promotion, or design response that could repeat a prior failed path, extract 2-5 concrete keywords and run:
  ```bash
  scripts/check_thread_vault_prior_art.sh --fail-on-blocker <keywords...>
  ```
  If blocker context is found, stop before executing. Continue only with an explicit new directive or a documented concrete delta from the failed path.
- **Current-state freshness gate:** Before and after editing front-facing Vault state surfaces such as `HANDOFF.md`, `SOMA.md`, or dashboard `state.md`, run:
  ```bash
  scripts/audit_thread_vault_current_state.sh --strict-log
  scripts/validate.sh --layer 4
  ```
- **Exit-code exception:** These guard wrappers intentionally call `env_isaaclab/bin/python` directly because `./isaaclab.sh -p` can mask non-zero Python exits. Use the wrapper scripts above for fail-closed guard behavior.
- **Evidence basis:** When reporting Vault/current-state conclusions, state whether the claim is based on session context, command output, files read, or timestamped observation. Do not write unqualified `RUNNING`, `PENDING`, or `no final report` as timeless Current State.
- **Reuse / official-specification gate:** Before designing or modifying robot mechanisms, physics/contact models, sensors, cameras, measurement points, controllers, IK, replay/render pipelines, or similarly specification-sensitive surfaces, first check for reusable local/official implementations. Prefer the proven implementation when available. If custom implementation is necessary, verify the official/public specification first and document why reuse is insufficient. For Franka/mechanism work, consult `LL-KinematicAttachment-Failure` and `LL-Process` (`LL-2026-06-03-PROC-006`, including its mechanism/sensor preflight Knowledge set) before source promotion.
- **Visual judgment boundary:** For video/frame/visual physical-validity work, Codex may generate artifacts and record auxiliary observations, but Codex self-judgment is not authoritative. Formal physical-validity verdicts require the independent reviewer/blind-judge path specified by VaultProtocol V12, and video must be judge-fit before interpretation.

### Run tests

```bash
# run all tests (extremely heavy, should be avoided).
./isaaclab.sh -t

# run a specific test file by name
./isaaclab.sh -p -m pytest PATH_TO_TEST

# run a specific example test
./isaaclab.sh -p -m pytest PATH_TO_TEST::METHOD
```

### Pre-commit (lint/format hooks)

**CRITICAL: Always run pre-commit hooks BEFORE committing, not after.**

Proper workflow:
1. Make your code changes
2. Run `./isaaclab.sh -f` to check ALL files
3. If pre-commit modifies any files (e.g., formatting), review the changes
4. Stage the modified files with `git add`
5. Run `./isaaclab.sh -f` again to ensure all checks pass
6. Only then create your commit with `git commit`

```bash
# Run pre-commit checks on all files
./isaaclab.sh -f
```

**Common mistake to avoid:**
- Don't commit first and then run pre-commit (requires amending commits)
- Do run pre-commit before committing (clean workflow)

**When reviewing code** (e.g. via a code-reviewer agent), always run `./isaaclab.sh -f` as part of the review to catch formatting or lint issues early.

## Changelog

- **Update `CHANGELOG.rst` for every change** targeting the source directory. Each extension has its own changelog at `source/<package>/docs/CHANGELOG.rst` (e.g. `source/isaaclab/docs/CHANGELOG.rst`, `source/isaaclab_physx/docs/CHANGELOG.rst`).
- **Always create a new version heading.** Never add entries to an existing version — they are released and immutable. Bump the patch version (e.g. `1.5.0` → `1.5.1`) and use today's date.
- **Bump `config/extension.toml` to match.** When creating a new changelog version, update the `version` field in `source/<package>/config/extension.toml` to the same version string.
- **Determine which changelog(s) to update** by looking at which `source/<package>/` directories your changes touch. A single PR may require entries in multiple changelogs.
- Use **past tense** matching the section header: "Added X", "Fixed Y", "Changed Z".
- Place entries under the correct category: `Added`, `Changed`, `Deprecated`, `Removed`, or `Fixed`.
- Avoid internal implementation details users wouldn't understand.
- **For `Deprecated`, `Changed`, and `Removed` entries, include migration guidance.**
  - Example: "Deprecated `Articulation.A` in favor of `Articulation.B`."
- Use Sphinx cross-reference roles for class/method/module names.

### RST formatting reference

```
X.Y.Z (YYYY-MM-DD)
~~~~~~~~~~~~~~~~~~

Added
^^^^^

* Added :class:`~package.ClassName` to support feature X.

Fixed
^^^^^

* Fixed edge case in :meth:`~package.ClassName.method` where input was
  not validated, causing ``AttributeError`` at runtime.
```

Key formatting rules:
- Version heading: underline with `~` (tildes), must be at least as long as the heading text.
- Category heading: underline with `^` (carets).
- Entries: `* ` prefix, continuation lines indented by 2 spaces.
- Blank line between the last entry and the next version heading.

## Commit and Pull Request Guidelines

Follow conventional commit message practices.

- **Use feature branches**: All development work should be on branches named `<username>/feature-desc` (e.g., `jdoe/docs-versioning`). Do not commit directly to `main`.
- Keep commits focused and atomic—one logical change per commit.
- Reference related issues in commit messages when applicable.
- **When iterating on PR feedback**, prefer adding new commits over amending existing ones. This avoids force-pushing and lets the reviewer easily verify each change request was addressed.
- **Do not include AI attribution or co-authorship lines** (e.g., "Co-Authored-By: Claude...") in commit messages. Commits should represent human contributions without explicit AI attribution.
- **Commit message format**:
  - Separate subject from body with a blank line
  - Subject: imperative mood, capitalized, ~50 chars, no trailing period
    - Write as a command: "Fix bug" not "Fixed bug" or "Fixes bug"
    - Test: "If applied, this commit will _[your subject]_"
  - Body: wrap at 72 chars, explain _what_ and _why_ (not _how_—the diff shows that)

## File headers and copyright

- New files must use the current year (2026) in the SPDX copyright header:
  ```
  # Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
  # All rights reserved.
  #
  # SPDX-License-Identifier: BSD-3-Clause
  ```
- Do not change the year in existing file headers.

## Sandbox & Networking

- Network access (e.g., `git push`) is blocked by the sandbox. Use `dangerouslyDisableSandbox: true` so the user gets an approval prompt — don't ask them to run it manually.

## GitHub Actions and CI/CD

- IMPORTANT: Pin actions by SHA hash. Use `action@<sha>  # vX.Y.Z` format for supply-chain security. Check existing workflows in `.github/workflows/` for the allowlisted hashes. New actions or versions require repo admin approval to be added to the allowlist.

## Testing Guidelines

- **Always verify regression tests fail without the fix.** When writing a regression test for a bug fix, temporarily revert the fix and run the test to confirm it fails. Then reapply the fix and verify the test passes. This ensures the test actually covers the bug.

### Debugging Warp kernels

**Do not add `wp.printf` to kernels in production code.** Debug prints in Warp kernels affect performance and can produce noisy test output. Use them only in standalone reproduction scripts during development, and always remove them before committing.

To debug Warp kernel behavior:

1. **Write a standalone reproduction script** and run it directly with `./isaaclab.sh -p -c "..."` or `./isaaclab.sh -p script.py`. This keeps stdout visible and avoids the test framework entirely.
2. **Use high-precision format strings** for floating-point debugging (e.g., `wp.printf("val=%.15e\n", x)`) — the default `%f` format hides values smaller than ~1e-6 that can still affect control flow.
3. **Remove all `wp.printf` calls before committing.**

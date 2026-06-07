# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""RobotTAS v1 — Phase 2-UI (narrow A) Day 1-6.

Day 1 (scaffold): argparse + ViewerGL instantiation + dummy side panel.
Day 2 (spec §6.1): STEP selector + 8-value spinboxes + dirty flag + diff preview.
Day 3 (spec §6.1): 3D target markers (log_points blue/red/gray) + STEP-update redraw.
Day 4 (spec §4.5, §6.1): Async invoke threading + Apply/Cancel buttons + state machine
  (IDLE/RUNNING/CANCELLING/DONE) + progress text. Worker thread invokes
  wrapper.invoke_dry_run; UI polls state.latest_result for results.
Day 5 (spec §4.4, §4.8, §6.1): Inline error display (Summary + FAIL list + current STEP
  detail + marker FAIL tint) + baseline JSON hash check for concurrent-edit detection.
Day 6 (spec §4.4, §4.7, §4.8, §6.1): NA-5 backup/restore modal (Restore Backup list
  modal, Reload button with dirty-guard modal, auto-persist tempfile with startup
  restore modal), baseline_mismatch proper modal `[Load fresh / Abort]` replacing Day 5
  inline-only surface, yellow text for current STEP detail, FAIL STEP expanded diag
  panel, `● Unsaved` header indicator, X-close warning notification. Modals serialized
  via ``active_modal`` mutex to prevent imgui popup stacking (pre-impl CC Debate
  2026-04-22 CC2/CC3 HIGH).

Usage (must activate env_isaaclab6 explicitly; ./isaaclab.sh -p uses env_isaaclab
which lacks imgui_bundle):
    source ~/env_isaaclab6/bin/activate
    python thread_isaac_lab/scripts/robottas_v1.py --json thread_isaac_lab/data/waypoints/full_43step.json
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import datetime
import hashlib
import json
import os
import sys
import tempfile
import threading
import time
from pathlib import Path
from typing import Any

DEVICE_WHITELIST = frozenset({"cuda:0", "cuda:1", "cuda:2"})

# Day 2: Display format for float widgets (mm-precision per spec §4.2).
FMT_4F = "%.4f"

# Day 3: 3D marker constants per spec §4.3.
# Radii in meters; colors in 0-1 RGB (alpha defaulted by viewer).
_TARGET_MARKER_RADIUS = 0.015  # [m] — 15mm sphere for target_l/r
_CLIP_MARKER_RADIUS = 0.010  # [m] — 10mm sphere for clip reference points
_COLOR_TARGET_L = (0.0, 0.5, 1.0)  # blue (RGB, 0-1)
_COLOR_TARGET_R = (1.0, 0.2, 0.2)  # red (RGB, 0-1)
_COLOR_CLIP = (0.5, 0.5, 0.5)  # gray (RGB, 0-1)
# Day 5 (§4.4): marker tint on current STEP FAIL status.
_COLOR_TARGET_FAIL = (1.0, 0.5, 0.0)  # orange (RGB, 0-1) — target_l/r FAIL tint

# Day 4: Async invoke timeouts per spec §4.6 (Phase 1b.6 cold 92.85s + 2x margin
# for first invoke; warm 49.41s + 2.4x for subsequent).
_TIMEOUT_COLD_S = 180  # [s] first invoke (cold start)
_TIMEOUT_WARM_S = 120  # [s] subsequent invokes (warm)

# Day 5 (§4.4): inline error display color constants (RGBA, 0-1).
_COLOR_PASS = (0.0, 0.8, 0.0, 1.0)  # green — status PASS
_COLOR_FAIL = (0.9, 0.2, 0.2, 1.0)  # red — status FAIL
_COLOR_UNKNOWN = (0.7, 0.7, 0.7, 1.0)  # gray — status missing/unknown

# Day 5 (CC2 MED 2026-04-22): summary FAIL list cap to fit 300px side panel.
_FAIL_LIST_MAX = 10

# Day 6 (spec §4.7 L379 (b), pre-impl Debate CC4 MED + CC6 NHA missing): header
# dirty-indicator color (RGBA, 0-1) — red visible against the ViewerGL dark theme.
_COLOR_UNSAVED_INDICATOR = (1.0, 0.2, 0.2, 1.0)

# Day 6 (spec §4.4 L214, Option α rs承認 2026-04-22): current STEP "yellow background"
# implemented as YELLOW TEXT via push_style_color(Col_.Text) — Day 5 _colored_text
# pattern precedent (vs Col_.ChildBg begin_child alternative which would add border
# + framepadding, disrupting 300px side panel layout).
_COLOR_CURRENT_STEP_HIGHLIGHT = (1.0, 1.0, 0.2, 1.0)

# Day 6 (spec §4.7 L380, pre-impl Debate CC3 HIGH X-close data loss): autopersist
# debounce must be short enough to bound data loss on SIGKILL/X-close. 0.5s is the
# balance between disk I/O and worst-case loss ceiling (chosen over spec "1 秒 interval"
# wording since spec allows either-or phrasing "毎 frame 末 (or debounce 1 秒 interval)"
# and the Debate flagged 1s as unsafe).
_AUTOPERSIST_DEBOUNCE_S = 0.5

# Day 6 (spec §4.7 L380): autopersist schema version for forward-compat.
# Restore flow rejects autopersist files with different schema_version.
_AUTOPERSIST_SCHEMA_VERSION = 1

# Day 6: stale autopersist expiration (24 hours). Older tempfiles are auto-deleted
# at startup without offering restore (pre-impl Debate CC3 M7).
_AUTOPERSIST_STALE_AGE_S = 24 * 3600

# Day 6 (CC4 H1, spec §4.7 L382 step 2-3): SSOT 43STEP canonical hash bootstrap
# seed. Used by `_load_recorded_hash` first-run path when no prior sidecar exists.
# Sourced from vault `thread-vault/10-SSOT-Integrity-43STEP/Phase2a-pre-execution-log.md`
# L201 (canonical baseline `4d60a2b4...c442b786`, schema version=2). The sidecar
# evolves from this seed via `_bless_current_baseline` (Apply success and
# `ssot43_canonical_drift` [Load fresh]); it is NOT the long-term canonical anchor
# — see Day 6 close report semantic concession + Day 7 hardening item A7
# (two-tier check) for the canonical-anchored design (Debate #2 CC6-v2 NHA #1+#3).
_SSOT_43STEP_BOOTSTRAP_HASH = "4d60a2b4a5f7f15fd0d5cefc607c0af9f1f15f6da7148889357c7562c442b786"
# Debate #2 CC4-v2 C4: paste-corruption guard at module load.
assert (
    len(_SSOT_43STEP_BOOTSTRAP_HASH) == 64
    and all(c in "0123456789abcdef" for c in _SSOT_43STEP_BOOTSTRAP_HASH)
), "_SSOT_43STEP_BOOTSTRAP_HASH must be 64-char lowercase sha256 hex"

# Day 6 (CC4 H1): recorded-hash sidecar schema version + tempfile prefix.
_RECORDED_HASH_SCHEMA_VERSION = 1
# Debate #2 CC5-v2 C3 + CC4-v2 C5: single source of truth — used by both
# `_write_recorded_hash` (mkstemp prefix) and main() orphan sweep glob.
_RECORDED_HASH_TMP_PREFIX = ".robottas_recorded_hash_"


def _parse_args() -> argparse.Namespace:
    """Parse CLI arguments. Day 1 minimal: --json + --device."""
    parser = argparse.ArgumentParser(
        description="RobotTAS v1 - Phase 2-UI (narrow A) Day 1-2 scaffold",
    )
    parser.add_argument(
        "--json",
        type=Path,
        required=True,
        help="Path to waypoint JSON (e.g., data/waypoints/full_43step.json)",
    )
    parser.add_argument(
        "--device",
        type=str,
        default="cuda:0",
        choices=sorted(DEVICE_WHITELIST),
        help="CUDA device (cuda:0/1/2, spec §5.2 whitelist)",
    )
    # Day 6 (CC4 H1, NHA #2): bypass startup SSOT 43STEP hash check (CI / Day 7 gate).
    # Production UI sessions should NEVER pass this flag; intended for headless
    # automation where the modal would block.
    parser.add_argument(
        "--skip-hash-check",
        action="store_true",
        help="Skip startup SSOT 43STEP hash drift check (CI/Day 7 gate use only)",
    )
    return parser.parse_args()


def _load_waypoint_json(json_path: Path) -> dict[str, Any]:
    """Load waypoint JSON. Day 1 minimal: existence + parse only."""
    if not json_path.is_file():
        sys.exit(f"JSON path not found: {json_path}")
    try:
        with json_path.open("r") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        sys.exit(f"JSON parse error at {json_path}: {e}")
    return data


def _compute_json_file_hash(json_path: Path) -> str:
    """Return sha256 hex digest of the JSON file's raw bytes (Day 5, spec §4.8).

    Used as the concurrent-edit baseline anchor. Refreshed after each successful
    Apply so ``state.baseline_json_hash`` tracks the last-known-good disk state;
    mismatch at next Apply start indicates external editor wrote the file.

    Args:
        json_path: Path to the waypoint JSON file.

    Returns:
        64-char lowercase hex string, or empty string on OSError (non-fatal).
    """
    try:
        with json_path.open("rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except OSError:
        return ""


def _import_heavy_deps():
    """Late-import heavy deps (imgui_bundle + newton.viewer + warp + task_config).

    Keeping heavy imports inside this function lets argparse --help and
    basic JSON validation (and the RobotTASState class import) run without
    env_isaaclab6 active, which lets Day 1-3 L1 tests execute via the
    standard test venv.

    Day 3 additions:
      - warp (wp): required by log_points which takes wp.array(dtype=wp.vec3)
      - task_config: SSOT for TABLE_HEIGHT + CLIP_POSITIONS (spec §4.3 literal).
        Imported via relative sys.path append (task_config has no heavy deps
        per inspection; lightweight even in env_isaaclab).

    Day 4 additions:
      - robottas_v1_ik_wrapper (wrapper): Phase 1b wrapper for invoke_dry_run,
        atomic_write_json, create_backup (spec §5.1 ★ hash-locked, read-only).
    """
    try:
        import warp as wp
        from imgui_bundle import imgui  # noqa: F401 (re-exported via tuple)
        from newton.viewer import ViewerGL

        # SSOT import for clip z + clip XY (CC3/CC5 HIGH 2026-04-21).
        configs_dir = Path(__file__).resolve().parent.parent / "configs"
        if str(configs_dir) not in sys.path:
            sys.path.insert(0, str(configs_dir))
        import task_config  # noqa: I001 (relative sys.path precedes import)

        # Day 4: Phase 1b wrapper for async invoke (spec §5.1 read-only).
        scripts_dir = Path(__file__).resolve().parent
        if str(scripts_dir) not in sys.path:
            sys.path.insert(0, str(scripts_dir))
        import robottas_v1_ik_wrapper as wrapper  # noqa: I001
    except ImportError as e:
        sys.exit(
            "ImportError: imgui_bundle / newton / warp / task_config / wrapper not available. "
            "Activate env_isaaclab6 explicitly:\n"
            "    source ~/env_isaaclab6/bin/activate\n"
            "Note: ./isaaclab.sh -p uses env_isaaclab which lacks imgui_bundle.\n"
            f"Original error: {e}"
        )
    return imgui, ViewerGL, wp, task_config, wrapper


class RobotTASState:
    """UI state for Day 1-4 scaffold (spec §4.1 / §4.5 / §5.5 / §6.1 Day 2-4).

    Day 1: minimal json_path / data / device / current_step / num_steps.
    Day 2: baseline_steps (deep-copy for diff/restore) + current_edit
    (8-value editable buffer per NA-1) + dirty (event-set bool per spec §5.5)
    + on_step_change (blocks when dirty; silent discard rejected by CC Debate
    2026-04-21 due to spec §4.7 dirty-guard spirit + data-loss risk).
    Day 4: threading fields per spec §4.5 (invoke_thread / cancel_event /
    latest_result / invoke_is_first / invoke_start_t / invoke_thread_generation).
    """

    def __init__(self, json_path: Path, data: dict[str, Any], device: str) -> None:
        self.json_path = json_path
        self.data = data
        self.device = device
        # `or []` guards against explicit `{"steps": None}` (dict.get default only
        # triggers on missing key, not null value; CC2 post-impl LOW 2026-04-21).
        steps_raw = data.get("steps") or []
        self.num_steps = len(steps_raw)
        # Day 2 preflight (CC2-MEDIUM 2026-04-21): empty-steps JSON is unrecoverable
        # for narrow A (NA-1 requires ≥1 STEP) and would IndexError at _snapshot(1).
        if self.num_steps == 0:
            raise ValueError("JSON has no steps - cannot edit empty waypoint list (narrow A requires >=1 STEP)")
        # Day 2: baseline_steps = pristine deep-copy consumed by _snapshot() for
        # diff-preview. Full-row access (atomic_write, restore) is deferred to Day 5+.
        self.baseline_steps: list[dict[str, Any]] = copy.deepcopy(steps_raw)
        self.current_step: int = 1
        self.current_edit: dict[str, list[float] | float] = self._snapshot(1)
        # dirty: event-set attribute (spec §5.5 pattern). Set True by widget-change
        # branches; reset False only on on_step_change (Day 2), Revert (Day 3+),
        # or Apply success (Day 4+). Event-set chosen over structural-diff to avoid
        # float %.4f round-trip false-positives (CC2-MEDIUM 2026-04-21).
        self.dirty: bool = False
        # Day 4: Async invoke state machine fields per spec §4.5.
        # Written by main thread (on_apply_click), read by main + worker.
        # Python GIL makes single-attribute assignment atomic — no lock needed
        # since worker only publishes whole dicts to latest_result (spec §5.3).
        self.invoke_thread: threading.Thread | None = None
        self.cancel_event: threading.Event = threading.Event()
        self.latest_result: dict | None = None  # set by worker, polled by main
        self.invoke_is_first: bool = True  # cold vs warm timeout marker
        self.invoke_start_t: float | None = None  # wall-clock elapsed tracker
        self.invoke_thread_generation: int = 0  # stale-result detection counter
        # Day 5 (spec §4.8): baseline JSON hash for concurrent-edit detection.
        # Computed at load time; refreshed after each successful Apply.
        # Comparison happens at Apply start — mismatch → baseline_mismatch error.
        # Proper modal UI (`Load fresh / Abort`) deferred to Day 6 (§4.7 reload flow).
        self.baseline_json_hash: str = _compute_json_file_hash(json_path)
        # Day 5 (CC5 HIGH 2026-04-22 post-impl): Gate for `_process_done_success`
        # to run EXACTLY once per Apply cycle. Without this, if the user re-edits
        # after a successful Apply (dirty becomes True again) while latest_result
        # still holds {ok: True} in DONE state, the next frame's call to
        # `_process_done_success` would see dirty=True + ok=True and silently
        # clear the user's fresh edits' dirty flag, disabling Apply and allowing
        # STEP nav to overwrite current_edit without warning.
        # Lifecycle: False at init → False at each `_on_apply_click` spawn →
        # True after first DONE+ok dirty clear → stays True until next Apply.
        self.result_consumed: bool = False

        # Day 6 (pre-impl Debate CC2+CC3 HIGH modal mutex): single active-modal name
        # to serialize modal display. imgui.open_popup + begin_popup_modal stacking
        # produces arbitrary z-order; we enforce one-at-a-time via `_open_modal` /
        # `_close_modal` helpers. Valid values: "none", "restore_backup", "reload",
        # "baseline_mismatch", "autopersist_startup".
        self.active_modal: str = "none"

        # Day 6 (spec §4.7 L375): Restore Backup modal — backup file path selected by
        # the user (Path, not int index per CC2 H5 stale-index concern). None = no
        # selection yet. Reset to None on modal open / close / restore-success.
        self.selected_backup_path: Path | None = None

        # Day 6 (spec §4.7 L380 + pre-impl Debate CC2 H1 + CC3 H1 path pollution):
        # autopersist tempfile lives under BACKUP_DIR/autosave/ (wrapper-owned
        # namespace) rather than beside the waypoint JSON. Path is deterministic
        # per json_path stem; format is schema-v1 JSON with baseline_hash + timestamp.
        # Full path is lazily-assigned in main() after heavy deps import (needs wrapper
        # module for BACKUP_DIR); placeholder None here.
        self.autopersist_path: Path | None = None

        # Day 6: monotonic timestamp of last autopersist write. Debounce gate uses
        # `time.monotonic() - last_autopersist_t > _AUTOPERSIST_DEBOUNCE_S`. Initialized
        # to 0.0 so the first-dirty frame writes immediately (catches rapid X-close).
        self.last_autopersist_t: float = 0.0

        # Day 6 (spec §4.7 L379 (c)): one-shot X-close warning notification. Rendered
        # as dismissable banner at startup. True once dismissed; persists across
        # modal sequence so it's only shown once per session launch.
        self.xclose_warning_dismissed: bool = False

        # Day 6 (pre-impl Debate CC5 H2 + CC4 M3): baseline_mismatch acknowledgment.
        # True once user has seen the modal in this mismatch cycle — prevents modal
        # re-opening every frame while state.latest_result still holds the error. Reset
        # to False on next Apply success (via _process_done_success) or reload.
        self.baseline_mismatch_acknowledged: bool = False

        # Day 6 (CC4 H1, spec §4.7 L382 step 2-3): startup-time SSOT 43STEP hash
        # drift detection. `recorded_hash_path` is wrapper-coupled and lazily
        # assigned in main() (parallel to `autopersist_path` deferral above).
        # `exit_requested` flips True ONLY at startup `ssot43_canonical_drift`
        # [Abort]; the main loop checks it to break out cleanly. `pending_modal`
        # is the deferred-modal queue used by the `ssot43_canonical_drift`
        # [Load fresh] handler to chain into `autopersist_startup` modal that
        # was suppressed by modal mutex during startup (Debate #1 CC5 C1 CRIT
        # + Debate #2 CC5-v2 C5 lifecycle clarity).
        self.recorded_hash_path: Path | None = None
        # Debate #2 CC5-v2 C8: explicit False, not None — main loop uses
        # `not state.exit_requested` and None would invert (False truthy).
        self.exit_requested: bool = False
        self.pending_modal: str | None = None


    def _snapshot(self, step_1based: int) -> dict[str, list[float] | float]:
        """Return editable 8-value snapshot from baseline (deep list copy).

        Args:
            step_1based: 1-indexed STEP number (1 .. num_steps).

        Returns:
            Dict with keys target_l/target_r (list[float] length 3) +
            left_finger/right_finger (float). Matches NA-1 8 editable values.
        """
        s = self.baseline_steps[step_1based - 1]
        return {
            "target_l": [float(v) for v in s["target_l"]],
            "target_r": [float(v) for v in s["target_r"]],
            "left_finger": float(s["left_finger"]),
            "right_finger": float(s["right_finger"]),
        }

    def on_step_change(self, new_step: int) -> bool:
        """Attempt a STEP change. Returns True if applied, False if blocked/no-op.

        Day 2 policy (CC Debate 2026-04-21): STEP selector is disabled via
        imgui.begin_disabled(state.dirty) when dirty, so this method rarely
        receives new_step != current_step while dirty. The explicit dirty
        block here is defense-in-depth against future non-UI callers (L1 tests
        and any Day 3+ helpers).

        Silent-discard of dirty edits on STEP nav was rejected by CC2-MEDIUM /
        CC3-HIGH / CC5-CRITICAL (spec §4.7 dirty-guard spirit + data-loss risk).
        Apply (Day 4) or Revert (Day 3+) clear dirty.

        Args:
            new_step: Target STEP (clamped to [1, num_steps]).

        Returns:
            True if applied, False if no-op (same STEP) or blocked (dirty).
        """
        new_step = max(1, min(new_step, self.num_steps))
        if new_step == self.current_step:
            return False
        if self.dirty:
            return False
        self.current_step = new_step
        self.current_edit = self._snapshot(new_step)
        return True


# -----------------------------------------------------------------------------
# Day 4: async invoke pure functions + worker + apply handler + state machine
# (spec §4.5 async model; §4.6 timeout; §5.1 wrapper read-only ★)
# -----------------------------------------------------------------------------


def _compute_timeout(invoke_is_first: bool) -> int:
    """Return subprocess timeout in seconds per spec §4.6.

    Args:
        invoke_is_first: True if this is the first invoke since UI launch
            (cold start needing larger margin over Phase 1b.6 measured 92.85s).

    Returns:
        ``_TIMEOUT_COLD_S`` (180) if first invoke, else ``_TIMEOUT_WARM_S`` (120).
    """
    return _TIMEOUT_COLD_S if invoke_is_first else _TIMEOUT_WARM_S


def _parse_invoke_result(result: Any, cancel_requested: bool) -> dict:
    """Map ``InvokeResult`` + user cancel flag to UI state dict (pure function).

    Per spec §4.5, 6 branching paths in priority order:
      1. cancelled (user requested cancel; wrapper could not interrupt per §4.5
         narrow A limitation, so subprocess ran to completion/timeout — we label
         the outcome as cancelled to reflect user intent regardless of exit)
      2. timeout (result.timed_out True)
      3. killed (result.killed True)
      4. crash (result.returncode not in {0, 1})
      5. no_output (result.updated_steps None; subprocess died mid-write)
      6. ok (returncode 0 or 1 with valid updated_steps)

    Args:
        result: InvokeResult dataclass from ``wrapper.invoke_dry_run``.
        cancel_requested: Whether ``state.cancel_event.is_set()`` when parsed.

    Returns:
        Dict with keys ``ok`` (bool), ``result`` (InvokeResult), and for !ok
        also ``error`` (str category) and ``detail`` (str message).
    """
    if cancel_requested:
        return {
            "ok": False,
            "error": "cancelled",
            "detail": "User requested cancel; subprocess ran to completion/timeout.",
            "result": result,
        }
    if result.timed_out:
        return {
            "ok": False,
            "error": "timeout",
            "detail": "Subprocess exceeded timeout.",
            "result": result,
        }
    if result.killed:
        return {
            "ok": False,
            "error": "killed",
            "detail": "Subprocess killed externally.",
            "result": result,
        }
    if result.returncode not in (0, 1):
        return {
            "ok": False,
            "error": "crash",
            "detail": f"returncode={result.returncode}",
            "result": result,
        }
    if result.updated_steps is None:
        return {
            "ok": False,
            "error": "no_output",
            "detail": "updated_steps is None (JSON read-back failed).",
            "result": result,
        }
    return {"ok": True, "result": result}


def _invoke_worker(
    json_path: Path,
    device: str,
    timeout_s: int,
    state: RobotTASState,
    wrapper: Any,
    generation: int,
) -> None:
    """Run ``wrapper.invoke_dry_run`` in background; write result to state.

    CC2-2 HIGH rule (spec §4.5): worker MUST NOT call imgui/viewer APIs.
    OpenGL context is single-thread (viewer_gl.py:964-974); cross-thread GL
    would corrupt the context. Worker only touches state dict + cancel_event.

    Stale-result detection: worker writes ``state.latest_result`` only if
    ``state.invoke_thread_generation`` still matches the generation captured
    at spawn. Stale writes are logged to stderr and dropped (spec §4.5).

    Args:
        json_path: Waypoint JSON path (already written by ``_on_apply_click``).
        device: CUDA device string (``cuda:0``/``cuda:1``/``cuda:2``).
        timeout_s: Subprocess timeout per ``_compute_timeout``.
        state: UI state object (dict writes only; no read-modify-write).
        wrapper: ``robottas_v1_ik_wrapper`` module.
        generation: Value of ``state.invoke_thread_generation`` at spawn time.
    """
    try:
        result = wrapper.invoke_dry_run(json_path, device, timeout_s=timeout_s)
        result_dict = _parse_invoke_result(result, state.cancel_event.is_set())
    except Exception as e:  # noqa: BLE001 (defensive safety net for worker)
        result_dict = {
            "ok": False,
            "error": "exception",
            "detail": f"{type(e).__name__}: {e}",
            "result": None,
        }
    if state.invoke_thread_generation == generation:
        state.latest_result = result_dict
        state.invoke_is_first = False
    else:
        print(
            f"[robottas_v1] stale invoke result dropped "
            f"(captured gen={generation}, current gen={state.invoke_thread_generation})",
            file=sys.stderr,
        )
    # Defensive: always clear cancel_event at worker exit so next Apply starts clean
    # regardless of spawn-site discipline (CC2 post-impl LOW).
    state.cancel_event.clear()


def _on_apply_click(state: RobotTASState, wrapper: Any) -> None:
    """Apply current_edit to JSON + spawn invoke thread (spec §4.5 / §4.7).

    Flow:
      1. Guard: no-op if already running or nothing dirty.
      2. Build ``new_data`` = deepcopy of state.data + patched current STEP
         (CC2 HIGH 2026-04-21: avoid in-place mutation that would leave
         state.data dirty on write failure).
      3. Create backup (skip_if_exists preserves oldest baseline, Phase 1b
         precedent; full backup/restore UI deferred to Day 6 §4.7).
      4. atomic_write_json — on failure, set latest_result["write_failed"]
         and return WITHOUT touching state.data.
      5. On success: commit state.data = new_data; spawn worker thread.

    Args:
        state: UI state object.
        wrapper: Phase 1b wrapper module with ``invoke_dry_run``,
            ``atomic_write_json``, ``create_backup``.
    """
    # 1. Guard
    if state.invoke_thread and state.invoke_thread.is_alive():
        return  # serialize: ignore concurrent clicks
    if not state.dirty:
        return  # nothing to apply
    # Day 6 post-impl (CC2 MED): defense-in-depth against modal-bypass.
    # UI button gate also checks active_modal (see apply_disabled), but this
    # guard catches programmatic/keyboard paths that might skip the button.
    if state.active_modal != "none":
        return

    # 2. Day 5/6 (spec §4.8): baseline hash check for concurrent-edit detection.
    # If disk content changed since our last Apply (or since startup), another
    # process edited the file — abort this Apply and surface via latest_result
    # AND trigger the Day 6 `[Load fresh / Abort]` modal (spec §4.8 L390).
    # Day 5 used inline-only text; Day 6 keeps inline text as persistent banner
    # (pre-impl Debate CC5 H2) while adding the modal for user action.
    current_disk_hash = _compute_json_file_hash(state.json_path)
    if state.baseline_json_hash and current_disk_hash and current_disk_hash != state.baseline_json_hash:
        state.latest_result = {
            "ok": False,
            "error": "baseline_mismatch",
            "detail": "Another process may have edited the JSON since last Apply.",
            "result": None,
        }
        # Day 6: trigger proper modal (only if no modal is active). Acknowledge
        # flag prevents modal re-opening every Apply click while mismatch persists.
        if not state.baseline_mismatch_acknowledged:
            _open_modal(state, "baseline_mismatch")
        return  # state.data UNCHANGED; no thread spawned

    # 3. Build new_data fail-safe (CC2 HIGH 2026-04-21)
    new_data = copy.deepcopy(state.data)
    step = new_data["steps"][state.current_step - 1]
    step["target_l"] = list(state.current_edit["target_l"])
    step["target_r"] = list(state.current_edit["target_r"])
    step["left_finger"] = float(state.current_edit["left_finger"])
    step["right_finger"] = float(state.current_edit["right_finger"])

    # 4. Backup (data safety net, Day 6 backup/restore UI deferred per §4.7)
    try:
        wrapper.create_backup(state.json_path, skip_if_exists=True)
    except Exception as e:  # noqa: BLE001 (non-fatal; log and proceed)
        print(
            f"[robottas_v1] backup failed (non-fatal): {type(e).__name__}: {e}",
            file=sys.stderr,
        )

    # 5. Atomic write; preserve state.data on failure
    try:
        wrapper.atomic_write_json(state.json_path, new_data)
    except Exception as e:  # noqa: BLE001
        state.latest_result = {
            "ok": False,
            "error": "write_failed",
            "detail": f"{type(e).__name__}: {e}",
            "result": None,
        }
        return  # state.data UNCHANGED; no thread spawned

    # 6. Commit + refresh hash + spawn
    state.data = new_data
    # Day 5: refresh baseline hash so next Apply compares against the just-written content.
    state.baseline_json_hash = _compute_json_file_hash(state.json_path)
    state.cancel_event.clear()
    state.invoke_thread_generation += 1
    state.invoke_start_t = time.time()
    state.latest_result = None  # transition IDLE/DONE → RUNNING
    # Day 5 (CC5 HIGH fix): reset once-per-Apply gate so `_process_done_success`
    # re-runs exactly once for this cycle.
    state.result_consumed = False
    timeout_s = _compute_timeout(state.invoke_is_first)
    state.invoke_thread = threading.Thread(
        target=_invoke_worker,
        args=(
            state.json_path,
            state.device,
            timeout_s,
            state,
            wrapper,
            state.invoke_thread_generation,
        ),
        daemon=True,
    )
    state.invoke_thread.start()


def _invoke_state_machine(state: RobotTASState) -> str:
    """Return current state machine state per spec §4.5.

    Args:
        state: UI state object read for invoke_thread / cancel_event / latest_result.

    Returns:
        One of ``"IDLE"`` / ``"RUNNING"`` / ``"CANCELLING"`` / ``"DONE"``.
    """
    if state.invoke_thread is not None and state.invoke_thread.is_alive():
        return "CANCELLING" if state.cancel_event.is_set() else "RUNNING"
    return "DONE" if state.latest_result is not None else "IDLE"


def _process_done_success(state: RobotTASState) -> None:
    """After DONE + ok, clear dirty and sync baseline for correct future diffs.

    Runs EXACTLY once per Apply cycle via ``state.result_consumed`` gate
    (CC5 HIGH 2026-04-22 post-impl fix). Without the gate, re-edits after
    a successful Apply (user touches a widget → dirty=True again) would be
    silently cleared on the next frame because ``latest_result`` remains in
    DONE+ok state. The gate is reset to False on each ``_on_apply_click``.

    Called once per frame from main loop after end_frame is handled.
    The result dict remains in ``state.latest_result`` so the state machine
    stays in DONE (next Apply click clears it, transitioning DONE → RUNNING).

    Args:
        state: UI state object. On first DONE+ok encounter per Apply cycle,
            mutates ``baseline_steps`` (deepcopy of ``state.data["steps"]``),
            sets ``dirty=False``, and sets ``result_consumed=True``. No-op
            thereafter until next ``_on_apply_click`` resets ``result_consumed``.
    """
    if state.invoke_thread is not None and state.invoke_thread.is_alive():
        return
    if state.latest_result is None:
        return
    if not state.latest_result.get("ok"):
        return
    if state.result_consumed:
        return  # already processed this Apply cycle's success; do not re-clear user's new edits
    if state.dirty:
        # Baseline MUST be updated for diff-preview correctness: after Apply
        # the disk has new values, and next edit should diff against those
        # (not the pre-Apply baseline, which would show misleading old-values).
        state.baseline_steps = copy.deepcopy(state.data["steps"])
        state.dirty = False
        # Day 6: successful Apply means user's edits are now on disk; autopersist
        # tempfile is stale and must be cleaned up.
        _cleanup_autopersist(state)
        # Day 6 CC4 H1 (Debate #1 CC5 C2 + Debate #2 CC5-v2 C2/C4): bless the
        # post-Apply disk content as the new SSOT 43STEP recorded hash. Placement
        # AFTER `state.dirty = False` is intentional — IK validation has succeeded
        # (we're in DONE+ok branch), so the new hash represents a verified state.
        # Nested INSIDE the `if state.dirty` block (Debate #2 CC5-v2 C4) so a
        # spurious DONE+ok with dirty=False (impossible in practice but defensive)
        # does NOT bless an unintentional hash.
        _bless_current_baseline(state)
    # Day 6: successful Apply clears any prior baseline_mismatch_acknowledged
    # flag so the next mismatch event can legitimately open the modal again.
    state.baseline_mismatch_acknowledged = False
    state.result_consumed = True


# -----------------------------------------------------------------------------
# Day 5: error display pure helpers (spec §4.4) + text coloring utility
# -----------------------------------------------------------------------------


def _compute_summary(steps: list[dict]) -> tuple[int, int, list[int]]:
    """Count PASS/FAIL + collect FAIL step indices (spec §4.4 summary).

    Args:
        steps: ``InvokeResult.updated_steps`` list from wrapper (one dict per STEP).

    Returns:
        ``(pass_count, fail_count, fail_step_indices)``. FAIL indices are the
        1-indexed STEP numbers from each dict's ``"step"`` key (fallback 0).
    """
    pass_c = 0
    fail_c = 0
    fail_indices: list[int] = []
    for s in steps:
        status = s.get("status", "")
        if status == "PASS":
            pass_c += 1
        elif status == "FAIL":
            fail_c += 1
            fail_indices.append(int(s.get("step", 0)))
    return pass_c, fail_c, fail_indices


def _format_step_error(step: dict) -> tuple[str, tuple[float, float, float, float]]:
    """Format one STEP's IK validation result for inline display (spec §4.4).

    Defensive formatting: None/NaN err values render as ``"n/a"`` rather than
    crashing the render callback with ``TypeError`` (CC2 HIGH 2026-04-22).
    NaN self-compare trick (``v == v``) filters both ``None`` and ``float('nan')``.

    Args:
        step: One dict from ``InvokeResult.updated_steps`` with keys
            ``step`` / ``err_l_mm`` / ``err_r_mm`` / ``status``.

    Returns:
        ``(display_text, rgba_color)`` tuple. Color is ``_COLOR_PASS`` (green)
        for PASS, ``_COLOR_FAIL`` (red) for FAIL, ``_COLOR_UNKNOWN`` (gray) else.
    """
    step_idx = step.get("step", "?")
    err_l = step.get("err_l_mm")
    err_r = step.get("err_r_mm")
    status = step.get("status", "UNKNOWN")
    # CC2 HIGH 2026-04-22: guard None/NaN to avoid render crash.
    err_l_str = f"{err_l:.2f}" if isinstance(err_l, (int, float)) and err_l == err_l else "n/a"
    err_r_str = f"{err_r:.2f}" if isinstance(err_r, (int, float)) and err_r == err_r else "n/a"
    text = f"STEP {step_idx}: err_l={err_l_str}mm, err_r={err_r_str}mm, {status}"
    if status == "PASS":
        color = _COLOR_PASS
    elif status == "FAIL":
        color = _COLOR_FAIL
    else:
        color = _COLOR_UNKNOWN
    return text, color


def _render_fail_diag(imgui: Any, state: RobotTASState, step_dict: dict) -> None:
    """Render FAIL STEP expanded diag panel (spec §4.4 L218).

    Displays waypoint values (target_l, target_r, left_finger, right_finger) plus
    err_l_mm, err_r_mm, and status. All values formatted with Day 2 mm-precision.
    Uses imgui.text_wrapped to fit the 300px side panel (pre-impl Debate CC5 L1).

    Content follows spec §4.4 L218 literal: ``err_l/r_mm + status + waypoint values``.
    Waypoint values = the 8 editable values per §4.1 NA-1.

    Args:
        imgui: imgui module reference.
        state: UI state (read only for current_step context).
        step_dict: One element of ``InvokeResult.updated_steps``.
    """
    err_l = step_dict.get("err_l_mm")
    err_r = step_dict.get("err_r_mm")
    status = step_dict.get("status", "UNKNOWN")
    # Baseline waypoint values for diag panel — read from state.baseline_steps so
    # we show what was validated (consistent with err_l/r_mm from that submission).
    idx = state.current_step - 1
    if 0 <= idx < len(state.baseline_steps):
        base = state.baseline_steps[idx]
        tl = base.get("target_l", [0.0, 0.0, 0.0])
        tr = base.get("target_r", [0.0, 0.0, 0.0])
        lf = base.get("left_finger", 0.0)
        rf = base.get("right_finger", 0.0)
    else:
        tl, tr, lf, rf = [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], 0.0, 0.0
    err_l_str = f"{err_l:.2f}" if isinstance(err_l, (int, float)) and err_l == err_l else "n/a"
    err_r_str = f"{err_r:.2f}" if isinstance(err_r, (int, float)) and err_r == err_r else "n/a"
    imgui.text_wrapped(f"  status: {status}")
    imgui.text_wrapped(f"  err_l_mm: {err_l_str}")
    imgui.text_wrapped(f"  err_r_mm: {err_r_str}")
    tl_fmt = _format_vec3(tl)
    tr_fmt = _format_vec3(tr)
    imgui.text_wrapped(f"  target_l: ({tl_fmt[0]}, {tl_fmt[1]}, {tl_fmt[2]})")
    imgui.text_wrapped(f"  target_r: ({tr_fmt[0]}, {tr_fmt[1]}, {tr_fmt[2]})")
    imgui.text_wrapped(f"  left_finger: {_format_float(lf)}")
    imgui.text_wrapped(f"  right_finger: {_format_float(rf)}")


def _colored_text(imgui: Any, rgba: tuple[float, float, float, float], text: str) -> None:
    """Render text with color via push_style_color + text_unformatted + pop pattern.

    Avoids ``imgui.text_colored`` (CC3 CRITICAL 2026-04-22): text_colored uses
    printf-format (``Text(fmt, ...)``), reintroducing the ``%`` directive hazard
    that Day 2 migrated away from via text_unformatted discipline. This helper
    preserves that defense-in-depth invariant while still applying the requested
    RGBA color.

    Wraps rgba via ``imgui.ImVec4(*rgba)`` to match the project-wide convention
    used by Newton internal call sites (viewer_gl.py:1739/1796/1802/1854,
    example_replay_viewer.py:100). The raw 4-tuple form relies on undocumented
    nanobind implicit conversion and is not guaranteed to work at runtime
    (CC5 HIGH 2026-04-22 post-impl).

    Args:
        imgui: imgui module reference (late-bound per _make_side_panel_cb pattern).
        rgba: 4-tuple RGBA in 0-1 range.
        text: Display string. Must be pre-formatted (f-string); no printf directives.
    """
    imgui.push_style_color(imgui.Col_.text, imgui.ImVec4(*rgba))
    imgui.text_unformatted(text)
    imgui.pop_style_color()


def _format_float(v: float) -> str:
    """Format a single float with Day 2 mm-precision (4 decimals, no %-directive)."""
    return f"{v:.4f}"


def _format_vec3(v: list[float]) -> tuple[str, str, str]:
    """Format a 3-component float vector with Day 2 mm-precision."""
    return (_format_float(v[0]), _format_float(v[1]), _format_float(v[2]))


# -----------------------------------------------------------------------------
# Day 6: backup/restore/reload/autopersist pure helpers (spec §4.7, §4.8)
#   + modal mutex + startup sequence state machine (pre-impl Debate 2026-04-22)
# -----------------------------------------------------------------------------


def _compute_autopersist_path(wrapper: Any, json_path: Path) -> Path:
    """Return autopersist tempfile path under BACKUP_DIR/autosave/ (wrapper namespace).

    Pre-impl Debate CC2 H1 + CC3 H1 both flagged that placing the tempfile
    beside the waypoint JSON (``json_path.with_suffix(...)``) pollutes
    ``VALID_JSON_DIR`` with stray ``.robottas_tmp_*.json`` fragments and
    risks confusing operators. Moving autopersist to a wrapper-owned
    ``BACKUP_DIR / "autosave"`` subdirectory isolates the churn.

    Args:
        wrapper: ``robottas_v1_ik_wrapper`` module (provides BACKUP_DIR).
        json_path: Waypoint JSON path (used for per-stem disambiguation).

    Returns:
        Absolute path ``BACKUP_DIR / "autosave" / "{stem}.ui_dirty_autosave.tmp"``.
    """
    autosave_dir = Path(wrapper.BACKUP_DIR) / "autosave"
    return autosave_dir / f"{json_path.stem}.ui_dirty_autosave.tmp"


def _write_autopersist(state: RobotTASState) -> None:
    """Atomically write autopersist tempfile with current UI edit state.

    Format (schema v1):
    ```
    {
        "schema_version": 1,
        "timestamp": "2026-04-22T10:00:00+09:00",
        "json_path": "/abs/path/to/full_43step.json",
        "baseline_hash": "sha256hex",
        "current_step": N,
        "current_edit": {"target_l": [...], ..., "right_finger": f}
    }
    ```

    Uses a private atomic write (tempfile.mkstemp + os.replace) rather than
    ``wrapper.atomic_write_json`` to (a) keep the wrapper-contract boundary
    clean and (b) land the mkstemp fragment in the same ``autosave/`` subdir
    so pollution is bounded (pre-impl Debate CC3 H1).

    Args:
        state: UI state object with ``autopersist_path`` assigned by main().
    """
    if state.autopersist_path is None:
        return
    state.autopersist_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": _AUTOPERSIST_SCHEMA_VERSION,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "json_path": str(state.json_path),
        "baseline_hash": state.baseline_json_hash,
        "current_step": state.current_step,
        "current_edit": {
            "target_l": list(state.current_edit["target_l"]),
            "target_r": list(state.current_edit["target_r"]),
            "left_finger": float(state.current_edit["left_finger"]),
            "right_finger": float(state.current_edit["right_finger"]),
        },
    }
    # Post-impl Debate CC2 MED + CC3 LOW: tmp_path init outside try so the except
    # block can reference it even if mkstemp itself raised. fd-leak guarded via
    # explicit os.close in fdopen-failure path (rare under fd exhaustion).
    tmp_path: str | None = None
    fd = -1
    try:
        fd, tmp_path = tempfile.mkstemp(
            dir=state.autopersist_path.parent,
            prefix=".robottas_autosave_",
            suffix=".tmp",
        )
        try:
            f = os.fdopen(fd, "w")
        except Exception:
            os.close(fd)
            raise
        fd = -1  # fdopen now owns the descriptor; don't double-close.
        with f:
            json.dump(payload, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, state.autopersist_path)
        tmp_path = None  # ownership transferred to autopersist_path.
    except Exception:
        if tmp_path is not None:
            try:
                os.unlink(tmp_path)
            except FileNotFoundError:
                pass
        if fd >= 0:
            try:
                os.close(fd)
            except OSError:
                pass
        raise
    state.last_autopersist_t = time.monotonic()


def _validate_autopersist(path: Path, json_path: Path, baseline_hash: str) -> dict | None:
    """Return parsed autopersist payload if valid + relevant; else None.

    Rejects (returns None) for:
      - Missing file / read error
      - Non-JSON / schema_version mismatch
      - ``json_path`` mismatch (autopersist was for a different waypoint file)
      - ``baseline_hash`` mismatch (disk drifted since autopersist was written)
      - Age > ``_AUTOPERSIST_STALE_AGE_S`` (24h default)

    Pre-impl Debate CC3 M7 + CC5 CRITICAL: without these checks a stale or
    corrupt autopersist would trigger a false-positive "restore unsaved edits?"
    modal, potentially loading garbage into ``state.current_edit``.

    Args:
        path: Autopersist tempfile path.
        json_path: Expected waypoint JSON path (absolute).
        baseline_hash: Current baseline JSON sha256 hex.

    Returns:
        Parsed payload dict on success, else None.
    """
    if not path.is_file():
        return None
    try:
        with path.open() as f:
            payload = json.load(f)
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    if payload.get("schema_version") != _AUTOPERSIST_SCHEMA_VERSION:
        return None
    # Day 6 CC4 H1 (Debate #2 CC3-v2 C1 + CC5-v2 C1): forward-compat for
    # `args.json.resolve()` introduction. Pre-revision sessions wrote unresolved
    # path strings; post-revision compares against resolved. Accept either if
    # ANY of (resolved-payload, original-payload, payload-resolved) matches the
    # caller's `json_path` (which is itself resolved by main() startup). Without
    # this triple-compare, pre-revision tempfiles get rejected on the upgrade
    # session and user loses unsaved edits silently.
    payload_path_str = payload.get("json_path")
    if not isinstance(payload_path_str, str):
        return None
    json_path_str = str(json_path)
    if payload_path_str != json_path_str:
        try:
            payload_resolved = str(Path(payload_path_str).resolve())
        except (OSError, RuntimeError):
            payload_resolved = payload_path_str
        if payload_resolved != json_path_str:
            return None
    if payload.get("baseline_hash") != baseline_hash:
        return None
    try:
        mtime = path.stat().st_mtime
    except OSError:
        return None
    age = time.time() - mtime
    if age > _AUTOPERSIST_STALE_AGE_S:
        return None
    return payload


def _compute_recorded_hash_path(wrapper: Any, json_path: Path) -> Path:
    """Return SSOT 43STEP recorded-hash sidecar path under BACKUP_DIR/autosave/.

    Day 6 (CC4 H1, spec §4.7 L382 step 2-3): the sidecar persists the last
    "blessed" baseline JSON hash across UI sessions, enabling startup-time
    detection of external (between-session) modifications to the waypoint JSON.
    Co-located with autopersist tempfiles in ``BACKUP_DIR/autosave/`` (wrapper
    namespace) per pre-impl Debate CC2 H1 + CC3 H1 path-pollution fix; stems
    are disambiguated by suffix (``.recorded_hash.json`` vs
    ``.ui_dirty_autosave.tmp``) so no collision.

    Args:
        wrapper: ``robottas_v1_ik_wrapper`` module (provides ``BACKUP_DIR``).
        json_path: Waypoint JSON path (used for per-stem disambiguation).

    Returns:
        Absolute path ``BACKUP_DIR / "autosave" / "{stem}.recorded_hash.json"``.
    """
    autosave_dir = Path(wrapper.BACKUP_DIR) / "autosave"
    return autosave_dir / f"{json_path.stem}.recorded_hash.json"


def _load_recorded_hash(path: Path) -> tuple[str | None, str]:
    """Load SSOT 43STEP recorded hash from sidecar, distinguishing failure modes.

    Day 6 (CC4 H1, Debate #2 CC4-v2 C1): returns a 2-tuple
    ``(hash_or_None, status)`` rather than collapsing absent / corrupt /
    schema-mismatch / invalid-format into a single ``None`` return. Caller
    inspects ``status`` to decide whether to forensically preserve the
    existing file (corrupt cases) or silently bootstrap (absent case).

    Status values:
        - ``"absent"``: sidecar file does not exist (clean first-run path).
        - ``"ok"``: sidecar parsed and validated; hash is the returned tuple[0].
        - ``"corrupt"``: file exists but is not valid JSON or top-level dict.
        - ``"schema_mismatch"``: ``schema_version`` field missing or != current.
        - ``"invalid_hash"``: ``recorded_hash`` field missing or wrong type/format
          (must be 64-char lowercase hex string).

    All non-``ok`` statuses return ``hash_or_None = None``. Caller MUST NOT
    silently overwrite ``corrupt`` / ``schema_mismatch`` / ``invalid_hash``
    sidecar files; preserve to ``BACKUP_DIR/autosave/.stale/`` for forensic
    recovery (autopersist precedent at main() L1609-1620).

    Args:
        path: Sidecar file path (typically from ``_compute_recorded_hash_path``).

    Returns:
        ``(hash_hex_64_chars, "ok")`` on success, ``(None, "<status>")`` otherwise.
    """
    if not path.is_file():
        return None, "absent"
    try:
        payload = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None, "corrupt"
    if not isinstance(payload, dict):
        return None, "corrupt"
    if payload.get("schema_version") != _RECORDED_HASH_SCHEMA_VERSION:
        return None, "schema_mismatch"
    rec = payload.get("recorded_hash")
    if not isinstance(rec, str) or len(rec) != 64:
        return None, "invalid_hash"
    try:
        int(rec, 16)
    except ValueError:
        return None, "invalid_hash"
    return rec, "ok"


def _write_recorded_hash(state: RobotTASState) -> None:
    """Atomically write the SSOT 43STEP recorded-hash sidecar.

    Day 6 (CC4 H1, Debate #1 CC4 C11 + Debate #2 CC5-v2 C3): atomic write via
    ``tempfile.mkstemp`` + ``os.fdopen`` + ``json.dump`` + ``flush`` +
    ``os.fsync`` + ``os.replace`` (mirrors ``_write_autopersist`` L838-866
    pattern). The mkstemp prefix is ``_RECORDED_HASH_TMP_PREFIX`` so main()'s
    orphan sweep (extended glob) can clean partial-write fragments.

    No-op if ``state.recorded_hash_path is None`` (test isolation;
    `__init__` initialises to None per Debate #1 CC4 C13 + Debate #2 CC5-v2 C7).
    No-op if ``state.baseline_json_hash`` is empty (degenerate hash compute fail).

    Schema v1::

        {
            "schema_version": 1,
            "timestamp": "<iso utc>",
            "json_path": "<absolute path string>",
            "recorded_hash": "<sha256 hex 64 chars>"
        }

    Note: ``json_path`` field is INFORMATIONAL only per Debate #1 CC3 C9 — not
    enforced for sidecar validity. Stem-based filename is the disambiguation key.

    Args:
        state: UI state with ``recorded_hash_path`` and ``baseline_json_hash`` set.

    Raises:
        OSError: On disk write failure (caller wraps via
            ``_bless_current_baseline`` to surface to UI per Debate #2 CC3-v2 C3).
    """
    if state.recorded_hash_path is None or not state.baseline_json_hash:
        return
    state.recorded_hash_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": _RECORDED_HASH_SCHEMA_VERSION,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "json_path": str(state.json_path),
        "recorded_hash": state.baseline_json_hash,
    }
    tmp_path: str | None = None
    fd = -1
    try:
        fd, tmp_path = tempfile.mkstemp(
            dir=state.recorded_hash_path.parent,
            prefix=_RECORDED_HASH_TMP_PREFIX,
            suffix=".tmp",
        )
        try:
            f = os.fdopen(fd, "w")
        except Exception:
            os.close(fd)
            raise
        fd = -1
        with f:
            json.dump(payload, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, state.recorded_hash_path)
        tmp_path = None
    except Exception:
        if tmp_path is not None:
            with contextlib.suppress(FileNotFoundError):
                os.unlink(tmp_path)
        if fd >= 0:
            with contextlib.suppress(OSError):
                os.close(fd)
        raise


def _bless_current_baseline(state: RobotTASState) -> None:
    """Commit current ``state.baseline_json_hash`` as the SSOT 43STEP recorded hash.

    Day 6 (CC4 H1, Debate #1 CC4 C7 + Debate #2 CC4-v2 C3): wraps
    ``_write_recorded_hash`` with UI-surfacing failure handling.

    **Caller set (intentionally narrow per Debate #1 CC4 C7)**:
      - ``_process_done_success``: Apply DONE+ok, IK validation passed → bless.
      - ``ssot43_canonical_drift`` modal [Load fresh]: user explicitly accepted
        the current disk content as the new baseline.

    **NOT called from**:
      - ``_reload_from_disk`` (generic reload, contract preserved).
      - Reload modal [Discard & Reload] (per Debate #1 CC5 C4: explicit user
        recovery action, sidecar deliberately not auto-blessed).
      - Restore Backup confirm chain (per Debate #1 CC5 C3: backup is
        unverified content, blessing it would amplify SSOT drift).
      - Apply-time ``baseline_mismatch`` modal [Load fresh] (per Debate #2
        CC4-v2 C3: runtime mismatch handled by in-memory ``baseline_json_hash``;
        startup variant is the canonical-drift detector).

    On write failure (``OSError``), records the error in ``state.latest_result``
    so the side-panel "Validate" status surfaces "[warn: bless failed]" — without
    this, a silent failure causes false-positive ``ssot43_canonical_drift`` modal
    on the NEXT startup despite legitimate Apply success (Debate #2 CC3-v2 C3 +
    CC5-v2 C2).

    Args:
        state: UI state with ``recorded_hash_path`` set (typically by main()).
    """
    if state.recorded_hash_path is None:
        return
    try:
        _write_recorded_hash(state)
    except OSError as e:
        msg = f"{type(e).__name__}: {e}"
        print(
            f"[robottas_v1] recorded hash write failed (non-fatal): {msg}",
            file=sys.stderr,
        )
        # Surface to UI: existing or new latest_result entry.
        if state.latest_result is None:
            state.latest_result = {
                "ok": False,
                "error": "bless_failed",
                "detail": msg,
                "result": None,
            }
        else:
            state.latest_result.setdefault("bless_warning", msg)


def _cleanup_autopersist(state: RobotTASState) -> None:
    """Remove autopersist tempfile if it exists. Non-fatal on errors.

    Called from (a) ``_process_done_success`` after dirty→clean (Apply success),
    (b) startup modal [Discard] click, (c) Reload / Restore flow success.
    """
    if state.autopersist_path is None:
        return
    try:
        state.autopersist_path.unlink()
    except FileNotFoundError:
        pass
    except OSError as e:
        print(
            f"[robottas_v1] autopersist cleanup failed (non-fatal): {type(e).__name__}: {e}",
            file=sys.stderr,
        )


def _should_autopersist(state: RobotTASState, now: float) -> bool:
    """Return True iff autopersist write should fire on this frame.

    Conditions: dirty flag set + debounce interval elapsed + no active modal
    (modal opens suspend autopersist to avoid writing stale pre-modal state —
    pre-impl Debate CC2 H2).

    Args:
        state: UI state.
        now: ``time.monotonic()`` timestamp for debounce math.
    """
    if not state.dirty:
        return False
    if state.active_modal != "none":
        return False
    return (now - state.last_autopersist_t) > _AUTOPERSIST_DEBOUNCE_S


def _reload_from_disk(state: RobotTASState) -> None:
    """Re-read ``state.json_path`` and rebuild state; preserve current_step via clamp.

    Post-reload state:
      - ``state.data`` = fresh parse from disk
      - ``state.baseline_steps`` = deep-copy of fresh steps
      - ``state.num_steps`` = updated length
      - ``state.current_step`` = ``min(max(1, prev_current_step), new_num_steps)``
        (pre-impl Debate CC2 M2 + CC5 M1: preserve navigation when possible)
      - ``state.current_edit`` = snapshot of new current_step
      - ``state.dirty`` = False
      - ``state.baseline_json_hash`` = recomputed from disk
      - ``state.result_consumed`` = False
      - ``state.latest_result`` = None (transition DONE→IDLE)
      - ``state.baseline_mismatch_acknowledged`` = False
      - autopersist tempfile unlinked

    Used by: Reload button (direct), Reload modal [Discard & Reload], Restore Backup
    confirm (auto-chained per pre-impl Debate CC3 H3 + CC5 avoidance of data clobber).

    Pre-condition: caller MUST ensure no worker thread is alive. Reload during
    RUNNING is blocked at UI gate (pre-impl Debate CC2 H4 + CC5 H1).

    Post-impl Debate CC2 MED + CC3 MED: read raw bytes ONCE and derive both the
    parsed dict and sha256 hash from the same byte sequence. Eliminates the TOCTOU
    window between `json.load` and a subsequent `_compute_json_file_hash` read
    where a concurrent writer could slip a different file content between the two
    disk reads. All new values are built into locals first, then assigned to
    state in a single atomic block at the bottom — partial-update on mid-flow
    exception is prevented.
    """
    with state.json_path.open("rb") as f:
        raw_bytes = f.read()
    try:
        data = json.loads(raw_bytes.decode("utf-8"))
    except UnicodeDecodeError as e:
        raise json.JSONDecodeError(f"non-utf8 bytes: {e}", "", 0) from e
    steps_raw = data.get("steps") or []
    if len(steps_raw) == 0:
        raise ValueError("Reload target JSON has no steps")

    # Build ALL new values into locals; assign only after every step succeeds.
    new_num_steps = len(steps_raw)
    new_baseline = copy.deepcopy(steps_raw)
    new_current_step = min(max(1, state.current_step), new_num_steps)
    s = new_baseline[new_current_step - 1]
    new_current_edit = {
        "target_l": [float(v) for v in s["target_l"]],
        "target_r": [float(v) for v in s["target_r"]],
        "left_finger": float(s["left_finger"]),
        "right_finger": float(s["right_finger"]),
    }
    new_hash = hashlib.sha256(raw_bytes).hexdigest()

    # Atomic assignment block.
    state.data = data
    state.num_steps = new_num_steps
    state.baseline_steps = new_baseline
    state.current_step = new_current_step
    state.current_edit = new_current_edit
    state.dirty = False
    state.baseline_json_hash = new_hash
    state.result_consumed = False
    state.latest_result = None
    state.baseline_mismatch_acknowledged = False
    _cleanup_autopersist(state)


def _current_step_fail_status(state: RobotTASState) -> str | None:
    """Return "PASS" / "FAIL" / None for the current STEP in latest_result.

    Returns None if result absent/!ok/step out of range. Used by (a) FAIL diag
    panel trigger (show when FAIL) and (b) marker FAIL tint (Day 5).
    """
    if state.latest_result is None or not state.latest_result.get("ok"):
        return None
    result = state.latest_result.get("result")
    steps = (result.updated_steps or []) if result else []
    idx = state.current_step - 1
    if not (0 <= idx < len(steps)):
        return None
    status = steps[idx].get("status")
    return status if isinstance(status, str) else None


def _open_modal(state: RobotTASState, name: str) -> bool:
    """Request a modal open, enforcing single-modal mutex.

    Returns True if this call acquired the modal; False if another modal is
    already active (caller should defer the trigger or drop the request).

    Pre-impl Debate CC2 H3 + CC3 M6: without mutex, multiple open_popup calls
    stack in arbitrary z-order and input events may route to the wrong modal.
    """
    if state.active_modal not in ("none", name):
        return False
    state.active_modal = name
    return True


def _close_modal(state: RobotTASState) -> None:
    """Release the active modal."""
    state.active_modal = "none"


def _make_side_panel_cb(state: RobotTASState, imgui, wrapper: Any):
    """Build the Day 1-4 side panel callback.

    Day 1: header + static info (JSON / device / num_steps).
    Day 2: STEP selector (input_int, locked when dirty) + 8-value edit widgets
    (input_float3 x2, input_float x2) + dirty indicator (plain text) + diff
    preview (string-format comparison per spec §6.1).
    Day 4: Apply + Cancel buttons (begin_disabled per state machine) + progress
    text (elapsed/timeout countdown) + minimal error text on DONE+!ok (full
    PASS/FAIL summary deferred to Day 5).

    All text uses text_unformatted (CC2-HIGH 2026-04-21: defense-in-depth against
    printf-directive hazard on user-supplied `%` characters). The full side panel
    (§4.4 validation display / §5 preview / §6 Apply / §7 result / §8 backup /
    §9 footer) is completed Day 5-6 per spec §6.1.
    """

    def _render(_ctx):
        # --- Header (Day 1) ---
        # ASCII hyphen only (imgui default font lacks em-dash U+2014).
        # Labels and messages shortened for ViewerGL 300px side panel (viewer_gl.py:1589,
        # no_resize flag); rs visual check 2026-04-21 reported text truncation. Unit
        # info consolidated in header; text_wrapped used for multi-line messages.
        imgui.text_unformatted("RobotTAS v1 narrow A")
        imgui.separator()
        imgui.text_unformatted(f"JSON: {state.json_path.name}")
        imgui.text_unformatted(f"Device: {state.device}  Units: m")
        imgui.text_unformatted(f"STEPs: {state.num_steps}")
        # Day 6 (spec §4.7 L379 (b)): `● Unsaved` indicator. Persistent red-colored
        # text whenever dirty=True; hidden when clean. Provides always-visible
        # feedback about unsaved edits, complementing the [dirty]/[clean] line below.
        if state.dirty:
            _colored_text(imgui, _COLOR_UNSAVED_INDICATOR, "● Unsaved edits")
        imgui.separator()

        # Day 6 (spec §4.7 L379 (c)): one-shot X-close warning notification. Shown
        # until user dismisses it via [OK]. Informs user that OS window-X cannot be
        # intercepted, so autopersist is the data-safety path.
        if not state.xclose_warning_dismissed:
            imgui.text_wrapped(
                "Note: OS window [X] cannot be intercepted. Unsaved edits "
                "auto-persist to a backup; prefer normal Apply before closing."
            )
            if imgui.button("OK##xclose_warn"):
                state.xclose_warning_dismissed = True
            imgui.separator()

        # --- Day 2: STEP selector + edit state ---
        imgui.text_unformatted(f"Editing STEP {state.current_step}:")

        # STEP selector - disabled when dirty (spec §6.1 Day 2 + CC Debate 2026-04-21).
        # Day 6 CC4 H1 (Debate #2 CC3-v2 C2): also disabled while ANY modal is
        # active to close the 1-frame race between modal close and chained modal
        # open (e.g., ssot43_canonical_drift [Load fresh] → autopersist_startup),
        # during which dirty=False would otherwise allow STEP nav and miss the
        # chained restore prompt.
        imgui.begin_disabled(state.dirty or state.active_modal != "none")
        changed_step, new_step = imgui.input_int("STEP", state.current_step, 1, 5)
        imgui.end_disabled()
        if changed_step:
            state.on_step_change(new_step)

        # Dirty indicator uses text_wrapped for auto-wrap in the 300px panel.
        if state.dirty:
            imgui.text_wrapped(f"[dirty] STEP {state.current_step}: unsaved edits. Apply/Revert to clear.")
        else:
            imgui.text_unformatted("[clean] No unsaved edits.")

        imgui.separator()

        # --- Day 2: 8-value edit widgets (always enabled) ---
        # Labels without "(m)" suffix to fit panel; units in header.

        changed_tl, state.current_edit["target_l"] = imgui.input_float3(
            "target_l", state.current_edit["target_l"], FMT_4F
        )
        if changed_tl:
            state.dirty = True

        changed_tr, state.current_edit["target_r"] = imgui.input_float3(
            "target_r", state.current_edit["target_r"], FMT_4F
        )
        if changed_tr:
            state.dirty = True

        changed_lf, state.current_edit["left_finger"] = imgui.input_float(
            "left_finger",
            state.current_edit["left_finger"],
            step=0.001,
            step_fast=0.005,
            format=FMT_4F,
        )
        if changed_lf:
            state.dirty = True

        changed_rf, state.current_edit["right_finger"] = imgui.input_float(
            "right_finger",
            state.current_edit["right_finger"],
            step=0.001,
            step_fast=0.005,
            format=FMT_4F,
        )
        if changed_rf:
            state.dirty = True

        imgui.separator()

        # --- Day 2: Diff preview (text_wrapped to fit 300px panel) ---
        imgui.text_unformatted("Diff (old -> new):")
        baseline = state._snapshot(state.current_step)
        diff_any = False
        for key in ("target_l", "target_r"):
            b_fmt = _format_vec3(baseline[key])
            c_fmt = _format_vec3(state.current_edit[key])
            if b_fmt != c_fmt:
                imgui.text_wrapped(
                    f"  {key}: ({b_fmt[0]}, {b_fmt[1]}, {b_fmt[2]}) -> ({c_fmt[0]}, {c_fmt[1]}, {c_fmt[2]})"
                )
                diff_any = True
        for key in ("left_finger", "right_finger"):
            b_fmt = _format_float(baseline[key])
            c_fmt = _format_float(state.current_edit[key])
            if b_fmt != c_fmt:
                imgui.text_wrapped(f"  {key}: {b_fmt} -> {c_fmt}")
                diff_any = True
        if not diff_any:
            imgui.text_unformatted("  (no visible changes)")

        imgui.separator()

        # --- Day 6: Backup / Restore / Reload (spec §4.7) ---
        # Backup/Restore section placed before Validate per spec §9 footer concept.
        # Both buttons are disabled during RUNNING/CANCELLING (apply_disabled mirror)
        # + while any modal is active (modal mutex guard per pre-impl Debate CC2 H3).
        imgui.text_unformatted("Backup/Restore:")
        _ui_state_pre = _invoke_state_machine(state)
        backup_disabled = _ui_state_pre in ("RUNNING", "CANCELLING") or state.active_modal != "none"

        imgui.begin_disabled(backup_disabled)
        restore_clicked = imgui.button("Restore Backup...")
        imgui.end_disabled()
        if restore_clicked and _open_modal(state, "restore_backup"):
            state.selected_backup_path = None

        imgui.same_line()

        imgui.begin_disabled(backup_disabled)
        reload_clicked = imgui.button("Reload JSON")
        imgui.end_disabled()
        if reload_clicked:
            if state.dirty:
                # Dirty-guard (spec §4.7 L377): defer reload to modal confirmation.
                _open_modal(state, "reload")
            else:
                # Clean state: direct reload.
                try:
                    _reload_from_disk(state)
                except (OSError, json.JSONDecodeError, ValueError) as e:
                    state.latest_result = {
                        "ok": False,
                        "error": "reload_failed",
                        "detail": f"{type(e).__name__}: {e}",
                        "result": None,
                    }

        imgui.separator()

        # --- Day 4: Async invoke (Apply / Cancel / progress) ---
        # State machine per spec §4.5: IDLE -> RUNNING -> (Cancel) CANCELLING
        # -> DONE -> IDLE (transition via next Apply click).
        imgui.text_unformatted("Validate:")
        ui_state = _invoke_state_machine(state)

        # Apply button - disabled during RUNNING/CANCELLING, when clean, OR while
        # any modal is active (post-impl Debate CC2/CC5 convergence: defense-in-depth
        # against imgui modal-overlay input-bypass edge cases).
        apply_disabled = (
            ui_state in ("RUNNING", "CANCELLING")
            or not state.dirty
            or state.active_modal != "none"
        )
        imgui.begin_disabled(apply_disabled)
        apply_clicked = imgui.button("Apply + Validate")
        imgui.end_disabled()
        if apply_clicked:
            _on_apply_click(state, wrapper)

        imgui.same_line()

        # Cancel button - only enabled during RUNNING (cancel during CANCELLING
        # is a no-op; during IDLE/DONE the event should stay clear).
        imgui.begin_disabled(ui_state != "RUNNING")
        cancel_clicked = imgui.button("Cancel")
        imgui.end_disabled()
        if cancel_clicked:
            state.cancel_event.set()

        # Progress / status text per state.
        if ui_state == "RUNNING":
            elapsed = time.time() - (state.invoke_start_t or time.time())
            timeout_s = _compute_timeout(state.invoke_is_first)
            imgui.text_wrapped(f"Running... {elapsed:.0f}s / {timeout_s}s")
        elif ui_state == "CANCELLING":
            # spec §4.5: subprocess runs to timeout (wrapper cancel not
            # supported in narrow A). UI keeps Apply disabled and shows
            # remaining wait so user knows Cancel is soft-cancel.
            elapsed = time.time() - (state.invoke_start_t or time.time())
            timeout_s = _compute_timeout(state.invoke_is_first)
            remaining = max(0.0, timeout_s - elapsed)
            imgui.text_wrapped(f"Cancelling... subprocess up to {remaining:.0f}s remaining")
        elif ui_state == "DONE":
            # Day 4: error hint on !ok path.
            # Day 5 (§4.4): expanded display on ok path — summary + FAIL list + current STEP detail.
            # Bind latest_result to a local pointer once to avoid torn reads
            # across worker-side writes (spec §5.3 GIL atomic dict pointer swap).
            result_local = state.latest_result or {}
            if result_local.get("ok"):
                invoke_result = result_local.get("result")
                steps = (invoke_result.updated_steps or []) if invoke_result else []
                if steps:
                    pass_c, fail_c, fail_indices = _compute_summary(steps)
                    total = pass_c + fail_c
                    if fail_c == 0:
                        _colored_text(imgui, _COLOR_PASS, f"Summary: {pass_c}/{total} PASS")
                    else:
                        _colored_text(
                            imgui,
                            _COLOR_FAIL,
                            f"Summary: {pass_c}/{total} PASS, {fail_c} FAIL",
                        )
                        # Cap FAIL list to _FAIL_LIST_MAX entries to fit 300px panel
                        # (CC2 MED 2026-04-22: text_wrapped + long list overflows layout).
                        display = fail_indices[:_FAIL_LIST_MAX]
                        suffix = (
                            f" (+{len(fail_indices) - _FAIL_LIST_MAX} more)"
                            if len(fail_indices) > _FAIL_LIST_MAX
                            else ""
                        )
                        imgui.text_wrapped(f"FAIL at: {', '.join(str(i) for i in display)}{suffix}")
                    # Current STEP detail (spec §4.4 inline err_l/r_mm + status)
                    idx = state.current_step - 1
                    if 0 <= idx < len(steps):
                        # Day 6 (spec §4.4 L214, Option α rs承認): yellow ▶ indicator
                        # for "current STEP 強調" — preserves PASS/FAIL color discipline
                        # from Day 5 _format_step_error while meeting spec L214 intent
                        # (emphasizing the current STEP vs others).
                        _colored_text(imgui, _COLOR_CURRENT_STEP_HIGHLIGHT, "▶")
                        imgui.same_line()
                        cur_text, cur_color = _format_step_error(steps[idx])
                        _colored_text(imgui, cur_color, cur_text)
                        # Day 6 (spec §4.4 L218): FAIL STEP 選択時, 追加 panel に
                        # err_l/r_mm + status + waypoint values 展開。Trigger: current
                        # STEP has status=="FAIL" (pre-impl Debate CC2 M3 resolution:
                        # tie to current_step per spec L218 「選択時」= 現 STEP being
                        # edited, no separate click required).
                        if steps[idx].get("status") == "FAIL":
                            if imgui.collapsing_header(
                                f"FAIL diagnostics (STEP {state.current_step})##fail_diag",
                                imgui.TreeNodeFlags_.default_open.value,
                            ):
                                _render_fail_diag(imgui, state, steps[idx])
            elif result_local:
                # Day 4/5 error hint retained for !ok path as PERSISTENT BANNER
                # (pre-impl Debate CC5 H2: baseline_mismatch modal is additive;
                # inline text stays visible so user sees state even after modal dismiss).
                # Post-impl Debate CC5 MED: differentiate filesystem-origin errors
                # from IK validation errors via prefix — prevents conflation between
                # "IK validation failed" and "reload/restore failed".
                error_type = result_local.get("error", "unknown")
                fs_errors = {"reload_failed", "restore_failed", "write_failed", "baseline_mismatch"}
                prefix = "[fs error:" if error_type in fs_errors else "[error:"
                _colored_text(imgui, _COLOR_FAIL, f"{prefix} {error_type}]")
                # On baseline_mismatch Abort, user is "stuck" until Reload; surface
                # advisory (post-impl Debate CC2 H1 PARTIAL ACCEPT).
                if error_type == "baseline_mismatch" and state.baseline_mismatch_acknowledged:
                    imgui.text_wrapped("Click 'Reload JSON' to recover against fresh baseline.")

        # --- Day 6: modal rendering block (spec §4.7 / §4.8) ---
        # All modals serialized via state.active_modal mutex. imgui.open_popup
        # is called once on button click (state.active_modal transition);
        # begin_popup_modal renders on every frame until closed. end_popup is
        # the only allowed return path (matches imgui_bundle's invariant).

        # Modal 1: Restore Backup (spec §4.7 L375)
        if state.active_modal == "restore_backup":
            imgui.open_popup("Restore Backup##modal")
        opened_restore, _ = imgui.begin_popup_modal(
            "Restore Backup##modal",
            None,
            imgui.WindowFlags_.always_auto_resize.value,
        )
        if opened_restore:
            imgui.text_unformatted("Select a backup to restore:")
            imgui.separator()
            # Re-query every frame (pre-impl Debate CC2 H5): list may change if
            # external process creates new backups. Cost is trivial (small dir).
            backups = wrapper.list_backups()
            if not backups:
                imgui.text_wrapped("(No backups available for this JSON.)")
            else:
                for bk in backups:
                    is_selected = state.selected_backup_path == bk
                    if imgui.selectable(bk.name, is_selected)[0]:
                        state.selected_backup_path = bk
            imgui.separator()
            can_restore = state.selected_backup_path is not None
            imgui.begin_disabled(not can_restore)
            do_restore = imgui.button("Restore##confirm")
            imgui.end_disabled()
            if do_restore and state.selected_backup_path is not None:
                try:
                    wrapper.restore_backup(state.selected_backup_path, state.json_path)
                    # Chain into reload so state.data + baseline_steps match new disk.
                    _reload_from_disk(state)
                except (OSError, ValueError, json.JSONDecodeError) as e:
                    state.latest_result = {
                        "ok": False,
                        "error": "restore_failed",
                        "detail": f"{type(e).__name__}: {e}",
                        "result": None,
                    }
                _close_modal(state)
                state.selected_backup_path = None
                imgui.close_current_popup()
            imgui.same_line()
            if imgui.button("Cancel##restore"):
                _close_modal(state)
                state.selected_backup_path = None
                imgui.close_current_popup()
            imgui.end_popup()

        # Modal 2: Reload dirty-guard (spec §4.7 L377)
        if state.active_modal == "reload":
            imgui.open_popup("Confirm Reload##modal")
        opened_reload, _ = imgui.begin_popup_modal(
            "Confirm Reload##modal",
            None,
            imgui.WindowFlags_.always_auto_resize.value,
        )
        if opened_reload:
            imgui.text_wrapped("Unsaved changes will be lost. Continue?")
            if imgui.button("Discard & Reload##confirm"):
                try:
                    _reload_from_disk(state)
                except (OSError, json.JSONDecodeError, ValueError) as e:
                    state.latest_result = {
                        "ok": False,
                        "error": "reload_failed",
                        "detail": f"{type(e).__name__}: {e}",
                        "result": None,
                    }
                _close_modal(state)
                imgui.close_current_popup()
            imgui.same_line()
            if imgui.button("Cancel##reload"):
                _close_modal(state)
                imgui.close_current_popup()
            imgui.end_popup()

        # Modal 3: baseline_mismatch (spec §4.8 L390)
        if state.active_modal == "baseline_mismatch":
            imgui.open_popup("Baseline JSON hash mismatch##modal")
        opened_bmm, _ = imgui.begin_popup_modal(
            "Baseline JSON hash mismatch##modal",
            None,
            imgui.WindowFlags_.always_auto_resize.value,
        )
        if opened_bmm:
            # Spec §4.8 L390 verbatim: "Baseline JSON hash mismatch —
            # another process may have edited. [Load fresh / Abort]".
            # Post-impl Debate CC3 H1 + CC4 L: em-dash U+2014 replaced with ASCII " - "
            # per L1033 comment ("imgui default font lacks em-dash"). Spec §4.8 L390
            # uses em-dash; runtime font fallback would render as missing-glyph box.
            imgui.text_wrapped("Baseline JSON hash mismatch - another process may have edited.")
            if imgui.button("Load fresh##confirm"):
                try:
                    # _reload_from_disk resets baseline_mismatch_acknowledged=False so a
                    # future mismatch (post-reload external edit) can open the modal again.
                    # Do NOT re-assert True here (post-impl Debate CC2/CC3/CC5 3-agent
                    # convergence: L1375 in original impl blocked 2nd-mismatch modal).
                    _reload_from_disk(state)
                except (OSError, json.JSONDecodeError, ValueError) as e:
                    state.latest_result = {
                        "ok": False,
                        "error": "reload_failed",
                        "detail": f"{type(e).__name__}: {e}",
                        "result": None,
                    }
                _close_modal(state)
                imgui.close_current_popup()
            imgui.same_line()
            if imgui.button("Abort##bmm"):
                # Abort keeps user's in-memory edits; acknowledge flag prevents modal
                # from re-opening on every subsequent Apply during THIS same mismatch
                # cycle (i.e., while disk hash stays at the same mismatching value).
                state.baseline_mismatch_acknowledged = True
                _close_modal(state)
                imgui.close_current_popup()
            imgui.end_popup()

        # Modal 5: ssot43_canonical_drift (Day 6 CC4 H1, spec §4.7 L382 step 2-3
        # + §4.8 L390 startup variant). NEW separate modal name (per Debate #1
        # CC4 C6 + Debate #2 CC4-v2 C6) to avoid baseline_mismatch_acknowledged
        # cross-contamination with Apply-time `baseline_mismatch` modal.
        # Source-order placement BEFORE Modal 4 (autopersist_startup) is
        # intentional — [Load fresh] handler chains `pending_modal` to
        # autopersist_startup, which then renders in the same frame because
        # Modal 4's `imgui.open_popup` block executes after this one.
        if state.active_modal == "ssot43_canonical_drift":
            imgui.open_popup("SSOT 43STEP canonical hash drift##modal")
        opened_drift, _ = imgui.begin_popup_modal(
            "SSOT 43STEP canonical hash drift##modal",
            None,
            imgui.WindowFlags_.always_auto_resize.value,
        )
        if opened_drift:
            # Spec §4.8 L390 verbatim base text (ASCII " - " per post-impl
            # Debate CC3 H1 em-dash precedent + Debate #2 CC2-v2 C1) plus a
            # secondary line for startup-context disambiguation.
            imgui.text_wrapped(
                "Baseline JSON hash mismatch - another process may have edited."
            )
            imgui.text_wrapped(
                "Detected at startup before edit loop began. [Load fresh] accepts "
                "the current disk content as the new SSOT 43STEP baseline; [Abort] "
                "exits without modifying anything."
            )
            if imgui.button("Load fresh##drift_confirm"):
                # User explicitly accepts current disk state as the new baseline.
                # File was already loaded at startup — do NOT call _reload_from_disk
                # (Debate #2 CC2-v2 C2 ordering fix: avoid invalidating autopersist
                # payload's baseline_hash field by changing in-memory hash).
                _bless_current_baseline(state)
                _close_modal(state)
                imgui.close_current_popup()
                # Chain to deferred autopersist modal (Debate #1 CC5 C1 CRIT +
                # Debate #2 CC5-v2 C5 lifecycle): if autopersist was suppressed
                # by modal mutex during startup, fire it now.
                if state.pending_modal == "autopersist_startup":
                    _open_modal(state, "autopersist_startup")
                state.pending_modal = None
            imgui.same_line()
            if imgui.button("Abort##drift"):
                # Startup [Abort] = exit application (spec §4.8 L390 [Abort]
                # semantics for startup variant per Debate #1 CC5 C2 + Debate
                # #2 CC3-v2 C5). main loop checks exit_requested and breaks;
                # finally block guard skips final autopersist write.
                state.exit_requested = True
                state.pending_modal = None
                _close_modal(state)
                imgui.close_current_popup()
            imgui.end_popup()

        # Modal 4: autopersist_startup (spec §4.7 L380-382)
        if state.active_modal == "autopersist_startup":
            imgui.open_popup("Previous session had unsaved edits##modal")
        opened_auto, _ = imgui.begin_popup_modal(
            "Previous session had unsaved edits##modal",
            None,
            imgui.WindowFlags_.always_auto_resize.value,
        )
        if opened_auto:
            imgui.text_wrapped("Previous session had unsaved edits, restore?")
            if imgui.button("Restore##auto_confirm"):
                # Apply autopersist payload to current_edit + current_step; mark dirty.
                # Payload is already validated by _validate_autopersist at startup, so
                # we can trust its schema here. On structural error, abort gracefully.
                try:
                    with state.autopersist_path.open() as f:
                        payload = json.load(f)
                    ce = payload.get("current_edit", {})
                    state.current_step = int(payload.get("current_step", state.current_step))
                    state.current_step = max(1, min(state.current_step, state.num_steps))
                    state.current_edit = {
                        "target_l": [float(v) for v in ce.get("target_l", [0.0, 0.0, 0.0])],
                        "target_r": [float(v) for v in ce.get("target_r", [0.0, 0.0, 0.0])],
                        "left_finger": float(ce.get("left_finger", 0.0)),
                        "right_finger": float(ce.get("right_finger", 0.0)),
                    }
                    state.dirty = True
                except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as e:
                    print(
                        f"[robottas_v1] autopersist apply failed (non-fatal): {type(e).__name__}: {e}",
                        file=sys.stderr,
                    )
                    _cleanup_autopersist(state)
                _close_modal(state)
                imgui.close_current_popup()
            imgui.same_line()
            if imgui.button("Discard##auto"):
                _cleanup_autopersist(state)
                _close_modal(state)
                imgui.close_current_popup()
            imgui.end_popup()

    return _render


def _render_markers(viewer: Any, state: RobotTASState, wp: Any, task_config: Any) -> None:
    """Day 3: render 3D target + clip markers via viewer.log_points (spec §4.3).

    Updates each frame:
      - ``target_l`` (1 instance, blue, 15mm) at ``state.current_edit['target_l']``
      - ``target_r`` (1 instance, red, 15mm) at ``state.current_edit['target_r']``
      - ``clips`` (N instances, gray, 10mm) at ``task_config.CLIP_POSITIONS``
        appended with z = ``task_config.TABLE_HEIGHT``

    Notes (CC Debate 2026-04-21, pre-impl):
      * viewer_gl.log_points does NOT normalize scalar radii or tuple colors
        (asymmetric with log_lines viewer_gl.py:729-737). Must pre-build
        ``wp.full(..., device=viewer.device)`` broadcast arrays.
      * ``device=viewer.device`` required to avoid mismatch with
        ``viewer_gl.py:798`` internal kernel launch.
      * Clip source is ``task_config.CLIP_POSITIONS`` per spec §4.3 literal
        ("task_config.py 読込"), NOT JSON ``clip_positions`` (SSOT CC3/CC5 HIGH).
      * num_points is constant per name (1 for target_l/r, N for clips) →
        no GL resource recreation per spec §4.3 ISSUE 7 invariant.
      * Fixed colors; status-dependent tint deferred to Day 5 per §4.4.
    """
    dev = viewer.device

    # Day 5 (§4.4): status-dependent FAIL tint for current STEP's target markers.
    # Only applies when state is clean (not dirty) — an in-progress edit moves
    # the marker position, so stale validation status should NOT be visualized
    # (CC2 MED 2026-04-22: dirty invalidates prior IK result for this STEP).
    current_status: str | None = None
    if not state.dirty and state.latest_result and state.latest_result.get("ok"):
        invoke_result = state.latest_result.get("result")
        steps = (invoke_result.updated_steps or []) if invoke_result else []
        idx = state.current_step - 1
        if 0 <= idx < len(steps):
            current_status = steps[idx].get("status")
    tl_rgb = _COLOR_TARGET_FAIL if current_status == "FAIL" else _COLOR_TARGET_L
    tr_rgb = _COLOR_TARGET_FAIL if current_status == "FAIL" else _COLOR_TARGET_R

    # target_l (1 point; blue default, orange on current-STEP FAIL)
    tl_pos = wp.array([list(state.current_edit["target_l"])], dtype=wp.vec3, device=dev)
    tl_radii = wp.full(1, _TARGET_MARKER_RADIUS, dtype=wp.float32, device=dev)
    tl_colors = wp.full(1, wp.vec3(*tl_rgb), dtype=wp.vec3, device=dev)
    viewer.log_points("target_l", tl_pos, radii=tl_radii, colors=tl_colors)

    # target_r (1 point; red default, orange on current-STEP FAIL)
    tr_pos = wp.array([list(state.current_edit["target_r"])], dtype=wp.vec3, device=dev)
    tr_radii = wp.full(1, _TARGET_MARKER_RADIUS, dtype=wp.float32, device=dev)
    tr_colors = wp.full(1, wp.vec3(*tr_rgb), dtype=wp.vec3, device=dev)
    viewer.log_points("target_r", tr_pos, radii=tr_radii, colors=tr_colors)

    # clips (N points, gray; N = len(CLIP_POSITIONS), e.g. 5 for full_43step)
    clip_positions = task_config.CLIP_POSITIONS
    n_clips = len(clip_positions)
    if n_clips > 0:
        clip_z = task_config.TABLE_HEIGHT  # [m]
        clip_pts = wp.array(
            [[x, y, clip_z] for (x, y) in clip_positions],
            dtype=wp.vec3,
            device=dev,
        )
        clip_radii = wp.full(n_clips, _CLIP_MARKER_RADIUS, dtype=wp.float32, device=dev)
        clip_colors = wp.full(n_clips, wp.vec3(*_COLOR_CLIP), dtype=wp.vec3, device=dev)
        viewer.log_points("clips", clip_pts, radii=clip_radii, colors=clip_colors)


def main() -> int:
    args = _parse_args()
    # Day 6 CC4 H1 (Debate #2 CC3-v2 C7 / CC4-v2 C5 / CC5-v2 C1): resolve symlinks
    # and relative paths at startup. Ensures consistent stem/parent for sidecar +
    # autopersist path computation across sessions launched from different cwds.
    # Forward-compat for old autopersist payloads with unresolved paths is handled
    # by `_validate_autopersist` triple-compare (Debate #2 CC3-v2 C1 / CC5-v2 C1).
    # Symlink loop / FS error — fall through, _load_waypoint_json will surface.
    with contextlib.suppress(OSError, RuntimeError):
        args.json = args.json.resolve()
    data = _load_waypoint_json(args.json)
    imgui, ViewerGL, wp, task_config, wrapper = _import_heavy_deps()
    # Day 3 fix (CC2 MED post-impl 2026-04-21): propagate --device to warp/viewer so
    # ViewerBase.__init__ (viewer.py:38 `self.device = wp.get_device()`) picks it up.
    # Without this, markers always allocate on wp default (cuda:0) and --device is a no-op.
    wp.set_device(args.device)
    state = RobotTASState(args.json, data, args.device)

    # Day 6: compute autopersist path (needs wrapper for BACKUP_DIR). Assignment
    # is deferred here from __init__ to avoid hard-coupling state to the wrapper
    # module during tests that construct RobotTASState directly.
    state.autopersist_path = _compute_autopersist_path(wrapper, args.json)
    # Day 6 CC4 H1: same lazy-assignment pattern for SSOT 43STEP recorded-hash sidecar.
    state.recorded_hash_path = _compute_recorded_hash_path(wrapper, args.json)

    # Day 6 (spec §4.7 L381-382 NEW 3 MEDIUM fix): startup 5-step sequence.
    # CC4 H1 (Debate #1+#2 final): adds steps 2-3 (SSOT 43STEP hash drift check
    # with canonical bootstrap + ssot43_canonical_drift modal) BEFORE step 4
    # (autopersist tempfile check). When both fire, autopersist is queued via
    # `state.pending_modal` and chained when the hash modal closes via [Load fresh].
    # Post-impl Debate CC2/CC3 MED: sweep mkstemp orphan fragments
    # (.robottas_autosave_*.tmp + .robottas_recorded_hash_*.tmp per Debate #1
    # CC5 C8) from prior crashes. Only orphans older than _AUTOPERSIST_STALE_AGE_S
    # are removed to avoid racing a concurrent UI instance's mid-write fragment.
    autosave_dir = state.autopersist_path.parent
    if autosave_dir.is_dir():
        for pattern in (".robottas_autosave_*.tmp", f"{_RECORDED_HASH_TMP_PREFIX}*.tmp"):
            for orphan in autosave_dir.glob(pattern):
                try:
                    if (time.time() - orphan.stat().st_mtime) > _AUTOPERSIST_STALE_AGE_S:
                        orphan.unlink()
                except OSError:
                    pass

    # Post-impl Debate CC3 H2: if autopersist exists but fails validation due to
    # baseline_hash drift (external edit between sessions), we used to silently
    # cleanup, losing the user's unsaved edits without warning. Now we distinguish
    # between "stale/invalid" (cleanup silently) and "baseline-drifted" (preserve
    # tempfile in `.stale/` subdir + stderr warning so rs can recover manually).
    auto_payload = _validate_autopersist(
        state.autopersist_path, args.json, state.baseline_json_hash
    )
    autopersist_modal_pending = auto_payload is not None
    if not autopersist_modal_pending:
        # Invalid — distinguish the baseline-drift case and preserve forensically.
        if state.autopersist_path is not None and state.autopersist_path.is_file():
            stale_dir = state.autopersist_path.parent / ".stale"
            try:
                stale_dir.mkdir(parents=True, exist_ok=True)
                preserved = stale_dir / f"{state.autopersist_path.stem}.{int(time.time())}.json"
                state.autopersist_path.rename(preserved)
                print(
                    f"[robottas_v1] autopersist rejected (schema/hash/age mismatch); "
                    f"preserved at {preserved} for manual recovery.",
                    file=sys.stderr,
                )
            except OSError:
                _cleanup_autopersist(state)

    # Day 6 CC4 H1 (spec §4.7 L382 step 2-3): SSOT 43STEP hash drift check.
    # Bypassed by `--skip-hash-check` (NHA #2 for CI / Day 7 gate).
    if not args.skip_hash_check:
        recorded, status = _load_recorded_hash(state.recorded_hash_path)
        if status == "absent":
            # First-run bootstrap — seed sidecar with canonical (NOT current disk)
            # so genuine drift from canonical fires the modal. Per Debate #1
            # CC6 NHA + Cluster A: silent self-validate-as-canonical defeats spec
            # intent; canonical anchor is the comparison baseline at first run.
            recorded = _SSOT_43STEP_BOOTSTRAP_HASH
            print(
                f"[robottas_v1] no SSOT 43STEP recorded hash sidecar; bootstrapping "
                f"with vault canonical {_SSOT_43STEP_BOOTSTRAP_HASH[:12]}",
                file=sys.stderr,
            )
        elif status != "ok":
            # Corrupt / schema_mismatch / invalid_hash — preserve forensically
            # to .stale/ before bootstrapping (parallel to autopersist precedent
            # at L1614-1620 + Debate #2 CC4-v2 C1).
            try:
                stale_dir = state.recorded_hash_path.parent / ".stale"
                stale_dir.mkdir(parents=True, exist_ok=True)
                preserved = stale_dir / (
                    f"{state.recorded_hash_path.stem}.{int(time.time())}.{status}.json"
                )
                state.recorded_hash_path.rename(preserved)
                print(
                    f"[robottas_v1] recorded hash sidecar invalid ({status}); "
                    f"preserved at {preserved}; bootstrapping with vault canonical "
                    f"{_SSOT_43STEP_BOOTSTRAP_HASH[:12]}",
                    file=sys.stderr,
                )
            except OSError:
                pass  # best-effort preservation; bootstrap proceeds regardless
            recorded = _SSOT_43STEP_BOOTSTRAP_HASH

        if recorded != state.baseline_json_hash:
            _open_modal(state, "ssot43_canonical_drift")
            if autopersist_modal_pending:
                # Defer autopersist modal — chain after [Load fresh] of drift modal.
                state.pending_modal = "autopersist_startup"
                autopersist_modal_pending = False  # consumed by chain queue

    if autopersist_modal_pending:
        # Either no drift detected, or hash check skipped — open autopersist modal directly.
        _open_modal(state, "autopersist_startup")

    viewer = ViewerGL(headless=False)
    viewer.register_ui_callback(_make_side_panel_cb(state, imgui, wrapper), position="side")

    # Main loop: viewer.begin_frame(time: float) required per viewer_gl.py:953.
    # For editor UI (non-simulation), wall-clock elapsed time is acceptable
    # (dry_run_43step.py:186 uses sim_time; editor uses wall-clock).
    # Day 3: _render_markers guarded so marker failure doesn't kill the editor
    # session (CC2-MED 2026-04-21; editor must remain usable for restore).
    # Day 4: _process_done_success clears dirty + syncs baseline after an
    # Apply success so subsequent edits diff against the just-committed values.
    # Day 6: _write_autopersist fires when dirty + debounce elapsed + no active modal.
    start_t = time.time()
    _marker_error_seen: dict[str, bool] = {}  # error-class dedup per-run
    try:
        # Day 6 CC4 H1 (Debate #1 CC5 C2 + Debate #2 CC3-v2 C5): exit_requested
        # is flipped True ONLY by `ssot43_canonical_drift` [Abort] at startup.
        # Loop check breaks cleanly so finally block runs. Mid-session [Abort]
        # of the runtime baseline_mismatch modal does NOT set exit_requested
        # (semantics preserved per Debate #2 CC3-v2 C5).
        while viewer.is_running() and not state.exit_requested:
            t_now = time.time() - start_t
            viewer.begin_frame(t_now)
            try:
                _render_markers(viewer, state, wp, task_config)
            except Exception as e:  # noqa: BLE001 (display-only guard, must not kill)
                cls = type(e).__name__
                if not _marker_error_seen.get(cls):
                    print(f"[robottas_v1] _render_markers {cls}: {e}", file=sys.stderr)
                    _marker_error_seen[cls] = True
            _process_done_success(state)
            # Day 6: autopersist debounce write (before end_frame so even if viewer
            # exits next iteration, the current frame's dirty state is persisted).
            if _should_autopersist(state, time.monotonic()):
                try:
                    _write_autopersist(state)
                except OSError as e:
                    print(
                        f"[robottas_v1] autopersist write failed (non-fatal): {type(e).__name__}: {e}",
                        file=sys.stderr,
                    )
            viewer.end_frame()
    finally:
        # Day 6 (pre-impl Debate CC5 L2): on normal exit or exception path, force
        # one final autopersist if dirty — bounds data loss for clean shutdown
        # (X-close, Ctrl-C). SIGKILL still bypasses this, hence the
        # per-frame debounce write remains the primary safety net.
        # Day 6 CC4 H1 (Debate #1 CC3 C6 + Debate #2 CC3-v2 C5): exit_requested
        # guard skips final autopersist — startup [Abort] means user explicitly
        # rejected current session, persisting in-memory state would contradict.
        # In practice state.dirty is False at startup (no edits made yet) so
        # the existing dirty guard already covers this case; the explicit
        # exit_requested guard is defense-in-depth for edge cases.
        if (
            state.dirty
            and state.autopersist_path is not None
            and not state.exit_requested
        ):
            try:
                _write_autopersist(state)
            except OSError as e:
                print(
                    f"[robottas_v1] final autopersist failed: {type(e).__name__}: {e}",
                    file=sys.stderr,
                )
    return 0


if __name__ == "__main__":
    sys.exit(main())

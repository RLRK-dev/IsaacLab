# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Bind unchanged mechanical evidence to a camera-only final native, by SHA256."""

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "analysis/op030_candidate_8674_v06"


def digest(path: Path) -> str:
    """Return exact file identity without loading large banks into memory."""
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def resolved(path: str) -> Path:
    """Resolve report paths relative to the run directory."""
    value = Path(path)
    return value if value.is_absolute() else ROOT / value


def main() -> None:
    """Verify the camera delta and old evidence, then write a new inheritance index."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--delta", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or args.output.with_suffix(".md").exists():
        raise FileExistsError(args.output)
    delta = json.loads(args.delta.read_text())
    checks = delta["result"]
    if not checks.get("eligible_to_inherit_geometry_checks") or checks.get("unexpected_review_camera_changes"):
        raise ValueError("Camera-only equality is not established")
    if set(delta["allowed_review_cameras"]) != {"Review_OP030_split_B", "Review_OP030_split_B_joint"}:
        raise ValueError("Unexpected camera edit scope")
    native = resolved(delta["final"])
    if digest(native) != delta["final_sha256"]:
        raise ValueError("Final native changed after delta comparison")
    driver_path = ROOT / "audit/op030_camera_delta_v06_driver_names.json"
    driver_names = json.loads(driver_path.read_text())
    if not driver_names["exact_equality"] or driver_names["final_sha256"] != delta["final_sha256"]:
        raise ValueError("Driver variable names are not equal in the final native")
    if driver_names["original_sha256"] != delta["original_sha256"]:
        raise ValueError("Driver variable supplement uses another original native")
    previous_path = ARCHIVE / "audit/op030_stagger_v06_integration_evidence.json"
    previous = json.loads(previous_path.read_text())
    if previous["native"]["sha256"] != delta["original_sha256"]:
        raise ValueError("Delta original is not the previously observed native")
    verified = []
    for row in previous["evidence"]:
        relative = resolved(row["path"]).relative_to(ROOT)
        if str(relative) == "scripts/collect_op030_stagger_integration_v06.py":
            path = ARCHIVE / "recovered_observation_source" / relative
        else:
            path = ARCHIVE / relative
            if not path.exists():
                path = ROOT / relative
        if digest(path) != row["sha256"]:
            raise ValueError("An observed evidence file cannot be recovered: " + str(path))
        verified.append(dict(original_path=str(relative), preserved_path=str(path), sha256=row["sha256"]))
    prepared = ROOT / "data/op030_split_animation_v06.npz"
    if digest(prepared) != previous["prepared"]["sha256"]:
        raise ValueError("Prepared mechanical arrays changed")
    for row in previous["banks"].values():
        if digest(resolved(row["path"])) != row["sha256"]:
            raise ValueError("A station bank changed")
    final_audit_path = ROOT / "audit/op030_split_native_v06.json"
    final_audit = json.loads(final_audit_path.read_text())
    if final_audit["output_sha256"] != delta["final_sha256"]:
        raise ValueError("Final native audit is not bound to the compared native")
    if final_audit["prepared_sha256"] != previous["prepared"]["sha256"]:
        raise ValueError("Final native audit uses a different mechanical track")
    archive_manifest = ARCHIVE / "manifest.json"
    recovery = ARCHIVE / "recovered_observation_source_manifest.json"
    source = ROOT / "scripts/animate_op030_split_v06.py"
    shots_path = ROOT / "data/op030_split_shots_v06.json"
    old_shots_path = ARCHIVE / "data/op030_split_shots_v06.json"
    shots = json.loads(shots_path.read_text())
    old_shots = json.loads(old_shots_path.read_text())
    if shots["native_sha256"] != delta["final_sha256"]:
        raise ValueError("Shot plan is not bound to the final native")
    shot_changes = [key for key in shots.keys() | old_shots.keys() if shots.get(key) != old_shots.get(key)]
    if shot_changes != ["native_sha256"]:
        raise ValueError("A shot schedule field changed outside the native SHA binding")
    selection_path = ROOT / "audit/op030_stagger_camera_v06_selection.json"
    report = dict(
        observed_at=datetime.now().astimezone().isoformat(),
        native=dict(path=str(native), sha256=delta["final_sha256"]),
        original_native=dict(path=delta["original"], sha256=delta["original_sha256"]),
        mechanical_evidence=dict(path=str(previous_path), sha256=digest(previous_path)),
        camera_delta=dict(path=str(args.delta), sha256=digest(args.delta)),
        driver_symbol_supplement=dict(
            path=str(driver_path),
            sha256=digest(driver_path),
            driver_count=driver_names["driver_count"],
            driver_variable_count=driver_names["driver_variable_count"],
            exact_equality=driver_names["exact_equality"],
        ),
        strict_non_camera_equality=checks["strict_non_camera_equality"],
        matrix_roundoff_only=checks["matrix_roundoff_only"],
        final_native_audit=dict(path=str(final_audit_path), sha256=digest(final_audit_path)),
        final_animate_source=dict(path=str(source), sha256=digest(source)),
        final_shot_plan=dict(
            path=str(shots_path),
            sha256=digest(shots_path),
            original_path=str(old_shots_path),
            original_sha256=digest(old_shots_path),
            changed_keys=shot_changes,
            unchanged_ranges=len(shots["ranges"]),
        ),
        camera_selection=dict(path=str(selection_path), sha256=digest(selection_path)),
        archive_manifest=dict(path=str(archive_manifest), sha256=digest(archive_manifest)),
        recovered_observation_source=dict(path=str(recovery), sha256=digest(recovery)),
        unchanged_prepared=previous["prepared"],
        unchanged_banks=previous["banks"],
        preserved_evidence=verified,
        relation="The final native differs only in the two specified review-camera fits. "
        "The original 33 reports remain pinned to their original native and retain all raw contacts. "
        "Their unchanged mechanical data is inherited through this separate delta proof.",
        collision_checks_reexecuted=False,
        raw_report_sha_pins_rewritten=False,
        scope="Saved-data equivalence and provenance only; camera visibility is a separate visual observation.",
        formal_physical_validity_verdict=None,
    )
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    args.output.with_suffix(".md").write_text(
        "# OP030 v06 撮影カメラ変更後の根拠対応\n\n"
        f"確認時刻: {report['observed_at']}。最終native SHA `{delta['final_sha256']}`。\n\n"
        f"旧native `{delta['original_sha256']}` に対する元33報告は書き換えず保存した。"
        f"参照 {len(verified)} ファイルを元SHAと照合した。\n\n"
        "2つの撮影カメラの位置・姿勢・レンズ以外の保存データを別native比較で確認し、"
        "同じ機構・動作への根拠として旧検査を引き継ぐ。FCLの再実行はない。\n\n"
        f"非camera厳密一致: {checks['strict_non_camera_equality']}。"
        f"matrix丸め差の別記件数: {len(checks['matrix_roundoff_only'])}。\n\n"
        "元の固定接続・把持面・力未検証等の限定はそのまま保持する。正式な物理妥当性判定は行わない。\n",
    )
    print("CAMERA_DELTA_EVIDENCE_LINKED", args.output, len(verified), flush=True)


if __name__ == "__main__":
    main()

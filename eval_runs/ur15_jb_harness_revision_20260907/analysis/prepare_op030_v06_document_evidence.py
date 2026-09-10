# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Bind final camera-native evidence and measured videos when encoding is complete."""

import argparse
import ast
import copy
import hashlib
import json
import re
from contextlib import suppress
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def digest(path: Path) -> str:
    """Return a file SHA256 digest."""
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def save(path: Path, data: dict) -> None:
    """Save one new-version metadata record."""
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def video_records(native_sha: str, motion_sha: str, shots_sha: str, require_videos: bool) -> dict:
    """Validate complete encoder reports and their actual video files [s]."""
    report_paths = {view: ROOT / f"audit/UR15_JB_OP030_split_{view}_v06_video.json" for view in ("process", "wide")}
    result = dict(
        status="planned_not_encoded_or_measured",
        views=4,
        sample_count_per_view=7031,
        fps=15,
        planned_encoded_duration_s=7031 / 15,
        native_sample_frames=dict(first=1, last=14061, step=2),
        measured_duration_s=None,
        measured_video_sha256=None,
        qualification="Planned frame count/rate only; actual encode reports are not both available",
    )
    if not all(path.is_file() for path in report_paths.values()):
        if require_videos:
            raise FileNotFoundError("Both completed final-native encoder reports are required")
        return result
    measured, reports = {}, {}
    for view, path in report_paths.items():
        report = json.loads(path.read_text())
        assert report["native_sha256"] == native_sha
        assert report["motion_sha256"] == motion_sha and report["presentation_sha256"] == shots_sha
        assert report["frame_count"] == 7031 and abs(report["duration_s"] - 7031 / 15) < 1e-9
        assert [row["native_frame"] for row in report["mapping"]] == list(range(1, 14062, 2))
        expected_names = {f"UR15_JB_OP030_split_{view}_v06_{suffix}.mp4" for suffix in ("raw", "review")}
        assert set(report["videos"]) == expected_names
        for name, record in report["videos"].items():
            assert digest(ROOT / name) == record["sha256"]
            assert record["full_decode_exit_code"] == 0 and not record["full_black_intervals"]
            streams = [stream for stream in record["metadata"]["streams"] if stream["codec_type"] == "video"]
            assert len(streams) == 1
            stream = streams[0]
            assert int(stream["nb_read_frames"]) == 7031 and stream["r_frame_rate"] == "15/1"
            assert (stream["width"], stream["height"]) == ((1280, 720) if view == "process" else (960, 540))
            duration = float(record["metadata"]["format"]["duration"])
            assert abs(duration - 7031 / 15) < 0.02
            measured[name] = dict(
                sha256=record["sha256"],
                bytes=(ROOT / name).stat().st_size,
                duration_s=duration,
                frames=int(stream["nb_read_frames"]),
                fps=stream["r_frame_rate"],
                width=stream["width"],
                height=stream["height"],
                full_decode_exit_code=0,
                full_black_intervals=[],
            )
        reports[view] = dict(path=str(path.relative_to(ROOT)), sha256=digest(path))
    result.update(
        status="encoded_measured_and_full_decode_verified",
        measured_duration_s={name: record["duration_s"] for name, record in measured.items()},
        measured_video_sha256={name: record["sha256"] for name, record in measured.items()},
        videos=measured,
        reports=reports,
        qualification="Saved encoder observations and unchanged file hashes; browser delivery is a separate gate",
    )
    return result


def render_source_records(native_sha: str, videos_ready: bool) -> dict[str, tuple[str, str]]:
    """Verify the actual disjoint render ranges and return their evidence paths."""
    if not videos_ready:
        return {}
    parallel = json.loads((ROOT / "audit/op030_v06_render_parallel_completion.json").read_text())
    assert parallel["native_sha256"] == native_sha and parallel["inputs_unchanged"]
    assert not parallel["rendering_settings_changed"] and not parallel["motion_geometry_or_cameras_changed"]
    assert digest(ROOT / "analysis/render_split_parallel_v06.py") == parallel["script_sha256"]
    additions = {
        relative: ("v06_render_sources", "Unchanged renderer, disjoint native ranges and PNG provenance")
        for relative in (
            "audit/op030_v06_render_parallel_completion.json",
            "analysis/render_split_parallel_v06.py",
            "analysis/render_split_view_v06.sh",
            "analysis/op030_v06_parallel_render_scope.md",
        )
    }
    for view, record in parallel["views"].items():
        assert record["sample_count"] == 7031 and record["expected_frame_set"]
        assert record["all_png_sha256_checked"] and record["original_renderer_resume_exit_code"] == 0
        assert digest(ROOT / record["final_manifest"]) == record["final_manifest_sha256"]
        for source in record["sources"]:
            for key in ("manifest", "log"):
                relative = source[key]
                assert digest(ROOT / relative) == source[key + "_sha256"]
                additions[relative] = ("v06_render_sources", f"{view}: saved range {source['first']}..{source['last']}")
    return additions


def main() -> None:
    """Read prior evidence without mutation; do not import Blender or execute rebake."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--require_videos", action="store_true")
    options = parser.parse_args()
    previous_path = ROOT / "analysis/op030_v05_package_evidence.json"
    previous_document = ROOT / "OP030_三ST工程・部品確認書_v05.md"
    previous_sha, previous_document_sha = digest(previous_path), digest(previous_document)
    previous = json.loads(previous_path.read_text())
    package_path = ROOT / "scripts/package_op030_split_v06.py"
    constants = {}
    for node in ast.parse(package_path.read_text()).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            with suppress(ValueError, TypeError):
                constants[node.targets[0].id] = ast.literal_eval(node.value)
    helpers = list(constants["SCRIPT_FILES"])
    assert len(helpers) == 19 and len(set(helpers)) == 19
    helper_records = {}
    included_modules = {Path(path).stem: path for path in helpers}
    search_roots = {ROOT / Path(path).parent for path in helpers}
    graph, missing, deferred_planning = {}, [], []
    for relative in helpers:
        path = ROOT / relative
        assert path.is_file()
        tree = ast.parse(path.read_text())
        local = set()
        for node in ast.walk(tree):
            imports = []
            if isinstance(node, ast.Import):
                imports = [alias.name.split(".")[0] for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports = [node.module.split(".")[0]]
            for name in imports:
                found = [
                    directory / (name + ".py") for directory in search_roots if (directory / (name + ".py")).is_file()
                ]
                if found:
                    if name in included_modules:
                        local.add(included_modules[name])
                    elif (
                        relative == "scripts/op030_fixed_height_timeline_v04.py" and name == "op030_split_b_v04_drawer"
                    ):
                        owner = next(
                            function.name
                            for function in ast.walk(tree)
                            if isinstance(function, ast.FunctionDef) and node in list(ast.walk(function))
                        )
                        assert owner == "assemble_timeline"
                        deferred_planning.append(
                            dict(
                                importer=relative,
                                function=owner,
                                module=name,
                                reason="Planning only; saved-array rebake imports CONVEYOR_RISE without calling this",
                            )
                        )
                    else:
                        missing.append(dict(importer=relative, module=name, candidates=[str(p) for p in found]))
        graph[relative] = sorted(local)
        helper_records[relative] = dict(
            sha256=digest(path), bytes=path.stat().st_size, status="Final camera-native runtime input"
        )
    assert not missing, missing
    static_path = "analysis/op030_stagger_air_clearance_static_v06.blend"
    static_manifest = "audit/op030_stagger_air_clearance_static_v06.json"
    static = json.loads((ROOT / static_manifest).read_text())
    assert static["output"] == static_path and digest(ROOT / static_path) == static["output_sha256"]
    assert not static["stagger_support_v06"]["fixed_check_pending"]
    assert not static["air_drop_clearance_v06"]["fixed_check_pending"]
    inputs = copy.deepcopy(helper_records)
    for path in (static_path, static_manifest):
        inputs[path] = dict(
            sha256=digest(ROOT / path), bytes=(ROOT / path).stat().st_size, status="Current static input"
        )
    for key in ("MOTION", "PREPARED"):
        relative = constants[key]
        inputs[relative] = dict(
            sha256=digest(ROOT / relative),
            bytes=(ROOT / relative).stat().st_size,
            exists_at_observation=True,
            status="Final saved prepared input; no replanning",
        )
    assert len(inputs) == 23
    native_audit = json.loads((ROOT / constants["NATIVE_AUDIT"]).read_text())
    native_sha = digest(ROOT / constants["NATIVE"])
    prepared = json.loads((ROOT / constants["PREPARED"]).read_text())
    shots = json.loads((ROOT / constants["PLAN"]).read_text())
    assert native_sha == native_audit["output_sha256"] == shots["native_sha256"]
    assert native_sha == "e65bef607c1d29671fc982d14d72d4c2694420edd284378cb2f1445f18f354ed"
    assert digest(ROOT / constants["MOTION"]) == native_audit["prepared_sha256"] == shots["motion_sha256"]
    assert prepared["output_sha256"] == native_audit["prepared_sha256"]
    assert native_audit["frames"] == prepared["frames"] == shots["frame_end"] == 14062
    assert not native_audit["matrix_readback"]["failures"]
    assert not native_audit["native_dependencies"]["external_images"]
    assert not native_audit["native_dependencies"]["external_libraries"]
    videos = video_records(
        native_sha, native_audit["prepared_sha256"], digest(ROOT / constants["PLAN"]), options.require_videos
    )
    videos_ready = videos["status"] == "encoded_measured_and_full_decode_verified"
    portable_relative = "audit/op030_split_layout_portable_rebake_camera_final_v06.json"
    portable = json.loads((ROOT / portable_relative).read_text()) if (ROOT / portable_relative).is_file() else None
    if portable is not None:
        assert portable["baseline_native"]["sha256"] == native_sha
        assert portable["copied_file_count"] == 23 and portable["helper_count"] == 19
        assert portable["input_sha256_unchanged"] and not portable["original_root_imports"]
        assert portable["blender_exit_code"] == 0 and portable["frames"] == native_audit["frames"]
        assert portable["camera_overrides_match"] and not portable["matrix_readback"]["failures"]
        for relative, record in portable["copied_inputs"].items():
            assert record["sha256"] == inputs[relative]["sha256"], relative
    plan_path = ROOT / "analysis/op030_v06_portable_rebake_plan.json"
    plan = dict(
        observed_at=datetime.now().astimezone().isoformat(),
        status="final_inputs_verified_against_executed_rebake" if portable else "final_inputs_pinned_execution_pending",
        package=str(package_path.relative_to(ROOT)),
        package_sha256=digest(package_path),
        reference_runner="analysis/split_layout_portable_rebake_v05.py",
        reference_runner_sha256=digest(ROOT / "analysis/split_layout_portable_rebake_v05.py"),
        input_count=23,
        helper_count=19,
        inputs=inputs,
        local_import_graph=graph,
        missing_local_imports=missing,
        deferred_planning_imports_not_used_by_rebake=deferred_planning,
        import_check=(
            "AST dependency closure plus separately recorded isolated actual execution"
            if portable
            else "AST dependency closure; final isolated execution report not yet received"
        ),
        expected_native=constants["NATIVE"],
        expected_native_audit=constants["NATIVE_AUDIT"],
        final_native_sha256=native_sha,
        execution_record=(dict(path=portable_relative, sha256=digest(ROOT / portable_relative)) if portable else None),
        execution_gate="Execution claims are taken only from the final-camera 23-input report, never from this plan",
        steps=[
            "Validate final native hash/completion marker and prepared/static SHA chain",
            "Create an isolated temporary ROOT and copy only the exact 23 input files; compare copied byte hashes",
            "Use the v05 runner's background Blender; import animate_op030_split_v06 from isolated ROOT",
            "Bake saved prepared arrays only; do not replan IK or rerun physical/collision evaluation",
            "Check completion, source/prepared/frame agreement, and saved matrix/deformation/tool readback",
            "Compare presentation cameras, downstream restored actors, B parent-local drawer and fixed-height tracks",
            "Require external images/libraries zero, no original-ROOT imports, and unchanged input hashes",
            "Keep one diagnostic native/readback/log, remove temporary inputs; do not touch stage/Downloads/Vault",
        ],
        new_v06_focus=[
            "B drawer retains rotated parent and local +X0..340 mm",
            "Product/frame Y offset is applied only once",
            "B fixed base/supply are already rotated in saved static; no second rigid delta",
            "A/C, product orientation and constant pallet origin Z0.789 m retained",
            "Four 0782 drop actors retain saved Y-.78 m displacement without motion overwrite",
        ],
        rebake_executed=portable is not None,
        native_created=portable is not None,
        stage_executed=False,
        formal_physical_validity_verdict=None,
    )
    save(plan_path, plan)

    retained_groups = {
        "A_final",
        "A_inherited",
        "C_final",
        "C_fixed_layout",
        "fixed_height",
        "fixed_height_inherited",
        "wire_geometry_inherited",
    }
    files = {}
    for relative, old in previous["files"].items():
        if old["group"] not in retained_groups:
            continue
        path = ROOT / relative
        assert path.is_file() and digest(path) == old["sha256"]
        files[relative] = dict(
            sha256=old["sha256"],
            bytes=path.stat().st_size,
            group="inherited_" + old["group"],
            reason=old["reason"],
            qualification=(
                "Inherited A/C/geometry basis; B standalone and v06 integration are recorded separately. "
                "Camera-final inheritance requires the original native pin and non-camera identity delta."
            ),
            prior_qualification=old.get("qualification"),
        )
    additions = {
        "analysis/OP030_v06_scope.md": (
            "v06_scope",
            "User-directed B-only stagger, fixed product/F01 and process boundary",
        ),
        "analysis/op030_stagger_static_v06_delta.md": (
            "v06_static",
            "420-object rigid selection including four actual air-drop parts",
        ),
        "audit/op030_stagger_static_v06_completion.json": (
            "v06_static",
            "Rigid move, fixed geometry, air-main interface classification",
        ),
        "audit/op030_stagger_static_v06_geometry.json": (
            "v06_static",
            "Explicit 420 world transforms/local signatures and all omitted fixed AABBs",
        ),
        "audit/op030_stagger_static_v06_raw_check.json": (
            "v06_static",
            "2352 fixed pairs / 144 FCL queries and two individual construction contacts",
        ),
        "audit/op030_stagger_static_v06_readback.json": (
            "v06_static",
            "Saved native identity and drawer0/170/340 evaluated-shape comparison",
        ),
        "analysis/op030_stagger_static_v06_completion.md": (
            "v06_static",
            "Static scope and retained initial floor gap before repair",
        ),
        "analysis/op030_stagger_support_v06_scope.md": (
            "v06_support",
            "Bounded correction reason, reused implementation and dimensions",
        ),
        "audit/op030_stagger_support_v06_components.json": (
            "v06_support",
            "Actual existing controller base-plate component identification",
        ),
        "audit/op030_stagger_supported_static_v06_completion.json": (
            "v06_support",
            "Final support repair summary and individual intended contacts",
        ),
        "audit/op030_stagger_supported_static_v06_geometry.json": (
            "v06_support",
            "Nine changed meshes, preserved upper objects/vertices and omitted AABBs",
        ),
        "audit/op030_stagger_supported_static_v06_raw_check.json": (
            "v06_support",
            "333 pairs / 28 FCL, five floor surfaces and sixteen old construction pairs",
        ),
        "audit/op030_stagger_supported_static_v06_readback.json": (
            "v06_support",
            "Saved nine-mesh correction, 9562 unchanged objects and exact support gaps",
        ),
        "analysis/op030_stagger_supported_static_v06_completion.md": (
            "v06_support",
            "Support repair explanation; 0782 unchanged statement is superseded by later four-part air-drop shift",
        ),
        "analysis/op030_air_drop_v06_scope.md": (
            "v06_air_clearance",
            "Three finite positions and measured full-sweep displacement reason",
        ),
        "audit/op030_air_drop_v06_full_envelope.json": (
            "v06_air_clearance",
            "975-pose per-solid X/Z surface projection selecting third center Y-.33 m",
        ),
        "audit/op030_air_drop_v06_environment.json": (
            "v06_air_clearance",
            "Actual main/nearby geometry source and omitted fixed-object AABB coverage",
        ),
        "audit/op030_air_drop_v06_candidate_03.json": (
            "v06_air_clearance",
            "975 finite poses/179 moving meshes/119 FCL queries; zero moving hits",
        ),
        "audit/op030_stagger_air_clearance_static_v06_geometry.json": (
            "v06_air_clearance",
            "Four saved translations, 9567 unchanged object signatures, complete native readback",
        ),
        "audit/op030_stagger_air_clearance_static_v06_completion.json": (
            "v06_air_clearance",
            "Two exact main-cylinder interfaces, internal rigid assembly and finite-motion scope; its "
            "historical pending-B field is superseded by final B records",
        ),
        "audit/op030_split_b_stagger_v06_completion.json": (
            "v06_B_final",
            "Final B artifact/SHA index: 3787 frames, 126.2 s, fixed product/UIDs, actual mesh and original FK",
        ),
        "audit/op030_split_b_stagger_motion_v06.json": (
            "v06_B_final",
            "Final B config/factory, 33 phases, every-frame FK/FCL and joint/torso speed caps; complete "
            "native_12 result copied with the same bank digest",
        ),
        "audit/op030_split_b_stagger_v06_identity_12.json": (
            "v06_B_final",
            "Independent saved-array checks of the identical final bank bytes: 78 node IDs, L=J1/R=T, ten "
            "wires, lengths, simultaneous approach/open/180 mm rise and final v05 equality",
        ),
        "audit/op030_split_b_stagger_v06_connection_11.json": (
            "v06_B_final",
            "811 retained constrained samples, four simultaneous 12D connections and 5634 actual "
            "time-varying grip samples",
        ),
        "audit/op030_split_b_stagger_air_clearance_v06_meshes.json": (
            "v06_B_actual_geometry",
            "Final static0de256 actual B export: 569 rigid meshes, ten reconstructed tubes, A installed M4 "
            "and current A/C park context",
        ),
        "analysis/op030_split_b_stagger_v06_reuse_contract.md": (
            "v06_B_contract",
            "Final one-argument factory, baseline/global transformation, drawer axis, original physical "
            "arms and fixed product/UID contract",
        ),
        "audit/op030_air_drop_ac_v06_completion.json": (
            "v06_AC_air_delta",
            "New 0782 four surfaces versus unchanged full A/C banks: positive swept AABB separation, no "
            "narrow-phase candidates or exemptions",
        ),
        "audit/op030_air_drop_a_v06.json": (
            "v06_AC_air_delta",
            "A7165 frames/623 tracked meshes: minimum swept AABB separation 0.998969 m from new pipe; inputs unchanged",
        ),
        "audit/op030_air_drop_c_v06.json": (
            "v06_AC_air_delta",
            "C2430 frames/175 tracked meshes: minimum swept AABB separation 2.471703 m from new pipe; inputs unchanged",
        ),
        "audit/op030_split_b_motion_v05.json": (
            "v05_B_time_comparison_only",
            "Previous B bank 4551 frames/151.666667 s for saved animation-time comparison only; not proof "
            "for the new B layout",
        ),
        "audit/op030_split_v04_prefill_installation_classified.json": (
            "inherited_installation",
            "Original exact 7 mm grouted baseplate/floor role used by static classification",
        ),
        "analysis/op030_v06_portable_rebake_plan.json": (
            "v06_portable_preparation",
            "Final 23-input dependency/hash contract; actual rebake claims belong to the separate execution report",
        ),
    }
    camera_link_relative = "audit/op030_camera_delta_v06_evidence.json"
    camera_link = json.loads((ROOT / camera_link_relative).read_text())
    assert camera_link["native"]["sha256"] == native_sha
    assert camera_link["strict_non_camera_equality"] and not camera_link["matrix_roundoff_only"]
    assert not camera_link["collision_checks_reexecuted"] and not camera_link["raw_report_sha_pins_rewritten"]
    assert camera_link["unchanged_prepared"]["sha256"] == native_audit["prepared_sha256"]
    assert camera_link["driver_symbol_supplement"]["exact_equality"]
    for key in (
        "mechanical_evidence",
        "camera_delta",
        "driver_symbol_supplement",
        "archive_manifest",
        "recovered_observation_source",
        "camera_selection",
    ):
        record = camera_link[key]
        path = Path(record["path"])
        assert digest(path) == record["sha256"]
        additions[str(path.relative_to(ROOT))] = (
            "v06_camera_inheritance",
            "Original-native mechanical evidence and separately verified camera-only provenance; "
            "no direct FCL rerun on the camera-final native",
        )
    additions[camera_link_relative] = (
        "v06_camera_inheritance",
        "Final-native link retaining all original raw report/native SHA pins",
    )
    additions["audit/op030_camera_delta_v06_evidence.md"] = (
        "v06_camera_inheritance",
        "Human-readable scope of the camera-only inheritance link",
    )
    # Preserve original report paths in the archive; never replace their native SHA with the final camera SHA.
    for record in camera_link["preserved_evidence"]:
        path = Path(record["preserved_path"])
        if path.suffix not in {".json", ".md"}:
            continue
        assert digest(path) == record["sha256"]
        relative = str(path.relative_to(ROOT))
        if relative in additions or relative in files or relative == static_manifest:
            continue
        additions[relative] = (
            "v06_original_native_integration",
            "Original 8674-native input/report pin retained; inherited only via the strict non-camera delta",
        )
    delta = json.loads(Path(camera_link["camera_delta"]["path"]).read_text())
    assert delta["result"]["strict_non_camera_equality"]
    mechanical = json.loads(Path(camera_link["mechanical_evidence"]["path"]).read_text())
    assert mechanical["native"]["sha256"] == camera_link["original_native"]["sha256"]
    assert mechanical["prepared"]["sha256"] == native_audit["prepared_sha256"]
    assert mechanical["added_contact_exemptions"] == []
    if portable is not None:
        for relative in (portable_relative, "audit/op030_split_layout_portable_rebake_v06.json"):
            assert digest(ROOT / relative) == digest(ROOT / portable_relative)
            additions[relative] = (
                "v06_camera_final_portable",
                "Final-camera isolated actual rebake from 23 copied inputs",
            )
        for key in ("output_readback", "log"):
            record = portable[key]
            path = ROOT / record["path"]
            assert digest(path) == record["sha256"]
            additions[str(path.relative_to(ROOT))] = (
                "v06_camera_final_portable",
                "Saved final-camera isolated rebake readback/runtime record",
            )
    additions.update(render_source_records(native_sha, videos_ready))
    for relative, (group, reason) in additions.items():
        path = ROOT / relative
        assert path.is_file()
        files[relative] = dict(sha256=digest(path), bytes=path.stat().st_size, group=group, reason=reason)
    b_report = json.loads((ROOT / "audit/op030_split_b_stagger_motion_v06.json").read_text())
    b_identity = json.loads((ROOT / "audit/op030_split_b_stagger_v06_identity_12.json").read_text())
    b_connection = json.loads((ROOT / "audit/op030_split_b_stagger_v06_connection_11.json").read_text())
    b_previous = json.loads((ROOT / "audit/op030_split_b_motion_v05.json").read_text())
    ac_delta = json.loads((ROOT / "audit/op030_air_drop_ac_v06_completion.json").read_text())
    assert b_report["passed"] and b_identity["passed"] and b_connection["passed"]
    b_bank = "data/op030_split_b_stagger_motion_v06.npz"
    assert digest(ROOT / b_bank) == b_report["output_sha256"] == b_identity["bank_sha256"]
    assert b_report["sequence_sha256"] == digest(ROOT / "scripts/op030_split_b_stagger_v06.py")
    assert b_report["frames"] == b_report["actual_mesh_frames"] == 3787
    assert b_report["mesh_hit_frame_count"] == 0 and not b_report["failures"]
    assert b_report["factory"] == "op030_split_b_stagger_v06:build_sequence_final"
    assert b_report["variant"]["swap_roles"] and b_report["variant"]["bend_during_turn"]
    assert not b_report["variant"]["overbody"]
    for key in ("stock_center", "lift_clearance", "above_work", "h1_form_center_z", "grasp_offset"):
        assert b_report["config"][key] == b_previous["config"][key]
    assert ac_delta["static_sha256"] == digest(ROOT / static_path)
    for record in ac_delta["reports"]:
        assert digest(ROOT / record["report"]) == record["report_sha256"]
        assert record["inputs_unchanged"] and record["collision_frames"] == 0
    b_summary = dict(
        bank=dict(path=b_bank, sha256=digest(ROOT / b_bank)),
        report=dict(
            path="audit/op030_split_b_stagger_motion_v06.json",
            sha256=digest(ROOT / "audit/op030_split_b_stagger_motion_v06.json"),
        ),
        factory=b_report["factory"],
        factory_sha256=b_report["sequence_sha256"],
        frames=b_report["frames"],
        duration_s=b_report["duration_s"],
        authored_duration_s=b_report["authored_duration_s"],
        phases=len(b_report["phases"]),
        physical_arm_assignment=b_report["physical_arm_assignment"],
        normal_height_retained=True,
        bend_during_turn=True,
        simultaneous_grip_and_180mm_rise=True,
        all_native_frames_checked=b_report["all_frames_mesh_checked"],
        original_fk_matrix_error=b_report["maximum_original_fk_matrix_error"],
        moving_mesh_hit_frames=0,
        speed_caps_pass=b_report["speed_caps_pass"],
        previous_v05_frames=b_previous["frames"],
        previous_v05_duration_s=b_previous["duration_s"],
        animation_duration_reduction_s=b_previous["duration_s"] - b_report["duration_s"],
        comparison_scope=(
            "Complete saved standalone B animation banks, two cable pickups/placements/retreats; not "
            "hardware takt or mathematical path optimum"
        ),
    )
    document_path = ROOT / constants["DOCUMENT"]
    document = document_path.read_text()
    for relative, sha in re.findall(r"\| `((?:audit|analysis)/[^`]+)` \| `([0-9a-f]{64})` \|", document):
        assert digest(ROOT / relative) == sha, (relative, "Document SHA differs from the saved report")
    refs = sorted(set(re.findall(r"`((?:audit|analysis)/[^`]+\.(?:json|md))`", document)))
    coverage = []
    automatic = {
        constants["DOCUMENT"],
        static_path,
        static_manifest,
        constants["NATIVE_AUDIT"],
        constants["MOTION"],
        constants["PREPARED"],
        constants["PLAN"],
        *(record["path"] for record in videos.get("reports", {}).values()),
        *helpers,
    }
    for relative in refs:
        path = ROOT / relative
        assert path.is_file()
        assert relative in files or relative in automatic, relative
        coverage.append(
            dict(
                path=relative,
                exists=True,
                sha256=digest(path),
                included=relative in files,
                automatic=relative in automatic,
            )
        )
    totals = {}
    for info in files.values():
        entry = totals.setdefault(info["group"], dict(files=0, bytes=0))
        entry["files"] += 1
        entry["bytes"] += info["bytes"]
    selection = dict(
        observed_at=datetime.now().astimezone().isoformat(),
        status=(
            "camera_final_and_four_videos_verified_browser_pending"
            if videos_ready and portable
            else "camera_final_evidence_confirmed_videos_pending"
            if portable
            else "camera_final_portable_report_pending"
        ),
        basis=(
            "Pinned final B and A/C banks; original 8674-native integration evidence inherited through strict "
            "camera-only delta; final saved native/prepared/shot hashes and document references"
        ),
        native_sha256=native_sha,
        static_native=dict(path=static_path, sha256=digest(ROOT / static_path)),
        static_manifest=dict(path=static_manifest, sha256=digest(ROOT / static_manifest)),
        purpose="Final-camera evidence selection; browser and copy/archive verification follow the frozen stage",
        final_native=dict(
            path=constants["NATIVE"],
            sha256=native_sha,
            frames=native_audit["frames"],
            native_fps=native_audit["fps"],
            first_to_last_frame_duration_s=native_audit["duration_s"],
            audit=dict(path=constants["NATIVE_AUDIT"], sha256=digest(ROOT / constants["NATIVE_AUDIT"])),
            prepared_npz=dict(path=constants["MOTION"], sha256=digest(ROOT / constants["MOTION"])),
            prepared_json=dict(path=constants["PREPARED"], sha256=digest(ROOT / constants["PREPARED"])),
            shots=dict(path=constants["PLAN"], sha256=digest(ROOT / constants["PLAN"]), count=len(shots["ranges"])),
            detailed_phase_count=len(shots["phases"]),
            native_readback=native_audit["matrix_readback"],
        ),
        mechanical_inheritance=dict(
            link=dict(path=camera_link_relative, sha256=digest(ROOT / camera_link_relative)),
            original_native=camera_link["original_native"],
            original_mechanical_evidence=camera_link["mechanical_evidence"],
            camera_delta=camera_link["camera_delta"],
            checked_records=delta["result"]["checked_record_count"],
            checked_arrays=delta["result"]["checked_array_count"],
            strict_non_camera_equality=True,
            matrix_roundoff_only=[],
            collision_checks_reexecuted=False,
            raw_report_sha_pins_rewritten=False,
            relation=camera_link["relation"],
        ),
        video_plan=videos,
        portable_execution=(
            dict(path=portable_relative, sha256=digest(ROOT / portable_relative), executed=True)
            if portable
            else dict(path=portable_relative, executed=False, status="Final report not yet received")
        ),
        B_final=b_summary,
        AC_air_delta=dict(
            path="audit/op030_air_drop_ac_v06_completion.json",
            sha256=digest(ROOT / "audit/op030_air_drop_ac_v06_completion.json"),
            reports=ac_delta["reports"],
        ),
        evidence_paths=list(files),
        files=files,
        file_count=len(files),
        total_bytes=sum(v["bytes"] for v in files.values()),
        group_totals=totals,
        document=dict(path=constants["DOCUMENT"], sha256=digest(document_path), draft=not videos_ready),
        document_reference_coverage=coverage,
        automatic_package_inputs=dict(
            package=str(package_path.relative_to(ROOT)),
            sha256=digest(package_path),
            helper_count=19,
            exact_rebake_input_count=23,
            excluded_from_extra_evidence=(
                "Static/native/manifest, prepared, plan, document, 19 helpers and video reports are auto-included"
            ),
        ),
        pending_required_records=(
            ([] if portable else ["Final-camera isolated actual 23-input rebake execution report"])
            + ([] if videos_ready else ["Four encoded videos: actual frame count/duration, complete decode and hashes"])
            + ["Browser delivery check and exact copy/archive inventory verification"]
        ),
        exclusions=[
            "Old v05 B report is included only for saved animation duration comparison, not as "
            "collision/identity proof for the new B path",
            "Old v05 integration/portable success is not substituted for v06 execution",
            "Incomplete B seeds, failed candidates, old videos, huge mesh NPZ/inventory and diagnostic "
            "natives; selected identity_12/connection_11 are completed final evidence",
            "Initial afb642 and repaired e197a90 are provenance; final active static is air-clearance0de256",
        ],
        qualifications=[
            "A/C saved banks remain unchanged. New B background/transfer records retain original 8674 "
            "native pins and are inherited via the separately recorded non-camera identity delta",
            "Initial static completion notes 33mm support gaps; supported completion records their bounded correction",
            "Pipe selection completion records historical pending-B scope; later full B final records "
            "complete that standalone motion check",
            "No formal physical validity, hardware takt or shortest-path proof is made; "
            "encoded-video completion is stated only when all four actual files match their full-decode reports",
            "F01 remains unchanged; two-level pallet return is not implemented; "
            "OP040 connection diagram inquiry pending",
        ],
        previous_v05_preserved=dict(
            selection_path=str(previous_path.relative_to(ROOT)),
            selection_sha256=previous_sha,
            document_path=str(previous_document.relative_to(ROOT)),
            document_sha256=previous_document_sha,
        ),
        stage_downloads_vault_modified=False,
        rebake_executed=portable is not None,
        formal_physical_validity_verdict=None,
    )
    output = ROOT / "analysis/op030_v06_package_evidence.json"
    save(output, selection)
    assert digest(previous_path) == previous_sha and digest(previous_document) == previous_document_sha
    print(
        "V06_DOCUMENT_EVIDENCE_PREPARED",
        len(files),
        selection["total_bytes"],
        digest(document_path),
        digest(output),
        flush=True,
    )


if __name__ == "__main__":
    main()

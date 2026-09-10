# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Rebake the final saved motion from only its portable runtime inputs."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import package_op030_split_v06 as package

PINNED_NATIVE = "8674c2483ac1fe7e3dc42e6b1d14fdc4919f28818784de4f53f878477714d338"
PINNED_AUDIT = "aa633cf21da9400d0b6a0b8fcf7a101544c323984d5e3fc83190c919be1a5dfe"
PINNED_NPZ = "660d47df3dac122337e4ff82c3c4ce92c8e15ef3edf68dbc9dd9b24ed943f296"
PINNED_PREPARED = "0327cf57bfb91b6437ba2ab9fec43f4ac1a04e0a1c4a6633c8b833dcbd63e897"

# Executed inside the isolated Blender process after reopening the saved file.
# This diagnostic is supplied as code, not imported from the original project.
SAVED_READBACK = r"""
import bpy, numpy as np
with np.load(root / "data/op030_split_animation_v06.npz", allow_pickle=False) as z:
    arrays = {key: z[key] for key in z.files}
prepared = json.loads((root / "data/op030_split_animation_v06.json").read_text())
static = json.loads((root / prepared["static_native"]["manifest"]).read_text())
audit = json.loads((root / "audit/op030_split_native_v06.json").read_text())
bpy.ops.wm.open_mainfile(filepath=str(root / "UR15_JB_OP030_split_v06.blend"))
samples = audit["matrix_readback"]["frames"]
matrix_error = wire_error = lug_error = tool_error = pipe_error = drawer_local_error = 0.0
matrix_checks = 0
def compare(name, expected):
    global matrix_error, matrix_checks
    actual = np.asarray(bpy.data.objects[name].matrix_world)
    error = float(np.max(abs(actual - expected)))
    matrix_error = max(matrix_error, error)
    matrix_checks += 1
    assert error <= 5e-5, (name, frame, error)
drawer = static["wire_supply"]["drawer"]
animate.check_drawer_parent(drawer, static)
pipe_poses = {row["name"]: row["after"]["world"] for row in static["air_drop_clearance_v06"]["records"]}
active = {row["uid"] for row in prepared["wires"]}
for frame in samples:
    index = frame - 1
    bpy.context.scene.frame_set(frame)
    bpy.context.view_layer.update()
    compare("JB_OP020_UID001", arrays["product"][index])
    compare("source_0292", arrays["pallet"][index])
    assert abs(bpy.data.objects["source_0292"].matrix_world.translation.z - .789) < 5e-6
    for j, name in enumerate(arrays["object_names"]):
        compare(str(name), arrays["object_poses"][index, j])
    for station in ("A", "B", "C"):
        times = arrays["robot_frames_" + station]
        found = np.flatnonzero(times == frame)
        if len(found):
            cell = static["layout"]["cells"]["OP030" + station]
            for j, node in enumerate(arrays["robot_nodes_" + station]):
                name = cell["source_names"][f"source_{int(node):04d}"]
                if name in bpy.data.objects:
                    compare(name, arrays["robot_poses_" + station][found[-1], j])
    compare(drawer, arrays["drawer_B_world"][index])
    drawer_local_error = max(drawer_local_error, abs(float(bpy.data.objects[drawer].location.x)
                                                    - arrays["drawer_B"][index]))
    for row in static["wires"]:
        if row["uid"] not in active:
            compare(row["uid"], arrays["drawer_B_world"][index])
    for row in prepared["wires"]:
        compare(row["uid"], arrays[f"wire_{row['number']}_root"][index])
        vertex, lug = animate.readback_wire(row, arrays, frame)
        wire_error, lug_error = max(wire_error, vertex), max(lug_error, lug)
    for driver in static["drivers"].values():
        tool_world = np.asarray(bpy.data.objects[driver["root"]].matrix_world)
        flange_world = np.asarray(bpy.data.objects[driver["flange"]].matrix_world)
        tool_error = max(tool_error, float(np.max(abs(tool_world - flange_world))))
    failures = []
    pipe_error = max(pipe_error, animate.readback_background(pipe_poses, frame, failures))
    assert not failures
assert wire_error <= 5e-6 and lug_error <= 5e-5 and tool_error <= 5e-5
assert pipe_error == 0 and drawer_local_error <= 5e-6
for station, row in prepared["fastener_ownership"].items():
    assert all(name in bpy.data.objects for name in row["assembled_uids"] + row["end_loaded_uids"])
saved = dict(sample_count=len(samples), matrix_checks=matrix_checks, maximum_matrix_error=matrix_error,
             maximum_wire_vertex_error_m=wire_error, maximum_lug_matrix_error=lug_error,
             maximum_tool_flange_error=tool_error, air_drop_matrix_error=pipe_error,
             drawer_local_x_error_m=drawer_local_error, drawer_parent=bpy.data.objects[drawer].parent.name,
             active_wire_uids=sorted(active), fastener_ownership=prepared["fastener_ownership"],
             pallet_origin_z_m=.789, removed_restraints_absent=not bool(static.get("retention", {}).get("clips")),
             frames=int(bpy.context.scene.frame_end), formal_physical_validity_verdict=None)
print("PORTABLE_SAVED_READBACK", json.dumps(saved, sort_keys=True), flush=True)
"""


def main():
    destination = ROOT / "analysis/op030_split_portable_rebake_v06.blend"
    report_path = ROOT / "audit/op030_split_layout_portable_rebake_v06.json"
    log_path = ROOT / "audit/op030_split_layout_portable_rebake_v06.log"
    readback_path = ROOT / "audit/op030_split_layout_portable_rebake_native_v06.json"
    for path in (destination, report_path, log_path, readback_path):
        if path.exists():
            raise FileExistsError(path)
    baseline_path = ROOT / package.NATIVE_AUDIT
    baseline_sha = package.digest(baseline_path)
    baseline = json.loads(baseline_path.read_text())
    original_native_sha = package.digest(ROOT / package.NATIVE)
    assert original_native_sha == baseline["output_sha256"] == PINNED_NATIVE
    assert baseline_sha == PINNED_AUDIT
    assert package.digest(ROOT / package.MOTION) == PINNED_NPZ
    assert package.digest(ROOT / package.PREPARED) == PINNED_PREPARED
    assert baseline["presentation_cameras"]
    build_log = ROOT / "audit/op030_split_bake_v06.log"
    assert "OP030_SPLIT_NATIVE_COMPLETE" in build_log.read_text()
    prepared = json.loads((ROOT / package.PREPARED).read_text())
    source = prepared["static_native"]
    selected = (*package.SCRIPT_FILES, package.MOTION, package.PREPARED, source["path"], source["manifest"])
    assert len(selected) == len(set(selected)) == 23 and len(package.SCRIPT_FILES) == 19
    expected_hashes = {
        package.MOTION: prepared["output_sha256"],
        source["path"]: source["sha256"],
        source["manifest"]: source["manifest_sha256"],
    }
    files = {}
    for relative in selected:
        path = package.local_path(ROOT, relative)
        sha = package.digest(path)
        if relative in expected_hashes:
            assert sha == expected_hashes[relative]
        files[relative] = dict(sha256=sha, bytes=path.stat().st_size)
    with tempfile.TemporaryDirectory(prefix="op030_split_portable_rebake_") as directory:
        isolated = Path(directory)
        for relative, record in files.items():
            target = isolated / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / relative, target)
            assert package.digest(target) == record["sha256"]
        expression = (
            "import pathlib,sys,json\n"
            f"root=pathlib.Path({str(isolated)!r})\n"
            "sys.path.insert(0,str(root/'scripts'))\n"
            "import animate_op030_split_v06 as animate\n"
            "assert animate.ROOT==root\n"
            f"animate.bake_native(root/{package.MOTION!r},root/{package.NATIVE!r})\n" + SAVED_READBACK + "\n"
            "loaded={name:str(pathlib.Path(module.__file__).relative_to(root)) "
            "for name,module in sys.modules.items() if getattr(module,'__file__',None) "
            "and pathlib.Path(module.__file__).is_relative_to(root)}\n"
            f"assert all(not str(getattr(module,'__file__','')).startswith({str(ROOT)!r}) "
            "for module in sys.modules.values())\n"
            "print('PORTABLE_REBAKE_IMPORTS',json.dumps(loaded,sort_keys=True),flush=True)\n"
        )
        command = [
            "/home/rlrk/.local/opt/blender-4.5.13-linux-x64/blender",
            "--background",
            "--factory-startup",
            "--threads",
            "2",
            "--python-exit-code",
            "1",
            "--python-expr",
            expression,
        ]
        with log_path.open("w") as stream:
            process = subprocess.run(
                command,
                cwd=isolated,
                stdout=stream,
                stderr=subprocess.STDOUT,
                env={
                    **os.environ,
                    "PYTHONPATH": "",
                    "PYTHONDONTWRITEBYTECODE": "1",
                    "OPENBLAS_NUM_THREADS": "1",
                    "OMP_NUM_THREADS": "1",
                },
                check=False,
            )
        log = log_path.read_text()
        if process.returncode != 0 or "OP030_SPLIT_NATIVE_COMPLETE" not in log:
            raise RuntimeError(f"Portable rebake failed ({process.returncode}); inspect {log_path}")
        loaded = json.loads(
            next(line.split(" ", 1)[1] for line in log.splitlines() if line.startswith("PORTABLE_REBAKE_IMPORTS "))
        )
        saved_readback = json.loads(
            next(line.split(" ", 1)[1] for line in log.splitlines() if line.startswith("PORTABLE_SAVED_READBACK "))
        )
        actual = json.loads((isolated / package.NATIVE_AUDIT).read_text())
        assert actual["prepared_sha256"] == baseline["prepared_sha256"]
        assert actual["source"] == baseline["source"]
        assert actual["frames"] == baseline["frames"] == prepared["frames"]
        assert actual["matrix_readback"]["frames"] == baseline["matrix_readback"]["frames"]
        assert not actual["matrix_readback"]["failures"]
        for key in (
            "wire_animation",
            "presentation_cameras",
            "native_dependencies",
            "downstream_restored_readback",
            "fixed_conveyor",
            "parallel_operations",
            "staggered_layout",
            "fastener_ownership",
        ):
            assert actual[key] == baseline[key], key
        assert not actual["native_dependencies"]["external_images"]
        assert not actual["native_dependencies"]["external_libraries"]
        assert actual["matrix_readback"]["max_error"] <= 5e-5
        assert actual["deformation_readback"]["max_vertex_error_m"] <= 5e-6
        assert actual["deformation_readback"]["max_lug_matrix_error"] <= 5e-5
        assert actual["permanent_tool_readback"]["max_flange_matrix_error"] <= 5e-5
        for relative, record in files.items():
            assert package.digest(isolated / relative) == record["sha256"]
            assert package.digest(ROOT / relative) == record["sha256"]
        assert package.digest(ROOT / package.NATIVE) == original_native_sha
        assert package.digest(baseline_path) == baseline_sha
        output_native = isolated / package.NATIVE
        assert package.digest(output_native) == actual["output_sha256"]
        shutil.move(output_native, destination)
        shutil.copy2(isolated / package.NATIVE_AUDIT, readback_path)
        report = dict(
            observed_at=datetime.now().astimezone().isoformat(),
            baseline_native=dict(path=package.NATIVE, sha256=original_native_sha),
            baseline_readback=dict(path=package.NATIVE_AUDIT, sha256=baseline_sha),
            original_completion_log_sha256=package.digest(build_log) if build_log.exists() else None,
            original_completion_basis=(
                "Pinned final native/audit and prepared SHA chain; isolated completion marker required"
            ),
            copied_inputs=files,
            copied_file_count=len(files),
            helper_count=len(package.SCRIPT_FILES),
            runner_sha256=package.digest(Path(__file__)),
            input_sha256_unchanged=True,
            isolated_imports=loaded,
            original_root_imports=False,
            blender_exit_code=process.returncode,
            output_native=dict(
                path=str(destination.relative_to(ROOT)),
                sha256=package.digest(destination),
                bytes=destination.stat().st_size,
            ),
            output_readback=dict(path=str(readback_path.relative_to(ROOT)), sha256=package.digest(readback_path)),
            log=dict(path=str(log_path.relative_to(ROOT)), sha256=package.digest(log_path)),
            frames=actual["frames"],
            readback_samples=len(actual["matrix_readback"]["frames"]),
            matrix_readback=actual["matrix_readback"],
            deformation_readback=actual["deformation_readback"],
            permanent_tool_readback=actual["permanent_tool_readback"],
            downstream_restored_readback=actual["downstream_restored_readback"],
            native_dependencies=actual["native_dependencies"],
            saved_file_reopened_readback=saved_readback,
            camera_overrides_match=True,
            stage_executed=False,
            temporary_input_copy_removed_after_check=True,
            scope=(
                "Exact saved-motion rebake from packaged helpers plus static native/manifest and prepared NPZ/JSON; "
                "does not rerun IK, collision checking or a formal physical-validity review"
            ),
            formal_physical_validity_verdict=None,
        )
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print("PORTABLE_REBAKE_COMPLETE", report["frames"], report["readback_samples"], str(destination), flush=True)


if __name__ == "__main__":
    main()

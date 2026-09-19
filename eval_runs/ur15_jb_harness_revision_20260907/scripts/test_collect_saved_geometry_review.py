# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Check review-frame provenance rejection and the unchanged legacy collection path."""

import json
from pathlib import Path

import collect_saved_geometry_review as samples
import encode_process_review_video as encoder
import pytest
from encode_review_video import digest


def _write(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value))


@pytest.fixture
def package(tmp_path, monkeypatch):
    for folder in ("data", "audit", "scripts", "previews/samples"):
        (tmp_path / folder).mkdir(parents=True, exist_ok=True)
    for name in ("data/motion.npz", "scripts/renderer.py", "scripts/render_op030_v02.py", "native.blend"):
        (tmp_path / name).write_bytes(b"test-only source identity")
    # Collection hashes bytes; actual image decoding belongs to render/encode readback.
    png = tmp_path / "previews/samples/sample.png"
    png.write_bytes(b"test-only image identity")
    plan_path = tmp_path / "data/plan.json"
    expected = [
        dict(feature_id="P16", saved_frame=f, saved_bank_index=i, saved_time_s=i / 15) for i, f in enumerate((1, 3))
    ]
    plan = dict(
        source_kind="saved_geometry_samples",
        native=None,
        native_sha256=None,
        motion="motion.npz",
        motion_sha256=digest(tmp_path / "data/motion.npz"),
        input_sha256={"data/motion.npz": digest(tmp_path / "data/motion.npz")},
        renderer="scripts/renderer.py",
        camera="process",
        frame_end=8,
        expected_source_samples=expected,
        repeat_each_source_sample=2,
    )
    _write(plan_path, plan)
    rows = [
        dict(
            row,
            display_segment="saved_sample",
            view="process",
            frame=2 * i + 1,
            camera="process",
            file="sample.png",
            sha256=digest(png),
        )
        for i, row in enumerate([row for row in expected for _ in range(2)])
    ]
    manifest = dict(
        complete=True,
        source_kind=plan["source_kind"],
        shot_plan_sha256=digest(plan_path),
        renderer_sha256=digest(tmp_path / plan["renderer"]),
        input_sha256_current=plan["input_sha256"],
        output_fps=15,
        settings={"width": 1, "height": 1},
        images=rows,
    )
    manifest_path = tmp_path / "previews/samples/manifest.json"
    _write(manifest_path, manifest)
    monkeypatch.setattr(samples, "ROOT", tmp_path)
    monkeypatch.setattr(encoder, "ROOT", tmp_path)
    return tmp_path, plan_path, plan, manifest_path, manifest


def test_saved_samples_have_explicit_provenance(package):
    _, path, _, _, _ = package
    plan, records, manifests, _ = encoder.collect_frames(["samples"], path)
    assert plan["native_sha256"] is None
    assert [r["saved_frame"] for r in records.values()] == [1, 1, 3, 3]
    assert len(manifests) == 1


def test_changed_png_is_rejected(package):
    root, path, _, _, _ = package
    (root / "previews/samples/sample.png").write_bytes(b"changed image bytes")
    with pytest.raises(AssertionError):
        encoder.collect_frames(["samples"], path)


def test_omitted_source_sample_is_rejected_even_with_complete_output_count(package):
    _, path, _, manifest_path, manifest = package
    first = manifest["images"][0]
    for row in manifest["images"]:
        for key in ("saved_frame", "saved_bank_index", "saved_time_s"):
            row[key] = first[key]
    _write(manifest_path, manifest)
    with pytest.raises(AssertionError):
        encoder.collect_frames(["samples"], path)


def test_legacy_native_collection_is_preserved(package):
    root, path, plan, manifest_path, manifest = package
    plan.pop("source_kind")
    plan.update(
        native="native.blend",
        native_sha256=digest(root / "native.blend"),
        ranges=[dict(first_frame=1, last_frame=8, camera="process")],
    )
    _write(path, plan)
    manifest.update(
        native_sha256=plan["native_sha256"],
        native_frame_end=8,
        shot_plan_sha256=digest(path),
        renderer_sha256=digest(root / "scripts/render_op030_v02.py"),
    )
    _write(manifest_path, manifest)
    (root / "audit/samples_render.log").write_text("OP030_RENDER_COMPLETE\n")
    actual, records, _, _ = encoder.collect_frames(["samples"], path)
    assert actual == plan and sorted(records) == [1, 3, 5, 7]

# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Copy the observed native and evidence before a bounded review-camera edit."""

import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def digest(path: Path) -> str:
    """Read the exact file SHA256."""
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main() -> None:
    """Preserve original native/source/JSON files without editing their contents."""
    output = ROOT / "analysis/op030_candidate_8674_v06"
    if output.exists():
        raise FileExistsError(output)
    native = ROOT / "UR15_JB_OP030_split_v06.blend"
    source = ROOT / "scripts/animate_op030_split_v06.py"
    assert digest(native) == "8674c2483ac1fe7e3dc42e6b1d14fdc4919f28818784de4f53f878477714d338"
    assert digest(source) == "8d8102e12da3aa60abd5e9242ff2666f7b234d5492a0a6231c72d9a20c1b756b"
    evidence = ROOT / "audit/op030_stagger_v06_integration_evidence.json"
    original = json.loads(evidence.read_text())
    paths = {
        native,
        source,
        evidence,
        ROOT / "scripts/prepare_op030_split_v06.py",
        ROOT / "data/op030_split_animation_v06.json",
        ROOT / "data/op030_split_shots_v06.json",
        ROOT / "audit/op030_split_native_v06.json",
        ROOT / "analysis/op030_stagger_v06_integration_evidence.md",
    }
    references = []
    changed_after_observation = []
    for row in original["evidence"]:
        path = Path(row["path"])
        if not path.is_absolute():
            path = ROOT / path
        actual = digest(path)
        if actual != row["sha256"]:
            # The reviewed table-label correction happened after collection;
            # preserve both provenance values instead of rewriting the raw JSON.
            assert path == ROOT / "scripts/collect_op030_stagger_integration_v06.py", str(path)
            changed_after_observation.append(
                dict(
                    path=str(path.relative_to(ROOT)),
                    observed_sha256=row["sha256"],
                    current_sha256=actual,
                    reason="Later MD table-label correction: drawer return applies only to b_c; no mechanics change.",
                )
            )
        if path.suffix in {".json", ".md", ".py"}:
            paths.add(path)
        else:
            references.append(dict(path=str(path.relative_to(ROOT)), sha256=row["sha256"], bytes=path.stat().st_size))
    copies = []
    for path in sorted(paths):
        relative = path.relative_to(ROOT)
        destination = output / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        before = digest(path)
        shutil.copy2(path, destination)
        assert digest(destination) == digest(path) == before
        assert destination.stat().st_ino != path.stat().st_ino
        copies.append(dict(path=str(relative), sha256=before, bytes=path.stat().st_size, independent_inode=True))
    manifest = dict(
        observed_at=datetime.now().astimezone().isoformat(),
        copies=copies,
        unchanged_external_references=references,
        source_changes_after_evidence_observation=changed_after_observation,
        reason="Before review-camera-only fitting; raw integration report SHA pins remain unchanged.",
        prior_art=dict(findings=30, blockers=23, report="audit/op030_camera_delta_v06_prior_art.log"),
        concrete_delta="Read-only equivalence of camera fitting, distinct from old physical on-hand camera collisions.",
    )
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print("CAMERA_BASELINE_PRESERVED", output, len(copies), len(references), flush=True)


if __name__ == "__main__":
    main()

"""Calibrate co_run against lines whose co-run length and shape are known by construction.

Runs without Blender. The probe imports bpy at module scope, so bpy and the two build modules
it borrows from are stubbed; nothing below touches either.

Every case states what the answer must be before it is measured. Two defects were found this
way and neither would have shown up on the scene: a 2 mm gap was being called a boundary of a
10 mm limit, and a pair that never came close raised an exception instead of returning nothing
-- on a 118 pair survey that is not one bad row, it is no survey.

    python3 scripts/check_co_run_calibration.py
"""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PROBE = HERE / "probe_op030_v07c_routing_survey.py"


class _Anything:
    """Stands in for whatever the probe reads off bpy while it is being imported."""

    def __getattr__(self, name: str) -> _Anything:
        return _Anything()

    def __call__(self, *args: object, **kwargs: object) -> _Anything:
        return _Anything()


def load_probe() -> types.ModuleType:
    """Import the probe with Blender stubbed out."""
    for name in ("bpy", "mathutils", "mathutils.bvhtree"):
        sys.modules.setdefault(name, types.ModuleType(name))
    for attribute in ("types", "data", "context", "ops"):
        setattr(sys.modules["bpy"], attribute, _Anything())
    sys.modules["mathutils.bvhtree"].BVHTree = _Anything()
    for name, members in (
        ("build_op030_split_v04", ("_world_vertices",)),
        ("build_op030_stagger_static_v06", ("digest", "geometry")),
    ):
        module = types.ModuleType(name)
        for member in members:
            setattr(module, member, _Anything())
        sys.modules[name] = module
    spec = importlib.util.spec_from_file_location("probe_under_test", PROBE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


probe = load_probe()
STEP = probe.STEP_M
LIMIT = 0.010


def straight(count: int) -> np.ndarray:
    """A run along +Y sampled at the probe's own step, so lengths are exact multiples of it."""
    return np.array([[0.0, index * STEP, 0.0] for index in range(count)])


def partner(count: int, closes: list[tuple[int, int, float]]) -> np.ndarray:
    """A second run held far away except where it is asked to come within a stated distance."""
    line = straight(count)
    line[:, 0] = 0.500
    for first, last, distance in closes:
        line[first:last, 0] = distance
    return line


def case(title: str, expected: dict, second: np.ndarray, count: int = 60) -> bool:
    measured = probe.co_run(straight(count), second, (LIMIT,))
    if not measured:
        print(f"FAIL {title}: co_run returned nothing at all")
        return False
    got = measured[0]
    bad = {key: (value, got.get(key)) for key, value in expected.items() if not close_enough(value, got.get(key))}
    print(f"{'ok  ' if not bad else 'FAIL'} {title}")
    for key, (want, have) in bad.items():
        print(f"       {key}: expected {want}, got {have}")
    return not bad


def close_enough(want: object, have: object) -> bool:
    if isinstance(want, float) and isinstance(have, float):
        return abs(want - have) < 1e-9
    return want == have


def one_firm_end_and_one_soft() -> bool:
    """A span can be firm at one end and on the limit at the other.

    S3R at 56 mm sits 2.1 mm from the limit at one end and 7.1 mm at the other, which the
    executor had to measure by hand because only the count was reported. Each boundary now
    carries its own margin, so the asymmetry is readable without a second instrument.
    """
    uncertainty = probe.CENTRE_LINE_GAP_UNCERTAINTY_M
    # Held well inside the limit, then tapering onto it just before parting.
    second = partner(60, [(10, 19, 0.002), (19, 20, 0.0099)])
    got = probe.co_run(straight(60), second, (LIMIT,))[0]
    span = got["spans"][0]
    before, after = span["margin_before_m"], span["margin_after_m"]
    ok = before is not None and after is not None and before > uncertainty > after
    print(f"{'ok  ' if ok else 'FAIL'} a span firm at one end and on the limit at the other")
    print(f"       margin before {before:.4f} m, after {after:.4f} m, against {uncertainty:.4f} m of uncertainty")
    return ok


def invisible_dip_is_not_a_lower_bound() -> bool:
    """Show that extent_sampled_m can exceed the length the runs are truly together.

    The second run spikes away between two samples of the first and comes straight back. No
    sample sees it, so co_run reports one unbroken span, while the runs have in fact parted.
    This is why the sampled figure is not named a lower bound.
    """
    first = straight(40)
    close, away = 0.002, 0.200
    second = [[close, index * STEP, 0.0] for index in range(10, 15)]
    second += [[away, 14 * STEP + STEP / 2, 0.0]]  # the spike, between two samples
    second += [[close, index * STEP, 0.0] for index in range(15, 21)]
    got = probe.co_run(first, np.array(second), (LIMIT,))[0]
    # Every sample from 10 to 20 is within the limit of some segment, so one span is reported.
    reported = got["extent_sampled_m"]
    midpoint = np.array([0.0, 14 * STEP + STEP / 2, 0.0])
    truly_apart = min(
        probe.segment_gap(midpoint, midpoint, np.array(second[j]), np.array(second[j + 1]))[0]
        for j in range(len(second) - 1)
    )
    ok = got["span_count"] == 1 and truly_apart > LIMIT and reported > 0.0
    print(f"{'ok  ' if ok else 'FAIL'} the sampled extent is not a lower bound")
    print(
        f"       reported one span of {reported:.4f} m, while midway between two samples the"
        f" runs are {truly_apart:.4f} m apart, which is outside the {LIMIT} m limit"
    )
    return ok


def main() -> int:
    print(f"step {STEP} m, limit {LIMIT} m, gap uncertainty {probe.CENTRE_LINE_GAP_UNCERTAINTY_M:.4f} m\n")
    results = [
        # Fourteen points held at 2 mm: thirteen steps of witnessed width, padded by one each end.
        case(
            "one continuous approach witnesses its own width",
            dict(span_count=1, extent_sampled_m=13 * STEP, extent_upper_m=15 * STEP, span_shape_resolved=True),
            partner(60, [(10, 24, 0.002)]),
        ),
        # Two approaches with a real parting between them must not be reported as one.
        case(
            "two approaches stay two",
            dict(span_count=2, extent_sampled_m=10 * STEP, zero_width_spans=0, span_shape_resolved=True),
            partner(60, [(10, 16, 0.002), (26, 32, 0.002)]),
        ),
        # A single sample witnesses no length. The old extent credited it with two steps.
        case(
            "a single point witnesses nothing",
            dict(span_count=1, zero_width_spans=1, extent_sampled_m=0.0, extent_upper_m=2 * STEP),
            partner(60, [(20, 21, 0.002)]),
        ),
        # Gaps sitting on the limit: the samples cross it in and out and the shape is an artefact.
        case(
            "gaps on the limit leave the shape unresolved",
            dict(span_shape_resolved=False),
            partner(60, [(i, i + 1, 0.009 if i % 2 == 0 else 0.011) for i in range(10, 30)]),
        ),
        # The control for the case above. 2 mm against a 10 mm limit is not a close boundary.
        case(
            "gaps far from the limit leave the shape resolved",
            dict(span_count=1, span_shape_resolved=True),
            partner(60, [(10, 24, 0.002)]),
        ),
        # Parting to 50 mm and returning is a real parting at every distance that matters.
        case(
            "a real parting is resolved, not smoothed away",
            dict(span_count=2, span_shape_resolved=True),
            partner(60, [(10, 20, 0.002), (20, 30, 0.050), (30, 40, 0.002)]),
        ),
        # A span that runs off the end of the line is a lower bound, and says so.
        case(
            "a span reaching the end of the run is flagged",
            dict(span_count=1, touches_run_end=True),
            partner(60, [(45, 60, 0.002)]),
        ),
        # Most pairs in the survey never come close. This must return an empty span list.
        case(
            "no approach at all returns nothing, and does not raise",
            dict(span_count=0, points_inside=0, extent_sampled_m=0.0, extent_upper_m=0.0, spans=[]),
            partner(60, []),
        ),
    ]
    results.append(one_firm_end_and_one_soft())
    results.append(invisible_dip_is_not_a_lower_bound())
    failed = results.count(False)
    print(f"\n{len(results) - failed} of {len(results)} cases hold")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""JB harness concept geometry; commercial envelopes are not detailed vendor CAD.

Lengths [m]. The wire construction and connector envelope use the references in
product_definition.json. Bends, supports and circuit layout remain design inputs.
"""

from __future__ import annotations

import math

import numpy as np

WIRE_RADIUS = 0.0158 / 2
PIN_PITCH = 0.023
ROUTE_RADIUS = 0.090
NOMINAL_ROUTE_LENGTH = 0.900
PORT_FRAME = np.array([[0, 0, -1], [-1, 0, 0], [0, 1, 0]], dtype=float)
FREE_FRAME = np.array([[0, 0, -1], [0, 1, 0], [1, 0, 0]], dtype=float)
PORT_ORIGIN = np.array([-0.250, -0.300, 0.012])


def route_paths():
    """Return two continuous conductor routes, including unequal bend allowances [m]."""
    # Arc-length parameterization avoids duplicated points at segment joins.
    initial = 0.0555
    outgoing = 0.310
    returning = NOMINAL_ROUTE_LENGTH - initial - 1.5 * math.pi * ROUTE_RADIUS - outgoing
    lengths = [initial, math.pi * ROUTE_RADIUS / 2, outgoing, math.pi * ROUTE_RADIUS, returning]
    yz, tangent = [], []
    y, z = -0.300, 0.0545
    for section, length in enumerate(lengths):
        for s in np.linspace(0, length, max(3, math.ceil(length / 0.0015))):
            if yz and s == 0:
                continue
            if section == 0:
                point, direction = (y, z + s), (0, 1)
            elif section == 1:
                a = s / ROUTE_RADIUS
                point = (y + ROUTE_RADIUS * (1 - math.cos(a)), z + ROUTE_RADIUS * math.sin(a))
                direction = (math.sin(a), math.cos(a))
            elif section == 2:
                point, direction = (y + s, z), (1, 0)
            elif section == 3:
                a = s / ROUTE_RADIUS
                point = (y + ROUTE_RADIUS * math.sin(a), z - ROUTE_RADIUS * (1 - math.cos(a)))
                direction = (math.cos(a), -math.sin(a))
            else:
                point, direction = (y - s, z), (-1, 0)
            yz.append(point)
            tangent.append(direction)
        y, z = point
    yz, tangent = np.asarray(yz), np.asarray(tangent)
    normals = np.column_stack((-tangent[:, 1], tangent[:, 0]))
    # The last 110 mm shifts outward by 10 mm to meet the capped free connector.
    # The quintic blend has zero slope and curvature at both ends.
    u = np.clip(
        (np.arange(len(yz)) - (len(yz) - math.ceil(returning / 0.0015))) / max(1, math.ceil(returning / 0.0015) - 1),
        0,
        1,
    )
    shift = 6 * u**5 - 15 * u**4 + 10 * u**3
    paths = []
    for sign in (-1, 1):
        offset = yz + sign * PIN_PITCH / 2 * normals
        paths.append(np.column_stack((-0.282 - 0.010 * shift, offset)))
    origin = np.array([-0.260, yz[-1, 0] - 0.0425, yz[-1, 1]])
    return paths, origin


def frame_object(obj, rotation, location):
    """Assign a rigid local transform [m]."""
    from mathutils import Matrix

    pose = np.eye(4)
    pose[:3, :3], pose[:3, 3] = rotation, location
    obj.matrix_basis = Matrix(pose.tolist())


def connector(name, parent, rotation, location, *, cap=False, lever_open=False):
    """Create a 2-pole, right-angle plug envelope and articulated lock [m]."""
    from allocation_product import box, cylinder, empty, material

    orange = material("JB_HV_orange", (0.78, 0.175, 0.025), 0.06, 0.39)
    black = material("JB_polymer_black", (0.027, 0.033, 0.039), 0.0, 0.46)
    grey = material("JB_connector_metal", (0.34, 0.38, 0.41), 0.65, 0.32)
    red = material("JB_secondary_lock_red", (0.50, 0.025, 0.018), 0, 0.40)
    root = empty(name, parent)
    root["geometry_basis"] = (
        "TE HVP800 2P 90-degree published envelope; modeled approximation, not vendor CAD"  # codespell:ignore te
    )
    root["published_envelope_m"] = [0.0975, 0.085, 0.0623]
    root["connector_end"] = "vehicle_end_capped" if cap else "JB_end"
    frame_object(root, rotation, location)
    # Mating neck is narrower than the backshell. The rigid envelope includes
    # lever cheeks; two individual cable entries are visible at the elbow.
    box(name + "_mating_neck", (0.061, 0.037, 0.013), (0, 0, 0.0065), black, root, 0.004)
    box(name + "_backshell", (0.0855, 0.074, 0.0493), (0, 0, 0.03765), orange, root, 0.008)
    for x in (-0.0115, 0.0115):
        cylinder(name + f"_wire_seal{x}", 0.0097, 0.013, (x, 0.036, 0.032), black, root, (math.pi / 2, 0, 0))
        cylinder(name + f"_pin_socket{x}", 0.0041, 0.010, (x, 0, 0.002), grey, root)
    lever = empty(name + "_lever", root)
    lever.location = (0, -0.022, 0.027)
    for x in (-0.046, 0.046):
        box(name + f"_lever_cheek{x}", (0.0055, 0.053, 0.012), (x, 0.0235, 0), black, lever, 0.003)
        cylinder(name + f"_lever_pin{x}", 0.006, 0.004, (x, 0, 0), grey, lever, (0, math.pi / 2, 0))
    box(name + "_lever_bridge", (0.094, 0.008, 0.012), (0, 0.049, 0), black, lever, 0.003)
    lever.rotation_euler.x = -math.radians(80) if lever_open else 0
    cpa = box(name + "_CPA", (0.018, 0.009, 0.007), (0, -0.024, 0.0588), red, root)
    cpa["function"] = "secondary_lock; actuator/contact details provisional"
    if cap:
        cover = box(name + "_shipping_cap", (0.063, 0.039, 0.0014), (0, 0, -0.0007), black, root, 0.0005)
        cover["function"] = "removable manufacturing protection; no IP rating claimed"
        box(name + "_cap_pull_tab", (0.018, 0.008, 0.0104), (0, -0.023, 0.0045), black, root)
    return root


def replace_headers(housing, product):
    """Replace four single-pipe visual receivers with distinguishable two-pole interfaces [m]."""
    import bpy
    from allocation_product import box, cylinder, empty, material

    metal = material("JB_header_flange", (0.42, 0.46, 0.49), 0.72, 0.38)
    polymer = material("JB_header_polymer", (0.032, 0.04, 0.045), 0, 0.42)
    copper = material("JB_contact_copper", (0.64, 0.37, 0.13), 0.78, 0.28)
    for obj in list(housing.children):
        if int(obj.name.rsplit("_p", 1)[-1]) >= 6:
            bpy.data.objects.remove(obj, do_unlink=True)
    # Preserve the original housing mesh, including its 34-mm through-bores.
    # The two 8-mm pins at 23-mm pitch fit inside those openings geometrically.
    # The rectangular outer mating interface remains a concept header, not a
    # released vendor panel cutout or an electrical-clearance specification.
    for index, (x, y, purpose) in enumerate(
        (
            (-0.238, -0.300, "J1_inverter"),
            (-0.238, 0.300, "J2_battery_input"),
            (0.238, -0.300, "J3_charge_input"),
            (0.238, 0.300, "J4_auxiliary_output"),
        ),
        1,
    ):
        header = empty(product.name + "_" + purpose, product)
        header["port_role"] = purpose
        header["definition_status"] = "concept connection table; rating and circuit not released"
        # Frame follows the mating plane, leaving a real aperture in the flange.
        sign = math.copysign(1, x)
        for yy in (-0.035, 0.035):
            box(header.name + f"_flange_side{yy}", (0.007, 0.014, 0.053), (sign * 0.2445, y + yy, 0.012), metal, header)
        for zz in (-0.023, 0.023):
            box(header.name + f"_flange_edge{zz}", (0.007, 0.057, 0.007), (sign * 0.2445, y, 0.012 + zz), metal, header)
        for yy in (-0.0115, 0.0115):
            cylinder(
                header.name + f"_contact{yy}",
                0.004,
                0.020,
                (sign * 0.237, y + yy, 0.012),
                copper,
                header,
                (0, math.pi / 2, 0),
            )
        for yy in (-0.035, 0.035):
            for zz in (-0.018, 0.018):
                cylinder(
                    header.name + f"_bolt{yy}_{zz}",
                    0.003,
                    0.003,
                    (sign * 0.249, y + yy, 0.012 + zz),
                    metal,
                    header,
                    (0, math.pi / 2, 0),
                    6,
                )
        if index != 1:
            box(header.name + "_blanking_cap", (0.004, 0.059, 0.037), (sign * 0.251, y, 0.012), polymer, header)


def harness_and_carrier(product, stage):
    """Add one consistent harness assembly and a separately identified carrier [m]."""
    from allocation_product import box, cylinder, empty, material, tube

    orange = material("JB_HV_orange", (0.78, 0.175, 0.025), 0.06, 0.39)
    polymer = material("JB_fixture_liner", (0.08, 0.12, 0.15), 0, 0.52)
    blue = material("JB_removable_carrier", (0.12, 0.27, 0.34), 0.20, 0.43)
    paths, free_origin = route_paths()
    if stage >= 2:
        harness = empty(product.name + "_E01_harness", product)
        harness["assembly_id"] = product.name + "/E01"
        harness["wire_count"] = 2
        harness["end_A"] = "J1 JB-side mated"
        harness["end_B"] = "vehicle inverter end capped and held in removable carrier"
        for number, points in enumerate(paths, 1):
            wire = tube(harness.name + f"_wire_{number}", points, WIRE_RADIUS, orange, harness)
            wire["drawn_centerline_length_m"] = float(np.linalg.norm(np.diff(points, axis=0), axis=1).sum())
            wire["manufacturer_min_bend_radius_m"] = "not verified"
        connector(harness.name + "_A_JB", harness, PORT_FRAME, PORT_ORIGIN)
        connector(harness.name + "_B_vehicle", harness, FREE_FRAME, free_origin, cap=True)
    carrier = empty(product.name + "_F01_removable_transport_carrier", product)
    carrier["ownership"] = "manufacturing_transport_tooling; remove for vehicle installation"
    carrier["operation"] = "moves with JB to rack; original process pallet remains on line"
    # The detachable bottom carrier fits above the original pallet. Two pickup
    # cheeks provide an explicit transfer interface for the unloading tool.
    for x in (-0.240, 0.240):
        box(carrier.name + f"_under_rail{x}", (0.018, 0.72, 0.008), (x, 0, -0.059), blue, carrier)
    for y in (-0.24, 0.24):
        box(carrier.name + f"_crossmember{y}", (0.580, 0.018, 0.008), (-0.020, y, -0.059), blue, carrier)
    # Stop 7.5 mm short of the preserved pallet corner nests at Y = +/-300 mm.
    box(carrier.name + "_side_base", (0.054, 0.510, 0.010), (-0.301, 0.0, -0.053), blue, carrier)
    # Open comb saddles support the two separated conductors without crossing
    # the lid opening. No support tower is a component of the installed product.
    for y in (-0.125, 0.030):
        box(carrier.name + f"_comb_stem{y}", (0.010, 0.016, 0.236), (-0.317, y, 0.070), blue, carrier)
        for z in (0.1885, 0.2115):
            cylinder(
                carrier.name + f"_saddle{y}_{z}",
                0.0045,
                0.031,
                (-0.301, y, z - WIRE_RADIUS - 0.0045),
                polymer,
                carrier,
                (0, math.pi / 2, 0),
            )
    box(carrier.name + "_free_end_nest", (0.024, 0.062, 0.02525), (-0.308, free_origin[1], -0.035375), polymer, carrier)
    for y in (-0.20, 0.20):
        box(carrier.name + f"_pickup_cheek{y}", (0.013, 0.05, 0.065), (0.265, y, -0.020), blue, carrier)
    return carrier


def definition():
    """Return source provenance and the current design dimensions [m]."""
    paths, free_origin = route_paths()
    values = np.vstack(paths)
    return {
        "revision": "jb_inverter_harness_v02",
        "accepted_scenario": "JB end mated; inverter end capped in removable transport tooling",
        "reference_connector": {
            "manufacturer": "TE Connectivity",  # codespell:ignore te
            "part": "YHV800-2P-90-50M-A",
            "envelope_m": [0.0975, 0.085, 0.0623],
            "pin_pitch_m": PIN_PITCH,
            "url": "https://www.te.com/en/product-YHV800-2P-90-50M-A.html",  # codespell:ignore te
            "geometry": "modeled envelope, not detailed vendor CAD",
        },
        "reference_wire": {
            "manufacturer": "Coroflex",
            "family": "9-2611 COROFLEX 180HV SSC FHL2GCB2G",
            "section_mm2": 50,
            "outer_diameter_m": 2 * WIRE_RADIUS,
            "count": 2,
            "url": "https://www.coroflex-cable.com/en/high-voltage-cables/coroflex-180hv-ssc-fhl2gcb2g/",
            "manufacturer_min_bend_radius_m": None,
        },
        "wire_drawn_lengths_m": [float(np.linalg.norm(np.diff(p, axis=0), axis=1).sum()) for p in paths],
        "reference_route_length_m": NOMINAL_ROUTE_LENGTH,
        "provisional_center_route_radius_m": ROUTE_RADIUS,
        "smallest_planar_wire_arc_radius_m": ROUTE_RADIUS - PIN_PITCH / 2,
        "cable_bounds_local_m": [list(values.min(0) - WIRE_RADIUS), list(values.max(0) + WIRE_RADIUS)],
        "free_connector_origin_m": free_origin.tolist(),
        "port_roles": {"J1": "inverter output", "J2": "battery input", "J3": "charge input", "J4": "auxiliary output"},
        "port_role_status": "concept allocation; actual electrical circuit and ratings not released",
        "added_transport_tooling": "F01 removable carrier including cable combs, free-end nest and pickup cheeks",
        "vehicle_installed_support_towers": False,
        "electrical_test_results": None,
        "validation": "auxiliary geometry review only; no formal physical-validity verdict",
    }


def build_jb_product(template, name, stage=8):
    """Build the accepted product scenario through an assembly stage [m]."""
    from allocation_product import build_product
    from continuous_common import delete_tree

    product = build_product(template, name, stage=stage)
    # Reuse the corrected cover, locating sleeves, and latch subassemblies only.
    # The withdrawn U-arch and product-mounted towers must never survive reuse.
    for child in list(product.children):
        if "_B04_support_" in child.name or "_E01_" in child.name:
            delete_tree(child)
    housing = next(obj for obj in product.children if "_B01_B02_B03" in obj.name)
    replace_headers(housing, product)
    harness_and_carrier(product, stage)
    product["product_revision"] = "jb_inverter_harness_v02"
    product["shipping_definition"] = "J1 mated, vehicle end capped; F01 transport tooling removable"
    product["circuit_definition"] = "concept interface roles only; wiring and ratings pending engineering definition"
    return product

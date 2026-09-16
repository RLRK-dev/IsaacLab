# UR15 production-line video work

Apply the repository AGENTS.md and THREAD Vault protocol.

## User-selected video format (2026-09-11)

- For all new revisions, render only the process view (`--views process`).
- Generate only `*_split_process_*_review.mp4`, with the process descriptions burned in.
- Use `scripts/encode_process_review_video.py` to encode the PNG frames directly into that MP4. Do not generate an intermediate raw MP4 or a separate wide-view movie.
- Put only this video type in new Downloads deliveries and ZIP archives. Native models, source, still images and verification records can accompany it.
- `data/video_delivery_policy.json` records the same user preference. Older encoders, orchestration scripts and four-video packages are historical reproduction inputs, not defaults for new work.

The user confirmed `UR15_JB_OP030_split_process_v06_review.mp4` and instructed proceeding to OP040 on 2026-09-11. Use the delivered v06 native and its recorded product state as the starting point. User review of the video is not a formal physical-validity verdict.

OP040's final-frame incoming snapshot is in `audit/op040_incoming_product_v01.json`. `OP040_工程・部品確認書_v01.md` proposes six new wires, an incoming distribution subassembly, and separate routing/fastening stations. These are review proposals, not accepted product requirements; do not treat the proposed D04 or extra station as present in v06.

On 2026-09-12 the user selected actual-product connection drawings and parts
lists, and requested searching the internet because no such files were available.
`analysis/op040_real_reference_research_20260912.md` records the public evidence
and its missing details. The Ampere product is a reference candidate, not an
adopted replacement for the v06 product. Keep unpublished dimensions and part
numbers unknown until their basis and the scope of the product change are set.

## User decisions received on 2026-09-13

- The user subsequently approved matching the Ampere public circuit and major
  components, including a new upstream product revision. Preserve v06. The
  September 12 candidate status above is historical; unpublished manufacturing
  dimensions and complete part numbers are still unknown.
- Divide work among three stations operating on separate workpieces in parallel.
  This does not require three arms at each station.
- Video/model motion production was paused. The currently authorized work is
  selecting hands and documenting their process roles before arm trajectories.
- Prefer a single arm where it completes the task. Retain OP030-A/B as the user's
  dual-arm candidates. Consider three arms only where their distinct roles are
  necessary; permission to consider them is not a selected three-arm mechanism.
- Consider two-, three-, and four-finger hands. Set the finger count, arrangement,
  drive configuration, fingertip geometry and grasp interfaces before designing
  complete arm motion. The supplied G3/G4 documents are design inputs, not
  verified product capabilities or automatically adopted acceptance criteria.
- The v06 B wire animation prescribes the full centerline and derives hand
  targets from it. Its length and geometry checks do not demonstrate physical
  S-bending using endpoint grasps. Do not present them as such.
- See `analysis/hand_selection_inputs_20260913.md` for source comparison,
  candidate roles and unresolved hand-selection inputs. Do not reinstate deleted
  cable hold-down mechanisms as an automatic response to the S-bend question.

## Subsequent handoff decision on 2026-09-13

- The user withdrew the pallet upper-retainer proposal and requested fastening
  while the fingers continue holding the cable/terminal. The v01 retainer pack
  is historical comparison evidence, not a hardware selection.
- Compare continuous hand retention and fastening at the same work position.
  Do not describe release at B followed by transport and regrasp at C as solving
  the unsupported interval. Do not invent a transport-capable temporary torque.
- Two holding arms plus station-mounted fastening units are a comparison
  candidate; no extra robot or selected fastening hardware is authorized by
  that candidate label. Keep the existing simultaneous different-size fastening
  requirement visible. Three-station task redistribution remains unresolved.
- `data/hand_held_fastening_v01.json` and the corresponding analysis document
  record the new direction. Existing hand-function v01 and fixture v01 describe
  the earlier handoff proposals. Arm trajectory and video production stay paused.
- The subsequent user `ok` authorized the next comparison step.
  `analysis/three_station_connection_groups_v01.md` proposes A for mechanical
  mounting, B for main/precharge/discharge power connections, and C for auxiliary
  and control connections. This is not a selected factory process or arm count.
  Actual common fastener stacks and incoming one-piece harnesses may change the
  B/C boundary; electrical common nodes do not establish physical shared bolts.
- `data/hand_target_contacts_v02.json` updates target-family station labels and
  holding periods for that proposal. Use F01-F10 for the current correspondence;
  the v01 A/B-prefixed IDs and placement-at-B/fastening-at-C notes are historical.
  Busbars and fuse bodies are assigned to their connection stage as candidates;
  separately supplied support bodies may be mounted at A. Two fingers remain
  the baseline comparison. Contact dimensions, force and installed hand counts
  are unselected, including the three targets without photo-location annotations.
- `analysis/hand_tool_access_v01.md` observes the unchanged isolated EDGE/GUIDE
  meshes. The 50 mm illustrative tool band has a different result from the
  extended band: in the near pose, the tool axis intersects a gripper-body
  surface at 120.577 mm above the sample connection plane. Do not extrapolate
  the short-band radial difference to a complete socket or fastening unit.
  The observation does not select tool dimensions, redesign the hand, or
  establish physical validity. Preserve the source mesh and saved poses when
  reproducing it; production arm motion and video remain paused.
- The user then requested moving the black hardware away from the terminal to
  maximize tool space. `analysis/hand_body_setback_v01.md` compares 30/60 mm
  rearward body offsets against the original EDGE sample. The original hardware
  geometry and four joint states are retained; the blue carriers extend while
  the terminal-side contact contours retain their world positions. Offsets,
  beam sections and tool cylinders are comparison values, not selected hardware.
  Upper tool space and lower fingertip space are separate observations. Existing
  carrier/mount surface overlaps remain recorded; mounting details, stiffness
  and force capability are unresolved. No upper retainer or arm motion is added.
- `analysis/hand_mount_interface_v02.md` records the subsequent mounting detail.
  The retained 2016-dated mesh matches the 2018 manual's 14 x 31 mm face, two
  3.4 mm clearances at 16 mm pitch, and central 3 mm indexing hole. The later
  2019 TM M5-center drawing does not match it. Keep that version distinction.
  The new 4 mm plate and nominal smooth M3/index bores are comparison geometry;
  no material, manufacturing fit, screw engagement or force criterion is chosen.
  The source hardware, contacts and saved transforms stay unchanged. Closed
  edge topology is observed, but zero-area tessellation faces and mounting
  surface contacts remain explicitly recorded; this is not manufacturing CAD
  or a physical acceptance verdict. Arm motion and video remain paused.

## Initial setback and root clamp decision on 2026-09-13

- The user selected 40 mm as the initial body setback and requested cable
  clamping at the mounting area as well as the existing terminal-side contact.
  The earlier 30/60 mm alternatives remain historical comparisons.
- `data/hand_root_clamp_v03.json` and `analysis/hand_root_clamp_v03.md` describe
  the new D40 sample: front terminal contours retained, paired root jacket
  pads at Y=61-71 mm, attached to the same original distal links. No separate
  actuator or upper retainer is added. The 10 mm contact length, reference
  14 mm wire and pad dimensions are comparison geometry, not identified Ampere
  parts or manufacturing specifications.
- Nominal pad surfaces match the saved wire facets. This does not establish
  pressure distribution or stable holding at both contact locations with one
  actuator. Pad material, compliance, attachment and screw access remain open;
  preserve the existing front contour's 0.1 mm display gap in observations.
- Four static poses, native readback, browser checks and surface-pair records
  are auxiliary observations. Original mounting contacts and degenerate faces
  remain recorded. Finger selection precedes arm motion and video production.

## Pad conditions comparison on 2026-09-14

- The user authorized the next pad-compliance/holding-condition study after
  confirming D40. `analysis/hand_pad_conditions_v01.md` compares P1 (terminal
  positioning contour and compliant root pad) before P2 (a guided passive root
  mechanism if pad compression is insufficient). Neither is manufacturing
  approval, and P2 has not been fitted into the current 3 mm backing space.
- The UI's closure, contact lead and stiffness ratio are a one-dimensional
  teaching example. Its normalized reactions are not N, four contact-force
  targets, friction capacities or gripper force commands. Actual values and
  acceptance requirements remain null in `data/hand_pad_conditions_v01.json`.
- Robotiq's public 60A silicone and the supplied G3/G4 draft's A30-50/3 mm are
  references, not selected D40 pad properties. Use measured compression,
  friction, pressure, time response and actual part limits before selecting
  force settings. Do not infer local pad forces from motor current or wrist
  resultant alone. Check the source-generation grasp-mode/equilibrium-line
  behavior; four saved poses do not establish its loaded behavior.

## Pad service comparison on 2026-09-14

- The subsequent user `ok` continued hand selection. The D40 service comparison
  in `analysis/hand_pad_service_v01.md` uses unchanged geometry and proposes
  replacing one complete custom fingertip through the original two screws.
  It does not select a separate root cartridge, adhesive, material or force.
- The retained holder takes its screws from the outer side (2018 manual p25).
  The root pads are absent from the measured outer 50 mm axial band in all four
  saved poses. Do not require removing them first solely because they overlap
  the inner-side screw projection. The 2 mm hex envelope and 50 mm shaft band
  do not establish access for a complete selected tool or screw extraction.
- Detached service translations sampled every 0.5 mm retain carrier/holder
  surface crossings in 10 of 25 samples per side. The local observation places
  the nonzero-offset crossing candidates near the mounting upper edge. Do not
  treat the last 12 mm illustration or zero later samples as a collision-free
  continuous removal path. Screw heads and the indexing pin are absent.
- During these observations, translate derived vertices instead of reassigning
  Blender scene matrices: the first attempt failed exact restoration because
  reassigning a matrix changes its floating-point decomposition. Keep the
  original mesh data and four poses intact, and retain the failed-run log.
- Root pad-to-support joining, support integration, mounting-edge relief,
  custom screw engagement and the needed pin travel remain design inputs.
  Physical acceptance, arm trajectories and video production remain outside
  this isolated service study.

## Mounting upper-edge comparison on 2026-09-14

- The following user `ok` authorized the local relief comparison recorded in
  `analysis/hand_mount_relief_v01.md`. Only four upper plate corners per side
  move, by 0.25 or 0.5 mm along the source mounting face. D40's original
  hardware, hole rims, terminal/root contacts and four poses stay unchanged.
  Neither relief value is selected for manufacture or an acceptance threshold.
- Repeating the same service samples gives surface pairs in nine of 24 positive
  offsets per side for the baseline and zero for both relief candidates. The
  zero-offset mounting surface pairs remain included in the full record.
  Do not infer continuous extraction, pin/screw access or loaded clearance from
  these samples. Original degenerate tessellation faces remain unmodified.
- Service sampling continues using derived world vertices without reassigning
  scene matrices. When comparing historical static reports, normalize only the
  candidate prefix in scene-qualified object names; keep measurements intact.
  Root support joining, material/compliance, screw engagement and actual
  manufacturing tolerances remain unresolved. Arm/video production stays paused.

## Integral root-support comparison on 2026-09-14

- The user continued after the relief comparison. The new J025/J050 candidates
  in `analysis/hand_support_integration_v01.md` combine each blue root support
  with its carrier while retaining D40's hardware, terminal/root pad meshes,
  colors and four saved poses. Both relief values remain comparison values.
- Rebuild the previous nominal primitives in the measured mounting frame and
  bore once. Re-Booleaning the old tessellated carrier failed closed-topology
  assertions; retain that failed output instead of promoting it. The final
  blue bodies each have one closed component and no strict zero-area faces.
  This is an auxiliary mesh observation, not manufacturing or force approval.
- Nominal reconstruction changes blue external samples by up to 1.3725 microns.
  Record actual 3D rim changes separately from u/v identity at the new 0/2/4 mm
  bore sections. Do not claim all carrier vertices remain unchanged. Evaluate
  trimesh distances on mm-scaled copies to avoid its fixed dot-product epsilon
  obscuring pad-seat edge detail; return SI values and keep tolerances unchanged.
- The root-covered hole retains a nominal 4 mm bore space, followed by about
  3 mm of support to the unchanged pad-seat plane. Smooth model holes do not
  specify thread engagement or a custom screw length. The pad remains separate;
  material, joining and grip force are still unselected.
- Service sampling moves three parts against thirteen fixed parts, 39 pairs
  per offset, using derived vertices only. Positive-offset samples have no
  surface pairs in either candidate; zero-offset mount contacts remain recorded.
  Do not compare triangle counts across changed topology as penetration depth.
  Keep arm/video production paused until the hand configuration is resolved.

## Terminal-side black-sleeve grasp on 2026-09-14

- The user explicitly replaced metal-terminal-edge clamping with gripping the
  terminal-facing black covering. `analysis/hand_sleeve_clamp_v01.md` and
  H025/H050 implement that change. Do not restore the old metal-edge pads as
  the active contact surface. Retain the 40 mm setback, root cable pads,
  source hardware and four saved poses.
- The Y22-30 mm front band, 2 mm edge inset and 2 mm central pad thickness are
  initial comparison geometry, not accepted manufacturing conditions. The
  source black sleeve is illustrative, not measured heatshrink on an adopted
  Ampere part. Sleeve slip/roll and transmission of terminal torque remain
  unresolved; static surface matching does not establish secure holding.
- Reuse source outer facets and the common-frame primitive union with one set
  of bores. Separate the source annulus at its largest radial gap; equality to
  its maximum radius drops facets rounded at serialization. Blender helper
  imports require the script directory on sys.path. Retain both failure logs.
- The 22.6469 mm tool-band observation is the distance from the terminal axis
  to the projected hand surface, not a selected tool's clearance. Keep the
  two upper-edge reliefs unselected and arm/video production paused.

## Sleeve-grasp tool-space comparison on 2026-09-14

- The next user `ok` continued with the unchanged H025/H050 hand geometry.
  `analysis/hand_sleeve_tool_access_v01.md` compares KTC B3-10/B3-17 catalogue
  dimensions as maximum-diameter socket envelopes. These examples do not
  select a socket, motor tool, fastener size or DEPRAG module.
- The phi12 shaft, phi40/60 body, prior height bands and 0/25/50 mm vertical
  offsets are sensitivity comparisons, not actual equipment dimensions or
  approved strokes. The exact union of translated coaxial cylinder bands is
  an auxiliary surface observation with the saved hand pose held fixed.
  Do not call it a real fastening cycle or solid/continuous-motion acceptance.
- Near-pose socket-band radius is 22.646854 mm. The upper comparison band's
  radius is 28.5 mm, giving +8.5/-1.5 mm differences for phi40/60. These are
  projected radial differences, not 3D penetration depths or acceptance margins.
  Actual spindle/nose, cameras, the other hand/tool and the workpiece remain
  outside this measurement. Keep the hand-holding and two station tools as a
  comparison direction, and continue to pause arm trajectories and video.

## Published fastening-component dimensions on 2026-09-14

- The next continuation compares individual public DEPRAG dimensions in
  `analysis/hand_fastening_reference_v01.md`: MINIMAT-ED phi36 with lengths
  314/356 mm and magnetic shaft sockets 804133/804134, not adopted equipment.
  E6.3/F6.3 correspondence does not specify insertion depth or an assembled
  stack. Keep the seven lower heights explicit comparison parameters.
- DFM pages 5-7 supply nose length/stroke options but not the required closed
  and open nose/feed-port outlines. Do not scale those illustrations using
  one of the alternative lengths. Tool Changer's M8 nut record is for another
  configuration and must not replace DFM's M6 nut limit. No changer is adopted.
- The phi36 comparison at a 53.8 mm lower height has a +10.5 mm projected
  radial difference in the near hand pose. At 3.8 mm it is +4.646854 mm.
  Neither is the clearance of a complete tool. Preserve source hand geometry,
  hold-at-sleeve intent, 40 mm setback and paused arm/video work.

## Clockwise mechanism tilt on 2026-09-14

- The user explicitly requested about 15 degrees clockwise in the +X side
  view. `analysis/hand_clockwise_tilt_v01.md` records T025/T050, rotating the
  original black hardware and mounting plates around the mean mounting origin.
  Screen right is +Y and up is +Z; the signed world X rotation is -15 degrees.
- Near-pose front sleeve and root cable pad world geometry stays fixed. Rebuild
  the four simple carrier solids, keeping rail and pad seats in place, then
  union and bore once. Do not rotate the contact pads away from the black
  sleeve, restore metal-terminal clamping or re-Boolean the old detailed body.
- Original hardware meshes, colors and internal saved states stay intact;
  world poses change. Preserve clear as 25 mm world-Z above the rotated open
  sample. These four samples are not a continuous arm or loaded finger motion.
- The public phi36 component at the 53.8 mm lower comparison height changes
  its projected radial difference from +10.5 to +40.015 mm. At 3.8 mm it stays
  +4.647 mm, because the near contact location is preserved. Do not describe
  the upper result as the clearance of the complete tool or its fastening tip.
- Both relief values remain comparisons. Native readback and discrete surface
  observations are auxiliary; sleeve stability, mounting strength and the
  complete feed-nose outline remain unresolved. Keep arm/video work paused.

## User-selected working default on 2026-09-14

- The user then explicitly selected the 15-degree version as the default.
  For new sleeve/root holding-hand work, use
  `data/hand_working_default_v01.json` and
  `scripts/prepare_hand_working_default_v01.py`. The active working model is
  T050 in the near state, with four source states retained. This supersedes
  the default choice in old comparison-only configs (D30, D60, H025/H050).
- The selector verifies pinned mesh/native/GLB/observation identities and
  extracts T050 without remeshing or changing any object or saved transform.
  The active geometry keeps 40 mm setback, terminal-side black-sleeve grasp,
  root jacket support and clockwise 15 degrees in the supplied side view.
  T050's 0.5 mm relief is the working sample value, not manufacturing approval.
- Apply this default to the current cable-holding hand, not automatically to
  other target families or every station. Finger count for unrelated work,
  force/material, full fastening equipment and arm paths are not selected by
  this directive. The user selected a working default, not physical acceptance.
- The next tooling input is recorded in
  `analysis/hand_default_tooling_next_v01.md`. The official CAD route leads to
  myDEPRAG; the unauthenticated browser showed a login page on 2026-09-14.
  Do not present catalogue dimensions as a full open/closed nose envelope or
  claim authenticated CAD access. Keep the existing two-tool/continuous-hold
  comparison and the separate simultaneous-tightening requirement.

## Provisional hand architecture on 2026-09-14

- The user requested choosing stable-clamping configurations quickly and
  adjusting fingertip details later. Use `data/hand_provisional_spec_v01.json`
  and `analysis/hand_provisional_spec_v01.md` for the current role selection.
  These are executor-selected provisional configurations under that directive,
  not a record of measured stability or accepted manufacturing parameters.
- Opposed two-finger hands with target-specific replaceable tips are the
  working baseline. H01-H08 cover all F01-F10 families plus body, cover and
  external connector roles. Multiple pads on one finger do not create
  independently actuated G3/G4 fingers. No G3/G4 role is selected at this stage.
- H04 retains T050, 15 degrees, 40 mm and black-sleeve/root contact. This
  supersedes the F06 metal-edge contact in historical target v02. Two round
  contact bands do not geometrically prevent axial slip or axial rotation;
  sleeve-to-terminal motion and fastening loads remain unverified.
- Reuse the existing 2F mechanism where opening and force are appropriate.
  Wide body/cover transport needs a suitably sized hand; do not imply the
  2F-85 grasps the entire enclosure width. Do not apply its nominal force
  range or old 14 mm cable shape to every small wire.
- Detailed dimensions/material optimization may follow this provisional
  selection. Use it for static placement without treating it as completed arm
  trajectories or physical acceptance. Keep the known trapped-underlip issue,
  continuous hand retention, two-tool comparison and synchronous requirements.
  Old OP050/060/080 components are not adopted merely to populate this table.

## Static hand review and cell allocation on 2026-09-14

- After accepting the provisional hand architecture, the user requested cell
  configuration with single, dual or three arms as appropriate, explicitly
  allowing one-axis and two-axis robots. Do not default every cell to dual arms.
  Use `analysis/cell_robot_allocation_v01.md` as the next comparison input.
- Count independent holding roles, articulated arms, positioning axes and
  fastening spindles separately. XY positioning plus a tool Z feed is not a
  two-axis-only system. A third arm with one spindle does not provide the
  existing two-spindle simultaneous fastening requirement.
- Keep A mechanical assembly, B power connections and C auxiliary/control
  connections as the current three-station comparison. B/C complete their
  assigned joints while held; do not revert to unfastened B-to-C transfer.
  Initial cell candidates are not selected machines or physical acceptance.
- `hand_placement_review_v01` provides thirteen target views with eight
  scale-free schematics, unchanged public-photo regions and the saved T050
  model. Unlocated parts have no photo rectangle. Drawn contacts, holes and
  tool directions are not actual manufacturing dimensions or collision checks.
- The separate T050 page preserves all real meshes and four saved transforms,
  hiding the old guide cylinder. It adds no full tool envelope or interpolated
  arm motion. This step does not update line native files or produce a video.

## Video restart and OP010 selection on 2026-09-14

- The user explicitly resumed video production to adjust fingers while watching
  motion. This supersedes the earlier video/arm-motion pause for the new review.
  Include revised OP010, OP020 and the three OP030 station roles.
- OP010 needs stock capacity for 20 housings. After first requesting a single
  articulated arm, the user explicitly selected XYZ Cartesian handling instead.
  Use a three-axis Cartesian robot and the provisional H06 opposed two-finger
  hand; the initial two-axis and single-articulated-arm alternatives are historical.
- The adopted public product drawing gives 292.10 x 160.00 x 92.29 mm including
  mounting flanges, with connector projections additional. These are different
  from the old v06 housing envelope. The measured input PDF SHA remains
  643648bcea77b4d7c37c65d073664f746f68689952da2d5ce932e3d10bd5a9e1.
- Keep unpublished internal dimensions and machine parameters identified as
  initial review geometry. Do not claim that endpoint-driven cable deformation,
  loaded grasp stability, manufacturing fit or real takt has been established.
  Preserve the current hold-through-fastening and two-tool comparison.
- Continue producing only the process review MP4 directly from process PNGs.
  New line files must have new names; the pinned v06 and T050 source files stay
  unchanged. Geometric observations and native readback remain auxiliary.

## OP020 connector correction on 2026-09-15

- The user rejected the box-shaped connector surrogate and explicitly selected
  installation and screw fastening of the enclosure-side outer headers for OP020.
  Do not keep the previous push-cylinder/plug-mating operation for this step.
- Match the Ampere public A/D/E + D/F key layout using TE's public 2103340-1 and
  2103346-2 outer-header STEP geometry. Their flange fastener counts are eight
  and six M4 screws. Inner contact housings and external cable plugs are separate
  parts and operations; an empty outer header is not a completed electrical port.
- Use one holding arm and a station-mounted XYZ screwdriving unit as the initial
  motion-review implementation. Keep holding through all fasteners. The dedicated
  flange-side tips are shared between the two sizes with different jaw commands.
- Record the 60 mm outward hardware shift and initial tip/carrier details as H05
  review geometry. They do not replace the cable T050 40 mm/15-degree selection.
- The main HV two-pole metal flange and white caps are a photo-based outline;
  their exact Amphenol part number and dimensions remain unresolved. OP030-C's
  control connector is still a representative model, not a matched actual part.
- Preserve v02 and v06 native files. Continue rendering one process-review movie
  directly from PNGs. Model and sampled geometric checks are not physical acceptance.

## Photo-to-product reconstruction on 2026-09-15

- The user rejected treating v03's provisional interior as a faithful Ampere
  reproduction. First map the supplied interior photograph's parts and connections
  individually to model IDs, correct the product, and only then develop motions.
- Use DSC02860-1.jpg as the assembled-product visual reference, together with
  the two other official photographs and the public V1.1 circuit/pinout. Record
  visible features separately from electrical functions and purchasing parts.
- Do not retain the arbitrary orange control block, sample S cable, two sample
  terminal stands, or generic fuse/relay placements as matched actual components.
- Keep unlocated but documented parts and occluded connections in the inventory.
  A functional circuit edge is not a physical wire, and a visible wire segment
  is not proof of both endpoints. Do not infer a complete manufacturing BOM,
  fuse-to-photo assignment, HVIL order, or hidden joints from colors alone.
- Static photo reconstruction may record estimated display dimensions and
  unresolved identities. Such estimates must not silently become hand targets,
  selected part numbers, complete electrical assembly, or accepted motions.
- Keep v03 and earlier files intact. Do not make a new process movie until the
  relevant product interfaces and operations have been reconciled.

## External preassembly correction on 2026-09-16

- The user confirmed the correction that Ampere's official 2025 assembly video
  shows substantial external preassembly followed by enclosure installation and
  further connector/busbar work. Use `analysis/hvjb_preassembly_process_v01.md`
  and its correspondence JSON to distinguish these phases before motion.
- External baseplate assembly A, fuse-panel assembly B and enclosure integration C
  are a new comparison, not an adopted three-cell layout or robot count. Their
  flow converges; do not treat it as the old mechanical/power/auxiliary serial split.
- Keep OP010 XYZ plus 20 housings and OP020 header installation/screw fastening.
  In the comparison, header work occurs after internal-unit installation at C.
  A separate OP020 would need sequence reconciliation; do not install it twice.
- The current photo model's P01 case floor is not a separately identified carrier
  plate. Do not animate that floor as a removable assembly plate. Reconcile the
  actual plate, supports, grasp surfaces and its joint with the fuse panel first.
- Visible free leads during manual unit insertion do not define automatic handoff.
  Keep unit support and free-end guidance explicit, without reinstating the upper
  retainer, abandoning hand retention, or declaring a single arm sufficient.
- Retain all required functions and unknown endpoints. The 92 registered photo
  features do not constitute a complete BOM or 92 assembly operations. The 2025
  build and the target 2022 photographs remain separate manufacturing revisions
  unless their equivalence is established. Preserve the existing native files.

## Plate and free-end sequence follow-up on 2026-09-16

- Use `analysis/hvjb_preassembly_process_v02.md` for the updated observations.
  The 146-second source frame shows the baseplate side and fuse panel being
  carried together into the case. The mechanical joint itself is unobserved;
  do not turn co-carrying into a rigidity or fastening-completion claim.
- The inner housings are above the edge at 154 seconds and outside through the
  side openings at 170 seconds, while the outer headers remain on the bench.
  Keep this routing step before outer-header installation in the comparison.
- `V25_BASE_PLATE` is separate from P01 in the video observation ledger. V25
  entities are not additions to the target 2022 photo BOM. No confirmed mapping,
  dimensions, manufacturing contour, fastening points or grasp surfaces exist.
- The tool enters the case after insertion, but its work point is obscured.
  Do not invent carrier screws or their torque from this view. Free lead groups
  are not wire counts or robot-arm counts; retain the unresolved handoff roles.

## Header aperture correction on 2026-09-16

- `analysis/hvjb_header_interface_v01.md` corrects the old all-22.8 mm wall
  openings. TE 2103340 A2 specifies 23.0/22.8/23.0 mm for the three bays;
  2103346 A3 specifies 22.8/23.0 mm for the two bays. The new static native
  `UR15_JB_photo_correspondence_v03_p03.blend` changes those three widths only.
  Preserve p02, the 92-feature catalog, and the unresolved physical connections.
- The bare inner-housing CAD projects to about 22.4 x 12.6 mm, with full length
  42.6 mm; the drawing's reference 32.4 mm is not its full length. Nominal
  projected distances of 0.2/0.3 mm exclude wires, fingers, tolerances and actual
  passage. They do not establish a grasp envelope, clearance or physical fit.
- TE's installation sequence and Ampere's video state sequence remain separate.
  The 168-second frame shows inner housings outside the case before outer-header
  installation; inner locking versus flange-fastening suborder is unresolved.
  Neither the plate joint nor a new ST/arm allocation is selected in this step.

## Plate-joint evidence boundary on 2026-09-16

- `analysis/hvjb_join_followup_v01.md` records the 87.0/87.2-second video cut:
  separate plates appear together after the cut, but the joining operation is
  unobserved. The sampling interval is not assembly time or a cycle estimate.
- The additional 2022 official photo DSC02861-1.jpg has two unresolved visible
  attachment features near P07. Keep them as observations, not identified case
  screws, new BOM quantities, or the target of the obscured tool at 158 seconds.
  Plate joints, case fastening points and automated grasp surfaces remain open.
- The p03 static native, prior catalog and process v02 are preserved. The new
  join review is source evidence, not another model or process-video revision.

## Provisional unitization procedure adopted on 2026-09-16

- The user explicitly accepted the five-step procedure for now: locate the
  baseplate unit; align the fuse-panel side; retain the relative pose while
  screw-fastening; guide free ends out of the insertion path; insert the combined
  unit into the case. Use `analysis/hvjb_unitization_procedure_v01.md` and process
  v03. Do not revert this procedure to unselected merely because its factory
  counterpart is unobserved.
- This selects a working procedure, not the factual Ampere joint geometry.
  Direct versus bracket/standoff attachment, screw locations/count/specification,
  torque, grasp surfaces, station layout and robot count remain unresolved.
  Preserve source observations and prior natives. Case fastening and remaining
  connections follow insertion; do not treat unitization as a completed product.

## Unitization support-role comparison on 2026-09-16

- `analysis/hvjb_unitization_roles_v01.md` and its data record compare a fixed
  baseplate nest, panel-holding hand, and station-mounted fastening tool.
  Nine diagram states refine the five adopted steps; robot counts, contact
  surfaces, joint geometry and release-detection conditions remain unselected.
- Regripping is on the nest after fastening and tool withdrawal. This candidate
  requires the completed panel-to-base joint to carry its load; no transient
  bolt torque or unverified hand release is authorized by the diagram.
- Whole-unit transport and free-end guidance remain distinct roles. Check the
  receiver and finger-opening path before showing release inside the case.
  Do not add lifting tabs, trap fingers under the baseplate, or use cables or
  contactor bodies as a demonstrated lifting interface. The page is scale-free;
  its role coverage check is bookkeeping, not physical support validation.

## Task allocation and robot consolidation goal on 2026-09-16

- The user explicitly set the goal: decompose work, assign robot roles, then
  consolidate onto a small number of robots. Use
  `analysis/cell_robot_allocation_v02.md` and
  `data/hvjb_robot_allocation_v01.json` for the current allocation comparison.
  The process v03's old A tool-arm-first wording is historical for allocation;
  compare the stationary tool/positioning-axis route before adding a tool arm.
- R-A/B/C are initial primary-role slots, not a selected final count. X-A/B/C
  reserve conditional independent holding roles, not three purchased robots.
  Allocate concurrent jobs first, then combine sequential jobs and compare
  sharing across cells. Do not replace an unresolved role with zero equipment.
- Holding dwell, tool waits, final handoff, release, travel and hand changes
  occupy the resource too. Keep the free-end guide reserved until its handoff;
  do not free it automatically after enclosure insertion. Preserve the three-ST
  parallel-work intent and conditional two-spindle simultaneous fastening.
- Count Cartesian robots, external axes, spindles, feeders, changers, fixtures,
  supported buffers, inspection, replenishment and recovery separately. Source
  video timestamps are not durations. Minimum robot count, cadence and physical
  feasibility remain unmeasured; role-reference checks do not establish them.

## Task occupancy comparison on 2026-09-16

- `analysis/hvjb_task_occupancy_v01.md` and its workcards expand the 20 assigned
  jobs into target-review destinations and holding intervals. The 92 feature
  rows are traceability, not a full BOM or selected assembly operations. A
  fastener's photo parent does not determine its joint stack or fixing function.
- Keep the two documented header hole groups (P16 eight, P17 six M4 holes)
  separate from the 23 interior fastener features. Compare continuous holding
  for each header and sequential reuse of R-C/T-C; fastening order, duration,
  complete tool outlines and conditions remain unset.
- Inner-housing retention and outer-header pickup cannot occupy the same
  single hand at once. Keep the independent support/handoff role unresolved
  until its geometry and sequence are specified. X-C does not become available
  just because insertion or opening passage ended. Workcard completion phrases
  are planning boundaries, not sensor thresholds or release authorization.

## Auxiliary-role sharing comparison on 2026-09-16

- `analysis/hvjb_robot_sharing_v01.md` compares all five partitions of X-A/B/C
  with three separate primary roles. S4 (one shared assistant) and S5_AB
  (A/B shared, C separate) are priorities for comparison, not selected machines.
- Four to six arm slots count this limited role mapping, not robot bases,
  line-wide equipment or proven minimum arms. One auxiliary role may need more
  than one real actuator; its physical support scope is still unresolved.
- The eight auxiliary-demand subsets assume all three primary roles occupied
  in that illustrative instant. The forty plan/subset pairs check duplicate
  resource IDs only. They are not observed timing, occurrence probabilities,
  scheduling feasibility, reach checks or physical acceptance.
- Keep all twenty tasks and other equipment roles. Resolve holds and handoffs,
  then include hand changes and cell travel before reassigning a shared arm.
  Waiting must preserve support before grasp starts; do not interrupt a hold.
  Leave unmeasured worksheet time fields empty, not zero. No task uses source
  video timestamps as measured durations.

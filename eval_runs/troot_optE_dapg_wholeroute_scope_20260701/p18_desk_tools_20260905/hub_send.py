#!/usr/bin/env python3
# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Hub-only send / verify / resend tool for the pane w2:p18 (T-ROOT-OPS-SUPERVISOR).

Design of record: eval_runs/troot_optE_dapg_wholeroute_scope_20260701/P18_D1_VERIFY_CYCLE2_20260905.md Part 2
(PROPOSE v3, increment 1'). Authorized by Rs1 (the human): files = transcript line 39366; build = line 40230.
Post-build fixes (2026-09-06, 層2/層5 cycle 1): CONTROLS_20260906.md in this directory lists them with the rows.

Procedure (send):
- Guard = a pane bind, not a two-factor bind: HERDR_PANE_ID must be w2:p18 and CLAUDE_CODE_SESSION_ID must equal
  the live w2:p18 agent session. Subagents and background jobs of the hub inherit both (measured 2026-09-05) and
  cannot be excluded by the environment: they run this tool only as HUB_SEND_READONLY=1 ... --dry_run (nothing
  is sent, pressed or written in that mode). Every row records hub_session_id and child_session.
- Roster = non-comment lines of scripts/validations/nest_role_labels.txt read at run time, minus RETIRED.
  Resolution = `herdr agent list`, w2 agents only, name "w2:pN ROLE" -> exact match -> exactly one live agent.
  An agent whose `agent` kind is not claude is refused (refused(agent_type_not_banked)): no delivery table is
  banked for other kinds (the node's codex exclusion), so the tool does not send to them (fail-closed; stricter
  than the spec's UNKNOWN(table-not-banked)).
  --to_pane skips role resolution for the primary member: the pane must be a live w2 agent with a live label in
  the roster (--control lifts the roster check); the head carries that label (row fields resolved_by = "pane",
  to_requested = the typed --to); a --to that itself resolves uniquely to another pane is refused
  (refused(contradiction)); retired labels, unlabelled panes and the hub's own pane are refused.
  HUB_SEND_REPO (env) redirects the repo root (roster file and init's git leg) for simulations from a copied
  directory; unset in normal use.
- Order: resolve every member -> read every member -> decide every member -> only then allocate the id, compose the
  text once (head line + body + footer), write bodies/m-p18-N.txt, send the identical bytes to each member.
  --id completes a held fan-out: the bytes are read back from bodies/m-p18-N.txt (never re-composed), the members
  must belong to the recorded fan-out, and a --body_file whose body differs from the stored body is refused.
  Only members never handed to `herdr agent send` (a pre-send held row, or HELD(fanout_stopped)) are sent; every
  other member is skipped with skipped(<state>) before any read, so one id never reaches a queue twice.
- Pre-send decision (fail-closed): HELD when agent_status is not idle/done/working; when a herdr dialog marker is
  anywhere in the viewport (over-HELD by design, never under-HELD); when there is no composer line (prompt glyph +
  U+00A0) or more than one; when the composer shows a folded paste; when the composer holds any non-dim text
  (a draft, or one of our own non-final messages); when the destination is working and --queue was not given.
  Dim text (SGR 2 = a UI suggestion) and the queue hint "Press up to edit queued messages" are not drafts.
  A folded paste hides its identity: our own un-pressed text in a composer reads as HELD(paste_in_composer), not
  as composer_holds_own_message (that state needs an unfolded head line); correlate through the pane's held rows.
  Nothing is ever sent before the whole fan-out has been decided.
- Post-send gate: after `herdr agent send` the composer is re-read (up to 6 x 0.25 s). The keypress is pressed only
  when the composer line starts with the head line, or is exactly one folded-paste marker "[Pasted text #N +K lines]"
  whose K+1 equals the line count of the sent text (Claude Code folds a multi-line paste; measured 2026-09-06 on
  m-p18-323, n=1; the marker text is stored in the row as landed_as). A foreign paste of the same line count
  arriving between the pre-send read and the post-send read is the documented residual; a fold whose count
  differs from ours holds as HELD(paste_count_mismatch). Before the keypress the agent status is re-read (one
  `agent list`, ~0.35 s; a flip inside the last ~0.8 s is invisible); a working<->idle flip, or a status outside
  idle/done/working, holds (HELD(status_changed)) instead of pressing. Return codes of `agent send` and
  `send-keys` are stored (send_rc, keypress_rc); a refused keypress holds (HELD(keypress_refused)) with via none.
  A post-send HELD stops the fan-out: members not yet sent get HELD(fanout_stopped) rows. Any exception after the
  text was placed still appends the row it has built (HELD(error:...) before the keypress, UNKNOWN(error:...)
  after) before propagating.
- Observation: the state of a row comes from the destination transcript, never from the keypress.
  P1 DELIVERED = a user record (string content, promptSource typed|queued, no toolUseResult, not a compaction
  summary, not a local-command echo) containing the sent bytes (evidence user@<byte offset>+<k>, k = character
  index into the decoded content); position > 0 = DELIVERED(fused) when the prefix
  holds other hub heads, DELIVERED(fused_with_unknown_prefix) otherwise (the prefix's first 200 chars are printed,
  never stored). DELIVERED at position 0 may still share its record with later hub messages: fused_with says so.
  Q1 QUEUED(observed) = an enqueue record with the sent bytes, or the queued marker in the viewport.
  Q2 ABSORBED(unacked) = a remove/popAll record followed by a queued_command attachment with the sent bytes
  (the reason field is absent in ~98% of removes: 2600 of 2634 counted 2026-09-05, 2561 of 2603 on 2026-09-06
  over the 28 project transcripts; it is an annotation, not the key). The row keeps absorbed_at = the remove
  record's timestamp (the attachment carries the enqueue time). Non-terminal. A1 DELIVERED(absorbed,acked) =
  after Q2, an assistant record (text or thinking) naming the bare id. Q3 DELIVERED(turn_end) = the P1 shape
  with promptSource queued. Q4 REMOVED = a remove with no following
  attachment or user record. Unknown queue operations on our bytes surface as UNKNOWN(unmapped_op).
  The tool never writes LOST. A DELIVERED verify row after a send row with via "none" means the keypress came
  from outside the tool (the documented operator recovery: read the composer, press Enter once, verify --id);
  origin.kind of the record is "human" even when the tool pressed the key, so it never discriminates. verify
  keeps a HELD state unless it observes something (never HELD -> UNKNOWN(no-record)), skips never-sent
  HELD(fanout_stopped) rows, and computes overdue only for rows with a keypress.
  P1's string-content / no-toolUseResult rule comes from the two false by-hand verdicts of 2026-09-05
  (m-p18-290@w2:p0, m-p18-291@w2:pZ; by_hand_20260905/verify_*.txt), which were tool_result records.
- Measured semantics (2026-09-05, one leg of each n=2 pair has no banked keypress stamp): record 18-23 ms after
  Enter (n=2; the tool's own m-p18-324 on 2026-09-06 = 40 ms, n=3); Enter->working 0.29/0.41 s (n=2);
  Tab->enqueue 4.6-314 s (n=10, 1/10 within 6 s); enqueue->remove 5.9-72.1 s (n=9; the queued_command attachment
  carries the enqueue time); Tab->terminal record (remove for absorbed, user record otherwise) 30.7-517.5 s
  (n=15, median 103 s); viewport 66-80 lines; composer line = U+276F U+00A0, echoes = U+276F U+0020.
- Rows: body_sha256 of a tool row = sha256 of the sent bytes (the file holds them plus one final newline); the
  imported by-hand rows in by_hand_20260905/sent.jsonl keep their sha over the file. DELIVERED rows carry the byte
  offset and the transcript line of the record.
- verify re-reads every non-final row from its stored byte offset (a mid-line offset is resynchronised to the
  next newline); rows without a body file are refused, never scanned. --dry_run (after the subcommand) and
  HUB_SEND_READONLY=1 read and print, write nothing, send nothing.
- resend --id re-sends the same body bytes with an appended "resend of <id> <date>" line as a new row of
  row_type resend (field resend_of); rows of the hub's own control sends are not resent.
- init computes bodies/.floor once by a closed query over the delivered heads of every project transcript, the
  head-shaped tokens of the repo (tracked and untracked, any position) and the id-shaped files of the retired
  by-hand directories (ids_retired_*, desk_msgs_retired_*) of the hub's own session scratchpad — the hub's
  subagents write into that scratchpad, so fixtures elsewhere in it are not counted; it refuses to write while
  .floor exists (a dry run still prints the query's result beside the live floor) or while the by-hand
  directories (ids, desk_msgs) exist un-renamed.
- Operating rule: the row, body file and .floor of a send are committed (pathspec) in the same turn as the send;
  a message body cites only artifacts that exist at send time, with full shas or none.
- Provenance: append_row's flock + loop-write + fsync core is copied from the untracked
  scripts/verification_log_append.py:235-261 (sha256 30509c34b026f18a1a9eb3db44e786f989144d5f9042797b82d680cc75628f4c,
  2026-09-06); the 層4 guard scripts/check_thread_vault_prior_art.sh is untracked too
  (sha256 b8d85cdb99ab66737ee130e5d9624e4eee06ebef98b144ed97a2bcc3e40a5e48, 2026-09-06).
Deviations from v3 section 3-D and from the node DoD are listed in the design of record (section 7) and in
CONTROLS_20260906.md (size, the unmeasured draft half of control (h), the agent-type leg of T/C).
"""

from __future__ import annotations

import argparse
import datetime as _dt
import fcntl
import glob
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

HUB_PANE = "w2:p18"
HUB_ROLE = "OPS-SUPERVISOR"
RETIRED = {"COORD", "COORD2", "VT-DESIGN", "OPS-SUPERVISOR-CODEX"}
DIR = Path(__file__).resolve().parent
BODIES = DIR / "bodies"
FLOOR = BODIES / ".floor"
RECORDS = DIR / "sent_records.jsonl"
REPO = Path(os.environ.get("HUB_SEND_REPO") or DIR.parents[2])
LABELS = REPO / "scripts" / "validations" / "nest_role_labels.txt"
PROJECTS = Path.home() / ".claude" / "projects"
SCRATCH_GLOB = "/tmp/claude-1000/-home-rlrk-IsaacLab/*/scratchpad"
SCRATCH_OWN = "/tmp/claude-1000/-home-rlrk-IsaacLab/" + os.environ.get("CLAUDE_CODE_SESSION_ID", "-") + "/scratchpad"
PROMPT = "\u276f\u00a0"  # composer prompt = glyph + NO-BREAK SPACE; echo lines use U+0020 (measured 2026-09-05)
DIALOG_MARKERS = (
    "do you want to proceed?",
    "esc to cancel",
    "enter to select",
    "waiting for permission",
    "do you want to allow this connection?",
    "select model",
    "showing detailed transcript",
    "run a dynamic workflow?",
)
QUEUE_HINT = "press up to edit queued messages"
QUEUED_MARKERS = (QUEUE_HINT, "queued message")
EXCLUDED_PREFIXES = ("<local-command-", "<command-name>", "<task-notification>")
ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")
FLOOR_RE = re.compile(r"^MSG m-p18-(\d+) /", re.MULTILINE)
FLOOR_JSON_RE = re.compile(r'"content":"MSG m-p18-(\d+) /')
HEAD_RE = re.compile(r"MSG (m-p18-\d+) /")
PASTE_RE = re.compile(r"\[pasted text #\d+(?: \+(\d+) lines?)?\]")
FOOTER_RE = re.compile(r"^\d{4}-\d\d-\d\d \d\d:\d\d:\d\d JST \(hub_send\.py\)$")
RESEND_LINE_RE = re.compile(r"^resend of m-p18-\d+ \d{4}-\d\d-\d\d \d\d:\d\d:\d\d JST$")
ID_FILE_RE = re.compile(r"^(?:body_)?m-p18-(\d+)(?:\.txt)?$")
FINAL_STATES = ("DELIVERED", "refused")
READONLY = os.environ.get("HUB_SEND_READONLY") == "1"


def jst_now() -> str:
    return _dt.datetime.now().astimezone().isoformat(timespec="milliseconds")


def run_rc(argv: list[str]) -> tuple[str, int]:
    """Run a command without a shell; return (decoded stdout, return code)."""
    out = subprocess.run(argv, capture_output=True, check=False)
    return out.stdout.decode("utf-8", errors="replace"), out.returncode


def run(argv: list[str]) -> str:
    return run_rc(argv)[0]


def herdr_json(argv: list[str]) -> dict | None:
    try:
        return json.loads(run(["herdr", *argv]))
    except (json.JSONDecodeError, ValueError):
        return None


def agent_list() -> list[dict]:
    doc = herdr_json(["agent", "list"])
    if not doc:
        raise SystemExit("refused: herdr agent list did not return JSON")
    return [a for a in doc["result"]["agents"] if str(a.get("pane_id", "")).startswith("w2:")]


def guard(agents: list[dict]) -> str:
    hub = [a for a in agents if a.get("pane_id") == HUB_PANE]
    live = hub[0]["agent_session"]["value"] if hub else ""
    if os.environ.get("HERDR_PANE_ID") != HUB_PANE or os.environ.get("CLAUDE_CODE_SESSION_ID") != live:
        raise SystemExit("refused(not_hub): this tool runs only inside the w2:p18 session")
    return live


def roster() -> set[str]:
    names = {
        ln.strip() for ln in LABELS.read_text(encoding="utf-8").splitlines() if ln.strip() and not ln.startswith("#")
    }
    return names - RETIRED


def live_label(agent: dict) -> str:
    name = str(agent.get("name", ""))
    label = name.split(" ", 1)[1] if " " in name else ""
    return label[len("T-ROOT-") :] if label.startswith("T-ROOT-") else label


def check_kind(a: dict) -> dict:
    kind = a.get("agent")
    if kind not in (None, "claude"):
        raise SystemExit(f"refused(agent_type_not_banked: {kind}): {a.get('pane_id')} has no banked delivery table")
    return a


def resolve(role: str, agents: list[dict], control: bool) -> dict:
    if role in RETIRED:
        raise SystemExit(f"refused(retired): {role}")
    if role == HUB_ROLE and not control:
        raise SystemExit("refused(self): use --control for the hub's own pane")
    if role not in roster() and role != HUB_ROLE:
        raise SystemExit(f"refused(unregistered): {role}")
    hits = [a for a in agents if live_label(a) == role]
    if len(hits) != 1:
        raise SystemExit(
            f"refused({'unresolved' if not hits else 'ambiguous'}): {role} -> {[h['pane_id'] for h in hits]}"
        )
    return check_kind(hits[0])


def resolve_pane(pane: str, to: str, agents: list[dict], control: bool) -> tuple[str, dict]:
    """The --to_pane escape: a live, labelled w2 agent by pane id; the role is its live label."""
    forced = [a for a in agents if a.get("pane_id") == pane]
    if not forced:
        raise SystemExit(f"refused(unresolved): {pane} is not a live w2 agent")
    label = live_label(forced[0])
    if not label:
        raise SystemExit(f"refused(unlabelled_pane): {pane} has no live label")
    if label in RETIRED:
        raise SystemExit(f"refused(retired): {pane} carries the retired label {label}")
    if pane == HUB_PANE and not control:
        raise SystemExit("refused(self): use --control for the hub's own pane")
    if label not in roster() and label != HUB_ROLE and not control:
        raise SystemExit(f"refused(unregistered_label): {pane} carries {label}, not in the roster")
    elsewhere = [a["pane_id"] for a in agents if live_label(a) == to and a.get("pane_id") != pane]
    if to != label and len(elsewhere) == 1:
        raise SystemExit(f"refused(contradiction): --to {to} resolves to {elsewhere[0]}, not {pane}")
    return label, check_kind(forced[0])


def read_view(pane: str) -> dict:
    doc = herdr_json(["agent", "read", pane, "--source", "recent-unwrapped", "--format", "ansi"])
    if not doc or "result" not in doc or "read" not in doc["result"] or "text" not in doc["result"]["read"]:
        return {"error": "read_failed"}
    rd = doc["result"]["read"]
    raw_lines = rd["text"].split("\n")
    plain = [ANSI_RE.sub("", ln).rstrip("\r") for ln in raw_lines]
    composer_idx = [i for i, ln in enumerate(plain) if ln.startswith(PROMPT)]
    view = {"truncated": bool(rd.get("truncated")), "plain": plain, "raw": raw_lines, "composer_idx": composer_idx}
    if len(composer_idx) == 1:
        i = composer_idx[0]
        view["composer_plain"] = plain[i][len(PROMPT) :].strip()
        view["composer_raw"] = raw_lines[i]
        view["composer_dim_only"] = dim_only(raw_lines[i])
    return view


def dim_only(raw_line: str) -> bool:
    """True when every visible character after the prompt lies inside an SGR-2 (dim) run.

    SGR parameters are parsed as a list: ``2`` alone means dim, ``0``/``22`` clear it; the extended colour forms
    ``38;5;n``, ``48;5;n``, ``38;2;r;g;b`` and ``48;2;r;g;b`` consume their arguments so that a colour whose
    argument happens to be 2 is never read as dim.
    """
    body = raw_line.split(PROMPT, 1)[1] if PROMPT in raw_line else raw_line
    dim, seen = False, False
    for tok in re.split(r"(\x1b\[[0-9;?]*[A-Za-z])", body):
        if tok.startswith("\x1b["):
            if not tok.endswith("m"):
                continue
            params = [q for q in tok[2:-1].split(";")]
            if params == [""]:
                dim = False
                continue
            k = 0
            while k < len(params):
                q = params[k]
                if q in ("38", "48", "58") and k + 1 < len(params):
                    k += 3 if params[k + 1] == "5" else (5 if params[k + 1] == "2" else 1)
                    continue
                if q == "2":
                    dim = True
                elif q in ("0", "22", ""):
                    dim = False
                k += 1
            continue
        for ch in tok:
            if ch.isspace() or ch == "\r":
                continue
            seen = True
            if not dim:
                return False
    return seen


def decide(status: str, view: dict, queue: bool, own_heads: dict[str, str]) -> tuple[str, dict]:
    """Return (reason, facts); reason == '' means send is allowed."""
    facts = {"status": status, "composer_before_kind": "empty", "composer_before_sha256": ""}
    if "error" in view:
        return "HELD(read_failed)", facts
    if view["truncated"]:
        return "HELD(viewport_truncated)", facts
    if status not in ("idle", "done", "working"):
        return f"HELD(status={status})", facts
    whole = "\n".join(view["plain"]).lower()
    for mk in DIALOG_MARKERS:
        if mk in whole:
            return f"HELD(dialog:{mk})", facts
    if len(view["composer_idx"]) != 1:
        return "HELD(no_composer)" if not view["composer_idx"] else "HELD(ambiguous_composer)", facts
    comp = view["composer_plain"]
    if comp:
        facts["composer_before_sha256"] = hashlib.sha256(comp.encode()).hexdigest()
        if "[pasted text" in comp.lower():
            facts["composer_before_kind"] = "paste"
            return "HELD(paste_in_composer)", facts
        if comp.lower() == QUEUE_HINT:
            facts["composer_before_kind"] = "queue_hint"
        elif view["composer_dim_only"]:
            facts["composer_before_kind"] = "ghost"
        else:
            for mid, head in own_heads.items():
                if head and comp.startswith(head):
                    facts["composer_before_kind"] = "own_message"
                    return f"HELD(composer_holds_own_message id={mid})", facts
            facts["composer_before_kind"] = "draft"
            return "HELD(draft)", facts
    if status == "working" and not queue:
        return "HELD(working)", facts
    return "", facts


def transcript_path(agent: dict) -> Path:
    proj = str(agent.get("cwd", "/home/rlrk/IsaacLab")).replace("/", "-")
    return PROJECTS / proj / f"{agent['agent_session']['value']}.jsonl"


def line_of(path: Path, offset: int) -> int:
    """1-based line number of the record that starts at byte offset."""
    n, remaining = 1, offset
    with open(path, "rb") as fh:
        while remaining > 0:
            chunk = fh.read(min(1 << 20, remaining))
            if not chunk:
                break
            n += chunk.count(b"\n")
            remaining -= len(chunk)
    return n


def append_row(row: dict) -> None:
    """Atomic append with flock + loop-write + fsync (core from scripts/verification_log_append.py:235-261)."""
    if READONLY:
        print("dry_run row:", json.dumps(row, ensure_ascii=False))
        return
    payload = (json.dumps(row, ensure_ascii=False) + "\n").encode("utf-8")
    fd = os.open(str(RECORDS), os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        try:
            view = memoryview(payload)
            off = 0
            while off < len(view):
                n = os.write(fd, view[off:])
                if n == 0:
                    raise OSError("short write")
                off += n
            os.fsync(fd)
        finally:
            fcntl.flock(fd, fcntl.LOCK_UN)
    finally:
        os.close(fd)


def load_rows() -> list[dict]:
    if not RECORDS.exists():
        return []
    rows = []
    for ln in RECORDS.read_text(encoding="utf-8").splitlines():
        try:
            rows.append(json.loads(ln))
        except json.JSONDecodeError:
            continue
    return rows


def latest_states(rows: list[dict]) -> dict[tuple[str, str], dict]:
    latest: dict[tuple[str, str], dict] = {}
    for r in rows:
        if r.get("row_type") in ("send", "resend", "verify", "held"):
            latest[(r["id"], r.get("pane", ""))] = r
    return latest


def alloc_id() -> str:
    if not FLOOR.exists():
        raise SystemExit("refused(no_floor): run `hub_send.py init` first")
    n = int(FLOOR.read_text().strip()) + 1
    BODIES.mkdir(exist_ok=True)
    while True:
        try:
            fd = os.open(str(BODIES / f"m-p18-{n}.txt"), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
            os.close(fd)
            FLOOR.write_text(f"{n}\n")
            return f"m-p18-{n}"
        except FileExistsError:
            n += 1


def compose(mid: str, members: list[tuple[str, dict]], body: str, resend_of: str | None) -> str:
    head = f"MSG {mid} / {HUB_PANE} / {HUB_ROLE} → {members[0][1]['pane_id']} {members[0][0]}"
    if len(members) > 1:
        head += "（cc " + ", ".join(f"{a['pane_id']} {r}" for r, a in members[1:]) + "）"
    lines = [ln.rstrip() for ln in body.rstrip("\n").split("\n")]
    text = (
        head + "\n" + "\n".join(lines) + "\n" + _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S JST") + " (hub_send.py)"
    )
    if resend_of:
        text += "\nresend of " + resend_of + " " + _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S JST")
    return text


def strip_body(text: str) -> str:
    """The body of a composed text: drop the head line and every trailing footer / resend line."""
    lines = text.rstrip("\n").split("\n")[1:]
    if lines and RESEND_LINE_RE.match(lines[-1]):
        lines.pop()
    if lines and FOOTER_RE.match(lines[-1]):
        lines.pop()
    return "\n".join(lines)


def norm_body(body: str) -> str:
    return "\n".join(ln.rstrip() for ln in body.rstrip("\n").split("\n"))


def paste_marker_lines(comp: str) -> int:
    """Line count a composer that is exactly one folded-paste marker stands for (``+K lines`` = K+1); else 0."""
    m = PASTE_RE.fullmatch(comp.strip().lower())
    if not m:
        return 0
    return int(m.group(1) or 0) + 1


def scan(path: Path, offset: int, sent: str, head: str, mid: str) -> dict:
    """Read the destination transcript from offset and classify (P1, Q1-Q4, A1). Refuses an empty needle."""
    if not sent or len(sent) < len(head):
        raise ValueError("refused(no_body): scan needs the sent bytes")
    res = {"state": "UNKNOWN(no-record)", "evidence": "", "fused_with": [], "head_found": False}
    if not path.exists():
        res["state"] = "UNKNOWN(no-transcript)"
        return res
    with open(path, "rb") as fh:
        fh.seek(offset)
        if offset > 0:
            fh.seek(offset - 1)
            if fh.read(1) != b"\n":
                fh.readline()
        pos = fh.tell()
        absorbed_at, queue_seen, removed_ts = None, False, ""
        for raw in fh:
            line_off = pos
            pos += len(raw)
            try:
                d = json.loads(raw.decode("utf-8", errors="replace"))
            except json.JSONDecodeError:
                continue
            if not isinstance(d, dict):
                continue
            t = d.get("type")
            if t == "queue-operation":
                op = d.get("operation")
                content = str(d.get("content", ""))
                if sent not in content:
                    continue
                if op == "enqueue":
                    res.update(state="QUEUED(observed)", evidence=f"enqueue@{line_off}")
                elif op in ("remove", "popAll"):
                    queue_seen = True
                    removed_ts = str(d.get("timestamp") or "")
                    reason = d.get("reason") or "reason=absent"
                    res.update(state=f"REMOVED({reason})", evidence=f"{op}@{line_off}")
                elif op != "dequeue":
                    res.update(state=f"UNKNOWN(unmapped_op={op})", evidence=f"queue-operation@{line_off}")
            elif t == "attachment" and (d.get("attachment") or {}).get("type") == "queued_command":
                if sent in str(d["attachment"].get("prompt", "")) and queue_seen:
                    absorbed_at = line_off
                    res.update(
                        state="ABSORBED(unacked)",
                        evidence=f"queued_command@{line_off}",
                        delivered_at="",
                        absorbed_at=removed_ts,
                    )
            elif t == "user" and not d.get("isCompactSummary") and "toolUseResult" not in d:
                c = (d.get("message") or {}).get("content")
                if not isinstance(c, str) or d.get("promptSource") not in ("typed", "queued"):
                    continue
                if c.startswith(EXCLUDED_PREFIXES):
                    continue
                if sent in c:
                    k = c.find(sent)
                    others = sorted({m for m in HEAD_RE.findall(c) if m != mid})
                    if d.get("promptSource") == "queued":
                        st = "DELIVERED(turn_end)"
                    elif k == 0:
                        st = "DELIVERED"
                    elif others:
                        st = "DELIVERED(fused)"
                    else:
                        st = "DELIVERED(fused_with_unknown_prefix)"
                        print("unknown_prefix (first 200 chars, not stored):", repr(c[:k][:200]))
                    res.update(
                        state=st,
                        evidence=f"user@{line_off}+{k}",
                        delivered_at=str(d.get("timestamp")),
                        fused_with=others,
                        head_found=head in c,
                        line=line_of(path, line_off),
                    )
                    if k > 0 and not others:
                        res["unknown_prefix_len"] = k
                    return res
            elif t == "assistant" and absorbed_at is not None:
                blocks = (d.get("message") or {}).get("content") or []
                joined = " ".join(str(b.get("text") or b.get("thinking") or "") for b in blocks if isinstance(b, dict))
                if mid in joined:
                    res.update(
                        state="DELIVERED(absorbed,acked)",
                        evidence=f"assistant@{line_off}",
                        delivered_at=str(d.get("timestamp")),
                        line=line_of(path, line_off),
                    )
                    return res
    return res


def recorded_members(rows: list[dict], mid: str) -> set[str]:
    panes: set[str] = set()
    for r in rows:
        if r.get("id") != mid:
            continue
        if r.get("row_type") == "held":
            for m in r.get("members") or []:
                panes.add(m if isinstance(m, str) else str(m.get("pane", "")))
        elif r.get("row_type") in ("send", "resend") and r.get("pane"):
            panes.add(r["pane"])
    return panes


def do_send(args: argparse.Namespace) -> int:
    agents = agent_list()
    hub_sid = guard(agents)
    rows = load_rows()
    latest = latest_states(rows)
    resolved_by = "label"
    if args.to_pane:
        role0, a0 = resolve_pane(args.to_pane, args.to, agents, args.control)
        members = [(role0, a0)]
        resolved_by = "pane"
        print("resolved_by=pane", args.to_pane, "label=", role0)
    else:
        members = [(args.to, resolve(args.to, agents, args.control))]
    members += [(r, resolve(r, agents, args.control)) for r in (args.cc or [])]
    body_text = getattr(args, "body_text", None)
    if body_text is None and args.body_file:
        body_text = Path(args.body_file).read_text(encoding="utf-8")
    if args.id:
        if not any(r.get("id") == args.id and r.get("row_type") in ("held", "send", "resend") for r in rows):
            raise SystemExit(f"refused(unknown_id): {args.id} has no held/send row")
        bpath = BODIES / f"{args.id}.txt"
        if not bpath.exists():
            raise SystemExit(f"refused(no_body): {bpath} is missing")
        text = bpath.read_text(encoding="utf-8").rstrip("\n")
        if body_text is not None and norm_body(body_text) != strip_body(text):
            raise SystemExit(f"refused(body_mismatch): --body_file differs from the stored body of {args.id}")
        allowed = recorded_members(rows, args.id)
        strangers = [a["pane_id"] for _, a in members if a["pane_id"] not in allowed]
        if strangers:
            raise SystemExit(f"refused(member_not_in_fanout): {strangers} not in {sorted(allowed)}")
        mid = args.id
        unsent = []
        for role, a in members:
            st = str(latest.get((mid, a["pane_id"]), {}).get("state", ""))
            if st == "" or st == "HELD(fanout_stopped)":
                unsent.append((role, a))
            else:
                print(f"{a['pane_id']} {role}: skipped({st})")
        if not unsent:
            print(f"{mid}: nothing to complete")
            return 0
        members = unsent
    elif body_text is None:
        raise SystemExit("refused(no_body): --body_file is required")
    sent_ids = {r_id for (r_id, pane) in latest if pane}
    own = {
        r["id"]: r.get("head", "")
        for (r_id, pane), r in latest.items()
        if (pane or r_id not in sent_ids) and not str(r.get("state", "")).startswith(FINAL_STATES)
    }
    decisions = []
    for role, a in members:
        st = str(a.get("agent_status"))
        reason, facts = decide(st, read_view(a["pane_id"]), args.queue, own)
        decisions.append((role, a, reason, facts))
        if reason:
            print(f"{a['pane_id']} {role}: {reason} status={st} composer={facts['composer_before_kind']}")
    if not args.id:
        mid = "dry-run" if READONLY else alloc_id()
        text = compose(mid, members, body_text, args.resend_of)
        if not READONLY:
            (BODIES / f"{mid}.txt").write_text(text + "\n", encoding="utf-8")
    head = text.split("\n", 1)[0]
    sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
    base = {
        "id": mid,
        "body_sha256": sha,
        "head": head,
        "to": members[0][0],
        "to_requested": args.to,
        "cc": args.cc or [],
        "to_pane": args.to_pane or "",
        "resolved_by": resolved_by,
        "hub_session_id": hub_sid,
        "child_session": os.environ.get("CLAUDE_CODE_CHILD_SESSION", ""),
        "herdr_version": run(["herdr", "--version"]).strip(),
        "control": bool(args.control),
        "queued_on_topic": bool(args.queue),
    }
    if args.resend_of:
        base["resend_of"] = args.resend_of
    if any(r for _, _, r, _ in decisions):
        append_row(
            {
                **base,
                "row_type": "held",
                "state": ";".join(r for _, _, r, _ in decisions if r),
                "sent_at": jst_now(),
                "members": [
                    {
                        "pane": a["pane_id"],
                        "role": role,
                        "status": facts["status"],
                        "composer_before_kind": facts["composer_before_kind"],
                        "composer_before_sha256": facts["composer_before_sha256"],
                        "reason": reason,
                    }
                    for role, a, reason, facts in decisions
                ],
            }
        )
        return 2
    rc = 0
    pending = list(decisions)
    while pending:
        role, a, _, facts = pending.pop(0)
        if args.id and any(
            r.get("id") == mid and r.get("pane") == a["pane_id"] and str(r.get("state", "")).startswith("DELIVERED")
            for r in rows
        ):
            continue
        one = send_one(mid, role, a, text, head, sha, base, facts, args.queue)
        rc |= one
        if one == 2 and pending:
            for role2, a2, _, facts2 in pending:
                append_row({**base, **stopped_row(role2, a2, facts2)})
                print(a2["pane_id"], "HELD(fanout_stopped)")
            break
    return rc


def stopped_row(role: str, a: dict, facts: dict) -> dict:
    tpath = transcript_path(a)
    return {
        "row_type": "send",
        "pane": a["pane_id"],
        "role": role,
        "session_id": a["agent_session"]["value"],
        "transcript_path": str(tpath),
        "pre_send_offset": tpath.stat().st_size if tpath.exists() else 0,
        "via": "none",
        "state": "HELD(fanout_stopped)",
        "status": facts["status"],
        "sent_at": jst_now(),
        "composer_before_kind": facts["composer_before_kind"],
        "composer_before_sha256": facts["composer_before_sha256"],
    }


def status_of(pane: str) -> str:
    for a in agent_list():
        if a.get("pane_id") == pane:
            return str(a.get("agent_status"))
    return "None"


def send_one(mid: str, role: str, a: dict, text: str, head: str, sha: str, base: dict, facts: dict, queue: bool) -> int:
    pane = a["pane_id"]
    tpath = transcript_path(a)
    offset = tpath.stat().st_size if tpath.exists() else 0
    row = {
        **base,
        "row_type": "resend" if base.get("resend_of") else "send",
        "pane": pane,
        "role": role,
        "session_id": a["agent_session"]["value"],
        "transcript_path": str(tpath),
        "pre_send_offset": offset,
        "via": "none",
        "state": "",
        "status": facts["status"],
        "sent_at": jst_now(),
        "composer_before_kind": facts["composer_before_kind"],
        "composer_before_sha256": facts["composer_before_sha256"],
    }
    if READONLY:
        row["state"] = "dry_run(would_send)"
        append_row(row)
        return 0
    _, row["send_rc"] = run_rc(["herdr", "agent", "send", pane, text])
    try:
        return _after_send(mid, a, text, head, row, queue)
    except BaseException as exc:
        if not row["state"]:
            kind = "UNKNOWN" if row.get("via", "none") != "none" else "HELD"
            row["state"] = f"{kind}(error:{type(exc).__name__})"
            append_row(row)
            print(a["pane_id"], row["state"])
        raise


def _after_send(mid: str, a: dict, text: str, head: str, row: dict, queue: bool) -> int:
    """Post-send gate, status re-read, keypress and observation; the caller banks the row on any exception."""
    pane = a["pane_id"]
    tpath = Path(row["transcript_path"])
    offset = int(row["pre_send_offset"])
    landed = ""
    n_lines = text.count("\n") + 1
    for _ in range(6):
        v = read_view(pane)
        comp = v.get("composer_plain", "")
        if comp.startswith(head):
            landed = "head"
            break
        pm = paste_marker_lines(comp)
        if pm == n_lines:
            landed = comp.strip()
            break
        if pm:
            row["state"] = f"HELD(paste_count_mismatch:{pm}!={n_lines})"
            append_row(row)
            print(pane, row["state"])
            return 2
        if comp and not comp.startswith("MSG " + mid):
            row["state"] = "HELD(foreign_text_in_composer)"
            append_row(row)
            print(pane, row["state"])
            return 2
        time.sleep(0.25)
    if not landed:
        row["state"] = "HELD(send_not_rendered)"
        append_row(row)
        print(pane, row["state"])
        return 2
    row["landed_as"] = landed
    before, now = str(a.get("agent_status")), status_of(pane)
    row["status_at_keypress"] = now
    if now not in ("idle", "done", "working") or (before == "working") != (now == "working"):
        row["state"] = f"HELD(status_changed:{before}->{now})"
        append_row(row)
        print(pane, row["state"])
        return 2
    key = "Tab" if (now == "working" and queue) else "Enter"
    _, row["keypress_rc"] = run_rc(["herdr", "pane", "send-keys", pane, key])
    if row["keypress_rc"] != 0:
        row["state"] = f"HELD(keypress_refused:rc={row['keypress_rc']})"
        append_row(row)
        print(pane, row["state"])
        return 2
    row["via"] = key
    row["enter_at"] = jst_now()
    if key == "Enter":
        for _ in range(12):
            time.sleep(0.5)
            res = scan(tpath, offset, text, head, mid)
            if res["state"].startswith("DELIVERED"):
                row.update(res, first_seen_at=jst_now())
                break
        else:
            v = read_view(pane)
            stuck = "composer_plain" in v and (
                v["composer_plain"].startswith("MSG " + mid) or "[pasted text" in v["composer_plain"].lower()
            )
            row.update(scan(tpath, offset, text, head, mid))
            if stuck:
                row["state"] = "STUCK_IN_COMPOSER"
    else:
        time.sleep(0.5)
        v = read_view(pane)
        whole = "\n".join(v.get("plain", [])).lower()
        res = scan(tpath, offset, text, head, mid)
        if res["state"] == "UNKNOWN(no-record)":
            res["state"] = (
                "QUEUED(observed:viewport)" if any(m in whole for m in QUEUED_MARKERS) else "UNKNOWN(no-observation)"
            )
        row.update(res)
    append_row(row)
    print(pane, row["state"], row.get("evidence", ""))
    return 0 if row["state"].startswith(("DELIVERED", "QUEUED")) else 1


VERIFY_COPY = (
    "id",
    "pane",
    "role",
    "to",
    "to_requested",
    "cc",
    "to_pane",
    "resolved_by",
    "control",
    "resend_of",
    "session_id",
    "transcript_path",
    "pre_send_offset",
    "head",
    "body_sha256",
    "hub_session_id",
    "sent_at",
    "via",
    "enter_at",
)


def norm_state(state: str) -> str:
    """QUEUED(observed:viewport) and QUEUED(observed) are one state for the change test."""
    return state.replace("(observed:viewport)", "(observed)")


def do_verify(args: argparse.Namespace) -> int:
    if not READONLY:
        guard(agent_list())
    rows = load_rows()
    latest = latest_states(rows)
    rc = 0
    for (mid, pane), r in latest.items():
        if args.id and mid != args.id:
            continue
        old = str(r.get("state", ""))
        if (
            r.get("row_type") == "held"
            or old.startswith(FINAL_STATES)
            or old == "HELD(fanout_stopped)"
            or not r.get("transcript_path")
        ):
            continue
        try:
            bpath = BODIES / f"{mid}.txt"
            text = bpath.read_text(encoding="utf-8").rstrip("\n") if bpath.exists() else ""
            if not text:
                print(mid, pane, "refused(no_body): row skipped, nothing scanned")
                rc = 1
                continue
            res = scan(Path(r["transcript_path"]), int(r["pre_send_offset"]), text, r.get("head", ""), mid)
            if old.startswith("HELD(") and res["state"] == "UNKNOWN(no-record)":
                print(mid, pane, old, "-> kept (nothing observed)")
                continue
            sent_at = _dt.datetime.fromisoformat(r["sent_at"]) if r.get("sent_at") else None
            pressed = r.get("via", "none") != "none"
            overdue = (
                (_dt.datetime.now().astimezone() - sent_at).total_seconds() > 3600
                if (sent_at is not None and pressed)
                else None
            )
            new = {
                **{k: r[k] for k in VERIFY_COPY if k in r},
                "row_type": "verify",
                "verified_at": jst_now(),
                "overdue": overdue,
                **res,
            }
            print(mid, pane, old, "->", res["state"], res.get("evidence", ""))
            if norm_state(res["state"]) != norm_state(old):
                append_row(new)
        except (OSError, ValueError, KeyError) as exc:
            print(mid, pane, f"verify_error({type(exc).__name__}): {exc}")
            rc = 1
    return rc


def do_resend(args: argparse.Namespace) -> int:
    rows = load_rows()
    src = [r for r in rows if r.get("id") == args.id and r.get("row_type") in ("send", "resend", "held")]
    if not src:
        raise SystemExit(f"refused(unknown_id): {args.id}")
    if src[0].get("control"):
        raise SystemExit(f"refused(control_row): {args.id} was a control send to the hub's own pane; not resent")
    body_path = BODIES / f"{args.id}.txt"
    if not body_path.exists():
        raise SystemExit(f"refused(no_body): {body_path} is missing")
    body = strip_body(body_path.read_text(encoding="utf-8"))
    ns = argparse.Namespace(
        to=src[0]["to"],
        cc=src[0].get("cc") or [],
        body_file=None,
        body_text=body,
        queue=args.queue,
        id=None,
        to_pane=src[0].get("to_pane") or None,
        control=False,
        resend_of=args.id,
    )
    return do_send(ns)


def id_files(root: str) -> list[Path]:
    """Id-shaped files of the retired by-hand directories only (the hub's subagents write elsewhere in root)."""
    paths = glob.glob(root + "/ids_retired_*/*") + glob.glob(root + "/desk_msgs_retired_*/*")
    return [Path(p) for p in paths if ID_FILE_RE.match(os.path.basename(p))]


def do_init(_args: argparse.Namespace) -> int:
    if not READONLY:
        guard(agent_list())
    live = FLOOR.read_text().strip() if FLOOR.exists() else "absent"
    if FLOOR.exists() and not READONLY:
        raise SystemExit(f"refused(floor_exists): {FLOOR} = {live}; init runs once")
    for d in glob.glob(SCRATCH_GLOB + "/ids") + glob.glob(SCRATCH_GLOB + "/desk_msgs"):
        raise SystemExit(f"refused(by_hand_alive): rename {d} first")
    transcripts = sorted(PROJECTS.glob("-home-rlrk-IsaacLab/*.jsonl"))
    own_files = id_files(SCRATCH_OWN)
    top = 0
    for p in transcripts:
        try:
            with open(p, encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    m = FLOOR_JSON_RE.search(line)
                    if m:
                        top = max(top, int(m.group(1)))
        except OSError:
            continue
    for p in own_files:
        top = max(top, int(ID_FILE_RE.match(p.name).group(1)))
        try:
            for m in FLOOR_RE.finditer(p.read_text(encoding="utf-8", errors="replace")):
                top = max(top, int(m.group(1)))
        except (OSError, UnicodeDecodeError):
            continue
    git = run(["git", "-C", str(REPO), "grep", "--untracked", "-ohE", "MSG m-p18-[0-9]+ /", "--", "."])
    for m in FLOOR_RE.finditer(git):
        top = max(top, int(m.group(1)))
    query = (
        "max N over delivered heads: transcripts (content starting with MSG m-p18-N /) in "
        "~/.claude/projects/-home-rlrk-IsaacLab/*.jsonl; git grep --untracked (head tokens) in the repo; "
        "id-shaped files ((body_)m-p18-N(.txt), name and line-start heads) under ids_retired_*/ and "
        "desk_msgs_retired_*/ of " + SCRATCH_OWN
    )
    if READONLY:
        counts = f"transcripts {len(transcripts)} | own id files {len(own_files)}"
        print(f"dry_run floor: {top} (live .floor = {live}) | {counts}")
        return 0
    BODIES.mkdir(exist_ok=True)
    FLOOR.write_text(f"{top}\n")
    append_row(
        {
            "row_type": "init",
            "floor": top,
            "query": query,
            "at": jst_now(),
            "transcripts": len(transcripts),
            "paths_scanned": len(transcripts) + len(own_files),
            "hub_session_id": os.environ.get("CLAUDE_CODE_SESSION_ID", ""),
        }
    )
    print("floor", top)
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="hub-only send/verify/resend tool for w2:p18")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("send")
    s.add_argument("--to", required=True)
    s.add_argument("--cc", nargs="*")
    s.add_argument("--body_file")
    s.add_argument("--queue", action="store_true")
    s.add_argument("--id")
    s.add_argument("--to_pane")
    s.add_argument("--control", action="store_true")
    s.set_defaults(func=do_send, resend_of=None)
    v = sub.add_parser("verify")
    v.add_argument("--id")
    v.set_defaults(func=do_verify)
    r = sub.add_parser("resend")
    r.add_argument("--id", required=True)
    r.add_argument("--queue", action="store_true")
    r.set_defaults(func=do_resend)
    i = sub.add_parser("init")
    i.set_defaults(func=do_init)
    for p in (s, v, r, i):
        p.add_argument("--dry_run", action="store_true", help="after the subcommand: read and print only")
    args = ap.parse_args(argv)
    global READONLY
    READONLY = READONLY or bool(getattr(args, "dry_run", False))
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

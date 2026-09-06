#!/usr/bin/env python3
# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Hub-only send / verify / resend tool for the pane w2:p18 (T-ROOT-OPS-SUPERVISOR).

Design of record: eval_runs/troot_optE_dapg_wholeroute_scope_20260701/P18_D1_VERIFY_CYCLE2_20260905.md Part 2
(PROPOSE v3, increment 1'). Authorized by Rs1 (the human): files = transcript line 39366; build = line 40230.

Procedure (send):
- Guard = a pane bind, not a two-factor bind: HERDR_PANE_ID must be w2:p18 and CLAUDE_CODE_SESSION_ID must equal
  the live w2:p18 agent session. Subagents and background jobs of the hub inherit both (measured 2026-09-05) and
  cannot be excluded by the environment: they must not invoke this tool. Every row records hub_session_id.
- Roster = non-comment lines of scripts/validations/nest_role_labels.txt read at run time, minus RETIRED.
  Resolution = `herdr agent list`, w2 agents only, name "w2:pN ROLE" -> exact match -> exactly one live agent.
- Order: resolve every member -> read every member -> decide every member -> only then allocate the id, compose the
  text once (head line + body + footer), write bodies/m-p18-N.txt, send the identical bytes to each member.
- Pre-send decision (fail-closed): HELD when agent_status is not idle/done/working; when a herdr dialog marker is
  in the viewport; when there is no composer line (prompt glyph + U+00A0) or more than one; when the composer shows
  a folded paste; when the composer holds one of our own non-final messages; when the composer holds any text that
  is not dim (SGR 2) in an ANSI read; when the destination is working and --queue was not given. Only dim text
  (a UI suggestion) is typed over. Nothing is ever sent before the whole fan-out has been decided.
- Post-send gate: after `herdr agent send` the composer is re-read (up to 6 x 0.25 s); the keypress (Enter, or
  Tab with --queue on a working pane) is pressed only when the composer starts with the head line.
- Observation: the state of a row comes from the destination transcript, never from the keypress.
  P1 DELIVERED = a user record (string content, promptSource typed|queued, no toolUseResult, not a compaction
  summary, not a local-command echo) containing the sent bytes; position > 0 = DELIVERED(fused).
  Q1 QUEUED(observed) = an enqueue record with the sent bytes, or the queued marker in the viewport.
  Q2 ABSORBED(unacked) = a remove/popAll record followed by a queued_command attachment with the sent bytes
  (the reason field is absent in 2600 of 2634 removes; it is an annotation, not the key). Non-terminal.
  A1 DELIVERED(absorbed,acked) = after Q2, an assistant record (text or thinking) naming the bare id.
  Q3 DELIVERED(turn_end) = the P1 shape with promptSource queued. Q4 REMOVED = a remove with no following
  attachment or user record (1 of 2600 measured). Unknown queue operations surface as UNKNOWN(unmapped_op).
  The tool never writes LOST.
- Measured semantics (2026-09-05): record 18-23 ms after Enter (n=2); Enter->working 0.29/0.41 s (n=2);
  Tab->enqueue 4.6-314 s (n=10, 1/10 within 6 s); enqueue->absorb 5.9-72.1 s (n=9); Tab->terminal record
  30.7-517.5 s (n=15, median 103 s); viewport 66-80 lines; composer line = U+276F U+00A0, echoes = U+276F U+0020.
- verify re-reads every non-final row from its stored byte offset (a mid-line offset is resynchronised to the
  next newline). --dry_run / HUB_SEND_READONLY=1 read and print, write nothing, send nothing.
- resend --id re-sends the same body bytes with an appended "resend <date>" line as a new row.
- init computes bodies/.floor by a closed query over all transcripts, the repo and every session scratchpad; it
  refuses while the by-hand scratchpad directories (ids, desk_msgs) still exist un-renamed.
Deviations from v3 section 3-D and from the node DoD are listed in the design of record (section 7).
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
PROMPT = "❯ "
ECHO = "❯ "
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
QUEUED_MARKERS = ("press up to edit queued messages", "queued message")
EXCLUDED_PREFIXES = ("<local-command-", "<command-name>", "<task-notification>")
ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")
ID_RE = re.compile(r"m-p18-(\d+)")
FLOOR_RE = re.compile(r"^MSG m-p18-(\d+) /", re.MULTILINE)
FLOOR_JSON_RE = re.compile(r'"content":"MSG m-p18-(\d+) /')
HEAD_RE = re.compile(r"MSG (m-p18-\d+) /")
FINAL_STATES = ("DELIVERED", "refused")
READONLY = os.environ.get("HUB_SEND_READONLY") == "1"


def jst_now() -> str:
    return _dt.datetime.now().astimezone().isoformat(timespec="milliseconds")


def run(argv: list[str]) -> str:
    """Run a command without a shell; return decoded stdout (errors replaced)."""
    out = subprocess.run(argv, capture_output=True, check=False)
    return out.stdout.decode("utf-8", errors="replace")


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


def resolve(role: str, agents: list[dict], control: bool) -> dict:
    if role in RETIRED:
        raise SystemExit(f"refused(retired): {role}")
    if role == HUB_ROLE and not control:
        raise SystemExit("refused(self): use --control for the hub's own pane")
    if role not in roster() and role != HUB_ROLE:
        raise SystemExit(f"refused(unregistered): {role}")
    hits = []
    for a in agents:
        name = str(a.get("name", ""))
        label = name.split(" ", 1)[1] if " " in name else ""
        label = label[len("T-ROOT-") :] if label.startswith("T-ROOT-") else label
        if label == role:
            hits.append(a)
    if len(hits) != 1:
        raise SystemExit(
            f"refused({'unresolved' if not hits else 'ambiguous'}): {role} -> {[h['pane_id'] for h in hits]}"
        )
    return hits[0]


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


def decide(status: str, view: dict, queue: bool, own_texts: dict[str, str]) -> tuple[str, dict]:
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
        for mid, text in own_texts.items():
            if comp.startswith("MSG m-p18-") and text.startswith(comp[:40]):
                facts["composer_before_kind"] = "own_message"
                return f"HELD(composer_holds_own_message id={mid})", facts
        if view["composer_dim_only"]:
            facts["composer_before_kind"] = "ghost"
        else:
            facts["composer_before_kind"] = "draft"
            return "HELD(draft)", facts
    if status == "working" and not queue:
        return "HELD(working)", facts
    return "", facts


def transcript_path(agent: dict) -> Path:
    proj = str(agent.get("cwd", "/home/rlrk/IsaacLab")).replace("/", "-")
    return PROJECTS / proj / f"{agent['agent_session']['value']}.jsonl"


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


def latest_states(rows: list[dict]) -> dict[str, dict]:
    latest: dict[str, dict] = {}
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


def scan(path: Path, offset: int, sent: str, head: str, mid: str) -> dict:
    """Read the destination transcript from offset and classify (P1, Q1-Q4, A1)."""
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
        absorbed_at, queue_seen = None, False
        for raw in fh:
            line_off = pos
            pos += len(raw)
            try:
                d = json.loads(raw.decode("utf-8", errors="replace"))
            except json.JSONDecodeError:
                continue
            t = d.get("type")
            if t == "queue-operation":
                op = d.get("operation")
                content = str(d.get("content", ""))
                if op == "enqueue" and sent in content:
                    res.update(state="QUEUED(observed)", evidence=f"enqueue@{line_off}")
                elif op in ("remove", "popAll") and sent in content:
                    queue_seen = True
                    res.update(state=f"REMOVED({d.get('reason')})", evidence=f"{op}@{line_off}")
                elif op == "dequeue" or (op in ("remove", "popAll") and not content):
                    continue
                elif op not in ("enqueue", "remove", "popAll", "dequeue"):
                    res.update(state=f"UNKNOWN(unmapped_op={op})", evidence=f"queue-operation@{line_off}")
            elif t == "attachment" and (d.get("attachment") or {}).get("type") == "queued_command":
                if sent in str(d["attachment"].get("prompt", "")) and queue_seen:
                    absorbed_at = line_off
                    res.update(state="ABSORBED(unacked)", evidence=f"queued_command@{line_off}", delivered_at="")
            elif t == "user" and not d.get("isCompactSummary") and "toolUseResult" not in d:
                c = (d.get("message") or {}).get("content")
                if not isinstance(c, str) or d.get("promptSource") not in ("typed", "queued"):
                    continue
                if c.startswith(EXCLUDED_PREFIXES):
                    continue
                if sent in c:
                    k = c.find(sent)
                    others = sorted({m for m in HEAD_RE.findall(c) if m != mid})
                    st = (
                        "DELIVERED(turn_end)"
                        if d.get("promptSource") == "queued"
                        else ("DELIVERED" if k == 0 else "DELIVERED(fused)")
                    )
                    res.update(
                        state=st,
                        evidence=f"user@{line_off}+{k}",
                        delivered_at=str(d.get("timestamp")),
                        fused_with=others,
                        head_found=head in c,
                    )
                    return res
            elif t == "assistant" and absorbed_at is not None:
                blocks = (d.get("message") or {}).get("content") or []
                joined = " ".join(str(b.get("text") or b.get("thinking") or "") for b in blocks if isinstance(b, dict))
                if mid in joined:
                    res.update(
                        state="DELIVERED(absorbed,acked)",
                        evidence=f"assistant@{line_off}",
                        delivered_at=str(d.get("timestamp")),
                    )
                    return res
    return res


def do_send(args: argparse.Namespace) -> int:
    agents = agent_list()
    hub_sid = guard(agents)
    roles = [args.to, *(args.cc or [])]
    members = [(r, resolve(r, agents, args.control)) for r in roles]
    if args.to_pane:
        forced = [a for a in agents if a.get("pane_id") == args.to_pane]
        if not forced:
            raise SystemExit(f"refused(unresolved): {args.to_pane}")
        members[0] = (args.to, forced[0])
        print("resolved_by=pane", args.to_pane)
    rows = load_rows()
    own = {
        r["id"]: r.get("head", "")
        for r in rows
        if r.get("row_type") in ("send", "resend") and not r.get("state", "").startswith(FINAL_STATES)
    }
    decisions = []
    for role, a in members:
        st = str(a.get("agent_status"))
        reason, facts = decide(st, read_view(a["pane_id"]), args.queue, own)
        decisions.append((role, a, reason, facts))
        if reason:
            print(f"{a['pane_id']} {role}: {reason} status={st} composer={facts['composer_before_kind']}")
    body = Path(args.body_file).read_text(encoding="utf-8")
    mid = args.id or ("dry-run" if READONLY else alloc_id())
    text = compose(mid, members, body, args.resend_of)
    head = text.split("\n", 1)[0]
    sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
    if not READONLY and not args.id:
        (BODIES / f"{mid}.txt").write_text(text + "\n", encoding="utf-8")
    base = {
        "id": mid,
        "body_sha256": sha,
        "head": head,
        "to": args.to,
        "cc": args.cc or [],
        "hub_session_id": hub_sid,
        "child_session": os.environ.get("CLAUDE_CODE_CHILD_SESSION", ""),
        "herdr_version": run(["herdr", "--version"]).strip(),
        "control": bool(args.control),
        "queued_on_topic": bool(args.queue),
    }
    if any(r for _, _, r, _ in decisions):
        append_row(
            {
                **base,
                "row_type": "held",
                "state": ";".join(r for _, _, r, _ in decisions if r),
                "sent_at": jst_now(),
                "members": [a["pane_id"] for _, a, _, _ in decisions],
            }
        )
        return 2
    rc = 0
    for role, a, _, facts in decisions:
        if args.id and any(
            r.get("id") == mid and r.get("pane") == a["pane_id"] and str(r.get("state", "")).startswith("DELIVERED")
            for r in rows
        ):
            continue
        rc |= send_one(mid, role, a, text, head, sha, base, facts, args.queue)
    return rc


def send_one(mid: str, role: str, a: dict, text: str, head: str, sha: str, base: dict, facts: dict, queue: bool) -> int:
    pane = a["pane_id"]
    tpath = transcript_path(a)
    offset = tpath.stat().st_size if tpath.exists() else 0
    row = {
        **base,
        "row_type": "send",
        "pane": pane,
        "role": role,
        "session_id": a["agent_session"]["value"],
        "transcript_path": str(tpath),
        "pre_send_offset": offset,
        "via": "none",
        "state": "",
        "sent_at": jst_now(),
        "composer_before_kind": facts["composer_before_kind"],
        "composer_before_sha256": facts["composer_before_sha256"],
    }
    if READONLY:
        row["state"] = "dry_run(would_send)"
        append_row(row)
        return 0
    run(["herdr", "agent", "send", pane, text])
    landed = False
    for _ in range(6):
        v = read_view(pane)
        if "composer_plain" in v and v["composer_plain"].startswith(head):
            landed = True
            break
        if "composer_plain" in v and v["composer_plain"] and not v["composer_plain"].startswith("MSG " + mid):
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
    key = "Tab" if (a.get("agent_status") == "working" and queue) else "Enter"
    run(["herdr", "pane", "send-keys", pane, key])
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


def do_verify(args: argparse.Namespace) -> int:
    rows = load_rows()
    latest = latest_states(rows)
    for (mid, pane), r in latest.items():
        if args.id and mid != args.id:
            continue
        if (
            r.get("row_type") == "held"
            or str(r.get("state", "")).startswith(FINAL_STATES)
            or not r.get("transcript_path")
        ):
            continue
        text = (
            (BODIES / f"{mid}.txt").read_text(encoding="utf-8").rstrip("\n") if (BODIES / f"{mid}.txt").exists() else ""
        )
        res = scan(Path(r["transcript_path"]), int(r["pre_send_offset"]), text, r.get("head", ""), mid)
        overdue = (_dt.datetime.now().astimezone() - _dt.datetime.fromisoformat(r["sent_at"])).total_seconds() > 3600
        new = {
            **{
                k: r[k]
                for k in (
                    "id",
                    "pane",
                    "role",
                    "transcript_path",
                    "pre_send_offset",
                    "head",
                    "body_sha256",
                    "hub_session_id",
                )
            },
            "row_type": "verify",
            "verified_at": jst_now(),
            "overdue": overdue,
            **res,
        }
        print(mid, pane, r.get("state"), "->", res["state"], res.get("evidence", ""))
        if res["state"] != r.get("state"):
            append_row(new)
    return 0


def do_resend(args: argparse.Namespace) -> int:
    rows = load_rows()
    src = [r for r in rows if r.get("id") == args.id and r.get("row_type") in ("send", "resend", "held")]
    if not src:
        raise SystemExit(f"refused(unknown_id): {args.id}")
    body_path = BODIES / f"{args.id}.txt"
    text = body_path.read_text(encoding="utf-8")
    body = "\n".join(text.split("\n")[1:-2])
    tmp = DIR / ".resend_body.txt"
    tmp.write_text(body, encoding="utf-8")
    ns = argparse.Namespace(
        to=src[0]["to"],
        cc=src[0].get("cc") or [],
        body_file=str(tmp),
        queue=args.queue,
        id=None,
        to_pane=None,
        control=src[0].get("control", False),
        resend_of=args.id,
    )
    try:
        return do_send(ns)
    finally:
        tmp.unlink(missing_ok=True)


def do_init(_args: argparse.Namespace) -> int:
    for d in glob.glob(SCRATCH_GLOB + "/ids") + glob.glob(SCRATCH_GLOB + "/desk_msgs"):
        raise SystemExit(f"refused(by_hand_alive): rename {d} first")
    paths = list(PROJECTS.glob("-home-rlrk-IsaacLab/*.jsonl")) + [
        Path(p) for p in glob.glob(SCRATCH_GLOB + "/**/*", recursive=True)
    ]
    top = 0
    for p in paths:
        try:
            rx = FLOOR_JSON_RE if p.suffix == ".jsonl" else FLOOR_RE
            for m in rx.finditer(p.read_text(encoding="utf-8", errors="replace")):
                top = max(top, int(m.group(1)))
        except (OSError, UnicodeDecodeError):
            continue
    git = run(["git", "-C", str(REPO), "grep", "-ohE", "MSG m-p18-[0-9]+ /", "--", "."])
    for m in FLOOR_RE.finditer(git):
        top = max(top, int(m.group(1)))
    BODIES.mkdir(exist_ok=True)
    if READONLY:
        print("dry_run floor:", top)
        return 0
    FLOOR.write_text(f"{top}\n")
    append_row(
        {
            "row_type": "init",
            "floor": top,
            "query": "max N over delivered heads (jsonl: content starting with MSG m-p18-N /; files: line-start MSG m-p18-N /) in ~/.claude/projects/-home-rlrk-IsaacLab/*.jsonl, git grep, "
            + SCRATCH_GLOB,
            "at": jst_now(),
            "transcripts": len(paths),
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
    s.add_argument("--body_file", required=True)
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
    for p in (ap, s, v, r, i):
        p.add_argument("--dry_run", action="store_true", help="read and print only; set HUB_SEND_READONLY=1 as well")
    args = ap.parse_args(argv)
    global READONLY
    READONLY = READONLY or bool(getattr(args, "dry_run", False))
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

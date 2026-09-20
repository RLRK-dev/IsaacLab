# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Transport regressions; all terminal calls are replaced by a rejecting fake.

Set HUB_SEND_UNDER_TEST to the frozen script to demonstrate failures without the repair.
"""

from __future__ import annotations

import argparse
import copy
import importlib.util
import io
import json
import os
import tempfile
import unittest
from contextlib import ExitStack, redirect_stdout
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(os.environ.get("HUB_SEND_UNDER_TEST", Path(__file__).with_name("hub_send.py")))
SPEC = importlib.util.spec_from_file_location("hub_send_under_test", SCRIPT)
hub = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(hub)


class DeliveryTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.root = Path(self.stack.enter_context(tempfile.TemporaryDirectory()))
        self.transcript = self.root / "recipient.jsonl"
        self.transcript.write_text("")
        self.agent = {
            "pane_id": "w2:p6",
            "agent": "claude",
            "agent_session": {"value": "recipient-session"},
            "agent_status": "idle",
            "label": "w2:p6 PLAN-KEEPER",
        }
        self.mid = "fixture-delivery-1"
        self.head = f"MSG {self.mid} / test sender"
        self.text = self.head + "\n種別: 報告 | 用件: fixture\n根拠: fixture\n次担当: test"
        self.rows = []
        self.calls = []
        self.view = self.make_view("")
        self.transport_error = None
        self.transport_rc = 0
        self.emit_delivery = True
        self.base = {"id": self.mid, "head": self.head}
        self.facts = {"status": "idle", "composer_before_kind": "empty", "composer_before_sha256": ""}
        self.mock("READONLY", False)
        self.mock("BODIES", self.root)
        self.mock("FLOOR", self.root / ".floor")
        hub.FLOOR.write_text("1\n")
        self.mock("transcript_path", lambda _agent: self.transcript)
        self.mock("agent_list", lambda: [self.agent])
        self.mock("read_view", lambda _pane: copy.deepcopy(self.view))
        self.mock("append_row", lambda row: self.rows.append(copy.deepcopy(row)))
        self.mock("run_rc", self.transport)
        self.stack.enter_context(
            patch.object(hub.subprocess, "run", side_effect=AssertionError("real process forbidden"))
        )
        self.stack.enter_context(patch.object(hub.time, "sleep", return_value=None))
        self.stack.enter_context(redirect_stdout(io.StringIO()))

    def mock(self, name, value):
        return self.stack.enter_context(patch.object(hub, name, value))

    @staticmethod
    def make_view(text, dim=False):
        return {
            "plain": [hub.PROMPT + text],
            "raw": [],
            "truncated": False,
            "composer_idx": [0],
            "composer_plain": text,
            "composer_dim_only": dim,
        }

    def transport(self, argv):
        self.calls.append(argv)
        if self.transport_error:
            raise self.transport_error
        if argv[:3] == ["herdr", "agent", "prompt"]:
            # The intent must already be durable when any terminal mutation becomes possible.
            if not self.rows or self.rows[-1].get("submission_attempted") is not True:
                raise AssertionError("missing submission intent")
            if self.emit_delivery:
                event = {
                    "type": "user",
                    "promptSource": "typed",
                    "timestamp": "2026-09-20T01:00:00Z",
                    "message": {"content": argv[4]},
                }
                with self.transcript.open("a") as stream:
                    stream.write(json.dumps(event) + "\n")
            return "{}", self.transport_rc
        if argv[:3] in (["herdr", "pane", "send-text"], ["herdr", "pane", "send-keys"]):
            return "", 0  # frozen implementation only; observable mutation, no real terminal
        raise AssertionError(f"unexpected process: {argv}")

    def send(self, queue=False):
        original = copy.deepcopy(self.agent)
        original["agent_status"] = "idle"
        return hub.send_one(
            self.mid, "PLAN-KEEPER", original, self.text, self.head, "fixture-sha", self.base, self.facts, queue
        )

    def test_ghost_suggestion_does_not_leave_a_partial_paste(self):
        self.view = self.make_view("Continue with this suggestion", dim=True)
        self.assertEqual(self.send(), 0)
        self.assertEqual(self.calls, [["herdr", "agent", "prompt", "w2:p6", self.text]])
        self.assertTrue(self.rows[-1]["state"].startswith("DELIVERED"))

    def test_foreign_draft_after_initial_fanout_check_submits_nothing(self):
        self.view = self.make_view("the user's unfinished input")
        self.assertEqual(self.send(), 2)
        self.assertEqual(self.calls, [])
        self.assertIs(self.rows[-1]["submission_attempted"], False)
        self.assertTrue(hub.never_submitted(self.rows[-1]))

    def test_working_recipient_is_rechecked_before_submission(self):
        self.agent["agent_status"] = "working"
        self.assertEqual(self.send(), 2)
        self.assertEqual(self.calls, [])

    def test_session_replacement_submits_nothing(self):
        original = copy.deepcopy(self.agent)
        self.agent["agent_session"] = {"value": "replacement"}
        rc = hub.send_one(self.mid, "PLAN-KEEPER", original, self.text, self.head, "sha", self.base, self.facts, False)
        self.assertEqual(rc, 2)
        self.assertEqual(self.calls, [])
        self.assertEqual(self.rows[-1]["state"], "HELD(destination_changed)")

    def test_unknown_transport_failure_is_not_retryable(self):
        self.transport_error = TimeoutError("uncertain transport")
        with self.assertRaises(TimeoutError):
            self.send()
        self.assertTrue(self.rows[-1]["state"].startswith("UNKNOWN"))
        self.assertIs(self.rows[-1]["submission_attempted"], True)
        self.assertFalse(hub.never_submitted(self.rows[-1]))

    def test_successful_cli_without_transcript_is_not_delivery(self):
        self.emit_delivery = False
        self.assertEqual(self.send(), 1)
        self.assertEqual(self.rows[-1]["state"], "UNKNOWN(no-record)")
        self.assertFalse(hub.never_submitted(self.rows[-1]))

    def test_nonzero_transport_result_is_retained(self):
        self.emit_delivery = False
        self.transport_rc = 1
        self.send()
        self.assertEqual(self.rows[-1]["send_rc"], 1)
        self.assertFalse(hub.never_submitted(self.rows[-1]))

    def test_dry_run_does_not_submit_or_read_new_input(self):
        self.mock("READONLY", True)
        self.mock("agent_list", lambda: self.fail("dry run reached submission preflight"))
        self.assertEqual(self.send(), 0)
        self.assertEqual(self.calls, [])

    def test_legacy_post_paste_hold_is_never_completed_automatically(self):
        for state in (
            "HELD(foreign_text_in_composer)",
            "STUCK_IN_COMPOSER",
            "QUEUED(observed)",
            "ABSORBED(unacked)",
            "UNKNOWN(no-record)",
            "DELIVERED",
        ):
            self.assertFalse(hub.never_submitted({"state": state, "via": "none"}), state)
        self.assertTrue(hub.never_submitted({"state": "HELD(fanout_stopped)"}))
        self.assertFalse(hub.never_submitted({"state": "DELIVERED", "submission_attempted": False}))

    def test_tool_result_mention_is_not_delivery(self):
        event = {"type": "user", "promptSource": "typed", "toolUseResult": {}, "message": {"content": self.text}}
        self.transcript.write_text(json.dumps(event) + "\n")
        result = hub.scan(self.transcript, 0, self.text, self.head, self.mid)
        self.assertEqual(result["state"], "UNKNOWN(no-record)")

    def test_queue_enqueue_is_not_delivery(self):
        event = {"type": "queue-operation", "operation": "enqueue", "content": self.text}
        self.transcript.write_text(json.dumps(event) + "\n")
        result = hub.scan(self.transcript, 0, self.text, self.head, self.mid)
        self.assertEqual(result["state"], "QUEUED(observed)")

    def test_busy_cc_does_not_hold_an_idle_primary(self):
        other = {**self.agent, "pane_id": "w2:p4", "label": "w2:p4 RS-TECH-LEAD", "agent_status": "working"}
        self.mock("agent_list", lambda: [self.agent, other])
        self.mock("guard", lambda _agents: "hub-fixture")
        self.mock("resolve", lambda role, _agents, _control: self.agent if role == "PLAN-KEEPER" else other)
        self.mock("load_rows", lambda: [])
        self.mock("alloc_id", lambda: self.mid)
        self.mock("run", lambda _argv: "herdr 0.9.0")
        args = argparse.Namespace(
            to="PLAN-KEEPER",
            cc=["RS-TECH-LEAD"],
            body_text="fixture body",
            body_file=None,
            to_pane=None,
            id=None,
            control=False,
            resend_of=None,
            queue=False,
        )
        self.assertEqual(hub.do_send(args), 2)  # partial delivery remains visible to the caller
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(self.calls[0][3], "w2:p6")
        self.assertTrue(self.rows[-1]["state"].startswith("DELIVERED"))

    def test_pending_distinguishes_never_sent_and_uncertain_without_writes(self):
        history = [
            {
                "id": self.mid,
                "row_type": "held",
                "members": [{"pane": "w2:p6", "role": "PLAN-KEEPER", "reason": "HELD(working)"}],
            },
            {"id": "fixture-old", "row_type": "send", "pane": "w2:p4", "state": "HELD(foreign_text_in_composer)"},
        ]
        self.mock("load_rows", lambda: history)
        output = io.StringIO()
        with redirect_stdout(output):
            hub.do_pending(argparse.Namespace(id=None))
        results = {row["id"]: row for row in json.loads(output.getvalue())["pending"]}
        self.assertTrue(results[self.mid]["never_submitted"])
        self.assertFalse(results["fixture-old"]["never_submitted"])
        self.assertEqual(self.rows, [])
        self.assertEqual(self.calls, [])

    def test_sender_lock_contention_submits_nothing(self):
        with patch.object(hub.fcntl, "flock", side_effect=BlockingIOError):
            self.assertEqual(hub.main(["send", "--to", "PLAN-KEEPER", "--body_file", "not-read"]), 2)
        self.assertEqual(self.calls, [])
        self.assertEqual(self.rows, [])


if __name__ == "__main__":
    unittest.main()

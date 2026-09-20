# Pane delivery reliability — 2026-09-20

Owner: implementation p19 (Codex); live hub operation p18; planning-state reflection p6.
Parent: T-ROOT-Agentic-Improvement-OpsSup-20260904, existing delivery tool.

## Authorization and boundary

The user asked whether sharing delays were merely a matter of time. Codex distinguished ordinary reading delay
from suspended delivery and identified reliable delivery/readback plus shared-record reflection as the improvement
target. The user then instructed **「ok 改善して」**. Custody is the current p19 Codex conversation and Vault
`log.md` 2026-09-20 09:47:22 JST. This new task authorizes a bounded repair of the delivery workflow; the earlier
format-only scope is not being silently expanded. The old frozen code is `44e0f9a2d1`, SHA-256
`b4944c191dcc20f11d3eb3135197d55be5ceac95d0fa8f12968609d0810b00b5`.

This task changes message transport and its observation, not robot code, engineering acceptance, run permission,
role labels, Herdr server version, model selection or pane lifetimes. The hub-only guard stays in place.
There is no new delegation of p4's acceptance or p6's planning responsibility. No mass resend of old instructions.

## Failure evidence and change

The prior-art guard found six entries and two blocker contexts. CONTROLS_20260906.md:48-73 describes the old
folded-paste gate, uncertain delivery states and freeze. The user instruction above is the new directive.
At 09:50 the sender ledger contained ten 09-20 post-paste foreign-text holds; **all ten had a ghost suggestion
at the pre-send check**. A stale rendered suggestion can itself cause that post-send classifier to hold before
Enter. Those records do not prove that ten other senders inserted text. The regression suite reproduces the
failure with a suggestion that remains visible after the paste call.

The repair reuses the installed Herdr 0.9.0 skill's documented `agent prompt`: text plus encoded Enter in one
ordered submission. It avoids the old separate paste, rendering wait, folded-line-count test and keypress.
It also:

- Reads the visible viewport and rechecks each recipient's session, role, status and composer immediately before
  submission. A new draft or a working recipient without `--queue` causes a recorded hold with no submission.
- Serializes this sender's send/resend commands using a nonblocking lock on the existing `.floor` file.
- Persists submission intent before touching a terminal. Timeout, exception or an absent destination record
  stays uncertain and cannot become an automatic completion retry.
- Completes only affirmatively never-submitted legs. Legacy post-paste holds remain operator-review items.
- Allows a ready recipient to receive a fan-out while a busy recipient remains held; return code 2 still exposes
  partial completion. The original shared message bytes and fan-out header stay intact.
- Adds `pending [--id ID]`, a read-only, **recorded-only** list with separate never-submitted and uncertain legs.
  A pending list is not a claim that the recipient has not read the artifact by another route.

The transcript classifier remains the delivery authority. Command success, a message visible in a composer,
an enqueue record and engineering acceptance remain different facts. `--queue` still requires the existing
same-matter assertion; the new transport's live queue behavior must be observed before relying on it.

## Validation and rollout

`test_hub_send.py` replaces every terminal subprocess with a fake and rejects any accidental real process.
Run from the shared repo using `./isaaclab.sh -p <worktree>/.../test_hub_send.py`.
Set `HUB_SEND_UNDER_TEST` to the frozen script to demonstrate the same regressions without the fix.
The 14-case candidate run passes; the baseline exposes the old partial-paste and stale-recipient failures.
Formatting and staged-file checks are recorded below before landing.

The p18 rollout checkpoint is one current, useful message to an available recipient, preferably p6:

1. Read this task, code and checks; use the repaired sender after its landing is identified.
2. Run `pending` and `verify` as observations. Do not replay the backlog wholesale: many older instructions
   have already been superseded or read from bodies/.
3. Deliver a fresh checkpoint referring to the latest committed court/verifier artifacts. Capture its message
   ID, destination session, transcript evidence and resulting state. If the result is uncertain, observe it;
   do not send the bytes again or press Enter over unknown input.
4. Obtain the recipient's receipt/disposition. For p6, ask for the current artifact pointers to be reflected
   in the planning record, preserving the distinction between landed, independently verified and accepted.
5. Return that disposition to the source/record. A one-way submission does not close this task.

At subsequent ordinary checkpoints, p18 reviews pending delivery work, records receipts/dispositions and returns
unresolved conditions to the source. p6 updates its surfaces from the named artifacts. Avoid standalone ACK
storms: an ordinary result can carry the receipt and state-record pointer together.

## Explicit limits

The local lock excludes overlapping uses of this sender, not the human or every other terminal client.
Herdr does not offer an atomic compare-composer-and-submit operation in the installed CLI. A human input or
session change in the final read-to-submit interval remains possible. This repair reduces that interval and
removes the observed post-paste failure mode; it does not promise exactly-once transport under every race.
Old HELD/UNKNOWN records are not rewritten or silently called delivered. `resend` remains an explicit new-send
operation and is not used for automatic recovery. A receipt never authorizes a controller or simulation run.

## Validation record (10:02 JST)

The candidate passes all 14 isolated cases. Against the frozen script the same suite gives seven assertion
failures and four errors (three cases pass). Missing new helper/command errors are not claimed as reproduced
historical incidents. The behavioral baseline failures include stale suggestion rendering, changed recipient
or draft, and all-held fan-out. The tests reject any unmocked subprocess; no test sends to a real terminal.
Logs: `/tmp/thread-hub-delivery-tests-fixed.log` and `/tmp/thread-hub-delivery-tests-baseline.log`.

`./isaaclab.sh -f` ran before and after staging in the isolated worktree. Both repository-wide checks failed on
pre-existing E501, historical spelling and other baseline errors. No unrelated formatter edits will be included.
In particular, the two trailing spaces in the old CONTROLS viewport measurements must be preserved: their
recorded line lengths are evidence. That historical file is not part of this repair.
The applicable file-scoped hooks passed on the second pass after formatting the new tests' two long lines.
Logs: `/tmp/thread-hub-delivery-format-1.log`, `/tmp/thread-hub-delivery-format-2.log`,
and `/tmp/thread-hub-delivery-targeted-2.log`. Final staged hooks follow this record.

Read-only live observations at 10:01:24 JST: the new visible-viewport reader classified 15 existing agent panes,
holding the working panes and the draft/paste composers. It sent nothing. The pending view of the live journal
reported 111 never-submitted recipient legs and 12 uncertain legacy post-paste legs. These are recipient legs,
not 123 engineering tasks, and the view says recorded-only; artifacts may already have been read through bodies/.

Live rollout remains a separate observation until p18 returns the message ID, destination readback and the
recipient's disposition/state-record pointer. The p19 review notice was received in p18's transcript at line
45941; its lifecycle wait timed out, so it was not resent. This is not the repaired sender's live acceptance.

## Independent-check expectations (before p18's execution; candidate already exists)

Order is explicit: these expectations are recorded after candidate implementation and before p18's independent
execution, not claimed as a pre-implementation blind registration. Their basis is the user's reliability
request, the installed Herdr skill, and the existing no-duplicate/readback rules, rather than observed success.

| ID | Trigger | Required observation |
|---|---|---|
| E1 | Available recipient, including dim suggestion | One agent-prompt call; exact stored body; destination record required for DELIVERED |
| E2 | Recipient changes session/status or has a real draft after initial fan-out check | No terminal call; explicit never-submitted hold |
| E3 | Transport exception or missing destination record | Durable intent and uncertain state; send --id cannot repeat it |
| E4 | Working recipient without --queue | No submission |
| E5 | One busy CC and one available recipient | Available recipient receives; busy leg remains visible; result is partial |
| E6 | Competing sender uses the same floor lock | Second sender submits nothing; no ID is allocated |
| E7 | pending / read-only inspection | No file write, terminal write or sender lock; historical post-paste holds remain uncertain |
| E8 | Delivery is followed by recipient disposition | p18 records readback; p6 records artifact pointers and returns that pointer; no inferred engineering acceptance |

p18's 10:02:40 review confirms custody and agrees with the diagnosis, intent journal, completion boundary,
partial fan-out, lock and pending command. Requested follow-ups are live queue behavior, visible-composer
coverage, the possible 29-byte paste wrapper, test execution and compatibility with its read scripts.
Visible-composer coverage was observed read-only at 10:01:24 above. The wrapper must be handled by the unchanged
exact-substring transcript predicate, not a guessed prefix length. Initial rollout uses an idle recipient;
working-recipient --queue is outside that live acceptance until separately observed. p18 can run its own
isolated checks and the supplied tests; no new user permission is needed for this already requested repair.

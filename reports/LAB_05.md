# Assignment 5 · The autonomy policy, the gate, the stop button

Model: Google Gemini 3.5 Flash Lite, the same for every real run.

## Part A · The policy, in the hook

**The ranking.** One row per action and circumstance, every action at least once.

| Action | Circumstance | Undo path | Would anyone notice? | Blast radius | Column |
|---|---|---|---|---|---|
| read_issue, search_repo, read_file, run_tests | all | no change to undo | yes | narrow, internal | independent |
| apply_label | all | remove_label | yes | narrow, public | independent |
| close_issue | all | reopen_issue | yes | narrow, public | independent |
| post_comment | agent opened or quiet human thread | none | yes | narrow | independent |
| post_comment | human active in last hour | none | yes | wide, active public thread | approval |
| open_pr | all | close_pr | yes | wide, public | approval |
| push_commit | unprotected branch | none | yes | wide | approval |
| push_commit | protected branch | none | yes | wide | prohibited |
| merge_pr | all | none | yes | wide | prohibited |

- I would remove merge_pr. Triage does not need it and a bad merge has no compensation here.
- Prohibiting merge and protected-branch push gives up speed, but keeps final integration with a maintainer.

**The replay of 2026-08-04.**

| Column | Action class | Calls |
|---|---|---|
| independent | read/search/read file | 440 |
| independent | apply_label | 40 |
| independent | post_comment/agent_opened | 22 |
| approval | open_pr | 6 |
| approval | post_comment/human_active | 9 |
| prohibited | merge_pr | 2 |
| prohibited | push_commit/protected | 1 |

- Prompts per day: 15
- Seconds per prompt, at ten minutes a day: 40

## Part B · A gate that gets read

**One rendered screen**, pasted as bin/review showed it:

```
APPROVAL: open_pr
Run: planned-4302-s01-39f4e2

Dry run:
{"branch":"repomind/issue-4302","base":"develop","title":"Support decimal commas...","body":"File: src/util/money.ts..."}

Harness facts:
{"issue":4302,"issue_opened_by_agent":false,"minutes_since_human_comment":20.1,
 "branch_protected":false,"target_created_by_agent":true}
```

**Your decisions.**

| | All | On the irreversible, wide-reaching classes (name them) |
|---|---|---|
| Decisions | 17 | 2 |
| Approval rate | 1.0 | 1.0 |

| Action class | Decisions | Median seconds |
|---|---|---|
| open_pr | 15 | 16.0 |
| post_comment/human_active | 2 | 18.8 |

- The 100% rate alone is not enough to call the gate good. The day had no planted bad request. The 16.0s and 18.8s medians show I spent time reading both classes, but this is still a small sample.
- **The plan review.** One review covers open_pr and active-thread comment for a run. A changed plan is reviewed again. It reduces the replay estimate from 15 to 12 prompts. The recorded day has no revisions, so the estimate leaves their extra reviews out and is a floor.

## Part C · Escalation, a stop button, and rollback

**Your escalation.** The named signals are failed verification, memory contradiction,
an uninterpretable result, and the same blocked step three times. The packet records
what was attempted, why it stopped, and what the reviewer must decide. The timeout is
300 seconds. No answer holds the run; it never becomes approval. The daily cap is
three escalations, within the same ten-minute reviewer budget. Hitting the cap is
logged and still holds the run.

| Moment | What happened | Escalated? | Packet | Expected |
|---|---|---|---|---|
| A | Tests failed before push; the run wrote a packet and stopped. | yes | `escalations/<run_id>.json` | no push |
| B | Both searches were empty, recorded not determined, and retried. | no | none | comment posted |
| C | Label doubt was not a named signal; the reversible label proceeded. | no | none | comment posted |

**The stop, against five conditions.**

| Condition | What you built | Your evidence |
|---|---|---|
| Watched | A live notification is sent at run start. | It precedes the first remote write. |
| Fast | The hook checks stop before every tool call. | 10 stops: median 3.081s, largest 4.771s. |
| Durable | The effective stop saves a checkpoint; resume lifts it. | All 10 resumed without duplicate writes. |
| Safe | The current call may finish; completed writes stay recorded. | Checkpoints contain completed calls and keys. |
| Outside the agent | The registry hook refuses the next call. | No remote write occurred before resume. |

- Safe is partial. A call already running finishes and is recorded. If it is destructive, stop cannot undo it; rollback only compensates supported writes.

**Rollback** of run `planned-4191-s01-e8add9`:

| Write | Undone by | Or none |
|---|---|---|
| post_comment comment-22 | | none |
| open_pr pr-21 | close_pr | |
| apply_label docs | remove_label | |

- Cancel: "stop now: the label, the comment and the commit stay." Interrupt: "state saved; step 4 runs with a person's answer." Rollback: "steps 3, 2, 1 undone in reverse; mostly not available." This stop is an interrupt because it saves state and resumes later.

## Part D · Tell readers an agent wrote it

- The line: `This comment was written by RepoMind, an automated AI agent. Contact a Ledgerline maintainer for help.`
- A comment without the line is refused as `disclosure` in `logs/hook.jsonl`.

## AI assistance

I used Codex to implement the policy, hook, scripts, and first report draft. I checked the code with the unit tests, scripted moments, replay output, and `make check-05`.

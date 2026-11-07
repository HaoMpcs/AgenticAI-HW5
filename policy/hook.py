from __future__ import annotations

import fnmatch
import json
from pathlib import Path

import yaml

from harness.clock import now
from harness.reviewer import Reviewer
from harness.roles import action_of
from policy.stop import StopRequested, active, append as stop_event

ROOT = Path(__file__).resolve().parents[1]
DISCLOSURE = "This comment was written by RepoMind, an automated AI agent. Contact a Ledgerline maintainer for help."
TIMEOUT_S = 300


def action_class(action: str, facts: dict) -> str:
    if action == "post_comment":
        if facts.get("issue_opened_by_agent"):
            return "post_comment/agent_opened"
        minutes = facts.get("minutes_since_human_comment")
        return "post_comment/human_active" if minutes is not None and minutes < 60 else "post_comment/human_quiet"
    if action == "push_commit":
        return "push_commit/protected" if facts.get("branch_protected") else "push_commit/unprotected"
    return action


def load_policy(root: Path = ROOT) -> dict:
    return yaml.safe_load((root / "policy" / "autonomy.yaml").read_text())


def place(action: str, facts: dict, root: Path = ROOT) -> tuple[str, str]:
    cls = action_class(action, facts)
    policy = load_policy(root)
    for column in ("independent", "requires_approval", "prohibited"):
        if cls in policy[column]:
            return cls, column
    raise ValueError(f"unplaced action class {cls}")


def _append(path: Path, line: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as fh:
        fh.write(json.dumps(line, default=str) + "\n")


def _refuse(ctx, action, cls, column, reason, args):
    root = Path(getattr(ctx.tracker, "root", ROOT))
    _append(root / "logs" / "hook.jsonl", {"at": now(), "run_id": ctx.run_id,
            "action": action, "action_class": cls, "column": column, "reason": reason, "args": args})
    return reason


def _boundary(ctx, facts: dict) -> bool:
    path = Path(getattr(ctx.tracker, "root", ROOT)) / "policy" / "rules.jsonl"
    if not path.exists():
        return False
    for raw in path.read_text().splitlines():
        rule = json.loads(raw)
        if rule.get("run_id") != ctx.run_id or rule.get("effect") != "deny":
            continue
        if any(fnmatch.fnmatchcase(p, rule["path"]) for p in facts.get("paths") or []):
            return True
    return False


def make_hook(ctx):
    def autonomy_hook(name: str, args: dict):
        root = Path(getattr(ctx.tracker, "root", ROOT))
        action = action_of(name)
        if active(root, ctx.run_id):
            stop_event(root, ctx.run_id, "effective", action=action)
            return _refuse(ctx, action, action, None, "stopped", args)
        facts = ctx.tracker.facts(ctx.run_id, action, args, ctx.issue)
        cls, column = place(action, facts, root)
        if _boundary(ctx, facts):
            return _refuse(ctx, action, cls, None, "boundary", args)
        if action == "post_comment" and DISCLOSURE not in str(next((v for k, v in args.items() if k == "body"), "")):
            return _refuse(ctx, action, cls, None, "disclosure", args)
        if column == "prohibited":
            return _refuse(ctx, action, cls, column, "prohibited", args)
        if column == "requires_approval":
            request = {"run_id": ctx.run_id, "action": action, "action_class": cls,
                       "args": args, "facts": facts, "kind": "approval"}
            answer = Reviewer.from_env(root).ask(request, TIMEOUT_S)
            decision = answer["decision"] if answer else "none"
            reviewer = Reviewer.from_env(root)
            _append(root / "logs" / "approvals.jsonl", {"at": now(), **request,
                    "decision": decision, "seconds": answer.get("seconds") if answer else None,
                    "reviewer": answer.get("reviewer", "scripted") if answer else "scripted",
                    "mode": answer.get("mode", reviewer.mode) if answer else reviewer.mode})
            if decision != "approve":
                return _refuse(ctx, action, cls, column, "declined" if decision == "deny" else "no_answer", args)
        return None
    return autonomy_hook

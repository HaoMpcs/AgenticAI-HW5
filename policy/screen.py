from __future__ import annotations

import json

from harness.tracker import Tracker


def render(request: dict) -> str:
    facts, args = request.get("facts") or {}, request.get("args") or {}
    lines = [f"{request.get('kind', 'approval').upper()}: {request.get('action_class')}",
             f"Run: {request.get('run_id')}", "", "Dry run:", json.dumps(args, indent=2, ensure_ascii=False),
             "", "Harness facts:", json.dumps(facts, indent=2, ensure_ascii=False)]
    issue = facts.get("issue")
    if issue:
        try:
            thread = Tracker().issue(issue)
            lines += ["", "Issue thread:", thread.get("text") or json.dumps(thread, ensure_ascii=False)]
        except Exception:
            pass
    return "\n".join(lines)

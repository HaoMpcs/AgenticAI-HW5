from __future__ import annotations

import json
from pathlib import Path

from harness.clock import now


class StopRequested(Exception):
    pass


def path(root: Path) -> Path:
    return root / "logs" / "stops.jsonl"


def append(root: Path, run_id: str, event: str, **fields):
    target = path(root)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a") as fh:
        fh.write(json.dumps({"run_id": run_id, "event": event, "at": now(), **fields}) + "\n")


def active(root: Path, run_id: str) -> bool:
    target = path(root)
    events = [json.loads(x) for x in target.read_text().splitlines() if x.strip()] if target.exists() else []
    mine = [x for x in events if x.get("run_id") == run_id and x.get("event") in ("requested", "lifted")]
    return bool(mine and mine[-1]["event"] == "requested")

from __future__ import annotations

import json

from harness.clock import now
from harness.formats import BOUNDARY
from harness.inbox import drain


class InboxClient:
    """Drain user messages immediately before every model request."""

    def __init__(self, client, ctx):
        self._client, self._ctx = client, ctx

    def create(self, **request):
        user_messages = []
        for message in drain(self._ctx):
            match = BOUNDARY.fullmatch(message["text"])
            if match:
                path = self._ctx.root / "policy" / "rules.jsonl"
                path.parent.mkdir(parents=True, exist_ok=True)
                with path.open("a") as fh:
                    fh.write(json.dumps({"run_id": self._ctx.run_id, "effect": "deny", "path": match.group(1),
                                         "stated_at": message.get("delivered_at") or now(),
                                         "message": message["text"]}) + "\n")
            else:
                user_messages.append({"role": "user", "content": message["text"]})
        if user_messages:
            request["messages"] = [*request.get("messages", []), *user_messages]
        return self._client.create(**request)

    def __getattr__(self, name):
        return getattr(self._client, name)

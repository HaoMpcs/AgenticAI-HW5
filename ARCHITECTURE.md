# ARCHITECTURE.md · RepoMind on the seven layers

For each layer: what does this job, and where is it enforced. Cite code as a file
path and line number joined by a colon, inside backticks; a checker opens every
reference (`checks/FORMATS.md`, section 8). A layer held only by a sentence in a
prompt (any file under `prompts/`) is **EMPTY**, and so is a layer nothing does
yet. Status is one of: present, partial (say what is missing), or **EMPTY**. Each
assignment brings this file up to date.

What each layer is for (Lecture 1, slides 42 to 44):

- **Model**: reasoning, choosing tools, generating text.
- **Harness**: runs the loop, builds each prompt, trims old history.
- **Tools**: where the system acts on the world.
- **Memory & State**: what survives a step, a session, a restart.
- **Control & Policy**: what the system may do, and when it must ask.
- **Observability**: a step-by-step record of what it did.
- **Evaluation**: measuring quality, before and after release.

The table below is RepoMind as Assignment 4 left it.

| Layer | What does this job | Where it is enforced | Status |
|---|---|---|---|
| Model | The configured model, called only through the metered client | `harness/client.py:150` | present |
| Harness | The loop checks bounds, validates a plan, and executes only planned steps | `agent/loop.py:38`, `ways/planned.py:311`, `ways/planned.py:397` | present |
| Tools | Ten namespaced tools behind one registry: every call checked at the boundary before it runs; every write keyed by the harness, checked before each attempt and read back after a timeout; every attempt in the call record | `tools/__init__.py:167`, `tools/__init__.py:257`, `tools/__init__.py:266`, `tools/__init__.py:283`, `tools/__init__.py:322` | present |
| Memory & State | A checkpoint after each file read and before each write, sync, and a resume from the last one; a store of dated records with their origin, read before the first search and written once at the end of a run | `ways/planned.py:338`, `ways/planned.py:351`, `ways/planned.py:220`, `ways/planned.py:240`, `state/checkpointer.py:55`, `state/store.py:96` | present |
| Control & Policy | The hook classifies each call from harness facts, enforces boundaries and disclosure, prohibits unsafe classes, and asks before gated classes | `policy/hook.py:19`, `policy/hook.py:69`, `tools/__init__.py:153` | present |
| Observability | Traces and call records show every step; live notifications make writable runs visible | `agent/loop.py:50`, `ways/planned.py:723`, `harness/notify.py:26` | present |
| Evaluation | The grounded check reads the tracker, never the agent | `eval/check_triage.py:7` | partial: offline only |

**Empty layers: 0 of 7**. Evaluation remains partial because it is offline only.

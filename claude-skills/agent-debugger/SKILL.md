---
name: agent-debugger
description: Use when an agent/Claude Code run failed or went off-target and you want a root-cause diagnosis from its trace — diagnoses irrelevant recall, buried context, task misunderstanding, and off-target answers with evidence and concrete fixes. Triggers on "为什么这个 agent 答偏了", "debug this agent run", "复盘这次失败", "诊断 trace".
---

# agent-debugger

Diagnose why a single agent run failed or answered off-target, from its Claude Code transcript. Each finding is an evidence card: severity, the exact trace evidence, a root cause, and a concrete fix.

## How to run it

The engine is a CLI installed in a project venv. Always invoke it by ABSOLUTE PATH (it is not on PATH):

```bash
/Users/liancong/agent-debugger/.venv/bin/agent-debugger analyze <TRANSCRIPT.jsonl> \
  --accept "验收点1" --accept "验收点2"
```

Requires the `ANTHROPIC_API_KEY` env var (the detectors call the Anthropic API for attribution).

## Workflow for the agent

1. **Find the transcript.** Claude Code sessions live at `~/.claude/projects/<project-slug>/<session-id>.jsonl`. If the user doesn't give a path, list candidates:
   ```bash
   ls -lt ~/.claude/projects/*/*.jsonl | head
   ```
   and confirm which run they mean.

2. **Derive acceptance points.** `--accept` is one flag per acceptance point of the ORIGINAL request (used by detector 10 「答非所问」). Read the user's original ask, break it into checkable points, and pass each with its own `--accept`. Omit `--accept` entirely to skip detector 10.

3. **Run** the CLI (absolute path above).

4. **Relay the report.** Present the evidence cards to the user and lead with the overall card's primary root cause + the top fix.

## What it checks (MVP)

| Code | Failure mode | Signal |
|------|--------------|--------|
| 1 | 召回无关 | per-chunk relevance score × token share |
| 2 | 关键上下文被淹没 | constraint position in context (middle band) + token share |
| 4 | 任务理解跑偏 | semantic drift: original request vs first action |
| 10 | 答非所问 | acceptance points uncovered by final output |

## Scope & source

MVP consumes Claude Code transcripts only. Source lives at `~/agent-debugger`
(spec/plan under `docs/superpowers/`). To support another framework, add an
adapter that produces the standard `Trace` (`src/agent_debugger/schema.py`);
the engine is unchanged.

---
name: work-retrospective
description: Use when reviewing recent work history (weekly/monthly retrospective, "what should I automate?", "回顾最近的工作/复盘") to find repetitive, time-consuming, or error-prone workflows worth packaging into skills, subagents, or automations. Also use when a Codex-flavored retrospective prompt names Codex sessions / Memories / rollouts / Chronicle but you are running in Claude Code and must translate the evidence sources.
---

# Work Retrospective → Package Reusable Assets

## Overview
Mine your own recent work history for recurring manual workflows, then package only the high-confidence, genuinely-missing ones into the lightest sufficient form. Default to NOT creating — a mature setup already covers most patterns.

**Core principle:** Evidence before assets. No new asset without 2+ real occurrences AND proof nothing already covers it.

## When to Use
- Periodic retrospective (monthly/weekly) over your own work
- "What repetitive work should I turn into a skill / agent / automation?"
- A Codex-flavored prompt cites Codex sessions / Memories / rollouts / Chronicle — translate to the Claude Code sources below before answering

**When NOT:** packaging a one-off task, or a project-specific code convention (that belongs in CLAUDE.md or a `cs-decide` doc, not a skill).

## Evidence Sources (Claude Code equivalents)
Codex prompts cite Codex-only sources. Map them, then gather across the window (default 30 days), dedupe by theme, and count occurrences per theme:

| Codex source | Claude Code equivalent | How |
|---|---|---|
| Codex sessions / task summaries | **claude-mem** observations | `mcp__plugin_claude-mem_mcp-search__search`, then `timeline` / `get_observations`; session boot also injects a recent-context index |
| Codex Memories / rollouts | **episodic-memory** (past conversations) | `mcp__plugin_episodic-memory_episodic-memory__search`, then `read` |
| Chronicle | claude-mem `timeline` + `git log` | lead-finding only; confirm details in the source system |
| Existing skills / agents / automations | local inventory | `ls ~/.claude/skills` (+ plugin skills); `ls ~/.claude/agents`; `CronList` & `/schedule`; project memory dir + CLAUDE.md |

## Selection Criteria (ALL must hold)
- Occurred ≥2 times, OR clearly recurs with non-trivial per-repeat cost
- Stable input + repeatable process + clear output / stop condition
- Material gain in speed, quality, consistency, or reliability
- **Not already covered** by an existing skill, agent, automation, or convention doc

## Form Decision
| Signal | Form |
|---|---|
| Reusable playbook / technique across projects | **Skill** |
| Bounded, delegable expert or research role | **Subagent** |
| Time- or event-triggered check / report / monitor | **Automation** (`/schedule`, cron) |
| Existing asset almost covers it | **Extend** it (e.g. add a `cs-trick`, a CLAUDE.md rule) |
| Sparse / vague / sensitive / thin evidence | **Skip** |

## Output Structure
1. **Candidate table** — workflow · evidence + dates · frequency / confidence · recommended form · why / why-not
2. **Create** only the high-confidence + genuinely-missing items; keep them focused, sourced, verifiable
3. **Summary** — what you created or extended · what you deliberately skipped · what needs more evidence

## Common Mistakes
- **Over-creating.** Mature setups (CodeStable `cs-*`, superpowers, OMC) already cover most workflows — inventory first, default to skip.
- **Packaging a project convention as a skill.** A codebase rule goes in CLAUDE.md or a `cs-decide` convention doc, not a global skill.
- **Trusting the index alone.** claude-mem titles are leads; fetch full observations / read conversations before asserting a pattern.
- **Treating one templated run as proof of recurrence** — confirm the workflow actually repeats, not just that the prompt looks reusable.
- **Spawning agents to "test" the new skill** when the user has said not to spawn agents — do a gap self-check instead.

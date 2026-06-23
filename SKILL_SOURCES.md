# Skill Sources

This repository backs up three local skill roots from this machine.

## Sources

- `codex-skills/`
  - Source: `~/.codex/skills`
  - Direct `SKILL.md` files: 34
  - Role: Codex personal skills loaded by the Codex app/runtime.

- `agents-skills/`
  - Source: `~/.agents/skills`
  - Direct `SKILL.md` files: 37
  - Role: shared local agent skills. Codex can also load this root in the current setup.

- `claude-skills/`
  - Source: `~/.claude/skills`
  - Direct `SKILL.md` files: 40
  - Symlinks to `agents-skills/`: 32
  - Resolved `SKILL.md` files when following symlinks: 72
  - Role: Claude Code user skills. Some entries reuse `~/.agents/skills` through symlinks.

## What Was Not Copied

- `~/.claude/plugins/cache`
- `~/.claude/plugins/marketplaces`
- `~/.claude/backups`
- `node_modules`, `.DS_Store`, zip archives, and other local cache artifacts

Those paths contain installed plugin caches, marketplace clones, historical backups, or generated dependencies. They are not the current user skill root and would add duplicate third-party content.

## Main Differences

- Codex skills are mostly task/tool skills for this Codex environment, such as React Doctor, Agent Guard, Playwright, image-to-code, and local workflow helpers.
- Agents skills are shared local workflow skills, with many CodeStable (`cs-*`) and frontend/browser automation skills.
- Claude skills are Claude Code specific user skills and orchestration helpers. They include Claude-oriented commands such as setup, trace, deep-dive, team/session helpers, and OMC-related workflows.
- Claude skills reuse many `agents-skills` entries through symlinks. In this repo those links point to `../agents-skills/<skill-name>` so the backup remains portable.

## Overlap

- `codex-skills` and `agents-skills` overlap on `learning-skill`.
- `codex-skills` and `claude-skills` overlap on `agent-guard-plan` and `learning-skill`.
- `agents-skills` and `claude-skills` overlap heavily through Claude symlinks, especially `browser-*`, `cs-*`, `find-skills`, `learning-skill*`, `performance-review`, and `vercel-react-best-practices`.

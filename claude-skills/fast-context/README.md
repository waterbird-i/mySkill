# Fast Context Skill

[![skills.sh](https://skills.sh/b/oulkurt/fast-context-skill)](https://skills.sh/oulkurt/fast-context-skill)

Fast Context Skill is an Agent Skill and CLI adaptation of [`SammySnake-d/fast-context-mcp`](https://github.com/SammySnake-d/fast-context-mcp).

It is a fork-style rewrite of the original MCP project: the Windsurf Devstral semantic search core is vendored from upstream `v1.3.0-beta.2`, while the MCP server wrapper is removed. Any Skills-compatible agent that can run local scripts can use this Skill; Codex is one supported install target, not a requirement.

## Prerequisites

- Install [Windsurf desktop](https://windsurf.com/) and log in once.

That is the only setup. The Skill reads the API key directly from Windsurf's local state DB (`state.vscdb`), so you do **not** need to keep Windsurf running, copy a key, or set any environment variable. Manual key handling is only required if you do not have Windsurf desktop installed (for example on CI or a remote server) — see [Windsurf API Key](#windsurf-api-key).

## Quick Start

1. Install the Skill (interactive — picks up agent targets from your local `skills` CLI):

```bash
npx skills add oulkurt/fast-context-skill
```

For a fully non-interactive install to every supported agent target:

```bash
npx skills add oulkurt/fast-context-skill --skill fast-context -a '*' -y
```

2. (Optional) Verify the Windsurf key is auto-discovered:

```bash
npx --yes github:oulkurt/fast-context-skill --check-key
```

3. Use Fast Context:

Invoke `$fast-context` or your agent's skill invocation convention, or run the CLI directly:

```bash
npx --yes github:oulkurt/fast-context-skill \
  --project "/absolute/path/to/project" \
  --query "Where is authentication implemented?"
```

## What Changed From The MCP Repo

- Keeps the upstream semantic search loop that talks to Windsurf Devstral.
- Keeps local command execution helpers for `rg`, file reads, tree output, and context gathering.
- Removes the MCP server entry point from the runtime path.
- Adds an agent-friendly `SKILL.md` workflow.
- Adds `scripts/fast-context-search.mjs` as the direct CLI entry point.
- Adds npm packaging for direct CLI use.

## Install With skills CLI

One-command install via the open `skills` CLI:

```bash
npx skills add oulkurt/fast-context-skill --skill fast-context -y
```

To install to every agent target supported by your local `skills` CLI:

```bash
npx skills add oulkurt/fast-context-skill --skill fast-context -a '*' -y
```

Use the `-a` flag when you want to target a specific agent supported by your `skills` CLI version. For Codex:

```bash
npx skills add oulkurt/fast-context-skill --skill fast-context -a codex -y
```

For a global Codex install specifically:

```bash
npx skills add oulkurt/fast-context-skill --skill fast-context -a codex -g -y
```

Manual install is agent-specific: clone this repository into the skill directory your agent reads, then run `npm install` from that directory. For Codex:

```bash
git clone https://github.com/oulkurt/fast-context-skill.git ~/.codex/skills/fast-context
cd ~/.codex/skills/fast-context
npm install
```

Then invoke `$fast-context` or your agent's skill invocation convention. The Skill instructs the agent to run the bundled script from the installed skill directory, for example:

```bash
node /path/to/installed/fast-context/scripts/fast-context-search.mjs \
  --project "/absolute/path/to/project" \
  --query "Where is authentication implemented?"
```

## Use As A CLI

From a clone:

```bash
npm install
node scripts/fast-context-search.mjs \
  --project "/absolute/path/to/project" \
  --query "Where is the database connection pool configured?"
```

From GitHub without cloning:

```bash
npx --yes github:oulkurt/fast-context-skill \
  --project "/absolute/path/to/project" \
  --query "Where is the database connection pool configured?"
```

## Windsurf API Key

This project still depends on Windsurf's Devstral backend. It replaces the MCP layer, not the Windsurf backend.

**Most users can skip this section.** If you have [Windsurf desktop](https://windsurf.com/) installed and have logged in once, the script auto-discovers the key from `state.vscdb` on every run — no env var, no copy/paste, and Windsurf does not need to be running.

Manual key handling is only needed when:

- You do not have Windsurf desktop installed (CI, remote server, container).
- You want to override the auto-discovered key with a different one.
- Auto-discovery fails and you need to verify or inspect the value.

No-clone one-liners:

```bash
npx --yes github:oulkurt/fast-context-skill --check-key   # verify, masked output
npx --yes github:oulkurt/fast-context-skill --print-key   # print full key
eval "$(npx --yes github:oulkurt/fast-context-skill --key-env)"   # export to current shell
```

To persist the key across shells (only do this if you cannot rely on Windsurf desktop), add the export to your shell rc file, for example:

```bash
echo "export WINDSURF_API_KEY=$(npx --yes github:oulkurt/fast-context-skill --print-key)" >> ~/.zshrc
```

After installing the Skill, the same commands work against the installed script path:

```bash
node /path/to/installed/fast-context/scripts/fast-context-search.mjs --check-key
node /path/to/installed/fast-context/scripts/fast-context-search.mjs --print-key
eval "$(node /path/to/installed/fast-context/scripts/fast-context-search.mjs --key-env)"
```

For a project install, that path is `.agents/skills/fast-context/scripts/fast-context-search.mjs`. For a global Codex install, it is usually `~/.codex/skills/fast-context/scripts/fast-context-search.mjs`. From a repository clone, use `scripts/fast-context-search.mjs` directly.

Treat the value like any other API secret:

- Do not commit it.
- Do not paste it into GitHub issues, README files, workflows, or logs.

## Development

```bash
npm install
npm test
npm pack --dry-run
```

## Attribution

This repository vendors and adapts code from [`SammySnake-d/fast-context-mcp`](https://github.com/SammySnake-d/fast-context-mcp), originally licensed under MIT. The vendored upstream license is preserved at `scripts/lib/LICENSE.fast-context-mcp`.

This project is not affiliated with Windsurf.

## other
Thanks https://linux.do

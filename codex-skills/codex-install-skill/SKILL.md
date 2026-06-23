---
name: codex-install-skill
description: Install or validate Codex skills, plugins, plugin-marketplace packages, and MCP integrations. Use when the user asks to install a skill globally, install PM-SKILL or another Codex plugin, add an MCP server, migrate a Claude-style skill into Codex, or verify whether a newly installed tool is actually discoverable and usable.
---

# Codex Install Skill

## Goal

Turn "install this Codex capability" into a verified local asset.

Do not stop at "files exist". Distinguish:

- Registered: config or files were written.
- Installed: Codex can list or load the package.
- Enabled: the plugin/MCP/skill is active for new sessions.
- Auth/policy ready: external service login or tenant policy allows real use.
- Smoke-tested: a minimal safe command or import proves the runtime path works.

## Source Classification

Identify the requested source before acting:

- Local `SKILL.md` or skill folder.
- GitHub repository path that contains a skill.
- Codex plugin or plugin marketplace package.
- MCP server configuration.
- Existing installed asset that only needs validation or explanation.

Do not assume the repo root is the skill path. Confirm the real directory containing `SKILL.md`.

## Skill Install Flow

1. Read the system installer guidance:
   - `~/.codex/skills/.system/skill-installer/SKILL.md`
2. Determine target directory:
   - Prefer `$CODEX_HOME/skills`.
   - Fall back to `~/.codex/skills`.
3. Check for an existing same-name directory.
   - If it exists, inspect it and stop unless the user explicitly wants an update.
4. For GitHub sources, prefer the installer script:
   - `~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py`
   - Use explicit `--repo`, `--path`, `--ref`, and `--dest` when the tree path is known.
5. If installer download stalls on a large repo, switch to a safer fallback:
   - Use `curl -L` for the archive or sparse checkout.
   - Extract only the target skill directory.
6. For local single-file skills, do minimal Codex compatibility edits only.
   - Keep the original workflow.
   - Remove platform-specific hook or tool claims that are false in Codex.

## Plugin Flow

Use Codex native plugin commands for plugin-like requests.

1. Inspect available commands:
   - `codex plugin --help`
   - `codex plugin marketplace --help`
2. If the user gave a marketplace repo, add it first:
   - `codex plugin marketplace add <owner/repo>`
3. If the user gave a plugin name, list marketplaces and install from the matching marketplace:
   - `codex plugin marketplace list`
   - `codex plugin add <plugin>@<marketplace>`
4. Verify:
   - `codex plugin list`
   - plugin cache directory exists
   - if it provides skills, count `skills/**/SKILL.md`
5. Tell the user that a new Codex session or restart may be required.

## MCP Flow

For MCP requests, do not treat config as proof of usability.

1. Identify whether the user wants a local MCP server, a remote connector, or an app/plugin.
2. Prefer Codex MCP commands if available, such as `codex mcp add`.
3. Verify the layers separately:
   - config entry exists
   - command path or package is available
   - dependency install succeeded
   - auth/OAuth/token state is ready when relevant
   - tenant or policy permits access
   - the MCP tools appear in a new or refreshed session
4. If the MCP cannot appear in the current session without restart, say that clearly.

## Runtime Smoke

Use the smallest safe check:

- Skill folder: `SKILL.md` exists and frontmatter `name` matches.
- Python script skill: install declared requirements only when needed, then import or `--help` smoke.
- Node script skill: use `node <script> --help` or equivalent no-side-effect command.
- Plugin: `codex plugin list` shows installed and enabled.
- MCP: config exists and the expected tool is callable or documented as requiring restart/auth.

## Common Pitfalls

- `CODEX_HOME` is empty: fall back to `~/.codex`.
- GitHub tree URL path is wrong: inspect the real repo path before retrying.
- `skills find` / `skills add` fails on the default registry: retry with `--registry=https://registry.npmjs.org` when appropriate.
- A repo contains multiple skills: ask or infer the exact target from the user's request; do not install the whole repo.
- Zip extraction errors in unrelated directories: verify the target skill directory specifically.
- MCP appears configured but unusable: check auth, tenant policy, and session reload before blaming the config.
- Plugin installed but not visible in this conversation: new sessions may be required.

## Output Contract

End with:

- Source type and target path.
- What was installed or found already.
- Verification commands and results.
- Remaining requirement, if any: restart, auth, policy, dependency, or user confirmation.

Never claim an installed tool is usable unless the relevant verification layer passed.

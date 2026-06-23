# Fast Context Script Contract

## Command

Run semantic repository search without the Fast Context MCP server:

```bash
node /path/to/installed/fast-context/scripts/fast-context-search.mjs \
  --project "/absolute/path/to/project" \
  --query "Where is <feature> implemented?"
```

The script imports vendored Fast Context core files from `scripts/lib/` and calls `searchWithContent()` directly. It uses Windsurf Devstral over the network and obtains credentials from `WINDSURF_API_KEY` or Windsurf's local logged-in database.

## Arguments

Required:

- `--query`, `-q`: Natural-language search query.

Common:

- `--project`, `--project-path`, `-p`: Absolute project root. Defaults to the current working directory.
- `--max-results`: Maximum returned files. Use 3-5 for focused lookup, 10-20 for feature tracing, 15-30 for broad exploration.
- `--max-turns`: Search rounds. Use 1 for quick lookup, 3 by default, 4-5 for deep tracing.
- `--max-commands`: Max local commands the remote search loop may request per round.
- `--tree-depth`: Initial repo map depth. Use 0 for auto, 1-2 for huge repos, 4-6 for small repos.
- `--timeout-ms`: Connect timeout for Devstral requests.
- `--exclude`: Directory or file patterns to omit from tree/search context. May be repeated or comma-separated.
- `--repo-map-mode`: `classic` or `bootstrap_hotspot`.

Hotspot and bootstrap:

- `--bootstrap-tree-depth`
- `--hotspot-top-k`
- `--hotspot-tree-depth`
- `--hotspot-max-bytes`
- `--bootstrap-enabled` / `--no-bootstrap`
- `--bootstrap-max-turns`
- `--bootstrap-max-commands`

Key check:

- `--check-key`: Verify Windsurf key discovery and print only a masked key plus source path. Never prints the full key.
- `--print-key`: Print the full discovered Windsurf key to stdout. Use only on the user's local machine.
- `--key-env`: Print `export WINDSURF_API_KEY='...'` so users can run `eval "$(node scripts/fast-context-search.mjs --key-env)"`.
- `--db-path`: Optional custom Windsurf `state.vscdb` path for key commands.

## Response Expectations

- Relevant files and line ranges are pointers, not proof. Always inspect files locally before editing or making claims.
- Grep keywords are intended follow-up terms for `rg`.
- The `[config]` line reports effective `tree_depth`, `max_turns`, `max_results`, timeout, and excludes. Use it to tune retries.

## Completeness Checklist

Before producing code or project-specific advice, confirm that you have the full definitions and signatures for:

- Entry points and public APIs.
- Core functions, classes, hooks, components, commands, or handlers.
- Types, interfaces, schemas, validators, and configuration.
- Data access, side effects, external calls, and persistence boundaries.
- Callers, consumers, and routing from user-visible behavior to implementation.
- Existing tests, fixtures, helpers, and snapshot or integration coverage.

If any item is unknown and relevant, run another focused Fast Context query or inspect with local search.

## Failure Handling

If Node dependencies are missing, run `npm install` from the installed Fast Context skill directory. If the vendored core files are missing, repair or reinstall the skill. If the search fails because the repository is too large, retry with lower `tree_depth` and more `exclude_paths`. If results are incomplete, retry with a narrower query, higher `max_turns`, or `repo_map_mode: "bootstrap_hotspot"`. If Windsurf authentication fails, run `--check-key`, ensure Windsurf is logged in, or set `WINDSURF_API_KEY` in the environment. If the user asks how to obtain the key, use `--print-key` or `--key-env` and remind them not to commit or share the output.

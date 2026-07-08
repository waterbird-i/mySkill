# mySkill

Personal Codex, agent, and Claude Code skills backup.

## Layout

- `codex-skills/`: symlink to `~/.codex/skills`
- `agents-skills/`: copied from `~/.agents/skills`
- `claude-skills/`: copied from `~/.claude/skills`

## Notes

- Plugin cache, marketplace cache, and backup skills are not included.
- Non-skill local artifacts such as `.DS_Store`, zip archives, and `node_modules` caches are excluded.
- Claude skills may include symlinks to `agents-skills/`; these are rewritten as repo-local relative symlinks.
- See `SKILL_SOURCES.md` for source comparison.

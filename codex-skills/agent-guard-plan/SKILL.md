---
name: agent-guard-plan
description: Use when the user wants an explicit manual agent-guard checkpoint instead of running agent-guard after every code edit. Trigger for requests mentioning agent-guard, guard check, guard checkpoint, 一键触发, 手动校验, or when the user asks Codex to inspect the current worktree and run `agent-guard check --mode worktree`.
---

# Agent Guard Plan

## Purpose

Use this skill as an intentional checkpoint, not as an automatic post-edit hook.

The default behavior is:

1. Inspect the current repo or the requested change scope.
2. Build one shared scope snapshot from that read-only context.
3. Spawn two read-only subagents in parallel and pass both the scope snapshot:
   - `ponytail_ultra_reuse_reviewer`: Ponytail ultra reuse / over-engineering review.
   - `react_doctor_quality_checker`: React Doctor changed-scope quality scan.
4. Run `agent-guard check --mode worktree` immediately in the main agent.
5. Report what was inspected, what command ran, and the merged results.

Keep this workflow lightweight. Do not run heavy TypeScript checks, create tests, or do unrelated cleanup while using this skill.

## Workflow

Use this when the user asks for a manual guard checkpoint or asks to inspect the current worktree with Agent Guard.

Collect read-only context first:

```bash
pwd
git rev-parse --show-toplevel
git status --short
git diff --stat
git diff --name-only
git diff --cached --name-only
```

Build a concise scope snapshot from those outputs and pass it to every subagent:

```markdown
**Scope Snapshot**
- repo root: ...
- status: ...
- diff stat: ...
- changed files: ...
- staged files: ...
- unstaged files: ...
- untracked files: ...
- relevant diff excerpts: ...
```

Include relevant diff excerpts for touched frontend files when the diff is small. For large diffs, include file names, diff stat, and only the hunks needed for the subagent task.

Then spawn these subagents in parallel. They are read-only; they must not edit files. Subagents should trust the scope snapshot as the starting point and only run extra `rg`, `sed`, or package metadata reads when needed to answer their specific task.

### Subagent 1: ponytail_ultra_reuse_reviewer

Use `multi_agent_v1.spawn_agent` with `agent_type: "explorer"` when available.

Task contract:

- Agent name: `ponytail_ultra_reuse_reviewer`
- Task definition: Inspect the current worktree diff with Ponytail ultra intensity. Judge whether the change can be deleted, simplified, or replaced by existing code.
- Execution actions:
  - Use the provided scope snapshot instead of re-running broad diff discovery.
  - Search likely reuse points in `src/utils`, `src/hooks`, `src/contexts`, touched sibling modules, and installed dependencies when relevant.
  - Check for unnecessary abstractions, duplicated logic, speculative code, avoidable state, avoidable effects, and wider-than-needed blast radius.
  - Ask exactly five questions: can it be deleted, is there an existing reuse point, did it add unnecessary abstraction, did it widen shared-component impact, is there a smaller diff.
  - Do not edit files.
- Expected result format:

```markdown
**Ponytail Ultra**
- 结论：通过 / 有问题
- 复用检查：...
- 过度设计风险：...
- 五问结论：...
- 建议：...
```

### Subagent 2: react_doctor_quality_checker

Use `multi_agent_v1.spawn_agent` with `agent_type: "explorer"` when available.

Task contract:

- Agent name: `react_doctor_quality_checker`
- Task definition: Run React Doctor changed-scope quality scan for the current worktree.
- Execution actions:
  - Use the provided scope snapshot for context; do not do manual review beyond command result extraction.
  - Prefer a repo-local `react-doctor` executable if present.
  - Otherwise run the known working fixed-version command for this workstation:

```bash
npx -y --registry=https://registry.npmjs.org react-doctor@0.5.8 --verbose --scope changed
```

  - Do not install dependencies into the project.
  - Do not edit files.
- Expected result format:

```markdown
**React Doctor**
- 命令：...
- 分数：...
- 问题：...
```

Then run from the repository root:

```bash
agent-guard check --mode worktree
```

If `agent-guard` is missing, run:

```bash
command -v agent-guard
```

Then report that the guard entrypoint is unavailable and stop. Do not substitute unrelated checks.

Report in this shape:

```markdown
**执行过程**
- 范围盘点：...
- 范围快照：...
- 并行子代理：
  - `ponytail_ultra_reuse_reviewer`: ...
  - `react_doctor_quality_checker`: ...
- 执行命令：`agent-guard check --mode worktree`

**结果**
- Agent Guard：...
- Ponytail Ultra：...
- React Doctor：...
```

If the user is asking for a future code change rather than validating an existing diff, inspect only the relevant files with `rg`, `sed`, `ls`, or existing project structure before running guard. For frontend work, explicitly mention whether reusable utilities, hooks, contexts, and installed third-party libraries were checked.

## Result Handling

When guard passes, summarize the command and result in one short paragraph.

When guard fails:

- Summarize only actionable findings.
- Map each finding to the likely file or rule.
- Propose a fix plan.
- Ask for confirmation before editing files unless the user already asked to fix failures.
- Prefer scoped lightweight follow-up checks after fixes.
- Rerun `agent-guard check --mode worktree` after fixes when the user asked to fix failures or explicitly asks for another guard pass.

## Boundaries

- Do not run `yarn lint-type`, `yarn typecheck`, `pnpm run typecheck`, `pnpm exec tsc --noEmit`, `npx tsc --noEmit`, or `tsc --noEmit` unless the user explicitly asks.
- Do not create tests when local instructions forbid test code.
- Do not delete, move, or rewrite broad file sets without explicit confirmation.
- Do not treat this skill as an automatic check after every code edit.
- Do not hide broad or risky changes inside vague result wording.

---
name: comate-crrules-reviewer
description: Use for comate-stack-fe CRRules/iCode frontend review, unstaged diff inspection, and narrow UI polish. Trigger when the user asks to inspect CRRules page UI, review unstaged/staged CRRules changes, fix Smart Rules/智能评审规则 dialog details, or apply iCode-only token/icon/permission tweaks.
---

# Comate CRRules Reviewer

## Scope

Use this only for `comate-stack-fe` CRRules/iCode work. It is not a general frontend design skill.

Typical inputs:

- User gives detailed UI instructions for 智能评审规则 / CRRules.
- User asks to review staged or unstaged CRRules changes.
- User asks for minimal fixes around iCode icons, color tokens, hover states, permission gates, sticky scroll, message popovers, or rule list layout.

## Preflight

1. Confirm repo and worktree.
   - `git rev-parse --show-toplevel`
   - `git status --short`
   - `git diff --name-only`
   - `git diff --cached --name-only`
2. Frontend reuse check required by local policy.
   - Search `src/utils`, `src/hooks`, `src/contexts`, and dependency manifests before adding helpers or dependencies.
   - Report the conclusion before editing, even if the answer is "no matching helper found".
3. Read only the relevant CRRules files.
   - Common files: `src/iCode/CRRules/RuleItem.tsx`, `RuleDetailModal.tsx`, `CreateRuleModal.tsx`, `RulesToolbar.tsx`, `MessagePanel.tsx`, `VersionDropdown.tsx`, `StatusBadge.tsx`, `RuleTag.tsx`, `messageCenter.ts`, `styles.ts`, `useRuleEditPermission.ts`, `api.ts`, `index.tsx`.
4. If Semi Design behavior is involved, use `semi-design-guide` first.

## Review Workflow

When the user asks for a review, findings come first:

1. Inspect both staged and unstaged diffs if they are relevant.
2. Check touched files for project-specific UI contract violations.
3. List only actionable findings with file and line references.
4. If no issue is found, say so and name the remaining verification gap.

Do not mix a read-only review with broad refactors. If the user later says "依次动手" or gives explicit fixes, apply them in order.

## Implementation Workflow

1. Split the request into concrete visual contracts.
   - Example: "消息已读/删除按钮 hover 再展示", "搜索框恢复原宽度", "更多 icon 去边框".
2. Prefer existing local pieces.
   - Text overflow: reuse `TextOverflowTooltip` or local overflow helpers.
   - Scrollbar: reuse `thinScrollbarStyle` where already used.
   - Icons: prefer iCode generated icons and `currentColor`; avoid new `@ant-design/icons` in CRRules.
   - Colors: use iCode constants or CSS variables; avoid new inline hex values.
3. Keep permission gates centralized.
   - Reuse `useRuleEditPermission` for list row and detail modal checks.
   - Treat `60003` and `60001` from `apiGetKnowledgeDirectoryTree({kbUuid})` as denied.
   - Direct edit/upload routes still need route-level author/user checks when applicable.
4. Keep layout stable.
   - For internal scroll, ensure the flex/grid chain has `min-height: 0` or `minmax(0, 1fr)`.
   - For full-screen modals, use viewport-safe `100vw` / `100dvh` patterns already present in the file.
   - For sticky toolbar/header/pagination, avoid moving scroll ownership unless the request requires it.
5. Preserve existing interaction contracts.
   - Message popover read/delete actions should be hover-only when that is the current baseline.
   - Restoring a previous width or hover state is a baseline correction, not a new responsive redesign.
6. Keep patches narrow.
   - Do not reformat unrelated code.
   - Do not rename exports unless the user explicitly asks.
   - Do not revert user changes outside the requested scope.

## Validation

Default validation chain:

1. Targeted ESLint for touched files or the smallest touched directory.
2. `git diff --check`.

Do not run full typecheck commands unless the user explicitly asks.

Do not run `agent-guard check --mode worktree` automatically. If the user asks for Agent Guard, use `agent-guard-plan`.

If browser validation is useful but unavailable, report the exact gap and the code-level evidence that was checked instead.

## Output Contract

For implementation tasks, end with:

- Reuse conclusion: what existing utils/hooks/contexts/dependencies were checked.
- Changes: concise list of files and behavior changes.
- Validation: exact commands run and results, or why a check was not run.
- Residual risk: only if something could not be verified.

For review tasks, end with:

- Findings ordered by severity.
- Open questions or assumptions.
- Test/verification gaps.

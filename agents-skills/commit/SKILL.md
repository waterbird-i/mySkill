---
name: commit
description: 按主题分组提交代码变更，严格通过仓库规范检查后再提交或推送，支持可选卡片 ID，禁止 git add . 和 --no-verify
---

# Git Commit 技能

提交当前未 commit 的修改到 git 仓库。

## 不可绕过的质量门禁

- **所有仓库规范检查通过后才能执行 `git commit`。** 不允许先提交、后补检查。
- **执行 push 前必须完成推送前检查，并使用正常的 `git push` 触发 pre-push hook。** hook 失败时不得推送。
- **绝对禁止**在 `git commit`、`git push` 或其他 Git 命令中使用 `--no-verify`。
- **绝对禁止**通过 `HUSKY=0`、`SKIP_*`、临时修改或删除 hooks、忽略退出码等方式绕过检查。
- 检查失败后，先定位并修复本次变更引入的问题，再重新执行完整检查。只有全部检查退出码为 0 才能继续。
- 如果失败来自无关历史问题、环境故障或缺失依赖，必须停止提交或推送并如实报告；不得降低检查标准或伪造通过结果。
- **提交前必须并行派两个 subagent（ponytail 审查者 + agent-guard 审查者）审查待提交 diff**，见「并行 subagent 代码质量审查」。两个审查者都无阻断性问题才能执行 `git commit`。
- 用户要求快速提交、紧急提交或直接 push，也不能覆盖以上门禁。

## 卡片 ID 处理

卡片 ID 仅在用户显式声明时使用（如 `/commit ComateStack-1234`）：
- **用户显式声明了卡片 ID**：commit message 开头加上卡片 ID，格式为 `卡片ID 提交描述`
- **用户未显式声明**：不加卡片 ID，也不需要询问

## 工作流程

### 步骤一：查看未提交修改

执行 `git status --short` 查看所有变更。

分析变更类型：
- M - 已修改
- ?? - 新文件（未跟踪）
- D - 已删除
- R - 重命名

如果没有任何变更，告知用户无需提交并结束。

**重要**：先根据「排除规则」过滤掉不应提交的文件，后续步骤仅处理过滤后的文件列表。如果过滤后无变更，告知用户无需提交并结束。

同时检查当前仓库的规范来源，确定本次必须执行的检查：

1. 当前目录及上级目录适用的 `AGENTS.md`、`CLAUDE.md`、`CONTRIBUTING.md` 等仓库说明
2. `package.json`、构建配置和项目文档中定义的 lint、test、build、typecheck 等脚本
3. `.husky/`、`core.hooksPath` 和 `.git/hooks/` 中实际生效的 pre-commit、commit-msg、pre-push hooks
4. 用户在当前请求中明确指定的检查

规范冲突时，执行不违反上层约束的更严格检查；不得自行省略仓库或用户明确要求的检查。

**不能把 Hook 的退出码当成唯一检查证据**：如果 `core.hooksPath` 指向的目录不存在对应 Hook，或 Hook 只配置了 `pre-push`，提交前仍必须按仓库脚本手动执行检查。对于 TypeScript/JavaScript 代码变更，至少执行仓库定义的轻量 lint/专项检查；本仓库的提交前基线是 `yarn lint-strict`，并结合触达文件 ESLint 和 `git diff --cached --check`。除非仓库规范、用户明确要求或 CI/发布语境要求，不主动执行全量 TypeScript 类型检查。

### 步骤二：分析变更内容

对每个变更文件执行 `git diff` 或 `git diff --cached` 查看具体修改内容。

根据修改文件路径判断变更类型：

| 路径模式 | 变更类型 |
|----------|----------|
| posts/YYYY-MM-DD/[slug]/ | 文章相关 |
| .Codex/skills/ | 技能配置 |
| src/ | 脚本代码 |
| .r2-upload-map/ | 资源映射（通常不单独提交） |
| 其他 | 项目配置 |

### 步骤三：决定提交策略

**单一主题修改**：一次性提交所有文件。

**多主题修改**：按目录/主题分组提交。

分组优先级：
1. 文章目录（每篇文章一个 commit）
2. 技能目录（每个技能一个 commit）
3. 代码变更（合并为一个 commit）
4. 配置文件（合并为一个 commit）

### 步骤四：生成 Commit Message

格式规范：
- 用中文
- 简洁描述变更内容
- 不超过 50 字
- 如果有卡片 ID，格式为：`卡片ID 提交描述`（如 `ComateStack-1234 修复登录页样式问题`）

常用模板：
- 文章：添加 [文章主题简述]、润色 [文章标题]、更新 [文章标题]
- 技能：添加 [技能名] 技能、更新 [技能名] 技能
- 代码：优化 [功能描述]、修复 [问题描述]
- 配置：更新项目配置

### 步骤五：精确暂存并执行提交前检查

对每个分组明确指定文件进行暂存：

```
git add <file1> <file2> ...
```

暂存后必须执行：

1. `git status --short`：确认暂存范围，没有混入其他主题或排除文件
2. `git diff --cached --name-status` 和 `git diff --cached`：复核实际将要提交的完整内容
3. `git diff --cached --check`：检查空白错误和冲突标记
4. 仓库规范要求的检查：按触达文件或目录执行 lint、test、build、typecheck 或专项脚本
5. 用户明确要求的其他检查
6. 并行 subagent 代码质量审查：按「并行 subagent 代码质量审查」小节派发 ponytail 与 agent-guard 两个只读审查 subagent

对本仓库 `src/` 代码变更，检查清单必须明确记录并执行：

```
yarn lint-strict
yarn eslint <触达的 .ts/.tsx 文件>
git diff --cached --check
```

其中 `yarn lint-strict` 用于覆盖仓库的技术债规则，触达文件 ESLint 用于覆盖常规代码规范；不能只依赖 `pre-push`，也不能因为 `git commit` 没有输出 lint 日志就视为检查已执行。

检查命令必须保留真实退出码，不得附加 `|| true`、管道吞错或其他忽略失败的写法。优先使用仓库规定的轻量、精确检查范围；只有仓库规范或用户明确要求时才执行全量重型检查。

任何检查失败时：

1. 不得执行 `git commit`
2. 定位并修复本次变更引入的问题
3. 重新暂存修复后的精确文件
4. 从本步骤的检查清单开头完整重跑
5. 直到所有检查通过后才能进入下一步

### 步骤六：执行提交

对每个分组依次执行：

```
git commit -m "commit message"
```

注意：
- **禁止**使用 `git add .` 或 `git add -A`
- 必须明确指定要提交的文件
- 排除临时文件（.bak-*、.html.bak-*）
- `git commit` 必须正常触发 pre-commit 和 commit-msg hooks
- **禁止**使用 `git commit --no-verify`
- hook 失败则视为检查未通过：停止提交，修复后重新执行步骤五

### 步骤七：执行推送（仅在用户要求 push 时）

提交成功不代表可以直接绕过推送前检查。push 前必须：

1. 执行 `git status --short --branch`，确认分支、工作区和暂存区状态符合预期
2. 复核待推送提交范围、目标 remote 和目标 branch/ref，避免推错分支
3. 执行仓库规范或用户要求的推送前检查；若 pre-push hook 定义了检查，不得删除、禁用或跳过
4. 使用正常的 `git push <remote> <refspec>`，让 pre-push hook 实际运行

**绝对禁止**使用 `git push --no-verify`。pre-push hook 或远端检查失败时，必须停止，修复问题并重新完成提交前/推送前检查；全部通过后才能再次 push。

### 步骤八：确认结果

执行 `git log --oneline -3` 和 `git status --short --branch` 确认提交结果。若执行了 push，还要根据 `git push` 的成功退出码及远端返回信息确认推送成功，不能只凭本地日志判断。

## 并行 subagent 代码质量审查

提交前质量门禁的一部分，在脚本检查之外进行。**并行**派两个只读 subagent 审查本次待提交内容（审查 `git diff --cached` 范围，禁止改动工作区/暂存区、禁止 `git add` / `git commit` / `--no-verify`）。

**审查者一：ponytail 审查者**
- 输入：待提交文件清单 + `git diff --cached`
- 视角：以 ponytail（最省、最简、YAGNI）标准审查本次变更
- 找：未复用仓库内已有实现 / 标准库 / 已装依赖的重写、过度抽象（一个实现的 interface、一个产品的 factory）、可删除的冗余与脚手架、绕远路的复杂写法
- 输出：按「可删除 / 可简化 / 可复用」三类列出，逐项标注是**阻断**（根因级：重复实现、未复用现成工具、纯冗余）还是**建议**（风格偏好，不阻塞提交）

**审查者二：agent-guard 审查者**
- 前置检测：仓库是否存在 `agent-guard` 工具与 `frontend/CLAUDE.md` 等硬性规约，且本次变更是否触达前端文件
- 适用时：按 agent-guard-plan 流程执行 H 预检 + `agent-guard check --mode worktree`（或缩小到变更文件范围）
- 不适用（无该工具 / 无前端变更）：如实报告 N/A，不编造通过结果，也不因此降低另一路标准
- 输出：H 系列高优 finding + agent-guard finding，逐条给修复建议

**汇合判定（两个审查者都返回后）**
- 两个 subagent **在同一轮并行派发**，不要串行等待
- 任一审查者报告**阻断性**问题 → 修复 → 重新暂存 → 从步骤五检查清单开头完整重跑
- 两个审查者都无阻断性问题，才允许进入步骤六执行 `git commit`

## 排除规则

以下文件默认不提交：
- .gitignore - 忽略规则文件，不自动提交
- *.bak-* - 备份文件
- .DS_Store - macOS 系统文件
- node_modules/ - 依赖目录
- .r2-upload-map/*.json - 通常随文章一起提交，除非单独要求

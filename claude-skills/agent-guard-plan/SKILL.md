---
name: agent-guard-plan
description: 手动 agent-guard 校验入口，并按需调度「特征测试驱动子代理」与「并行死代码审查子代理」。三模式：check / tdd / cleanup。
argument-hint: "[check|tdd|cleanup]"
---

# Agent Guard Plan

把 `agent-guard` 从「写代码后自动跑」改成「按需手动调度」。本 skill 既是原始校验点，也是两类子代理的调度器。

| 模式 | 用途 | 子代理形态 |
|------|------|-----------|
| `check`（默认）| 当前 worktree 跑一次 `agent-guard check --mode worktree` | 不分发，主代理直跑 |
| `tdd <component-path>` | 重构前用 Vitest+RTL 写特征测试，自验绿后驱动重构，红即回滚 | 单个 executor 子代理串行 |
| `cleanup [<module>...]` | 多模块并行死代码扫描，自验闸门全绿才提 commit | N 个 executor 子代理并行（worktree 隔离）|

---

## 0. 最高优先级：frontend/CLAUDE.md 硬性规约预检（**所有模式都必跑，在任何其他检查之前**）

`agent-guard` 二进制工具只覆盖了部分 `frontend/CLAUDE.md` 硬性条款（颜色硬编码 / inline style / toLocale* / JSON 深拷贝 / className 拼接 / 组件目录命名 / 行数 / 圈复杂度）。下列条款 **agent-guard 不会自动报**，必须在跑 `agent-guard check` 之前补充检查。

任一命中 → 必须在汇总开头用 **`⚠️ 高优关注（H?）`** 显式标注并要求修复，**不能淹没在普通 finding 列表里**。无命中也要在汇总里说一句「H1–H22 预检通过」。

### Pre-check 套件执行方式

**首选：调用项目内脚本（确定性，不依赖 AI 逐条 grep）**

```bash
# 在 repo 根目录执行
bash frontend/scripts/h-precheck.sh changed
```

脚本覆盖 H1–H17、H22（H8/H10/H11/H16-H21 为流程检查，输出提示而不 exit 1）。
H1/H2 同时已固化在 `frontend/.eslintrc.cjs` ESLint 规则中，`pnpm lint --changed` 亦会检测。
**脚本不存在时**再退回下方逐条 grep 方式。

**备用：逐条 grep（脚本不可用时）**

收集变更文件：

```bash
CHANGED_FE=$(git diff --name-only --diff-filter=ACMR -- 'frontend/**/*.ts' 'frontend/**/*.tsx'; \
             git diff --cached --name-only --diff-filter=ACMR -- 'frontend/**/*.ts' 'frontend/**/*.tsx'; \
             git ls-files --others --exclude-standard -- 'frontend/**/*.ts' 'frontend/**/*.tsx')
CHANGED_FE=$(echo "$CHANGED_FE" | sort -u | grep -v '^$' || true)
[ -z "$CHANGED_FE" ] && echo 'H 预检：本次无前端文件改动，跳过' && exit 0
```

逐条规则跑（命中即记 finding，**不要**`exit 1`，把所有 finding 都收集完一并报告）：

| ID | 条款 | 命令（在 worktree 根目录） | 例外 |
|----|------|----------------------------|------|
| **H1** | 禁止 `import React from 'react'`（React 19 新 JSX 转换） | `echo "$CHANGED_FE" \| xargs rg -n "^import React from ['\"]react['\"]"` | 无 |
| **H2** | 必须用 `@/` 别名，禁止 `from '../../..'` 及更深 | `echo "$CHANGED_FE" \| xargs rg -n "from ['\"]\.\./\.\./\.\./\""` | 无 |
| **H3** | 移动端必须 `useIsMobile`，禁止直接读 `window.innerWidth` 与断点比较 | `echo "$CHANGED_FE" \| xargs rg -n "window\.innerWidth\s*[<>=]"` | `hooks/useIsMobile.ts` / `hooks/useIsCompact.ts` / `components/UseConfigPanel/useIsUseConfigCompactLayout.ts` |
| **H4** | Electron 判断必须用 `isElectron / isMacElectron / isWindowsElectron`，禁止业务代码直读 `navigator.userAgent` | `echo "$CHANGED_FE" \| xargs rg -n "navigator\.userAgent"` | `constants/platform.ts` |
| **H5** | 外链必须经 `links/external.ts`，禁止业务代码直接 `window.open('http...')` 或赋 `window.location.href = 'http...'` | `echo "$CHANGED_FE" \| xargs rg -n "window\.open\(['\"]https?:\|window\.location\.href\s*=\s*['\"]https?:"` | `links/**` |
| **H6** | 禁止手写库已覆盖的功能（debounce/throttle/cloneDeep 自定义实现） | `echo "$CHANGED_FE" \| xargs rg -n "(function\|const)\s+(debounce\|throttle\|cloneDeep\|deepClone)\b"` | 无 |
| **H7** | 时间格式化函数（`format*Date / format*Time / format*Datetime`）新增必须落到 `src/utils/time.ts` | `echo "$CHANGED_FE" \| grep -v '^frontend/src/utils/time\.ts$' \| xargs rg -n "(function\|const\|export const)\s+format[A-Z][a-zA-Z]*(Date\|Time\|Datetime)\b"` | `src/utils/time.ts` |
| **H8** | 新增 `src/utils/**` / `src/hooks/**` / `src/contexts/**` 文件前，必须申报已搜索过现有同名 / 同义实现 | 流程检查：`echo "$CHANGED_FE" \| grep -E '^frontend/src/(utils\|hooks\|contexts)/[^/]+$'` 有新文件时，要求主代理在汇总中明确说明「已 grep 现有可复用项」 | 无 |
| **H9** | `src/api/` 下使用 `createInterface / createRawInterface` 时，URL 路径不得带 `/api/v1` 前缀（baseURL 已注入），路径参数用 `{paramName}` 占位 | `echo "$CHANGED_FE" \| grep -E '^frontend/src/api/.*\.ts$' \| xargs rg -n "create(Raw)?Interface[^\n]*['\"]/api/v1"` | `src/api/common.ts`（factory 配置处）、`src/api/sseService.ts`（SSE 自建请求）、`fetchWithAuth` 场景（需手动拼接完整路径） |
| **H10** | 禁止手动编辑 `src/icons/` 下自动生成的 `.tsx` 与 `index.ts`；应修改 `.svg` 源并跑 `pnpm generate-icons` | 流程检查：`echo "$CHANGED_FE" \| grep -E '^frontend/src/icons/(.*\.tsx\|(.*/)?index\.ts)$'` 有命中时，要求主代理在汇总中明确声明「已通过 `pnpm generate-icons` 重新生成，非手写改动」 | `frontend/src/icons/**/*.svg`（源文件改动本身不受限） |
| **H11** | 修改 `frontend/src/routes.tsx` 中的路由路径，必须同步 `src/interface/iframe.ts`（`RouteTarget` 类型）与 `src/components/Layout/useEmbedRouteSync.ts`（路由匹配正则），否则 embed 模式侧边栏高亮等联动会静默失效 | 流程检查：`echo "$CHANGED_FE" \| grep -qE '^frontend/src/routes\.tsx$'` 命中时，再检查同一 diff 是否包含 `frontend/src/interface/iframe\.ts` 与 `frontend/src/components/Layout/useEmbedRouteSync\.ts`；缺一即报 H11 | 仅调整 `routes.tsx` 内部非路径字段（如组件、loader）可豁免，需主代理在汇总中说明「未改动路径」 |
| **H12** | `src/api/` 不得出现 `index.ts` 桶文件（消费方直接从各业务域文件导入） | `echo "$CHANGED_FE" \| grep -E '^frontend/src/api/index\.ts$'` | 无 |
| **H13** | `src/regions/` 下不得直接导出 Region 实例，只暴露 `use* / set* / get* / load*` 等访问器 | `echo "$CHANGED_FE" \| grep -E '^frontend/src/regions/.*\.ts$' \| xargs rg -n "^export\s+(const\|let\|var)\s+\w+Region\b"` | 无 |
| **H14** | `src/contexts/` 顶层 `.tsx` 文件命名必须落在两种模式之一：**原生 Context** `XxxContext.tsx`（对应导出 `XxxProvider` + `useXxx`）或 **constate** `useXxx.tsx`（对应导出 `XxxProvider` + `useXxxContext`）；其他命名一律违规 | 两步：(a) 文件名过滤 `echo "$CHANGED_FE" \| grep -E '^frontend/src/contexts/[^/]+\.tsx$' \| grep -vE '/(use[A-Z][a-zA-Z]*\|[A-Z][a-zA-Z]*Context)\.tsx$'` —— 命中即文件名不合规；(b) 流程检查：对(a)未命中但新增/改名的文件，主代理需在汇总中目视确认导出对是否配套（`XxxProvider` + 对应 hook），避免只有 Provider 没有 hook 或反之 | `src/contexts/**/*` 的子目录文件（如 `ConversationList/useConversationLoader.ts`、`ConversationList/index.tsx`）—— 这类是 constate 实现内部拆分，pattern `contexts/[^/]+\.tsx` 已自然排除 |
| **H15** | 通用组件（`src/design/**` 与 `src/components/` 下的通用组件目录，不含 `src/components/UseConfigPanel/sections/**` 特性子树）不得从特性模块（`@/modules/*`、`@/features/*`、`@/components/UseConfigPanel/sections/*`）导入样式、barrel 或内部组件；跨边界反向依赖会在被依赖方重构/迁移时悄然断链，且违背「通用组件不向特性模块依赖」的分层原则 | `echo "$CHANGED_FE" \| grep -E '^frontend/src/(design\|components)/' \| grep -vE '^frontend/src/(modules\|features\|components/UseConfigPanel/sections)/' \| xargs rg -n "from ['\"]@/(modules\|features\|components/UseConfigPanel/sections)/"` | 特性子树内部互相引用不触发（pattern 已排除 `src/components/UseConfigPanel/sections/`、`src/modules/`、`src/features/` 作为 importer） |
| **H16** | 乐观更新 / 分页重载类 hook 中，`try` 前被改写的每个 `*Ref.current`（如 `queryRef` / `pageRef` / `hasMoreRef` / `cursorRef` 等）在 `catch` 回滚分支里都必须有对应的 `prev*` 快照还原；漏回滚任一字段，后续 `loadMore` / 分页请求会用"新条件 + 旧页码 / 旧数据"组合参数，把不匹配的下一页追加到旧列表后形成数据混合 | 流程检查：`echo "$CHANGED_FE" \| xargs rg -l "catch\s*\(" 2>/dev/null \| xargs rg -l "Ref\.current\s*=" 2>/dev/null` 有命中时，主代理须在汇总中逐文件列出「try 前被改写的 ref → 对应的 catch 回滚语句（或显式说明该路径无需回滚的理由）」；任何遗漏都按 H16 报 | `try` 之外的 ref 写入 / 无 `catch` 分支 / 捕获后主动重新抛出不回滚的代码路径，需主代理在说明中点明 |
| **H17** | Ant Design `Typography.Title`（含 `styled(Typography.Title)` / `styled(Title)` 包装与 `<Typography.Title style={{...}}>` 内联）禁止再设置 `font-weight: 500` / `fontWeight: 500`（含 `!important`）；项目主题已全局配置 `fontWeightStrong: 500`（见 `frontend/src/constants/theme.ts`），Title 默认字重即为 500，任何显式 500 都是冗余样式，还会遮蔽未来修改全局字重时的级联效果。非 500 的真实覆盖（如 600 / bold / 400）不触发 | `echo "$CHANGED_FE" \| xargs rg -nU "styled\((?:Typography\.)?Title\)[^\`]*\`[^\`]*font-weight\s*:\s*500" 2>/dev/null; echo "$CHANGED_FE" \| xargs rg -n "<Typography\.Title[^>]*style=\{[^}]*fontWeight\s*:\s*500" 2>/dev/null` | 不显式写 500 权重的 Title（交给主题默认值）；显式改为非 500 的真实需求 |
| **H18** | 禁止在 error / fallback 早返回分支中卸载持有 `ref` 的 DOM 元素（当该 ref 被 effect 用于恢复/重渲染逻辑时）。早返回导致 `ref.current === null`，后续 effect 即使收到新数据也无法执行渲染，组件永久卡在错误 UI 无法自动恢复。正确做法：始终保留 ref 持有元素在 DOM 中，通过 CSS（`visibility: hidden` + `position: absolute`）隐藏 | 流程检查：`echo "$CHANGED_FE" \| xargs rg -l "useRef" 2>/dev/null \| xargs rg -l "if\s*\(.*error" 2>/dev/null` 有命中时，主代理须检查：(a) 该组件是否有 `if (error) { return ... }` 或 `if (someState) { return ... }` 的早返回分支；(b) 早返回分支之后是否有 `<Xxx ref={someRef} />` 的 JSX；(c) 该 ref 是否在 `useEffect` / `useCallback` 中被用于恢复性渲染（如重新 fetch 后重渲染）。三者同时满足即报 H18 | 纯展示型 ref（如 `scrollRef` 仅用于滚动定位、不参与数据恢复逻辑）；error 状态下确实不需要自动恢复的场景（如终态错误，用户必须手动操作才能继续） |
| **H19** | 使用 inflight ticket（`++xxxRef.current`）做并发控制的 async 函数中，若 `try` 块内在 `finally` 之前调用了另一个会同步递增同一 `xxxRef` 的函数（如 fire-and-forget 的 prefetch / 预加载），则 `finally` 中的 `ticket === xxxRef.current` 守卫永远为 false，loading 状态永远无法重置。正确做法：在调用可能递增 ticket 的函数**之前**完成 loading 状态重置，`finally` 仅作为异常路径兜底 | 流程检查：`echo "$CHANGED_FE" \| xargs rg -l "inflightRef\|ticketRef\|versionRef" 2>/dev/null \| xargs rg -l "finally" 2>/dev/null` 有命中时，主代理须检查：(a) `try` 块内是否有不 await 的 async 调用（fire-and-forget）；(b) 该调用是否会同步执行 `++sameRef.current`；(c) `finally` 是否依赖 `ticket === sameRef.current` 来决定是否重置状态。三者同时满足即报 H19 | `finally` 中无条件重置（不依赖 ticket 守卫）的写法；被调用函数不递增同一 ref 的场景 |
| **H20** | `catch` 块中设置阻断性错误标志（如 `xxxErrorRef.current = true`）或显示用户可见错误提示（`message.error` / `notification.error`）时，必须先校验当前请求是否仍为最新请求（通过 inflight ticket / version 快照比对）。否则：(a) 已被 `resetAndReload` 等操作超越的旧请求失败会污染新状态，导致后续操作被永久阻断；(b) 用户看到与当前数据不匹配的虚假错误提示 | 流程检查：`echo "$CHANGED_FE" \| xargs rg -n "catch\s*\(" 2>/dev/null \| xargs rg -n "Ref\.current\s*=\s*true\|message\.error\|notification\.error" 2>/dev/null` 有命中时，主代理须检查：(a) 该 catch 所在的 async 函数是否可被并发调用或被其他操作超越（如 resetAndReload 会递增 inflight）；(b) catch 中是否有 ticket/version 校验守卫。可被超越但无守卫即报 H20 | 不可被超越的操作（如一次性初始化、用户主动触发且无并发可能的操作）；catch 中已有 `if (ticket === xxxRef.current)` 或等价守卫 |
| **H21** | 错误标志（`xxxErrorRef.current = true`）一旦被设置，必须存在**可达的清除路径**让用户恢复正常操作。若唯一清除路径是切换筛选条件 / 导航离开等非直觉操作，而错误提示暗示"稍后重试"即可恢复，则构成 UX 误导。正确做法：(a) 使用带自动恢复的退避机制（如 `setTimeout(() => { ref.current = false }, 3000)`）；或 (b) 在下一次用户主动触发时自动清除（如下一次滚动到底部时重置标志再尝试） | 流程检查：`echo "$CHANGED_FE" \| xargs rg -n "Ref\.current\s*=\s*true" 2>/dev/null` 有命中时，主代理须检查：(a) 该标志是否用于阻断后续操作（如 `if (xxxRef.current) return`）；(b) 是否存在用户可直觉触达的清除路径（不含切换页面/筛选条件等间接操作）；(c) 错误提示文案是否与实际恢复方式一致。阻断标志无直觉清除路径即报 H21 | 标志仅用于日志/统计不阻断操作；标志在同一函数的 success 路径中被清除且该路径可达（如重试成功）；标志有明确的 setTimeout 自动恢复 |

### 输出格式（必须先于其他 finding 出现）

有命中：

```
⚠️ 高优关注（frontend/CLAUDE.md 硬性规约）：触发 N 条
  - [H1] frontend/src/foo/Bar.tsx:3  `import React from 'react'`  → React 19 不需要，改按需 import
  - [H3] frontend/src/baz/Qux.tsx:42 `window.innerWidth < 768`    → 改用 useIsMobile()
  - ...
（请优先修这些再继续；它们不会被 agent-guard 报，但属于项目硬性条款）
```

无命中：

```
H1–H21 预检：通过（无 CLAUDE.md 硬性条款违规）
```

H8 有新文件时附加一行：

```
H8：新增 src/utils/Xxx.ts —— 请确认已 grep src/utils, src/hooks, src/contexts 中没有可复用项再继续
```

### 与 agent-guard 的关系

- 这 18 条是 **agent-guard 漏检的补丁**，不替代 `agent-guard check`。
- 跑完 H 预检后继续按各模式原本流程：`agent-guard check --mode worktree` → ESLint 复杂度补刀 → 汇总。
- 汇总分两栏：**高优关注（H 系列） / 常规 finding（agent-guard + ESLint）**。

---

## Mode: check（默认）

**默认行为：不等确认，直接跑**。进入 check 模式时（严格按顺序）：

0. **先跑「0. 最高优先级 H 预检」**（H1–H8），收集 ⚠️ 高优 finding。
1. 并行跑一次只读 context 收集（见下）
2. 执行 `agent-guard check --mode worktree`
3. 跑 ESLint 复杂度补刀（见 2b）
4. 用一段话汇总，**高优 finding 必须出现在最前**：当前 worktree 范围、H 预检结果、guard 结果、ESLint 结果、下一步建议

仅当用户在参数里显式写 `check --confirm` 或类似意图时，才走「先出计划、等确认」的旧流程。

### 1. Collect Context（可与 Run Guard 并行）

只跑只读命令：

```bash
pwd
git rev-parse --show-toplevel
git status --short
git diff --stat
git diff --name-only
git diff --cached --name-only
```

未来代码修改场景（非检查已有 diff）只读取相关文件，并说明是否检查过 `src/utils`、`src/hooks`、`src/contexts` 与已安装第三方库的可复用项。

### 2. Run Guard（默认立即执行）

```bash
agent-guard check --mode worktree
```

入口缺失先跑 `command -v agent-guard` 报告，不要替换成无关检查。

#### 2b. 补跑 ESLint 复杂度 / 质量规则（agent-guard 未覆盖）

已知漏网：`agent-guard` 不跑 ESLint 的 `complexity`、`max-lines-per-function`、`max-depth` 等代码质量规则。典型漏报案例：

> `Async arrow function has a complexity of 11. Maximum allowed is 10. (complexity)`

对 diff 涉及的前端文件追加一次 ESLint 扫描，覆盖圈复杂度类规则：

```bash
# 仅跑 diff 涉及的 frontend 文件（staged + unstaged + untracked）
cd frontend && \
  git diff --name-only --diff-filter=ACMR -- '*.ts' '*.tsx' | sed 's|^frontend/||' | \
  xargs -r pnpm eslint --no-warn-ignored
```

- 有 `complexity` / `max-*` 类报错 → 列入 finding，和 agent-guard 结果一起汇总。
- 与 agent-guard 的 inline-style 等前端规则合并后再给「下一步建议」。
- 新建重构 / 重写函数时，若改动行数大或含多分支，即使没命中阈值也建议主动检查，避免 PR 阶段才被拦。

### 3. Report

两段式汇总（**高优在前**）：

```
worktree: <path>
改动：N 个文件（列主要路径）

⚠️ 高优关注（H 系列）：触发 K 条 / 或「H1–H18 预检通过」
  - [Hx] file:line  说明  → 修复建议
  - ...

常规 finding：
  agent-guard: no frontend guard findings / 或列出摘要
  eslint(complexity): 0 / 或列出摘要

下一步：先修高优 H 系列 → 再修常规 finding → 然后继续开发
```

### 4. Confirm-first 旧流程（仅当用户显式要求）

参数里看到 `--confirm` / `带计划` / `先别跑` 等意图时，才按旧流程出「范围 / 修改计划 / 验证计划 / 需要确认」四段式等用户回复。

---

## Mode: tdd —— 特征测试驱动子代理

### 何时启动

任何「重构既有组件 / 调样式 / 改交互」的任务，且不希望破坏原行为时。

### 抽象工作流

1. 主代理读组件源码，盘点行为面。
2. 主代理用 ExitPlanMode 给出**场景级**测试清单（每条一行），等用户补充或直接通过。
3. 计划通过后 spawn 一个 `executor` 子代理，按下面的 prompt 模板执行。
4. 子代理跑完返回 commit hash 列表与回滚记录。

### 子代理自校验闸门（必须全绿才报完成）

- **gate-1**：测试文件被 `pnpm vitest list` 发现
- **gate-2**：测试在**未改动**的代码上 100% 通过（捕获 stdout 作为证据）
- **gate-3**：测试单独 commit
- **gate-4**：重构后所有测试仍 100% 通过
- **gate-5**：gate-4 红 → `git revert <refactor-commit>`（**绝不**回滚 test commit），换实现路径回到 gate-4 重试，最多 3 次后停下报告 root cause

### 子代理 prompt 模板

```
你是 <COMPONENT_PATH> 的特征测试驱动者。

执行步骤：

1. 读 <COMPONENT_PATH> 与相关文件，盘点：
   - 渲染变体（影响输出的 props 组合）
   - 用户交互（点击 / 输入 / 键盘 / 焦点）
   - 边界状态（空数据 / loading / error / disabled）
   - 副作用（hooks 调用、callback 触发、context 消费）

2. 在 <COMPONENT_DIR>/__tests__/<Component>.characterize.test.tsx 写
   Vitest + @testing-library/react 测试。
   覆盖目标：行为覆盖（「它还做不做 X」），不是行 %。

3. `pnpm vitest run <test-file>` 必须全绿。
   若红：是测试写错了，不是组件 bug —— 修测试，不改组件。

4. 全绿后 `git add` 测试文件并 commit。
   message 风格：看 `git log --oneline -5` 复用前缀格式
   （示例："<ticket-id> test: characterize <Component>"）

5. 执行重构：<REFACTOR_BRIEF>

6. 再跑 `pnpm vitest run <test-file>`：
   - 全绿 → 单独 commit 重构（沿用同样 message 风格）
   - 任一红 → `git revert HEAD`（只回退重构 commit，**不**碰测试 commit），
     换思路重试，最多 3 次，仍失败则停下报告 root cause

禁止：
- 修改测试以让重构通过（违背特征测试目的）
- 把测试和重构合在一个 commit
- 跳过 gate-1～gate-5 任意一个

返回（结构化）：
- 测试文件路径与场景列表
- test commit hash + refactor commit hash（或回滚记录）
- 三次重试都失败时的 root cause
```

### 案例：弹窗样式统一（参考 CreateExtensionModal）

顶层任务：以 CreateExtensionModal 为参考，统一可选添加弹窗 / 团队设置弹窗 / 技能删除确认弹窗的样式。

调度顺序：
1. 每个目标弹窗 spawn 一个 tdd 子代理，`REFACTOR_BRIEF` 填："对齐到 CreateExtensionModal 的样式：复用主题常量与共享 mixin；禁止 inline style（高频纯数值尺寸除外，见 Known Exceptions）；通过 Playwright MCP 截图对比，迭代不超过 5 次直到视觉差 < 2%。"
2. 子代理**串行**跑（避免 worktree 共享时 git 冲突），每个产出一对 commit（test + refactor）
3. 主代理最后聚合：抽离的共享 mixin 清单 + 残留差异

---

## Mode: cleanup —— 并行死代码审查子代理

### 何时启动

需要在多个模块同时清理无引用代码。模块间无依赖时天然适合并行。

### 抽象工作流

1. 主代理决定模块列表（用户指定，或扫 `src/` 一级目录）。
2. 对每个模块 spawn 一个 `executor` 子代理，**Agent 工具开 `isolation: "worktree"`**，子代理在独立 worktree 工作。
3. 所有子代理**并行**执行（同一条消息里多个 Agent tool_use 块）。
4. 全部返回后主代理汇总成表，标出风险与模糊符号。

### 子代理自校验闸门（必须全绿才提 commit）

- **gate-1**：`pnpm typecheck` 绿
- **gate-2**：`pnpm lint`（若存在）绿
- **gate-3**：`agent-guard check --mode worktree` 无 finding
- **gate-4**：`git diff --check` 干净

### 双闸门删除规则

候选符号必须**同时**满足两条才删：
- **静态零引用**：`rg --type ts --type tsx '<symbol>'` 在声明文件外 0 命中（index.ts 的 re-export 不算"使用"）
- **历史无复用**：`git log --since=90.days.ago -S'<symbol>' --oneline` 为空

任一不满足 → 保留。
被动态键访问（`obj[name]`）或 `*` 星号导入引用 → 标 **AMBIGUOUS**，不删，列入报告交用户审核。

### 子代理 prompt 模板

```
你是 <MODULE_NAME> 模块（<MODULE_PATH>）的死代码审查者。

执行步骤：

1. worktree 已由调用方创建在分支 cleanup/<MODULE_NAME>。
   pwd 确认你在该 worktree 根目录。

2. 枚举候选：
   - 顶层导出：rg -tts -ttsx '^export ' <MODULE_PATH>
   - styled-component 变体：扫 **/styles.ts
   - prop 联合成员：扫 | { type: '...' 与 | '...' 字面量联合
   汇成 candidates 列表。

3. 双闸门过滤：
   - rg 在声明文件外 0 命中（排除 index.ts re-export-only 文件）
   - git log --since=90.days.ago -S'<symbol>' --oneline 为空
   都满足 → 加入 to-delete。
   动态键 / 星号 import → 加入 ambiguous-flagged，不删。

4. 删除 to-delete 与连锁孤儿 import。
   ⚠️ 易错点：删一个组件消费者后，文件顶部的 Button / 工具 import 会变孤儿。
   每删一批就跑一次 typecheck，让 TS6133 / unused-import 报错暴露孤儿。

5. 自校验闸门：
   - pnpm typecheck 绿
   - pnpm lint 绿（若有）
   - agent-guard check --mode worktree 无 finding
   - git diff --check 干净
   任一红 → 别提 commit，缩小删除范围或回滚部分，重跑闸门。

6. commit。message 沿用当前分支风格（看 git log --oneline -5），
   中文描述清理范围。

禁止：
- 跨模块边界改文件
- 删 index.ts 的 re-export，除非下游消费者也已确认无引用
- 闸门红还坚持 commit
- 删除被动态键 / 星号 import 触达的符号

返回（结构化）：
- module: <MODULE_NAME>
- branch: cleanup/<MODULE_NAME>
- files_changed: <数量>
- loc_removed: <行数>
- risk:
    low    —— 纯类型 / 注释 / 模块内私有 helper
    medium —— 导出的 helper / hook
    high   —— 组件 / context / 公共 API
- ambiguous_flagged: [{symbol, reason}]
- gates: {typecheck, lint, agent_guard, git_diff_check} 全 pass
```

### 主代理聚合表（所有子代理返回后输出）

```markdown
| 模块 | 文件改动 | 删除行数 | 风险 | 分支 | 模糊标记 |
|------|---------|---------|------|------|---------|
| skills | 4 | -127 | low | cleanup/skills | 0 |
| knowledge | 2 | -56 | medium | cleanup/knowledge | 1（动态导出 key）|
| ... |
```

模糊标记的符号单独列出，等用户审核：

```markdown
**待审核（AMBIGUOUS）**
- knowledge / `KNOWLEDGE_TYPES['<key>']` —— 通过动态键访问，rg 命中但调用方用变量
- ...
```

### 案例：src/ 五模块并行清理

参与模块：skills、knowledge、extensions、teams、layout。
主代理在**一条消息里**发出 5 个 Agent tool_use，每个：
- `subagent_type: "executor"`
- `isolation: "worktree"`
- `prompt`: 上面的模板填空（替换 `<MODULE_NAME>` / `<MODULE_PATH>`）

5 个并行返回后聚合成表，主代理不动手做删除。

---

## 通用 Pitfalls

- **Button 孤儿 import**：移除 CardActionButton 类消费者后，文件顶部的 `import { Button } from 'antd'` 会变孤儿。每删一批跑 typecheck，让 TS6133 暴露。
- **index.ts re-export 不是引用**：`export { Foo } from './foo'` 在 rg 中会命中，但本身不消费。判定零引用时，排除"只做 re-export"的文件。
- **测试 commit 与重构 commit 必须分离**：合并后回滚会连测试一起丢，失去保护网。
- **特征测试 ≠ 单元测试**：覆盖目标是「组件还做不做 X」，不是函数纯度。允许 mock context / router；不要 mock 内部实现细节。
- **dynamic key access**：`obj[someVar]` rg 找不到字符串字面量，必须靠 `git log -S` 与人工审核兜底。

---

## Known Exceptions（不要 flag）

以下情况即便触发 inline-style 类规则，也属于合理例外，需在汇总中跳过或标注为「忽略」：

- **高频变化的纯数值布局尺寸** —— 虚拟列表 `totalSize`、`translateY`、拖拽位移、动画帧位置等动态像素值，允许直接写 `style={{height: x}}` / `style={{transform: ...}}`。
  - 原因：把这类值塞进 emotion `css` 模板或 styled-component props 模板，每个唯一值都会注入一条新 CSS 规则且永不卸载，长会话累积大量泄漏。inline style 走 DOM 属性通道，不进 CSSOM，是唯一无泄漏写法。
  - 适用边界：仅限「值频繁变化的纯数值尺寸 / 位移」。颜色、字体、padding、token 相关样式仍须走 styled-component + CSS variable。静态部分（position、margin、box-sizing 等）仍要抽到模块级 className 或 styled component。
  - 参考：`frontend/src/modules/Conversation/ConversationContent.tsx` 的 `innerCls` + `style={{height: totalSize}}`。

---

## Boundaries

- 不要在每次 Edit / Write 后自动运行 `agent-guard`。
- 不要运行全仓 TypeScript 重型检查，除非：(a) 用户明确要求；或 (b) `tdd` / `cleanup` 子代理在自己的闸门内运行（这属于子代理职责，不算"自动跑"）。
- 不要创建测试代码，除非进入 `tdd` 模式且测试清单已通过 ExitPlanMode。
- 不要删除、移动或批量改写文件，除非：(a) 用户明确确认；或 (b) `cleanup` 模式双闸门双绿 + 子代理自校验闸门全绿。
- 提交前的 Git hook staged 门禁不属于本 skill 的自动触发范围。
- 子代理跨边界写文件、跳过自校验闸门、合并 test/refactor commit —— 主代理收到这类返回时，不要采纳，要求子代理重跑或人工接手。

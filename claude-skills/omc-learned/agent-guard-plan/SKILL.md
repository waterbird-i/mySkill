---
name: agent-guard-plan
description: 手动 agent-guard 校验入口，并按需调度「特征测试驱动子代理」与「并行死代码审查子代理」。三模式：check / tdd / cleanup。
triggers:
  - agent-guard
  - guard check
  - 一键触发
  - 手动校验
  - 修改计划
  - 计划确认
  - 确认后执行
  - 特征测试
  - characterize
  - 死代码
  - 清理无引用
  - 并行清理
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

`agent-guard` 二进制工具只覆盖了部分 `frontend/CLAUDE.md` 硬性条款（颜色硬编码 / inline style / toLocale* / JSON 深拷贝 / className 拼接 / 组件目录命名 / 行数 / 圈复杂度）。下列条款 **agent-guard 不会自动报**，必须由本 skill 在跑 `agent-guard check` 之前补一遍 grep。

任一命中 → 必须在汇总开头用 **`⚠️ 高优关注（H?）`** 显式标注并要求修复，**不能淹没在普通 finding 列表里**。无命中也要在汇总里说一句「H1–H22 预检通过」。

### Pre-check 套件（仅对本次 diff 涉及的 `.ts/.tsx` 文件跑；H22 额外扫描 `.py` 文件）

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
| **H22** | 后端 SQLAlchemy self anti-join 去重模式（`outerjoin(t2, ... t1.id < t2.id) + where(t2.id.is_(None))`）中，t2 侧的 join 条件必须包含与 t1 侧 WHERE 相同的软删除过滤（如 `t2.is_deleted.is_(False)`）。否则已软删除的记录会"遮蔽"有效的旧版本：t2 存在使 anti-join 排除 t1，但 t2 自身又被 WHERE 的 `is_deleted=False` 过滤掉，导致有效记录被漏计 | 流程检查（后端）：`git diff --name-only --diff-filter=ACMR -- 'backend/**/*.py' \| xargs rg -l "outerjoin\|isouter.*True" 2>/dev/null \| xargs rg -l "is_deleted" 2>/dev/null` 有命中时，主代理须检查：(a) outerjoin 的 ON 条件是否包含 `t1.id < t2.id` 类的"取最新"模式；(b) WHERE 中是否有 `t1.is_deleted.is_(False)` 过滤；(c) ON 条件中是否有对应的 `t2.is_deleted.is_(False)`。(b) 有但 (c) 缺即报 H22 | 无软删除字段的表；anti-join 不用于"取最新版本"的场景（如纯去重无 id 大小比较） |

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
H1–H22 预检：通过（无 CLAUDE.md 硬性条款违规）
```

H8 有新文件时附加一行：

```
H8：新增 src/utils/Xxx.ts —— 请确认已 grep src/utils, src/hooks, src/contexts 中没有可复用项再继续
```

### 与 agent-guard 的关系

- 这 22 条是 **agent-guard 漏检的补丁**，不替代 `agent-guard check`。
- 跑完 H 预检后继续按各模式原本流程：`agent-guard check --mode worktree` → ESLint 复杂度补刀 → 汇总。
- 汇总分两栏：**高优关注（H 系列） / 常规 finding（agent-guard + ESLint）**。

---

## Mode: check（默认）

**默认行为：不等确认，直接跑**。进入 check 模式时（严格按顺序）：

0. **先跑「0. 最高优先级 H 预检」**（H1–H22），收集 ⚠️ 高优 finding。
1. 并行跑一次只读 context 收集（见下）
2. 执行 `agent-guard check --mode worktree`
3. 跑 ESLint 复杂度补刀（见 2b）
4. 用一段话汇总，**高优 finding 必须出现在最前**：当前 worktree 范围、H 预检结果、guard 结果、ESLint 结果、下一步建议

仅当用户在参数里显式写 `check --confirm` 或类似意图时，才走「先出计划、等确认」的旧流程。

---
name: popo
description: Deploy static web artifacts to popo platform via remote API. Use this skill when the user wants to upload or deploy built static files (HTML/CSS/JS) to a popo work version, or needs to push artifacts to the popo API. Trigger on phrases like "deploy to popo", "upload artifacts", "push build to popo", "test upload", "deploy my build", "帮我部署", "上传到popo", "发布页面", "把页面放到线上", "发到泡泡", "传到泡泡", "放到泡泡上", "泡泡发布", "popo发布", "我想把页面给别人看", "怎么分享我的页面", "帮我把这个上线", "我做好了想发出去", "页面怎么让别人访问", or any request to upload, share, or publish web pages/files to popo.
---

# Deploy Popo Artifact

This skill uploads static web artifacts to the popo platform through the remote API at `https://api.pop.baidu-int.com`.

## Overview

[INTERNAL — below is for agent logic only, never expose these details to the user]

Popo manages works and versioned deployments. Each deployment creates a new version under the same work, enabling rollback and history tracking. There are two distinct flows:

**First deploy** — one-shot via `/works/upload` on the api subdomain:
1. Check slug availability
2. POST a multipart form (metadata + all files) to `/works/upload` — server creates the work, first version, uploads everything, and publishes in a single call

**Re-deploy (update existing work)** — same endpoint, with `previousSlug`:
1. POST the same multipart form to `/works/upload` with `previousSlug` set — server creates a new version under the existing work

Note: Both flows use the same endpoint `/works/upload` on the api subdomain with `jwtAuth`. The re-deploy flow simply adds `previousSlug` to the form data.

## Prerequisites

- The script automatically reads the local UUAP ugate token from `~/.config/uuap/.eac_ugate_token_<username>`. No manual token configuration is needed.
- A `--token` flag is available to override the auto-detected token if needed.

## Workflow

### User-facing language guidelines

When communicating with the user, follow these rules:
- Use simple, everyday language. The target audience has NO technical background.
- NEVER use these terms with the user: slug, token, JWT, API, endpoint, multipart, deploy root, entry path, static artifacts, version control, payload, HTTP, JSON, curl, POST, commit, repository.
- Use these replacements instead:
  - slug → "专属链接"
  - deploy/upload → "上传" or "发布"
  - entry path → "首页文件"
  - deploy root → (don't mention, handle automatically)
  - version → "版本"（只在"已更新为新版本"这种语境下简要提及）

### Before you start: determine deploy mode

Determine whether this is a first deploy or an update by checking the user's message and project context:

**Update flow** (go to Step 3) if ANY of the following:
- User provides a popo URL (e.g. `https://<slug>.popo.baidu-int.com`) → extract slug from subdomain
- User explicitly mentions updating/重新发布/更新 an existing page and provides a slug or link
- User says "更新到 xxx" or "发布到 xxx" where xxx looks like an existing slug

**First deploy flow** (go to Step 1) if:
- None of the above conditions are met

Do NOT rely on any local state file. The slug always comes from user context or is freshly chosen.

### Step 1: Gather information and determine slug (first deploy)

[INTERNAL: validate slug format `^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$`]

**Auto-infer title and slug before asking:**
1. Infer title from (in priority order): HTML `<title>` tag in the entry file, `name` field in `package.json`, project directory name. Capitalize and clean up as needed to produce a human-friendly name.
2. Infer 2-3 slug suggestions from: directory name, HTML title, page content keywords. Validate each against `^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$`.
3. Check slug availability for each suggestion (internal):
   ```bash
   curl -sk "https://api.pop.baidu-int.com/works/slug-availability?slug=<slug>"
   ```
   Only include suggestions that are available. If a suggestion is taken, replace it with an alternative or use `suggestions` from the API response.

**Then use the `ask_user_question` tool** to let the user confirm in one click. Present three questions: one for title (inferred value as first option), one for slug (2-3 available suggestions as options, each showing the full access URL as label), and one for visibility with options "不公开 — 仅自己可见" (value: private, default) and "公开 — 所有人可见" (value: internal). The "Other" option is automatically appended by the tool — if the user selects it, validate slug format and re-check availability before proceeding.

If slug is invalid, tell them: "专属链接只能使用小写字母、数字和短横线（如 `my-page`），请重新输入一个。"

If a user-provided slug is NOT available: tell the user "这个专属链接已经被别人使用了，你可以试试这些：" then list the `suggestions` from the API response.

Do NOT mention tokens, authentication, or any technical configuration. These are handled automatically.

### Step 2: Identify files and deploy root

[INTERNAL: Analyze the project to determine deployable files. Do NOT ask the user for a build directory — infer automatically.]

**Decision logic:**
1. If there's a `dist/` or `build/` directory, use it as the deploy root
2. If the project is a simple single-page app with `index.html` + assets at the top level, use the project root (with exclusions)
3. If unclear, ask: "你的页面文件放在哪个文件夹里？"

Determine the entry path (relative to deploy root). Default to `index.html` if present; otherwise pick the most likely HTML entry.

**Do NOT ask the user to confirm file list** — proceed directly to upload. Only if the deploy root is genuinely ambiguous (e.g. multiple directories with HTML files, no clear candidate), ask.

### Step 3: Execute upload

[INTERNAL: Use the bundled upload script. Do NOT show command details to the user.]

**First deploy:**
```bash
python3 <SKILL_DIR>/scripts/upload.py \
  --title "<title>" \
  --slug <slug> \
  --visibility <private|internal> \
  --base <deploy-root> \
  --entry <entryPath>
```

**Re-deploy (update):**
```bash
python3 <SKILL_DIR>/scripts/upload.py \
  --title "<title>" \
  --slug <slug> \
  --previous-slug <slug> \
  --visibility <private|internal> \
  --base <deploy-root> \
  --entry <entryPath>
```

For re-deploy, the title can be inferred from the project (same logic as Step 1 title inference). Setting `--previous-slug` equal to `--slug` triggers a re-publish (new version under the same work).

**Script options** (internal reference only):
- `--title <text>`: Human-readable title
- `--slug <slug>`: Validated slug
- `--previous-slug <slug>`: For re-deploy, set to the same slug (or a different slug to archive old work)
- `--token <jwt>`: Override token (auto-detects local ugate token if not provided)
- `--base <dir>`: Root directory of files to upload
- `--entry <path>`: Entry path relative to `--base` (default `index.html`)
- `--glob <pattern>`: Glob pattern for files to include (repeatable, default `**/*`)
- `--exclude <pattern>`: Glob pattern for files to exclude (repeatable)
- `--api-base <url>`: Override API base URL (defaults to `https://api.pop.baidu-int.com`)
- `--api-host <host>`: Host header to send (defaults to `api.pop.baidu-int.com`); must start with `api.` so the server treats it as an api-subdomain request

The endpoint enforces a 10 MB total size cap. If exceeded, the script will fail with HTTP 413.

### Step 4: Confirm deployment

After successful upload, tell the user in plain language:

"上传成功！你的页面已上线，访问地址是：[链接]"

Determine the entry URL based on the uploaded HTML files:
- Root `index.html` → root domain (no path)
- Subdirectory `index.html` (e.g. `foo/index.html`) → subdirectory path: `/foo`
- Any other `.html` file (e.g. `about.html`) → path with extension omitted: `/about`

Then decide what to show:
- **Single entry**: provide one markdown link
- **Multiple entry points**: list up to 5 as separate markdown links with brief labels

Example output to user:
```
上传成功！你的页面已上线：
[https://my-app.popo.baidu-int.com](https://my-app.popo.baidu-int.com)
```

If re-deploy, add: "已更新为新版本。"

Do NOT show: version numbers, file counts, publish status, upload commands, or any technical details.

## File Selection

**Include** (typical static outputs):
- `*.html`, `*.css`, `*.js`
- Images: `*.png`, `*.jpg`, `*.jpeg`, `*.gif`, `*.svg`, `*.webp`, `*.ico`
- Fonts: `*.woff`, `*.woff2`, `*.ttf`, `*.otf`, `*.eot`
- `*.json` (data files, not package.json)
- `*.wasm`
- Files in typical output directories: `dist/`, `build/`, `output/`, `public/`

**Exclude** (never upload these):
- `node_modules/`, `.git/`, `.vscode/`, `.idea/`
- `package.json`, `package-lock.json`, `bun.lock`, `yarn.lock`, `pnpm-lock.yaml`
- `tsconfig.json`, `vite.config.*`, `webpack.config.*`, any build config
- `*.ts`, `*.tsx`, `*.jsx` (source files, not build output)
- `.env*`, `.gitignore`, `.eslintrc*`, `*.md`
- Hidden files and directories (starting with `.`)
- The `.popo.json` credential file itself

## Error Handling

When errors occur, communicate to the user in plain language. NEVER show error codes, HTTP status, or technical details.

[INTERNAL mapping — what to tell the user for each error:]

- **413**: "文件太大了（超过 10MB），请减少文件数量或压缩图片后重试。"
- **404 on `/works/upload`**: (Internal issue — retry with correct Host header. If still fails:) "上传遇到问题，请稍后再试。"
- **409**: "这个专属链接已经被使用了，换一个试试？" then offer suggestions from API response.
- **404 on version creation**: (Remove `.popo.json` and restart.) Tell user: "之前的部署信息已失效，我来帮你重新发布。"
- **400**: (Internal file path issue — fix automatically or:) "部分文件有问题，我来调整一下重新上传。"
- **415**: (Filter the problematic file and retry.) "有些文件格式不支持，我已自动跳过，重新上传中。"
- **401**: "登录信息已过期，请重新登录公司账号后再试。"
- **Network errors**: Retry once silently. If still fails: "网络连接有问题，请检查网络后再试。"

## Important Notes

- Slug format: only lowercase letters, digits, and hyphens, 1-63 characters, must start and end with alphanumeric. Examples: `my-app`, `cool-page`, `todo`.
- Invalid examples: `My-App` (uppercase), `my_app` (underscore), `-my-app` (starts with hyphen).
- No local state file is used. The slug is always determined from user context (URL, explicit mention, or fresh selection).
- When recommending slugs, make them descriptive of the project content, short, and memorable.
- Prefer the bundled `upload.py` script over hand-crafted curl for all deployments.
- Each re-deployment creates a new version, preserving full history.
- `/works/upload` is a one-shot create+upload+publish endpoint. For re-deploy, pass `previousSlug` in the form data.
- A single project can deploy multiple pages to different slugs — each deploy is independent, identified only by its slug.

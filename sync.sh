#!/usr/bin/env bash
# 把 ~/.agents/skills（共享实体源）里的非厂内 skill 镜像进本仓，并刷新 claude/comate 软链。
# 排除名单就是 .gitignore —— 厂内 / 含个人信息的 skill 只留在本机，不入公开仓。
set -uo pipefail
cd "$(dirname "$0")"

AG=$HOME/.agents/skills
mkdir -p agents-skills claude-skills comate-skills

for src in "$AG"/*; do
  n=$(basename "$src")
  [ -f "$src/SKILL.md" ] || continue
  [ -L "$src" ] && { echo "skip  ${n}（外部 live 安装，只在本机软链）"; continue; }
  git check-ignore -q "agents-skills/$n/" && { echo "skip  ${n}（厂内，按 .gitignore 排除）"; continue; }

  rsync -aL --delete --exclude .git --exclude .DS_Store --exclude node_modules \
    "$src/" "agents-skills/$n/"

  for sub in claude-skills comate-skills; do
    # 本机该 agent 根下没有这个 skill 就不建仓内软链（如 commit / frontend-design 与 Claude 已有命令冲突）
    root=$HOME/.${sub%%-skills}/skills
    [ -e "$root/$n" ] || continue
    [ -e "$sub/$n" ] || ln -s "../agents-skills/$n" "$sub/$n"
  done
  echo "sync  $n"
done

echo
echo "未入仓（厂内 / 个人信息）："
sed -n 's|^agents-skills/\(.*\)/$|\1|p' .gitignore | tr '\n' ' '
echo

#!/usr/bin/env bash
# 一键推送 hermes-skills 到 GitHub（SSH over 443）
set -e
cd "E:/hermes_memes/hermes-skills"

USER_NAME="${1:-}"
if [ -z "$USER_NAME" ]; then
  echo "用法: bash push.sh <github用户名> [仓库名默认 hermes-skills]"
  exit 1
fi
REPO="${2:-hermes-skills}"

git config --local core.sshCommand "ssh -i ~/.ssh/id_ed25519_github -p 443 -o StrictHostKeyChecking=no"
git remote remove origin 2>/dev/null || true
git remote add origin "git@github.com:${USER_NAME}/${REPO}.git"

echo "=== 测试认证 ==="
ssh -T -p 443 -i ~/.ssh/id_ed25519_github -o StrictHostKeyChecking=no git@github.com 2>&1 | head -2 || true

echo "=== 推送 ==="
GIT_SSH_COMMAND="ssh -i ~/.ssh/id_ed25519_github -p 443 -o StrictHostKeyChecking=no" \
  git push -u origin main 2>&1 | tail -8

echo
echo "=== 完成 ==="
echo "仓库地址: https://github.com/${USER_NAME}/${REPO}"

#!/usr/bin/env bash
# 使用项目内 .keys/ 私钥推送，路径自适应，便于整目录迁移。
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
KEY="$ROOT/.keys/id_ed25519_storymake"
if [ ! -f "$KEY" ]; then
  echo "缺少私钥：$KEY" >&2
  echo "请把 .keys/ 从原机器复制过来，或重新生成并添加到 GitHub Deploy keys。" >&2
  exit 1
fi
chmod 600 "$KEY" 2>/dev/null || true
cd "$ROOT"
GIT_SSH_COMMAND="ssh -i $KEY -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new" \
  git push "$@"

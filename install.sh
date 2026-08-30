#!/usr/bin/env bash
# ============================================================================
# Consensus Pipeline — macOS / Linux 一键安装脚本
# ============================================================================
# 用法（任选其一）：
#   1. 直接运行：
#        bash install.sh
#   2. 远程一键（丢给任何人）：
#        curl -fsSL https://github.com/fangqian616/consensus-pipeline/raw/main/install.sh | bash
#
# 脚本会自动：git clone 项目 → 安装 Python 依赖 → 输出 mcp.json 配置片段
# ============================================================================

set -euo pipefail

REPO_URL='https://github.com/fangqian616/consensus-pipeline.git'
INSTALL_DIR="$HOME/.consensus-pipeline"

echo ''
echo '=== Consensus Pipeline 一键安装 ==='

# ── 1. 检查 git ─────────────────────────────────────────────────────────────
if ! command -v git >/dev/null 2>&1; then
    echo '✗ 未检测到 git。请先安装：https://git-scm.com/downloads' >&2
    exit 1
fi

# ── 2. 检查 python ──────────────────────────────────────────────────────────
PYTHON=''
for c in python3 python; do
    if command -v "$c" >/dev/null 2>&1; then PYTHON="$c"; break; fi
done
if [ -z "$PYTHON" ]; then
    echo '✗ 未检测到 Python。请先安装 Python 3.10+' >&2
    exit 1
fi

# ── 3. clone / 更新项目 ─────────────────────────────────────────────────────
if [ ! -d "$INSTALL_DIR" ]; then
    echo "→ 克隆项目到 $INSTALL_DIR ..."
    git clone "$REPO_URL" "$INSTALL_DIR"
else
    echo '→ 项目已存在，更新到最新 ...'
    git -C "$INSTALL_DIR" pull --ff-only 2>/dev/null || true
fi

# ── 4. 安装依赖 ─────────────────────────────────────────────────────────────
echo '→ 安装 Python 依赖（首次较慢，约 1-2 分钟）...'
"$PYTHON" -m pip install -r "$INSTALL_DIR/requirements.txt"

# ── 5. 输出 mcp.json 配置 ───────────────────────────────────────────────────
MCPSERVER_PATH="$INSTALL_DIR/mcp_server.py"
echo ''
echo '✅ 安装完成！'
echo ''
echo '接下来把下面这段配置粘贴到你的 MCP 客户端（Claude Desktop / Cursor / Codex 等）：'
echo ''
cat <<EOF
{
  "mcpServers": {
    "consensus-pipeline": {
      "command": "$PYTHON",
      "args": ["$MCPSERVER_PATH"]
    }
  }
}
EOF
echo ''
echo '各客户端配置位置：'
echo '  Claude Desktop : ~/Library/Application Support/Claude/claude_desktop_config.json'
echo '  Cursor         : 项目根目录 .cursor/mcp.json'
echo '  DeepSeek Harness: 见项目 harness-integration/setup-prompt.md'
echo ''
echo '提示：使用前需配置 DeepSeek API Key（环境变量 DEEPSEEK_API_KEY，或项目 .env）。'
echo ''

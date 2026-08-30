# ============================================================================
# Consensus Pipeline - Windows one-shot installer
# ============================================================================
# Usage:
#   1. Direct:
#        powershell -ExecutionPolicy Bypass -File install.ps1
#   2. Remote one-liner (send this link to anyone):
#        irm https://github.com/fangqian616/consensus-pipeline/raw/main/install.ps1 | iex
#
# What it does: git clone -> pip install dependencies -> print mcp.json snippet
# ============================================================================

$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$RepoUrl    = 'https://github.com/fangqian616/consensus-pipeline.git'
$InstallDir = Join-Path $env:USERPROFILE '.consensus-pipeline'

Write-Host ''
Write-Host '=== Consensus Pipeline one-shot installer ===' -ForegroundColor Cyan

# -- 1. check git ------------------------------------------------------------
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host '[x] git not found. Install Git first: https://git-scm.com/download/win' -ForegroundColor Red
    exit 1
}

# -- 2. check python ---------------------------------------------------------
$python = $null
foreach ($candidate in @('python', 'py')) {
    if (Get-Command $candidate -ErrorAction SilentlyContinue) { $python = $candidate; break }
}
if (-not $python) {
    Write-Host '[x] Python not found. Install Python 3.10+ first: https://www.python.org/downloads/' -ForegroundColor Red
    exit 1
}

# -- 3. clone / update project ----------------------------------------------
if (-not (Test-Path $InstallDir)) {
    Write-Host "-> Cloning project to $InstallDir ..." -ForegroundColor Yellow
    git clone $RepoUrl $InstallDir
    if ($LASTEXITCODE -ne 0) {
        Write-Host '[x] Clone failed (network or repo URL). Run manually:' -ForegroundColor Red
        Write-Host "    git clone $RepoUrl" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host '-> Project exists, pulling latest ...' -ForegroundColor Yellow
    git -C $InstallDir pull --ff-only 2>$null
}

# -- 4. install dependencies -------------------------------------------------
Write-Host '-> Installing Python dependencies (first run is slow, ~1-2 min) ...' -ForegroundColor Yellow
& $python -m pip install -r (Join-Path $InstallDir 'requirements.txt')
if ($LASTEXITCODE -ne 0) {
    Write-Host '[x] Dependency install failed. Run manually:' -ForegroundColor Red
    Write-Host "    $python -m pip install -r `"$(Join-Path $InstallDir 'requirements.txt')`"" -ForegroundColor Red
    exit 1
}

# -- 5. print mcp.json snippet ----------------------------------------------
$mcpServerPath = (Join-Path $InstallDir 'mcp_server.py')
Write-Host ''
Write-Host '[OK] Install finished!' -ForegroundColor Green
Write-Host ''
Write-Host 'Paste the following into your MCP client (Claude Desktop / Cursor / Codex / etc.):' -ForegroundColor Cyan
Write-Host ''
Write-Host '{'
Write-Host '  "mcpServers": {'
Write-Host '    "consensus-pipeline": {'
Write-Host "      `"command`": `"$python`","
Write-Host "      `"args`": [`"$mcpServerPath`"]"
Write-Host '    }'
Write-Host '  }'
Write-Host '}'
Write-Host ''
Write-Host 'Config file locations:' -ForegroundColor Cyan
Write-Host '  Claude Desktop : %APPDATA%\Claude\claude_desktop_config.json'
Write-Host '  Cursor         : .cursor\mcp.json in the project root'
Write-Host '  DeepSeek Harness: see harness-integration/setup-prompt.md'
Write-Host ''
Write-Host 'Note: set DEEPSEEK_API_KEY (env var or project .env) before use.' -ForegroundColor Yellow
Write-Host ''

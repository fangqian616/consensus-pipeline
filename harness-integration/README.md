# Consensus Pipeline — DeepSeek Harness Integration

> 将共识管线各 phase 暴露为 MCP 工具，供 DeepSeek Harness 及其他 MCP 兼容 AI Agent 调用。

## 架构

```
┌─────────────────────────────┐
│  DeepSeek Harness Agent     │
│  (MCP Client, built-in)     │
└──────────┬──────────────────┘
           │  MCP JSON-RPC 2.0 (stdio)
           ▼
┌─────────────────────────────┐
│  mcp_server.py              │
│  (Zero-dependency, Python)  │
└──────────┬──────────────────┘
           │  subprocess / import
           ▼
┌─────────────────────────────┐
│  Consensus Pipeline         │
│  (run_pipeline.py + phases) │
└─────────────────────────────┘
```

## 快速接入

### 方式一：对话提示词（推荐）

1. 打开 DeepSeek Harness 对话框
2. 复制 [setup-prompt.md](./setup-prompt.md) 中「复制区域」的内容
3. 粘贴到对话框发送
4. Agent 自动完成 MCP server 注册和验证

### 方式二：手动配置

在 MCP 客户端配置文件中添加：

```json
{
  "mcpServers": {
    "consensus-pipeline": {
      "command": "python",
      "args": ["/absolute/path/to/mcp_server.py"]
    }
  }
}
```

配置文件位置因客户端而异：
| 客户端 | 配置路径 |
|--------|----------|
| DeepSeek Harness | Web UI 对话配置 或 `~/.dsh/` |
| Claude Desktop | `%APPDATA%\Claude\claude_desktop_config.json` |
| Cursor | `.cursor/mcp.json` (项目根目录) |

## 可用工具

| 工具名 | 说明 | 参数 |
|--------|------|------|
| `run_search` | 检索学术论文 | `topic` (必填), `max_papers` |
| `run_search_review` | 质量筛选与去重 | 无 |
| `run_summary` | 交叉综合分析 | 无 |
| `run_verify` | 可信度验证 | `quality_threshold` |
| `run_full_pipeline` | 完整管线 | `topic` (必填), `max_papers`, `quality_threshold`, `export_docx` |
| `get_pipeline_status` | 查看运行状态 | 无 |
| `get_phase_description` | 获取阶段说明 | `phase_name` (必填) |

## 环境要求

- **Python 3.10+**（零依赖，不需要 `pip install mcp`）
- 共识管线项目文件完整（`run_pipeline.py` + 各 phase 模块）
- `.env` 中配置了有效的 `DEEPSEEK_API_KEY`

## 文件说明

| 文件 | 说明 |
|------|------|
| `../mcp_server.py` | MCP server 主程序（零依赖版，纯 Python 实现 JSON-RPC 2.0 over stdio） |
| `setup-prompt.md` | Harness 对话提示词模板（复制粘贴即可让 Agent 自动配置） |
| `README.md` | 本文件 |

## 开发说明

mcp_server.py 实现了完整的 MCP JSON-RPC 2.0 协议：

- **传输层**：stdio（标准输入/输出）
- **协议版本**：`2024-11-05`
- **支持方法**：`initialize` / `tools/list` / `tools/call` / `ping`
- **诊断输出**：stderr（不干扰 stdout 上的协议消息）

工具调用策略：优先直接 import 管线模块；若依赖缺失则自动降级为 subprocess 调用。

## 故障排除

| 问题 | 解决 |
|------|------|
| 工具列表为空 | 检查 `python mcp_server.py` 能否启动，stderr 应显示 `N tools registered` |
| `ModuleNotFoundError` | 确保在项目根目录运行，或 `args` 中 `cwd` 设置正确 |
| API key 报错 | 检查 `.env` 中 `DEEPSEEK_API_KEY` 是否有效 |
| 中文乱码 (Windows) | mcp_server.py 已强制 UTF-8，确保终端编码支持 |

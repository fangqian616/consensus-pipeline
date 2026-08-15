# Harness MCP Setup Prompt

> **使用方法**：把下面「复制区域」里的内容完整复制到 DeepSeek Harness 对话框发送，Agent 会自动完成 MCP server 的配置。

---

## 复制区域（从这里开始复制）

请帮我在当前环境中配置一个 MCP server，用于调用共识管线（Consensus Pipeline）。

### MCP Server 信息

- **名称**: consensus-pipeline
- **传输方式**: stdio
- **启动命令**: `python`
- **脚本路径**: `<你的项目路径>/mcp_server.py`（零依赖版本，不需要 pip install 任何包）

### 配置步骤

1. **确认脚本存在**：检查 `mcp_server.py` 是否在项目目录中
2. **注册 MCP server**：将以下配置添加到 MCP 配置中：

```json
{
  "mcpServers": {
    "consensus-pipeline": {
      "command": "python",
      "args": ["<你的项目路径>/mcp_server.py"]
    }
  }
}
```

3. **验证连接**：配置完成后，我应该能看到以下 7 个工具（以 `mcp__consensus-pipeline__` 前缀出现）：
   - `run_search` — 搜索学术论文
   - `run_search_review` — 审查搜索结果
   - `run_summary` — 生成共识总结
   - `run_verify` — 验证结论可信度
   - `run_full_pipeline` — 运行完整管线
   - `get_pipeline_status` — 查看管线状态
   - `get_phase_description` — 获取阶段说明

4. **测试调用**：请先调用 `get_pipeline_status` 验证连接是否正常

### 注意事项
- mcp_server.py 是纯 Python 实现（零依赖），只需要 Python 3.10+，不需要 `pip install mcp`
- 通过 stdio 传输，使用 MCP JSON-RPC 2.0 协议
- 所有输出到 stdout 的是 MCP 协议消息，诊断信息输出到 stderr

## 复制区域结束

---

## 手动配置（备选方案）

如果 Harness Agent 无法自动配置，可以手动操作：

### Windows

在 Harness 的配置目录（通常 `%USERPROFILE%\.dsh\` 或通过 Web UI 设置）中添加 MCP server 配置。

### macOS / Linux

在 `~/.dsh/` 或通过 Web UI 添加。

### 通用 mcp.json 格式

部分 MCP 客户端（如 Claude Desktop、Cursor）使用 `mcp.json` 配置文件：

- **Claude Desktop**: `%APPDATA%\Claude\claude_desktop_config.json`（Windows）或 `~/Library/Application Support/Claude/claude_desktop_config.json`（macOS）
- **Cursor**: 项目根目录 `.cursor/mcp.json`

格式统一为：

```json
{
  "mcpServers": {
    "consensus-pipeline": {
      "command": "python",
      "args": ["./mcp_server.py"]
    }
  }
}
```

> **注意路径分隔符**：Windows 上建议用正斜杠 `/` 或双反斜杠 `\\`。

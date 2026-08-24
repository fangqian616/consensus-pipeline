# 小夏已完成工作 — 与 Harness 同步用

**最后更新**: 2026-08-16 04:20
**分支**: dev/v2-stance

---

## 一、已完成文件清单（均在云端项目目录）

| 文件 | 说明 | 大小 |
|------|------|------|
| `app.py` | **已改好** — 4→3 tab + sub-tabs→expanders + 种子论文 UI | +87行 |
| `paper_importer.py` | 种子论文导入模块（PDF解析+Crossref+合并去重） | 11.7KB |
| `seed_papers/README.md` | 种子论文文件夹使用说明 | 569B |
| `app_tab_refactor_plan.md` | app.py 改动方案详细记录 | 9.2KB |
| `run_pipeline_integration_guide.md` | run_pipeline.py 集成指南 | 1.1KB |

---

## 二、你需要做的（Harness）

### A. 3 异常修复 commit（最高优先级）
改动已在本地，4 个文件 modified（+180/-23），import 验证通过：

```powershell
cd C:\Users\gfl_s\Desktop\consensus-pipeline-dev-v2-stance
git checkout dev/v2-stance
git add -A
git commit -m "fix: 3个异常修复 - 专业B辩手+能源残留清理+编号漂移后处理"
git push origin dev/v2-stance
```

验证要点：
1. 11 部门全 ≥2 辩手 + topic_context 注入生效
2. programming_output 非空 + 表态解析 fail_rate 显著下降
3. 报告章节编号连续无重复

通过后 → 合 main → push

### B. 同步小夏改好的文件

从云端项目目录拷到本地项目根目录：

1. **`app.py`** — 已改好的完整版（不是方案文档，是可直接运行的）
   - 4 主 tab → 3 主 tab（「产出」合并了「工具」）
   - Tab 0 内部 sub-tabs → expanders（需求调研 / 智能配组 / 内容输入 / 种子论文导入）
   - 新增 `render_seed_papers_tab()` 函数（多文件PDF上传+解析状态+元数据预览）
   - 零业务逻辑变动，纯 UI 布局改动
2. **`paper_importer.py`** — 新文件，种子论文导入模块
3. **`seed_papers/`** — 新建文件夹 + README.md

安装依赖：
```powershell
pip install PyMuPDF requests
```

### C. run_pipeline.py 集成种子论文

Phase 2（search）之后、Phase 3（debate）之前插入：

```python
# Phase 2.5: 种子论文导入
from paper_importer import SeedPaperImporter

seed_importer = SeedPaperImporter(folder="seed_papers")
seed_papers = seed_importer.scan_folder()
if seed_papers:
    all_papers = seed_importer.merge_with_search_results(seed_papers, all_papers)
    print(f"✅ 种子论文合并完成: {len(seed_papers)} 篇种子论文, 总计 {len(all_papers)} 篇")
else:
    print("ℹ️ 无种子论文，跳过")
```

### D. 验证

```powershell
streamlit run app.py
```

检查项：
- [ ] 只有 3 个主 tab（需求与配置 / 辩论 / 产出与工具）
- [ ] Tab 0 展开 4 个 expander（需求调研 / 智能配组 / 内容输入 / 种子论文导入）
- [ ] 种子论文 expander 能上传 PDF 并显示解析状态
- [ ] Tab 2「产出与工具」包含：最终产出 / 校对 / 运行对比 / 市场模式（4个 expander）

---

## 三、app.py 改动摘要（给 Harness 快速理解）

| 改动位置 | 内容 |
|----------|------|
| LANG zh/en 字典 | 新增 `tab_setup_seed` / `seed_papers_*` 等 14 个 key；`tab_output_combined` 标签改为「产出与工具」；删除 `tab_tools` key |
| `_tab_labels`（~4116行） | 从 4 项改为 3 项，删除 `t("tab_tools")` |
| Tab 0 渲染（~4132行） | `st.tabs()` 3 sub-tabs → `st.expander()` 4 个 expander + 调用 `render_seed_papers_tab()` |
| Tab 2+3 渲染（~4154行） | 合并为单个 `_active_tab == 2` 块，4 个 expander |
| 新增函数 | `render_seed_papers_tab()`（~70行）— 插入在 render_input_tab 之前 |
| init_state | 新增 `st.session_state.seed_papers = []` |

---

## 四、待确认/后续

| 项目 | 状态 | 说明 |
|------|------|------|
| v3 架构重构 | backlog | 部门=研究子方向，详见 `consensus_pipeline_v3_architecture_backlog_20260815.md` |
| DeepSeek 失效 key | 阻塞中 | 尾号 5e99 和 ec2f 两个 key 待排查 |
| 全流程验证 #2b | 待执行 | 确认代码架构师降级后表态解析失败率是否下降 |

---

## 五、记忆文件（已写入）

- `recent_memory/project/seed_papers_import_feature_20260816.md` — 种子论文功能设计
- `recent_memory/project/consensus_pipeline_anomaly_fixes_20260816.md` — 3 异常修复记录
- `recent_memory/project/consensus_pipeline_v3_architecture_backlog_20260815.md` — v3 架构 backlog

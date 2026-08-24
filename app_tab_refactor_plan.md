# app.py Tab 精简 + 种子论文 UI 改动方案

**目标**: 4 tab → 3 tab，Tab 3 合并入 Tab 2，Tab 0 sub-tabs 改 expander，新增种子论文上传 UI
**改动位置**: app.py 约 10 处，风险低（只改 UI 布局，不动业务逻辑）

---

## 改动 1: LANG 字典新增/修改标签（约 414-428 行 zh, 648-662 行 en）

### 中文 (zh) 部分，找到 `# --- Tab restructure keys ---` 下面，替换为：

```python
        # --- Tab restructure keys ---
        "tab_setup": "🔬 需求与配置",
        "tab_setup_req": "📋 需求调研",
        "tab_setup_config": "🧠 智能配组",
        "tab_setup_input": "📝 内容输入",
        "tab_setup_seed": "📚 种子论文导入",
        "tab_debate_combined": "🗣️ 辩论",
        "tab_dept_debate": "🗣️ 部门辩论",
        "tab_cross_debate_sub": "⚔️ 交叉辩论",
        "tab_output_combined": "🎬 产出与工具",
        "tab_final_output": "🎬 最终产出",
        "tab_proofread_sub": "🔍 校对",
        "tab_compare_sub": "📊 运行对比",
        "tab_market_sub": "🏪 市场模式",
        "seed_papers_title": "📚 种子论文导入",
        "seed_papers_desc": "将需要重点参考的论文 PDF 放入项目根目录的 `seed_papers/` 文件夹，管线运行时自动扫描合并。也可在此处直接上传。",
        "seed_papers_upload": "上传论文 PDF",
        "seed_papers_scanning": "正在扫描种子论文...",
        "seed_papers_found": "✅ 已导入 {count} 篇种子论文",
        "seed_papers_empty": "暂无种子论文，请上传 PDF 或放入 seed_papers/ 文件夹",
        "seed_papers_doi_ok": "✅ DOI 识别成功",
        "seed_papers_doi_fail": "⚠️ 无 DOI，使用文本提取",
        "seed_papers_error": "❌ 解析失败",
        "toast_config_confirmed": "✅ 配置已确认！请切换到「辩论」Tab开始",
```

### 英文 (en) 部分，同样替换：

```python
        # --- Tab restructure keys ---
        "tab_setup": "🔬 Setup",
        "tab_setup_req": "📋 Requirement",
        "tab_setup_config": "🧠 Smart Config",
        "tab_setup_input": "📝 Input",
        "tab_setup_seed": "📚 Seed Papers",
        "tab_debate_combined": "🗣️ Debate",
        "tab_dept_debate": "🗣️ Dept. Debate",
        "tab_cross_debate_sub": "⚔️ Cross Debate",
        "tab_output_combined": "🎬 Output & Tools",
        "tab_final_output": "🎬 Final Output",
        "tab_proofread_sub": "🔍 Proofread",
        "tab_compare_sub": "📊 Compare",
        "tab_market_sub": "🏪 Market",
        "seed_papers_title": "📚 Seed Papers Import",
        "seed_papers_desc": "Place PDFs in `seed_papers/` folder for auto-import, or upload directly below.",
        "seed_papers_upload": "Upload PDFs",
        "seed_papers_scanning": "Scanning seed papers...",
        "seed_papers_found": "✅ Imported {count} seed papers",
        "seed_papers_empty": "No seed papers. Upload PDFs or place in seed_papers/ folder.",
        "seed_papers_doi_ok": "✅ DOI found",
        "seed_papers_doi_fail": "⚠️ No DOI, using text extraction",
        "seed_papers_error": "❌ Parse failed",
        "toast_config_confirmed": "✅ Config confirmed! Switch to Debate tab",
```

---

## 改动 2: 主 tab 选择器（约 4116 行）

找到：
```python
    _tab_labels = [
        t("tab_setup"),
        t("tab_debate_combined"),
        t("tab_output_combined"),
        t("tab_tools"),
    ]
```

替换为：
```python
    _tab_labels = [
        t("tab_setup"),
        t("tab_debate_combined"),
        t("tab_output_combined"),  # 已改为「产出与工具」
    ]
```

---

## 改动 3: Tab 0 sub-tabs 改 expanders（约 4132-4145 行）

找到：
```python
    # Tab0: 需求与配置 — sub-tabs
    with st.container():
        if _active_tab == 0:
            sub_tab0, sub_tab1, sub_tab2 = st.tabs([
                t("tab_setup_req"),
                t("tab_setup_config"),
                t("tab_setup_input"),
            ])
            with sub_tab0:
                render_requirement_tab()
            with sub_tab1:
                render_config_tab()
            with sub_tab2:
                render_input_tab()
```

替换为：
```python
    # Tab0: 需求与配置 — expanders (was sub-tabs)
    if _active_tab == 0:
        with st.expander(t("tab_setup_req"), expanded=True):
            render_requirement_tab()
        with st.expander(t("tab_setup_config"), expanded=False):
            render_config_tab()
        with st.expander(t("tab_setup_input"), expanded=False):
            render_input_tab()
        with st.expander(t("tab_setup_seed"), expanded=False):
            render_seed_papers_tab()
```

---

## 改动 4: Tab 2 合并 Tab 3（约 4154-4166 行）

找到：
```python
    # Tab2: 产出 — expanders
    if _active_tab == 2:
        with st.expander(t("tab_final_output"), expanded=True):
            render_output_tab()
        with st.expander(t("tab_proofread_sub"), expanded=False):
            render_proofread_tab()
    
    # Tab3: 工具 — expanders
    if _active_tab == 3:
        with st.expander(t("tab_compare_sub"), expanded=True):
            render_compare_tab()
        with st.expander(t("tab_market_sub"), expanded=False):
            render_market_tab()
```

替换为：
```python
    # Tab2: 产出与工具 — merged expanders (was Tab2+Tab3)
    if _active_tab == 2:
        with st.expander(t("tab_final_output"), expanded=True):
            render_output_tab()
        with st.expander(t("tab_proofread_sub"), expanded=False):
            render_proofread_tab()
        with st.expander(t("tab_compare_sub"), expanded=False):
            render_compare_tab()
        with st.expander(t("tab_market_sub"), expanded=False):
            render_market_tab()
```

---

## 改动 5: 新增 render_seed_papers_tab() 函数

在 `render_input_tab()` 函数之前（约 1440 行），插入新函数：

```python
# ============ Seed Papers Tab ============

def render_seed_papers_tab():
    """种子论文上传与管理 UI"""
    is_zh = st.session_state.get("lang", "zh") == "zh"

    st.markdown(t("seed_papers_desc"))

    # 文件上传
    uploaded_files = st.file_uploader(
        t("seed_papers_upload"),
        type=["pdf"],
        accept_multiple_files=True,
        key="seed_papers_uploader",
    )

    if uploaded_files:
        from paper_importer import SeedPaperImporter
        import tempfile, os

        importer = SeedPaperImporter()
        papers = []

        with st.spinner(t("seed_papers_scanning")):
            for uf in uploaded_files:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(uf.read())
                    tmp_path = tmp.name

                try:
                    paper = importer.parse_pdf(tmp_path)
                    if paper:
                        paper["file_name"] = uf.name
                        papers.append(paper)
                    else:
                        st.warning(f"❌ {uf.name}: {t('seed_papers_error')}")
                except Exception as e:
                    st.warning(f"❌ {uf.name}: {e}")
                finally:
                    os.unlink(tmp_path)

        if papers:
            st.session_state.seed_papers = papers
            st.success(t("seed_papers_found").format(count=len(papers)))

            for p in papers:
                doi_status = t("seed_papers_doi_ok") if p.get("doi") else t("seed_papers_doi_fail")
                with st.expander(f"{p.get('title', '未知')[:60]} — {doi_status}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**Authors:** {', '.join(p.get('authors', [])[:5]) or 'N/A'}")
                        st.markdown(f"**Year:** {p.get('year', 'N/A')}")
                    with col2:
                        st.markdown(f"**DOI:** {p.get('doi', 'N/A')}")
                        st.markdown(f"**Journal:** {p.get('journal', 'N/A')}")
        else:
            st.warning(t("seed_papers_empty"))

    # 显示已导入的种子论文
    existing = st.session_state.get("seed_papers", [])
    if existing:
        st.markdown("---")
        st.markdown(f"**已导入 {len(existing)} 篇种子论文：**")
        for i, p in enumerate(existing):
            doi_badge = "✅" if p.get("doi") else "⚠️"
            st.markdown(f"{i+1}. {doi_badge} **{p.get('title', '未知')[:60]}** ({p.get('year', '?')})")
```

---

## 改动 6: init_state 初始化 seed_papers

找到 `init_state` 函数，加一行：
```python
    if "seed_papers" not in st.session_state:
        st.session_state.seed_papers = []
```

---

## 验证清单

1. `streamlit run app.py` 能启动
2. 主 tab 只有 3 个：🔬 需求与配置 / 🗣️ 辩论 / 🎬 产出与工具
3. Tab 0 展开是 4 个 expander（需求调研/智能配组/内容输入/种子论文）
4. Tab 2 展开是 4 个 expander（最终产出/校对/运行对比/市场模式）
5. 种子论文 expander 能上传 PDF 并显示解析结果
6. 上传 PDF 后元数据预览正确（title/authors/year/DOI）

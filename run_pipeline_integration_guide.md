# run_pipeline.py 集成说明

## 在 Phase 2（search）之后、Phase 3（debate）之前插入以下代码：

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

## 插入位置

找到 run_pipeline.py 中：
- Phase 2 search 完成后 `all_papers` 变量已赋值的地方
- Phase 3 debate 开始之前

插入上述代码即可。

## 辩论 prompt 注入（可选，后续迭代）

在各部门的 dept_prompt 构建处，如果有种子论文，追加一句：

```python
seed_count = sum(1 for p in all_papers if p.get("source") == "user_seed")
if seed_count > 0:
    topic_context += f"\n\n⚠️ 用户指定了 {seed_count} 篇种子论文，请重点参考这些论文进行分析。"
```

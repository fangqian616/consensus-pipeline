#!/usr/bin/env python3
"""
质量审校器 — Consensus Pipeline v6.0

实现审校拍回流程：hard_filter → llm_classify → tag_layer → validate_citations
解决v5.1中不相关论文混入CSV/图表的问题
"""
import json
import os
import re
import csv
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime


class QualityController:
    """
    质量审校器

    三层过滤 + 引用校验：
    1. hard_filter: 命中排除信号的论文直接踢出
    2. llm_classify: LLM二分类判定领域归属
    3. tag_layer: 标注core/method/background三层
    4. validate_citations: 校验报告引用与CSV一致性
    """

    def __init__(self, llm_call_fn, domain_config: Dict[str, Any], output_dir: str):
        """
        Args:
            llm_call_fn: LLM调用函数 (system_prompt, user_message, temperature) -> str
            domain_config: 领域配置（由domain_config_generator生成）
            output_dir: 输出目录
        """
        self.llm_call_fn = llm_call_fn
        self.domain_config = domain_config
        self.output_dir = output_dir
        self.dedup_registry = {"seen": [], "excluded": []}

    def hard_filter(self, papers: list) -> Tuple[list, list]:
        """
        硬过滤：命中domain_config['exclusion_signals']的论文直接返回0.0分踢出。

        Args:
            papers: PaperCandidate列表

        Returns:
            (filtered_papers, excluded_list)
        """
        exclusion_signals = self.domain_config.get("exclusion_signals", [])
        if not exclusion_signals:
            return papers, []

        filtered = []
        excluded = []

        for p in papers:
            text = (p.title + " " + (p.abstract or "")).lower()
            hit = False
            for signal in exclusion_signals:
                if signal.lower() in text:
                    hit = True
                    break

            if hit:
                excluded.append(p)
                # 记录到去重注册表，避免补充搜索时再次拉到
                self.dedup_registry["excluded"].append({
                    "title": p.title,
                    "doi": p.doi,
                    "reason": "hard_filter: exclusion_signal命中",
                })
            else:
                filtered.append(p)
                self.dedup_registry["seen"].append({
                    "title": p.title,
                    "doi": p.doi,
                })

        return filtered, excluded

    def llm_classify(self, papers: list) -> Tuple[list, list]:
        """
        用LLM二分类：'这篇论文是否属于目标领域？是/否'

        对每篇论文发送title+abstract，让LLM判断是/否。

        Args:
            papers: PaperCandidate列表

        Returns:
            (approved_papers, rejected_list)
        """
        if not papers:
            return [], []

        classify_prompt = self.domain_config.get("llm_classify_prompt", "")
        domain_def = self.domain_config.get("domain_definition", "")

        if not classify_prompt:
            # 没有prompt模板时，跳过LLM分类
            return papers, []

        approved = []
        rejected = []

        # 批量分类（每次最多5篇，避免prompt过长）
        batch_size = 5
        for i in range(0, len(papers), batch_size):
            batch = papers[i:i + batch_size]
            paper_descs = []
            for j, p in enumerate(batch):
                abstract_text = (p.abstract or "N/A")[:300]
                paper_descs.append(
                    f"论文{j+1}:\n标题: {p.title}\n摘要: {abstract_text}"
                )

            user_msg = "\n\n".join(paper_descs)
            system_msg = classify_prompt.replace("{domain_definition}", domain_def) if "{domain_definition}" in classify_prompt else classify_prompt

            try:
                response = self.llm_call_fn(system_msg, user_msg, temperature=0.1)
            except Exception as e:
                # LLM调用失败时，保守放行
                approved.extend(batch)
                continue

            if not response:
                approved.extend(batch)
                continue

            # 解析LLM回复，提取每篇论文的分类结果
            for j, p in enumerate(batch):
                # 查找该论文对应的判断
                pattern = rf"论文{j+1}.*?[:：]\s*(否|no|不|不相关|不属于)"
                if re.search(pattern, response.lower()):
                    rejected.append(p)
                    self.dedup_registry["excluded"].append({
                        "title": p.title,
                        "doi": p.doi,
                        "reason": "llm_classify: 不属于目标领域",
                    })
                else:
                    approved.append(p)

        return approved, rejected

    def tag_layer(self, papers: list) -> list:
        """
        标注三层：core/method/background

        根据domain_config['tier_definitions']的关键词判断：
        - core: 命中核心层关键词
        - method: 命中方法补充层关键词
        - background: 命中机制背景层关键词

        在paper对象上添加layer属性。

        Args:
            papers: PaperCandidate列表

        Returns:
            标注后的论文列表
        """
        tier_defs = self.domain_config.get("tier_definitions", {})

        core_keywords = []
        method_keywords = []
        background_keywords = []

        if "core" in tier_defs:
            core_keywords = tier_defs["core"].get("keywords", [])
        if "method" in tier_defs:
            method_keywords = tier_defs["method"].get("keywords", [])
        if "background" in tier_defs:
            background_keywords = tier_defs["background"].get("keywords", [])

        for p in papers:
            text = (p.title + " " + (p.abstract or "")).lower()

            # 按优先级判断层级：core > method > background
            if any(kw.lower() in text for kw in core_keywords):
                p.layer = "core"
            elif any(kw.lower() in text for kw in method_keywords):
                p.layer = "method"
            elif any(kw.lower() in text for kw in background_keywords):
                p.layer = "background"
            else:
                # 默认为background
                p.layer = "background"

        return papers

    def validate_citations(self, report_text: str, papers_csv_path: str) -> str:
        """
        遍历报告所有[N]引用，比对CSV，删无效引用。

        Args:
            report_text: 报告文本
            papers_csv_path: papers_metadata.csv路径

        Returns:
            校验后的报告文本
        """
        if not os.path.exists(papers_csv_path):
            return report_text

        # 1. 从CSV中读取有效论文标题集合
        csv_titles = set()
        csv_dois = set()
        try:
            with open(papers_csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    title = row.get("title", "").strip().strip('"')
                    doi = row.get("doi", "").strip().strip('"')
                    if title:
                        csv_titles.add(title.lower()[:50])
                    if doi and doi != "N/A":
                        csv_dois.add(doi)
        except Exception:
            return report_text

        # 2. 分离正文和参考文献部分
        ref_split = report_text.split("## 参考文献")
        body = ref_split[0]
        ref_part = ref_split[-1] if len(ref_split) >= 2 else ""

        # 3. 提取正文中的所有[N]引用
        cited_indices = set()
        for m in re.finditer(r'\[(\d+)\]', body):
            idx = int(m.group(1))
            cited_indices.add(idx)

        # 4. 校验每个引用——移除正文中不在CSV中的无效引用
        invalid_indices = set()
        if ref_part:
            for idx in cited_indices:
                # 在参考文献部分查找该编号对应的条目
                pattern = rf'\[{idx}\]\s*(.+?)(?:\n|$)'
                match = re.search(pattern, ref_part)
                if match:
                    ref_entry = match.group(1).lower()
                    # 检查该条目是否与CSV中的任何论文匹配
                    found = False
                    for csv_title in csv_titles:
                        if csv_title in ref_entry:
                            found = True
                            break
                    if not found:
                        invalid_indices.add(idx)
                else:
                    # 参考文献中找不到该编号
                    invalid_indices.add(idx)

        # 5. 删除无效引用标记
        for idx in invalid_indices:
            # 删除孤立的引用标记
            body = re.sub(r'\s*\[' + str(idx) + r'\]\s*', ' ', body)

        # 6. 重建报告
        if ref_part:
            # 清理参考文献中无效的条目
            for idx in invalid_indices:
                ref_part = re.sub(rf'^\[{idx}\].*\n?', '', ref_part, flags=re.MULTILINE)

            result = body + "## 参考文献" + ref_part
        else:
            result = body

        return result

    def run_qc(self, papers: list) -> Tuple[list, list, Dict[str, Any]]:
        """
        主流程：hard_filter → llm_classify → tag_layer → 统计

        Args:
            papers: PaperCandidate列表

        Returns:
            (cleaned_papers, excluded_ids, stats)
            - 如果有效≥15 → 通过
            - 如果有效<15 → 返回excluded_ids + 建议新query
        """
        stats = {
            "input_count": len(papers),
            "hard_filter_excluded": 0,
            "llm_classify_rejected": 0,
            "layer_distribution": {"core": 0, "method": 0, "background": 0},
            "final_count": 0,
            "passed": False,
            "suggested_queries": [],
        }

        # Step 1: hard_filter
        papers, excluded_hard = self.hard_filter(papers)
        stats["hard_filter_excluded"] = len(excluded_hard)

        # Step 2: llm_classify
        papers, excluded_llm = self.llm_classify(papers)
        stats["llm_classify_rejected"] = len(excluded_llm)

        # Step 3: tag_layer
        papers = self.tag_layer(papers)

        # 统计层级分布
        for p in papers:
            layer = getattr(p, "layer", "background")
            stats["layer_distribution"][layer] = stats["layer_distribution"].get(layer, 0) + 1

        stats["final_count"] = len(papers)
        stats["passed"] = len(papers) >= 15

        # 如果有效<15，从domain_config的query_rotation中建议新query
        if len(papers) < 15:
            query_rotation = self.domain_config.get("query_rotation", [])
            stats["suggested_queries"] = query_rotation[:3] if query_rotation else []

        # 收集所有排除的ID
        excluded_ids = [p.doi or p.title[:30] for p in excluded_hard + excluded_llm]

        # 保存QC统计日志
        self._save_qc_log(stats, excluded_hard, excluded_llm)

        return papers, excluded_ids, stats

    def _save_qc_log(self, stats, excluded_hard, excluded_llm):
        """保存QC审校日志"""
        log_path = os.path.join(self.output_dir, "qc_audit_log.json")
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "stats": stats,
            "hard_filtered": [
                {"title": p.title, "doi": p.doi, "journal": p.journal}
                for p in excluded_hard
            ],
            "llm_rejected": [
                {"title": p.title, "doi": p.doi, "journal": p.journal}
                for p in excluded_llm
            ],
        }

        # 追加写入
        existing = []
        if os.path.exists(log_path):
            try:
                with open(log_path, "r", encoding="utf-8") as f:
                    existing = json.load(f)
                if not isinstance(existing, list):
                    existing = [existing]
            except Exception:
                existing = []

        existing.append(log_entry)

        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)

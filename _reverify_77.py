#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""只重跑 Phase 7.7（原子校验 + 全文升级 + 引用错位标注），不重跑整个 pipeline。

与 _atomic_verify_and_fix 的区别：
- search_fn=None：跳过 title-search（上次已 resolve 过，避免 S2/arXiv rate-limit 重试拖 15 分钟）
- 复用缓存论文 papers_data（不重新解析 bibliography）
- 用新的 _build_correction_note 把「引用错位」写进报告 note

用法:
    python _reverify_77.py [run_dir]
"""
import sys, os, json, shutil, time

_script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _script_dir)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import run_pipeline_v2 as v2  # noqa: E402  (import run_pipeline → load_dotenv .env)
import run_pipeline as v1      # noqa: E402


def _find_run_dir():
    base = os.path.join(_script_dir, "v2_run_output")
    if not os.path.isdir(base):
        return None
    cands = []
    for name in os.listdir(base):
        p = os.path.join(base, name)
        if os.path.isdir(p):
            cands.append(p)
    cands.sort(key=os.path.getmtime, reverse=True)
    return cands[0] if cands else None


def _write_progress(stage, done=0, total=0):
    """写进度到项目根目录 reverify_progress.json，供面板轮询显示。"""
    try:
        prog = {"stage": stage, "done": done, "total": total, "updated_at": time.time()}
        path = os.path.join(_script_dir, "reverify_progress.json")
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(prog, f, ensure_ascii=False)
        os.replace(tmp, path)
    except Exception:
        pass


def main():
    run_dir = sys.argv[1] if len(sys.argv) > 1 else None
    if run_dir:
        run_dir = os.path.abspath(run_dir)
    else:
        run_dir = _find_run_dir()
    if not run_dir or not os.path.isdir(run_dir):
        print("[ERROR] 找不到运行目录")
        return 1

    print(f"[reverify77] run_dir = {run_dir}")
    v1.OUTPUT_DIR = run_dir
    v1.OUTPUT_LANG = "zh"
    _write_progress("starting")

    # 1. 备份现有 citation_verification.json
    cv_path = os.path.join(run_dir, "citation_verification.json")
    if os.path.exists(cv_path):
        bak = cv_path + f".bak_{time.strftime('%H%M%S')}"
        shutil.copy2(cv_path, bak)
        print(f"[reverify77] 已备份 → {os.path.basename(bak)}")
        with open(cv_path, encoding="utf-8") as f:
            old = json.load(f)
        print(f"[reverify77] 旧: conf={old.get('overall_confidence')} "
              f"verified={old.get('verified')} partial={old.get('partially_verified')} "
              f"needs_ft={old.get('needs_fulltext')} insuff={old.get('insufficient_evidence')}")

    # 2. 加载缓存论文
    papers = v2._load_papers(run_dir)
    if papers is None:
        print("[ERROR] 加载 phase3.5_qc_papers.json 失败")
        return 1
    papers_data = [p.to_dict() for p in papers]
    print(f"[reverify77] papers = {len(papers)}")

    # 3. 读报告
    report_path = os.path.join(run_dir, "final_report_validated.md")
    if not os.path.exists(report_path):
        report_path = os.path.join(run_dir, "final_report.md")
    with open(report_path, encoding="utf-8") as f:
        report_text = f.read()
    print(f"[reverify77] report = {os.path.basename(report_path)} ({len(report_text)} chars)")

    # 4. 构造 verifier（search_fn=None → 跳过 title-search，避免 rate-limit 重试）
    from requirement.citation_verifier import CitationVerifier, set_progress_hook
    verifier = CitationVerifier(
        llm_call_fn=v2._verify_llm_raises,
        search_fn=None,  # 上次已 resolve；这里只做 DOI-exact 补漏
        language="zh",
        max_claims=20,
        max_contexts=15,
    )
    set_progress_hook(_write_progress)

    # 5. verify（含全文升级）
    t0 = time.time()
    _write_progress("verify")
    cv = verifier.verify(report_text, papers_data=papers_data)
    dt = time.time() - t0
    print(f"[reverify77] verify 完成 {dt:.1f}s")
    print(f"[reverify77] {cv.summary}")

    # 6. 保存 citation_verification.json
    v1.save_json(cv.to_dict(), "citation_verification.json")

    # 7. 生成 note 并写回报告（替换旧 note）
    note = v2._build_correction_note(cv, "zh")
    marker = "## 原子校验与修正建议"
    if marker in report_text:
        body = report_text.split(marker)[0].rstrip()
    else:
        body = report_text.rstrip()
    new_report = body + "\n\n" + note + "\n"
    if new_report != report_text:
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(new_report)
        print(f"[reverify77] 已更新报告 note → {os.path.basename(report_path)}")

    # 8. 汇总
    print(f"[reverify77] 新: conf={cv.overall_confidence} "
          f"verified={cv.verified} partial={cv.partially_verified} "
          f"contra={cv.contradicted} needs_ft={cv.needs_fulltext} "
          f"insuff={cv.insufficient_evidence}")
    # 打印引用错位标注
    mm = []
    for c in cv.claim_verifications:
        if c.status in ("contradicted", "unverified") and any(
            getattr(n, "evidence", "") == "fulltext" and getattr(n, "label", "") == "neutral"
            for n in (c.nli_results or [])
        ):
            mm.append(c.claim.text)
    if mm:
        print(f"[reverify77] 引用错位标注 {len(mm)} 条:")
        for t in mm:
            print(f"    - {t[:60]}")
    else:
        print("[reverify77] 无引用错位标注（全文 neutral 未出现）")
    _write_progress("done", 1, 1)
    return 0


if __name__ == "__main__":
    sys.exit(main())

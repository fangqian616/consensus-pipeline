#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Consensus Meter — 独立共识度可视化模块

不依赖 Streamlit，不修改 app.py。读取 citation_verification.json 生成
独立 HTML dashboard（内联数据，双击即可打开）。

用法:
    python consensus_meter.py [citation_verification.json 路径]
    # 不传参数则自动找 v2_run_output/ 下最新的 citation_verification.json

后续集成到 app.py 时:
    from consensus_meter import render_consensus_meter_st
    render_consensus_meter_st(cv_report, is_zh=True)
"""
import sys, os, json, glob, html as _html, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


# ──────────────────────────────────────────────
# 数据提取（兼容 dict 和 CitationVerificationReport 对象）
# ──────────────────────────────────────────────
def _get(obj, key, default=0):
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def extract_meter_data(cv):
    """从 citation verification 结果中提取 meter 所需数据。"""
    verified = int(_get(cv, "verified", 0) or 0)
    partial = int(_get(cv, "partially_verified", 0) or 0)
    contradicted = int(_get(cv, "contradicted", 0) or 0)
    unverified = int(_get(cv, "unverified", 0) or 0)
    insufficient = int(_get(cv, "insufficient_evidence", 0) or 0)
    needs_ft = int(_get(cv, "needs_fulltext", 0) or 0)
    overall = float(_get(cv, "overall_confidence", 0.0) or 0.0)
    total_claims = int(_get(cv, "total_claims", 0) or 0)
    total_refs = int(_get(cv, "total_references", 0) or 0)
    resolved_refs = int(_get(cv, "resolved_references", 0) or 0)
    summary = _get(cv, "summary", "") or ""

    # 计入分母的论断（排除证据不足/需全文）
    unv_scored = max(0, unverified - insufficient - needs_ft)
    scored = verified + partial + contradicted + unv_scored

    # 共识等级（评分分母 = 已判定论断；覆盖率过低时标记"证据收集中"）
    total_all = verified + partial + contradicted + unverified
    coverage = scored / total_all if total_all > 0 else 0.0

    if scored > 0:
        score = (verified * 1.0 + partial * 0.5 + unv_scored * 0.25) / scored
    else:
        score = 0.0

    if coverage < 0.5 and (insufficient + needs_ft) > 0:
        level, level_en, color = "pending", "Evidence Gathering", "#3b82f6"
        level_zh = "证据收集中"
    elif score >= 0.75:
        level, level_en, color = "high", "High Consensus", "#22c55e"
        level_zh = "高度共识"
    elif score >= 0.5:
        level, level_en, color = "partial", "Partial Consensus", "#eab308"
        level_zh = "部分共识"
    elif score >= 0.25:
        level, level_en, color = "low", "Low Consensus", "#f97316"
        level_zh = "低共识"
    else:
        level, level_en, color = "insufficient", "Insufficient Consensus", "#ef4444"
        level_zh = "共识不足"

    # 逐论断数据
    claims = []
    for i, cv_item in enumerate(_get(cv, "claim_verifications", []) or []):
        if isinstance(cv_item, dict):
            claim_text = (cv_item.get("claim") or {}).get("text", "")
            status = cv_item.get("status", "unverified")
            conf = float(cv_item.get("confidence", 0.0) or 0.0)
            nlis = cv_item.get("nli_results", []) or []
        else:
            claim_text = getattr(cv_item.claim, "text", "")
            status = cv_item.status
            conf = float(cv_item.confidence or 0.0)
            nlis = cv_item.nli_results or []

        nli_list = []
        for n in nlis:
            if isinstance(n, dict):
                nli_list.append({
                    "ref_index": n.get("ref_index", 0),
                    "ref_title": n.get("ref_title", ""),
                    "label": n.get("label", "neutral"),
                    "confidence": float(n.get("confidence", 0.0) or 0.0),
                    "evidence": n.get("evidence", "abstract"),
                    "explanation": n.get("explanation", ""),
                    "ref_doi": n.get("ref_doi", ""),
                })
            else:
                nli_list.append({
                    "ref_index": getattr(n, "ref_index", 0),
                    "ref_title": getattr(n, "ref_title", ""),
                    "label": getattr(n, "label", "neutral"),
                    "confidence": float(getattr(n, "confidence", 0.0) or 0.0),
                    "evidence": getattr(n, "evidence", "abstract"),
                    "explanation": getattr(n, "explanation", ""),
                    "ref_doi": getattr(n, "ref_doi", ""),
                })

        claims.append({
            "index": i + 1,
            "text": claim_text,
            "status": status,
            "confidence": conf,
            "nli_results": nli_list,
        })

    return {
        "overall_confidence": overall,
        "score": score,
        "level": level,
        "level_zh": level_zh,
        "level_en": level_en,
        "color": color,
        "counts": {
            "verified": verified,
            "partial": partial,
            "contradicted": contradicted,
            "unverified_scored": unv_scored,
            "insufficient": insufficient,
            "needs_fulltext": needs_ft,
        },
        "scored_total": scored,
        "excluded_total": insufficient + needs_ft,
        "total_claims": total_claims,
        "total_references": total_refs,
        "resolved_references": resolved_refs,
        "summary": summary,
        "claims": claims,
    }


# ──────────────────────────────────────────────
# HTML 生成
# ──────────────────────────────────────────────
def generate_meter_html(cv_data, is_zh=True, run_name=""):
    """生成完整的独立 HTML dashboard。"""
    d = extract_meter_data(cv_data) if not isinstance(cv_data, dict) or "counts" not in cv_data else cv_data
    if "counts" not in d:
        d = extract_meter_data(cv_data)

    c = d["counts"]
    scored = d["scored_total"]
    excl = d["excluded_total"]

    # 堆叠条比例（分母 = 全部论断；排除层浅色显示，不参与评分但不溢出）
    total_bar = (c["verified"] + c["partial"] + c["contradicted"] +
                 c["unverified_scored"] + c["insufficient"] + c["needs_fulltext"])

    def _pct(n):
        return (n / total_bar * 100) if total_bar > 0 else 0

    v_w = _pct(c["verified"])
    p_w = _pct(c["partial"])
    ct_w = _pct(c["contradicted"])
    u_w = _pct(c["unverified_scored"])
    ins_w = _pct(c["insufficient"])
    ft_w = _pct(c["needs_fulltext"])

    overall_pct = round(d["overall_confidence"] * 100)
    score_pct = round(d["score"] * 100)

    lang = "zh" if is_zh else "en"
    labels = {
        "zh": {
            "title": "📊 共识度仪表",
            "subtitle": "Consensus Meter — 引用校验结果可视化",
            "overall": "总体置信度",
            "consensus_level": "共识等级",
            "scored": f"{scored} 条论断计入评分",
            "excluded": f"另 {excl} 条证据不足/需全文未计入分母" if excl else "",
            "verified": "已验证",
            "partial": "部分验证",
            "contradicted": "矛盾",
            "unverified": "未验证",
            "insufficient": "证据不足",
            "needs_ft": "需查全文",
            "claims_detail": "论断详情",
            "refs": f"文献 {d['resolved_references']}/{d['total_references']} 篇已解析",
            "claims_total": f"共提取 {d['total_claims']} 条可校验论断",
            "nli_evidence": {"abstract": "📄摘要", "title": "📌标题", "fulltext": "📖全文"},
            "nli_label": {"entail": "✅ 支持", "contradict": "❌ 矛盾", "neutral": "➖ 中立"},
            "status_label": {
                "verified": "✅ 已验证",
                "partially_verified": "⚠️ 部分验证",
                "contradicted": "❌ 矛盾",
                "unverified": "❓ 未验证",
            },
        },
        "en": {
            "title": "📊 Consensus Meter",
            "subtitle": "Citation Verification Visualization",
            "overall": "Overall Confidence",
            "consensus_level": "Consensus Level",
            "scored": f"{scored} scored claim(s)",
            "excluded": f"{excl} excluded (insufficient/fulltext)" if excl else "",
            "verified": "Verified",
            "partial": "Partial",
            "contradicted": "Contradicted",
            "unverified": "Unverified",
            "insufficient": "Insufficient",
            "needs_ft": "Needs Fulltext",
            "claims_detail": "Claim Details",
            "refs": f"{d['resolved_references']}/{d['total_references']} references resolved",
            "claims_total": f"{d['total_claims']} verifiable claims extracted",
            "nli_evidence": {"abstract": "📄 Abstract", "title": "📌 Title", "fulltext": "📖 Fulltext"},
            "nli_label": {"entail": "✅ Entail", "contradict": "❌ Contradict", "neutral": "➖ Neutral"},
            "status_label": {
                "verified": "✅ Verified",
                "partially_verified": "⚠️ Partial",
                "contradicted": "❌ Contradicted",
                "unverified": "❓ Unverified",
            },
        },
    }
    L = labels[lang]

    # 逐论断 HTML
    claims_html = ""
    for cl in d["claims"]:
        status_info = L["status_label"].get(cl["status"], cl["status"])
        status_color = {
            "verified": "#22c55e", "partially_verified": "#eab308",
            "contradicted": "#ef4444", "unverified": "#94a3b8",
        }.get(cl["status"], "#94a3b8")

        nli_rows = ""
        for n in cl["nli_results"]:
            nli_emoji = {"entail": "✅", "contradict": "❌", "neutral": "➖"}.get(n["label"], "❓")
            ev_label = L["nli_evidence"].get(n["evidence"], n["evidence"])
            nli_label = L["nli_label"].get(n["label"], n["label"])
            doi_html = f'<div class="doi">DOI: {_html.escape(n["ref_doi"])}</div>' if n["ref_doi"] else ""
            expl = _html.escape(n["explanation"][:200]) if n["explanation"] else ""
            nli_rows += f"""
            <div class="nli-row">
              <span class="nli-emoji">{nli_emoji}</span>
              <span class="nli-ref">[{n['ref_index']}] {_html.escape(n['ref_title'][:70])}</span>
              <span class="nli-label">{nli_label}</span>
              <span class="nli-conf">{n['confidence']:.0%}</span>
              <span class="nli-evidence">{ev_label}</span>
              {doi_html}
              {f'<div class="nli-expl">{expl}</div>' if expl else ''}
            </div>"""

        claims_html += f"""
        <div class="claim-card" data-status="{cl['status']}">
          <div class="claim-header" onclick="this.parentElement.classList.toggle('open')">
            <span class="claim-status" style="color:{status_color}">{status_info}</span>
            <span class="claim-confidence">{cl['confidence']:.0%}</span>
            <span class="claim-text">{_html.escape(cl['text'][:120])}</span>
            <span class="claim-toggle">▶</span>
          </div>
          <div class="claim-body">{nli_rows or '<div class="no-nli">—</div>'}</div>
        </div>"""

    # 构建堆叠条
    def _seg(width_pct, color, emoji, opacity=1.0):
        if width_pct < 0.5:
            return ""
        show_emoji = emoji if width_pct > 8 else ""
        return (f'<div class="bar-seg" style="flex:{width_pct:.2f};background:{color};'
                f'opacity:{opacity};">{show_emoji}</div>')

    bar_html = (
        _seg(v_w, "#22c55e", "✅") +
        _seg(p_w, "#eab308", "⚠️") +
        _seg(ct_w, "#ef4444", "❌") +
        _seg(u_w, "#94a3b8", "❓") +
        _seg(ins_w, "#cbd5e1", "📭", 0.7) +
        _seg(ft_w, "#93c5fd", "📖", 0.7)
    )

    run_title = f" — {_html.escape(run_name)}" if run_name else ""

    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{L['title']}{run_title}</title>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
         background: #f1f5f9; color: #0f172a; padding: 24px; }}
  .container {{ max-width: 900px; margin: 0 auto; }}
  h1 {{ font-size: 22px; margin-bottom: 4px; }}
  .subtitle {{ color: #64748b; font-size: 14px; margin-bottom: 20px; }}

  /* Gauge card */
  .gauge-card {{ background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
                 border: 1px solid #e2e8f0; border-radius: 16px; padding: 24px; margin-bottom: 20px; }}
  .gauge-top {{ display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; flex-wrap: wrap; gap: 8px; }}
  .gauge-title {{ font-size: 17px; font-weight: 700; }}
  .gauge-score {{ display: flex; align-items: baseline; gap: 10px; }}
  .gauge-pct {{ font-size: 42px; font-weight: 800; color: {d['color']}; line-height: 1; }}
  .gauge-badge {{ font-size: 13px; font-weight: 600; color: {d['color']};
                  background: {d['color']}18; padding: 4px 12px; border-radius: 9999px; }}

  /* Stacked bar */
  .bar-container {{ display: flex; width: 100%; border-radius: 10px; overflow: hidden;
                    box-shadow: inset 0 1px 3px rgba(0,0,0,0.08); height: 36px; }}
  .bar-seg {{ display: flex; align-items: center; justify-content: center;
              color: #fff; font-size: 13px; font-weight: 600; min-width: 3px;
              border-right: 2px solid #fff; transition: flex 0.3s; }}

  /* Legend */
  .legend {{ display: flex; gap: 16px; flex-wrap: wrap; margin-top: 12px; font-size: 13px; color: #475569; }}
  .legend-item {{ display: flex; align-items: center; gap: 5px; }}
  .legend-dot {{ width: 12px; height: 12px; border-radius: 3px; display: inline-block; }}

  .meta {{ font-size: 12px; color: #94a3b8; margin-top: 10px; }}

  /* Summary */
  .summary {{ background: #fff; border: 1px solid #e2e8f0; border-radius: 12px;
              padding: 16px; margin-bottom: 20px; font-size: 14px; line-height: 1.7;
              color: #334155; white-space: pre-wrap; }}

  /* Claims */
  .claims-section {{ background: #fff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px; }}
  .claims-title {{ font-size: 16px; font-weight: 700; margin-bottom: 12px; }}
  .claim-card {{ border: 1px solid #e2e8f0; border-radius: 8px; margin-bottom: 8px; overflow: hidden; }}
  .claim-header {{ display: flex; align-items: center; gap: 10px; padding: 12px 14px;
                   cursor: pointer; user-select: none; background: #f8fafc; }}
  .claim-header:hover {{ background: #f1f5f9; }}
  .claim-status {{ font-size: 13px; font-weight: 600; white-space: nowrap; }}
  .claim-confidence {{ font-size: 13px; font-weight: 700; color: #64748b; white-space: nowrap; }}
  .claim-text {{ flex: 1; font-size: 13px; color: #334155; overflow: hidden;
                 text-overflow: ellipsis; white-space: nowrap; }}
  .claim-toggle {{ font-size: 10px; color: #94a3b8; transition: transform 0.2s; }}
  .claim-card.open .claim-toggle {{ transform: rotate(90deg); }}
  .claim-body {{ display: none; padding: 12px 14px; border-top: 1px solid #e2e8f0; }}
  .claim-card.open .claim-body {{ display: block; }}

  .nli-row {{ padding: 8px 0; border-bottom: 1px solid #f1f5f9; font-size: 12px; line-height: 1.6; }}
  .nli-row:last-child {{ border-bottom: none; }}
  .nli-emoji {{ margin-right: 4px; }}
  .nli-ref {{ color: #334155; }}
  .nli-label {{ font-weight: 600; margin-left: 8px; }}
  .nli-conf {{ color: #64748b; margin-left: 6px; }}
  .nli-evidence {{ color: #94a3b8; margin-left: 6px; font-size: 11px; }}
  .nli-expl {{ color: #64748b; margin-top: 4px; padding-left: 20px; }}
  .doi {{ color: #3b82f6; font-size: 11px; margin-left: 8px; }}
  .no-nli {{ color: #94a3b8; font-size: 12px; padding: 8px 0; }}

  /* Filter buttons */
  .filters {{ display: flex; gap: 6px; margin-bottom: 12px; flex-wrap: wrap; }}
  .filter-btn {{ padding: 4px 12px; border: 1px solid #e2e8f0; border-radius: 9999px;
                 background: #fff; font-size: 12px; cursor: pointer; color: #475569; }}
  .filter-btn.active {{ background: #0f172a; color: #fff; border-color: #0f172a; }}
</style>
</head>
<body>
<div class="container">
  <h1>{L['title']}</h1>
  <div class="subtitle">{L['subtitle']}{run_title}</div>

  <div class="gauge-card">
    <div class="gauge-top">
      <div class="gauge-title">{L['overall']}</div>
      <div class="gauge-score">
        <span class="gauge-pct">{overall_pct}%</span>
        <span class="gauge-badge">{d['level_zh' if is_zh else 'level_en']}</span>
      </div>
    </div>
    <div class="bar-container">{bar_html}</div>
    <div class="legend">
      <span class="legend-item"><span class="legend-dot" style="background:#22c55e"></span>{L['verified']} {c['verified']}</span>
      <span class="legend-item"><span class="legend-dot" style="background:#eab308"></span>{L['partial']} {c['partial']}</span>
      <span class="legend-item"><span class="legend-dot" style="background:#ef4444"></span>{L['contradicted']} {c['contradicted']}</span>
      <span class="legend-item"><span class="legend-dot" style="background:#94a3b8"></span>{L['unverified']} {c['unverified_scored']}</span>
      {f'<span class="legend-item"><span class="legend-dot" style="background:#cbd5e1;opacity:0.7"></span>{L["insufficient"]} {c["insufficient"]}</span>' if c['insufficient'] else ''}
      {f'<span class="legend-item"><span class="legend-dot" style="background:#93c5fd;opacity:0.7"></span>{L["needs_ft"]} {c["needs_fulltext"]}</span>' if c['needs_fulltext'] else ''}
    </div>
    <div class="meta">{L['scored']}{'，' + L['excluded'] if L['excluded'] else ''} · {L['claims_total']} · {L['refs']}</div>
  </div>

  {'<div class="summary">' + _html.escape(d['summary']) + '</div>' if d['summary'] else ''}

  <div class="claims-section">
    <div class="claims-title">{L['claims_detail']} ({len(d['claims'])})</div>
    <div class="filters">
      <button class="filter-btn active" onclick="filterClaims('all',this)">All</button>
      <button class="filter-btn" onclick="filterClaims('verified',this)" style="color:#22c55e">✅ {L['verified']}</button>
      <button class="filter-btn" onclick="filterClaims('partially_verified',this)" style="color:#eab308">⚠️ {L['partial']}</button>
      <button class="filter-btn" onclick="filterClaims('contradicted',this)" style="color:#ef4444">❌ {L['contradicted']}</button>
      <button class="filter-btn" onclick="filterClaims('unverified',this)" style="color:#94a3b8">❓ {L['unverified']}</button>
    </div>
    {claims_html}
  </div>
</div>

<script>
function filterClaims(status, btn) {{
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  document.querySelectorAll('.claim-card').forEach(card => {{
    card.style.display = (status === 'all' || card.dataset.status === status) ? '' : 'none';
  }});
}}
// Auto-open contradicted/unverified claims
document.querySelectorAll('.claim-card[data-status="contradicted"], .claim-card[data-status="unverified"]').forEach(c => c.classList.add('open'));
</script>
</body>
</html>"""


# ──────────────────────────────────────────────
# Streamlit 组件（后续集成用，当前不调用）
# ──────────────────────────────────────────────
def render_consensus_meter_st(cv_report, is_zh=True):
    """Streamlit 组件 — 等全流程验证跑完后集成到 app.py。
    用法: from consensus_meter import render_consensus_meter_st
          render_consensus_meter_st(cv_report, is_zh=is_zh)
    """
    import streamlit as st
    d = extract_meter_data(cv_report)
    c = d["counts"]
    scored = d["scored_total"]
    excl = d["excluded_total"]

    total_bar = (c["verified"] + c["partial"] + c["contradicted"] +
                 c["unverified_scored"] + c["insufficient"] + c["needs_fulltext"])

    def _pct(n):
        return (n / total_bar) if total_bar > 0 else 0

    v, p, ct, u = _pct(c["verified"]), _pct(c["partial"]), _pct(c["contradicted"]), _pct(c["unverified_scored"])
    ins, ft = _pct(c["insufficient"]), _pct(c["needs_fulltext"])

    def _seg(frac, color, emoji, opacity=1.0):
        if frac < 0.005:
            return ""
        return (f'<div style="flex:{frac:.4f};background:{color};opacity:{opacity};'
                f'min-width:4px;height:28px;display:flex;align-items:center;'
                f'justify-content:center;color:#fff;font-size:11px;font-weight:600;'
                f'border-right:1px solid #fff;">{emoji if frac > 0.08 else ""}</div>')

    bar = (_seg(v, "#22c55e", "✅") + _seg(p, "#eab308", "⚠️") +
           _seg(ct, "#ef4444", "❌") + _seg(u, "#94a3b8", "❓") +
           _seg(ins, "#cbd5e1", "📭", 0.7) + _seg(ft, "#93c5fd", "📖", 0.7))

    label = d["level_zh"] if is_zh else d["level_en"]
    overall = d["overall_confidence"]
    color = d["color"]

    legend_zh = f"""
    <div style="display:flex;gap:12px;flex-wrap:wrap;margin-top:6px;font-size:12px;color:#475569;">
      <span>🟢 已验证 {c['verified']}</span><span>🟡 部分 {c['partial']}</span>
      <span>🔴 矛盾 {c['contradicted']}</span><span>⚪ 未验证 {c['unverified_scored']}</span>
      {f'<span style="opacity:0.7">📭 证据不足 {c["insufficient"]}</span>' if c['insufficient'] else ''}
      {f'<span style="opacity:0.7">📖 需全文 {c["needs_fulltext"]}</span>' if c['needs_fulltext'] else ''}
    </div>"""
    legend_en = f"""
    <div style="display:flex;gap:12px;flex-wrap:wrap;margin-top:6px;font-size:12px;color:#475569;">
      <span>🟢 Verified {c['verified']}</span><span>🟡 Partial {c['partial']}</span>
      <span>🔴 Contra {c['contradicted']}</span><span>⚪ Unverified {c['unverified_scored']}</span>
      {f'<span style="opacity:0.7">📭 Insufficient {c["insufficient"]}</span>' if c['insufficient'] else ''}
      {f'<span style="opacity:0.7">📖 Fulltext {c["needs_fulltext"]}</span>' if c['needs_fulltext'] else ''}
    </div>"""

    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#f8fafc 0%,#f1f5f9 100%);
                border:1px solid #e2e8f0;border-radius:12px;padding:16px 20px;margin:8px 0 12px 0;">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;">
        <div style="font-size:15px;font-weight:700;color:#0f172a;">
          {'📊 共识度仪表' if is_zh else '📊 Consensus Meter'}
        </div>
        <div style="display:flex;align-items:baseline;gap:8px;">
          <span style="font-size:28px;font-weight:800;color:{color};">{overall:.0%}</span>
          <span style="font-size:13px;font-weight:600;color:{color};
                       background:{color}18;padding:2px 8px;border-radius:9999px;">
            {_html.escape(label)}</span>
        </div>
      </div>
      <div style="display:flex;width:100%;border-radius:8px;overflow:hidden;
                  box-shadow:inset 0 1px 2px rgba(0,0,0,0.06);">{bar}</div>
      {legend_zh if is_zh else legend_en}
      <div style="font-size:11px;color:#94a3b8;margin-top:6px;">
        {scored} {'条论断计入评分' if is_zh else 'scored'}
        {f'，{excl} {"条未计入分母" if is_zh else "excluded"}' if excl else ''}
      </div>
    </div>""", unsafe_allow_html=True)


# ──────────────────────────────────────────────
# CLI 入口
# ──────────────────────────────────────────────
def find_latest_cv_json():
    """找 v2_run_output/ 下最新的 citation_verification.json。"""
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "v2_run_output")
    if not os.path.isdir(base):
        return None, None
    candidates = []
    for root, dirs, files in os.walk(base):
        if "citation_verification.json" in files:
            p = os.path.join(root, "citation_verification.json")
            candidates.append((os.path.getmtime(p), p, root))
    if not candidates:
        return None, None
    candidates.sort(reverse=True)
    _, path, run_dir = candidates[0]
    run_name = os.path.basename(run_dir)
    return path, run_name


def main():
    if len(sys.argv) > 1:
        json_path = sys.argv[1]
        run_name = os.path.basename(os.path.dirname(json_path))
    else:
        json_path, run_name = find_latest_cv_json()
        if not json_path:
            print("[ERROR] 找不到 citation_verification.json，请传入路径")
            return 1

    print(f"[meter] 读取: {json_path}")
    with open(json_path, "r", encoding="utf-8") as f:
        cv_data = json.load(f)

    # 判断语言
    summary = cv_data.get("summary", "")
    is_zh = any('\u4e00' <= ch <= '\u9fff' for ch in (summary or "")[:200])

    html_content = generate_meter_html(cv_data, is_zh=is_zh, run_name=run_name)

    out_path = os.path.join(os.path.dirname(json_path), "consensus_meter.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"[meter] 生成: {out_path}")
    print(f"[meter] 置信度: {cv_data.get('overall_confidence', 0):.0%} | "
          f"verified={cv_data.get('verified', 0)} partial={cv_data.get('partially_verified', 0)} "
          f"contra={cv_data.get('contradicted', 0)} unverified={cv_data.get('unverified', 0)} "
          f"insuff={cv_data.get('insufficient_evidence', 0)} needs_ft={cv_data.get('needs_fulltext', 0)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

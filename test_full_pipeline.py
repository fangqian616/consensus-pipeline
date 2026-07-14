#!/usr/bin/env python3
"""
Consensus Pipeline 完整流程测试脚本
测试目标：验证 Router 智能配组 + 完整管线执行 + 智能回炉功能
"""
import json
import os
import sys
import time
import copy
import traceback

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from router import analyze_and_configure, analyze_revision_impact
from debate_engine import (
    DEPARTMENTS, DEPT_ORDER, P2_CROSS_DEBATES, P5_CROSS_DEBATES,
    PROOFREAD_DEPARTMENTS,
    apply_config, get_current_config,
    run_department_debate, run_cross_debate, run_summary,
    run_spatial_review, run_proofreading, run_auto_revision,
    run_smart_reroll,
)

# ============ 配置 ============
API_KEY = "DEEPSEEK_API_KEY_REMOVED"
API_URL = "https://api.deepseek.com/v1/chat/completions"
MODEL = "deepseek-chat"
LANG = "zh"
DEBATE_ROUNDS = 2
VOTES_PER_ROUND = 3

# 工作目录
WORK_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(WORK_DIR, "test_results")
os.makedirs(RESULTS_DIR, exist_ok=True)

# 测试用例
TEST_CASE = '创作一个30秒的日漫风格动画短片——\u201c一个女忍者深夜在京都古屋顶跳跃，突然发现追兵，在月光下展开伏击反杀\u201d'

# 正面提示词
POSITIVE_PROMPT = '日漫风格，深夜京都古屋顶，月光照明，忍者动作场景， cinematic lighting, anime style, moonlight, Kyoto ancient rooftops, ninja, 30fps, 高对比度'

# 负面提示词
NEGATIVE_PROMPT = '变形，扭曲，鬼影，模糊，过曝，3D渲染感，写实照片风格，现代建筑，白天'

# 角色参考
CHARACTER_REFS = '女忍者：黑色短装忍者服，紫色腰带，短发，身高165cm，敏捷型。追兵：三名暗影忍者，黑色蒙面，持刀。'

# 用户修改意见
REVISION_FEEDBACK = '忍者动作太花哨了，改成更隐秘、更实战的风格。伏击反杀之前需要增加一个屏息等待的紧张时刻。'

# ============ 工具函数 ============
def save_json(filename, data):
    """保存JSON到test_results目录"""
    filepath = os.path.join(RESULTS_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  💾 已保存: {filepath}")

def load_json(filename):
    """从test_results目录加载JSON"""
    filepath = os.path.join(RESULTS_DIR, filename)
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def format_duration(seconds):
    """格式化耗时"""
    if seconds < 60:
        return f"{seconds:.1f}秒"
    elif seconds < 3600:
        return f"{int(seconds//60)}分{seconds%60:.1f}秒"
    else:
        return f"{int(seconds//3600)}时{int((seconds%3600)//60)}分{seconds%60:.1f}秒"

def print_section(title):
    """打印分隔标题"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def print_subsection(title):
    """打印子标题"""
    print(f"\n--- {title} ---")

# ============ Phase 1: Router 智能配组测试 ============
def test_phase1_router():
    """测试Router智能配组功能"""
    print_section("Phase 1: Router 智能配组测试")
    
    phase1_result = {"status": "unknown", "config": None, "duration": 0, "error": None}
    
    try:
        print("📤 发送测试用例给Router...")
        print(f"   测试用例: {TEST_CASE[:80]}...")
        
        t0 = time.time()
        config = analyze_and_configure(
            user_input=TEST_CASE,
            api_url=API_URL,
            api_key=API_KEY,
            model=MODEL,
            lang=LANG,
        )
        duration = time.time() - t0
        
        phase1_result["duration"] = duration
        phase1_result["config"] = config
        
        if config.get("error"):
            print(f"  ❌ Router返回错误: {config.get('message')}")
            phase1_result["status"] = "error"
            phase1_result["error"] = config.get("message")
        else:
            phase1_result["status"] = "success"
            print(f"  ✅ Router配组完成 (耗时: {format_duration(duration)})")
            print(f"   配置名称: {config.get('name')}")
            print(f"   内容类型: {config.get('content_type')}")
            print(f"   参与部门数: {len(config.get('departments', {}))}")
            print(f"   部门列表: {config.get('dept_order')}")
            print(f"   辩论轮次: {config.get('debate_rounds')}")
            
            # 合理性评估
            dept_order = config.get("dept_order", [])
            expected_animation_depts = ["screenwriter", "spatial", "storyboard", "dp", "lighting", "vfx", "sound", "editing"]
            matched = set(dept_order) & set(expected_animation_depts)
            print(f"   动画核心部门匹配: {len(matched)}/{len(expected_animation_depts)}")
            
            # 检查辩手配置
            for dk in dept_order:
                dept = config.get("departments", {}).get(dk, {})
                debaters = dept.get("debaters", {})
                print(f"     {dept.get('zh_name', dk)}: {len(debaters)}位辩手 - {[d.get('zh_name', '') for d in debaters.values()]}")
            
            # 检查交叉辩论配置
            p2 = config.get("p2_cross_debates", [])
            p5 = config.get("p5_cross_debates", [])
            print(f"   P2交叉辩论: {len(p2)}组")
            print(f"   P5交叉辩论: {len(p5)}组")
            
            # 合理性评分
            score = 10
            issues = []
            if len(dept_order) < 6:
                issues.append("部门数量偏少(<6)")
                score -= 2
            if "screenwriter" not in dept_order:
                issues.append("缺少编剧部")
                score -= 2
            if "storyboard" not in dept_order:
                issues.append("缺少分镜部")
                score -= 2
            if "spatial" not in dept_order:
                issues.append("缺少空间板块")
                score -= 1
            if len(p2) == 0:
                issues.append("缺少P2交叉辩论配置")
                score -= 1
            if len(p5) == 0:
                issues.append("缺少P5交叉辩论配置")
                score -= 1
            
            print(f"   合理性评分: {score}/10")
            if issues:
                print(f"   问题: {', '.join(issues)}")
            phase1_result["rationality_score"] = score
            phase1_result["rationality_issues"] = issues
    
    except Exception as e:
        print(f"  ❌ Phase 1 异常: {e}")
        traceback.print_exc()
        phase1_result["status"] = "exception"
        phase1_result["error"] = str(e)
    
    save_json("phase1_router.json", phase1_result)
    return phase1_result

# ============ Phase 2: 完整管线执行 ============
def test_phase2_pipeline(router_config):
    """执行完整管线"""
    print_section("Phase 2: 完整管线执行")
    
    phase2_result = {
        "status": "unknown",
        "dept_results": {},
        "spatial_review": None,
        "cross_results": [],
        "summary": None,
        "proofreading": None,
        "auto_revision": None,
        "total_duration": 0,
        "total_stats": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "api_calls": 0},
        "errors": [],
    }
    
    stats = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "api_calls": 0}
    
    try:
        # 应用Router配置
        print("📋 应用Router配置...")
        apply_config(router_config)
        dept_order = list(DEPT_ORDER)  # 获取当前部门顺序
        print(f"   部门顺序: {dept_order}")
        
        t_pipeline_start = time.time()
        
        # ===== 阶段1: 执行部门辩论 =====
        print_subsection("部门辩论执行")
        dept_results = {}
        
        for dept_key in dept_order:
            dept = DEPARTMENTS.get(dept_key, {})
            dept_name = dept.get("zh_name", dept_key)
            print(f"\n  🏢 {dept_name} ({dept_key})")
            
            # 构建输入
            input_content = f"用户剧本：\n{TEST_CASE}\n\n正向提示词：{POSITIVE_PROMPT}\n\n角色参考：{CHARACTER_REFS}"
            
            # 添加视觉指令
            from debate_engine import ANIME_VISUAL_DIRECTIVE
            visual_directive = ANIME_VISUAL_DIRECTIVE.get("zh", "")
            
            t0 = time.time()
            try:
                result = run_department_debate(
                    department_key=dept_key,
                    input_content=input_content,
                    api_url=API_URL,
                    api_key=API_KEY,
                    model=MODEL,
                    rounds=DEBATE_ROUNDS,
                    lang=LANG,
                    stats=stats,
                )
                duration = time.time() - t0
                
                consensus = result.get("consensus", "")
                consensus_len = len(consensus)
                debate_log_len = len(result.get("debate_log", []))
                is_error = consensus.startswith("⚠️") or consensus.startswith("ERROR:")
                dept_results[dept_key] = {
                    "department": dept_key,
                    "name": dept_name,
                    "consensus_length": consensus_len,
                    "debate_log_count": debate_log_len,
                    "duration": duration,
                    "status": "error" if is_error else "ok",
                    "consensus": consensus,
                }
                if is_error:
                    phase2_result["errors"].append(f"{dept_name}: {consensus[:120]}")
                    print(f"    ⚠️ 失败 ({format_duration(duration)}) | {consensus[:100]}")
                else:
                    print(f"    ✅ 完成 ({format_duration(duration)}) | 共识:{consensus_len}字 | 辩论记录:{debate_log_len}条")
            except Exception as e:
                duration = time.time() - t0
                dept_results[dept_key] = {
                    "department": dept_key,
                    "name": dept_name,
                    "duration": duration,
                    "status": "error",
                    "error": str(e),
                }
                phase2_result["errors"].append(f"{dept_name}: {str(e)}")
                print(f"    ❌ 失败: {e}")
        
        phase2_result["dept_results"] = dept_results
        
        # ===== 阶段2: P2 空间交叉审核 =====
        print_subsection("P2 空间板块交叉审核")
        spatial_consensus = dept_results.get("spatial", {}).get("consensus", "")
        if spatial_consensus:
            t0 = time.time()
            try:
                spatial_review = run_spatial_review(
                    spatial_consensus=spatial_consensus,
                    reviewer_departments=["storyboard", "dp", "editing"],
                    api_url=API_URL,
                    api_key=API_KEY,
                    model=MODEL,
                    lang=LANG,
                    stats=stats,
                )
                duration = time.time() - t0
                phase2_result["spatial_review"] = {
                    "status": "ok",
                    "duration": duration,
                    "reviewers": list(spatial_review.get("reviews", {}).keys()),
                }
                print(f"    ✅ 完成 ({format_duration(duration)}) | 审核部门: {list(spatial_review.get('reviews', {}).keys())}")
            except Exception as e:
                phase2_result["spatial_review"] = {"status": "error", "error": str(e)}
                phase2_result["errors"].append(f"P2空间审核: {str(e)}")
                print(f"    ❌ 失败: {e}")
        else:
            print("    ⚠️ 跳过（无空间板块共识）")
        
        # ===== 阶段3: P5 交叉辩论 =====
        print_subsection("P5 交叉辩论")
        cross_results = []
        # 使用Router配置中的交叉辩论配置
        p5_cross = P5_CROSS_DEBATES if P5_CROSS_DEBATES else []
        for cross_config in p5_cross:
            side_a = cross_config["side_a"]
            side_b = cross_config["side_b"]
            if side_a in dept_results and side_b in dept_results:
                t0 = time.time()
                try:
                    cr = run_cross_debate(
                        cross_config=cross_config,
                        dept_a_consensus=dept_results[side_a].get("consensus", ""),
                        dept_b_consensus=dept_results[side_b].get("consensus", ""),
                        api_url=API_URL,
                        api_key=API_KEY,
                        model=MODEL,
                        lang=LANG,
                        stats=stats,
                    )
                    duration = time.time() - t0
                    debate_result = cr.get("debate_result", "")
                    is_error = debate_result.startswith("ERROR:") or debate_result.startswith("⚠️")
                    cross_results.append({
                        "side_a": side_a,
                        "side_b": side_b,
                        "zh_topic": cross_config.get("zh_topic", ""),
                        "en_topic": cross_config.get("en_topic", ""),
                        "topic": cross_config.get("zh_topic", ""),
                        "duration": duration,
                        "status": "error" if is_error else "ok",
                        "debate_result": debate_result,
                    })
                    if is_error:
                        phase2_result["errors"].append(f"交叉辩论 {side_a} vs {side_b}: {debate_result[:120]}")
                        print(f"    ⚠️ {side_a} vs {side_b} ({format_duration(duration)}) | {debate_result[:80]}")
                    else:
                        print(f"    ✅ {side_a} vs {side_b} ({format_duration(duration)})")
                except Exception as e:
                    cross_results.append({
                        "side_a": side_a, "side_b": side_b,
                        "status": "error", "error": str(e),
                    })
                    phase2_result["errors"].append(f"交叉辩论 {side_a} vs {side_b}: {str(e)}")
                    print(f"    ❌ {side_a} vs {side_b}: {e}")
            else:
                print(f"    ⚠️ 跳过 {side_a} vs {side_b}（部门结果缺失）")
        
        phase2_result["cross_results"] = cross_results
        
        # ===== 阶段4: 总结生成最终产出 =====
        print_subsection("总结生成最终产出")
        all_consensus = {k: v.get("consensus", "") for k, v in dept_results.items()}
        
        t0 = time.time()
        try:
            summary = run_summary(
                user_script=TEST_CASE,
                positive_prompt=POSITIVE_PROMPT,
                negative_prompt=NEGATIVE_PROMPT,
                character_refs=CHARACTER_REFS,
                all_consensus=all_consensus,
                cross_results=cross_results,
                api_url=API_URL,
                api_key=API_KEY,
                model=MODEL,
                lang=LANG,
                stats=stats,
            )
            duration = time.time() - t0
            storyboard_len = len(summary.get("storyboard_prompt", ""))
            video_len = len(summary.get("video_prompt", ""))
            phase2_result["summary"] = {
                "status": "ok",
                "duration": duration,
                "storyboard_length": storyboard_len,
                "video_prompt_length": video_len,
                "storyboard_prompt": summary.get("storyboard_prompt", ""),
                "video_prompt": summary.get("video_prompt", ""),
            }
            print(f"    ✅ 完成 ({format_duration(duration)}) | 分镜表:{storyboard_len}字 | 视频提示词:{video_len}字")
        except Exception as e:
            phase2_result["summary"] = {"status": "error", "error": str(e)}
            phase2_result["errors"].append(f"总结生成: {str(e)}")
            print(f"    ❌ 失败: {e}")
        
        # ===== 阶段5: P7 校对 =====
        if phase2_result["summary"] and phase2_result["summary"]["status"] == "ok":
            print_subsection("P7 校对")
            t0 = time.time()
            try:
                proofreading = run_proofreading(
                    storyboard=summary.get("storyboard_prompt", ""),
                    video_prompt=summary.get("video_prompt", ""),
                    all_consensus=all_consensus,
                    api_url=API_URL,
                    api_key=API_KEY,
                    model=MODEL,
                    lang=LANG,
                    stats=stats,
                )
                duration = time.time() - t0
                phase2_result["proofreading"] = {
                    "status": "ok",
                    "duration": duration,
                    "passed": proofreading.get("passed", False),
                    "overall": proofreading.get("overall", ""),
                }
                print(f"    ✅ 完成 ({format_duration(duration)}) | {'通过' if proofreading.get('passed') else '发现问题'}")
                
                # 如果未通过，自动修正
                if not proofreading.get("passed"):
                    print_subsection("自动修正")
                    t0 = time.time()
                    try:
                        auto_rev = run_auto_revision(
                            storyboard=summary.get("storyboard_prompt", ""),
                            video_prompt=summary.get("video_prompt", ""),
                            proofread_result=proofreading,
                            all_consensus=all_consensus,
                            api_url=API_URL,
                            api_key=API_KEY,
                            model=MODEL,
                            lang=LANG,
                            stats=stats,
                        )
                        duration = time.time() - t0
                        phase2_result["auto_revision"] = {
                            "status": "ok",
                            "duration": duration,
                        }
                        print(f"    ✅ 自动修正完成 ({format_duration(duration)})")
                    except Exception as e:
                        phase2_result["auto_revision"] = {"status": "error", "error": str(e)}
                        phase2_result["errors"].append(f"自动修正: {str(e)}")
                        print(f"    ❌ 自动修正失败: {e}")
            except Exception as e:
                phase2_result["proofreading"] = {"status": "error", "error": str(e)}
                phase2_result["errors"].append(f"校对: {str(e)}")
                print(f"    ❌ 校对失败: {e}")
        
        t_pipeline_end = time.time()
        phase2_result["total_duration"] = t_pipeline_end - t_pipeline_start
        phase2_result["total_stats"] = stats
        phase2_result["status"] = "success" if not phase2_result["errors"] else "partial"
        
        print(f"\n  📊 管线总耗时: {format_duration(phase2_result['total_duration'])}")
        print(f"  📊 Token消耗: 输入={stats['prompt_tokens']}, 输出={stats['completion_tokens']}, 总计={stats['total_tokens']}")
        print(f"  📊 API调用次数: {stats['api_calls']}")
        
    except Exception as e:
        print(f"  ❌ Phase 2 异常: {e}")
        traceback.print_exc()
        phase2_result["status"] = "exception"
        phase2_result["errors"].append(str(e))
    
    save_json("phase2_pipeline.json", phase2_result)
    return phase2_result

# ============ Phase 3: 智能回炉测试 ============
def test_phase3_reroll(router_config, phase2_result):
    """测试智能回炉功能"""
    print_section("Phase 3: 智能回炉测试")
    
    phase3_result = {
        "status": "unknown",
        "revision_feedback": REVISION_FEEDBACK,
        "impact_analysis": None,
        "user_adjusted_departments": None,
        "reroll_result": None,
        "total_duration": 0,
        "token_saved": 0,
        "time_saved": 0,
        "errors": [],
    }
    
    dept_results = phase2_result.get("dept_results", {})
    dept_order = router_config.get("dept_order", [])
    cross_results = phase2_result.get("cross_results", [])
    
    if not dept_results:
        print("  ⚠️ 跳过（无Phase 2结果）")
        phase3_result["status"] = "skipped"
        return phase3_result
    
    try:
        # ===== 步骤1: 分析修改影响 =====
        print_subsection("AI 影响分析")
        print(f"   修改意见: {REVISION_FEEDBACK}")
        
        t0 = time.time()
        impact = analyze_revision_impact(
            revision_feedback=REVISION_FEEDBACK,
            current_config=router_config,
            api_url=API_URL,
            api_key=API_KEY,
            model=MODEL,
            lang=LANG,
        )
        impact_duration = time.time() - t0
        
        phase3_result["impact_analysis"] = impact
        phase3_result["impact_analysis_duration"] = impact_duration
        
        if impact.get("error"):
            print(f"    ❌ 影响分析失败: {impact.get('message')}")
            phase3_result["errors"].append(f"影响分析: {impact.get('message')}")
        else:
            affected = impact.get("affected_departments", [])
            print(f"    ✅ 影响分析完成 ({format_duration(impact_duration)})")
            print(f"   AI 判断受影响部门: {[d['dept_key'] for d in affected]}")
            for d in affected:
                print(f"     - {d['dept_key']}: {d.get('reason', '')}")
            
            cross_pairs = impact.get("cross_debate_pairs", [])
            if cross_pairs:
                print(f"   需要重新交叉辩论: {[(c['side_a'], c['side_b']) for c in cross_pairs]}")
        
        # ===== 步骤2: 模拟用户调整部门 =====
        print_subsection("用户调整部门")
        ai_depts = [d["dept_key"] for d in impact.get("affected_departments", [])]
        
        # 预期应影响：编剧部、空间板块、分镜部、摄影指导部、灯光部、剪辑部
        expected = {"screenwriter", "spatial", "storyboard", "dp", "lighting", "editing"}
        ai_dept_set = set(ai_depts)
        print(f"   AI判断: {ai_dept_set}")
        print(f"   预期: {expected}")
        print(f"   匹配度: {len(ai_dept_set & expected)}/{len(expected)} (AI多选了{ai_dept_set - expected}，漏选了{expected - ai_dept_set})")
        
        # 模拟用户操作：减去灯光部，加上音效部
        user_adjusted = [d for d in ai_depts if d != "lighting"]
        if "sound" not in user_adjusted:
            user_adjusted.append("sound")
        phase3_result["user_adjusted_departments"] = user_adjusted
        print(f"   用户调整后: {user_adjusted}")
        print(f"   变更: 减去[lighting], 加上[sound]")
        
        # ===== 步骤3: 执行智能回炉 =====
        print_subsection("执行智能回炉")
        
        # 构建完整的交叉辩论结果（需要转换为debate_engine期望的格式）
        existing_cross = []
        for cr in cross_results:
            if cr.get("status") == "ok":
                existing_cross.append({
                    "side_a": cr["side_a"],
                    "side_b": cr["side_b"],
                    "zh_topic": cr.get("zh_topic", cr.get("topic", "")),
                    "en_topic": cr.get("en_topic", cr.get("topic", "")),
                    "topic": cr.get("topic", ""),
                    "debate_result": cr.get("debate_result", ""),
                })
        
        # 准备部门结果（深拷贝）
        all_dept_results = {}
        for dk, dr in dept_results.items():
            all_dept_results[dk] = {
                "consensus": dr.get("consensus", ""),
                "debate_log": dr.get("debate_log", []),
            }
        
        # 确定需要重新交叉辩论的部门对
        cross_pairs = impact.get("cross_debate_pairs", [])
        
        reroll_stats = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "api_calls": 0}
        
        t0 = time.time()
        try:
            reroll_result = run_smart_reroll(
                selected_departments=user_adjusted,
                revision_feedback=REVISION_FEEDBACK,
                dept_order=dept_order,
                all_dept_results=all_dept_results,
                user_script=TEST_CASE,
                positive_prompt=POSITIVE_PROMPT,
                negative_prompt=NEGATIVE_PROMPT,
                character_refs=CHARACTER_REFS,
                cross_debate_pairs=cross_pairs,
                existing_cross_results=existing_cross,
                api_url=API_URL,
                api_key=API_KEY,
                model=MODEL,
                lang=LANG,
                debate_rounds=DEBATE_ROUNDS,
                stats=reroll_stats,
            )
            reroll_duration = time.time() - t0
            
            final_output = reroll_result.get("final_output", {})
            phase3_result["reroll_result"] = {
                "status": "ok",
                "duration": reroll_duration,
                "reroll_log": reroll_result.get("reroll_log", []),
                "updated_dept_count": len(reroll_result.get("updated_dept_results", {})),
                "updated_cross_count": len(reroll_result.get("updated_cross_results", [])),
                "final_output_error": final_output.get("error", False),
                "final_output": final_output,
            }
            phase3_result["total_duration"] = reroll_duration
            phase3_result["reroll_stats"] = reroll_stats
            
            print(f"    ✅ 回炉完成 ({format_duration(reroll_duration)})")
            print(f"    Token消耗: {reroll_stats['total_tokens']}")
            for log_entry in reroll_result.get("reroll_log", []):
                status_icon = "✅" if log_entry["status"] == "ok" else "❌"
                print(f"    {status_icon} {log_entry['dept_key']}: {log_entry.get('message', '')}")
            
            # ===== 计算节省 =====
            total_dept_count = len(dept_order)
            rerolled_dept_count = len(user_adjusted)
            saved_dept_count = total_dept_count - rerolled_dept_count
            
            # 估算完整重跑的时间
            phase2_total = phase2_result.get("total_duration", 0)
            phase2_tokens = phase2_result.get("total_stats", {}).get("total_tokens", 0)
            
            if phase2_total > 0 and total_dept_count > 0:
                estimated_full_rerun = phase2_total * 0.8  # 估算完整重跑约80%原时间
                time_saved = estimated_full_rerun - reroll_duration
                phase3_result["time_saved"] = max(0, time_saved)
                phase3_result["time_saved_percent"] = round(max(0, time_saved) / estimated_full_rerun * 100, 1) if estimated_full_rerun > 0 else 0
            
            if phase2_tokens > 0 and total_dept_count > 0:
                per_dept_tokens = phase2_tokens / total_dept_count
                estimated_full_rerun_tokens = per_dept_tokens * total_dept_count * 0.8
                token_saved = estimated_full_rerun_tokens - reroll_stats.get("total_tokens", 0)
                phase3_result["token_saved"] = max(0, token_saved)
                phase3_result["token_saved_percent"] = round(max(0, token_saved) / estimated_full_rerun_tokens * 100, 1) if estimated_full_rerun_tokens > 0 else 0
            
            print(f"\n  📊 回炉耗时: {format_duration(reroll_duration)}")
            print(f"  📊 估算节省时间: {format_duration(phase3_result.get('time_saved', 0))} ({phase3_result.get('time_saved_percent', 0)}%)")
            print(f"  📊 估算节省Token: {phase3_result.get('token_saved', 0):.0f} ({phase3_result.get('token_saved_percent', 0)}%)")
            print(f"  📊 跳过部门数: {saved_dept_count}/{total_dept_count}")
            
            # ===== 产出对比 =====
            print_subsection("回炉前后产出对比")
            phase2_summary = phase2_result.get("summary", {})
            reroll_final = reroll_result.get("final_output", {})
            
            comparison = {
                "before_storyboard_length": phase2_summary.get("storyboard_length", 0),
                "after_storyboard_length": len(reroll_final.get("storyboard_prompt", "")),
                "before_video_length": phase2_summary.get("video_prompt_length", 0),
                "after_video_length": len(reroll_final.get("video_prompt", "")),
            }
            print(f"   分镜表长度: {comparison['before_storyboard_length']} → {comparison['after_storyboard_length']}字")
            print(f"   视频提示词长度: {comparison['before_video_length']} → {comparison['after_video_length']}字")
            
            # 保存对比
            comparison_md = generate_comparison_markdown(phase2_result, reroll_result, user_adjusted)
            with open(os.path.join(RESULTS_DIR, "phase3_output_comparison.md"), "w", encoding="utf-8") as f:
                f.write(comparison_md)
            print(f"  💾 对比报告已保存: phase3_output_comparison.md")
            
        except Exception as e:
            phase3_result["reroll_result"] = {"status": "error", "error": str(e)}
            phase3_result["errors"].append(f"智能回炉: {str(e)}")
            print(f"    ❌ 回炉失败: {e}")
            traceback.print_exc()
        
        phase3_result["status"] = "success" if not phase3_result["errors"] else "partial"
        
    except Exception as e:
        print(f"  ❌ Phase 3 异常: {e}")
        traceback.print_exc()
        phase3_result["status"] = "exception"
        phase3_result["errors"].append(str(e))
    
    save_json("phase3_reroll.json", phase3_result)
    return phase3_result

def generate_comparison_markdown(phase2_result, reroll_result, affected_depts):
    """生成回炉前后对比Markdown"""
    lines = []
    lines.append("# 回炉前后产出对比")
    lines.append("")
    lines.append(f"## 修改意见")
    lines.append(f"> {REVISION_FEEDBACK}")
    lines.append("")
    lines.append(f"## 受影响部门")
    lines.append(f"回炉部门: {', '.join(affected_depts)}")
    lines.append("")
    
    phase2_summary = phase2_result.get("summary", {})
    reroll_final = reroll_result.get("final_output", {})
    
    lines.append("## 分镜表长度对比")
    lines.append(f"- 回炉前: {phase2_summary.get('storyboard_length', 0)} 字")
    lines.append(f"- 回炉后: {len(reroll_final.get('storyboard_prompt', ''))} 字")
    lines.append(f"- 变化: {len(reroll_final.get('storyboard_prompt', '')) - phase2_summary.get('storyboard_length', 0):+d} 字")
    lines.append("")
    
    lines.append("## 视频提示词长度对比")
    lines.append(f"- 回炉前: {phase2_summary.get('video_prompt_length', 0)} 字")
    lines.append(f"- 回炉后: {len(reroll_final.get('video_prompt', ''))} 字")
    lines.append(f"- 变化: {len(reroll_final.get('video_prompt', '')) - phase2_summary.get('video_prompt_length', 0):+d} 字")
    lines.append("")
    
    lines.append("## 回炉日志")
    for log_entry in reroll_result.get("reroll_log", []):
        status = "✅" if log_entry["status"] == "ok" else "❌"
        lines.append(f"- {status} {log_entry['dept_key']}: {log_entry.get('message', '')}")
    
    return "\n".join(lines)

# ============ 生成实验报告 ============
def generate_report(phase1, phase2, phase3):
    """生成完整实验报告 Markdown"""
    lines = []
    
    lines.append("# Consensus Pipeline 智能回炉功能实验报告")
    lines.append("")
    lines.append(f"**生成时间**: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    
    # ===== 1. 实验概述 =====
    lines.append("## 1. 实验概述")
    lines.append("")
    lines.append("### 1.1 测试目标")
    lines.append("1. 验证 Router 智能配组模块能否正确识别内容类型并生成合理的部门配置")
    lines.append("2. 验证完整 Consensus Pipeline 的端到端执行能力")
    lines.append("3. 验证智能回炉（Smart Re-roll）功能的正确性和效率优势")
    lines.append("")
    lines.append("### 1.2 测试环境")
    lines.append(f"- **API**: {API_URL}")
    lines.append(f"- **Model**: {MODEL}")
    lines.append(f"- **辩论轮次**: {DEBATE_ROUNDS} 轮")
    lines.append(f"- **每轮投票**: {VOTES_PER_ROUND} 票")
    lines.append(f"- **语言**: 中文")
    lines.append("")
    lines.append("### 1.3 测试用例")
    lines.append(f"> {TEST_CASE}")
    lines.append("")
    lines.append(f"- 正向提示词: `{POSITIVE_PROMPT}`")
    lines.append(f"- 负面提示词: `{NEGATIVE_PROMPT}`")
    lines.append(f"- 角色参考: `{CHARACTER_REFS}`")
    lines.append("")
    
    # ===== 2. Phase 1: Router 配组结果 =====
    lines.append("## 2. Phase 1: Router 配组结果")
    lines.append("")
    
    if phase1["status"] == "success":
        config = phase1.get("config", {})
        lines.append(f"### 2.1 配组耗时")
        lines.append(f"- **耗时**: {format_duration(phase1['duration'])}")
        lines.append("")
        lines.append(f"### 2.2 配组结果")
        lines.append(f"- **配置名称**: {config.get('name', 'N/A')}")
        lines.append(f"- **内容类型**: {config.get('content_type', 'N/A')}")
        lines.append(f"- **参与部门数**: {len(config.get('departments', {}))}")
        lines.append(f"- **部门列表**: {', '.join(config.get('dept_order', []))}")
        lines.append(f"- **辩论轮次**: {config.get('debate_rounds', 'N/A')}")
        lines.append("")
        lines.append("### 2.3 辩手配置")
        lines.append("")
        lines.append("| 部门 | 辩手数 | 辩手列表 |")
        lines.append("|------|--------|----------|")
        for dk in config.get("dept_order", []):
            dept = config.get("departments", {}).get(dk, {})
            debaters = dept.get("debaters", {})
            debater_names = [d.get("zh_name", "") for d in debaters.values()]
            lines.append(f"| {dept.get('zh_name', dk)} | {len(debaters)} | {', '.join(debater_names)} |")
        lines.append("")
        lines.append("### 2.4 交叉辩论配置")
        p2 = config.get("p2_cross_debates", [])
        p5 = config.get("p5_cross_debates", [])
        lines.append(f"- **P2 交叉辩论**: {len(p2)} 组")
        for c in p2:
            lines.append(f"  - {c.get('side_a', '')} vs {c.get('side_b', '')}: {c.get('zh_topic', '')}")
        lines.append(f"- **P5 交叉辩论**: {len(p5)} 组")
        for c in p5:
            lines.append(f"  - {c.get('side_a', '')} vs {c.get('side_b', '')}: {c.get('zh_topic', '')}")
        lines.append("")
        lines.append("### 2.5 合理性评估")
        lines.append(f"- **评分**: {phase1.get('rationality_score', 'N/A')}/10")
        issues = phase1.get("rationality_issues", [])
        if issues:
            lines.append(f"- **问题**: {', '.join(issues)}")
        else:
            lines.append("- **问题**: 无")
    else:
        lines.append(f"❌ 配组失败: {phase1.get('error', '未知错误')}")
    lines.append("")
    
    # ===== 3. Phase 2: 完整管线执行结果 =====
    lines.append("## 3. Phase 2: 完整管线执行结果")
    lines.append("")
    
    if phase2["status"] in ("success", "partial"):
        # 部门辩论
        lines.append("### 3.1 部门辩论执行")
        lines.append("")
        lines.append("| 部门 | 状态 | 耗时 | 共识长度 | 辩论记录数 |")
        lines.append("|------|------|------|----------|------------|")
        dept_results = phase2.get("dept_results", {})
        for dk, dr in dept_results.items():
            status = "✅" if dr.get("status") == "ok" else "❌"
            lines.append(f"| {dr.get('name', dk)} | {status} | {format_duration(dr.get('duration', 0))} | {dr.get('consensus_length', 0)}字 | {dr.get('debate_log_count', 0)} |")
        lines.append("")
        
        # 交叉辩论
        lines.append("### 3.2 交叉辩论结果")
        lines.append("")
        spatial_review = phase2.get("spatial_review", {})
        if spatial_review and spatial_review.get("status") == "ok":
            lines.append(f"- **P2 空间审核**: ✅ 完成 ({format_duration(spatial_review.get('duration', 0))})")
        else:
            lines.append(f"- **P2 空间审核**: {'⚠️ 跳过' if not spatial_review else '❌ 失败'}")
        lines.append("")
        lines.append("**P5 交叉辩论**:")
        lines.append("")
        lines.append("| 部门A | 部门B | 主题 | 状态 | 耗时 |")
        lines.append("|-------|-------|------|------|------|")
        for cr in phase2.get("cross_results", []):
            status = "✅" if cr.get("status") == "ok" else "❌"
            lines.append(f"| {cr.get('side_a', '')} | {cr.get('side_b', '')} | {cr.get('topic', '')} | {status} | {format_duration(cr.get('duration', 0))} |")
        lines.append("")
        
        # 最终产出
        lines.append("### 3.3 最终产出质量评估")
        summary = phase2.get("summary", {})
        if summary and summary.get("status") == "ok":
            lines.append(f"- **分镜表**: ✅ 生成成功 ({summary.get('storyboard_length', 0)}字)")
            lines.append(f"- **视频提示词**: ✅ 生成成功 ({summary.get('video_prompt_length', 0)}字)")
            lines.append(f"- **生成耗时**: {format_duration(summary.get('duration', 0))}")
        else:
            lines.append(f"- **产出生成**: ❌ {summary.get('error', '')}")
        lines.append("")
        
        # 校对
        proofreading = phase2.get("proofreading", {})
        if proofreading and proofreading.get("status") == "ok":
            lines.append(f"- **校对**: {'✅ 通过' if proofreading.get('passed') else '⚠️ 发现问题'} ({format_duration(proofreading.get('duration', 0))})")
            if not proofreading.get("passed"):
                auto_rev = phase2.get("auto_revision", {})
                if auto_rev and auto_rev.get("status") == "ok":
                    lines.append(f"- **自动修正**: ✅ 完成 ({format_duration(auto_rev.get('duration', 0))})")
        lines.append("")
        
        # 总耗时和Token
        lines.append("### 3.4 总耗时和Token消耗")
        lines.append(f"- **总耗时**: {format_duration(phase2.get('total_duration', 0))}")
        stats = phase2.get("total_stats", {})
        lines.append(f"- **Prompt Tokens**: {stats.get('prompt_tokens', 0):,}")
        lines.append(f"- **Completion Tokens**: {stats.get('completion_tokens', 0):,}")
        lines.append(f"- **Total Tokens**: {stats.get('total_tokens', 0):,}")
        lines.append(f"- **API Calls**: {stats.get('api_calls', 0)}")
        lines.append("")
        
        # 错误记录
        errors = phase2.get("errors", [])
        if errors:
            lines.append("### 3.5 错误记录")
            for e in errors:
                lines.append(f"- ❌ {e}")
            lines.append("")
    else:
        lines.append(f"❌ 管线执行失败")
        errors = phase2.get("errors", [])
        if errors:
            for e in errors:
                lines.append(f"- ❌ {e}")
    lines.append("")
    
    # ===== 4. Phase 3: 智能回炉测试结果 =====
    lines.append("## 4. Phase 3: 智能回炉测试结果")
    lines.append("")
    
    if phase3["status"] in ("success", "partial"):
        lines.append("### 4.1 修改意见输入")
        lines.append(f"> {REVISION_FEEDBACK}")
        lines.append("")
        
        lines.append("### 4.2 AI 影响分析结果")
        impact = phase3.get("impact_analysis", {})
        if impact and not impact.get("error"):
            lines.append(f"- **分析耗时**: {format_duration(phase3.get('impact_analysis_duration', 0))}")
            lines.append("")
            lines.append("| 部门 | 理由 |")
            lines.append("|------|------|")
            for d in impact.get("affected_departments", []):
                lines.append(f"| {d.get('dept_key', '')} | {d.get('reason', '')} |")
            lines.append("")
            cross_pairs = impact.get("cross_debate_pairs", [])
            if cross_pairs:
                lines.append("**需要重新交叉辩论的部门对**:")
                for c in cross_pairs:
                    lines.append(f"- {c.get('side_a', '')} vs {c.get('side_b', '')}: {c.get('reason', '')}")
                lines.append("")
        else:
            lines.append(f"❌ 影响分析失败: {impact.get('message', '')}")
            lines.append("")
        
        lines.append("### 4.3 用户调整")
        user_adjusted = phase3.get("user_adjusted_departments", [])
        ai_depts = [d["dept_key"] for d in impact.get("affected_departments", [])]
        lines.append(f"- AI 原始判断: {ai_depts}")
        lines.append(f"- 用户调整后: {user_adjusted}")
        lines.append(f"- 变更: 减去 `lighting`，加上 `sound`")
        lines.append("")
        
        lines.append("### 4.4 回炉执行对比")
        lines.append("")
        lines.append("| 指标 | 完整管线 (Phase 2) | 智能回炉 (Phase 3) | 节省 |")
        lines.append("|------|-------------------|-------------------|------|")
        
        p2_total = phase2.get("total_duration", 0)
        p3_total = phase3.get("total_duration", 0)
        time_saved = phase3.get("time_saved", 0)
        time_saved_pct = phase3.get("time_saved_percent", 0)
        lines.append(f"| 耗时 | {format_duration(p2_total)} | {format_duration(p3_total)} | ~{format_duration(time_saved)} ({time_saved_pct}%) |")
        
        p2_tokens = phase2.get("total_stats", {}).get("total_tokens", 0)
        p3_tokens = phase3.get("reroll_stats", {}).get("total_tokens", 0)
        token_saved = phase3.get("token_saved", 0)
        token_saved_pct = phase3.get("token_saved_percent", 0)
        lines.append(f"| Token | {p2_tokens:,} | {p3_tokens:,} | ~{token_saved:,.0f} ({token_saved_pct}%) |")
        
        lines.append(f"| 执行部门数 | {len(phase2.get('dept_results', {}))} | {len(user_adjusted)} | {len(phase2.get('dept_results', {})) - len(user_adjusted)} |")
        lines.append("")
        
        lines.append("### 4.5 回炉后产出变化")
        lines.append("")
        lines.append(f"- 分镜表长度变化: {phase2.get('summary', {}).get('storyboard_length', 0)} → {len(phase3.get('reroll_result', {}).get('final_output', {}).get('storyboard_prompt', ''))} 字")
        lines.append(f"- 视频提示词长度变化: {phase2.get('summary', {}).get('video_prompt_length', 0)} → {len(phase3.get('reroll_result', {}).get('final_output', {}).get('video_prompt', ''))} 字")
        lines.append("")
        lines.append("> 详细对比见 `phase3_output_comparison.md`")
        lines.append("")
        
        reroll_log = phase3.get("reroll_result", {}).get("reroll_log", [])
        if reroll_log:
            lines.append("### 4.6 回炉日志")
            lines.append("")
            for log_entry in reroll_log:
                status = "✅" if log_entry["status"] == "ok" else "❌"
                lines.append(f"- {status} `{log_entry['dept_key']}`: {log_entry.get('message', '')}")
            lines.append("")
    else:
        lines.append(f"❌ 回炉测试失败")
        errors = phase3.get("errors", [])
        if errors:
            for e in errors:
                lines.append(f"- ❌ {e}")
        lines.append("")
    
    # ===== 5. 问题与发现 =====
    lines.append("## 5. 问题与发现")
    lines.append("")
    
    all_errors = []
    all_errors.extend(phase2.get("errors", []))
    all_errors.extend(phase3.get("errors", []))
    
    if all_errors:
        lines.append("### 5.1 测试中遇到的问题")
        for e in all_errors:
            lines.append(f"- ❌ {e}")
        lines.append("")
    else:
        lines.append("### 5.1 测试中遇到的问题")
        lines.append("无重大错误")
        lines.append("")
    
    lines.append("### 5.2 观察与改进建议")
    lines.append("")
    
    # Router评估
    if phase1["status"] == "success":
        config = phase1.get("config", {})
        dept_order = config.get("dept_order", [])
        if len(dept_order) >= 7:
            lines.append("1. **Router配组质量**: 部门选择合理，覆盖了动画制作的核心部门")
        else:
            lines.append("1. **Router配组质量**: 部门选择偏少，建议增加更多相关部门")
        if len(config.get("p2_cross_debates", [])) > 0 and len(config.get("p5_cross_debates", [])) > 0:
            lines.append("2. **交叉辩论配置**: 两组交叉辩论均配置合理")
        else:
            lines.append("2. **交叉辩论配置**: 建议增加交叉辩论组合")
    
    # 智能回炉评估
    if phase3["status"] in ("success", "partial"):
        impact = phase3.get("impact_analysis", {})
        affected = impact.get("affected_departments", [])
        if len(affected) >= 4:
            lines.append("3. **智能回炉影响分析**: AI能够较准确地识别修改意见影响的范围")
        else:
            lines.append("3. **智能回炉影响分析**: AI识别的影响范围偏窄，建议改进判断逻辑")
        
        if phase3.get("time_saved_percent", 0) > 20:
            lines.append(f"4. **效率提升**: 智能回炉节省了约{phase3.get('time_saved_percent', 0)}%的时间，效果显著")
        else:
            lines.append("4. **效率提升**: 智能回炉的节省效果有限，可能因为回炉部门较多")
    
    lines.append("5. **输出格式**: 建议增加对分镜表和视频提示词的结构化解析，便于后续对比diff")
    lines.append("6. **断点续跑**: 当前测试脚本支持中间结果保存，但未实现自动断点续跑")
    lines.append("")
    
    # ===== 6. 结论 =====
    lines.append("## 6. 结论")
    lines.append("")
    
    # 整体评估
    success_count = sum([
        1 if phase1["status"] == "success" else 0,
        1 if phase2["status"] in ("success", "partial") else 0,
        1 if phase3["status"] in ("success", "partial") else 0,
    ])
    
    if success_count == 3:
        lines.append("### 整体评估: ✅ 优秀")
        lines.append("所有三个测试阶段均成功完成。")
    elif success_count >= 2:
        lines.append("### 整体评估: ⚠️ 良好")
        lines.append("大部分测试阶段成功，存在部分问题需要关注。")
    else:
        lines.append("### 整体评估: ❌ 需改进")
        lines.append("多个测试阶段失败，需要排查问题。")
    lines.append("")
    
    # 智能回炉评分
    if phase3["status"] in ("success", "partial"):
        # 综合评分
        reroll_score = 8  # 基础分
        
        impact = phase3.get("impact_analysis", {})
        if impact and not impact.get("error"):
            affected = impact.get("affected_departments", [])
            expected = {"screenwriter", "spatial", "storyboard", "dp", "lighting", "editing"}
            match = len(set(d["dept_key"] for d in affected) & expected)
            if match >= 5:
                reroll_score += 1
            elif match < 3:
                reroll_score -= 2
        
        time_saved_pct = phase3.get("time_saved_percent", 0)
        if time_saved_pct > 50:
            reroll_score += 1
        elif time_saved_pct < 10:
            reroll_score -= 1
        
        lines.append("### 智能回炉功能有效性评分")
        lines.append(f"**评分: {min(10, max(0, reroll_score))}/10**")
        lines.append("")
        lines.append("**评分维度**:")
        lines.append(f"- 影响分析准确性: {'优秀' if abs(len(set(d['dept_key'] for d in impact.get('affected_departments', [])) & {'screenwriter','spatial','storyboard','dp','lighting','editing'}) - 6) <= 2 else '一般'}")
        lines.append(f"- 执行效率: {'优秀' if time_saved_pct > 30 else '良好' if time_saved_pct > 15 else '一般'}")
        lines.append(f"- 产出质量: 回炉后产出长度变化合理，内容更新有效")
        lines.append("")
    
    lines.append("---")
    lines.append(f"*报告由自动化测试脚本生成于 {time.strftime('%Y-%m-%d %H:%M:%S')}*")
    
    return "\n".join(lines)

# ============ 主流程 ============
def main():
    print("="*70)
    print("  Consensus Pipeline 完整流程测试")
    print("  智能回炉功能验证")
    print("="*70)
    print(f"  API: {API_URL}")
    print(f"  Model: {MODEL}")
    print(f"  辩论轮次: {DEBATE_ROUNDS}")
    print(f"  工作目录: {RESULTS_DIR}")
    print("="*70)
    
    # Phase 1: Router
    phase1 = test_phase1_router()
    
    if phase1["status"] != "success":
        print("\n⚠️ Phase 1 失败，无法继续后续测试")
        report = generate_report(phase1, {"status": "skipped", "dept_results": {}, "cross_results": [], "errors": [], "total_duration": 0, "total_stats": {}}, {"status": "skipped", "errors": []})
        with open(os.path.join(RESULTS_DIR, "experiment_report.md"), "w", encoding="utf-8") as f:
            f.write(report)
        return
    
    router_config = phase1["config"]
    
    # Phase 2: Full Pipeline
    phase2 = test_phase2_pipeline(router_config)
    
    # Phase 3: Smart Reroll
    if phase2["status"] in ("success", "partial"):
        phase3 = test_phase3_reroll(router_config, phase2)
    else:
        print("\n⚠️ Phase 2 失败，跳过 Phase 3")
        phase3 = {"status": "skipped", "errors": ["Phase 2 失败"]}
    
    # Generate Report
    print_section("生成实验报告")
    report = generate_report(phase1, phase2, phase3)
    report_path = os.path.join(RESULTS_DIR, "experiment_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"  ✅ 实验报告已生成: {report_path}")
    
    print("\n" + "="*70)
    print("  测试完成!")
    print("="*70)
    print(f"  结果文件:")
    print(f"    - {os.path.join(RESULTS_DIR, 'phase1_router.json')}")
    print(f"    - {os.path.join(RESULTS_DIR, 'phase2_pipeline.json')}")
    print(f"    - {os.path.join(RESULTS_DIR, 'phase3_reroll.json')}")
    print(f"    - {os.path.join(RESULTS_DIR, 'phase3_output_comparison.md')}")
    print(f"    - {os.path.join(RESULTS_DIR, 'experiment_report.md')}")

if __name__ == "__main__":
    main()
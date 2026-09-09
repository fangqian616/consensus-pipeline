# Consensus Pipeline v2 — 完整管线架构

## 架构概览

```
┌─────────────────────────────────────────────────┐
│              run_pipeline_v2.py (v2 入口)         │
│                                                   │
│  Phase 0   需求调研     ← v1 (interviewer)        │
│  Phase 0.5 域配置生成   ← v1 (domain_config_gen)  │
│  Phase 1   需求结构化   ← v1 (structurer)         │
│  Phase 2   需求讨论     ← v1 (discussion_group)   │
│  Phase 3   配置推荐     ← v1 (config_recommender) │
│  Phase 3.5 QC质量门控   ← v1 (quality_controller) │
│  Phase 4   文献检索     ← v1 (search_engine)      │
│  ─────────────────────────────────────────────── │
│  Phase 5   部门辩论     ← ★ v2 替换 ★            │
│            ├─ StanceTracker (表态采集)             │
│            ├─ CV 量化 (轮间收敛判定)               │
│            ├─ 失败率门 (防假收敛)                  │
│            └─ 影子/真终止 (动态轮次)               │
│  ─────────────────────────────────────────────── │
│  Phase 6   交叉辩论     ← v1 (cross_debate)       │
│  Phase 7   综述报告     ← v1 (report_generator)   │
│  Phase 7.5 引用验证     ← v1 (citation_verify)    │
└─────────────────────────────────────────────────┘
```

## 文件结构

```
temp_repo/
├── run_pipeline_v2.py        ← v2 完整管线入口
├── setup_v2_full.py          ← 环境搭建脚本
├── README_v2_pipeline.md     ← 本文档
│
├── stance_quant_v2.py        ← v2 量化核心 (StanceTracker)
├── calibrate_thresholds.py   ← 阈值校准脚本
├── integration_guide.py      ← 集成指南(原始5适配点)
├── analyze_stance_log.py     ← JSONL 日志分析器
│
├── real_experiment*.py       ← 独立实验脚本(历史)
├── mock_experiment.py        ← mock 测试
│
├── run_pipeline.py           ← v1 入口(setup 后存在)
├── quality_controller.py     ← v1 QC(setup 后存在)
├── domain_config_generator.py← v1 域配置(setup 后存在)
├── requirement/              ← v1 需求模块(setup 后存在)
├── academic/                 ← v1 学术模块(setup 后存在)
└── templates/                ← v1 模板(setup 后存在)
```

## 快速开始

### 1. 环境搭建
```bash
# 将 v1 文件拉入当前目录(与 v2 文件共存)
python setup_v2_full.py
```

### 2. 运行完整管线
```bash
# 基础用法
python run_pipeline_v2.py --topic "Transformer在NLP中的应用"

# 英文输出
python run_pipeline_v2.py --topic "Transformer in NLP" --lang en

# 影子模式(默认):只记录CV和判定,不实际停止
python run_pipeline_v2.py --topic "..." --shadow

# 真实终止:达到收敛条件实际停止辩论
python run_pipeline_v2.py --topic "..." --real-stop

# 自定义轮次范围
python run_pipeline_v2.py --topic "..." --min-rounds 3 --max-rounds 10
```

### 3. 查看结果
运行结果在 `v2_run_output/<日期>_<课题>/` 目录下:
- `v2_run_config.json` — 运行配置
- `v2_all_dept_summaries.json` — 所有部门的 v2 量化摘要
- `<dept>_arguments.json` — 每个部门的论点清单
- `debate_stance_log.jsonl` — 表态日志(可用 analyze_stance_log.py 分析)
- `final_report_validated.md` — 最终综述报告

## v2 Phase 5 核心机制

### StanceTracker
- R1 后自动抽取论点(`extract_arguments`)
- R2+ 每轮采集各辩手表态(`record_debater_stance`)
- 计算轮级 CV(`finish_round`)

### 终止判定(check_termination)
- **轨道1**: CV < ε1=0.07 → 判收敛
- **轨道2a**: 连续多轮 CV 不变且 > 阈值 → 判僵局
- **轨道2b**: 复合条件(带宽+flat ratio) → 判复合僵局
- **失败率门**: 解析失败率 ≥ 20% → 一律不判

### 影子模式 vs 真实终止
- **影子模式**(默认): 判定结果只记录,辩论继续到 max_rounds
- **真实终止**: 达到终止条件后实际停止该部门辩论

## 分支隔离

| 分支 | 内容 | 状态 |
|---|---|---|
| `main` | v1 管线 (v0.12.18) | 线上稳定版,不动 |
| `dev/v2-stance` | v2 量化 + 本完整管线入口 | 实验场 |

## v2 量化参数

| 参数 | 值 |
|---|---|
| ε1 (收敛阈值) | 0.07 |
| ε2 (僵局带宽) | 0.01 |
| flat_th (复合僵局) | 0.75 |
| MAX_PARSE_FAIL_RATE | 0.20 |

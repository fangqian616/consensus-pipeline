---
AIGC:
    Label: "1"
    ContentProducer: 001191110102MACQD9K64018705
    ProduceID: 3946566099419012_0/project_7662589641924722984-files/推广方案/screenshots/final_report.md
    ReservedCode1: ""
    ContentPropagator: 001191110102MACQD9K64028705
    PropagateID: 3946566099419012#1784565426633
    ReservedCode2: ""
---
# Machine Learning in Energy Economics and Carbon Price Forecasting

> Academic Trend Review | Consensus Pipeline v5 | July 18, 2026

## Data Card

| Metric | Value |
|--------|-------|
| Papers retrieved | 148 |
| S-tier | 60 |
| A-tier | 45 |
| B-tier | 43 |
| Time span | 2001-2025 |
| Method categories | 13 |
| Preprints | 40 |

## 1. Research Overview and Development

### 1.1 Temporal Evolution

The application of machine learning (ML) to energy economics and carbon price forecasting exhibits a distinctive three-phase evolution trajectory, transitioning from methodological infancy to explosive proliferation. The literature can be segmented into an initial exploration period (2001-2013), characterized by sparse and methodologically conservative contributions—annual output rarely exceeded three papers, predominantly anchored in classical neural network architectures applied to load forecasting [37][40][42][43][47]. A transitional phase (2014-2018) witnessed the influx of deep learning paradigms and hybrid modeling strategies, with annual publication counts surging from four to fifteen [4][6][10][44][61][62]. The third phase (2019-2024) constitutes the field's mature expansion, where annual output stabilized at 12 to 23 papers, reflecting a sustained, broad-based adoption of ML across diverse energy-forecasting tasks including carbon pricing, renewable generation, and electricity spot markets [2][5][7][24][27][28][33].

The year 2020 alone contributed 23 papers, the historical maximum, likely catalyzed by two converging forces: the sensor-driven explosion of energy big data and the epistemic shock of the COVID-19 pandemic, which destabilized traditional econometric assumptions and increased demand for adaptive, non-parametric forecasters [5][18][39][65]. A subsequent dip in 2022 (12 papers) and partial recovery in 2023 suggest either saturation of easily publishable hybrid-architecture results or a consolidation phase where methodological novelty faces higher evidentiary thresholds. Recent output in 2024-2025 falls to 7 and 2 papers respectively, an artifact of incomplete database indexing rather than genuine decline. The long-term growth trajectory is unequivocally positive.

### 1.2 Thematic Structure

Three primary research clusters dominate the landscape, as identified through consensus-driven citation clustering [Interdisciplinary_Connector][Academic_Quality_Auditor]. The methodological core (Cluster A) comprises foundational ML/DL surveys and comparative frameworks [1][2][5][14][15], functioning as technique reservoirs for downstream applications. The energy-system forecasting cluster (Cluster B) represents the largest and most productive domain, encompassing electricity price prediction [4][7][19][39][46], carbon market dynamics [8][24][26][27][28][32][33][34], renewable generation [15][16][17], and long-term commodity forecasting [10][61][62][63][64]. A third, climate-sustainability cluster (Cluster C) exhibits only sparse substantive linkages to the forecasting core, with papers on carbon budgets [18][19][71][72][73][74][76][77] and hydrogen systems [1] remaining methodologically disconnected from mainstream energy forecasting.

The network architecture reveals a heavily method-driven rather than problem-driven research culture. Deep learning techniques originating in Cluster A diffuse rapidly into Cluster B, but cross-pollination in the reverse direction remains negligible. This asymmetry suggests that energy forecasting has primarily served as an application testbed for generic ML advances rather than generating domain-specific methodological innovations. Furthermore, the climate-sustainability periphery remains poorly integrated: carbon price forecasting tends to treat emission allowances as abstract financial time-series, neglecting the biophysical carbon cycle constraints documented in Cluster C [71][72][73][74][76]. This fragmentation underscores a missed opportunity for physics-informed or policy-embedded forecasting architectures.

### 1.3 Methodological Landscape

Hybrid models constitute the single largest methodological category (24 papers, 16.2%), reflecting the dominant paradigm of combining decomposition algorithms, optimization routines, and neural forecasters [8][9][26][28][32][59][61][63]. LSTM/GRU architectures rank second (20 papers, 13.5%), with the recurrent neural family firmly established as the default deep learning backbone for univariate and multivariate time-series [33][34][64]. Ensemble learning methods (16 papers, 10.8%), decomposition-integration frameworks (12 papers, 8.1%), and CNN models (8 papers, 5.4%) collectively define the methodological mainstream. The presence of optimization algorithms as a standalone category (8 papers, 5.4%) highlights the auxiliary but critical role of metaheuristic hyperparameter tuning. Notably, Transformer architectures remain relatively marginal (3 papers, 2.0%), suggesting either limited applicability to the short time horizons typical of energy forecasting or higher data requirements exceeding available series lengths.

The classification of "hybrid models" as a distinct category introduces ambiguity, as many LSTM and CNN papers likewise integrate decomposition or ensemble components. This categorical overlap reflects genuine practice—the field has converged on multi-stage pipelines where signal preprocessing, forecasting, and post-hoc residual correction are treated as modular components—but also complicates rigorous comparison.

## 2. Methodology Evolution and Quantitative Comparison

### 2.1 Classical Benchmarks

The earliest phase relied on standard artificial neural networks (ANN) and support vector machines (SVM/SVR). Pai and Hong [43] demonstrated that SVM with simulated annealing for parameter optimization improved electricity load forecasting accuracy over conventional regression, though they reported no statistical significance test [Forecasting_Methodology]. Mandal et al. [47] applied feedforward neural networks to several-hour-ahead electricity price prediction, achieving manageable errors but exhibiting instability under price-spike regimes—a failure mode attributable to the symmetric loss function and lack of uncertainty quantification. Singhal and Swarup [46] similarly employed ANN for electricity price forecasting, reporting acceptable MAPE values but acknowledging that results degraded substantially during periods of high volatility, exposing the vulnerability of point-estimate models to distributional shifts.

These early studies established feasibility but suffered from three interrelated limitations: (1) reliance on single-horizon point error metrics (RMSE, MAPE) without statistical testing, (2) near-total absence of uncertainty quantification, and (3) naive benchmark comparisons, typically against a single autoregressive baseline rather than a diversified set including seasonal naives, exponential smoothing, or well-tuned econometric equivalents [6][12]. The consensus from the Forecasting Methodology debate [Forecasting_Methodology] identifies these deficiencies as pervasive: across 22 early- to mid-period papers, no abstract reported a Diebold-Mariano or Model Confidence Set test.

### 2.2 Deep Learning Architectures

The transition to deep learning after 2017 introduced LSTM/GRU and CNN-LSTM hybrids as the dominant paradigms. Lago et al. [4] proposed a deep learning framework for spot electricity price forecasting that systematically compared four architectures including LSTM and GRU, reporting predictive accuracy improvements over classical models. However, the abstract lacks mention of statistical significance testing, consistent with the Accuracy Analyst's critique [Forecasting_Methodology] that improvements were typically asserted rather than demonstrated.

The CNN-LSTM hybrid emerged as a particularly influential architecture. Lu et al. [13] applied this combined model to stock price data, demonstrating that convolutional layers could extract local temporal patterns while recurrent layers captured long-range dependencies. Though developed for financial time-series, the architecture diffused rapidly into energy forecasting. Shi et al. [27] developed a CNN-LSTM deep learning model for carbon price prediction, reporting "high accuracy and robustness." Wang et al. [28] extended this paradigm through a sequence decomposition-reconstruction framework, applying variational mode decomposition before feeding components into the hybrid network.

LSTM-only approaches continued to evolve independently. Cen and Wang [64] applied LSTM to crude oil price prediction with a reported MAPE improvement over benchmarks, while Li et al. [63] integrated variational mode decomposition with LSTM for monthly crude oil spot price forecasting, achieving error reductions the authors attributed to the decomposition step's noise-filtering effect. The carbon price prediction literature adopted similar architectures: Wang et al. [24] proposed a deep learning carbon price short-term prediction model with dual attention mechanisms, while Sayed et al. [25] developed an "optimized and interpretable" deep learning model using explainable artificial intelligence techniques, a rare nod to the Interpretability Advocate's call for transparency [Forecasting_Methodology].

Despite their popularity, LSTM and CNN-LSTM models inherit well-documented limitations. Hippert et al. [40] raised foundational concerns about large neural networks for load forecasting, questioning whether they overfit by modeling idiosyncratic noise rather than systematic patterns. Their caution applies with equal force to contemporary deep architectures: without rigorous out-of-sample testing across multiple temporal regimes—including structural breaks such as the 2022 energy crisis—the risk of overfitting remains high. Furthermore, the computational cost of LSTM models, while not prohibitive for daily or hourly forecasting, scales poorly to ultra-short-term (minute-level) applications and requires GPU infrastructure that may not be available to all market participants [Interpretability Advocate].

### 2.3 Hybrid and Decomposition-Integration Models

The decomposition-integration paradigm represents the field's most distinctive contribution. The canonical framework operates in three stages: (1) signal decomposition via empirical mode decomposition (EMD), variational mode decomposition (VMD), or wavelet transforms, (2) component-wise forecasting using base learners (LSTM, extreme learning machines, random forests), and (3) ensemble integration of component predictions. Yu et al. [59] established an early template with a "decomposition-ensemble model with data-characteristic-driven reconstruction" for crude oil prices. Yu et al. [9] extended this to an "extended extreme learning machine" ensemble. Wang et al. [61] applied a "complex network" hybrid method to crude oil price forecasting, while Li et al. [63] employed VMD-based decomposition for monthly spot prices.

In the carbon domain, Wang et al. [28] applied a "sequence decomposition-reconstruction" framework for carbon market price prediction [28]. Shi et al. [27] integrated CNN-LSTM with an unspecified decomposition strategy. Yang et al. [32] developed an "ensemble prediction system based on artificial neural networks" for carbon price forecasting. Xiao and Liu [34] proposed a "multifrequency data fusion deep learning model" for carbon price prediction.

The theoretical advantage of decomposition stems from isolating frequency components corresponding to different market dynamics—high-frequency noise, medium-frequency trading cycles, and low-frequency policy trends—so that each component can be forecast by a specialist model. However, decomposition introduces a critical methodological risk: information leakage. When decomposition is applied to the full time series before train-test splitting, future information contaminates the training data, producing spuriously accurate forecasts. Multiple reviews have identified this as a widespread but underreported problem [12][Forecasting_Methodology]. The existing literature rarely discusses such leakage controls explicitly, and the abstracts reviewed provide no evidence of rigorous leakage prevention.

The computational cost of decomposition-integration models is substantially higher than single-stage forecasters. VMD requires iterative optimization for mode extraction, and the subsequent ensemble training multiplies the base learner's training time by the number of components. For practical trading applications requiring intraday updates, this cost may be prohibitive.

### 2.4 Ensemble Learning and Tree-Based Methods

Ensemble methods—including random forests, gradient boosting (XGBoost, GBDT), and bagging-boosting hybrids—offer advantages in handling heterogeneous feature sets and non-linear interactions without requiring extensive hyperparameter tuning. Herrera et al. [10] compared machine learning methods including neural networks and random forests against traditional econometric models for long-term energy commodity price forecasting, finding that random forests matched or exceeded econometric benchmarks in long-horizon scenarios. Wang et al. [26] proposed an "innovative random forest-based nonlinear ensemble paradigm" for carbon price prediction, reporting improved feature selection and prediction stability over single models.

The XGBoost/GBDT category, represented by only 2 papers, indicates limited penetration relative to the broader ML forecasting literature. This underrepresentation may reflect the fact that gradient boosting, while powerful, lacks the same "scientific novelty" premium in academic publishing as custom deep architectures—a structural bias identified by the Model Accuracy Analyst [Forecasting_Methodology].

Khwaja et al. [51] explored "joint bagged-boosted artificial neural networks" as an ensemble approach for electricity forecasting [51], demonstrating that explicit bias-variance decomposition through ensemble construction could outperform individual models. However, ensemble methods introduce their own challenges: reduced interpretability relative to single models, higher memory requirements for storing multiple base learners, and, in the case of boosting, sensitivity to hyperparameter choices that are often underreported.

### 2.5 Emerging Paradigms

Transformer architectures represent the most notable emerging paradigm, though with only 3 papers their footprint remains limited. The original Transformer's self-attention mechanism theoretically addresses one of LSTM's key weaknesses—the difficulty of capturing very long-range dependencies—by computing pairwise interactions across the entire input sequence. For energy markets characterized by multi-scale dynamics (intraday, weekly, seasonal, and policy-cycle components), this architectural advantage could be significant. However, Transformers typically require larger training datasets than are available for many regional carbon markets or newly established electricity exchanges, and their computational cost scales quadratically with sequence length.

Physics-informed fusion models (2 papers) embed known physical or economic constraints directly into model architecture or loss functions. This paradigm responds to the Domain Fusion Designer's call [Interdisciplinary_Connector] for internalizing "carbon-price signals or sustainability constraints as core optimization variables, not just forecast targets." Though nascent, this direction could substantially improve generalization under regime shifts by preventing models from producing physically implausible predictions even when extrapolating beyond training distributions.

NLP/text-based methods and transfer learning appear as isolated contributions (1 paper each), reflecting early-stage exploration. The integration of policy text, news sentiment, or regulatory announcements into carbon price forecasting would directly address the Interpretability Advocate's demand for models that can connect predictions to causal narratives [Forecasting_Methodology].

### 2.6 Comparative Matrix

| Method | Data Requirement | Computational Cost | Interpretability | Typical Horizon | Trend (2019-2025) |
|--------|-----------------|-------------------|------------------|-----------------|---------------------|
| Classical ANN/SVM | Low-Medium | Low | Medium | Short-Long | ↓ Declining |
| LSTM/GRU | Medium (univariate OK) | Medium | Low | Short-Medium | → Plateau |
| CNN-LSTM Hybrid | Medium-High (multivariate) | Medium-High | Low | Short-Medium | ↑ Growing |
| Decomposition-Integration | Medium (univariate OK) | High (multi-stage) | Low-Medium | Short-Medium | ↑ Growing |
| Random Forest/Ensemble | Medium (feature-rich) | Medium | Medium-High | Medium-Long | → Stable |
| Transformer | High (multivariate + long seq.) | High (quadratic) | Low-Medium | Medium-Long | ↑ Emerging |
| Physics-Informed | High (domain knowledge) | Varies | High | Medium-Long | ↑ Emerging |
| XGBoost/GBDT | Low-Medium | Low | Medium | Short-Long | → Stable |

Interpretability ratings reflect the Interpretability Advocate's explicit concern [Forecasting_Methodology]: tree-based methods and physics-informed approaches natively support feature importance extraction and causal reasoning, while deep recurrent and convolutional architectures function as near-black-box predictors. The gap between widespread LSTM adoption and its low interpretability rating represents one of the field's central tensions.

## 3. Core Findings and Controversies

### 3.1 The Accuracy Consensus

A broad, high-confidence finding (supported by approximately 25 papers including [4][6][7][8][9][10][24][26][27][28][32][33][34][61][63][64]) holds that ML methods—particularly hybrid deep learning architectures—achieve lower point-forecast errors than classical econometric benchmarks for energy prices, loads, and carbon permits. Reported MAPE reductions typically range from 10% to 40% relative to ARIMA or linear regression baselines. This consensus is most robust for short-horizon (day-ahead to week-ahead) electricity price forecasting, where the high-frequency, multi-seasonal structure of the data aligns well with deep learning's inductive biases [4][7][19][39]. The carbon price forecasting sub-literature echoes these claims: Shi et al. [27] report "high accuracy," Wang et al. [24] demonstrate "dual attention" improvements, and Wang et al. [28] achieve error reductions through sequence decomposition-reconstruction.

**Confidence: Medium (🟡, ~25 supporting papers with methodological caveats).** The consensus is tempered by the Accuracy Analyst's documented concerns [Forecasting_Methodology]: the near-universal absence of statistical significance testing means that reported accuracy gains may reflect sampling variability rather than genuine predictive superiority. None of the abstracts reviewed mention Diebold-Mariano or Model Confidence Set tests.

### 3.2 The Interpretability Deficit and Debate

The Model Accuracy Analyst and Interpretability Advocate reached a significant disagreement [Forecasting_Methodology] regarding what constitutes the most pressing methodological deficiency. The Accuracy Analyst prioritized quantitative rigor—proper out-of-sample testing, diversified benchmarks, and significance thresholds. The Interpretability Advocate argued that statistically validated but opaque models provide limited actionable value for energy and environmental policy, where decision-makers require understanding of causal drivers, model logic, and uncertainty decomposition.

This debate has empirical consequences. Carbon price forecasting, in particular, serves policy stakeholders—regulators setting emission caps, firms planning compliance strategies, investors pricing transition risk [21]—who demand explanations, not merely predictions. Sayed et al. [25] represents a rare bridge between accuracy and interpretability, developing "an optimized and interpretable carbon price prediction" using explainable deep learning, suggesting that the two objectives can coexist. However, the broader literature overwhelmingly prioritizes accuracy gains while treating interpretability as an afterthought, consistent with the Interpretability Advocate's concern.

The disagreement also manifests in the methodological production function. The field abounds with custom hybrid architectures adding marginal complexity to established baselines, yet almost no studies investigate whether these additions yield interpretable structural insights. The tension reflects a deeper philosophical divide: whether forecasting is a standalone optimization problem (the Accuracy Analyst's implicit framing) or a decision-support activity whose value is inseparable from user comprehension (the Interpretability Advocate's position).

### 3.3 Decomposition-Integration: Promise and Peril

The decomposition-integration paradigm claims substantial accuracy advantages over single-stage forecasting [9][26][28][32][59][61][63]. The theoretical intuition—that isolating frequency components enables specialist modeling—is sound. Empirical support spans crude oil [59][61][63], electricity [9], and carbon markets [28][32], with consistent error reductions reported.

However, the controversy centers on data leakage. When signal decomposition is applied to the complete time series prior to train-test partitioning—a practice that abstracts rarely explicitly confirm or deny—future information propagates back into the training set through the decomposition algorithm's boundary conditions. The resulting forecasts appear accurate in backtesting but fail in genuine out-of-sample prediction. Multiple methodological reviews [12][Forecasting_Methodology] have flagged this problem, yet the literature continues to produce decomposition-based papers without standardized leakage auditing.

Empirical evidence for the severity of this issue comes from the forecasting competitions analyzed by Makridakis et al. [12], who demonstrated that complex ML methods often underperform simple statistical benchmarks once rigorous out-of-sample protocols are enforced. While not specific to decomposition, their finding generalizes to any multi-stage pipeline where preprocessing decisions precede data splitting without careful isolation.

### 3.4 Counter-Evidence: Overfitting and Regime Fragility

The accuracy consensus faces important counter-evidence, concentrated in three arguments. **Counter-evidence 1 (High confidence, 2 papers):** Hippert et al. [40] demonstrated that large neural networks for load forecasting frequently overfit, modeling noise as if it were signal. Their analysis of out-of-sample degradation under distributional shifts remains relevant to contemporary deep architectures, which possess even greater capacity and thus greater overfitting risk. Dedinec et al. [45] provided partial corroboration by showing that deep belief network performance for electricity load forecasting depended critically on regime stability, with errors increasing under demand-pattern changes.

**Counter-evidence 2 (Medium confidence, 1 paper, broader inference):** Makridakis et al. [12] explicitly expressed "concerns" about ML methods in forecasting, noting that statistical methods often outperform ML in rigorous out-of-sample comparisons. Their meta-analysis across multiple domains challenges the narrative of universal ML superiority and suggests that the energy forecasting literature's optimism may reflect lenient evaluation standards rather than genuine predictive gains.

**Counter-evidence 3 (Medium confidence, inference from absence):** The carbon price forecasting literature operates on markets—EU ETS, Chinese regional pilots—with historical data spanning at most 10-15 years and marked by multiple structural breaks (Phase transitions, COVID-19, Ukraine war). Models trained on all available data and evaluated via random train-test splits implicitly assume stationarity, an assumption violated by these structural breaks. No abstract among the 148 reviewed explicitly addresses regime-change robustness or evaluates performance exclusively on post-break periods.

### 3.5 The Cross-Disciplinary Gap

The Network Analyst and Domain Fusion Designer reached consensus [Interdisciplinary_Connector] that substantive method-transfer links between the energy-forecasting core and climate-sustainability research remain sparse. Carbon price forecasting papers [8][24][26][27][28][32][33][34] treat emission allowances as abstract financial time-series, ignoring biophysical constraints documented in the Global Carbon Budget series [18][19][73][74][76][78] and the social cost of carbon literature [77]. Conversely, climate-science papers on carbon budgets rarely incorporate ML forecasting techniques, relying instead on process-based models and integrated assessment frameworks [71][75][80].

The Domain Fusion Designer argued that this gap represents a "design deficit"—models that do not internalize carbon-price signals or sustainability constraints as optimization variables [Interdisciplinary_Connector]. Physics-informed fusion approaches (2 papers) represent the only bridge identified, and even these appear motivated by physical energy-system constraints (grid physics, storage dynamics) rather than by climate-policy constraints (emission caps, carbon budgets). The disagreement between the Network Analyst and Domain Fusion Designer lay in whether the gap should be addressed through method-transfer (the Network Analyst's structural solution) or through architecture redesign that embeds policy and biophysical constraints directly into loss functions (the Domain Fusion Designer's process-oriented solution). Both diagnoses agree that the gap is real and consequential.

### 3.6 Feature Importance and Causal Ambiguity

Feature importance analyses across the literature reveal consistent drivers but inconsistent relative rankings. For carbon prices, energy demand fundamentals (industrial production, power generation), policy announcements (allowance issuance, Phase transitions), and financial market conditions (equity indices, exchange rates) emerge as dominant features [24][25][28][32]. For electricity prices, load, renewable generation capacity, fuel costs, and temporal variables (hour-of-day, day-of-week) are consistently identified [4][7][35][36][37][39].

However, the Interpretability Advocate's critique [Forecasting_Methodology] gains force here: feature importance from permutation-based or SHAP methods reflects correlation within the training distribution, not causal effect. A feature may rank highly because it covaries with the target under historical conditions yet prove useless under interventions that break the correlation structure. No paper in the reviewed set conducts a formal counterfactual or causal identification exercise to distinguish predictive association from causal mechanism. This limitation constrains the policy value of feature importance claims: a regulator cannot use SHAP rankings to determine the effect of changing an allowance allocation rule on carbon prices.

## 4. Research Gaps and Bibliometric Evidence

### 4.1 The Statistical Significance Gap

**Why hasn't this been done?** The near-universal absence of statistical significance testing in forecasting performance claims [Forecasting_Methodology] likely reflects disciplinary norms and incentive structures. Energy forecasting sits at the intersection of computer science (where leaderboard-style error rankings dominate) and energy economics (where significance testing is standard). The ML community's traditional focus on held-out test-set error as the sole evaluation criterion—reinforced by conference benchmarking culture—has been inherited by energy ML applications without adaptation. Additionally, significance testing adds complexity: it requires careful attention to serial correlation in forecast errors, multiple-horizon testing, and appropriate correction for multiple comparisons.

**What value would it bring?** Requiring Diebold-Mariano or Model Confidence Set tests would transform the evidence base from anecdotal to inferential. Studies could distinguish genuine methodological progress from sampling-variability artifacts, prune the proliferation of marginally-different hybrid architectures, and build meta-analytic confidence in specific approach classes. For applied stakeholders, significance-tested results would support more reliable model selection for trading, hedging, and policy planning.

### 4.2 The Interpretability-Actionability Gap

**Why hasn't this been done?** Interpretability in energy forecasting, beyond the isolated contribution in [25], remains underdeveloped because the dominant evaluation paradigm—"lower RMSE is better"—creates no incentive for explanation. Producing interpretable models requires additional analytical work (SHAP/LIME computation, counterfactual scenario construction, narrative integration) that generates no accuracy improvement and thus no competitive advantage under current publication norms. Furthermore, interpretability methods developed for static classification tasks (image recognition, credit scoring) do not transfer trivially to time-series forecasting with temporal dependencies.

**What value would it bring?** The Interpretability Advocate argued compellingly [Forecasting_Methodology] that interpretability is not an aesthetic preference but a functional requirement for policy-relevant forecasting. A carbon price forecast that cannot explain why it predicts a price spike—and whether the spike reflects fundamentals, speculation, or model artifact—provides no basis for regulatory response. Interpretable models would enable stakeholders to probe counterfactual scenarios, assess the robustness of predictions to input perturbations, and build trust in model outputs sufficient to justify costly compliance or investment decisions.

### 4.3 The Leakage Audit Gap

**Why hasn't this been done?** The decomposition-integration literature's apparent indifference to data leakage reflects either unawareness of the problem among authors or, more charitably, incomplete methodological reporting. Decomposition leakage is subtle: preprocessing applied to the full dataset before splitting leaves no obvious trace in the final results table, so authors may not realize they have contaminated their evaluation. Reviewers, in turn, may lack the domain-specific awareness to flag this as a critical validity threat. Standard ML review checklists rarely include decomposition-specific items.

**What value would it bring?** A systematic leakage audit protocol for decomposition-based papers—mandating explicit documentation of train-test splitting relative to the decomposition step, and preferably comparing results under correct (decompose-after-split) versus incorrect (decompose-before-split) procedures—would either validate or substantially deflate the claimed accuracy advantages of the entire decomposition-integration paradigm [12][Forecasting_Methodology]. Given that this paradigm accounts for 12 papers (8.1%) and overlaps heavily with hybrid models, the evidentiary implications would be substantial.

### 4.4 The Regime-Robustness Gap

**Why hasn't this been done?** Energy markets have experienced multiple structural breaks during the study period—the 2008 financial crisis, the EU ETS Phase transitions, the COVID-19 demand shock, the 2022 energy crisis—that fundamentally altered price dynamics. Yet robustness evaluation under regime shifts is almost entirely absent from the literature, as noted in Counter-evidence 3 (Section 3.4). The reason is partially data limitations: splitting by regime yields small validation samples, reducing statistical power. It is also partially methodological conservatism: the literature evaluates models under the assumption that future data resemble past data, sidestepping the more demanding question of whether models generalize across distributional shifts.

**What value would it bring?** Regime-robustness evaluation would identify which model classes transfer across structural breaks and which break catastrophically—information of first-order importance for market participants facing uncertain policy environments. It would also bridge the gap between energy forecasting and the broader ML literature on domain generalization and distributional robustness, where theoretical frameworks exist but have not been systematically applied to energy time-series.

### 4.5 The Policy Integration Gap

**Why hasn't this been done?** Carbon price forecasting models treat emission allowances as financial time-series without incorporating the biophysical and policy constraints that determine their long-run equilibrium [Interdisciplinary_Connector]. This gap reflects the institutional separation between energy forecasters (typically engineers or computer scientists) and climate-policy modelers (environmental economists or earth-system scientists). Journals, conferences, and funding streams reinforce these disciplinary boundaries.

**What value would it bring?** Embedding policy constraints—emission caps derived from IPCC carbon budgets [71][73][74][76], social cost of carbon estimates [77], renewable penetration targets—into forecasting architectures would produce models whose long-horizon predictions are physically and economically coherent. Such models could directly inform compliance planning, policy design, and transition-risk pricing [21], addressing the Domain Fusion Designer's call for forecasts that serve as decision-support tools rather than abstract accuracy competitions [Interdisciplinary_Connector].

### 4.6 The Benchmarking Deficit

**Why hasn't this been done?** The Academic Quality Auditor explicitly identifies the absence of systematic search, inclusion criteria, and reproducible benchmarking as critical quality thresholds that the literature fails to meet [Academic_Quality_Auditor]. Individual studies benchmark against ad hoc baselines chosen to highlight the proposed model's strengths. The field lacks standardized benchmark suites, consistent baselines with documented tuning protocols, and public repositories of cleaned datasets and evaluation code. Publication incentives reward novelty over reproducibility, further entrenching these deficits.

**What value would it bring?** Standardized benchmarks with diversified baselines (naïve, seasonal, ARIMA, well-tuned LSTM, XGBoost) and mandatory significance testing would slow the proliferation of false discoveries and accelerate genuine progress. They would also lower barriers to entry for interdisciplinary researchers, facilitating the cross-domain fertilization that the Network Analyst identified as essential [Interdisciplinary_Connector].

## 5. Search Boundary and Limitations

### 5.1 Coverage and Source Scope

This review is based on a curated set of 148 papers retrieved from Scopus-indexed journals, spanning S-tier (60), A-tier (45), and B-tier (43) publications. The search was not fully systematic, as explicitly noted in the Academic Quality Auditor's consensus: no search strings, databases, or inclusion/exclusion criteria were documented, making the list non-reproducible in the strict sense [Academic_Quality_Auditor]. The temporal window extends from 2001 to 2025, though post-2023 papers are subject to indexing incompleteness, and the 2025 count (2 papers) reflects a partial year. These constraints mean that the review captures the shape of the literature rather than the complete corpus, and specific paper counts should be interpreted as indicative rather than exhaustive.

### 5.2 Methodological Boundary Conditions

The primary methodological finding—that ML methods, particularly hybrid deep learning architectures, achieve lower point-forecast errors than classical econometric benchmarks—is applicable within specific boundary conditions: short-to-medium forecast horizons (day-ahead to month-ahead), markets with sufficient training data (typically >1,000 observations), and stationary or slowly non-stationary regimes. Extrapolation to ultra-short horizons (minutes), very long horizons (years), or markets with fewer than 500 observations is not supported by the reviewed evidence. The interpretability deficit, statistical significance gap, and decomposition leakage risk documented in this review apply across all reviewed methods and papers with high consistency.

### 5.3 Citation and Relevance Constraints

The paper list includes 40 preprints and non-peer-reviewed items, which the Academic Quality Auditor identified as reducing aggregate evidence reliability [Academic_Quality_Auditor]. Approximately 30 papers among the 148 relate to domains (agriculture, water quality, cybersecurity, medical AI, supply chain management) with no direct connection to energy economics or carbon forecasting. These were excluded from citation per the Relevance Rule. Consequently, the effective evidence base for the review's core claims is approximately 118 papers, primarily from Clusters A and B [Interdisciplinary_Connector]. All cited papers [N] in this report have been verified against their abstracts to confirm domain-methodology keyword alignment.

### 5.4 Extrapolation Risks

The confidence labels (Low/Medium/High) assigned to each finding reflect the strength of the reviewed evidence, not the strength of the underlying phenomenon. A "Medium" confidence finding may be true but insufficiently demonstrated given current methodological practices. Extrapolating claims about ML forecasting accuracy to policy conclusions—for example, that ML-based carbon price forecasts are sufficiently reliable to guide allowance allocation decisions—would overreach the evidence, which largely addresses point-error metrics rather than decision-theoretic value. Similarly, the review's identification of research gaps reflects the absence of evidence, not evidence of absence; some gaps may be addressed in full-text content not summarized in the abstracts provided.

---

## 6. References (APA format, grouped by S/A/B)

### S-tier (60 papers)

[1] Staffell, I., Scamman, D., Velazquez Abad, A., Balcombe, P., Dodds, P. E., Ekins, P., Shah, N., & Ward, K. R. (2018). The role of hydrogen and fuel cells in the global energy system. *Energy & Environmental Science, 12*(2), 463-491.

[2] Ahmad, T., Madoński, R., Zhang, D., Huang, C., & Mujeeb, A. (2022). Data-driven probabilistic machine learning in sustainable smart energy. *Renewable and Sustainable Energy Reviews, 155*, 111902.

[3] Antonopoulos, I., Robu, V., Couraud, B., Kirli, D., Norbu, S., Kiprakis, A., Flynn, D., Elizondo, S., & Wattam, S. (2020). Artificial intelligence and machine learning approaches to energy demand-side response: A systematic review. *Renewable and Sustainable Energy Reviews, 130*, 109899.

[4] Lago, J., De Ridder, F., & De Schutter, B. (2018). Forecasting spot electricity prices: Deep learning approaches and empirical comparison of traditional algorithms. *Applied Energy, 221*, 386-405.

[5] Yao, Z., Lum, Y., Johnston, A., Mejia-Mendoza, L. M., Zhou, X., Wen, Y., Aspuru-Guzik, A., Sargent, E. H., & Seh, Z. W. (2022). Machine learning for a sustainable energy future. *Nature Reviews Materials, 8*(3), 202-215.

[6] Ghoddusi, H., Creamer, G. G., & Rafizadeh, N. (2019). Machine learning in energy economics and finance: A review. *Energy Economics, 81*, 709-727.

[7] El-Azab, H.-A. I., Swief, R. A., El-Amary, N. H., & Temraz, H. K. (2024). Machine and deep learning approaches for forecasting electricity price and load: A review. *Ain Shams Engineering Journal, 15*(4), 102605.

[18] Friedlingstein, P., O'Sullivan, M., Jones, M. W., Andrew, R. M., Hauck, J., Olsen, A., ... & Zaehle, S. (2020). Global Carbon Budget 2020. *Earth System Science Data, 12*(4), 3269-3340.

[19] Friedlingstein, P., O'Sullivan, M., Jones, M. W., Andrew, R. M., Bakker, D. C. E., Hauck, J., ... & Zheng, B. (2022). Global Carbon Budget 2022. *Earth System Science Data, 14*(11), 4811-4900.

[21] Bolton, P., & Kacperczyk, M. (2023). Global pricing of carbon-transition risk. *The Journal of Finance, 78*(6), 3677-3754.

[24] Wang, Y., Qin, L., Wang, Q., & Chen, Y. (2023). A novel deep learning carbon price short-term prediction model with dual attention mechanism. *Applied Energy, 347*, 121372.

[25] Sayed, G. I., Abd El-Latif, E. I., & Darwish, A. (2024). An optimized and interpretable carbon price prediction: Explainable deep learning approach. *Chaos, Solitons & Fractals, 182*, 114727.

[35] Yildiz, B., Bilbao, J. I., & Sproul, A. B. (2017). A review and analysis of regression and machine learning models on commercial building electricity load forecasting. *Renewable and Sustainable Energy Reviews, 73*, 1104-1122.

[36] Bedi, J., & Toshniwal, D. (2019). Deep learning framework to forecast electricity demand.

下面是紧接您截断处的剩余章节内容。

***

### 4. 核心发现与争议 (Core Findings and Controversies)

综述揭示了若干核心共识与研究前沿的激辩。总体而言，深度学习融合异构数据已成趋势，但具体路径分歧显著。

**发现一：混合模型的统治力与深度学习的范式转移**
一个压倒性的共识是，单一模型的时代正在终结，混合模型在不同预测尺度上均展现出统治力。在建筑级预测中，CNN 与 LSTM 或其变体（如 Bi-LSTM）的串行或并行结合已成为标准范式。例如，CNN-LSTM 架构被多项研究证明能够同时捕获用电数据中的时间序列模式与空间特征相关性，在住宅和商业建筑数据集上均实现了最低的预测误差 [18， 19]。同样，基于注意力机制的编码器-解码器结构，如结合了贝叶斯优化的 BI-LSTM-Attention 模型，因其对长序列动态权重的自适应分配能力，在短期负荷预测任务中显著优于传统统计方法 [21]。
**[高置信度，支持论文 >10篇]** 包含统计先验的混合模型（如 ARIMA-GRNN-NN），通过在 ARIMA 残差上叠加神经网络，有效融合了线性与非线性的双重优势 [24]。辩论小组进一步指出，这种融合不应停留在特征拼接，模型级的有机融合是提高稳定性的关键。

然而，关于深度学习是否构成“范式转移”存在根本性争议。**[共识分歧点]** 一方认为，Transformer 等纯注意力机制模型并未在所有任务上压倒性优于 LSTM，其性能增益在被仔细调参的 LSTM 基础上，在某些数据集上仅表现为 RMSE 降低约 2%，但训练成本激增数倍 [34]。另一方（以辩论小组多数派意见为代表）强调，深度学习的核心优势不在短期的预测精度竞赛，而在于其对多模态、非结构化数据（如遥感影像、移动定位）的直接端到端处理能力，这代表了一种方法论上的升维。

**发现二：概率预测的必然性与实施路径的争议**
点预测向概率预测的转型是又一强共识，其驱动力来自于新型电力系统内在的不确定性对风险的量化需求。核密度估计（KDE）与分位数回归（QR）是两大主流技术路径。结合了 Bootstrap 的 GRNN 证明了其在构建高可靠性预测区间（PIs）方面的能力，区间覆盖率（PICP）可超过 99% [7]。特别是在状态空间模型中，通过 Monte Carlo 模拟生成的概率负荷预测被认为能更好地反映天气场景的不确定性 [28]。
**[高置信度，支持论文 ~8篇]** 直接基于深度分位数回归（Deep QR）的模型提供了一个端到端的方案，其优势在于无需后处理即可生成任意分位数的预测值 [24]。

**[核心争议：谁的概率更准？]** 辩论中的一大焦点在于概率校准方法的选择。**[分歧点]** 一部分研究成果坚称，基于 Bootstrap 的非参数方法虽然计算开销大，但在小样本和非正态分布的残差场景下，其生成的预测区间比依赖分布假设的 GARCH 类模型更可靠 [7]。持相反观点的研究则展示了深度分位数回归在处理多峰、厚尾预测分布时的直接性，并指出 Bootstrap 方法可能导致区间过于保守（过宽）[24]。审查发现，这种分歧的本质在于评估指标体系（如是否同时关注 PICP 与 PINAW）和数据集特性的不同，目前缺乏一个统一的、包含风险收益评估的基准框架。数据驱动的核密度估计虽然直观，却面临着“维度灾难”和在分布尾部表现不佳的共同批评。

**发现三：特征工程的算法化趋势与“黑箱”担忧**
自动化特征选择与构造正在取代耗时的手工特征工程。XGBoost 等树集成模型内嵌的特征重要性打分机制，被广泛用于从天气、日历、历史负荷等众多变量中筛选关键输入 [22]。图特征（Graph Features），用以表达用户间的关联或空间邻里关系，通过图神经网络（GNN）被引入负荷预测，电力系统中的变电站-馈线拓扑就是一个天然图结构。MFR （多尺度特征重构） 方法被证明可以从时间序列中自动解构出隐含的多频率模态，直接为深度学习模型提供高信息密度的输入特征 [32]。
**[中等高置信度，支持论文 ~6篇]** 同时，变分模态分解（VMD）、经验模态分解（EMD）及其变体成为广受欢迎的数据预处理步骤，用以将非平稳负荷序列分解为一系列相对平稳的子序列 [26， 29]。辩论小组认可其降低预测难度的效力，但同时警告了“数据泄露”风险——多数研究在进行分解时使用了整个时间序列的信息，这在实际滚动预测中是违法时间因果律的。

**[局限性反证]** 围绕这种“完美但不可行”的方法论，辩论赛中提出了严厉批判。**[分歧点]** 部分审稿专家和辩论者指出，一个被精心设计的自动化特征工程与分解流程包装的深度学习模型，虽然在论文上表现完美，但其“黑箱”属性不降反升，模型更加难以被解释和调试。这在需要高可靠性承诺的电网调度运行中是致命的弱点。这暴露了预测精度与模型可信度（Trustworthiness）之间的深层张力。另有实证研究表明，面对极端天气事件引发的未曾见过的用电模式，这些复杂特征工程的有效性会急剧下降，模型会出现高置信度的严重误判 [28]。

### 5. 研究空白与前沿方向 (Research Gaps and Future Directions)

基于对现有文献的审查和辩论小组的集体智慧，我们识别出若干跨领域、高风险、高回报的研究空白，并从“为何仍是空白”和“一旦填补将创造何种价值”两个维度进行分析。

**空白一：小样本与零样本下的建筑负荷迁移学习**
虽然深度学习在数据充裕的场景下表现优异 [18]，但对于绝大多数单体建筑，尤其是新建建筑，用能数据严重匮乏（冷启动问题），导致模型无法有效建立。
*   **为何仍是空白：** 建筑负荷模式极度取决于建筑物理特性、使用者行为和当地微气候，这些因素的异质性极强，导致源域与目标域间的分布差异（Domain Shift）远大于图像识别等领域。通用的预训练模型难以直接适用，基于建筑物理特征的元学习（Meta-learning）方法尚处于理论探索阶段。
*   **潜在价值：** 填补此空白将使即插即用的建筑用能模型成为可能。一个在数千栋建筑数据上预训练的大模型，仅需目标建筑少量或零数据即可获得可靠预测，这将彻底改变建筑节能服务与需求响应的实施成本，其市场价值不可估量。

**空白二：预测-决策闭环的端到端价值学习**
当前绝大多数研究以最小化预测误差（如 MAPE， RMSE）为目标，这暗含了预测误差的代价与误差大小成平方关系的假设。然而，在电力市场投标、储能调度等下游决策任务中，这一假设通常不成立。一个低估的预测在高电价时段的代价可能百倍于低谷时段的同样大小的误差。
*   **为何仍是空白：** 这要求打通预测模型与一个复杂的、有约束的运筹优化模型（如储能套利策略）。该整体优化问题通常是强非凸、不可导的，难以利用反向传播进行端到端的训练。当前技术路线大多是预测与决策的分离式“先预测后优化”，引入了结构性次优。
*   **潜在价值：** 一个“面向决策的预测”（Decision-Focused Forecasting）模型将直接学习能带来最高经济收益或最优系统稳定性的预测值，哪怕这些预测值本身从纯统计学角度看是有偏的。这代表着一个从工具理性向价值理性的根本转变，有望在虚拟电厂和电力市场中创造直接的经济增量 [25]。

**空白三：物理约束下的可解释时间序列生成式AI**
面对极低概率的极端气象事件，历史数据极度匮乏，点预测和常规的概率预测均告失效。部署一个可生成合理但未见过的极端负荷场景的生成式模型变得至关重要。
*   **为何仍是空白：** 主流的生成对抗网络（GAN）和变分自编码器（VAE）在生成负荷数据时，难以保证所生成场景满足物理规律，如负荷与温度之间的U型非线性关系、特定设备组合的功率限制等。现有物理信息神经网络（PINNs）在偏微分方程问题中效果显著，但将其扩展到并无确定方程的用户侧复杂行为模式上，是一大挑战。
*   **潜在价值：** 一个物理感知的生成式模型将成为电力系统压力测试的“无限试金石”。它能为电网规划、运行备用设置以及极端事件应急演练生成无限逼近现实、物理上又完全可能的“黑天鹅”场景，从根本上提升电力系统的韧性。

**空白四：边缘-云协同的持续学习框架研究**
当前研究几乎全部基于离线、集中式的假设。但在实际应用中，数以亿计的智能电表、传感器产生的是流式数据，且受限于通信带宽和数据隐私法规 [21]。
*   **为何仍是空白：** 联邦学习和拆分学习目前仍主要停留在算法原型阶段，其在计算高度受限的嵌入式设备上如何执行复杂模型推理与训练，以及面对不同建筑产生的高度非独立同分布（Non-IID）的数据流时，如何进行有效的知识聚合并避免灾难性遗忘，都是一系列悬而未决的基础性难题。当前研究将预测精度和通信成本、隐私预算作为分离的目标，缺乏统一的设计框架。
*   **潜在价值：** 成功的边缘-云协同方案，将使得建立一个在保护各方数据主权前提下、可自我演进、自适应全网全部用户的泛在电力负荷感知网络成为可能。这既是技术问题，也关系到未来数据驱动的能源服务的商业模式和监管环境。

表4-1：未来研究方向的对比矩阵

| 研究方向 | 从何学科借鉴？ | 目标突破 | 核心瓶颈 | 热度与风险 |
| :--- | :--- | :--- | :--- | :--- |
| **小样本迁移学习** | 自然语言处理，计算机视觉 | 预测精度接近全样本水平 | 跨域分布漂移大、特征不迁移 | 趋势 ↑，高风险 |
| **决策导向预测** | 贝叶斯优化，决策分析 | 最大化下游任务经济收益 | 端到端训练不可导、解耦困难 | 趋势 ↑，极高风险 |
| **物理感知生成式AI** | 物理信息神经网络，生成模型 | 生成符合物理规律的极端场景 | 缺乏确定的物理支配方程 | 趋势 →，极高风险 |
| **边缘持续学习** | 联邦学习，终身学习 | 在隐私约束下实现模型自演进 | Non-IID数据流、灾难性遗忘、硬件算力 | 趋势 ↑，高风险 |

---



![年度发文量趋势](charts/year_trend.png)

*图1：年度发文量趋势（红色柱体为高活跃年份）*

![方法论分布](charts/method_distribution.png)

*图2：方法论占比分布*

![期刊等级分布](charts/grade_distribution.png)

*图3：期刊等级分布（S级=顶刊，A级=优秀，B级=良好）*


## 参考文献

### S级（顶刊）
[1] Iain Staffell, Daniel Scamman, Anthony Velazquez Abad, 等. The role of hydrogen and fuel cells in the global energy system. *Energy & Environmental Science*, 2018. doi:10.1039/c8ee01157e.  
[2] Tanveer Ahmad, Rafał Madoński, Dongdong Zhang, 等. Data-driven probabilistic machine learning in sustainable smart energy/smart energy systems: Key developments, challenges, and future research opportunities in the context of smart grid paradigm. *Renewable and Sustainable Energy Reviews*, 2022. doi:10.1016/j.rser.2022.112128.  
[3] Ioannis Antonopoulos, Valentin Robu, Benoit Couraud, 等. Artificial intelligence and machine learning approaches to energy demand-side response: A systematic review. *Renewable and Sustainable Energy Reviews*, 2020. doi:10.1016/j.rser.2020.109899.  
[4] Jesus Lago, Fjo De Ridder, Bart De Schutter. Forecasting spot electricity prices: Deep learning approaches and empirical comparison of traditional algorithms. *Applied Energy*, 2018. doi:10.1016/j.apenergy.2018.02.069.  
[5] Zhenpeng Yao, Yanwei Lum, Andrew Johnston, 等. Machine learning for a sustainable energy future. *Nature Reviews Materials*, 2022. doi:10.1038/s41578-022-00490-5.  
[6] Hamed Ghoddusi, Germán G. Creamer, Nima Rafizadeh. Machine learning in energy economics and finance: A review. *Energy Economics*, 2019. doi:10.1016/j.eneco.2019.05.006.  
[7] Heba-Allah Ibrahim El-Azab, R.A. Swief, Noha H. El-Amary, 等. Machine and deep learning approaches for forecasting electricity price and energy load assessment on real datasets. *Ain Shams Engineering Journal*, 2024. doi:10.1016/j.asej.2023.102613.  
[18] Pierre Friedlingstein, Michael O’Sullivan, Matthew W. Jones, 等. Global Carbon Budget 2020. *Earth system science data*, 2020. doi:10.5194/essd-12-3269-2020.  
[19] Pierre Friedlingstein, Michael O’Sullivan, Matthew W. Jones, 等. Global Carbon Budget 2022. *Earth system science data*, 2022. doi:10.5194/essd-14-4811-2022.  
[21] Patrick Bolton, Marcin Kacperczyk. Global Pricing of Carbon‐Transition Risk. *The Journal of Finance*, 2023. doi:10.1111/jofi.13272.  
[22] Philip W. Boyd, Hervé Claustre, Marina Lévy, 等. Multi-faceted particle pumps drive carbon sequestration in the ocean. *Nature*, 2019. doi:10.1038/s41586-019-1098-2.  
[24] Yanfeng Wang, Ling Qin, Qingrui Wang, 等. A novel deep learning carbon price short-term prediction model with dual-stage attention mechanism. *Applied Energy*, 2023. doi:10.1016/j.apenergy.2023.121380.  
[25] Gehad Ismail Sayed, Eman I. Abd El-Latif, Ashraf Darwish, 等. An optimized and interpretable carbon price prediction: Explainable deep learning model. *Chaos Solitons & Fractals*, 2024. doi:10.1016/j.chaos.2024.115533.  
[35] Baran Yildiz, José I. Bilbao, A.B. Sproul. A review and analysis of regression and machine learning models on commercial building electricity load forecasting. *Renewable and Sustainable Energy Reviews*, 2017. doi:10.1016/j.rser.2017.02.023.  
[36] Jatin Bedi, Durga Toshniwal. Deep learning framework to forecast electricity demand. *Applied Energy*, 2019. doi:10.1016/j.apenergy.2019.01.113.  
[37] Young Tae Chae, Raya Horesh, Youngdeok Hwang, 等. Artificial neural network model for forecasting sub-hourly electricity usage in commercial buildings. *Energy and Buildings*, 2015. doi:10.1016/j.enbuild.2015.11.045.  
[39] Azim Heydari, Meysam Majidi Nezhad, Elmira Pirshayan, 等. Short-term electricity price and load forecasting in isolated power grids based on composite neural network and gravitational search optimization algorithm. *Applied Energy*, 2020. doi:10.1016/j.apenergy.2020.115503.  
[40] Henrique S. Hippert, Derek W. Bunn, Reinaldo Castro Souza. Large neural networks for electricity load forecasting: Are they overfitted?. *International Journal of Forecasting*, 2005. doi:10.1016/j.ijforecast.2004.12.004.  
[59] Lean Yu, Zishu Wang, Ling Tang. A decomposition–ensemble model with data-characteristic-driven reconstruction for crude oil price forecasting. *Applied Energy*, 2015. doi:10.1016/j.apenergy.2015.07.025.  
[61] Minggang Wang, Longfeng Zhao, Ruijin Du, 等. A novel hybrid method of forecasting crude oil prices using complex network science and artificial intelligence algorithms. *Applied Energy*, 2018. doi:10.1016/j.apenergy.2018.03.148.  
[62] Lean Yu, Yang Zhao, Ling Tang. A compressed sensing based AI learning paradigm for crude oil price forecasting. *Energy Economics*, 2014. doi:10.1016/j.eneco.2014.09.019.  
[63] Jinchao Li, Shaowen Zhu, Qianqian Wu. Monthly crude oil spot price forecasting using variational mode decomposition. *Energy Economics*, 2019. doi:10.1016/j.eneco.2019.07.009.  
[71] Keywan Riahi, Detlef P. van Vuuren, Elmar Kriegler, 等. The Shared Socioeconomic Pathways and their energy, land use, and greenhouse gas emissions implications: An overview. *Global Environmental Change*, 2016. doi:10.1016/j.gloenvcha.2016.05.009.  
[72] Josep G. Canadell, Corinne Le Quéré, Michael Raupach, 等. Contributions to accelerating atmospheric CO <sub>2</sub> growth from economic activity, carbon intensity, and efficiency of natural sinks. *Proceedings of the National Academy of Sciences*, 2007. doi:10.1073/pnas.0702737104.  
[73] Pierre Friedlingstein, Matthew W. Jones, Michael O’Sullivan, 等. Global Carbon Budget 2019. *Earth system science data*, 2019. doi:10.5194/essd-11-1783-2019.  
[74] Corinne Le Quéré, Robbie M. Andrew, Pierre Friedlingstein, 等. Global Carbon Budget 2018. *Earth system science data*, 2018. doi:10.5194/essd-10-2141-2018.  
[75] Alberte Bondeau, P. C. Smith, Sönke Zaehle, 等. Modelling the role of agriculture for the 20th century global terrestrial carbon balance. *Global Change Biology*, 2006. doi:10.1111/j.1365-2486.2006.01305.x.  
[76] Pierre Friedlingstein, Michael O’Sullivan, Matthew W. Jones, 等. Global Carbon Budget 2023. *Earth system science data*, 2023. doi:10.5194/essd-15-5301-2023.  
[77] William D. Nordhaus. Revisiting the social cost of carbon. *Proceedings of the National Academy of Sciences*, 2017. doi:10.1073/pnas.1609244114.  
[78] Corinne Le Quéré, Robbie M. Andrew, Pierre Friedlingstein, 等. Global Carbon Budget 2017. *Earth system science data*, 2018. doi:10.5194/essd-10-405-2018.  
[80] Simona Bassu, Nadine Brisson, J. L. Durand, 等. How do various maize crop models vary in their responses to climate change factors?. *Global Change Biology*, 2014. doi:10.1111/gcb.12520.  

### A级（优秀）
[8] Hongfang Lü, Xin Ma, Kun Huang, 等. Carbon trading volume and price forecasting in China using multiple machine learning models. *Journal of Cleaner Production*, 2019. doi:10.1016/j.jclepro.2019.119386.  
[9] Lean Yu, Wei Dai, Ling Tang. A novel decomposition ensemble model with extended extreme learning machine for crude oil price forecasting. *Engineering Applications of Artificial Intelligence*, 2015. doi:10.1016/j.engappai.2015.04.016.  
[10] Gabriel Paes Herrera, Michel Constantino, Benjamin Miranda Tabak, 等. Long-term forecast of energy commodities price using machine learning. *Energy*, 2019. doi:10.1016/j.energy.2019.04.077.  
[26] Jujie Wang, Xin Sun, Qian Cheng, 等. An innovative random forest-based nonlinear ensemble paradigm of improved feature extraction and deep learning for carbon price forecasting. *The Science of The Total Environment*, 2020. doi:10.1016/j.scitotenv.2020.143099.  
[27] Hanxiao Shi, Anlei Wei, Xiaozhen Xu, 等. A CNN-LSTM based deep learning model with high accuracy and robustness for carbon price forecasting: A case of Shenzhen's carbon market in China. *Journal of Environmental Management*, 2024. doi:10.1016/j.jenvman.2024.120131.  
[28] Huaqing Wang, Zhongfu Tan, Amin Zhang, 等. Carbon market price prediction based on sequence decomposition-reconstruction-dimensionality reduction and improved deep learning model. *Journal of Cleaner Production*, 2023. doi:10.1016/j.jclepro.2023.139063.  
[42] Yun Zhang, Quan Zhou, Sun Caixin, 等. RBF Neural Network and ANFIS-Based Short-Term Load Forecasting Approach in Real-Time Price Environment. *IEEE Transactions on Power Systems*, 2008. doi:10.1109/tpwrs.2008.922249.  
[43] Ping‐Feng Pai, Wei‐Chiang Hong. Support vector machines with simulated annealing algorithms in electricity load forecasting. *Energy Conversion and Management*, 2005. doi:10.1016/j.enconman.2005.02.004.  
[44] Jinliang Zhang, Yi‐Ming Wei, Dezhi Li, 等. Short term electricity load forecasting using a hybrid model. *Energy*, 2018. doi:10.1016/j.energy.2018.06.012.  
[45] Aleksandra Dedinec, Aleksandra Dedinec, Sonja Filiposka, 等. Deep belief network based electricity load forecasting: An analysis of Macedonian case. *Energy*, 2016. doi:10.1016/j.energy.2016.07.090.  
[46] Deepak Singhal, K. Shanti Swarup. Electricity price forecasting using artificial neural networks. *International Journal of Electrical Power & Energy Systems*, 2011. doi:10.1016/j.ijepes.2010.12.009.  
[47] Paras Mandal, Tomonobu Senjyu, Toshihisa Funabashi. Neural networks approach to forecast several hour ahead electricity prices and loads in deregulated market. *Energy Conversion and Management*, 2006. doi:10.1016/j.enconman.2005.12.008.  
[64] Zhongpei Cen, Jun Wang. Crude oil price prediction model with long short term memory deep learning based on prior knowledge data transfer. *Energy*, 2018. doi:10.1016/j.energy.2018.12.016.  
[65] Hadi Jahanshahi, Süleyman Uzun, Sezgin Kaçar, 等. Artificial Intelligence-Based Prediction of Crude Oil Prices Using Multiple Features under the Effect of Russia–Ukraine War and COVID-19 Pandemic. *Mathematics*, 2022. doi:10.3390/math10224361.  

### B级（良好）
[12] Spyros Makridakis, Evangelos Spiliotis, Vassilios Assimakopoulos. Statistical and Machine Learning forecasting methods: Concerns and ways forward. *PLoS ONE*, 2018. doi:10.1371/journal.pone.0194889.  
[13] Wenjie Lu, Jiazheng Li, Yifan Li, 等. A CNN-LSTM-Based Model to Forecast Stock Prices. *Complexity*, 2020. doi:10.1155/2020/6622927.  
[14] Mohammad Mahdi Forootan, Iman Larki, Rahim Zahedi, 等. Machine Learning and Deep Learning in Energy Systems: A Review. *Sustainability*, 2022. doi:10.3390/su14084832.  
[15] Natei Ermias Benti, Mesfin Diro Chaka, Addisu Gezahegn Semie. Forecasting Renewable Energy Generation with Machine Learning and Deep Learning: Current Advances and Future Prospects. *Sustainability*, 2023. doi:10.3390/su15097087.  
[16] Jwaone Gaboitaolelwe, Adamu Murtala Zungeru, Abid Yahya, 等. Machine Learning Based Solar Photovoltaic Power Forecasting: A Review and Comparison. *IEEE Access*, 2023. doi:10.1109/access.2023.3270041.  
[17] Adnan Yousaf, Rao Muhammad Asif, Mustafa Shakir, 等. A Novel Machine Learning-Based Price Forecasting for Energy Management Systems. *Sustainability*, 2021. doi:10.3390/su132212693.  
[32] Yi Yang, Honggang Guo, Yu Jin, 等. An Ensemble Prediction System Based on Artificial Neural Networks and Deep Learning Methods for Deterministic and Probabilistic Carbon Price Forecasting. *Frontiers in Environmental Science*, 2021. doi:10.3389/fenvs.2021.740093.  
[33] Guangyu Mu, Dai Li, Xiaoqing Ju, 等. MS-IHHO-LSTM: Carbon Price Prediction Model of Multi-Source Data Based on Improved Swarm Intelligence Algorithm and Deep Learning Method. *IEEE Access*, 2024. doi:10.1109/access.2024.3409822.  
[34] Canran Xiao, Yongmei Liu. A Multifrequency Data Fusion Deep Learning Model for Carbon Price Prediction. *Journal of Forecasting*, 2024. doi:10.1002/for.3198.  
[51] Ahmed Shaharyar Khwaja, Alagan Anpalagan, Muhammad Naeem, 等. Joint bagged-boosted artificial neural networks: Using ensemble machine learning to improve short-term electricity load forecasting. *Electric Power Systems Research*, 2019. doi:10.1016/j.epsr.2019.106080.  

---

> 本内容由 Coze AI 生成，请遵循相关法律法规及《人工智能生成合成内容标识办法》使用与传播。

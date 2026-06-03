# Significance Analysis for Short-Before-Long (SbL) Results

Evaluating the statistical significance of SbL results is entirely feasible and would add robust quantitative backing to the heuristic scores (e.g., H-Score out of 6) currently used. Below is an analysis of different ways we can measure and report significance, categorized by the level of analysis.

---

## 1. Significance of the Complex SbL $\beta$ Slope (Per Language)

Currently, the SbL $\beta$ is computed via a log-log linear regression plotting aggregate constituent size against distance from the verb edge.

*   **Proposed Measure:** **OLS Regression P-Value**
*   **How it works:** When computing the linear regression using `scipy.stats.linregress` or `statsmodels`, we can extract the $p$-value associated with the slope ($\beta$). 
*   **Null Hypothesis ($H_0$):** $\beta = 0$ (Distance from the verb has no effect on constituent size).
*   **Implementation:** Store the $p$-value alongside $\beta$ in `sbl_laws_summary.csv`. On the site, we can use asterisks to denote significance (e.g., `0.345***` for $p < 0.001$, `0.102*` for $p < 0.05$, and `0.023` for not significant).

## 2. Significance of Intra-Sentence Ordering (The Horizontal Law)

The Horizontal Law compares dependents within the *same* configuration (e.g., $R_3^1$ vs $R_3^2$). Because these dependents occur in the same sentence, they are paired observations.

*   **Proposed Measure:** **Binomial Test (Sign Test)**
*   **How it works:** The pipeline already computes ordering statistics (`lt`, `eq`, `gt`) for adjacent dependents in the same sentence. 
    *   Let $N_{SBL}$ be the number of sentences where the inner dependent is strictly shorter than the outer (`lt`).
    *   Let $N_{LBS}$ be the number of sentences where the inner is strictly longer (`gt`).
    *   We perform a Binomial test on $N_{SBL}$ successes out of $(N_{SBL} + N_{LBS})$ trials with an expected probability of $p=0.5$.
*   **Null Hypothesis ($H_0$):** Inner and outer dependents are equally likely to be longer.
*   **Implementation:** This requires zero changes to the CoNLL parsing logic since the `lt/eq/gt` counts are already extracted. We simply compute the $p$-value in the summarization step.

## 3. Significance of Cross-Context Laws (Vertical & Diagonal Laws)

The Vertical Law ($R_{n+1}^k < R_n^k$) and Diagonal Law ($R_n^k < R_{n+1}^{k+1}$) compare dependents from *different* sets of sentences. These are independent samples.

*   **Proposed Measure:** **Welch's Two-Sample t-test** (or Mann-Whitney U test for non-parametric).
*   **How it works:** To test if the mean size of $R_3^1$ is significantly smaller than $R_2^1$, we need three things for both groups: Mean, Sample Size ($N$), and Variance (or Standard Deviation).
*   **Null Hypothesis ($H_0$):** $E[R_{n+1}^k] \ge E[R_n^k]$
*   **Implementation:** Currently, `conll_processing.py` tracks the sum of sizes to compute the mean, but **does not track the sum of squared sizes**. We would need a minor update to `conll_processing.py` to accumulate squared lengths (to compute variance via $E[X^2] - E[X]^2$). Once we have the variance, we can easily compute Welch's t-test for every Vertical and Diagonal pair.

## 4. Significance of Typological / Cross-Linguistic Trends

We can test whether SbL behaviors correlate significantly with other typological features (e.g., Word Order, Language Family).

*   **Proposed Measure 1: Correlation Tests (Pearson / Spearman)**
    *   **Application:** Test the correlation between the continuous **Head-Initiality Score** (or VO Score) and the **SbL $\beta$**. Does a higher degree of VO strictly correlate with a stronger SbL effect?
*   **Proposed Measure 2: Kruskal-Wallis H-Test (ANOVA)**
    *   **Application:** Test whether different language families (Indo-European vs. Sino-Tibetan vs. Austronesian) have statistically significant differences in their average SbL $\beta$.

---

## Next Steps for Implementation

If you would like to proceed with integrating significance testing, we can do it in two phases:

**Phase A (Immediate, No re-parsing required):**
1. Update `compute_sbl_laws.py` to calculate and store the OLS regression $p$-value for the SbL $\beta$.
2. Update the site generation (`sbl_page_compliance.py`) to display these $p$-values.
3. Compute Binomial test $p$-values for the Horizontal ordering pairs using the existing `lt/gt` counts.

**Phase B (Requires re-running the corpus analysis):**
1. Modify `conll_processing.py` to track the sum of squared dependency lengths.
2. Output standard deviations to the cached pickle files.
3. Compute Welch's t-test for all Vertical and Diagonal comparisons and display a "Significance Matrix" alongside the existing Validation Matrix.

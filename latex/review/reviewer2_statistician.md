# Review — Reviewer 2 (Statistician / Quantitative Linguist)

**Paper:** *Verifying the Menzerath-Altmann law on verbal constructions in 180 languages*  
**Venue:** UDW 2026  
**Recommendation:** Major revisions

---

## General Assessment

The paper tackles an interesting quantitative-linguistic question at an impressive scale (180 languages). The directional decomposition into LMAL/RMAL is a methodological contribution. However, the statistical methodology has several serious issues that undermine the reliability of the conclusions. The claims are often stated without proper statistical tests, confidence intervals, or effect-size reporting.

---

## Critical Points

### 1. No confidence intervals or standard errors on β

The entire classification of languages (MAL / Anti-MAL / grey zone) hinges on the value of β, which is estimated from a linear regression with typically 3–6 data points (n = 1 to n = 4–6). With so few points, the uncertainty on β is enormous. A language classified as "grey zone" at β = 0.08 might have a 95% CI of [−0.15, +0.31]. Without reporting standard errors or confidence intervals, the three-way classification is essentially meaningless from a statistical perspective. At minimum, bootstrap confidence intervals on β should be computed and reported.

### 2. The ±0.1 threshold for classifying languages is arbitrary

The paper divides languages into MAL (β ≥ 0.1), Anti-MAL (β ≤ −0.1), and grey zone, but provides no justification for the 0.1 cutoff. Why not 0.05? Why not 0.15? The footnote acknowledges that the range of β values differs dramatically between MAL, LMAL, and RMAL (RMAL has 48 languages with β > 0.3!), yet the same threshold is used for all three. A proper approach would use statistical significance (is β significantly different from 0?) rather than an arbitrary cutoff.

### 3. R² is mentioned but never systematically reported or used

Section 4 shows R² = 0.892 for German as an example, but R² is never reported in the results for other languages, nor used as a filter. A language might have β = 0.2 (classified as MAL) but with R² = 0.1 (the power-law model is a terrible fit). The classification should incorporate goodness-of-fit. Languages where the power-law model is a poor fit should be flagged or excluded.

### 4. OLS regression on 3–4 data points is unreliable

Fitting a linear regression with 3 to 6 points in log-log space is statistically fragile. A single outlying n-value can flip the sign of β. The paper acknowledges that MAL₁ is often misaligned (Section 4, Figure 2) but then *includes* it in β(1→∞) anyway. This is contradictory. Furthermore, with so few points, it is impossible to test whether the relationship is truly a power law (as opposed to, say, exponential or logarithmic decay). The paper should:
- Report the number of data points per language
- Consider robust regression or weighted regression (points with higher counts should count more)
- Test alternative functional forms

### 5. The minimum count threshold (n = 100) is not justified

The paper requires at least 100 verbal constructions with n dependents to compute MAL_n. Why 100 and not 50 or 200? This threshold directly affects which languages have data at which n values, which in turn affects β. The choice should be motivated (e.g., via a power analysis or stability analysis showing how β changes with different thresholds).

### 6. No statistical tests for the cross-linguistic comparisons

The paper makes comparative claims such as "VO languages are significantly more likely to show a RMAL preference than OV languages" (84% vs. 63%). The word "significantly" is used in its colloquial sense — no χ² test, Fisher exact test, or logistic regression is reported. All percentage comparisons between VO/OV groups and between LMAL/RMAL should be accompanied by proper statistical tests with p-values and effect sizes.

### 7. The weighted average for MAL_n conflates different configurations

MAL_n is computed as a weighted average across all bilateral configurations (L+R = n). This means MAL₄ averages constructions like VXXXX (4 right) with XXVXX (2 left, 2 right). These are structurally very different configurations. If constituent length behaves differently in head-initial vs. head-final positions (which the LMAL/RMAL results suggest), then averaging them introduces noise. The paper should at least discuss this and ideally show that the result is robust to disaggregation.

### 8. Multiple comparisons problem

The paper computes β for 131 languages (or 124/103 for RMAL/LMAL), classifies each, then draws conclusions from the aggregate. If β were tested for statistical significance per language (which it should be — see point 1), a multiple testing correction (e.g., Benjamini-Hochberg) would be needed. Currently, some of the 10 "Anti-MAL" languages might simply be false positives from noisy regressions.

### 9. No effect of corpus size is modeled

Corpus size varies enormously across UD treebanks (from <1K to >1M tokens). Smaller corpora will produce noisier MAL_n estimates and fewer usable n values, systematically biasing β. The paper should:
- Report corpus size per language
- Test whether β correlates with corpus size (a meta-regression)
- Consider weighting languages by data quality in the aggregate analysis

### 10. Percentages denominator confusion

The results section mixes percentages with different denominators in a confusing way. For example: "out of the 81 languages showing a RMAL effect, 57 (79%) are VO" — but then "84% vs. 63%" appears to use VO and OV *totals* as denominators. The switching between "X% of MAL languages are VO" and "X% of VO languages are MAL" is disorienting. A clear 2×3 contingency table (VO/OV/mixed × MAL/Anti/Grey) for each of MAL, LMAL, RMAL would solve this.

---

## Minor Issues

- The notation β(1→∞) is non-standard. Clarify that ∞ means "the maximum observed n," not infinity.
- Figure 2 (β(1→2) vs. β(2→∞)) is informative but would benefit from a Pearson/Spearman correlation coefficient and a line of equality.
- The mini-plots in the appendix are a nice idea but the β values could be accompanied by standard errors.
- Consider a volcano plot (β vs. −log₁₀(p)) to simultaneously visualize effect size and significance.

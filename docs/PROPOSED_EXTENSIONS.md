# Proposals for Extending Typometric Analysis

This document outlines 10 proposed statistical extensions to the current "Helix Table" analysis, designed to deepen our understanding of constituent size constraints and typological patterns.

**Difficulty Scale**: 1 (Trivial) to 5 (Major Refactor).

---

## 1. Menzerath-Altmann Law at the Constituent Level

*   **Hypothesis**: The size of constituents (in words) decreases as the number of constituents (= valency) increases. "The more parts, the smaller the parts."
*   **Method**: Compute the correlation (Pearson/Spearman) between `Tot` (total number of dependents) and the `Average Constituent Size` (marginalized over all positions for that Tot).
*   **Expected Result**: Negative correlation. Languages with complex argument structures (high valency) will prefer shorter constituents (pronominalization) to avoid memory overload.
*   **Typological Impact**: A universal constant? Or do some languages tolerate "Heavy-Heavy" structures better?
*   **Difficulty**: 2 (Easy). Requires aggregating existing `position2sizes` by `Tot` key.

## 2. Behaghel's Law Quantification (Slope Analysis)

*   **Hypothesis**: Constituent sizes increase with distance from the head (Behaghel's Law of Increasing Terms).
*   **Method**: Perform a linear regression for each language: $Size = \beta \cdot PositionIndex + \alpha$. The slope $\beta$ quantifies the strength of the "Increasing Terms" effect.
*   **Expected Result**: Positive slope for Right-branching (VO) languages ($R_1 < R_2 < R_3$). Negative slope for Left-branching (OV)? Or is it universal ($L_3 < L_2 < L_1$)?
*   **Typological Impact**: Provides a single numeric "Behaghel Score" per language, allowing easy cross-linguistic ranking.
*   **Difficulty**: 2 (Easy). Apply `scipy.stats.linregress` on the `all_langs_average_sizes`.

## 3. Log-Normality Tests for Size Distributions

*   **Hypothesis**: Constituent sizes follow a log-normal distribution (multiplicative growth processes), validating the use of Geometric Means.
*   **Method**: For each language/position, perform a Kolmogorov-Smirnov test comparing the empirical distribution of sizes against a fitted Log-Normal distribution.
*   **Expected Result**: High p-values (fail to reject null hypothesis) for Log-Normal, confirming it as a good fit.
*   **Typological Impact**: Validates the fundamental mathematical assumption of the entire project. If some languages fail (e.g., bimodal), they warrant deep investigation.
*   **Difficulty**: 3 (Medium). Requires accessing raw count distributions (currently we store aggregates, might need `position2sizes` distributional data or re-run pass).

## 4. Part-of-Speech Specific Size Profiles

*   **Hypothesis**: The "size" profile is dominated by the ratio of Pronouns (size 1) vs. Full Nouns (size > 1).
*   **Method**: Split the analysis into two streams: `VERB -> PRON` and `VERB -> NOUN/PROPN`. Generate two separate Helix Tables per language.
*   **Expected Result**: PRON tables will be flat (size ~1 everywhere). NOUN tables will show the "true" syntactic heaviness constraints without the "noise" of pronominalization.
*   **Typological Impact**: Distinguish languages that shorten constituents via dropping (Null Subject) vs. pronominalization vs. reordering.
*   **Difficulty**: 4 (Medium-Hard). Requires modifying `conll_processing.py` to key data by `(position, dependent_POS)`.

## 5. Dependency Distance vs. Constituent Size

*   **Hypothesis**: Longer dependencies (linear distance between Head and Dep) bridge larger constituents (Interference Hypothesis).
*   **Method**: Compute the correlation between the linear distance ($|Index_{Head} - Index_{Dep}|$) and the size of the dependent constituent.
*   **Expected Result**: Positive correlation. To place a dependent far away, it usually needs to be "heavy" to be recognizable (or vice versa, heavy things float to edges).
*   **Typological Impact**: Connects Dependency Length Minimization (DLM) research with Constituent Size research.
*   **Difficulty**: 3 (Medium). Data is available in `tree` object during processing.

## 6. Disorder Significance Testing (Permutation Test)

*   **Hypothesis**: The observed "disorder" (non-monotonicity) in some languages is statistically significant and not just random noise due to small sample sizes.
*   **Method**: For a specific configuration (e.g., Tot=3), scramble the observed constituent sizes 10,000 times randomly among the positions $R_1, R_2, R_3$. Calculate how often the random assignment is "more ordered" than the observation.
*   **Expected Result**: Languages labeled as "Free Word Order" might actually show random ordering (high entropy), whereas fixed order languages will be significantly different from random.
*   **Typological Impact**: Distinguishes "Flexible/Free" order from "Rigid but Non-Behaghel" order.
*   **Difficulty**: 4 (Medium). Computationally intensive; needs efficient implementation.

## 7. Left-Right Complexity Trade-off

*   **Hypothesis**: Languages trade off complexity between sides. If a language allows very heavy constituents on the Left, it restricts them on the Right (and vice versa) to keep processing load constant.
*   **Method**: For each language, compute $Sum(AvgSize_{Left})$ vs. $Sum(AvgSize_{Right})$.
*   **Expected Result**: Inverse correlation. Disproves the idea that "Complex languages are complex everywhere".
*   **Typological Impact**: Supports "Constant Entropy" or "Uniform Information Density" theories at the syntax level.
*   **Difficulty**: 2 (Easy). Simple aggregation of existing table data.

## 8. Cross-Linguistic Clustering (PCA)

*   **Hypothesis**: Languages fall into distinct clusters based on their "Size Profile" vector, aligning with families or areas.
*   **Method**: Construct a fixed-length feature vector for each language (e.g., $[R_1, R_2, R_3, L_1, L_2, L_3]$ sizes). Run PCA or t-SNE.
*   **Expected Result**: Visual clusters. OVS languages, VSO languages, and SVO languages should inhabit distinct regions of the vector space.
*   **Typological Impact**: A new method for "Quantitative Typology" based on performance/corpus stats rather than grammar rules.
*   **Difficulty**: 3 (Medium). Requires `scikit-learn` and handling missing values (imputation) for sparse positions.

## 9. Size Variance/Entropy Analysis

*   **Hypothesis**: Some positions are "rigid slots" (always small, e.g., clitics), while others are "flexible intervals" (high variance).
*   **Method**: Instead of just GM (central tendency), compute the **Geometric Standard Deviation** or Entropy of sizes at each position.
*   **Expected Result**: Positions close to the verb ($R_1, L_1$) might have lower variance (tightly bound arguments) than peripheral positions ($R_{max}, L_{max}$) which hold adjuncts/heavy clauses.
*   **Typological Impact**: Defines "Tightness" of grammar.
*   **Difficulty**: 3 (Medium). Need to track sum of squares of logs during `conll_processing`.

## 10. The "Bastard" Impact Factor

*   **Hypothesis**: Discontinuous dependencies ("Bastards") are specifically used to mitigate size constraints (i.e., Extorposition of heavy elements).
*   **Method**: Compare the average size of *Bastard* constituents vs. *Continuous* constituents at the same positions.
*   **Expected Result**: Bastards should be significantly larger on average (Heavy Shift).
*   **Typological Impact**: Explains *why* discontinuity exists—as a repair mechanism for weight processing.
*   **Difficulty**: 3 (Medium). Requires flagging `is_bastard` in the stats collection size buckets.

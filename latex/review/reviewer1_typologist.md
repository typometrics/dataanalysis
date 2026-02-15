# Review — Reviewer 1 (Linguistic Typologist)

**Paper:** *Verifying the Menzerath-Altmann law on verbal constructions in 180 languages*  
**Venue:** UDW 2026  
**Recommendation:** Major revisions

---

## General Assessment

This paper makes a valuable contribution by extending MAL analysis to 180 UD languages with a directional (LMAL/RMAL) decomposition that is novel and promising. The core finding — that MAL is stronger in the postverbal domain and anti-MAL is stronger in the preverbal domain — is typologically interesting and connects well to the existing word-order literature. However, the typological framing and argumentation have significant weaknesses that must be addressed before publication.

---

## Critical Points

### 1. The language sample is not typologically controlled — but is treated as if it were

The paper acknowledges that UD is "an ad hoc language sample" (Section 1), yet proceeds to compute percentages across the full sample (e.g., "47% of languages show MAL") as if these numbers are typologically meaningful. With roughly 40% of the sample being Indo-European, raw counts are heavily biased. The paper mentions comparing "typologically valid subsets" in the introduction but never actually defines or consistently applies such a strategy. A proper genus-level or area-controlled subsample analysis (à la Dryer 1989) is needed.

### 2. The IE / non-IE binary is too coarse

Grouping all non-Indo-European languages into a single "non-IE" category (Section 5) collapses enormous typological diversity. Niger-Congo, Austronesian, Turkic, and Sino-Tibetan have fundamentally different clause structures. At minimum, the major families should be distinguished individually, or a genus-level analysis should be presented.

### 3. VO/OV classification needs more rigour

The paper uses a continuous VO score (0–1) from corpus data, then discretises it into VO (>0.66), OV (<0.33), and mixed. Several issues:
- This is a *corpus-derived* measure, not an independent typological classification. Using WALS or Dryer's classifications would provide an independent variable and avoid circularity (both VO score and MAL are computed from the same UD data).
- The thresholds (0.33, 0.66) are arbitrary and not motivated. A sensitivity analysis varying these thresholds would strengthen the claims.
- The NDO/mixed category is poorly discussed. Are these genuinely flexible-order languages, or small corpora with noisy estimates?

### 4. "Constituent" is not defined cross-linguistically

The notion of what counts as a verbal constituent (Section 3) is defined via UD relation labels. This is operationally clear but typologically problematic. UD's treatment of function words, serial verbs, and complex predicates varies across languages. For instance, the exclusion of `aux` works fine for European languages but may systematically undercount constituents in languages with extensive auxiliary chains (Bantu, Japanese). The paper should discuss how annotation inconsistencies across treebanks affect comparability.

### 5. No discussion of areal effects

The paper finds that Bambara, Khoekhoe, and Egyptian are anti-RMAL, and that ancient languages cluster in the anti-MAL category. These observations beg for an areal and diachronic discussion. Are the anti-MAL ancient languages an artefact of genre (legal, religious texts with formulaic structures)? Are the African anti-MAL languages areally clustered? The paper merely lists these languages without analysis.

### 6. The LMAL/RMAL asymmetry needs a typological explanation

The central finding — RMAL > LMAL — is stated but not explained. Why would MAL hold more strongly after the verb? The connection to the established head-initial/final asymmetry is mentioned in one sentence (citing Faghiri 2020) but not developed. A serious typological paper should engage with:
- The processing literature on head-initial vs. head-final parsing (Hawkins 2004, Gibson 2000)
- The information-structural explanation (given-before-new, weight effects)
- The possibility that preverbal positions are more structurally rigid (scrambling constraints in OV languages)

### 7. The claim "MAL is not a universal" needs qualification

Saying "MAL is not an absolute universal" based on 10 anti-MAL languages (out of 131) is a strong negative claim. But many of these are ancient languages with small or genre-restricted corpora. The paper should distinguish between *genuine* counter-examples and cases where data quality is questionable. A truly anti-MAL modern language with a large, balanced corpus would be much more convincing.

### 8. The "grey zone" is too large

59 out of 131 languages (45%) fall in the grey zone (|β| < 0.1). This suggests either that the metric lacks discriminative power, or that the threshold is poorly calibrated. The paper should discuss what these grey-zone languages look like — are they trending MAL but with low R², or are they genuinely flat? A histogram of β values would help.

### 9. Missing discussion of polysynthetic and incorporating languages

The sample includes some polysynthetic languages (e.g., Abkhaz, various Tupian languages). In such languages, the notion of "constituent length" in tokens may be misleading because a single word can encode an entire clause. The paper should discuss whether MAL even makes typological sense for such languages, or whether a morpheme-based measure would be more appropriate.

### 10. The conclusion is empty

Section 6 is literally blank. Even for a draft, a sketch of the main takeaways, limitations, and future directions is essential for reviewers to evaluate the contribution.

---

## Minor Issues

- Numerous typos throughout: "sepertayly", "caluclated", "syntacticlanguge", "ference", "postverdal", "follwoing", "contradic", "indvidual", etc.
- The abstract says "blabla" — obviously a placeholder.
- Figure labels use `\label{tab:...}` for figures (should be `fig:`).
- Duplicate labels: `\label{tab:FamLR}` is used for two different figures (FamRL and HeadRL).
- Section 5 references "Table \ref{tab:HeadR1}" and "Table \ref{tab:HeadL1}" which are undefined.

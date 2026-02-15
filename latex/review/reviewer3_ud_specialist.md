# Review — Reviewer 3 (Universal Dependencies Specialist)

**Paper:** *Verifying the Menzerath-Altmann law on verbal constructions in 180 languages*  
**Venue:** UDW 2026  
**Recommendation:** Minor to major revisions

---

## General Assessment

The paper presents a large-scale study of MAL using UD 2.17, with a careful discussion of which dependency relations to include or exclude from verbal constructions. The directional (LMAL/RMAL) analysis is a genuine contribution that leverages the surface-order information available in UD. However, several choices in the data extraction are either under-motivated or inconsistent with UD's design principles, and the paper does not sufficiently address known annotation inconsistencies across treebanks.

---

## Critical Points

### 1. Exclusion of `case` and `mark` is debatable and consequential

The paper excludes adpositions (`case`) and subordinating conjunctions (`mark`) on the grounds that they "are generally considered as heads of the constructions." This reflects a phrase-structure bias. In UD's dependency-based analysis, these are genuine syntactic dependents of the content word. More importantly, excluding `case` means that in consistently head-final/postpositional languages (e.g., Japanese, Korean, Turkish), a large number of tokens are stripped from constituents, systematically shortening right-peripheral elements. This introduces a structural bias that could partially *explain* the RMAL/LMAL asymmetry rather than being an independent finding. The paper should at minimum report results **with and without** `case`/`mark` exclusion to assess robustness.

### 2. Handling of multi-word tokens (MWTs) and contractions

UD uses multi-word tokens for languages with contractions (French *du* = *de* + *le*, German *im* = *in* + *dem*, Arabic clitics). The paper says "the size of each constituent, punctuations excluded" but does not specify whether constituent length is measured in *syntactic words* (the analytic level) or *surface tokens*. In languages with extensive MWTs (Arabic, Hebrew, Turkish), this choice can inflate or deflate constituent length by 20–30%. This must be specified and its impact discussed.

### 3. Treebank quality and consistency vary enormously

UD 2.17 contains treebanks of drastically varying quality. Some are gold-standard manually annotated, others are automatically parsed with minimal correction. The paper treats all treebanks equally. At minimum:
- Treebanks should be classified by annotation quality (manual, corrected automatic, fully automatic)
- Results for the top-quality treebanks should be compared with the full set
- Languages with multiple treebanks of different quality (e.g., English has ~10) should be discussed: are treebanks merged or is one selected?

### 4. Multiple treebanks per language are not addressed

Several languages have many treebanks (Czech: 4, English: ~10, French: ~7). The paper does not explain whether these are merged (which conflates genres and annotation conventions) or whether one is selected (introducing selection bias). This is a critical methodological gap. Genre effects are known to affect syntactic complexity and sentence length.

### 5. The treatment of `compound` exclusion is inconsistent

The paper excludes `compound` (particle verbs like *hand out*) but this relation has very different uses across treebanks. In English, `compound:prt` marks verb particles. In Japanese, `compound` marks the first element of compound verbs (V-V compounds). In Hindi, `compound` marks light-verb constructions. Excluding all of these uniformly is not well-motivated and affects languages differently.

### 6. Copular constructions are not discussed

In UD, copulas are annotated as `cop` dependents of the predicate, not as heads. This means a sentence like "The book is interesting" has *interesting* as the head, with *book* as `nsubj` and *is* as `cop`. Since `cop` is presumably excluded (like `aux`), the verbal construction is centered on a non-verb. The paper says "we focus on verbal constructions" but does not clarify whether copular predicates are included. If they are, the "verb" is actually an adjective or noun in many cases, which muddies the typological interpretation.

### 7. The split-constituent treatment is under-specified

Section 3 mentions that extracted or extraposed elements are counted as "two separate constituents." This is a consequential choice:
- In (\ref{ex:what}), *what* and *to do* are separate constituents of *like*, so n=3 instead of n=2
- This inflates constituent counts for languages with frequent extraction (e.g., wh-movement languages)
- How is the "split" detected algorithmically? Is it based on projectivity violations? What about free-word-order languages where non-projectivity is common?
The paper needs to specify the algorithm and discuss the frequency and cross-linguistic distribution of split constituents.

### 8. Enhanced dependencies are not used but could be relevant

UD provides enhanced dependency graphs that resolve control, raising, relative clauses, and coordination sharing. The paper uses basic trees only. For MAL analysis, this matters because:
- In a raising construction (*John seems to sleep*), *John* is a dependent of *seems* in basic UD but of *sleep* in enhanced UD
- In relative clauses, the relative pronoun's role is explicit only in enhanced UD
Using enhanced dependencies could give a more accurate picture of "true" verbal constructions. At minimum this limitation should be acknowledged.

### 9. The 186→131 language reduction is not transparent

Out of 186 languages, only 131 have a computable β(1→∞). The 55 excluded languages are never listed or characterized. Are they exclusively small corpora? Do they systematically belong to certain families or areas? This could introduce a major sampling bias — if all Papuan and Australian languages are excluded due to small corpus size, the "cross-linguistic" claims are limited to Eurasia + some large-corpus languages elsewhere. A table or map of included vs. excluded languages is essential.

### 10. The `disloc` inclusion is problematic

The paper keeps `dislocated` relations "because in some languages the line between governed units and dislocated units is difficult to draw." This is true but the solution creates its own problems. Dislocated elements are by definition outside the canonical clause structure. In languages with frequent left-dislocation (e.g., spoken French, Japanese), keeping `disloc` inflates the count of preverbal constituents, which directly affects LMAL. The frequency of dislocation annotation varies enormously across treebanks (some annotate it liberally, others almost never use it). This inconsistency should be quantified.

---

## Minor Issues

- The title says "180 languages" but the analysis covers 131 (or 186 depending on which number is used). Clarify.
- Section 3 title: "Constituents in a the verbal construction" — typo ("a the").
- The paper says "we suppose a certain knowledge of the UD annotation scheme" — this is acceptable for the UD workshop, but even so, a brief reminder of the key UD conventions used (dependency vs. phrase structure, content-word heads, function-word dependents) would make the paper more self-contained.
- The UD version should be cited precisely (UD v2.17, release date, DOI).
- The list of excluded relations should be presented as a table for clarity.
- Example (\ref{ex:out}): the exclusion of *out* as `compound:prt` should use the subtype label, not just `compound`.

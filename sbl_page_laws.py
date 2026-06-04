import os
from sbl_html_utils import get_header, get_nav, get_footer

def generate(out_dir):
    html = [
        get_header("The Sy Laws Explained"),
        get_nav("sbl_laws_explained.html"),
        "<h1 title='Theoretical background and hypotheses framing the Short-Before-Long principle.'>The Sy Laws: Formal Definition</h1>",
        "<div class='explanation'>",
        "<p>The traditional Short-Before-Long (SBL) principle suggests that shorter elements tend to be placed closer to the verb than longer elements. In our verb-centered Helix configurations, this principle is formalized into three distinct <strong>Sy Laws</strong>. Let $R_n^k$ be the mean size of the $k$-th dependent on the right in a configuration with $n$ total dependents on the right. Symmetrically, let $L_n^k$ be the mean size of the $k$-th dependent on the left (where $k=1$ is closest to the verb). The laws apply equally to both directions.</p>",
        "</div>",
        
        "<h2>1. The Horizontal Law (The Standard SBL Effect)</h2>",
        "<p><strong>Definition:</strong> In a fixed configuration of $n$ dependents, the inner dependents are shorter than the outer dependents.</p>",
        "<p class='formula'>Formula: $R_n^k < R_n^{k+1}$</p>",
        "<div class='info-box'>",
        "<strong>Example:</strong> Suppose a verb has $n=3$ dependents on the right. The law predicts that the first dependent ($k=1$) is smaller than the second ($k=2$), which is smaller than the third ($k=3$).",
        "<ul><li>$R_3^1 < R_3^2$</li><li>$R_3^2 < R_3^3$</li></ul>",
        "</div>",
        """<h3>Right-Side Corpus Example (English)</h3>
<p>Notice how the first right dependent <em>strict impartiality</em> (span=2) is shorter than the second right dependent <em>in its pages</em> (span=3), which in turn is shorter than the third right dependent <em>and a reasoned assessment of various ideologies</em> (span=7). Thus $R_3^1 < R_3^2 < R_3^3$, strictly adhering to the Right Horizontal Law.</p>
<p style="font-size: 13px; color: #666; margin-bottom: 5px;">Source Treebank: <code>en_partut-ud-train</code></p>
<div style="border: 1px solid #ddd; padding: 15px; border-radius: 5px; background: #fff; overflow-x: auto; margin-bottom: 20px;">
<reactive-dep-tree interactive="true" shown-features="UPOS,LEMMA,FORM,MISC.span" conll="# text = He tried to enforce strict impartiality in its pages and a reasoned assessment of various ideologies .
1	He	He	PRON	PRON	_	2	nsubj	_	_
2	tried	tried	VERB	VERB	_	0	root	_	_
3	to	to	PART	PART	_	4	mark	_	_
4	enforce	enforce	VERB	VERB	_	2	xcomp	_	highlight=red
5	strict	strict	ADJ	ADJ	_	6	amod	_	_
6	impartiality	impartiality	NOUN	NOUN	_	4	obj	_	highlight=green|span=2
7	in	in	ADP	ADP	_	9	case	_	_
8	its	its	DET	DET	_	9	nmod:poss	_	_
9	pages	pages	NOUN	NOUN	_	4	obl	_	highlight=green|span=3
10	and	and	CCONJ	CCONJ	_	13	cc	_	_
11	a	a	DET	DET	_	13	det	_	_
12	reasoned	reasoned	VERB	VERB	_	13	acl	_	_
13	assessment	assessment	NOUN	NOUN	_	6	conj	_	highlight=green|span=7
14	of	of	ADP	ADP	_	16	case	_	_
15	various	various	ADJ	ADJ	_	16	amod	_	_
16	ideologies	ideologies	NOUN	NOUN	_	13	nmod	_	_
17	.	.	PUNCT	PUNCT	_	2	punct	_	_"></reactive-dep-tree>
</div>

<h3>Left-Side Corpus Example (English)</h3>
<p>The Sy Laws apply symmetrically to the left side ($L_n^k$, where $k$ is the distance from the verb to the left). Notice how the inner left dependent <em>the FBI</em> (span=2) is shorter than the outer left dependent <em>In a bulletin</em> (span=3). Thus $L_2^1 < L_2^2$, adhering to the Left Horizontal Law.</p>
<p style="font-size: 13px; color: #666; margin-bottom: 5px;">Source Treebank: <code>en_ewt-ud-train</code></p>
<div style="border: 1px solid #ddd; padding: 15px; border-radius: 5px; background: #fff; overflow-x: auto; margin-bottom: 20px;">
<reactive-dep-tree interactive="true" shown-features="UPOS,LEMMA,FORM,MISC.span" conll="# text = In a bulletin , the FBI noted that the surveillance might relate to a plot to disperse a chemical or biological weapon .
1	In	In	ADP	ADP	_	3	case	_	_
2	a	a	DET	DET	_	3	det	_	_
3	bulletin	bulletin	NOUN	NOUN	_	7	obl	_	highlight=green|span=3
4	,	,	PUNCT	PUNCT	_	3	punct	_	_
5	the	the	DET	DET	_	6	det	_	_
6	FBI	FBI	PROPN	PROPN	_	7	nsubj	_	highlight=green|span=2
7	noted	noted	VERB	VERB	_	0	root	_	highlight=red
8	that	that	SCONJ	SCONJ	_	12	mark	_	_
9	the	the	DET	DET	_	10	det	_	_
10	surveillance	surveillance	NOUN	NOUN	_	12	nsubj	_	_
11	might	might	AUX	AUX	_	12	aux	_	_
12	relate	relate	VERB	VERB	_	7	ccomp	_	_
13	to	to	ADP	ADP	_	15	case	_	_
14	a	a	DET	DET	_	15	det	_	_
15	plot	plot	NOUN	NOUN	_	12	obl	_	_
16	to	to	PART	PART	_	17	mark	_	_
17	disperse	disperse	VERB	VERB	_	15	acl	_	_
18	a	a	DET	DET	_	22	det	_	_
19	chemical	chemical	ADJ	ADJ	_	22	amod	_	_
20	or	or	CCONJ	CCONJ	_	21	cc	_	_
21	biological	biological	ADJ	ADJ	_	19	conj	_	_
22	weapon	weapon	NOUN	NOUN	_	17	obj	_	_
23	.	.	PUNCT	PUNCT	_	7	punct	_	_"></reactive-dep-tree>
</div>""",
        
        "<h2>2. The Vertical Law</h2>",
        "<p><strong>Definition:</strong> When a new dependent is added to the periphery (increasing $n$), the existing inner dependents tend to shrink in size to compensate.</p>",
        "<p class='formula'>Formula: $R_{n+1}^k < R_n^k$</p>",
        "<div class='info-box'>",
        "<strong>Example:</strong> Compare a verb with 2 dependents vs a verb with 3 dependents. The first dependent in the 3-dependent configuration ($R_3^1$) will typically be shorter than the first dependent in the 2-dependent configuration ($R_2^1$).",
        "<ul><li>$R_3^1 < R_2^1$</li><li>$R_4^2 < R_3^2$</li></ul>",
        "</div>",
        "<div class='explanation' style='border-left-color: #2196F3; background: #e3f2fd;'>",
        "<p><strong>Theoretical Connection:</strong> The Vertical Law can be seen as an emergent property of the co-effect between the Horizontal Law and the Menzerath-Altmann Law (MAL). Put simply: <em>Horizontal Law + MAL &approx; Vertical Law</em>.</p>",
        "<p style='font-size: 0.9em;'><strong>Reference:</strong> Chen, X., Gerdes, K., Kahane, S., & Courtin, M. (2022). <a href='https://kahane.fr/wp-content/uploads/2022/09/the-co-effect-of-menzerath-altmann-law-and-heavy-constituent-shift-in-natural-languages.pdf' target='_blank'>The Co-Effect of Menzerath-Altmann Law and Heavy Constituent Shift in Natural Languages</a>. In <em>Quantitative Approaches to Universality and Individuality in Language</em> (pp. 11-24). De Gruyter.</p>",
        "</div>",
        
        "<h2>3. The Diagonal Law</h2>",
        "<p><strong>Definition:</strong> A dependent at position $k$ in an $n$-dependent configuration is shorter than the dependent at position $k+1$ in an $(n+1)$-dependent configuration.</p>",
        "<p class='formula'>Formula: $R_n^k < R_{n+1}^{k+1}$</p>",
        "<div class='info-box'>",
        "<strong>Example:</strong> This connects the Horizontal and Vertical laws diagonally across the Helix table.",
        "<ul><li>$R_2^1 < R_3^2$</li><li>$R_3^2 < R_4^3$</li></ul>",
        "</div>",
        
        "<h2>The Complex SbL $\\beta$ Regression</h2>",
        "<p>To summarize these effects into a single robust metric, we compute a log-log linear regression capturing how constituent size scales with distance from the absolute edge of the configuration.</p>",
        "<ul>",
        "<li><strong>Right Side Regression:</strong> We plot points at $X = -\\log(n+1-k)$ and $Y = \\log(R_n^k)$. The slope of this line is the Right SbL $\\beta$.</li>",
        "<li><strong>Left Side Regression:</strong> We plot points at $X = \\log(n+1-k)$ and $Y = \\log(L_n^k)$. Here, $n+1-k$ represents the distance outward from the verb. Since \"Short-Before-Long\" on the left side implies dependents further outward (which occur earlier) should be shorter, size naturally decreases as distance increases. Thus, a perfectly compliant language will yield a <strong>negative slope</strong> ($\\beta$). In comparative visualizations across this site, Left slopes are negated so that a positive value (Green) consistently indicates compliance.</li>",
        "</ul>",
        
        "<h2>4. Outer Constituent Ratio Effects</h2>",
        "<div class='explanation'>",
        "<p><strong>What is measured:</strong> The Right (or Left) Outer Constituent Ratio Effect is the geometric mean of the \"outermost\" horizontal ratios ($R_n^n / R_n^{n-1}$) divided by the geometric mean of the remaining inner horizontal ratios (e.g., $R_4^2 / R_4^1$).</p>",
        "<p><strong>Calculation & Thresholds:</strong>",
        "<ul>",
        "<li>We extract horizontal ratios across $n \\in \\{2, 3, 4\\}$ from the <strong>AnyOtherSide</strong> table.</li>",
        "<li><strong>Robustness Threshold:</strong> Any specific configuration (e.g. $n=4$) must have at least $10$ sentences ($N \\ge 10$) in the corpus to be included in the calculation. Configurations with $N < 10$ are excluded to prevent noise.</li>",
        "<li>The <strong>Outer GM</strong> is the geometric mean of all valid outermost step ratios.</li>",
        "<li>The <strong>Inner GM</strong> is the geometric mean of all remaining valid inner step ratios.</li>",
        "<li>The final metric is the <strong>Effect Ratio</strong> = $\\text{Outer GM} / \\text{Inner GM}$.</li>",
        "</ul></p>",
        "<p><strong>The Hypothesis:</strong> We hypothesize that the Short-Before-Long effect is not uniform across all positions in the sentence. Instead, the pressure to place long constituents far from the verb becomes exponentially stronger at the absolute periphery of the clause. A ratio effect &gt; 1 confirms this hypothesis, indicating that the relative jump in size at the outermost boundary is significantly larger than the size changes closer to the verb.</p>",
        "</div>",
        
        "<h2>5. Horizontal Right-Left Effect</h2>",
        "<div class='explanation'>",
        "<p><strong>What is measured:</strong> The overall geometric mean of all valid Right horizontal ratios ($R_n^{k+1} / R_n^k$) divided by the overall geometric mean of all valid Left horizontal ratios ($L_n^{k+1} / L_n^k$).</p>",
        "<p><strong>Calculation & Thresholds:</strong> Uses the exact same robustness thresholds ($n \\in \\{2, 3, 4\\}$ and $N \\ge 10$) on the AnyOtherSide table as the Outer Constituent Ratio Effect. We first compute the global geometric mean of all valid horizontal growth steps on the Right, and do the same for the Left. The final score is $\\text{Right GM} / \\text{Left GM}$.</p>",
        "<p><strong>The Hypothesis:</strong> This captures broad structural asymmetry. Post-verbal (Right) domains often tolerate and exhibit stronger Short-Before-Long effects than pre-verbal (Left) domains. A score &gt; 1 confirms that right-ward branching dependencies grow at a faster structural rate than left-ward dependencies.</p>",
        "</div>",
        
        get_footer()
    ]
    
    with open(os.path.join(out_dir, "sbl_laws_explained.html"), "w", encoding="utf-8") as f:
        f.write("\n".join(html))

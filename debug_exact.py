
from conll import conllFile2trees
from conll_processing import get_bastard_stats
import os

def test_exact_example():
    conll_content = """
# Example 1
# sent_id = train-s6
# text = Sauberkeit, Ordnung und Freundlichkeit brauche ich hier nicht zu erwähnen, denn das gehört für mich zum Standard, der aber auch noch übertroffen wird.
1	Sauberkeit	Sauberkeit	NOUN	NN	Case=Nom|Gender=Fem|Number=Sing	11	obj	_	SpaceAfter=No
2	,	,	PUNCT	$,	_	3	punct	_	_
3	Ordnung	Ordnung	NOUN	NN	Case=Nom|Gender=Fem|Number=Sing	1	conj	_	_
4	und	und	CCONJ	KON	_	5	cc	_	_
5	Freundlichkeit	Freundlichkeit	NOUN	NN	Case=Nom|Gender=Fem|Number=Sing	1	conj	_	_
6	brauche	brauchen	VERB	VVFIN	Mood=Ind|Number=Sing|Person=1|Tense=Pres|VerbForm=Fin	0	root	_	_
7	ich	ich	PRON	PPER	Case=Nom|Number=Sing|Person=1|PronType=Prs	6	nsubj	_	_
8	hier	hier	ADV	ADV	_	6	advmod	_	_
9	nicht	nicht	PART	PTKNEG	Polarity=Neg	11	advmod	_	_
10	zu	zu	PART	PTKZU	_	11	mark	_	_
11	erwähnen	erwähnen	VERB	VVINF	VerbForm=Inf	6	acl	_	SpaceAfter=No
12	,	,	PUNCT	$,	_	15	punct	_	_
13	denn	denn	SCONJ	KON	_	15	mark	_	_
14	das	der	PRON	PDS	Case=Nom|Gender=Neut|Number=Sing|PronType=Dem,Rel	15	nsubj	_	_
15	gehört	gehören	VERB	VVFIN	Mood=Ind|Number=Sing|Person=3|Tense=Pres|VerbForm=Fin	6	advcl	_	_
16	für	für	ADP	APPR	_	17	case	_	_
17	mich	ich	PRON	PPER	Case=Acc|Number=Sing|Person=1|PronType=Prs	15	obl	_	_
18	zu	zu	ADP	APPR	_	20	case	_	_
19	dem	der	DET	ART	Case=Dat|Definite=Def|Gender=Masc|Number=Sing|PronType=Art	20	det	_	_
20	Standard	Standard	NOUN	NN	Case=Dat|Gender=Masc|Number=Sing	15	obl	_	SpaceAfter=No
21	,	,	PUNCT	$,	_	26	punct	_	_
22	der	der	PRON	PRELS	Case=Nom|Gender=Masc|Number=Sing|PronType=Dem,Rel	26	nsubj:pass	_	_
23	aber	aber	ADV	ADV	_	26	advmod	_	_
24	auch	auch	ADV	ADV	_	25	advmod	_	_
25	noch	noch	ADV	ADV	_	26	advmod	_	_
26	übertroffen	übertreffen	VERB	VVPP	VerbForm=Part	20	acl	_	_
27	wird	werden	AUX	VAFIN	Mood=Ind|Number=Sing|Person=3|Tense=Pres|VerbForm=Fin|Voice=Pass	26	aux:pass	_	SpaceAfter=No
28	.	.	PUNCT	$.	_	6	punct	_	_
"""
    with open("temp_test.conllu", "w") as f:
        f.write(conll_content.strip())
        
    trees = conllFile2trees("temp_test.conllu")
    tree = trees[0]
    
    tree.addspan(exclude=['punct'], compute_bastards=True)
    
    print("Bastards found:")
    for i in tree:
        if tree[i].get('bastards'):
            print(f"Node {i} ({tree[i]['t']}) has bastards: {tree[i]['bastards']}")
            for b in tree[i]['bastards']:
                print(f"  Bastard {b} ({tree[b]['t']}) relation: {tree[b]['gov']}")

    v, b, r, ex = get_bastard_stats(tree)
    print(f"\nStats: Verbs={v}, Bastards={b}, Relations={r}")
    
    os.remove("temp_test.conllu")

if __name__ == "__main__":
    test_exact_example()

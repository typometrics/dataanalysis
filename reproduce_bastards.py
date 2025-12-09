
import sys
sys.path.append('/bigstorage/kim/typometrics/dataanalysis')
from conll import Tree

def test_bastards():
    # Example: "he met a guy on Friday night who seemed really nice."
    # 1: he (nsubj) -> 2
    # 2: met (root)
    # 3: a (det) -> 4
    # 4: guy (obj) -> 2
    # 5: on (case) -> 6
    # 6: Friday (obl) -> 2
    # 7: night (flat) -> 6
    # 8: who (nsubj) -> 9
    # 9: seemed (acl:relcl) -> 4
    # 10: really (advmod) -> 11
    # 11: nice (xcomp) -> 9
    
    # Note: "who seemed really nice" is the relative clause.
    # "who" (8) is usually the nsubj of "seemed" (9).
    # "seemed" (9) is the head of the relative clause, attached to "guy" (4).
    # So 4 -> 9.
    # 9 -> 8.
    # 9 -> 11.
    # 11 -> 10.
    
    # Let's build the tree manually.
    t = Tree()
    t[1] = {'id': 1, 't': 'he', 'gov': {2: 'nsubj'}}
    t[2] = {'id': 2, 't': 'met', 'gov': {0: 'root'}}
    t[3] = {'id': 3, 't': 'a', 'gov': {4: 'det'}}
    t[4] = {'id': 4, 't': 'guy', 'gov': {2: 'obj'}}
    t[5] = {'id': 5, 't': 'on', 'gov': {6: 'case'}}
    t[6] = {'id': 6, 't': 'Friday', 'gov': {2: 'obl'}}
    t[7] = {'id': 7, 't': 'night', 'gov': {6: 'flat'}}
    t[8] = {'id': 8, 't': 'who', 'gov': {9: 'nsubj'}}
    t[9] = {'id': 9, 't': 'seemed', 'gov': {4: 'acl:relcl'}}
    t[10] = {'id': 10, 't': 'really', 'gov': {11: 'advmod'}}
    t[11] = {'id': 11, 't': 'nice', 'gov': {9: 'xcomp'}}
    
    print("Tree constructed.")
    t.addkids()
    print("Kids added.")
    
    # Current behavior
    t.addspan(compute_bastards=True)
    print("Span added with compute_bastards=True.")
    print(f"Span of 'guy' (4): {t[4]['span']}")
    
    print(f"Direct Span of 'guy' (4): {t[4].get('direct_span')}")
    print(f"Bastards of 'guy' (4): {t[4].get('bastards')}")
    print(f"All kids of 'guy' (4): {t[4].get('all_kids')}")
    
    print(f"Direct Span of 'met' (2): {t[2].get('direct_span')}")
    print(f"Bastards of 'met' (2): {t[2].get('bastards')}")
    print(f"All kids of 'met' (2): {t[2].get('all_kids')}")
    
    # Verification
    # 9 (who) should be bastard of 2 (met)
    if 9 in t[2].get('bastards', []):
        print("SUCCESS: 9 is a bastard of 2.")
    else:
        print("FAILURE: 9 is NOT a bastard of 2.")
        
    # 9 should NOT be in direct_span of 4
    if 9 not in t[4].get('direct_span', []):
        print("SUCCESS: 9 is removed from direct_span of 4.")
    else:
        print("FAILURE: 9 is STILL in direct_span of 4.")
        
    # 9 should be in all_kids of 2
    if 9 in t[2].get('all_kids', []):
        print("SUCCESS: 9 is in all_kids of 2.")
    else:
        print("FAILURE: 9 is NOT in all_kids of 2.")

    return t

if __name__ == "__main__":
    t = test_bastards()

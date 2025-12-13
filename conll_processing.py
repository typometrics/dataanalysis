"""
CoNLL file processing and dependency analysis functions.
"""

import os
import re
import psutil
import multiprocessing
from tqdm.notebook import tqdm
from conll import conllFile2trees
from tqdm import tqdm
import functools

# Compile regex pattern for relation splitting
relation_split = re.compile(r'\W')


def make_shorter_conll_files(langConllFiles, version):
    """
    Split large CoNLL files into chunks of 10,000 sentences each.
    
    Parameters
    ----------
    langConllFiles : dict
        Dictionary mapping language codes to lists of CoNLL file paths
    version : str
        Version string (e.g., 'ud-treebanks-v2.17')
        
    Returns
    -------
    tuple
        (lang2shortconll, allshortconll) where:
        - lang2shortconll: dict mapping language codes to lists of short file paths
        - allshortconll: flat list of all short file paths
    """
    directory = version + "_short"
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    lang2shortconll = {}
    allshortconll = []
    
    for lang in tqdm(langConllFiles, desc="Processing languages"):
        lang2shortconll[lang] = []
        
        for conllfile in langConllFiles[lang]:
            starter = '' if os.path.basename(conllfile).startswith(lang + '_') else lang + '_'
            with open(conllfile) as f:
                conll = f.read()
            sentences = conll.split('\n\n')
            
            for i in range(0, len(sentences), 10000):
                shortconll = '\n\n'.join(sentences[i:i+10000])
                shortconllfile = os.path.join(
                    directory, 
                    starter + os.path.basename(conllfile).replace('.conllu', '') + f'_{i}.conllu'
                )
                lang2shortconll[lang].append(shortconllfile)
                allshortconll.append(shortconllfile)
                with open(shortconllfile, 'w') as f:
                    f.write(shortconll)
    
    print(f"Created {len(allshortconll)} short CoNLL files in {directory}")
    return lang2shortconll, allshortconll


def read_shorter_conll_files(langConllFiles, version):
    """
    Read existing shorter CoNLL files from directory.
    
    Parameters
    ----------
    langConllFiles : dict
        Dictionary mapping language codes to lists of CoNLL file paths
    version : str
        Version string (e.g., 'ud-treebanks-v2.17')
        
    Returns
    -------
    tuple
        (lang2shortconll, allshortconll)
    """
    directory = version + "_short"
    lang2shortconll = {}
    allshortconll = []
    
    for lang in langConllFiles:
        lang2shortconll[lang] = []
        for shortconllfile in os.listdir(directory):
            if shortconllfile.startswith(lang + '_'):
                lang2shortconll[lang].append(os.path.join(directory, shortconllfile))
        allshortconll.extend(lang2shortconll[lang])
    
    print(f"Found {len(allshortconll)} short CoNLL files in {directory}")
    return lang2shortconll, allshortconll


def process_kids(tree, kids, direction, other_kids, position2num, position2sizes, sizes2freq, use_direct_span=False):
    """
    Process the dependents of a head in a given direction (left or right).
    
    The function updates the position2num, position2sizes and sizes2freq dictionaries.
    
    Parameters
    ----------
    tree : dict
        Dependency tree structure
    kids : list
        List of dependent node IDs
    direction : str
        Either 'left' or 'right'
    other_kids : list
        List of dependents in the opposite direction (unused currently)
    position2num : dict
        Dictionary tracking occurrence counts for each position type
    position2sizes : dict
        Dictionary tracking total sizes for each position type
    sizes2freq : dict
        Dictionary tracking size distributions for each position type
    use_direct_span : bool, optional
        If True, use 'direct_span' for size calculation. Else use 'span'.
    """
    kids_sizes = []
    
    for i, ki in enumerate(kids):
        # Create key for the position of the kid: from the verb to the outside nodes
        if direction == "right":
            key_base = f'{direction}_{i+1}'
        else:  # left
            key_base = f'{direction}_{len(kids)-i}'
        
        # Update position2num: count occurrences
        position2num[key_base] = position2num.get(key_base, 0) + 1
        
        # Determine size based on flag
        if use_direct_span:
            size = len(tree[ki].get('direct_span', tree[ki]['span']))
        else:
            size = len(tree[ki]['span'])
        
        # Update position2sizes: accumulate sizes
        position2sizes[key_base] = position2sizes.get(key_base, 0) + size
        
        # Context-aware key including total number of kids in this direction
        key_tot = f'{key_base}_tot{direction}_{len(kids)}'
        position2num[key_tot] = position2num.get(key_tot, 0) + 1
        position2sizes[key_tot] = position2sizes.get(key_tot, 0) + size
        
        kids_sizes.append(size)
    
    # Average key for this configuration
    avg_key = f'average_tot{direction}_{len(kids)}'
    position2num[avg_key] = position2num.get(avg_key, 0) + 1
    position2sizes[avg_key] = position2sizes.get(avg_key, 0) + (
        sum(kids_sizes) / len(kids_sizes) if kids_sizes else 0
    )
    
    # Track size distributions
    sizes2freq[avg_key] = sizes2freq.get(avg_key, {})
    sizes2freq[avg_key][str(kids_sizes)] = sizes2freq[avg_key].get(str(kids_sizes), 0) + 1


def get_ordering_stats(tree, include_bastards=False):
    """
    Compute ordering statistics for each configuration (side, tot).
    
    Returns counts of size comparisons between adjacent constituents.
    
    Parameters
    ----------
    tree : dict
        Dependency tree structure
    include_bastards : bool
        Whether to include bastard dependencies
        
    Returns
    -------
    dict
        Dictionary mapping (side, tot, position_idx) to {'lt': 0, 'eq': 0, 'gt': 0}
        position_idx corresponds to the index of the first element in the pair.
        For Right tot=3 (1,2,3): 
            idx=0 -> pair(1,2)
            idx=1 -> pair(2,3)
        For Left tot=3 (3,2,1):
            idx=0 -> pair(3,2)
            idx=1 -> pair(2,1)
    """
    ordering_stats = {}
    
    # Only consider VERB governors
    head_pos = ["VERB"]
    
    # Only consider these dependency relations
    deps = [
        "nsubj", "obj", "iobj", "csubj", "ccomp", "xcomp", 
        "obl", "expl", "dislocated", "advcl", "advmod", 
        "nmod", "appos", "nummod", "acl", "amod"
    ]
    
    # Find all verb heads with spans
    heads = [i for i in tree if len(tree[i]["span"]) > 1 and tree[i]["tag"] in head_pos]
    
    for head in heads:
        relevant_kids = []
        
        # Identify valid direct kids
        valid_direct_kids = {
            ki for (ki, krel) in tree[head]['kids'].items()
            if relation_split.split(krel)[0] in deps
        }
        
        if include_bastards:
            all_kids = tree[head].get('all_kids', list(tree[head]['kids'].keys()))
            
            for k in all_kids:
                if k in valid_direct_kids:
                    relevant_kids.append(k)
                elif k not in tree[head]['kids']:
                    # Find bastard's ancestor that is a direct kid
                    curr = k
                    ancestor = None
                    steps = 0
                    while steps < 100:
                        govs = tree[curr].get('gov', {})
                        p = None
                        for g in govs:
                            if g > 0: 
                                p = g
                                break
                        
                        if p == head:
                            ancestor = curr
                            break
                        elif p is None:
                            break
                        else:
                            curr = p
                        steps += 1
                    
                    if ancestor and ancestor in valid_direct_kids:
                        relevant_kids.append(k)
        else:
            relevant_kids = list(valid_direct_kids)

        # Get left and right dependents
        # Left kids: sorted visually Left-to-Right (furthest ... closest)
        # IDs: smaller < head. So smallest ID is furthest left.
        # sorted() gives smallest first. So [far, ..., close]
        left_kids = sorted([ki for ki in relevant_kids if ki < head])
        
        # Right kids: sorted visually Left-to-Right (closest ... furthest)
        # IDs: larger > head. So smallest ID is closest.
        # sorted() gives smallest first. So [close, ..., far]
        right_kids = sorted([ki for ki in relevant_kids if ki > head])
        
        # Check ordering for right side (Right-to-Left visual order: V -> R1 -> R2)
        # right_kids are [R1, R2, ...] (Left-to-Right)
        if len(right_kids) >= 2:
            if include_bastards:
                sizes = [len(tree[ki].get('direct_span', tree[ki]['span'])) for ki in right_kids]
            else:
                sizes = [len(tree[ki]['span']) for ki in right_kids]
            
            # Pairs (R1, R2), (R2, R3)...
            for i in range(len(sizes) - 1):
                key = ('right', len(right_kids), i) # i is index of first element (Left one visually)
                if key not in ordering_stats:
                    ordering_stats[key] = {'lt': 0, 'eq': 0, 'gt': 0}
                
                s1 = sizes[i]
                s2 = sizes[i+1]
                
                if s1 < s2:
                    ordering_stats[key]['lt'] += 1
                elif s1 == s2:
                    ordering_stats[key]['eq'] += 1
                else:
                    ordering_stats[key]['gt'] += 1
        
        # Check ordering for left side (Left-to-Right visual order: Lk...L2 -> L1 -> V)
        # left_kids are [Lk, ..., L2, L1] (Left-to-Right, IDs increasing towards head)
        if len(left_kids) >= 2:
            if include_bastards:
                sizes = [len(tree[ki].get('direct_span', tree[ki]['span'])) for ki in left_kids]
            else:
                sizes = [len(tree[ki]['span']) for ki in left_kids]
            
            # Pairs (Lk, Lk-1)...
            for i in range(len(sizes) - 1):
                # Visually: sizes[i] is to the left of sizes[i+1]
                # Compare sizes[i] vs sizes[i+1]
                
                key = ('left', len(left_kids), i)
                if key not in ordering_stats:
                    ordering_stats[key] = {'lt': 0, 'eq': 0, 'gt': 0}
                
                s1 = sizes[i]
                s2 = sizes[i+1]
                
                if s1 < s2:
                    ordering_stats[key]['lt'] += 1
                elif s1 == s2:
                    ordering_stats[key]['eq'] += 1
                else:
                    ordering_stats[key]['gt'] += 1
    
    return ordering_stats


def get_dep_sizes(tree, position2num=None, position2sizes=None, sizes2freq=None, include_bastards=False):
    """
    Get the sizes of dependents in a dependency tree.
    
    Only considers governors that are verbs and specific dependency relations.
    
    Parameters
    ----------
    tree : dict
        Dependency tree structure
    position2num : dict, optional
        Dictionary to accumulate occurrence counts
    position2sizes : dict, optional
        Dictionary to accumulate total sizes
    sizes2freq : dict, optional
        Dictionary to accumulate size distributions
    include_bastards : bool, optional
        Whether to include bastard dependencies
        
    Returns
    -------
    tuple
        (position2num, position2sizes, sizes2freq)
    """
    if position2num is None:
        position2num = {}
    if position2sizes is None:
        position2sizes = {}
    if sizes2freq is None:
        sizes2freq = {}
    
    # Only consider VERB governors
    head_pos = ["VERB"]
    
    # Only consider these dependency relations
    deps = [
        "nsubj", "obj", "iobj", "csubj", "ccomp", "xcomp", 
        "obl", "expl", "dislocated", "advcl", "advmod", 
        "nmod", "appos", "nummod", "acl", "amod"
    ]
    
    # Find all verb heads with spans
    heads = [i for i in tree if len(tree[i]["span"]) > 1 and tree[i]["tag"] in head_pos]
    
    for head in heads:
        relevant_kids = []
        
        # Identify valid direct kids (those with allowed relations)
        valid_direct_kids = {
            ki for (ki, krel) in tree[head]['kids'].items()
            if relation_split.split(krel)[0] in deps
        }
        
        if include_bastards:
            # Iterate over all_kids (includes bastards)
            # tree[head]['all_kids'] should exist if include_bastards was used in addspan
            all_kids = tree[head].get('all_kids', list(tree[head]['kids'].keys()))
            
            for k in all_kids:
                if k in valid_direct_kids:
                    relevant_kids.append(k)
                elif k not in tree[head]['kids']:
                    # It's a bastard. Find its ancestor that is a direct kid of head.
                    # Climb up parents until we hit a node whose parent is head
                    curr = k
                    ancestor = None
                    # Safety counter to prevent infinite loops in cyclic graphs (though trees shouldn't have them)
                    steps = 0
                    while steps < 100:
                        govs = tree[curr].get('gov', {})
                        # gov is {head_id: rel}
                        # We assume single head for tree structure
                        # But conll.py allows multiple heads? 
                        # Standard dependency tree has one head.
                        # Let's pick the first one that is not 0 (root) or -1
                        p = None
                        for g in govs:
                            if g > 0: 
                                p = g
                                break
                        
                        if p == head:
                            ancestor = curr
                            break
                        elif p is None:
                            break # Reached root or detached
                        else:
                            curr = p
                        steps += 1
                    
                    if ancestor and ancestor in valid_direct_kids:
                        relevant_kids.append(k)
        else:
            relevant_kids = list(valid_direct_kids)

        # Get left dependents (sorted right to left, i.e., closest to verb first)
        left_kids = sorted([
            ki for ki in relevant_kids 
            if ki < head
        ], reverse=True)
        
        # Get right dependents (sorted left to right, i.e., closest to verb first)
        right_kids = sorted([
            ki for ki in relevant_kids 
            if ki > head
        ])
        
        if left_kids:
            process_kids(tree, left_kids, 'left', right_kids, position2num, position2sizes, sizes2freq, use_direct_span=include_bastards)
        
        if right_kids:
            process_kids(tree, right_kids, 'right', left_kids, position2num, position2sizes, sizes2freq, use_direct_span=include_bastards)
    
    return position2num, position2sizes, sizes2freq


def get_dep_sizes_file(conll_filename, include_bastards=False, compute_sentence_disorder=False):
    """
    Get the sizes of dependents in a CoNLL file.
    
    Calls get_dep_sizes on each tree in the file.
    
    Parameters
    ----------
    conll_filename : str
        Path to CoNLL file
    include_bastards : bool
        Whether to include bastard dependencies
    compute_sentence_disorder : bool
        Whether to also compute sentence-level disorder statistics
        
    Returns
    -------
    tuple
        If compute_sentence_disorder=False: (lang, position2num, position2sizes, sizes2freq)
        If compute_sentence_disorder=True: (lang, position2num, position2sizes, sizes2freq, sentence_disorder_stats)
    """
    lang = os.path.basename(conll_filename).split('_')[0]
    position2num, position2sizes, sizes2freq = {}, {}, {}
    sentence_disorder_stats = {} if compute_sentence_disorder else None
    
    for tree in conllFile2trees(conll_filename):
        tree.addspan(exclude=['punct'], compute_bastards=include_bastards)
        get_dep_sizes(tree, position2num, position2sizes, sizes2freq, include_bastards=include_bastards)
        
        if compute_sentence_disorder:
            # Get disorder stats for this sentence
            disorder = get_sentence_disorder(tree, include_bastards=include_bastards)
            
            # Accumulate disorder stats
            for key, disorder_flags in disorder.items():
                if key not in sentence_disorder_stats:
                    sentence_disorder_stats[key] = []
                sentence_disorder_stats[key].extend(disorder_flags)
    
    if compute_sentence_disorder:
        return (lang, position2num, position2sizes, sizes2freq, sentence_disorder_stats)
    else:
        return (lang, position2num, position2sizes, sizes2freq)


def get_type_freq_all_files_parallel(allshortconll, include_bastards=False, compute_sentence_disorder=False):
    """
    Process all short CoNLL files in parallel to compute dependency statistics.
    
    Parameters
    ----------
    allshortconll : list
        List of paths to short CoNLL files
    include_bastards : bool
        Whether to include bastard dependencies
    compute_sentence_disorder : bool
        Whether to also compute sentence-level disorder percentages
        
    Returns
    -------
    tuple
        If compute_sentence_disorder=False: 
            (all_langs_position2num, all_langs_position2sizes, all_langs_average_sizes)
        If compute_sentence_disorder=True:
            (all_langs_position2num, all_langs_position2sizes, all_langs_average_sizes, sentence_disorder_percentages)
    """
    
    
    print(f"Starting processing all files, running on {psutil.cpu_count()} cores")
    
    all_langs_average_sizes = {}
    all_langs_position2num = {}
    all_langs_position2sizes = {}
    all_langs_sentence_disorder = {} if compute_sentence_disorder else None
    
    with multiprocessing.Pool(psutil.cpu_count()) as pool:
        # Use imap for better progress tracking
        # Use partial to pass arguments
        process_func = functools.partial(
            get_dep_sizes_file, 
            include_bastards=include_bastards,
            compute_sentence_disorder=compute_sentence_disorder
        )
        results = list(tqdm(
            pool.imap(process_func, allshortconll),
            total=len(allshortconll),
            desc="Processing files"
        ))
        
        print(f'Finished processing. Combining results...')
        
        for result in results:
            if compute_sentence_disorder:
                lang, position2num, position2sizes, sizes2freq, sentence_disorder_stats = result
            else:
                lang, position2num, position2sizes, sizes2freq = result
                sentence_disorder_stats = None
            
            all_langs_position2sizes[lang] = all_langs_position2sizes.get(lang, {})
            all_langs_position2num[lang] = all_langs_position2num.get(lang, {})
            
            for ty, size in position2sizes.items():
                all_langs_position2sizes[lang][ty] = all_langs_position2sizes[lang].get(ty, 0) + size
                all_langs_position2num[lang][ty] = all_langs_position2num[lang].get(ty, 0) + position2num[ty]
            
            if compute_sentence_disorder and sentence_disorder_stats:
                if lang not in all_langs_sentence_disorder:
                    all_langs_sentence_disorder[lang] = {}
                
                for key, disorder_flags in sentence_disorder_stats.items():
                    if key not in all_langs_sentence_disorder[lang]:
                        all_langs_sentence_disorder[lang][key] = []
                    all_langs_sentence_disorder[lang][key].extend(disorder_flags)
    
    # Compute averages
    for lang in all_langs_position2sizes:
        all_langs_average_sizes[lang] = {
            ty: all_langs_position2sizes[lang][ty] / all_langs_position2num[lang][ty] 
            for ty in all_langs_position2sizes[lang]
        }
    
    print('Done!')
    
    if compute_sentence_disorder:
        # Compute disorder percentages per language
        sentence_disorder_percentages = {}
        for lang in all_langs_sentence_disorder:
            sentence_disorder_percentages[lang] = {}
            for (side, tot), disorder_flags in all_langs_sentence_disorder[lang].items():
                total_sentences = len(disorder_flags)
                disordered_sentences = sum(disorder_flags)
                pct = (disordered_sentences / total_sentences * 100) if total_sentences > 0 else 0
                sentence_disorder_percentages[lang][(side, tot)] = {
                    'total': total_sentences,
                    'disordered': disordered_sentences,
                    'percentage': pct
                }
        
        return all_langs_position2num, all_langs_position2sizes, all_langs_average_sizes, sentence_disorder_percentages
    else:
        return all_langs_position2num, all_langs_position2sizes, all_langs_average_sizes


def get_bastard_stats(tree):
    """
    Count verbs and bastards in a tree.
    
    Parameters
    ----------
    tree : dict
        Dependency tree structure
        
    Returns
    -------
    tuple
        (verb_count, bastard_count, relation_counts, examples)
        examples: dict {rel: [tree_str, ...]}
    """
    verb_count = 0
    bastard_count = 0
    relation_counts = {}
    examples = {}
    
    # Only consider VERB governors (as per get_dep_sizes)
    head_pos = ["VERB"]
    
    for i in tree:
        if tree[i].get("tag") in head_pos:
            verb_count += 1
            bastards = tree[i].get("bastards", [])
            bastard_count += len(bastards)
            for b in bastards:
                # Get the relation of the bastard to its original governor
                # We need to find the governor of b in the original tree
                # tree[b]['gov'] is {govid: rel}
                for govid, rel in tree[b].get("gov", {}).items():
                    # Use the main relation part
                    rel_type = relation_split.split(rel)[0]
                    relation_counts[rel_type] = relation_counts.get(rel_type, 0) + 1
                    
                    # Collect example (one per relation per tree to avoid duplicates/bloat)
                    if rel_type not in examples:
                        examples[rel_type] = []
                    # We only need one example per tree for now to keep it light
                    if not examples[rel_type]: 
                         examples[rel_type].append(tree.conllu())

    return verb_count, bastard_count, relation_counts, examples


def get_bastard_stats_file(conll_filename):
    """
    Get bastard statistics for a CoNLL file.
    
    Parameters
    ----------
    conll_filename : str
        Path to CoNLL file
        
    Returns
    -------
    tuple
        (lang, verb_count, bastard_count, relation_counts, examples)
    """
    lang = os.path.basename(conll_filename).split('_')[0]
    total_verbs = 0
    total_bastards = 0
    total_relations = {}
    total_examples = {}
    
    for tree in conllFile2trees(conll_filename):
        tree.addspan(exclude=['punct'], compute_bastards=True)
        v, b, r, ex = get_bastard_stats(tree)
        total_verbs += v
        total_bastards += b
        for rel, count in r.items():
            total_relations[rel] = total_relations.get(rel, 0) + count
        
        # Collect examples, cap at 10 per relation per file
        for rel, treestrs in ex.items():
            if rel not in total_examples:
                total_examples[rel] = []
            if len(total_examples[rel]) < 10:
                total_examples[rel].extend(treestrs)
            
    return (lang, total_verbs, total_bastards, total_relations, total_examples)


def get_bastard_stats_all_files_parallel(allshortconll):
    """
    Process all short CoNLL files in parallel to compute bastard statistics.
    
    Parameters
    ----------
    allshortconll : list
        List of paths to short CoNLL files
        
    Returns
    -------
    tuple
        (lang_stats, all_relations)
        lang_stats: dict {lang: {'verbs': v, 'bastards': b, 'relations': r, 'examples': {rel: [trees]}}}
        all_relations: dict {rel: count} (global counts)
    """
    print(f"Starting bastard analysis, running on {psutil.cpu_count()} cores")
    
    lang_stats = {}
    all_relations = {}
    
    with multiprocessing.Pool(psutil.cpu_count()) as pool:
        results = list(tqdm(
            pool.imap(get_bastard_stats_file, allshortconll),
            total=len(allshortconll),
            desc="Analyzing bastards"
        ))
        
        print(f'Finished processing. Combining results...')
        
        for (lang, v, b, r, ex) in results:
            if lang not in lang_stats:
                lang_stats[lang] = {'verbs': 0, 'bastards': 0, 'relations': {}, 'examples': {}}
            
            lang_stats[lang]['verbs'] += v
            lang_stats[lang]['bastards'] += b
            
            for rel, count in r.items():
                lang_stats[lang]['relations'][rel] = lang_stats[lang]['relations'].get(rel, 0) + count
                all_relations[rel] = all_relations.get(rel, 0) + count
            
            # Aggregate examples, cap at 10 per relation per language
            for rel, treestrs in ex.items():
                if rel not in lang_stats[lang]['examples']:
                    lang_stats[lang]['examples'][rel] = []
                
                current_len = len(lang_stats[lang]['examples'][rel])
                if current_len < 10:
                    needed = 10 - current_len
                    lang_stats[lang]['examples'][rel].extend(treestrs[:needed])
                
    print('Done!')
    return lang_stats, all_relations


def save_conll_data(lang2shortconll, allshortconll, output_dir='data'):
    """
    Save CoNLL file lists to pickle files.
    
    Parameters
    ----------
    lang2shortconll : dict
        Dictionary mapping language codes to lists of short CoNLL files
    allshortconll : list
        List of all short CoNLL files
    output_dir : str
        Output directory
    """
    import pickle
    
    os.makedirs(output_dir, exist_ok=True)
    
    with open(f'{output_dir}/lang2shortconll.pkl', 'wb') as f:
        pickle.dump(lang2shortconll, f)
    
    with open(f'{output_dir}/allshortconll.pkl', 'wb') as f:
        pickle.dump(allshortconll, f)
    
    print(f"Saved CoNLL data to {output_dir}/")


def load_conll_data(output_dir='data'):
    """
    Load CoNLL file lists from pickle files.
    
    Parameters
    ----------
    output_dir : str
        Input directory
        
    Returns
    -------
    tuple
        (lang2shortconll, allshortconll)
    """
    import pickle
    
    with open(f'{output_dir}/lang2shortconll.pkl', 'rb') as f:
        lang2shortconll = pickle.load(f)
    
    with open(f'{output_dir}/allshortconll.pkl', 'rb') as f:
        allshortconll = pickle.load(f)
    
    print(f"Loaded CoNLL data from {output_dir}/")
    return lang2shortconll, allshortconll


def get_vo_hi_stats(tree):
    """
    Compute VO and Head-Initiality statistics for a single tree.
    
    Parameters
    ----------
    tree : dict
        Dependency tree
        
    Returns
    -------
    dict
        {
            'vo_right': count,
            'vo_total': count,
            'all_right': count,
            'all_total': count
        }
    """
    stats = {
        'vo_right': 0,
        'vo_total': 0,
        'all_right': 0,
        'all_total': 0
    }
    
    # Target dependencies for Head-Initiality (same as used in dependency analysis)
    TARGET_DEPS = {
        "nsubj", "obj", "iobj", "csubj", "ccomp", "xcomp", 
        "obl", "expl", "dislocated", "advcl", "advmod", 
        "nmod", "appos", "nummod", "acl", "amod"
    }
    
    for nid, node in tree.items():
        # Only consider VERB governors
        if node.get('tag') != 'VERB':
            continue
        
        # Check children
        kids = node.get('kids', {})
        for kid_id, deprel in kids.items():
            # Clean relation (remove subtype)
            base_rel = relation_split.split(deprel)[0]
            
            # General Head-Initiality Filter
            if base_rel in TARGET_DEPS:
                try:
                    is_right = float(kid_id) > float(nid)
                except ValueError:
                    continue 
                    
                stats['all_total'] += 1
                if is_right:
                    stats['all_right'] += 1
                
                # Specific VO Filter
                if base_rel == 'obj':
                    stats['vo_total'] += 1
                    if is_right:
                        stats['vo_right'] += 1
                        
    return stats


def process_file_complete(conll_filename, include_bastards=True, compute_sentence_disorder=False):
    """
    Process a single CoNLL file to compute ALL metrics in one pass.
    
    Computes:
    1. Dependency position sizes
    2. Bastard statistics
    3. VO / Head-Initiality statistics
    4. Sentence disorder statistics (optional)
    
    Returns
    -------
    tuple
        (lang, 
         position2num, position2sizes, sizes2freq, 
         verb_count, bastard_count, bastard_relations, bastard_examples,
         vo_hi_stats,
         sentence_disorder_stats)
    """
    lang = os.path.basename(conll_filename).split('_')[0]
    
    # 1. Dep sizes containers
    position2num, position2sizes, sizes2freq = {}, {}, {}
    
    # 2. Bastard stats containers
    total_verbs = 0
    total_bastards = 0
    total_bastard_relations = {}
    total_bastard_examples = {}
    
    # 3. VO/HI stats containers
    vo_hi_total = {
        'vo_right': 0, 'vo_total': 0,
        'all_right': 0, 'all_total': 0
    }
    
    # 4. Disorder / Ordering stats
    ordering_stats = {} if compute_sentence_disorder else None
    
    for tree in conllFile2trees(conll_filename):
        # Add spans (critical for dep sizes and bastards)
        tree.addspan(exclude=['punct'], compute_bastards=include_bastards)
        
        # 1. Dep Sizes
        get_dep_sizes(tree, position2num, position2sizes, sizes2freq, include_bastards=include_bastards)
        
        # 2. Bastard Stats
        v, b, r, ex = get_bastard_stats(tree)
        total_verbs += v
        total_bastards += b
        for rel, count in r.items():
            total_bastard_relations[rel] = total_bastard_relations.get(rel, 0) + count
        # Collect examples (cap at 5 per relation per file to save memory/space)
        for rel, treestrs in ex.items():
            if rel not in total_bastard_examples:
                total_bastard_examples[rel] = []
            if len(total_bastard_examples[rel]) < 5:
                # Only take new unique ones
                for ts in treestrs:
                    if ts not in total_bastard_examples[rel] and len(total_bastard_examples[rel]) < 5:
                        total_bastard_examples[rel].append(ts)
                        
        # 3. VO / HI Stats
        stats = get_vo_hi_stats(tree)
        for k, v in stats.items():
            vo_hi_total[k] += v
            
        # 4. Ordering Stats
        if compute_sentence_disorder:
            order_stats = get_ordering_stats(tree, include_bastards=include_bastards)
            for key, counts in order_stats.items():
                if key not in ordering_stats:
                    ordering_stats[key] = {'lt': 0, 'eq': 0, 'gt': 0}
                ordering_stats[key]['lt'] += counts['lt']
                ordering_stats[key]['eq'] += counts['eq']
                ordering_stats[key]['gt'] += counts['gt']
                
    return (lang, 
            position2num, position2sizes, sizes2freq, 
            total_verbs, total_bastards, total_bastard_relations, total_bastard_examples,
            vo_hi_total,
            ordering_stats)


def get_all_stats_parallel(allshortconll, include_bastards=True, compute_sentence_disorder=False):
    """
    Process all short CoNLL files in parallel to compute ALL metrics.
    
    Unified function replacing separate passes.
    """
    print(f"Starting unified processing on {psutil.cpu_count()} cores")
    
    # Aggregators
    all_langs_average_sizes = {}
    all_langs_position2num = {}
    all_langs_position2sizes = {}
    
    lang_bastard_stats = {}
    all_bastard_relations = {}
    
    lang_vo_hi_stats = {} # Will store accumulated raw counts first
    
    all_langs_ordering_stats = {} if compute_sentence_disorder else None
    
    with multiprocessing.Pool(psutil.cpu_count()) as pool:
        process_func = functools.partial(
            process_file_complete, 
            include_bastards=include_bastards,
            compute_sentence_disorder=compute_sentence_disorder
        )
        
        results = list(tqdm(
            pool.imap(process_func, allshortconll),
            total=len(allshortconll),
            desc="Processing files"
        ))
        
        print('Finished processing. Combining results...')
        
        for result in results:
            (lang, 
             position2num, position2sizes, sizes2freq, 
             verbs, bastards, bastard_relations, bastard_examples,
             vo_hi_file_stats,
             file_ordering_stats) = result
            
            # --- 1. Dep Sizes Aggregation ---
            all_langs_position2sizes[lang] = all_langs_position2sizes.get(lang, {})
            all_langs_position2num[lang] = all_langs_position2num.get(lang, {})
            
            for ty, size in position2sizes.items():
                all_langs_position2sizes[lang][ty] = all_langs_position2sizes[lang].get(ty, 0) + size
                all_langs_position2num[lang][ty] = all_langs_position2num[lang].get(ty, 0) + position2num[ty]
                
            # --- 2. Bastard Stats Aggregation ---
            if lang not in lang_bastard_stats:
                lang_bastard_stats[lang] = {'verbs': 0, 'bastards': 0, 'relations': {}, 'examples': {}}
            
            lang_bastard_stats[lang]['verbs'] += verbs
            lang_bastard_stats[lang]['bastards'] += bastards
            
            for rel, count in bastard_relations.items():
                lang_bastard_stats[lang]['relations'][rel] = lang_bastard_stats[lang]['relations'].get(rel, 0) + count
                all_bastard_relations[rel] = all_bastard_relations.get(rel, 0) + count
                
            for rel, treestrs in bastard_examples.items():
                if rel not in lang_bastard_stats[lang]['examples']:
                    lang_bastard_stats[lang]['examples'][rel] = []
                # Keep up to 10 global examples per language
                curr_len = len(lang_bastard_stats[lang]['examples'][rel])
                if curr_len < 10:
                    needed = 10 - curr_len
                    lang_bastard_stats[lang]['examples'][rel].extend(treestrs[:needed])
                    
            # --- 3. VO/HI Stats Aggregation ---
            if lang not in lang_vo_hi_stats:
                lang_vo_hi_stats[lang] = {'vo_right': 0, 'vo_total': 0, 'all_right': 0, 'all_total': 0}
            
            for k, v in vo_hi_file_stats.items():
                lang_vo_hi_stats[lang][k] += v
                
            # --- 4. Ordering Stats Aggregation ---
            if compute_sentence_disorder and file_ordering_stats:
                if lang not in all_langs_ordering_stats:
                    all_langs_ordering_stats[lang] = {}
                
                for key, counts in file_ordering_stats.items():
                    if key not in all_langs_ordering_stats[lang]:
                        all_langs_ordering_stats[lang][key] = {'lt': 0, 'eq': 0, 'gt': 0}
                    all_langs_ordering_stats[lang][key]['lt'] += counts['lt']
                    all_langs_ordering_stats[lang][key]['eq'] += counts['eq']
                    all_langs_ordering_stats[lang][key]['gt'] += counts['gt']

    # Post-processing
    
    # 1. Average sizes
    for lang in all_langs_position2sizes:
        all_langs_average_sizes[lang] = {
            ty: all_langs_position2sizes[lang][ty] / all_langs_position2num[lang][ty] 
            for ty in all_langs_position2sizes[lang]
        }

    # 3. VO/HI Scores Calculation
    lang_vo_hi_scores = {}
    for lang, stats in lang_vo_hi_stats.items():
        vo_total = stats['vo_total']
        all_total = stats['all_total']
        
        vo_score = stats['vo_right'] / vo_total if vo_total > 0 else None
        hi_score = stats['all_right'] / all_total if all_total > 0 else None
        
        # Classify word order type (tripartite classification)
        if vo_score is not None:
            if vo_score > 0.666:
                vo_type = 'VO'
            elif vo_score < 0.333:
                vo_type = 'OV'
            else:
                vo_type = 'NDO'
        else:
            vo_type = None
        
        lang_vo_hi_scores[lang] = {
            'vo_score': vo_score,
            'vo_type': vo_type,
            'head_initiality_score': hi_score,
            'vo_count': vo_total,
            'total_deps': all_total,
            'vo_right': stats['vo_right'],
            'all_right': stats['all_right']
        }
        
    print('Done!')
    
    return (all_langs_position2num, all_langs_position2sizes, all_langs_average_sizes, 
            lang_bastard_stats, all_bastard_relations, 
            lang_vo_hi_scores, 
            all_langs_ordering_stats)

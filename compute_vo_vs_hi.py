
import os
import pickle
import multiprocessing
import pandas as pd
from collections import defaultdict
from tqdm import tqdm
from conll import conllFile2trees

# Configuration
UD_DIR = "ud-treebanks-v2.17"
SHORT_DIR = "2.17_short"
OUTPUT_FILE = "data/vo_vs_hi_scores.csv"
EXCLUSION_FILE = "data/excluded_treebanks.txt"

# Dependencies to consider for general Head-Initiality (matching conll_processing.py)
TARGET_DEPS = {
    "nsubj", "obj", "iobj", "csubj", "ccomp", "xcomp", 
    "obl", "expl", "dislocated", "advcl", "advmod", 
    "nmod", "appos", "nummod", "acl", "amod"
}

def load_exclusions():
    exclusions = set()
    if os.path.exists(EXCLUSION_FILE):
        with open(EXCLUSION_FILE, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    exclusions.add(line)
    return exclusions

def process_file(filepath):
    """
    Process a single CoNLL file to count VO/OV and general Right/Left dependencies.
    Returns: (vo_right, vo_total, all_right, all_total, lang_code)
    """
    filename = os.path.basename(filepath)
    # simple language extraction from short filename logic (e.g. en_ewt_0.conllu -> en)
    # Assuming standard UD naming or matching regenerate_metadata.py logic
    # But files in SHORT_DIR might be like 'en_ewt-ud-train_0.conllu'
    # Actually regenerate_metadata logic: first_file.split('_', 1)[0].lower()
    # Let's extract lang key differently if needed, but for now passing it back is hard if we don't know it.
    # Better to pass lang code in or extract from filename.
    
    # Extract lang code
    if filename.startswith("fr_alts"):
        lang = "fr_alts"
    else:
        lang = filename.split('_')[0]
        
    stats = {
        'vo_right': 0,
        'vo_total': 0,
        'all_right': 0,
        'all_total': 0
    }
    
    try:
        trees = conllFile2trees(filepath)
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return lang, stats

    for tree in trees:
        tree.addkids()
        for nid, node in tree.items():
            # Only consider VERB governors
            if node.get('tag') != 'VERB':
                continue
            
            # Check children
            kids = node.get('kids', {})
            for kid_id, deprel in kids.items():
                # General Head-Initiality Filter
                if deprel in TARGET_DEPS:
                    try:
                        is_right = float(kid_id) > float(nid)
                    except ValueError:
                        continue # Skip if ID comparison fails (rare)
                        
                    stats['all_total'] += 1
                    if is_right:
                        stats['all_right'] += 1
                    
                    # Specific VO Filter
                    if deprel == 'obj':
                        stats['vo_total'] += 1
                        if is_right:
                            stats['vo_right'] += 1
                            
    return lang, stats

def main():
    # 1. Load Exclusions to filter source files (if we were processing raw files)
    # But here we assume SHORT_DIR was generated *after* filtering or we filter now.
    # regenerate_metadata.py deleted SHORT_DIR and recreated it respecting exclusions.
    # So SHORT_DIR should already be clean.
    # However, to be safe, we can double check against metadata if needed.
    # For now, trust SHORT_DIR contains valid split files.
    
    if not os.path.exists(SHORT_DIR):
        print(f"Directory {SHORT_DIR} not found.")
        return

    # Get list of files
    files = [os.path.join(SHORT_DIR, f) for f in os.listdir(SHORT_DIR) if f.endswith('.conllu')]
    
    print(f"Processing {len(files)} files with {multiprocessing.cpu_count()} cores...")
    
    with multiprocessing.Pool() as pool:
        results = list(tqdm(pool.imap_unordered(process_file, files), total=len(files)))
    
    # Aggregate by language
    lang_stats = defaultdict(lambda: {'vo_right': 0, 'vo_total': 0, 'all_right': 0, 'all_total': 0})
    
    for lang, stats in results:
        for k, v in stats.items():
            lang_stats[lang][k] += v
            
    # Compute scores
    output_data = []
    for lang, stats in lang_stats.items():
        vo_total = stats['vo_total']
        all_total = stats['all_total']
        
        # Avoid division by zero
        vo_score = stats['vo_right'] / vo_total if vo_total > 0 else None
        hi_score = stats['all_right'] / all_total if all_total > 0 else None
        
        output_data.append({
            'language': lang,
            'vo_score': vo_score,
            'head_initiality_score': hi_score,
            'vo_count': vo_total,
            'total_deps': all_total
        })
        
    df = pd.DataFrame(output_data)
    
    # Load metadata for full language names (optional but good for plotting)
    # But the plotting notebook likely handles mapping code -> name.
    # We just need code.
    
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"Saved scores for {len(df)} languages to {OUTPUT_FILE}")
    print(df.head())

if __name__ == "__main__":
    main()

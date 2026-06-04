import os
import pickle
import functools
import multiprocessing
import psutil
from tqdm import tqdm
from conll import conllFile2trees
import conll_processing

DATA_DIR = "data"

def process_vo_hi_file(conll_filename):
    lang = os.path.basename(conll_filename).split('_')[0]
    
    vo_hi_total = {
        'vo_right': 0, 'vo_total': 0,
        'sv_right': 0, 'sv_total': 0,
        'all_right': 0, 'all_total': 0
    }
    
    for tree in conllFile2trees(conll_filename):
        stats = conll_processing.get_vo_hi_stats(tree)
        for k, v in stats.items():
            vo_hi_total[k] += v
            
    return lang, vo_hi_total

def main():
    print("Loading file list...")
    with open(os.path.join(DATA_DIR, 'allshortconll.pkl'), 'rb') as f:
        allshortconll = pickle.load(f)
        
    print(f"Processing {len(allshortconll)} files on {psutil.cpu_count()} cores...")
    lang_vo_hi_stats = {}
    
    with multiprocessing.Pool(psutil.cpu_count()) as pool:
        results = list(tqdm(
            pool.imap(process_vo_hi_file, allshortconll),
            total=len(allshortconll),
            desc="Extracting VO/HI stats"
        ))
        
    print("Combining results...")
    for lang, vo_hi_file_stats in results:
        if lang not in lang_vo_hi_stats:
            lang_vo_hi_stats[lang] = {'vo_right': 0, 'vo_total': 0, 'sv_right': 0, 'sv_total': 0, 'all_right': 0, 'all_total': 0}
        
        for k, v in vo_hi_file_stats.items():
            lang_vo_hi_stats[lang][k] += v

    print("Calculating scores...")
    lang_vo_hi_scores = {}
    for lang, stats in lang_vo_hi_stats.items():
        vo_total = stats['vo_total']
        all_total = stats['all_total']
        
        vo_score = stats['vo_right'] / vo_total if vo_total > 0 else None
        hi_score = stats['all_right'] / all_total if all_total > 0 else None
        
        lang_vo_hi_scores[lang] = {
            'vo_score': vo_score,
            'hi_score': hi_score,
            'raw_stats': stats
        }
        
    out_path = os.path.join(DATA_DIR, 'lang_vo_hi_scores.pkl')
    with open(out_path, 'wb') as f:
        pickle.dump(lang_vo_hi_scores, f)
        
    print(f"Saved scores to {out_path}")

if __name__ == '__main__':
    main()

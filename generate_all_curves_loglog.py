import os
import pickle
import numpy as np
import matplotlib.pyplot as plt
import re
from collections import defaultdict
import data_utils

DATA_DIR = "data"
OUTPUT_DIR = "plots"

def load_data():
    with open(os.path.join(DATA_DIR, 'all_langs_position2sizes.pkl'), 'rb') as f:
        sizes = pickle.load(f)
    with open(os.path.join(DATA_DIR, 'all_langs_position2num.pkl'), 'rb') as f:
        nums = pickle.load(f)
        
    metadata = data_utils.load_metadata(os.path.join(DATA_DIR, 'metadata.pkl'))
    langNames = metadata['langNames']
    langnameGroup = metadata['langnameGroup']
    return sizes, nums, langNames, langnameGroup

def _compute_mal_scores(sizes, nums):
    lang2MAL = {}
    for lang in sizes:
        total_n_to_constituents = defaultdict(list)
        right_n_to_constituents = defaultdict(list)
        left_n_to_constituents = defaultdict(list)

        for key, size_sum in sizes[lang].items():
            count = nums[lang].get(key, 0)
            if count == 0: continue

            m = re.match(r'bilateral_L(\d+)_R(\d+)_pos_(\d+)_(left|right)$', key)
            if m:
                n_left, n_right = int(m.group(1)), int(m.group(2))
                total_n = n_left + n_right
                avg_size = size_sum / count
                total_n_to_constituents[total_n].append((avg_size, count))

            m2 = re.match(r'right_(\d+)_anyother_totright_(\d+)$', key)
            if m2:
                tot = int(m2.group(2))
                avg_size = size_sum / count
                right_n_to_constituents[tot].append((avg_size, count))

            m3 = re.match(r'left_(\d+)_anyother_totleft_(\d+)$', key)
            if m3:
                tot = int(m3.group(2))
                avg_size = size_sum / count
                left_n_to_constituents[tot].append((avg_size, count))

        def _weighted_avg(n_to_c):
            out = {}
            for n, cs in n_to_c.items():
                tw = sum(s * c for s, c in cs)
                tc = sum(c for _, c in cs)
                if tc > 0:
                    out[n] = tw / tc
            return out

        lang2MAL[lang] = {
            'total': _weighted_avg(total_n_to_constituents),
            'right': _weighted_avg(right_n_to_constituents),
            'left':  _weighted_avg(left_n_to_constituents),
        }
    return lang2MAL

def compute_regression(data_dict, start_n=1):
    points = []
    for n, val in data_dict.items():
        if n >= start_n and val > 0:
            points.append((np.log(n), np.log(val)))
    if len(points) < 2: return None
    x = np.array([p[0] for p in points])
    y = np.array([p[1] for p in points])
    slope, intercept = np.polyfit(x, y, 1)
    return {'slope': slope, 'intercept': intercept}

def setup_loglog_axes(ax, title, xlabel, ylabel):
    ax.set_xscale('log')
    ax.set_yscale('log')
    # Identical scale for all 3 diagrams
    ax.set_xlim(0.8, 12)
    ax.set_ylim(1.0, 4.0)
    
    ax.set_xticks([1, 2, 3, 4, 5, 6, 8, 10])
    ax.set_xticklabels(['1', '2', '3', '4', '5', '6', '8', '10'], fontsize=14)
    ax.set_yticks([1, 1.5, 2, 3, 4])
    ax.set_yticklabels(['1', '1.5', '2', '3', '4'], fontsize=14)
    
    ax.set_xlabel(xlabel, fontsize=16)
    ax.set_ylabel(ylabel, fontsize=16)
    ax.set_title(title, fontsize=16)
    ax.grid(True, which='both', linestyle=':', alpha=0.6)

def main():
    sizes, nums, langNames, langnameGroup = load_data()
    lang2MAL = _compute_mal_scores(sizes, nums)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # We need an appearance dict or group to color mapping
    group_to_color = {
        'Indo-European': '#1f77b4', 'Uralic': '#ff7f0e', 'Turkic': '#2ca02c',
        'Afro-Asiatic': '#d62728', 'Dravidian': '#9467bd', 'Sino-Tibetan': '#8c564b',
        'Austronesian': '#e377c2', 'Niger-Congo': '#7f7f7f', 'Tai-Kadai': '#bcbd22',
        'Other': '#17becf'
    }

    # Combine all 3 into a single 1x3 panel
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    
    # 1. Total
    ax = axes[0]
    lang2MAL_total = {lang: data['total'] for lang, data in lang2MAL.items() if data['total']}
    all_n_values = set()
    for data in lang2MAL_total.values():
        all_n_values.update(data.keys())
    max_n = min(max(all_n_values) if all_n_values else 4, 10)
    ns = list(range(1, max_n + 1))
    
    filtered_data = {lang: data for lang, data in lang2MAL_total.items() if 1 in data}
    if filtered_data:
        for lang, data in filtered_data.items():
            lang_name = langNames.get(lang, lang)
            group = langnameGroup.get(lang_name, 'Other')
            color = group_to_color.get(group, 'gray')
            lang_ns = sorted([n for n in ns if n in data])
            values = [data[n] for n in lang_ns]
            ax.plot(lang_ns, values, alpha=0.3, color=color)
            
        mean_vals = []
        mean_ns = []
        for n in ns:
            vals = [filtered_data[l][n] for l in filtered_data if n in filtered_data[l]]
            # Only plot the mean if we have a robust sample (at least 10 languages)
            # This prevents the mean curve from shooting up at high n due to data scarcity.
            if len(vals) >= 10:
                mean_vals.append(np.mean(vals))
                mean_ns.append(n)
        
        ax.plot(mean_ns, mean_vals, color='black', linewidth=2.5, label=f'Mean')
        setup_loglog_axes(ax, f"MAL_n (Total)", "Total dependents ($n$)", "Average constituent size")
        ax.legend(loc='upper right', fontsize=12)

    # 2. Left and Right
    titles = {
        'left': 'LMAL_n (Left dependents)',
        'right': 'RMAL_n (Right dependents)'
    }
    for ax, side in zip([axes[1], axes[2]], ['left', 'right']):
        lang2MAL_side = {lang: data[side] for lang, data in lang2MAL.items() if data[side]}
        filtered_data_side = {lang: data for lang, data in lang2MAL_side.items() if 1 in data}
        
        if filtered_data_side:
            for lang, data in filtered_data_side.items():
                lang_name = langNames.get(lang, lang)
                group = langnameGroup.get(lang_name, 'Other')
                color = group_to_color.get(group, 'gray')
                lang_ns = sorted([n for n in ns if n in data])
                values = [data[n] for n in lang_ns]
                ax.plot(lang_ns, values, alpha=0.3, color=color)
            
            mean_vals = []
            mean_ns = []
            for n in ns:
                vals = [filtered_data_side[l][n] for l in filtered_data_side if n in filtered_data_side[l]]
                if vals:
                    mean_vals.append(np.mean(vals))
                    mean_ns.append(n)
            
            ax.plot(mean_ns, mean_vals, color='black', linewidth=2.5, label=f'Mean')
            setup_loglog_axes(ax, titles[side], f"Number of {side} dependents ($n$)", "Average constituent size" if side == 'left' else "")
            ax.legend(loc='upper right', fontsize=12)

    plt.tight_layout()
    out_path = os.path.join(OUTPUT_DIR, 'mal_combined_curves_1x3.pdf')
    plt.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved {out_path}")

if __name__ == "__main__":
    main()

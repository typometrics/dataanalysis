import os
import pickle
import numpy as np
import matplotlib.pyplot as plt
import re
from collections import defaultdict

DATA_DIR = "data"
OUTPUT_DIR = "plots"

def load_data():
    with open(os.path.join(DATA_DIR, 'all_langs_position2sizes.pkl'), 'rb') as f:
        sizes = pickle.load(f)
    with open(os.path.join(DATA_DIR, 'all_langs_position2num.pkl'), 'rb') as f:
        nums = pickle.load(f)
    return sizes, nums

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
                    out[n] = (tw / tc, tc)
            return out

        lang2MAL[lang] = {
            'total': _weighted_avg(total_n_to_constituents),
            'right': _weighted_avg(right_n_to_constituents),
            'left':  _weighted_avg(left_n_to_constituents),
        }
    return lang2MAL

def compute_regression(data_dict, start_n=1):
    points = []
    weights = []
    for n, (val, count) in data_dict.items():
        if n >= start_n and val > 0:
            points.append((np.log(n), np.log(val)))
            weights.append(count)
    if len(points) < 2: return None
    
    x = np.array([p[0] for p in points])
    y = np.array([p[1] for p in points])
    w = np.array(weights)
    
    # Weighted polyfit: w is the inverse standard error.
    # In np.polyfit, we minimize sum((w * (y - y_pred))**2).
    # Since we want to weight by count, we pass np.sqrt(w).
    slope, intercept = np.polyfit(x, y, 1, w=np.sqrt(w))
    
    # R^2 weighted
    y_pred = slope * x + intercept
    y_mean = np.average(y, weights=w)
    ss_tot = np.sum(w * (y - y_mean)**2)
    ss_res = np.sum(w * (y - y_pred)**2)
    r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
    
    return {'slope': slope, 'intercept': intercept, 'r2': r2, 'points': points}

def plot_lang(lang_code, lang_name, mal_data, ax):
    # Data
    d_tot = mal_data['total']
    d_left = mal_data['left']
    d_right = mal_data['right']
    
    # We want consistent axes: let's plot x and y as actual values, but set axis to log
    for d, label, color, marker in [(d_tot, 'MAL (Total)', 'black', 'o'),
                                    (d_left, 'LMAL (Left)', 'blue', 's'),
                                    (d_right, 'RMAL (Right)', 'red', '^')]:
        if not d: continue
        
        # Sort keys
        ns = sorted(d.keys())
        # Filter to n<=10 and count >= 100 to hide noisy outliers
        ns = [n for n in ns if n <= 10 and d[n][1] >= 100]
        if not ns: continue
        vals = [d[n][0] for n in ns]
        
        ax.scatter(ns, vals, label=label, color=color, marker=marker, s=80, alpha=0.7)
        
        # Add regression line (start from n=1)
        reg = compute_regression(d, start_n=1)
        if reg:
            # We want to plot the regression line in log-log space, which is a power law curve in linear space
            # or just a straight line on log-log axis.
            # y = exp(intercept) * x^slope
            x_vals = np.linspace(1, max(ns), 100)
            y_vals = np.exp(reg['intercept']) * (x_vals ** reg['slope'])
            ax.plot(x_vals, y_vals, color=color, linestyle='--', linewidth=2, alpha=0.5)

    ax.set_xscale('log')
    ax.set_yscale('log')
    # Set identical limits to fit Arabic (which goes up to ~11)
    ax.set_xlim(0.8, 12)
    ax.set_ylim(1.5, 15.0)
    
    ax.set_xticks([1, 2, 3, 4, 5, 6, 8, 10])
    ax.set_xticklabels(['1', '2', '3', '4', '5', '6', '8', '10'], fontsize=14)
    # y-ticks
    ax.set_yticks([2, 3, 4, 6, 8, 12])
    ax.set_yticklabels(['2', '3', '4', '6', '8', '12'], fontsize=14)
    
    ax.set_xlabel('Number of dependents ($n$)', fontsize=16)
    ax.set_ylabel('Average constituent size', fontsize=16)
    ax.legend(fontsize=14)
    ax.grid(True, which='both', linestyle=':', alpha=0.6)

def main():
    sizes, nums = load_data()
    lang2MAL = _compute_mal_scores(sizes, nums)
    
    langs = [('de', 'German'), ('pcm', 'Naija'), ('ar', 'Arabic')]
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    for lc, ln in langs:
        fig, ax = plt.subplots(figsize=(8, 4.5))
        plot_lang(lc, ln, lang2MAL[lc], ax)
        # remove title from the plot as it is in the poster text usually
        # ax.set_title(ln)
        fig.tight_layout()
        out_path = os.path.join(OUTPUT_DIR, f"{ln}_loglog.pdf")
        fig.savefig(out_path, format='pdf', bbox_inches='tight')
        plt.close(fig)
        print(f"Saved {out_path}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Check XXV configuration files to compare sample GM vs global Helix GM.
"""

import re
from pathlib import Path
from collections import defaultdict

def extract_stats_from_html(html_path):
    """
    Extract the geometric mean statistics from an XXV HTML file.
    Returns dict with keys: 'x2_sample', 'x2_global', 'x1_sample', 'x1_global'
    """
    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Look for the pattern:
    # X<sub>2</sub>: <b>1.39</b> <span style='color: #666; font-weight: normal;'>(2.08)</span>, 
    # X<sub>1</sub>: <b>1.15</b> <span style='color: #666; font-weight: normal;'>(1.34)</span>
    
    pattern = r'X<sub>2</sub>:\s*<b>([\d.]+)</b>.*?\(([\d.]+)\).*?X<sub>1</sub>:\s*<b>([\d.]+)</b>.*?\(([\d.]+)\)'
    
    match = re.search(pattern, content, re.DOTALL)
    
    if not match:
        return None
    
    return {
        'x2_sample': float(match.group(1)),
        'x2_global': float(match.group(2)),
        'x1_sample': float(match.group(3)),
        'x1_global': float(match.group(4)),
    }

def main():
    html_dir = Path('/bigstorage/kim/typometrics/dataanalysis/html_examples')
    
    # Find all XXV.html files
    xxv_files = sorted(html_dir.glob('*/XXV.html'))
    
    print(f"Found {len(xxv_files)} XXV.html files")
    print("\n" + "="*80)
    
    results = []
    
    for html_file in xxv_files:
        lang_name = html_file.parent.name
        stats = extract_stats_from_html(html_file)
        
        if stats:
            results.append({
                'language': lang_name,
                **stats
            })
    
    # Analysis
    print(f"\nAnalyzed {len(results)} files with statistics\n")
    
    # Count comparisons
    x2_sample_larger = 0
    x2_global_larger = 0
    x2_equal = 0
    
    x1_sample_larger = 0
    x1_global_larger = 0
    x1_equal = 0
    
    print("POSITION X2 (Outer, farther from verb):")
    print("-" * 80)
    for r in results:
        if r['x2_sample'] > r['x2_global']:
            x2_sample_larger += 1
        elif r['x2_sample'] < r['x2_global']:
            x2_global_larger += 1
        else:
            x2_equal += 1
    
    print(f"  Sample > Global: {x2_sample_larger} ({100*x2_sample_larger/len(results):.1f}%)")
    print(f"  Sample < Global: {x2_global_larger} ({100*x2_global_larger/len(results):.1f}%)")
    print(f"  Sample = Global: {x2_equal}")
    
    print("\nPOSITION X1 (Inner, closer to verb):")
    print("-" * 80)
    for r in results:
        if r['x1_sample'] > r['x1_global']:
            x1_sample_larger += 1
        elif r['x1_sample'] < r['x1_global']:
            x1_global_larger += 1
        else:
            x1_equal += 1
    
    print(f"  Sample > Global: {x1_sample_larger} ({100*x1_sample_larger/len(results):.1f}%)")
    print(f"  Sample < Global: {x1_global_larger} ({100*x1_global_larger/len(results):.1f}%)")
    print(f"  Sample = Global: {x1_equal}")
    
    # Show some examples where global > sample significantly
    print("\n" + "="*80)
    print("EXAMPLES WHERE GLOBAL > SAMPLE (by > 0.3):")
    print("-" * 80)
    
    for r in sorted(results, key=lambda x: x['x2_global'] - x['x2_sample'], reverse=True)[:10]:
        diff = r['x2_global'] - r['x2_sample']
        if diff > 0.3:
            print(f"{r['language']:25} X2: sample={r['x2_sample']:.2f}, global={r['x2_global']:.2f} (diff: +{diff:.2f})")
    
    print("\nFor X1:")
    for r in sorted(results, key=lambda x: x['x1_global'] - x['x1_sample'], reverse=True)[:10]:
        diff = r['x1_global'] - r['x1_sample']
        if diff > 0.3:
            print(f"{r['language']:25} X1: sample={r['x1_sample']:.2f}, global={r['x1_global']:.2f} (diff: +{diff:.2f})")
    
    # Show examples where sample > global significantly
    print("\n" + "="*80)
    print("EXAMPLES WHERE SAMPLE > GLOBAL (by > 0.3):")
    print("-" * 80)
    
    for r in sorted(results, key=lambda x: x['x2_sample'] - x['x2_global'], reverse=True)[:10]:
        diff = r['x2_sample'] - r['x2_global']
        if diff > 0.3:
            print(f"{r['language']:25} X2: sample={r['x2_sample']:.2f}, global={r['x2_global']:.2f} (diff: +{diff:.2f})")
    
    print("\nFor X1:")
    for r in sorted(results, key=lambda x: x['x1_sample'] - x['x1_sample'], reverse=True)[:10]:
        diff = r['x1_sample'] - r['x1_global']
        if diff > 0.3:
            print(f"{r['language']:25} X1: sample={r['x1_sample']:.2f}, global={r['x1_global']:.2f} (diff: +{diff:.2f})")
    
    # Show the French example specifically
    print("\n" + "="*80)
    print("FRENCH EXAMPLE (mentioned by user):")
    print("-" * 80)
    french = [r for r in results if 'French' in r['language'] or r['language'] == 'fr']
    for r in french:
        print(f"{r['language']:25}")
        print(f"  X2: Sample={r['x2_sample']:.2f}, Global={r['x2_global']:.2f} (Global-Sample: {r['x2_global']-r['x2_sample']:+.2f})")
        print(f"  X1: Sample={r['x1_sample']:.2f}, Global={r['x1_global']:.2f} (Global-Sample: {r['x1_global']-r['x1_sample']:+.2f})")

if __name__ == '__main__':
    main()

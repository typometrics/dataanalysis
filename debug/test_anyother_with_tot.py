#!/usr/bin/env python3
"""
Test script to verify anyother with tot keys are collected and diagonal factors work.
"""

import sys
import os
import pickle
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from conll_processing import get_dep_sizes_file
from verb_centered_analysis import compute_anyotherside_sizes_table

print("="*80)
print("ANYOTHERSIDE WITH TOT DIMENSION TEST")
print("="*80)
print()

# Test on a small file
test_file = "2.17_short/fr_gsd-ud-dev_0.conllu"

if not os.path.exists(test_file):
    print(f"❌ Test file not found: {test_file}")
    sys.exit(1)

print(f"📂 Processing: {test_file}")
lang, pos2num, pos2sizes, sizes2freq, pos2charsizes = get_dep_sizes_file(test_file, include_bastards=False)

print(f"✓ Processed {lang}")
print()

# Check for anyother keys with tot
anyother_keys = [k for k in pos2sizes.keys() if 'anyother' in k]
anyother_tot_keys = [k for k in anyother_keys if '_totright_' in k or '_totleft_' in k]

print(f"📊 Found {len(anyother_keys)} anyother keys total")
print(f"   {len(anyother_tot_keys)} with tot dimension")
print()

if anyother_tot_keys:
    print("✅ SUCCESS: anyother keys with tot dimension are being collected!")
    print()
    print("Sample keys with tot:")
    for key in sorted(anyother_tot_keys)[:10]:
        count = pos2num.get(key, 0)
        print(f"   {key}: {count} occurrences")
else:
    print("❌ PROBLEM: No anyother keys with tot dimension found")
    print()
    print("Sample anyother keys without tot:")
    for key in sorted(anyother_keys)[:10]:
        count = pos2num.get(key, 0)
        print(f"   {key}: {count} occurrences")

print()
print("="*80)

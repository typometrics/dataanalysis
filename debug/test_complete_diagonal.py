#!/usr/bin/env python3
"""
Complete test: process a small dataset and generate anyotherside tables with diagonal factors.
"""

import sys
import os
import pickle
import numpy as np
from pathlib import Path
from tqdm import tqdm

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from conll_processing import get_dep_sizes_file
from verb_centered_analysis import compute_anyotherside_sizes_table, generate_anyotherside_helix_tables

print("="*80)
print("COMPLETE ANYOTHERSIDE WITH DIAGONAL FACTORS TEST")
print("="*80)
print()

# Test on French dev file
test_file = "2.17_short/fr_gsd-ud-dev_0.conllu"

if not os.path.exists(test_file):
    print(f"❌ Test file not found: {test_file}")
    sys.exit(1)

print(f"📂 Processing: {test_file}")
lang, pos2num, pos2sizes, sizes2freq, pos2charsizes = get_dep_sizes_file(test_file, include_bastards=False)

# Compute averages (geometric means)
pos_avgs = {}
for key in pos2sizes:
    if pos2num.get(key, 0) > 0:
        pos_avgs[key] = np.exp(pos2sizes[key] / pos2num[key])

print(f"✓ Processed {lang} - {len(pos_avgs)} position averages")
print()

# Check for anyother_tot keys
anyother_tot_keys = [k for k in pos_avgs.keys() if 'anyother' in k and ('_totright_' in k or '_totleft_' in k)]
print(f"📊 Found {len(anyother_tot_keys)} anyother keys with tot dimension")
print()

if anyother_tot_keys:
    print("Sample keys:")
    for key in sorted(anyother_tot_keys)[:5]:
        print(f"   {key}: {pos_avgs[key]:.2f}")
    print()

# Create language data structure
all_langs_data = {lang: pos_avgs}

# Compute anyotherside table
print("📊 Computing AnyOtherSide statistics...")
anyother_stats = compute_anyotherside_sizes_table(all_langs_data)

# Check for diagonal factors
diag_factor_keys = [k for k in anyother_stats.keys() if k.startswith('factor_') and '_totright_' in k or '_totleft_' in k]
print(f"   Found {len(diag_factor_keys)} diagonal factor keys")

if diag_factor_keys:
    print()
    print("✅ Diagonal factors computed successfully!")
    print()
    print("Sample diagonal factors:")
    for key in sorted(diag_factor_keys)[:5]:
        val = anyother_stats[key]
        print(f"   {key}: {val:.3f}")
else:
    print()
    print("❌ No diagonal factors found!")

print()

# Generate table
print("📝 Generating AnyOtherSide Helix table...")
output_dir = "test_diagonal_output"
os.makedirs(output_dir, exist_ok=True)

langnames = {lang: 'French'}

generate_anyotherside_helix_tables(
    all_langs_data,
    langnames,
    output_dir,
    arrow_direction='right_to_left'
)

# Read and display TSV
tsv_file = f"{output_dir}/Helix_French_fr_AnyOtherSide.tsv"
if os.path.exists(tsv_file):
    print()
    print(f"✅ TSV file created: {tsv_file}")
    print()
    print("📄 TSV Content:")
    print("-"*80)
    with open(tsv_file) as f:
        print(f.read())
    print("-"*80)
else:
    print(f"❌ TSV file not found: {tsv_file}")

# Cleanup
import shutil
shutil.rmtree(output_dir)
print()
print("🎉 Test complete!")
print("🧹 Cleaned up test_diagonal_output")
print()
print("="*80)

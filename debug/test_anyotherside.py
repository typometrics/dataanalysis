#!/usr/bin/env python3
"""
Test script for any-other-side implementation.
Tests data collection and table generation with a small dataset.
"""

import os
import sys
import pickle
import numpy as np
from collections import defaultdict

# Add current dir to path
sys.path.insert(0, os.path.dirname(__file__))

import conll_processing
import verb_centered_analysis
from conll import conllFile2trees

def test_anyotherside_stats():
    """Test that any-other-side statistics are being collected properly."""
    print("="*80)
    print("TEST 1: Any-Other-Side Statistics Collection")
    print("="*80)
    
    # Find a small test file
    test_file = "2.17_short/en_ewt-ud-test_0.conllu"
    if not os.path.exists(test_file):
        print(f"ERROR: Test file {test_file} not found")
        return False
    
    print(f"\nProcessing: {test_file}")
    
    # Process file
    position2num = {}
    position2sizes = {}
    sizes2freq = {}
    position2charsizes = {}
    
    tree_count = 0
    for tree in conllFile2trees(test_file):
        tree.addspan(exclude=['punct'], compute_bastards=True)
        conll_processing.get_dep_sizes(
            tree, 
            position2num, 
            position2sizes, 
            sizes2freq,
            include_bastards=True,
            position2charsizes=position2charsizes
        )
        tree_count += 1
        if tree_count >= 50:  # Process first 50 trees
            break
    
    print(f"\nProcessed {tree_count} trees")
    
    # Check for anyother keys
    anyother_keys = [k for k in position2num.keys() if '_anyother' in k]
    exact_keys = [k for k in position2num.keys() if '_totright_' in k or '_totleft_' in k]
    
    print(f"\n📊 Statistics collected:")
    print(f"   - Total position keys: {len(position2num)}")
    print(f"   - Exact config keys (totright/totleft): {len(exact_keys)}")
    print(f"   - Any-other-side keys (_anyother): {len(anyother_keys)}")
    
    if not anyother_keys:
        print("\n❌ FAILED: No any-other-side keys found!")
        return False
    
    print(f"\n✅ Any-other-side keys found:")
    for key in sorted(anyother_keys):
        count = position2num.get(key, 0)
        if count > 0:
            log_sum = position2sizes.get(key, 0)
            gm = np.exp(log_sum / count) if count > 0 else 0
            print(f"   {key:30s} N={count:4d}  GM={gm:.2f}")
    
    # Verify relationship: anyother should have >= count than exact
    print(f"\n📐 Verification: anyother >= exact counts")
    test_cases = [
        ('right_1_anyother', 'right_1_totright_1'),
        ('right_2_anyother', 'right_2_totright_2'),
        ('left_1_anyother', 'left_1_totleft_1'),
        ('left_2_anyother', 'left_2_totleft_2'),
    ]
    
    for any_key, exact_key in test_cases:
        any_count = position2num.get(any_key, 0)
        exact_count = position2num.get(exact_key, 0)
        status = "✅" if any_count >= exact_count else "❌"
        print(f"   {status} {any_key:25s} ({any_count:4d}) >= {exact_key:25s} ({exact_count:4d})")
    
    return len(anyother_keys) > 0


def test_config_examples():
    """Test that partial config examples are being generated."""
    print("\n" + "="*80)
    print("TEST 2: Partial Configuration Examples")
    print("="*80)
    
    test_file = "2.17_short/en_ewt-ud-test_0.conllu"
    if not os.path.exists(test_file):
        print(f"ERROR: Test file {test_file} not found")
        return False
    
    print(f"\nProcessing: {test_file}")
    
    # Collect examples
    all_examples = []
    tree_count = 0
    for tree in conllFile2trees(test_file):
        tree.addspan(exclude=['punct'], compute_bastards=True)
        examples = conll_processing.extract_verb_config_examples(tree, include_bastards=True)
        all_examples.extend(examples)
        tree_count += 1
        if tree_count >= 50:
            break
    
    print(f"\nProcessed {tree_count} trees")
    print(f"Collected {len(all_examples)} config examples")
    
    # Categorize examples
    exact_examples = [ex for ex in all_examples if '_any' not in ex[0]]
    partial_examples = [ex for ex in all_examples if '_any' in ex[0]]
    
    print(f"\n📊 Example breakdown:")
    print(f"   - Exact configs: {len(exact_examples)}")
    print(f"   - Partial configs: {len(partial_examples)}")
    
    if not partial_examples:
        print("\n❌ FAILED: No partial config examples found!")
        return False
    
    # Count by config type
    config_counts = defaultdict(int)
    for config, _, _ in all_examples:
        config_counts[config] += 1
    
    print(f"\n✅ Configuration counts (top 20):")
    for config, count in sorted(config_counts.items(), key=lambda x: x[1], reverse=True)[:20]:
        marker = "🔸" if '_any' in config else "  "
        print(f"   {marker} {config:30s} {count:4d}")
    
    return len(partial_examples) > 0


def test_table_generation():
    """Test any-other-side table generation."""
    print("\n" + "="*80)
    print("TEST 3: Any-Other-Side Table Generation")
    print("="*80)
    
    # Create fake data for testing
    print("\nCreating test data...")
    
    test_lang = "test_en"
    test_data = {
        test_lang: {
            # Right side (any left)
            'right_1_anyother': 2.5,
            'right_2_anyother': 3.2,
            'right_3_anyother': 4.1,
            'right_4_anyother': 5.0,
            # Left side (any right)
            'left_1_anyother': 2.0,
            'left_2_anyother': 2.8,
            'left_3_anyother': 3.5,
            'left_4_anyother': 4.2,
            # Bilateral (XVX any-other)
            'xvx_left_1_anyother': 1.8,
            'xvx_right_1_anyother': 2.2,
        }
    }
    
    langnames = {test_lang: "TestEnglish"}
    
    # Generate table
    output_dir = "test_output"
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Generating any-other-side table to {output_dir}/...")
    verb_centered_analysis.generate_anyotherside_helix_tables(
        test_data,
        langnames,
        output_dir=output_dir
    )
    
    # Check output files
    tsv_file = f"{output_dir}/Helix_AnyOtherSide_TestEnglish_{test_lang}.tsv"
    txt_file = f"{output_dir}/Helix_AnyOtherSide_TestEnglish_{test_lang}.txt"
    
    if not os.path.exists(tsv_file):
        print(f"\n❌ FAILED: Output file not created: {tsv_file}")
        return False
    
    print(f"\n✅ Output files created:")
    print(f"   - {tsv_file}")
    print(f"   - {txt_file}")
    
    # Display content
    print(f"\n📄 Table content:")
    with open(tsv_file, 'r') as f:
        content = f.read()
        print(content)
    
    # Verify content has expected sections
    required_sections = [
        "RIGHT-SIDE PATTERNS",
        "BILATERAL PATTERN",
        "LEFT-SIDE PATTERNS"
    ]
    
    for section in required_sections:
        if section not in content:
            print(f"\n❌ FAILED: Missing section: {section}")
            return False
    
    print(f"\n✅ All required sections present")
    
    return True


def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("ANY-OTHER-SIDE IMPLEMENTATION TEST SUITE")
    print("="*80)
    
    results = []
    
    # Test 1: Statistics collection
    try:
        results.append(("Statistics Collection", test_anyotherside_stats()))
    except Exception as e:
        print(f"\n❌ TEST 1 CRASHED: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Statistics Collection", False))
    
    # Test 2: Config examples
    try:
        results.append(("Config Examples", test_config_examples()))
    except Exception as e:
        print(f"\n❌ TEST 2 CRASHED: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Config Examples", False))
    
    # Test 3: Table generation
    try:
        results.append(("Table Generation", test_table_generation()))
    except Exception as e:
        print(f"\n❌ TEST 3 CRASHED: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Table Generation", False))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status:15s} {test_name}")
    
    all_passed = all(result[1] for result in results)
    
    print("\n" + "="*80)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
    else:
        print("⚠️  SOME TESTS FAILED")
    print("="*80)
    
    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())

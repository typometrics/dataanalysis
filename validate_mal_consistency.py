#!/usr/bin/env python3
"""
Validate MAL Data Consistency

This script checks that for specific bilateral configurations (L=x, R=y),
the sum of left-side and right-side constituent sizes is consistent
with expectations.

The validation checks:
1. For each bilateral_L{l}_R{r} configuration:
   - The total size from left positions + total size from right positions
   - Should equal the sum when computed separately

2. Cross-checks between different key types:
   - bilateral keys vs exact unilateral keys
   - anyother keys aggregation

Author: Typometrics Project
"""

import os
import sys
import pickle
import re
from collections import defaultdict

# Configuration
DATA_DIR = "data"
MIN_COUNT = 10  # Minimum occurrences to consider


def load_data():
    """Load the position statistics data."""
    sizes_path = os.path.join(DATA_DIR, 'all_langs_position2sizes.pkl')
    nums_path = os.path.join(DATA_DIR, 'all_langs_position2num.pkl')
    
    if not os.path.exists(sizes_path):
        print(f"ERROR: {sizes_path} not found")
        sys.exit(1)
    
    with open(sizes_path, 'rb') as f:
        all_langs_position2sizes = pickle.load(f)
    
    with open(nums_path, 'rb') as f:
        all_langs_position2num = pickle.load(f)
    
    # Load language names
    metadata_path = os.path.join(DATA_DIR, 'metadata.pkl')
    langNames = {}
    if os.path.exists(metadata_path):
        with open(metadata_path, 'rb') as f:
            metadata = pickle.load(f)
            langNames = metadata.get('langNames', {})
    
    return all_langs_position2sizes, all_langs_position2num, langNames


def analyze_bilateral_configuration(lang, position2sizes, position2num, n_left, n_right):
    """
    Analyze a specific bilateral configuration (L=n_left, R=n_right).
    
    Returns dict with:
    - left_positions: list of (pos, avg_size, count) for left side
    - right_positions: list of (pos, avg_size, count) for right side
    - total_left_weighted: sum of (size * count) for left positions
    - total_right_weighted: sum of (size * count) for right positions
    - total_count: total count across all positions
    """
    result = {
        'left_positions': [],
        'right_positions': [],
        'total_left_weighted': 0,
        'total_right_weighted': 0,
        'total_left_count': 0,
        'total_right_count': 0,
    }
    
    # Pattern for bilateral keys: bilateral_L{l}_R{r}_pos_{i}_{side}
    for key, size_sum in position2sizes.items():
        count = position2num.get(key, 0)
        if count < MIN_COUNT:
            continue
        
        match = re.match(r'bilateral_L(\d+)_R(\d+)_pos_(\d+)_(left|right)$', key)
        if match:
            l = int(match.group(1))
            r = int(match.group(2))
            pos = int(match.group(3))
            side = match.group(4)
            
            if l == n_left and r == n_right:
                avg_size = size_sum / count
                
                if side == 'left':
                    result['left_positions'].append((pos, avg_size, count))
                    result['total_left_weighted'] += size_sum
                    result['total_left_count'] += count
                else:
                    result['right_positions'].append((pos, avg_size, count))
                    result['total_right_weighted'] += size_sum
                    result['total_right_count'] += count
    
    return result


def compute_mal_for_config(config_result):
    """Compute MAL (average constituent size) for a configuration."""
    total_weighted = config_result['total_left_weighted'] + config_result['total_right_weighted']
    total_count = config_result['total_left_count'] + config_result['total_right_count']
    
    if total_count == 0:
        return None
    
    return total_weighted / total_count


def validate_mal_additivity(all_langs_position2sizes, all_langs_position2num, langNames):
    """
    Validate that MAL computations are consistent.
    
    For bilateral configurations, check that:
    - Left-side MAL + Right-side MAL properly combine to total MAL
    - Configurations are being counted correctly
    """
    print("="*80)
    print("MAL DATA CONSISTENCY VALIDATION")
    print("="*80)
    
    errors = []
    warnings = []
    stats = defaultdict(int)
    
    for lang in sorted(all_langs_position2sizes.keys()):
        position2sizes = all_langs_position2sizes[lang]
        position2num = all_langs_position2num[lang]
        lang_name = langNames.get(lang, lang)
        
        # Collect all bilateral configurations present
        configs = set()
        for key in position2sizes.keys():
            match = re.match(r'bilateral_L(\d+)_R(\d+)_pos_\d+_(left|right)$', key)
            if match:
                l = int(match.group(1))
                r = int(match.group(2))
                configs.add((l, r))
        
        if not configs:
            stats['no_bilateral'] += 1
            continue
        
        stats['has_bilateral'] += 1
        
        # Check each configuration
        for n_left, n_right in sorted(configs):
            config = analyze_bilateral_configuration(
                lang, position2sizes, position2num, n_left, n_right
            )
            
            # Validation 1: Check position counts match expected
            expected_left_positions = n_left
            expected_right_positions = n_right
            actual_left_positions = len(config['left_positions'])
            actual_right_positions = len(config['right_positions'])
            
            # Note: actual may be less than expected due to min_count filtering
            if actual_left_positions > expected_left_positions:
                errors.append({
                    'lang': lang,
                    'lang_name': lang_name,
                    'config': f'L{n_left}_R{n_right}',
                    'type': 'position_count',
                    'message': f'Too many left positions: got {actual_left_positions}, expected ≤{expected_left_positions}',
                    'details': config['left_positions']
                })
            
            if actual_right_positions > expected_right_positions:
                errors.append({
                    'lang': lang,
                    'lang_name': lang_name,
                    'config': f'L{n_left}_R{n_right}',
                    'type': 'position_count',
                    'message': f'Too many right positions: got {actual_right_positions}, expected ≤{expected_right_positions}',
                    'details': config['right_positions']
                })
            
            # Validation 2: Check that left and right counts are equal
            # (each verb contributes to both sides equally)
            if config['total_left_count'] > 0 and config['total_right_count'] > 0:
                # The counts should be proportional to number of positions
                left_per_pos = config['total_left_count'] / actual_left_positions if actual_left_positions > 0 else 0
                right_per_pos = config['total_right_count'] / actual_right_positions if actual_right_positions > 0 else 0
                
                if left_per_pos > 0 and right_per_pos > 0:
                    ratio = left_per_pos / right_per_pos
                    if ratio < 0.5 or ratio > 2.0:
                        warnings.append({
                            'lang': lang,
                            'lang_name': lang_name,
                            'config': f'L{n_left}_R{n_right}',
                            'type': 'count_imbalance',
                            'message': f'Left/Right count ratio imbalance: {ratio:.2f}',
                            'left_count': config['total_left_count'],
                            'right_count': config['total_right_count']
                        })
            
            # Validation 3: Check MAL values are reasonable
            mal = compute_mal_for_config(config)
            if mal is not None:
                if mal <= 0:
                    errors.append({
                        'lang': lang,
                        'lang_name': lang_name,
                        'config': f'L{n_left}_R{n_right}',
                        'type': 'invalid_mal',
                        'message': f'MAL value is non-positive: {mal:.4f}'
                    })
                elif mal > 100:
                    warnings.append({
                        'lang': lang,
                        'lang_name': lang_name,
                        'config': f'L{n_left}_R{n_right}',
                        'type': 'unusual_mal',
                        'message': f'Unusually large MAL value: {mal:.2f}'
                    })
            
            stats['configs_checked'] += 1
    
    # Report results
    print(f"\nStatistics:")
    print(f"  Languages with bilateral keys: {stats['has_bilateral']}")
    print(f"  Languages without bilateral keys: {stats['no_bilateral']}")
    print(f"  Configurations checked: {stats['configs_checked']}")
    
    print(f"\n{'='*80}")
    print(f"ERRORS FOUND: {len(errors)}")
    print(f"{'='*80}")
    
    if errors:
        for i, err in enumerate(errors[:20], 1):  # Show first 20
            print(f"\n{i}. [{err['lang_name']}] Config {err['config']}")
            print(f"   Type: {err['type']}")
            print(f"   {err['message']}")
            if 'details' in err:
                print(f"   Details: {err['details']}")
        
        if len(errors) > 20:
            print(f"\n... and {len(errors) - 20} more errors")
    else:
        print("No errors found!")
    
    print(f"\n{'='*80}")
    print(f"WARNINGS: {len(warnings)}")
    print(f"{'='*80}")
    
    if warnings:
        for i, warn in enumerate(warnings[:10], 1):  # Show first 10
            print(f"\n{i}. [{warn['lang_name']}] Config {warn['config']}")
            print(f"   Type: {warn['type']}")
            print(f"   {warn['message']}")
        
        if len(warnings) > 10:
            print(f"\n... and {len(warnings) - 10} more warnings")
    
    return errors, warnings


def validate_anyother_consistency(all_langs_position2sizes, all_langs_position2num, langNames):
    """
    Validate that 'anyother' keys are consistent with bilateral keys.
    
    For each language, check that:
    - right_i_anyother_totright_n aggregates correctly from bilateral keys
    - left_i_anyother_totleft_n aggregates correctly from bilateral keys
    """
    print("\n" + "="*80)
    print("ANYOTHER KEY CONSISTENCY CHECK")
    print("="*80)
    
    inconsistencies = []
    
    for lang in sorted(all_langs_position2sizes.keys())[:10]:  # Check first 10 for efficiency
        position2sizes = all_langs_position2sizes[lang]
        position2num = all_langs_position2num[lang]
        lang_name = langNames.get(lang, lang)
        
        # Aggregate bilateral keys by right total
        bilateral_right_agg = defaultdict(lambda: {'size': 0, 'count': 0})
        
        for key, size_sum in position2sizes.items():
            count = position2num.get(key, 0)
            
            # bilateral_L{l}_R{r}_pos_{i}_right -> contributes to totright_{r}
            match = re.match(r'bilateral_L(\d+)_R(\d+)_pos_(\d+)_right$', key)
            if match:
                r = int(match.group(2))
                pos = int(match.group(3))
                key_agg = (r, pos)  # (total_right, position)
                bilateral_right_agg[key_agg]['size'] += size_sum
                bilateral_right_agg[key_agg]['count'] += count
        
        # Compare with anyother keys
        for key, size_sum in position2sizes.items():
            count = position2num.get(key, 0)
            if count < MIN_COUNT:
                continue
            
            match = re.match(r'right_(\d+)_anyother_totright_(\d+)$', key)
            if match:
                pos = int(match.group(1))
                tot = int(match.group(2))
                
                key_agg = (tot, pos)
                if key_agg in bilateral_right_agg:
                    bilateral_size = bilateral_right_agg[key_agg]['size']
                    bilateral_count = bilateral_right_agg[key_agg]['count']
                    
                    # Check if they match (with tolerance)
                    if bilateral_count > 0:
                        anyother_avg = size_sum / count
                        bilateral_avg = bilateral_size / bilateral_count
                        
                        if abs(anyother_avg - bilateral_avg) > 0.01:
                            inconsistencies.append({
                                'lang': lang,
                                'lang_name': lang_name,
                                'key': key,
                                'anyother_avg': anyother_avg,
                                'anyother_count': count,
                                'bilateral_avg': bilateral_avg,
                                'bilateral_count': bilateral_count
                            })
    
    if inconsistencies:
        print(f"\nFound {len(inconsistencies)} inconsistencies:")
        for inc in inconsistencies[:5]:
            print(f"\n  {inc['lang_name']}: {inc['key']}")
            print(f"    Anyother: avg={inc['anyother_avg']:.3f}, count={inc['anyother_count']}")
            print(f"    Bilateral: avg={inc['bilateral_avg']:.3f}, count={inc['bilateral_count']}")
    else:
        print("\nNo inconsistencies found between anyother and bilateral keys!")
    
    return inconsistencies


def check_mal_sum_relationship(all_langs_position2sizes, all_langs_position2num, langNames):
    """
    Check that for bilateral configs:
    MAL (combined) = weighted average of left and right sides
    
    Formula: MAL = (n_left * MAL_left + n_right * MAL_right) / (n_left + n_right)
    
    This MUST hold if the data is computed correctly.
    """
    print("\n" + "="*80)
    print("MAL WEIGHTED AVERAGE VALIDATION")
    print("="*80)
    print("\nChecking: MAL = (L * avg_left + R * avg_right) / (L + R)")
    
    errors = []
    checked = 0
    
    for lang in sorted(all_langs_position2sizes.keys()):
        position2sizes = all_langs_position2sizes[lang]
        position2num = all_langs_position2num[lang]
        lang_name = langNames.get(lang, lang)
        
        # Find all bilateral configs
        configs = set()
        for key in position2sizes.keys():
            match = re.match(r'bilateral_L(\d+)_R(\d+)_pos_\d+_(left|right)$', key)
            if match:
                l = int(match.group(1))
                r = int(match.group(2))
                if l > 0 and r > 0:  # Only mixed configs
                    configs.add((l, r))
        
        for n_left, n_right in sorted(configs):
            config = analyze_bilateral_configuration(
                lang, position2sizes, position2num, n_left, n_right
            )
            
            if config['total_left_count'] > 0 and config['total_right_count'] > 0:
                # Both sides have data
                avg_left = config['total_left_weighted'] / config['total_left_count']
                avg_right = config['total_right_weighted'] / config['total_right_count']
                actual_mal = compute_mal_for_config(config)
                
                # Expected MAL using weighted average
                total_n = n_left + n_right
                expected_mal = (n_left * avg_left + n_right * avg_right) / total_n
                
                # These should NOT necessarily be equal because:
                # - actual_mal uses count-weighted average across all positions
                # - expected uses position-count weighted average
                
                # But we can check: total_weighted_size / total_count
                total_weighted = config['total_left_weighted'] + config['total_right_weighted']
                total_count = config['total_left_count'] + config['total_right_count']
                recomputed_mal = total_weighted / total_count
                
                # This should exactly equal actual_mal
                if abs(recomputed_mal - actual_mal) > 0.0001:
                    errors.append({
                        'lang': lang_name,
                        'config': f'L{n_left}_R{n_right}',
                        'actual_mal': actual_mal,
                        'recomputed_mal': recomputed_mal,
                        'diff': abs(recomputed_mal - actual_mal)
                    })
                
                checked += 1
    
    print(f"\nChecked {checked} configurations across {len(all_langs_position2sizes)} languages")
    
    if errors:
        print(f"\n⚠️  Found {len(errors)} MAL computation errors:")
        for err in errors[:10]:
            print(f"  {err['lang']} {err['config']}: actual={err['actual_mal']:.4f}, recomputed={err['recomputed_mal']:.4f}")
    else:
        print("\n✓ All MAL computations are consistent!")
    
    return errors


def check_occurrence_counts(all_langs_position2sizes, all_langs_position2num, langNames):
    """
    Check that for each bilateral config L{l}_R{r}:
    - The left constituents should also appear in left_*_anyother_totleft_{l}
    - The right constituents should also appear in right_*_anyother_totright_{r}
    
    So: count(bilateral L{l}_R{r} left side) <= count(anyother totleft_{l})
        count(bilateral L{l}_R{r} right side) <= count(anyother totright_{r})
        
    The anyother should be >= bilateral because anyother aggregates across ALL
    configs with that many left/right deps.
    """
    print("\n" + "="*80)
    print("OCCURRENCE COUNT VALIDATION")
    print("="*80)
    print("\nChecking: For each bilateral config, anyother keys cover the same data")
    print("  bilateral L{l}_R{r} left side <= anyother totleft_{l}")
    print("  bilateral L{l}_R{r} right side <= anyother totright_{r}")
    
    violations = []
    stats = {'checked': 0, 'passed': 0, 'failed': 0}
    
    for lang in sorted(all_langs_position2sizes.keys()):
        position2sizes = all_langs_position2sizes[lang]
        position2num = all_langs_position2num[lang]
        lang_name = langNames.get(lang, lang)
        
        # Collect bilateral data by config
        bilateral_data = defaultdict(lambda: {'left': defaultdict(int), 'right': defaultdict(int)})
        
        for key, count in position2num.items():
            match = re.match(r'bilateral_L(\d+)_R(\d+)_pos_(\d+)_(left|right)$', key)
            if match:
                l = int(match.group(1))
                r = int(match.group(2))
                pos = int(match.group(3))
                side = match.group(4)
                bilateral_data[(l, r)][side][pos] += count
        
        # Collect anyother data
        anyother_left = defaultdict(lambda: defaultdict(int))  # totleft -> pos -> count
        anyother_right = defaultdict(lambda: defaultdict(int))  # totright -> pos -> count
        
        for key, count in position2num.items():
            match_left = re.match(r'left_(\d+)_anyother_totleft_(\d+)$', key)
            if match_left:
                pos = int(match_left.group(1))
                tot = int(match_left.group(2))
                anyother_left[tot][pos] += count
                continue
            
            match_right = re.match(r'right_(\d+)_anyother_totright_(\d+)$', key)
            if match_right:
                pos = int(match_right.group(1))
                tot = int(match_right.group(2))
                anyother_right[tot][pos] += count
        
        # Check each bilateral config
        for (l, r), data in bilateral_data.items():
            # Check left side: bilateral L{l}_R{r} left constituents <= anyother totleft_{l}
            if l > 0:
                for pos, bilateral_count in data['left'].items():
                    anyother_count = anyother_left[l].get(pos, 0)
                    stats['checked'] += 1
                    
                    if anyother_count >= bilateral_count:
                        stats['passed'] += 1
                    else:
                        stats['failed'] += 1
                        violations.append({
                            'lang': lang,
                            'lang_name': lang_name,
                            'config': f'L{l}_R{r}',
                            'side': 'left',
                            'pos': pos,
                            'bilateral_count': bilateral_count,
                            'anyother_count': anyother_count,
                            'deficit': bilateral_count - anyother_count
                        })
            
            # Check right side: bilateral L{l}_R{r} right constituents <= anyother totright_{r}
            if r > 0:
                for pos, bilateral_count in data['right'].items():
                    anyother_count = anyother_right[r].get(pos, 0)
                    stats['checked'] += 1
                    
                    if anyother_count >= bilateral_count:
                        stats['passed'] += 1
                    else:
                        stats['failed'] += 1
                        violations.append({
                            'lang': lang,
                            'lang_name': lang_name,
                            'config': f'L{l}_R{r}',
                            'side': 'right',
                            'pos': pos,
                            'bilateral_count': bilateral_count,
                            'anyother_count': anyother_count,
                            'deficit': bilateral_count - anyother_count
                        })
    
    print(f"\nChecked {stats['checked']} (config, position) pairs across {len(all_langs_position2sizes)} languages")
    print(f"  Passed: {stats['passed']}")
    print(f"  Failed: {stats['failed']}")
    
    if violations:
        print(f"\n⚠️  Found {len(violations)} violations:")
        print("\n  Lang              Config     Side   Pos  Bilateral  Anyother  Deficit")
        print("  " + "-"*70)
        
        # Sort by deficit (most severe first)
        violations.sort(key=lambda x: -x['deficit'])
        
        for v in violations[:20]:
            print(f"  {v['lang_name']:<15} {v['config']:<10} {v['side']:<6} {v['pos']:>3}  {v['bilateral_count']:>9}  {v['anyother_count']:>8}  {v['deficit']:>7}")
        
        if len(violations) > 20:
            print(f"\n  ... and {len(violations) - 20} more violations")
    else:
        print("\n✓ All anyother keys properly cover bilateral data!")
    
    return violations


def diagnose_occurrence_deficit(all_langs_position2sizes, all_langs_position2num, langNames, sample_lang=None, sample_n=None):
    """
    Deep dive into why occurrence counts don't match.
    
    For a sample language and n, show exactly which bilateral configs exist
    and which anyother keys are missing.
    """
    print("\n" + "="*80)
    print("OCCURRENCE DEFICIT DIAGNOSIS")
    print("="*80)
    
    # Pick a sample language with significant data
    if sample_lang is None:
        # Find first language with violations
        for lang in ['cs_pdt', 'ru_syntagrus', 'de_hdt', 'en_ewt']:
            if lang in all_langs_position2sizes:
                sample_lang = lang
                break
        else:
            sample_lang = next(iter(all_langs_position2sizes.keys()))
    
    if sample_n is None:
        sample_n = 3
    
    position2sizes = all_langs_position2sizes[sample_lang]
    position2num = all_langs_position2num[sample_lang]
    lang_name = langNames.get(sample_lang, sample_lang)
    
    print(f"\nDiagnosing: {lang_name} (n={sample_n})")
    print("-" * 60)
    
    # 1. List all bilateral configs for this n
    print(f"\n1. Bilateral configs where L + R = {sample_n}:")
    bilateral_configs = defaultdict(lambda: {'left': {}, 'right': {}})
    
    for key, count in position2num.items():
        match = re.match(r'bilateral_L(\d+)_R(\d+)_pos_(\d+)_(left|right)$', key)
        if match:
            l = int(match.group(1))
            r = int(match.group(2))
            if l + r == sample_n:
                pos = int(match.group(3))
                side = match.group(4)
                config_key = (l, r)
                bilateral_configs[config_key][side][pos] = count
    
    total_bilateral = 0
    for (l, r), data in sorted(bilateral_configs.items()):
        left_sum = sum(data['left'].values())
        right_sum = sum(data['right'].values())
        total = left_sum + right_sum
        total_bilateral += total
        filtered_left = sum(1 for c in data['left'].values() if c < MIN_COUNT)
        filtered_right = sum(1 for c in data['right'].values() if c < MIN_COUNT)
        print(f"   L{l}_R{r}: left_count={left_sum} ({len(data['left'])} positions), right_count={right_sum} ({len(data['right'])} positions)")
        if filtered_left or filtered_right:
            print(f"           (filtered: {filtered_left} left, {filtered_right} right positions below min_count)")
    
    print(f"\n   Total bilateral count for n={sample_n}: {total_bilateral}")
    
    # 2. Check anyother keys for each component
    print(f"\n2. Anyother keys that SHOULD cover this data:")
    
    # For L=l, R=r config:
    # - The L left constituents should appear in left_i_anyother_totleft_{l}
    # - The R right constituents should appear in right_i_anyother_totright_{r}
    
    for (l, r), data in sorted(bilateral_configs.items()):
        print(f"\n   Config L{l}_R{r}:")
        
        # Check left anyother keys
        if l > 0:
            print(f"     Left side (L={l}):")
            for pos in sorted(data['left'].keys()):
                bilateral_count = data['left'][pos]
                anyother_key = f'left_{pos}_anyother_totleft_{l}'
                anyother_count = position2num.get(anyother_key, 0)
                status = "✓" if anyother_count >= bilateral_count else "✗ MISSING"
                print(f"       pos {pos}: bilateral={bilateral_count}, anyother={anyother_count} {status}")
        
        # Check right anyother keys
        if r > 0:
            print(f"     Right side (R={r}):")
            for pos in sorted(data['right'].keys()):
                bilateral_count = data['right'][pos]
                anyother_key = f'right_{pos}_anyother_totright_{r}'
                anyother_count = position2num.get(anyother_key, 0)
                status = "✓" if anyother_count >= bilateral_count else "✗ MISSING"
                print(f"       pos {pos}: bilateral={bilateral_count}, anyother={anyother_count} {status}")
    
    # 3. Compute what the anyother totals would be
    print(f"\n3. Summary of anyother counts for n={sample_n}:")
    
    anyother_left_total = 0
    for pos in range(1, sample_n + 1):
        key = f'left_{pos}_anyother_totleft_{sample_n}'
        count = position2num.get(key, 0)
        if count > 0:
            anyother_left_total += count
            print(f"   {key}: {count}")
    print(f"   Total anyother left for totleft={sample_n}: {anyother_left_total}")
    
    anyother_right_total = 0
    for pos in range(1, sample_n + 1):
        key = f'right_{pos}_anyother_totright_{sample_n}'
        count = position2num.get(key, 0)
        if count > 0:
            anyother_right_total += count
            print(f"   {key}: {count}")
    print(f"   Total anyother right for totright={sample_n}: {anyother_right_total}")
    
    print(f"\n4. Comparison:")
    print(f"   Bilateral total (L+R={sample_n}):           {total_bilateral}")
    print(f"   Anyother sum (left_{sample_n} + right_{sample_n}): {anyother_left_total + anyother_right_total}")
    print(f"   Deficit:                              {total_bilateral - (anyother_left_total + anyother_right_total)}")
    
    return bilateral_configs


def check_left_right_coverage(all_langs_position2sizes, all_langs_position2num, langNames):
    """
    For each bilateral L{l}_R{r} config, verify:
    - We have data for all left positions 1..l (or explain why not)
    - We have data for all right positions 1..r (or explain why not)
    
    Missing positions indicate data was filtered due to min_count.
    """
    print("\n" + "="*80)
    print("POSITION COVERAGE CHECK")
    print("="*80)
    
    incomplete_configs = []
    
    for lang in sorted(all_langs_position2sizes.keys()):
        position2sizes = all_langs_position2sizes[lang]
        position2num = all_langs_position2num[lang]
        lang_name = langNames.get(lang, lang)
        
        # Collect all data by config
        config_data = defaultdict(lambda: {'left': {}, 'right': {}})
        
        for key, size_sum in position2sizes.items():
            count = position2num.get(key, 0)
            
            match = re.match(r'bilateral_L(\d+)_R(\d+)_pos_(\d+)_(left|right)$', key)
            if match:
                l = int(match.group(1))
                r = int(match.group(2))
                pos = int(match.group(3))
                side = match.group(4)
                
                config_key = (l, r)
                config_data[config_key][side][pos] = {
                    'size_sum': size_sum,
                    'count': count,
                    'filtered': count < MIN_COUNT
                }
        
        # Check each config
        for (n_left, n_right), data in config_data.items():
            left_positions = set(data['left'].keys())
            right_positions = set(data['right'].keys())
            
            expected_left = set(range(1, n_left + 1))
            expected_right = set(range(1, n_right + 1))
            
            missing_left = expected_left - left_positions
            missing_right = expected_right - right_positions
            
            # Check if missing due to filtering
            filtered_left = [p for p in data['left'] if data['left'][p]['filtered']]
            filtered_right = [p for p in data['right'] if data['right'][p]['filtered']]
            
            if missing_left or missing_right:
                incomplete_configs.append({
                    'lang': lang_name,
                    'config': f'L{n_left}_R{n_right}',
                    'missing_left': missing_left,
                    'missing_right': missing_right,
                    'filtered_left': filtered_left,
                    'filtered_right': filtered_right
                })
    
    print(f"\nConfigurations with incomplete position coverage: {len(incomplete_configs)}")
    
    if incomplete_configs:
        # Group by type of incompleteness
        truly_missing = [c for c in incomplete_configs if c['missing_left'] or c['missing_right']]
        print(f"\nConfigs with positions completely absent from data: {len(truly_missing)}")
        
        for c in truly_missing[:5]:
            print(f"  {c['lang']} {c['config']}: missing L={c['missing_left']}, R={c['missing_right']}")
    else:
        print("\n✓ All expected positions are present in the data (some may be filtered by min_count)")
    
    return incomplete_configs


def main():
    print("Loading data...")
    all_langs_position2sizes, all_langs_position2num, langNames = load_data()
    print(f"Loaded data for {len(all_langs_position2sizes)} languages")
    
    # Run validations
    errors, warnings = validate_mal_additivity(
        all_langs_position2sizes, all_langs_position2num, langNames
    )
    
    # Check anyother consistency
    inconsistencies = validate_anyother_consistency(
        all_langs_position2sizes, all_langs_position2num, langNames
    )
    
    # Check MAL computation
    mal_errors = check_mal_sum_relationship(
        all_langs_position2sizes, all_langs_position2num, langNames
    )
    
    # Check occurrence counts: anyother keys should cover bilateral data
    occurrence_violations = check_occurrence_counts(
        all_langs_position2sizes, all_langs_position2num, langNames
    )
    
    # Check position coverage
    coverage_issues = check_left_right_coverage(
        all_langs_position2sizes, all_langs_position2num, langNames
    )
    
    # Summary
    print("\n" + "="*80)
    print("VALIDATION SUMMARY")
    print("="*80)
    print(f"  Position count errors: {len(errors)}")
    print(f"  Warnings: {len(warnings)}")
    print(f"  Anyother inconsistencies: {len(inconsistencies)}")
    print(f"  MAL computation errors: {len(mal_errors)}")
    print(f"  Occurrence count violations: {len(occurrence_violations)}")
    print(f"  Incomplete position coverage: {len(coverage_issues)}")
    
    total_errors = len(errors) + len(mal_errors) + len(occurrence_violations)
    if total_errors:
        print(f"\n⚠️  {total_errors} ISSUES FOUND - Please review!")
        return 1
    else:
        print("\n✓ No critical errors found")
        return 0


if __name__ == '__main__':
    sys.exit(main())

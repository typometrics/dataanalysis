#!/usr/bin/env python3
"""
Debug XXV geometric mean computation by creating a test language with exactly 20 trees.
Then compare Helix table computation vs HTML sample computation.
"""

import os
import sys
import pickle
from pathlib import Path

def extract_trees_by_config(source_conll_file, target_configs, max_per_config=20):
    """
    Extract trees with specific verb configurations from a CoNLL file.
    
    Args:
        source_conll_file: Path to CoNLL file
        target_configs: Dict like {'XXV': 20, 'XXVXX': 5, 'VXXX': 5}
        max_per_config: Max trees per configuration
    
    Returns:
        Dict mapping config to list of trees
    """
    from conll import conllFile2trees
    
    print(f"Reading {source_conll_file}...")
    
    collected_trees = {config: [] for config in target_configs}
    tree_count = 0
    
    deps = [
        "nsubj", "obj", "iobj", "csubj", "ccomp", "xcomp", 
        "obl", "expl", "dislocated", "advcl", "advmod", 
        "nmod", "appos", "nummod", "acl", "amod"
    ]
    
    for tree in conllFile2trees(source_conll_file):
        tree_count += 1
        
        # Check if we've collected enough of all configs
        if all(len(trees) >= target_configs[cfg] for cfg, trees in collected_trees.items()):
            break
        
        # Add spans to identify verb configurations
        tree.addspan(exclude=['punct'], compute_bastards=True)
        
        # Find verbs and their configurations
        for node_id in tree:
            node = tree[node_id]
            if node.get('tag') != 'VERB':
                continue
            
            # Count valid left and right dependents
            left_deps = []
            right_deps = []
            kids = node.get('kids', {})
            
            for kid_id, rel in kids.items():
                base_rel = rel.split(':')[0]
                if base_rel in deps:
                    if kid_id < node_id:
                        left_deps.append(kid_id)
                    else:
                        right_deps.append(kid_id)
            
            # Determine configuration
            left_count = len(left_deps)
            right_count = len(right_deps)
            
            config = 'X' * left_count + 'V' + 'X' * right_count
            
            # Check if this is a target config
            if config in target_configs:
                if len(collected_trees[config]) < target_configs[config]:
                    collected_trees[config].append(tree)
                    print(f"  Found {config} tree #{len(collected_trees[config])} at sentence {tree_count}")
                    break
    
    print(f"\nCollected trees from {tree_count} total sentences:")
    for config, trees in collected_trees.items():
        print(f"  {config}: {len(trees)} trees")
    
    return collected_trees


def write_trees_to_file(trees_by_config, output_file):
    """
    Write collected trees to a CoNLL file.
    """
    print(f"Writing to {output_file}...")
    total_trees = 0
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for config, trees in trees_by_config.items():
            for tree in trees:
                # Write tree in CoNLL-U format
                lines = []
                for node_id in sorted([k for k in tree.keys() if isinstance(k, int)]):
                    node = tree[node_id]
                    # Format: ID FORM LEMMA UPOS XPOS FEATS HEAD DEPREL DEPS MISC
                    gov_dict = node.get('gov', {})
                    head = list(gov_dict.keys())[0] if gov_dict else 0
                    deprel = list(gov_dict.values())[0] if gov_dict else 'root'
                    
                    line = f"{node_id}\t{node.get('t', '_')}\t{node.get('t', '_')}\t{node.get('tag', '_')}\t_\t_\t{head}\t{deprel}\t_\t_"
                    lines.append(line)
                
                # Add sentence text comment if available
                if 0 in tree and 't' in tree[0]:
                    f.write(f"# text = {tree[0]['t']}\n")
                
                f.write('\n'.join(lines))
                f.write('\n\n')
                total_trees += 1
    
    print(f"Done! Wrote {total_trees} trees to {output_file}")
    return total_trees


def run_helix_computation(test_lang_code, test_conll_file, data_dir):
    """
    Run the Helix table computation for the test language.
    """
    print("\n" + "="*80)
    print("STEP 2: Computing Helix table for test language")
    print("="*80)
    
    import conll_processing
    
    # Process the single file
    results = conll_processing.process_file_complete(
        test_conll_file,
        include_bastards=True,
        compute_sentence_disorder=False,
        collect_config_examples=False
    )
    
    lang, position2num, position2sizes, sizes2freq, position2charsizes, *_ = results
    
    # Compute geometric means
    import numpy as np
    position_averages = {}
    
    for key in position2num:
        if position2num[key] > 0:
            # GM = exp(sum_of_logs / count)
            position_averages[key] = np.exp(position2sizes[key] / position2num[key])
    
    print(f"\nHelix computation for {test_lang_code}:")
    print(f"  left_2_totleft_2: {position_averages.get('left_2_totleft_2', 'N/A')}")
    print(f"  left_1_totleft_2: {position_averages.get('left_1_totleft_2', 'N/A')}")
    
    return position_averages, position2num


def run_html_sample_computation(test_lang_code, test_conll_file):
    """
    Run the HTML sample computation (mimics generate_html_examples.py logic).
    """
    print("\n" + "="*80)
    print("STEP 3: Computing sample geometric means (HTML-style)")
    print("="*80)
    
    from conll import conllFile2trees
    import numpy as np
    
    # Collect XXV examples
    examples = []
    
    for tree in conllFile2trees(test_conll_file):
        tree.addspan(exclude=['punct'], compute_bastards=True)
        
        deps = [
            "nsubj", "obj", "iobj", "csubj", "ccomp", "xcomp", 
            "obl", "expl", "dislocated", "advcl", "advmod", 
            "nmod", "appos", "nummod", "acl", "amod"
        ]
        
        for node_id in tree:
            node = tree[node_id]
            if node.get('tag') != 'VERB':
                continue
            
            # Count valid left dependents
            left_deps = []
            kids = node.get('kids', {})
            
            for kid_id, rel in kids.items():
                base_rel = rel.split(':')[0]
                if base_rel in deps and kid_id < node_id:
                    left_deps.append(kid_id)
            
            if len(left_deps) == 2:
                # Calculate span sizes
                dep_sizes = {}
                for kid in left_deps:
                    span = tree[kid].get('direct_span', tree[kid]['span'])
                    dep_sizes[kid] = len(span)
                
                examples.append({
                    'verb_id': node_id,
                    'dep_ids': left_deps,
                    'dep_sizes': dep_sizes
                })
                break
    
    print(f"\nFound {len(examples)} XXV examples")
    
    # Compute geometric means per position (mimics calculate_position_stats)
    left_sizes = {0: [], 1: []}  # index -> list of sizes
    
    for ex in examples:
        vid = ex['verb_id']
        dids = ex['dep_ids']
        dsizes = ex['dep_sizes']
        
        # Sort left dependents (farther to closer)
        left_deps = sorted([d for d in dids if d < vid])
        
        for i, d in enumerate(left_deps):
            if d in dsizes and dsizes[d] > 0:
                left_sizes[i].append(dsizes[d])
    
    # Compute geometric means
    sample_gm = {}
    for i in [0, 1]:
        if left_sizes[i]:
            gm = np.exp(np.mean(np.log(left_sizes[i])))
            sample_gm[i] = gm
            print(f"  Position {i} (Left {2-i}): GM = {gm:.3f} from {len(left_sizes[i])} values")
            print(f"    Raw sizes: {left_sizes[i]}")
    
    return sample_gm, left_sizes


def main():
    # Configuration
    TEST_LANG = "test_xxv"
    
    # Find a source language with many XXV examples
    source_lang = "en"  # English usually has many examples
    source_files = []
    
    # Look for English CoNLL files
    base_dir = Path("/bigstorage/kim/typometrics/dataanalysis/2.17_short")
    if base_dir.exists():
        source_files = list(base_dir.glob("en_*.conllu"))
    
    if not source_files:
        print("ERROR: Could not find English CoNLL files in 2.17_short/")
        return
    
    print(f"Using source file: {source_files[0]}")
    
    # Create output directory
    test_dir = Path("/bigstorage/kim/typometrics/dataanalysis/debug_xxv")
    test_dir.mkdir(exist_ok=True)
    
    test_conll_file = test_dir / f"{TEST_LANG}_test.conllu"
    
    # Step 1: Extract trees with different configurations
    print("\n" + "="*80)
    print("STEP 1: Extracting trees with multiple configurations")
    print("="*80)
    
    # Request 20 XXV, 5 XXVXX, 5 VXXX
    target_configs = {
        'XXV': 20,    # 2 left, 0 right
        'XXVXX': 5,   # 2 left, 2 right
        'VXXX': 5     # 0 left, 3 right
    }
    
    trees_by_config = extract_trees_by_config(str(source_files[0]), target_configs)
    num_trees = write_trees_to_file(trees_by_config, str(test_conll_file))
    
    if num_trees == 0:
        print("ERROR: No XXV trees found!")
        return
    
    # Step 2: Run Helix computation
    helix_averages, helix_counts = run_helix_computation(TEST_LANG, str(test_conll_file), "data")
    
    # Step 3: Run HTML sample computation
    sample_gm, sample_sizes = run_html_sample_computation(TEST_LANG, str(test_conll_file))
    
    # Step 4: Compare results
    print("\n" + "="*80)
    print("STEP 4: COMPARISON")
    print("="*80)
    
    print("\n*** IMPORTANT: Only XXV trees should be counted (20 trees) ***")
    print("*** XXVXX (5 trees) and VXXX (5 trees) should be IGNORED ***\n")
    
    print("Position X2 (outer, farther from verb = left_2_totleft_2):")
    helix_x2 = helix_averages.get('left_2_totleft_2', None)
    sample_x2 = sample_gm.get(0, None)
    print(f"  Helix computation: {helix_x2:.3f}" if helix_x2 else "  Helix: N/A")
    print(f"  Sample computation: {sample_x2:.3f}" if sample_x2 else "  Sample: N/A")
    if helix_x2 and sample_x2:
        diff_pct = 100*(helix_x2-sample_x2)/sample_x2 if sample_x2 != 0 else 0
        print(f"  Difference: {helix_x2 - sample_x2:.3f} ({diff_pct:.1f}%)")
        if abs(helix_x2 - sample_x2) < 0.001:
            print("  ✓ MATCH - Both methods give same result!")
        else:
            print("  ✗ MISMATCH - Different results!")
    
    print("\nPosition X1 (inner, closer to verb = left_1_totleft_2):")
    helix_x1 = helix_averages.get('left_1_totleft_2', None)
    sample_x1 = sample_gm.get(1, None)
    print(f"  Helix computation: {helix_x1:.3f}" if helix_x1 else "  Helix: N/A")
    print(f"  Sample computation: {sample_x1:.3f}" if sample_x1 else "  Sample: N/A")
    if helix_x1 and sample_x1:
        diff_pct = 100*(helix_x1-sample_x1)/sample_x1 if sample_x1 != 0 else 0
        print(f"  Difference: {helix_x1 - sample_x1:.3f} ({diff_pct:.1f}%)")
        if abs(helix_x1 - sample_x1) < 0.001:
            print("  ✓ MATCH - Both methods give same result!")
        else:
            print("  ✗ MISMATCH - Different results!")
    
    print("\n" + "="*80)
    print("DEBUG INFO")
    print("="*80)
    print(f"\nHelix counts (should be 20 for XXV only):")
    print(f"  left_2_totleft_2: {helix_counts.get('left_2_totleft_2', 0)} occurrences")
    print(f"  left_1_totleft_2: {helix_counts.get('left_1_totleft_2', 0)} occurrences")
    
    # Check other configurations to ensure they're not counted
    print(f"\nOther configurations in Helix (should be present but not affecting XXV):")
    print(f"  left_2_totleft_2 (XXVXX left part): counted separately")
    print(f"  right_1_totright_3 (VXXX): {helix_counts.get('right_1_totright_3', 0)} occurrences")
    print(f"  right_2_totright_3 (VXXX): {helix_counts.get('right_2_totright_3', 0)} occurrences")
    print(f"  right_3_totright_3 (VXXX): {helix_counts.get('right_3_totright_3', 0)} occurrences")
    
    print(f"\nSample raw sizes (should be 20 values from XXV only):")
    print(f"  Position 0 (X2): {len(sample_sizes.get(0, []))} values - {sample_sizes.get(0, [])}")
    print(f"  Position 1 (X1): {len(sample_sizes.get(1, []))} values - {sample_sizes.get(1, [])}")
    
    print("\n" + "="*80)
    print(f"Test files saved to: {test_dir}")
    print("="*80)


if __name__ == '__main__':
    main()

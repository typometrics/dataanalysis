"""
Test configuration example collection with a small subset of files.
"""
import os
import glob
import pickle
import conll_processing

# Test with a small subset (first 3 files)
test_files = sorted(glob.glob('2.17_short/*.conllu'))[:3]

print(f"Testing with {len(test_files)} files:")
for f in test_files:
    print(f"  - {os.path.basename(f)}")

print("\nRunning get_all_stats_parallel with collect_config_examples=True...")

results = conll_processing.get_all_stats_parallel(
    test_files,
    include_bastards=True,
    compute_sentence_disorder=False,
    collect_config_examples=True,
    max_examples_per_config=10
)

print("\nUnpacking results...")
(all_langs_position2num, all_langs_position2sizes, all_langs_average_sizes, all_langs_average_charsizes,
 lang_bastard_stats, global_bastard_relations, 
 lang_vo_hi_scores, 
 sentence_disorder_pct,
 all_config_examples) = results

print(f"\nResults:")
print(f"  Languages processed: {len(all_config_examples)}")
for lang, configs in all_config_examples.items():
    print(f"  {lang}:")
    for config, examples in configs.items():
        print(f"    {config}: {len(examples)} examples")
        if examples:
            # Verify structure
            ex = examples[0]
            print(f"      First example has keys: {list(ex.keys())}")
            print(f"      Tree has keys: {list(ex['tree'].keys())}")
            print(f"      Verb ID: {ex['verb_id']}, Dep IDs: {ex['dep_ids']}")

print("\n✅ Test passed! Integration working correctly.")
print("\nTo collect all examples, run:")
print("  python run_data_extraction.py")
print("\nTo generate HTML, run:")
print("  python generate_html_examples.py")

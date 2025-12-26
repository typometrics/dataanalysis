#!/usr/bin/env python3
"""
Generate a real AnyOtherSide table for French to verify everything works.
"""

import os
import sys
import pickle

sys.path.insert(0, os.path.dirname(__file__))

def main():
    print("="*80)
    print("REAL ANYOTHERSIDE TABLE GENERATION TEST")
    print("="*80)
    
    # Load real data
    print("\n📂 Loading real data...")
    
    # Load the all_langs_average_sizes data
    data_file = 'data/all_langs_average_sizes_filtered.pkl'
    if not os.path.exists(data_file):
        print(f"❌ Data file not found: {data_file}")
        return 1
    
    with open(data_file, 'rb') as f:
        all_langs_data = pickle.load(f)
    
    print(f"   Loaded data for {len(all_langs_data)} languages")
    
    # Load language names from metadata
    metadata_file = 'data/metadata.pkl'
    if not os.path.exists(metadata_file):
        print(f"❌ Metadata file not found: {metadata_file}")
        return 1
    
    with open(metadata_file, 'rb') as f:
        metadata = pickle.load(f)
        langnames = metadata.get('langNames', {})
    
    # Select French as test case
    test_lang = 'fr'
    if test_lang not in all_langs_data:
        print(f"❌ French (fr) not found in data")
        print(f"   Available languages: {list(all_langs_data.keys())[:10]}")
        return 1
    
    print(f"\n📊 Generating AnyOtherSide table for French (fr)...")
    
    # Check what anyother keys are available
    fr_data = all_langs_data[test_lang]
    anyother_keys = [k for k in fr_data.keys() if 'anyother' in k]
    print(f"   Found {len(anyother_keys)} anyother keys:")
    for key in sorted(anyother_keys)[:10]:
        print(f"     {key}: {fr_data[key]:.2f}")
    
    if not anyother_keys:
        print("\n❌ No anyother statistics found for French!")
        print("   This means the data was not collected with anyother support.")
        return 1
    
    # Generate the table
    import verb_centered_analysis
    
    output_dir = "test_real_output"
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        verb_centered_analysis.generate_anyotherside_helix_tables(
            {test_lang: all_langs_data[test_lang]},
            {test_lang: langnames.get(test_lang, test_lang)},
            output_dir=output_dir
        )
        
        # Check output (updated filename format)
        tsv_file = f"{output_dir}/Helix_{langnames.get(test_lang, test_lang)}_fr_AnyOtherSide.tsv"
        xlsx_file = f"{output_dir}/Helix_{langnames.get(test_lang, test_lang)}_fr_AnyOtherSide.xlsx"
        
        if os.path.exists(tsv_file):
            print(f"\n✅ TSV file created: {tsv_file}")
            with open(tsv_file, 'r') as f:
                content = f.read()
                print("\n📄 TSV Content:")
                print("-" * 80)
                print(content)
                print("-" * 80)
        else:
            print(f"\n❌ TSV file not created")
        
        if os.path.exists(xlsx_file):
            print(f"\n✅ XLSX file created: {xlsx_file}")
        else:
            print(f"\n❌ XLSX file not created")
        
        print("\n🎉 SUCCESS!")
        return 0
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        # Cleanup
        import shutil
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
            print(f"\n🧹 Cleaned up {output_dir}")

if __name__ == '__main__':
    sys.exit(main())

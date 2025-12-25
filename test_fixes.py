#!/usr/bin/env python3
"""
Test the fixes for HTML and AnyOtherSide Helix tables.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

def test_html_fix():
    """Test that partial configs only show relevant side."""
    print("="*80)
    print("TEST 1: HTML Partial Config Display")
    print("="*80)
    
    import generate_html_examples
    from importlib import reload
    reload(generate_html_examples)
    
    # Create fake examples for VXX_anyleft (2 right, any left)
    fake_examples = [
        {
            'verb_id': 5,
            'dep_ids': [3, 4, 6, 7],  # 2 left (3,4), 2 right (6,7)
            'dep_sizes': {3: 2, 4: 1, 6: 3, 7: 5}
        }
    ]
    
    fake_global_stats = {
        'right_1_anyother': 2.5,
        'right_2_anyother': 4.0,
        'left_1_anyother': 1.5,
        'left_2_anyother': 1.8,
    }
    
    # Test partial_right (VXX_anyleft) - should only show RIGHT side
    print("\n📊 Testing VXX_anyleft (partial_right):")
    print("   Should show: Post-verbal (V X₁ X₂)")
    print("   Should NOT show: Pre-verbal")
    
    html = generate_html_examples.calculate_position_stats(
        fake_examples,
        global_stats=fake_global_stats,
        l_count=0,  # No fixed left count
        r_count=2,  # 2 right dependents
        config_type='partial_right'
    )
    
    has_preverbal = 'Pre-verbal' in html
    has_postverbal = 'Post-verbal' in html
    
    print(f"\n   Contains 'Pre-verbal': {has_preverbal}")
    print(f"   Contains 'Post-verbal': {has_postverbal}")
    
    if not has_preverbal and has_postverbal:
        print("\n   ✅ PASSED: Only showing post-verbal (correct!)")
        return True
    else:
        print("\n   ❌ FAILED: Showing wrong sides")
        print("\n   HTML output:")
        print(html)
        return False


def test_anyotherside_table():
    """Test that AnyOtherSide tables have proper format."""
    print("\n" + "="*80)
    print("TEST 2: AnyOtherSide Helix Table Format")
    print("="*80)
    
    import verb_centered_analysis
    from importlib import reload
    reload(verb_centered_analysis)
    
    # Create test data
    test_data = {
        'test_en': {
            'right_1_anyother': 2.5,
            'right_2_anyother': 3.2,
            'right_3_anyother': 4.1,
            'left_1_anyother': 2.0,
            'left_2_anyother': 2.8,
            'left_3_anyother': 3.5,
            'xvx_left_1_anyother': 1.8,
            'xvx_right_1_anyother': 2.2,
        }
    }
    
    langnames = {'test_en': 'TestEnglish'}
    
    output_dir = "test_output_fixes"
    os.makedirs(output_dir, exist_ok=True)
    
    print("\n📊 Generating AnyOtherSide table...")
    
    try:
        verb_centered_analysis.generate_anyotherside_helix_tables(
            test_data,
            langnames,
            output_dir=output_dir
        )
        
        # Check output files
        tsv_file = f"{output_dir}/Helix_AnyOtherSide_TestEnglish_test_en.tsv"
        xlsx_file = f"{output_dir}/Helix_AnyOtherSide_TestEnglish_test_en.xlsx"
        
        tsv_exists = os.path.exists(tsv_file)
        xlsx_exists = os.path.exists(xlsx_file)
        
        print(f"\n   TSV file exists: {tsv_exists}")
        print(f"   XLSX file exists: {xlsx_exists}")
        
        if tsv_exists:
            with open(tsv_file, 'r') as f:
                content = f.read()
                print("\n   TSV Content:")
                print("   " + "\n   ".join(content.split('\n')[:20]))
                
                # Check for expected patterns
                has_notation = '... V' in content or 'V ...' in content
                has_values = '2.50' in content or '2.00' in content
                
                print(f"\n   Has '... V X' notation: {has_notation}")
                print(f"   Has numeric values: {has_values}")
                
                if tsv_exists and xlsx_exists and has_notation and has_values:
                    print("\n   ✅ PASSED: Proper format with TSV/XLSX")
                    return True
                else:
                    print("\n   ❌ FAILED: Missing expected format elements")
                    return False
        else:
            print("\n   ❌ FAILED: TSV file not created")
            return False
            
    except Exception as e:
        print(f"\n   ❌ FAILED with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Cleanup
        import shutil
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)


def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("FIX VALIDATION TEST SUITE")
    print("="*80)
    
    results = []
    
    # Test 1: HTML fix
    try:
        results.append(("HTML Partial Config", test_html_fix()))
    except Exception as e:
        print(f"\n❌ TEST 1 CRASHED: {e}")
        import traceback
        traceback.print_exc()
        results.append(("HTML Partial Config", False))
    
    # Test 2: AnyOtherSide table
    try:
        results.append(("AnyOtherSide Table", test_anyotherside_table()))
    except Exception as e:
        print(f"\n❌ TEST 2 CRASHED: {e}")
        import traceback
        traceback.print_exc()
        results.append(("AnyOtherSide Table", False))
    
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

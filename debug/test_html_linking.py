import os
import shutil
import unittest
import sys

# Add parent directory to path to import generate_html_examples
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from generate_html_examples import parse_tsv_to_html, generate_language_index, classify_configuration

class TestHtmlLinking(unittest.TestCase):
    def setUp(self):
        self.test_dir = 'test_html_output'
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        os.makedirs(self.test_dir)
        
        # Create a mock language folder
        self.lang_folder = os.path.join(self.test_dir, 'TestLang_tl')
        os.makedirs(self.lang_folder)
        self.samples_dir = os.path.join(self.lang_folder, 'samples')
        os.makedirs(self.samples_dir)
        
        # Mock TSV content (Standard)
        self.tsv_std_path = os.path.join(self.lang_folder, 'Helix_TestLang_tl.tsv')
        with open(self.tsv_std_path, 'w') as f:
            f.write("Row\tL4\tL3\tL2\tL1\tV\tR1\tR2\tR3\tR4\n")
            f.write("R tot=2\t\t\t\t\tV\t3.5\t2.1\t\t\n")  # Should link to VXX.html
            f.write("L tot=1\t\t\t\t1.2\tV\t\t\t\t\n")  # Should link to XV.html

        # Mock Sample Files
        # For R tot=2 -> VXX_anyleft (AnyOtherSide)
        with open(os.path.join(self.samples_dir, 'VXX_anyleft.html'), 'w') as f: f.write("<html></html>")
        # For L tot=3 -> XXXV_anyright (AnyOtherSide)
        with open(os.path.join(self.samples_dir, 'XXXV_anyright.html'), 'w') as f: f.write("<html></html>")
        
        # Standard Samples
        # VXX (l=0, r=2)
        with open(os.path.join(self.samples_dir, 'VXX.html'), 'w') as f: f.write("<html></html>")
        # XV (l=1, r=0)
        with open(os.path.join(self.samples_dir, 'XV.html'), 'w') as f: f.write("<html></html>")

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_parse_tsv_with_links_and_tooltip(self):
        """Test if parse_tsv_to_html adds links and tooltips."""
        link_map = {'R tot=2': 'samples/VXX.html'}
        html = parse_tsv_to_html(self.tsv_std_path, link_map=link_map)
        
        self.assertIn('<a href="samples/VXX.html"', html)
        self.assertIn('title="show samples"', html)
        self.assertIn('>R tot=2</a>', html)

    def test_link_generation_logic(self):
        """Test logic to map standard and anyother configs."""
        # Helper to simulate generate_language_index logic locally for test
        # (This duplicates logic but confirms expected behavior of that logic block)
        standard_link_map = {}
        anyother_link_map = {}
        
        sample_files = ['VXX_anyleft.html', 'VXX.html', 'XV.html']
        
        for fname in sample_files:
            config = fname.replace('.html', '')
            is_partial = 'any' in config
            
            # Simple parser simulation
            l_count = 0
            r_count = 0
            if 'V' in config:
                base = config.split('_')[0]
                idx = base.index('V')
                l_count = base[:idx].count('X')
                r_count = base[idx+1:].count('X')
            
            ref_url = f"samples/{fname}"
            
            if is_partial:
                if 'anyleft' in config and l_count==0 and r_count>0:
                    anyother_link_map[f'R tot={r_count}'] = ref_url
            else:
                if l_count==0 and r_count>0:
                    standard_link_map[f'R tot={r_count}'] = ref_url
                if r_count==0 and l_count>0:
                    standard_link_map[f'L tot={l_count}'] = ref_url

        self.assertEqual(anyother_link_map.get('R tot=2'), 'samples/VXX_anyleft.html')
        self.assertEqual(standard_link_map.get('R tot=2'), 'samples/VXX.html')
        self.assertEqual(standard_link_map.get('L tot=1'), 'samples/XV.html')


if __name__ == '__main__':
    unittest.main()

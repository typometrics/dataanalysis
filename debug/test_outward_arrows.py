
import unittest
import sys
import os

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from verb_centered_model import TableConfig
from verb_centered_computations import FactorCalculator
from verb_centered_builder import VerbCenteredTableBuilder, TableStructure

class MockLayout:
    def get_right_column_index(self, pos, is_factor=False): return pos * 2
    def get_left_column_index(self, pos, is_factor=False): return pos * 2

class TestOutwardArrows(unittest.TestCase):
    def setUp(self):
        # Setup mock data
        # V = 100
        # Right: R1=50, R2=100 (Growth x2)
        # Left: L1=50, L2=100 (Growth x2 Outward)
        # If Inward (Standard?): L2(100) -> L1(50) is x0.5.
        
        self.data = {
            'right_1_totright_2': 50.0,
            'right_2_totright_2': 100.0,
            'right_1_totright_previous': 50.0, # For diagonal
            
            'left_1_totleft_2': 50.0,
            'left_2_totleft_2': 100.0,
            
            # Diagonal keys (Left)
            # L2@tot=2 (100) -> L1@tot=1 (Need mock)
            'left_1_totleft_1': 25.0, # Target (upper)
            # Diag Inward: L2@2 (100) -> L1@1 (25). Ratio 0.25?
            # Or L1@1 (25) -> L2@2 (100). Ratio 4.0?
        }
    
    def test_outward_horizontal_values(self):
        # 1. Test 'outward' configuration
        config = TableConfig(arrow_direction='outward', show_horizontal_factors=True)
        calc = FactorCalculator(self.data, config)
        
        # Right Side (R1->R2)
        # Outward: R2/R1 = 100/50 = 2.0
        f_right = calc.get_horizontal_factor('right', 2, 2)
        self.assertEqual(f_right.value, 2.0, "Right horizontal outward should be 2.0")
        
        # Left Side (L1<-L2)
        # Outward: L2/L1 = 100/50 = 2.0
        f_left = calc.get_horizontal_factor('left', 2, 2)
        # If the code works as analyzed (get_growth_direction returns 'outward'), this should be 2.0
        # If it returns 'inward' by default for left, it might be 0.5.
        self.assertEqual(f_left.value, 2.0, f"Left horizontal outward should be 2.0, got {f_left.value}")

    def test_outward_diagonal_values(self):
        config = TableConfig(arrow_direction='outward', show_diagonal_factors=True)
        calc = FactorCalculator(self.data, config)
        
        # Left Diagonal: Should be Reversed (Outward/Growth)
        f_diag_left = calc.get_diagonal_factor('left', 1, 1) # pos 1, tot 1
        # L2@2(100) -> L1@1(25). Default inward=0.25 (25/100).
        # Outward reversed = 4.0.
        self.assertEqual(f_diag_left.value, 4.0, f"Outward Left Diag should be 4.0 (Reversed), got {f_diag_left.value}")
        
        # Right Diagonal: Should NOT be Reversed (Standard/Outward)
        # R1@tot=2 (50) -> R2@tot=3 (need mock)
        # Mock R2@tot=3
        self.data['right_2_totright_3'] = 100.0
        self.data['right_1_totright_2'] = 50.0 # Source for diagonal
        
        f_diag_right = calc.get_diagonal_factor('right', 1, 3) # pos 1 (R1), tot 3 (target row)
        # Logic: key_b = right_2_tot_3 (100), key_a = right_1_tot_2 (50)
        # Default factor = b/a = 2.0. This is already Outward (growth).
        # So we expect 2.0. Previous bad fix might have made it 0.5.
        
        self.assertEqual(f_diag_right.value, 2.0, f"Outward Right Diag should be 2.0 (Standard), got {f_diag_right.value}")

    def test_outward_xvx_arrow(self):
        """Test that XVX arrow remains Left-to-Right (→) even in Outward mode."""
        config = TableConfig(arrow_direction='outward', show_horizontal_factors=True)
        # Mock data for XVX
        data = {
            'xvx_left_1': 50.0,
            'xvx_right_1': 100.0,
            'factor_xvx_right_1_vs_xvx_left_1': 2.0
        }
        
        # We need to test _build_xvx_row. 
        # Instantiating builder with minimal data
        builder = VerbCenteredTableBuilder(data, config)
        
        # Build the row
        row = builder._build_xvx_row()
        
        # Find the factor cell
        factor_cell = None
        for cell in row:
            if cell.cell_type == 'factor':
                factor_cell = cell
                break
        
        self.assertIsNotNone(factor_cell, "XVX row should have a factor cell")
        text = factor_cell.text
        # Expectation: "x2.00→"
        self.assertIn('→', text, f"XVX Arrow should be '→' (Left-to-Right), got '{text}'") # Fixed previously

if __name__ == '__main__':
    unittest.main()

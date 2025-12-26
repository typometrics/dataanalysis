
import sys
import os

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from verb_centered_model import TableConfig

def check_arrows(mode):
    config = TableConfig(arrow_direction=mode)
    gd = config.get_growth_direction('left')
    arrow_diag_left = config.get_arrow_symbol('left', 'diagonal')
    arrow_horiz_left = config.get_arrow_symbol('left', 'horizontal')
    
    print(f"Mode: {mode}")
    print(f"  Left Growth Logic: {gd}")
    print(f"  Left Diag Arrow: {arrow_diag_left} (Should be ↙ for Outward)")
    print(f"  Left Horiz Arrow: {arrow_horiz_left}")
    
check_arrows('diverging')
check_arrows('outward')
check_arrows('left_to_right')


import sys
import os
import numpy as np

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from verb_centered_computations import MarginalMeansCalculator, calc_geometric_mean
from verb_centered_model import TableConfig

# Mock Data simulating the user's report (approximate values)
# M Diag Right, Diagonal 2 (Short): R1T3 -> R2T4
# Table says: Diag R2-1 is x1.13, Diag R3-2 is x1.08, Diag R4-3 is x1.06
# User says last diag value (M Diag Right, 0? or 2?) is x1.18.
# Actually let's look at the implementation of Diagonals.

# Table Rows:
# R tot=2: Diag R2-1 (R1T1 -> R2T2)
# R tot=3: Diag R3-2 (R1T2 -> R2T3), (R2T2 -> R3T3)
# R tot=4: Diag R4-3 (R1T3 -> R2T4), (R2T3 -> R3T4), (R3T3 -> R4T4)

# Marginal Means:
# Diag 0 (Longest): R1T1, R2T2, R3T3, R4T4. Factors: (R1T1->R2T2), (R2T2->R3T3), (R3T3->R4T4).
# Diag 2 (Short): R1T3, R2T4. Factor: (R1T3->R2T4).

# User says "last diag value, x1.18, does not lie inside ... x1.13, x1.08, x1.06"
# This suggests M Diag Right aggregates ACROSS diagonals? 
# OR does M Diag Right show 3 different averages?
# Builder code:
# for diag_idx in [2, 1, 0]: ... place factor ...

# If 'last diag value' means the one for R4 column?
# The columns in M Diag Right are aligned with positions R2, R3, R4.
# diag_idx 0 (Longest R4 pos): R1T1->..->R4T4. (3 factors).
# diag_idx 2 (Shortest R2 pos): R1T3->R2T4. (1 factor).

# Let's verify what `calc_diagonal_means_right` actually computes vs what is expected.

# Mocking position averages
data = {}

# Set Size values to result in SPECIFIC ratios.
# Factor A (R1T3 -> R2T4): Size 100 -> 118 (Ratio 1.18).
data['right_1_totright_3'] = 100.0
data['right_2_totright_4'] = 118.0 
# Implied Factor: 1.18
data['factor_right_2_totright_4_vs_right_1_totright_3'] = 1.18 # Match size ratio

# Factor B (R2T3 -> R3T4). Size 100 -> 108. (Ratio 1.08).
data['right_2_totright_3'] = 100.0
data['right_3_totright_4'] = 108.0
data['factor_right_3_totright_4_vs_right_2_totright_3'] = 1.08

# Factor C (R3T3 -> R4T4). Size 100 -> 106. (Ratio 1.06).
data['right_3_totright_3'] = 100.0
data['right_4_totright_4'] = 106.0
data['factor_right_4_totright_4_vs_right_3_totright_3'] = 1.06

# Now, introduce Discrepancy: Factors in table are NOT exactly Size ratios.
# In real data, Mean(Ratio) != Ratio(Mean).
# Let's force explicit Factor keys to be different from Size ratios.
# User sees x1.13, x1.08, x1.06 in the table.
# These correspond to specific row cells?
# Diag R2-1: R1T1->R2T2.
# Diag R3-2: R1T2->R2T3, R2T2->R3T3.
# Diag R4-3: R1T3->R2T4, R2T3->R3T4, R3T3->R4T4.

# Wait, the user listed "Diag R4-3... x1.28, x1.18, x1.06".
# These should be R1T3->R2T4, R2T3->R3T4, R3T3->R4T4.
data['factor_right_2_totright_4_vs_right_1_totright_3'] = 1.28
data['factor_right_3_totright_4_vs_right_2_totright_3'] = 1.18
data['factor_right_4_totright_4_vs_right_3_totright_3'] = 1.06

# If Marginal calculator uses SIZES, it sees 1.18, 1.08, 1.06 (from above setup).
# If it uses FACTORS, it sees 1.28, 1.18, 1.06.

# Let's run calculator
calc = MarginalMeansCalculator(data)
diags = calc.calc_diagonal_means_right()

# Diag 0 (Longest) corresponds to R4T4 endpoint?
# keys_sz for diag 0: u=1..5? No u=1..4: R1T1, R2T2, R3T3, R4T4.
# This is the "Main Diagonal" trace. Factors: R1T1->R2T2, R2T2->R3T3, R3T3->R4T4.
# This corresponds to column R4 in M Diag Right (position 4).

print("--- Data Setup ---")
print("Size Ratios (Implied): 1.18, 1.08, 1.06")
print("Factor Values (Explicit): 1.28, 1.18, 1.06")

print("\n--- Calculated Marginal Means ---")
# Check Diag 0 (Longest) - effectively Main Diagonal?
# Wait, let's check definitions in calc_diagonal_means_right:
# Diag 0: R1T1..R4T4.
# Diag 1: R1T2..R3T4.
# Diag 2: R1T3..R2T4.

# User reported: "last diag value... x1.18... composed of x1.13, x1.08, x1.06"
# This implies the user thinks M Diag Right column 4 aggregates the entire column or something?
# Actually, if the table shows:
# R tot=4 line: ... x1.28 ... x1.18 ... x1.06 ...
# That row IS the R tot=4 line.
# User: "M Diag Right... 1.63 x1.32, 1.87 x1.27, 3.13 x1.18"
# The x1.18 is in the last column (R4 column).
# This corresponds to Diag 0 (Main Diagonal R1T1..R4T4).
# This is composed of factors: R1T1->R2T2, R2T2->R3T3, R3T3->R4T4.
# In the user's table, these are:
# R tot=2: Diag R2-1 cell -> x0.88 (R1T1->R2T2)
# R tot=3: Diag R3-2 last cell -> x0.92 (R2T2->R3T3?? No R2T2->R3T3 is diff)

# Actually, the diagonals in the table lines:
# Diag R2-1: (R1T1->R2T2)
# Diag R3-2: (R1T2->R2T3), (R2T2->R3T3)
# Diag R4-3: (R1T3->R2T4), (R2T3->R3T4), (R3T3->R4T4)

# M Diag Right (Column 4) sums up the "Main Diagonal" (R1T1->R2T2->R3T3->R4T4).
# Components:
# 1. R1T1->R2T2 (From row R tot=2, Diag R2-1)
# 2. R2T2->R3T3 (From row R tot=3, Diag R3-2 rightmost cell)
# 3. R3T3->R4T4 (From row R tot=4, Diag R4-3 rightmost cell)

# Let's populate mock data for THESE specific transitions.
# 1. R1T1 -> R2T2
data['right_1_totright_1'] = 10.0
data['right_2_totright_2'] = 11.3 # x1.13
data['factor_right_2_totright_2_vs_right_1_totright_1'] = 1.13

# 2. R2T2 -> R3T3 (NOT in R tot=3 row? R tot=3 row has Diag R3-2: R_x_T2 -> R_y_T3)
# Row R tot=3 has indices pos=1..3.
# Diag row R3-2 has pos=1..2.
# Pos 1: R1T2 -> R2T3.
# Pos 2: R2T2 -> R3T3.
# So yes, R2T2->R3T3 is in R tot=3 Diag row.
data['right_3_totright_3'] = 11.3 * 1.08 # x1.08
data['factor_right_3_totright_3_vs_right_2_totright_2'] = 1.08

# 3. R3T3 -> R4T4 (In R tot=4 Diag row)
data['right_4_totright_4'] = data['right_3_totright_3'] * 1.06 # x1.06
data['factor_right_4_totright_4_vs_right_3_totright_3'] = 1.06

# Now calculate Marginal Mean for Diag 0
diags = calc.calc_diagonal_means_right()
sz, fac = diags[0]

print(f"Marginal Factor (Size-Based): {fac:.4f}")

# Expected Average of Factors: GM(1.13, 1.08, 1.06)
import math
expected = math.exp((math.log(1.13) + math.log(1.08) + math.log(1.06)) / 3)
print(f"Expected Factor (Mean of Factors): {expected:.4f}")

if abs(fac - expected) > 0.001:
    print("DISCREPANCY DETECTED: Marginal uses Size ratios, Table uses specific Factors.")
else:
    print("No discrepancy found with consistent data. (Try creating inconsistent data)")

# Force inconsistency:
# Size ratio is 1.13, but Factor is 1.50
data['factor_right_2_totright_2_vs_right_1_totright_1'] = 1.50
# Size ratio 1.08, Factor 1.50
data['factor_right_3_totright_3_vs_right_2_totright_2'] = 1.50
# Size ratio 1.06, Factor 1.50
data['factor_right_4_totright_4_vs_right_3_totright_3'] = 1.50

diags = calc.calc_diagonal_means_right()
sz, fac = diags[0]
print(f"\n--- After Forcing Inconsistency ---")
print(f"Marginal Factor (Size-Based): {fac:.4f}")
# Expected: 1.50
expected = 1.50
print(f"Expected Factor (Mean of Factors): {expected:.4f}")


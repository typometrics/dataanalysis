
def compute_average_sizes_table(all_langs_average_sizes_filtered):
    """
    Compute average constituent sizes at each position for different totals.
    Returns a dictionary of averages keyed by position string (e.g. 'right_1_totright_2').
    """
    # Dictionary to store sums and counts for averaging
    position_sums = {}
    position_counts = {}
    
    # Collect all values across languages
    for lang, positions in all_langs_average_sizes_filtered.items():
        for position_key, value in positions.items():
            if position_key not in position_sums:
                position_sums[position_key] = 0
                position_counts[position_key] = 0
            position_sums[position_key] += value
            position_counts[position_key] += 1
    
    # Calculate averages
    position_averages = {}
    for position_key in position_sums:
        if position_counts[position_key] > 0:
            position_averages[position_key] = position_sums[position_key] / position_counts[position_key]
    
    return position_averages

import os

def format_verb_centered_table(position_averages, 
                               show_horizontal_factors=False, 
                               show_diagonal_factors=False,
                               arrow_direction='diverging',
                               save_tsv=True,
                               output_dir='data',
                               filename=None):
    """
    Format the computed averages into a readable string table.
    Optionally saves the table to a TSV file.
    
    Parameters
    ----------
    position_averages : dict
        Dictionary of values.
    show_horizontal_factors : bool
        If True, adds columns with growth factors between positions.
    show_diagonal_factors : bool
        If True, adds rows with diagonal growth factors.
    arrow_direction : str
        'diverging': Arrows point outward from verb (Right->R, Left->L).
        'rightwards': Arrows point generally Top-Right (Right->R, Left->R).
    save_tsv : bool
        If True, save the table to a file.
    output_dir : str
        Directory to save output.
    filename : str
        Filename for TSV output. If None, auto-generated from options.
    """
    lines = []
    lines.append("=" * 120)
    lines.append("VERB-CENTERED CONSTITUENT SIZE TABLE")
    if show_horizontal_factors or show_diagonal_factors:
        lines.append("WITH GROWTH FACTORS")
    lines.append("=" * 120)
    lines.append("")
    
    # Layout constants
    VAL_WIDTH = 8   
    FAC_WIDTH = 12 if show_horizontal_factors else 0
    
    # Header V
    HALF_WIDTH = 4 * VAL_WIDTH + 3 * FAC_WIDTH
    V_MARKER = f"{' ':>{HALF_WIDTH}}   V   {' ':>{HALF_WIDTH}}"
    lines.append(f"     {V_MARKER}") 

    E_VAL = " " * VAL_WIDTH
    E_FAC = " " * FAC_WIDTH
    LEFT_PAD = " " * HALF_WIDTH

    # Store rows for TSV output
    # Each row is a list of cell strings
    tsv_rows = []
    # Add Header Row to TSV? Hard to represent complex structure.
    # We will write the exact text lines to the file, but tab-separated? 
    # Or just write the formatted string to a text file? user said ".tsv file".
    # TSV implies structure. Let's try to make a structured list of lists.
    # But the table is irregular (different num columns per row visually).
    # Best compromise: Write a TSV that maps to the visual grid.
    # Columns: RowLabel, L4, F43, L3, F32, L2, F21, L1, V, R1, F12, R2, F23, R3, F34, R4
    
    header_cols = ["Row", "L4", "F43", "L3", "F32", "L2", "F21", "L1", "V", "R1", "F12", "R2", "F23", "R3", "F34", "R4"]
    tsv_rows.append(header_cols)

    # ---------------------------------------------------------
    # 1. Right Dependents
    # ---------------------------------------------------------
    for tot in [4, 3, 2, 1]:
        # 1a. Print Current Row Values
        parts = []
        parts.append(" V") 
        
        # TSV Data for Right side
        tsv_right = ["V"]
        
        prev_val = None
        
        for pos in range(1, tot + 1):
            key = f'right_{pos}_totright_{tot}'
            val = position_averages.get(key, float('nan'))
            
            # Format Value
            if isinstance(val, float) and val != val:
                val_str = "N/A".center(VAL_WIDTH)
                tsv_val = "N/A"
                val = None
            else:
                val_str = f"{val:>{VAL_WIDTH}.3f}" if val is not None else "N/A".center(VAL_WIDTH)
                tsv_val = f"{val:.3f}" if val is not None else "N/A"
            
            # Horizontal Factor (between prev and current)
            if pos > 1 and show_horizontal_factors:
                if prev_val is not None and val is not None and prev_val != 0:
                    factor = val / prev_val
                    # Unicode Arrow: Right side always Rightwards ->
                    fac_str = f"×{factor:.2f} →".center(FAC_WIDTH)
                    tsv_fac = f"{factor:.2f}"
                else:
                    fac_str = E_FAC
                    tsv_fac = ""
                parts.append(fac_str)
                tsv_right.append(tsv_fac)
            
            parts.append(val_str)
            tsv_right.append(tsv_val)
            prev_val = val
            
        right_str = "".join(parts)
        lines.append(f"R tot={tot}: {LEFT_PAD}{right_str}")
        
        # Build TSV Row
        # Left side empty for R rows
        row_label = f"R tot={tot}"
        # Values: RowLabel + [Empty Left Cells] + [V + Right Cells]
        # Left Cells count: 7 (L4..L1). 
        # But we need padding?
        # Fixed 7 slots for Left: L4, F, L3, F, L2, F, L1.
        left_empty = [""] * 7
        
        # Right side can be variable length. Pad to 7 (R1..R4)
        # Standard: R1, F, R2, F, R3, F, R4. (7 slots)
        # tsv_right currently has: V, R1, [F, R2], [F, R3]...
        # Let's fix loop logic to standardize
        # It pushed V, then (if pos>1 F), Val.
        # Order: V, R1, F12, R2, F23, R3, F34, R4.
        # tsv_right content: "V", "R1", "F12", "R2"...
        # We need to pad tsv_right to max length 8 (V + 7).
        while len(tsv_right) < 8:
            tsv_right.append("")
            
        full_tsv_row = [row_label] + left_empty + tsv_right
        tsv_rows.append(full_tsv_row)
        
        # 1b. Print Diagonal Factors (Connection to Next Row: tot-1)
        if tot > 1 and show_diagonal_factors:
            diag_parts = []
            diag_parts.append("   ") 
            
            # TSV Diag Row
            tsv_diag_right = [""] # Under V
            
            for pos in range(1, tot): 
                diag_parts.append(E_VAL) 
                tsv_diag_right.append("") # Under R_pos
                
                if show_horizontal_factors:
                    src_key = f'right_{pos}_totright_{tot-1}'
                    tgt_key = f'right_{pos+1}_totright_{tot}'
                    src_val = position_averages.get(src_key, None)
                    tgt_val = position_averages.get(tgt_key, None)
                    
                    if src_val is not None and tgt_val is not None and src_val != 0:
                        factor = tgt_val / src_val
                        # Arrow Top-Right ↗
                        diag_str = f"×{factor:.2f} ↗".center(FAC_WIDTH)
                        tsv_fac = f"{factor:.2f} (diag)"
                    else:
                        diag_str = E_FAC
                        tsv_fac = ""
                    diag_parts.append(diag_str)
                    tsv_diag_right.append(tsv_fac)
                
            diag_parts.append(E_VAL) 
            while len(tsv_diag_right) < 8: tsv_diag_right.append("")
                
            lines.append(f"        {LEFT_PAD}{''.join(diag_parts)}")
            
            tsv_rows.append([f"Diag R{tot}-{tot-1}"] + left_empty + tsv_diag_right)

    lines.append("-" * 120)
    tsv_rows.append(["separator"])

    # ---------------------------------------------------------
    # 2. Left Dependents
    # ---------------------------------------------------------
    for tot in [1, 2, 3, 4]:
        # 2a. Print Current Row Values
        # TSV Left Row
        tsv_left = [""] * 7
        
        row_cells = []
        cells = [""] * (4 + 3) if show_horizontal_factors else [""] * 4
        # Fill with spaces
        for i in range(len(cells)):
             cells[i] = E_FAC if (show_horizontal_factors and i % 2 == 1) else E_VAL

        prev_val_inner = None 
        
        for pos in range(1, tot + 1):
             key = f'left_{pos}_totleft_{tot}'
             val = position_averages.get(key, None)
             
             if show_horizontal_factors:
                 val_idx = 6 - (pos - 1) * 2
             else:
                 val_idx = 3 - (pos - 1)
             
             if val is not None:
                 cells[val_idx] = f"{val:>{VAL_WIDTH}.3f}"
                 tsv_left[val_idx] = f"{val:.3f}"
             else:
                 cells[val_idx] = "N/A".center(VAL_WIDTH)
                 val = None

             if pos > 1 and show_horizontal_factors:
                 fac_idx = val_idx + 1 # Slot to the right
                 
                 # Arrow Direction Logic
                 if arrow_direction == 'rightwards':
                     # Left to Right -->
                     # factor = prev_val_inner / val
                     if prev_val_inner is not None and val is not None and val != 0:
                         factor = prev_val_inner / val
                         cells[fac_idx] = f"×{factor:.2f} →".center(FAC_WIDTH)
                         tsv_left[fac_idx] = f"{factor:.2f}"
                     else:
                         cells[fac_idx] = E_FAC
                 else: # diverging
                     # Right to Left <--
                     # factor = val / prev_val_inner
                     if prev_val_inner is not None and val is not None and prev_val_inner != 0:
                         factor = val / prev_val_inner
                         cells[fac_idx] = f"← {factor:.2f}×".center(FAC_WIDTH) # arrow before?
                         # Usually factor then arrow. "x 1.32 <--"
                         # Or "<-- 1.32 x".
                         # Standard requested: "x symbol followed by factor and then by a real unicode arrow"
                         # "x 1.23 <-"
                         cells[fac_idx] = f"×{factor:.2f} ←".center(FAC_WIDTH)
                         tsv_left[fac_idx] = f"{factor:.2f}"
                     else:
                         cells[fac_idx] = E_FAC

             prev_val_inner = val
             
        left_str = "".join(cells)
        # Add V
        lines.append(f"L tot={tot}: {left_str} V")
        
        tsv_row = [f"L tot={tot}"] + tsv_left + ["V"] + [""]*7
        tsv_rows.append(tsv_row)
        
        # 2b. Print Diagonal Factors
        if tot < 4 and show_diagonal_factors and show_horizontal_factors:
            diag_cells = [""] * 7
            tsv_diag_left = [""] * 7
            for i in range(7): diag_cells[i] = E_FAC if i % 2 == 1 else E_VAL
            
            for pos in range(1, tot + 1):
                tgt_key = f'left_{pos}_totleft_{tot}'
                src_key = f'left_{pos+1}_totleft_{tot+1}'
                tgt_val = position_averages.get(tgt_key, None)
                src_val = position_averages.get(src_key, None)
                
                if pos + 1 > 4: continue
                fac_idx = (6 - (pos - 1) * 2) - 1 # Slot left of pos
                
                if src_val is not None and tgt_val is not None and src_val != 0:
                     factor = tgt_val / src_val
                     # Arrow Top-Right ↗
                     diag_cells[fac_idx] = f"×{factor:.2f} ↗".center(FAC_WIDTH)
                     tsv_diag_left[fac_idx] = f"{factor:.2f} (diag)"
                
            lines.append(f"        {''.join(diag_cells)}   ")
            tsv_rows.append([f"Diag L{tot}-{tot+1}"] + tsv_diag_left + [""] * 8)


    lines.append("=" * 120)
    lines.append(f"Mode: Factors={show_horizontal_factors}, Diagonals={show_diagonal_factors}, Direction={arrow_direction}")
    lines.append("========================================================================================================================")
    
    # Save TSV
    if save_tsv and output_dir:
        # Auto-generate filename if not provided
        if filename is None:
            parts = ['verb_centered_table']
            if show_horizontal_factors:
                parts.append('factors')
            if show_diagonal_factors:
                parts.append('diagonal')
            if show_horizontal_factors or show_diagonal_factors:
                parts.append(arrow_direction)
            filename = "_".join(parts) + ".tsv"
            
        try:
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            full_path = os.path.join(output_dir, filename)
            with open(full_path, 'w', encoding='utf-8') as f:
                for row in tsv_rows:
                    f.write("\t".join(row) + "\n")
            lines.append(f"Table saved to: {full_path}")
        except Exception as e:
            lines.append(f"Error saving TSV: {e}")
            
    return "\n".join(lines)

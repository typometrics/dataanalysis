
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

class GridCell:
    def __init__(self, text="", value=None, cell_type='normal', rich_text=None, is_astonishing=False):
        self.text = text
        self.value = value
        self.cell_type = cell_type 
        self.rich_text = rich_text 
        self.is_astonishing = is_astonishing

def extract_verb_centered_grid(position_averages, 
                               show_horizontal_factors=False, 
                               show_diagonal_factors=False,
                               arrow_direction='diverging',
                               ordering_stats=None,
                               show_ordering_triples=False,
                               show_row_averages=False):
    """
    Constructs a grid of GridCell objects representing the table.
    """
    rows = []
    
    # Constants
    # E_VAL = GridCell(" " * 11) 
    
    # Colors
    COLOR_RED = "FF0000"
    COLOR_GREY = "555555"
    COLOR_DARK = "000000"
    
    # ---------------------------------------------------------
    # 1. Right Dependents
    # ---------------------------------------------------------
    for tot in [4, 3, 2, 1]:
        row_cells = []
        row_cells.append(GridCell(f"R tot={tot}", cell_type='label'))
        
        # Padding
        for _ in range(7): row_cells.append(GridCell(""))
        
        # Center "V"
        row_cells.append(GridCell("V", cell_type='label'))
        
        prev_val = None
        
        for pos in range(1, tot + 1):
             key = f'right_{pos}_totright_{tot}'
             val = position_averages.get(key, float('nan'))
             
             # Horizontal Factor logic
             if pos > 1 and show_horizontal_factors:
                 fac_cell = GridCell("", cell_type='factor')
                 rich_segments = []
                 text_parts = []
                 
                 # 1. Factor
                 factor_val = None
                 if prev_val is not None and val is not None and val != 0 and val == val:
                     factor_val = val / prev_val
                     f_str = f"×{factor_val:.2f}→" # Arrow right basically always for Right side
                     
                     # Color Rule: Red if factor < 1
                     f_color = COLOR_RED if factor_val < 1.0 else COLOR_GREY
                     rich_segments.append((f_str, f_color, True)) # Bold factor? User image shows bold red.
                     text_parts.append(f_str)

                 # 2. Triple
                 if show_ordering_triples and ordering_stats:
                     pair_idx = pos - 2
                     o_key = ('right', tot, pair_idx)
                     o_data = ordering_stats.get(o_key)
                     if o_data:
                        tot_count = o_data['lt'] + o_data['eq'] + o_data['gt']
                        if tot_count > 0:
                            lt = o_data['lt'] / tot_count * 100
                            eq = o_data['eq'] / tot_count * 100
                            gt = o_data['gt'] / tot_count * 100
                            
                            # Build text for TSV
                            t_str_full = f"(<{lt:.0f}={eq:.0f}>{gt:.0f})"
                            text_parts.append(t_str_full)
                            
                            # Build Rich Text Segments
                            # Prefix: " (<" + lt + "=" + eq + ">"
                            # User wants: (<31=35>34) where 34 is Red if gt > lt
                            
                            # Add space separator if factor exists
                            if rich_segments:
                                rich_segments.append((" ", COLOR_GREY, False))
                                
                            prefix = f"(<{lt:.0f}={eq:.0f}>"
                            rich_segments.append((prefix, COLOR_GREY, False))
                            
                            # GT part
                            gt_str = f"{gt:.0f}"
                            gt_color = COLOR_RED if gt > lt else COLOR_GREY
                            gt_bold = True if gt > lt else False
                            rich_segments.append((gt_str, gt_color, gt_bold))
                            
                            # Suffix
                            rich_segments.append((")", COLOR_GREY, False))

                 if text_parts:
                     fac_cell.text = " ".join(text_parts)
                     fac_cell.rich_text = rich_segments
                     
                 row_cells.append(fac_cell)
             
             # Value Cell (Numeric)
             val_cell = GridCell("", value=val, cell_type='value')
             if isinstance(val, float) and val == val: # not nan
                 val_cell.text = f"{val:.3f}"
                 # Ensure value is stored for Excel
                 val_cell.value = float(val) 
             else:
                 val_cell.text = "N/A"
                 val_cell.value = None
             row_cells.append(val_cell)
             
             prev_val = val
             
        # Row Average
        if show_row_averages:
             avg_key = f'average_totright_{tot}'
             row_avg = position_averages.get(avg_key)
             if row_avg is not None:
                 row_cells.append(GridCell(f"[Avg: {row_avg:.3f}]", cell_type='comment'))

        rows.append(row_cells)
        
        # Diagonals (Right)
        if tot > 1 and show_diagonal_factors:
            diag_row = [GridCell(f"Diag R{tot}-{tot-1}", cell_type='label')]
            for _ in range(7): diag_row.append(GridCell("")) 
            diag_row.append(GridCell("")) 
            
            for pos in range(1, tot):
                diag_row.append(GridCell("")) 
                if show_horizontal_factors:
                    src_key = f'right_{pos}_totright_{tot-1}'
                    tgt_key = f'right_{pos+1}_totright_{tot}'
                    src_val = position_averages.get(src_key)
                    tgt_val = position_averages.get(tgt_key)
                    
                    diag_cell = GridCell("", cell_type='factor')
                    if src_val and tgt_val:
                        factor = tgt_val / src_val
                        diag_str = f"×{factor:.2f} ↗"
                        diag_cell.text = diag_str
                        # Rich text for diagonal
                        d_color = COLOR_RED if factor < 1.0 else COLOR_GREY
                        diag_cell.rich_text = [(diag_str, d_color, True)]
                        
                    diag_row.append(diag_cell)
            rows.append(diag_row)

    rows.append([GridCell("separator", cell_type='separator')])
    
    # ---------------------------------------------------------
    # 2. Left Dependents
    # ---------------------------------------------------------
    for tot in [1, 2, 3, 4]:
        row_cells = []
        row_cells.append(GridCell(f"L tot={tot}", cell_type='label'))
        
        left_grid = [GridCell("") for _ in range(7)]
        prev_val_inner = None
        
        for pos in range(1, tot + 1):
             key = f'left_{pos}_totleft_{tot}'
             val = position_averages.get(key, None)
             
             if show_horizontal_factors:
                 val_idx = 6 - (pos - 1) * 2
             else:
                 val_idx = 3 - (pos - 1)
             
             # Value
             val_cell = GridCell("", value=val, cell_type='value')
             if val is not None: 
                 val_cell.text = f"{val:.3f}"
                 val_cell.value = float(val)
             else:
                 val_cell.text = "N/A"
             if val_idx >= 0 and val_idx < 7:
                 left_grid[val_idx] = val_cell
             
             # Factor (to the right of value)
             fac_idx = val_idx + 1
             if pos > 1 and show_horizontal_factors and fac_idx < 7:
                 fac_cell = GridCell("", cell_type='factor')
                 rich_segments = []
                 text_parts = []
                 
                 # 1. Factor
                 factor_val = None
                 if arrow_direction == 'rightwards':
                     if prev_val_inner is not None and val is not None and val != 0:
                         factor_val = prev_val_inner / val
                         f_str = f"×{factor_val:.2f}→"
                 else:
                     if prev_val_inner is not None and val is not None and prev_val_inner != 0:
                         factor_val = val / prev_val_inner
                         f_str = f"×{factor_val:.2f}←"
                         
                 if factor_val is not None:
                     f_color = COLOR_RED if factor_val < 1.0 else COLOR_GREY
                     rich_segments.append((f_str, f_color, True))
                     text_parts.append(f_str)

                 # 2. Triple
                 if show_ordering_triples and ordering_stats:
                     pair_idx = pos - 2
                     o_key = ('left', tot, pair_idx)
                     o_data = ordering_stats.get(o_key)
                     if o_data:
                        tot_count = o_data['lt'] + o_data['eq'] + o_data['gt']
                        if tot_count > 0:
                            lt = o_data['lt'] / tot_count * 100
                            eq = o_data['eq'] / tot_count * 100
                            gt = o_data['gt'] / tot_count * 100
                            
                            t_str_full = f"(<{lt:.0f}={eq:.0f}>{gt:.0f})"
                            text_parts.append(t_str_full)

                            if rich_segments:
                                rich_segments.append((" ", COLOR_GREY, False))
                                
                            prefix = f"(<{lt:.0f}={eq:.0f}>"
                            rich_segments.append((prefix, COLOR_GREY, False))
                            
                            gt_str = f"{gt:.0f}"
                            gt_color = COLOR_RED if gt > lt else COLOR_GREY
                            gt_bold = True if gt > lt else False
                            rich_segments.append((gt_str, gt_color, gt_bold))
                            
                            rich_segments.append((")", COLOR_GREY, False))

                 if text_parts:
                     fac_cell.text = " ".join(text_parts)
                     fac_cell.rich_text = rich_segments
                     
                 left_grid[fac_idx] = fac_cell
             
             prev_val_inner = val
             
        row_cells.extend(left_grid)
        row_cells.append(GridCell("V", cell_type='label'))
        
        # Row Average
        if show_row_averages:
             avg_key = f'average_totleft_{tot}'
             row_avg = position_averages.get(avg_key)
             if row_avg is not None:
                 row_cells.append(GridCell(f"[Avg: {row_avg:.3f}]", cell_type='comment'))
        
        rows.append(row_cells)

    return rows

def format_verb_centered_table(position_averages, 
                               show_horizontal_factors=False, 
                               show_diagonal_factors=False,
                               arrow_direction='diverging',
                               disorder_percentages=None,
                               ordering_stats=None,
                               show_ordering_triples=False,
                               show_row_averages=False,
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
    disorder_percentages : dict, optional
        Dictionary: (side, tot) -> percentage of disordered languages.
        If provided, adds disorder percentage to each row.
    ordering_stats : dict, optional
        Dictionary from get_ordering_stats with granular counts.
    show_ordering_triples : bool
        If True, replace horizontal factors with (lt, eq, gt) percentages.
        Requires ordering_stats.
    show_row_averages : bool
        If True, append average constituent size for the row.
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
    if show_ordering_triples:
        lines.append("WITH ORDERING TRIPLES ( < % | = % | > % )")
    lines.append("=" * 120)
    lines.append("")
    
    # Layout constants
    VAL_WIDTH = 8   
    FAC_WIDTH = 22 if show_ordering_triples else (12 if show_horizontal_factors else 0)
    
    # Header V
    HALF_WIDTH = 4 * VAL_WIDTH + 3 * FAC_WIDTH
    V_MARKER = f"{' ':>{HALF_WIDTH}}   V   {' ':>{HALF_WIDTH}}"
    lines.append(f"     {V_MARKER}") 

    E_VAL = " " * VAL_WIDTH
    E_FAC = " " * FAC_WIDTH
    LEFT_PAD = " " * HALF_WIDTH

    tsv_rows = []
    header_cols = ["Row", "L4", "F43", "L3", "F32", "L2", "F21", "L1", "V", "R1", "F12", "R2", "F23", "R3", "F34", "R4"]
    if show_row_averages:
        header_cols.append("RowAvg")
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
                fac_parts = []
                tsv_fac_parts = []
                
                # 1. Calculate Factor (Arrow)
                factor_val = None
                factor_str = ""
                
                # Check arrow direction logic first to get factor
                if arrow_direction == 'rightwards':
                     # Left to Right -->
                     if prev_val is not None and val is not None and val != 0:
                         factor_val = val / prev_val
                         factor_str = f"×{factor_val:.2f}→"
                else: 
                     # diverging (Right Side: L->R -> same as rightwards basically for R side)
                     # For Right side, diverging means V -> R1 -> R2. So Left-to-Right.
                     if prev_val is not None and val is not None and val != 0:
                         factor_val = val / prev_val
                         factor_str = f"×{factor_val:.2f}→"
                         
                if factor_str:
                     fac_parts.append(factor_str)
                     tsv_fac_parts.append(factor_str) # Use the string with symbols

                # 2. Ordering Triples logic
                if show_ordering_triples and ordering_stats:
                    pair_idx = pos - 2
                    o_key = ('right', tot, pair_idx)
                    o_data = ordering_stats.get(o_key)
                    
                    if o_data:
                        total = o_data['lt'] + o_data['eq'] + o_data['gt']
                        if total > 0:
                            lt = o_data['lt'] / total * 100
                            eq = o_data['eq'] / total * 100
                            gt = o_data['gt'] / total * 100
                            # Format: (<66=14>21)
                            trip_str = f"(<{lt:.0f}={eq:.0f}>{gt:.0f})"
                            fac_parts.append(trip_str)
                            tsv_fac_parts.append(f"(<{lt:.1f}={eq:.1f}>{gt:.1f})")
                
                # Combine
                if fac_parts:
                    final_fac_str = " ".join(fac_parts)
                    # Adjust width? Standard FAC_WIDTH might be too small (14).
                    # If both are present: "x1.32 -> 12<5=83>" is approx 18 chars.
                    # We might need to center it in a wider slot OR just let it take space?
                    # The function relies on fixed width formatting (center(FAC_WIDTH)).
                    # If text is longer than width, center() does nothing.
                    # This might break alignment if we don't increase FAC_WIDTH or handle total string construction differently.
                    # But Python formatting usually handles overflow by just pushing.
                    pass
                else:
                    final_fac_str = E_FAC.strip() # maintain emptiness if nothing
                
                # Update cells
                # If we output a very long string, it might shift dependent columns visually if we rely on simple concat.
                # However, cells are just joined: "".join(parts).
                # So alignment of diagonals (which are on next line) depends on FAC_WIDTH matching VAL_WIDTH etc.
                # If this row expands, diagonals won't match up unless we change global constants.
                # For now, let's just center it.
                parts.append(final_fac_str.center(max(FAC_WIDTH, len(final_fac_str))))
                tsv_right.append(" ".join(tsv_fac_parts))
            
            parts.append(val_str)
            tsv_right.append(tsv_val)
            prev_val = val
            
        right_str = "".join(parts)
        
        # Add disorder percentage if provided (legacy)
        suffix_str = ""
        if disorder_percentages is not None:
            disorder_pct = disorder_percentages.get(('right', tot))
            if disorder_pct is not None:
                suffix_str += f"  [unordered {disorder_pct:.1f}%]"
                
        # Add Row Average
        if show_row_averages:
            avg_key = f'average_totright_{tot}'
            row_avg = position_averages.get(avg_key)
            if row_avg is not None:
                suffix_str += f"  [Avg: {row_avg:.3f}]"
        
        lines.append(f"R tot={tot}: {LEFT_PAD}{right_str}{suffix_str}")
        
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
                 
                 fac_parts = []
                 tsv_fac_parts = []
                 
                 # 1. Calculate Factor (Arrow)
                 factor_val = None
                 factor_str = ""
                 
                 if arrow_direction == 'rightwards':
                     # Left to Right -->
                     if prev_val_inner is not None and val is not None and val != 0:
                         factor_val = prev_val_inner / val
                         factor_str = f"×{factor_val:.2f}→"
                 else: 
                     # diverging (Right to Left <--)
                     if prev_val_inner is not None and val is not None and prev_val_inner != 0:
                         factor_val = val / prev_val_inner
                         factor_str = f"×{factor_val:.2f}←"
                         
                 if factor_str:
                     fac_parts.append(factor_str)
                     tsv_fac_parts.append(factor_str) # Use the string with symbols

                 # 2. Ordering Triples logic
                 if show_ordering_triples and ordering_stats:
                     pair_idx = pos - 2
                     o_key = ('left', tot, pair_idx)
                     o_data = ordering_stats.get(o_key)
                     
                     if o_data:
                        total = o_data['lt'] + o_data['eq'] + o_data['gt']
                        if total > 0:
                            lt = o_data['lt'] / total * 100
                            eq = o_data['eq'] / total * 100
                            gt = o_data['gt'] / total * 100
                            # Format: 12< 5= 83>
                            trip_str = f"{lt:.0f}<{eq:.0f}={gt:.0f}>"
                            fac_parts.append(trip_str)
                            tsv_fac_parts.append(f"{lt:.1f}<|{eq:.1f}=|{gt:.1f}>")
                            
                 # Combine
                 if fac_parts:
                     final_fac_str = " ".join(fac_parts)
                 else:
                     final_fac_str = E_FAC.strip()

                 cells[fac_idx] = final_fac_str.center(max(FAC_WIDTH, len(final_fac_str)))
                 tsv_left[fac_idx] = " ".join(tsv_fac_parts)

             prev_val_inner = val
             
        left_str = "".join(cells)
        
        # Add disorder percentage if provided (legacy)
        suffix_str = ""
        if disorder_percentages is not None:
            disorder_pct = disorder_percentages.get(('left', tot))
            if disorder_pct is not None:
                suffix_str += f"  [unordered {disorder_pct:.1f}%]"
                
        # Add Row Average
        row_avg_str = ""
        if show_row_averages:
            avg_key = f'average_totleft_{tot}'
            row_avg = position_averages.get(avg_key)
            if row_avg is not None:
                suffix_str += f"  [Avg: {row_avg:.3f}]"
                row_avg_str = f"{row_avg:.3f}"
        
        # Add V
        lines.append(f"L tot={tot}: {left_str} V{suffix_str}")
        
        tsv_row = [f"L tot={tot}"] + tsv_left + ["V"] + [""]*7
        if show_row_averages:
            tsv_row.append(row_avg_str)
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


def save_excel_verb_centered_table(grid_rows, output_path):
    """
    Saves the grid to an Excel file with conditional formatting.
    """
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment, Color
        from openpyxl.utils import get_column_letter
        from openpyxl.cell.rich_text import CellRichText, TextBlock, InlineFont
    except ImportError:
        print("Error: openpyxl not installed. Cannot save Excel.")
        return

    wb = Workbook()
    ws = wb.active
    ws.title = "Verb Centered Analysis"

    # Styles
    bold_font = Font(bold=True)
    grey_font = Font(color="555555") 
    red_font = Font(color="FF0000", bold=True)
    
    # alignments
    center_align = Alignment(horizontal='center', vertical='center')
    left_align = Alignment(horizontal='left', vertical='center')

    for r_idx, row in enumerate(grid_rows, 1):
        for c_idx, cell in enumerate(row, 1):
            c = ws.cell(row=r_idx, column=c_idx)
            
            # 1. Content
            if cell.rich_text:
                # Construct CellRichText
                rt = CellRichText()
                for (text, color_hex, is_bold) in cell.rich_text:
                    # Convert to InlineFont
                    if_font = InlineFont(color=color_hex, b=is_bold)
                    rt.append(TextBlock(font=if_font, text=text))
                c.value = rt
            elif cell.value is not None:
                c.value = cell.value
                if isinstance(cell.value, (int, float)):
                    c.number_format = '0.000'
            else:
                c.value = cell.text
            
            # 2. Alignment
            if c_idx == 1:
                c.alignment = left_align
            else:
                c.alignment = center_align

            # 3. Base Font (if not RichText)
            # RichText overrides cell font for the parts, but base font might matter?
            # Actually RichText completely controls the content styling.
            if not cell.rich_text:
                if cell.cell_type == 'value':
                    c.font = bold_font
                elif cell.cell_type == 'factor':
                    # Fallback if logic failed or simple mode
                    if cell.is_astonishing: # Deprecated by RichText but keep for safety
                        c.font = red_font
                    else:
                        c.font = grey_font
                elif cell.cell_type == 'comment':
                    c.font = Font(italic=True, color="333333")
                elif cell.text == "V":
                    c.font = Font(bold=True, size=14)
            
    # Adjust column widths
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter 
        for cell in col:
            try:
                # Length of value str
                val_str = str(cell.value)
                if len(val_str) > max_length:
                    max_length = len(val_str)
            except:
                pass
        adjusted_width = (max_length + 2)
        # Cap width? Averages are small, factors are long.
        ws.column_dimensions[column].width = adjusted_width

    wb.save(output_path)
    # print(f"Saved Excel table to {output_path}")


def aggregate_ordering_stats(ordering_stats_dict):
    """
    Aggregates ordering statistics across multiple languages.
    """
    aggregated = {}
    for lang_stats in ordering_stats_dict.values():
        if not lang_stats: continue
        for key, counts in lang_stats.items():
            if key not in aggregated:
                aggregated[key] = {'lt': 0, 'eq': 0, 'gt': 0}
            aggregated[key]['lt'] += counts.get('lt', 0)
            aggregated[key]['eq'] += counts.get('eq', 0)
            aggregated[key]['gt'] += counts.get('gt', 0)
    return aggregated


def generate_mass_tables(all_langs_average_sizes, 
                         ordering_stats, 
                         metadata, 
                         vo_data=None, 
                         output_dir='data/tables'):
    """
    Generates text/TSV tables and Excel files.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    lang_names = metadata.get('langNames', {})
    
    # helper to process a subset of languages
    def process_subset(subset_langs, label, filename_label):
        if not subset_langs: return

        # Filter Data
        subset_avgs = {l: all_langs_average_sizes[l] for l in subset_langs if l in all_langs_average_sizes}
        subset_stats = {l: ordering_stats[l] for l in subset_langs if l in ordering_stats} if ordering_stats else None
        
        if not subset_avgs: return

        # Aggregate
        combined_avgs = compute_average_sizes_table(subset_avgs)
        combined_stats = aggregate_ordering_stats(subset_stats) if subset_stats else None
            
        # 1. Generate Standard TSV/Text
        filename_tsv = f"{filename_label}.tsv"
        format_verb_centered_table(
            combined_avgs,
            show_horizontal_factors=True,
            show_diagonal_factors=True,
            show_ordering_triples=True,
            show_row_averages=True,
            ordering_stats=combined_stats,
            arrow_direction='rightwards',
            save_tsv=True,
            output_dir=output_dir,
            filename=filename_tsv
        )
        
        # 2. Generate Excel with extracted grid
        grid = extract_verb_centered_grid(
            combined_avgs,
            show_horizontal_factors=True,
            show_diagonal_factors=True,
            arrow_direction='rightwards',
            ordering_stats=combined_stats,
            show_ordering_triples=True,
            show_row_averages=True
        )
        filename_xlsx = f"{filename_label}.xlsx"
        save_excel_verb_centered_table(grid, os.path.join(output_dir, filename_xlsx))

    print(f"Generating tables in {output_dir}...")
    
    all_langs = list(all_langs_average_sizes.keys())
    
    # Global
    process_subset(all_langs, "All Languages", "Table_All_Languages")
    
    # Individual
    for lang in all_langs:
        name = lang_names.get(lang, lang).replace(" ", "_").replace("/", "-")
        process_subset([lang], f"Language {name}", f"Table_Language_{name}_{lang}")
        
    # Families (IE / Non-IE)
    # Re-using previous logic but simpler iteration
    ie_langs = []
    non_ie_langs = []
    langnameGroup = metadata.get('langnameGroup', {})
    for lang in all_langs:
        name = lang_names.get(lang, lang)
        group = langnameGroup.get(name, 'Unknown')
        if group == 'Indo-European': ie_langs.append(lang)
        else: non_ie_langs.append(lang)
            
    process_subset(ie_langs, "Indo-European", "Table_Family_IndoEuropean")
    process_subset(non_ie_langs, "Non-Indo-European", "Table_Family_NonIndoEuropean")
    
    # Order
    if vo_data:
        vo_langs = []
        ov_langs = []
        ndo_langs = []
        for lang in all_langs:
            info = vo_data.get(lang)
            if info:
                vtype = info.get('vo_type')
                if not vtype and 'vo_score' in info:
                     score = info['vo_score']
                     if score is not None:
                         if score > 0.666: vtype = 'VO'
                         elif score < 0.333: vtype = 'OV'
                         else: vtype = 'NDO'
                if vtype == 'VO': vo_langs.append(lang)
                elif vtype == 'OV': ov_langs.append(lang)
                elif vtype == 'NDO': ndo_langs.append(lang)
        
        process_subset(vo_langs, "VO Languages", "Table_Order_VO")
        process_subset(ov_langs, "OV Languages", "Table_Order_OV")
        process_subset(ndo_langs, "NDO Languages", "Table_Order_NDO")
        
    print(f"Mass table generation complete. Output in: {output_dir}")

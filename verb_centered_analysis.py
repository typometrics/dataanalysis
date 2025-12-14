
import numpy as np

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
    
    # Generate Header Row
    header_row = [GridCell("Row", cell_type='label')]
    
    # Left Headers (Fixed 7 slots in data logic)
    l_headers = [GridCell("") for _ in range(7)]
    if show_horizontal_factors:
         # Logic matches loop: 6 - (pos-1)*2.
         # Pos 4 (L4): 0. Pos 3 (L3): 2. Pos 2 (L2): 4. Pos 1 (L1): 6.
         for pos in [4, 3, 2, 1]:
             idx = 6 - (pos - 1) * 2
             if 0 <= idx < 7:
                 l_headers[idx] = GridCell(f"L{pos}", cell_type='label')
    else:
         # Logic matches loop: 3 - (pos - 1).
         # Pos 4: 0. Pos 1: 3.
         for pos in [4, 3, 2, 1]:
             idx = 3 - (pos - 1)
             if 0 <= idx < 7:
                 l_headers[idx] = GridCell(f"L{pos}", cell_type='label')
                 
    header_row.extend(l_headers)
    header_row.append(GridCell("V", cell_type='label'))
    
    # Right Headers (Max Tot 4)
    for pos in range(1, 5):
        header_row.append(GridCell(f"R{pos}", cell_type='label'))
        if pos < 4 and show_horizontal_factors:
            header_row.append(GridCell("", cell_type='factor'))
            
    if show_row_averages:
        header_row.append(GridCell("[Avg | N | Slope]", cell_type='comment'))
    
    rows.append(header_row)
    
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
             
        if show_row_averages:
             avg_key = f'average_totright_{tot}'
             row_avg = position_averages.get(avg_key)
             comment_str = ""
             if row_avg is not None:
                 comment_str = f"[Avg: {row_avg:.3f}]"
             
             # Add N if available
             if ordering_stats:
                 # Try new explicit total
                 t_key = ('right', tot, 'total')
                 n_count = ordering_stats.get(t_key)
                 
                 # Fallback to pair sum if total not found (legacy data)
                 if n_count is None and tot >= 2:
                     o_key = ('right', tot, 0)
                     o_data = ordering_stats.get(o_key)
                     if o_data:
                         n_count = o_data['lt'] + o_data['eq'] + o_data['gt']
                 
                 if n_count is not None:
                     comment_str += f" [N={n_count}]"

             # Add Slope (Tot >= 2)
             if tot >= 2:
                 y_vals = []
                 valid_slope = True
                 for pos in range(1, tot + 1):
                     k = f'right_{pos}_totright_{tot}'
                     v = position_averages.get(k)
                     if v is None: 
                         valid_slope = False
                         break
                     y_vals.append(v)
                 
                 if valid_slope and len(y_vals) == tot:
                     # Regress y against x=0..tot-1
                     try:
                         slope, _ = np.polyfit(np.arange(tot), y_vals, 1)
                         comment_str += f" [Slope: {slope:+.2f}]"
                     except:
                         pass

             if comment_str:
                 # Pad the row to ensure comment is in the last column
                 # Expected Right Side width is 7 cells (Val, Fac, Val, Fac, Val, Fac, Val).
                 # Current cells added in loop approx: (tot vals + (tot-1) factors) if factors on.
                 # Actually, let's just count.
                 # row_cells has: Label(1) + Empty(7) + V(1) + [Data].
                 # We want [Data] to be length 7.
                 # Then append comment.
                 current_len = len(row_cells)
                 # Target length before comment: 1 + 7 + 1 + 7 = 16.
                 needed = 16 - current_len
                 if needed > 0:
                     for _ in range(needed):
                         row_cells.append(GridCell(""))
                         
                 row_cells.append(GridCell(comment_str, cell_type='comment'))
                 
                 # Ensure we didn't overshoot (unlikely with loop logic but safe to check)
                 # Actually if show_horizontal_factors=False, width is less.
                 # But Header assumes max width?
                 # Header generation uses check.
                 # If show_horizontal_factors=False, Max R cols is 4.
                 # My Header Generation makes 4 cols + 3 empty factors if False? No.
                 # Header generation: `if pos < 4 and show_horizontal_factors: append factor`.
                 # So if False, Header R-block is 4 cells.
                 # Target length: 1 + 7 + 1 + 4 = 13.
                 # If True, Target: 1 + 7 + 1 + 7 = 16.
                 
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
    # 1.5. XVX Configuration (L1 V R1)
    # ---------------------------------------------------------
    l_xvx = position_averages.get('xvx_left_1')
    r_xvx = position_averages.get('xvx_right_1')
    
    if l_xvx is not None or r_xvx is not None:
        row_cells = []
        row_cells.append(GridCell("X V X", cell_type='label'))
        
        # Left Grid: L1 is at index 6 (last slot)
        left_grid = [GridCell("") for _ in range(7)]
        if l_xvx is not None:
            left_grid[6] = GridCell(f"{l_xvx:.3f}", value=float(l_xvx), cell_type='value')
        else:
            left_grid[6] = GridCell("N/A", value=None)
            
        row_cells.extend(left_grid)
        row_cells.append(GridCell("V", cell_type='label'))
        
        # Right Grid: R1 is at first slot?
        # My header for Right is R1, F, R2...
        # So R1 is appended immediately.
        if r_xvx is not None:
             row_cells.append(GridCell(f"{r_xvx:.3f}", value=float(r_xvx), cell_type='value'))
        else:
             row_cells.append(GridCell("N/A", value=None))
        
        # Factor L1 -> R1 (Cross-verb)
        if show_horizontal_factors and l_xvx and r_xvx and l_xvx != 0:
            fac_cell = GridCell("", cell_type='factor')
            rich_segments = []
            text_parts = []
            
            # Factor
            factor_val = r_xvx / l_xvx
            # Arrow: L -> R (across verb) is V-crossing. 
            # If diverging: L->L is <--, R->R is -->.
            # L->R is -->.
            f_str = f"×{factor_val:.2f}→"
            f_color = COLOR_RED if factor_val < 1.0 else COLOR_GREY
            rich_segments.append((f_str, f_color, True))
            text_parts.append(f_str)
            
            # Ordering Stats
            if show_ordering_triples and ordering_stats:
                o_key = ('xvx', 2, 0) # L1 vs R1 pair
                o_data = ordering_stats.get(o_key)
                if o_data:
                    tot_count = o_data['lt'] + o_data['eq'] + o_data['gt']
                    if tot_count > 0:
                        lt = o_data['lt'] / tot_count * 100
                        eq = o_data['eq'] / tot_count * 100
                        gt = o_data['gt'] / tot_count * 100
                        trip_str = f"(<{lt:.0f}={eq:.0f}>{gt:.0f})"
                        text_parts.append(trip_str)
                        
                        if rich_segments: rich_segments.append((" ", COLOR_GREY, False))
                        rich_segments.append((f"(<{lt:.0f}={eq:.0f}>", COLOR_GREY, False))
                        gt_color = COLOR_RED if gt > lt else COLOR_GREY
                        gt_bold = True if gt > lt else False
                        rich_segments.append((f"{gt:.0f}", gt_color, gt_bold))
                        rich_segments.append((")", COLOR_GREY, False))
                        
            if text_parts:
                fac_cell.text = " ".join(text_parts)
                fac_cell.rich_text = rich_segments
                row_cells.append(fac_cell)
            else:
                row_cells.append(GridCell(""))
        else:
            if show_horizontal_factors:
                row_cells.append(GridCell(""))
        
        # Padding for rest of Right Side
        # Total Right side cells target: 7.
        # We added R1 (1) + Fac (1). Total 2.
        # Need 5 more.
        # If fac didn't add (False), we added 1. Need 3? (4 total if no fac).
        current_data_len = len(row_cells) - (1 + 7 + 1) # Label, LeftGrid, V
        target = 7 if show_horizontal_factors else 4
        while current_data_len < target:
            row_cells.append(GridCell(""))
            current_data_len += 1
            
        # Comment: N / Slope
        comment_str = ""
        # N
        if ordering_stats:
             n_key = ('xvx', 2, 'total')
             n_val = ordering_stats.get(n_key)
             # Fallback sum
             if n_val is None:
                  o_key = ('xvx', 2, 0)
                  d = ordering_stats.get(o_key)
                  if d: n_val = d['lt'] + d['eq'] + d['gt']
             
             if n_val is not None:
                  comment_str += f" [N={n_val}]"
        
        # Slope? L1 and R1.
        # x coordinates: L1 at -1? R1 at +1?
        # Or visual 1, 2? L1->1, R1->2?
        # "Slope" usually implies dependent vs position.
        # Here we have L1 and R1. 
        # Maybe slope L1->R1? (y2-y1)/(x2-x1).
        # Diff = R1 - L1.
        # If displayed as slope, sure.
        if l_xvx is not None and r_xvx is not None:
             slope = r_xvx - l_xvx # Change over 1 unit? Or 2? 
             # L1 is pos 1 Left. R1 is pos 1 Right.
             # Distance? 
             # Let's maybe skip Slope for XVX unless requested.
             pass

        if comment_str:
             row_cells.append(GridCell(comment_str, cell_type='comment'))
        
        rows.append(row_cells)
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
                     pair_idx = tot - pos
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
             comment_str = ""
             if row_avg is not None:
                 comment_str = f"[Avg: {row_avg:.3f}]"
             
             # Add N if available
             if ordering_stats:
                 t_key = ('left', tot, 'total')
                 n_count = ordering_stats.get(t_key)
                 
                 if n_count is None and tot >= 2:
                     o_key = ('left', tot, 0)
                     o_data = ordering_stats.get(o_key)
                     if o_data:
                         n_count = o_data['lt'] + o_data['eq'] + o_data['gt']
                 
                 if n_count is not None:
                     comment_str += f" [N={n_count}]"
                     
             # Add Slope (Tot >= 2)
             if tot >= 2:
                 y_vals = []
                 valid_slope = True
                 # Visual Order: Outer (L_tot) -> Inner (L1)
                 # Keys are left_{pos}_... where pos 1 is L1.
                 # So iterate pos from tot down to 1.
                 for pos in range(tot, 0, -1):
                     k = f'left_{pos}_totleft_{tot}'
                     v = position_averages.get(k)
                     if v is None: 
                         valid_slope = False
                         break
                     y_vals.append(v)
                     
                 if valid_slope and len(y_vals) == tot:
                     try:
                         slope, _ = np.polyfit(np.arange(tot), y_vals, 1)
                         comment_str += f" [Slope: {slope:+.2f}]"
                     except:
                         pass
                     
        # Left Rows need padding for the Right side gap
        # 1. Label (1) - already added
        # 2. LeftGrid (7) - already added/extended
        # 3. V (1) - already added
        
        # 4. Right Side Padding. 
        #    If factors: 7 cells. If no factors: 4 cells.
        r_pad_len = 7 if show_horizontal_factors else 4
        for _ in range(r_pad_len):
            row_cells.append(GridCell(""))
             
        # 5. Comment (Avg | N | Slope)
        if comment_str:
             row_cells.append(GridCell(comment_str, cell_type='comment'))
        
        rows.append(row_cells)
        
        # Diagonals (Left)
        # Logic matches print function: diagonals between Tot and Tot+1
        if tot < 4 and show_diagonal_factors and show_horizontal_factors:
            diag_row = [GridCell(f"Diag L{tot}-{tot+1}", cell_type='label')]
            diag_grid = [GridCell("") for _ in range(7)]
            
            for pos in range(1, tot + 1):
                tgt_key = f'left_{pos}_totleft_{tot}'
                src_key = f'left_{pos+1}_totleft_{tot+1}'
                tgt_val = position_averages.get(tgt_key)
                src_val = position_averages.get(src_key)
                
                if pos + 1 > 4: continue
                
                # Slot left of pos. 
                # pos 1 (L1) is at index 6. Slot left is 5.
                # pos 2 (L2) is at index 4. Slot left is 3.
                # Formula: (6 - (pos - 1) * 2) - 1
                fac_idx = (6 - (pos - 1) * 2) - 1
                
                if src_val and tgt_val:
                    factor = tgt_val / src_val
                    diag_str = f"×{factor:.2f} ↗"
                    
                    diag_cell = GridCell(diag_str, cell_type='factor')
                    d_color = COLOR_RED if factor < 1.0 else COLOR_GREY
                    diag_cell.rich_text = [(diag_str, d_color, True)]
                    
                    if 0 <= fac_idx < 7:
                        diag_grid[fac_idx] = diag_cell
                        
            diag_row.extend(diag_grid)
            diag_row.append(GridCell("")) # V column
            rows.append(diag_row)

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
    E_VAL = " " * VAL_WIDTH
    E_FAC = " " * FAC_WIDTH
    HALF_WIDTH = 4 * VAL_WIDTH + 3 * FAC_WIDTH
    LEFT_PAD = " " * HALF_WIDTH
    
    # Header V
    HALF_WIDTH = 4 * VAL_WIDTH + 3 * FAC_WIDTH
    
    # Text Header Row
    # Ident matching "R tot=X: " (9 chars)
    header_parts = [" " * 9]
    
    # Left Headers (L4 .. L1)
    l_headers = []
    for i in range(4, 0, -1):
        l_headers.append(f"L{i}".center(VAL_WIDTH))
        if i > 1 and (show_horizontal_factors or show_diagonal_factors):
            # Use FAC_WIDTH spaces or a label if desired
            l_headers.append(E_FAC)
    header_parts.append("".join(l_headers))
    
    # Center V
    header_parts.append(" V ") # Matches ' V ' (3 chars) approx logic
     # Actually data rows use ' V' (2 chars) near R side or ' V' near L side.
     # L-rows: left_str + ' V'.
     # R-rows: LEFT_PAD + ' V' + right_str_content.
    
    # Right Headers (R1 .. R4)
    r_headers = []
    for i in range(1, 5):
        r_headers.append(f"R{i}".center(VAL_WIDTH))
        if i < 4 and (show_horizontal_factors or show_diagonal_factors):
            r_headers.append(E_FAC)
    header_parts.append("".join(r_headers))
    
    if show_row_averages:
        header_parts.append("  [Avg | N | Slope]")
        
    lines.append("".join(header_parts)) 



    tsv_rows = []
    header_cols = ["Row", "L4", "F43", "L3", "F32", "L2", "F21", "L1", "V", "R1", "F12", "R2", "F23", "R3", "F34", "R4"]
    if show_row_averages:
        header_cols.append("Stats") # Avg | N | Slope
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
        row_avg = None # Initialize for scope
        if show_row_averages:
            avg_key = f'average_totright_{tot}'
            row_avg = position_averages.get(avg_key)
            if row_avg is not None:
                suffix_str += f"  [Avg: {row_avg:.3f}]"
        
        # Add N if available
        n_count = None # Initialize for scope
        # Add N if available
        n_count = None # Initialize for scope
        if ordering_stats:
             t_key = ('right', tot, 'total')
             n_count = ordering_stats.get(t_key)
             
             if n_count is None and tot >= 2:
                 o_key = ('right', tot, 0)
                 o_data = ordering_stats.get(o_key)
                 if o_data:
                     n_count = o_data['lt'] + o_data['eq'] + o_data['gt']
        
        if n_count is not None:
             suffix_str += f" [N={n_count}]"
        
        # Add Slope
        slope_val = None # Initialize for scope
        if tot >= 2:
             y_vals = []
             valid = True
             for pos in range(1, tot + 1):
                 v = position_averages.get(f'right_{pos}_totright_{tot}')
                 if v is None: valid=False; break
                 y_vals.append(v)
             if valid:
                 try:
                     slope_val, _ = np.polyfit(np.arange(tot), y_vals, 1)
                     suffix_str += f" [Slope: {slope_val:+.2f}]"
                 except: pass

        # Pad right_str to fixed width
        # Width: ' V' (2) + HALF_WIDTH (content)
        target_width = 2 + HALF_WIDTH
        right_str = right_str.ljust(target_width)
        
        lines.append(f"R tot={tot}: {LEFT_PAD}{right_str}{suffix_str}")
        
        # Build TSV Row
        # Left side empty for R rows
        row_label = f"R tot={tot}"
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
        while len(tsv_right) < 8: # Pad R columns 
            tsv_right.append("")
            
        full_tsv_row = [row_label] + left_empty + tsv_right
        if show_row_averages:
            stats_parts = []
            if row_avg is not None:
                stats_parts.append(f"[Avg: {row_avg:.3f}]")
            if n_count is not None:
                stats_parts.append(f"[N={n_count}]")
            if slope_val is not None:
                stats_parts.append(f"[Slope: {slope_val:+.2f}]")
            full_tsv_row.append(" ".join(stats_parts))
        
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
    # 1.5. XVX Configuration
    # ---------------------------------------------------------
    lx = position_averages.get('xvx_left_1')
    rx = position_averages.get('xvx_right_1')
    
    if lx is not None or rx is not None:
         # Text output
         # Layout: "X V X :   ...  L1  V  R1  ..."
         # Left Grid: L1 is at inner most slot (fac=6 if factors, 3 if not)
         # Wait, L1 index logic: 
         # Factors=True: L1->6.
         # Factors=False: L1->3.
         
         l_cells_x = [" " * VAL_WIDTH] * (7 if show_horizontal_factors else 4)
         # Fill L1
         idx_l1 = 6 if show_horizontal_factors else 3
         l_str_val = f"{lx:>{VAL_WIDTH}.3f}" if lx is not None else "N/A".center(VAL_WIDTH)
         l_cells_x[idx_l1] = l_str_val
         
         # Left String
         left_str_x = ""
         # We need to intersperse factors if needed (empty)
         # Actually l_cells_x slots encompass factors?
         # "Left Grid" logic (Lines 803) uses [""] * 7.
         # Factor slots are 1, 3, 5. Values 0, 2, 4, 6.
         # So L1 is at 6.
         # Factors are empty.
         # BUT `l_headers` construction uses explicit spacing.
         # Let's reconstruct consistent string.
         
         # If factors: [Val, Fac, Val, Fac, Val, Fac, Val]
         # L1 is last Val (Idx 6).
         # Previous are empty.
         full_l_cells = []
         for i in range(7):
             if i == 6 and lx is not None:
                 full_l_cells.append(l_str_val)
             else:
                 full_l_cells.append(E_VAL if i%2==0 else E_FAC)
         
         left_str_x = "".join(full_l_cells)
         
         # Right Part
         # V + R1 + Factor
         right_parts_x = [" V"]
         
         r_str_val = f"{rx:>{VAL_WIDTH}.3f}" if rx is not None else "N/A".center(VAL_WIDTH)
         right_parts_x.append(r_str_val)
         
         # Factor L1 -> R1
         fac_str_x = ""
         if show_horizontal_factors and lx and rx and lx!=0:
             fv = rx / lx
             arrow = "→"
             f_txt = f"×{fv:.2f}{arrow}"
             
             # Ordering
             trip_txt = ""
             if show_ordering_triples and ordering_stats:
                 d = ordering_stats.get(('xvx', 2, 0))
                 if d:
                    tot = d['lt']+d['eq']+d['gt']
                    if tot>0:
                        trip_txt = f"(<{d['lt']/tot*100:.0f}={d['eq']/tot*100:.0f}>{d['gt']/tot*100:.0f})"
             
             comb = f"{f_txt} {trip_txt}".strip() if trip_txt else f_txt
             fac_str_x = comb.center(max(FAC_WIDTH, len(comb)))
             right_parts_x.append(fac_str_x)
         else:
             if show_horizontal_factors:
                 right_parts_x.append(E_FAC)
         
         # Stats
         suffix_x = ""
         if ordering_stats:
             nx = ordering_stats.get(('xvx', 2, 'total'))
             if nx is None:
                 ox = ordering_stats.get(('xvx', 2, 0))
                 if ox: nx = ox['lt']+ox['eq']+ox['gt']
             if nx is not None:
                 suffix_x = f" [N={nx}]"
                 
         final_right_x = "".join(right_parts_x)
         # Pad
         t_w = 2 + HALF_WIDTH
         final_right_x = final_right_x.ljust(t_w)
         
         lines.append(f"X V X : {left_str_x}{final_right_x}{suffix_x}")
         lines.append("-" * 120)

         # TSV
         # L cols: 7. L1 at end.
         tsv_l_x = [""]*6 + [f"{lx:.3f}" if lx else ""]
         tsv_r_x = [f"{rx:.3f}" if rx else ""]
         # Right needs 7 cols (R1...R4). We gave R1.
         # Fac L1->R1?
         # Where does it go? Standard R cols: R1, F12, R2...
         # This factor L->R is strictly "F_L1_R1" or similar.
         # Does not fit F12 slot.
         # Maybe put in F12 slot? (Slot 1 in right list).
         # R1 is slot 0.
         if fac_str_x:
              # Clean format?
              # Use simplified logic.
              tsv_r_x.append(fac_str_x.strip()) 
         else:
              tsv_r_x.append("")
         
         while len(tsv_r_x) < 8: tsv_r_x.append("")
         
         tsv_row_x = ["X V X"] + tsv_l_x + ["V"] + tsv_r_x
         if show_row_averages and suffix_x:
             tsv_row_x.append(suffix_x.strip())
         else:
             if show_row_averages: tsv_row_x.append("")
             
         tsv_rows.append(tsv_row_x)
         tsv_rows.append(["separator"])

    # ---------------------------------------------------------
    # 2. Left Dependents
    # ---------------------------------------------------------
    for tot in [1, 2, 3, 4]:
        # 2a. Print Current Row Values
        # TSV Left Row
        tsv_left = [""] * 7
        
        row_cells_text = [] # For text output
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
                     # Fix: For Left side, neighbors in "L(pos) -> L(pos-1)" visual order
                     # correspond to list indices (tot-pos) and (tot-pos+1).
                     # pair_idx in ordering_stats matches the first element's index in the sorted list.
                     # List is [L_k ... L_1] (visual left-to-right).
                     # At pos (displaying L_pos, factor between L_pos and L_{pos-1}), 
                     # we want the pair (L_pos, L_{pos-1}).
                     # L_pos corresponds to index (tot - pos).
                     pair_idx = tot - pos
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
        row_avg = None # Initialize for scope
        if show_row_averages:
            avg_key = f'average_totleft_{tot}'
            row_avg = position_averages.get(avg_key)
            if row_avg is not None:
                suffix_str += f"  [Avg: {row_avg:.3f}]"
        
        # Add N
        n_count = None # Initialize for scope
        # Add N
        n_count = None # Initialize for scope
        if ordering_stats:
             t_key = ('left', tot, 'total')
             n_count = ordering_stats.get(t_key)
             
             if n_count is None and tot >= 2:
                 o_key = ('left', tot, 0)
                 o_data = ordering_stats.get(o_key)
                 if o_data:
                     n_count = o_data['lt'] + o_data['eq'] + o_data['gt']
                     
        if n_count is not None:
             suffix_str += f" [N={n_count}]"
                
        # Add Slope
        slope_val = None # Initialize for scope
        if tot >= 2:
             y_vals = []
             valid = True
             # Visual order: tot down to 1
             for pos in range(tot, 0, -1):
                 v = position_averages.get(f'left_{pos}_totleft_{tot}')
                 if v is None: valid=False; break
                 y_vals.append(v)
             if valid:
                 try:
                     slope_val, _ = np.polyfit(np.arange(tot), y_vals, 1)
                     suffix_str += f" [Slope: {slope_val:+.2f}]"
                 except: pass

        # Add V and Pad Right side
        # To align Avg column with R-rows (which end at 2*HALF_WIDTH + 2 + suffix)
        # L-row currently: left_str (HALF) + ' V' (2). Total HALF+2.
        # Need padding eq to HALF.
        right_pad = " " * HALF_WIDTH
        lines.append(f"L tot={tot}: {left_str} V{right_pad}{suffix_str}")
        
        tsv_row = [f"L tot={tot}"] + tsv_left + ["V"] + [""]*7
        
        # Append Stats to TSV
        if show_row_averages:
            stats_parts = []
            if row_avg is not None:
                stats_parts.append(f"[Avg: {row_avg:.3f}]")
            if n_count is not None:
                stats_parts.append(f"[N={n_count}]")
            if slope_val is not None:
                stats_parts.append(f"[Slope: {slope_val:+.2f}]")
            
            if stats_parts:
                tsv_row.append(" ".join(stats_parts))
            else:
                tsv_row.append("") # Empty stats if shown but none found
        
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
            if isinstance(counts, int):
                # Aggregate totals
                if key not in aggregated:
                    aggregated[key] = 0
                aggregated[key] += counts
            else:
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

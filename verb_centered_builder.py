"""
Unified table builder for verb-centered constituent size analysis.

This module brings together all components to build the complete table structure.
"""

import numpy as np
from typing import Dict, Optional, List
from verb_centered_model import CellData, TableConfig, TableStructure
from verb_centered_computations import (
    MarginalMeansCalculator, FactorCalculator, OrderingStatsFormatter
)
from verb_centered_layout import TableLayout


# Color constants
COLOR_RED = "FF0000"
COLOR_GREY = "555555"
COLOR_DARK = "000000"
COLOR_BLUE = "0000FF"
COLOR_ORANGE = "FFA500"


class VerbCenteredTableBuilder:
    """
    Unified table builder using composition of specialized components.
    """
    
    def __init__(self,
                 position_averages: Dict[str, float],
                 config: TableConfig,
                 ordering_stats: Optional[Dict] = None,
                 validation_info: Optional[Dict] = None):
        """
        Initialize the table builder.
        
        Args:
            position_averages: Dictionary of average sizes and factors
            config: Table configuration
            ordering_stats: Optional ordering statistics for triples
            validation_info: Optional statistical validation info (sample counts, warnings)
        """
        self.position_averages = position_averages
        self.config = config
        self.layout = TableLayout(config)
        self.marginals = MarginalMeansCalculator(position_averages, config)
        self.factors = FactorCalculator(position_averages, config)
        self.ordering = OrderingStatsFormatter(ordering_stats) if ordering_stats else None
        self.validation_info = validation_info
    
    def build(self) -> TableStructure:
        """
        Build the complete table structure.
        
        Returns:
            TableStructure with all rows populated
        """
        table = TableStructure(self.config)
        
        # Build in order
        table.add_row(self._build_header_row())
        
        if self.config.show_marginal_means:
            table.rows.extend(self._build_right_marginal_rows())
            table.add_separator()
        
        table.rows.extend(self._build_right_data_rows())
        table.add_separator()
        
        # X V X row in the middle
        table.rows.append(self._build_xvx_row())
        table.add_separator()
        
        table.rows.extend(self._build_left_data_rows())
        
        if self.config.show_marginal_means:
            table.add_separator()
            table.rows.extend(self._build_left_marginal_rows())
            
            # Add aggregate ordering triple row for left side (first pairs)
            if self.config.show_ordering_triples and self.ordering:
                agg_row = self._build_left_aggregate_ordering_row()
                if agg_row:
                    table.rows.append(agg_row)
        

        
        # Add Validation Footer
        validation_footer = self._build_validation_footer()
        if validation_footer:
            table.add_separator()
            table.rows.extend(validation_footer)
        
        return table
    
    def _create_empty_row(self) -> List[CellData]:
        """Create a row with empty cells."""
        return [CellData() for _ in range(self.layout.total_columns)]
    
    def _create_value_cell(self, value: Optional[float]) -> CellData:
        """Create a formatted value cell."""
        if value is None or (isinstance(value, float) and np.isnan(value)):
            return CellData(text="N/A", cell_type='value')
        return CellData(
            value=float(value),
            text=f"{value:.3f}",
            cell_type='value'
        )
    
    def _build_header_row(self) -> List[CellData]:
        """Build header row with column labels."""
        row = self._create_empty_row()
        
        # Label column
        row[self.layout.label_col_idx] = CellData(text="Row", cell_type='label')
        
        # Left headers (L4 ... L1)
        for pos in range(4, 0, -1):
            idx = self.layout.get_left_column_index(pos)
            row[idx] = CellData(text=f"L{pos}", cell_type='label')
        
        # V column
        row[self.layout.v_col_idx] = CellData(text="V", cell_type='label')
        
        # Right headers (R1 ... R4)
        for pos in range(1, 5):
            idx = self.layout.get_right_column_index(pos)
            row[idx] = CellData(text=f"R{pos}", cell_type='label')
        
        # Comment header
        if self.config.show_row_averages:
            row[self.layout.comment_col_idx] = CellData(text="[GM | N | Slope]", cell_type='comment')
        
        return row
    
    def _build_right_marginal_rows(self) -> List[List[CellData]]:
        """Build right-side marginal mean rows (M Vert and M Diag)."""
        rows = []
        
        # M Vert Row
        v_row = self._create_empty_row()
        v_row[self.layout.label_col_idx] = CellData(
            text="M Vert Right",
            cell_type='label',
            rich_segments=[("M Vert Right", COLOR_BLUE, True)]
        )
        
        v_sizes = self.marginals.calc_vertical_size_means_right()
        v_h_facs, v_d_facs = self.marginals.calc_vertical_factor_means_right()
        
        # Place size values
        for pos in range(1, 5):
            gm = v_sizes.get(pos)
            if gm is not None:
                idx = self.layout.get_right_column_index(pos)
                txt = f"{gm:.3f}"
                v_row[idx] = CellData(
                    value=float(gm),
                    text=txt,
                    cell_type='value',
                    rich_segments=[(txt, COLOR_BLUE, True)]
                )
        
        # Place horizontal factors
        if self.config.show_horizontal_factors:
            for pos in range(1, 4):
                h_gm = v_h_facs.get(pos)
                if h_gm is not None:
                    idx = self.layout.get_right_column_index(pos + 1, is_factor=True)
                    arrow = self.config.get_arrow_symbol('right', 'horizontal')
                    txt = f"×{h_gm:.2f}{arrow}"
                    v_row[idx] = CellData(
                        text=txt,
                        cell_type='factor',
                        rich_segments=[(txt, COLOR_BLUE, False)]
                    )
        
        rows.append(v_row)
        
        # M Diag Right Row  
        if self.config.show_diagonal_factors:
            d_row = self._create_empty_row()
            d_row[self.layout.label_col_idx] = CellData(
                text="M Diag Right",
                cell_type='label',
                rich_segments=[("M Diag Right", COLOR_ORANGE, True)]
            )
            
            diagonals = self.marginals.calc_diagonal_means_right()
            
            # M Diag Right shows 3 cells: R2, R3, R4
            # Each cell contains: size value followed by factor (in same visual cell, different columns)
            # diag_idx 0 is longest diagonal (R4 positions), 2 is shortest (R2 positions)
            # Display order: diag 2 (R2), diag 1 (R3), diag 0 (R4) to match ascending positions
            diag_to_pos = {2: 2, 1: 3, 0: 4}  # diag_idx -> position number
            
            for diag_idx in [2, 1, 0]:  # Process in display order
                sz_gm, fac_gm = diagonals.get(diag_idx, (None, None))
                pos = diag_to_pos[diag_idx]
                
                if sz_gm is not None:
                    # Place size in value column (R2, R3, or R4)
                    val_idx = self.layout.get_right_column_index(pos)
                    txt_size = f"{sz_gm:.2f}"
                    d_row[val_idx] = CellData(
                        text=txt_size,
                        cell_type='value',
                        rich_segments=[(txt_size, COLOR_ORANGE, False)]
                    )
                    
                    # Place factor adjacent to the value
                    # For R2: factor goes in F23 (after R2)
                    # For R3: factor goes in F34 (after R3, before R4)
                    # For R4: factor goes in extra column (after R4)
                    if fac_gm is not None and self.config.show_horizontal_factors:
                        if pos < 4:
                            # Factor goes in next position's factor column
                            fac_idx = self.layout.get_right_column_index(pos + 1, is_factor=True)
                        else:
                            # For R4, use the extra column after right columns
                            fac_idx = self.layout.extra_col_idx
                        
                        arrow = self.config.get_arrow_symbol('right', 'diagonal')
                        txt_fac = f"×{fac_gm:.2f}{arrow}"
                        d_row[fac_idx] = CellData(
                            text=txt_fac,
                            cell_type='factor',
                            rich_segments=[(txt_fac, COLOR_ORANGE, False)]
                        )
            
            rows.append(d_row)
        
        # Add aggregate ordering triple row for right side (last pairs)
        if self.config.show_ordering_triples and self.ordering:
            agg_row = self._build_right_aggregate_ordering_row()
            if agg_row:
                rows.append(agg_row)
        
        return rows
    
    def _build_right_data_rows(self) -> List[List[CellData]]:
        """Build all right-side data rows."""
        rows = []
        for tot in [4, 3, 2, 1]:
            rows.append(self._build_right_row(tot))
            if self.config.show_diagonal_factors and tot > 1:
                rows.append(self._build_right_diagonal_row(tot))
        return rows
    
    def _build_right_row(self, tot: int) -> List[CellData]:
        """Build a single right-side row."""
        row = self._create_empty_row()
        
        # Label
        row[self.layout.label_col_idx] = CellData(text=f"R tot={tot}", cell_type='label')
        
        # V column
        row[self.layout.v_col_idx] = CellData(text="V", cell_type='label')
        
        # Data columns
        prev_val = None
        for pos in range(1, tot + 1):
            # Get value
            key = f'right_{pos}_totright_{tot}'
            value = self.position_averages.get(key)
            
            # Place value
            val_idx = self.layout.get_right_column_index(pos)
            row[val_idx] = self._create_value_cell(value)
            
            # Place factor if needed
            if pos > 1 and self.config.show_horizontal_factors:
                fac_idx = self.layout.get_right_column_index(pos, is_factor=True)
                row[fac_idx] = self._create_factor_cell('right', pos, tot, prev_val)
            
            prev_val = value
        
        # Add comment if needed
        if self.config.show_row_averages:
            row[self.layout.comment_col_idx] = self._create_comment_cell('right', tot)
        
        return row
    
    def _build_right_diagonal_row(self, tot: int) -> List[CellData]:
        """Build a diagonal row for right side."""
        row = self._create_empty_row()
        
        row[self.layout.label_col_idx] = CellData(text=f"Diag R{tot}-{tot-1}", cell_type='label')
        
        if self.config.show_horizontal_factors:
            for pos in range(1, tot):
                factor = self.factors.get_diagonal_factor('right', pos, tot)
                if factor:
                    fac_idx = self.layout.get_right_column_index(pos + 1, is_factor=True)
                    arrow = self.config.get_arrow_symbol('right', 'diagonal')
                    txt = f"×{factor.value:.2f}{arrow}"
                    color = COLOR_RED if factor.value < 1.0 else COLOR_GREY
                    row[fac_idx] = CellData(
                        text=txt,
                        cell_type='factor',
                        rich_segments=[(txt, color, True)]
                    )
        
        return row
    
    def _build_left_marginal_rows(self) -> List[List[CellData]]:
        """Build left-side marginal mean rows (M Diag and M Vert)."""
        rows = []
        
        # M Diag Row (left)
        if self.config.show_diagonal_factors:
            d_row = self._create_empty_row()
            d_row[self.layout.label_col_idx] = CellData(
                text="M Diag Left",
                cell_type='label',
                rich_segments=[("M Diag Left", COLOR_ORANGE, True)]
            )
            
            diagonals = self.marginals.calc_diagonal_means_left()
            
            # M Diag Left shows 3 cells: L4, L3, L2 (symmetric to M Diag Right showing R2, R3, R4)
            # Display pattern: factor, size, factor, size, factor, size
            # For L4: factor in mirror column (BEFORE L4), size in L4
            # For L3: factor in F43 (BEFORE L3), size in L3
            # For L2: factor in F32 (BEFORE L2), size in L2
            # diag_idx 0 (longest) -> L4 position
            # diag_idx 1 (medium) -> L3 position  
            # diag_idx 2 (shortest) -> L2 position
            for diag_idx in range(3):
                sz_gm, fac_gm = diagonals.get(diag_idx, (None, None))
                
                if sz_gm is not None:
                    # Place size in value column (L4, L3, or L2)
                    pos = 4 - diag_idx  # diag_idx 0->pos 4, 1->pos 3, 2->pos 2
                    val_idx = self.layout.get_left_column_index(pos)
                    txt_size = f"{sz_gm:.2f}"
                    d_row[val_idx] = CellData(
                        text=txt_size,
                        cell_type='value',
                        rich_segments=[(txt_size, COLOR_ORANGE, False)]
                    )
                    
                    # Place factor BEFORE the value
                    # For L4: factor goes in mirror column (BEFORE L4)
                    # For L3: factor goes in F43 (BEFORE L3, between L4 and L3)
                    # For L2: factor goes in F32 (BEFORE L2, between L3 and L2)
                    if fac_gm is not None and self.config.show_horizontal_factors:
                        if pos == 4:
                            # For L4 (leftmost), place factor in mirror column
                            fac_idx = self.layout.mirror_col_idx
                        else:
                            # For L3 and L2, factor goes BEFORE: use pos+1 to get F43 for L3, F32 for L2
                            fac_idx = self.layout.get_left_column_index(pos + 1, is_factor=True)
                        
                        arrow = self.config.get_arrow_symbol('left', 'diagonal')
                        txt_fac = f"×{fac_gm:.2f}{arrow}"
                        d_row[fac_idx] = CellData(
                            text=txt_fac,
                            cell_type='factor',
                            rich_segments=[(txt_fac, COLOR_ORANGE, False)]
                        )
            
            rows.append(d_row)
        
        # M Vert Row (left)
        v_row = self._create_empty_row()
        v_row[self.layout.label_col_idx] = CellData(
            text="M Vert Left",
            cell_type='label',
            rich_segments=[("M Vert Left", COLOR_BLUE, True)]
        )
        
        v_sizes = self.marginals.calc_vertical_size_means_left()
        
        # Place size values
        for pos in range(1, 5):
            gm = v_sizes.get(pos)
            if gm is not None:
                idx = self.layout.get_left_column_index(pos)
                txt = f"{gm:.3f}"
                v_row[idx] = CellData(
                    value=float(gm),
                    text=txt,
                    cell_type='value',
                    rich_segments=[(txt, COLOR_BLUE, True)]
                )
        
        # Calculate and place horizontal factors from size values
        # For left side display (L4, L3, L2, L1), factors show growth in visual direction (L to R)
        # Factors are placed between consecutive positions: F43 between L4 and L3, F32 between L3 and L2, F21 between L2 and L1
        if self.config.show_horizontal_factors:
            # For each factor column, compute growth from left value to right value
            # Factor in F43 (column for pos=4) shows L3/L4 growth
            # Factor in F32 (column for pos=3) shows L2/L3 growth
            # Factor in F21 (column for pos=2) shows L1/L2 growth
            for pos in range(2, 5):  # pos 2, 3, 4
                # Get values on either side of this factor column
                # Factor column for pos N is between L_N and L_(N-1) visually
                gm_left = v_sizes.get(pos)  # Farther from V (left side of factor)
                gm_right = v_sizes.get(pos - 1)  # Closer to V (right side of factor)
                
                if gm_left is not None and gm_right is not None and gm_left > 0:
                    # Factor showing growth from left to right visually
                    h_gm = gm_right / gm_left
                    idx = self.layout.get_left_column_index(pos, is_factor=True)
                    arrow = self.config.get_arrow_symbol('left', 'horizontal')
                    txt = f"×{h_gm:.2f}{arrow}"
                    v_row[idx] = CellData(
                        text=txt,
                        cell_type='factor',
                        rich_segments=[(txt, COLOR_BLUE, False)]
                    )
        
        rows.append(v_row)
        
        return rows
    
    def _build_left_data_rows(self) -> List[List[CellData]]:
        """Build all left-side data rows (in reverse order: 1, 2, 3, 4)."""
        rows = []
        for tot in [1, 2, 3, 4]:
            if self.config.show_diagonal_factors and tot > 1:
                rows.append(self._build_left_diagonal_row(tot))
            rows.append(self._build_left_row(tot))
        return rows
    
    def _build_left_row(self, tot: int) -> List[CellData]:
        """Build a single left-side row."""
        row = self._create_empty_row()
        
        # Label
        row[self.layout.label_col_idx] = CellData(text=f"L tot={tot}", cell_type='label')
        
        # V column
        row[self.layout.v_col_idx] = CellData(text="V", cell_type='label')
        
        # Data columns (reverse order: 4, 3, 2, 1)
        prev_val = None
        for pos in range(tot, 0, -1):
            # Get value
            key = f'left_{pos}_totleft_{tot}'
            value = self.position_averages.get(key)
            
            # Place value
            val_idx = self.layout.get_left_column_index(pos)
            row[val_idx] = self._create_value_cell(value)
            
            # Place factor if needed (between pos and pos-1, so skip when pos==1)
            if pos < tot and self.config.show_horizontal_factors:
                # Factor connects pos+1 to pos
                fac_idx = self.layout.get_left_column_index(pos + 1, is_factor=True)
                row[fac_idx] = self._create_factor_cell('left', pos + 1, tot, value)
            
            prev_val = value
        
        # Add comment if needed
        if self.config.show_row_averages:
            row[self.layout.comment_col_idx] = self._create_comment_cell('left', tot)
        
        return row
    
    def _build_left_diagonal_row(self, tot: int) -> List[CellData]:
        """Build a diagonal row for left side."""
        row = self._create_empty_row()
        
        row[self.layout.label_col_idx] = CellData(text=f"Diag L{tot}-{tot-1}", cell_type='label')
        
        if self.config.show_horizontal_factors:
            for pos in range(tot, 1, -1):
                factor = self.factors.get_diagonal_factor('left', pos - 1, tot - 1)
                if factor:
                    fac_idx = self.layout.get_left_column_index(pos, is_factor=True)
                    arrow = self.config.get_arrow_symbol('left', 'diagonal')
                    txt = f"×{factor.value:.2f}{arrow}"
                    color = COLOR_RED if factor.value < 1.0 else COLOR_GREY
                    
                    # Don't add ordering triples to diagonal factors (only horizontal factors should have them)
                    row[fac_idx] = CellData(
                        text=txt,
                        cell_type='factor',
                        rich_segments=[(txt, color, True)]
                    )
        
        return row
    
    def _build_xvx_row(self) -> List[CellData]:
        """Build XVX (cross-verb) row comparing L1 to R1."""
        row = self._create_empty_row()
        
        # Label
        row[self.layout.label_col_idx] = CellData(text="X V X", cell_type='label')
        
        # V column
        row[self.layout.v_col_idx] = CellData(text="V", cell_type='label')
        
        # L1 value
        l_xvx = self.position_averages.get('xvx_left_1')
        l_idx = self.layout.get_left_column_index(1)
        row[l_idx] = self._create_value_cell(l_xvx)
        
        # R1 value
        r_xvx = self.position_averages.get('xvx_right_1')
        r_idx = self.layout.get_right_column_index(1)
        row[r_idx] = self._create_value_cell(r_xvx)
        
        # Factor (if enabled) - direction depends on arrow_direction setting
        if self.config.show_horizontal_factors and l_xvx and r_xvx:
            factor = self.factors.get_xvx_factor()
            if factor:
                # Determine direction based on arrow_direction
                # For left_to_right or diverging: L1 → R1 (factor between L1 and V)
                # For right_to_left or inward: R1 → L1 (factor between V and R1)
                
                if self.config.arrow_direction in ['left_to_right', 'diverging', 'outward']:
                    # Factor goes between L1 and V (in the factor column after L1)
                    fac_idx = self.layout.get_left_column_index(1, is_factor=True)
                    # Determine if we're moving inward or outward
                    if self.config.arrow_direction == 'left_to_right':
                        arrow = '→'  # L1 → V, moving right
                    elif self.config.arrow_direction == 'outward':
                        arrow = '→'  # XVX is always Left-to-Right (Request: "XVX line should always remain left to right")
                    else:  # diverging
                        arrow = '→'  # Legacy diverging? Or should this also be ←? Kept for safety.
                else:  # right_to_left or inward/converging
                    # Factor goes between V and R1
                    fac_idx = self.layout.get_right_column_index(1, is_factor=True)
                    if self.config.arrow_direction == 'right_to_left':
                        arrow = '←'  # V ← R1, moving left
                    else:  # inward/converging
                        arrow = '←'  # Moving inward to V perspective means ← for right side
                
                segments = []
                txt = f"×{factor.value:.2f}{arrow}"
                color = COLOR_RED if factor.value < 1.0 else COLOR_GREY
                segments.append((txt, color, True))
                
                # Add ordering triple if available
                if self.config.show_ordering_triples and self.ordering:
                    triple = self.ordering.get_xvx_triple()
                    if triple:
                        lt, eq, gt = triple
                        segments.append((f" (<{lt:.0f}={eq:.0f}>", COLOR_GREY, False))
                        gt_color = COLOR_RED if gt > lt else COLOR_GREY
                        segments.append((f"{gt:.0f})", gt_color, gt > lt))
                
                row[fac_idx] = CellData(
                    text="".join(seg[0] for seg in segments),
                    cell_type='factor',
                    rich_segments=segments
                )
        
        return row
    
    def _create_factor_cell(self, side: str, pos: int, tot: int, prev_val: Optional[float] = None) -> CellData:
        """Create a factor cell with optional ordering triple."""
        segments = []
        
        # Get factor
        factor = self.factors.get_horizontal_factor(side, pos, tot, prev_val)
        if factor:
            arrow = self.config.get_arrow_symbol(side, 'horizontal')
            txt = f"×{factor.value:.2f}{arrow}"
            color = COLOR_RED if factor.value < 1.0 else COLOR_GREY
            segments.append((txt, color, True))
        
        # Add ordering triple if enabled
        if self.config.show_ordering_triples and self.ordering:
            # For both sides: pos=2 uses pair_idx=0, pos=3 uses pair_idx=1, pos=4 uses pair_idx=2
            # This is because pos represents the "right" position in each factor (closer to V)
            pair_idx = pos - 2
            triple = self.ordering.get_triple(side, tot, pair_idx)
            if triple:
                lt, eq, gt = triple
                segments.append((f" (<{lt:.0f}={eq:.0f}>", COLOR_GREY, False))
                gt_color = COLOR_RED if gt > lt else COLOR_GREY
                segments.append((f"{gt:.0f})", gt_color, gt > lt))
        
        return CellData(
            text="".join(seg[0] for seg in segments),
            cell_type='factor',
            rich_segments=segments if segments else None
        )
    
    def _create_comment_cell(self, side: str, tot: int) -> CellData:
        """Create a comment cell with GM, N, and Slope."""
        parts = []
        
        # Average GM
        avg_key = f'average_tot{side}_{tot}'
        row_avg = self.position_averages.get(avg_key)
        if row_avg is not None:
            parts.append(f"GM: {row_avg:.3f}")
            
        # Global GM (Sentence Average)
        avg_global_key = f'average_global_tot{side}_{tot}'
        row_avg_global = self.position_averages.get(avg_global_key)
        if row_avg_global is not None:
            # Only show if different from GM (or maybe always show for consistency? User said "these... would be the same")
            # If standard table, they are same. If anyotherside, different.
            # Showing both verifies consistency for standard tables.
            # But let's check floating point equality just in case to avoid visual clutter?
            # User request: "these two numbers would then be the same... is it possible to have both information"
            # Implies they want to see it.
            parts.append(f"Global: {row_avg_global:.3f}")
        
        # N count
        if self.ordering:
            n_count = self.ordering.get_row_total(side, tot)
            if n_count is not None:
                parts.append(f"N={n_count}")
        
        # Slope (for tot >= 2)
        if tot >= 2:
            y_vals = []
            for pos in range(1, tot + 1):
                k = f'{side}_{pos}_tot{side}_{tot}'
                v = self.position_averages.get(k)
                if v is not None:
                    y_vals.append(v)
            
            if len(y_vals) == tot:
                try:
                    # For left side, reverse to get slope from L1→L2→L3→L4 (left to right)
                    # For right side, keep as is for R1→R2→R3→R4 (left to right)
                    if side == 'left':
                        y_vals_ordered = list(reversed(y_vals))
                    else:
                        y_vals_ordered = y_vals
                    slope, _ = np.polyfit(np.arange(tot), y_vals_ordered, 1)
                    parts.append(f"Slope: {slope:+.2f}")
                except:
                    pass
        
        comment_str = " | ".join(parts) if parts else ""
        return CellData(text=f"[{comment_str}]", cell_type='comment')
    
    def _build_right_aggregate_ordering_row(self) -> Optional[List[CellData]]:
        """Build aggregate ordering row for right side last pairs."""
        result = self.ordering.get_aggregate_right_last_pair_triple()
        if not result:
            return None
        
        lt_pct, eq_pct, gt_pct, total_n = result
        
        row = self._create_empty_row()
        row[self.layout.label_col_idx] = CellData(
            text="Agg R Last→",
            cell_type='label',
            rich_segments=[("Agg R Last→", COLOR_GREY, False)]
        )
        
        # Display the triple in the comment column
        if self.config.show_row_averages:
            triple_txt = f"[(<{lt_pct:.1f}={eq_pct:.1f}>{gt_pct:.1f}) N={total_n}]"
            row[self.layout.comment_col_idx] = CellData(
                text=triple_txt,
                cell_type='comment',
                rich_segments=[(triple_txt, COLOR_GREY, False)]
            )
        
        return row
    
    def _build_left_aggregate_ordering_row(self) -> Optional[List[CellData]]:
        """Build aggregate ordering row for left side first pairs."""
        result = self.ordering.get_aggregate_left_first_pair_triple()
        if not result:
            return None
        
        lt_pct, eq_pct, gt_pct, total_n = result
        
        row = self._create_empty_row()
        row[self.layout.label_col_idx] = CellData(
            text="Agg L First→",
            cell_type='label',
            rich_segments=[("Agg L First→", COLOR_GREY, False)]
        )
        
        # Display the triple in the comment column
        if self.config.show_row_averages:
            triple_txt = f"[(<{lt_pct:.1f}={eq_pct:.1f}>{gt_pct:.1f}) N={total_n}]"
            row[self.layout.comment_col_idx] = CellData(
                text=triple_txt,
                cell_type='comment',
                rich_segments=[(triple_txt, COLOR_GREY, False)]
            )
        
        return row
    
    def _build_validation_footer(self) -> List[List[CellData]]:
        """Build statistical validation footer rows."""
        rows = []
        
        if not self.validation_info:
            return rows
        
        min_threshold = self.validation_info.get('min_threshold', 5)
        low_sample_positions = self.validation_info.get('low_sample_positions', [])
        low_sample_factors = self.validation_info.get('low_sample_factors', [])
        
        # Row 1: Low-sample positions warning (if any)
        if low_sample_positions:
            row1 = self._create_empty_row()
            row1[self.layout.label_col_idx] = CellData(
                text="⚠️ Low n positions",
                cell_type='comment',
                rich_segments=[("⚠️ Low n positions", COLOR_ORANGE, False)]
            )
            examples = ', '.join(f'{k}(n={n})' for k, n in low_sample_positions[:5])
            warning_text = f"{len(low_sample_positions)} position(s) with <{min_threshold} samples. Examples: {examples}"
            row1[self.layout.v_col_idx] = CellData(
                text=warning_text,
                cell_type='comment',
                rich_segments=[(warning_text, COLOR_ORANGE, False)]
            )
            rows.append(row1)
        
        # Row 2: Low-sample factors warning (if any)
        if low_sample_factors:
            row2 = self._create_empty_row()
            row2[self.layout.label_col_idx] = CellData(
                text="⚠️ Low n factors",
                cell_type='comment',
                rich_segments=[("⚠️ Low n factors", COLOR_ORANGE, False)]
            )
            examples = ', '.join(f"{k.replace('factor_', '')}(n={n})" for k, n in low_sample_factors[:5])
            warning_text = f"{len(low_sample_factors)} factor(s) with <{min_threshold} samples. Examples: {examples}"
            row2[self.layout.v_col_idx] = CellData(
                text=warning_text,
                cell_type='comment',
                rich_segments=[(warning_text, COLOR_ORANGE, False)]
            )
            rows.append(row2)
        
        return rows


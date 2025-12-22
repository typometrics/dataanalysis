"""
Computation logic for verb-centered constituent size analysis.

This module handles all numerical calculations including geometric means,
growth factors, and ordering statistics.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from verb_centered_model import FactorData, TableConfig


def calc_geometric_mean(values: List[float]) -> Optional[float]:
    """
    Calculate geometric mean of a list of values.
    
    Args:
        values: List of positive values
        
    Returns:
        Geometric mean or None if no valid values
    """
    valid_vals = [v for v in values if v is not None and v > 0]
    if not valid_vals:
        return None
    return np.exp(np.mean(np.log(valid_vals)))


class MarginalMeansCalculator:
    """
    Calculates marginal means (vertical and diagonal) for the helix table.
    """
    
    def __init__(self, position_averages: Dict[str, float]):
        """
        Initialize calculator.
        
        Args:
            position_averages: Dictionary of position keys to average sizes/factors
        """
        self.position_averages = position_averages
    
    def calc_vertical_size_means_right(self) -> Dict[int, Optional[float]]:
        """
        Calculate vertical size means for right side (by position).
        
        For each position, calculates GM across all tot values.
        Example: R2 mean = GM(R2@tot=2, R2@tot=3, R2@tot=4)
        
        Returns:
            Dict mapping position (1-4) to geometric mean
        """
        means = {}
        for pos in range(1, 5):
            keys = [f'right_{pos}_totright_{tot}' for tot in range(pos, 5)]
            values = [self.position_averages.get(k) for k in keys]
            means[pos] = calc_geometric_mean(values)
        return means
    
    def calc_vertical_factor_means_right(self) -> Tuple[Dict[int, Optional[float]], Dict[int, Optional[float]]]:
        """
        Calculate vertical factor means for right side.
        
        Returns:
            Tuple of (horizontal_factors, diagonal_factors) dicts
        """
        h_means = {}
        d_means = {}
        
        for pos in range(1, 4):  # pos 1-3 (factors between pos and pos+1)
            # Horizontal factors: R_{pos+1}/R_pos for each tot
            h_keys = []
            for tot in range(pos + 1, 5):
                k_b = f'right_{pos+1}_totright_{tot}'
                k_a = f'right_{pos}_totright_{tot}'
                h_keys.append(f'factor_{k_b}_vs_{k_a}')
            h_values = [self.position_averages.get(k) for k in h_keys]
            h_means[pos] = calc_geometric_mean(h_values)
            
            # Diagonal factors: R_{pos+1}@tot / R_pos@(tot-1)
            d_keys = []
            for tot in range(pos + 1, 5):
                k_b = f'right_{pos+1}_totright_{tot}'
                k_a = f'right_{pos}_totright_{tot-1}'
                d_keys.append(f'factor_{k_b}_vs_{k_a}')
            d_values = [self.position_averages.get(k) for k in d_keys]
            d_means[pos] = calc_geometric_mean(d_values)
        
        return h_means, d_means
    
    def calc_diagonal_means_right(self) -> Dict[int, Tuple[Optional[float], Optional[float]]]:
        """
        Calculate diagonal means for right side.
        
        Diagonals:
        - 0 (Longest): R1T1 → R2T2 → R3T3 → R4T4
        - 1 (Medium): R1T2 → R2T3 → R3T4
        - 2 (Short): R1T3 → R2T4
        
        Returns:
            Dict mapping diagonal index to (size_gm, factor_gm)
        """
        diagonals = {}
        
        # Diagonal 0 (Longest, k=0): R1T1..R4T4
        keys_sz = [f'right_{u}_totright_{u}' for u in range(1, 5)]
        values_sz = [self.position_averages.get(k) for k in keys_sz]
        sz_gm = calc_geometric_mean(values_sz)
        
        # Calculate factor from individual diagonal values
        if sz_gm is not None and len([v for v in values_sz if v is not None]) >= 2:
            # Get the consecutive ratios
            ratios = []
            for i in range(len(values_sz) - 1):
                if values_sz[i] is not None and values_sz[i+1] is not None:
                    ratios.append(values_sz[i+1] / values_sz[i])
            fac_gm = calc_geometric_mean(ratios) if ratios else None
        else:
            fac_gm = None
            
        diagonals[0] = (sz_gm, fac_gm)
        
        # Diagonal 1 (Medium, k=1): R1T2..R3T4
        keys_sz = [f'right_{u}_totright_{u+1}' for u in range(1, 4)]
        values_sz = [self.position_averages.get(k) for k in keys_sz]
        sz_gm = calc_geometric_mean(values_sz)
        
        if sz_gm is not None and len([v for v in values_sz if v is not None]) >= 2:
            ratios = []
            for i in range(len(values_sz) - 1):
                if values_sz[i] is not None and values_sz[i+1] is not None:
                    ratios.append(values_sz[i+1] / values_sz[i])
            fac_gm = calc_geometric_mean(ratios) if ratios else None
        else:
            fac_gm = None
            
        diagonals[1] = (sz_gm, fac_gm)
        
        # Diagonal 2 (Short, k=2): R1T3..R2T4
        keys_sz = [f'right_{u}_totright_{u+2}' for u in range(1, 3)]
        values_sz = [self.position_averages.get(k) for k in keys_sz]
        sz_gm = calc_geometric_mean(values_sz)
        
        if sz_gm is not None and len([v for v in values_sz if v is not None]) >= 2:
            ratios = []
            for i in range(len(values_sz) - 1):
                if values_sz[i] is not None and values_sz[i+1] is not None:
                    ratios.append(values_sz[i+1] / values_sz[i])
            fac_gm = calc_geometric_mean(ratios) if ratios else None
        else:
            fac_gm = None
            
        diagonals[2] = (sz_gm, fac_gm)
        
        return diagonals
    
    def calc_vertical_size_means_left(self) -> Dict[int, Optional[float]]:
        """Calculate vertical size means for left side."""
        means = {}
        for pos in range(1, 5):
            keys = [f'left_{pos}_totleft_{tot}' for tot in range(pos, 5)]
            values = [self.position_averages.get(k) for k in keys]
            means[pos] = calc_geometric_mean(values)
        return means
    
    def calc_vertical_factor_means_left(self) -> Tuple[Dict[int, Optional[float]], Dict[int, Optional[float]]]:
        """Calculate vertical factor means for left side."""
        h_means = {}
        d_means = {}
        
        for pos in range(2, 5):  # pos 2-4
            # Horizontal factors: L_pos / L_{pos-1}
            h_keys = []
            for tot in range(pos, 5):
                h_keys.append(f'factor_left_{pos}_totleft_{tot}_vs_left_{pos-1}_totleft_{tot}')
            h_values = [self.position_averages.get(k) for k in h_keys]
            h_means[pos] = calc_geometric_mean(h_values)
            
            # Diagonal factors: L_{pos-1}@tot / L_pos@(tot+1)
            # Note: diagonal goes from higher tot to lower tot on left side
            if pos < 4:
                k_b = f'left_{pos-1}_totleft_{pos-1}'
                k_a = f'left_{pos}_totleft_{pos}'
                d_val = self.position_averages.get(f'factor_{k_b}_vs_{k_a}')
                d_means[pos] = d_val
        
        return h_means, d_means
    
    def calc_diagonal_means_left(self) -> Dict[int, Tuple[Optional[float], Optional[float]]]:
        """Calculate diagonal means for left side."""
        diagonals = {}
        
        # Diagonal 0 (Longest): L1T1..L4T4
        keys_sz = [f'left_{u}_totleft_{u}' for u in range(1, 5)]
        values_sz = [self.position_averages.get(k) for k in keys_sz]
        sz_gm = calc_geometric_mean(values_sz)
        
        # Calculate factor from individual diagonal values
        # For left side, invert ratios since visual direction is L4→L3→L2→L1 (reversed)
        if sz_gm is not None and len([v for v in values_sz if v is not None]) >= 2:
            # Get the consecutive ratios in REVERSE direction for left side
            ratios = []
            for i in range(len(values_sz) - 1):
                if values_sz[i] is not None and values_sz[i+1] is not None:
                    # Invert ratio: val[i] / val[i+1] instead of val[i+1] / val[i]
                    ratios.append(values_sz[i] / values_sz[i+1])
            fac_gm = calc_geometric_mean(ratios) if ratios else None
        else:
            fac_gm = None
            
        diagonals[0] = (sz_gm, fac_gm)
        
        # Diagonal 1 (Medium): L1T2..L3T4
        keys_sz = [f'left_{u}_totleft_{u+1}' for u in range(1, 4)]
        values_sz = [self.position_averages.get(k) for k in keys_sz]
        sz_gm = calc_geometric_mean(values_sz)
        
        if sz_gm is not None and len([v for v in values_sz if v is not None]) >= 2:
            ratios = []
            for i in range(len(values_sz) - 1):
                if values_sz[i] is not None and values_sz[i+1] is not None:
                    # Invert ratio for left side
                    ratios.append(values_sz[i] / values_sz[i+1])
            fac_gm = calc_geometric_mean(ratios) if ratios else None
        else:
            fac_gm = None
            
        diagonals[1] = (sz_gm, fac_gm)
        
        # Diagonal 2 (Short): L1T3..L2T4
        keys_sz = [f'left_{u}_totleft_{u+2}' for u in range(1, 3)]
        values_sz = [self.position_averages.get(k) for k in keys_sz]
        sz_gm = calc_geometric_mean(values_sz)
        
        if sz_gm is not None and len([v for v in values_sz if v is not None]) >= 2:
            ratios = []
            for i in range(len(values_sz) - 1):
                if values_sz[i] is not None and values_sz[i+1] is not None:
                    # Invert ratio for left side
                    ratios.append(values_sz[i] / values_sz[i+1])
            fac_gm = calc_geometric_mean(ratios) if ratios else None
        else:
            fac_gm = None
            
        diagonals[2] = (sz_gm, fac_gm)
        
        return diagonals


class FactorCalculator:
    """
    Calculates growth factors between positions.
    """
    
    def __init__(self, position_averages: Dict[str, float], config: TableConfig):
        """
        Initialize calculator.
        
        Args:
            position_averages: Dictionary of position keys to values
            config: Table configuration (for arrow direction)
        """
        self.position_averages = position_averages
        self.config = config
    
    def get_horizontal_factor(self, side: str, pos: int, tot: int, prev_val: Optional[float] = None) -> Optional[FactorData]:
        """
        Calculate horizontal factor between pos and pos-1.
        
        Args:
            side: 'left' or 'right'
            pos: Current position (2-4)
            tot: Total dependents
            prev_val: Optional previous position value for fallback calculation
            
        Returns:
            FactorData or None if cannot be calculated
        """
        if pos < 2:
            return None
        
        # Build keys
        key_b = f'{side}_{pos}_tot{side}_{tot}'
        key_a = f'{side}_{pos-1}_tot{side}_{tot}'
        fac_key = f'factor_{key_b}_vs_{key_a}'
        
        # Try to get precomputed factor
        geo_factor = self.position_averages.get(fac_key)
        
        if geo_factor is not None:
            factor_val = geo_factor
        else:
            # Fallback: compute from values
            val_b = self.position_averages.get(key_b)
            val_a = self.position_averages.get(key_a)
            if val_a is None:
                val_a = prev_val
            
            if val_a is None or val_b is None or val_a == 0:
                return None
            
            factor_val = val_b / val_a
        
        # Apply direction adjustment
        is_outward = self.config.get_growth_direction(side) == 'outward'
        if not is_outward and factor_val != 0:
            factor_val = 1.0 / factor_val
        
        return FactorData(
            value=factor_val,
            source_key=key_a,
            target_key=key_b,
            arrow_type='horizontal',
            side=side
        )
    
    def get_diagonal_factor(self, side: str, pos: int, tot: int) -> Optional[FactorData]:
        """
        Calculate diagonal factor.
        
        For right: R_{pos+1}@tot / R_pos@(tot-1) (going up-right)
        For left: L_pos@(tot-1) / L_{pos+1}@tot (going up-right, from lower-left to upper-right)
        
        Args:
            side: 'left' or 'right'
            pos: Position for diagonal base
            tot: Total for diagonal base
            
        Returns:
            FactorData or None
        """
        if side == 'right':
            if pos >= tot or tot < 2:
                return None
            key_b = f'right_{pos+1}_totright_{tot}'
            key_a = f'right_{pos}_totright_{tot-1}'
        else:  # left
            if pos >= 4 or tot >= 4:
                return None
            # For left diagonal: we want to go from lower-left to upper-right
            # From L_{pos+1} in tot+1 (lower) TO L_pos in tot (upper)
            # Example: Diag L2-1 goes from L2@tot=2 (lower) to L1@tot=1 (upper)
            key_a = f'left_{pos+1}_totleft_{tot+1}'  # Source (lower-left)
            key_b = f'left_{pos}_totleft_{tot}'       # Target (upper-right)
        
        fac_key = f'factor_{key_b}_vs_{key_a}'
        geo_factor = self.position_averages.get(fac_key)
        
        if geo_factor is None:
            # Try to compute from values
            val_b = self.position_averages.get(key_b)
            val_a = self.position_averages.get(key_a)
            if val_a is None or val_b is None or val_a == 0:
                return None
            # Diagonal always goes upward, so we compute growth factor as target/source
            geo_factor = val_b / val_a
        
        # For diagonal factors, we DON'T apply direction adjustment
        # Diagonal always shows the growth going up-right regardless of arrow_direction setting
        factor_val = geo_factor
        
        return FactorData(
            value=factor_val,
            source_key=key_a,
            target_key=key_b,
            arrow_type='diagonal',
            side=side
        )
    
    def get_xvx_factor(self) -> Optional[FactorData]:
        """
        Calculate cross-verb factor (R1 / L1).
        
        Returns:
            FactorData or None
        """
        key_b = 'xvx_right_1'
        key_a = 'xvx_left_1'
        fac_key = f'factor_{key_b}_vs_{key_a}'
        
        geo_factor = self.position_averages.get(fac_key)
        
        if geo_factor is None:
            val_b = self.position_averages.get(key_b)
            val_a = self.position_averages.get(key_a)
            if val_a is None or val_b is None or val_a == 0:
                return None
            geo_factor = val_b / val_a
        
        # XVX is treated as outward (left to right)
        is_outward = self.config.get_growth_direction('right') == 'outward'
        factor_val = geo_factor if is_outward else (1.0 / geo_factor if geo_factor != 0 else 1.0)
        
        return FactorData(
            value=factor_val,
            source_key=key_a,
            target_key=key_b,
            arrow_type='horizontal',
            side='xvx'
        )


class OrderingStatsFormatter:
    """
    Formats ordering statistics (triples: <, =, > percentages).
    """
    
    def __init__(self, ordering_stats: Optional[Dict] = None):
        """
        Initialize formatter.
        
        Args:
            ordering_stats: Dictionary of ordering statistics
        """
        self.ordering_stats = ordering_stats or {}
    
    def get_triple(self, side: str, tot: int, pair_idx: int) -> Optional[Tuple[float, float, float]]:
        """
        Get ordering triple (lt%, eq%, gt%) for a position pair.
        
        Args:
            side: 'left' or 'right'
            tot: Total dependents
            pair_idx: Pair index (0 = first pair)
            
        Returns:
            Tuple of (lt%, eq%, gt%) or None
        """
        if not self.ordering_stats:
            return None
        
        o_key = (side, tot, pair_idx)
        o_data = self.ordering_stats.get(o_key)
        
        if not o_data:
            return None
        
        total = o_data.get('lt', 0) + o_data.get('eq', 0) + o_data.get('gt', 0)
        if total == 0:
            return None
        
        lt = o_data['lt'] / total * 100
        eq = o_data['eq'] / total * 100
        gt = o_data['gt'] / total * 100
        
        return (lt, eq, gt)
    
    def get_xvx_triple(self) -> Optional[Tuple[float, float, float]]:
        """Get ordering triple for XVX (L1 vs R1)."""
        return self.get_triple('xvx', 2, 0)
    
    def get_row_total(self, side: str, tot: int) -> Optional[int]:
        """
        Get total count for a row configuration.
        
        Args:
            side: 'left' or 'right'
            tot: Total dependents
            
        Returns:
            Total count or None
        """
        # Try explicit total key
        t_key = (side, tot, 'total')
        n_count = self.ordering_stats.get(t_key)
        
        if n_count is not None:
            return n_count
        
        # Fallback: sum from first pair
        if tot >= 2:
            o_key = (side, tot, 0)
            o_data = self.ordering_stats.get(o_key)
            if o_data:
                return o_data.get('lt', 0) + o_data.get('eq', 0) + o_data.get('gt', 0)
        
        return None
    
    def get_aggregate_right_last_pair_triple(self) -> Optional[Tuple[float, float, float, int]]:
        """
        Get weighted aggregate triple for right side "second-to-last toward last" pairs.
        
        Aggregates across R tot=2,3,4 the comparisons of R(tot-1) vs R(tot):
        - R tot=2: R1 vs R2 (pair_idx=0)
        - R tot=3: R2 vs R3 (pair_idx=1)
        - R tot=4: R3 vs R4 (pair_idx=2)
        
        Returns:
            Tuple of (lt%, eq%, gt%, total_N) or None
        """
        if not self.ordering_stats:
            return None
        
        total_lt = 0
        total_eq = 0
        total_gt = 0
        
        for tot in [2, 3, 4]:
            pair_idx = tot - 2  # Last pair in each configuration
            o_key = ('right', tot, pair_idx)
            o_data = self.ordering_stats.get(o_key)
            
            if o_data:
                total_lt += o_data.get('lt', 0)
                total_eq += o_data.get('eq', 0)
                total_gt += o_data.get('gt', 0)
        
        total_n = total_lt + total_eq + total_gt
        if total_n == 0:
            return None
        
        lt_pct = total_lt / total_n * 100
        eq_pct = total_eq / total_n * 100
        gt_pct = total_gt / total_n * 100
        
        return (lt_pct, eq_pct, gt_pct, total_n)
    
    def get_aggregate_left_first_pair_triple(self) -> Optional[Tuple[float, float, float, int]]:
        """
        Get weighted aggregate triple for left side "first toward second" pairs.
        
        Aggregates across L tot=2,3,4 the comparisons of L1 vs L2 (pair_idx=0 for all).
        
        Returns:
            Tuple of (lt%, eq%, gt%, total_N) or None
        """
        if not self.ordering_stats:
            return None
        
        total_lt = 0
        total_eq = 0
        total_gt = 0
        
        for tot in [2, 3, 4]:
            pair_idx = 0  # First pair (L1 vs L2) in each configuration
            o_key = ('left', tot, pair_idx)
            o_data = self.ordering_stats.get(o_key)
            
            if o_data:
                total_lt += o_data.get('lt', 0)
                total_eq += o_data.get('eq', 0)
                total_gt += o_data.get('gt', 0)
        
        total_n = total_lt + total_eq + total_gt
        if total_n == 0:
            return None
        
        lt_pct = total_lt / total_n * 100
        eq_pct = total_eq / total_n * 100
        gt_pct = total_gt / total_n * 100
        
        return (lt_pct, eq_pct, gt_pct, total_n)

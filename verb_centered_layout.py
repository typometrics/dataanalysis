"""
Layout logic for verb-centered constituent size table.

This module handles column/row positioning and grid structure calculations.
"""

from verb_centered_model import TableConfig


class TableLayout:
    """
    Calculates column positions and row structure for the helix table.
    
    Table structure:
    [Label] [Mirror] [L4] [F43] [L3] [F32] [L2] [F21] [L1] [V] [R1] [F12] [R2] [F23] [R3] [F34] [R4] [Extra]
    
    When show_horizontal_factors=False, factor columns are omitted.
    """
    
    def __init__(self, config: TableConfig):
        """
        Initialize layout calculator.
        
        Args:
            config: Table configuration
        """
        self.config = config
        self._calculate_dimensions()
    
    def _calculate_dimensions(self):
        """Calculate table dimensions based on configuration."""
        # Fixed columns: Label (1) + Mirror (1)
        self.label_cols = 1
        self.mirror_cols = 1
        
        # Left side columns
        if self.config.show_horizontal_factors:
            # With factors: L4 F43 L3 F32 L2 F21 L1 = 7 cols
            self.left_cols = 7
        else:
            # Without factors: L4 L3 L2 L1 = 4 cols
            self.left_cols = 4
        
        # V column
        self.v_col_count = 1
        
        # Right side columns
        if self.config.show_horizontal_factors:
            # With factors: R1 F12 R2 F23 R3 F34 R4 = 7 cols
            self.right_cols = 7
        else:
            # Without factors: R1 R2 R3 R4 = 4 cols
            self.right_cols = 4
        
        # Extra column at end
        self.extra_cols = 1
        
        # Comment column (optional)
        self.comment_cols = 1 if self.config.show_row_averages else 0
        
        # Total
        self._total_cols = (self.label_cols + self.mirror_cols + 
                           self.left_cols + self.v_col_count + 
                           self.right_cols + self.extra_cols + 
                           self.comment_cols)
    
    @property
    def total_columns(self) -> int:
        """Total number of columns in the table."""
        return self._total_cols
    
    @property
    def label_col_idx(self) -> int:
        """Column index for row label."""
        return 0
    
    @property
    def mirror_col_idx(self) -> int:
        """Column index for mirror (leftmost marginal mean spot)."""
        return 1
    
    @property
    def v_col_idx(self) -> int:
        """Column index for V (verb center)."""
        return self.label_cols + self.mirror_cols + self.left_cols
    
    @property
    def extra_col_idx(self) -> int:
        """Column index for extra (rightmost marginal mean spot)."""
        return self.v_col_idx + self.v_col_count + self.right_cols
    
    @property
    def comment_col_idx(self) -> int:
        """Column index for comment (if enabled)."""
        return self.extra_col_idx + self.extra_cols
    
    def get_left_column_index(self, pos: int, is_factor: bool = False) -> int:
        """
        Get column index for left side position or factor.
        
        Left side is ordered: L4 [F43] L3 [F32] L2 [F21] L1
        
        Args:
            pos: Position (1-4)
            is_factor: True if this is a factor column (between pos and pos-1)
            
        Returns:
            Column index
        """
        base_offset = self.label_cols + self.mirror_cols
        
        if self.config.show_horizontal_factors:
            # Formula: L4 is at idx 0, L3 at 2, L2 at 4, L1 at 6
            # pos=4 -> 0, pos=3 -> 2, pos=2 -> 4, pos=1 -> 6
            # Formula: (4 - pos) * 2
            val_idx = (4 - pos) * 2
            
            if is_factor:
                # Factor is after value: F43 after L4, etc.
                # For pos=4, factor F43 is at val_idx + 1
                return base_offset + val_idx + 1
            else:
                return base_offset + val_idx
        else:
            # Without factors: L4 L3 L2 L1
            # pos=4 -> 0, pos=3 -> 1, pos=2 -> 2, pos=1 -> 3
            # Formula: 4 - pos
            return base_offset + (4 - pos)
    
    def get_right_column_index(self, pos: int, is_factor: bool = False) -> int:
        """
        Get column index for right side position or factor.
        
        Right side is ordered: R1 [F12] R2 [F23] R3 [F34] R4
        
        Args:
            pos: Position (1-4)
            is_factor: True if this is a factor column (between pos-1 and pos)
            
        Returns:
            Column index
        """
        base_offset = self.v_col_idx + self.v_col_count
        
        if self.config.show_horizontal_factors:
            # Formula: R1 is at idx 0, R2 at 2, R3 at 4, R4 at 6
            # pos=1 -> 0, pos=2 -> 2, pos=3 -> 4, pos=4 -> 6
            # Formula: (pos - 1) * 2
            val_idx = (pos - 1) * 2
            
            if is_factor:
                # Factor is after prev value: F12 after R1, etc.
                # For pos=2, factor F12 is at idx for R1 + 1
                return base_offset + val_idx - 1
            else:
                return base_offset + val_idx
        else:
            # Without factors: R1 R2 R3 R4
            # pos=1 -> 0, pos=2 -> 1, pos=3 -> 2, pos=4 -> 3
            # Formula: pos - 1
            return base_offset + (pos - 1)
    
    def create_empty_row(self) -> list:
        """
        Create a row with empty cells (None placeholders).
        
        Returns:
            List of None with length = total_columns
        """
        return [None] * self.total_columns
    
    def get_diagonal_placement_right(self, diagonal_idx: int) -> int:
        """
        Get column index for right diagonal marginal mean.
        
        Diagonals are placed in factor columns:
        - Diagonal 2 (shortest) at F23 position
        - Diagonal 1 (medium) at F34 position
        - Diagonal 0 (longest) at Extra column
        
        Args:
            diagonal_idx: 0 (longest), 1 (medium), 2 (shortest)
            
        Returns:
            Column index
        """
        if diagonal_idx == 2:
            # Shortest: at F23 position (between R2 and R3)
            return self.get_right_column_index(3, is_factor=True)
        elif diagonal_idx == 1:
            # Medium: at F34 position (between R3 and R4)
            return self.get_right_column_index(4, is_factor=True)
        elif diagonal_idx == 0:
            # Longest: at Extra column
            return self.extra_col_idx
        return -1
    
    def get_diagonal_placement_left(self, diagonal_idx: int) -> int:
        """
        Get column index for left diagonal marginal mean.
        
        Diagonals are placed in factor columns:
        - Diagonal 0 (longest) at Mirror column
        - Diagonal 1 (medium) at F43 position
        - Diagonal 2 (shortest) at F32 position
        
        Args:
            diagonal_idx: 0 (longest), 1 (medium), 2 (shortest)
            
        Returns:
            Column index
        """
        if diagonal_idx == 0:
            # Longest: at Mirror column
            return self.mirror_col_idx
        elif diagonal_idx == 1:
            # Medium: at F43 position (between L4 and L3)
            return self.get_left_column_index(4, is_factor=True)
        elif diagonal_idx == 2:
            # Shortest: at F32 position (between L3 and L2)
            return self.get_left_column_index(3, is_factor=True)
        return -1

"""
Data models for verb-centered constituent size analysis.

This module defines the core data structures used throughout the
verb-centered analysis pipeline.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Tuple, Dict, Any


@dataclass
class CellData:
    """
    Represents a single cell's content and metadata.
    
    Attributes:
        value: Numeric value (for Excel number formatting)
        text: Display text
        cell_type: Type of cell ('label', 'value', 'factor', 'comment', 'separator')
        rich_segments: List of (text, color_hex, is_bold) tuples for rich text formatting
    """
    value: Optional[float] = None
    text: str = ""
    cell_type: str = 'normal'
    rich_segments: Optional[List[Tuple[str, str, bool]]] = None
    
    def __post_init__(self):
        """Ensure rich_segments is a list if provided."""
        if self.rich_segments is not None and not isinstance(self.rich_segments, list):
            self.rich_segments = list(self.rich_segments)


@dataclass
class FactorData:
    """
    Represents a growth factor between two positions.
    
    Attributes:
        value: The computed factor value
        source_key: Key for the source position (e.g., 'right_1_totright_2')
        target_key: Key for the target position (e.g., 'right_2_totright_2')
        arrow_type: Type of arrow ('horizontal', 'diagonal')
        side: Side of verb ('left', 'right', 'xvx')
    """
    value: float
    source_key: str
    target_key: str
    arrow_type: str
    side: str


@dataclass
class TableConfig:
    """
    Configuration for table generation.
    
    Arrow direction modes:
    - 'diverging' or 'outward': Always outward (both sides grow away from V)
    - 'inward' or 'converging': Always inward (both sides grow toward V)
    - 'left_to_right': Left is inward (toward V), Right is outward (away from V)
    - 'right_to_left': Left is outward (away from V), Right is inward (toward V)
    """
    show_horizontal_factors: bool = False
    show_diagonal_factors: bool = False
    show_ordering_triples: bool = False
    show_row_averages: bool = False
    show_marginal_means: bool = True
    arrow_direction: str = 'diverging'  # 'diverging', 'inward', 'left_to_right', 'right_to_left'
    
    def get_growth_direction(self, side: str) -> str:
        """
        Determine growth direction for a given side.
        
        Args:
            side: 'left' or 'right'
            
        Returns:
            'outward' or 'inward'
        """
        # Normalize arrow_direction
        if self.arrow_direction in ['diverging', 'outward']:
            return 'outward'
        elif self.arrow_direction in ['inward', 'converging']:
            return 'inward'
        elif self.arrow_direction == 'left_to_right':
            # Left is inward (L4->L1 toward V), Right is outward (R1->R4 away from V)
            return 'inward' if side == 'left' else 'outward'
        elif self.arrow_direction == 'right_to_left':
            # Left is outward (L1->L4 away from V), Right is inward (R4->R1 toward V)
            return 'outward' if side == 'left' else 'inward'
        else:
            # Default fallback
            return 'outward'
    
    def get_arrow_symbol(self, side: str, arrow_type: str) -> str:
        """
        Get the appropriate arrow symbol.
        
        Args:
            side: 'left' or 'right'
            arrow_type: 'horizontal' or 'diagonal'
            
        Returns:
            Arrow symbol string
        """
        is_outward = self.get_growth_direction(side) == 'outward'
        
        if side == 'right':
            if arrow_type == 'horizontal':
                return '→' if is_outward else '←'
            else:  # diagonal
                return '↗' if is_outward else '↙'
        else:  # left
            if arrow_type == 'horizontal':
                return '←' if is_outward else '→'
            else:  # diagonal
                return '↙' if is_outward else '↗'


@dataclass
class TableStructure:
    """
    Represents the complete table structure.
    
    Attributes:
        config: Table configuration
        rows: List of rows, each row is a list of CellData
        metadata: Additional metadata (language info, statistics, etc.)
    """
    config: TableConfig
    rows: List[List[CellData]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_row(self, row: List[CellData]):
        """Add a row to the table."""
        self.rows.append(row)
    
    def add_separator(self):
        """Add a separator row."""
        self.rows.append([CellData(cell_type='separator')])
    
    @property
    def num_rows(self) -> int:
        """Number of rows in the table."""
        return len(self.rows)
    
    @property
    def num_cols(self) -> int:
        """Number of columns (based on first non-empty row)."""
        for row in self.rows:
            if row:
                return len(row)
        return 0


# Backward compatibility - GridCell alias
class GridCell:
    """
    Legacy GridCell class for backward compatibility.
    
    This is a thin wrapper around CellData to maintain compatibility
    with existing code that uses GridCell.
    """
    def __init__(self, text="", value=None, cell_type='normal', rich_text=None, is_astonishing=False):
        self.text = text
        self.value = value
        self.cell_type = cell_type
        self.rich_text = rich_text if rich_text is not None else []
        self.is_astonishing = is_astonishing
    
    def to_cell_data(self) -> CellData:
        """Convert to CellData."""
        return CellData(
            value=self.value,
            text=self.text,
            cell_type=self.cell_type,
            rich_segments=self.rich_text
        )
    
    @staticmethod
    def from_cell_data(cell: CellData) -> 'GridCell':
        """Create GridCell from CellData."""
        return GridCell(
            text=cell.text,
            value=cell.value,
            cell_type=cell.cell_type,
            rich_text=cell.rich_segments
        )

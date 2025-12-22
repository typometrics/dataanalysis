# Verb-Centered Analysis Refactoring Plan

## Current State Analysis

**File**: `verb_centered_analysis.py` (2441 lines)

### Problems Identified

1. **Massive Code Duplication** (~60% redundant code)
   - `extract_verb_centered_grid()` (600+ lines) and `format_verb_centered_table()` (800+ lines) share 90% logic
   - Marginal means calculated 4 times identically
   - Factor computation duplicated across right/left sides

2. **Complex Indexing Logic**
   - Column positions calculated with magic formulas: `idx = 6 - (pos - 1) * 2`
   - Different paths for `show_horizontal_factors` true/false
   - Hard to reason about correctness

3. **Monolithic Functions**
   - Functions have 10+ responsibilities each
   - Difficult to test individual components
   - Hard to add new features

4. **Scattered Configuration**
   - Arrow direction logic spread across multiple functions
   - Width constants defined at function level
   - No single source of truth

## Proposed Solution

### Phase 1: Extract Data Model (Priority: HIGH)

Create a unified data model that both grid and text formatting can use:

```python
# New file: verb_centered_model.py

@dataclass
class CellData:
    """Represents a single cell's content and metadata."""
    value: Optional[float] = None
    text: str = ""
    cell_type: str = 'normal'  # 'label', 'value', 'factor', 'comment', 'separator'
    rich_segments: List[Tuple[str, str, bool]] = None  # (text, color, bold)
    
@dataclass
class FactorData:
    """Represents a growth factor between two positions."""
    value: float
    source_key: str
    target_key: str
    arrow_type: str  # 'horizontal', 'diagonal'
    side: str  # 'left', 'right', 'xvx'

@dataclass
class TableConfig:
    """Configuration for table generation."""
    show_horizontal_factors: bool = False
    show_diagonal_factors: bool = False
    show_ordering_triples: bool = False
    show_row_averages: bool = False
    show_marginal_means: bool = True
    arrow_direction: str = 'diverging'
    
class TableStructure:
    """Represents the complete table structure."""
    def __init__(self, config: TableConfig):
        self.config = config
        self.rows: List[List[CellData]] = []
        self.metadata: Dict = {}
```

### Phase 2: Extract Computation Logic (Priority: HIGH)

Separate computation from presentation:

```python
# New file: verb_centered_computations.py

class MarginalMeansCalculator:
    """Handles all marginal means calculations."""
    
    def __init__(self, position_averages: Dict):
        self.position_averages = position_averages
        
    def calc_vertical_means_right(self) -> Dict[int, float]:
        """Calculate vertical means for right side (by position)."""
        pass
        
    def calc_diagonal_means_right(self) -> Dict[int, Tuple[float, float]]:
        """Calculate diagonal means (size GM, factor GM) for right side."""
        pass
    
    # Similar for left side...

class FactorCalculator:
    """Calculates growth factors between positions."""
    
    def __init__(self, position_averages: Dict, arrow_direction: str):
        self.position_averages = position_averages
        self.arrow_direction = arrow_direction
        
    def get_horizontal_factor(self, side: str, pos: int, tot: int) -> Optional[FactorData]:
        """Calculate horizontal factor between pos and pos-1."""
        pass
        
    def get_diagonal_factor(self, side: str, pos: int, tot: int) -> Optional[FactorData]:
        """Calculate diagonal factor."""
        pass

class OrderingStatsFormatter:
    """Formats ordering statistics (triples)."""
    
    def __init__(self, ordering_stats: Dict):
        self.ordering_stats = ordering_stats
        
    def get_triple(self, side: str, tot: int, pair_idx: int) -> Optional[Tuple[float, float, float]]:
        """Returns (lt%, eq%, gt%) for a position pair."""
        pass
```

### Phase 3: Extract Layout Logic (Priority: MEDIUM)

Create a layout calculator that handles indexing:

```python
# New file: verb_centered_layout.py

class TableLayout:
    """Calculates column positions and row structure."""
    
    def __init__(self, config: TableConfig):
        self.config = config
        self._calculate_dimensions()
        
    def get_left_column_index(self, pos: int, is_factor: bool = False) -> int:
        """Get column index for left side position or factor."""
        if self.config.show_horizontal_factors:
            base_idx = 6 - (pos - 1) * 2
            return base_idx + (1 if is_factor else 0)
        else:
            return 3 - (pos - 1)
            
    def get_right_column_index(self, pos: int, is_factor: bool = False) -> int:
        """Get column index for right side position or factor."""
        # After V column (index = left_cols + 1)
        v_col = self.left_cols
        if self.config.show_horizontal_factors:
            return v_col + 1 + (pos - 1) * 2 + (1 if is_factor else 0)
        else:
            return v_col + pos
            
    @property
    def total_columns(self) -> int:
        """Total number of columns in the table."""
        return self._total_cols
```

### Phase 4: Unified Table Builder (Priority: HIGH)

Single builder that creates the data structure:

```python
# Modified: verb_centered_analysis.py

class VerbCenteredTableBuilder:
    """Unified table builder using composition."""
    
    def __init__(self, 
                 position_averages: Dict,
                 config: TableConfig,
                 ordering_stats: Optional[Dict] = None):
        
        self.position_averages = position_averages
        self.config = config
        self.layout = TableLayout(config)
        self.marginals = MarginalMeansCalculator(position_averages)
        self.factors = FactorCalculator(position_averages, config.arrow_direction)
        self.ordering = OrderingStatsFormatter(ordering_stats) if ordering_stats else None
        
    def build(self) -> TableStructure:
        """Build the complete table structure."""
        table = TableStructure(self.config)
        
        # Build in order
        table.rows.append(self._build_header_row())
        
        if self.config.show_marginal_means:
            table.rows.extend(self._build_right_marginal_rows())
            
        table.rows.extend(self._build_right_data_rows())
        
        if self.config.show_marginal_means:
            table.rows.extend(self._build_left_marginal_rows())
            
        table.rows.extend(self._build_left_data_rows())
        table.rows.append(self._build_xvx_row())
        
        return table
        
    def _build_header_row(self) -> List[CellData]:
        """Build header row with column labels."""
        row = [CellData(text="Row", cell_type='label')]
        row.append(CellData(text=""))  # Mirror column
        
        # Left headers
        for pos in range(4, 0, -1):
            idx = self.layout.get_left_column_index(pos)
            # Insert at correct position...
            
        # Continue for V and right headers...
        return row
        
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
        row[0] = CellData(text=f"R tot={tot}", cell_type='label')
        
        # V column
        v_idx = self.layout.left_cols
        row[v_idx] = CellData(text="V", cell_type='label')
        
        # Data columns
        for pos in range(1, tot + 1):
            # Get value
            key = f'right_{pos}_totright_{tot}'
            value = self.position_averages.get(key)
            
            # Place value
            val_idx = self.layout.get_right_column_index(pos, is_factor=False)
            row[val_idx] = self._create_value_cell(value)
            
            # Place factor if needed
            if pos > 1 and self.config.show_horizontal_factors:
                fac_idx = self.layout.get_right_column_index(pos, is_factor=True)
                row[fac_idx] = self._create_factor_cell('right', pos, tot)
                
        return row
        
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
        
    def _create_factor_cell(self, side: str, pos: int, tot: int) -> CellData:
        """Create a factor cell with optional ordering triple."""
        segments = []
        
        # Get factor
        factor_data = self.factors.get_horizontal_factor(side, pos, tot)
        if factor_data:
            # Format factor with arrow
            arrow = get_arrow(side, 'horizontal', self.config.arrow_direction)
            text = f"×{factor_data.value:.2f}{arrow}"
            color = "FF0000" if factor_data.value < 1.0 else "555555"
            segments.append((text, color, True))
            
        # Add ordering triple if enabled
        if self.config.show_ordering_triples and self.ordering:
            triple = self.ordering.get_triple(side, tot, pos - 2)
            if triple:
                lt, eq, gt = triple
                segments.append((f" (<{lt:.0f}={eq:.0f}>", "555555", False))
                gt_color = "FF0000" if gt > lt else "555555"
                segments.append((f"{gt:.0f})", gt_color, gt > lt))
                
        return CellData(
            text=" ".join(seg[0] for seg in segments),
            cell_type='factor',
            rich_segments=segments
        )
```

### Phase 5: Separate Formatters (Priority: MEDIUM)

```python
# New file: verb_centered_formatters.py

class TextTableFormatter:
    """Formats TableStructure as fixed-width text."""
    
    def __init__(self, table: TableStructure):
        self.table = table
        self.VAL_WIDTH = 11
        self.FAC_WIDTH = 14
        
    def format(self) -> str:
        """Generate text representation."""
        lines = []
        for row in self.table.rows:
            line = self._format_row(row)
            lines.append(line)
        return "\n".join(lines)
        
class TSVFormatter:
    """Formats TableStructure as TSV."""
    
    def format(self, table: TableStructure) -> str:
        """Generate TSV representation."""
        rows = []
        for row in table.rows:
            rows.append("\t".join(cell.text for cell in row))
        return "\n".join(rows)
        
class ExcelFormatter:
    """Formats TableStructure as Excel with styling."""
    
    def save(self, table: TableStructure, output_path: str):
        """Save as Excel file with formatting."""
        # Use openpyxl to apply rich_segments styling
        pass
```

### Phase 6: Simplified Public API (Priority: HIGH)

```python
# Modified: verb_centered_analysis.py (main API)

def compute_average_sizes_table(all_langs_average_sizes_filtered):
    """Existing function - keep as is."""
    pass

def create_verb_centered_table(
    position_averages: Dict,
    config: Optional[TableConfig] = None,
    ordering_stats: Optional[Dict] = None
) -> TableStructure:
    """
    Create table structure (unified entry point).
    
    Args:
        position_averages: Dictionary of average sizes and factors
        config: Table configuration (uses defaults if None)
        ordering_stats: Optional ordering statistics
        
    Returns:
        TableStructure object that can be formatted multiple ways
    """
    if config is None:
        config = TableConfig()
        
    builder = VerbCenteredTableBuilder(position_averages, config, ordering_stats)
    return builder.build()

def format_verb_centered_table(
    position_averages: Dict,
    output_format: str = 'text',  # 'text', 'tsv', 'excel'
    **kwargs
) -> Union[str, None]:
    """
    Legacy API - formats table directly.
    
    Internally uses create_verb_centered_table() + formatter.
    """
    # Extract config from kwargs
    config = TableConfig(
        show_horizontal_factors=kwargs.get('show_horizontal_factors', False),
        show_diagonal_factors=kwargs.get('show_diagonal_factors', False),
        # ... other params
    )
    
    # Build table
    table = create_verb_centered_table(
        position_averages,
        config,
        kwargs.get('ordering_stats')
    )
    
    # Format
    if output_format == 'text':
        formatter = TextTableFormatter(table)
        return formatter.format()
    elif output_format == 'tsv':
        formatter = TSVFormatter()
        return formatter.format(table)
    elif output_format == 'excel':
        formatter = ExcelFormatter()
        formatter.save(table, kwargs['output_path'])
        return None

# Remove extract_verb_centered_grid() - replace with:
def get_grid_for_excel(
    position_averages: Dict,
    **kwargs
) -> List[List[GridCell]]:
    """
    Legacy API for Excel grid.
    
    Converts TableStructure to old GridCell format for backward compatibility.
    """
    table = create_verb_centered_table(position_averages, ...)
    return _convert_to_grid_cells(table)
```

## Benefits of Refactoring

### Code Quality
- **80% reduction in duplication** (from 2441 lines → ~800 lines core + utilities)
- **Single source of truth** for all computations
- **Testable components** - each class has one responsibility
- **Clear separation** of concerns (data, computation, layout, formatting)

### Maintainability
- **Easy to understand** - each component is < 200 lines
- **Easy to modify** - change one thing in one place
- **Easy to extend** - add new formatters without touching core logic
- **Self-documenting** - clear class/method names

### Backward Compatibility
- Old API (`format_verb_centered_table`) preserved
- Old `GridCell` format still available via conversion
- Existing notebooks continue to work

## Implementation Phases

### Phase 1 (Week 1): Core Refactoring
1. Create data models (`verb_centered_model.py`)
2. Extract computation logic (`verb_centered_computations.py`)
3. Create unified builder
4. Maintain old API as thin wrapper
5. Test with existing notebooks

### Phase 2 (Week 2): Layout & Formatters
1. Extract layout logic (`verb_centered_layout.py`)
2. Create separate formatters (`verb_centered_formatters.py`)
3. Update tests
4. Performance testing

### Phase 3 (Week 3): Cleanup & Documentation
1. Remove old duplicate code
2. Update docstrings
3. Create usage examples
4. Update HELIX_TABLE_GUIDE.md

## Testing Strategy

```python
# tests/test_verb_centered_refactor.py

def test_backward_compatibility():
    """Ensure old API produces identical output."""
    # Compare old vs new implementation
    pass

def test_marginal_means_calculator():
    """Test marginal means in isolation."""
    pass

def test_factor_calculator():
    """Test factor calculations."""
    pass

def test_layout_indexing():
    """Test column index calculations."""
    pass

def test_formatters():
    """Test each formatter independently."""
    pass
```

## Migration Guide

### For Notebook Users
No changes needed - old API still works:

```python
# This continues to work
table_str = verb_centered_analysis.format_verb_centered_table(
    position_averages,
    show_horizontal_factors=True,
    show_diagonal_factors=True
)
```

### For New Code
Use the cleaner API:

```python
from verb_centered_analysis import create_verb_centered_table, TableConfig
from verb_centered_formatters import TextTableFormatter, TSVFormatter

# Create table structure once
config = TableConfig(
    show_horizontal_factors=True,
    show_diagonal_factors=True,
    arrow_direction='rightwards'
)
table = create_verb_centered_table(position_averages, config, ordering_stats)

# Format multiple ways
text = TextTableFormatter(table).format()
tsv = TSVFormatter().format(table)
ExcelFormatter().save(table, 'output.xlsx')
```

## Risk Mitigation

1. **Keep old code temporarily** - don't delete until fully validated
2. **Extensive testing** - run against all existing datasets
3. **Side-by-side comparison** - generate tables with both old/new, compare byte-for-byte
4. **Gradual rollout** - update one notebook at a time

## Estimated Effort

- **Phase 1**: 3-4 days (core refactoring + testing)
- **Phase 2**: 2-3 days (formatters + layout)
- **Phase 3**: 1-2 days (cleanup + docs)
- **Total**: 6-9 days for one developer

## Success Criteria

1. ✅ All existing notebooks produce identical output
2. ✅ Code coverage > 80%
3. ✅ Main file < 500 lines
4. ✅ No function > 100 lines
5. ✅ All tests pass
6. ✅ Documentation complete

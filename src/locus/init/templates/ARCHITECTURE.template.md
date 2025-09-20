# System Architecture Guide — {project_name}

**Purpose:** Guidelines for designing robust software systems from scratch.

<design_principles>
## I. System Design Principles

### Why We Separate Concerns

**Problem**: Complex systems tend to become tangled when data processing, business logic, and presentation are mixed together. This leads to:
- Untestable code (hard to isolate logic)
- Difficult debugging (errors propagate through multiple layers)
- Poor reusability (logic tied to specific presentation formats)
- Maintenance overhead (changes require touching multiple concerns)

**Solution**: Clear architectural boundaries with single responsibilities:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data Layer    │    │  Business Core  │    │ Presentation    │
│                 │    │                 │    │                 │
│ • I/O Operations│────▶│ • Pure Logic    │────▶│ • Formatting    │
│ • Validation    │    │ • Computations  │    │ • Error Display │
│ • Error Convert │    │ • Fail Fast     │    │ • UI/Reports    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Core Design Rules

1. **Dependency Direction**: Higher layers depend on lower layers, never reverse
2. **Error Boundaries**: Each layer has specific error handling responsibilities
3. **Data Contracts**: Use typed interfaces between layers (Pydantic models)
4. **Testability**: Core logic must be testable without I/O or external dependencies
</design_principles>

<layer_architecture>
## II. Layer Architecture Patterns

### Three-Layer Pattern

**Layer 1: Core Business Logic**
- **Pure Functions**: No side effects, deterministic outputs
- **Explicit Inputs**: All dependencies passed as parameters
- **Standard Outputs**: Consistent data structures with fixed interfaces
- **Fast Failures**: Specific exceptions for different error types

```python
# core/business_logic.py
def compute_metrics(
    data: List[Dict],
    id_field: str,
    value_field: str
) -> List[Dict]:
    """Pure business logic: data → metrics."""
    if not data:
        raise InsufficientDataError("No data for metrics computation")

    result = []
    for item in data:
        metric = {{
            "id": item[id_field],
            "value": item[value_field],
            "computed_score": item[value_field] * 2  # Business logic
        }}
        result.append(metric)

    return result
```

**Layer 2: Formatting & Presentation**
- **Transform Structure**: Convert business results to presentation format
- **No Business Logic**: Only visual formatting, translations, styling
- **Stable Inputs**: Depends on Layer 1's standard output format

```python
# presentation/formatting.py
def format_metrics_table(metrics: List[Dict]) -> List[Dict]:
    """Format business results for display."""
    return [
        {{
            "ID": metric["id"],
            "Value": f"${{metric['value']:,.2f}}",
            "Score": f"{{metric['computed_score']:.1f}}"
        }}
        for metric in metrics
    ]
```

**Layer 3: Orchestration & Error Handling**
- **Workflow Management**: Coordinates multiple business functions
- **Error Recovery**: Centralized exception handling with graceful degradation
- **Context Management**: Manages data lifecycle and configuration

```python
# orchestration/coordinator.py
def build_metrics_section(cfg, ctx):
    """Orchestrate business logic with centralized error handling."""
    try:
        # Extract configuration
        id_field = cfg.data_mapping.id_column
        value_field = cfg.data_mapping.value_column

        # Execute business logic
        metrics = compute_metrics(ctx.data, id_field, value_field)

        # Format for presentation
        formatted = format_metrics_table(metrics)

        return create_section("Metrics", formatted)

    except InsufficientDataError as e:
        logger.info(f"Expected data limitation: {{e}}")
        return create_placeholder_section("Metrics", "No data available")
    except (DataValidationError, ConfigurationError) as e:
        logger.warning(f"Configuration issue: {{e}}")
        return create_placeholder_section("Metrics", "Configuration error")
```
</layer_architecture>

<data_flow>
## III. Data Flow Architecture

### Unidirectional Data Flow

```
Raw Data → Validation → Business Logic → Formatting → Output → Error Display
    ↓          ↓            ↓              ↓          ↓         ↓
[I/O Layer] [Guards]  [Pure Logic]   [Styling]  [Files]  [User UX]
```

**Benefits**:
- **Predictable**: Data flows in one direction
- **Debuggable**: Easy to trace where data comes from
- **Testable**: Each stage can be tested independently
- **Scalable**: New features follow the same pattern

### Error Flow Architecture

```
Business Logic → Specific Exceptions → Centralized Handler → User-Friendly Display
      ↓                 ↓                     ↓                      ↓
  [Fail Fast]     [Typed Errors]      [Recovery Logic]        [Graceful UX]
```

**Error Types by Layer**:
- **Business Layer**: `InsufficientDataError`, `DataValidationError`, `BusinessRuleError`
- **Formatting Layer**: Re-raise business errors, add `FormattingError` for display issues
- **Orchestration Layer**: Catch all specific errors, log appropriately, show placeholders
</data_flow>

<configuration_management>
## IV. Configuration Management Pattern

### Extract-Transform-Pass Pattern

**Problem**: Passing large config objects creates hidden dependencies and makes testing difficult.

**Solution**: Extract needed values at boundaries, pass explicitly to core functions.

```python
# ❌ BAD: Hidden dependencies
def process_data(data, config):
    # Function signature doesn't show what config fields are actually needed
    result = compute_business_logic(data, config)  # Hidden coupling

# ✅ GOOD: Explicit dependencies
def process_data_section(config, context):
    # Extract phase: Make dependencies explicit
    mapping_cfg = config.column_mapping
    business_cfg = config.business_rules

    # Transform phase: Call core with specific parameters
    result = compute_business_logic(
        data=context.raw_data,
        id_column=mapping_cfg.id_field,
        value_column=mapping_cfg.value_field,
        threshold=business_cfg.min_threshold
    )

    # Pass phase: Format and return
    formatted = format_result_table(result)
    return create_section("Business Data", formatted)
```

### Configuration Interface Design

```python
# Define clear configuration contracts
@dataclass
class DataMappingConfig:
    """Configuration for data field mappings."""
    id_field: str
    value_field: str
    timestamp_field: str

@dataclass
class BusinessRulesConfig:
    """Configuration for business logic parameters."""
    min_threshold: float
    max_samples: int
    include_nulls: bool

@dataclass
class AppConfig:
    """Top-level application configuration."""
    data_mapping: DataMappingConfig
    business_rules: BusinessRulesConfig
    output_format: str
```
</configuration_management>

<module_design>
## V. Module Design Guidelines

### When to Create New Modules

**Business Logic Module** (`core/new_feature.py`):
- When you need to implement new business rules or calculations
- When logic becomes complex (>100 lines)
- When multiple presentation layers need the same computations

**Presentation Module** (`presentation/new_format.py`):
- When you need specialized formatting for specific data types
- When presentation logic becomes substantial
- When multiple outputs need the same formatting

**Orchestration Module** (`orchestration/new_workflow.py`):
- When you need to coordinate multiple business modules
- When workflow becomes complex with multiple steps
- When error handling patterns become specific to a domain

### Standard Module Interface Pattern

```python
# Business logic modules
from typing import Protocol
from ..exceptions import InsufficientDataError, DataValidationError

class BusinessInput(Protocol):
    """Define expected input structure."""
    data: List[Dict]
    config_param1: str
    config_param2: int

def process_business_feature(input_data: BusinessInput) -> List[Dict]:
    """
    Process business feature with standardized interface.

    Returns:
        List of dictionaries with keys: ["id", "result", "confidence"]

    Raises:
        InsufficientDataError: When input data is empty or invalid
        DataValidationError: When configuration parameters are invalid
    """
    # Implementation
    pass
```
</module_design>

<scaling_guidelines>
## VI. Scaling Guidelines

### Adding New Features

**Step 1**: Design the business function
```python
# core/new_feature.py
def compute_new_business_logic(data: List[Dict], param1: str, param2: int) -> List[Dict]:
    """Pure business function with clear interface."""
    pass
```

**Step 2**: Create presentation function
```python
# presentation/formatters.py
def format_new_feature_output(results: List[Dict]) -> List[Dict]:
    """Format for display."""
    pass
```

**Step 3**: Create orchestration function
```python
# orchestration/builders.py
def build_new_feature_section(cfg, ctx):
    """Orchestrate business logic → formatting → section creation."""
    pass
```

**Step 4**: Add to main workflow
```python
# main_workflow.py
def build_main_output(cfg, ctx):
    return (OutputBuilder()
        .add_section(build_existing_section)
        .add_section(build_new_feature_section)  # Add here
    )
```

### Adding New Output Types

**Use Case**: Different stakeholders need different views of the same data.

**Pattern**: Create specialized builders that reuse existing business logic:

```python
# orchestration/executive_builder.py
def build_executive_output(cfg, ctx):
    """High-level metrics for executives."""
    return (OutputBuilder()
        .add_section(build_summary_section)      # Reuse existing
        .add_section(build_trends_section)       # Reuse existing
        .add_section(build_recommendations)      # New, executive-specific
    )

# orchestration/technical_builder.py
def build_technical_output(cfg, ctx):
    """Detailed analysis for technical users."""
    return (OutputBuilder()
        .add_section(build_raw_data_section)     # Reuse existing
        .add_section(build_detailed_metrics)     # Reuse existing
        .add_section(build_debug_information)    # New, technical-specific
    )
```
</scaling_guidelines>

<common_mistakes>
## VII. Common Design Mistakes

### Anti-Pattern: "God Functions"

**Problem**:
```python
def build_comprehensive_report(cfg, ctx):
    # 500+ lines of mixed concerns
    # Data loading + business logic + formatting + error handling
    # Impossible to test or reuse
```

**Solution**: Break into focused functions with single responsibilities.

### Anti-Pattern: "Configuration Soup"

**Problem**:
```python
def process_data(data, config):
    # Function doesn't declare what config fields it needs
    # Hidden dependencies on config.a.b.c.deep.nested.field
    # Hard to test, breaks when config structure changes
```

**Solution**: Extract needed config values at the boundary, pass explicitly.

### Anti-Pattern: "Silent Failures"

**Problem**:
```python
def compute_business_metrics(data):
    if not data:
        return []  # Silent failure, caller doesn't know why
    # Errors propagate as empty results
```

**Solution**: Fail fast with specific exceptions, handle at appropriate boundary.

### Anti-Pattern: "Mixed Abstractions"

**Problem**:
```python
def process_user_data(user_id):
    # Database queries mixed with business computations
    # HTML generation mixed with data analysis
    # I/O mixed with pure logic
```

**Solution**: Separate I/O, business logic, and presentation into different layers.
</common_mistakes>

<decision_framework>
## VIII. Design Decision Framework

### When Choosing Architecture

**Question 1**: Can this logic be tested without external dependencies?
- **Yes**: Put in business core layer
- **No**: Put in data/I/O layer

**Question 2**: Does this involve user-facing display formatting?
- **Yes**: Put in presentation layer
- **No**: Keep in core with standard output format

**Question 3**: Does this coordinate multiple business functions?
- **Yes**: Put in orchestration layer
- **No**: Keep as focused business function

**Question 4**: Does this handle multiple error types from lower layers?
- **Yes**: Put in orchestration layer (error boundary)
- **No**: Let specific errors bubble up to appropriate handler

### Performance vs. Maintainability Trade-offs

**Fast Development** (Early stages):
- Fewer abstractions
- Some duplication acceptable
- Focus on working solution

**Long-term Maintenance** (Mature system):
- More layers and abstractions
- Eliminate duplication through reusable components
- Invest in testing infrastructure

**Rule**: Start simple, refactor to patterns when you have 3+ similar components.
</decision_framework>

<implementation_checklist>
## IX. Implementation Checklist

### Before Starting Development
- [ ] Define clear data contracts between layers
- [ ] Identify error boundaries and exception types
- [ ] Design configuration structure
- [ ] Plan testing strategy for each layer

### During Development
- [ ] Keep business logic pure (no I/O dependencies)
- [ ] Use explicit parameter passing (avoid global configs)
- [ ] Implement specific exception types
- [ ] Add tests for each layer independently

### Before Code Review
- [ ] Verify layer separation is maintained
- [ ] Check that error handling is centralized
- [ ] Ensure configuration extraction is explicit
- [ ] Validate that core logic is testable in isolation

### Before Deployment
- [ ] All layers have appropriate test coverage
- [ ] Error scenarios are handled gracefully
- [ ] Configuration validation is in place
- [ ] Documentation reflects current architecture
</implementation_checklist>

This architecture guide provides the foundation for building maintainable, scalable systems that avoid the common pitfalls encountered in complex software applications.
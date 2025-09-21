# AI Agent Guidelines — {{project_name}}

**Goal:** Fast, reliable changes with tight quality gates.

## ?? Table of Contents

| Section | Description |
|---------|-------------|
| `<tools_and_mcp>` | Essential tools and MCP server configurations |
| `<llm_prompt_patterns>` | Prompt patterns for subagents and workflow |
| `<quick_checklist>` | Fast validation checklist for contributions |
| `<core_principles>` | Golden rules and development workflow |
| `<quality_gates>` | Commands and definition of done |
| `<architecture_patterns>` | Layer separation and code structure |
| `<error_handling>` | Exception handling strategy by layer |
| `<configuration_management>` | Extract-transform-pass patterns |
| `<anti_patterns>` | Critical mistakes to avoid |
| `<project_context>` | Project-specific workflow and modules |
| `<contribution_guide>` | Documentation and decision framework |

<tools_and_mcp>
## Recommended Tools & MCP Servers

### Essential Tools for AI Agents
- **Code Analysis**: Use `locus analyze` to understand codebase structure and scope changes
  ```bash
  # Quick overview of project structure
  locus analyze

  # Analyze specific module to understand scope
  locus analyze src/module_name/

  # Get full report for comprehensive analysis
  locus analyze -o analysis.md
  ```
- **File Operations**: Prefer `Read`, `Write`, `Edit` tools over shell commands for file manipulation
- **Search**: Use `Grep` and `Glob` tools for efficient code searching
- **Testing**: Use `Bash` tool for running tests and quality checks
- **Version Control**: Use `Bash` tool for git operations (status, diff, commit)

### Tool Usage Guidelines
- **Read before Edit**: Always read files before making changes
- **Batch Operations**: Use multiple tool calls in parallel when possible
- **Quality Checks**: Run linting and formatting after code changes
- **Test Integration**: Verify changes with test execution
- **Documentation**: Update relevant documentation when making significant changes

### MCP Configuration

#### Currently Available MCP Servers
- **Sequential Thinking**: Use for complex planning and step-by-step reasoning
  - When: Breaking down complex tasks, analyzing trade-offs, planning implementation steps
  - Example: "Think through the implications of this architectural change step by step"

- **Locus Analyzer** (future): For focused code analysis and change scoping
  - When: Need to understand what files to modify for a specific feature
  - Example: "Use locus to identify all files related to authentication before making changes"

#### MCP Usage Guidelines
- **Planning Phase**: Use Sequential Thinking MCP for complex reasoning and task breakdown
- **Analysis Phase**: Use Locus MCP (when available) to scope changes and understand dependencies
- **Implementation Phase**: Use core tools (Read, Write, Edit) for file operations
- **Validation Phase**: Use Bash tool for testing and quality checks
</tools_and_mcp>

<llm_prompt_patterns>
## LLM Prompt Patterns for Effective Development

### Core Workflow Prompts for Subagents

Use these patterns when invoking subagents to save context and provide clear instructions:

#### Analysis Phase (for Task/Agent tool)
```
"Use the Task tool with general-purpose agent: Analyze the requirements for [feature]. List key tasks, dependencies, and potential challenges. Return a structured breakdown without implementing anything."
```

#### Planning Phase (with Sequential Thinking MCP)
```
"Use Sequential Thinking MCP: Create detailed implementation plan for [feature]. Break down into: core functions > formatting > orchestration. Consider layer separation and return step-by-step plan."
```

#### Implementation Phase (for focused tasks)
```
"Implement step X from the plan: [specific task]. Follow single-responsibility principle and maintain layer separation between core/formatting/orchestration."
```

#### Code Scope Analysis (future Locus MCP)
```
"Use Locus MCP: Identify all files that need modification for [feature]. Provide focused scope to minimize search overhead."
```

### Advanced Reasoning Prompts

#### For Complex Problems
```
"Think step-by-step about this problem. Consider edge cases, dependencies, and potential failure modes before proposing a solution."
```

#### For Code Review
```
"Review this code for: 1) Layer separation violations, 2) Error handling issues, 3) Testing gaps, 4) Documentation needs."
```

#### For Debugging
```
"Analyze this error systematically: 1) Identify the failure point, 2) Trace the data flow, 3) Check layer boundaries, 4) Propose targeted fixes."
```

### Iterative Development Patterns

#### Code Review Integration
```
"Process my review comments and apply the suggested changes. Focus on [specific areas of concern]."
```

#### Incremental Feature Development
```
"Add feature X using our layered architecture. Start with core logic, then add formatting layer, finally integrate with orchestration."
```

#### Refactoring Guidance
```
"Refactor this code to improve [specific aspect]. Maintain existing functionality while improving code quality and maintainability."
```
</llm_prompt_patterns>

<quick_checklist>
## Quick Checklist for a Contribution
? **Core Logic**: Pure function? No global config? Explicit args?
? **Error Handling**: Used specific exceptions correctly?
? **Tests**: Added a new test for the change?
? **Quality Gates**: Ran `ruff check --fix`, `ruff format`, `pytest`?
? **Documentation**: Updated relevant docs and session log?
</quick_checklist>

<core_principles>
## I. Core Principles

### Golden Rules

1.  **Single Responsibility**: One module for one job (data processing, business logic, presentation).
    - *Why*: Easier to test, debug and reuse. Changes in one part don't break others.

2.  **Separate Concerns**: I/O and error handling at boundaries; core logic must be pure and testable.
    - *Why*: Pure logic can be tested without DB/files. Easier to find bugs in separate layers.

3.  **Small Interfaces**: Pass explicit arguments; no hidden globals or entire config objects.
    - *Why*: All function dependencies are visible. Easier to understand what's needed for testing.

4.  **Stable Contracts**: Use Pydantic models for data with typed, documented fields.
    - *Why*: Automatic validation. IDE shows errors before runtime. Fewer runtime bugs.

5.  **Fail Fast**: Raise narrow, specific exceptions. Never use `except Exception:` or return silent defaults.
    - *Why*: Errors don't propagate through system. Faster to find source of problem.

### Required Workflow: LLM-Driven Development Process
**Analyze > Plan > Code > Test > Document > Quality Gates > Commit**

#### Phase-by-Phase Guide

1. **Analyze** – Carefully examine requirements. Gather context, clarify ambiguities.
   - *LLM Instruction*: "Analyze the requirements before coding. List key tasks and questions first."
   - *Why*: Prevents hasty coding. Ensures problem understanding before implementation.

2. **Plan** – Create step-by-step solution strategy before writing code.
   - *LLM Instruction*: "Outline a detailed plan in bullet points. Do not write any code yet."
   - *Why*: Planning first significantly improves results on complex tasks. Guides focused implementation.

3. **Code** – Implement according to approved plan. Write modular, incremental code.
   - *LLM Instruction*: "Implement step X of the plan. Follow single-responsibility principle."
   - *Why*: Structured implementation reduces errors. Easier to review and debug.

4. **Test** – Run automated tests. Fix failures before proceeding.
   - *LLM Instruction*: "Run tests and fix any failures. Do not proceed until tests pass."
   - *Why*: Fail-fast philosophy. Catch issues early rather than accumulating technical debt.

5. **Document** – Update docs, docstrings, README as needed.
   - *LLM Instruction*: "Update documentation to reflect these changes."
   - *Why*: Ensures implementation and usage are clearly recorded for future reference.
</core_principles>

<quality_gates>
## II. Quality Gates

### Commands
```bash
ruff check --fix src/ tests/
ruff format src/ tests/
pytest -q
```

### Definition of Done
*   Lint clean and correctly formatted.
*   All tests passing (including new, minimal tests for changes).
*   A `SESSION.md` entry is appended.
*   Commit message follows Conventional Commits format (`feat:`, `fix:`, etc.).

### Example Workflow
```bash
# 1. Analyze the problem
# Read existing code, understand the codebase structure

# 2. Plan the solution
# Break down into: core functions > formatting > orchestration

# 3. Code with layer separation
# core/ - pure logic
# formatting/ - presentation
# orchestration/ - coordination

# 4. Quality gates
ruff check --fix src/ tests/  # Fix style issues automatically
ruff format src/ tests/       # Format code consistently
pytest -q                    # Run tests (must pass)

# 5. Document and commit
echo "feat: add new feature" >> SESSION.md
git add . && git commit -m "feat: add new feature"
```
</quality_gates>

<architecture_patterns>
## III. Architecture Patterns

### Layer Separation Pattern

```
------------------¬    ------------------¬    ------------------¬
¦   Data Layer    ¦    ¦  Core Logic     ¦    ¦ Presentation    ¦
¦                 ¦    ¦                 ¦    ¦                 ¦
¦ • I/O Operations¦----?¦ • Pure Logic    ¦----?¦ • Formatting    ¦
¦ • Validation    ¦    ¦ • Computations  ¦    ¦ • Error Display ¦
¦ • Error Convert ¦    ¦ • Fail Fast     ¦    ¦ • HTML/Reports  ¦
L------------------    L------------------    L------------------
```

### Boundary vs Logic (keep logic pure)

```python
from pathlib import Path

class ProcessingError(Exception): ...


def load_text(path: Path) -> str:
    """Boundary function: Handles I/O and converts low-level errors."""
    try:
        return path.read_text(encoding="utf-8")
    except (FileNotFoundError, UnicodeDecodeError) as e:
        raise ProcessingError(f"Error loading {path}: {e}") from e
```

```python
import ast


def analyze_content(text: str) -> dict:
    """Pure logic function: Assumes valid input, raises specific errors."""
    tree = ast.parse(text)  # May raise SyntaxError, which is expected to be handled upstream.
    funcs = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
    classes = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
    return {"functions": funcs, "classes": classes}
```

### Small Interface (pass only what's needed)

```python
def format_tree(files: list, show_comments: bool = False) -> str:
    """This function only needs a list of files and a boolean, not the whole config."""
    lines = []
    for f in files:
        line = f"+- {f.rel_path}"
        if show_comments and getattr(f, 'comment', None):
            line += f"  # {f.comment}"
        lines.append(line)

    if lines:
        lines[-1] = lines[-1].replace("+", "L", 1)
    return "\n".join(lines)
```
</architecture_patterns>

<error_handling>
## IV. Error Handling Strategy

### Exception Types by Layer
- **Core Layer**: `InsufficientDataError`, `DataValidationError`, `ColumnMappingError`
- **Processing Layer**: Re-raise core errors, add `ProcessingError` for workflow issues
- **Presentation Layer**: Catch all specific errors, log appropriately, show placeholders

### Error Handling Examples

**? BAD - Silent failures:**
```python
def compute_metrics(data):
    if data.empty:
        return None  # Silent failure
    # ... logic
```

**? GOOD - Fail fast:**
```python
def compute_metrics(data):
    if data.empty:
        raise InsufficientDataError("No data for metrics computation")
    # ... logic
```

**? GOOD - Centralized error handling:**
```python
def add_section(self, title, builder_func):
    try:
        section_data = builder_func()
        self._add_section_html(title, section_data)
    except InsufficientDataError as e:
        logger.info(f"Skipping section '{title}': {e}")  # Expected situation
        self._add_placeholder(title, "Insufficient data")
    except (DataValidationError, ProcessingError) as e:
        logger.warning(f"Data issue in section '{title}': {e}")  # Config problem
        self._add_placeholder(title, "Data error")
```

### Testing Exception Handling
```python
def test_compute_metrics_raises_insufficient_data():
    """Test that empty data raises appropriate exception."""
    empty_data = []

    with pytest.raises(InsufficientDataError, match="No data for metrics computation"):
        compute_metrics(empty_data)


def test_compute_metrics_raises_validation_error():
    """Test that invalid data raises appropriate exception."""
    invalid_data = ["not", "valid", "format"]

    with pytest.raises(DataValidationError, match="Invalid data format"):
        compute_metrics(invalid_data)
```
</error_handling>

<configuration_management>
## V. Configuration Management

### Extract-Transform-Pass Pattern

**? BAD: Hidden dependencies**
```python
def build_feature_section(cfg, ctx):
    # Function signature doesn't show what config fields are actually needed
    result = compute_feature_metrics(ctx.data, cfg)  # Hidden coupling
```

**? GOOD: Explicit dependencies**
```python
def build_feature_section(cfg, ctx):
    # Extract phase: Make dependencies explicit
    mapping_cfg = cfg.column_mapping
    feature_cfg = cfg.feature_settings

    # Transform phase: Call core with specific parameters
    result = compute_feature_metrics(
        data=ctx.data,
        id_column=mapping_cfg.id_field,
        value_column=mapping_cfg.value_field,
        min_samples=feature_cfg.min_samples
    )

    # Pass phase: Format and return
    formatted = format_feature_table(result)
    return create_table_section("Feature Analysis", formatted)
```

### Standard Section Builder Pattern
```python
def build_section_name(cfg, ctx):
    """
    Standard template for all build_* functions.

    Args:
        cfg: Application configuration object
        ctx: Runtime context with data

    Returns:
        Section object with formatted content

    Raises:
        InsufficientDataError: When input data is empty or invalid
        DataValidationError: When configuration is invalid
    """
    # Step 1: Extract parameters with type annotations
    mapping_cfg = cfg.column_mapping
    specific_cfg = cfg.specific_feature

    # Step 2: Check and analyze
    if ctx.data is None or len(ctx.data) == 0:
        raise InsufficientDataError("No data for section")

    result = core_analysis_function(ctx.data, mapping_cfg.field, specific_cfg.param)

    # Step 3: Format and return
    formatted = format_function(result)
    return create_section("Title", formatted)
```
</configuration_management>

<anti_patterns>
## VI. Critical Anti-patterns & Common Mistakes

### ? NEVER EVER: Dynamic Introspection
```python
# NEVER: Using getattr for dynamic method calls - creates silent failures
action = "delete"
getattr(self, f"{action}_item")()  # Fails silently if method doesn't exist
```

### ? Explicit Dispatch
```python
# ALWAYS: Use explicit dispatch with clear error handling
actions = {"delete": self.delete_item, "create": self.create_item}
if action in actions:
    actions[action]()
else:
    raise ValueError(f"Unknown action: {action}")
```

### ? CRITICAL: Broad Exception Handling
```python
# NEVER: Swallowing all exceptions hides critical bugs
try:
    result = do_critical_operation()
except Exception as e:
    print("Error occurred:", e)  # Masks real problems
    return None  # Silent failure
```

### ? Targeted Exception Handling
```python
# ALWAYS: Catch only what you can handle, let others bubble up
try:
    result = do_critical_operation()
except SpecificError as e:
    handle_specific_error(e)
    # Let other exceptions propagate for debugging
```

### ? CRITICAL: Global State Dependencies
```python
# NEVER: Hidden global dependencies break testability
CONFIG = {"threshold": 5}

def check_value(x):
    if x > CONFIG["threshold"]:  # Hidden dependency
        ...
```

### ? Explicit Dependencies
```python
# ALWAYS: Make all dependencies visible in function signature
def check_value(x, threshold=5):
    if x > threshold:
        ...
```

### ?? DECISION POINT: Simple Arguments vs Pydantic Models

### ? Use Simple Arguments For:
```python
# Data transformation, plotting, core logic, Jupyter-friendly functions
def plot_distribution(values: list[float], bins: int = 20, title: str = "") -> Figure:
    """Easy to use in notebooks, clear parameters"""
    pass

def compute_statistics(data: pd.DataFrame, column: str, method: str = "mean") -> float:
    """Core logic with minimal, explicit parameters"""
    pass

def transform_data(df: pd.DataFrame, normalize: bool = True, scale_factor: float = 1.0) -> pd.DataFrame:
    """Data transformation with simple, testable interface"""
    pass
```

### ? Use Pydantic Models For:
```python
# Cross-module coordination, 5+ related params, validation-critical scenarios
@dataclass
class AnalysisConfig:
    input_columns: list[str]
    output_format: str
    validation_rules: dict
    processing_options: dict
    error_handling: str

def generate_full_report(config: AnalysisConfig, data: pd.DataFrame) -> Report:
    """When coordinating multiple operations with complex validation"""
    pass

def process_pipeline(config: PipelineConfig) -> Results:
    """When you have many related settings that need validation"""
    pass
```

### ?? Decision Guidelines:
- **Simple args**: Can you easily call this in a notebook? < 5 parameters? Core computation?
- **Pydantic model**: Cross-module? Complex validation? 5+ related parameters?
- **Consistency rule**: Within the same submodule, stick to one approach

### ? Silent Failures
```python
# NEVER: Return None to signal errors - they get ignored
def find_user(username) -> User:
    user = db.lookup(username)
    if not user:
        return None  # Silent failure
    return user
```

### ? Explicit Error Handling
```python
# ALWAYS: Be explicit about error conditions
def find_user_optional(username: str) -> Optional[User]:
    """Returns None if not found - callers must handle this"""
    return db.lookup(username)

def find_user_required(username: str) -> User:
    """Raises exception if not found - use when user must exist"""
    user = db.lookup(username)
    if user is None:
        raise UserNotFoundError(f"User '{username}' not found")
    return user
```
</anti_patterns>

<project_context>
## VII. Project Context

### Architecture Flow
<!-- <fill_project_specific_workflow>
Describe your project's main workflow here. For example:
- Input Processing: How data enters the system
- Core Processing: Main business logic flow
- Output Generation: How results are produced
- Error Handling: How errors are managed across layers
</fill_project_specific_workflow> -->

### Module Mapping
*   **Core Logic**: `src/{{project_name}}/core/`
*   **Processing**: `src/{{project_name}}/processing/`
*   **Output Generation**: `src/{{project_name}}/formatting/`
*   **Data Models**: `src/{{project_name}}/models.py`

<!-- <fill_additional_modules>
Add project-specific modules here:
*   **Custom Module**: `src/{{project_name}}/custom/`
*   **Integration Layer**: `src/{{project_name}}/integrations/`
*   **Utils**: `src/{{project_name}}/utils/`
</fill_additional_modules> -->

### Data Flow Pattern
```
Configuration > Core Analysis > Formatting > Output Generation > Error Handling
      v              v             v              v               v
[Validation]   [Pure Logic]   [Styling]    [HTML/JSON]    [Graceful UX]
```

<!-- <fill_project_data_flow>
Customize this data flow for your project:
```
Input > Validation > Processing > Analysis > Output
  v        v           v           v        v
[Clean]  [Verify]   [Transform]  [Compute] [Format]
```
</fill_project_data_flow> -->

### Project-Specific Best Practices
<!-- <fill_project_conventions>
Add project-specific conventions here:
- Naming conventions for your domain
- Specific error types used in your project
- Domain-specific validation rules
- Integration patterns with external services
- Performance considerations for your use case
</fill_project_conventions> -->
</project_context>

<contribution_guide>
## VIII. Contribution & Logging

*   Tests are mandatory > see **[TESTS.md](TESTS.md)**
*   System design principles > see **[ARCHITECTURE.md](ARCHITECTURE.md)**
*   Track live progress in **[TODO.md](TODO.md)** (gitignored)
*   After completion, append notes to **[SESSION.md](SESSION.md)**
*   **Debugging Hint**: Check **[SESSION.md](SESSION.md)** for similar issues fixed previously

<!-- <fill_project_documentation>
Add project-specific documentation references:
*   Domain guide > see **[DOMAIN.md](DOMAIN.md)**
*   API documentation > see **[API.md](API.md)**
*   Deployment guide > see **[DEPLOY.md](DEPLOY.md)**
</fill_project_documentation> -->

### Design Decision Framework

**Question 1**: Can this logic be tested without external dependencies?
- **Yes**: Put in core layer
- **No**: Put in data/I/O layer

**Question 2**: Does this involve user-facing display formatting?
- **Yes**: Put in formatting layer
- **No**: Keep in core with standard output format

**Question 3**: Does this coordinate multiple core functions?
- **Yes**: Put in orchestration layer
- **No**: Keep as focused core function

**Question 4**: Does this handle multiple error types from lower layers?
- **Yes**: Put in presentation layer (error boundary)
- **No**: Let specific errors bubble up to appropriate handler

<!-- <fill_project_decision_questions>
Add project-specific design decision questions:
**Question 5**: Does this involve [domain-specific concern]?
- **Yes**: Put in [specific layer]
- **No**: Follow standard layer guidelines

**Question 6**: Does this require [project-specific integration]?
- **Yes**: Use [specific pattern]
- **No**: Follow core patterns
</fill_project_decision_questions> -->
</contribution_guide>

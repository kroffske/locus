# Locus - Code Context Analyzer for LLMs

**Locus** is a flexible tool for analyzing project structure and exporting codebase context in LLM-friendly formats. It helps you select and prepare the right code context for AI chat interactions.

[🇷🇺 Русская версия](README.ru.md)

## 🎯 Purpose

When working with LLMs (ChatGPT, Claude, etc.), you need to provide relevant code context. Locus helps you:

- 📊 **Analyze** project structure and visualize it as a tree
- 📦 **Export** code in modular groups optimized for LLM context windows
- 🎨 **Format** output as Markdown reports or plain text files
- 🔍 **Filter** files by patterns and depth to focus on what matters
- 📝 **Extract** annotations, docstrings, and function signatures
- 🎛️ **Configure** custom grouping rules via `.locus/settings.json`

## 🚀 Quick Start

### Installation

```bash
pip install -e .
```

### Basic Usage

```bash
# Analyze project and view in terminal
locus analyze

# Export to Markdown report
locus analyze -o report.md

# Export as modular text files (for LLM chat)
locus analyze -o output_dir

# Focus on specific directory
locus analyze src/ -o context.md
```

## 📋 Common Commands

### 1. Quick Overview

```bash
# Interactive view with summaries
locus analyze -p

# Show flat file list (grep-friendly)
locus analyze -p -f
```

### 2. Export for LLM Chat

```bash
# Export with modular grouping (recommended)
locus analyze -o llm_context

# This creates organized files like:
# - src_myapp_features.txt  (all features/* in one file)
# - src_myapp_main.py.txt   (main.py separately)
# - conf.txt                (all config files together)
```

### 3. Create Configuration

```bash
# Initialize project with default config
locus init --config

# Edit .locus/settings.json to customize grouping rules
```

### 4. Focused Export

```bash
# Only include Python files
locus analyze -o context --include "**/*.py"

# Exclude tests and migrations
locus analyze -o context --exclude "tests/**" "**/migrations/**"

# Limit import depth
locus analyze src/main.py -d 2 -o context.md
```

## 🎨 Output Modes

| Mode | Command | Use Case |
|------|---------|----------|
| **Interactive** | `locus analyze` | Quick terminal view |
| **Markdown Report** | `locus analyze -o report.md` | Single file documentation |
| **Modular Export** | `locus analyze -o output_dir` | LLM chat context (multiple organized files) |

## 🔧 Modular Export Configuration

Create `.locus/settings.json` to customize how files are grouped:

```json
{
  "modular_export": {
    "enabled": true,
    "max_lines_per_file": 5000,
    "grouping_rules": [
      {
        "pattern": "src/*/features/*",
        "group_by": "module",
        "depth": 3
      },
      {
        "pattern": "src/*/main.py",
        "group_by": "file",
        "separate": true
      }
    ],
    "default_depth": 2
  }
}
```

**Grouping strategies:**
- `module` - Group by module path (e.g., `src_myapp_features.txt`)
- `directory` - Group by directory at specified depth
- `file` - Each file separately when `separate: true`

## 📖 Example Workflow with LLM

### 1. Prepare context for new feature

```bash
# Export only relevant modules
locus analyze src/features src/utils -o llm_context --include "**/*.py"
```

### 2. Copy files to chat

```bash
# Files are already grouped by module
ls llm_context/
# src_features.txt
# src_utils.txt

# Copy content to your LLM chat:
cat llm_context/src_features.txt
```

### 3. Update code based on LLM response

```bash
# Use locus update to apply changes from LLM's markdown output
locus update < llm_response.md
```

## 🎓 Advanced Features

### Extract Annotations

```bash
# Include docstrings and signatures
locus analyze -o context -a

# Focus on interfaces
locus analyze -p --no-code
```

### Similarity Detection

```bash
# Find duplicate code patterns
locus analyze --similarity -o report.md

# Or use dedicated sim command
locus sim src/ -s ast -j similarity.json
```

### File Updates from Markdown

```bash
# Preview changes
locus update --dry-run < changes.md

# Apply changes with backup
locus update --backup < changes.md
```

## 📊 Output Examples

### Modular Export (for LLM)

```
output_dir/
├── src_myapp_features.txt      # All feature files grouped
├── src_myapp_utils.txt         # Utility files grouped
├── src_myapp_main.py.txt       # Main entry point (separate)
├── conf.txt                    # All config files together
└── README.md                   # Project README (optional)
```

Each file contains:
```python
# File: src/myapp/features/auth.py
# ==============================================================================

def login(username, password):
    """Authenticate user."""
    # ... implementation


# File: src/myapp/features/profile.py
# ==============================================================================

def get_profile(user_id):
    """Get user profile."""
    # ... implementation
```

## ⚙️ Command Reference

| Command | Description |
|---------|-------------|
| `locus analyze [paths]` | Analyze code and generate output |
| `locus init --config` | Create default configuration |
| `locus update` | Update files from markdown input |
| `locus sim` | Run similarity/duplicate detection |

### Key Options

| Option | Description |
|--------|-------------|
| `-o, --output PATH` | Output file (.md) or directory (modular export) |
| `-p, --headers` | Include file headers and summaries |
| `-a, --annotations` | Extract docstrings and signatures |
| `-d, --depth N` | Import depth: 0=off, 1=direct, 2=nested, -1=unlimited |
| `--include PATTERN` | Glob patterns to include (e.g., `**/*.py`) |
| `--exclude PATTERN` | Glob patterns to exclude (e.g., `tests/**`) |

## 🛠️ Development

### Quick Setup (using uv - recommended, faster)

```bash
# Install with dev dependencies (20x faster than pip)
make install-dev

# Run quality checks
make quality
```

### Manual Setup

```bash
# Install with dev dependencies
pip install -e .[dev]

# Run tests
pytest tests/ --ignore=tests/mcp -q

# Lint and format
ruff check --fix src/ tests/
ruff format src/ tests/
```

### Available Make Targets

Run `make help` to see all commands:
- `make install-dev` - Fast setup with uv
- `make test` - Run core tests
- `make quality` - Lint + format + test

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed development guide.

## 📚 Documentation

- [CONTRIBUTING.md](CONTRIBUTING.md) - Development setup and workflow
- [ARCHITECTURE.md](ARCHITECTURE.md) - System design and patterns
- [TESTS.md](TESTS.md) - Testing strategy
- [AGENTS.md](AGENTS.md) - AI agent guidelines

## 🔗 Use Cases

**For LLM Chat Context:**
- Export specific modules to provide focused context
- Group related files to fit in context windows
- Extract interfaces and signatures for API understanding

**For Code Analysis:**
- Visualize project structure
- Find duplicate code patterns
- Generate documentation

**For Code Updates:**
- Apply LLM-suggested changes via markdown
- Preview updates with dry-run mode
- Backup files before modifications

## 📝 License

MIT

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 💡 Tips

1. **Start small**: Use `locus analyze -p` to get overview first
2. **Use modular export**: `-o output_dir` is better than single file for LLMs
3. **Configure grouping**: Customize `.locus/settings.json` for your project structure
4. **Filter wisely**: Use `--include` and `--exclude` to reduce noise
5. **Check output size**: Large exports may exceed LLM context limits

---

Made with ❤️ for better LLM-human collaboration

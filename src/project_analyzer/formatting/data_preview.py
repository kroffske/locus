import os
import logging
import csv
import json
from typing import Set

logger = logging.getLogger(__name__)

# --- Optional Imports ---
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    import pyarrow.parquet as pq
    PYARROW_AVAILABLE = True
except ImportError:
    PYARROW_AVAILABLE = False

ALL_DATA_EXTENSIONS: Set[str] = {'.csv', '.json', '.parquet', '.tsv'}

def preview_data_file(file_path: str) -> str:
    """Generate a preview for a data file based on its extension."""
    if not os.path.isfile(file_path):
        return f"## Error: File not found\n\n`{file_path}`"

    _, ext = os.path.splitext(file_path)
    ext = ext.lower()

    header = f"## Preview: {os.path.basename(file_path)}\n"
    try:
        if ext == '.csv':
            return header + (_preview_csv_pandas(file_path) if PANDAS_AVAILABLE else _preview_csv_basic(file_path))
        if ext == '.tsv':
             return header + (_preview_csv_pandas(file_path, delimiter='\t') if PANDAS_AVAILABLE else _preview_csv_basic(file_path, delimiter='\t'))
        if ext == '.parquet':
            return header + (_preview_parquet(file_path) if PYARROW_AVAILABLE else "Preview requires `pyarrow`.")
        if ext == '.json':
            return header + _preview_json(file_path)
    except Exception as e:
        logger.error(f"Failed to preview data file '{file_path}': {e}", exc_info=True)
        return f"{header}\n**Error:** Could not generate preview. {type(e).__name__}: {e}"

    return f"{header}\nNo preview available for this file type."

# --- Specific Preview Functions ---

def _preview_csv_pandas(file_path: str, delimiter=',') -> str:
    """Preview CSV with pandas."""
    df = pd.read_csv(file_path, delimiter=delimiter, nrows=5)
    info = [
        f"- **Columns:** {df.shape[1]}",
        f"- **Column Names:** `{', '.join(df.columns)}`"
    ]
    return "\n".join(info) + f"\n\n### First 5 Rows\n\n{df.to_markdown(index=False)}"

def _preview_csv_basic(file_path: str, delimiter=',') -> str:
    """Basic CSV preview without pandas."""
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.reader(f, delimiter=delimiter)
        header = next(reader, [])
        rows = [row for _, row in zip(range(5), reader)]
    info = [
        f"- **Columns:** {len(header)}",
        f"- **Column Names:** `{', '.join(header)}`",
        f"- **Rows Previewed:** {len(rows)}"
    ]
    return "\n".join(info)

def _preview_parquet(file_path: str) -> str:
    """Preview Parquet file with pyarrow."""
    p_file = pq.ParquetFile(file_path)
    schema = p_file.schema
    info = [
        f"- **Rows:** {p_file.metadata.num_rows}",
        f"- **Columns:** {len(schema)}",
        f"- **Schema:**",
        "```",
    ]
    info.extend([f"  - {name}: {dtype}" for name, dtype in zip(schema.names, schema.types)])
    info.append("```")
    return "\n".join(info)

def _preview_json(file_path: str) -> str:
    """Preview JSON file."""
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content_sample = f.read(2048) # Read first 2KB
    
    try: # Try parsing as a single JSON object/array
        data = json.loads(content_sample)
        if isinstance(data, dict):
            keys = list(data.keys())
            return f"- **Type:** JSON Object\n- **Top-level keys:** `{', '.join(keys[:5])}`"
        elif isinstance(data, list):
            return f"- **Type:** JSON Array\n- **Number of items:** {len(data)}"
    except json.JSONDecodeError:
        try: # Try parsing as JSON Lines
            first_line = content_sample.splitlines()[0]
            data = json.loads(first_line)
            keys = list(data.keys())
            return f"- **Type:** JSON Lines\n- **Keys in first object:** `{', '.join(keys[:5])}`"
        except (json.JSONDecodeError, IndexError):
            return "Could not determine JSON structure (might be malformed or multi-line)."
    return "Could not determine JSON structure."

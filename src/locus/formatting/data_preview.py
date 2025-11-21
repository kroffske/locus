import csv
import json
import logging
import os
from typing import Set

logger = logging.getLogger(__name__)

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

ALL_DATA_EXTENSIONS: Set[str] = {".csv", ".json", ".parquet", ".tsv"}


def preview_data_file(file_path: str) -> str:
    """Generate a preview for a data file based on its extension."""
    if not os.path.isfile(file_path):
        return f"## Error: File not found: `{file_path}`"

    ext = os.path.splitext(file_path)[1].lower()
    header = f"## Preview: {os.path.basename(file_path)}\n"

    try:
        if ext == ".csv":
            return header + (
                _preview_csv_pandas(file_path)
                if PANDAS_AVAILABLE
                else _preview_csv_basic(file_path)
            )
        if ext == ".tsv":
            return header + (
                _preview_csv_pandas(file_path, "\t")
                if PANDAS_AVAILABLE
                else _preview_csv_basic(file_path, "\t")
            )
        if ext == ".parquet":
            return header + (
                _preview_parquet(file_path)
                if PYARROW_AVAILABLE
                else "Preview requires `pyarrow`."
            )
        if ext == ".json":
            return header + _preview_json(file_path)
    except Exception as e:
        logger.error(f"Failed to preview '{file_path}': {e}", exc_info=True)
        return f"{header}\n**Error:** Could not generate preview: {e}"
    return f"{header}\nNo preview available for this file type."


def _preview_csv_pandas(file_path: str, delimiter=",") -> str:
    df = pd.read_csv(file_path, delimiter=delimiter, nrows=5)
    info = (
        f"- **Columns:** {df.shape[1]}\n- **Column Names:** `{', '.join(df.columns)}`"
    )
    return f"{info}\n\n### First 5 Rows\n\n{df.to_markdown(index=False)}"


def _preview_csv_basic(file_path: str, delimiter=",") -> str:
    with open(file_path, encoding="utf-8", errors="ignore") as f:
        reader = csv.reader(f, delimiter=delimiter)
        header = next(reader, [])
    return f"- **Columns:** {len(header)}\n- **Column Names:** `{', '.join(header)}`"


def _preview_parquet(file_path: str) -> str:
    p_file = pq.ParquetFile(file_path)
    schema = p_file.schema
    info = [
        f"- **Rows:** {p_file.metadata.num_rows}",
        f"- **Columns:** {len(schema)}",
        "### Schema",
        "```",
    ]
    info.extend(
        [f"- {name}: {dtype}" for name, dtype in zip(schema.names, schema.types)]
    )
    info.append("```")
    return "\n".join(info)


def _preview_json(file_path: str) -> str:
    with open(file_path, encoding="utf-8", errors="ignore") as f:
        sample = f.read(2048)
    try:
        data = json.loads(sample)
        if isinstance(data, dict):
            return f"- **Type:** JSON Object\n- **Top-level keys:** `{', '.join(list(data.keys())[:5])}`"
        if isinstance(data, list):
            return f"- **Type:** JSON Array\n- **Items:** {len(data)}"
    except json.JSONDecodeError:
        try:
            first_line = sample.splitlines()[0]
            data = json.loads(first_line)
            return f"- **Type:** JSON Lines\n- **Keys in first object:** `{', '.join(list(data.keys())[:5])}`"
        except (json.JSONDecodeError, IndexError):
            return "Could not determine JSON structure."
    return "Could not determine JSON structure."

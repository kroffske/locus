from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class TargetSpecifier:
    """Represents a single target for analysis, including optional line ranges."""

    path: str
    line_ranges: List[Tuple[int, int]] = field(default_factory=list)


@dataclass
class FileInfo:
    """Represents information about a single file."""

    absolute_path: str
    relative_path: str
    filename: str
    module_name: Optional[str] = None
    is_init: bool = False
    is_empty: bool = False
    is_stub: bool = False
    is_data_preview: bool = False


@dataclass
class AnnotationInfo:
    """Represents extracted annotations (docstrings, signatures) for a file."""

    module_docstring: Optional[str] = None
    elements: Dict[str, Any] = field(default_factory=dict)
    imports: List[str] = field(default_factory=list)  # List of import statements


@dataclass
class FileAnalysis:
    """Combines FileInfo and analysis results for a single file."""

    file_info: FileInfo
    annotations: Optional[AnnotationInfo] = None
    comments: List[str] = field(default_factory=list)
    content: Optional[str] = None
    line_ranges: List[Tuple[int, int]] = field(default_factory=list)


@dataclass
class AnalysisResult:
    """Represents the overall result of a code analysis run."""

    project_path: str
    config_root_path: Optional[str] = None
    target_specs: List[TargetSpecifier] = field(default_factory=list)
    required_files: Dict[str, FileAnalysis] = field(default_factory=dict)  # Keyed by absolute path
    file_tree: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    project_readme_content: Optional[str] = None

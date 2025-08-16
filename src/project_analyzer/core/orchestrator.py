import os
import logging
from typing import List, Optional, Set

from . import scanner, resolver, processor
from ..models import AnalysisResult, TargetSpecifier, FileInfo, FileAnalysis
from ..utils.file_cache import FileCache
from ..utils import config, helpers

logger = logging.getLogger(__name__)

def analyze(
    project_path: str,
    target_specs: List[TargetSpecifier],
    max_depth: int,
    include_patterns: Optional[List[str]],
    exclude_patterns: Optional[List[str]]
) -> AnalysisResult:
    """
    Main high-level analysis function orchestrating the entire process.
    """
    result = AnalysisResult(project_path=project_path, target_specs=target_specs)
    file_cache = FileCache()

    # 1. Load Configuration
    ignore_patterns, allow_patterns = config.load_project_config(project_path)
    if not allow_patterns:
        allow_patterns = {'*.py', '*.md'} # Default if .claudeallow is missing
        logger.info(f"No .claudeallow file found, defaulting to: {allow_patterns}")

    # 2. Scan Directory and apply ignore/allow patterns
    try:
        scanned_files = scanner.scan_directory(project_path, ignore_patterns, allow_patterns)
        if not scanned_files:
            result.errors.append("Initial scan found no files matching the allow patterns.")
            return result
    except OSError as e:
        result.errors.append(f"Failed to scan directory {project_path}: {e}")
        return result

    # 3. Create initial file maps and tree from all visible files
    all_file_infos: Dict[str, FileInfo] = {} # abs_path -> FileInfo
    for abs_path in scanned_files:
        rel_path = helpers.get_relative_path(abs_path, project_path)
        module_name = helpers.get_module_name(rel_path) if rel_path.endswith('.py') else None
        all_file_infos[abs_path] = FileInfo(
            absolute_path=abs_path,
            relative_path=rel_path,
            filename=os.path.basename(rel_path),
            module_name=module_name,
            is_init=os.path.basename(rel_path) == '__init__.py'
        )
    result.file_tree = helpers.build_file_tree([fi for fi in all_file_infos.values()])
    module_to_file_map = {fi.module_name: path for path, fi in all_file_infos.items() if fi.module_name}

    # 4. Determine Initial Targets
    initial_targets_abs: Set[str] = set()
    for spec in target_specs:
        abs_target_path = os.path.abspath(os.path.join(project_path, spec.path))
        if os.path.isdir(abs_target_path):
             for path in scanned_files:
                 if path.startswith(abs_target_path):
                     initial_targets_abs.add(path)
        elif os.path.isfile(abs_target_path):
            if abs_target_path in all_file_infos:
                initial_targets_abs.add(abs_target_path)
            else:
                result.errors.append(f"Target file '{spec.path}' was specified but is ignored by config.")
    
    if not initial_targets_abs:
        if target_specs:
            result.errors.append("No specified targets were found after applying ignore/allow rules.")
        else: # Default mode, analyze all
            initial_targets_abs.update(scanned_files)

    # 5. Resolve Dependencies if necessary
    if max_depth != 0:
        required_abs_paths = resolver.resolve_dependencies(
            initial_targets_abs, all_file_infos, module_to_file_map, max_depth
        )
    else:
        required_abs_paths = initial_targets_abs
        logger.info("Dependency resolution skipped (max_depth=0).")

    # 6. Process each required file
    for abs_path in sorted(list(required_abs_paths)):
        file_info = all_file_infos.get(abs_path)
        if not file_info:
            logger.warning(f"Required path {abs_path} not found in file info map. Skipping.")
            continue
        
        try:
            analysis_data = processor.process_file(file_info, file_cache)
            result.required_files[abs_path] = analysis_data
        except Exception as e:
            error_msg = f"Failed to process file '{file_info.relative_path}': {e}"
            logger.error(error_msg, exc_info=True)
            result.errors.append(error_msg)
            # Still add a file analysis object to indicate it was processed but failed
            result.required_files[abs_path] = FileAnalysis(
                file_info=file_info,
                content=f"# ERROR: Could not process file.\n# {e}"
            )

    logger.info(f"Analysis complete. Processed {len(result.required_files)} files.")
    return result

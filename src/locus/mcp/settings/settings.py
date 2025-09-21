from __future__ import annotations

import os
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _load_yaml_config(path: Path) -> dict:
    try:
        import yaml

        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
    except ImportError:
        print(
            "PyYAML not installed, cannot load YAML settings. Please run: pip install 'locus-analyzer[mcp]'"
        )
    except Exception:
        pass
    return {}


class EmbeddingSettings(BaseSettings):
    provider: str = "huggingface"
    model_name: str = "nomic-ai/CodeRankEmbed-v1"
    trust_remote_code: bool = True
    batch_size: int = 32  # New: tunable batch size for embeddings
    dimensions: int = 1024


class VectorStoreSettings(BaseSettings):
    type: str = "lancedb"
    path: str = ".locus_mcp/lancedb"


class IndexSettings(BaseSettings):
    chunking_strategy: str = "lines"  # New: "lines" or "semantic"
    max_lines: int = 150
    overlap: int = 25


class WatcherSettings(BaseSettings):
    enabled: bool = True
    debounce_ms: int = 2000


class MCPSettings(BaseSettings):
    transport: str = "stdio"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_nested_delimiter="__", extra="ignore"
    )
    embedding: EmbeddingSettings = Field(default_factory=EmbeddingSettings)
    vector_store: VectorStoreSettings = Field(default_factory=VectorStoreSettings)
    index: IndexSettings = Field(default_factory=IndexSettings)
    watcher: WatcherSettings = Field(default_factory=WatcherSettings)
    mcp: MCPSettings = Field(default_factory=MCPSettings)


def load_settings() -> Settings:
    """Load settings from YAML files and environment variables."""
    profile = os.environ.get("LCS_PROFILES", "local")
    base_path = Path("src/locus/mcp/settings/settings.yaml")
    profile_path = Path(f"src/locus/mcp/settings/settings-{profile}.yaml")

    config_data = {}
    config_data.update(_load_yaml_config(base_path))
    config_data.update(_load_yaml_config(profile_path))

    return Settings.model_validate(config_data)

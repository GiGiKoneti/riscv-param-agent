"""
Configuration management for RISC-V Parameter Extractor.

This module handles loading and validating configuration from YAML files
using Pydantic for type safety and validation.
"""

from typing import Optional, Literal
from pathlib import Path
import yaml
from pydantic import BaseModel, Field, field_validator


class ModelConfig(BaseModel):
    """Model configuration settings."""
    primary: str = Field(default="gemini/gemini-2.5-flash", description="Primary LLM model")
    secondary: str = Field(default="ollama_chat/llama3.1", description="Secondary LLM model")
    temperature: float = Field(default=0.0, ge=0.0, le=2.0, description="Model temperature")
    max_tokens: int = Field(default=4000, gt=0, description="Maximum tokens per request")
    retry_attempts: int = Field(default=5, ge=1, description="Number of retry attempts")
    retry_delay: int = Field(default=5, ge=1, description="Delay between retries (seconds)")


class ExtractionConfig(BaseModel):
    """Extraction pipeline settings."""
    chunk_size: int = Field(default=3000, gt=0, description="Text chunk size in tokens")
    overlap: int = Field(default=200, ge=0, description="Overlap between chunks")
    num_examples: int = Field(default=12, gt=0, description="Number of UDB examples")
    balanced_examples: bool = Field(default=True, description="Use balanced examples")


class ValidationConfig(BaseModel):
    """Validation settings."""
    similarity_threshold: float = Field(default=0.85, ge=0.0, le=1.0, description="Fuzzy match threshold")
    enable_hallucination_detection: bool = Field(default=False, description="Enable hallucination detection")
    enable_tag_generation: bool = Field(default=False, description="Enable tag generation")


class OutputConfig(BaseModel):
    """Output settings."""
    default_path: str = Field(default="outputs/extracted_parameters.yaml", description="Default output path")
    comparison_path: str = Field(default="outputs/model_comparison.yaml", description="Comparison output path")
    validation_path: str = Field(default="outputs/validation_report.yaml", description="Validation output path")
    format: Literal["yaml", "json"] = Field(default="yaml", description="Output format")


class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(default="INFO", description="Log level")
    format: Literal["rich", "standard"] = Field(default="rich", description="Log format")
    file: Optional[str] = Field(default=None, description="Optional log file path")


class PathsConfig(BaseModel):
    """Path configuration."""
    udb_examples: str = Field(default="data/udb_examples.yaml", description="UDB examples path")
    specs_dir: str = Field(default="specs/", description="Specs directory")
    outputs_dir: str = Field(default="outputs/", description="Outputs directory")


class Config(BaseModel):
    """Main configuration class."""
    models: ModelConfig = Field(default_factory=ModelConfig)
    extraction: ExtractionConfig = Field(default_factory=ExtractionConfig)
    validation: ValidationConfig = Field(default_factory=ValidationConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    paths: PathsConfig = Field(default_factory=PathsConfig)
    
    @field_validator('paths')
    @classmethod
    def validate_paths(cls, v: PathsConfig) -> PathsConfig:
        """Ensure output directory exists."""
        Path(v.outputs_dir).mkdir(parents=True, exist_ok=True)
        return v


def load_config(config_path: str = "config.yaml") -> Config:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Validated configuration object
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If config is invalid
    """
    config_file = Path(config_path)
    
    if not config_file.exists():
        # Return default config if file doesn't exist
        return Config()
    
    with open(config_file, 'r') as f:
        config_data = yaml.safe_load(f)
    
    return Config(**config_data)


def save_config(config: Config, config_path: str = "config.yaml") -> None:
    """
    Save configuration to YAML file.
    
    Args:
        config: Configuration object
        config_path: Path to save configuration
    """
    with open(config_path, 'w') as f:
        yaml.safe_dump(config.model_dump(), f, sort_keys=False, default_flow_style=False)


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """
    Get global configuration instance.
    
    Returns:
        Configuration object
    """
    global _config
    if _config is None:
        _config = load_config()
    return _config


def reload_config(config_path: str = "config.yaml") -> Config:
    """
    Reload configuration from file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Reloaded configuration object
    """
    global _config
    _config = load_config(config_path)
    return _config

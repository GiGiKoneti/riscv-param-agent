"""
Tests for configuration management.
"""

import pytest
import tempfile
import yaml
from pathlib import Path

from src.config.settings import (
    Config,
    ModelConfig,
    ExtractionConfig,
    ValidationConfig,
    OutputConfig,
    LoggingConfig,
    PathsConfig,
    load_config,
    save_config,
    get_config,
    reload_config
)


class TestModelConfig:
    """Test ModelConfig class."""
    
    def test_model_config_defaults(self):
        """Test default model configuration."""
        config = ModelConfig()
        assert config.primary == "gemini/gemini-2.5-flash"
        assert config.temperature == 0.0
        assert config.max_tokens == 4000
    
    def test_model_config_custom(self):
        """Test custom model configuration."""
        config = ModelConfig(
            primary="custom/model",
            temperature=0.5,
            max_tokens=2000
        )
        assert config.primary == "custom/model"
        assert config.temperature == 0.5
        assert config.max_tokens == 2000


class TestExtractionConfig:
    """Test ExtractionConfig class."""
    
    def test_extraction_config_defaults(self):
        """Test default extraction configuration."""
        config = ExtractionConfig()
        assert config.chunk_size == 3000
        assert config.overlap == 200
        assert config.num_examples == 12
    
    def test_extraction_config_validation(self):
        """Test extraction configuration validation."""
        with pytest.raises(ValueError):
            ExtractionConfig(chunk_size=-1)


class TestConfig:
    """Test main Config class."""
    
    def test_config_defaults(self):
        """Test default configuration."""
        config = Config()
        assert isinstance(config.models, ModelConfig)
        assert isinstance(config.extraction, ExtractionConfig)
        assert isinstance(config.validation, ValidationConfig)
    
    def test_config_from_dict(self):
        """Test creating config from dictionary."""
        data = {
            "models": {"primary": "test/model"},
            "extraction": {"chunk_size": 5000}
        }
        config = Config(**data)
        assert config.models.primary == "test/model"
        assert config.extraction.chunk_size == 5000


class TestConfigIO:
    """Test configuration I/O operations."""
    
    def test_load_config_default(self):
        """Test loading default config when file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "nonexistent.yaml"
            config = load_config(str(config_path))
            assert isinstance(config, Config)
    
    def test_save_and_load_config(self):
        """Test saving and loading configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test_config.yaml"
            
            # Create and save config
            original = Config(
                models=ModelConfig(primary="test/model"),
                extraction=ExtractionConfig(chunk_size=5000)
            )
            save_config(original, str(config_path))
            
            # Load and verify
            loaded = load_config(str(config_path))
            assert loaded.models.primary == "test/model"
            assert loaded.extraction.chunk_size == 5000
    
    def test_config_yaml_format(self):
        """Test that saved config is valid YAML."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test_config.yaml"
            
            config = Config()
            save_config(config, str(config_path))
            
            # Verify YAML is valid
            with open(config_path, 'r') as f:
                data = yaml.safe_load(f)
            
            assert 'models' in data
            assert 'extraction' in data
            assert 'validation' in data


class TestGlobalConfig:
    """Test global configuration management."""
    
    def test_get_config_singleton(self):
        """Test that get_config returns same instance."""
        config1 = get_config()
        config2 = get_config()
        assert config1 is config2
    
    def test_reload_config(self):
        """Test reloading configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test_config.yaml"
            
            # Save custom config
            custom = Config(models=ModelConfig(primary="custom/model"))
            save_config(custom, str(config_path))
            
            # Reload
            reloaded = reload_config(str(config_path))
            assert reloaded.models.primary == "custom/model"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

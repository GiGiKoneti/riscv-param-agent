"""
Tests for UDB examples loader.
"""

import pytest
import yaml
from pathlib import Path
from src.loaders.udb_loader import UDBExamplesLoader, UDBExample, load_udb_examples


class TestUDBExamplesLoader:
    """Test UDB examples loading."""
    
    def test_loader_with_valid_file(self, tmp_path):
        """Test loading valid UDB examples."""
        examples_file = tmp_path / "examples.yaml"
        examples_data = {
            "examples": [
                {
                    "name": "test_param",
                    "description": "Test parameter",
                    "param_type": "integer",
                    "classification": "named",
                    "implementation_defined": False,
                    "source_quote": "Test quote"
                }
            ]
        }
        
        with open(examples_file, 'w') as f:
            yaml.dump(examples_data, f)
        
        loader = UDBExamplesLoader(str(examples_file))
        assert len(loader.examples) == 1
        assert loader.examples[0].name == "test_param"
    
    def test_loader_with_nonexistent_file(self):
        """Test loader with non-existent file."""
        loader = UDBExamplesLoader("nonexistent.yaml")
        assert len(loader.examples) == 0
    
    def test_get_examples(self, tmp_path):
        """Test getting a subset of examples."""
        examples_file = tmp_path / "examples.yaml"
        examples_data = {
            "examples": [
                {"name": f"param{i}", "description": f"Param {i}", 
                 "param_type": "integer", "classification": "named",
                 "implementation_defined": False}
                for i in range(20)
            ]
        }
        
        with open(examples_file, 'w') as f:
            yaml.dump(examples_data, f)
        
        loader = UDBExamplesLoader(str(examples_file))
        examples = loader.get_examples(num_examples=5)
        
        assert len(examples) == 5
    
    def test_get_examples_by_classification(self, tmp_path):
        """Test filtering examples by classification."""
        examples_file = tmp_path / "examples.yaml"
        examples_data = {
            "examples": [
                {"name": "named1", "description": "Named", "param_type": "integer",
                 "classification": "named", "implementation_defined": False},
                {"name": "unnamed1", "description": "Unnamed", "param_type": "integer",
                 "classification": "unnamed", "implementation_defined": True},
                {"name": "named2", "description": "Named", "param_type": "integer",
                 "classification": "named", "implementation_defined": False},
            ]
        }
        
        with open(examples_file, 'w') as f:
            yaml.dump(examples_data, f)
        
        loader = UDBExamplesLoader(str(examples_file))
        named_examples = loader.get_examples(classification="named")
        
        assert len(named_examples) == 2
        assert all(ex.classification == "named" for ex in named_examples)
    
    def test_format_for_prompt(self, tmp_path):
        """Test formatting examples for LLM prompt."""
        examples_file = tmp_path / "examples.yaml"
        examples_data = {
            "examples": [
                {
                    "name": "test_param",
                    "description": "Test parameter",
                    "param_type": "integer",
                    "classification": "named",
                    "implementation_defined": False,
                    "source_quote": "Test quote",
                    "constraints": [{"rule": "Must be 12 bits", "is_hard_constraint": True}]
                }
            ]
        }
        
        with open(examples_file, 'w') as f:
            yaml.dump(examples_data, f)
        
        loader = UDBExamplesLoader(str(examples_file))
        formatted = loader.format_for_prompt(num_examples=1)
        
        assert "test_param" in formatted
        assert "Test parameter" in formatted
        assert "integer" in formatted
        assert "named" in formatted
        assert "Must be 12 bits" in formatted
    
    def test_get_balanced_examples(self, tmp_path):
        """Test getting balanced examples across classifications."""
        examples_file = tmp_path / "examples.yaml"
        examples_data = {
            "examples": [
                {"name": f"named{i}", "description": "Named", "param_type": "integer",
                 "classification": "named", "implementation_defined": False}
                for i in range(5)
            ] + [
                {"name": f"unnamed{i}", "description": "Unnamed", "param_type": "integer",
                 "classification": "unnamed", "implementation_defined": True}
                for i in range(5)
            ] + [
                {"name": f"config{i}", "description": "Config", "param_type": "integer",
                 "classification": "configuration-dependent", "implementation_defined": True}
                for i in range(5)
            ]
        }
        
        with open(examples_file, 'w') as f:
            yaml.dump(examples_data, f)
        
        loader = UDBExamplesLoader(str(examples_file))
        formatted = loader.get_balanced_examples(num_examples=9)
        
        # Should have 3 of each type
        assert "[NAMED]" in formatted
        assert "[UNNAMED]" in formatted
        assert "[CONFIGURATION-DEPENDENT]" in formatted
    
    def test_udb_example_dataclass(self):
        """Test UDBExample dataclass."""
        example = UDBExample(
            name="test",
            description="Test param",
            param_type="integer",
            classification="named",
            implementation_defined=False,
            source_quote="Quote",
            constraints=[{"rule": "Test rule"}]
        )
        
        assert example.name == "test"
        assert example.param_type == "integer"
        assert example.classification == "named"
        assert len(example.constraints) == 1


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    def test_load_udb_examples_function(self, tmp_path):
        """Test load_udb_examples convenience function."""
        examples_file = tmp_path / "examples.yaml"
        examples_data = {
            "examples": [
                {"name": "param1", "description": "Param 1", "param_type": "integer",
                 "classification": "named", "implementation_defined": False}
            ]
        }
        
        with open(examples_file, 'w') as f:
            yaml.dump(examples_data, f)
        
        formatted = load_udb_examples(str(examples_file), num_examples=1, balanced=False)
        
        assert "param1" in formatted
        assert "Param 1" in formatted


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

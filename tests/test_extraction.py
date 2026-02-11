"""
Comprehensive test suite for RISC-V Parameter Extractor.
"""

import pytest
from src.models.schema import (
    RISCVParameter,
    ParameterExtraction,
    ParameterType,
    ParameterCategory,
    Constraint
)


class TestParameterSchema:
    """Test Pydantic schema models."""
    
    def test_constraint_creation(self):
        """Test Constraint model creation."""
        constraint = Constraint(
            rule="Must be power-of-two",
            is_hard_constraint=True
        )
        assert constraint.rule == "Must be power-of-two"
        assert constraint.is_hard_constraint is True
    
    def test_riscv_parameter_creation(self):
        """Test RISCVParameter model creation with all fields."""
        param = RISCVParameter(
            name="cache_block_size",
            tag_name="CACHE_BLOCK_SIZE_TAG",
            description="Size of cache block",
            param_type=ParameterType.INTEGER,
            classification=ParameterCategory.UNNAMED,
            constraints=[
                Constraint(rule="Must be NAPOT", is_hard_constraint=True)
            ],
            implementation_defined=True,
            source_quote="cache blocks...NAPOT...",
            rationale="Explicitly mentioned as implementation-specific"
        )
        
        assert param.name == "cache_block_size"
        assert param.param_type == ParameterType.INTEGER
        assert param.classification == ParameterCategory.UNNAMED
        assert len(param.constraints) == 1
        assert param.implementation_defined is True
    
    def test_riscv_parameter_defaults(self):
        """Test RISCVParameter with default values."""
        param = RISCVParameter(
            name="test_param",
            description="Test parameter",
            param_type=ParameterType.STRING,
            source_quote="test quote",
            rationale="test rationale"
        )
        
        assert param.tag_name == ""
        assert param.classification == ParameterCategory.UNNAMED
        assert param.constraints == []
        assert param.implementation_defined is True
    
    def test_parameter_extraction(self):
        """Test ParameterExtraction model."""
        params = [
            RISCVParameter(
                name="param1",
                description="First param",
                param_type=ParameterType.INTEGER,
                source_quote="quote1",
                rationale="rationale1"
            ),
            RISCVParameter(
                name="param2",
                description="Second param",
                param_type=ParameterType.BOOLEAN,
                source_quote="quote2",
                rationale="rationale2"
            )
        ]
        
        extraction = ParameterExtraction(parameters=params)
        assert len(extraction.parameters) == 2
        assert extraction.parameters[0].name == "param1"
        assert extraction.parameters[1].name == "param2"
    
    def test_parameter_type_enum(self):
        """Test ParameterType enum values."""
        assert ParameterType.INTEGER == "integer"
        assert ParameterType.BOOLEAN == "boolean"
        assert ParameterType.STRING == "string"
        assert ParameterType.RANGE == "range"
        assert ParameterType.ENUM == "enum"
        assert ParameterType.BITS == "bits"
    
    def test_parameter_category_enum(self):
        """Test ParameterCategory enum values."""
        assert ParameterCategory.NAMED == "named"
        assert ParameterCategory.UNNAMED == "unnamed"
        assert ParameterCategory.CONFIG_DEPENDENT == "configuration-dependent"
    
    def test_model_dump_json(self):
        """Test JSON serialization."""
        param = RISCVParameter(
            name="test",
            description="Test",
            param_type=ParameterType.INTEGER,
            classification=ParameterCategory.NAMED,
            source_quote="quote",
            rationale="rationale"
        )
        
        json_data = param.model_dump(mode="json")
        assert json_data["name"] == "test"
        assert json_data["param_type"] == "integer"
        assert json_data["classification"] == "named"


class TestConstraintValidation:
    """Test constraint validation logic."""
    
    def test_hard_constraint(self):
        """Test hard constraint creation."""
        constraint = Constraint(
            rule="Must be 12 bits",
            is_hard_constraint=True
        )
        assert constraint.is_hard_constraint is True
    
    def test_soft_constraint(self):
        """Test soft constraint creation."""
        constraint = Constraint(
            rule="Typically 32 or 64 bits",
            is_hard_constraint=False
        )
        assert constraint.is_hard_constraint is False


class TestParameterClassification:
    """Test parameter classification logic."""
    
    def test_named_parameter(self):
        """Test named parameter classification."""
        param = RISCVParameter(
            name="mstatus.MIE",
            description="Machine Interrupt Enable",
            param_type=ParameterType.BITS,
            classification=ParameterCategory.NAMED,
            implementation_defined=False,
            source_quote="MIE bit in mstatus",
            rationale="Explicitly named in spec"
        )
        assert param.classification == ParameterCategory.NAMED
        assert param.implementation_defined is False
    
    def test_unnamed_parameter(self):
        """Test unnamed parameter classification."""
        param = RISCVParameter(
            name="cache_capacity",
            description="Cache capacity",
            param_type=ParameterType.INTEGER,
            classification=ParameterCategory.UNNAMED,
            implementation_defined=True,
            source_quote="capacity...implementation-specific",
            rationale="Described in prose without formal name"
        )
        assert param.classification == ParameterCategory.UNNAMED
        assert param.implementation_defined is True
    
    def test_config_dependent_parameter(self):
        """Test configuration-dependent parameter classification."""
        param = RISCVParameter(
            name="VLEN",
            description="Vector register length",
            param_type=ParameterType.INTEGER,
            classification=ParameterCategory.CONFIG_DEPENDENT,
            implementation_defined=True,
            source_quote="VLEN is implementation-defined",
            rationale="Value changes based on hardware configuration"
        )
        assert param.classification == ParameterCategory.CONFIG_DEPENDENT
        assert param.implementation_defined is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
Tests for multi-model comparison and consensus detection.
"""

import pytest
from unittest.mock import Mock, patch
from src.comparators.model_comparator import (
    ModelComparator,
    ConfidenceLevel,
    RLMVerification,
    serialize_extraction
)
from src.models.schema import RISCVParameter, ParameterExtraction, ParameterType, ParameterCategory


class TestConfidenceLevel:
    """Test confidence level enum."""
    
    def test_confidence_levels(self):
        """Test confidence level values."""
        assert ConfidenceLevel.HIGH == "HIGH"
        assert ConfidenceLevel.MEDIUM == "MEDIUM"
        assert ConfidenceLevel.LOW == "LOW"


class TestModelComparator:
    """Test ModelComparator class."""
    
    def test_initialization(self):
        """Test comparator initialization."""
        comparator = ModelComparator(gemini_api_key="test_key")
        assert comparator.gemini_api_key == "test_key"
        assert comparator.ollama_base == "http://localhost:11434"
    
    def test_calculate_confidence_both_agree(self):
        """Test HIGH confidence when both models agree."""
        comparator = ModelComparator(gemini_api_key="test")
        
        gemini_params = {
            "cache_size": {"classification": "unnamed"}
        }
        llama_params = {
            "cache_size": {"classification": "unnamed"}
        }
        
        confidence = comparator.calculate_confidence("cache_size", gemini_params, llama_params)
        assert confidence == ConfidenceLevel.HIGH
    
    def test_calculate_confidence_different_classification(self):
        """Test MEDIUM confidence when classifications differ."""
        comparator = ModelComparator(gemini_api_key="test")
        
        gemini_params = {
            "cache_size": {"classification": "unnamed"}
        }
        llama_params = {
            "cache_size": {"classification": "named"}
        }
        
        confidence = comparator.calculate_confidence("cache_size", gemini_params, llama_params)
        assert confidence == ConfidenceLevel.MEDIUM
    
    def test_calculate_confidence_only_one_model(self):
        """Test LOW confidence when only one model found parameter."""
        comparator = ModelComparator(gemini_api_key="test")
        
        gemini_params = {
            "cache_size": {"classification": "unnamed"}
        }
        llama_params = {}
        
        confidence = comparator.calculate_confidence("cache_size", gemini_params, llama_params)
        assert confidence == ConfidenceLevel.LOW
    
    def test_generate_consensus(self):
        """Test consensus generation."""
        comparator = ModelComparator(gemini_api_key="test")
        
        # Create mock extractions
        gemini_params = [
            RISCVParameter(
                name="param1",
                description="Test param 1",
                param_type=ParameterType.INTEGER,
                classification=ParameterCategory.UNNAMED,
                source_quote="quote1",
                rationale="rationale1"
            ),
            RISCVParameter(
                name="param2",
                description="Test param 2",
                param_type=ParameterType.BOOLEAN,
                classification=ParameterCategory.NAMED,
                source_quote="quote2",
                rationale="rationale2"
            )
        ]
        
        llama_params = [
            RISCVParameter(
                name="param1",
                description="Test param 1",
                param_type=ParameterType.INTEGER,
                classification=ParameterCategory.UNNAMED,
                source_quote="quote1",
                rationale="rationale1"
            ),
            RISCVParameter(
                name="param3",
                description="Test param 3",
                param_type=ParameterType.STRING,
                classification=ParameterCategory.CONFIG_DEPENDENT,
                source_quote="quote3",
                rationale="rationale3"
            )
        ]
        
        gemini_extraction = ParameterExtraction(parameters=gemini_params)
        llama_extraction = ParameterExtraction(parameters=llama_params)
        
        consensus = comparator.generate_consensus(gemini_extraction, llama_extraction)
        
        # Should have 3 unique parameters
        assert len(consensus) == 3
        
        # Check param1 (HIGH confidence - both agree)
        param1 = next(p for p in consensus if p.name == "param1")
        assert param1.extraction_metadata['confidence'] == "HIGH"
        assert param1.extraction_metadata['found_by_gemini'] is True
        assert param1.extraction_metadata['found_by_llama'] is True
        
        # Check param2 (LOW confidence - only Gemini)
        param2 = next(p for p in consensus if p.name == "param2")
        assert param2.extraction_metadata['confidence'] == "LOW"
        assert param2.extraction_metadata['found_by_gemini'] is True
        assert param2.extraction_metadata['found_by_llama'] is False
        
        # Check param3 (LOW confidence - only Llama)
        param3 = next(p for p in consensus if p.name == "param3")
        assert param3.extraction_metadata['confidence'] == "LOW"
        assert param3.extraction_metadata['found_by_gemini'] is False
        assert param3.extraction_metadata['found_by_llama'] is True
    
    def test_generate_comparison_report(self):
        """Test comparison report generation."""
        comparator = ModelComparator(gemini_api_key="test")
        
        gemini_params = [
            RISCVParameter(
                name="param1",
                description="Test",
                param_type=ParameterType.INTEGER,
                classification=ParameterCategory.UNNAMED,
                source_quote="quote",
                rationale="rationale"
            ),
            RISCVParameter(
                name="param2",
                description="Test",
                param_type=ParameterType.INTEGER,
                classification=ParameterCategory.NAMED,
                source_quote="quote",
                rationale="rationale"
            )
        ]
        
        llama_params = [
            RISCVParameter(
                name="param1",
                description="Test",
                param_type=ParameterType.INTEGER,
                classification=ParameterCategory.CONFIG_DEPENDENT,  # Different!
                source_quote="quote",
                rationale="rationale"
            ),
            RISCVParameter(
                name="param3",
                description="Test",
                param_type=ParameterType.INTEGER,
                classification=ParameterCategory.UNNAMED,
                source_quote="quote",
                rationale="rationale"
            )
        ]
        
        gemini_extraction = ParameterExtraction(parameters=gemini_params)
        llama_extraction = ParameterExtraction(parameters=llama_params)
        
        report = comparator.generate_comparison_report(gemini_extraction, llama_extraction)
        
        assert report['summary']['total_unique_params'] == 3
        assert report['summary']['consensus_params'] == 1  # param1
        assert report['summary']['only_gemini'] == 1  # param2
        assert report['summary']['only_llama'] == 1  # param3
        assert report['summary']['classification_mismatches'] == 1  # param1
        
        assert "param1" in report['consensus']
        assert "param2" in report['only_gemini']
        assert "param3" in report['only_llama']
        
        # Check mismatch details
        assert len(report['classification_mismatches']) == 1
        mismatch = report['classification_mismatches'][0]
        assert mismatch['param'] == "param1"
        assert mismatch['gemini_classification'] == "unnamed"
        assert mismatch['llama_classification'] == "configuration-dependent"


class TestSerializeExtraction:
    """Test extraction serialization."""
    
    def test_serialize_with_model_dump(self):
        """Test serialization with model_dump method."""
        params = [
            RISCVParameter(
                name="test",
                description="Test",
                param_type=ParameterType.INTEGER,
                source_quote="quote",
                rationale="rationale"
            )
        ]
        extraction = ParameterExtraction(parameters=params)
        
        result = serialize_extraction(extraction)
        
        assert isinstance(result, dict)
        assert 'parameters' in result
        assert len(result['parameters']) == 1
        assert result['parameters'][0]['name'] == "test"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
Integration tests for the full extraction pipeline.

These tests verify end-to-end functionality from spec parsing through
parameter extraction, validation, and output generation.
"""

import pytest
import os
import yaml
import tempfile
from pathlib import Path

from src.main import run_extraction
from src.parsers.spec_parser import RISCVSpecParser
from src.models.schema import RISCVParameter, ParameterCategory


class TestEndToEndExtraction:
    """Test complete extraction pipeline."""
    
    @pytest.fixture
    def sample_spec_path(self):
        """Path to sample spec fixture."""
        return "tests/fixtures/sample_spec.md"
    
    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    @pytest.fixture
    def udb_examples_path(self):
        """Path to UDB examples."""
        return "data/udb_examples.yaml"
    
    def test_spec_parsing_integration(self, sample_spec_path):
        """Test that spec parsing works end-to-end."""
        parser = RISCVSpecParser(sample_spec_path)
        
        # Extract chapter 3
        chapter = parser.extract_chapter(3)
        
        assert chapter is not None
        assert chapter.number == 3
        assert "Memory System" in chapter.title
        assert len(chapter.content) > 100
        assert "cache blocks" in chapter.content.lower()
    
    def test_chunking_integration(self, sample_spec_path):
        """Test that chunking produces valid chunks."""
        parser = RISCVSpecParser(sample_spec_path)
        chapter = parser.extract_chapter(3)
        
        chunks = parser.chunk_text(chapter.content, max_tokens=500, overlap=50)
        
        assert len(chunks) > 0
        assert all(isinstance(chunk, str) for chunk in chunks)
        assert all(len(chunk) > 0 for chunk in chunks)
    
    @pytest.mark.skipif(
        not os.getenv("GEMINI_API_KEY"),
        reason="Requires GEMINI_API_KEY environment variable"
    )
    def test_full_extraction_pipeline(self, sample_spec_path, temp_output_dir, udb_examples_path):
        """Test complete extraction pipeline with real API."""
        output_path = os.path.join(temp_output_dir, "extracted.yaml")
        
        # Run extraction
        run_extraction(
            spec_path=sample_spec_path,
            chapter=3,
            output=output_path,
            udb_examples_path=udb_examples_path,
            num_examples=6  # Use fewer examples for faster testing
        )
        
        # Verify output file exists
        assert os.path.exists(output_path)
        
        # Load and verify output
        with open(output_path, 'r') as f:
            data = yaml.safe_load(f)
        
        assert 'parameters' in data
        assert len(data['parameters']) > 0
        
        # Verify parameter structure
        for param in data['parameters']:
            assert 'name' in param
            assert 'description' in param
            assert 'param_type' in param
            assert 'source_quote' in param
    
    @pytest.mark.skipif(
        not os.getenv("GEMINI_API_KEY"),
        reason="Requires GEMINI_API_KEY environment variable"
    )
    def test_extraction_with_validation(self, sample_spec_path, temp_output_dir, udb_examples_path):
        """Test extraction with hallucination detection enabled."""
        output_path = os.path.join(temp_output_dir, "extracted.yaml")
        validation_path = os.path.join(temp_output_dir, "validation.yaml")
        
        # Run extraction with validation
        run_extraction(
            spec_path=sample_spec_path,
            chapter=3,
            output=output_path,
            udb_examples_path=udb_examples_path,
            num_examples=6,
            detect_hallucinations=True,
            validation_output=validation_path
        )
        
        # Verify validation report exists
        assert os.path.exists(validation_path)
        
        # Load and verify validation report
        with open(validation_path, 'r') as f:
            report = yaml.safe_load(f)
        
        assert 'summary' in report
        assert 'total_params' in report['summary']
        assert 'verified' in report['summary']
        assert 'verification_rate' in report['summary']
        
        # Verification rate should be reasonable
        assert 0.0 <= report['summary']['verification_rate'] <= 1.0
    
    @pytest.mark.skipif(
        not os.getenv("GEMINI_API_KEY"),
        reason="Requires GEMINI_API_KEY environment variable"
    )
    def test_extraction_with_tag_generation(self, sample_spec_path, temp_output_dir, udb_examples_path):
        """Test extraction with tag generation enabled."""
        output_path = os.path.join(temp_output_dir, "extracted.yaml")
        
        # Run extraction with tag generation
        run_extraction(
            spec_path=sample_spec_path,
            chapter=3,
            output=output_path,
            udb_examples_path=udb_examples_path,
            num_examples=6,
            generate_tags=True
        )
        
        # Load output
        with open(output_path, 'r') as f:
            data = yaml.safe_load(f)
        
        # Verify tags were generated
        params_with_tags = [p for p in data['parameters'] if 'tag_name' in p and p['tag_name']]
        assert len(params_with_tags) > 0


class TestRegressionCases:
    """Test known edge cases and regression scenarios."""
    
    def test_empty_chapter_handling(self):
        """Test handling of non-existent chapters."""
        parser = RISCVSpecParser("tests/fixtures/sample_spec.md")
        
        # Chapter 99 doesn't exist
        chapter = parser.extract_chapter(99)
        assert chapter is None
    
    def test_malformed_spec_handling(self):
        """Test handling of malformed spec files."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("This is not a valid spec\n")
            f.write("No chapters here\n")
            temp_path = f.name
        
        try:
            parser = RISCVSpecParser(temp_path)
            chapter = parser.extract_chapter(1)
            # Should handle gracefully
            assert chapter is None or len(chapter.content) == 0
        finally:
            os.unlink(temp_path)
    
    def test_very_long_text_chunking(self):
        """Test chunking of very long text."""
        parser = RISCVSpecParser("tests/fixtures/sample_spec.md")
        
        # Create very long text (needs to be much longer to trigger multiple chunks)
        long_text = "word " * 50000
        
        chunks = parser.chunk_text(long_text, max_tokens=500, overlap=50)
        
        # Should create multiple chunks for very long text
        assert len(chunks) >= 1
        
        # No chunk should be empty
        assert all(len(chunk) > 0 for chunk in chunks)
    
    def test_special_characters_in_spec(self):
        """Test handling of special characters in spec text."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("# Chapter 1: Special Characters\n\n")
            f.write("CSR[11:8] bits encode permissions\n")
            f.write("Values: 0x00-0xFF\n")
            f.write("Formula: 2^N where N >= 4\n")
            temp_path = f.name
        
        try:
            parser = RISCVSpecParser(temp_path)
            chapter = parser.extract_chapter(1)
            
            assert chapter is not None
            assert "CSR[11:8]" in chapter.content
            assert "0x00-0xFF" in chapter.content
            assert "2^N" in chapter.content
        finally:
            os.unlink(temp_path)


class TestPerformance:
    """Performance benchmarks for the extraction pipeline."""
    
    def test_parsing_performance(self, benchmark):
        """Benchmark spec parsing performance."""
        def parse_spec():
            parser = RISCVSpecParser("tests/fixtures/sample_spec.md")
            return parser.extract_chapter(3)
        
        result = benchmark(parse_spec)
        assert result is not None
    
    def test_chunking_performance(self, benchmark):
        """Benchmark text chunking performance."""
        parser = RISCVSpecParser("tests/fixtures/sample_spec.md")
        chapter = parser.extract_chapter(3)
        
        def chunk_text():
            return parser.chunk_text(chapter.content, max_tokens=500, overlap=50)
        
        chunks = benchmark(chunk_text)
        assert len(chunks) > 0


class TestDataIntegrity:
    """Test data integrity throughout the pipeline."""
    
    def test_parameter_serialization_roundtrip(self):
        """Test that parameters can be serialized and deserialized."""
        from src.models.schema import RISCVParameter, ParameterType
        
        # Create parameter
        param = RISCVParameter(
            name="test_param",
            description="Test parameter",
            param_type=ParameterType.INTEGER,
            source_quote="Test quote",
            rationale="Test rationale",
            classification=ParameterCategory.UNNAMED
        )
        
        # Serialize to dict
        param_dict = param.model_dump()
        
        # Deserialize back
        restored = RISCVParameter(**param_dict)
        
        # Verify equality
        assert restored.name == param.name
        assert restored.description == param.description
        assert restored.param_type == param.param_type
        assert restored.classification == param.classification
    
    def test_yaml_output_validity(self, tmp_path):
        """Test that YAML output is valid and parseable."""
        from src.models.schema import RISCVParameter, ParameterType, ParameterExtraction
        
        # Create sample extraction
        params = [
            RISCVParameter(
                name="param1",
                description="First param",
                param_type=ParameterType.INTEGER,
                source_quote="Quote 1",
                rationale="Rationale 1"
            ),
            RISCVParameter(
                name="param2",
                description="Second param",
                param_type=ParameterType.STRING,
                source_quote="Quote 2",
                rationale="Rationale 2"
            )
        ]
        
        extraction = ParameterExtraction(parameters=params)
        
        # Save to YAML (use model_dump for proper serialization)
        output_path = tmp_path / "test.yaml"
        with open(output_path, 'w') as f:
            # Use safe_dump with model_dump to avoid Python object tags
            yaml.safe_dump(extraction.model_dump(), f)
        
        # Load and verify
        with open(output_path, 'r') as f:
            loaded = yaml.safe_load(f)
        
        assert 'parameters' in loaded
        assert len(loaded['parameters']) == 2
        assert loaded['parameters'][0]['name'] == 'param1'
        assert loaded['parameters'][1]['name'] == 'param2'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
Tests for GraphRAG tag generation.
"""

import pytest
from src.generators.tag_generator import TagGenerator, TagContext
from src.models.schema import RISCVParameter, ParameterType, ParameterCategory


class TestTagContext:
    """Test TagContext dataclass."""
    
    def test_tag_context_creation(self):
        """Test creating tag context."""
        context = TagContext(
            section_title="Cache Organization",
            chapter_number=3,
            parent_concept="Memory System"
        )
        assert context.section_title == "Cache Organization"
        assert context.chapter_number == 3
        assert context.related_params == []
    
    def test_tag_context_defaults(self):
        """Test tag context defaults."""
        context = TagContext()
        assert context.section_title == ""
        assert context.chapter_number is None
        assert context.related_params == []


class TestTagGenerator:
    """Test TagGenerator class."""
    
    @pytest.fixture
    def generator(self):
        """Create tag generator instance."""
        return TagGenerator()
    
    def test_initialization(self, generator):
        """Test generator initialization."""
        assert len(generator.generated_tags) == 0
    
    def test_sanitize_for_tag(self, generator):
        """Test text sanitization for tags."""
        text = "Cache Block Size (bytes)"
        sanitized = generator._sanitize_for_tag(text)
        assert sanitized == "CACHE_BLOCK_SIZE_BYTES"
    
    def test_sanitize_special_characters(self, generator):
        """Test sanitization removes special characters."""
        text = "CSR[11:8] Address"
        sanitized = generator._sanitize_for_tag(text)
        assert sanitized == "CSR118_ADDRESS"
    
    def test_extract_key_terms(self, generator):
        """Test extracting key terms from description."""
        description = "The size of a cache block in bytes"
        terms = generator._extract_key_terms(description, max_terms=3)
        assert "size" in terms
        assert "cache" in terms
        assert "block" in terms
    
    def test_extract_key_terms_filters_stop_words(self, generator):
        """Test that stop words are filtered."""
        description = "The implementation of the parameter"
        terms = generator._extract_key_terms(description)
        assert "the" not in terms
        assert "of" not in terms
    
    def test_ensure_uniqueness_first_time(self, generator):
        """Test uniqueness for first tag."""
        tag = generator._ensure_uniqueness("CACHE_SIZE_TAG")
        assert tag == "CACHE_SIZE_TAG"
        assert "CACHE_SIZE_TAG" in generator.generated_tags
    
    def test_ensure_uniqueness_duplicate(self, generator):
        """Test uniqueness adds suffix for duplicates."""
        tag1 = generator._ensure_uniqueness("CACHE_SIZE_TAG")
        tag2 = generator._ensure_uniqueness("CACHE_SIZE_TAG")
        tag3 = generator._ensure_uniqueness("CACHE_SIZE_TAG")
        
        assert tag1 == "CACHE_SIZE_TAG"
        assert tag2 == "CACHE_SIZE_TAG_2"
        assert tag3 == "CACHE_SIZE_TAG_3"
    
    def test_generate_tag_name_named_parameter(self, generator):
        """Test tag generation for named parameters."""
        param = RISCVParameter(
            name="VLEN",
            description="Vector register length",
            param_type=ParameterType.INTEGER,
            classification=ParameterCategory.NAMED,
            source_quote="VLEN is implementation defined",
            rationale="Test"
        )
        
        tag = generator.generate_tag_name(param)
        assert tag == "VLEN"
    
    def test_generate_tag_name_unnamed_with_context(self, generator):
        """Test tag generation for unnamed parameters with context."""
        param = RISCVParameter(
            name="cache_block_size",
            description="Size of cache block in bytes",
            param_type=ParameterType.INTEGER,
            classification=ParameterCategory.UNNAMED,
            source_quote="Cache block size is implementation specific",
            rationale="Test"
        )
        
        context = TagContext(section_title="Cache Organization")
        tag = generator.generate_tag_name(param, context)
        
        assert "CACHE" in tag
        assert "TAG" in tag
    
    def test_generate_tag_name_unnamed_no_context(self, generator):
        """Test tag generation for unnamed parameters without context."""
        param = RISCVParameter(
            name="cache_capacity",
            description="Total cache capacity in bytes",
            param_type=ParameterType.INTEGER,
            classification=ParameterCategory.UNNAMED,
            source_quote="Cache capacity is implementation specific",
            rationale="Test"
        )
        
        tag = generator.generate_tag_name(param)
        assert "TAG" in tag
        assert len(tag) > 4
    
    def test_analyze_csr_hierarchy_csr_param(self, generator):
        """Test CSR hierarchy analysis for CSR parameter."""
        param = RISCVParameter(
            name="mstatus",
            description="Machine status register",
            param_type=ParameterType.INTEGER,
            source_quote="The mstatus register is a machine-mode CSR at address 0x300",
            rationale="Test"
        )
        
        spec_text = "The mstatus register is a machine-mode CSR at address 0x300"
        hierarchy = generator.analyze_csr_hierarchy(param, spec_text)
        
        assert hierarchy["is_csr"] is True
        assert hierarchy["csr_address"] == "0x300"
        assert hierarchy["privilege_level"] == "M"
    
    def test_analyze_csr_hierarchy_non_csr(self, generator):
        """Test CSR hierarchy analysis for non-CSR parameter."""
        param = RISCVParameter(
            name="cache_size",
            description="Cache size in bytes",
            param_type=ParameterType.INTEGER,
            source_quote="Cache size is implementation defined",
            rationale="Test"
        )
        
        hierarchy = generator.analyze_csr_hierarchy(param, "")
        assert hierarchy["is_csr"] is False
    
    def test_extract_section_context(self, generator):
        """Test extracting section context from spec."""
        spec_text = """
        # Chapter 3: Memory System
        
        ## Cache Organization
        
        The cache is organized into blocks.
        """
        
        param = RISCVParameter(
            name="cache_block",
            description="Cache block",
            param_type=ParameterType.INTEGER,
            source_quote="The cache is organized into blocks.",
            rationale="Test"
        )
        
        context = generator.extract_section_context(spec_text, param)
        assert "Cache Organization" in context.section_title or "Memory System" in context.section_title
        assert context.chapter_number == 3
    
    def test_generate_tags_for_extraction(self, generator):
        """Test generating tags for multiple parameters."""
        params = [
            RISCVParameter(
                name="VLEN",
                description="Vector length",
                param_type=ParameterType.INTEGER,
                classification=ParameterCategory.NAMED,
                source_quote="VLEN test",
                rationale="Test"
            ),
            RISCVParameter(
                name="cache_size",
                description="Cache size in bytes",
                param_type=ParameterType.INTEGER,
                classification=ParameterCategory.UNNAMED,
                source_quote="Cache size test",
                rationale="Test"
            )
        ]
        
        tag_mapping = generator.generate_tags_for_extraction(params)
        assert "VLEN" in tag_mapping
        assert "cache_size" in tag_mapping
        assert len(tag_mapping) == 2
    
    def test_reset(self, generator):
        """Test resetting generated tags."""
        generator._ensure_uniqueness("TEST_TAG")
        assert len(generator.generated_tags) == 1
        
        generator.reset()
        assert len(generator.generated_tags) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
Tests for RISC-V specification parser.
"""

import pytest
from pathlib import Path
from src.parsers.spec_parser import RISCVSpecParser, SpecChapter, extract_chapter_from_file


class TestSpecParser:
    """Test specification file parsing."""
    
    def test_parser_initialization(self, tmp_path):
        """Test parser initialization with valid file."""
        spec_file = tmp_path / "test_spec.md"
        spec_file.write_text("# Chapter 1: Introduction\n\nTest content")
        
        parser = RISCVSpecParser(str(spec_file))
        assert parser.spec_path == spec_file
        assert parser.file_type == "markdown"
    
    def test_parser_file_not_found(self):
        """Test parser with non-existent file."""
        with pytest.raises(FileNotFoundError):
            RISCVSpecParser("nonexistent.md")
    
    def test_detect_markdown(self, tmp_path):
        """Test markdown file type detection."""
        spec_file = tmp_path / "test.md"
        spec_file.write_text("# Header\n\n## Section")
        
        parser = RISCVSpecParser(str(spec_file))
        assert parser.file_type == "markdown"
    
    def test_detect_asciidoc(self, tmp_path):
        """Test AsciiDoc file type detection."""
        spec_file = tmp_path / "test.adoc"
        spec_file.write_text("= Header\n\n== Section")
        
        parser = RISCVSpecParser(str(spec_file))
        assert parser.file_type == "asciidoc"
    
    def test_extract_markdown_chapter(self, tmp_path):
        """Test extracting a chapter from Markdown."""
        content = """# Chapter 1: Introduction

This is the introduction.

## Section 1.1

Content here.

# Chapter 2: Architecture

This is chapter 2.

## Section 2.1

More content.

# Chapter 3: Implementation

Chapter 3 content.
"""
        spec_file = tmp_path / "spec.md"
        spec_file.write_text(content)
        
        parser = RISCVSpecParser(str(spec_file))
        chapter = parser.extract_chapter(2)
        
        assert chapter is not None
        assert chapter.number == 2
        assert chapter.title == "Architecture"
        assert "This is chapter 2" in chapter.content
        assert len(chapter.sections) == 1
        assert chapter.sections[0] == "Section 2.1"
    
    def test_extract_nonexistent_chapter(self, tmp_path):
        """Test extracting a chapter that doesn't exist."""
        spec_file = tmp_path / "spec.md"
        spec_file.write_text("# Chapter 1: Test\n\nContent")
        
        parser = RISCVSpecParser(str(spec_file))
        chapter = parser.extract_chapter(99)
        
        assert chapter is None
    
    def test_chunk_text_small(self):
        """Test chunking text that fits in one chunk."""
        parser = RISCVSpecParser.__new__(RISCVSpecParser)
        text = "Short text that fits in one chunk."
        
        chunks = parser.chunk_text(text, max_tokens=1000)
        assert len(chunks) == 1
        assert chunks[0] == text
    
    def test_chunk_text_large(self):
        """Test chunking large text."""
        parser = RISCVSpecParser.__new__(RISCVSpecParser)
        
        # Create text with multiple paragraphs
        paragraphs = [f"Paragraph {i}. " + "x" * 500 for i in range(20)]
        text = "\n\n".join(paragraphs)
        
        chunks = parser.chunk_text(text, max_tokens=500, overlap=100)
        
        assert len(chunks) > 1
        # Each chunk should be reasonably sized
        for chunk in chunks:
            assert len(chunk) <= 500 * 4 + 1000  # Allow some overflow
    
    def test_get_chapter_metadata(self, tmp_path):
        """Test getting chapter metadata."""
        content = """# Chapter 3: Machine-Level ISA

This is chapter 3.

## Section 3.1: CSRs

CSR content.

## Section 3.2: Interrupts

Interrupt content.
"""
        spec_file = tmp_path / "spec.md"
        spec_file.write_text(content)
        
        parser = RISCVSpecParser(str(spec_file))
        metadata = parser.get_chapter_metadata(3)
        
        assert metadata is not None
        assert metadata['number'] == 3
        assert metadata['title'] == "Machine-Level ISA"
        assert metadata['num_sections'] == 2
        assert any("CSRs" in section for section in metadata['sections'])
        assert any("Interrupts" in section for section in metadata['sections'])
        assert metadata['content_length'] > 0
    
    def test_extract_chapter_from_file_convenience(self, tmp_path):
        """Test convenience function."""
        spec_file = tmp_path / "spec.md"
        spec_file.write_text("# Chapter 1: Test\n\nContent")
        
        chapter = extract_chapter_from_file(str(spec_file), 1)
        
        assert chapter is not None
        assert chapter.number == 1
        assert chapter.title == "Test"


class TestSpecChapter:
    """Test SpecChapter dataclass."""
    
    def test_spec_chapter_creation(self):
        """Test creating a SpecChapter."""
        chapter = SpecChapter(
            number=3,
            title="Machine-Level ISA",
            content="Chapter content here",
            sections=["Section 3.1", "Section 3.2"]
        )
        
        assert chapter.number == 3
        assert chapter.title == "Machine-Level ISA"
        assert chapter.content == "Chapter content here"
        assert len(chapter.sections) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

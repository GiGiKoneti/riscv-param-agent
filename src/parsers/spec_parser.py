"""
RISC-V Specification Parser

Parses RISC-V specification files (Markdown/AsciiDoc) and extracts chapters
for parameter extraction.
"""

import re
from pathlib import Path
from typing import List, Optional, Dict
from dataclasses import dataclass


@dataclass
class SpecChapter:
    """Represents a chapter from the RISC-V specification."""
    number: int
    title: str
    content: str
    sections: List[str]


class RISCVSpecParser:
    """Parser for RISC-V specification files."""
    
    def __init__(self, spec_path: str):
        """
        Initialize the parser with a spec file path.
        
        Args:
            spec_path: Path to the RISC-V specification file
        """
        self.spec_path = Path(spec_path)
        if not self.spec_path.exists():
            raise FileNotFoundError(f"Spec file not found: {spec_path}")
        
        self.content = self.spec_path.read_text(encoding='utf-8')
        self.file_type = self._detect_file_type()
    
    def _detect_file_type(self) -> str:
        """Detect if the file is Markdown or AsciiDoc."""
        if self.spec_path.suffix in ['.md', '.markdown']:
            return 'markdown'
        elif self.spec_path.suffix in ['.adoc', '.asciidoc']:
            return 'asciidoc'
        else:
            # Try to detect from content
            if '= ' in self.content[:1000] and '==' in self.content[:1000]:
                return 'asciidoc'
            return 'markdown'
    
    def extract_chapter(self, chapter_number: int) -> Optional[SpecChapter]:
        """
        Extract a specific chapter from the specification.
        
        Args:
            chapter_number: The chapter number to extract (e.g., 3 for Chapter 3)
        
        Returns:
            SpecChapter object or None if not found
        """
        if self.file_type == 'markdown':
            return self._extract_markdown_chapter(chapter_number)
        else:
            return self._extract_asciidoc_chapter(chapter_number)
    
    def _extract_markdown_chapter(self, chapter_number: int) -> Optional[SpecChapter]:
        """Extract chapter from Markdown format."""
        # Pattern to match chapter headers like "# Chapter 3: Machine-Level ISA"
        chapter_pattern = rf'^#\s+(?:Chapter\s+)?{chapter_number}[\s:]+(.+?)$'
        next_chapter_pattern = rf'^#\s+(?:Chapter\s+)?{chapter_number + 1}[\s:]'
        
        lines = self.content.split('\n')
        chapter_start = None
        chapter_title = None
        
        # Find chapter start
        for i, line in enumerate(lines):
            if re.match(chapter_pattern, line, re.IGNORECASE):
                chapter_start = i
                chapter_title = re.match(chapter_pattern, line, re.IGNORECASE).group(1).strip()
                break
        
        if chapter_start is None:
            return None
        
        # Find chapter end (next chapter or end of file)
        chapter_end = len(lines)
        for i in range(chapter_start + 1, len(lines)):
            if re.match(next_chapter_pattern, lines[i], re.IGNORECASE):
                chapter_end = i
                break
        
        # Extract content
        chapter_content = '\n'.join(lines[chapter_start:chapter_end])
        
        # Extract sections (## headers)
        sections = self._extract_sections(chapter_content)
        
        return SpecChapter(
            number=chapter_number,
            title=chapter_title,
            content=chapter_content,
            sections=sections
        )
    
    def _extract_asciidoc_chapter(self, chapter_number: int) -> Optional[SpecChapter]:
        """Extract chapter from AsciiDoc format."""
        # Pattern for AsciiDoc chapter headers
        chapter_pattern = rf'^=\s+(?:Chapter\s+)?{chapter_number}[\s:]+(.+?)$'
        next_chapter_pattern = rf'^=\s+(?:Chapter\s+)?{chapter_number + 1}[\s:]'
        
        lines = self.content.split('\n')
        chapter_start = None
        chapter_title = None
        
        for i, line in enumerate(lines):
            if re.match(chapter_pattern, line, re.IGNORECASE):
                chapter_start = i
                chapter_title = re.match(chapter_pattern, line, re.IGNORECASE).group(1).strip()
                break
        
        if chapter_start is None:
            return None
        
        chapter_end = len(lines)
        for i in range(chapter_start + 1, len(lines)):
            if re.match(next_chapter_pattern, lines[i], re.IGNORECASE):
                chapter_end = i
                break
        
        chapter_content = '\n'.join(lines[chapter_start:chapter_end])
        sections = self._extract_sections(chapter_content, is_asciidoc=True)
        
        return SpecChapter(
            number=chapter_number,
            title=chapter_title,
            content=chapter_content,
            sections=sections
        )
    
    def _extract_sections(self, content: str, is_asciidoc: bool = False) -> List[str]:
        """Extract section titles from chapter content."""
        sections = []
        pattern = r'^==\s+(.+?)$' if is_asciidoc else r'^##\s+(.+?)$'
        
        for line in content.split('\n'):
            match = re.match(pattern, line)
            if match:
                sections.append(match.group(1).strip())
        
        return sections
    
    def chunk_text(self, text: str, max_tokens: int = 3000, overlap: int = 200) -> List[str]:
        """
        Split text into chunks suitable for LLM processing.
        
        Args:
            text: The text to chunk
            max_tokens: Maximum tokens per chunk (rough estimate: 1 token ≈ 4 chars)
            overlap: Number of characters to overlap between chunks
        
        Returns:
            List of text chunks
        """
        max_chars = max_tokens * 4  # Rough approximation
        
        if len(text) <= max_chars:
            return [text]
        
        chunks = []
        paragraphs = text.split('\n\n')
        current_chunk = []
        current_length = 0
        
        for para in paragraphs:
            para_length = len(para)
            
            if current_length + para_length > max_chars and current_chunk:
                # Save current chunk
                chunks.append('\n\n'.join(current_chunk))
                
                # Start new chunk with overlap (last paragraph)
                current_chunk = [current_chunk[-1]] if current_chunk else []
                current_length = len(current_chunk[0]) if current_chunk else 0
            
            current_chunk.append(para)
            current_length += para_length
        
        # Add final chunk
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))
        
        return chunks
    
    def get_chapter_metadata(self, chapter_number: int) -> Optional[Dict]:
        """Get metadata about a chapter without extracting full content."""
        chapter = self.extract_chapter(chapter_number)
        if not chapter:
            return None
        
        return {
            'number': chapter.number,
            'title': chapter.title,
            'num_sections': len(chapter.sections),
            'sections': chapter.sections,
            'content_length': len(chapter.content),
            'estimated_chunks': len(self.chunk_text(chapter.content))
        }


def extract_chapter_from_file(spec_path: str, chapter_number: int) -> Optional[SpecChapter]:
    """
    Convenience function to extract a chapter from a spec file.
    
    Args:
        spec_path: Path to the specification file
        chapter_number: Chapter number to extract
    
    Returns:
        SpecChapter object or None if not found
    """
    parser = RISCVSpecParser(spec_path)
    return parser.extract_chapter(chapter_number)

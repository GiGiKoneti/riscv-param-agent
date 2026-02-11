"""
GraphRAG-based tag name generation for unnamed RISC-V parameters.

This module generates unique, context-aware tag names for unnamed parameters
using relational analysis of the specification structure.
"""

from typing import Dict, List, Optional
import re
from dataclasses import dataclass

from src.models.schema import RISCVParameter, ParameterCategory


@dataclass
class TagContext:
    """Context information for tag generation."""
    section_title: str = ""
    chapter_number: Optional[int] = None
    parent_concept: str = ""
    related_params: List[str] = None
    
    def __post_init__(self):
        if self.related_params is None:
            self.related_params = []


class TagGenerator:
    """
    Generates unique tag names for unnamed parameters using GraphRAG-style
    relational analysis.
    """
    
    def __init__(self):
        """Initialize tag generator."""
        self.generated_tags = set()
    
    def _sanitize_for_tag(self, text: str) -> str:
        """
        Sanitize text for use in tag names.
        
        Args:
            text: Text to sanitize
            
        Returns:
            Sanitized text (uppercase, underscores, alphanumeric only)
        """
        # Remove special characters, keep alphanumeric and spaces
        sanitized = re.sub(r'[^a-zA-Z0-9\s]', '', text)
        # Replace spaces with underscores
        sanitized = re.sub(r'\s+', '_', sanitized)
        # Convert to uppercase
        return sanitized.upper()
    
    def _extract_key_terms(self, description: str, max_terms: int = 3) -> List[str]:
        """
        Extract key terms from description for tag generation.
        
        Args:
            description: Parameter description
            max_terms: Maximum number of terms to extract
            
        Returns:
            List of key terms
        """
        # Common words to skip
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
            'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'should', 'could', 'may', 'might', 'must', 'can', 'this', 'that',
            'these', 'those', 'implementation', 'specific', 'defined', 'parameter'
        }
        
        # Extract words
        words = description.lower().split()
        
        # Filter out stop words and short words
        key_words = [w for w in words if w not in stop_words and len(w) > 2]
        
        # Return first max_terms words
        return key_words[:max_terms]
    
    def _ensure_uniqueness(self, base_tag: str) -> str:
        """
        Ensure tag is unique by adding suffix if needed.
        
        Args:
            base_tag: Base tag name
            
        Returns:
            Unique tag name
        """
        if base_tag not in self.generated_tags:
            self.generated_tags.add(base_tag)
            return base_tag
        
        # Add numeric suffix
        counter = 2
        while f"{base_tag}_{counter}" in self.generated_tags:
            counter += 1
        
        unique_tag = f"{base_tag}_{counter}"
        self.generated_tags.add(unique_tag)
        return unique_tag
    
    def generate_tag_name(self, param: RISCVParameter, context: Optional[TagContext] = None) -> str:
        """
        Generate unique tag name for a parameter.
        
        Args:
            param: Parameter to generate tag for
            context: Optional context information
            
        Returns:
            Generated tag name
        """
        # Named parameters use their name
        if param.classification == ParameterCategory.NAMED:
            tag = self._sanitize_for_tag(param.name)
            return self._ensure_uniqueness(tag)
        
        # For unnamed parameters, build tag from context and description
        tag_parts = []
        
        # Add section context if available
        if context and context.section_title:
            section_key = self._sanitize_for_tag(context.section_title)
            # Take first 2 words from section
            section_words = section_key.split('_')[:2]
            tag_parts.extend(section_words)
        
        # Add key terms from description
        key_terms = self._extract_key_terms(param.description, max_terms=3)
        tag_parts.extend([self._sanitize_for_tag(term) for term in key_terms])
        
        # Build base tag
        if tag_parts:
            base_tag = '_'.join(tag_parts[:4])  # Limit to 4 parts
        else:
            # Fallback: use first 3 words of description
            desc_words = param.description.split()[:3]
            base_tag = '_'.join([self._sanitize_for_tag(w) for w in desc_words])
        
        # Add _TAG suffix
        base_tag = f"{base_tag}_TAG"
        
        return self._ensure_uniqueness(base_tag)
    
    def analyze_csr_hierarchy(self, param: RISCVParameter, spec_text: str) -> Dict:
        """
        Analyze CSR hierarchy and relationships for a parameter.
        
        Args:
            param: Parameter to analyze
            spec_text: Specification text
            
        Returns:
            Dictionary with hierarchy information
        """
        hierarchy = {
            "is_csr": False,
            "csr_address": None,
            "privilege_level": None,
            "related_csrs": []
        }
        
        # Check if parameter is CSR-related
        csr_keywords = ['csr', 'control', 'status', 'register']
        if any(keyword in param.description.lower() for keyword in csr_keywords):
            hierarchy["is_csr"] = True
            
            # Try to extract CSR address from source quote
            address_pattern = r'0x[0-9A-Fa-f]{3}'
            address_match = re.search(address_pattern, param.source_quote)
            if address_match:
                hierarchy["csr_address"] = address_match.group()
            
            # Try to determine privilege level
            if 'machine' in param.source_quote.lower():
                hierarchy["privilege_level"] = "M"
            elif 'supervisor' in param.source_quote.lower():
                hierarchy["privilege_level"] = "S"
            elif 'user' in param.source_quote.lower():
                hierarchy["privilege_level"] = "U"
        
        return hierarchy
    
    def extract_section_context(self, spec_text: str, param: RISCVParameter) -> TagContext:
        """
        Extract section context from specification text.
        
        Args:
            spec_text: Full specification text
            param: Parameter to extract context for
            
        Returns:
            Tag context with section information
        """
        context = TagContext()
        
        # Find the section containing the source quote
        if param.source_quote in spec_text:
            quote_pos = spec_text.find(param.source_quote)
            
            # Look backwards for section header (markdown format)
            text_before = spec_text[:quote_pos]
            
            # Find most recent heading
            heading_patterns = [
                r'###\s+(.+?)$',  # Level 3 heading
                r'##\s+(.+?)$',   # Level 2 heading
                r'#\s+(.+?)$'     # Level 1 heading
            ]
            
            for pattern in heading_patterns:
                matches = list(re.finditer(pattern, text_before, re.MULTILINE))
                if matches:
                    last_heading = matches[-1].group(1).strip()
                    context.section_title = last_heading
                    break
            
            # Try to extract chapter number
            chapter_match = re.search(r'Chapter\s+(\d+)', text_before, re.IGNORECASE)
            if chapter_match:
                context.chapter_number = int(chapter_match.group(1))
        
        return context
    
    def generate_tags_for_extraction(self, parameters: List[RISCVParameter], spec_text: str = "") -> Dict[str, str]:
        """
        Generate tags for all parameters in an extraction.
        
        Args:
            parameters: List of parameters
            spec_text: Optional specification text for context
            
        Returns:
            Dictionary mapping parameter names to generated tags
        """
        tag_mapping = {}
        
        for param in parameters:
            # Extract context if spec text available
            if spec_text:
                context = self.extract_section_context(spec_text, param)
            else:
                context = None
            
            # Generate tag
            tag = self.generate_tag_name(param, context)
            tag_mapping[param.name] = tag
        
        return tag_mapping
    
    def reset(self):
        """Reset generated tags set."""
        self.generated_tags.clear()

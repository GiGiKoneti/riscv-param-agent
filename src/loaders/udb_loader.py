"""
UDB Examples Loader

Loads example parameters from the RISC-V Unified Database (UDB) for few-shot
prompting and validation.
"""

import yaml
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class UDBExample:
    """Represents an example parameter from the UDB."""
    name: str
    description: str
    param_type: str
    classification: str
    implementation_defined: bool
    source_quote: Optional[str] = None
    constraints: Optional[List[Dict]] = None


class UDBExamplesLoader:
    """Loader for UDB example parameters."""
    
    def __init__(self, examples_path: str = "data/udb_examples.yaml"):
        """
        Initialize the loader.
        
        Args:
            examples_path: Path to the UDB examples YAML file
        """
        self.examples_path = Path(examples_path)
        self.examples: List[UDBExample] = []
        
        if self.examples_path.exists():
            self._load_examples()
    
    def _load_examples(self):
        """Load examples from YAML file."""
        with open(self.examples_path, 'r') as f:
            data = yaml.safe_load(f)
        
        if not data or 'examples' not in data:
            return
        
        for ex in data['examples']:
            self.examples.append(UDBExample(
                name=ex.get('name', ''),
                description=ex.get('description', ''),
                param_type=ex.get('param_type', 'string'),
                classification=ex.get('classification', 'named'),
                implementation_defined=ex.get('implementation_defined', False),
                source_quote=ex.get('source_quote'),
                constraints=ex.get('constraints', [])
            ))
    
    def get_examples(self, num_examples: int = 12, 
                     classification: Optional[str] = None) -> List[UDBExample]:
        """
        Get a subset of examples.
        
        Args:
            num_examples: Maximum number of examples to return
            classification: Filter by classification (named/unnamed/configuration-dependent)
        
        Returns:
            List of UDBExample objects
        """
        examples = self.examples
        
        if classification:
            examples = [ex for ex in examples if ex.classification == classification]
        
        return examples[:num_examples]
    
    def format_for_prompt(self, num_examples: int = 12) -> str:
        """
        Format examples as a string for LLM prompting.
        
        Args:
            num_examples: Number of examples to include
        
        Returns:
            Formatted string with examples
        """
        examples = self.get_examples(num_examples)
        
        if not examples:
            return "No UDB examples available."
        
        formatted = "Here are example parameters from the RISC-V Unified Database:\n\n"
        
        for i, ex in enumerate(examples, 1):
            formatted += f"Example {i}:\n"
            formatted += f"  Name: {ex.name}\n"
            formatted += f"  Description: {ex.description}\n"
            formatted += f"  Type: {ex.param_type}\n"
            formatted += f"  Classification: {ex.classification}\n"
            formatted += f"  Implementation-defined: {ex.implementation_defined}\n"
            
            if ex.source_quote:
                formatted += f"  Source Quote: \"{ex.source_quote}\"\n"
            
            if ex.constraints:
                formatted += f"  Constraints:\n"
                for constraint in ex.constraints:
                    formatted += f"    - {constraint.get('rule', 'N/A')}\n"
            
            formatted += "\n"
        
        return formatted
    
    def get_balanced_examples(self, num_examples: int = 12) -> str:
        """
        Get a balanced mix of all three classification types.
        
        Args:
            num_examples: Total number of examples to return
        
        Returns:
            Formatted string with balanced examples
        """
        per_type = num_examples // 3
        
        named = self.get_examples(per_type, classification='named')
        unnamed = self.get_examples(per_type, classification='unnamed')
        config_dep = self.get_examples(per_type, classification='configuration-dependent')
        
        all_examples = named + unnamed + config_dep
        
        formatted = "Here are example parameters from the RISC-V Unified Database (balanced across all types):\n\n"
        
        for i, ex in enumerate(all_examples, 1):
            formatted += f"Example {i} [{ex.classification.upper()}]:\n"
            formatted += f"  Name: {ex.name}\n"
            formatted += f"  Description: {ex.description}\n"
            formatted += f"  Type: {ex.param_type}\n"
            formatted += f"  Implementation-defined: {ex.implementation_defined}\n"
            
            if ex.source_quote:
                formatted += f"  Source Quote: \"{ex.source_quote[:100]}...\"\n"
            
            formatted += "\n"
        
        return formatted


def load_udb_examples(examples_path: str = "data/udb_examples.yaml", 
                      num_examples: int = 12,
                      balanced: bool = True) -> str:
    """
    Convenience function to load and format UDB examples.
    
    Args:
        examples_path: Path to the UDB examples YAML file
        num_examples: Number of examples to load
        balanced: Whether to balance across classification types
    
    Returns:
        Formatted string with examples for LLM prompting
    """
    loader = UDBExamplesLoader(examples_path)
    
    if balanced:
        return loader.get_balanced_examples(num_examples)
    else:
        return loader.format_for_prompt(num_examples)

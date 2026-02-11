from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from enum import Enum

class ParameterType(str, Enum):
    INTEGER = "integer"
    BOOLEAN = "boolean"
    STRING = "string"
    RANGE = "range"
    ENUM = "enum"
    BITS = "bits"

class ParameterCategory(str, Enum):
    """Motto 1(c): Classification of parameters"""
    NAMED = "named"
    UNNAMED = "unnamed"
    CONFIG_DEPENDENT = "configuration-dependent"

class Constraint(BaseModel):
    rule: str = Field(..., description="The architectural rule (e.g., 'Must be NAPOT')")
    is_hard_constraint: bool = Field(True, description="True if the ISA forbids violation")

class RISCVParameter(BaseModel):
    name: str = Field(..., description="Unique snake_case identifier (e.g., cache_block_size)")
    tag_name: str = Field(default="", description="Motto 4: Unique tag name for spec insertion (e.g., {TAG_NAME})")
    description: str = Field(..., description="High-level architectural purpose")
    param_type: ParameterType = Field(..., description="Data type of the parameter")
    classification: ParameterCategory = Field(default=ParameterCategory.UNNAMED, description="Classification per project motto 1(c)")
    constraints: List[Constraint] = Field(default_factory=list)
    implementation_defined: bool = Field(True, description="True if text says 'implementation-specific'")
    source_quote: str = Field(..., description="Verbatim text from the ISA manual for verification")
    rationale: str = Field(..., description="Internal reasoning for classification and extraction")
    extraction_metadata: Dict = Field(default_factory=dict, description="Metadata about extraction (confidence, models used, etc.)")

class ParameterExtraction(BaseModel):
    parameters: List[RISCVParameter]
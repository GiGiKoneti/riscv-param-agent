from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class ParameterType(str, Enum):
    INTEGER = "integer"
    BOOLEAN = "boolean"
    STRING = "string"
    RANGE = "range"
    ENUM = "enum"
    BITS = "bits"  # Added for CSR address widths

class Constraint(BaseModel):
    rule: str = Field(..., description="The architectural rule (e.g., 'Must be NAPOT')")
    is_hard_constraint: bool = Field(True, description="True if the ISA forbids violation")

class RISCVParameter(BaseModel):
    name: str = Field(..., description="Unique snake_case identifier (e.g., cache_block_size)")
    description: str = Field(..., description="High-level architectural purpose")
    param_type: ParameterType = Field(..., description="Data type of the parameter")
    constraints: List[Constraint] = Field(default_factory=list)
    implementation_defined: bool = Field(True, description="True if text says 'implementation-specific'")
    source_quote: str = Field(..., description="Verbatim text from the ISA manual for verification")
    rationale: str = Field(..., description="Internal reasoning for why this is a parameter")

class ParameterExtraction(BaseModel):
    parameters: List[RISCVParameter]
import dspy
from src.models.schema import ParameterExtraction

class RISCVArchitecturalMiner(dspy.Signature):
    """
    You are a Senior Silicon Verification Engineer. 
    Extract architectural parameters from RISC-V specification snippets.
    Look for keywords: 'may', 'should', 'optional', 'implementation-defined'.
    """
    text_snippet: str = dspy.InputField(desc="Raw text from the RISC-V ISA manual")
    extracted_data: ParameterExtraction = dspy.OutputField(
        desc="Structured parameters following the defined schema"
    )
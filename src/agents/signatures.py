import dspy
from src.models.schema import ParameterExtraction

class RISCVArchitecturalMiner(dspy.Signature):
    """
    Act as a Linux Kernel Engineer and Senior Silicon Verification Expert. 
    
    Extract hardware parameters from RISC-V specification snippets that are 
    required for system discovery tools (e.g., lscpu, dmidecode, /proc/cpuinfo).
    
    Instruction:
    1. Identify implementation-defined variables (e.g., cache levels, block sizes).
    2. Capture fixed architectural constants (e.g., address widths, bit-field mappings).
    3. Look for linguistic triggers: 'shall', 'may', 'should', 'implementation-specific'.
    4. Focus on parameters critical for Device Tree (DT) generation and OS hardware abstraction.
    """
    
    text_snippet: str = dspy.InputField(
        desc="Raw architectural prose from the RISC-V ISA manual"
    )
    
    extracted_data: ParameterExtraction = dspy.OutputField(
        desc="Validated schema containing OS-relevant parameters, constraints, and source-grounded rationales"
    )
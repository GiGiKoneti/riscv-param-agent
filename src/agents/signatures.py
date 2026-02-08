import dspy
from src.models.schema import ParameterExtraction

class RISCVArchitecturalMiner(dspy.Signature):
    """
    Act as a Recursive Language Model (RLM) and Linux Kernel Engineer.
    
    Instruction:
    1. Extract hardware parameters required for system discovery (lscpu, dmidecode) 
       and Device Tree generation.
    2. Motto 1(c): Classify each parameter as 'named', 'unnamed', or 
       'configuration-dependent' based on its visibility in the ISA.
    3. Motto 4: For 'unnamed' parameters, utilize GraphRAG-style relational analysis 
       of surrounding CSRs or privilege levels to generate a unique 'tag_name'.
    4. Refine extractions using 'udb_examples' to ensure consistency with existing 
       Unified Database entries.
    5. Identify triggers: 'shall', 'may', 'should', 'implementation-specific'.
    """
    
    text_snippet: str = dspy.InputField(
        desc="Raw architectural prose from the RISC-V ISA manual"
    )
    
    udb_examples: str = dspy.InputField(
        desc="Examples from the manually created Unified Database (UDB) for few-shot guidance"
    )
    
    extracted_data: ParameterExtraction = dspy.OutputField(
        desc="Motto-compliant schema containing classified parameters, unique tags, and source-grounded rationales"
    )
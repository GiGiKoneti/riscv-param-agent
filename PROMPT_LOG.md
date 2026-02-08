# Prompt Refinement & Iteration Log (Motto 3)

### **Iteration 1: Initial Extraction**
- **Goal:** Identify parameters and classify as Named/Unnamed.
- **Model:** Gemini 2.5 Flash.
- **Observation:** Successfully identified base parameters like `cache_block_size`, but lacked unique tag generation for unnamed parameters.

### **Iteration 2: Multi-Model Comparison (Motto 3a)**
- **Models:** Gemini 2.5 Flash (Cloud) vs. Llama 3.1 (Local via Ollama).
- **Discrepancy:** Llama 3.1 failed to classify `cache_capacity` as 'named' and missed the 'configuration-dependent' nature of `cache_organization`.
- **Action:** Identified these as "Negative Examples" to be corrected in the system prompt.

### **Iteration 3: Recursive Logic Refinement (Motto 3b)**
- **Refinement:** Updated the **Recursive Language Model (RLM)** signature to include few-shot examples from the **Unified Database (UDB)**. 
- **Instruction Update:** Added specific triggers for 'implementation-defined' properties to force the model to evaluate the "Named" status against the RISC-V Privileged Spec structure.
- **Result:** Consensus achieved across both models. Unique `tag_name` generation implemented for unnamed parameters using GraphRAG relational mapping.

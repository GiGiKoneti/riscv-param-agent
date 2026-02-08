import dspy
import os
import yaml
import time
from dotenv import load_dotenv
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
from src.models.schema import ParameterExtraction
from src.agents.signatures import RISCVArchitecturalMiner

# Load credentials from .env
load_dotenv()

# Define a robust retry strategy specifically for Rate Limits (429)
# wait_exponential: waits 2^x * 1 second between retries
@retry(
    wait=wait_exponential(multiplier=1, min=4, max=60),
    stop=stop_after_attempt(5),
    retry=retry_if_exception_type(Exception), # Catch generic Exception as dspy/litellm wrap errors
    before_sleep=lambda retry_state: print(f"[!] Rate limit hit. Retrying in {retry_state.next_action.sleep}s...")
)
def extract_with_retry(miner, snippet):
    """Wrapper function to handle API calls with exponential backoff."""
    return miner(text_snippet=snippet)

def run_extraction():
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key or not api_key.startswith("AIza"):
        print("[!] Error: GEMINI_API_KEY is missing or invalid in .env")
        return

    try:
        # 1. Configure the Language Model (Using Gemini 2.5 Flash)
        gemini = dspy.LM('gemini/gemini-2.5-flash', api_key=api_key)
        dspy.configure(lm=gemini)

        # 2. Define the Program
        miner = dspy.ChainOfThought(RISCVArchitecturalMiner)

        # 3. Input Snippets
        snippets = [
            "Caches organize copies of data into cache blocks, each of which represents a contiguous, naturally aligned power-of-two (or NAPOT) range of memory locations. The capacity and organization of a cache and the size of a cache block are both implementation-specific...",
            "The standard RISC-V ISA sets aside a 12-bit encoding space (csr[11:0]) for up to 4,096 CSRs. By convention, the upper 4 bits of the CSR address (csr[11:8]) are used to encode the read and write accessibility..."
        ]

        all_extracted_params = []
        for i, snippet in enumerate(snippets):
            print(f"[*] Processing Snippet {i+1}...")
            
            # Execute with exponential backoff
            prediction = extract_with_retry(miner, snippet)
            
            if prediction.extracted_data:
                all_extracted_params.extend(prediction.extracted_data.parameters)
            
            # Mandatory 5s delay even on success to stay within Free Tier RPM (5-15 RPM)
            if i < len(snippets) - 1:
                time.sleep(5)

        # 4. Clean Export to YAML
        os.makedirs("outputs", exist_ok=True)
        output_path = "outputs/extracted_parameters.yaml"
        
        yaml_output = {
            "parameters": [p.model_dump(mode="json") for p in all_extracted_params]
        }
        
        with open(output_path, "w") as f:
            yaml.dump(yaml_output, f, sort_keys=False, default_flow_style=False)
        
        print(f"[+] Success! Clean YAML results saved to {output_path}")

    except Exception as e:
        print(f"[!] Final failure after retries: {e}")

if __name__ == "__main__":
    run_extraction()
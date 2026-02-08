import dspy
import yaml
import os
import json
from src.agents.signatures import RISCVArchitecturalMiner
from src.models.schema import ParameterExtraction

class RLMVerification(dspy.Signature):
    """
    Act as a Verification Critic. Review the extracted parameters against 
    the original spec to identify hallucinations or missing constraints.
    """
    text_snippet = dspy.InputField()
    extracted_data = dspy.InputField(desc="The initial Pydantic extraction")
    critique = dspy.OutputField(desc="Identify specific errors or missing bit-fields")
    corrected_data: ParameterExtraction = dspy.OutputField(desc="The final hardware-validated ParameterExtraction")

def run_rlm_pipeline(lm, text_snippet, udb_examples):
    """
    Implements the Recursive Language Model (RLM) method via a 
    Self-Correction REPL loop using BMA (Branching Memory Architecture).
    """
    with dspy.context(lm=lm):
        # Branch 1: Task Memory (Initial Extraction)
        extractor = dspy.Predict(RISCVArchitecturalMiner)
        initial_out = extractor(text_snippet=text_snippet, udb_examples=udb_examples)
        
        # Branch 2: Critic Branch (Recursive Verification)
        # We use ChainOfThought for the RLM loop to improve hardware reasoning
        verifier = dspy.ChainOfThought(RLMVerification)
        verification = verifier(
            text_snippet=text_snippet, 
            extracted_data=initial_out.extracted_data
        )
        
        # BMA Logic: Ensure we return the structured object, not the raw string
        return verification.corrected_data if hasattr(verification, 'corrected_data') else initial_out.extracted_data

def compare_models(text_snippet, udb_examples=""):
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    
    gemini = dspy.LM('gemini/gemini-2.5-flash', api_key=gemini_key)
    llama_local = dspy.LM('ollama_chat/llama3.1', api_base='http://localhost:11434', timeout_s=300)

    print("[*] Executing RLM Self-Correction Loop with Gemini 2.5...")
    gemini_final = run_rlm_pipeline(gemini, text_snippet, udb_examples)

    print("[*] Executing RLM Self-Correction Loop with Llama 3.1...")
    llama_final = run_rlm_pipeline(llama_local, text_snippet, udb_examples)

    # Helper to handle potential string/object mismatches during the RLM transition
    def serialize(obj):
        if hasattr(obj, 'model_dump_json'):
            return json.loads(obj.model_dump_json())
        return {}

    return {
        "gemini": serialize(gemini_final),
        "llama_local": serialize(llama_final)
    }

def generate_comparison_report(results):
    g_params = {p['name']: p for p in results['gemini'].get('parameters', [])}
    l_params = {p['name']: p for p in results['llama_local'].get('parameters', [])}
    
    g_names = set(g_params.keys())
    l_names = set(l_params.keys())
    
    report = {
        "consensus": list(g_names & l_names),
        "only_gemini": list(g_names - l_names),
        "only_llama": list(l_names - g_names),
        "mismatches": []
    }
    
    for name in report["consensus"]:
        if g_params[name]['classification'] != l_params[name]['classification']:
            report["mismatches"].append({
                "param": name,
                "gemini": g_params[name]['classification'],
                "llama": l_params[name]['classification']
            })
    return report

if __name__ == "__main__":
    snippet = "The capacity and organization of a cache and the size of a cache block are both implementation-specific."
    udb_ref = "cache_block_size, cache_capacity"
    
    results = compare_models(snippet, udb_examples=udb_ref)
    report = generate_comparison_report(results)
    
    os.makedirs("outputs", exist_ok=True)
    with open("outputs/model_comparison_report.yaml", "w") as f:
        yaml.dump(report, f, default_flow_style=False)
    
    print("[+] RLM-validated report saved to outputs/model_comparison_report.yaml")

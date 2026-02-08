import dspy
import yaml
import os
import json
from src.agents.signatures import RISCVArchitecturalMiner

def compare_models(text_snippet, udb_examples=""):
    raw_key = os.getenv("GEMINI_API_KEY", "")
    gemini_key = raw_key.strip()
    
    gemini = dspy.LM('gemini/gemini-2.5-flash', api_key=gemini_key)
    llama_local = dspy.LM('ollama_chat/llama3.1', api_base='http://localhost:11434', timeout_s=300)

    miner = dspy.Predict(RISCVArchitecturalMiner)

    print("[*] Running Extraction with Gemini 2.5 Flash...")
    with dspy.context(lm=gemini):
        gemini_out = miner(text_snippet=text_snippet, udb_examples=udb_examples)

    print("[*] Running Extraction with Local Llama 3.1...")
    with dspy.context(lm=llama_local):
        llama_out = miner(text_snippet=text_snippet, udb_examples=udb_examples)

    # Use json.loads/dumps to clean up Enums for YAML export
    return {
        "gemini": json.loads(gemini_out.extracted_data.model_dump_json()),
        "llama_local": json.loads(llama_out.extracted_data.model_dump_json())
    }

def generate_comparison_report(results):
    g_params = {p['name']: p for p in results['gemini']['parameters']}
    l_params = {p['name']: p for p in results['llama_local']['parameters']}
    
    g_names = set(g_params.keys())
    l_names = set(l_params.keys())
    
    report = {
        "consensus": list(g_names & l_names),
        "only_gemini": list(g_names - l_names),
        "only_llama": list(l_names - g_names),
        "classification_mismatch": []
    }
    
    for name in report["consensus"]:
        if g_params[name]['classification'] != l_params[name]['classification']:
            report["classification_mismatch"].append({
                "parameter": name,
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
        # Use default_flow_style=False for clean, human-readable YAML
        yaml.dump(report, f, default_flow_style=False)
    
    print("[+] Clean comparison report saved to outputs/model_comparison_report.yaml")

import dspy
import os
import yaml
import time
import argparse
from pathlib import Path
from dotenv import load_dotenv
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
from typing import List, Optional

from src.models.schema import ParameterExtraction, RISCVParameter
from src.agents.signatures import RISCVArchitecturalMiner
from src.parsers.spec_parser import RISCVSpecParser
from src.loaders.udb_loader import load_udb_examples
from src.comparators.model_comparator import ModelComparator
from src.validators.hallucination_detector import HallucinationDetector
from src.generators.tag_generator import TagGenerator, TagContext

# Load credentials from .env
load_dotenv()


@retry(
    wait=wait_exponential(multiplier=1, min=4, max=60),
    stop=stop_after_attempt(5),
    retry=retry_if_exception_type(Exception),
    before_sleep=lambda retry_state: print(f"[!] Rate limit hit. Retrying in {retry_state.next_action.sleep}s...")
)
def extract_with_retry(miner, snippet, udb_examples):
    """Wrapper function to handle API calls with exponential backoff."""
    return miner(text_snippet=snippet, udb_examples=udb_examples)


def extract_from_snippets(api_key: str, udb_examples: str) -> List[RISCVParameter]:
    """Extract parameters from hardcoded snippets (legacy mode)."""
    print("[*] Running in LEGACY mode (hardcoded snippets)")
    
    gemini = dspy.LM('gemini/gemini-2.5-flash', api_key=api_key)
    dspy.configure(lm=gemini)
    
    miner = dspy.ChainOfThought(RISCVArchitecturalMiner)
    
    snippets = [
        "Caches organize copies of data into cache blocks, each of which represents a contiguous, naturally aligned power-of-two (or NAPOT) range of memory locations. The capacity and organization of a cache and the size of a cache block are both implementation-specific...",
        "The standard RISC-V ISA sets aside a 12-bit encoding space (csr[11:0]) for up to 4,096 CSRs. By convention, the upper 4 bits of the CSR address (csr[11:8]) are used to encode the read and write accessibility..."
    ]
    
    all_params = []
    for i, snippet in enumerate(snippets):
        print(f"[*] Processing snippet {i+1}/{len(snippets)}...")
        
        prediction = extract_with_retry(miner, snippet, udb_examples)
        
        if prediction.extracted_data:
            all_params.extend(prediction.extracted_data.parameters)
        
        if i < len(snippets) - 1:
            time.sleep(5)
    
    return all_params


def extract_from_spec(api_key: str, spec_path: str, chapter: int, udb_examples: str) -> List[RISCVParameter]:
    """Extract parameters from a RISC-V specification file."""
    print(f"[*] Parsing spec file: {spec_path}")
    print(f"[*] Extracting Chapter {chapter}...")
    
    # Parse spec file
    parser = RISCVSpecParser(spec_path)
    chapter_data = parser.extract_chapter(chapter)
    
    if not chapter_data:
        raise ValueError(f"Chapter {chapter} not found in spec file")
    
    print(f"[+] Found Chapter {chapter}: {chapter_data.title}")
    print(f"[+] Sections: {len(chapter_data.sections)}")
    
    # Chunk the chapter content
    chunks = parser.chunk_text(chapter_data.content, max_tokens=3000, overlap=200)
    print(f"[+] Split into {len(chunks)} chunks for processing")
    
    # Configure LLM
    gemini = dspy.LM('gemini/gemini-2.5-flash', api_key=api_key)
    dspy.configure(lm=gemini)
    
    miner = dspy.ChainOfThought(RISCVArchitecturalMiner)
    
    # Extract from each chunk
    all_params = []
    for i, chunk in enumerate(chunks):
        print(f"[*] Processing chunk {i+1}/{len(chunks)}...")
        
        try:
            prediction = extract_with_retry(miner, chunk, udb_examples)
            
            if prediction.extracted_data:
                all_params.extend(prediction.extracted_data.parameters)
                print(f"    → Extracted {len(prediction.extracted_data.parameters)} parameters")
        
        except Exception as e:
            print(f"[!] Error processing chunk {i+1}: {e}")
            continue
        
        # Rate limiting delay
        if i < len(chunks) - 1:
            time.sleep(5)
    
    return all_params


def save_results(params: List[RISCVParameter], output_path: str):
    """Save extracted parameters to YAML file."""
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    
    yaml_output = {
        "parameters": [p.model_dump(mode="json") for p in params]
    }
    
    with open(output_path, "w") as f:
        yaml.dump(yaml_output, f, sort_keys=False, default_flow_style=False)
    
    print(f"[+] Saved {len(params)} parameters to {output_path}")


def run_extraction(spec_path: Optional[str] = None,
                   chapter: Optional[int] = None,
                   output: str = "outputs/extracted_parameters.yaml",
                   udb_examples_path: str = "data/udb_examples.yaml",
                   num_examples: int = 12,
                   multi_model: bool = False,
                   comparison_output: str = "outputs/model_comparison.yaml",
                   detect_hallucinations: bool = False,
                   generate_tags: bool = False,
                   validation_output: str = "outputs/validation_report.yaml"):
    """
    Main extraction pipeline.
    
    Args:
        spec_path: Path to RISC-V spec file (if None, uses legacy hardcoded snippets)
        chapter: Chapter number to extract
        output: Output YAML file path
        udb_examples_path: Path to UDB examples YAML
        num_examples: Number of UDB examples to use for few-shot prompting
        multi_model: Enable multi-model comparison (Gemini + Llama)
        comparison_output: Output path for comparison report
        detect_hallucinations: Enable hallucination detection
        generate_tags: Enable GraphRAG tag generation
        validation_output: Output path for validation report
    """
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key or not api_key.startswith("AIza"):
        print("[!] Error: GEMINI_API_KEY is missing or invalid in .env")
        return
    
    try:
        # Load UDB examples for few-shot prompting
        print(f"[*] Loading {num_examples} UDB examples from {udb_examples_path}...")
        udb_examples = load_udb_examples(udb_examples_path, num_examples, balanced=True)
        print(f"[+] Loaded UDB examples successfully")
        
        # Multi-model mode
        if multi_model:
            params = run_multi_model_extraction(api_key, spec_path, chapter, udb_examples, comparison_output)
        # Single model mode
        elif spec_path and chapter:
            params = extract_from_spec(api_key, spec_path, chapter, udb_examples)
        else:
            params = extract_from_snippets(api_key, udb_examples)
        
        # Post-processing: Hallucination detection and tag generation
        spec_text = ""
        if detect_hallucinations or generate_tags:
            if spec_path and chapter:
                parser = RISCVSpecParser(spec_path)
                chapter_data = parser.extract_chapter(chapter)
                spec_text = chapter_data.content if chapter_data else ""
        
        # Hallucination detection
        if detect_hallucinations and spec_text:
            print("\n[*] Running hallucination detection...")
            detector = HallucinationDetector(spec_text)
            validation_report = detector.generate_report(params)
            
            print(f"    → Verified: {validation_report['summary']['verified']} params")
            print(f"    → Suspicious: {validation_report['summary']['suspicious']} params")
            print(f"    → Hallucinated: {validation_report['summary']['hallucinated']} params")
            print(f"    → Verification rate: {validation_report['summary']['verification_rate']:.1%}")
            
            # Save validation report
            os.makedirs(os.path.dirname(validation_output) if os.path.dirname(validation_output) else ".", exist_ok=True)
            with open(validation_output, "w") as f:
                yaml.dump(validation_report, f, sort_keys=False, default_flow_style=False)
            print(f"[+] Validation report saved to {validation_output}")
        
        # Tag generation
        if generate_tags:
            print("\n[*] Generating GraphRAG tags...")
            tag_gen = TagGenerator()
            tag_mapping = tag_gen.generate_tags_for_extraction(params, spec_text)
            
            # Update parameters with generated tags
            for param in params:
                if param.name in tag_mapping:
                    param.tag_name = tag_mapping[param.name]
            
            print(f"[+] Generated {len(tag_mapping)} unique tags")
        
        # Save results
        save_results(params, output)
        
        print(f"\n[+] Extraction complete!")
        print(f"[+] Total parameters extracted: {len(params)}")
        
        # Print summary by classification
        classifications = {}
        for p in params:
            cls = p.classification if hasattr(p, 'classification') else 'unknown'
            classifications[cls] = classifications.get(cls, 0) + 1
        
        print(f"\n[*] Breakdown by classification:")
        for cls, count in classifications.items():
            print(f"    - {cls}: {count}")
    
    except Exception as e:
        print(f"[!] Extraction failed: {e}")
        raise


def run_multi_model_extraction(api_key: str,
                               spec_path: Optional[str],
                               chapter: Optional[int],
                               udb_examples: str,
                               comparison_output: str) -> List[RISCVParameter]:
    """
    Run multi-model extraction with consensus detection.
    
    Args:
        api_key: Gemini API key
        spec_path: Path to spec file
        chapter: Chapter number
        udb_examples: UDB examples string
        comparison_output: Path for comparison report
        
    Returns:
        List of consensus parameters with confidence scores
    """
    print("\n[*] Running MULTI-MODEL extraction (Gemini + Llama)...")
    print("[!] Note: This requires Ollama running locally with llama3.1 model")
    
    # Initialize comparator
    comparator = ModelComparator(gemini_api_key=api_key)
    
    # Get text snippets
    if spec_path and chapter:
        print(f"[*] Parsing spec file: {spec_path}")
        parser = RISCVSpecParser(spec_path)
        chapter_data = parser.extract_chapter(chapter)
        
        if not chapter_data:
            raise ValueError(f"Chapter {chapter} not found in spec file")
        
        chunks = parser.chunk_text(chapter_data.content, max_tokens=3000, overlap=200)
        print(f"[+] Split into {len(chunks)} chunks for processing")
    else:
        # Legacy mode
        chunks = [
            "Caches organize copies of data into cache blocks, each of which represents a contiguous, naturally aligned power-of-two (or NAPOT) range of memory locations. The capacity and organization of a cache and the size of a cache block are both implementation-specific...",
            "The standard RISC-V ISA sets aside a 12-bit encoding space (csr[11:0]) for up to 4,096 CSRs. By convention, the upper 4 bits of the CSR address (csr[11:8]) are used to encode the read and write accessibility..."
        ]
    
    # Process each chunk with both models
    all_consensus_params = []
    all_reports = []
    
    for i, chunk in enumerate(chunks):
        print(f"\n[*] Processing chunk {i+1}/{len(chunks)} with both models...")
        
        try:
            # Run both models
            results = comparator.compare_models(chunk, udb_examples)
            
            # Generate consensus
            consensus_params = comparator.generate_consensus(results["gemini"], results["llama"])
            all_consensus_params.extend(consensus_params)
            
            # Generate comparison report
            report = comparator.generate_comparison_report(results["gemini"], results["llama"])
            report['chunk_index'] = i + 1
            all_reports.append(report)
            
            print(f"    → Consensus: {report['summary']['consensus_params']} params")
            print(f"    → Only Gemini: {report['summary']['only_gemini']} params")
            print(f"    → Only Llama: {report['summary']['only_llama']} params")
            print(f"    → Mismatches: {report['summary']['classification_mismatches']} params")
            
        except Exception as e:
            print(f"[!] Error processing chunk {i+1}: {e}")
            continue
        
        # Rate limiting
        if i < len(chunks) - 1:
            time.sleep(5)
    
    # Save comparison report
    os.makedirs(os.path.dirname(comparison_output) if os.path.dirname(comparison_output) else ".", exist_ok=True)
    
    with open(comparison_output, "w") as f:
        yaml.dump({
            "chunks_processed": len(chunks),
            "total_consensus_params": len(all_consensus_params),
            "chunk_reports": all_reports
        }, f, sort_keys=False, default_flow_style=False)
    
    print(f"\n[+] Comparison report saved to {comparison_output}")
    
    return all_consensus_params


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="RISC-V Architectural Parameter Extractor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract from hardcoded snippets (legacy mode)
  python -m src.main

  # Extract Chapter 3 from a spec file
  python -m src.main --spec-path specs/riscv-privileged.md --chapter 3

  # Extract with custom output path
  python -m src.main --spec-path specs/riscv-privileged.md --chapter 3 --output results/chapter3.yaml

  # Use fewer UDB examples
  python -m src.main --spec-path specs/riscv-privileged.md --chapter 3 --num-examples 6
  
  # Multi-model extraction with consensus (requires Ollama)
  python -m src.main --spec-path specs/riscv-privileged.md --chapter 3 --multi-model
        """
    )
    
    parser.add_argument(
        '--spec-path',
        type=str,
        help='Path to RISC-V specification file (Markdown or AsciiDoc)'
    )
    
    parser.add_argument(
        '--chapter',
        type=int,
        help='Chapter number to extract (e.g., 3 for Chapter 3)'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default='outputs/extracted_parameters.yaml',
        help='Output YAML file path (default: outputs/extracted_parameters.yaml)'
    )
    
    parser.add_argument(
        '--udb-examples',
        type=str,
        default='data/udb_examples.yaml',
        help='Path to UDB examples YAML (default: data/udb_examples.yaml)'
    )
    
    parser.add_argument(
        '--num-examples',
        type=int,
        default=12,
        help='Number of UDB examples to use for few-shot prompting (default: 12)'
    )
    
    parser.add_argument(
        '--multi-model',
        action='store_true',
        help='Enable multi-model comparison (Gemini + Llama via Ollama)'
    )
    
    parser.add_argument(
        '--comparison-output',
        type=str,
        default='outputs/model_comparison.yaml',
        help='Output path for model comparison report (default: outputs/model_comparison.yaml)'
    )
    
    parser.add_argument(
        '--detect-hallucinations',
        action='store_true',
        help='Enable hallucination detection (verify source quotes exist in spec)'
    )
    
    parser.add_argument(
        '--generate-tags',
        action='store_true',
        help='Enable GraphRAG-based tag name generation for unnamed parameters'
    )
    
    parser.add_argument(
        '--validation-output',
        type=str,
        default='outputs/validation_report.yaml',
        help='Output path for validation report (default: outputs/validation_report.yaml)'
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.spec_path and not args.chapter:
        parser.error("--chapter is required when --spec-path is specified")
    
    if args.chapter and not args.spec_path:
        parser.error("--spec-path is required when --chapter is specified")
    
    # Run extraction
    run_extraction(
        spec_path=args.spec_path,
        chapter=args.chapter,
        output=args.output,
        udb_examples_path=args.udb_examples,
        num_examples=args.num_examples,
        multi_model=args.multi_model,
        comparison_output=args.comparison_output,
        detect_hallucinations=args.detect_hallucinations,
        generate_tags=args.generate_tags,
        validation_output=args.validation_output
    )


if __name__ == "__main__":
    main()
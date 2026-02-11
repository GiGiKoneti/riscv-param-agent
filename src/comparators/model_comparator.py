"""
Multi-model comparison and consensus detection for RISC-V parameter extraction.

This module implements:
1. RLM (Recursive Language Model) verification
2. Multi-model extraction (Gemini + Llama)
3. Consensus detection and confidence scoring
4. Comparison report generation
"""

import dspy
import os
import json
from typing import List, Dict, Tuple, Optional
from enum import Enum

from src.models.schema import ParameterExtraction, RISCVParameter
from src.agents.signatures import RISCVArchitecturalMiner


class ConfidenceLevel(str, Enum):
    """Confidence levels for extracted parameters."""
    HIGH = "HIGH"      # Both models agree on name and classification
    MEDIUM = "MEDIUM"  # Both models agree on name, different classification
    LOW = "LOW"        # Only one model found the parameter


class RLMVerification(dspy.Signature):
    """
    Verification Critic: Reviews extracted parameters against the original spec
    to identify hallucinations or missing constraints.
    """
    text_snippet = dspy.InputField()
    extracted_data = dspy.InputField(desc="The initial Pydantic extraction")
    critique = dspy.OutputField(desc="Identify specific errors or missing bit-fields")
    corrected_data: ParameterExtraction = dspy.OutputField(desc="The final hardware-validated ParameterExtraction")


class ModelComparator:
    """
    Handles multi-model extraction and comparison.
    
    Implements the Recursive Language Model (RLM) method via a 
    Self-Correction REPL loop using BMA (Branching Memory Architecture).
    """
    
    def __init__(self, gemini_api_key: Optional[str] = None, ollama_base: str = "http://localhost:11434"):
        """
        Initialize model comparator.
        
        Args:
            gemini_api_key: Gemini API key (defaults to GEMINI_API_KEY env var)
            ollama_base: Ollama API base URL
        """
        self.gemini_api_key = gemini_api_key or os.getenv("GEMINI_API_KEY", "").strip()
        self.ollama_base = ollama_base
        
        # Initialize models
        self.gemini = dspy.LM('gemini/gemini-2.5-flash', api_key=self.gemini_api_key)
        self.llama = dspy.LM('ollama_chat/llama3.1', api_base=self.ollama_base, timeout_s=300)
    
    def run_rlm_pipeline(self, lm: dspy.LM, text_snippet: str, udb_examples: str) -> ParameterExtraction:
        """
        Run RLM self-correction loop for a single model.
        
        Args:
            lm: Language model to use
            text_snippet: Text to extract parameters from
            udb_examples: UDB examples for few-shot learning
            
        Returns:
            Corrected parameter extraction
        """
        with dspy.context(lm=lm):
            # Branch 1: Task Memory (Initial Extraction)
            extractor = dspy.Predict(RISCVArchitecturalMiner)
            initial_out = extractor(text_snippet=text_snippet, udb_examples=udb_examples)
            
            # Branch 2: Critic Branch (Recursive Verification)
            verifier = dspy.ChainOfThought(RLMVerification)
            verification = verifier(
                text_snippet=text_snippet, 
                extracted_data=initial_out.extracted_data
            )
            
            # BMA Logic: Return structured object
            return verification.corrected_data if hasattr(verification, 'corrected_data') else initial_out.extracted_data
    
    def extract_with_model(self, model_name: str, text_snippet: str, udb_examples: str) -> ParameterExtraction:
        """
        Extract parameters using a specific model.
        
        Args:
            model_name: "gemini" or "llama"
            text_snippet: Text to extract from
            udb_examples: UDB examples
            
        Returns:
            Parameter extraction result
        """
        lm = self.gemini if model_name == "gemini" else self.llama
        return self.run_rlm_pipeline(lm, text_snippet, udb_examples)
    
    def compare_models(self, text_snippet: str, udb_examples: str = "") -> Dict[str, ParameterExtraction]:
        """
        Run extraction with both models and return results.
        
        Args:
            text_snippet: Text to extract from
            udb_examples: UDB examples for few-shot learning
            
        Returns:
            Dictionary with "gemini" and "llama" extraction results
        """
        print("[*] Executing RLM Self-Correction Loop with Gemini 2.5...")
        gemini_result = self.run_rlm_pipeline(self.gemini, text_snippet, udb_examples)
        
        print("[*] Executing RLM Self-Correction Loop with Llama 3.1...")
        llama_result = self.run_rlm_pipeline(self.llama, text_snippet, udb_examples)
        
        return {
            "gemini": gemini_result,
            "llama": llama_result
        }
    
    def calculate_confidence(self, param_name: str, gemini_params: Dict, llama_params: Dict) -> ConfidenceLevel:
        """
        Calculate confidence level for a parameter based on model agreement.
        
        Args:
            param_name: Parameter name
            gemini_params: Gemini extracted parameters (name -> param dict)
            llama_params: Llama extracted parameters (name -> param dict)
            
        Returns:
            Confidence level (HIGH/MEDIUM/LOW)
        """
        in_gemini = param_name in gemini_params
        in_llama = param_name in llama_params
        
        # Only one model found it
        if in_gemini != in_llama:
            return ConfidenceLevel.LOW
        
        # Both models found it
        if in_gemini and in_llama:
            gemini_class = gemini_params[param_name].get('classification', '')
            llama_class = llama_params[param_name].get('classification', '')
            
            # Same classification = HIGH confidence
            if gemini_class == llama_class:
                return ConfidenceLevel.HIGH
            else:
                return ConfidenceLevel.MEDIUM
        
        return ConfidenceLevel.LOW
    
    def generate_consensus(self, gemini_result: ParameterExtraction, llama_result: ParameterExtraction) -> List[RISCVParameter]:
        """
        Generate consensus parameters with confidence scores.
        
        Args:
            gemini_result: Gemini extraction result
            llama_result: Llama extraction result
            
        Returns:
            List of parameters with confidence scores
        """
        # Convert to dictionaries for easier comparison
        gemini_params = {p.name: p.model_dump() for p in gemini_result.parameters}
        llama_params = {p.name: p.model_dump() for p in llama_result.parameters}
        
        # Get all unique parameter names
        all_names = set(gemini_params.keys()) | set(llama_params.keys())
        
        consensus_params = []
        for name in all_names:
            confidence = self.calculate_confidence(name, gemini_params, llama_params)
            
            # Prefer Gemini for HIGH/MEDIUM confidence, use whichever found it for LOW
            if name in gemini_params:
                param_dict = gemini_params[name].copy()
            else:
                param_dict = llama_params[name].copy()
            
            # Add confidence metadata
            param_dict['extraction_metadata'] = {
                'confidence': confidence.value,
                'found_by_gemini': name in gemini_params,
                'found_by_llama': name in llama_params
            }
            
            # Reconstruct RISCVParameter
            consensus_params.append(RISCVParameter(**param_dict))
        
        return consensus_params
    
    def generate_comparison_report(self, gemini_result: ParameterExtraction, llama_result: ParameterExtraction) -> Dict:
        """
        Generate detailed comparison report.
        
        Args:
            gemini_result: Gemini extraction result
            llama_result: Llama extraction result
            
        Returns:
            Comparison report dictionary
        """
        gemini_params = {p.name: p.model_dump() for p in gemini_result.parameters}
        llama_params = {p.name: p.model_dump() for p in llama_result.parameters}
        
        gemini_names = set(gemini_params.keys())
        llama_names = set(llama_params.keys())
        
        consensus_names = gemini_names & llama_names
        
        # Find classification mismatches
        mismatches = []
        for name in consensus_names:
            g_class = gemini_params[name].get('classification', '')
            l_class = llama_params[name].get('classification', '')
            
            if g_class != l_class:
                mismatches.append({
                    "param": name,
                    "gemini_classification": g_class,
                    "llama_classification": l_class
                })
        
        report = {
            "summary": {
                "total_unique_params": len(gemini_names | llama_names),
                "consensus_params": len(consensus_names),
                "only_gemini": len(gemini_names - llama_names),
                "only_llama": len(llama_names - gemini_names),
                "classification_mismatches": len(mismatches)
            },
            "consensus": list(consensus_names),
            "only_gemini": list(gemini_names - llama_names),
            "only_llama": list(llama_names - gemini_names),
            "classification_mismatches": mismatches
        }
        
        return report


def serialize_extraction(extraction: ParameterExtraction) -> Dict:
    """
    Serialize ParameterExtraction to dictionary.
    
    Args:
        extraction: ParameterExtraction object
        
    Returns:
        Dictionary representation
    """
    if hasattr(extraction, 'model_dump'):
        return extraction.model_dump()
    elif hasattr(extraction, 'model_dump_json'):
        return json.loads(extraction.model_dump_json())
    return {}

"""
Hallucination detection for RISC-V parameter extraction.

This module verifies that extracted parameters are grounded in the actual spec text,
preventing LLM hallucinations by checking:
1. Source quotes actually exist in the spec
2. Parameter names appear in the spec (for named parameters)
3. Suspicious patterns that indicate hallucination
"""

from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from difflib import SequenceMatcher
import re

from src.models.schema import RISCVParameter, ParameterCategory


@dataclass
class HallucinationReport:
    """Report of hallucination detection results."""
    verified_params: List[RISCVParameter]
    suspicious_params: List[RISCVParameter]
    hallucinated_params: List[RISCVParameter]
    verification_details: Dict[str, Dict]


class HallucinationDetector:
    """
    Detects hallucinations in extracted parameters by verifying against source text.
    """
    
    def __init__(self, spec_text: str, similarity_threshold: float = 0.85):
        """
        Initialize hallucination detector.
        
        Args:
            spec_text: Full specification text to verify against
            similarity_threshold: Minimum similarity ratio for fuzzy matching (0.0-1.0)
        """
        self.spec_text = spec_text
        self.similarity_threshold = similarity_threshold
        
        # Normalize spec text for better matching
        self.normalized_spec = self._normalize_text(spec_text)
    
    def _normalize_text(self, text: str) -> str:
        """
        Normalize text for comparison by removing extra whitespace.
        
        Args:
            text: Text to normalize
            
        Returns:
            Normalized text
        """
        # Replace multiple whitespace with single space
        normalized = re.sub(r'\s+', ' ', text)
        return normalized.strip()
    
    def verify_source_quote(self, param: RISCVParameter) -> Tuple[bool, float, str]:
        """
        Verify that the source quote actually exists in the spec.
        
        Args:
            param: Parameter to verify
            
        Returns:
            Tuple of (is_verified, similarity_score, match_type)
            - is_verified: True if quote found (exact or fuzzy match)
            - similarity_score: 1.0 for exact, 0.0-1.0 for fuzzy, 0.0 for no match
            - match_type: "exact", "fuzzy", or "none"
        """
        if not param.source_quote:
            return False, 0.0, "none"
        
        normalized_quote = self._normalize_text(param.source_quote)
        
        # Check for exact match
        if normalized_quote in self.normalized_spec:
            return True, 1.0, "exact"
        
        # Check for fuzzy match (handles minor variations)
        best_similarity = 0.0
        quote_words = normalized_quote.split()
        
        # Use sliding window to find best match
        window_size = len(quote_words)
        spec_words = self.normalized_spec.split()
        
        for i in range(len(spec_words) - window_size + 1):
            window = ' '.join(spec_words[i:i + window_size])
            similarity = SequenceMatcher(None, normalized_quote, window).ratio()
            best_similarity = max(best_similarity, similarity)
            
            if best_similarity >= self.similarity_threshold:
                return True, best_similarity, "fuzzy"
        
        return False, best_similarity, "none"
    
    def verify_parameter_name(self, param: RISCVParameter) -> bool:
        """
        Verify that parameter name appears in spec (for named parameters).
        
        Args:
            param: Parameter to verify
            
        Returns:
            True if name found in spec (case-insensitive)
        """
        if param.classification != ParameterCategory.NAMED:
            # Only verify named parameters
            return True
        
        # Check if name appears in spec (case-insensitive)
        name_pattern = re.compile(re.escape(param.name), re.IGNORECASE)
        return bool(name_pattern.search(self.spec_text))
    
    def flag_suspicious_params(self, param: RISCVParameter) -> List[str]:
        """
        Identify suspicious patterns that indicate hallucination.
        
        Args:
            param: Parameter to check
            
        Returns:
            List of suspicion reasons (empty if not suspicious)
        """
        suspicions = []
        
        # Check 1: Source quote is too short
        if len(param.source_quote.split()) < 5:
            suspicions.append("source_quote_too_short")
        
        # Check 2: Source quote is suspiciously generic
        generic_phrases = [
            "implementation defined",
            "implementation specific",
            "may be",
            "can be",
            "is defined"
        ]
        if any(phrase in param.source_quote.lower() for phrase in generic_phrases) and len(param.source_quote.split()) < 10:
            suspicions.append("generic_quote")
        
        # Check 3: Named parameter but name not in quote
        if param.classification == ParameterCategory.NAMED:
            if param.name.lower() not in param.source_quote.lower():
                suspicions.append("named_param_not_in_quote")
        
        # Check 4: Description is too vague
        vague_words = ["parameter", "value", "setting", "option", "configuration"]
        desc_words = param.description.lower().split()
        if len(desc_words) < 5 and any(word in desc_words for word in vague_words):
            suspicions.append("vague_description")
        
        # Check 5: Rationale is too short or missing
        if len(param.rationale.split()) < 10:
            suspicions.append("weak_rationale")
        
        return suspicions
    
    def verify_parameter(self, param: RISCVParameter) -> Dict:
        """
        Comprehensive verification of a single parameter.
        
        Args:
            param: Parameter to verify
            
        Returns:
            Verification details dictionary
        """
        quote_verified, similarity, match_type = self.verify_source_quote(param)
        name_verified = self.verify_parameter_name(param)
        suspicions = self.flag_suspicious_params(param)
        
        # Determine overall status
        if quote_verified and name_verified and not suspicions:
            status = "verified"
        elif not quote_verified or not name_verified:
            status = "hallucinated"
        else:
            status = "suspicious"
        
        return {
            "status": status,
            "quote_verified": quote_verified,
            "quote_similarity": similarity,
            "quote_match_type": match_type,
            "name_verified": name_verified,
            "suspicions": suspicions,
            "suspicion_count": len(suspicions)
        }
    
    def verify_all(self, parameters: List[RISCVParameter]) -> HallucinationReport:
        """
        Verify all extracted parameters.
        
        Args:
            parameters: List of parameters to verify
            
        Returns:
            Hallucination report with categorized parameters
        """
        verified = []
        suspicious = []
        hallucinated = []
        details = {}
        
        for param in parameters:
            verification = self.verify_parameter(param)
            details[param.name] = verification
            
            if verification["status"] == "verified":
                verified.append(param)
            elif verification["status"] == "suspicious":
                suspicious.append(param)
            else:
                hallucinated.append(param)
        
        return HallucinationReport(
            verified_params=verified,
            suspicious_params=suspicious,
            hallucinated_params=hallucinated,
            verification_details=details
        )
    
    def generate_report(self, parameters: List[RISCVParameter]) -> Dict:
        """
        Generate detailed hallucination detection report.
        
        Args:
            parameters: List of parameters to verify
            
        Returns:
            Report dictionary
        """
        report_obj = self.verify_all(parameters)
        
        return {
            "summary": {
                "total_params": len(parameters),
                "verified": len(report_obj.verified_params),
                "suspicious": len(report_obj.suspicious_params),
                "hallucinated": len(report_obj.hallucinated_params),
                "verification_rate": len(report_obj.verified_params) / len(parameters) if parameters else 0.0
            },
            "verified_params": [p.name for p in report_obj.verified_params],
            "suspicious_params": [
                {
                    "name": p.name,
                    "suspicions": report_obj.verification_details[p.name]["suspicions"]
                }
                for p in report_obj.suspicious_params
            ],
            "hallucinated_params": [
                {
                    "name": p.name,
                    "quote_verified": report_obj.verification_details[p.name]["quote_verified"],
                    "name_verified": report_obj.verification_details[p.name]["name_verified"],
                    "quote_similarity": report_obj.verification_details[p.name]["quote_similarity"]
                }
                for p in report_obj.hallucinated_params
            ],
            "details": report_obj.verification_details
        }

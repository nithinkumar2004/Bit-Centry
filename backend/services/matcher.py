"""
Matcher Service — Semantic similarity matching using Sentence-BERT.
Combines embedding-based similarity with rule-based numeric checks.
"""
import logging
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

# Lazy-loaded model
_model = None


def _get_model():
    """Lazy-load the Sentence-BERT model."""
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("✅ Sentence-BERT model loaded (all-MiniLM-L6-v2)")
        except Exception as e:
            logger.error(f"❌ Failed to load Sentence-BERT: {e}")
    return _model


class MatcherService:
    """Service for semantic matching between criteria and extracted data."""

    @staticmethod
    def compute_similarity(text1: str, text2: str) -> float:
        """
        Compute cosine similarity between two text strings using Sentence-BERT.
        
        Returns:
            Similarity score between 0 and 1
        """
        model = _get_model()
        if model is None:
            return 0.0

        try:
            from sklearn.metrics.pairwise import cosine_similarity
            import numpy as np

            embeddings = model.encode([text1, text2])
            sim = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
            return float(max(0.0, min(1.0, sim)))
        except Exception as e:
            logger.error(f"Similarity computation failed: {e}")
            return 0.0

    @staticmethod
    def find_best_match(
        query: str, 
        candidates: List[str]
    ) -> Tuple[int, float]:
        """
        Find the best matching candidate for a query.
        
        Returns:
            Tuple of (best_index, best_similarity)
        """
        if not candidates:
            return -1, 0.0

        model = _get_model()
        if model is None:
            return 0, 0.0

        try:
            from sklearn.metrics.pairwise import cosine_similarity
            
            query_embedding = model.encode([query])
            candidate_embeddings = model.encode(candidates)
            
            similarities = cosine_similarity(query_embedding, candidate_embeddings)[0]
            best_idx = int(similarities.argmax())
            best_sim = float(similarities[best_idx])
            
            return best_idx, best_sim
        except Exception as e:
            logger.error(f"Best match search failed: {e}")
            return 0, 0.0

    @staticmethod
    def match_criteria_to_data(
        criteria: List[Dict[str, Any]],
        extracted_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Match each criterion to the most relevant extracted data field.
        Uses a hybrid approach: semantic similarity for text matching + 
        rule-based logic for numeric/boolean checks.
        
        Args:
            criteria: List of criterion dicts with type, description, threshold
            extracted_data: Dict with turnover, certifications, project_count, etc.
            
        Returns:
            List of match results with matched_value, match_type, and confidence
        """
        results = []
        
        for criterion in criteria:
            c_type = criterion.get("type", "").lower()
            c_desc = criterion.get("description", "").lower()
            c_threshold = criterion.get("threshold")
            c_id = criterion.get("id", "?")
            
            matched_value = None
            match_confidence = 0.0
            match_type = "semantic"
            source_field = None

            # Rule-based matching by criterion type
            if c_type == "financial":
                # Match to turnover
                turnover = extracted_data.get("turnover")
                if turnover is not None:
                    matched_value = turnover
                    match_confidence = 0.95
                    match_type = "rule"
                    source_field = "turnover"
                else:
                    # Try semantic matching against raw text
                    raw_text = extracted_data.get("raw_text", "")
                    if raw_text:
                        sim = MatcherService.compute_similarity(
                            criterion.get("description", ""),
                            raw_text[:500]
                        )
                        match_confidence = sim
                        match_type = "semantic"

            elif c_type == "compliance":
                # Match to certifications
                certs = extracted_data.get("certifications", [])
                cert_keywords = {
                    "gst": ["gst", "gstin", "goods and service"],
                    "iso": ["iso", "iso 9001", "iso 14001", "iso certification"],
                    "pan": ["pan", "permanent account"],
                    "msme": ["msme", "udyam", "udyog"],
                    "epf": ["epf", "provident fund"],
                    "esi": ["esi", "employee state insurance"],
                }

                matched_cert = None
                for cert_type, keywords in cert_keywords.items():
                    if any(kw in c_desc for kw in keywords):
                        # Check if this cert exists in extracted certs
                        cert_found = any(
                            cert_type.upper() in c.upper() or
                            any(kw in c.lower() for kw in keywords)
                            for c in certs
                        )
                        if cert_found:
                            matched_value = True
                            matched_cert = cert_type.upper()
                        else:
                            matched_value = False
                        match_confidence = 0.9
                        match_type = "rule"
                        source_field = "certifications"
                        break

                if matched_value is None:
                    # Fallback: semantic match against cert list
                    if certs:
                        cert_text = ", ".join(certs)
                        sim = MatcherService.compute_similarity(
                            criterion.get("description", ""),
                            cert_text
                        )
                        match_confidence = sim
                        matched_value = sim > 0.6
                        match_type = "semantic"
                        source_field = "certifications"

            elif c_type == "technical":
                # Match to project count or experience
                if "project" in c_desc or "similar" in c_desc or "experience" in c_desc:
                    project_count = extracted_data.get("project_count")
                    if project_count is not None:
                        matched_value = project_count
                        match_confidence = 0.9
                        match_type = "rule"
                        source_field = "project_count"

            # If no rule-based match found, try semantic on raw text
            if matched_value is None and match_confidence < 0.5:
                raw_text = extracted_data.get("raw_text", "")
                if raw_text:
                    sim = MatcherService.compute_similarity(
                        criterion.get("description", ""),
                        raw_text[:1000]
                    )
                    match_confidence = sim * 0.7  # Reduce confidence for raw text matches
                    match_type = "semantic"

            results.append({
                "criterion_id": c_id,
                "criterion_type": c_type,
                "criterion_description": criterion.get("description", ""),
                "threshold": c_threshold,
                "matched_value": matched_value,
                "match_confidence": match_confidence,
                "match_type": match_type,
                "source_field": source_field
            })

        return results

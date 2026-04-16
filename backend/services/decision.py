"""
Decision Engine — Deterministic evaluation of bidders against tender criteria.
Combines matched data with threshold rules to produce Eligible/Not Eligible/Needs Review decisions.
"""
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class DecisionEngine:
    """Rule-based decision engine for tender evaluation."""

    AMBIGUITY_THRESHOLD = 0.75  # Below this confidence → Needs Manual Review
    
    @staticmethod
    def evaluate_single_criterion(
        match_result: Dict[str, Any],
        criterion: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evaluate a single criterion against matched data.
        
        Returns dict with: decision, confidence, explanation, is_ambiguous
        """
        c_type = criterion.get("type", "").lower()
        c_desc = criterion.get("description", "")
        threshold = criterion.get("threshold")
        mandatory = criterion.get("mandatory", True)
        
        matched_value = match_result.get("matched_value")
        match_confidence = match_result.get("match_confidence", 0.0)
        match_type = match_result.get("match_type", "unknown")
        
        decision = "Needs Manual Review"
        confidence = match_confidence
        is_ambiguous = False
        explanation = ""
        value_str = str(matched_value) if matched_value is not None else "Not found"

        # Case 1: No value extracted
        if matched_value is None:
            if mandatory:
                decision = "Needs Manual Review"
                is_ambiguous = True
                explanation = f"Could not extract value for: {c_desc}. Manual verification required."
            else:
                decision = "Eligible"
                confidence = 0.8
                explanation = f"Optional criterion: {c_desc}. No data found but criterion is not mandatory."
            
            return {
                "decision": decision,
                "confidence": confidence,
                "extracted_value": value_str,
                "explanation": explanation,
                "is_ambiguous": is_ambiguous
            }

        # Case 2: Low confidence
        if match_confidence < DecisionEngine.AMBIGUITY_THRESHOLD:
            decision = "Needs Manual Review"
            is_ambiguous = True
            explanation = (
                f"Low confidence match ({match_confidence:.0%}) for: {c_desc}. "
                f"Extracted value: {value_str}. Manual review recommended."
            )
            return {
                "decision": decision,
                "confidence": confidence,
                "extracted_value": value_str,
                "explanation": explanation,
                "is_ambiguous": is_ambiguous
            }

        # Case 3: Financial — numeric threshold comparison
        if c_type == "financial":
            if threshold is not None:
                try:
                    numeric_value = float(matched_value)
                    if numeric_value >= threshold:
                        decision = "Eligible"
                        confidence = min(0.95, match_confidence)
                        explanation = (
                            f"Bidder's turnover (₹{numeric_value:.2f} Cr) meets the minimum "
                            f"requirement of ₹{threshold:.2f} Cr."
                        )
                    else:
                        decision = "Not Eligible"
                        confidence = min(0.95, match_confidence)
                        explanation = (
                            f"Bidder's turnover (₹{numeric_value:.2f} Cr) is below the minimum "
                            f"requirement of ₹{threshold:.2f} Cr."
                        )
                except (ValueError, TypeError):
                    decision = "Needs Manual Review"
                    is_ambiguous = True
                    explanation = f"Unable to parse numeric value for: {c_desc}. Value: {value_str}."
            else:
                decision = "Needs Manual Review"
                is_ambiguous = True
                explanation = f"Financial criterion has no defined threshold: {c_desc}."

        # Case 4: Compliance — boolean check
        elif c_type == "compliance":
            if isinstance(matched_value, bool):
                if matched_value:
                    decision = "Eligible"
                    confidence = min(0.95, match_confidence)
                    explanation = f"Required certification/registration found: {c_desc}."
                else:
                    decision = "Not Eligible"
                    confidence = min(0.90, match_confidence)
                    explanation = f"Required certification/registration NOT found: {c_desc}."
            else:
                decision = "Needs Manual Review"
                is_ambiguous = True
                explanation = f"Compliance check unclear for: {c_desc}. Extracted: {value_str}."

        # Case 5: Technical — count comparison
        elif c_type == "technical":
            if threshold is not None:
                try:
                    numeric_value = float(matched_value)
                    if numeric_value >= threshold:
                        decision = "Eligible"
                        confidence = min(0.95, match_confidence)
                        explanation = (
                            f"Bidder has {int(numeric_value)} completed projects, "
                            f"meeting the minimum requirement of {int(threshold)}."
                        )
                    else:
                        decision = "Not Eligible"
                        confidence = min(0.95, match_confidence)
                        explanation = (
                            f"Bidder has {int(numeric_value)} completed projects, "
                            f"below the minimum requirement of {int(threshold)}."
                        )
                except (ValueError, TypeError):
                    decision = "Needs Manual Review"
                    is_ambiguous = True
                    explanation = f"Unable to parse count for: {c_desc}. Value: {value_str}."
            else:
                decision = "Needs Manual Review"
                is_ambiguous = True
                explanation = f"Technical criterion has no defined threshold: {c_desc}."

        else:
            decision = "Needs Manual Review"
            is_ambiguous = True
            explanation = f"Unknown criterion type for: {c_desc}."

        return {
            "decision": decision,
            "confidence": confidence,
            "extracted_value": value_str,
            "explanation": explanation,
            "is_ambiguous": is_ambiguous
        }

    @staticmethod
    def evaluate_bidder(
        criteria: List[Dict[str, Any]],
        match_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Evaluate all criteria for a single bidder.
        
        Returns list of evaluation results per criterion.
        """
        evaluations = []
        
        for criterion, match in zip(criteria, match_results):
            result = DecisionEngine.evaluate_single_criterion(match, criterion)
            result["criterion_id"] = criterion.get("id", "?")
            result["criterion_description"] = criterion.get("description", "")
            result["criterion_type"] = criterion.get("type", "")
            result["threshold"] = str(criterion.get("threshold", "")) if criterion.get("threshold") else None
            evaluations.append(result)

        return evaluations

    @staticmethod
    def compute_final_status(results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Compute the overall evaluation status from individual criterion results.
        
        Rules:
        - If ANY mandatory criterion is "Not Eligible" → Not Eligible
        - If ANY criterion is "Needs Manual Review" → Needs Manual Review
        - Otherwise → Eligible
        """
        if not results:
            return {
                "final_status": "Needs Manual Review",
                "overall_confidence": 0.0,
                "ambiguous_count": 0
            }

        has_not_eligible = any(r["decision"] == "Not Eligible" for r in results)
        has_review = any(r["decision"] == "Needs Manual Review" for r in results)
        ambiguous_count = sum(1 for r in results if r.get("is_ambiguous", False))
        
        confidences = [r.get("confidence", 0.0) for r in results]
        overall_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        if has_not_eligible:
            final_status = "Not Eligible"
        elif has_review:
            final_status = "Needs Manual Review"
        else:
            final_status = "Eligible"

        return {
            "final_status": final_status,
            "overall_confidence": round(overall_confidence, 3),
            "ambiguous_count": ambiguous_count
        }

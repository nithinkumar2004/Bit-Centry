"""
Evaluation API routes — Run evaluations, view results, export reports.
"""
import csv
import io
import json
import logging
from datetime import datetime

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from backend.db.mongodb import Database
from backend.services.matcher import MatcherService
from backend.services.decision import DecisionEngine
from backend.services.llm import LLMService
from backend.services.audit import AuditService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/evaluations", tags=["evaluations"])


@router.post("/run")
async def run_evaluation(
    tender_id: str = Query(...),
    bidder_ids: str = Query(None, description="Comma-separated bidder IDs. If empty, evaluates all bidders for the tender.")
):
    """
    Run evaluation for bidder(s) against a tender's criteria.
    Uses semantic matching + rule-based decision engine.
    """
    # Get tender
    tender_col = Database.get_collection("tenders")
    try:
        tender = await tender_col.find_one({"_id": ObjectId(tender_id)})
    except Exception:
        raise HTTPException(400, "Invalid tender ID")

    if not tender:
        raise HTTPException(404, "Tender not found")

    criteria = tender.get("criteria", [])
    if not criteria:
        raise HTTPException(400, "Tender has no criteria. Extract criteria first.")

    # Get bidders
    bidder_col = Database.get_collection("bidders")
    
    if bidder_ids:
        bid_list = [b.strip() for b in bidder_ids.split(",")]
        try:
            bidder_query = {"_id": {"$in": [ObjectId(b) for b in bid_list]}}
        except Exception:
            raise HTTPException(400, "Invalid bidder ID(s)")
    else:
        bidder_query = {"tender_id": tender_id}

    bidders = []
    async for doc in bidder_col.find(bidder_query):
        bidders.append(doc)

    if not bidders:
        raise HTTPException(404, "No bidders found for this tender")

    # Evaluate each bidder
    eval_col = Database.get_collection("evaluations")
    evaluations = []

    for bidder in bidders:
        bidder_id = str(bidder["_id"])
        extracted_data = bidder.get("extracted_data", {})

        # Step 1: Match criteria to extracted data
        match_results = MatcherService.match_criteria_to_data(criteria, extracted_data)

        # Step 2: Evaluate each criterion
        criterion_results = DecisionEngine.evaluate_bidder(criteria, match_results)

        # Step 3: Generate explanations via LLM (optional enhancement)
        for result in criterion_results:
            try:
                explanation = await LLMService.generate_explanation(
                    criterion_description=result.get("criterion_description", ""),
                    extracted_value=result.get("extracted_value", "Not found"),
                    decision=result.get("decision", ""),
                    context=f"Bidder: {bidder.get('name', '')}"
                )
                result["explanation"] = explanation
            except Exception as e:
                logger.debug(f"Explanation generation failed: {e}")
                # Keep template-based explanation

            # Add source document info
            docs = bidder.get("documents", [])
            result["source_document"] = docs[0]["filename"] if docs else "Unknown"

        # Step 4: Compute final status
        final = DecisionEngine.compute_final_status(criterion_results)

        # Store evaluation
        eval_doc = {
            "tender_id": tender_id,
            "bidder_id": bidder_id,
            "bidder_name": bidder.get("name", ""),
            "results": criterion_results,
            "final_status": final["final_status"],
            "overall_confidence": final["overall_confidence"],
            "ambiguous_count": final["ambiguous_count"],
            "evaluated_at": datetime.utcnow()
        }

        # Upsert — update if evaluation already exists for this tender+bidder pair
        await eval_col.update_one(
            {"tender_id": tender_id, "bidder_id": bidder_id},
            {"$set": eval_doc},
            upsert=True
        )

        # Get the evaluation ID
        stored = await eval_col.find_one(
            {"tender_id": tender_id, "bidder_id": bidder_id}
        )
        eval_id = str(stored["_id"]) if stored else bidder_id

        # Audit log
        await AuditService.log_action(
            action="EVALUATE",
            entity_type="evaluation",
            entity_id=eval_id,
            input_data={
                "tender_id": tender_id,
                "bidder_id": bidder_id,
                "criteria_count": len(criteria),
                "extracted_data": {
                    k: v for k, v in extracted_data.items()
                    if k != "raw_text"
                }
            },
            output_data={
                "final_status": final["final_status"],
                "overall_confidence": final["overall_confidence"],
                "ambiguous_count": final["ambiguous_count"]
            }
        )

        evaluations.append({
            "id": eval_id,
            "bidder_id": bidder_id,
            "bidder_name": bidder.get("name", ""),
            "final_status": final["final_status"],
            "overall_confidence": final["overall_confidence"],
            "ambiguous_count": final["ambiguous_count"],
            "results": criterion_results
        })

    return {
        "tender_id": tender_id,
        "tender_title": tender.get("title", ""),
        "evaluated_count": len(evaluations),
        "evaluations": evaluations
    }


@router.get("/{tender_id}")
async def get_evaluations(tender_id: str):
    """Get all evaluations for a tender."""
    eval_col = Database.get_collection("evaluations")
    
    cursor = eval_col.find({"tender_id": tender_id}).sort("evaluated_at", -1)
    evaluations = []
    async for doc in cursor:
        evaluations.append({
            "id": str(doc["_id"]),
            "tender_id": doc.get("tender_id", ""),
            "bidder_id": doc.get("bidder_id", ""),
            "bidder_name": doc.get("bidder_name", ""),
            "results": doc.get("results", []),
            "final_status": doc.get("final_status", "Pending"),
            "overall_confidence": doc.get("overall_confidence", 0),
            "ambiguous_count": doc.get("ambiguous_count", 0),
            "evaluated_at": doc.get("evaluated_at", "").isoformat() if doc.get("evaluated_at") else "",
        })

    # Get tender title
    tender_col = Database.get_collection("tenders")
    try:
        tender = await tender_col.find_one({"_id": ObjectId(tender_id)})
        tender_title = tender.get("title", "") if tender else ""
    except Exception:
        tender_title = ""

    return {
        "evaluations": evaluations,
        "total": len(evaluations),
        "tender_title": tender_title
    }


@router.get("/{tender_id}/{bidder_id}")
async def get_evaluation_detail(tender_id: str, bidder_id: str):
    """Get specific evaluation for a tender-bidder pair."""
    eval_col = Database.get_collection("evaluations")
    
    doc = await eval_col.find_one({
        "tender_id": tender_id,
        "bidder_id": bidder_id
    })

    if not doc:
        raise HTTPException(404, "Evaluation not found")

    return {
        "id": str(doc["_id"]),
        "tender_id": doc.get("tender_id", ""),
        "bidder_id": doc.get("bidder_id", ""),
        "bidder_name": doc.get("bidder_name", ""),
        "results": doc.get("results", []),
        "final_status": doc.get("final_status", "Pending"),
        "overall_confidence": doc.get("overall_confidence", 0),
        "ambiguous_count": doc.get("ambiguous_count", 0),
        "evaluated_at": doc.get("evaluated_at", "").isoformat() if doc.get("evaluated_at") else "",
    }


@router.get("/{tender_id}/export/csv")
async def export_evaluation_csv(tender_id: str):
    """Export evaluation results as CSV."""
    eval_col = Database.get_collection("evaluations")
    
    evaluations = []
    async for doc in eval_col.find({"tender_id": tender_id}):
        evaluations.append(doc)

    if not evaluations:
        raise HTTPException(404, "No evaluations found")

    # Build CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        "Bidder Name", "Criterion", "Type", "Threshold",
        "Extracted Value", "Decision", "Confidence",
        "Explanation", "Source Document", "Final Status"
    ])

    for ev in evaluations:
        for result in ev.get("results", []):
            writer.writerow([
                ev.get("bidder_name", ""),
                result.get("criterion_description", ""),
                result.get("criterion_type", ""),
                result.get("threshold", ""),
                result.get("extracted_value", ""),
                result.get("decision", ""),
                f"{result.get('confidence', 0):.0%}",
                result.get("explanation", ""),
                result.get("source_document", ""),
                ev.get("final_status", "")
            ])

    # Audit log
    await AuditService.log_action(
        action="EXPORT",
        entity_type="evaluation",
        entity_id=tender_id,
        details={"format": "csv", "count": len(evaluations)}
    )

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=evaluation_{tender_id}.csv"}
    )


@router.get("/{tender_id}/export/json")
async def export_evaluation_json(tender_id: str):
    """Export evaluation results as JSON."""
    eval_col = Database.get_collection("evaluations")

    evaluations = []
    async for doc in eval_col.find({"tender_id": tender_id}):
        doc["_id"] = str(doc["_id"])
        if doc.get("evaluated_at"):
            doc["evaluated_at"] = doc["evaluated_at"].isoformat()
        evaluations.append(doc)

    if not evaluations:
        raise HTTPException(404, "No evaluations found")

    await AuditService.log_action(
        action="EXPORT",
        entity_type="evaluation",
        entity_id=tender_id,
        details={"format": "json", "count": len(evaluations)}
    )

    content = json.dumps({"evaluations": evaluations}, indent=2, default=str)
    return StreamingResponse(
        iter([content]),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=evaluation_{tender_id}.json"}
    )

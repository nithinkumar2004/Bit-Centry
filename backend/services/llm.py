"""
LLM Service — OpenRouter API integration for criteria extraction and explanations.
Includes response caching via MongoDB to reduce API usage.
"""
import os
import json
import hashlib
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

import httpx
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "google/gemini-2.0-flash-001")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

MAX_RETRIES = 3


class LLMService:
    """Service for LLM-powered text analysis via OpenRouter."""

    @staticmethod
    def _hash_prompt(prompt: str) -> str:
        """Create SHA-256 hash of prompt for caching."""
        return hashlib.sha256(prompt.encode()).hexdigest()

    @staticmethod
    async def _get_cached_response(prompt_hash: str) -> Optional[str]:
        """Check MongoDB cache for a previous response."""
        try:
            from backend.db.mongodb import Database
            cache = Database.get_collection("llm_cache")
            if cache is not None:
                entry = await cache.find_one({"prompt_hash": prompt_hash})
                if entry:
                    logger.info(f"🎯 Cache hit for prompt hash: {prompt_hash[:12]}...")
                    return entry.get("response")
        except Exception as e:
            logger.debug(f"Cache lookup failed: {e}")
        return None

    @staticmethod
    async def _set_cached_response(prompt_hash: str, response: str):
        """Store LLM response in MongoDB cache."""
        try:
            from backend.db.mongodb import Database
            cache = Database.get_collection("llm_cache")
            if cache is not None:
                await cache.update_one(
                    {"prompt_hash": prompt_hash},
                    {"$set": {
                        "prompt_hash": prompt_hash,
                        "response": response,
                        "cached_at": datetime.utcnow()
                    }},
                    upsert=True
                )
        except Exception as e:
            logger.debug(f"Cache store failed: {e}")

    @staticmethod
    async def _call_openrouter(messages: list, temperature: float = 0.2) -> Optional[str]:
        """Make API call to OpenRouter with retry logic."""
        if not OPENROUTER_API_KEY or OPENROUTER_API_KEY == "your_openrouter_api_key_here":
            logger.warning("⚠️ OpenRouter API key not configured — using mock response")
            return None

        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:5173",
            "X-Title": "BidSentry"
        }

        payload = {
            "model": LLM_MODEL,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 4096,
            "response_format": {"type": "json_object"}
        }

        for attempt in range(MAX_RETRIES):
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(
                        OPENROUTER_URL,
                        headers=headers,
                        json=payload
                    )
                    response.raise_for_status()
                    data = response.json()

                    if "choices" in data and len(data["choices"]) > 0:
                        content = data["choices"][0].get("message", {}).get("content", "")
                        return content

                    logger.warning(f"Unexpected response format: {data}")
                    return None

            except httpx.HTTPStatusError as e:
                logger.error(f"OpenRouter HTTP error (attempt {attempt + 1}): {e.response.status_code}")
                if attempt < MAX_RETRIES - 1:
                    import asyncio
                    await asyncio.sleep(2 ** attempt)
            except Exception as e:
                logger.error(f"OpenRouter error (attempt {attempt + 1}): {e}")
                if attempt < MAX_RETRIES - 1:
                    import asyncio
                    await asyncio.sleep(2 ** attempt)

        return None

    @staticmethod
    async def extract_criteria(raw_text: str) -> List[Dict[str, Any]]:
        """
        Extract eligibility criteria from tender document text using LLM.
        
        Returns list of criterion dicts with: id, type, description, mandatory, threshold, unit
        """
        prompt = f"""You are a tender document analysis expert. Extract all eligibility criteria from the following tender document text.

For each criterion, identify:
- A unique ID (C1, C2, C3, etc.)
- Type: "financial" (turnover, revenue, net worth), "technical" (experience, project count, staff), or "compliance" (certifications, registrations like GST, ISO, PAN)
- Description: Clear human-readable description
- Mandatory: true/false
- Threshold: numeric value if applicable (null otherwise)
- Unit: measurement unit if applicable (e.g., "crore", "lakh", "count", "years")

IMPORTANT: Return ONLY valid JSON in this exact format:
{{
  "criteria": [
    {{
      "id": "C1",
      "type": "financial",
      "description": "Minimum annual turnover of 5 crore",
      "mandatory": true,
      "threshold": 5,
      "unit": "crore"
    }}
  ]
}}

TENDER DOCUMENT TEXT:
{raw_text[:8000]}
"""

        prompt_hash = LLMService._hash_prompt(prompt)
        
        # Check cache
        cached = await LLMService._get_cached_response(prompt_hash)
        if cached:
            try:
                data = json.loads(cached)
                return data.get("criteria", [])
            except json.JSONDecodeError:
                pass

        # Call LLM
        messages = [
            {"role": "system", "content": "You are a precise document analysis AI. Always respond with valid JSON only."},
            {"role": "user", "content": prompt}
        ]

        response = await LLMService._call_openrouter(messages)

        if response:
            # Cache the response
            await LLMService._set_cached_response(prompt_hash, response)
            
            try:
                data = json.loads(response)
                return data.get("criteria", [])
            except json.JSONDecodeError:
                # Try to extract JSON from response
                import re
                json_match = re.search(r'\{[\s\S]*\}', response)
                if json_match:
                    try:
                        data = json.loads(json_match.group())
                        return data.get("criteria", [])
                    except json.JSONDecodeError:
                        pass
                logger.error(f"Failed to parse LLM response as JSON")

        # Return mock criteria if API is not configured
        logger.info("Using mock criteria (API not available)")
        return [
            {
                "id": "C1",
                "type": "financial",
                "description": "Minimum annual turnover of 5 crore",
                "mandatory": True,
                "threshold": 5.0,
                "unit": "crore"
            },
            {
                "id": "C2",
                "type": "compliance",
                "description": "Valid GST registration required",
                "mandatory": True,
                "threshold": None,
                "unit": None
            },
            {
                "id": "C3",
                "type": "compliance",
                "description": "ISO 9001 certification required",
                "mandatory": True,
                "threshold": None,
                "unit": None
            },
            {
                "id": "C4",
                "type": "technical",
                "description": "Minimum 3 completed similar projects",
                "mandatory": True,
                "threshold": 3,
                "unit": "count"
            }
        ]

    @staticmethod
    async def generate_explanation(
        criterion_description: str,
        extracted_value: str,
        decision: str,
        context: str = ""
    ) -> str:
        """
        Generate human-readable explanation for an evaluation decision.
        """
        prompt = f"""Generate a brief, professional explanation for this tender evaluation decision.

Criterion: {criterion_description}
Extracted Value: {extracted_value}
Decision: {decision}
Context: {context}

Return JSON: {{"explanation": "your explanation here"}}
"""
        prompt_hash = LLMService._hash_prompt(prompt)
        cached = await LLMService._get_cached_response(prompt_hash)
        if cached:
            try:
                return json.loads(cached).get("explanation", cached)
            except json.JSONDecodeError:
                return cached

        messages = [
            {"role": "system", "content": "You are a professional tender evaluation analyst. Be concise and factual."},
            {"role": "user", "content": prompt}
        ]

        response = await LLMService._call_openrouter(messages, temperature=0.3)

        if response:
            await LLMService._set_cached_response(prompt_hash, response)
            try:
                return json.loads(response).get("explanation", response)
            except json.JSONDecodeError:
                return response

        # Template-based fallback
        if decision == "Eligible":
            return f"The bidder meets the requirement: {criterion_description}. Extracted value: {extracted_value}."
        elif decision == "Not Eligible":
            return f"The bidder does NOT meet the requirement: {criterion_description}. Extracted value: {extracted_value}."
        else:
            return f"Ambiguous result for: {criterion_description}. Extracted value: {extracted_value}. Manual review recommended."

"""
Data extraction utilities — regex-based extraction of financial, compliance, and technical data.
"""
import re
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


def extract_turnover(text: str) -> Optional[float]:
    """
    Extract turnover/revenue value from text.
    Handles formats: ₹5 crore, 5 Cr, Rs. 50 lakh, INR 5,00,00,000, etc.
    
    Returns:
        Turnover in crores, or None if not found
    """
    if not text:
        return None

    text_lower = text.lower()
    
    # Pattern: X crore(s)
    patterns_crore = [
        r'(?:turnover|revenue|annual\s+turnover|avg\.?\s*annual\s*turnover)[^\d]*?(?:rs\.?|₹|inr)?\s*([\d,]+\.?\d*)\s*(?:cr(?:ore)?s?)',
        r'(?:rs\.?|₹|inr)\s*([\d,]+\.?\d*)\s*(?:cr(?:ore)?s?)',
        r'([\d,]+\.?\d*)\s*(?:cr(?:ore)?s?)',
    ]

    for pattern in patterns_crore:
        match = re.search(pattern, text_lower)
        if match:
            try:
                value = float(match.group(1).replace(",", ""))
                if 0.01 <= value <= 100000:  # sanity check
                    return value
            except ValueError:
                continue

    # Pattern: X lakh → convert to crore
    patterns_lakh = [
        r'(?:turnover|revenue)[^\d]*?(?:rs\.?|₹|inr)?\s*([\d,]+\.?\d*)\s*(?:lakh|lac|lacs)',
        r'(?:rs\.?|₹|inr)\s*([\d,]+\.?\d*)\s*(?:lakh|lac|lacs)',
    ]

    for pattern in patterns_lakh:
        match = re.search(pattern, text_lower)
        if match:
            try:
                value_lakh = float(match.group(1).replace(",", ""))
                return round(value_lakh / 100, 2)  # Convert lakh to crore
            except ValueError:
                continue

    # Pattern: Large absolute numbers (likely in rupees)
    pattern_abs = r'(?:turnover|revenue)[^\d]*?(?:rs\.?|₹|inr)\s*([\d,]+)'
    match = re.search(pattern_abs, text_lower)
    if match:
        try:
            value = float(match.group(1).replace(",", ""))
            if value > 10000000:  # More than 1 crore in absolute
                return round(value / 10000000, 2)
        except ValueError:
            pass

    return None


def extract_certifications(text: str) -> List[str]:
    """
    Extract certifications and registrations from text.
    Detects: GST, ISO, PAN, MSME, EPF, ESI, TAN, etc.
    
    Returns:
        List of certification types found
    """
    if not text:
        return []

    text_upper = text.upper()
    certs = []
    
    cert_patterns = {
        "GST": [r'GST\s*(?:IN|NO|NUMBER|REG)', r'GSTIN', r'GST\s*REGISTRATION', r'GOODS\s*AND\s*SERVICE\s*TAX'],
        "ISO 9001": [r'ISO\s*9001', r'ISO-9001', r'QUALITY\s*MANAGEMENT\s*SYSTEM'],
        "ISO 14001": [r'ISO\s*14001', r'ISO-14001', r'ENVIRONMENTAL\s*MANAGEMENT'],
        "ISO 45001": [r'ISO\s*45001', r'ISO-45001', r'OCCUPATIONAL\s*HEALTH'],
        "PAN": [r'PAN\s*(?:NO|NUMBER|CARD)', r'PERMANENT\s*ACCOUNT\s*NUMBER'],
        "MSME": [r'MSME', r'UDYAM', r'UDYOG\s*AADHAR', r'MICRO\s*SMALL\s*MEDIUM'],
        "EPF": [r'EPF\s*(?:NO|NUMBER|REG)', r'PROVIDENT\s*FUND\s*REG'],
        "ESI": [r'ESI\s*(?:NO|NUMBER|REG)', r'EMPLOYEE\s*STATE\s*INSURANCE'],
        "TAN": [r'TAN\s*(?:NO|NUMBER)', r'TAX\s*DEDUCTION\s*ACCOUNT'],
    }

    for cert_name, patterns in cert_patterns.items():
        for pattern in patterns:
            if re.search(pattern, text_upper):
                certs.append(cert_name)
                break

    return list(set(certs))


def extract_project_count(text: str) -> Optional[int]:
    """
    Extract number of completed projects from text.
    
    Returns:
        Number of projects, or None if not found
    """
    if not text:
        return None

    text_lower = text.lower()
    
    patterns = [
        r'(\d+)\s*(?:similar\s+)?(?:completed\s+)?projects?\s*(?:completed|executed|done)',
        r'(?:completed|executed|undertaken)\s*(\d+)\s*(?:similar\s+)?projects?',
        r'(?:number\s+of\s+projects?|project\s+count|projects?\s+completed)\s*[:\-]?\s*(\d+)',
        r'(\d+)\s*(?:nos?\.)?\s*(?:similar\s+)?(?:works?|projects?)\s*(?:of\s+similar)',
        r'experience\s+(?:of|in)\s+(\d+)\s*(?:similar\s+)?projects?',
    ]

    for pattern in patterns:
        match = re.search(pattern, text_lower)
        if match:
            try:
                count = int(match.group(1))
                if 1 <= count <= 1000:  # sanity check
                    return count
            except ValueError:
                continue

    return None


def extract_all_data(text: str) -> Dict[str, Any]:
    """
    Run all extractors on the given text and return structured data.
    
    Returns:
        Dict with turnover, certifications, project_count, and any additional data
    """
    return {
        "turnover": extract_turnover(text),
        "certifications": extract_certifications(text),
        "project_count": extract_project_count(text),
    }

"""
OCR Service — Text extraction from PDFs and images using PaddleOCR.
Handles scanned documents, multi-page PDFs, and low-confidence detection.
"""
import os
import logging
from typing import Tuple, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# Lazy imports to avoid loading heavy ML libraries at module level
_ocr_instance = None


def _get_ocr():
    """Lazy-load PaddleOCR instance."""
    global _ocr_instance
    if _ocr_instance is None:
        try:
            from paddleocr import PaddleOCR
            _ocr_instance = PaddleOCR(
                use_angle_cls=True,
                lang='en',
                show_log=False,
                use_gpu=False
            )
            logger.info("✅ PaddleOCR initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize PaddleOCR: {e}")
            _ocr_instance = None
    return _ocr_instance


class OCRService:
    """Service for extracting text from documents using OCR."""

    LOW_CONFIDENCE_THRESHOLD = 0.7

    @staticmethod
    def extract_text_from_image(image_path: str) -> Tuple[str, float]:
        """
        Extract text from an image file using PaddleOCR.
        
        Returns:
            Tuple of (extracted_text, average_confidence)
        """
        ocr = _get_ocr()
        if ocr is None:
            logger.warning("PaddleOCR not available, returning empty text")
            return "", 0.0

        try:
            result = ocr.ocr(image_path, cls=True)
            
            if not result or not result[0]:
                return "", 0.0

            lines = []
            confidences = []

            for page in result:
                if page is None:
                    continue
                for line in page:
                    if line and len(line) >= 2:
                        text = line[1][0]
                        conf = line[1][1]
                        lines.append(text)
                        confidences.append(conf)

            full_text = "\n".join(lines)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

            if avg_confidence < OCRService.LOW_CONFIDENCE_THRESHOLD:
                logger.warning(
                    f"⚠️ Low OCR confidence ({avg_confidence:.2f}) for {image_path}"
                )

            return full_text, avg_confidence

        except Exception as e:
            logger.error(f"OCR error on image {image_path}: {e}")
            return "", 0.0

    @staticmethod
    def extract_text_from_pdf(pdf_path: str) -> Tuple[str, float]:
        """
        Extract text from a PDF file.
        First tries text-based extraction (PyPDF2), falls back to OCR for scanned pages.
        
        Returns:
            Tuple of (extracted_text, average_confidence)
        """
        try:
            from PyPDF2 import PdfReader
        except ImportError:
            logger.error("PyPDF2 not installed")
            return "", 0.0

        try:
            reader = PdfReader(pdf_path)
            all_text = []
            all_confidences = []
            has_text_content = False

            for page_num, page in enumerate(reader.pages):
                # Try extracting embedded text first
                text = page.extract_text()
                
                if text and text.strip() and len(text.strip()) > 50:
                    # Page has embedded text — high confidence
                    all_text.append(text.strip())
                    all_confidences.append(0.95)
                    has_text_content = True
                else:
                    # Scanned page — need OCR
                    logger.info(f"Page {page_num + 1}: No embedded text, attempting OCR...")
                    # For scanned PDFs, we'll try OCR on the whole file
                    # PaddleOCR can handle PDFs directly
                    pass

            if has_text_content and all_text:
                full_text = "\n\n".join(all_text)
                avg_conf = sum(all_confidences) / len(all_confidences)
                return full_text, avg_conf

            # Fallback: Use PaddleOCR directly on the PDF
            logger.info(f"Using PaddleOCR for scanned PDF: {pdf_path}")
            ocr = _get_ocr()
            if ocr is None:
                return "", 0.0

            result = ocr.ocr(pdf_path, cls=True)
            
            if not result:
                return "", 0.0

            lines = []
            confidences = []
            for page in result:
                if page is None:
                    continue
                for line in page:
                    if line and len(line) >= 2:
                        lines.append(line[1][0])
                        confidences.append(line[1][1])

            full_text = "\n".join(lines)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            return full_text, avg_confidence

        except Exception as e:
            logger.error(f"PDF extraction error for {pdf_path}: {e}")
            return "", 0.0

    @staticmethod
    def extract_text(file_path: str) -> Tuple[str, float]:
        """
        Auto-detect file type and extract text accordingly.
        
        Returns:
            Tuple of (extracted_text, average_confidence)
        """
        ext = Path(file_path).suffix.lower()
        
        if ext == ".pdf":
            return OCRService.extract_text_from_pdf(file_path)
        elif ext in (".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp"):
            return OCRService.extract_text_from_image(file_path)
        else:
            logger.warning(f"Unsupported file type: {ext}")
            return "", 0.0

    @staticmethod
    def is_low_confidence(confidence: float) -> bool:
        """Check if OCR confidence is below the threshold."""
        return confidence < OCRService.LOW_CONFIDENCE_THRESHOLD

"""Document Parser - PDF and Image extraction"""

import os
from typing import Dict, Any, Optional
from io import BytesIO
from PyPDF2 import PdfReader
from PIL import Image
import google.generativeai as genai

from .llm_client import LLMClient


class DocumentParser:
    """Parse PDFs and images to extract structured data."""
    
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client
    
    def parse_pdf(self, file_content: bytes) -> str:
        """Extract text from PDF."""
        try:
            pdf_reader = PdfReader(BytesIO(file_content))
            text_parts = []
            
            for page in pdf_reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
            
            return "\n\n".join(text_parts)
        except Exception as e:
            return f"PDF parsing error: {str(e)}"
    
    def parse_image(self, file_content: bytes, mime_type: str = "image/jpeg") -> str:
        """Extract text from image using Gemini Vision."""
        try:
            image = Image.open(BytesIO(file_content))
            
            model = genai.GenerativeModel("gemini-2.5-flash")
            response = model.generate_content([
                "Extract all text from this document image. Return the raw text only.",
                image
            ])
            
            return response.text
        except Exception as e:
            return f"Image parsing error: {str(e)}"
    
    def extract_claim_fields(self, text: str) -> Dict[str, Any]:
        """Extract structured claim fields from document text."""
        schema = {
            "claim_type": "health/motor/life/travel",
            "date_of_incident": "YYYY-MM-DD or description",
            "amount_claimed": "numeric value",
            "description": "brief description of incident",
            "policy_number": "policy number if found",
            "claimant_name": "name of person filing claim",
            "supporting_documents": "list of documents mentioned"
        }
        
        return self.llm.extract_structured(text, schema)
    
    def parse(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Parse document and extract fields."""
        ext = os.path.splitext(filename)[1].lower()
        
        # Extract raw text
        if ext == ".pdf":
            raw_text = self.parse_pdf(file_content)
        elif ext in [".jpg", ".jpeg", ".png", ".webp"]:
            mime_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}
            raw_text = self.parse_image(file_content, mime_map.get(ext, "image/jpeg"))
        else:
            return {"error": f"Unsupported file type: {ext}"}
        
        if raw_text.startswith(("PDF parsing error", "Image parsing error")):
            return {"error": raw_text}
        
        # Extract structured fields
        fields = self.extract_claim_fields(raw_text)
        
        return {
            "filename": filename,
            "raw_text": raw_text[:2000],  # Truncate for storage
            "extracted_fields": fields,
            "status": "parsed"
        }

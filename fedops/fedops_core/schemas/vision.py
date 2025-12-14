from pydantic import BaseModel, Field
from typing import List, Optional, Dict

class OCRExtraction(BaseModel):
    """Output from Vision model (Claude Vision or Qwen)"""
    extracted_text: str = Field(..., description="All readable text from image/scan")
    detected_language: str = Field("en", description="Detected language (en, es, fr, etc.)")
    ocr_confidence: float = Field(0.90, ge=0.0, le=1.0, description="Text recognition confidence")
    document_type_detected: str = Field(..., description="Type of document identified (form, contract, table, etc.)")
    
    # Structured data (if form)
    form_fields: Optional[Dict[str, str]] = Field(None, description="Form field names and values")
    
    # Issues detected
    illegible_sections: List[str] = Field(default_factory=list, description="Areas too blurry/faded to read")
    signatures_detected: List[str] = Field(default_factory=list, description="Signature locations/names")
    handwritten_content: bool = Field(False, description="Contains handwritten text?")
    
    # For government forms
    form_number: Optional[str] = Field(None, description="Form ID if applicable (SF-86, etc.)")
    required_fields_missing: List[str] = Field(default_factory=list, description="Unfilled required fields")
    
    # Image quality
    image_quality: str = Field(..., description="Quality assessment: Poor, Fair, Good, Excellent")
    recommendations: List[str] = Field(default_factory=list, description="Improvement recommendations")

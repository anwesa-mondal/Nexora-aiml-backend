# raw_test_api.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import os
import json
from raw_test import RawMaterialProcurementAnalyzer  # Make sure raw_test.py is in the same folder
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# FastAPI app
app = FastAPI(title="Raw Material Procurement API")

# Pydantic model for request body
class MaterialRequest(BaseModel):
    material_name: str
    category: str
    specifications: Dict[str, Any]
    budget_range: Dict[str, Any]
    timeline: Dict[str, Any]
    preferred_location: str
    business_type: str
    order_frequency: str
    payment_preference: str

# Root endpoint
@app.get("/")
def read_root():
    return {"message": "Raw Material Procurement API is running"}

# Analyze material endpoint
@app.post("/analyze")
def analyze_material(request: MaterialRequest):
    if not GROQ_API_KEY:
        raise HTTPException(status_code=500, detail="Groq API key not configured")
    
    analyzer = RawMaterialProcurementAnalyzer(GROQ_API_KEY)
    result = analyzer.analyze_material_procurement(request.dict())
    return result

# Optional: health check endpoint
@app.get("/health")
def health_check():
    return {"status": "ok", "timestamp": json.dumps(str(os.times()))}

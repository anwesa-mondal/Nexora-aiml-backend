from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, Any
from dotenv import load_dotenv
import os
import json

# Import the main function from raw_test.py
from raw_test import main as procurement_main

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

# Allow CORS for all origins (you can restrict in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Request Models ----------

class Specifications(BaseModel):
    grade: str
    quantity_required: str

class BudgetRange(BaseModel):
    min_price: float
    max_price: float
    currency: str
    unit: str

class Timeline(BaseModel):
    required_by: str
    flexibility: str

class MaterialData(BaseModel):
    material_name: str
    category: str
    specifications: Dict[str, Any]
    budget_range: Dict[str, Any]
    timeline: Dict[str, Any]
    preferred_location: str
    business_type: str
    order_frequency: str
    payment_preference: str

# ---------- Response Models ----------

class SupplierDetails(BaseModel):
    company_name: str
    location: str
    price_range: str
    minimum_order: str
    delivery_time: str
    contact_method: str

class Supplier(BaseModel):
    title: str
    link: str
    snippet: str
    supplier_details: SupplierDetails

class ProcurementResponse(BaseModel):
    material_details: Dict[str, Any]
    analysis_timestamp: str
    discovered_platforms: list[str]
    platform_search_results: Dict[str, list[Supplier]]

# ---------- API Endpoints ----------

@app.post("/analyze-procurement", response_model=ProcurementResponse)
async def analyze_procurement_api(material_data: MaterialData):
    """
    Analyze procurement options for raw materials and fetch suppliers.
    """
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    if not GROQ_API_KEY:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY not set in environment.")

    try:
        result_json = procurement_main(material_data.model_dump(), GROQ_API_KEY)
        result_dict = json.loads(result_json)
        return result_dict
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse procurement response: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Procurement analysis failed: {str(e)}")

@app.get("/")
def root():
    return {
        "message": "Raw Material Procurement Analysis API. Submit material details to get platform & supplier analysis.",
        "endpoints": {
            "analyze_procurement": {
                "path": "/analyze-procurement",
                "method": "POST",
                "description": "Analyze procurement options for raw materials",
                "request": {
                    "material_name": "string",
                    "category": "string",
                    "specifications": "object (e.g. {grade, quantity_required})",
                    "budget_range": "object (min_price, max_price, currency, unit)",
                    "timeline": "object (required_by, flexibility)",
                    "preferred_location": "string",
                    "business_type": "string",
                    "order_frequency": "string",
                    "payment_preference": "string"
                },
                "response": {
                    "material_details": "object",
                    "analysis_timestamp": "string",
                    "discovered_platforms": "list of platforms",
                    "platform_search_results": "dict of platforms -> suppliers"
                }
            }
        }
    }




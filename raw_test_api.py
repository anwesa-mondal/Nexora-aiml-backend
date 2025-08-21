# raw_test_api.py

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict
from dotenv import load_dotenv
import os
import json
from raw_test import main as analyze_raw_material_main  # import main() from raw_test.py

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Raw Material Procurement Analyzer API",
    description="Analyze raw material sourcing and recommend procurement platforms.",
    version="1.0.0"
)

# Enable CORS (open - tighten in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Request & Response Models ----------

class MaterialDetails(BaseModel):
    material_name: str = Field(..., description="Name of the raw material (e.g., 'Cotton Fabric')")
    category: str = Field(..., description="Material category (e.g., 'Textiles')")
    specifications: Dict = Field(default_factory=dict, description="Key specifications like grade, quantity")
    budget_range: Dict = Field(default_factory=dict, description="Budget info with min_price, max_price, currency")
    timeline: Dict = Field(default_factory=dict, description="Required by date and flexibility")
    preferred_location: str = Field(..., description="Preferred sourcing location")
    business_type: str = Field(..., description="Business type (e.g., 'Textile Manufacturing')")
    order_frequency: str = Field(..., description="Frequency of orders (e.g., 'Monthly')")
    payment_preference: str = Field(..., description="Preferred payment terms (e.g., '30 days credit')")

class SupplierInfo(BaseModel):
    title: str
    link: str
    snippet: str
    supplier_details: Dict

class PlatformSearchResults(BaseModel):
    platform_name: str
    suppliers: List[SupplierInfo]

class RawMaterialAnalysisResponse(BaseModel):
    material_details: MaterialDetails
    analysis_timestamp: str
    discovered_platforms: List[str]
    platform_search_results: Dict[str, List[SupplierInfo]]

# ---------- API Routes ----------

@app.get("/")
def root():
    return {
        "message": "Raw Material Procurement Analyzer API is running",
        "endpoints": {
            "analyze_raw_material": {
                "path": "/analyze-raw-material",
                "method": "POST",
                "description": "Analyze raw material sourcing and recommend procurement platforms"
            }
        }
    }

@app.post("/analyze-raw-material", response_model=RawMaterialAnalysisResponse)
async def analyze_raw_material_api(material: MaterialDetails):
    """
    Analyze raw material requirements and recommend the most suitable procurement platforms.
    """
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")

    if not GROQ_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="GROQ_API_KEY must be set in environment."
        )

    try:
        material_dict = material.model_dump()
        result_json = analyze_raw_material_main(material_dict, GROQ_API_KEY)
        result_dict = json.loads(result_json)
        return RawMaterialAnalysisResponse(**result_dict)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse analysis response: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Raw material analysis failed: {str(e)}")


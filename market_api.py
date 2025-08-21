# market_api_v2.py

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List
from dotenv import load_dotenv
import os
import json
from market import main as analyze_product_main  # import main() from market.py

# Load environment variables
load_dotenv()

app = FastAPI(
    title="E-commerce Platform Analyzer API",
    description="Analyze product suitability across Indian e-commerce platforms.",
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

class ProductDetails(BaseModel):
    name: str = Field(..., description="Product name")
    category: str = Field(..., description="Product category")
    price: float = Field(..., ge=0, description="Product price")
    features: List[str] = Field(default_factory=list, description="Key product features")
    target_audience: str = Field(..., description="Intended target audience")
    brand: str = Field(..., description="Brand name")
    description: str = Field(..., description="Short description")

# Flexible models for platform analysis
class PlatformAnalysis(BaseModel):
    name: str
    homepage: str
    rank: int
    score: float
    reasoning: str
    advantages: List[str]
    disadvantages: List[str]
    target_audience_match: str
    category_fit: str
    competition_level: str
    recommended_strategy: str

class OverallRecommendations(BaseModel):
    top_3_platforms: List[str]
    diversification_strategy: str
    pricing_considerations: str
    marketing_focus: str

class AnalysisResponse(BaseModel):
    platforms: List[PlatformAnalysis]
    overall_recommendations: OverallRecommendations

# ---------- API Routes ----------

@app.get("/")
def root():
    return {
        "message": "E-commerce Platform Analyzer API is running",
        "endpoints": {
            "analyze_product": {
                "path": "/analyze-product",
                "method": "POST",
                "description": "Analyze a product and recommend suitable e-commerce platforms"
            }
        }
    }

@app.post("/analyze-product", response_model=AnalysisResponse)
async def analyze_product_api(product: ProductDetails):
    """
    Analyze a product and recommend the most suitable e-commerce platforms.
    """
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")

    if not GROQ_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="GROQ_API_KEY must be set in environment."
        )

    try:
        product_dict = product.model_dump()
        result_json = analyze_product_main(product_dict, GROQ_API_KEY)
        result_dict = json.loads(result_json)
        return AnalysisResponse(**result_dict)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse analysis response: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Product analysis failed: {str(e)}")

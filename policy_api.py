from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Union
import json
import os
from dotenv import load_dotenv
from policy_generator import main as generate_policies_main

# Load environment variables
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

app = FastAPI(title="Policy Generator API")

# Allow CORS (you can restrict origins in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Input Models for API ----------

class BusinessDetails(BaseModel):
    business_name: str
    business_type: str
    industry: str
    location_country: str
    location_state: str | None = None
    location_city: str | None = None
    website_url: str | None = None
    has_online_presence: bool = False
    has_physical_store: bool = False
    collects_personal_data: bool = True
    processes_payments: bool = False
    uses_cookies: bool = False
    has_newsletter: bool = False
    target_audience: str = "B2C"
    data_retention_period: int = 365

class PolicyGenerateRequest(BaseModel):
    business_details: BusinessDetails
    policy_types: List[str]
    language: str = "en"
    strict_compliance: bool = True

# ---------- API Endpoint ----------

@app.post("/generate-policies")
async def generate_policies_api(request: PolicyGenerateRequest):
    """
    Generate legal policies (privacy, terms, refund, cookie, etc.)
    based on business details and compliance requirements.
    """
    if not GROQ_API_KEY:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY not set in environment.")

    try:
        print("Starting policy generation...")
        result_json = generate_policies_main(request.dict(), GROQ_API_KEY)
        print(f"Policy generation result: {result_json}")

        # Parse back into dict for FastAPI response
        result_dict = json.loads(result_json)
        return JSONResponse(content=result_dict)

    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse policy response: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Policy generation failed: {str(e)}")

@app.get("/")
def root():
    return {
        "message": "Policy Generator API. Submit business details to generate legal policies.",
        "endpoints": {
            "generate_policies": {
                "path": "/generate-policies",
                "method": "POST",
                "description": "Generate privacy policy, terms, refund, cookie policy etc.",
                "request_example": {
                    "business_details": {
                        "business_name": "TechNova Solutions",
                        "business_type": "saas",
                        "industry": "Software",
                        "location_country": "India",
                        "location_state": "Delhi",
                        "location_city": "New Delhi",
                        "website_url": "https://technova.example",
                        "has_online_presence": True,
                        "processes_payments": True,
                        "uses_cookies": True,
                        "has_newsletter": True,
                        "target_audience": "B2B",
                        "data_retention_period": 730
                    },
                    "policy_types": ["privacy_policy", "terms_conditions", "refund_policy", "cookie_policy"],
                    "language": "en",
                    "strict_compliance": True
                },
                "response": {
                    "generated_policies": {
                        "privacy_policy": {"policy_type": "privacy_policy", "content": "string"},
                        "terms_conditions": {"policy_type": "terms_conditions", "content": "string"}
                    },
                    "timestamp": "string",
                    "api_model": "string"
                }
            }
        }
    }

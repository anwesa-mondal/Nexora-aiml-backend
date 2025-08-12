from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import shutil
import os
import json
import asyncio
from typing import List, Dict, Optional
from invoice_2 import main as extract_invoice_main
from dotenv import load_dotenv

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

class LineItem(BaseModel):
    description: str
    amount: float

class InvoiceDetails(BaseModel):
    invoice_number: str
    client: str
    date: str
    payment_terms: str
    industry: str
    total_amount: float
    currency: str
    line_items: List[LineItem]
    tax_amount: Optional[float] = None
    extra_charges: Optional[float] = None

class InvoiceResponse(BaseModel):
    invoice_details: InvoiceDetails
    total_line_items: int

async def process_single_invoice(image: UploadFile, groq_api_key: str) -> dict:
    """Process a single invoice image."""
    if not image.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
        raise HTTPException(status_code=400, detail=f"File {image.filename} must be a PNG or JPG image")

    temp_image_path = f"temp_{image.filename}"
    try:
        with open(temp_image_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)

        print("Extracting invoice...")
        result_json = extract_invoice_main(temp_image_path, groq_api_key)
        print(f"Processed {image.filename}: {result_json}")
        return json.loads(result_json)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process {image.filename}: {str(e)}")
    finally:
        if os.path.exists(temp_image_path):
            os.remove(temp_image_path)

@app.post("/extract-invoice", response_model=InvoiceResponse)
async def extract_invoice(image: UploadFile = File(...)):
    """Extract invoice details from an invoice image."""
    if not image:
        raise HTTPException(status_code=400, detail="No images provided")

    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    if not GROQ_API_KEY:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY not set in environment.")

    try:
        print("Starting extraction...")
        extraction = await process_single_invoice(image, GROQ_API_KEY)
        print(f"Extraction result: {extraction}")
        return InvoiceResponse(**extraction)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Invoice extraction failed: {str(e)}")

@app.get("/")
def root():
    return {
        "message": "Invoice Extractor API. Upload an invoice image to extract structured details.",
        "endpoints": {
            "extract_invoice": {
                "path": "/extract-invoice",
                "method": "POST",
                "description": "Upload an invoice image to get structured invoice details",
                "request": {
                    "image": "file (image)"
                },
                "response": {
                    "invoice_details": {
                        "invoice_number": "string",
                        "client": "string",
                        "date": "string",
                        "payment_terms": "string",
                        "industry": "string",
                        "total_amount": "number",
                        "currency": "string",
                        "line_items": [
                            {
                                "description": "string",
                                "amount": "number"
                            }
                        ],
                        "tax_amount": "number (optional)",
                        "extra_charges": "number (optional)"
                    },
                    "total_line_items": "integer"
                }
            }
        }
    }

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from invoice_api_2 import app as invoice_app
from credit_score_api import app as credit_score_app
import uvicorn

main_app = FastAPI(title="Invoice Analysis & Credit Score API")

# Enable CORS
main_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Mount the invoice API under /invoice
main_app.mount("/invoice", invoice_app)

# Mount the credit score API under /credit-score
main_app.mount("/credit-score", credit_score_app)

@main_app.get("/")
def root():
    return {
        "message": "Invoice Analysis & Credit Score API",
        "version": "1.0",
        "services": {
            "invoice_extraction": {
                "description": "Extract detailed invoice information from a single invoice image",
                "endpoint": "/invoice/extract-invoice",
                "method": "POST",
                "input": {
                    "image": "Single invoice image file"
                },
                "response": {
                    "invoice_details": {
                        "invoice_number": "string",
                        "client": "string",
                        "date": "string",
                        "payment_terms": "string",
                        "industry": "string",
                        "total_amount": "float",
                        "currency": "string",
                        "line_items": [
                            {"description": "string", "amount": "float"}
                        ],
                        "tax_amount": "float (optional)",
                        "extra_charges": "float (optional)",
                        "pending_amount": "float (optional)",
                        "small_analysis": "string (optional)"
                    },
                    "total_line_items": "integer"
                },
                "features": [
                    "Detailed invoice field extraction",
                    "Single invoice processing",
                    "Tax/extra charges calculation",
                    "Structured line items",
                    "Invoice analysis"
                ]
            },
            "credit_score_analysis": {
                "description": "Calculate weighted credit score based on financial metrics",
                "endpoint": "/credit-score/calculate-credit-score",
                "method": "POST",
                "input": {
                    "no_of_invoices": "integer (>= 1)",
                    "total_amount": "number (>= 0)",
                    "total_amount_pending": "number (>= 0)", 
                    "total_amount_paid": "number (>= 0)",
                    "tax": "number (>= 0)",
                    "extra_charges": "number (>= 0)",
                    "payment_completion_rate": "number (0-1)",
                    "paid_to_pending_ratio": "number (>= 0)"
                },
                "response": {
                    "credit_score_analysis": {
                        "final_weighted_credit_score": "number (0-100)",
                        "score_category": "string (Excellent/Good/Fair/Poor)",
                        "factor_breakdown": "object with weighted scores",
                        "detailed_analysis": "object with strengths, weaknesses, risk assessment",
                        "recommendations": "object with actionable insights"
                    },
                    "timestamp": "string",
                    "api_model": "string"
                },
                "features": [
                    "Weighted credit scoring (0-100)",
                    "Payment completion rate analysis (40% weight)",
                    "Paid-to-pending ratio evaluation (30% weight)", 
                    "Tax compliance assessment (15% weight)",
                    "Extra charges management (15% weight)",
                    "Risk assessment and recommendations",
                    "Detailed factor breakdown",
                    "AI-powered insights"
                ]
            }
        }
    }

if __name__ == "__main__":
    uvicorn.run("server:main_app", host="127.0.0.1", port=8000, reload=True)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from invoice_api_2 import app as invoice_app
from credit_score_api import app as credit_score_app
from market_api import app as ecommerce_app
import uvicorn

main_app = FastAPI(title="Invoice, Credit Score & E-commerce Analyzer API")

# Enable CORS
main_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Mount the individual apps
main_app.mount("/invoice", invoice_app)
main_app.mount("/credit-score", credit_score_app)
main_app.mount("/ecommerce", ecommerce_app)

@main_app.get("/")
def root():
    return {
        "message": "Unified API Gateway",
        "version": "1.0",
        "services": {
            "invoice_extraction": {
                "description": "Extract detailed invoice information from a single invoice image",
                "endpoint": "/invoice/extract-invoice",
                "method": "POST"
            },
            "credit_score_analysis": {
                "description": "Calculate weighted credit score based on financial metrics",
                "endpoint": "/credit-score/calculate-credit-score",
                "method": "POST"
            },
            "ecommerce_platform_analysis": {
                "description": "Analyze product and recommend suitable e-commerce platforms",
                "endpoint": "/ecommerce/analyze-product",
                "method": "POST"
            }
        }
    }

if __name__ == "__main__":
    uvicorn.run("server:main_app", host="127.0.0.1", port=8000, reload=True)



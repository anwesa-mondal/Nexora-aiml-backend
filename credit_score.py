import json
import re
from typing import Dict, Optional
from groq import Groq
from decimal import Decimal
from dotenv import load_dotenv
import os

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")


def calculate_credit_score(financial_data, groq_client):
    """
    Calculate weighted credit score using Groq API
    
    Args:
        financial_data (dict): Financial metrics data
        groq_client: Groq client instance
    
    Returns:
        dict: Credit score analysis with breakdown
    """
    
    prompt = f"""You are a financial credit analysis expert. Based on the provided financial data, calculate a weighted CIBIL-style credit score from 0 to 100.

Use these weightings for calculation:
- Payment Completion Rate: 40% weight (most important)
- Paid-to-Pending Ratio: 30% weight (second most important)
- Tax Compliance: 15% weight (moderate importance)
- Extra Charges Management: 15% weight (moderate importance)

Input Data:
{json.dumps(financial_data, indent=2)}

Scoring Guidelines:
- Payment Completion Rate: 90-100% = Excellent (90-100 points), 70-89% = Good (70-89 points), 50-69% = Fair (50-69 points), <50% = Poor (0-49 points)
- Paid-to-Pending Ratio: >4.0 = Excellent (90-100 points), 2.0-4.0 = Good (70-89 points), 1.0-2.0 = Fair (50-69 points), <1.0 = Poor (0-49 points)
- Tax Compliance: Lower tax percentage of total = Better score
- Extra Charges Management: Lower extra charges percentage = Better score

Return the analysis in this exact JSON structure. Your final response should contain only this json and nothing else, no extra text or anything apart from this json data:
{{
    "final_weighted_credit_score": "number (0-100)",
    "score_category": "string (Excellent/Good/Fair/Poor)",
    "factor_breakdown": {{
        "payment_completion_rate": {{
            "actual_value": "number",
            "individual_score": "number (0-100)",
            "weighted_score": "number",
            "weight_percentage": 40,
            "comment": "string"
        }},
        "paid_to_pending_ratio": {{
            "actual_value": "number",
            "individual_score": "number (0-100)",
            "weighted_score": "number",
            "weight_percentage": 30,
            "comment": "string"
        }},
        "tax_compliance": {{
            "actual_value": "number (tax percentage of total)",
            "individual_score": "number (0-100)",
            "weighted_score": "number",
            "weight_percentage": 15,
            "comment": "string"
        }},
        "extra_charges_management": {{
            "actual_value": "number (extra charges percentage of total)",
            "individual_score": "number (0-100)",
            "weighted_score": "number",
            "weight_percentage": 15,
            "comment": "string"
        }}
    }},
    "detailed_analysis": {{
        "strengths": ["string array of positive aspects"],
        "weaknesses": ["string array of areas needing improvement"],
        "risk_assessment": "string (Low/Medium/High risk)",
        "creditworthiness_summary": ["array of detailed analysis statements"]
    }},
    "recommendations": {{
        "immediate_actions": ["string array"],
        "long_term_improvements": ["string array"],
        "priority_focus_areas": ["string array"]
    }}
}}

Ensure all calculations are mathematically accurate and provide insightful, actionable comments.

For the creditworthiness_summary, provide 2-4 detailed analytical statements as an array, covering:
- Cash flow stability and payment patterns
- Revenue utilization efficiency and pending amount management
- Cost optimization opportunities (tax compliance and extra charges)
- Overall financial health assessment

Example creditworthiness_summary format:
[
  "Cash inflow appears stable enough to cover 80% of monthly invoices, but pending amounts remain significant.",
  "The low paid-to-pending ratio suggests that either payments are being delayed or incoming revenue is not being efficiently used to clear outstanding dues.",
  "Extra charges, while moderate, could be optimized by improving operational efficiency and avoiding late fees or penalties."
]"""
    
    try:
        # Create chat completion
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            temperature=0.1,
            max_tokens=1500
        )
        
        # Extract response content
        response_text = chat_completion.choices[0].message.content

        print(response_text)
        
        # Parse credit score analysis
        credit_analysis = parse_credit_score_response(response_text)
        
        return credit_analysis
        
    except Exception as e:
        print(f"❌ Error calculating credit score with Groq API: {str(e)}")
        return {}


def parse_credit_score_response(text):
    """
    Parse credit score analysis from JSON text or dict.
    Cleans and extracts JSON from messy model outputs.
    """
    
    # Handle empty or invalid responses
    if not text or not str(text).strip():
        return {}

    # If input is already a dict
    if isinstance(text, dict):
        return validate_credit_response(text)
    
    # Try to extract JSON block if it's inside ```json ... ```
    json_match = re.search(r"```json\s*(\{[\s\S]*?\})\s*```", text, re.IGNORECASE)
    if json_match:
        text = json_match.group(1)
    else:
        # Try to find any JSON object in the text
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            text = match.group(0)

    # Remove trailing commas before } or ]
    text = re.sub(r",(\s*[}\]])", r"\1", text)

    # Try parsing cleaned text
    try:
        credit_data = json.loads(text)
        return validate_credit_response(credit_data)
    except Exception as e:
        print(f"❌ JSON parse failed for credit score: {e}")
        return {}


def validate_credit_response(data):
    """
    Validate and structure credit response data with defaults
    """
    if not isinstance(data, dict):
        return {}
    
    # Ensure required structure with defaults
    validated_response = {
        "final_weighted_credit_score": float(data.get("final_weighted_credit_score", 0)),
        "score_category": data.get("score_category", "Unknown"),
        "factor_breakdown": {},
        "detailed_analysis": {
            "strengths": data.get("detailed_analysis", {}).get("strengths", []),
            "weaknesses": data.get("detailed_analysis", {}).get("weaknesses", []),
            "risk_assessment": data.get("detailed_analysis", {}).get("risk_assessment", "Unknown"),
            "creditworthiness_summary": data.get("detailed_analysis", {}).get("creditworthiness_summary", [])
        },
        "recommendations": {
            "immediate_actions": data.get("recommendations", {}).get("immediate_actions", []),
            "long_term_improvements": data.get("recommendations", {}).get("long_term_improvements", []),
            "priority_focus_areas": data.get("recommendations", {}).get("priority_focus_areas", [])
        }
    }
    
    # Validate factor breakdown
    factor_breakdown = data.get("factor_breakdown", {})
    factors = ["payment_completion_rate", "paid_to_pending_ratio", "tax_compliance", "extra_charges_management"]
    
    for factor in factors:
        factor_data = factor_breakdown.get(factor, {})
        validated_response["factor_breakdown"][factor] = {
            "actual_value": float(factor_data.get("actual_value", 0)),
            "individual_score": float(factor_data.get("individual_score", 0)),
            "weighted_score": float(factor_data.get("weighted_score", 0)),
            "weight_percentage": int(factor_data.get("weight_percentage", 0)),
            "comment": factor_data.get("comment", "N/A")
        }
    
    return validated_response


def structure_credit_score_json(credit_analysis):
    """
    Convert structured credit analysis to JSON format
    
    Args:
        credit_analysis (dict): Credit score analysis details

    Returns:
        str: JSON-formatted string
    """
    return json.dumps({
        "credit_score_analysis": credit_analysis,
        "timestamp": "generated",
        "api_model": "meta-llama/llama-4-scout-17b-16e-instruct"
    }, indent=2, ensure_ascii=False)


def main(financial_data, groq_api_key):
    """
    Main function to calculate credit score
    
    Args:
        financial_data (dict): Financial metrics for credit scoring
        groq_api_key (str): Groq API key
        
    Returns:
        str: JSON formatted credit score analysis
    """
    
    # Initialize Groq client
    try:
        groq_client = Groq(api_key=groq_api_key)
    except Exception as e:
        print(f"❌ Error initializing Groq client: {str(e)}")
        return {}
    
    # Calculate credit score
    credit_analysis = calculate_credit_score(financial_data, groq_client)
    formatted_analysis = structure_credit_score_json(credit_analysis)
    
    return formatted_analysis


# Example usage
if __name__ == "__main__":
    # Sample financial data
    sample_data = {
        "no_of_invoices": 6,
        "total_amount": 50000,
        "total_amount_pending": 40000,
        "total_amount_paid": 10000,
        "tax": 5000,
        "extra_charges": 900,
        "payment_completion_rate": 0.2,
        "paid_to_pending_ratio": 0.25
    }
    
    api_key = GROQ_API_KEY
    credit_score_analysis = main(sample_data, api_key)
    print(credit_score_analysis)

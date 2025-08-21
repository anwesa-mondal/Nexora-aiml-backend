#!/usr/bin/env python3
"""
AI-Powered Privacy & Legal Policy Generator for MSMEs
Uses Groq API (LLaMA models) to generate customized legal policies
"""

import json
import re
from typing import Dict, List, Union
from pydantic import BaseModel, Field
from datetime import datetime
from dotenv import load_dotenv
import os
from groq import Groq

# Load API key
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# ---------- Input Models ----------

class BusinessDetails(BaseModel):
    business_name: str = Field(..., min_length=1, max_length=255)
    business_type: str = Field(..., pattern="^(retail|service|manufacturing|e-commerce|saas|consulting|restaurant|healthcare|education|other)$")
    industry: str = Field(..., min_length=1, max_length=100)
    location_country: str = Field(..., min_length=1, max_length=100)
    location_state: str = Field(None, max_length=100)
    location_city: str = Field(None, max_length=100)
    website_url: str = Field(None, max_length=500)
    has_online_presence: bool = False
    has_physical_store: bool = False
    collects_personal_data: bool = True
    processes_payments: bool = False
    uses_cookies: bool = False
    has_newsletter: bool = False
    target_audience: str = Field(default="B2C", pattern="^(B2B|B2C|Both)$")
    data_retention_period: int = Field(default=365, ge=30, le=3650)  # days

class PolicyGenerateRequest(BaseModel):
    business_details: BusinessDetails
    policy_types: list[str] = Field(..., min_items=1)  
    language: str = Field(default="en", pattern="^(en|hi|es|fr)$")
    strict_compliance: bool = True

# ---------- Compliance Detection ----------

def determine_compliance_regions(country: str) -> List[str]:
    regions = []
    if country.lower() in ['india', 'in']:
        regions.extend(['Indian_IT_Act', 'Indian_Consumer_Protection_Act'])
    if country.lower() in [
        'germany','france','italy','spain','netherlands','belgium','austria','poland',
        'czech republic','hungary','romania','bulgaria','croatia','slovakia','slovenia',
        'estonia','latvia','lithuania','luxembourg','malta','cyprus','denmark','sweden',
        'finland','ireland','portugal','greece'
    ]:
        regions.append('GDPR')
    if country.lower() in ['united states','usa','us']:
        regions.extend(['CCPA','COPPA','US_FTC'])
    if country.lower() in ['canada','ca']:
        regions.append('PIPEDA')
    if country.lower() in ['united kingdom','uk','gb']:
        regions.extend(['UK_GDPR','UK_DPA'])
    if country.lower() in ['australia','au']:
        regions.append('Australian_Privacy_Act')
    if not regions:
        regions.append('International_Best_Practices')
    return regions

# ---------- Regex JSON Extractor ----------

def extract_json_block(text: str) -> str:
    """
    Extract the first JSON object from a string using regex.
    Falls back to the raw text if no braces found.
    """
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return match.group(0)
    return text.strip()

# ---------- Groq-powered Policy Generation ----------

SYSTEM_PROMPT = """
You are a legal compliance and policy drafting assistant.
Output ONLY valid JSON.
Do NOT wrap it in markdown code fences (no ```json ... ```).
Do NOT add explanations or text outside the JSON.
The JSON must follow this schema:

{
  "policy_type": "<string, e.g., privacy_policy>",
  "content": "<policy text as a single string, escape newlines with \\n>"
}
"""

def call_groq_for_policy(
    business: BusinessDetails,
    policy_type: str,
    language: str,
    compliance_regions: List[str],
    strict_compliance: bool,
    groq_client,
    max_retries: int = 2
) -> Dict:
    compliance_text = (
        f"Ensure compliance with these frameworks: {', '.join(compliance_regions)}"
        if strict_compliance else
        "Follow international best practices. Mention compliance frameworks only if highly relevant."
    )

    prompt = f"""
Business Details:
{json.dumps(business.model_dump(), indent=2)}

Generate a comprehensive {policy_type.replace("_", " ")} in {language}.
{compliance_text}
"""

    for attempt in range(max_retries + 1):
        try:
            chat_completion = groq_client.chat.completions.create(
                model="meta-llama/llama-4-scout-17b-16e-instruct",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1500,
            )

            response_text = chat_completion.choices[0].message.content.strip()
            if not response_text:
                raise ValueError("Empty response from Groq")

            # 🔹 Extract JSON block with regex
            json_str = extract_json_block(response_text)

            return json.loads(json_str)

        except Exception as e:
            print(f"❌ Error generating {policy_type} (attempt {attempt+1}): {e}")
            if attempt == max_retries:
                return {
                    "policy_type": policy_type,
                    "content": f"⚠️ Failed to generate {policy_type}. Please retry later."
                }

# ---------- Policy Generation Flow ----------

def generate_policies(request: PolicyGenerateRequest) -> Dict:
    groq_client = Groq(api_key=GROQ_API_KEY)

    compliance_regions = determine_compliance_regions(
        request.business_details.location_country
    )

    results = {
        "business": request.business_details.model_dump(),
        "compliance_regions": compliance_regions,
        "strict_compliance": request.strict_compliance,
        "generated_policies": {},
        "timestamp": datetime.now().isoformat(),
        "api_model": "meta-llama/llama-4-scout-17b-16e-instruct"
    }

    for ptype in request.policy_types:
        policy_json = call_groq_for_policy(
            request.business_details,
            ptype,
            request.language,
            compliance_regions,
            request.strict_compliance,
            groq_client
        )
        if policy_json:
            results["generated_policies"][ptype] = policy_json

    return results



def main(request: Union[PolicyGenerateRequest, dict], groq_api_key: str) -> str:
    """
    Main function to generate policies with Groq.
    Accepts either a dict or a PolicyGenerateRequest.
    Returns a JSON-dumped string (structured).
    """
    if isinstance(request, dict):
        request = PolicyGenerateRequest(**request)

    raw_result = generate_policies(request)
    structured = {
        "generated_policies": raw_result.get("generated_policies", {}),
        "timestamp": raw_result.get("timestamp", datetime.now().isoformat()),
        "api_model": raw_result.get("api_model", "meta-llama/llama-4-scout-17b-16e-instruct")
    }

    # 🔹 Structure = return pretty JSON
    return json.dumps(structured, indent=2, ensure_ascii=False)


# ---------- Example Run ----------

if __name__ == "__main__":
    sample_request = {
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
        "policy_types": ["privacy_policy", "terms_conditions", "refund_policy", "cookie_policy","employee_policy"],
        "language": "en",
        "strict_compliance": True
    }

    api_key = GROQ_API_KEY
    output = main(sample_request, api_key)
    print(output)

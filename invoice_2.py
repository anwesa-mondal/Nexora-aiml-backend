import json
import base64
import re
from typing import List, Dict, Optional
from groq import Groq
from decimal import Decimal
from dotenv import load_dotenv
import os

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")


# In[12]:


def encode_image_to_base64(image_path):
    """
    Encode image to base64 for API transmission
    
    Args:
        image_path (str): Path to prescription image
        
    Returns:
        str: Base64 encoded image
    """
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        print(f"Error encoding image: {str(e)}")
        return None

def extract_invoice_details(image_path, groq_client):
    """
    Extract dosage and instructions from prescription
    
    Args:
        image_path (str): Path to prescription image
        groq_client: Groq client instance
    
    Returns:
        dict: Medicine dosage details
    """
    
    # Encode image to base64
    base64_image = encode_image_to_base64(image_path)
    if not base64_image:
        return {}
    
    prompt =  """You are an invoice analysis expert. Extract key information from this invoice image and return it in JSON format.
    
    Extract the following information:
    - Invoice number
    - Client/Customer name
    - Date
    - Payment terms
    - Industry (if mentioned)
    - Total amount
    - Currency
    - Line items (brief description and amounts)
    - tax or extra charges if applicable
    - pending amount if applicable
    - small analysis of the invoice

    Return the data in this JSON structure:
    {
        "invoice_number": "string",
        "client": "string",
        "date": "string",
        "payment_terms": "string",
        "industry": "string",
        "total_amount": "number",
        "currency": "string",
        "line_items": [
            {"description": "string", "amount": "number"}
        ] ,
        "tax_amount": "number",  # if applicable
        "extra_charges": "number",  # if applicable
        "pending_amount": "number",  # if applicable
        "small_analysis": "string"  # if applicable
    }
    
    If any field is not clearly visible, use "N/A" or 0.0 for amounts.
t: Parsed invoice data.
    """
    
    try:
        # Create chat completion with image
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            temperature=0.1,
            max_tokens=800
        )
        
        # Extract response content
        response_text = chat_completion.choices[0].message.content
        
        # Parse dosage details
        invoice_details = parse_invoice_information(response_text)
        
        return invoice_details
        
    except Exception as e:
        print(f"❌ Error extracting details with Groq API: {str(e)}")
        return {}


def parse_invoice_information(text):
    """
    Parse invoice information from JSON text or dict.
    Cleans and extracts JSON from messy model outputs.
    """
    invoice_info = {}
    currency_precision = Decimal("0.01")

    # Handle "no invoice" special case (case-insensitive)
    if "no_invoice_found" in str(text).lower():
        return {}

    # If input is already a dict
    if isinstance(text, dict):
        invoice_data = text
    else:
        # Try to extract JSON block if it's inside ```json ... ```
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            text = match.group(0)

        # Remove trailing commas before } or ]
        text = re.sub(r",(\s*[}\]])", r"\1", text)

        # Try parsing cleaned text
        try:
            invoice_data = json.loads(text)
        except Exception as e:
            print(f"❌ JSON parse failed: {e}")
            return {}

    # Ensure we have a dict
    if not isinstance(invoice_data, dict):
        return {}

    # Extract fields with defaults
    invoice_info["invoice_number"] = invoice_data.get("invoice_number", "Unknown")
    invoice_info["client"] = invoice_data.get("client", "Unknown")
    invoice_info["date"] = invoice_data.get("date", "Unknown")
    invoice_info["payment_terms"] = invoice_data.get("payment_terms", "Not specified")
    invoice_info["industry"] = invoice_data.get("industry", "Not specified")
    invoice_info["total_amount"] = Decimal(invoice_data.get("total_amount", 0)).quantize(currency_precision)
    invoice_info["currency"] = invoice_data.get("currency", "Unknown")
    invoice_info["pending_amount"] = Decimal(invoice_data.get("pending_amount", 0)).quantize(currency_precision)
    invoice_info["small_analysis"] = invoice_data.get("small_analysis", "N/A")
    invoice_info["line_items"] = []

    # Process line items
    for item in invoice_data.get("line_items", []):
        description = item.get("description", "").strip()
        amount = Decimal(item.get("amount", 0)).quantize(currency_precision)
        if description:
            invoice_info["line_items"].append({
                "description": description,
                "amount": amount
            })

    # Handle tax and extra charges from API response or calculate if needed
    invoice_info["tax_amount"] = Decimal(invoice_data.get("tax_amount", 0)).quantize(currency_precision)
    invoice_info["extra_charges"] = Decimal(invoice_data.get("extra_charges", 0)).quantize(currency_precision)
    
    # If tax_amount and extra_charges are not provided, try to detect from difference
    if invoice_info["tax_amount"] == 0 and invoice_info["extra_charges"] == 0:
        line_items_total = sum(item.get("amount", Decimal(0)) for item in invoice_info["line_items"])
        difference = (invoice_info["total_amount"] - line_items_total).quantize(currency_precision)

        if difference != Decimal(0):
            text_check = json.dumps(invoice_data).lower()
            if any(word in text_check for word in ["tax", "vat", "gst", "sales tax"]):
                invoice_info["tax_amount"] = difference
            else:
                invoice_info["extra_charges"] = difference

    def convert_decimals(obj):
        if isinstance(obj, list):
            return [convert_decimals(i) for i in obj]
        elif isinstance(obj, dict):
            return {k: convert_decimals(v) for k, v in obj.items()}
        elif isinstance(obj, Decimal):
            return float(obj)
        return obj

    return convert_decimals(invoice_info)



def structure_invoice_json(invoice_info):
    """
    Convert structured invoice info to JSON format.
if
    Args:
        invoice_info (dict): Parsed invoice details

    Returns:
        str: JSON-formatted string
    """
    return json.dumps({
        "invoice_details": invoice_info,
        "total_line_items": len(invoice_info.get("line_items", []))
    }, indent=2, ensure_ascii=False)


def main(image_path, groq_api_key):
    """
    Main function to extract dosage details
    
    Args:
        image_path (str): Path to prescription image
        groq_api_key (str): Groq API key
    """
    
 
    # Initialize Groq client
    try:
        groq_client = Groq(api_key=groq_api_key)
        
    except Exception as e:
        print(f"❌ Error initializing Groq client: {str(e)}")
        return {}
    
    # Extract dosage details
    details = extract_invoice_details(image_path, groq_client)
    details= structure_invoice_json(details)
    return details

# Example usage
if __name__ == "__main__":
 # Set your Groq API key here
    api_key=GROQ_API_KEY
        
    # Process dosage details
    sample_image = r"inv3.jpg"  # Replace with actual image path
    dosage_info = main(sample_image, api_key)
    print(dosage_info)


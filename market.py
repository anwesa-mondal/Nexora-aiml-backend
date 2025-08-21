import json
import re
from typing import Dict, List
from groq import Groq
from datetime import datetime
from dotenv import load_dotenv
import os
import time

# Load API keys
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")


class EcommercePlatformAnalyzer:
    def __init__(self, groq_api_key: str):
        """Initialize the analyzer with API credentials."""
        self.groq_client = Groq(api_key=groq_api_key)

        self.known_platforms = {
            # B2C Platforms
            "Amazon": "https://www.amazon.in",
            "Flipkart": "https://www.flipkart.com",
            "Myntra": "https://www.myntra.com",
            "Ajio": "https://www.ajio.com",
            "Meesho": "https://www.meesho.com",
            "Snapdeal": "https://www.snapdeal.com",
            "Nykaa": "https://www.nykaa.com",
            "BigBasket": "https://www.bigbasket.com",
            "Grofers": "https://blinkit.com",
            "Paytm Mall": "https://paytmmall.com",
            "Shopclues": "https://www.shopclues.com",
            "Tata CLiQ": "https://www.tatacliq.com",
            "JioMart": "https://www.jiomart.com",
            "FirstCry": "https://www.firstcry.com",
            
            # B2B & Hybrid Platforms
            "ONDC Network": "https://ondc.org",
            "IndiaMART": "https://www.indiamart.com",
            "TradeIndia": "https://www.tradeindia.com",
            "Amazon Business": "https://business.amazon.in",
            "Alibaba India": "https://www.alibaba.com/countrysearch/IN",
            "Government e-Marketplace (GeM)": "https://gem.gov.in",
            "Udaan": "https://udaan.com",
            "ExportersIndia": "https://www.exportersindia.com",
            "Global Sources": "https://www.globalsources.com",
            "DHgate": "https://www.dhgate.com"
        }

        # B2B Categories and Keywords
        self.b2b_keywords = [
            'industrial', 'commercial', 'wholesale', 'bulk', 'professional', 'corporate',
            'business', 'office', 'manufacturing', 'equipment', 'machinery', 'tools',
            'safety', 'medical', 'laboratory', 'construction', 'automotive parts',
            'electronic components', 'raw materials', 'packaging materials',
            'chemicals', 'pharmaceuticals', 'textiles', 'metals', 'plastics'
        ]

        self.b2b_target_audiences = [
            'companies', 'manufacturers', 'distributors', 'retailers', 'wholesalers',
            'businesses', 'enterprises', 'industries', 'factories', 'workshops',
            'hospitals', 'clinics', 'laboratories', 'schools', 'offices',
            'construction', 'automotive', 'mining', 'agriculture'
        ]

        # Category-specific platform mapping
        self.category_platforms = {
            # B2B Categories
            "Industrial": ["IndiaMART", "TradeIndia", "Amazon Business", "Government e-Marketplace (GeM)", "ONDC Network"],
            "Safety Equipment": ["IndiaMART", "Government e-Marketplace (GeM)", "Amazon Business", "TradeIndia"],
            "Office Supplies": ["Amazon Business", "IndiaMART", "Udaan", "Government e-Marketplace (GeM)"],
            "Manufacturing": ["IndiaMART", "TradeIndia", "Alibaba India", "ExportersIndia", "ONDC Network"],
            "Construction": ["IndiaMART", "Government e-Marketplace (GeM)", "TradeIndia", "Amazon Business"],
            "Medical Equipment": ["IndiaMART", "Government e-Marketplace (GeM)", "Amazon Business", "TradeIndia"],
            "Electronic Components": ["IndiaMART", "Amazon Business", "TradeIndia", "Alibaba India"],
            "Automotive Parts": ["IndiaMART", "TradeIndia", "Amazon Business", "Alibaba India"],
            "Chemicals": ["IndiaMART", "TradeIndia", "ExportersIndia", "Alibaba India"],
            "Textiles": ["IndiaMART", "TradeIndia", "ExportersIndia", "ONDC Network"],
            "Packaging": ["IndiaMART", "TradeIndia", "Amazon Business", "Alibaba India"],
            
            # B2C Categories
            "Food & Grocery": ["BigBasket", "JioMart", "Grofers", "ONDC Network"],
            "Fashion": ["Myntra", "Ajio", "Amazon", "Flipkart", "Meesho"],
            "Beauty": ["Nykaa", "Amazon", "Flipkart", "Myntra"],
            "Electronics": ["Amazon", "Flipkart", "Tata CLiQ", "Paytm Mall"],
            "Baby & Kids": ["FirstCry", "Amazon", "Flipkart"],
            
            # Local & Artisan
            "Handmade": ["ONDC Network", "Meesho", "Amazon", "IndiaMART"],
            "Local Products": ["ONDC Network", "Meesho", "JioMart"]
        }

    def is_b2b_product(self, product_details: Dict) -> bool:
        """Detect if a product is B2B based on various indicators."""
        product_name = product_details.get('name', '').lower()
        category = product_details.get('category', '').lower()
        description = product_details.get('description', '').lower()
        target_audience = product_details.get('target_audience', '').lower()
        features = ' '.join(product_details.get('features', [])).lower()
        
        # Check for B2B keywords in all fields
        all_text = f"{product_name} {category} {description} {target_audience} {features}"
        
        b2b_score = 0
        
        # Strong B2B indicators
        for keyword in self.b2b_keywords:
            if keyword in all_text:
                b2b_score += 2
        
        # Target audience indicators
        for audience in self.b2b_target_audiences:
            if audience in target_audience:
                b2b_score += 3
        
        # Category-based detection
        b2b_categories = [
            'industrial', 'commercial', 'office', 'manufacturing', 'construction',
            'medical equipment', 'safety', 'laboratory', 'automotive parts',
            'electronic components', 'chemicals', 'machinery', 'tools'
        ]
        
        for b2b_cat in b2b_categories:
            if b2b_cat in category:
                b2b_score += 3
        
        # Price-based indicator (higher prices often indicate B2B)
        price = product_details.get('price', 0)
        if price > 5000:  # Products over ₹5000 might be B2B
            b2b_score += 1
        
        # Return True if B2B score is 3 or higher
        return b2b_score >= 3

    def discover_platforms_with_groq(self, product_details: Dict) -> List[str]:
        """Discover relevant e-commerce platforms using Groq API instead of Google Search."""
        product_name = product_details.get('name', '')
        category = product_details.get('category', '')
        
        # Detect if product is B2B
        is_b2b = self.is_b2b_product(product_details)
        
        # Start with category-specific platforms
        discovered_platforms = set()
        
        # Check if category matches any specific platform categories
        for cat_key, platforms in self.category_platforms.items():
            if cat_key.lower() in category.lower() or any(word in category.lower() for word in cat_key.lower().split()):
                discovered_platforms.update(platforms)

        # Use Groq to get additional platform recommendations
        prompt = f"""You are an e-commerce platform expert for India. Based on the product details below, recommend the most suitable Indian e-commerce platforms.

Product Details:
- Name: {product_name}
- Category: {category}
- Product Type: {"B2B (Business-to-Business)" if is_b2b else "B2C (Business-to-Consumer)"}
- Target Audience: {product_details.get('target_audience', '')}
- Price: ₹{product_details.get('price', 0)}

Available platforms to choose from:
{list(self.known_platforms.keys())}

Consider these factors:
- Product category fit
- Target audience alignment
- Business model (B2B vs B2C)
- Market presence in India
- Commission structure
- Platform specialization

Return ONLY a JSON array of the top 8-10 most suitable platform names from the available list above.
Example format: ["Amazon", "Flipkart", "IndiaMART", "Myntra"]"""

        try:
            chat_completion = self.groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.1-8b-instant",
                temperature=0.3,
                max_tokens=500
            )
            
            response_text = chat_completion.choices[0].message.content
            # Parse JSON response - find array brackets
            start_bracket = response_text.find('[')
            end_bracket = response_text.rfind(']')
            
            if start_bracket != -1 and end_bracket != -1 and end_bracket > start_bracket:
                json_str = response_text[start_bracket:end_bracket + 1]
                try:
                    groq_platforms = json.loads(json_str)
                    discovered_platforms.update([p for p in groq_platforms if p in self.known_platforms])
                except json.JSONDecodeError:
                    print("⚠️ Failed to parse platform recommendations from Groq")
        
        except Exception as e:
            print(f"⚠️ Groq platform discovery failed: {e}")

        # Essential platforms based on product type
        if is_b2b:
            # Always include these B2B platforms
            essential_platforms = ['IndiaMART', 'Amazon Business', 'ONDC Network', 'Government e-Marketplace (GeM)']
        else:
            # Always include these B2C platforms
            essential_platforms = ['Amazon', 'Flipkart', 'ONDC Network']
        
        discovered_platforms.update(essential_platforms)
        
        return list(discovered_platforms)

    def analyze_platform_suitability(self, product_details: Dict, platforms: List[str]) -> Dict:
        """Use Groq API to analyze and rank platforms by suitability."""
        
        # Detect if product is B2B
        is_b2b = self.is_b2b_product(product_details)
        
        prompt = f"""You are an e-commerce platform analysis expert specializing in both B2C and B2B platforms in India.

Product Details:
{json.dumps(product_details, indent=2)}

Available Platforms:
{json.dumps(platforms, indent=2)}

Product Type: {"B2B (Business-to-Business)" if is_b2b else "B2C (Business-to-Consumer)"}

🔍 *B2B Platform Specializations:*
- *IndiaMART*: India's largest B2B marketplace, 2-5% commission, verified suppliers, trade credit facilities
- *Government e-Marketplace (GeM)*: Government procurement platform, transparent pricing, quality assurance, tender opportunities
- *ONDC Network*: Open network supporting both B2B & B2C, 2-3% commission, direct customer relationships, government backing
- *Amazon Business*: B2B marketplace with bulk pricing, business credit lines, GST invoicing
- *TradeIndia*: B2B platform focusing on exports/imports, trade finance, 1-3% commission
- *Alibaba India*: Global B2B sourcing, international suppliers, trade assurance

🔍 *B2C Platform Specializations:*
- *Amazon/Flipkart*: Mass market reach, 8-15% commission, high competition
- *Myntra/Ajio*: Fashion focus, 15-25% commission
- *Nykaa*: Beauty & personal care, 10-20% commission
- *ONDC Network*: Supporting local businesses, 2-3% commission

⚠️ Important Instructions for Calculations:
1. Calculate *GST* as (GST% × Product Price). Show percentage and rupee value.
2. Calculate *Commission* based on platform and product type:
   - IndiaMART: 2-5% commission
   - Government e-Marketplace (GeM): 0-1% commission (government platform)
   - ONDC Network: 2-3% commission
   - Amazon Business: 5-12% commission (lower than B2C)
   - TradeIndia: 1-3% commission
   - Amazon (B2C): 8-15% commission
   - Flipkart: 10-20% commission
3. Include *Shipping Charges* and *Other Fees*.
4. Compute *Final Selling Charge* = (Commission + GST + Shipping + Other Fees).
5. Compute *Profit* = (Selling Price – Final Selling Charge) and *Net Profit Margin %*.

For B2B products, emphasize:
- Bulk order capabilities
- Trade credit facilities
- Quality certifications
- Supplier verification
- Export opportunities

Return JSON only:
{{
    "platform_analysis": {{
        "platform_name": {{
            "rank": "number",
            "score": "number (0-100)",
            "reasoning": "string",
            "advantages": ["list"],
            "disadvantages": ["list"],
            "target_audience_match": "Excellent/Good/Fair/Poor",
            "category_fit": "Excellent/Good/Fair/Poor",
            "competition_level": "Low/Medium/High",
            "business_model": "B2B/B2C/Hybrid",
            "gst_taxes": "string (GST percentage and cost impact)",
            "commission_fees": "string (platform commission and amount)",
            "other_charges": "string (listing, shipping, payment gateway fees)",
            "final_selling_charge": "string (total cost breakdown)",
            "profit_analysis": "string (profit amount and margin percentage)",
            "bulk_order_benefits": "string (for B2B platforms)",
            "verification_standards": "string (quality checks, certifications)",
            "recommended_strategy": "string"
        }}
    }},
    "overall_recommendations": {{
        "top_3_platforms": ["list"],
        "diversification_strategy": "string",
        "pricing_considerations": "string",
        "marketing_focus": "string",
        "b2b_specific_advice": "string (if B2B product)"
    }}
}}"""

        try:
            chat_completion = self.groq_client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert e-commerce analyst. Always respond with valid JSON only, no additional text or explanations."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model="llama-3.1-8b-instant",
                temperature=0.1,
                max_tokens=4000,
                top_p=0.9,
                stop=None,
                stream=False,
            )
            
            response_text = chat_completion.choices[0].message.content.strip()
            return self.parse_platform_analysis(response_text)
            
        except Exception as e:
            print(f"Groq API error: {e}")
            return {"error": f"Analysis failed: {str(e)}"}

    def parse_platform_analysis(self, text: str) -> Dict:
        """Parse JSON response from Groq API."""
        if not text.strip():
            return {}
        
        # Remove markdown code blocks if present
        text = re.sub(r'```json\s*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'```\s*', '', text)
    
    # Find JSON object - look for balanced braces
        start_idx = text.find('{')
        if start_idx == -1:
            print("⚠️ No JSON object found in response")
            return {}
        
        brace_count = 0
        end_idx = start_idx
        
        for i in range(start_idx, len(text)):
            if text[i] == '{':
                brace_count += 1
            elif text[i] == '}':
                brace_count -= 1
                if brace_count == 0:
                    end_idx = i
                    break
        
        if brace_count != 0:
            print("⚠️ Unbalanced braces in JSON")
            return {}
        
        json_str = text[start_idx:end_idx + 1]
        
        # Clean up common JSON issues
        json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)  # Remove trailing commas
        json_str = re.sub(r'\n\s*', ' ', json_str)  # Remove extra whitespace
        
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            print(f"⚠️ JSON parse failed: {e}")
            print(f"Problematic JSON: {json_str[:200]}...")
            return {}

    def analyze_product(self, product_details: Dict) -> Dict:
        """Run the full product analysis pipeline and return ranked results."""
        platforms = self.discover_platforms_with_groq(product_details)
        analysis = self.analyze_platform_suitability(product_details, platforms)

        platforms_list = []

        for platform in platforms:
            info = analysis.get("platform_analysis", {}).get(platform, {})
            platforms_list.append({
                "name": platform,
                "homepage": self.known_platforms.get(platform, ""),
                "rank": int(info.get("rank", 999)),
                "score": float(info.get("score", 0)),
                "reasoning": info.get("reasoning", ""),
                "gst_taxes": info.get("gst_taxes", "Unknown"),
                "other_charges": info.get("other_charges", "Unknown"),
                "profit": info.get("profit_analysis", "Unknown"),
                "final_selling_charge": info.get("final_selling_charge", "Unknown"),
                "commission_fees": info.get("commission_fees", "Unknown"),
                "advantages": info.get("advantages", []),
                "disadvantages": info.get("disadvantages", []),
                "target_audience_match": info.get("target_audience_match", "Unknown"),
                "category_fit": info.get("category_fit", "Unknown"),
                "competition_level": info.get("competition_level", "Unknown"),
                "business_model": info.get("business_model", "Unknown"),
                "bulk_order_benefits": info.get("bulk_order_benefits", ""),
                "verification_standards": info.get("verification_standards", ""),
                "recommended_strategy": info.get("recommended_strategy", "")
            })

        platforms_list.sort(key=lambda x: x["rank"])

        final_results = {
            "platforms": platforms_list,
            "overall_recommendations": analysis.get("overall_recommendations", {})
        }

        return final_results


def main(product_data: Dict, groq_api_key: str) -> str:
    """
    Main function to analyze product and return JSON results.
    """
    try:
        analyzer = EcommercePlatformAnalyzer(groq_api_key=groq_api_key)
        results = analyzer.analyze_product(product_data)
        return json.dumps(results, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️ Error in main: {e}")
        return "{}"


if __name__ == "__main__":
    # Sample B2C product data
    sample_data_b2c = {
        "name": "Men's Slim Fit Cotton Shirt",
        "category": "Apparel / Fashion",
        "price": 999,
        "features": ["Breathable fabric", "Wrinkle-free", "Available in 5 colors"],
        "target_audience": "Young professionals",
        "brand": "Local Brand",
        "description": "Comfortable and stylish cotton shirt"
    }
    
    # Sample B2B product data - Industrial Safety Equipment
    sample_data_b2b = {
        "name": "Industrial Safety Helmets - ABS Material",
        "category": "Safety Equipment / Industrial Supplies",
        "price": 450,
        "features": [
            "ISI marked compliance",
            "Adjustable chin strap", 
            "Ventilation slots",
            "Impact resistant ABS shell",
            "UV stabilized material"
        ],
        "target_audience": "Construction companies, Manufacturing units, Mining operations",
        "brand": "SafeGuard Pro",
        "description": "Premium quality industrial safety helmets meeting IS 2925 standards for workplace protection"
    }
    
    # Sample B2B product data - Office Supplies
    sample_data_office = {
        "name": "Heavy Duty Paper Shredder - Cross Cut",
        "category": "Office Equipment / Security Equipment", 
        "price": 15000,
        "features": [
            "Cross-cut shredding",
            "15 sheet capacity",
            "Continuous duty motor",
            "Auto start/stop",
            "Overload protection"
        ],
        "target_audience": "Corporate offices, Government departments, Financial institutions",
        "brand": "SecureOffice",
        "description": "Professional grade paper shredder for secure document destruction in offices"
    }

    api_key = GROQ_API_KEY
    
    print("=== B2C PRODUCT ANALYSIS (Cotton Shirt) ===")
    analysis1 = main(sample_data_b2c, api_key)
    print(analysis1)
    
    print("\n=== B2B PRODUCT ANALYSIS (Safety Helmets) ===")
    analysis2 = main(sample_data_b2b, api_key)
    print(analysis2)
    
    print("\n=== B2B PRODUCT ANALYSIS (Office Equipment) ===")
    analysis3 = main(sample_data_office, api_key)
    print(analysis3)



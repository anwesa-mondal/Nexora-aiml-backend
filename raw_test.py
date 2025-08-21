from typing import Dict, List
from groq import Groq
from datetime import datetime
from dotenv import load_dotenv
import os
import json

# Load API key
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")


class RawMaterialProcurementAnalyzer:
    def __init__(self, groq_api_key: str):
        self.groq_client = Groq(api_key=groq_api_key)

        self.known_procurement_platforms = {
            "IndiaMART": "https://www.indiamart.com",
            "TradeIndia": "https://www.tradeindia.com",
            "ExportersIndia": "https://www.exportersindia.com",
            "Alibaba India": "https://www.alibaba.com/countrysearch/IN",
            "Global Sources": "https://www.globalsources.com",
            "Made-in-China": "https://www.made-in-china.com",
            "DHgate": "https://www.dhgate.com",
            "EC21": "https://www.ec21.com",
            "eWorldTrade": "https://www.eworldtrade.com",
            "Go4WorldBusiness": "https://www.go4worldbusiness.com",
            "TradeFord": "https://www.tradeford.com",
            "Kompass": "https://www.kompass.com",
            "Amazon Business": "https://business.amazon.in",
            "Udaan": "https://udaan.com",
            "Direct Government Suppliers": "https://gem.gov.in",
            "Local Wholesale Markets": "Local/Regional Markets"
        }

        self.material_categories = {
            "Textiles": ["Cotton", "Silk", "Polyester", "Wool", "Linen", "Synthetic fabrics"],
            "Metals": ["Steel", "Aluminum", "Copper", "Iron", "Brass", "Stainless steel"],
            "Plastics": ["PVC", "Polyethylene", "Polypropylene", "ABS", "Acrylic"],
            "Electronics": ["Semiconductors", "Circuit boards", "Cables", "Resistors", "Capacitors"],
            "Chemicals": ["Industrial chemicals", "Dyes", "Adhesives", "Solvents", "Lubricants"],
            "Food & Agriculture": ["Grains", "Spices", "Dairy products", "Oils", "Preservatives"],
            "Construction": ["Cement", "Sand", "Bricks", "Steel bars", "Paint"],
            "Packaging": ["Cardboard", "Plastic films", "Glass containers", "Metal cans"],
            "Automotive": ["Engine parts", "Tires", "Batteries", "Filters", "Bearings"],
            "Leather": ["Raw leather", "Processed leather", "Leather chemicals", "Tanning materials"]
        }

    def discover_suppliers_with_ai(self, material_details: Dict) -> List[str]:
        """Discover procurement platforms using AI with JSON-only response."""
        prompt = f"""You are a procurement and supply chain expert specializing in raw material sourcing for MSME businesses in India. 

Based on the material requirements provided, recommend the 5-8 most suitable procurement platforms from the list below. 

Material Requirements:
{json.dumps(material_details, indent=2)}

Available Platform Options:
{json.dumps(list(self.known_procurement_platforms.keys()), indent=2)}

Material Categories and Typical Sources:
{json.dumps(self.material_categories, indent=2)}

⚠ IMPORTANT:
- Return ONLY a JSON array of platform names.
- Do NOT include any text explanation or reasoning.
- Limit to 8 platforms max.
- Ensure essential B2B platforms: 'IndiaMART', 'TradeIndia', 'Amazon Business' are included if relevant.

Example output:
["IndiaMART", "TradeIndia", "Amazon Business", "Alibaba India", "Udaan"]
"""
        try:
            response = self.groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.1-8b-instant",
                temperature=0.2,
                max_tokens=500,
            )
            raw_text = response.choices[0].message.content.strip()
            start = raw_text.find('[')
            end = raw_text.rfind(']') + 1
            platforms = json.loads(raw_text[start:end])

            # Filter known platforms and include essential ones
            platforms = [p for p in platforms if p in self.known_procurement_platforms]
            for essential in ['IndiaMART', 'TradeIndia', 'Amazon Business']:
                if essential not in platforms:
                    platforms.append(essential)
            return platforms[:8]

        except Exception:
            # Fallback platforms
            return ['IndiaMART', 'TradeIndia', 'Amazon Business', 'Alibaba India', 'Udaan']

    def get_fallback_supplier_data(self, platform_name: str, material_details: Dict) -> List[Dict]:
        """Fallback supplier info if AI unavailable."""
        material_name = material_details.get('material_name', 'Material')
        return [{
            "title": f"{material_name} Suppliers - {platform_name}",
            "link": f"{self.known_procurement_platforms.get(platform_name, '#')}/search?q={material_name}",
            "snippet": f"Verified {material_name} suppliers on {platform_name}.",
            "supplier_details": {
                "company_name": "Multiple suppliers",
                "location": "Pan India",
                "price_range": "Market competitive",
                "minimum_order": "As per requirement",
                "delivery_time": "7-15 days",
                "contact_method": f"Through {platform_name}"
            }
        }]
        
    def get_suppliers_with_ai(self, platform_name: str, material_details: Dict) -> List[Dict]:
        prompt = f"""
    You are an expert B2B procurement advisor. 
    Given the following raw material and procurement platform, generate structured supplier information.

    Material Details:
    {json.dumps(material_details, indent=2)}

    Procurement Platform: {platform_name}

    ⚠ IMPORTANT INSTRUCTIONS:
    - Return ONLY valid JSON (a list of suppliers).
    - Each supplier should include:
    - title (string)
    - link (string, example: {self.known_procurement_platforms.get(platform_name, '#')}/search?q={{material_name}})
    - snippet (short summary of supplier offering)
    - supplier_details (object with company_name, location, price_range, minimum_order, delivery_time, contact_method)
    - Provide 3 suppliers per platform.
    - Do NOT include extra commentary.

    Example output:
    [
    {{
        "title": "Cotton Fabric Supplier - ABC Textiles",
        "link": "https://www.indiamart.com/search?q=Cotton+Fabric",
        "snippet": "Leading supplier of cotton fabrics with bulk availability.",
        "supplier_details": {{
        "company_name": "ABC Textiles Pvt Ltd",
        "location": "Surat, India",
        "price_range": "₹55 - ₹85 per meter",
        "minimum_order": "500 meters",
        "delivery_time": "7-10 days",
        "contact_method": "Through IndiaMART"
        }}
    }}
    ]
    """
        try:
            response = self.groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.1-8b-instant",
                temperature=0.3,
                max_tokens=800,
            )
            raw_text = response.choices[0].message.content.strip()

            start = raw_text.find("[")
            end = raw_text.rfind("]") + 1
            suppliers = json.loads(raw_text[start:end])

            return suppliers

        except Exception as e:
            # fallback if Groq fails
            return self.get_fallback_supplier_data(platform_name, material_details)


    def analyze_material_procurement(self, material_details: Dict) -> Dict:
        """Main method to analyze raw material procurement."""
        platforms = self.discover_suppliers_with_ai(material_details)

        # Get supplier results via Groq for each platform
        platform_results = {
            p: self.get_suppliers_with_ai(p, material_details)
            for p in platforms[:5]
        }

        return {
            "material_details": material_details,
            "analysis_timestamp": datetime.now().isoformat(),
            "discovered_platforms": platforms,
            "platform_search_results": platform_results
        }



def main(material_data: Dict, groq_api_key: str) -> str:
    if not groq_api_key:
        return json.dumps({"error": "Groq API key not found"})
    analyzer = RawMaterialProcurementAnalyzer(groq_api_key)
    result = analyzer.analyze_material_procurement(material_data)
    return json.dumps(result, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    sample_data = {
        "material_name": "Cotton Fabric",
        "category": "Textiles",
        "specifications": {"grade": "Commercial Grade", "quantity_required": "1000 meters"},
        "budget_range": {"min_price": 50, "max_price": 100, "currency": "INR", "unit": "per meter"},
        "timeline": {"required_by": "2025-10-01", "flexibility": "2 weeks"},
        "preferred_location": "India",
        "business_type": "Textile Manufacturing",
        "order_frequency": "Monthly",
        "payment_preference": "30 days credit"
    }
    print(main(sample_data, GROQ_API_KEY))


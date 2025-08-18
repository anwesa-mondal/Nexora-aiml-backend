import json
import re
import requests
from typing import Dict, List
from groq import Groq
from datetime import datetime
from dotenv import load_dotenv
import os
import time

# Load API keys
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GOOGLE_SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")
GOOGLE_SEARCH_ENGINE_ID = os.getenv("GOOGLE_SEARCH_ENGINE_ID")


class EcommercePlatformAnalyzer:
    def __init__(self, groq_api_key: str, google_api_key: str, search_engine_id: str):
        """Initialize the analyzer with API credentials."""
        self.groq_client = Groq(api_key=groq_api_key)
        self.google_api_key = google_api_key
        self.search_engine_id = search_engine_id

        self.known_platforms = {
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
            "FirstCry": "https://www.firstcry.com"
        }

    def google_search(self, query: str, num_results: int = 10) -> List[Dict]:
        """Perform Google Custom Search."""
        try:
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                'key': self.google_api_key,
                'cx': self.search_engine_id,
                'q': query,
                'num': min(num_results, 10)
            }
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            return [
                {
                    'title': item.get('title', ''),
                    'link': item.get('link', ''),
                    'snippet': item.get('snippet', '')
                }
                for item in data.get('items', [])
            ]
        except Exception as e:
            print(f"❌ Error performing Google search: {str(e)}")
            return []

    def discover_platforms(self, product_details: Dict) -> List[str]:
        """Discover relevant e-commerce platforms using Google Search."""
        product_name = product_details.get('name', '')
        category = product_details.get('category', '')
        search_queries = [
            f"{product_name} buy online best sites",
            f"{category} online shopping platforms India",
            f"best ecommerce sites for {category}",
            f"where to buy {product_name} online"
        ]

        discovered_platforms = set()
        for query in search_queries:
            results = self.google_search(query, 10)
            for result in results:
                url, title, snippet = result['link'].lower(), result['title'].lower(), result['snippet'].lower()
                for platform, homepage in self.known_platforms.items():
                    domain = homepage.replace('https://', '').replace('www.', '')
                    if (domain in url or platform.lower() in title or platform.lower() in snippet):
                        discovered_platforms.add(platform)
            time.sleep(0.5)

        essential_platforms = ['Amazon', 'Flipkart', 'Myntra']
        discovered_platforms.update(essential_platforms)
        return list(discovered_platforms)

    def analyze_platform_suitability(self, product_details: Dict, platforms: List[str]) -> Dict:
        """Use Groq API to analyze and rank platforms by suitability."""
        prompt = f"""You are an e-commerce platform analysis expert. Analyze the suitability of platforms.

        Product Details:
        {json.dumps(product_details, indent=2)}

        Available Platforms:
        {json.dumps(platforms, indent=2)}

        ⚠️ Important Instructions for Calculations:
        1. Always calculate **GST** as `(GST% × Product Price)`. Show the percentage and the rupee value.
        2. Always calculate **Commission** as `(Commission% × Sale Price)` unless stated otherwise.
        3. Always include **Shipping Charges** as fixed or range-based (₹X–₹Y). If unknown, assume average ₹200.
        4. Compute **Final Selling Charge** as `(Commission + GST + Shipping + Other Fees)`.
        5. Compute **Profit** as `(Selling Price – Final Selling Charge)`. Also return **Net Profit Margin %** = `(Profit ÷ Selling Price × 100)`.
        6. Keep all numeric fields consistent: if Product Price is ₹999, deductions and profit must add up logically.
        7. If platform incentives, subsidies, or monetary benefits apply, deduct them from the cost and add them to profit calculation.
        8. Do not estimate arbitrarily — show actual formula-based breakdowns.
        9. If any data is missing, clearly state assumptions (e.g., "Commission assumed at 15%").

        Return JSON only:
        {{
            "platform_analysis": {{
                "platform_name": {{
                    "rank": "number",
                    "score": "number",
                    "reasoning": "string",
                    "advantages": ["list"],
                    "disadvantages": ["list"],
                    "target_audience_match": "Excellent/Good/Fair/Poor",
                    "category_fit": "Excellent/Good/Fair/Poor",
                    "competition_level": "Low/Medium/High",
                    "gst_taxes": "string (approx GST percentage and cost impact, e.g., 18% = ₹180 on ₹999)",
                    "other_charges": "string (listing fees, commission, shipping, etc.)",
                    "final_selling_charge": "string (Commission + GST + Shipping = ₹X)",
                    "monetary_benefits": ["list of benefits such as subsidies, seller programs, incentives"],
                    "profit": "string (Profit = Selling Price – Final Selling Charge = ₹X, Net Margin = Y%)",
                    "recommended_strategy": "string"
                }}
            }},
            "overall_recommendations": {{
                "top_3_platforms": ["list"],
                "diversification_strategy": "string",
                "pricing_considerations": "string",
                "marketing_focus": "string"
            }}
        }}"""


        try:
            chat_completion = self.groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="meta-llama/llama-4-scout-17b-16e-instruct",
                temperature=0.1,
                max_tokens=2000
            )
            response_text = chat_completion.choices[0].message.content
            return self.parse_platform_analysis(response_text)
        except Exception as e:
            print(f"❌ Error analyzing platforms: {str(e)}")
            return {}

    def parse_platform_analysis(self, text: str) -> Dict:
        """Parse JSON response from Groq API."""
        if not text.strip():
            return {}
        match = re.search(r"```json\s*(\{[\s\S]*?\})\s*```", text, re.IGNORECASE)
        if match:
            text = match.group(1)
        else:
            bracket_match = re.search(r"\{[\s\S]*\}", text)
            if bracket_match:
                text = bracket_match.group(0)
        text = re.sub(r",(\s*[}\]])", r"\1", text)
        try:
            return json.loads(text)
        except Exception as e:
            print(f"❌ JSON parse failed: {e}")
            return {}

    def get_platform_search_results(self, platform_name: str, product_details: Dict) -> List[Dict]:
        """Get top search results for a specific platform."""
        product_name = product_details.get('name', '')
        category = product_details.get('category', '')
        queries = [
            f"{product_name} {platform_name} bestseller",
            f"{category} top products {platform_name}",
            f"{platform_name} {product_name} deals"
        ]
        all_results = []
        domain = self.known_platforms.get(platform_name, '').replace('https://', '').replace('www.', '')

        for query in queries:
            results = self.google_search(query, 5)
            filtered = [r for r in results if domain and domain in r['link'].lower()]
            all_results.extend(filtered)
            time.sleep(0.5)

        seen, unique = set(), []
        for r in all_results:
            if r['link'] not in seen:
                seen.add(r['link'])
                unique.append(r)
            if len(unique) >= 10:
                break
        return unique

    def analyze_product(self, product_details: Dict) -> Dict:
        """Run the full product analysis pipeline and return ranked results."""
        platforms = self.discover_platforms(product_details)
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
            "profit": info.get("profit", "Unknown"),
            "final_selling_charge": info.get("final_selling_charge", "Unknown"),
            "monetary_benefits": info.get("monetary_benefits", []),
            "advantages": info.get("advantages", []),
            "disadvantages": info.get("disadvantages", []),
            "target_audience_match": info.get("target_audience_match", "Unknown"),
            "category_fit": info.get("category_fit", "Unknown"),
            "competition_level": info.get("competition_level", "Unknown"),
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
        analyzer = EcommercePlatformAnalyzer(
            groq_api_key=groq_api_key,
            google_api_key=GOOGLE_SEARCH_API_KEY,
            search_engine_id=GOOGLE_SEARCH_ENGINE_ID
        )
        results = analyzer.analyze_product(product_data)
        return json.dumps(results, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"❌ Error in main: {e}")
        return "{}"


if __name__ == "__main__":
    # Sample product data
    sample_data = {
        "name": "Men's Slim Fit Cotton Shirt",
        "category": "Apparel / Fashion",
        "price": 999,
        "features": ["Breathable fabric", "Wrinkle-free", "Available in 5 colors"],
        "target_audience": "Young professionals",
        "brand": "Local Brand",
        "description": "Comfortable and stylish cotton shirt"
    }

    api_key = GROQ_API_KEY
    analysis = main(sample_data, api_key)
    print(analysis)




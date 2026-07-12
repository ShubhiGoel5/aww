"""
Pricing API
Get pricing tiers and plans
"""
from fastapi import APIRouter, Query
import json
from pathlib import Path

router = APIRouter(prefix="/v1/pricing", tags=["Pricing"])

# Load pricing data
PRICING_FILE = Path(__file__).parent.parent.parent / "data" / "pricing.json"

def load_pricing():
    """Load pricing data from JSON file"""
    try:
        with open(PRICING_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading pricing: {e}")
        return {"tiers": [], "features_comparison": {}, "addons": []}

@router.get("")
async def get_pricing(lang: str = Query("vi", pattern="^(vi|en)$")):
    """
    Get pricing tiers and plans
    
    Query params:
    - lang: Language (vi or en)
    """
    pricing_data = load_pricing()
    
    # Format tiers based on language
    tiers = []
    for tier in pricing_data.get("tiers", []):
        formatted_tier = {
            "id": tier["id"],
            "name": tier.get(f"name_{lang}", tier["name"]) if lang == "en" else tier["name"],
            "price_usd": tier["price_usd"],
            "price_vnd": tier["price_vnd"],
            "billing": tier.get("billing", "monthly"),
            "description": tier.get(f"description_{lang}", tier.get("description", "")),
            "features": tier["features"],
            "limits": tier.get("limits", {}),
            "recommended_for": tier.get(f"recommended_for_{lang}", tier.get("recommended_for", ""))
        }
        
        # Add SLA info for enterprise
        if tier["id"] == "enterprise":
            formatted_tier["sla_uptime"] = tier.get("sla_uptime")
            formatted_tier["support_response_time"] = tier.get("support_response_time")
        
        tiers.append(formatted_tier)
    
    # Format features comparison
    features = {}
    for feat_id, feat_data in pricing_data.get("features_comparison", {}).items():
        features[feat_id] = {
            "name": feat_data.get(f"name_{lang}", feat_data.get("name", "")),
            "description": feat_data.get(f"description_{lang}", feat_data.get("description", ""))
        }
    
    # Format addons
    addons = []
    for addon in pricing_data.get("addons", []):
        addons.append({
            "id": addon["id"],
            "name": addon.get(f"name_{lang}", addon["name"]) if lang == "en" else addon["name"],
            "price_usd": addon["price_usd"],
            "price_vnd": addon["price_vnd"]
        })
    
    # Format discounts
    discounts = {}
    for disc_id, disc_data in pricing_data.get("discounts", {}).items():
        discounts[disc_id] = {
            "discount_percentage": disc_data["discount_percentage"],
            "description": disc_data.get(f"description_{lang}", disc_data.get("description", "")),
            "eligibility": disc_data.get("eligibility")
        }
    
    # Format FAQ
    faq = []
    for item in pricing_data.get("faq", []):
        faq.append({
            "question": item.get(f"question_{lang}", item.get("question", "")),
            "answer": item.get(f"answer_{lang}", item.get("answer", ""))
        })
    
    return {
        "tiers": tiers,
        "features_comparison": features,
        "addons": addons,
        "discounts": discounts,
        "trial": pricing_data.get("trial", {}),
        "payment_methods": pricing_data.get("payment_methods", []),
        "faq": faq,
        "currency_conversion": pricing_data.get("currency_conversion", {})
    }

@router.get("/tiers/{tier_id}")
async def get_pricing_tier(tier_id: str, lang: str = Query("vi", pattern="^(vi|en)$")):
    """Get details of a specific pricing tier"""
    pricing_data = load_pricing()
    
    tier = None
    for t in pricing_data.get("tiers", []):
        if t["id"] == tier_id:
            tier = t
            break
    
    if not tier:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Pricing tier not found")
    
    # Format tier
    formatted_tier = {
        "id": tier["id"],
        "name": tier.get(f"name_{lang}", tier["name"]) if lang == "en" else tier["name"],
        "price_usd": tier["price_usd"],
        "price_vnd": tier["price_vnd"],
        "billing": tier.get("billing", "monthly"),
        "description": tier.get(f"description_{lang}", tier.get("description", "")),
        "features": tier["features"],
        "limits": tier.get("limits", {}),
        "recommended_for": tier.get(f"recommended_for_{lang}", tier.get("recommended_for", ""))
    }
    
    if tier["id"] == "enterprise":
        formatted_tier["sla_uptime"] = tier.get("sla_uptime")
        formatted_tier["support_response_time"] = tier.get("support_response_time")
    
    return formatted_tier

@router.get("/calculate")
async def calculate_pricing(
    tier_id: str = Query(...),
    billing: str = Query("monthly", pattern="^(monthly|annual)$"),
    team_size: int = Query(1, ge=1),
    discount_code: str = Query(None),
    lang: str = Query("vi", pattern="^(vi|en)$")
):
    """
    Calculate total pricing with discounts
    
    Query params:
    - tier_id: Pricing tier ID
    - billing: monthly or annual
    - team_size: Number of team members
    - discount_code: Discount code (startup, ngo, annual_billing)
    - lang: Language
    """
    pricing_data = load_pricing()
    
    # Get tier
    tier = None
    for t in pricing_data.get("tiers", []):
        if t["id"] == tier_id:
            tier = t
            break
    
    if not tier:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Pricing tier not found")
    
    base_price_vnd = tier["price_vnd"]
    base_price_usd = tier["price_usd"]
    
    # Check if team size exceeds limit
    team_limit = tier.get("limits", {}).get("team_members")
    extra_users = 0
    if team_limit and team_limit != "unlimited" and team_size > team_limit:
        extra_users = team_size - team_limit
        # Assume extra user cost = 10% of base price per user
        extra_user_cost_vnd = int(base_price_vnd * 0.1 * extra_users)
        extra_user_cost_usd = int(base_price_usd * 0.1 * extra_users)
        base_price_vnd += extra_user_cost_vnd
        base_price_usd += extra_user_cost_usd
    
    # Apply billing discount
    discount_percentage = 0
    discount_reason = []
    
    if billing == "annual":
        annual_discount = pricing_data.get("discounts", {}).get("annual_billing", {})
        discount_percentage = annual_discount.get("discount_percentage", 0)
        discount_reason.append(f"Annual billing: {discount_percentage}% off")
    
    # Apply discount code
    if discount_code:
        code_discount = pricing_data.get("discounts", {}).get(discount_code, {})
        if code_discount:
            code_discount_pct = code_discount.get("discount_percentage", 0)
            discount_percentage += code_discount_pct
            discount_reason.append(f"{discount_code.capitalize()}: {code_discount_pct}% off")
    
    # Calculate final price
    discount_amount_vnd = int(base_price_vnd * discount_percentage / 100)
    discount_amount_usd = int(base_price_usd * discount_percentage / 100)
    
    final_price_vnd = base_price_vnd - discount_amount_vnd
    final_price_usd = base_price_usd - discount_amount_usd
    
    # If annual, multiply by 12
    if billing == "annual":
        final_price_vnd *= 12
        final_price_usd *= 12
    
    return {
        "tier": tier["name"] if lang == "vi" else tier.get("name_en", tier["name"]),
        "tier_id": tier_id,
        "billing": billing,
        "team_size": team_size,
        "base_price_vnd": base_price_vnd,
        "base_price_usd": base_price_usd,
        "discount_percentage": discount_percentage,
        "discount_reason": discount_reason,
        "discount_amount_vnd": discount_amount_vnd,
        "discount_amount_usd": discount_amount_usd,
        "final_price_vnd": final_price_vnd,
        "final_price_usd": final_price_usd,
        "extra_users": extra_users,
        "currency": "VND" if lang == "vi" else "USD"
    }

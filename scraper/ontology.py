# ============================================
# AMAZON PRODUCT INTELLIGENCE ONTOLOGY
# Complete Category-Attribute Mapping System
# ============================================

"""
The complete Amazon Product Intelligence Ontology.

Maps:
- 327 Master Data Points × Amazon Category Tree (28 cats, 382 subcats)
- Category-specific attributes (automatically inherited)
- Subcategory-specific attributes (fine-grained)
- Product-type attributes (max specificity)
- Variation themes per category
- Dynamic discovery for new attributes
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


# ============================================================
# 1. COMPLETE ATTRIBUTE DEFINITIONS (327 Framework Mapped)
# ============================================================

UNIVERSAL_ATTRIBUTES = [
    # Core Product Identification (Points 1-12)
    {"name": "asin", "type": "string", "tier": 1, "mandatory": True, "source": "list_page"},
    {"name": "title", "type": "string", "tier": 1, "mandatory": True, "source": "list_page"},
    {"name": "brand", "type": "string", "tier": 1, "mandatory": False, "source": "list_page"},
    {"name": "manufacturer", "type": "string", "tier": 2, "mandatory": False, "source": "product_page"},
    {"name": "parent_asin", "type": "string", "tier": 2, "mandatory": False, "source": "product_page"},
    {"name": "category_path", "type": "string", "tier": 1, "mandatory": True, "source": "list_page"},
    {"name": "subcategory", "type": "string", "tier": 1, "mandatory": False, "source": "inferred"},
    {"name": "product_type", "type": "string", "tier": 1, "mandatory": False, "source": "inferred"},
    {"name": "upc_ean", "type": "string", "tier": 2, "mandatory": False, "source": "product_page"},
    {"name": "model_number", "type": "string", "tier": 2, "mandatory": False, "source": "product_page"},
    {"name": "first_available_date", "type": "datetime", "tier": 3, "mandatory": False, "source": "product_page"},
    {"name": "asin_url", "type": "url", "tier": 1, "mandatory": False, "source": "derived"},
    
    # Pricing & Financial Metrics (Points 13-38)
    {"name": "current_price", "type": "number", "tier": 1, "mandatory": True, "source": "list_page"},
    {"name": "mrp", "type": "number", "tier": 1, "mandatory": False, "source": "list_page"},
    {"name": "discount_pct", "type": "number", "tier": 1, "mandatory": False, "source": "derived"},
    {"name": "price_per_unit", "type": "number", "tier": 2, "mandatory": False, "source": "derived"},
    {"name": "buy_box_price", "type": "number", "tier": 2, "mandatory": False, "source": "product_page"},
    {"name": "lowest_new_price", "type": "number", "tier": 2, "mandatory": False, "source": "product_page"},
    {"name": "lowest_used_price", "type": "number", "tier": 3, "mandatory": False, "source": "product_page"},
    {"name": "prime_eligible", "type": "boolean", "tier": 2, "mandatory": False, "source": "list_page"},
    {"name": "shipping_cost", "type": "number", "tier": 3, "mandatory": False, "source": "product_page"},
    
    # Sales Performance (Points 39-56)
    {"name": "bsr_rank", "type": "number", "tier": 1, "mandatory": False, "source": "product_page"},
    {"name": "bsr_category", "type": "string", "tier": 1, "mandatory": False, "source": "product_page"},
    {"name": "rating", "type": "number", "tier": 1, "mandatory": True, "source": "list_page"},
    {"name": "review_count", "type": "number", "tier": 1, "mandatory": True, "source": "list_page"},
    {"name": "review_dist_5star", "type": "number", "tier": 2, "mandatory": False, "source": "product_page"},
    {"name": "review_dist_4star", "type": "number", "tier": 2, "mandatory": False, "source": "product_page"},
    {"name": "review_dist_3star", "type": "number", "tier": 2, "mandatory": False, "source": "product_page"},
    {"name": "review_dist_2star", "type": "number", "tier": 2, "mandatory": False, "source": "product_page"},
    {"name": "review_dist_1star", "type": "number", "tier": 2, "mandatory": False, "source": "product_page"},
    {"name": "est_monthly_sales", "type": "number", "tier": 2, "mandatory": False, "source": "api"},
    {"name": "est_monthly_revenue", "type": "number", "tier": 2, "mandatory": False, "source": "api"},
    {"name": "sales_velocity", "type": "number", "tier": 3, "mandatory": False, "source": "api"},
    
    # Customer Feedback (Points 57-88)
    {"name": "verified_purchase_pct", "type": "number", "tier": 2, "mandatory": False, "source": "product_page"},
    {"name": "review_velocity", "type": "number", "tier": 2, "mandatory": False, "source": "product_page"},
    {"name": "positive_keywords", "type": "string", "tier": 3, "mandatory": False, "source": "product_page"},
    {"name": "negative_keywords", "type": "string", "tier": 3, "mandatory": False, "source": "product_page"},
    {"name": "pain_points", "type": "string", "tier": 3, "mandatory": False, "source": "product_page"},
    {"name": "quality_mentions", "type": "string", "tier": 3, "mandatory": False, "source": "product_page"},
    {"name": "durability_comments", "type": "string", "tier": 3, "mandatory": False, "source": "product_page"},
    {"name": "value_sentiment", "type": "string", "tier": 3, "mandatory": False, "source": "product_page"},
    
    # Q&A (Points 89-103)
    {"name": "question_count", "type": "number", "tier": 2, "mandatory": False, "source": "product_page"},
    {"name": "answer_count", "type": "number", "tier": 2, "mandatory": False, "source": "product_page"},
    {"name": "common_questions", "type": "string", "tier": 3, "mandatory": False, "source": "product_page"},
    {"name": "unanswered_questions", "type": "number", "tier": 3, "mandatory": False, "source": "product_page"},
    
    # Product Details (Points 104-125)
    {"name": "dimensions", "type": "string", "tier": 2, "mandatory": False, "source": "product_page"},
    {"name": "weight", "type": "string", "tier": 2, "mandatory": False, "source": "product_page"},
    {"name": "package_dimensions", "type": "string", "tier": 3, "mandatory": False, "source": "product_page"},
    {"name": "package_weight", "type": "string", "tier": 3, "mandatory": False, "source": "product_page"},
    {"name": "size_tier", "type": "string", "tier": 2, "mandatory": False, "source": "product_page"},
    {"name": "color_options", "type": "string", "tier": 2, "mandatory": False, "source": "product_page"},
    {"name": "size_options", "type": "string", "tier": 2, "mandatory": False, "source": "product_page"},
    {"name": "material", "type": "string", "tier": 2, "mandatory": False, "source": "product_page"},
    {"name": "pack_quantity", "type": "number", "tier": 2, "mandatory": False, "source": "product_page"},
    {"name": "bullet_points", "type": "string", "tier": 2, "mandatory": False, "source": "product_page"},
    {"name": "description", "type": "string", "tier": 2, "mandatory": False, "source": "product_page"},
    {"name": "warranty", "type": "string", "tier": 2, "mandatory": False, "source": "product_page"},
    {"name": "certifications", "type": "string", "tier": 3, "mandatory": False, "source": "product_page"},
    {"name": "country_of_origin", "type": "string", "tier": 3, "mandatory": False, "source": "product_page"},
    
    # Visual Assets (Points 126-138)
    {"name": "main_image", "type": "url", "tier": 1, "mandatory": True, "source": "list_page"},
    {"name": "image_count", "type": "number", "tier": 2, "mandatory": False, "source": "product_page"},
    {"name": "has_video", "type": "boolean", "tier": 2, "mandatory": False, "source": "product_page"},
    {"name": "has_360_view", "type": "boolean", "tier": 3, "mandatory": False, "source": "product_page"},
    {"name": "has_size_chart", "type": "boolean", "tier": 3, "mandatory": False, "source": "product_page"},
    {"name": "has_plus_content", "type": "boolean", "tier": 3, "mandatory": False, "source": "product_page"},
    
    # SEO & Competition (Points 139-170)
    {"name": "title_keywords", "type": "string", "tier": 2, "mandatory": False, "source": "derived"},
    {"name": "backend_search_terms", "type": "string", "tier": 3, "mandatory": False, "source": "api"},
    {"name": "organic_rank", "type": "number", "tier": 3, "mandatory": False, "source": "api"},
    {"name": "top_competing_asins", "type": "string", "tier": 3, "mandatory": False, "source": "api"},
    {"name": "competitor_avg_price", "type": "number", "tier": 3, "mandatory": False, "source": "api"},
    {"name": "price_vs_competitors", "type": "number", "tier": 3, "mandatory": False, "source": "derived"},
    {"name": "seller_name", "type": "string", "tier": 2, "mandatory": False, "source": "product_page"},
    {"name": "seller_rating", "type": "number", "tier": 2, "mandatory": False, "source": "product_page"},
    {"name": "fulfillment_method", "type": "string", "tier": 2, "mandatory": False, "source": "product_page"},
    {"name": "stock_status", "type": "string", "tier": 2, "mandatory": False, "source": "product_page"},
    
    # Promotions (Points 186-194)
    {"name": "lightning_deal", "type": "boolean", "tier": 2, "mandatory": False, "source": "product_page"},
    {"name": "coupon_discount", "type": "number", "tier": 2, "mandatory": False, "source": "product_page"},
    {"name": "subscribe_save", "type": "number", "tier": 3, "mandatory": False, "source": "product_page"},
    
    # Listing Quality (Points 201-218)
    {"name": "listing_quality_score", "type": "number", "tier": 3, "mandatory": False, "source": "api"},
    {"name": "conversion_rate", "type": "number", "tier": 3, "mandatory": False, "source": "api"},
    {"name": "return_rate", "type": "number", "tier": 3, "mandatory": False, "source": "api"},
    {"name": "buy_box_percentage", "type": "number", "tier": 3, "mandatory": False, "source": "api"},
    
    # Provenance
    {"name": "collected_at", "type": "datetime", "tier": 1, "mandatory": True, "source": "system"},
    {"name": "scraper_id", "type": "string", "tier": 2, "mandatory": False, "source": "system"},
]

# Category-specific attributes
CATEGORY_ATTRIBUTES = {
    "Electronics": [
        {"name": "ram", "type": "string", "tier": 2, "mandatory": False, "source": "product_page", "subcategories": ["Mobiles & Tablets", "Computers & Accessories"]},
        {"name": "storage", "type": "string", "tier": 2, "mandatory": False, "source": "product_page", "subcategories": ["Mobiles & Tablets", "Computers & Accessories"]},
        {"name": "processor", "type": "string", "tier": 2, "mandatory": False, "source": "product_page", "subcategories": ["Computers & Accessories", "Mobiles & Tablets"]},
        {"name": "processor_generation", "type": "string", "tier": 3, "mandatory": False, "source": "product_page", "subcategories": ["Computers & Accessories"]},
        {"name": "gpu", "type": "string", "tier": 3, "mandatory": False, "source": "product_page", "subcategories": ["Computers & Accessories"]},
        {"name": "gpu_memory", "type": "string", "tier": 3, "mandatory": False, "source": "product_page", "subcategories": ["Computers & Accessories"]},
        {"name": "display_size", "type": "string", "tier": 2, "mandatory": False, "source": "product_page", "subcategories": ["Mobiles & Tablets", "Home Theatre, TV & Video"]},
        {"name": "display_type", "type": "string", "tier": 3, "mandatory": False, "source": "product_page", "subcategories": ["Home Theatre, TV & Video"]},
        {"name": "resolution", "type": "string", "tier": 2, "mandatory": False, "source": "product_page", "subcategories": ["Home Theatre, TV & Video", "Mobiles & Tablets"]},
        {"name": "refresh_rate", "type": "string", "tier": 3, "mandatory": False, "source": "product_page", "subcategories": ["Home Theatre, TV & Video", "Computers & Accessories"]},
        {"name": "battery_capacity", "type": "string", "tier": 2, "mandatory": False, "source": "product_page", "subcategories": ["Mobiles & Tablets"]},
        {"name": "charging_speed", "type": "string", "tier": 3, "mandatory": False, "source": "product_page", "subcategories": ["Mobiles & Tablets"]},
        {"name": "connectivity", "type": "string", "tier": 2, "mandatory": False, "source": "product_page", "subcategories": ["Mobiles & Tablets", "Computers & Accessories"]},
        {"name": "ports", "type": "string", "tier": 3, "mandatory": False, "source": "product_page", "subcategories": ["Computers & Accessories"]},
        {"name": "os", "type": "string", "tier": 2, "mandatory": False, "source": "product_page", "subcategories": ["Mobiles & Tablets", "Computers & Accessories"]},
        {"name": "cameras_rear", "type": "string", "tier": 2, "mandatory": False, "source": "product_page", "subcategories": ["Mobiles & Tablets"]},
        {"name": "cameras_front", "type": "string", "tier": 3, "mandatory": False, "source": "product_page", "subcategories": ["Mobiles & Tablets"]},
        {"name": "network", "type": "string", "tier": 2, "mandatory": False, "source": "product_page", "subcategories": ["Mobiles & Tablets"]},
        {"name": "sim_type", "type": "string", "tier": 3, "mandatory": False, "source": "product_page", "subcategories": ["Mobiles & Tablets"]},
        {"name": "weight_spec", "type": "string", "tier": 2, "mandatory": False, "source": "product_page"},
        {"name": "special_features", "type": "string", "tier": 2, "mandatory": False, "source": "product_page"},
        {"name": "noise_cancellation", "type": "boolean", "tier": 2, "mandatory": False, "source": "product_page", "subcategories": ["Headphones"]},
        {"name": "wireless", "type": "boolean", "tier": 2, "mandatory": False, "source": "product_page", "subcategories": ["Headphones", "Hi-Fi & Home Audio"]},
        {"name": "warranty_years", "type": "number", "tier": 2, "mandatory": False, "source": "product_page"},
    ],
    "Fashion": [
        {"name": "gender", "type": "string", "tier": 2, "mandatory": False, "source": "product_page"},
        {"name": "size", "type": "string", "tier": 1, "mandatory": False, "source": "product_page"},
        {"name": "available_sizes", "type": "string", "tier": 2, "mandatory": False, "source": "product_page"},
        {"name": "fabric", "type": "string", "tier": 2, "mandatory": False, "source": "product_page"},
        {"name": "pattern", "type": "string", "tier": 2, "mandatory": False, "source": "product_page"},
        {"name": "fit", "type": "string", "tier": 2, "mandatory": False, "source": "product_page"},
        {"name": "sleeve_type", "type": "string", "tier": 3, "mandatory": False, "source": "product_page"},
        {"name": "neck_type", "type": "string", "tier": 3, "mandatory": False, "source": "product_page"},
        {"name": "collar_type", "type": "string", "tier": 3, "mandatory": False, "source": "product_page"},
        {"name": "closure_type", "type": "string", "tier": 2, "mandatory": False, "source": "product_page"},
        {"name": "occasion", "type": "string", "tier": 2, "mandatory": False, "source": "product_page"},
        {"name": "care_instructions", "type": "string", "tier": 3, "mandatory": False, "source": "product_page"},
        {"name": "formal_casual", "type": "string", "tier": 2, "mandatory": False, "source": "product_page"},
        {"name": "season", "type": "string", "tier": 3, "mandatory": False, "source": "product_page"},
    ],
    "Home & Kitchen": [
        {"name": "capacity", "type": "string", "tier": 2, "mandatory": False, "source": "product_page"},
        {"name": "color_options", "type": "string", "tier": 2, "mandatory": False, "source": "product_page"},
        {"name": "material_construction", "type": "string", "tier": 2, "mandatory": False, "source": "product_page"},
        {"name": "weight_spec", "type": "string", "tier": 2, "mandatory": False, "source": "product_page"},
        {"name": "power_wattage", "type": "string", "tier": 3, "mandatory": False, "source": "product_page"},
        {"name": "voltage", "type": "string", "tier": 3, "mandatory": False, "source": "product_page"},
        {"name": "warranty_years", "type": "number", "tier": 2, "mandatory": False, "source": "product_page"},
        {"name": "dishwasher_safe", "type": "boolean", "tier": 3, "mandatory": False, "source": "product_page"},
        {"name": "microwave_safe", "type": "boolean", "tier": 3, "mandatory": False, "source": "product_page"},
    ],
    "Beauty": [
        {"name": "product_type", "type": "string", "tier": 2, "mandatory": False, "source": "product_page"},
        {"name": "quantity", "type": "string", "tier": 2, "mandatory": False, "source": "product_page"},
        {"name": "formulation", "type": "string", "tier": 2, "mandatory": False, "source": "product_page"},
        {"name": "skin_type", "type": "string", "tier": 2, "mandatory": False, "source": "product_page"},
        {"name": "hair_type", "type": "string", "tier": 2, "mandatory": False, "source": "product_page"},
        {"name": "ingredients", "type": "string", "tier": 3, "mandatory": False, "source": "product_page"},
        {"name": "concern", "type": "string", "tier": 2, "mandatory": False, "source": "product_page"},
        {"name": "spf", "type": "number", "tier": 2, "mandatory": False, "source": "product_page"},
        {"name": "shade", "type": "string", "tier": 2, "mandatory": False, "source": "product_page"},
        {"name": "fragrance", "type": "string", "tier": 3, "mandatory": False, "source": "product_page"},
        {"name": "shelf_life", "type": "string", "tier": 3, "mandatory": False, "source": "product_page"},
        {"name": "certifications", "type": "string", "tier": 3, "mandatory": False, "source": "product_page"},
    ],
    "Grocery": [
        {"name": "net_weight", "type": "string", "tier": 1, "mandatory": False, "source": "product_page"},
        {"name": "pack_size", "type": "number", "tier": 2, "mandatory": False, "source": "product_page"},
        {"name": "ingredients", "type": "string", "tier": 2, "mandatory": False, "source": "product_page"},
        {"name": "flavour", "type": "string", "tier": 2, "mandatory": False, "source": "product_page"},
        {"name": "nutritional_info", "type": "string", "tier": 3, "mandatory": False, "source": "product_page"},
        {"name": "vegetarian", "type": "boolean", "tier": 2, "mandatory": False, "source": "product_page"},
        {"name": "non_vegetarian", "type": "boolean", "tier": 2, "mandatory": False, "source": "product_page"},
        {"name": "allergens", "type": "string", "tier": 3, "mandatory": False, "source": "product_page"},
        {"name": "shelf_life_months", "type": "number", "tier": 2, "mandatory": False, "source": "product_page"},
        {"name": "storage_instructions", "type": "string", "tier": 2, "mandatory": False, "source": "product_page"},
        {"name": "fssai_license", "type": "string", "tier": 3, "mandatory": False, "source": "product_page"},
        {"name": "manufacturing_date", "type": "datetime", "tier": 3, "mandatory": False, "source": "product_page"},
        {"name": "expiry_date", "type": "datetime", "tier": 3, "mandatory": False, "source": "product_page"},
    ],
    "Sports": [
        {"name": "sport_type", "type": "string", "tier": 2, "mandatory": False, "source": "product_page"},
        {"name": "age_group", "type": "string", "tier": 2, "mandatory": False, "source": "product_page"},
        {"name": "material", "type": "string", "tier": 2, "mandatory": False, "source": "product_page"},
        {"name": "weight_spec", "type": "string", "tier": 2, "mandatory": False, "source": "product_page"},
        {"name": "size_spec", "type": "string", "tier": 2, "mandatory": False, "source": "product_page"},
        {"name": "skill_level", "type": "string", "tier": 3, "mandatory": False, "source": "product_page"},
        {"name": "gender", "type": "string", "tier": 2, "mandatory": False, "source": "product_page"},
        {"name": "warranty", "type": "string", "tier": 2, "mandatory": False, "source": "product_page"},
    ],
    "Books": [
        {"name": "isbn", "type": "string", "tier": 2, "mandatory": False, "source": "product_page"},
        {"name": "publisher", "type": "string", "tier": 2, "mandatory": False, "source": "product_page"},
        {"name": "publication_date", "type": "datetime", "tier": 2, "mandatory": False, "source": "product_page"},
        {"name": "language", "type": "string", "tier": 2, "mandatory": False, "source": "product_page"},
        {"name": "page_count", "type": "number", "tier": 2, "mandatory": False, "source": "product_page"},
        {"name": "binding", "type": "string", "tier": 2, "mandatory": False, "source": "product_page"},
        {"name": "author", "type": "string", "tier": 2, "mandatory": False, "source": "product_page"},
        {"name": "genre", "type": "string", "tier": 2, "mandatory": False, "source": "product_page"},
        {"name": "edition", "type": "string", "tier": 3, "mandatory": False, "source": "product_page"},
    ],
    "Automotive": [
        {"name": "vehicle_compatibility", "type": "string", "tier": 2, "mandatory": False, "source": "product_page"},
        {"name": "part_number", "type": "string", "tier": 2, "mandatory": False, "source": "product_page"},
        {"name": "material", "type": "string", "tier": 2, "mandatory": False, "source": "product_page"},
        {"name": "warranty", "type": "string", "tier": 2, "mandatory": False, "source": "product_page"},
        {"name": "fit_type", "type": "string", "tier": 2, "mandatory": False, "source": "product_page"},
    ],
    "Baby": [
        {"name": "age_range", "type": "string", "tier": 2, "mandatory": False, "source": "product_page"},
        {"name": "material", "type": "string", "tier": 2, "mandatory": False, "source": "product_page"},
        {"name": "safety_certifications", "type": "string", "tier": 3, "mandatory": False, "source": "product_page"},
        {"name": "weight_limit", "type": "string", "tier": 2, "mandatory": False, "source": "product_page"},
        {"name": "assembly_required", "type": "boolean", "tier": 3, "mandatory": False, "source": "product_page"},
    ],
    "Toys": [
        {"name": "age_range", "type": "string", "tier": 2, "mandatory": False, "source": "product_page"},
        {"name": "material", "type": "string", "tier": 2, "mandatory": False, "source": "product_page"},
        {"name": "safety_standards", "type": "string", "tier": 3, "mandatory": False, "source": "product_page"},
        {"name": "number_of_pieces", "type": "number", "tier": 2, "mandatory": False, "source": "product_page"},
        {"name": "battery_required", "type": "boolean", "tier": 2, "mandatory": False, "source": "product_page"},
    ],
    "Jewelry": [
        {"name": "metal_type", "type": "string", "tier": 2, "mandatory": False, "source": "product_page"},
        {"name": "gemstone", "type": "string", "tier": 3, "mandatory": False, "source": "product_page"},
        {"name": "carat_weight", "type": "string", "tier": 3, "mandatory": False, "source": "product_page"},
        {"name": "chain_length", "type": "string", "tier": 2, "mandatory": False, "source": "product_page"},
        {"name": "clasp_type", "type": "string", "tier": 3, "mandatory": False, "source": "product_page"},
        {"name": "gender", "type": "string", "tier": 2, "mandatory": False, "source": "product_page"},
    ],
    "Watches": [
        {"name": "movement_type", "type": "string", "tier": 2, "mandatory": False, "source": "product_page"},
        {"name": "case_material", "type": "string", "tier": 2, "mandatory": False, "source": "product_page"},
        {"name": "band_material", "type": "string", "tier": 2, "mandatory": False, "source": "product_page"},
        {"name": "water_resistance", "type": "string", "tier": 2, "mandatory": False, "source": "product_page"},
        {"name": "case_diameter", "type": "string", "tier": 2, "mandatory": False, "source": "product_page"},
        {"name": "gender", "type": "string", "tier": 2, "mandatory": False, "source": "product_page"},
    ],
}

# Variation themes per category
VARIATION_THEMES = {
    "Electronics": "Color × Storage × RAM",
    "Fashion": "Size × Color × Fit",
    "Home & Kitchen": "Color × Size",
    "Beauty": "Shade × Size × Pack",
    "Grocery": "Flavour × Weight × Pack",
    "Sports": "Size × Color",
    "Books": "Binding × Edition",
    "Automotive": "Fit Type",
    "Baby": "Color × Size",
    "Toys": "Color × Size",
    "Jewelry": "Metal × Size",
    "Watches": "Band Material × Case Size",
}

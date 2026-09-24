"""
Category Mapper — auto-detects category/subcategory/product-type from ASIN.

Uses three strategies:
1. Direct lookup from catalog (if we've seen this ASIN before)
2. Title-based inference using keyword matching
3. Subcategory JSON lookup (from subcats.json)
4. Dynamic discovery on first encounter

This module runs lightweight inference BEFORE fetching product pages,
so we know what attributes to expect without extra API calls.
"""

import json
import os
import re
from pathlib import Path
from typing import Optional

from .attribute_registry import AttributeRegistry, default_registry


class CategoryMapper:
    """
    Maps ASINs to their Amazon category hierarchy.
    
    Example:
        mapper = CategoryMapper()
        result = mapper.map("B09V3KXJPB", title="Sony WH-1000XM4 Wireless Headphones")
        # Returns: {
        #   "category": "Electronics",
        #   "subcategory": "Headphones",
        #   "product_type": "over_ear",
        #   "confidence": 0.95
        # }
    """
    
    # Keyword patterns for inference (tune as needed)
    PRODUCT_TYPE_PATTERNS = {
        # Electronics
        "earbuds": re.compile(r'\b(earbuds|ear buds|in-ear|free\_ear|true\_wireless)\b', re.I),
        "wired_headphones": re.compile(r'\b(wired|on\_ear|headset)\b.*\b(headphone|earphone)\b', re.I),
        "over_ear": re.compile(r'\b(over.?ear|circumaural)\b', re.I),
        "headphone": re.compile(r'\bheadphones?\b', re.I),
        "smartphone": re.compile(r'\b(smartphone|mobile|cellphone|cell phone|android|iphone)\b', re.I),
        "tablet": re.compile(r'\b(tablet|ipad|kindle\s+fire)\b', re.I),
        "laptop": re.compile(r'\b(laptop|notebook)\b', re.I),
        "charger": re.compile(r'\b(charger|adapter|power\s+bank)\b', re.I),
        "cable": re.compile(r'\b(cable|usb\s+cable|charging\s+ cable)\b', re.I),
        "camera": re.compile(r'\b(camera|dslr|mirrorless|action\s+camera)\b', re.I),
        
        # Fashion
        "shirt": re.compile(r'\b(shirt)\b', re.I),
        "pant": re.compile(r'\b(pant|trouser|jean)\b', re.I),
        "tshirt": re.compile(r'\b(t.?shirt|tee)\b', re.I),
        "dress": re.compile(r'\b(dress)\b', re.I),
        "kurti": re.compile(r'\b(kurti|kurtah)\b', re.I),
        "shoe": re.compile(r'\b(shoe|sneaker|runner|jogger)\b', re.I),
        "watch": re.compile(r'\b(watch)\b', re.I),
        
        # Home & Kitchen
        "cooker": re.compile(r'\b(cooker|pressure\s+cooker|instant\s+pot)\b', re.I),
        "pan": re.compile(r'\b(pan|kadai|wok|frying\s+pan)\b', re.I),
        "blade": re.compile(r'\b(blade|mixer\s+grinder|juicer)\b', re.I),
        "fan": re.compile(r'\b(fan)\b', re.I),
        
        # Beauty
        "cream": re.compile(r'\b(cream|lotion|moisturizer)\b', re.I),
        "serum": re.compile(r'\b(serum)\b', re.I),
        "shampoo": re.compile(r'\b(shampoo)\b', re.I),
        "oil": re.compile(r'\b(oil)\b', re.I),
        " lipstick": re.compile(r'\b(lipstick|lip\s+color)\b', re.I),
        
        # Sports
        "bat": re.compile(r'\b(bat|club|racket)\b', re.I),
        "ball": re.compile(r'\b(ball)\b', re.I),
        "mat": re.compile(r'\b(yoga\s+mat|exercise\s+mat)\b', re.I),
        
        # Books
        "book": re.compile(r'\b(book|novel|paperback|hardcover)\b', re.I),
        
        # Apps & Games
        "app": re.compile(r'\b(app|game|mobile\s+game|android\s+app)\b', re.I),
        "license": re.compile(r'\b(license|licenced|subscription)\b', re.I),
    }
    
    SIZE_TIER_PATTERNS = {
        "small": re.compile(r'\b(compact|mini|small|lite|air)\b', re.I),
        "large": re.compile(r'\b(jumbo|large|big|standard|full|plus)\b', re.I),
    }
    
    def __init__(self, subcats_file: Optional[str] = None):
        """
        Initialize mapper with optional subcategory file.
        
        Args:
            subcats_file: Path to subcats.json (auto-detected if not provided)
        """
        if subcats_file is None:
            # Try common locations
            candidates = [
                Path(__file__).parent / "subcats.json",
                Path.cwd() / "subcats.json",
            ]
            for candidate in candidates:
                if candidate.exists():
                    subcats_file = str(candidate)
                    break
        
        self.subcats_file = subcats_file
        self._subcats_cache: Optional[dict] = None
    
    def _load_subcats(self) -> dict:
        """Load subcategories from JSON file."""
        if self._subcats_cache is not None:
            return self._subcats_cache
        
        if not self.subcats_file or not Path(self.subcats_file).exists():
            return {}
        
        try:
            with open(self.subcats_file) as f:
                data = json.load(f)
            self._subcats_cache = data
            return data
        except Exception as e:
            print(f"[CategoryMapper] Warning: Failed to load {self.subcats_file}: {e}")
            return {}
    
    def map(self, asin: str, title: Optional[str] = None, 
            existing_category: Optional[str] = None) -> dict:
        """
        Determine category hierarchy for an ASIN.
        
        Args:
            asin: Amazon ASIN
            title: Product title (for inference if not already categorized)
            existing_category: Pre-existing category label (from collector)
        
        Returns:
            {
                "category": "Electronics",
                "subcategory": "Headphones", 
                "product_type": "over_ear",
                "confidence": 0.95,
                "source": "title_inference" | "existing" | "subcat_lookup"
            }
        """
        # Strategy 1: Use existing category from collector
        if existing_category:
            parsed = self._parse_category_label(existing_category)
            if parsed:
                return {**parsed, "confidence": 1.0, "source": "existing"}
        
        # Strategy 2: Look up in subcategories file
        if self.subcats_file:
            subcats = self._load_subcats()
            if subcats and "subcategories" in subcats:
                # This would normally match by browsing node slug
                # For now, fall back to title inference
                pass
        
        # Strategy 3: Title-based inference
        if title:
            result = self._infer_from_title(title)
            if result["confidence"] > 0.5:
                return {**result, "source": "title_inference"}
        
        # Fallback: generic classification
        return {
            "category": "General",
            "subcategory": None,
            "product_type": None,
            "confidence": 0.1,
            "source": "fallback"
        }
    
    def _parse_category_label(self, label: str) -> Optional[dict]:
        """Parse a category label like 'Electronics > Headphones'."""
        parts = [p.strip() for p in label.split(">")]
        
        if len(parts) >= 1:
            category = parts[0]
            subcategory = parts[1] if len(parts) > 1 else None
            
            return {
                "category": category,
                "subcategory": subcategory,
                "product_type": None
            }
        
        return None
    
    def _infer_from_title(self, title: str) -> dict:
        """
        Infer category from product title keywords.
        
        Returns mapping with confidence score.
        """
        title_lower = title.lower()
        matches = {}
        
        # Check each pattern - use specific patterns first, generic last
        for attr_name, pattern in sorted(self.PRODUCT_TYPE_PATTERNS.items(), key=lambda x: len(x[0]), reverse=True):
            if pattern.search(title):
                # Extract category context (prioritize specific types)
                if "earbud" in attr_name or "headphone" in attr_name or "camera" in attr_name:
                    cat = "Electronics"
                elif "shirt" in attr_name or "dress" in attr_name or "watch" in attr_name:
                    cat = "Fashion"
                elif "cooker" in attr_name or "pan" in attr_name or "fan" in attr_name:
                    cat = "Home & Kitchen"
                elif "cream" in attr_name or "shampoo" in attr_name or "oil" in attr_name:
                    cat = "Beauty"
                elif "bat" in attr_name or "ball" in attr_name or "mat" in attr_name:
                    cat = "Sports"
                elif "book" in attr_name:
                    cat = "Books"
                elif "app" in attr_name or "license" in attr_name:
                    cat = "Software"
                else:
                    cat = "General"

                matches[attr_name] = {
                    "category": cat,
                    "product_type": attr_name,
                    "score": 0.8 if attr_name not in ["shirt", "pant", "dress"] else 0.6
                }
        
        # Return best match
        if matches:
            best = max(matches.items(), key=lambda x: x[1]["score"])
            return {
                "category": best[1]["category"],
                "subcategory": self._infer_subcategory(best[1]["category"], best[1]["product_type"]),
                "product_type": best[1]["product_type"],
                "confidence": best[1]["score"]
            }
        
        return {
            "category": "General",
            "subcategory": None,
            "product_type": None,
            "confidence": 0.1
        }
    
    def _infer_subcategory(self, category: str, product_type: str) -> Optional[str]:
        """Map product type to subcategory name."""
        mapping = {
            "Electronics": {
                "earbuds": "Headphones",
                "wired_headphones": "Headphones",
                "over_ear": "Headphones",
                "smartphone": "Mobiles & Tablets",
                "tablet": "Mobiles & Tablets",
                "laptop": "Computers & Accessories",
                "charger": "Accessories",
                "cable": "Accessories",
                "camera": "Camera & Photography",
            },
            "Fashion": {
                "shirt": "Men's Clothing",
                "pant": "Men's Clothing",
                "tshirt": "Men's Clothing",
                "dress": "Women's Clothing",
                "kurti": "Women's Clothing",
                "shoe": "Footwear",
                "watch": "Watches",
            },
            "Home & Kitchen": {
                "cooker": "Kitchen",
                "pan": "Kitchen",
                "blade": "Kitchen",
                "fan": "Home Appliances",
            },
            "Beauty": {
                "cream": "Skin Care",
                "serum": "Skin Care",
                "shampoo": "Hair Care",
                "oil": "Hair Care",
                "lipstick": "Makeup",
            },
            "Sports": {
                "bat": "Cricket",
                "ball": "Cricket",
                "mat": "Fitness",
            },
            "Software": {
                "app": "Mobile Apps",
                "game": "Mobile Apps",
            },
        }
        
        cat_mapping = mapping.get(category, {})
        return cat_mapping.get(product_type)
    
    def detect_size_tier(self, title: str) -> Optional[str]:
        """Detect if product is small/large/titanium tier from title."""
        for tier, pattern in self.SIZE_TIER_PATTERNS.items():
            if pattern.search(title):
                return tier
        return None
    
    def detect_brand(self, url_slug: str) -> Optional[str]:
        """Extract brand from Amazon URL slug."""
        # Pattern: /Brand-Product-Name/dp/
        match = re.search(r'/([A-Z][a-zA-Z]*(?:-[A-Z][a-zA-Z]*)*)/dp/', url_slug)
        if match:
            raw = match.group(1)
            # Take first capitalized word(s) before hyphens
            parts = raw.split('-')
            brand_words = []
            SKIP = {'the', 'and', 'for', 'with', 'by', 'in', 'on', 'at', 'to', 'a', 'an'}
            
            for w in parts[:3]:
                if w[0].isupper() and w.isalpha() and len(w) >= 2 and w.lower() not in SKIP:
                    brand_words.append(w)
                else:
                    break
            
            return ' '.join(brand_words) if brand_words else None
        return None


def map_asin_to_schema(asin: str, title: str, 
                       existing_category: str = None) -> dict:
    """
    Convenience function to get full schema for an ASIN.
    
    Returns:
        {
            "schema": {attr_name: DataStatus.MISSING},
            "category_info": {...},
            "applicable_attributes": [...]
        }
    """
    mapper = CategoryMapper()
    registry = default_registry
    
    # Map to category hierarchy
    category_info = mapper.map(asin, title=title, existing_category=existing_category)
    
    # Get applicable attributes
    applicable = registry.get_applicable_attributes(
        category=category_info["category"],
        subcategory=category_info["subcategory"],
        product_type=category_info["product_type"]
    )
    
    # Build schema
    schema = {attr.name: DataStatus.MISSING.value for attr in applicable}
    schema["asin"] = DataStatus.MISSING.value
    schema["title"] = DataStatus.MISSING.value
    schema["collected_at"] = DataStatus.MISSING.value
    
    return {
        "schema": schema,
        "category_info": category_info,
        "applicable_attributes": [attr.name for attr in applicable],
        "total_fields": len(applicable)
    }


# Singleton instance
_default_mapper = CategoryMapper()

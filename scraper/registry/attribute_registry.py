"""
Master Attribute Registry — central schema for all ScoutVeda scrapers.

Maintains a hierarchy of attributes:
  Universal (all products)
  → Category (e.g., Electronics)
    → Subcategory (e.g., Headphones)
      → Product Type (e.g., Wireless Earbuds)
        → Dynamic (discovered at runtime)

Each attribute tracks:
  - name: human-readable field name
  - data_type: string, number, boolean, url, etc.
  - data_status: COLLECTED, MISSING, NOT_APPLICABLE, DERIVED, ESTIMATED, FAILED
  - applicability: which categories/subcats/product_types it applies to
  - source: where the data comes from (list_page, product_page, api, derived)
  - tier: collection priority (1=essential, 2=important, 3=advanced)
"""

from __future__ import annotations

import json
import os
import re
import threading
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Optional

# --- Data Status Enum ---

class DataStatus(str, Enum):
    """Status of a data point for a given ASIN."""
    COLLECTED = "COLLECTED"
    MISSING = "MISSING"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    NOT_PUBLICLY_AVAILABLE = "NOT_PUBLICLY_AVAILABLE"
    REQUIRES_EXTERNAL_SOURCE = "REQUIRES_EXTERNAL_SOURCE"
    REQUIRES_SELLER_ACCOUNT = "REQUIRES_SELLER_ACCOUNT"
    DERIVED = "DERIVED"
    ESTIMATED = "ESTIMATED"
    FAILED = "FAILED"


# --- Attribute Data Classes ---

@dataclass
class Attribute:
    """Defines a single data point that can be collected."""
    name: str
    data_type: str  # "string", "number", "boolean", "url", "datetime"
    description: str
    tier: int  # 1=essential, 2=important, 3=advanced
    source: str  # "list_page", "product_page", "api", "derived", "external"
    
    # Applicability (which categories use this)
    universal: bool = False
    categories: list[str] = field(default_factory=list)
    subcategories: list[str] = field(default_factory=list)
    product_types: list[str] = field(default_factory=list)
    
    # Dynamic discovery
    is_dynamic: bool = False
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    # Validation rules
    required: bool = False
    validators: list[str] = field(default_factory=list)
    
    def applies_to(self, category: str, subcategory: Optional[str] = None, 
                   product_type: Optional[str] = None) -> bool:
        """Check if this attribute applies to the given category hierarchy."""
        if self.universal:
            return True
        
        # Check category match
        if not any(cat.lower() in category.lower() for cat in self.categories):
            return False
        
        # Check subcategory if specified
        if subcategory and self.subcategories:
            if not any(sub.lower() in subcategory.lower() for sub in self.subcategories):
                return False
        
        # Check product type if specified
        if product_type and self.product_types:
            if not any(pt.lower() in product_type.lower() for pt in self.product_types):
                return False
        
        return True


# --- Registry Implementation ---

class AttributeRegistry:
    """
    Centralized attribute registry for all ScoutVeda scrapers.
    
    Thread-safe singleton that loads from JSON file and supports
    dynamic attribute discovery.
    """
    
    _instance: Optional['AttributeRegistry'] = None
    _lock = threading.Lock()
    
    # Known category hierarchies (Amazon India browse nodes)
    CATEGORY_HIERARCHY = {
        "electronics": {
            "name": "Electronics",
            "subcategories": {
                "headphones": {"name": "Headphones", "product_types": ["earbuds", "wired_headphones", "wireless_earbuds", "over_ear"]},
                "computers": {"name": "Computers & Accessories", "product_types": ["laptop", "desktop", "tablet", "accessories"]},
                "mobiles": {"name": "Mobiles & Tablets", "product_types": ["smartphone", "feature_phone", "tablet", "power_bank", "charger", "cable", "cover", "case"]},
                "camera": {"name": "Camera & Photography", "product_types": ["dslr", "mirrorless", "action_camera", "lens", "tripod"]},
                "tv_audio": {"name": "Home Theatre, TV & Video", "product_types": ["television", "soundbar", "home_theatre"]},
            }
        },
        "fashion": {
            "name": "Clothing & Accessories",
            "subcategories": {
                "mens_clothing": {"name": "Men's Clothing", "product_types": ["shirt", "pant", "tshirt", "kurta", "jacket", "jeans", "shorts"]},
                "womens_clothing": {"name": "Women's Clothing", "product_types": ["dress", "kurti", "top", "jeans", "skirt", "saree", "salwar"]},
                "footwear": {"name": "Footwear", "product_types": ["sneaker", "formal_shoe", "sandals", "sandal", "flip_flop"]},
                "watches": {"name": "Watches", "product_types": ["analog_watch", "digital_watch", "smart_watch"]},
            }
        },
        "home_kitchen": {
            "name": "Home & Kitchen",
            "subcategories": {
                "kitchen": {"name": "Kitchen", "product_types": ["cooker", "pan", "pot", "blade", "mixer", "grinder"]},
                "furniture": {"name": "Furniture", "product_types": ["sofa", "bed", "table", "chair", "wardrobe"]},
                "decor": {"name": "Home Decor", "product_types": ["pillow", "blanket", "curtain", "rack"]},
            }
        },
        "beauty": {
            "name": "Beauty & Personal Care",
            "subcategories": {
                "skin_care": {"name": "Skin Care", "product_types": ["cream", "serum", "moisturizer", "facewash", "sunscreen"]},
                "hair_care": {"name": "Hair Care", "product_types": ["shampoo", "conditioner", "oil", "serum", "color"]},
                "makeup": {"name": "Makeup", "product_types": ["lipstick", "foundation", "mascara", "eyeshadow"]},
            }
        },
        "sports": {
            "name": "Sports, Fitness & Outdoor",
            "subcategories": {
                "fitness": {"name": "Fitness", "product_types": ["dumbbell", "yoga_mat", "resistance_band", "gym_bag"]},
                "cricket": {"name": "Cricket", "product_types": ["bat", "ball", "pad", "glove", "helmet"]},
                "football": {"name": "Football", "product_types": ["ball", "boot", "goal"]},
            }
        },
        "toys": {
            "name": "Toys & Games",
            "subcategories": {
                "kids_toys": {"name": "Kids Toys", "product_types": ["action_figure", "doll", "vehicle", "puzzle", "building_block"]},
                "board_games": {"name": "Board Games", "product_types": ["card_game", "board_game", "dice"]},
            }
        },
        "books": {
            "name": "Books",
            "subcategories": {
                "fiction": {"name": "Fiction", "product_types": ["novel", "short_story", "anthology"]},
                "non_fiction": {"name": "Non-Fiction", "product_types": ["biography", "self_help", "business"]},
            }
        },
        "grocery": {
            "name": "Grocery & Gourmet Foods",
            "subcategories": {
                "food": {"name": "Food", "product_types": ["snack", "chocolate", "biscuit", "tea", "coffee"]},
                "personal_care_food": {"name": "Personal Care & Food", "product_types": ["soap", "toothpaste", "sanitary"]},
            }
        },
        "health": {
            "name": "Health & Personal Care",
            "subcategories": {
                "medication": {"name": "Medicine", "product_types": ["tablet", "syrup", "capsule", "inhaler"]},
                "supplements": {"name": "Vitamins & Supplements", "product_types": ["powder", "tablet", "capsule", "liquid"]},
            }
        },
        "automotive": {
            "name": "Car & Vehicle Electronics",
            "subcategories": {
                "car_electronics": {"name": "Car Electronics", "product_types": ["charger", "holder", "camera", "locator"]},
                "accessories": {"name": "Accessories", "product_types": ["mat", "cover", "seat_cover"]},
            }
        },
        "baby": {
            "name": "Baby Products",
            "subcategories": {
                "feeding": {"name": "Feeding", "product_types": ["bottle", "sipper", "spoon"]},
                "gear": {"name": "Gear", "product_types": ["stroller", "carrier", "pram"]},
                "safety": {"name": "Safety", "product_types": ["gate", "lock", "outlet_cover"]},
            }
        },
        "pet": {
            "name": "Pet Supplies",
            "subcategories": {
                "dog": {"name": "Dog", "product_types": ["food", "toy", "bed", "collar"]},
                "cat": {"name": "Cat", "product_types": ["food", "toy", "litter"]},
            }
        },
        "office": {
            "name": "Stationery & Office",
            "subcategories": {
                "writing": {"name": "Writing", "product_types": ["pen", "pencil", "notebook"]},
                "desk": {"name": "Desk Accessories", "product_types": ["organizer", "stand", "lamp"]},
            }
        },
    }
    
    # Master attribute definitions grouped by tier
    UNIVERSAL_ATTRIBUTES: list[Attribute] = [
        # Tier 1: Core identification
        Attribute(name="asin", data_type="string", description="Amazon Standard Identification Number", 
                  tier=1, source="list_page", universal=True, required=True),
        Attribute(name="title", data_type="string", description="Product title/name", 
                  tier=1, source="list_page", universal=True, required=True),
        Attribute(name="brand", data_type="string", description="Brand name", 
                  tier=1, source="list_page", universal=True),
        Attribute(name="price", data_type="number", description="Current selling price in INR", 
                  tier=1, source="list_page", universal=True, required=True),
        Attribute(name="mrp", data_type="number", description="Maximum Retail Price", 
                  tier=2, source="list_page", universal=True),
        Attribute(name="discount_pct", data_type="number", description="Discount percentage", 
                  tier=2, source="derived", universal=True, required=False),
        Attribute(name="rating", data_type="number", description="Average customer rating", 
                  tier=1, source="list_page", universal=True, required=True),
        Attribute(name="review_count", data_type="number", description="Total number of ratings", 
                  tier=1, source="list_page", universal=True, required=True),
        Attribute(name="rank", data_type="number", description="Best seller rank position", 
                  tier=1, source="list_page", universal=True, required=True),
        Attribute(name="image_url", data_type="url", description="Main product image URL", 
                  tier=2, source="list_page", universal=True),
        Attribute(name="category", data_type="string", description="Amazon category path", 
                  tier=1, source="list_page", universal=True, required=True),
        Attribute(name="list_type", data_type="string", description="Type of list (bestsellers/new-releases/etc)", 
                  tier=1, source="list_page", universal=True, required=True),
        Attribute(name="collected_at", data_type="datetime", description="Timestamp when data was collected", 
                  tier=1, source="system", universal=True, required=True),
        Attribute(name="asin_url", data_type="url", description="Amazon product page URL", 
                  tier=2, source="derived", universal=True),
        
        # Tier 2: Product details
        Attribute(name="availability_text", data_type="string", description="Stock availability text", 
                  tier=2, source="product_page", universal=True),
        Attribute(name="in_stock", data_type="boolean", description="Whether item is in stock", 
                  tier=2, source="product_page", universal=True),
        Attribute(name="seller", data_type="string", description="Seller name", 
                  tier=2, source="product_page", universal=True),
        Attribute(name="fulfillment", data_type="string", description="Fulfillment method (FBA/FBM)", 
                  tier=2, source="product_page", universal=True),
        
        # Tier 2: Physical specs
        Attribute(name="dimensions", data_type="string", description="Product dimensions", 
                  tier=2, source="product_page", universal=True),
        Attribute(name="weight", data_type="string", description="Item weight", 
                  tier=2, source="product_page", universal=True),
        Attribute(name="package_dimensions", data_type="string", description="Package dimensions", 
                  tier=3, source="product_page", universal=True),
        Attribute(name="package_weight", data_type="string", description="Package weight", 
                  tier=3, source="product_page", universal=True),
        
        # Tier 3: Extended info
        Attribute(name="bsr_rank", data_type="number", description="Best Seller Rank", 
                  tier=2, source="product_page", universal=True),
        Attribute(name="bsr_category", data_type="string", description="BSR category", 
                  tier=2, source="product_page", universal=True),
        Attribute(name="material", data_type="string", description="Material composition", 
                  tier=3, source="product_page", universal=True),
        Attribute(name="warranty", data_type="string", description="Warranty information", 
                  tier=3, source="product_page", universal=True),
        Attribute(name="country_of_origin", data_type="string", description="Country of origin", 
                  tier=3, source="product_page", universal=True),
        Attribute(name="model_number", data_type="string", description="Manufacturer model number", 
                  tier=3, source="product_page", universal=True),
        Attribute(name="item_part_number", data_type="string", description="Amazon part number", 
                  tier=3, source="product_page", universal=True),
    ]
    
    # Category-specific attributes
    CATEGORY_ATTRIBUTES: dict[str, list[Attribute]] = {
        "electronics": [
            Attribute(name="ram", data_type="string", description="RAM size", 
                      tier=2, source="product_page", categories=["Electronics"]),
            Attribute(name="storage", data_type="string", description="Storage capacity", 
                      tier=2, source="product_page", categories=["Electronics"]),
            Attribute(name="processor", data_type="string", description="Processor/CPU model", 
                      tier=2, source="product_page", categories=["Electronics"]),
            Attribute(name="display_size", data_type="string", description="Display size in inches", 
                      tier=2, source="product_page", categories=["Electronics"]),
            Attribute(name="battery_capacity", data_type="string", description="Battery capacity in mAh", 
                      tier=2, source="product_page", categories=["Electronics"]),
            Attribute(name="connectivity", data_type="string", description="Connectivity options", 
                      tier=2, source="product_page", categories=["Electronics"]),
            Attribute(name="color", data_type="string", description="Product color", 
                      tier=2, source="product_page", categories=["Electronics"]),
            Attribute(name="special_features", data_type="string", description="Special features", 
                      tier=3, source="product_page", categories=["Electronics"]),
        ],
        "fashion": [
            Attribute(name="size", data_type="string", description="Size variant", 
                      tier=2, source="product_page", categories=["Fashion"]),
            Attribute(name="fabric", data_type="string", description="Fabric/material type", 
                      tier=2, source="product_page", categories=["Fashion"]),
            Attribute(name="pattern", data_type="string", description="Pattern/print type", 
                      tier=2, source="product_page", categories=["Fashion"]),
            Attribute(name="closure_type", data_type="string", description="Closure mechanism", 
                      tier=3, source="product_page", categories=["Fashion"]),
            Attribute(name="care_instructions", data_type="string", description="Care directions", 
                      tier=3, source="product_page", categories=["Fashion"]),
        ],
        "home_kitchen": [
            Attribute(name="capacity", data_type="string", description="Capacity/volume", 
                      tier=2, source="product_page", categories=["Home & Kitchen"]),
            Attribute(name="material", data_type="string", description="Construction material", 
                      tier=2, source="product_page", categories=["Home & Kitchen"]),
            Attribute(name="color_options", data_type="string", description="Available colors", 
                      tier=2, source="product_page", categories=["Home & Kitchen"]),
            Attribute(name="warranty", data_type="string", description="Manufacturer warranty", 
                      tier=3, source="product_page", categories=["Home & Kitchen"]),
        ],
        "beauty": [
            Attribute(name="volume", data_type="string", description="Product volume/weight", 
                      tier=2, source="product_page", categories=["Beauty"]),
            Attribute(name="ingredients", data_type="string", description="Key ingredients", 
                      tier=2, source="product_page", categories=["Beauty"]),
            Attribute(name="skin_type", data_type="string", description="Suitable skin type", 
                      tier=2, source="product_page", categories=["Beauty"]),
            Attribute(name="shelf_life", data_type="string", description="Shelf life/expiry", 
                      tier=3, source="product_page", categories=["Beauty"]),
        ],
        "sports": [
            Attribute(name="sport_type", data_type="string", description="Target sport/activity", 
                      tier=2, source="product_page", categories=["Sports"]),
            Attribute(name="age_group", data_type="string", description="Recommended age group", 
                      tier=2, source="product_page", categories=["Sports"]),
            Attribute(name="material", data_type="string", description="Construction material", 
                      tier=2, source="product_page", categories=["Sports"]),
            Attribute(name="weight_spec", data_type="string", description="Product weight spec", 
                      tier=2, source="product_page", categories=["Sports"]),
        ],
    }
    
    def __init__(self, registry_file: Optional[str] = None):
        """Initialize the registry.
        
        Args:
            registry_file: Path to JSON file for persistent storage. 
                          Defaults to scraper/attribute_registry.json
        """
        if registry_file is None:
            registry_file = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "attribute_registry.json"
            )
        
        self._registry_file = Path(registry_file)
        self._attributes: dict[str, Attribute] = {}
        self._asins: dict[str, dict[str, Any]] = {}  # asin -> {attr_name: {value, status}}
        self._lock = threading.RLock()
        self._load_or_create()
    
    def _load_or_create(self):
        """Load registry from file or create fresh."""
        if self._registry_file.exists():
            self._load_from_disk()
        else:
            self._create_baseline()
            self._save_to_disk()
    
    def _create_baseline(self):
        """Create baseline registry from hardcoded definitions."""
        for attr in self.UNIVERSAL_ATTRIBUTES:
            self._attributes[attr.name] = attr
        
        for category, attrs in self.CATEGORY_ATTRIBUTES.items():
            for attr in attrs:
                self._attributes[attr.name] = attr
    
    def _load_from_disk(self):
        """Load registry from JSON file."""
        try:
            with open(self._registry_file) as f:
                data = json.load(f)
            
            # Restore universal attributes
            for attr_dict in data.get("universal_attributes", []):
                attr = Attribute(**attr_dict)
                self._attributes[attr.name] = attr
            
            # Restore category attributes
            for cat_attrs in data.get("category_attributes", {}).values():
                for attr_dict in cat_attrs:
                    attr = Attribute(**attr_dict)
                    self._attributes[attr.name] = attr
            
            # Restore dynamic attributes
            for attr_dict in data.get("dynamic_attributes", []):
                attr = Attribute(**attr_dict)
                self._attributes[attr.name] = attr
                
        except Exception as e:
            print(f"[Registry] Warning: Failed to load {self._registry_file}: {e}")
            self._create_baseline()
    
    def _save_to_disk(self):
        """Persist registry to JSON file."""
        try:
            data = {
                "universal_attributes": [asdict(a) for a in self._attributes.values() if a.universal],
                "category_attributes": {},
                "dynamic_attributes": [],
                "last_updated": datetime.now(timezone.utc).isoformat(),
            }
            
            # Group category-specific attributes
            for name, attr in self._attributes.items():
                if attr.universal:
                    continue
                if attr.is_dynamic:
                    data["dynamic_attributes"].append(asdict(attr))
                elif attr.categories:
                    for cat in attr.categories:
                        if cat not in data["category_attributes"]:
                            data["category_attributes"][cat] = []
                        data["category_attributes"][cat].append(asdict(attr))
            
            self._registry_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self._registry_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"[Registry] Warning: Failed to save {self._registry_file}: {e}")
    
    def register_attribute(self, attribute: Attribute):
        """Register a new attribute (for dynamic discovery)."""
        with self._lock:
            self._attributes[attribute.name] = attribute
            self._save_to_disk()
            print(f"[Registry] Registered new attribute: {attribute.name} ({attribute.data_type})")
    
    def get_attribute(self, name: str) -> Optional[Attribute]:
        """Get an attribute by name."""
        return self._attributes.get(name)
    
    def get_applicable_attributes(self, category: str, 
                                   subcategory: Optional[str] = None,
                                   product_type: Optional[str] = None,
                                   tier_limit: Optional[int] = None) -> list[Attribute]:
        """
        Get all attributes applicable to the given category hierarchy.
        
        Args:
            category: Main category (e.g., "Electronics")
            subcategory: Subcategory (e.g., "Headphones")
            product_type: Product type (e.g., "earbuds")
            tier_limit: Only return attributes up to this tier
        
        Returns:
            List of applicable attributes sorted by tier
        """
        applicable = []
        
        with self._lock:
            for attr in self._attributes.values():
                # Apply tier filter if specified
                if tier_limit and attr.tier > tier_limit:
                    continue
                
                # Check if attribute applies
                if attr.applies_to(category, subcategory, product_type):
                    applicable.append(attr)
        
        # Sort by tier (essential first), then alphabetically
        applicable.sort(key=lambda a: (a.tier, a.name))
        return applicable
    
    def get_schema_for_asin(self, asin: str, category: str,
                            subcategory: Optional[str] = None,
                            product_type: Optional[str] = None) -> dict[str, str]:
        """
        Get the expected schema for an ASIN with all attributes pre-initialized.
        
        Returns dict: {attr_name: DataStatus.MISSING}
        """
        attrs = self.get_applicable_attributes(category, subcategory, product_type)
        schema = {attr.name: DataStatus.MISSING.value for attr in attrs}
        
        # Add core identification fields even if not in tier list
        for core_field in ["asin", "title", "price", "rating", "review_count", 
                           "rank", "category", "list_type", "collected_at"]:
            if core_field not in schema:
                schema[core_field] = DataStatus.MISSING.value
        
        return schema
    
    def record_data(self, asin: str, attr_name: str, value: Any, 
                    status: DataStatus = DataStatus.COLLECTED):
        """Record collected data for an ASIN."""
        with self._lock:
            if asin not in self._asins:
                self._asins[asin] = {}
            
            if attr_name not in self._asins[asin]:
                self._asins[asin][attr_name] = {
                    "value": value,
                    "status": status.value,
                    "recorded_at": datetime.now(timezone.utc).isoformat()
                }
            else:
                self._asins[asin][attr_name]["value"] = value
                self._asins[asin][attr_name]["status"] = status.value
    
    def get_recorded_data(self, asin: str) -> dict[str, dict]:
        """Get all recorded data for an ASIN."""
        return self._asins.get(asin, {})
    
    def get_data_status(self, asin: str, attr_name: str) -> str:
        """Get the data status for a specific ASIN-attribute pair."""
        records = self._asins.get(asin, {})
        record = records.get(attr_name, {})
        return record.get("status", DataStatus.MISSING.value)
    
    def compute_completeness_score(self, asin: str, 
                                    category: str,
                                    subcategory: Optional[str] = None,
                                    product_type: Optional[str] = None) -> dict:
        """
        Compute completeness score for an ASIN's data.
        
        Returns:
            {
                "total_fields": N,
                "collected_fields": N,
                "missing_fields": N,
                "not_applicable_fields": N,
                "score": 0.0-1.0
            }
        """
        schema = self.get_schema_for_asin(asin, category, subcategory, product_type)
        records = self.get_recorded_data(asin)
        
        total = len(schema)
        collected = sum(1 for attr in schema if records.get(attr, {}).get("status") == DataStatus.COLLECTED.value)
        missing = sum(1 for attr in schema if records.get(attr, {}).get("status") == DataStatus.MISSING.value)
        not_applicable = sum(1 for attr in schema if records.get(attr, {}).get("status") == DataStatus.NOT_APPLICABLE.value)
        
        return {
            "total_fields": total,
            "collected_fields": collected,
            "missing_fields": missing,
            "not_applicable_fields": not_applicable,
            "score": round(collected / total, 2) if total > 0 else 0.0
        }
    
    @classmethod
    def instance(cls) -> 'AttributeRegistry':
        """Get singleton instance of the registry."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    def reset(self):
        """Reset registry to baseline (for testing)."""
        with self._lock:
            self._attributes = {}
            self._asins = {}
            self._create_baseline()
            self._save_to_disk()
            AttributeRegistry._instance = None


# Export singleton for convenience
default_registry = AttributeRegistry.instance()

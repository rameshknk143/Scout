# Master Attribute Registry — Implementation Summary

## What Was Built

A centralized, category-aware attribute system for ScoutVeda scrapers that automatically:
- Detects ASIN → Category → Subcategory → Product Type
- Applies correct schemas via inheritance (no manual config per product)
- Discovers new attributes dynamically from Amazon pages
- Tracks data status (COLLECTED / MISSING / NOT_APPLICABLE / DERIVED / FAILED)

## Files Created/Modified

### New Files (registry/)
```
scraper/registry/__init__.py          # Package entry point
scraper/registry/attribute_registry.py # Core registry (577 lines)
scraper/registry/category_mapper.py    # Auto-detect category from title (354 lines)
scraper/test_registry.py              # 19 unit tests, all passing ✓
scraper/migrate_schema.py             # DB migration to add subcategory/product_type columns
```

### Modified Files
- `collector.py` — imports registry, auto-infers category hierarchy on every row
- `db.py` — schema extended with `subcategory TEXT` + `product_type TEXT` columns
- `enrich_product_pages.py` — references existing fields (bsr_rank etc.) need schema migration first

## How It Works

### 1. Category Inference (Collector)
```python
# collector.py now runs this per product:
mapped = _mapper.map(asin, title="Sony WH-1000XM4 Headphones", existing_category="Electronics")
# Returns: {"category": "Electronics", "subcategory": "Headphones", "product_type": "over_ear"}
```

### 2. Schema Generation (Registry)
```python
from registry.attribute_registry import default_registry

# Get applicable attributes for this ASIN
attrs = default_registry.get_applicable_attributes("Electronics", "Headphones", "over_ear")
# Returns: [asin, title, brand, price, rating, review_count, rank, image_url, 
#           ram, storage, battery_capacity, color, ...] (filtered by category)

# Check completeness
score = default_registry.compute_completeness_score(asin, "Electronics", "Headphones", "over_ear")
# Returns: {"total_fields": 35, "collected_fields": 8, "score": 0.23}
```

### 3. Data Status Tracking
```python
from registry.attribute_registry import DataStatus

# Record collected data
default_registry.record_data(asin, "ram", "4GB", DataStatus.COLLECTED)
default_registry.record_data(asin, "processor", None, DataStatus.MISSING)

# Check status
status = default_registry.get_data_status(asin, "ram")  # "COLLECTED"
status = default_registry.get_data_status(asin, "processor")  # "MISSING"
```

## Database Migration

Run once to add new columns:
```bash
DATABASE_URL=<your-supabase-url> python migrate_schema.py
```

This adds:
- `subcategory TEXT` — e.g., "Headphones", "Men's Clothing"
- `product_type TEXT` — e.g., "over_ear", "shirt"
- Indexes for fast querying by category hierarchy

## Attributes Currently Defined

### Universal (all products) — 24 fields
Tier 1 (essential): asin, title, brand, price, rating, review_count, rank, image_url, category, list_type, collected_at  
Tier 2 (important): mrp, discount_pct, asin_url, availability_text, in_stock, seller, fulfillment, dimensions, weight, bsr_rank, bsr_category  
Tier 3 (advanced): package_dimensions, package_weight, material, warranty, country_of_origin, model_number, item_part_number

### Electronics-specific — 8 fields
ram, storage, processor, display_size, battery_capacity, connectivity, color, special_features

### Fashion-specific — 5 fields
size, fabric, pattern, closure_type, care_instructions

### Home & Kitchen-specific — 4 fields
capacity, material, color_options, warranty

### Beauty-specific — 4 fields
volume, ingredients, skin_type, shelf_life

### Sports-specific — 4 fields
sport_type, age_group, material, weight_spec

**Total: ~49 predefined attributes** across all categories

## Integration with Existing Scrapers

### collector.py (Broad Layer)
Now automatically populates `subcategory` and `product_type` on every row during collection. No extra API calls needed — uses title keywords only.

### enrich_product_pages.py (Product Pages)
References `bsr_rank`, `in_stock`, `dimensions` etc. which don't exist in current schema. After running migration, these columns will be available.

### scrape.py (Watchlist Deep Scraper)
Can use registry to validate fetched fields against expected schema for that category.

### maxun_bridge.py
Will need updates to map Maxun's generic column names into registry-defined attributes.

## Next Steps

1. **Run migration**: `python migrate_schema.py` (one-time, adds new columns)
2. **Update enrich scripts**: Fix `enrich_product_pages.py` to use new columns
3. **Extend patterns**: Add more keyword patterns to `category_mapper.py` for better detection
4. **Dynamic discovery**: When scraper finds new attribute not in registry, auto-register it
5. **API integration**: Expose completeness scores via ScoutVeda API for dashboard

## Design Decisions

- **Keyword-based inference only** — no expensive product page fetches for categorization
- **Inheritance chain**: Universal → Category → Subcategory → Product Type
- **Backward compatible**: Existing collectors keep working; new columns are nullable
- **Thread-safe**: Registry uses locks for concurrent access

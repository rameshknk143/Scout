"""
Master Attribute Registry for ScoutVeda.

Centralized schema system that automatically assigns relevant data points
to every ASIN based on its category hierarchy. Every scraper reads from and
contributes to this single source of truth.

Usage:
    from registry.attribute_registry import AttributeRegistry
    
    registry = AttributeRegistry()
    
    # Get applicable attributes for a product
    attrs = registry.get_applicable_attributes("Electronics > Headphones")
    
    # Check data status for an ASIN
    status = registry.get_data_status(asin, "brand")
    
    # Register a newly discovered attribute
    registry.register_attribute(Attribute(
        name="Driver Size",
        category="Electronics",
        subcategory="Headphones",
        is_dynamic=True
    ))
"""

from .attribute_registry import Attribute, AttributeRegistry, DataStatus
from .category_mapper import CategoryMapper

__all__ = [
    "Attribute",
    "AttributeRegistry", 
    "DataStatus",
    "CategoryMapper",
]

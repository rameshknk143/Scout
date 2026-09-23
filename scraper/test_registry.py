"""
Test suite for Master Attribute Registry.
"""

import unittest
import os
import sys
import json
import tempfile
from pathlib import Path
from datetime import datetime, timezone

# Add scraper directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from registry.attribute_registry import Attribute, AttributeRegistry, DataStatus
from registry.category_mapper import CategoryMapper


class TestAttribute(unittest.TestCase):
    """Test Attribute class."""
    
    def test_universal_attribute(self):
        attr = Attribute(
            name="asin",
            data_type="string",
            description="Amazon ID",
            tier=1,
            source="list_page",
            universal=True
        )
        
        self.assertTrue(attr.universal)
        self.assertEqual(attr.name, "asin")
        self.assertEqual(attr.tier, 1)
    
    def test_category_attribute(self):
        attr = Attribute(
            name="ram",
            data_type="string",
            description="RAM size",
            tier=2,
            source="product_page",
            categories=["Electronics"]
        )
        
        self.assertFalse(attr.universal)
        self.assertIn("Electronics", attr.categories)
    
    def test_applies_to_universal(self):
        attr = Attribute(
            name="price",
            data_type="number",
            description="Price",
            tier=1,
            source="list_page",
            universal=True
        )
        
        self.assertTrue(attr.applies_to("Electronics"))
        self.assertTrue(attr.applies_to("Fashion"))
        self.assertTrue(attr.applies_to("Any Category"))
    
    def test_applies_to_category(self):
        attr = Attribute(
            name="ram",
            data_type="string",
            description="RAM",
            tier=2,
            source="product_page",
            categories=["Electronics"]
        )
        
        self.assertTrue(attr.applies_to("Electronics"))
        self.assertFalse(attr.applies_to("Fashion"))
    
    def test_applies_to_subcategory(self):
        attr = Attribute(
            name="driver_size",
            data_type="string",
            description="Driver size",
            tier=2,
            source="product_page",
            categories=["Electronics"],
            subcategories=["Headphones"]
        )
        
        self.assertTrue(attr.applies_to("Electronics", "Headphones"))
        self.assertFalse(attr.applies_to("Electronics", "Computers"))


class TestAttributeRegistry(unittest.TestCase):
    """Test AttributeRegistry class."""
    
    def setUp(self):
        """Create a fresh registry for each test."""
        self.registry = AttributeRegistry()
        self.registry.reset()
    
    def tearDown(self):
        """Clean up after each test."""
        # Reset singleton
        AttributeRegistry._instance = None
    
    def test_get_applicable_attributes(self):
        """Test getting attributes for a category."""
        attrs = self.registry.get_applicable_attributes("Electronics")
        
        # Should include universal attributes
        attr_names = [a.name for a in attrs]
        self.assertIn("asin", attr_names)
        self.assertIn("title", attr_names)
        self.assertIn("price", attr_names)
        
        # Should include Electronics-specific attributes
        self.assertIn("ram", attr_names)
        self.assertIn("processor", attr_names)
    
    def test_get_applicable_with_subcategory(self):
        """Test attribute filtering by subcategory."""
        attrs = self.registry.get_applicable_attributes(
            "Electronics", 
            subcategory="Headphones"
        )
        
        attr_names = [a.name for a in attrs]
        # Headphones should have specific attributes
        # (in a real implementation, we'd define these)
        self.assertIsInstance(attrs, list)
        self.assertGreater(len(attrs), 0)
    
    def test_register_dynamic_attribute(self):
        """Test registering a new attribute."""
        attr = Attribute(
            name="npu_top_s",
            data_type="number",
            description="NPU performance in TOPS",
            tier=2,
            source="product_page",
            categories=["Electronics"],
            is_dynamic=True
        )
        
        self.registry.register_attribute(attr)
        
        retrieved = self.registry.get_attribute("npu_top_s")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.name, "npu_top_s")
    
    def test_record_and_retrieve_data(self):
        """Test recording and retrieving data for an ASIN."""
        # Use local registry, not singleton
        reg = AttributeRegistry()
        reg.reset()
        asin = "B09V3KXJPB"

        reg.record_data(asin, "asin", "B09V3KXJPB", DataStatus.COLLECTED)
        reg.record_data(asin, "title", "Sony WH-1000XM4", DataStatus.COLLECTED)
        reg.record_data(asin, "price", 19990.0, DataStatus.COLLECTED)
        reg.record_data(asin, "ram", None, DataStatus.MISSING)

        records = reg.get_recorded_data(asin)

        self.assertEqual(records["asin"]["value"], "B09V3KXJPB")
        self.assertEqual(records["price"]["value"], 19990.0)
        self.assertEqual(records["ram"]["status"], DataStatus.MISSING.value)
    
    def test_get_data_status(self):
        """Test getting data status."""
        # Use local registry, not singleton
        reg = AttributeRegistry()
        reg.reset()
        asin = "B09V3KXJPB"

        reg.record_data(asin, "brand", "Sony", DataStatus.COLLECTED)
        reg.record_data(asin, "material", None, DataStatus.MISSING)

        self.assertEqual(
            reg.get_data_status(asin, "brand"),
            DataStatus.COLLECTED.value
        )
        self.assertEqual(
            reg.get_data_status(asin, "material"),
            DataStatus.MISSING.value
        )
    
    def test_compute_completeness(self):
        """Test completeness score calculation."""
        asin = "B09V3KXJPB"
        category = "Electronics"
        
        # Record some data
        self.registry.record_data(asin, "asin", "B09V3KXJPB", DataStatus.COLLECTED)
        self.registry.record_data(asin, "title", "Test", DataStatus.COLLECTED)
        self.registry.record_data(asin, "price", 1000.0, DataStatus.COLLECTED)
        # Leave others as MISSING (default)
        
        result = self.registry.compute_completeness_score(asin, category)
        
        self.assertIn("total_fields", result)
        self.assertIn("collected_fields", result)
        self.assertIn("score", result)
        self.assertGreater(result["score"], 0.0)
        self.assertLessEqual(result["score"], 1.0)
    
    def test_persistence(self):
        """Test that registry persists to disk."""
        # Register a dynamic attribute
        attr = Attribute(
            name="test_attribute",
            data_type="string",
            description="Test",
            tier=2,
            source="product_page",
            categories=["Electronics"],
            is_dynamic=True
        )
        
        self.registry.register_attribute(attr)
        
        # Create new registry instance pointing to same file
        new_registry = AttributeRegistry(
            registry_file=str(self.registry._registry_file)
        )
        
        # Should be able to retrieve it
        retrieved = new_registry.get_attribute("test_attribute")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.name, "test_attribute")


class TestCategoryMapper(unittest.TestCase):
    """Test CategoryMapper class."""
    
    def setUp(self):
        self.mapper = CategoryMapper()
    
    def test_infer_from_title_headphones(self):
        """Test inference for headphones."""
        result = self.mapper._infer_from_title(
            "Sony WH-1000XM4 Wireless Over-Ear Noise Cancelling Headphones"
        )

        # Should detect Electronics category with headphones product type
        self.assertEqual(result["category"], "Electronics")
        self.assertIn(result["product_type"], ["over_ear", "headphone"])
        self.assertGreaterEqual(result["confidence"], 0.8)
    
    def test_infer_from_title_earbuds(self):
        """Test inference for earbuds."""
        result = self.mapper._infer_from_title(
            "boAt Airdopes 141 TWS Earbuds with BEAST Mode"
        )
        
        self.assertEqual(result["category"], "Electronics")
        self.assertEqual(result["product_type"], "earbuds")
    
    def test_infer_from_title_shirt(self):
        """Test inference for shirt."""
        result = self.mapper._infer_from_title(
            "Allen Solly Men's Slim Fit Formal Shirt"
        )
        
        self.assertEqual(result["category"], "Fashion")
        self.assertEqual(result["product_type"], "shirt")
    
    def test_detect_brand(self):
        """Test brand detection from URL slug."""
        slug = "/Portronics-Kanban-Portable-Charger/dp/B09XXXXXXX"
        brand = self.mapper.detect_brand(slug)
        # First capitalized word(s) before hyphens are the brand
        self.assertIsNotNone(brand)
        self.assertIn("Portronics", brand)
    
    def test_map_with_existing_category(self):
        """Test mapping when category already exists."""
        result = self.mapper.map(
            "B09V3KXJPB",
            existing_category="Electronics > Headphones"
        )
        
        self.assertEqual(result["category"], "Electronics")
        self.assertEqual(result["subcategory"], "Headphones")
        self.assertEqual(result["confidence"], 1.0)
    
    def test_map_without_info(self):
        """Test mapping with minimal info."""
        result = self.mapper.map("B09V3KXJPB")
        
        # Should fall back to generic
        self.assertEqual(result["category"], "General")
        self.assertLessEqual(result["confidence"], 0.5)


class TestIntegration(unittest.TestCase):
    """Integration tests for registry + mapper."""
    
    def test_end_to_end_mapping(self):
        """Test full pipeline: map ASIN -> get schema -> record data."""
        registry = AttributeRegistry.instance()
        mapper = CategoryMapper()
        
        # Map an ASIN
        result = mapper.map(
            asin="B09V3KXJPB",
            title="Sony WH-1000XM4 Wireless Headphones",
            existing_category="Electronics > Headphones"
        )
        
        self.assertEqual(result["category"], "Electronics")
        self.assertEqual(result["subcategory"], "Headphones")
        
        # Get schema
        schema = registry.get_schema_for_asin(
            "B09V3KXJPB",
            result["category"],
            result["subcategory"],
            result["product_type"]
        )
        
        # Schema should have expected fields
        self.assertIn("asin", schema)
        self.assertIn("title", schema)
        self.assertIn("price", schema)
        
        # All should start as MISSING
        for attr, status in schema.items():
            self.assertEqual(status, DataStatus.MISSING.value)
        
        # Record some data
        registry.record_data("B09V3KXJPB", "asin", "B09V3KXJPB", DataStatus.COLLECTED)
        registry.record_data("B09V3KXJPB", "title", "Sony WH-1000XM4", DataStatus.COLLECTED)
        registry.record_data("B09V3KXJPB", "price", 19990.0, DataStatus.COLLECTED)
        
        # Check completeness
        completeness = registry.compute_completeness_score(
            "B09V3KXJPB",
            result["category"],
            result["subcategory"],
            result["product_type"]
        )
        
        self.assertGreater(completeness["collected_fields"], 0)
        self.assertGreater(completeness["score"], 0.0)


if __name__ == "__main__":
    unittest.main()

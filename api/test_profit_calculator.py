"""Unit tests for ScoutVeda India profit calculator (Amazon.in fees as of 2026-08-15)."""

import sys
import types
import unittest

import profit_calculator
from profit_calculator import calculate, _verdict


def _base(**kwargs):
    """Sensible defaults so tests can override one dimension at a time."""
    params = dict(
        sell_price=1199,
        buy_price=450,
        category="electronics_accessories",
        weight_grams=300,
        fulfillment="easy_ship",
        gst_rate_pct=18,
        zone="national",
        returns_pct=5,
        ppc_per_unit=0,
        gst_registered=True,
    )
    params.update(kwargs)
    return calculate(**params)


class ReferralFeeTests(unittest.TestCase):
    def test_1_grocery_dried_fruits_750_zero_referral(self):
        """Official: Dried fruits / grocery ₹750 → referral 0 (0% <= ₹1000)."""
        r = _base(sell_price=750, category="grocery")
        self.assertEqual(r["referral_fee"], 0)
        self.assertEqual(r["referral_pct_applied"], 0)
        self.assertEqual(r["category_key"], "grocery")

    def test_2_baby_other_1450_not_apparel_baby(self):
        """Official Apparel-Baby is 7%, but we use Baby-Other 7.5%.
        baby ₹1450 → 7.5% of 1450 = 108.75 referral.
        """
        r = _base(sell_price=1450, category="baby")
        self.assertAlmostEqual(r["referral_fee"], 108.75, places=2)
        self.assertEqual(r["referral_pct_applied"], 7.5)
        self.assertEqual(r["category_key"], "baby")

    def test_3_electronics_accessories_1500_seventeen_pct(self):
        """electronics_accessories ₹1500 → 17% referral = 255."""
        r = _base(sell_price=1500, category="electronics_accessories")
        self.assertAlmostEqual(r["referral_fee"], 255.0, places=2)
        self.assertEqual(r["referral_pct_applied"], 17)

    def test_4_electronics_accessories_500_five_pct_below_1000_exception(self):
        """electronics_accessories ₹500 → 5% referral = 25 (below-₹1000 exception)."""
        r = _base(sell_price=500, category="electronics_accessories")
        self.assertAlmostEqual(r["referral_fee"], 25.0, places=2)
        self.assertEqual(r["referral_pct_applied"], 5)

    def test_5_beauty_400_zero_pct(self):
        """Beauty-Other 0% for item price <= ₹500."""
        r = _base(sell_price=400, category="beauty_personal_care")
        self.assertEqual(r["referral_fee"], 0)
        self.assertEqual(r["referral_pct_applied"], 0)

    def test_6_beauty_800_nine_pct(self):
        """Beauty-Other 9% for item price > ₹500."""
        r = _base(sell_price=800, category="beauty_personal_care")
        self.assertAlmostEqual(r["referral_fee"], 72.0, places=2)
        self.assertEqual(r["referral_pct_applied"], 9)

    def test_7_watches_1200_fifteen_pct(self):
        """Watches ₹1200 → 15% referral."""
        r = _base(sell_price=1200, category="watches")
        self.assertAlmostEqual(r["referral_fee"], 180.0, places=2)
        self.assertEqual(r["referral_pct_applied"], 15)


class GstAndCashModelTests(unittest.TestCase):
    def test_8_unregistered_net_lower_by_gst_on_amazon_fees(self):
        """Same inputs: unregistered net is lower by gst_on_amazon_fees (no ITC)."""
        common = dict(
            sell_price=1199,
            buy_price=450,
            category="electronics_accessories",
            weight_grams=300,
            fulfillment="easy_ship",
            gst_rate_pct=18,
            zone="national",
            returns_pct=5,
            ppc_per_unit=60,
        )
        reg = calculate(gst_registered=True, **common)
        unreg = calculate(gst_registered=False, **common)
        self.assertEqual(reg["gst_on_amazon_fees"], unreg["gst_on_amazon_fees"])
        self.assertEqual(reg["gst_on_amazon_fees"], reg["gst_on_amazon_fees_info_only"])
        self.assertAlmostEqual(
            reg["net_margin_rupees"] - unreg["net_margin_rupees"],
            unreg["gst_on_amazon_fees"],
            places=2,
        )
        self.assertAlmostEqual(
            unreg["cash_amazon_cost"] - reg["cash_amazon_cost"],
            unreg["gst_on_amazon_fees"],
            places=2,
        )
        self.assertTrue(reg["gst_registered"])
        self.assertFalse(unreg["gst_registered"])
        self.assertLess(unreg["net_margin_rupees"], reg["net_margin_rupees"])


class ClosingAndPickPackTests(unittest.TestCase):
    def test_9_easy_ship_closing_official_examples(self):
        """Easy Ship closing at 299 is ₹1, at 450 is ₹22 (official sandals examples)."""
        r299 = _base(sell_price=299, fulfillment="easy_ship")
        r450 = _base(sell_price=450, fulfillment="easy_ship")
        self.assertEqual(r299["closing_fee"], 1)
        self.assertEqual(r450["closing_fee"], 22)

    def test_10_fba_pick_pack_300g_standard_is_17(self):
        """FBA pick & pack 300g standard = ₹17, not the old ₹20."""
        r = _base(fulfillment="fba", weight_grams=300, is_oversize=False)
        self.assertEqual(r["weight_or_pickpack_fee"], 17)


class VerdictTests(unittest.TestCase):
    def test_11_verdict_thresholds(self):
        self.assertEqual(_verdict(20), "Strong")
        self.assertEqual(_verdict(20.0), "Strong")
        self.assertEqual(_verdict(35), "Strong")
        self.assertEqual(_verdict(10), "Workable")
        self.assertEqual(_verdict(19.99), "Workable")
        self.assertEqual(_verdict(0), "Thin")
        self.assertEqual(_verdict(9.99), "Thin")
        self.assertEqual(_verdict(-0.01), "Loss")
        self.assertEqual(_verdict(-12), "Loss")

        strong = _base(sell_price=2000, buy_price=100, category="baby", ppc_per_unit=0, returns_pct=0)
        self.assertEqual(strong["verdict"], "Strong")
        loss = _base(sell_price=400, buy_price=390, category="beauty_personal_care", ppc_per_unit=50)
        self.assertEqual(loss["verdict"], "Loss")


class ScorerMappingTests(unittest.TestCase):
    def test_12_category_to_fee_key_has_no_other_default(self):
        """scorer CATEGORY_TO_FEE_KEY contains no other_default values."""
        if "db" not in sys.modules:
            sys.modules["db"] = types.ModuleType("db")
        if "trend_radar" not in sys.modules:
            sys.modules["trend_radar"] = types.ModuleType("trend_radar")
        import scorer

        self.assertNotIn("other_default", scorer.CATEGORY_TO_FEE_KEY.values())
        expected = {
            "Electronics Accessories": "electronics_accessories",
            "Home & Kitchen": "home_kitchen",
            "Beauty & Personal Care": "beauty_personal_care",
            "Sports & Fitness": "sports_fitness",
            "Toys & Games": "toys",
            "Stationery/Office": "office",
            "Pet Supplies": "pet_supplies",
            "Car Accessories": "automotive_parts",
            "Garden & Outdoors": "garden",
            "Baby Products": "baby",
            "Watches & Gifting": "watches",
        }
        for label, key in expected.items():
            self.assertEqual(scorer.CATEGORY_TO_FEE_KEY[label], key)


class CompatibilityAndAlgebraTests(unittest.TestCase):
    def test_referral_override_replaces_table_entirely(self):
        r = _base(sell_price=500, category="electronics_accessories", referral_pct_override=12)
        self.assertEqual(r["referral_pct_applied"], 12)
        self.assertAlmostEqual(r["referral_fee"], 60.0, places=2)

    def test_storage_default_zero_and_fba_cuft_months(self):
        r0 = _base(fulfillment="fba", storage_cuft_months=0)
        self.assertEqual(r0["storage_fee"], 0)
        r = _base(fulfillment="fba", storage_cuft_months=2)  # 2 cuft-months * ₹50
        self.assertEqual(r["storage_fee"], 100)
        self.assertAlmostEqual(
            r["amazon_fees_subtotal"] - r0["amazon_fees_subtotal"], 100, places=2
        )

    def test_easy_ship_under_300_weight_discount(self):
        fees = profit_calculator.load_fee_table()
        discount = fees["weight_handling_fee_easy_ship"]["easy_ship_under_300_weight_discount_rupees"]
        self.assertEqual(discount, 10)
        below = _base(sell_price=299, fulfillment="easy_ship", weight_grams=300, zone="national")
        above = _base(sell_price=301, fulfillment="easy_ship", weight_grams=300, zone="national")
        # Same 300g national base slab; only the under-₹300 discount differs.
        self.assertAlmostEqual(
            above["weight_or_pickpack_fee"] - below["weight_or_pickpack_fee"], 10, places=2
        )

    def test_breakeven_zero_net_at_solved_price_gst_registered(self):
        """Closed-form identity: plug S=breakeven_price into the cash model
        holding referral %, closing, weight and storage fixed (closing is a
        step function, so re-calling calculate() would re-band it)."""
        r = _base(
            sell_price=1199,
            buy_price=450,
            category="electronics_accessories",
            fulfillment="easy_ship",
            gst_registered=True,
            ppc_per_unit=60,
            returns_pct=5,
        )
        be = r["breakeven_price"]
        self.assertIsNotNone(be)
        g = 1 + 18 / 100.0
        taxable_sell = be / g
        taxable_buy = 450 / g
        referral = be * r["referral_pct_applied"] / 100.0
        cash = referral + r["closing_fee"] + r["weight_or_pickpack_fee"] + r["storage_fee"]
        returns_provision = be * 5 / 100.0
        net = taxable_sell - taxable_buy - cash - 60 - returns_provision
        self.assertAlmostEqual(net, 0.0, places=2)

    def test_unknown_category_falls_back_to_other_default(self):
        r = _base(sell_price=1500, category="not_a_real_category")
        self.assertEqual(r["category_key"], "other_default")
        self.assertEqual(r["referral_pct_applied"], 12)
        self.assertAlmostEqual(r["referral_fee"], 180.0, places=2)

    def test_net_margin_pct_basis_is_gst_inclusive_sell(self):
        r = _base()
        self.assertIn("GST-inclusive", r["basis"])
        expected_pct = r["net_margin_rupees"] / 1199 * 100
        self.assertAlmostEqual(r["net_margin_pct"], round(expected_pct, 2), places=2)


if __name__ == "__main__":
    unittest.main()

import html
import json
import os
import re
import unittest
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path


ROOT = Path(__file__).parents[1]
RENDERED_DIR = os.environ.get("FUJI_RENDERED_DIR")
RENDERED = Path(RENDERED_DIR) if RENDERED_DIR else None


def rendered(name):
    path = RENDERED / name
    return path.read_text(encoding="utf-8")


def text_without_tags(source):
    return html.unescape(re.sub(r"<[^>]+>", " ", source))


@unittest.skipUnless(RENDERED_DIR, "FUJI_RENDERED_DIR is unset; skipping rendered-site checks")
class RenderedRiceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "data/rice_prices.json").read_text(encoding="utf-8"))
        cls.reserve = rendered("reserve/index.html")
        cls.home = rendered("index.html")
        cls.buy_js = (ROOT / "functions/go/buy/[[path]].js").read_text(encoding="utf-8")

    def test_reserve_has_all_base_rows_prices_and_rounded_units(self):
        rows = re.findall(r'<tr\s+data-price-key=(?:"([^"]+)"|([^\s>]+))(.*?)</tr>', self.reserve, re.S)
        rows = [(quoted or bare, body) for quoted, bare, body in rows]
        self.assertEqual(len(rows), 20)
        self.assertEqual({key for key, _ in rows}, set(self.data["base"]))
        for key, row in rows:
            item = self.data["base"][key]
            values = re.findall(r"([0-9,]+)円", text_without_tags(row))
            self.assertGreaterEqual(len(values), 2, key)
            expected_unit = int((Decimal(item["price"]) / Decimal(item["kg"])).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
            self.assertIn(f"{item['price']:,}", values)
            self.assertIn(f"{expected_unit:,}", values)

    def test_all_four_savings_numbers_are_correct(self):
        savings = re.search(r'<div[^>]+class=(?:["\']rice-saving["\']|rice-saving)(?:\s|>)[^>]*>(.*?)</div>', self.reserve, re.S)
        self.assertIsNotNone(savings)
        text = text_without_tags(savings.group(1))
        expected = {
            "hakumai10kg": 2 * self.data["base"]["hakumai5kg"]["price"] - self.data["base"]["hakumai10kg"]["price"],
            "hakumai20kg": 4 * self.data["base"]["hakumai5kg"]["price"] - self.data["base"]["hakumai20kg"]["price"],
            "genmai10kg": 2 * self.data["base"]["genmai5kg"]["price"] - self.data["base"]["genmai10kg"]["price"],
            "genmai20kg": 4 * self.data["base"]["genmai5kg"]["price"] - self.data["base"]["genmai20kg"]["price"],
        }
        for key, saving in expected.items():
            self.assertRegex(text, rf"{saving:,}円")

    def test_no_duplicate_ids_and_preserved_main_anchors(self):
        for page in (self.home, self.reserve):
            ids = re.findall(r'<[^>]+\sid=(?:["\']([^"\']+)["\']|([^\s>]+))', page)
            ids = [quoted or bare for quoted, bare in ids]
            self.assertEqual(len(ids), len(set(ids)))
        for anchor in ("main-content", "gd-concept", "gd-timelapse", "gd-music", "rice-shop"):
            self.assertRegex(self.home, rf'id=(?:["\']{re.escape(anchor)}["\']|{re.escape(anchor)}(?:\s|>))')
        for anchor in ("purchase-route", "base-first", "libe-lineup", "osusume", "lineup"):
            self.assertRegex(self.reserve, rf'id=(?:["\']{re.escape(anchor)}["\']|{re.escape(anchor)}(?:\s|>))')

    def test_rendered_pages_have_no_raw_hugo_shortcodes(self):
        without_scripts = re.sub(r"<script\b.*?</script>", "", self.home + self.reserve, flags=re.S)
        self.assertNotRegex(without_scripts, r"{{|}}")

    def test_table_routes_match_data_and_base_function_definitions(self):
        table_rows = re.findall(r'<tr\s+data-price-key=(?:"[^"]+"|[^\s>]+).*?</tr>', self.reserve, re.S)
        table_keys = re.findall(r'href=(?:["\'])?/go/buy/base/site/reserve/([^"\'\s>]+)', "".join(table_rows))
        self.assertEqual(len(table_keys), 20)
        self.assertEqual(set(table_keys), set(self.data["base"]))
        function_keys = set(re.findall(r'^\s+([a-z]+\d+kgw?)\s*:', self.buy_js, re.M))
        self.assertTrue(set(table_keys) <= function_keys)

    def test_home_price_matches_data_and_two_real_photo_assets_exist(self):
        base_price = self.data["base"]["hakumai5kg"]["price"]
        libe_price = self.data["libe"]["hakumai5kg"]["price"]
        self.assertRegex(self.home, rf"白米5kg：BASE\s*{base_price:,}円／リベ市場\s*{libe_price:,}円")
        for asset in ("images/products/r8-rice-bag-fuji-20260925.webp", "images/products/r8-cooked-rice-20260925.webp"):
            self.assertTrue((RENDERED / asset).is_file(), asset)


if __name__ == "__main__":
    unittest.main()

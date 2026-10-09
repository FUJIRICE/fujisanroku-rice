import html
from html.parser import HTMLParser
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


class DomNode:
    def __init__(self, tag="root", attrs=None, parent=None):
        self.tag, self.attrs, self.parent = tag, dict(attrs or []), parent
        self.children = []

    def text(self):
        return "".join(c if isinstance(c, str) else c.text() for c in self.children)

    def find_all(self, tag=None, **attrs):
        found = []
        if (tag is None or self.tag == tag) and all(self.attrs.get(k) == v for k, v in attrs.items()):
            found.append(self)
        for child in self.children:
            if isinstance(child, DomNode):
                found.extend(child.find_all(tag, **attrs))
        return found


class RiceHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = DomNode()
        self.current = self.root

    def handle_starttag(self, tag, attrs):
        node = DomNode(tag, attrs, self.current)
        self.current.children.append(node)
        if tag not in {"meta", "link", "img", "input", "br", "hr", "source"}:
            self.current = node

    def handle_startendtag(self, tag, attrs):
        self.current.children.append(DomNode(tag, attrs, self.current))

    def handle_endtag(self, tag):
        node = self.current
        while node is not self.root and node.tag != tag:
            node = node.parent
        if node is not self.root:
            self.current = node.parent

    def handle_data(self, data):
        self.current.children.append(data)


def parse_dom(source):
    parser = RiceHTMLParser()
    parser.feed(source)
    return parser.root


@unittest.skipUnless(RENDERED_DIR, "FUJI_RENDERED_DIR is unset; skipping rendered-site checks")
class RenderedRiceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "data/rice_prices.json").read_text(encoding="utf-8"))
        cls.reserve = rendered("reserve/index.html")
        cls.home = rendered("index.html")
        cls.buy_js = (ROOT / "functions/go/buy/[[path]].js").read_text(encoding="utf-8")
        cls.reserve_dom = parse_dom(cls.reserve)
        cls.home_dom = parse_dom(cls.home)

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

    def test_all_four_savings_numbers_are_correct_and_collapsed(self):
        savings = [n for n in self.reserve_dom.find_all("details") if "rice-saving" in n.attrs.get("class", "").split()]
        self.assertEqual(len(savings), 1)
        savings = savings[0]
        self.assertNotIn("open", savings.attrs)
        self.assertEqual(len(savings.find_all("summary")), 1)
        text = savings.text()
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
        catalog = [n for n in self.reserve_dom.find_all("details") if "rice-catalog" in n.attrs.get("class", "").split()]
        self.assertEqual(len(catalog), 1)
        catalog = catalog[0]
        self.assertNotIn("open", catalog.attrs)
        self.assertEqual(catalog.attrs.get("id"), "lineup")
        table_keys = [n.attrs.get("href", "").rsplit("/", 1)[-1] for n in catalog.find_all("a") if "/go/buy/base/site/reserve/" in n.attrs.get("href", "")]
        self.assertEqual(len(table_keys), 20)
        self.assertEqual(set(table_keys), set(self.data["base"]))
        function_keys = set(re.findall(r'^\s+([a-z]+\d+kgw?)\s*:', self.buy_js, re.M))
        self.assertTrue(set(table_keys) <= function_keys)

    def test_home_leads_with_quality_and_keeps_purchase_link_only_at_end(self):
        hero = re.search(r'<section[^>]+class=(?:["\']gd-hero["\']|gd-hero)(?:\s|>).*?</section>', self.home, re.S)
        self.assertIsNotNone(hero)
        self.assertNotRegex(text_without_tags(hero.group(0)), r'\d[\d,]*円')
        hero_nodes = [n for n in self.home_dom.find_all("a") if n.attrs.get("href") == "#rice-shop"]
        self.assertTrue(any("このお米について" in n.text() for n in hero_nodes))
        shops = [n for n in self.home_dom.find_all("section") if n.attrs.get("id") == "rice-shop"]
        self.assertEqual(len(shops), 1)
        shop = shops[0]
        shop_text = shop.text()
        self.assertNotRegex(shop_text, r'\d[\d,]*円')
        self.assertFalse([n for n in shop.find_all("a") if n.attrs.get("href", "").startswith(("/go/buy", "/reserve", "https://ichiba.libecity.com"))])
        for feature in ("ご注文を受けてから精米", "大粒", "富士宮"):
            self.assertIn(feature, shop_text)
        self.assertEqual(len(shop.find_all("h3")), 3)
        for asset in ("images/products/r8-rice-bag-fuji-20260925.webp", "images/products/r8-cooked-rice-20260925.webp"):
            self.assertTrue((RENDERED / asset).is_file(), asset)
            self.assertIn("/" + asset, [n.attrs.get("src") for n in shop.find_all("img")], asset)
        mains = self.home_dom.find_all("main")
        self.assertEqual(len(mains), 1)
        self.assertEqual(sum(n.attrs.get("href", "").startswith("/reserve/") or n.attrs.get("href") == "/reserve" for n in mains[0].find_all("a")), 1)

    def test_reserve_explains_quality_before_purchase_and_has_two_store_links(self):
        headings = [(n.text().strip(), n) for n in self.reserve_dom.find_all("h2")]
        heading_text = [text for text, _ in headings]
        qualities = [n for n in self.reserve_dom.find_all("div") if "rice-qualities" in n.attrs.get("class", "").split()]
        route_nodes = [n for n in self.reserve_dom.find_all("section") if n.attrs.get("id") == "purchase-route"]
        self.assertEqual(len(qualities), 1)
        self.assertEqual(len(route_nodes), 1)
        quality_index = heading_text.index("FUJI RICEのお米について")
        work_index = next(i for i, text in enumerate(heading_text) if "作業" in text)
        rice_index = next(i for i, text in enumerate(heading_text) if "白米と玄米" in text)
        purchase_heading = route_nodes[0].find_all("h2")[0]
        purchase_index = next(i for i, (_, node) in enumerate(headings) if node is purchase_heading)
        self.assertLess(quality_index, work_index)
        self.assertLess(work_index, rice_index)
        self.assertLess(rice_index, purchase_index)
        for feature in ("ご注文を受けてから精米", "大粒", "富士宮"):
            self.assertIn(feature, qualities[0].text())
        route = route_nodes[0]
        stores = [n for n in route.find_all("section") if "rice-store" in n.attrs.get("class", "").split()]
        self.assertEqual(len(stores), 2)
        for store in stores:
            self.assertEqual(len(store.find_all("a")), 1)
        links = [n.attrs.get("href") for n in route.find_all("a") if n.attrs.get("href", "").startswith("/go/buy/")]
        self.assertEqual(len(links), 2)
        self.assertIn("/go/buy/base/site/reserve", links)
        self.assertIn("/go/buy/libe", links)
        self.assertFalse([n for n in route.find_all("a") if "rice-option" in n.attrs.get("class", "").split()])

    def test_reserve_catalog_keeps_twenty_rows_and_individual_links(self):
        catalog = [n for n in self.reserve_dom.find_all("details") if "rice-catalog" in n.attrs.get("class", "").split()]
        self.assertEqual(len(catalog), 1)
        catalog = catalog[0]
        self.assertNotIn("open", catalog.attrs)
        table_rows = [n for n in catalog.find_all("tr") if "data-price-key" in n.attrs]
        self.assertEqual(len(table_rows), 20)
        table_keys = [n.attrs.get("href", "").rsplit("/", 1)[-1] for n in catalog.find_all("a") if "/go/buy/base/site/reserve/" in n.attrs.get("href", "")]
        self.assertEqual(len(table_keys), 20)
        self.assertEqual(set(table_keys), set(self.data["base"]))

if __name__ == "__main__":
    unittest.main()

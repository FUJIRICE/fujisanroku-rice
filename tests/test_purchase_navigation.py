import os
import unittest
from pathlib import Path

from test_rendered_rice import parse_dom


RENDERED_DIR = os.environ.get("FUJI_RENDERED_DIR")
RENDERED = Path(RENDERED_DIR) if RENDERED_DIR else None


def rendered(name):
    return (RENDERED / name).read_text(encoding="utf-8")


@unittest.skipUnless(RENDERED_DIR, "FUJI_RENDERED_DIR is unset; skipping rendered-site checks")
class PurchaseNavigationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pages = {
            "home": parse_dom(rendered("index.html")),
            "reserve": parse_dom(rendered("reserve/index.html")),
        }

    def test_purchase_links_are_in_header_outside_main_nav(self):
        for name, page in self.pages.items():
            with self.subTest(page=name):
                headers = page.find_all("header", id="site-header")
                self.assertEqual(len(headers), 1)
                links = [
                    node
                    for node in headers[0].find_all("a")
                    if "gd-nav-buy" in node.attrs.get("class", "").split()
                ]
                self.assertEqual(len(links), 1)
                self.assertEqual(links[0].attrs.get("href"), "/reserve/#purchase-route")

                ancestor = links[0].parent
                while ancestor is not None:
                    self.assertFalse(
                        ancestor.tag == "nav" and ancestor.attrs.get("id") == "main-nav"
                    )
                    ancestor = ancestor.parent

    def test_reserve_has_purchase_route(self):
        reserve = self.pages["reserve"]
        self.assertEqual(
            len([node for node in reserve.find_all() if node.attrs.get("id") == "purchase-route"]),
            1,
        )


if __name__ == "__main__":
    unittest.main()

from pathlib import Path
import unittest


ROOT = Path(__file__).parents[1]
NEW_URL = "https://lin.ee/Clcbnkj"


class LineRoutesTest(unittest.TestCase):
    def test_line_routes_use_new_short_url(self):
        for relative in ("hugo.toml", "static/_redirects", "functions/go/t/[[path]].js"):
            text = (ROOT / relative).read_text()
            self.assertIn(NEW_URL, text)
            self.assertNotIn("line.me/R/ti/p/", text)

    def test_contact_qr_path_and_link_are_present(self):
        contact = (ROOT / "content/pages/contact.md").read_text()
        self.assertIn(NEW_URL, contact)
        self.assertIn("/images/line-qr-20261010.jpeg", contact)
        self.assertTrue((ROOT / "static/images/line-qr-20261010.jpeg").is_file())

    def test_page_links_and_measurement(self):
        for name in ("contact", "reserve", "faq"):
            text = (ROOT / f"content/pages/{name}.md").read_text()
            self.assertIn(NEW_URL, text)
            self.assertNotIn("line.me/R/ti/p/", text)
        self.assertIn("target.hostname === 'lin.ee'", (ROOT / "themes/fujirice/static/js/main.js").read_text())

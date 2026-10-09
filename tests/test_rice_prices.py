import json
import unittest
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path


ROOT = Path(__file__).parents[1]


class RicePricesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with (ROOT / "data/rice_prices.json").open() as f:
            cls.data = json.load(f)

    def test_item_counts(self):
        self.assertEqual(len(self.data["base"]), 20)
        self.assertEqual(len(self.data["libe"]), 3)

    def test_prices_match_independent_fixture(self):
        base = {
            "hakumai1kg": (1490, 1), "hakumai2kg": (2200, 2), "hakumai3kg": (2650, 3),
            "hakumai4kg": (3350, 4), "hakumai4kgw": (3380, 4), "hakumai5kg": (3630, 5),
            "hakumai10kg": (6180, 10), "hakumai10kgw": (6180, 10), "hakumai20kg": (12230, 20),
            "hakumai30kg": (18120, 30), "genmai1kg": (1360, 1), "genmai2kg": (1990, 2),
            "genmai3kg": (2450, 3), "genmai4kg": (3090, 4), "genmai4kgw": (3130, 4),
            "genmai5kg": (3340, 5), "genmai10kg": (5910, 10), "genmai10kgw": (5910, 10),
            "genmai20kg": (11260, 20), "genmai30kg": (16080, 30),
        }
        libe = {"hakumai5kg": (3350, 5), "hakumai10kg": (5730, 10), "hakumai20kg": (11380, 20)}
        for store, fixture in (("base", base), ("libe", libe)):
            self.assertEqual({k: (v["price"], v["kg"]) for k, v in self.data[store].items()}, fixture)

    def test_round_half_up_and_savings(self):
        def unit(price, kg):
            return int((Decimal(price) / Decimal(kg)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        self.assertEqual(unit(2650, 3), 883)
        self.assertEqual(unit(5, 2), 3)
        p = self.data["base"]
        self.assertEqual(p["hakumai5kg"]["price"] * 2 - p["hakumai10kg"]["price"], 1080)
        self.assertEqual(p["hakumai5kg"]["price"] * 4 - p["hakumai20kg"]["price"], 2290)
        self.assertEqual(p["genmai5kg"]["price"] * 2 - p["genmai10kg"]["price"], 770)
        self.assertEqual(p["genmai5kg"]["price"] * 4 - p["genmai20kg"]["price"], 2100)


if __name__ == "__main__":
    unittest.main()

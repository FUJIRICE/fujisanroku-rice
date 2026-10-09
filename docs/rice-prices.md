# Rice price source and update workflow

The canonical price data is [`data/rice_prices.json`](../data/rice_prices.json).
It contains the current displayed price and kilogram amount for each BASE item,
plus the corresponding Libe-market prices.

## Updating prices

1. Confirm the intended price changes against the shop listings and record the
   exact税込 price and package weight.
2. Edit only the matching entries in `data/rice_prices.json`; keep product keys
   stable because templates and purchase routes use them.
3. Run `python3 -m unittest discover -s tests -v` and rebuild the site.
4. Run the same command with the rendered build directory, for example:
   `FUJI_RENDERED_DIR=/path/build python3 -m unittest discover -s tests -v`.
5. Review the rendered price table and home offer before publishing.

`tests/test_rice_prices.py` contains an independent expected-price fixture.
For a future approved and verified price change, update that fixture deliberately
alongside the JSON change. Do not blindly derive or regenerate the fixture from
production data, since it is intended to catch unintended data changes.

Prices are not changed by this document, and they are not automatically synced
from BASE, the Libe market, or any other shop. A future price change requires a
deliberate JSON edit followed by the checks above.

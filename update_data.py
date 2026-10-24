"""Builds data.json for the item value page.

Pulls the full item catalog and in-game shop prices from the UEX API, then
merges in the player-market snapshot from data/marketplace.csv. Items with no
price data get null values, which the page shows as N/A.
"""
import csv
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE = "https://uexcorp.space/api/2.0"
TOKEN = os.environ.get("UEX_TOKEN", "").strip()
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data.json"
MARKET = ROOT / "data" / "marketplace.csv"
PAUSE = 1.2  # UEX allows 60 requests a minute


def get(path, **params):
    url = f"{BASE}/{path}"
    if params:
        url += "?" + "&".join(f"{k}={v}" for k, v in params.items())
    headers = {"Accept": "application/json", "User-Agent": "sc-item-value-page/1.0"}
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    for attempt in range(4):
        try:
            with urlopen(Request(url, headers=headers), timeout=60) as r:
                body = json.load(r)
            time.sleep(PAUSE)
            if body.get("status") == "ok":
                return body.get("data") or []
            print(f"  {path}: status {body.get('status')}")
        except (HTTPError, URLError, ValueError) as e:
            print(f"  {path}: {e}")
        time.sleep(5 * (attempt + 1))
    return None


def num(x):
    try:
        n = float(x)
        return n if n > 0 else None
    except (TypeError, ValueError):
        return None


def avg(values):
    good = [n for n in (num(v) for v in values) if n]
    return round(sum(good) / len(good)) if good else None


def load_market():
    rows = {}
    if MARKET.exists():
        with open(MARKET, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                rows[r["name"].strip().lower()] = r
    return rows


def entry(name, cat, sec, shop_rows, m):
    return {
        "n": name,
        "c": cat or "Other",
        "s": sec or "",
        "buy": avg(p.get("price_buy") for p in shop_rows),    # what shops charge you
        "sell": avg(p.get("price_sell") for p in shop_rows),  # what shops pay you
        "shops": sum(1 for p in shop_rows if num(p.get("price_buy")) or num(p.get("price_sell"))),
        "ask": num(m and m["avg_ask"]),
        "lo": num(m and m["min_ask"]),
        "hi": num(m and m["max_ask"]),
        "k": int(m["listings"]) if m else None,
        "offer": num(m and m["avg_buy"]),
    }


def main():
    cats = get("categories", type="item")
    if not cats:
        sys.exit("Could not load the category list. Leaving data.json as it is.")
    market = load_market()
    matched, items, shown = set(), [], False
    for c in cats:
        if str(c.get("is_game_related", 1)) == "0":
            continue
        rows = get("items", id_category=c["id"])
        if not rows:
            continue
        prices = get("items_prices", id_category=c["id"]) or []
        if prices and not shown:
            print("shop price fields:", sorted(prices[0]))
            shown = True
        by_item = {}
        for p in prices:
            by_item.setdefault(p.get("id_item"), []).append(p)
        for r in rows:
            name = (r.get("name") or "").strip()
            if not name:
                continue
            matched.add(name.lower())
            items.append(entry(name, c.get("name"), c.get("section"), by_item.get(r["id"], []), market.get(name.lower())))
    for key, m in market.items():  # keep market items the catalog names differently
        if key not in matched:
            items.append(entry(m["name"], m["category"], "Player market", [], m))
    if len(items) < 200:
        sys.exit(f"Only {len(items)} items came back. Leaving data.json as it is.")
    items.sort(key=lambda i: i["n"].lower())
    data = {"updated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"), "items": items}
    OUT.write_text(json.dumps(data, separators=(",", ":"), ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(items)} items, {sum(1 for i in items if i['ask'] or i['buy'] or i['sell'])} with prices.")


if __name__ == "__main__":
    main()

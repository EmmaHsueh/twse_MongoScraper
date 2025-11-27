"""
MOPS monthly revenue crawler (Python)
Source: https://mops.twse.com.tw/mops/#/web/t21sc04_ifrs
Markets: listed (sii) / OTC (otc) / emerging (rotc)
Writes to MongoDB (default DB: TW_Stock; collections: 每月營收 / 公司基本資料 / 歷史股價)

Usage:
    py -3 python/fetch_monthly_revenue.py --year 2024 --month 11 --markets sii,otc,rotc
Defaults to previous month and all three markets.

Dependencies:
    pip install requests beautifulsoup4 pymongo
"""

from __future__ import annotations

import argparse
import datetime as dt
from typing import List, Dict, Any

import requests
import urllib3
from bs4 import BeautifulSoup
from pymongo import MongoClient
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

MOPS_URL = "https://mops.twse.com.tw/mops/web/ajax_t21sc04_ifrs"

MARKET_LABEL = {
    "sii": "上市",
    "otc": "上櫃",
    "rotc": "興櫃",
}

REVENUE_COLLECTION = "每月營收"
BASIC_COLLECTION = "公司基本資料"
STOCK_PRICE_COLLECTION = "歷史股價"
DEFAULT_DB = "TW_Stock"


def to_minguo(year: int) -> int:
    return year - 1911


def parse_number(text: str) -> float:
    clean = text.replace(",", "").strip()
    try:
        return float(clean)
    except ValueError:
        return 0.0


def build_form(year: int, month: int, market: str) -> Dict[str, str]:
    return {
        "encodeURIComponent": "1",
        "step": "1",
        "firstin": "true",
        "TYPEK": market,
        "year": str(to_minguo(year)),
        "month": str(month).zfill(2),
    }


def resolve_header_index(headers: List[str], keywords: List[str]) -> int:
    for i, h in enumerate(headers):
        if any(k in h for k in keywords):
            return i
    return -1


def parse_table(table, meta: Dict[str, Any]) -> List[Dict[str, Any]]:
    header_cells = table.find_all("th")
    headers = [h.get_text(strip=True).replace("\xa0", " ") for h in header_cells]

    idx = {
        "stockId": resolve_header_index(headers, ["公司代號"]),
        "companyName": resolve_header_index(headers, ["公司名稱"]),
        "revenue": resolve_header_index(headers, ["營業收入", "當月", "本月", "本期"]),
        "revenueLastYear": resolve_header_index(headers, ["去年同月", "去年本月", "去年本期", "去年同期"]),
        "revenueChangePercent": resolve_header_index(headers, ["增減百分比", "年增率", "年增(減)"]),
        "cumulativeRevenue": resolve_header_index(headers, ["本年累計", "累計營收"]),
        "cumulativeRevenueLastYear": resolve_header_index(headers, ["去年累計", "去年本期累計"]),
        "cumulativeChangePercent": resolve_header_index(headers, ["累計增減百分比", "累計年增率"]),
    }

    records: List[Dict[str, Any]] = []
    for tr in table.find_all("tr")[1:]:
        tds = tr.find_all("td")
        if not tds:
            continue

        stock_id = tds[idx["stockId"]].get_text(strip=True) if idx["stockId"] >= 0 else ""
        company_name = tds[idx["companyName"]].get_text(strip=True) if idx["companyName"] >= 0 else ""
        if not stock_id or stock_id == "合計":
            continue

        rec = {
            # for query/upsert
            "stockId": stock_id,
            "year": meta["year"],
            "month": meta["month"],
            "market": meta["market"],
            # Chinese field names for Mongo document
            "公司代號": stock_id,
            "公司名稱": company_name,
            "營業收入": parse_number(tds[idx["revenue"]].get_text()) if idx["revenue"] >= 0 else 0,
            "去年同月營收": parse_number(tds[idx["revenueLastYear"]].get_text()) if idx["revenueLastYear"] >= 0 else 0,
            "營收年增率(%)": parse_number(tds[idx["revenueChangePercent"]].get_text()) if idx["revenueChangePercent"] >= 0 else 0,
            "本年累計營收": parse_number(tds[idx["cumulativeRevenue"]].get_text()) if idx["cumulativeRevenue"] >= 0 else 0,
            "去年累計營收": parse_number(tds[idx["cumulativeRevenueLastYear"]].get_text()) if idx["cumulativeRevenueLastYear"] >= 0 else 0,
            "累計年增率(%)": parse_number(tds[idx["cumulativeChangePercent"]].get_text()) if idx["cumulativeChangePercent"] >= 0 else 0,
            "createdAt": dt.datetime.utcnow(),
            "raw": {headers[i]: tds[i].get_text(strip=True) for i in range(min(len(headers), len(tds)))},
        }
        records.append(rec)

    return records


def make_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["POST"],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def fetch_monthly_revenue(year: int, month: int, market: str) -> List[Dict[str, Any]]:
    form = build_form(year, month, market)
    session = make_session()
    resp = session.post(
        MOPS_URL,
        data=form,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": "https://mops.twse.com.tw/mops/web/t21sc04_ifrs",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        },
        timeout=60,
        verify=False,  # disable SSL verification to avoid cert issues on some hosts
    )
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    tables = soup.find_all("table")

    all_records: List[Dict[str, Any]] = []
    for t in tables:
        all_records.extend(parse_table(t, {"year": year, "month": month, "market": market}))
    return all_records


def save_monthly_revenue(client: MongoClient, records: List[Dict[str, Any]]) -> int:
    if not records:
        return 0
    col = client[DEFAULT_DB][REVENUE_COLLECTION]
    ops = []
    for r in records:
        ops.append(
            {
                "updateOne": {
                    "filter": {"stockId": r["stockId"], "year": r["year"], "month": r["month"], "market": r["market"]},
                    "update": {"$set": r},
                    "upsert": True,
                }
            }
        )
    result = col.bulk_write(ops, ordered=False)
    return result.upserted_count + result.modified_count


def find_missing_companies(client: MongoClient, records: List[Dict[str, Any]]) -> List[str]:
    basic_col = client[DEFAULT_DB][BASIC_COLLECTION]
    all_companies = list(basic_col.find({}, {"stock_id": 1, "_id": 0}))
    if not all_companies:
        return []
    revenue_ids = {r["stockId"] for r in records}
    return [c["stock_id"] for c in all_companies if c.get("stock_id") not in revenue_ids]


def run(year: int, month: int, markets: List[str], client: MongoClient):
    total_saved = 0
    per_market = {}
    all_records: List[Dict[str, Any]] = []

    for market in markets:
        label = MARKET_LABEL.get(market, market)
        print(f"Fetching {year}-{str(month).zfill(2)} {label} ({market}) ...")
        records = fetch_monthly_revenue(year, month, market)
        saved = save_monthly_revenue(client, records)
        print(f"  pulled {len(records)} rows, saved {saved}")
        per_market[market] = len(records)
        all_records.extend(records)
        total_saved += saved

    missing = find_missing_companies(client, all_records)
    if missing:
        print(f"Companies missing revenue data ({len(missing)}): {', '.join(missing)}")
    else:
        print("All companies in 公司基本資料 have revenue data for this month.")

    print(f"Total saved: {total_saved}")
    print("Per market:", ", ".join(f"{MARKET_LABEL.get(k, k)}:{v}" for k, v in per_market.items()))


def parse_args():
    now = dt.datetime.now()
    now = now.replace(day=1) - dt.timedelta(days=1)  # previous month

    parser = argparse.ArgumentParser(description="Fetch monthly revenue from MOPS and store to MongoDB.")
    parser.add_argument("--year", type=int, default=now.year, help="Gregorian year, default: previous month year")
    parser.add_argument("--month", type=int, default=now.month, help="month (1-12), default: previous month")
    parser.add_argument("--markets", type=str, default="sii,otc,rotc", help="comma separated markets: sii,otc,rotc")
    parser.add_argument("--mongo-uri", type=str, default="mongodb://localhost:27017", help="MongoDB connection uri")
    parser.add_argument("--mongo-db", type=str, default=DEFAULT_DB, help="MongoDB database name (default TW_Stock)")
    return parser.parse_args()


def main():
    args = parse_args()
    global DEFAULT_DB
    DEFAULT_DB = args.mongo_db

    client = MongoClient(args.mongo_uri)
    try:
        run(args.year, args.month, [m.strip() for m in args.markets.split(",") if m.strip()], client)
    finally:
        client.close()


if __name__ == "__main__":
    main()

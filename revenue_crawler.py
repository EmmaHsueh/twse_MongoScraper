"""Crawler for TWSE monthly revenue data.

This script fetches monthly revenue data from Taiwan Stock Exchange OpenAPI
and stores it in MongoDB.

Data sources:
- Listed companies (上市): /opendata/t187ap05_L
- Public companies (公開發行): /opendata/t187ap05_P

Note: The OpenAPI provides the latest monthly revenue data.
For historical data, this script needs to be run periodically.
"""
from __future__ import annotations

import argparse
import logging
import ssl
import urllib3
from typing import Dict, List

import requests
from pymongo import MongoClient
from pymongo.collection import Collection

# Setup SSL bypass
ssl._create_default_https_context = ssl._create_unverified_context
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# TWSE and TPEx OpenAPI base URLs
TWSE_API_BASE = "https://openapi.twse.com.tw/v1"
TPEX_API_BASE = "https://www.tpex.org.tw/openapi/v1"

# Revenue endpoints
REVENUE_ENDPOINTS = {
    "listed": (TWSE_API_BASE, "/opendata/t187ap05_L"),  # 上市公司每月營業收入彙總表
    "public": (TWSE_API_BASE, "/opendata/t187ap05_P"),  # 公開發行公司每月營業收入彙總表
    "otc": (TPEX_API_BASE, "/mopsfin_t187ap05_O"),  # 上櫃公司每月營業收入彙總表
    "emerging": (TPEX_API_BASE, "/t187ap05_R"),  # 興櫃公司每月營業收入彙總表
}


def fetch_revenue_data(base_url: str, endpoint: str, verify_ssl: bool = False) -> List[Dict]:
    """Fetch monthly revenue data from TWSE/TPEx OpenAPI.

    Parameters
    ----------
    base_url:
        The API base URL (e.g., TWSE_API_BASE or TPEX_API_BASE)
    endpoint:
        The API endpoint path (e.g., "/opendata/t187ap05_L")
    verify_ssl:
        Whether to verify SSL certificates (default: False)

    Returns
    -------
    List[Dict]
        List of revenue records
    """
    url = base_url + endpoint
    logging.info(f"Fetching revenue data from {url}")

    try:
        response = requests.get(url, timeout=30, verify=verify_ssl)
        response.raise_for_status()

        data = response.json()
        logging.info(f"Fetched {len(data)} revenue records")
        return data

    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch data from {url}: {e}")
        raise
    except ValueError as e:
        logging.error(f"Failed to parse JSON response: {e}")
        raise


def persist_revenue_to_mongo(
    collection: Collection,
    documents: List[Dict],
    *,
    key_fields: List[str] = None
) -> None:
    """Persist revenue documents into MongoDB using upsert.

    Parameters
    ----------
    collection:
        MongoDB collection to store the data
    documents:
        List of revenue records to store
    key_fields:
        Fields to use as unique identifier for upsert
        Default: ["公司代號", "資料年月"]
    """
    if key_fields is None:
        key_fields = ["公司代號", "資料年月"]

    logging.info(f"Saving {len(documents)} documents into MongoDB collection {collection.full_name}")

    inserted = 0
    updated = 0

    for doc in documents:
        # Build unique key
        unique_key = {field: doc.get(field) for field in key_fields}

        # Check if any key field is missing
        if any(v is None for v in unique_key.values()):
            logging.warning(f"Skipping document with missing key fields: {unique_key}")
            continue

        # Upsert document
        result = collection.replace_one(unique_key, doc, upsert=True)

        if result.upserted_id:
            inserted += 1
        elif result.modified_count > 0:
            updated += 1

    logging.info(f"Completed: {inserted} inserted, {updated} updated")


def check_data_coverage(
    revenue_col: Collection,
    company_col: Collection
) -> None:
    """Check which companies from 公司基本資料 have revenue data.

    Parameters
    ----------
    revenue_col:
        MongoDB collection containing revenue data
    company_col:
        MongoDB collection containing company basic data
    """
    logging.info("Checking data coverage...")

    # Get all company codes from 公司基本資料
    all_companies = set(company_col.distinct("公司 代號"))
    logging.info(f"Total companies in 公司基本資料: {len(all_companies)}")

    # Get companies with revenue data
    companies_with_revenue = set(revenue_col.distinct("公司代號"))
    logging.info(f"Companies with revenue data: {len(companies_with_revenue)}")

    # Find missing companies
    missing = all_companies - companies_with_revenue
    if missing:
        logging.warning(f"Companies missing revenue data: {len(missing)}")
        # Show first 20 missing company codes
        missing_list = sorted(list(missing))[:20]
        logging.warning(f"Sample missing codes: {missing_list}")
        if len(missing) > 20:
            logging.warning(f"... and {len(missing) - 20} more")
    else:
        logging.info("All companies have revenue data!")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch monthly revenue data from TWSE OpenAPI and store into MongoDB."
    )
    parser.add_argument(
        "--mongo-uri",
        default="mongodb://localhost:27017",
        help="MongoDB connection URI (default: %(default)s)",
    )
    parser.add_argument(
        "--database",
        default="TW_Stock",
        help="MongoDB database name (default: %(default)s)",
    )
    parser.add_argument(
        "--collection",
        default="每月營收",
        help="MongoDB collection name (default: %(default)s)",
    )
    parser.add_argument(
        "--drop",
        action="store_true",
        help="Drop the target collection before inserting documents.",
    )
    parser.add_argument(
        "--verify-ssl",
        action="store_true",
        help="Verify SSL certificates (default: False).",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level (default: %(default)s)",
    )
    parser.add_argument(
        "--check-coverage",
        action="store_true",
        help="Check which companies from 公司基本資料 have revenue data.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

    if not args.verify_ssl:
        logging.info("SSL certificate verification is disabled")

    # Fetch data from all endpoints
    all_documents = []
    for category, (base_url, endpoint) in REVENUE_ENDPOINTS.items():
        try:
            data = fetch_revenue_data(base_url, endpoint, verify_ssl=args.verify_ssl)
            all_documents.extend(data)
            logging.info(f"Fetched {len(data)} records from {category}")
        except Exception as e:
            logging.error(f"Failed to fetch {category} data: {e}")
            # Continue with other endpoints even if one fails

    if not all_documents:
        logging.error("No data fetched from any endpoint!")
        return

    logging.info(f"Total revenue records fetched: {len(all_documents)}")

    # Connect to MongoDB
    client = MongoClient(args.mongo_uri)
    db = client[args.database]
    revenue_col = db[args.collection]

    if args.drop:
        logging.info(f"Dropping collection {revenue_col.full_name}")
        revenue_col.drop()

    # Persist to MongoDB
    persist_revenue_to_mongo(revenue_col, all_documents)

    # Check coverage if requested
    if args.check_coverage:
        company_col = db["公司基本資料"]
        check_data_coverage(revenue_col, company_col)

    logging.info("Completed successfully")


if __name__ == "__main__":
    main()

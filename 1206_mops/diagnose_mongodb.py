#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
診斷 MongoDB 資料結構
檢查實際的欄位名稱和值
"""

from pymongo import MongoClient
import json


def diagnose_mongodb():
    """診斷 MongoDB 資料結構"""

    client = MongoClient("mongodb://localhost:27017/")
    db = client['TW_Stock']

    print("\n" + "="*60)
    print("MongoDB 資料結構診斷")
    print("="*60)

    # 1. 檢查所有 collections
    print("\n【Collections 列表】")
    collections = db.list_collection_names()
    for i, col in enumerate(collections, 1):
        count = db[col].count_documents({})
        print(f"{i}. {col}: {count} 筆")

    # 2. 檢查「公司基本資料」的結構
    print("\n" + "="*60)
    print("【公司基本資料】結構分析")
    print("="*60)

    company_basic = db['公司基本資料']

    # 取得第一筆資料
    sample = company_basic.find_one()

    if sample:
        print("\n範例資料 (第一筆):")
        print(json.dumps(sample, indent=2, ensure_ascii=False, default=str))

        print("\n所有欄位名稱:")
        for key in sample.keys():
            print(f"  - {key}")

        # 檢查可能的市場別欄位
        print("\n\n【市場別欄位檢測】")
        possible_market_fields = ["市場別", "市場", "market", "Market", "MARKET", "type", "Type"]

        for field in possible_market_fields:
            if field in sample:
                print(f"✓ 找到欄位: {field} = {sample[field]}")

        # 如果有市場別欄位,統計所有可能的值
        market_field = None
        for field in possible_market_fields:
            if field in sample:
                market_field = field
                break

        if market_field:
            print(f"\n使用欄位: {market_field}")
            print("\n市場別統計:")

            pipeline = [
                {"$group": {"_id": f"${market_field}", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]

            market_stats = list(company_basic.aggregate(pipeline))
            for stat in market_stats:
                print(f"  {stat['_id']}: {stat['count']} 家")
        else:
            print("\n⚠ 未找到市場別欄位")
            print("請檢查資料結構")

        # 檢查公司代號欄位
        print("\n\n【公司代號欄位檢測】")
        possible_code_fields = ["公司代號", "代號", "code", "Code", "stock_code", "ticker"]

        code_field = None
        for field in possible_code_fields:
            if field in sample:
                print(f"✓ 找到欄位: {field} = {sample[field]}")
                code_field = field

        if code_field:
            # 顯示前 10 筆公司代號
            print(f"\n前 10 筆公司代號:")
            companies = company_basic.find({}, {code_field: 1, "_id": 0}).limit(10)
            codes = [c[code_field] for c in companies if code_field in c]
            print(f"  {codes}")

    else:
        print("⚠ 「公司基本資料」collection 是空的")

    # 3. 提供修正建議
    print("\n\n" + "="*60)
    print("【修正建議】")
    print("="*60)

    if sample and market_field:
        print(f"\n請在 mongodb_helper.py 中修改:")
        print(f'  將 "市場別" 改為 "{market_field}"')
        print(f'\n例如:')
        print(f'  query["{market_field}"] = market_name')

    if sample and code_field:
        print(f"\n請在 mongodb_helper.py 中修改:")
        print(f'  將 "公司代號" 改為 "{code_field}"')

    client.close()
    print("\n✓ 診斷完成\n")


if __name__ == "__main__":
    diagnose_mongodb()

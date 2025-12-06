#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MongoDB 資料庫操作輔助模組
"""

from pymongo import MongoClient, ASCENDING
from datetime import datetime


class MongoDBHelper:
    def __init__(self, connection_string="mongodb://localhost:27017/"):
        """
        初始化 MongoDB 連線

        Args:
            connection_string: MongoDB 連線字串
        """
        self.client = MongoClient(connection_string)
        self.db = self.client['TW_Stock']

        # Collections
        self.company_basic = self.db['公司基本資料']
        self.balance_sheet = self.db['上市櫃公司資產負債表']

        # 建立索引以提升查詢效率
        self._create_indexes()

    def _create_indexes(self):
        """建立索引"""
        try:
            # 公司基本資料：公司代號索引 (注意:欄位名稱有空格)
            self.company_basic.create_index([("公司 代號", ASCENDING)], unique=True)

            # 資產負債表：複合索引 (公司代號 + 年度 + 季別)
            self.balance_sheet.create_index(
                [("公司代號", ASCENDING), ("年度", ASCENDING), ("季別", ASCENDING)],
                unique=True
            )
            print("✓ MongoDB 索引建立完成")
        except Exception as e:
            print(f"建立索引時發生錯誤: {e}")

    def get_all_company_codes(self, market_type=None):
        """
        取得所有公司代號

        Args:
            market_type: 市場類型 ("sii": 上市, "otc": 上櫃, None: 全部)

        Returns:
            list: 公司代號列表
        """
        try:
            query = {}
            if market_type:
                # 市場別的實際值: "listed" (上市), "otc" (上櫃), "emerging" (興櫃)
                market_map = {
                    "sii": "listed",
                    "otc": "otc",
                    "rotc": "emerging",
                    "pub": "pub"
                }
                market_name = market_map.get(market_type)
                if market_name:
                    query["市場別"] = market_name

            # 注意:欄位名稱是 "公司 代號" (有空格)
            companies = self.company_basic.find(query, {"公司 代號": 1, "_id": 0})
            codes = [c["公司 代號"] for c in companies if "公司 代號" in c]
            print(f"✓ 從 MongoDB 取得 {len(codes)} 家公司代號")
            return codes
        except Exception as e:
            print(f"✗ 取得公司代號失敗: {e}")
            return []

    def company_exists(self, company_code):
        """
        檢查公司是否存在於基本資料中

        Args:
            company_code: 公司代號

        Returns:
            bool: 是否存在
        """
        return self.company_basic.find_one({"公司 代號": company_code}) is not None

    def balance_sheet_exists(self, company_code, year, season):
        """
        檢查資產負債表資料是否已存在

        Args:
            company_code: 公司代號
            year: 年度
            season: 季別

        Returns:
            bool: 是否存在
        """
        return self.balance_sheet.find_one({
            "公司代號": company_code,
            "年度": year,
            "季別": season
        }) is not None

    def insert_balance_sheet(self, data):
        """
        插入資產負債表資料

        Args:
            data: 資料字典

        Returns:
            bool: 是否成功
        """
        try:
            # 新增更新時間
            data["更新時間"] = datetime.now()

            # 使用 upsert 避免重複
            self.balance_sheet.update_one(
                {
                    "公司代號": data["公司代號"],
                    "年度": data["年度"],
                    "季別": data["季別"]
                },
                {"$set": data},
                upsert=True
            )
            return True
        except Exception as e:
            print(f"✗ 插入資料失敗: {e}")
            return False

    def insert_balance_sheets_batch(self, data_list):
        """
        批次插入資產負債表資料

        Args:
            data_list: 資料字典列表

        Returns:
            int: 成功插入的筆數
        """
        success_count = 0
        for data in data_list:
            if self.insert_balance_sheet(data):
                success_count += 1
        return success_count

    def get_missing_data(self, company_code, start_year, end_year):
        """
        取得缺少的資料 (年度+季別組合)

        Args:
            company_code: 公司代號
            start_year: 起始年度
            end_year: 結束年度

        Returns:
            list: [(year, season), ...] 缺少的資料組合
        """
        missing = []

        for year in range(start_year, end_year + 1):
            for season in range(1, 5):
                if not self.balance_sheet_exists(company_code, year, season):
                    missing.append((year, season))

        return missing

    def get_statistics(self):
        """
        取得資料庫統計資訊

        Returns:
            dict: 統計資訊
        """
        stats = {
            "公司總數": self.company_basic.count_documents({}),
            "上市公司數": self.company_basic.count_documents({"市場別": "listed"}),
            "上櫃公司數": self.company_basic.count_documents({"市場別": "otc"}),
            "資產負債表筆數": self.balance_sheet.count_documents({})
        }
        return stats

    def close(self):
        """關閉連線"""
        if self.client:
            self.client.close()
            print("✓ MongoDB 連線已關閉")


def test_connection():
    """測試 MongoDB 連線"""
    try:
        helper = MongoDBHelper()
        stats = helper.get_statistics()

        print("\n=== MongoDB 連線測試 ===")
        print(f"資料庫: TW_Stock")
        print(f"公司總數: {stats['公司總數']}")
        print(f"上市公司: {stats['上市公司數']}")
        print(f"上櫃公司: {stats['上櫃公司數']}")
        print(f"資產負債表資料: {stats['資產負債表筆數']} 筆")

        # 測試取得公司代號
        sii_codes = helper.get_all_company_codes("sii")
        print(f"\n上市公司代號前 10 筆: {sii_codes[:10]}")

        helper.close()
        print("\n✓ 連線測試成功")
        return True
    except Exception as e:
        print(f"\n✗ 連線測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_connection()

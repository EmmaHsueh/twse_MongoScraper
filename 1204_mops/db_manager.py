"""
MongoDB 資料庫管理器
"""
from pymongo import MongoClient, UpdateOne
from pymongo.errors import BulkWriteError
from typing import List, Dict, Any
import logging
from config import (
    MONGODB_URI,
    MONGODB_DATABASE,
    COMPANY_COLLECTION,
    BALANCE_SHEET_COLLECTION
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MongoDBManager:
    """MongoDB 資料庫管理類別"""

    def __init__(self):
        """初始化 MongoDB 連接"""
        try:
            self.client = MongoClient(MONGODB_URI)
            self.db = self.client[MONGODB_DATABASE]
            self.company_collection = self.db[COMPANY_COLLECTION]
            self.balance_sheet_collection = self.db[BALANCE_SHEET_COLLECTION]
            logger.info(f"成功連接到 MongoDB: {MONGODB_DATABASE}")

            # 建立索引以提升查詢效能
            self._create_indexes()
        except Exception as e:
            logger.error(f"MongoDB 連接失敗: {e}")
            raise

    def _create_indexes(self):
        """建立必要的索引"""
        try:
            # 為歷史負債資料建立複合索引
            self.balance_sheet_collection.create_index([
                ('stock_code', 1),
                ('year', -1),
                ('season', -1)
            ], unique=True, name='stock_year_season_idx')

            self.balance_sheet_collection.create_index([
                ('stock_code', 1)
            ], name='stock_code_idx')

            logger.info("索引建立完成")
        except Exception as e:
            logger.warning(f"索引建立警告: {e}")

    def get_all_companies(self) -> List[Dict[str, Any]]:
        """
        從公司基本資料 collection 取得所有公司

        Returns:
            List[Dict]: 公司資料列表，每個公司包含股票代碼等資訊
        """
        try:
            companies = list(self.company_collection.find({}))
            logger.info(f"成功取得 {len(companies)} 家公司資料")
            return companies
        except Exception as e:
            logger.error(f"取得公司資料失敗: {e}")
            return []

    def get_company_stock_codes(self) -> List[str]:
        """
        取得所有公司的股票代碼

        Returns:
            List[str]: 股票代碼列表
        """
        try:
            # 嘗試常見的欄位名稱
            field_names = [ '股票 代碼', 'symbol', '公司 代號']
            companies = self.get_all_companies()

            if not companies:
                logger.warning("沒有找到任何公司資料")
                return []

            # 檢查第一筆資料，找出股票代碼的欄位名稱
            first_company = companies[0]
            stock_code_field = None

            for field in field_names:
                if field in first_company:
                    stock_code_field = field
                    break

            if not stock_code_field:
                logger.warning(f"無法識別股票代碼欄位。可用欄位: {list(first_company.keys())}")
                return []

            stock_codes = [
                str(company[stock_code_field])
                for company in companies
                if stock_code_field in company and company[stock_code_field]
            ]

            logger.info(f"成功取得 {len(stock_codes)} 個股票代碼 (欄位: {stock_code_field})")
            return stock_codes

        except Exception as e:
            logger.error(f"取得股票代碼失敗: {e}")
            return []

    def save_balance_sheet_data(self, data_list: List[Dict[str, Any]]) -> int:
        """
        批量儲存資產負債表資料到 MongoDB
        使用 upsert 避免重複資料

        Args:
            data_list: 資產負債表資料列表

        Returns:
            int: 成功儲存的筆數
        """
        if not data_list:
            return 0

        try:
            operations = []
            for data in data_list:
                filter_query = {
                    'stock_code': data['stock_code'],
                    'year': data['year'],
                    'season': data['season']
                }
                operations.append(
                    UpdateOne(
                        filter_query,
                        {'$set': data},
                        upsert=True
                    )
                )

            result = self.balance_sheet_collection.bulk_write(operations, ordered=False)
            saved_count = result.upserted_count + result.modified_count

            logger.info(f"成功儲存 {saved_count} 筆資產負債表資料")
            return saved_count

        except BulkWriteError as bwe:
            # 即使有錯誤，部分資料可能已成功寫入
            saved_count = bwe.details.get('nUpserted', 0) + bwe.details.get('nModified', 0)
            logger.warning(f"批量寫入時發生部分錯誤，已儲存 {saved_count} 筆")
            return saved_count
        except Exception as e:
            logger.error(f"儲存資產負債表資料失敗: {e}")
            return 0

    def get_existing_records(self, stock_code: str) -> List[Dict[str, Any]]:
        """
        取得特定股票代碼已存在的記錄

        Args:
            stock_code: 股票代碼

        Returns:
            List[Dict]: 已存在的記錄
        """
        try:
            records = list(self.balance_sheet_collection.find(
                {'stock_code': stock_code},
                {'year': 1, 'season': 1, '_id': 0}
            ))
            return records
        except Exception as e:
            logger.error(f"查詢已存在記錄失敗: {e}")
            return []

    def close(self):
        """關閉 MongoDB 連接"""
        if self.client:
            self.client.close()
            logger.info("MongoDB 連接已關閉")

"""
測試 MongoDB 連接和資料庫結構
"""
from db_manager import MongoDBManager
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_mongodb_connection():
    """測試 MongoDB 連接"""
    logger.info("=" * 60)
    logger.info("測試 MongoDB 連接")
    logger.info("=" * 60)

    try:
        # 初始化資料庫管理器
        db_manager = MongoDBManager()

        # 測試 1: 檢查資料庫連接
        logger.info("\n[測試 1] 檢查資料庫連接")
        collections = db_manager.db.list_collection_names()
        logger.info(f"資料庫中的 collections: {collections}")

        # 測試 2: 檢查公司基本資料
        logger.info("\n[測試 2] 檢查公司基本資料 collection")
        company_count = db_manager.company_collection.count_documents({})
        logger.info(f"公司基本資料總數: {company_count}")

        if company_count > 0:
            # 顯示第一筆資料的結構
            first_company = db_manager.company_collection.find_one({})
            logger.info(f"第一筆公司資料的欄位: {list(first_company.keys())}")
            logger.info(f"第一筆公司資料: {first_company}")

            # 測試 3: 取得股票代碼
            logger.info("\n[測試 3] 取得股票代碼")
            stock_codes = db_manager.get_company_stock_codes()
            logger.info(f"成功取得 {len(stock_codes)} 個股票代碼")
            if stock_codes:
                logger.info(f"前 10 個股票代碼: {stock_codes[:10]}")
        else:
            logger.warning("公司基本資料 collection 是空的！")
            logger.info("請先確保 MongoDB 中有公司資料")

        # 測試 4: 檢查歷史負債資料 collection
        logger.info("\n[測試 4] 檢查歷史負債資料 collection")
        balance_count = db_manager.balance_sheet_collection.count_documents({})
        logger.info(f"歷史負債資料總數: {balance_count}")

        if balance_count > 0:
            first_balance = db_manager.balance_sheet_collection.find_one({})
            logger.info(f"第一筆歷史負債資料: {first_balance}")

        # 測試 5: 檢查索引
        logger.info("\n[測試 5] 檢查索引")
        indexes = list(db_manager.balance_sheet_collection.list_indexes())
        logger.info("歷史負債資料 collection 的索引:")
        for idx in indexes:
            logger.info(f"  - {idx['name']}: {idx.get('key', {})}")

        logger.info("\n" + "=" * 60)
        logger.info("測試完成！系統準備就緒")
        logger.info("=" * 60)

        db_manager.close()
        return True

    except Exception as e:
        logger.error(f"測試失敗: {e}", exc_info=True)
        return False


if __name__ == '__main__':
    test_mongodb_connection()

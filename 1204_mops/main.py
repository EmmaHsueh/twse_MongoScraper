"""
MOPS 資產負債表爬蟲主程式
"""
import asyncio
import sys
from datetime import datetime
from tqdm import tqdm
from db_manager import MongoDBManager
from mops_scraper import MOPSScraper
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'scraper_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


async def main():
    """主程式入口"""
    logger.info("=" * 60)
    logger.info("MOPS 資產負債表爬蟲啟動")
    logger.info("=" * 60)

    # 初始化資料庫管理器
    db_manager = MongoDBManager()

    try:
        # 1. 從 MongoDB 取得所有公司的股票代碼
        logger.info("\n[步驟 1/3] 從 MongoDB 取得公司清單...")
        stock_codes = db_manager.get_company_stock_codes()

        if not stock_codes:
            logger.error("未找到任何公司資料，請檢查 MongoDB 中的公司基本資料 collection")
            return

        logger.info(f"成功取得 {len(stock_codes)} 家公司")
        logger.info(f"前 10 家公司代碼: {stock_codes[:10]}")

        # 2. 使用爬蟲抓取所有公司的資產負債表
        logger.info("\n[步驟 2/3] 開始爬取資產負債表資料...")
        logger.info(f"設定: 並發數={MAX_CONCURRENT_REQUESTS}, 請求延遲={REQUEST_DELAY}秒")

        async with MOPSScraper() as scraper:
            # 可以指定起始年份，預設從民國 102 年 (2013) 開始
            start_year = 102  # 民國年

            all_data = await scraper.fetch_all_companies(
                stock_codes=stock_codes,
                start_year=start_year,
                batch_size=10  # 每批處理 10 家公司
            )

            # 顯示爬蟲統計
            stats = scraper.get_statistics()
            logger.info("\n" + "=" * 60)
            logger.info("爬蟲統計資訊:")
            logger.info(f"  總請求數: {stats['total_requests']}")
            logger.info(f"  成功數: {stats['success_count']}")
            logger.info(f"  失敗數: {stats['error_count']}")
            logger.info(f"  成功率: {stats['success_rate']}")
            logger.info("=" * 60)

        # 3. 儲存資料到 MongoDB
        logger.info("\n[步驟 3/3] 儲存資料到 MongoDB...")
        if all_data:
            saved_count = db_manager.save_balance_sheet_data(all_data)
            logger.info(f"成功儲存 {saved_count} 筆資料到 MongoDB")
        else:
            logger.warning("沒有資料可儲存")

    except KeyboardInterrupt:
        logger.info("\n使用者中斷程式")
    except Exception as e:
        logger.error(f"程式執行時發生錯誤: {e}", exc_info=True)
    finally:
        # 關閉資料庫連接
        db_manager.close()
        logger.info("\n程式結束")


if __name__ == '__main__':
    # 匯入配置
    from config import MAX_CONCURRENT_REQUESTS, REQUEST_DELAY

    # 執行主程式
    asyncio.run(main())

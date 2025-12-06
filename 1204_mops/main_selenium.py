"""
MOPS 資產負債表爬蟲主程式 - Selenium 版本
"""
import sys
import logging
from datetime import datetime
from db_manager import MongoDBManager
from mops_scraper_selenium import MOPSSeleniumScraper

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'scraper_selenium_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def main():
    """主程式入口"""
    logger.info("=" * 60)
    logger.info("MOPS 資產負債表爬蟲啟動 (Selenium 版本)")
    logger.info("=" * 60)

    # 初始化資料庫管理器
    db_manager = MongoDBManager()

    try:
        # 設定爬取參數
        start_year = 112  # 民國年，可以修改起始年份

        logger.info(f"\n[設定] 起始年份: 民國 {start_year} 年")
        logger.info(f"[設定] 目標: 爬取所有上市公司的資產負債表")

        # 使用 Selenium 爬蟲
        logger.info("\n[步驟 1/2] 開始爬取資產負債表資料...")
        logger.info("提示: 使用 Selenium 模擬瀏覽器，速度較慢但成功率高")

        with MOPSSeleniumScraper(headless=True) as scraper:  # headless=True 無頭模式
            # 爬取所有季度的資料
            all_data = scraper.fetch_all_quarters(start_year=start_year)

            # 顯示爬蟲統計
            stats = scraper.get_statistics()
            logger.info("\n" + "=" * 60)
            logger.info("爬蟲統計資訊:")
            logger.info(f"  總請求數: {stats['total_requests']}")
            logger.info(f"  成功數: {stats['success_count']}")
            logger.info(f"  失敗數: {stats['error_count']}")
            logger.info(f"  成功率: {stats['success_rate']}")
            logger.info(f"  取得資料筆數: {len(all_data)}")
            logger.info("=" * 60)

        # 儲存資料到 MongoDB
        logger.info("\n[步驟 2/2] 儲存資料到 MongoDB...")
        if all_data:
            # 統計每個季度的資料
            from collections import defaultdict
            quarter_stats = defaultdict(int)
            for data in all_data:
                key = f"{data['year']}Q{data['season']}"
                quarter_stats[key] += 1

            logger.info(f"\n各季度統計:")
            for quarter, count in sorted(quarter_stats.items()):
                logger.info(f"  {quarter}: {count} 家公司")

            saved_count = db_manager.save_balance_sheet_data(all_data)
            logger.info(f"\n✓ 成功儲存 {saved_count} 筆資料到 MongoDB")
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
    main()

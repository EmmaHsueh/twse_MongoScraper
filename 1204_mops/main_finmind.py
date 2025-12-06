"""
使用 FinMind API 爬取台股財務報表 - 主程式
這是最穩定可靠的解決方案
"""
import sys
import logging
from datetime import datetime
from finmind_scraper import FinMindScraper
from db_manager import MongoDBManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'finmind_scraper_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def main():
    """主程式入口"""
    logger.info("=" * 60)
    logger.info("FinMind API 財務報表爬蟲啟動")
    logger.info("=" * 60)

    # 初始化資料庫管理器
    db_manager = MongoDBManager()

    # 初始化 FinMind API
    # 如果有 API Token，可以在這裡設定：api_token='your_token'
    scraper = FinMindScraper()

    try:
        # 設定參數
        start_date = '2013-01-01'  # 起始日期，可以修改
        logger.info(f"\n[設定] 起始日期: {start_date}")

        # 方式 1：從 MongoDB 取得公司清單（使用您現有的公司資料）
        logger.info("\n[步驟 1/3] 從 MongoDB 取得公司清單...")
        stock_codes = db_manager.get_company_stock_codes()

        if not stock_codes:
            logger.warning("MongoDB 中沒有公司資料，改用 FinMind 取得所有上市公司")
            # 方式 2：從 FinMind 取得所有上市公司
            stock_codes = scraper.get_all_stock_ids()

        if not stock_codes:
            logger.error("無法取得公司清單，程式終止")
            return

        logger.info(f"成功取得 {len(stock_codes)} 家公司")
        logger.info(f"前 10 家公司代碼: {stock_codes[:10]}")

        # 開始爬取
        logger.info("\n[步驟 2/3] 開始使用 FinMind API 爬取財務報表...")
        logger.info("提示: FinMind API 穩定快速，無需擔心被阻擋")

        all_data = scraper.fetch_all_companies_balance_sheet(
            stock_ids=stock_codes,
            start_date=start_date,
            delay=0.5  # 每次請求間隔 0.5 秒（免費版建議）
        )

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
        logger.info("\n[步驟 3/3] 儲存資料到 MongoDB...")
        if all_data:
            # 統計每家公司的資料
            from collections import defaultdict
            company_stats = defaultdict(int)
            for data in all_data:
                company_stats[data['stock_code']] += 1

            logger.info(f"\n各公司統計（前 10 家）:")
            for i, (stock_code, count) in enumerate(sorted(company_stats.items())[:10], 1):
                logger.info(f"  {i}. {stock_code}: {count} 筆季報")

            saved_count = db_manager.save_balance_sheet_data(all_data)
            logger.info(f"\n✓ 成功儲存 {saved_count} 筆資料到 MongoDB")

            # 顯示儲存詳情
            logger.info(f"\n儲存詳情:")
            logger.info(f"  - 資料庫: TW_Stock")
            logger.info(f"  - Collection: 歷史負債資料")
            logger.info(f"  - 資料來源: FinMind API")
            logger.info(f"  - 時間範圍: {start_date} ~ {datetime.now().strftime('%Y-%m-%d')}")
        else:
            logger.warning("沒有資料可儲存")

        logger.info("\n" + "=" * 60)
        logger.info("✅ 程式執行完成！")
        logger.info("=" * 60)

    except KeyboardInterrupt:
        logger.info("\n使用者中斷程式")
    except Exception as e:
        logger.error(f"程式執行時發生錯誤: {e}", exc_info=True)
    finally:
        # 關閉資料庫連接
        db_manager.close()


if __name__ == '__main__':
    main()

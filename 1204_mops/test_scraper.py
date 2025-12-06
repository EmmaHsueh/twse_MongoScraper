"""
測試 MOPS 爬蟲功能
爬取單一公司的資料進行測試
"""
import asyncio
import logging
from mops_scraper import MOPSScraper
from db_manager import MongoDBManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_single_company():
    """測試單一公司的爬取"""
    logger.info("=" * 60)
    logger.info("測試 MOPS 爬蟲功能")
    logger.info("=" * 60)

    # 測試用股票代碼（台積電）
    test_stock_code = '2330'
    test_year = 112  # 民國 112 年
    test_season = 3  # 第 3 季

    async with MOPSScraper() as scraper:
        # 測試 1: 單一季度爬取
        logger.info(f"\n[測試 1] 爬取 {test_stock_code} {test_year}Q{test_season}")
        result = await scraper._fetch_balance_sheet(
            test_stock_code,
            test_year,
            test_season
        )

        if result:
            logger.info("成功取得資料！")
            logger.info(f"公司 代號: {result['stock_code']}")
            logger.info(f"年度: {result['year']}")
            logger.info(f"季度: {result['season']}")
            logger.info(f"項目數量: {len(result['items'])}")
            logger.info(f"前 5 個項目: {list(result['items'].items())[:5]}")
        else:
            logger.warning("未取得資料")

        # 測試 2: 單一公司所有季度
        logger.info(f"\n[測試 2] 爬取 {test_stock_code} 最近 4 季的資料")
        all_results = await scraper.fetch_company_all_seasons(
            test_stock_code,
            start_year=112  # 只爬取民國 112 年之後
        )

        logger.info(f"成功取得 {len(all_results)} 季的資料")

        # 顯示統計
        stats = scraper.get_statistics()
        logger.info("\n" + "=" * 60)
        logger.info("爬蟲統計:")
        logger.info(f"  總請求數: {stats['total_requests']}")
        logger.info(f"  成功數: {stats['success_count']}")
        logger.info(f"  失敗數: {stats['error_count']}")
        logger.info(f"  成功率: {stats['success_rate']}")
        logger.info("=" * 60)

        # 測試 3: 儲存到 MongoDB
        if all_results:
            logger.info("\n[測試 3] 儲存資料到 MongoDB")
            db_manager = MongoDBManager()
            saved_count = db_manager.save_balance_sheet_data(all_results)
            logger.info(f"成功儲存 {saved_count} 筆資料")

            # 驗證資料
            logger.info("\n[測試 4] 驗證儲存的資料")
            saved_data = list(db_manager.balance_sheet_collection.find(
                {'stock_code': test_stock_code}
            ).sort([('year', -1), ('season', -1)]).limit(5))

            logger.info(f"資料庫中 {test_stock_code} 的資料筆數: {len(saved_data)}")
            for data in saved_data:
                logger.info(f"  - {data['year']}Q{data['season']}: {len(data.get('items', {}))} 個項目")

            db_manager.close()

    logger.info("\n測試完成！")


async def test_multiple_companies():
    """測試多家公司的批次爬取"""
    logger.info("=" * 60)
    logger.info("測試批次爬取多家公司")
    logger.info("=" * 60)

    # 測試用股票代碼（台積電、鴻海、聯發科）
    test_stock_codes = ['2330', '2317', '2454']

    async with MOPSScraper() as scraper:
        logger.info(f"爬取 {len(test_stock_codes)} 家公司的資料")

        all_data = await scraper.fetch_all_companies(
            stock_codes=test_stock_codes,
            start_year=112,  # 只爬取民國 112 年之後
            batch_size=3
        )

        logger.info(f"總共取得 {len(all_data)} 筆資料")

        # 儲存到 MongoDB
        if all_data:
            db_manager = MongoDBManager()
            saved_count = db_manager.save_balance_sheet_data(all_data)
            logger.info(f"成功儲存 {saved_count} 筆資料到 MongoDB")
            db_manager.close()

        # 顯示統計
        stats = scraper.get_statistics()
        logger.info("\n" + "=" * 60)
        logger.info("爬蟲統計:")
        logger.info(f"  總請求數: {stats['total_requests']}")
        logger.info(f"  成功數: {stats['success_count']}")
        logger.info(f"  失敗數: {stats['error_count']}")
        logger.info(f"  成功率: {stats['success_rate']}")
        logger.info("=" * 60)

    logger.info("\n測試完成！")


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == 'multi':
        # 測試多家公司
        asyncio.run(test_multiple_companies())
    else:
        # 測試單一公司（預設）
        asyncio.run(test_single_company())

"""
測試 Playwright 版本的 MOPS 爬蟲
"""
import asyncio
import logging
from mops_scraper_playwright import MOPSPlaywrightScraper
from db_manager import MongoDBManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_single_quarter():
    """測試單一季度的爬取"""
    logger.info("=" * 60)
    logger.info("測試 Playwright MOPS 爬蟲 - 單一季度")
    logger.info("=" * 60)

    test_year = 112  # 民國 112 年
    test_season = 3  # 第 3 季

    async with MOPSPlaywrightScraper(headless=False) as scraper:  # 顯示瀏覽器
        logger.info(f"\n[測試] 爬取 {test_year}Q{test_season} 所有上市公司資料")

        result = await scraper.fetch_balance_sheet(test_year, test_season)

        if result:
            logger.info(f"✓ 成功取得資料！")
            logger.info(f"  公司數量: {len(result)}")

            # 顯示前 3 家公司的資訊
            logger.info(f"\n前 3 家公司:")
            for i, company_data in enumerate(result[:3], 1):
                logger.info(f"\n  {i}. 股票代碼: {company_data['stock_code']}")
                logger.info(f"     年度: {company_data['year']}")
                logger.info(f"     季度: {company_data['season']}")
                logger.info(f"     項目數量: {len(company_data['items'])}")
                if company_data['items']:
                    logger.info(f"     前 3 個項目: {list(company_data['items'].items())[:3]}")

            # 測試儲存到 MongoDB
            logger.info(f"\n[測試] 儲存資料到 MongoDB")
            db_manager = MongoDBManager()
            saved_count = db_manager.save_balance_sheet_data(result)
            logger.info(f"✓ 成功儲存 {saved_count} 筆資料")
            db_manager.close()

        else:
            logger.warning("❌ 未取得資料")

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


async def test_multiple_quarters():
    """測試多個季度的爬取"""
    logger.info("=" * 60)
    logger.info("測試 Playwright MOPS 爬蟲 - 多個季度")
    logger.info("=" * 60)

    async with MOPSPlaywrightScraper(headless=True) as scraper:  # 無頭模式
        logger.info("\n爬取民國 112 年所有季度...")

        all_data = await scraper.fetch_all_quarters(start_year=112)

        logger.info(f"\n✓ 總共取得 {len(all_data)} 筆資料")

        # 統計每個季度的公司數量
        from collections import defaultdict
        quarter_stats = defaultdict(int)
        for data in all_data:
            key = f"{data['year']}Q{data['season']}"
            quarter_stats[key] += 1

        logger.info(f"\n各季度統計:")
        for quarter, count in sorted(quarter_stats.items()):
            logger.info(f"  {quarter}: {count} 家公司")

        # 儲存到 MongoDB
        if all_data:
            logger.info(f"\n儲存資料到 MongoDB...")
            db_manager = MongoDBManager()
            saved_count = db_manager.save_balance_sheet_data(all_data)
            logger.info(f"✓ 成功儲存 {saved_count} 筆資料")
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
        # 測試多個季度
        asyncio.run(test_multiple_quarters())
    else:
        # 測試單一季度（預設）
        asyncio.run(test_single_quarter())

"""
測試 FinMind API 爬蟲
"""
import logging
from finmind_scraper import FinMindScraper
from db_manager import MongoDBManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_single_company():
    """測試單一公司的資料抓取"""
    logger.info("=" * 60)
    logger.info("測試 FinMind API - 單一公司")
    logger.info("=" * 60)

    # 初始化 FinMind（不需要 API Token 也可以使用，但有每日限制）
    scraper = FinMindScraper()

    # 測試台積電
    test_stock_id = '2330'
    logger.info(f"\n[測試] 抓取 {test_stock_id}（台積電）的財務報表")

    df = scraper.fetch_balance_sheet(
        stock_id=test_stock_id,
        start_date='2022-01-01'  # 從 2022 年開始
    )

    if df is not None and not df.empty:
        logger.info(f"\n✓ 成功取得資料！")
        logger.info(f"  資料筆數: {len(df)}")
        logger.info(f"  欄位: {list(df.columns)}")
        logger.info(f"\n前 3 筆資料:")
        logger.info(df.head(3).to_string())

        # 轉換為 MongoDB 格式
        records = scraper._convert_df_to_records(df, test_stock_id)
        logger.info(f"\n轉換為 MongoDB 格式: {len(records)} 筆季報")

        if records:
            logger.info(f"\n第一筆記錄範例:")
            first_record = records[0]
            logger.info(f"  股票代碼: {first_record['stock_code']}")
            logger.info(f"  年度: {first_record['year']}")
            logger.info(f"  季度: {first_record['season']}")
            logger.info(f"  項目數量: {len(first_record['items'])}")
            logger.info(f"  前 5 個項目:")
            for i, (key, value) in enumerate(list(first_record['items'].items())[:5], 1):
                logger.info(f"    {i}. {key}: {value}")

            # 儲存到 MongoDB
            logger.info(f"\n[測試] 儲存資料到 MongoDB")
            db_manager = MongoDBManager()
            saved_count = db_manager.save_balance_sheet_data(records)
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


def test_multiple_companies():
    """測試多家公司的資料抓取"""
    logger.info("=" * 60)
    logger.info("測試 FinMind API - 多家公司")
    logger.info("=" * 60)

    # 初始化 FinMind
    scraper = FinMindScraper()

    # 測試幾家知名公司
    test_stock_ids = ['2330', '2317', '2454']  # 台積電、鴻海、聯發科
    logger.info(f"\n抓取 {len(test_stock_ids)} 家公司的財務報表")

    all_data = scraper.fetch_all_companies_balance_sheet(
        stock_ids=test_stock_ids,
        start_date='2022-01-01',
        delay=1  # 每次請求間隔 1 秒
    )

    logger.info(f"\n✓ 總共取得 {len(all_data)} 筆季報資料")

    # 統計每家公司的資料筆數
    from collections import defaultdict
    company_stats = defaultdict(int)
    for data in all_data:
        company_stats[data['stock_code']] += 1

    logger.info(f"\n各公司統計:")
    for stock_code, count in sorted(company_stats.items()):
        logger.info(f"  {stock_code}: {count} 筆季報")

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


def test_get_all_companies():
    """測試取得所有公司清單"""
    logger.info("=" * 60)
    logger.info("測試 FinMind API - 取得所有公司清單")
    logger.info("=" * 60)

    scraper = FinMindScraper()

    stock_ids = scraper.get_all_stock_ids()

    if stock_ids:
        logger.info(f"\n✓ 成功取得 {len(stock_ids)} 家上市公司")
        logger.info(f"\n前 20 家公司代碼:")
        logger.info(f"  {stock_ids[:20]}")
    else:
        logger.warning("❌ 未取得公司清單")

    logger.info("\n測試完成！")


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == 'multi':
            test_multiple_companies()
        elif sys.argv[1] == 'list':
            test_get_all_companies()
    else:
        # 預設測試單一公司
        test_single_company()

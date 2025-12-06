"""
除錯 FinMind 資料結構
"""
import logging
from finmind_scraper import FinMindScraper

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def debug_finmind_data():
    """檢查 FinMind 返回的原始資料結構"""
    logger.info("=" * 60)
    logger.info("除錯 FinMind API 資料結構")
    logger.info("=" * 60)

    scraper = FinMindScraper()

    # 取得台積電資料
    df = scraper.fetch_balance_sheet('2330', '2022-01-01')

    if df is not None and not df.empty:
        logger.info(f"\n原始 DataFrame 資訊:")
        logger.info(f"  資料筆數: {len(df)}")
        logger.info(f"  欄位數量: {len(df.columns)}")
        logger.info(f"\n所有欄位:")
        logger.info(f"  {list(df.columns)}")

        logger.info(f"\n前 10 筆資料:")
        print(df.head(10).to_string())

        logger.info(f"\n資料結構分析:")
        logger.info(f"  DataFrame shape: {df.shape}")
        logger.info(f"  各欄位資料類型:")
        for col in df.columns:
            logger.info(f"    {col}: {df[col].dtype}")

        logger.info(f"\n檢查 'date' 欄位的唯一值（前 20 個）:")
        if 'date' in df.columns:
            unique_dates = df['date'].unique()[:20]
            logger.info(f"  {unique_dates}")
        else:
            logger.warning("  沒有 'date' 欄位！")

        logger.info(f"\n檢查 'type' 欄位:")
        if 'type' in df.columns:
            logger.info(f"  'type' 的唯一值: {df['type'].unique()}")
        else:
            logger.warning("  沒有 'type' 欄位！")

        # 查看特定幾筆完整資料
        logger.info(f"\n第 1 筆完整資料:")
        first_row = df.iloc[0]
        for col in df.columns:
            logger.info(f"  {col}: {first_row[col]}")

    else:
        logger.warning("未取得資料")


if __name__ == '__main__':
    debug_finmind_data()

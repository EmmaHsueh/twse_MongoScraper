"""
驗證 MongoDB 中的實際資料筆數
"""
import logging
from db_manager import MongoDBManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def verify_data():
    """驗證 MongoDB 資料"""
    logger.info("=" * 60)
    logger.info("驗證 MongoDB 資料")
    logger.info("=" * 60)

    db_manager = MongoDBManager()

    try:
        # 1. 查詢台積電的總筆數
        count_2330 = db_manager.balance_sheet_collection.count_documents({'stock_code': '2330'})
        logger.info(f"\n台積電 (2330) 的實際資料筆數: {count_2330}")

        # 2. 查詢所有資料的總筆數
        total_count = db_manager.balance_sheet_collection.count_documents({})
        logger.info(f"資料庫中的總資料筆數: {total_count}")

        # 3. 顯示台積電的前 5 筆資料
        logger.info(f"\n台積電前 5 筆資料:")
        sample = list(db_manager.balance_sheet_collection.find(
            {'stock_code': '2330'}
        ).sort('year', -1).limit(5))

        for i, record in enumerate(sample, 1):
            logger.info(f"\n  {i}. 年度: {record.get('year')}民國 / 季度: {record.get('season')}")
            logger.info(f"     來源: {record.get('source')}")
            logger.info(f"     爬取時間: {record.get('crawl_time')}")
            logger.info(f"     財務項目數量: {len(record.get('items', {}))}")

            # 顯示前 3 個財務項目
            items = record.get('items', {})
            if items:
                logger.info(f"     前 3 個財務項目:")
                for j, (key, value) in enumerate(list(items.items())[:3], 1):
                    logger.info(f"       {j}. {key}: {value}")

        # 4. 按年度和季度統計台積電的資料
        logger.info(f"\n台積電資料按年度季度統計:")
        pipeline = [
            {'$match': {'stock_code': '2330'}},
            {'$group': {
                '_id': {'year': '$year', 'season': '$season'},
                'count': {'$sum': 1}
            }},
            {'$sort': {'_id.year': -1, '_id.season': -1}},
            {'$limit': 20}
        ]

        stats = list(db_manager.balance_sheet_collection.aggregate(pipeline))
        for stat in stats:
            year = stat['_id']['year']
            season = stat['_id']['season']
            count = stat['count']
            logger.info(f"  {year}民國 Q{season}: {count} 筆")

        # 5. 統計各公司的資料筆數
        logger.info(f"\n各公司資料筆數（前 10 家）:")
        pipeline = [
            {'$group': {
                '_id': '$stock_code',
                'count': {'$sum': 1}
            }},
            {'$sort': {'count': -1}},
            {'$limit': 10}
        ]

        company_stats = list(db_manager.balance_sheet_collection.aggregate(pipeline))
        for i, stat in enumerate(company_stats, 1):
            logger.info(f"  {i}. 股票代碼 {stat['_id']}: {stat['count']} 筆")

        logger.info("\n" + "=" * 60)
        logger.info("✓ 驗證完成")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"驗證時發生錯誤: {e}", exc_info=True)
    finally:
        db_manager.close()


if __name__ == '__main__':
    verify_data()

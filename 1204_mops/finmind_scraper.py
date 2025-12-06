"""
使用 FinMind API 取得台股財務報表資料
這是最穩定可靠的方案
"""
import logging
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
from FinMind.data import DataLoader
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FinMindScraper:
    """FinMind API 資料爬取類別"""

    def __init__(self, api_token: Optional[str] = None):
        """
        初始化 FinMind API

        Args:
            api_token: API Token（可選，免費使用不需要 token，但有請求限制）
                      註冊網址：https://finmindtrade.com/
        """
        self.api = DataLoader()
        self.api_token = api_token

        if api_token:
            try:
                self.api.login_by_token(api_token=api_token)
                logger.info("成功登入 FinMind API")
            except Exception as e:
                logger.warning(f"FinMind API 登入失敗: {e}")
                logger.info("將使用免費模式（每天限制 600 次請求）")
        else:
            logger.info("使用 FinMind 免費模式（每天限制 600 次請求）")

        self.request_count = 0
        self.success_count = 0
        self.error_count = 0

    def fetch_balance_sheet(
        self,
        stock_id: str,
        start_date: str = '2013-01-01',
        end_date: Optional[str] = None
    ) -> Optional[pd.DataFrame]:
        """
        抓取單一公司的財務報表（資產負債表）

        Args:
            stock_id: 股票代碼
            start_date: 開始日期 (格式: YYYY-MM-DD)
            end_date: 結束日期 (格式: YYYY-MM-DD)，預設為今天

        Returns:
            DataFrame: 財務報表資料
        """
        try:
            self.request_count += 1

            if end_date is None:
                end_date = datetime.now().strftime('%Y-%m-%d')

            logger.info(f"正在抓取 {stock_id} 的財務報表 ({start_date} ~ {end_date})...")

            df = self.api.taiwan_stock_balance_sheet(
                stock_id=stock_id,
                start_date=start_date,
                end_date=end_date
            )

            if df is not None and not df.empty:
                self.success_count += 1
                logger.info(f"成功取得 {stock_id} 的資料，共 {len(df)} 筆")
                return df
            else:
                logger.warning(f"{stock_id} 無資料")
                return None

        except Exception as e:
            logger.error(f"抓取 {stock_id} 時發生錯誤: {e}")
            self.error_count += 1
            return None

    def fetch_all_companies_balance_sheet(
        self,
        stock_ids: List[str],
        start_date: str = '2013-01-01',
        end_date: Optional[str] = None,
        delay: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        批次抓取多家公司的財務報表

        Args:
            stock_ids: 股票代碼列表
            start_date: 開始日期
            end_date: 結束日期
            delay: 每次請求間的延遲（秒）

        Returns:
            List[Dict]: 所有公司的財務報表資料
        """
        all_data = []
        total_companies = len(stock_ids)

        logger.info(f"開始抓取 {total_companies} 家公司的財務報表")
        start_time = time.time()

        for i, stock_id in enumerate(stock_ids, 1):
            logger.info(f"處理 {i}/{total_companies}: {stock_id}")

            df = self.fetch_balance_sheet(stock_id, start_date, end_date)

            if df is not None and not df.empty:
                # 轉換 DataFrame 為字典格式
                records = self._convert_df_to_records(df, stock_id)
                all_data.extend(records)
                logger.info(f"{stock_id} 完成，取得 {len(records)} 季資料")
            else:
                logger.warning(f"{stock_id} 無資料")

            # 延遲避免超過 API 限制
            time.sleep(delay)

        elapsed_time = time.time() - start_time
        logger.info(
            f"爬蟲完成！共處理 {self.request_count} 個請求，"
            f"成功 {self.success_count} 家，失敗 {self.error_count} 家，"
            f"取得 {len(all_data)} 筆季報資料，"
            f"耗時 {elapsed_time:.2f} 秒"
        )

        return all_data

    def _convert_df_to_records(
        self,
        df: pd.DataFrame,
        stock_id: str
    ) -> List[Dict[str, Any]]:
        """
        將 DataFrame 轉換為 MongoDB 格式的記錄

        Args:
            df: FinMind 返回的 DataFrame（長格式）
            stock_id: 股票代碼

        Returns:
            List[Dict]: 轉換後的記錄列表
        """
        records = []

        # FinMind 返回的是長格式資料，需要按日期分組
        # 每個日期對應一個季度，包含多個財務項目
        grouped = df.groupby('date')

        for date_str, group in grouped:
            try:
                date_obj = pd.to_datetime(date_str)
                year = date_obj.year - 1911  # 轉為民國年
                month = date_obj.month
                season = (month - 1) // 3 + 1
            except Exception as e:
                logger.warning(f"無法解析日期: {date_str}, 錯誤: {e}")
                continue

            # 建立該季度的記錄
            record = {
                'stock_code': stock_id,
                'year': year,
                'season': season,
                'crawl_time': datetime.now(),
                'source': 'FinMind',
                'items': {}
            }

            # 將該日期下的所有財務項目加入 items
            for _, row in group.iterrows():
                type_name = row.get('type', '')
                value = row.get('value', '')
                origin_name = row.get('origin_name', '')

                if pd.notna(type_name) and type_name != '':
                    # 儲存財務項目
                    record['items'][type_name] = {
                        'value': str(value) if pd.notna(value) else '',
                        'origin_name': origin_name if pd.notna(origin_name) else ''
                    }

            if record['items']:
                records.append(record)
                logger.debug(f"轉換季度: {year}民國 Q{season}, 包含 {len(record['items'])} 個財務項目")

        logger.info(f"轉換完成: 共 {len(records)} 個季度，每季平均 {len(df) / len(records):.0f} 個財務項目")
        return records

    def get_statistics(self) -> Dict[str, Any]:
        """取得統計資訊"""
        return {
            'total_requests': self.request_count,
            'success_count': self.success_count,
            'error_count': self.error_count,
            'success_rate': f"{(self.success_count / self.request_count * 100):.2f}%"
            if self.request_count > 0 else "0%"
        }

    def get_all_stock_ids(self) -> List[str]:
        """
        取得所有上市公司的股票代碼

        Returns:
            List[str]: 股票代碼列表
        """
        try:
            logger.info("正在取得台灣上市公司清單...")
            df = self.api.taiwan_stock_info()

            if df is not None and not df.empty:
                # 過濾出上市公司（industry_category 不為空）
                df_listed = df[df['industry_category'].notna()]
                stock_ids = df_listed['stock_id'].tolist()
                logger.info(f"成功取得 {len(stock_ids)} 家上市公司")
                return stock_ids
            else:
                logger.warning("無法取得公司清單")
                return []

        except Exception as e:
            logger.error(f"取得公司清單時發生錯誤: {e}")
            return []

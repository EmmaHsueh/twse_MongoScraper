"""
MOPS 資產負債表爬蟲
支援非同步並發爬取，提升效率
"""
import asyncio
import aiohttp
import time
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
import logging
from datetime import datetime
from config import (
    MOPS_BASE_URL,
    MOPS_HEADERS,
    MAX_CONCURRENT_REQUESTS,
    REQUEST_DELAY,
    RETRY_TIMES,
    TIMEOUT
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MOPSScraper:
    """MOPS 資產負債表爬蟲類別"""

    def __init__(self):
        """初始化爬蟲"""
        self.session: Optional[aiohttp.ClientSession] = None
        self.semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
        self.request_count = 0
        self.success_count = 0
        self.error_count = 0

    async def __aenter__(self):
        """進入非同步上下文管理器"""
        import ssl

        # 建立 SSL context，關閉證書驗證
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        # 建立 TCP connector，使用 cookie jar
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        cookie_jar = aiohttp.CookieJar()

        timeout = aiohttp.ClientTimeout(total=TIMEOUT)
        self.session = aiohttp.ClientSession(
            headers=MOPS_HEADERS,
            timeout=timeout,
            connector=connector,
            cookie_jar=cookie_jar
        )

        # 重要：先訪問頁面取得 cookies（參考 gemini.py 的做法）
        try:
            page_url = 'https://mops.twse.com.tw/mops/web/t163sb05'
            async with self.session.get(page_url) as resp:
                await resp.text()
                logger.info("成功訪問 MOPS 頁面並取得 cookies")
                await asyncio.sleep(1)  # 模擬真人操作
        except Exception as e:
            logger.warning(f"訪問 MOPS 頁面時發生錯誤: {e}")

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """退出非同步上下文管理器"""
        if self.session:
            await self.session.close()

    def _get_year_season_list(self, start_year: int = 2013) -> List[tuple]:
        """
        生成年份和季度列表

        Args:
            start_year: 起始年份（民國年）

        Returns:
            List[tuple]: (民國年, 季度) 的列表
        """
        current_year = datetime.now().year - 1911  # 轉換為民國年
        current_month = datetime.now().month
        current_season = (current_month - 1) // 3 + 1

        year_season_list = []
        for year in range(start_year, current_year + 1):
            for season in range(1, 5):
                if year == current_year and season > current_season:
                    break
                year_season_list.append((year, season))

        return year_season_list

    async def _fetch_balance_sheet(
        self,
        stock_code: str,
        year: int,
        season: int,
        retry_count: int = 0
    ) -> Optional[Dict[str, Any]]:
        """
        抓取單一公司特定季度的資產負債表

        Args:
            stock_code: 股票代碼
            year: 民國年
            season: 季度 (1-4)
            retry_count: 重試次數

        Returns:
            Dict: 資產負債表資料，若失敗則返回 None
        """
        async with self.semaphore:
            try:
                # 準備 POST 請求參數
                data = {
                    'encodeURIComponent': '1',
                    'step': '1',
                    'firstin': '1',
                    'off': '1',
                    'TYPEK': 'sii',  # sii=上市公司
                    'year': str(year),
                    'season': str(season),  # 1-4，不需要補零
                }

                self.request_count += 1

                # 發送 POST 請求
                async with self.session.post(MOPS_BASE_URL, data=data) as response:
                    if response.status != 200:
                        logger.warning(
                            f"股票 {stock_code} {year}Q{season} 回應狀態碼: {response.status}"
                        )
                        if retry_count < RETRY_TIMES:
                            await asyncio.sleep(REQUEST_DELAY * 2)
                            return await self._fetch_balance_sheet(
                                stock_code, year, season, retry_count + 1
                            )
                        return None

                    html_content = await response.text()

                    # 解析 HTML
                    result = self._parse_balance_sheet(
                        html_content, stock_code, year, season
                    )

                    if result:
                        self.success_count += 1
                        logger.info(
                            f"成功抓取 {stock_code} {year}Q{season} "
                            f"(進度: {self.success_count}/{self.request_count})"
                        )
                    else:
                        logger.debug(f"股票 {stock_code} {year}Q{season} 無資料")

                    # 請求延遲，避免過於頻繁
                    await asyncio.sleep(REQUEST_DELAY)
                    return result

            except asyncio.TimeoutError:
                logger.warning(f"股票 {stock_code} {year}Q{season} 請求逾時")
                if retry_count < RETRY_TIMES:
                    await asyncio.sleep(REQUEST_DELAY * 2)
                    return await self._fetch_balance_sheet(
                        stock_code, year, season, retry_count + 1
                    )
                self.error_count += 1
                return None

            except Exception as e:
                logger.error(f"抓取 {stock_code} {year}Q{season} 時發生錯誤: {e}")
                if retry_count < RETRY_TIMES:
                    await asyncio.sleep(REQUEST_DELAY * 2)
                    return await self._fetch_balance_sheet(
                        stock_code, year, season, retry_count + 1
                    )
                self.error_count += 1
                return None

    def _parse_balance_sheet(
        self,
        html_content: str,
        stock_code: str,
        year: int,
        season: int
    ) -> Optional[Dict[str, Any]]:
        """
        解析資產負債表 HTML

        Args:
            html_content: HTML 內容
            stock_code: 股票代碼
            year: 民國年
            season: 季度

        Returns:
            Dict: 解析後的資產負債表資料
        """
        try:
            soup = BeautifulSoup(html_content, 'lxml')

            # 檢查是否有錯誤訊息或無資料
            error_messages = ['查無所需資料', '沒有符合條件', '無資料']
            page_text = soup.get_text()
            if any(msg in page_text for msg in error_messages):
                return None

            # 尋找資產負債表的表格
            tables = soup.find_all('table')
            if not tables:
                return None

            # 解析表格資料
            balance_sheet_data = {
                'stock_code': stock_code,
                'year': year,
                'season': season,
                'crawl_time': datetime.now(),
                'items': {}
            }

            # 遍歷表格，提取資產負債表項目
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        # 第一欄是項目名稱，第二欄是金額
                        item_name = cells[0].get_text(strip=True)
                        item_value = cells[1].get_text(strip=True)

                        # 過濾標題列
                        if item_name and item_value and not item_name.startswith('會計項目'):
                            # 清理數值（移除逗號等）
                            try:
                                # 嘗試轉換為數值
                                clean_value = item_value.replace(',', '').replace(' ', '')
                                if clean_value and clean_value != '-':
                                    balance_sheet_data['items'][item_name] = clean_value
                            except:
                                balance_sheet_data['items'][item_name] = item_value

            # 如果沒有解析到任何項目，返回 None
            if not balance_sheet_data['items']:
                return None

            return balance_sheet_data

        except Exception as e:
            logger.error(f"解析 HTML 時發生錯誤: {e}")
            return None

    async def fetch_company_all_seasons(
        self,
        stock_code: str,
        start_year: int = 2013
    ) -> List[Dict[str, Any]]:
        """
        抓取單一公司所有季度的資產負債表

        Args:
            stock_code: 股票代碼
            start_year: 起始年份（民國年）

        Returns:
            List[Dict]: 所有季度的資產負債表資料
        """
        year_season_list = self._get_year_season_list(start_year)
        tasks = [
            self._fetch_balance_sheet(stock_code, year, season)
            for year, season in year_season_list
        ]

        results = await asyncio.gather(*tasks)
        # 過濾掉 None 的結果
        return [result for result in results if result is not None]

    async def fetch_all_companies(
        self,
        stock_codes: List[str],
        start_year: int = 2013,
        batch_size: int = 10
    ) -> List[Dict[str, Any]]:
        """
        批次抓取所有公司的資產負債表

        Args:
            stock_codes: 股票代碼列表
            start_year: 起始年份（民國年）
            batch_size: 每批處理的公司數量

        Returns:
            List[Dict]: 所有公司的資產負債表資料
        """
        all_results = []
        total_companies = len(stock_codes)

        logger.info(f"開始爬取 {total_companies} 家公司的資產負債表資料")
        start_time = time.time()

        # 分批處理公司
        for i in range(0, total_companies, batch_size):
            batch_codes = stock_codes[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (total_companies + batch_size - 1) // batch_size

            logger.info(f"處理第 {batch_num}/{total_batches} 批公司")

            # 並發抓取該批次的所有公司
            tasks = [
                self.fetch_company_all_seasons(stock_code, start_year)
                for stock_code in batch_codes
            ]

            batch_results = await asyncio.gather(*tasks)

            # 合併結果
            for company_data in batch_results:
                all_results.extend(company_data)

            logger.info(f"第 {batch_num} 批完成，目前共取得 {len(all_results)} 筆資料")

        elapsed_time = time.time() - start_time
        logger.info(
            f"爬蟲完成！共處理 {self.request_count} 個請求，"
            f"成功 {self.success_count} 筆，失敗 {self.error_count} 筆，"
            f"耗時 {elapsed_time:.2f} 秒"
        )

        return all_results

    def get_statistics(self) -> Dict[str, int]:
        """
        取得爬蟲統計資訊

        Returns:
            Dict: 統計資訊
        """
        return {
            'total_requests': self.request_count,
            'success_count': self.success_count,
            'error_count': self.error_count,
            'success_rate': f"{(self.success_count / self.request_count * 100):.2f}%"
            if self.request_count > 0 else "0%"
        }

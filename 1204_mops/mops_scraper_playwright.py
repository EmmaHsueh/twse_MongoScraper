"""
MOPS 資產負債表爬蟲 - Playwright 版本
使用 Playwright 處理現代化 SPA 網站
"""
import asyncio
import time
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from playwright.async_api import async_playwright, Page, Browser
from bs4 import BeautifulSoup
from config import REQUEST_DELAY

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MOPSPlaywrightScraper:
    """MOPS 資產負債表爬蟲類別 - Playwright 版本"""

    def __init__(self, headless: bool = True):
        """
        初始化 Playwright 爬蟲

        Args:
            headless: 是否使用無頭模式（不顯示瀏覽器視窗）
        """
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.request_count = 0
        self.success_count = 0
        self.error_count = 0

    async def _init_browser(self):
        """初始化瀏覽器"""
        try:
            playwright = await async_playwright().start()

            self.browser = await playwright.chromium.launch(
                headless=self.headless,
                args=['--disable-blink-features=AutomationControlled']
            )

            # 建立新的上下文（類似無痕模式）
            context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )

            self.page = await context.new_page()

            logger.info("Playwright 瀏覽器初始化成功")

        except Exception as e:
            logger.error(f"初始化瀏覽器失敗: {e}")
            raise

    def _get_year_season_list(self, start_year: int = 102) -> List[tuple]:
        """
        生成年份和季度列表

        Args:
            start_year: 起始年份（民國年）

        Returns:
            List[tuple]: (民國年, 季度) 的列表
        """
        current_year = datetime.now().year - 1911
        current_month = datetime.now().month
        current_season = (current_month - 1) // 3 + 1

        year_season_list = []
        for year in range(start_year, current_year + 1):
            for season in range(1, 5):
                if year == current_year and season > current_season:
                    break
                year_season_list.append((year, season))

        return year_season_list

    async def fetch_balance_sheet(
        self,
        year: int,
        season: int
    ) -> Optional[List[Dict[str, Any]]]:
        """
        抓取特定季度的資產負債表（所有上市公司）

        Args:
            year: 民國年
            season: 季度 (1-4)

        Returns:
            List[Dict]: 該季度所有公司的資產負債表資料
        """
        try:
            self.request_count += 1

            # 訪問資產負債表頁面
            url = 'https://mops.twse.com.tw/mops/web/t163sb05'
            logger.info(f"訪問 MOPS 資產負債表頁面 ({year}Q{season})...")

            await self.page.goto(url, wait_until='networkidle', timeout=30000)

            # 等待頁面完全載入
            await asyncio.sleep(3)

            # 填寫年度 - 尋找 name="year" 的輸入框
            try:
                await self.page.wait_for_selector('input[name="year"]', timeout=10000)
                await self.page.fill('input[name="year"]', str(year))
                logger.info(f"已填入年度: {year}")
            except Exception as e:
                logger.error(f"找不到年度輸入框: {e}")
                # 嘗試其他選擇器
                await self.page.fill('input[placeholder*="年"]', str(year))

            # 選擇季度
            try:
                await self.page.select_option('select[name="season"]', str(season))
                logger.info(f"已選擇季度: {season}")
            except Exception as e:
                logger.error(f"找不到季度選擇器: {e}")

            # 點擊查詢按鈕
            try:
                # 嘗試多種方式找到查詢按鈕
                button_selectors = [
                    'input[type="button"][value*="查詢"]',
                    'button:has-text("查詢")',
                    'input[value="查詢"]',
                ]

                for selector in button_selectors:
                    try:
                        await self.page.click(selector, timeout=5000)
                        logger.info("已點擊查詢按鈕")
                        break
                    except:
                        continue

            except Exception as e:
                logger.error(f"找不到查詢按鈕: {e}")

            # 等待結果載入
            logger.info(f"等待 {year}Q{season} 資料載入...")
            await asyncio.sleep(REQUEST_DELAY + 3)

            # 等待表格出現
            try:
                await self.page.wait_for_selector('table', timeout=10000)
            except:
                logger.warning("等待表格超時")

            # 取得頁面 HTML
            page_content = await self.page.content()

            # 解析資料
            result = self._parse_balance_sheet(page_content, year, season)

            if result and len(result) > 0:
                self.success_count += 1
                logger.info(
                    f"成功抓取 {year}Q{season} - {len(result)} 家公司 "
                    f"(進度: {self.success_count}/{self.request_count})"
                )
            else:
                logger.warning(f"{year}Q{season} 無資料")

            return result

        except Exception as e:
            logger.error(f"抓取 {year}Q{season} 時發生錯誤: {e}")
            self.error_count += 1
            return None

    def _parse_balance_sheet(
        self,
        html_content: str,
        year: int,
        season: int
    ) -> Optional[List[Dict[str, Any]]]:
        """
        解析資產負債表 HTML

        Args:
            html_content: HTML 內容
            year: 民國年
            season: 季度

        Returns:
            List[Dict]: 解析後的所有公司資產負債表資料
        """
        try:
            soup = BeautifulSoup(html_content, 'lxml')

            # 檢查錯誤訊息
            error_messages = ['查無所需資料', '沒有符合條件', '無資料', '無法執行']
            page_text = soup.get_text()
            if any(msg in page_text for msg in error_messages):
                return None

            # 尋找資產負債表的表格
            tables = soup.find_all('table')
            if not tables:
                logger.warning("未找到任何表格")
                return None

            all_companies_data = []

            # 找到包含財務資料的主要表格
            for table in tables:
                # 檢查表格是否包含「公司代號」或財務相關資訊
                table_text = table.get_text()
                if '公司代號' not in table_text and '資產總額' not in table_text:
                    continue

                rows = table.find_all('tr')
                if len(rows) < 2:
                    continue

                current_company = None
                company_data = None

                for row in rows:
                    cells = row.find_all(['td', 'th'])

                    if len(cells) == 0:
                        continue

                    row_text = row.get_text(strip=True)

                    # 檢查是否為公司標題列
                    if '公司代號' in row_text or '公司名稱' in row_text:
                        # 儲存前一家公司的資料
                        if company_data and company_data['items']:
                            all_companies_data.append(company_data)

                        # 提取股票代碼
                        stock_code = None
                        for cell in cells:
                            text = cell.get_text(strip=True)
                            # 股票代碼通常是 4 位數字
                            if text.isdigit() and len(text) == 4:
                                stock_code = text
                                break

                        if stock_code:
                            current_company = stock_code
                            company_data = {
                                'stock_code': stock_code,
                                'year': year,
                                'season': season,
                                'crawl_time': datetime.now(),
                                'items': {}
                            }

                    # 解析財務數據
                    elif current_company and company_data and len(cells) >= 2:
                        item_name = cells[0].get_text(strip=True)
                        item_value = cells[1].get_text(strip=True)

                        if item_name and item_value and item_name != '會計項目':
                            # 清理數值
                            try:
                                clean_value = item_value.replace(',', '').replace(' ', '')
                                if clean_value and clean_value != '-':
                                    company_data['items'][item_name] = clean_value
                            except:
                                company_data['items'][item_name] = item_value

                # 儲存最後一家公司的資料
                if company_data and company_data['items']:
                    all_companies_data.append(company_data)

            logger.info(f"解析完成，共 {len(all_companies_data)} 家公司")
            return all_companies_data if all_companies_data else None

        except Exception as e:
            logger.error(f"解析 HTML 時發生錯誤: {e}")
            return None

    async def fetch_all_quarters(
        self,
        start_year: int = 102
    ) -> List[Dict[str, Any]]:
        """
        抓取所有季度的資產負債表

        Args:
            start_year: 起始年份（民國年）

        Returns:
            List[Dict]: 所有季度所有公司的資產負債表資料
        """
        if not self.browser:
            await self._init_browser()

        all_results = []
        year_season_list = self._get_year_season_list(start_year)

        logger.info(f"開始爬取 {len(year_season_list)} 個季度的資產負債表資料")
        start_time = time.time()

        for year, season in year_season_list:
            logger.info(f"處理 {year}Q{season}...")

            result = await self.fetch_balance_sheet(year, season)

            if result:
                all_results.extend(result)
                logger.info(f"{year}Q{season} 完成，目前共 {len(all_results)} 筆資料")
            else:
                logger.warning(f"{year}Q{season} 無資料")

            # 延遲避免請求過快
            await asyncio.sleep(REQUEST_DELAY)

        elapsed_time = time.time() - start_time
        logger.info(
            f"爬蟲完成！共處理 {self.request_count} 個請求，"
            f"成功 {self.success_count} 個季度，失敗 {self.error_count} 個，"
            f"取得 {len(all_results)} 筆公司資料，"
            f"耗時 {elapsed_time:.2f} 秒"
        )

        return all_results

    def get_statistics(self) -> Dict[str, Any]:
        """取得爬蟲統計資訊"""
        return {
            'total_requests': self.request_count,
            'success_count': self.success_count,
            'error_count': self.error_count,
            'success_rate': f"{(self.success_count / self.request_count * 100):.2f}%"
            if self.request_count > 0 else "0%"
        }

    async def close(self):
        """關閉瀏覽器"""
        if self.browser:
            await self.browser.close()
            logger.info("Playwright 瀏覽器已關閉")

    async def __aenter__(self):
        """進入非同步上下文管理器"""
        await self._init_browser()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """退出非同步上下文管理器"""
        await self.close()

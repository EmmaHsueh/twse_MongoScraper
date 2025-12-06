"""
MOPS 資產負債表爬蟲 - Selenium 版本
使用 Selenium 模擬瀏覽器操作，繞過 MOPS 的安全機制
"""
import time
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from config import REQUEST_DELAY

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MOPSSeleniumScraper:
    """MOPS 資產負債表爬蟲類別 - Selenium 版本"""

    def __init__(self, headless: bool = True):
        """
        初始化 Selenium 爬蟲

        Args:
            headless: 是否使用無頭模式（不顯示瀏覽器視窗）
        """
        self.headless = headless
        self.driver = None
        self.request_count = 0
        self.success_count = 0
        self.error_count = 0

    def _init_driver(self):
        """初始化 Chrome WebDriver"""
        try:
            chrome_options = Options()

            if self.headless:
                chrome_options.add_argument('--headless')
                chrome_options.add_argument('--disable-gpu')

            # 其他優化選項
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)

            # 使用 webdriver-manager 自動管理 chromedriver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)

            # 設定隱式等待
            self.driver.implicitly_wait(10)

            logger.info("Chrome WebDriver 初始化成功")

        except Exception as e:
            logger.error(f"初始化 WebDriver 失敗: {e}")
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

    def fetch_balance_sheet(
        self,
        stock_code: str,
        year: int,
        season: int
    ) -> Optional[Dict[str, Any]]:
        """
        抓取單一公司特定季度的資產負債表

        Args:
            stock_code: 股票代碼（不使用，使用 TYPEK='sii' 抓取所有上市公司）
            year: 民國年
            season: 季度 (1-4)

        Returns:
            Dict: 資產負債表資料，若失敗則返回 None
        """
        try:
            self.request_count += 1

            # 訪問資產負債表頁面
            url = 'https://mops.twse.com.tw/mops/web/t163sb05'
            logger.info(f"訪問 MOPS 資產負債表頁面...")
            self.driver.get(url)

            # 等待頁面載入
            time.sleep(2)

            # 填寫年度
            year_input = self.driver.find_element(By.NAME, 'year')
            year_input.clear()
            year_input.send_keys(str(year))

            # 選擇季度
            season_select = Select(self.driver.find_element(By.NAME, 'season'))
            season_select.select_by_value(str(season))

            # 點擊查詢按鈕
            submit_button = self.driver.find_element(By.CSS_SELECTOR, 'input[type="button"][value="查詢"]')
            submit_button.click()

            # 等待結果載入
            logger.info(f"等待 {year}Q{season} 資料載入...")
            time.sleep(REQUEST_DELAY + 2)

            # 取得頁面 HTML
            page_source = self.driver.page_source

            # 解析資料
            result = self._parse_balance_sheet(page_source, year, season)

            if result:
                self.success_count += 1
                logger.info(f"成功抓取 {year}Q{season} (進度: {self.success_count}/{self.request_count})")
            else:
                logger.debug(f"{year}Q{season} 無資料")

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
    ) -> Optional[Dict[str, Any]]:
        """
        解析資產負債表 HTML

        Args:
            html_content: HTML 內容
            year: 民國年
            season: 季度

        Returns:
            Dict: 解析後的資產負債表資料（包含所有公司）
        """
        try:
            soup = BeautifulSoup(html_content, 'lxml')

            # 檢查是否有錯誤訊息或無資料
            error_messages = ['查無所需資料', '沒有符合條件', '無資料', '無法執行']
            page_text = soup.get_text()
            if any(msg in page_text for msg in error_messages):
                return None

            # 尋找資產負債表的表格
            tables = soup.find_all('table', {'class': 'hasBorder'})
            if not tables:
                return None

            # 儲存所有公司的資料
            all_companies_data = []

            # 解析每個表格（每家公司一個表格）
            for table in tables:
                rows = table.find_all('tr')

                if len(rows) < 2:
                    continue

                # 第一列通常包含公司資訊
                first_row = rows[0]
                company_info = first_row.get_text(strip=True)

                # 提取股票代碼（通常格式為 "公司代號-公司名稱"）
                stock_code = None
                if '公司代號' in company_info or '-' in company_info:
                    parts = company_info.split('-')
                    if len(parts) >= 1:
                        stock_code = parts[0].replace('公司代號', '').replace(':', '').strip()

                if not stock_code:
                    continue

                # 解析財務數據
                balance_sheet_data = {
                    'stock_code': stock_code,
                    'year': year,
                    'season': season,
                    'crawl_time': datetime.now(),
                    'items': {}
                }

                # 遍歷表格行提取資產負債表項目
                for row in rows[1:]:  # 跳過第一列
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        item_name = cells[0].get_text(strip=True)
                        item_value = cells[1].get_text(strip=True)

                        # 過濾標題列和空值
                        if item_name and item_value and not item_name.startswith('會計項目'):
                            # 清理數值
                            try:
                                clean_value = item_value.replace(',', '').replace(' ', '')
                                if clean_value and clean_value != '-':
                                    balance_sheet_data['items'][item_name] = clean_value
                            except:
                                balance_sheet_data['items'][item_name] = item_value

                # 如果有解析到項目，加入結果
                if balance_sheet_data['items']:
                    all_companies_data.append(balance_sheet_data)

            # 返回所有公司的資料
            return all_companies_data if all_companies_data else None

        except Exception as e:
            logger.error(f"解析 HTML 時發生錯誤: {e}")
            return None

    def fetch_all_quarters(
        self,
        start_year: int = 102
    ) -> List[Dict[str, Any]]:
        """
        抓取所有季度的資產負債表（所有上市公司）

        Args:
            start_year: 起始年份（民國年）

        Returns:
            List[Dict]: 所有季度所有公司的資產負債表資料
        """
        if not self.driver:
            self._init_driver()

        all_results = []
        year_season_list = self._get_year_season_list(start_year)

        logger.info(f"開始爬取 {len(year_season_list)} 個季度的資產負債表資料")
        start_time = time.time()

        for year, season in year_season_list:
            logger.info(f"處理 {year}Q{season}...")

            result = self.fetch_balance_sheet('', year, season)

            if result:
                # result 是一個列表，包含該季度所有公司的資料
                all_results.extend(result)
                logger.info(f"{year}Q{season} 取得 {len(result)} 家公司資料，目前共 {len(all_results)} 筆")
            else:
                logger.warning(f"{year}Q{season} 無資料")

            # 延遲避免請求過快
            time.sleep(REQUEST_DELAY)

        elapsed_time = time.time() - start_time
        logger.info(
            f"爬蟲完成！共處理 {self.request_count} 個請求，"
            f"成功 {self.success_count} 個季度，失敗 {self.error_count} 個，"
            f"取得 {len(all_results)} 家公司資料，"
            f"耗時 {elapsed_time:.2f} 秒"
        )

        return all_results

    def get_statistics(self) -> Dict[str, Any]:
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

    def close(self):
        """關閉瀏覽器"""
        if self.driver:
            self.driver.quit()
            logger.info("Chrome WebDriver 已關閉")

    def __enter__(self):
        """進入上下文管理器"""
        self._init_driver()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文管理器"""
        self.close()

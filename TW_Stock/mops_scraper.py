#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MOPS 網站爬蟲 - 查詢財務報表資料
透過 Selenium 處理動態載入和反爬蟲機制
"""

import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
import pandas as pd


class MOPSScraper:
    def __init__(self, headless=False):
        """
        初始化爬蟲

        Args:
            headless: 是否使用無頭模式(背景執行)
        """
        self.url = "https://mops.twse.com.tw/mops/#/web/t163sb05"
        chrome_options = Options()

        if headless:
            chrome_options.add_argument('--headless')

        # 反爬蟲設定
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            '''
        })

        self.wait = WebDriverWait(self.driver, 20)

    def select_market(self, market_type):
        """
        選擇市場別

        Args:
            market_type: 市場類型
                - "sii": 上市
                - "otc": 上櫃
                - "rotc": 興櫃
                - "pub": 公開發行
        """
        try:
            # 等待市場別下拉選單載入
            market_select = self.wait.until(
                EC.presence_of_element_located((By.ID, "TYPEK"))
            )
            select = Select(market_select)
            select.select_by_value(market_type)
            time.sleep(0.5)
            print(f"✓ 已選擇市場別: {market_type}")
        except Exception as e:
            print(f"✗ 選擇市場別失敗: {e}")
            raise

    def input_year(self, year):
        """
        輸入年度

        Args:
            year: 民國年度 (例如: 113)
        """
        try:
            year_input = self.wait.until(
                EC.presence_of_element_located((By.ID, "year"))
            )
            # 清空現有內容
            year_input.clear()
            # 輸入年度
            year_input.send_keys(str(year))
            time.sleep(0.5)
            print(f"✓ 已輸入年度: {year}")
        except Exception as e:
            print(f"✗ 輸入年度失敗: {e}")
            raise

    def select_season(self, season):
        """
        選擇季別

        Args:
            season: 季別 (1, 2, 3, 4)
        """
        try:
            season_select = self.wait.until(
                EC.presence_of_element_located((By.ID, "season"))
            )
            select = Select(season_select)

            # 季別選項為「第一季」「第二季」「第三季」「第四季」
            season_map = {
                1: "第一季",
                2: "第二季",
                3: "第三季",
                4: "第四季"
            }

            season_text = season_map.get(season)
            if not season_text:
                raise ValueError(f"季別必須是 1, 2, 3 或 4,但得到: {season}")

            # 使用可見文字選擇
            select.select_by_visible_text(season_text)
            time.sleep(0.5)
            print(f"✓ 已選擇季別: {season_text}")
        except Exception as e:
            print(f"✗ 選擇季別失敗: {e}")
            raise

    def get_result_url_from_session_storage(self):
        """
        從 sessionStorage 中取得查詢結果的 URL

        Returns:
            str: 查詢結果的 URL
        """
        try:
            # 從 sessionStorage 取得 queryResultsSet
            query_results = self.driver.execute_script(
                "return sessionStorage.getItem('queryResultsSet');"
            )

            if query_results:
                result_data = json.loads(query_results)

                # 檢查結構: result.code 和 result.result.url
                if 'result' in result_data:
                    result_obj = result_data['result']

                    if result_obj.get('code') == 200 and 'result' in result_obj:
                        url = result_obj['result'].get('url')
                        if url:
                            print(f"✓ 成功取得結果 URL")
                            return url

                    # 顯示錯誤訊息
                    message = result_obj.get('message', '未知錯誤')
                    print(f"✗ 查詢失敗: {message}")
                    return None
                else:
                    print("✗ sessionStorage 結構不符合預期")
                    return None
            else:
                print("✗ sessionStorage 中沒有查詢結果")
                return None
        except Exception as e:
            print(f"✗ 取得結果 URL 失敗: {e}")
            import traceback
            traceback.print_exc()
            return None

    def click_query_button(self):
        """
        點擊查詢按鈕
        """
        try:
            # 找到查詢按鈕並點擊 (ID: searchBtn)
            query_button = self.wait.until(
                EC.element_to_be_clickable((By.ID, "searchBtn"))
            )
            query_button.click()
            print("✓ 已點擊查詢按鈕")
            time.sleep(2)  # 等待 sessionStorage 更新
        except Exception as e:
            print(f"✗ 點擊查詢按鈕失敗: {e}")
            raise

    def scrape_data(self, market_type="sii", year=113, season=3):
        """
        執行完整的爬蟲流程

        Args:
            market_type: 市場類型 (預設: sii 上市)
            year: 民國年度 (預設: 113)
            season: 季別 (預設: 3)

        Returns:
            str: 查詢結果的 URL,可用於進一步爬取資料
        """
        try:
            print(f"\n開始爬取 MOPS 資料...")
            print(f"參數: 市場別={market_type}, 年度={year}, 季別=Q{season}\n")

            # 1. 開啟網頁
            print("正在開啟網頁...")
            self.driver.get(self.url)
            time.sleep(3)  # 等待頁面載入

            # 2. 選擇條件
            self.select_market(market_type)
            self.input_year(year)
            self.select_season(season)

            # 3. 點擊查詢
            self.click_query_button()

            # 4. 從 sessionStorage 取得結果 URL
            result_url = self.get_result_url_from_session_storage()

            if result_url:
                print(f"\n✓ 查詢成功!")
                print(f"結果 URL: {result_url}")

                # 5. 開啟結果頁面
                print("\n正在開啟結果頁面...")
                self.driver.get(result_url)
                time.sleep(3)

                return result_url
            else:
                print("\n✗ 無法取得查詢結果")
                return None

        except Exception as e:
            print(f"\n✗ 爬蟲執行失敗: {e}")
            import traceback
            traceback.print_exc()
            return None

    def parse_table_data(self):
        """
        解析結果頁面的表格資料

        Returns:
            pd.DataFrame: 解析後的資料表
        """
        try:
            # 等待表格載入
            time.sleep(2)

            # 嘗試直接使用 pandas 讀取表格
            tables = pd.read_html(self.driver.page_source)

            if tables:
                print(f"\n✓ 成功解析表格,共 {len(tables)} 個表格")
                for i, table in enumerate(tables):
                    print(f"\n表格 {i+1} 維度: {table.shape}")
                    print(table.head())
                return tables
            else:
                print("\n✗ 未找到表格")
                return None

        except Exception as e:
            print(f"\n✗ 解析表格失敗: {e}")
            return None

    def save_to_csv(self, data, filename="mops_data.csv"):
        """
        將資料儲存為 CSV

        Args:
            data: DataFrame 或 list of DataFrames
            filename: 檔案名稱
        """
        try:
            if isinstance(data, list):
                # 如果有多個表格,儲存第一個主要表格
                if data:
                    data[0].to_csv(filename, index=False, encoding='utf-8-sig')
                    print(f"\n✓ 資料已儲存至: {filename}")
            else:
                data.to_csv(filename, index=False, encoding='utf-8-sig')
                print(f"\n✓ 資料已儲存至: {filename}")
        except Exception as e:
            print(f"\n✗ 儲存資料失敗: {e}")

    def close(self):
        """關閉瀏覽器"""
        if self.driver:
            self.driver.quit()
            print("\n瀏覽器已關閉")


def main():
    """主程式範例"""
    scraper = MOPSScraper(headless=False)  # headless=True 可在背景執行

    try:
        # 爬取資料 - 可以自訂參數
        # market_type: "sii"(上市), "otc"(上櫃), "rotc"(興櫃), "pub"(公開發行)
        result_url = scraper.scrape_data(
            market_type="sii",
            year=113,
            season=3
        )

        if result_url:
            # 解析表格資料
            tables = scraper.parse_table_data()

            if tables:
                # 儲存資料
                scraper.save_to_csv(tables, "mops_financial_data.csv")

        # 保持瀏覽器開啟以便查看 (可選)
        input("\n按 Enter 關閉瀏覽器...")

    finally:
        scraper.close()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MOPS 網站爬蟲 - 查詢 query6_1 頁面資料
針對 https://mops.twse.com.tw/mops/#/web/query6_1
爬取公司特定年月的資料
"""

import time
import json
import logging
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from mops_scraper import MOPSScraper
from mongodb_helper import MongoDBHelper

# 設定 logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('query6_1_scraper.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class Query61Scraper(MOPSScraper):
    """
    繼承 MOPSScraper，專門處理 query6_1 頁面
    """

    def __init__(self, headless=False):
        """初始化爬蟲"""
        super().__init__(headless)
        # 覆寫 URL
        self.url = "https://mops.twse.com.tw/mops/#/web/query6_1"

    def input_company_code(self, company_code):
        """
        輸入公司代號

        Args:
            company_code: 公司代號 (例如: 2330)
        """
        try:
            # 使用 JavaScript 先清空並輸入新的公司代號（合併操作）
            self.driver.execute_script(f"""
                var input = document.getElementById('companyId');
                if (input) {{
                    input.value = '{company_code}';
                    input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                }}
            """)
            print(f"✓ 已輸入公司代號: {company_code}")
        except Exception as e:
            print(f"✗ 輸入公司代號失敗: {e}")
            raise

    def select_custom_date(self):
        """
        選擇「自訂」時間選項
        """
        try:
            # 使用 JavaScript 直接點擊元素（不需要額外等待）
            self.driver.execute_script("""
                var radio = document.getElementById('dataType_2');
                if (radio) {
                    radio.click();
                    return true;
                }
                return false;
            """)
            print("✓ 已選擇「自訂」時間")
        except Exception as e:
            print(f"✗ 選擇自訂時間失敗: {e}")
            raise

    def input_custom_year(self, year):
        """
        輸入民國年度（自訂模式）

        Args:
            year: 民國年度 (例如: 114)
        """
        try:
            # 使用 JavaScript 直接設置值
            self.driver.execute_script(f"""
                var yearInput = document.getElementById('year');
                if (yearInput) {{
                    yearInput.value = '{year}';
                    yearInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    yearInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
                }}
            """)
            print(f"✓ 已輸入年度: {year}")
        except Exception as e:
            print(f"✗ 輸入年度失敗: {e}")
            raise

    def wait_for_loading_to_disappear(self, timeout=5):
        """
        等待 loading 元素消失（優化版）

        Args:
            timeout: 最長等待秒數
        """
        try:
            # 使用更高效的等待策略
            start_time = time.time()
            while time.time() - start_time < timeout:
                loading_visible = self.driver.execute_script("""
                    var loadingElements = document.querySelectorAll('.loadingElement');
                    for (var i = 0; i < loadingElements.length; i++) {
                        var style = window.getComputedStyle(loadingElements[i]);
                        if (style.display !== 'none' && style.visibility !== 'hidden') {
                            return true;
                        }
                    }
                    return false;
                """)

                if not loading_visible:
                    print("  已等待 loading 消失")
                    return

                time.sleep(0.05)  # 縮短檢查間隔，加快響應

        except Exception as e:
            print(f"  等待 loading 時發生錯誤: {e}")

    def click_query_button_with_retry(self, max_retries=3):
        """
        點擊查詢按鈕（帶重試機制，優化版）

        Args:
            max_retries: 最大重試次數
        """
        for attempt in range(max_retries):
            try:
                # 等待 loading 消失
                self.wait_for_loading_to_disappear()

                # 使用 JavaScript 直接點擊，避免被遮擋
                clicked = self.driver.execute_script("""
                    var btn = document.getElementById('searchBtn');
                    if (btn) {
                        btn.click();
                        return true;
                    }
                    return false;
                """)

                if clicked:
                    print("✓ 已點擊查詢按鈕")
                    time.sleep(0.3)  # 大幅減少等待時間，改為依賴後續 sessionStorage 檢查
                    return True
                else:
                    print(f"✗ 找不到查詢按鈕 (嘗試 {attempt + 1}/{max_retries})")

            except Exception as e:
                print(f"✗ 點擊查詢按鈕失敗 (嘗試 {attempt + 1}/{max_retries}): {e}")

            # 如果不是最後一次嘗試，等待後重試
            if attempt < max_retries - 1:
                print(f"  等待 1 秒後重試...")
                time.sleep(1)  # 減少重試等待時間

        # 所有嘗試都失敗
        raise Exception("點擊查詢按鈕失敗，已達最大重試次數")

    def input_custom_month(self, month):
        """
        選擇月份（自訂模式 - 使用下拉式選單）

        Args:
            month: 月份 (1-12)
        """
        try:
            # 使用 JavaScript 直接設置值
            month_text = f"{month}月"
            self.driver.execute_script(f"""
                var monthSelect = document.getElementById('month');
                if (monthSelect) {{
                    var options = monthSelect.options;
                    for (var i = 0; i < options.length; i++) {{
                        if (options[i].text === '{month_text}') {{
                            monthSelect.selectedIndex = i;
                            monthSelect.dispatchEvent(new Event('change', {{ bubbles: true }}));
                            break;
                        }}
                    }}
                }}
            """)
            print(f"✓ 已選擇月份: {month_text}")
        except Exception as e:
            print(f"✗ 選擇月份失敗: {e}")
            raise

    def get_query_results_from_session_storage(self):
        """
        從 sessionStorage 中取得 queryResultsSet 的資料

        Returns:
            dict: 包含 data 和 titles 的字典，失敗則返回 None
        """
        try:
            # 從 sessionStorage 取得 queryResultsSet
            query_results = self.driver.execute_script(
                "return sessionStorage.getItem('queryResultsSet');"
            )

            if query_results:
                result_data = json.loads(query_results)
                print(f"✓ 成功取得 sessionStorage 資料")

                # 檢查結構：result.result.data 和 result.result.titles
                if 'result' in result_data and 'result' in result_data['result']:
                    inner_result = result_data['result']['result']

                    if 'data' in inner_result and 'titles' in inner_result:
                        data = inner_result['data']
                        titles = inner_result['titles']

                        print(f"✓ 查詢結果包含 {len(data)} 筆資料")

                        return {
                            'data': data,
                            'titles': titles,
                            'year': inner_result.get('year', ''),
                            'month': inner_result.get('month', ''),
                            'marketName': inner_result.get('marketName', ''),
                            'companyAbbreviation': inner_result.get('companyAbbreviation', '')
                        }
                    else:
                        print("⚠ 找不到 data 或 titles 欄位")
                        return None
                else:
                    print("⚠ sessionStorage 中無結果或格式不符")
                    print(f"資料結構: {result_data}")
                    return None
            else:
                print("✗ sessionStorage 中沒有 queryResultsSet")
                return None

        except json.JSONDecodeError as e:
            print(f"✗ JSON 解析失敗: {e}")
            return None
        except Exception as e:
            print(f"✗ 取得查詢結果失敗: {e}")
            import traceback
            traceback.print_exc()
            return None

    def scrape_company_data(self, company_code, year, month):
        """
        爬取單一公司的資料（優化版）

        Args:
            company_code: 公司代號
            year: 民國年度
            month: 月份

        Returns:
            dict: 包含公司代號、年月及查詢結果的字典，失敗則返回 None
        """
        start_time = time.time()  # 記錄開始時間
        try:
            print(f"\n{'='*60}")
            print(f"開始爬取公司 {company_code} - {year}年{month}月資料")
            print(f"{'='*60}")

            # 1. 開啟網頁（如果尚未開啟）
            current_url = self.driver.current_url
            if "query6_1" not in current_url:
                print("正在開啟網頁...")
                self.driver.get(self.url)
                time.sleep(1)  # 減少初始等待時間（從 2 秒降到 1 秒）

            # 2. 先選擇自訂時間（在輸入公司代號之前）
            self.select_custom_date()

            # 3. 輸入公司代號
            self.input_company_code(company_code)

            # 4. 輸入年度和月份
            self.input_custom_year(year)
            self.input_custom_month(month)

            # 5. 點擊查詢按鈕（使用重試機制）
            self.click_query_button_with_retry()

            # 6. 等待 sessionStorage 更新（使用智能等待，優化版）
            max_wait = 5  # 最多等待 5 秒（給予足夠時間但檢查更頻繁）
            start_time = time.time()
            results = None

            while time.time() - start_time < max_wait:
                results = self.get_query_results_from_session_storage()
                if results:
                    break
                time.sleep(0.05)  # 縮短檢查間隔，從 0.2 秒降到 0.05 秒

            if results:
                elapsed_time = time.time() - start_time
                print(f"✓ 公司 {company_code} 查詢成功，共 {len(results['data'])} 筆明細")
                logger.info(f"爬取成功 | 股票代碼: {company_code} | 年月: {year}年{month}月 | 花費時間: {elapsed_time:.2f}秒 | 資料筆數: {len(results['data'])}")

                # 返回包含完整資訊的字典
                return {
                    "公司代號": company_code,
                    "查詢年度": year,
                    "查詢月份": month,
                    "市場別": results.get('marketName', ''),
                    "公司簡稱": results.get('companyAbbreviation', ''),
                    "標題": results['titles'],
                    "明細資料": results['data'],
                    "爬取時間": elapsed_time
                }
            else:
                elapsed_time = time.time() - start_time
                print(f"⚠ 公司 {company_code} 無資料或查詢失敗")
                logger.warning(f"爬取失敗 | 股票代碼: {company_code} | 年月: {year}年{month}月 | 花費時間: {elapsed_time:.2f}秒 | 原因: 無資料")
                return None

        except Exception as e:
            elapsed_time = time.time() - start_time
            print(f"✗ 爬取公司 {company_code} 資料失敗: {e}")
            logger.error(f"爬取錯誤 | 股票代碼: {company_code} | 年月: {year}年{month}月 | 花費時間: {elapsed_time:.2f}秒 | 錯誤: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    def parse_titles_to_columns(self, titles):
        """
        將 titles 轉換為欄位名稱列表（處理巢狀結構）

        Args:
            titles: titles 陣列

        Returns:
            list: 欄位名稱列表
        """
        columns = []

        for title in titles:
            main = title.get('main', '')

            # 如果有 sub，展開 sub
            if title.get('sub') and len(title['sub']) > 0:
                for sub in title['sub']:
                    sub_main = sub.get('main', '')
                    columns.append(f"{main}-{sub_main}")
            else:
                columns.append(main)

        return columns

    def save_to_mongodb(self, mongo_helper, data):
        """
        將資料儲存到 MongoDB（每筆明細分開存）

        Args:
            mongo_helper: MongoDBHelper 實例
            data: 要儲存的資料字典

        Returns:
            bool: 是否成功
        """
        try:
            collection = mongo_helper.db['內部人持股異動事後申報表']

            # 解析標題
            columns = self.parse_titles_to_columns(data['標題'])
            print(f"  欄位數: {len(columns)}")

            # 基本資訊
            base_info = {
                "公司代號": data["公司代號"],
                "查詢年度": data["查詢年度"],
                "查詢月份": data["查詢月份"],
                "市場別": data["市場別"],
                "公司簡稱": data["公司簡稱"],
            }

            # 處理每一筆明細資料
            success_count = 0
            for row_index, row_data in enumerate(data['明細資料']):
                # 建立單筆明細文件
                document = base_info.copy()

                # 將 row_data 與 columns 對應
                for col_index, value in enumerate(row_data):
                    if col_index < len(columns):
                        column_name = columns[col_index]
                        document[column_name] = value

                try:
                    # 直接插入，不使用唯一鍵，讓 MongoDB 使用預設的 _id
                    collection.insert_one(document)
                    success_count += 1
                except Exception as e:
                    print(f"  ✗ 第 {row_index + 1} 筆明細存入失敗: {e}")

            print(f"✓ 公司 {data['公司代號']} 共存入 {success_count}/{len(data['明細資料'])} 筆明細")
            return True

        except Exception as e:
            print(f"✗ 存入 MongoDB 失敗: {e}")
            import traceback
            traceback.print_exc()
            return False


def generate_year_month_list(start_year, start_month, end_year, end_month):
    """
    生成年月列表

    Args:
        start_year: 起始民國年
        start_month: 起始月份
        end_year: 結束民國年
        end_month: 結束月份

    Returns:
        list: [(year, month), ...] 的列表
    """
    year_month_list = []
    for year in range(start_year, end_year + 1):
        start_m = start_month if year == start_year else 1
        end_m = end_month if year == end_year else 12
        for month in range(start_m, end_m + 1):
            year_month_list.append((year, month))
    return year_month_list


def main():
    """主程式"""
    # 初始化
    print("\n" + "="*60)
    print("MOPS Query6_1 爬蟲程式 - 內部人持股異動事後申報表")
    print("="*60 + "\n")

    logger.info("="*60)
    logger.info("程式啟動 - 內部人持股異動事後申報表爬蟲")
    logger.info("="*60)

    # 連接 MongoDB
    print("正在連接 MongoDB...")
    mongo_helper = MongoDBHelper()

    # 顯示選單
    print("\n請選擇爬取模式：")
    print("1. 完整爬取（所有上市上櫃公司）")
    print("2. 部分爬取（指定索引範圍）")
    print("3. 個別爬取（輸入特定公司代號）")

    choice = input("\n請輸入選項 (1/2/3): ").strip()

    # 根據選擇決定要爬取的公司代號
    all_codes = []

    if choice == "1":
        # 完整爬取
        print("\n正在取得所有公司代號...")
        sii_codes = mongo_helper.get_all_company_codes("sii")  # 上市
        otc_codes = mongo_helper.get_all_company_codes("otc")  # 上櫃
        all_codes = sii_codes + otc_codes
        print(f"\n總共需要爬取 {len(all_codes)} 家公司")
        print(f"  - 上市: {len(sii_codes)} 家")
        print(f"  - 上櫃: {len(otc_codes)} 家")

    elif choice == "2":
        # 部分爬取
        print("\n正在取得所有公司代號...")
        sii_codes = mongo_helper.get_all_company_codes("sii")  # 上市
        otc_codes = mongo_helper.get_all_company_codes("otc")  # 上櫃
        all_available_codes = sii_codes + otc_codes

        print(f"\n可用公司總數: {len(all_available_codes)}")
        print(f"  - 上市: {len(sii_codes)} 家")
        print(f"  - 上櫃: {len(otc_codes)} 家")

        # 讓使用者選擇範圍
        while True:
            try:
                start_idx = int(input(f"\n請輸入起始索引 (0-{len(all_available_codes)-1}): "))
                end_idx = int(input(f"請輸入結束索引 (0-{len(all_available_codes)-1}): "))

                if 0 <= start_idx < len(all_available_codes) and 0 <= end_idx < len(all_available_codes) and start_idx <= end_idx:
                    all_codes = all_available_codes[start_idx:end_idx+1]
                    print(f"\n將爬取 {len(all_codes)} 家公司（索引 {start_idx} 到 {end_idx}）")
                    print(f"公司代號: {', '.join(all_codes[:10])}{'...' if len(all_codes) > 10 else ''}")
                    break
                else:
                    print("✗ 索引範圍無效，請重新輸入")
            except ValueError:
                print("✗ 請輸入有效的數字")

    elif choice == "3":
        # 個別爬取
        print("\n請輸入要爬取的公司代號")
        codes_input = input("多個代號請用逗號分隔 (例如: 2330,1101,2317): ").strip()
        all_codes = [code.strip() for code in codes_input.split(",") if code.strip()]

        if all_codes:
            print(f"\n將爬取 {len(all_codes)} 家公司: {', '.join(all_codes)}")
        else:
            print("✗ 沒有輸入有效的公司代號")
            mongo_helper.close()
            return

    else:
        print("✗ 無效的選項")
        mongo_helper.close()
        return

    # 確認是否繼續
    confirm = input("\n確定要開始爬取嗎? (y/n): ").strip().lower()
    if confirm != 'y':
        print("已取消爬取")
        mongo_helper.close()
        return

    # 設定爬取時間範圍：2012年1月 到 2025年11月
    # 2012年 = 民國101年，2025年 = 民國114年
    start_year, start_month = 101, 1  # 2012年1月
    end_year, end_month = 114, 11     # 2025年11月

    year_month_list = generate_year_month_list(start_year, start_month, end_year, end_month)

    print(f"\n爬取時間範圍: 民國 {start_year} 年 {start_month} 月 到 {end_year} 年 {end_month} 月")
    print(f"總共 {len(year_month_list)} 個月份")
    logger.info(f"爬取時間範圍: {start_year}/{start_month} - {end_year}/{end_month}，共 {len(year_month_list)} 個月份")

    # 初始化爬蟲（headless=True 用於背景執行）
    scraper = Query61Scraper(headless=False)

    # 全域統計變數
    total_success_count = 0
    total_fail_count = 0
    total_mongodb_success_count = 0

    try:
        # 開啟網頁一次
        print("\n正在開啟 MOPS 網站...")
        scraper.driver.get(scraper.url)
        time.sleep(1.5)  # 減少初始等待時間（從 2 秒降到 1.5 秒）

        # 遍歷所有年月
        for year_month_idx, (year, month) in enumerate(year_month_list, 1):
            month_start_time = time.time()  # 記錄該月開始時間

            print("\n" + "="*80)
            print(f"開始爬取 {year} 年 {month} 月資料 ({year_month_idx}/{len(year_month_list)})")
            print("="*80)
            logger.info(f"{'='*60}")
            logger.info(f"開始爬取 {year} 年 {month} 月資料 (進度: {year_month_idx}/{len(year_month_list)})")
            logger.info(f"{'='*60}")

            # 該月統計變數
            month_success_count = 0
            month_fail_count = 0
            month_mongodb_success_count = 0
            month_success_codes = []
            month_fail_codes = []

            # 批次爬取該月所有公司
            for i, company_code in enumerate(all_codes, 1):
                print(f"\n[{year}年{month}月] 進度: {i}/{len(all_codes)} - 公司代號: {company_code}")

                try:
                    # 爬取資料
                    data = scraper.scrape_company_data(company_code, year, month)

                    if data:
                        month_success_count += 1
                        month_success_codes.append(company_code)

                        # 存入 MongoDB
                        if scraper.save_to_mongodb(mongo_helper, data):
                            month_mongodb_success_count += 1
                    else:
                        month_fail_count += 1
                        month_fail_codes.append(company_code)

                    # 每爬取一家公司後暫停一下，避免被封鎖
                    # 優化隨機延遲時間，在速度與穩定性間取得平衡
                    import random
                    delay = random.uniform(0.2, 0.6)  # 0.2-0.6 秒隨機延遲（進一步優化）
                    time.sleep(delay)

                except Exception as e:
                    print(f"✗ 處理公司 {company_code} 時發生錯誤: {e}")
                    month_fail_count += 1
                    month_fail_codes.append(company_code)
                    continue

            # 計算該月總耗時
            month_elapsed_time = time.time() - month_start_time

            # 顯示該月統計
            print("\n" + "-"*80)
            print(f"{year} 年 {month} 月 爬取完成")
            print("-"*80)
            print(f"成功爬取: {month_success_count} 家")
            print(f"成功存入 MongoDB: {month_mongodb_success_count} 家")
            print(f"失敗: {month_fail_count} 家")
            print(f"總計: {len(all_codes)} 家")
            print(f"總耗時: {month_elapsed_time:.2f} 秒 ({month_elapsed_time/60:.2f} 分鐘)")
            print("-"*80)

            # 記錄該月統計到 log
            logger.info(f"{'='*60}")
            logger.info(f"{year} 年 {month} 月 爬取統計")
            logger.info(f"總耗時: {month_elapsed_time:.2f} 秒 ({month_elapsed_time/60:.2f} 分鐘)")
            logger.info(f"成功: {month_success_count} 家，失敗: {month_fail_count} 家，總計: {len(all_codes)} 家")
            logger.info(f"成功存入 MongoDB: {month_mongodb_success_count} 家")
            # logger.info(f"成功公司代碼: {', '.join(month_success_codes) if month_success_codes else '無'}")
            logger.info(f"失敗公司代碼: {', '.join(month_fail_codes) if month_fail_codes else '無'}")
            logger.info(f"{'='*60}")

            # 累加到全域統計
            total_success_count += month_success_count
            total_fail_count += month_fail_count
            total_mongodb_success_count += month_mongodb_success_count

        # 顯示總體統計
        print("\n" + "="*80)
        print("所有月份爬取完成")
        print("="*80)
        print(f"總成功爬取: {total_success_count} 筆")
        print(f"總成功存入 MongoDB: {total_mongodb_success_count} 筆")
        print(f"總失敗: {total_fail_count} 筆")
        print(f"總計: {len(all_codes) * len(year_month_list)} 筆（{len(all_codes)} 家公司 × {len(year_month_list)} 個月）")
        print("="*80)

        logger.info(f"{'='*60}")
        logger.info("所有月份爬取完成 - 總體統計")
        logger.info(f"總成功: {total_success_count} 筆，總失敗: {total_fail_count} 筆")
        logger.info(f"總成功存入 MongoDB: {total_mongodb_success_count} 筆")
        logger.info(f"總計: {len(all_codes) * len(year_month_list)} 筆")
        logger.info(f"{'='*60}")

        # 保持瀏覽器開啟以便查看
        input("\n按 Enter 關閉瀏覽器...")

    except KeyboardInterrupt:
        print("\n\n使用者中斷程式")
    finally:
        scraper.close()
        mongo_helper.close()


if __name__ == "__main__":
    main()

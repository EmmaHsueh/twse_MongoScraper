#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MOPS 網站爬蟲 - 使用 Tor 代理
針對 https://mops.twse.com.tw/mops/#/web/query6_1
"""

import time
from selenium.webdriver.chrome.options import Options
from query6_1_scraper import Query61Scraper, main as original_main
from mops_scraper import MOPSScraper


class Query61ScraperWithTor(Query61Scraper):
    """
    使用 Tor 代理的爬蟲
    """

    def __init__(self, headless=False, tor_host='127.0.0.1', tor_port=9050):
        """
        初始化爬蟲（使用 Tor）

        Args:
            headless: 是否使用無頭模式
            tor_host: Tor SOCKS 代理主機
            tor_port: Tor SOCKS 代理端口
        """
        # 不調用父類的 __init__，而是自己初始化
        self.url = "https://mops.twse.com.tw/mops/#/web/query6_1"
        self.tor_host = tor_host
        self.tor_port = tor_port

        chrome_options = Options()

        if headless:
            chrome_options.add_argument('--headless')

        # === Tor 代理設置 ===
        chrome_options.add_argument(f'--proxy-server=socks5://{tor_host}:{tor_port}')
        print(f"✓ 已設置 Tor 代理: socks5://{tor_host}:{tor_port}")

        # 反爬蟲設定
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        # 初始化 Selenium
        from selenium import webdriver
        from selenium.webdriver.support.ui import WebDriverWait

        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            '''
        })

        self.wait = WebDriverWait(self.driver, 20)

    def verify_tor_connection(self):
        """
        驗證 Tor 連接是否正常
        """
        try:
            print("\n正在驗證 Tor 連接...")
            self.driver.get('https://api.ipify.org?format=json')
            time.sleep(2)

            body_text = self.driver.find_element('tag name', 'body').text
            import json
            ip_info = json.loads(body_text)
            ip = ip_info.get('ip', 'Unknown')

            print(f"✓ 當前使用的 IP: {ip}")
            print("✓ Tor 連接驗證成功")

            return ip

        except Exception as e:
            print(f"✗ Tor 連接驗證失敗: {e}")
            return None

    def change_tor_identity(self):
        """
        更換 Tor 身份（獲取新的 IP）
        注意：需要配置 Tor 控制端口才能使用此功能
        """
        print("提示：如需自動更換 IP，請配置 Tor 控制端口")
        print("簡單方法：重啟 Tor 服務即可獲得新 IP")

    def wait_for_loading_to_disappear(self, timeout=10):
        """
        等待 loading 元素消失（Tor 專用 - 更長等待時間）

        Args:
            timeout: 最長等待秒數
        """
        try:
            # Tor 較慢，使用更長的等待時間
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

                time.sleep(0.3)  # Tor 較慢，增加檢查間隔

        except Exception as e:
            print(f"  等待 loading 時發生錯誤: {e}")

    def click_query_button_with_retry(self, max_retries=5):
        """
        點擊查詢按鈕（Tor 專用 - 增加重試次數和等待時間）

        Args:
            max_retries: 最大重試次數
        """
        for attempt in range(max_retries):
            try:
                # 等待 loading 消失
                self.wait_for_loading_to_disappear()

                # 額外等待，確保頁面完全載入
                time.sleep(1)

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
                    time.sleep(3)  # Tor 較慢，需要更長等待時間
                    return True
                else:
                    print(f"✗ 找不到查詢按鈕 (嘗試 {attempt + 1}/{max_retries})")
                    # 嘗試印出當前頁面狀態以便除錯
                    page_ready = self.driver.execute_script("return document.readyState")
                    print(f"  頁面狀態: {page_ready}")

            except Exception as e:
                print(f"✗ 點擊查詢按鈕失敗 (嘗試 {attempt + 1}/{max_retries}): {e}")

            # 如果不是最後一次嘗試，等待後重試
            if attempt < max_retries - 1:
                print(f"  等待 3 秒後重試...")
                time.sleep(3)  # Tor 較慢，增加重試等待時間

        # 所有嘗試都失敗
        raise Exception("點擊查詢按鈕失敗，已達最大重試次數")

    def scrape_company_data(self, company_code, year, month):
        """
        爬取單一公司的資料（Tor 專用版本）

        Args:
            company_code: 公司代號
            year: 民國年度
            month: 月份

        Returns:
            dict: 包含公司代號、年月及查詢結果的字典，失敗則返回 None
        """
        try:
            print(f"\n{'='*60}")
            print(f"開始爬取公司 {company_code} - {year}年{month}月資料")
            print(f"{'='*60}")

            # 1. 開啟網頁（如果尚未開啟）
            current_url = self.driver.current_url
            if "query6_1" not in current_url:
                print("正在開啟網頁...")
                self.driver.get(self.url)
                time.sleep(5)  # Tor 較慢，增加等待時間

            # 額外等待確保頁面完全載入
            time.sleep(2)

            # 2. 先選擇自訂時間（在輸入公司代號之前）
            self.select_custom_date()

            # 3. 輸入公司代號
            self.input_company_code(company_code)

            # 4. 輸入年度和月份
            self.input_custom_year(year)
            self.input_custom_month(month)

            # 5. 點擊查詢按鈕（使用重試機制）
            self.click_query_button_with_retry()

            # 6. 等待 sessionStorage 更新（Tor 較慢）
            max_wait = 5  # 最多等待 5 秒
            start_time = time.time()
            results = None

            while time.time() - start_time < max_wait:
                results = self.get_query_results_from_session_storage()
                if results:
                    break
                time.sleep(0.5)  # Tor 較慢，增加檢查間隔

            if results:
                print(f"✓ 公司 {company_code} 查詢成功，共 {len(results['data'])} 筆明細")
                # 返回包含完整資訊的字典
                return {
                    "公司代號": company_code,
                    "查詢年度": year,
                    "查詢月份": month,
                    "市場別": results.get('marketName', ''),
                    "公司簡稱": results.get('companyAbbreviation', ''),
                    "標題": results['titles'],
                    "明細資料": results['data'],
                }
            else:
                print(f"⚠ 公司 {company_code} 無資料或查詢失敗")
                return None

        except Exception as e:
            print(f"✗ 爬取公司 {company_code} 資料失敗: {e}")
            import traceback
            traceback.print_exc()
            return None

    def save_to_mongodb(self, mongo_helper, data):
        """
        將資料儲存到 MongoDB（存入 Tor 專用 collection）

        Args:
            mongo_helper: MongoDBHelper 實例
            data: 要儲存的資料字典

        Returns:
            bool: 是否成功
        """
        try:
            # 使用 Tor 專用的 collection
            collection = mongo_helper.db['內部人持股異動事後申報表_tor']

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

            print(f"✓ 公司 {data['公司代號']} 共存入 {success_count}/{len(data['明細資料'])} 筆明細到 Tor collection")
            return True

        except Exception as e:
            print(f"✗ 存入 MongoDB 失敗: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """主程式 - Tor 版本"""
    print("\n" + "="*60)
    print("MOPS Query6_1 爬蟲程式 - Tor 代理版本")
    print("="*60 + "\n")

    print("⚠ 注意事項：")
    print("1. 確保 Tor 服務已啟動")
    print("2. Tor 連接速度較慢，請耐心等待")
    print("3. 建議使用部分爬取模式，避免爬取時間過長")
    print("")

    # 確認 Tor 是否運行
    confirm = input("確認 Tor 已啟動？(y/n): ").strip().lower()
    if confirm != 'y':
        print("\n請先啟動 Tor 服務：")
        print("  方法 1: tor")
        print("  方法 2: nohup tor > tor.log 2>&1 &")
        return

    # 使用 Tor 版本的爬蟲
    from mongodb_helper import MongoDBHelper

    # 連接 MongoDB
    print("\n正在連接 MongoDB...")
    mongo_helper = MongoDBHelper()

    # 顯示選單（與原版相同）
    print("\n請選擇爬取模式：")
    print("1. 完整爬取（所有上市上櫃公司）⚠ 不建議使用 Tor")
    print("2. 部分爬取（指定索引範圍）✓ 推薦")
    print("3. 個別爬取（輸入特定公司代號）✓ 推薦")

    choice = input("\n請輸入選項 (1/2/3): ").strip()

    # 根據選擇決定要爬取的公司代號
    all_codes = []

    if choice == "1":
        print("\n⚠ 警告：完整爬取可能需要數小時，且 Tor 連接可能不穩定")
        confirm = input("確定要繼續嗎？(y/n): ").strip().lower()
        if confirm != 'y':
            print("已取消")
            mongo_helper.close()
            return

        print("\n正在取得所有公司代號...")
        sii_codes = mongo_helper.get_all_company_codes("sii")
        otc_codes = mongo_helper.get_all_company_codes("otc")
        all_codes = sii_codes + otc_codes
        print(f"\n總共需要爬取 {len(all_codes)} 家公司")

    elif choice == "2":
        print("\n正在取得所有公司代號...")
        sii_codes = mongo_helper.get_all_company_codes("sii")
        otc_codes = mongo_helper.get_all_company_codes("otc")
        all_available_codes = sii_codes + otc_codes

        print(f"\n可用公司總數: {len(all_available_codes)}")

        while True:
            try:
                start_idx = int(input(f"\n請輸入起始索引 (0-{len(all_available_codes)-1}): "))
                end_idx = int(input(f"請輸入結束索引 (0-{len(all_available_codes)-1}): "))

                if 0 <= start_idx < len(all_available_codes) and 0 <= end_idx < len(all_available_codes) and start_idx <= end_idx:
                    all_codes = all_available_codes[start_idx:end_idx+1]
                    print(f"\n將爬取 {len(all_codes)} 家公司")
                    break
                else:
                    print("✗ 索引範圍無效")
            except ValueError:
                print("✗ 請輸入有效的數字")

    elif choice == "3":
        codes_input = input("\n請輸入公司代號（多個以逗號分隔）: ").strip()
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

    # 確認開始
    confirm = input("\n確定要開始爬取嗎? (y/n): ").strip().lower()
    if confirm != 'y':
        print("已取消爬取")
        mongo_helper.close()
        return

    # 設定參數
    year = 114
    month = 10

    print(f"\n爬取時間: 民國 {year} 年 {month} 月")

    # 初始化 Tor 爬蟲
    print("\n正在初始化 Tor 爬蟲...")
    scraper = Query61ScraperWithTor(headless=False)

    # 驗證 Tor 連接
    tor_ip = scraper.verify_tor_connection()
    if not tor_ip:
        print("\n✗ Tor 連接驗證失敗，請檢查 Tor 服務")
        scraper.close()
        mongo_helper.close()
        return

    # 統計
    success_count = 0
    fail_count = 0
    mongodb_success_count = 0

    try:
        print("\n正在開啟 MOPS 網站...")
        scraper.driver.get(scraper.url)
        time.sleep(5)  # Tor 較慢，多等待一些

        # 批次爬取
        for i, company_code in enumerate(all_codes, 1):
            print(f"\n進度: {i}/{len(all_codes)}")

            try:
                data = scraper.scrape_company_data(company_code, year, month)

                if data:
                    success_count += 1

                    if scraper.save_to_mongodb(mongo_helper, data):
                        mongodb_success_count += 1
                else:
                    fail_count += 1

                # Tor 較慢，增加延遲
                import random
                delay = random.uniform(3, 6)
                time.sleep(delay)

            except Exception as e:
                print(f"✗ 處理公司 {company_code} 時發生錯誤: {e}")
                fail_count += 1
                continue

        # 顯示統計
        print("\n" + "="*60)
        print("爬取完成")
        print("="*60)
        print(f"成功爬取: {success_count} 家")
        print(f"成功存入 MongoDB: {mongodb_success_count} 家")
        print(f"失敗: {fail_count} 家")
        print(f"總計: {len(all_codes)} 家")

        input("\n按 Enter 關閉瀏覽器...")

    except KeyboardInterrupt:
        print("\n\n使用者中斷程式")
    finally:
        scraper.close()
        mongo_helper.close()


if __name__ == "__main__":
    main()

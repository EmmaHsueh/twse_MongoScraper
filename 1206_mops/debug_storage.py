#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
偵錯腳本 - 檢查 sessionStorage 的內容
"""

import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options


def debug_session_storage():
    """執行查詢並檢查 sessionStorage"""

    chrome_options = Options()
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': '''
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
        '''
    })

    wait = WebDriverWait(driver, 20)

    try:
        url = "https://mops.twse.com.tw/mops/#/web/t163sb05"
        print(f"開啟網頁: {url}")
        driver.get(url)
        time.sleep(3)

        # 選擇市場別
        print("\n選擇市場別...")
        market_select = wait.until(EC.presence_of_element_located((By.ID, "TYPEK")))
        Select(market_select).select_by_value("sii")
        time.sleep(0.5)

        # 輸入年度
        print("輸入年度...")
        year_input = wait.until(EC.presence_of_element_located((By.ID, "year")))
        year_input.clear()
        year_input.send_keys("113")
        time.sleep(0.5)

        # 選擇季別
        print("選擇季別...")
        season_select = wait.until(EC.presence_of_element_located((By.ID, "season")))
        Select(season_select).select_by_visible_text("第三季")
        time.sleep(0.5)

        # 點擊查詢
        print("點擊查詢按鈕...")
        query_button = wait.until(EC.element_to_be_clickable((By.ID, "searchBtn")))
        query_button.click()
        print("✓ 已點擊查詢按鈕")

        # 等待查詢完成
        print("\n等待 5 秒讓查詢完成...")
        time.sleep(5)

        # 檢查所有 sessionStorage 的內容
        print("\n=== 檢查 sessionStorage 所有鍵值 ===")
        all_keys = driver.execute_script(
            "return Object.keys(sessionStorage);"
        )
        print(f"sessionStorage 的所有鍵: {all_keys}")

        # 逐一檢查每個鍵的內容
        for key in all_keys:
            print(f"\n鍵: {key}")
            value = driver.execute_script(
                f"return sessionStorage.getItem('{key}');"
            )
            print(f"值: {value[:200] if value and len(value) > 200 else value}")

        # 特別檢查 queryResultsSet
        print("\n=== 特別檢查 queryResultsSet ===")
        query_results = driver.execute_script(
            "return sessionStorage.getItem('queryResultsSet');"
        )

        if query_results:
            print("✓ 找到 queryResultsSet")
            print(f"原始內容: {query_results}")

            try:
                result_data = json.loads(query_results)
                print(f"\n解析後的 JSON:")
                print(json.dumps(result_data, indent=2, ensure_ascii=False))
            except Exception as e:
                print(f"JSON 解析失敗: {e}")
        else:
            print("✗ queryResultsSet 為空或不存在")

        # 檢查是否有新分頁
        print(f"\n=== 檢查瀏覽器分頁 ===")
        print(f"當前分頁數: {len(driver.window_handles)}")
        print(f"分頁列表: {driver.window_handles}")

        # 如果有多個分頁,切換到新分頁
        if len(driver.window_handles) > 1:
            print("\n切換到新分頁...")
            driver.switch_to.window(driver.window_handles[-1])
            print(f"新分頁 URL: {driver.current_url}")

        print("\n\n按 Enter 關閉...")
        input()

    except Exception as e:
        print(f"\n錯誤: {e}")
        import traceback
        traceback.print_exc()
        input("\n按 Enter 關閉...")
    finally:
        driver.quit()
        print("\n瀏覽器已關閉")


if __name__ == "__main__":
    debug_session_storage()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
偵錯腳本 - 檢查 MOPS 網頁的實際元素結構
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options


def debug_page_elements():
    """檢查網頁上的所有下拉選單和按鈕元素"""

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

    try:
        url = "https://mops.twse.com.tw/mops/#/web/t163sb05"
        print(f"開啟網頁: {url}")
        driver.get(url)

        print("\n等待 10 秒讓頁面完全載入...")
        time.sleep(10)

        print("\n=== 檢查所有 <select> 下拉選單 ===")
        selects = driver.find_elements(By.TAG_NAME, "select")
        print(f"找到 {len(selects)} 個下拉選單:")

        for i, select in enumerate(selects):
            try:
                element_id = select.get_attribute('id')
                element_name = select.get_attribute('name')
                element_class = select.get_attribute('class')

                # 取得選項
                options = select.find_elements(By.TAG_NAME, "option")
                options_text = [opt.text for opt in options[:5]]  # 只顯示前5個選項

                print(f"\n下拉選單 {i+1}:")
                print(f"  ID: {element_id}")
                print(f"  Name: {element_name}")
                print(f"  Class: {element_class}")
                print(f"  選項數量: {len(options)}")
                print(f"  前幾個選項: {options_text}")
            except Exception as e:
                print(f"  讀取失敗: {e}")

        print("\n\n=== 檢查所有按鈕 ===")
        buttons = driver.find_elements(By.TAG_NAME, "button")
        print(f"找到 {len(buttons)} 個按鈕:")

        for i, btn in enumerate(buttons):
            try:
                btn_text = btn.text
                btn_id = btn.get_attribute('id')
                btn_class = btn.get_attribute('class')
                btn_type = btn.get_attribute('type')

                print(f"\n按鈕 {i+1}:")
                print(f"  文字: {btn_text}")
                print(f"  ID: {btn_id}")
                print(f"  Class: {btn_class}")
                print(f"  Type: {btn_type}")
            except Exception as e:
                print(f"  讀取失敗: {e}")

        print("\n\n=== 檢查 input 按鈕 ===")
        inputs = driver.find_elements(By.TAG_NAME, "input")
        print(f"找到 {len(inputs)} 個 input 元素:")

        for i, inp in enumerate(inputs):
            try:
                inp_type = inp.get_attribute('type')
                if inp_type in ['button', 'submit']:
                    inp_value = inp.get_attribute('value')
                    inp_id = inp.get_attribute('id')
                    inp_class = inp.get_attribute('class')

                    print(f"\nInput 按鈕 {i+1}:")
                    print(f"  Type: {inp_type}")
                    print(f"  Value: {inp_value}")
                    print(f"  ID: {inp_id}")
                    print(f"  Class: {inp_class}")
            except Exception as e:
                pass

        print("\n\n=== 檢查頁面 HTML (部分) ===")
        try:
            # 儲存完整的 HTML
            with open('page_source.html', 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            print("完整的 HTML 已儲存至 page_source.html")
        except Exception as e:
            print(f"儲存 HTML 失敗: {e}")

        print("\n\n按 Enter 繼續...")
        input()

    except Exception as e:
        print(f"\n錯誤: {e}")
        import traceback
        traceback.print_exc()
    finally:
        driver.quit()
        print("\n瀏覽器已關閉")


if __name__ == "__main__":
    debug_page_elements()

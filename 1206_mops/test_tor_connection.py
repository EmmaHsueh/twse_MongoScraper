#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試 Tor 連接是否正常
"""

import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

def test_normal_ip():
    """測試不使用 Tor 的 IP"""
    print("\n=== 測試正常連接的 IP ===")
    try:
        response = requests.get('https://api.ipify.org?format=json', timeout=10)
        ip = response.json()['ip']
        print(f"您的真實 IP: {ip}")
        return ip
    except Exception as e:
        print(f"獲取真實 IP 失敗: {e}")
        return None


def test_tor_ip():
    """測試使用 Tor 的 IP"""
    print("\n=== 測試 Tor 連接的 IP ===")
    try:
        # 設置 SOCKS 代理
        proxies = {
            'http': 'socks5h://127.0.0.1:9050',
            'https': 'socks5h://127.0.0.1:9050'
        }

        response = requests.get(
            'https://api.ipify.org?format=json',
            proxies=proxies,
            timeout=30
        )
        ip = response.json()['ip']
        print(f"通過 Tor 的 IP: {ip}")
        return ip
    except Exception as e:
        print(f"通過 Tor 獲取 IP 失敗: {e}")
        print("請確認：")
        print("1. Tor 服務已啟動")
        print("2. 已安裝 PySocks: pip install pysocks")
        return None


def test_selenium_with_tor():
    """測試 Selenium 使用 Tor"""
    print("\n=== 測試 Selenium + Tor ===")

    chrome_options = Options()

    # 設置 Tor SOCKS 代理
    chrome_options.add_argument('--proxy-server=socks5://127.0.0.1:9050')

    # 反爬蟲設定
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    try:
        driver = webdriver.Chrome(options=chrome_options)

        # 訪問 IP 檢查網站
        print("正在通過 Tor 訪問 IP 檢查網站...")
        driver.get('https://api.ipify.org?format=json')
        time.sleep(2)

        # 獲取頁面內容
        body_text = driver.find_element('tag name', 'body').text
        print(f"Selenium + Tor 的 IP: {body_text}")

        driver.quit()
        print("✓ Selenium + Tor 測試成功！")
        return True

    except Exception as e:
        print(f"✗ Selenium + Tor 測試失敗: {e}")
        return False


def main():
    print("="*60)
    print("Tor 連接測試工具")
    print("="*60)

    # 測試正常 IP
    normal_ip = test_normal_ip()

    # 測試 Tor IP
    tor_ip = test_tor_ip()

    # 比較結果
    if normal_ip and tor_ip:
        print("\n" + "="*60)
        if normal_ip != tor_ip:
            print("✓ Tor 連接成功！IP 已改變")
            print(f"  真實 IP: {normal_ip}")
            print(f"  Tor IP:  {tor_ip}")
        else:
            print("✗ Tor 可能未生效，IP 沒有改變")
        print("="*60)

    # 測試 Selenium + Tor
    test_selenium_with_tor()


if __name__ == "__main__":
    main()

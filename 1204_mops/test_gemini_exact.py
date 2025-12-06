"""
完全按照 gemini.py 的方法測試
"""
import requests
import time
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 使用 Session 來維持 Cookies
session = requests.Session()

# 偽裝瀏覽器 Headers (Referer 非常重要)
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://mops.twse.com.tw/mops/web/t164sb03',
    'Origin': 'https://mops.twse.com.tw',
    'Content-Type': 'application/x-www-form-urlencoded',
}

print("=" * 60)
print("完全按照 gemini.py 的方法測試")
print("=" * 60)

# 1. 先訪問頁面，取得 Cookies
print("\n[步驟 1] 訪問頁面...")
url_page = 'https://mops.twse.com.tw/mops/web/t164sb03'
try:
    resp = session.get(url_page, headers=headers, verify=False, timeout=10)
    print(f"   狀態碼: {resp.status_code}")
    print(f"   Cookies: {dict(session.cookies)}")
except Exception as e:
    print(f"   錯誤: {e}")

time.sleep(1) # 稍微等待，模擬真人

# 2. 準備 AJAX 請求的 URL 和 Data
url_ajax = 'https://mops.twse.com.tw/mops/web/ajax_t164sb03'

payload = {
    'encodeURIComponent': '1',
    'step': '1',
    'firstin': '1',
    'off': '1',
    'co_id': '2330',  # 台積電範例
    'year': '112',
    'season': '3',
}

print(f"\n[步驟 2] 發送 POST 請求...")
print(f"   URL: {url_ajax}")
print(f"   Payload: {payload}")

# 3. 發送 POST 請求
try:
    response = session.post(url_ajax, headers=headers, data=payload, verify=False, timeout=10)

    if response.status_code == 200:
        print(f"\n✓ 狀態碼: 200")
        print(f"  回應長度: {len(response.text)} 字元")
        print(f"\n前 1000 字元:")
        print(response.text[:1000])

        # 分析回應
        print("\n" + "=" * 60)
        if '無法執行' in response.text or 'CANNOT BE ACCESSED' in response.text:
            print("❌ 被安全機制阻擋")
        elif '查無' in response.text:
            print("⚠️ 查無資料（可能年份/季度參數不對）")
        elif '<table' in response.text.lower():
            print("✅ 成功取得表格資料！")
            print(f"   表格數量: {response.text.lower().count('<table')}")
        else:
            print("⚠️ 未知回應")
        print("=" * 60)
    else:
        print(f"❌ 失敗，狀態碼：{response.status_code}")
except Exception as e:
    print(f"   錯誤: {e}")

"""
測試使用 Session 方法爬取 MOPS（參考 gemini.py）
"""
import requests
import time
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 使用 Session 來維持 Cookies
session = requests.Session()

# 偽裝瀏覽器 Headers
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://mops.twse.com.tw/mops/web/t163sb05',
    'Origin': 'https://mops.twse.com.tw',
    'Content-Type': 'application/x-www-form-urlencoded',
}

print("=" * 60)
print("測試 MOPS 爬蟲 - Session 方法")
print("=" * 60)

# 1. 先訪問頁面，取得 Cookies
print("\n[步驟 1] 訪問頁面取得 cookies...")
url_page = 'https://mops.twse.com.tw/mops/web/t163sb05'
try:
    response = session.get(url_page, headers=headers, verify=False, timeout=10)
    print(f"   狀態碼: {response.status_code}")
    print(f"   Cookies: {session.cookies.get_dict()}")
    time.sleep(1)  # 稍微等待，模擬真人
except Exception as e:
    print(f"   錯誤: {e}")

# 2. 準備 AJAX 請求
print("\n[步驟 2] 發送 AJAX 請求...")
url_ajax = 'https://mops.twse.com.tw/mops/web/ajax_t163sb05'

payload = {
    'encodeURIComponent': '1',
    'step': '1',
    'firstin': '1',
    'off': '1',
    'TYPEK': 'sii',  # 上市公司
    'year': '112',
    'season': '3',
}

print(f"   URL: {url_ajax}")
print(f"   Payload: {payload}")

# 3. 發送 POST 請求
try:
    response = session.post(url_ajax, headers=headers, data=payload, verify=False, timeout=10)

    print(f"\n[步驟 3] 檢查回應...")
    print(f"   狀態碼: {response.status_code}")
    print(f"   回應長度: {len(response.text)} 字元")
    print(f"   Content-Type: {response.headers.get('Content-Type', 'N/A')}")

    print(f"\n前 1000 字元:")
    print(response.text[:1000])

    # 檢查結果
    print("\n" + "=" * 60)
    if '查無' in response.text:
        print("❌ 查無資料")
    elif '無法執行' in response.text or 'CANNOT BE ACCESSED' in response.text:
        print("❌ 仍被安全機制阻擋")
    elif '<table' in response.text.lower():
        print("✅ 成功取得表格資料！")
        print(f"   表格數量: {response.text.lower().count('<table')}")

        # 嘗試解析表格
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, 'lxml')
        tables = soup.find_all('table')
        print(f"   解析到 {len(tables)} 個表格")

        if tables:
            print("\n   第一個表格的前 5 列:")
            rows = tables[0].find_all('tr')[:5]
            for i, row in enumerate(rows, 1):
                cells = [cell.get_text(strip=True) for cell in row.find_all(['td', 'th'])]
                print(f"      列 {i}: {cells[:3]}")
    else:
        print("⚠️ 未知回應格式")
    print("=" * 60)

except Exception as e:
    print(f"   錯誤: {e}")

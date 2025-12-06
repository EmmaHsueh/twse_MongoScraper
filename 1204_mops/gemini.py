import requests
import time

# 使用 Session 來維持 Cookies
session = requests.Session()

# 偽裝瀏覽器 Headers (Referer 非常重要)
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://mops.twse.com.tw/mops/web/t164sb03',
    'Origin': 'https://mops.twse.com.tw',
    'Content-Type': 'application/x-www-form-urlencoded',
}

# 1. 先訪問頁面，取得 Cookies
url_page = 'https://mops.twse.com.tw/mops/web/t164sb03'
session.get(url_page, headers=headers)
time.sleep(1) # 稍微等待，模擬真人

# 2. 準備 AJAX 請求的 URL 和 Data
# 注意：真實的 AJAX URL 通常是 ajax_ 開頭的
url_ajax = 'https://mops.twse.com.tw/mops/web/ajax_t164sb03' 

# 這些參數必須透過瀏覽器 F12 (Network -> Payload) 仔細核對
payload = {
    'encodeURIComponent': '1',
    'step': '1',
    'firstin': '1',
    'off': '1',
    'co_id': '2330',  # 台積電範例
    'year': '112',
    'season': '3',
    # 可能還有其他隱藏參數，請務必檢查 F12
}

# 3. 發送 POST 請求
response = session.post(url_ajax, headers=headers, data=payload)

if response.status_code == 200:
    print("成功獲取數據：")
    print(response.text[:500]) # 打印前500字檢查
else:
    print(f"失敗，狀態碼：{response.status_code}")
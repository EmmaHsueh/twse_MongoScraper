"""
直接測試新的 MOPS API
"""
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

url = 'https://mops.twse.com.tw/mops/web/ajax_t163sb05'

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Content-Type': 'application/x-www-form-urlencoded',
}

data = {
    'encodeURIComponent': '1',
    'step': '1',
    'firstin': '1',
    'off': '1',
    'TYPEK': 'sii',
    'year': '112',
    'season': '3',
}

print("測試 API 端點:", url)
print("請求參數:", data)
print()

response = requests.post(url, headers=headers, data=data, verify=False, timeout=10)

print(f"狀態碼: {response.status_code}")
print(f"回應長度: {len(response.text)} 字元")
print()
print("前 1000 字元:")
print(response.text[:1000])
print()

# 檢查是否成功
if '查無' in response.text:
    print("❌ 查無資料")
elif '無法執行' in response.text:
    print("❌ 被安全機制阻擋")
elif '<table' in response.text.lower():
    print("✅ 成功取得表格資料")
    print(f"   表格數量: {response.text.lower().count('<table')}")
else:
    print("⚠️ 未知回應格式")

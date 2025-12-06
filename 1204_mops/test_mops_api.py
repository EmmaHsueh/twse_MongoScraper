"""
測試 MOPS API 的不同請求方式
"""
import requests
from bs4 import BeautifulSoup

# 測試不同的 URL 和參數
def test_mops_api():
    print("測試 MOPS API...")

    # 建立 session
    session = requests.Session()

    # 更完整的 headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Referer': 'https://mops.twse.com.tw/mops/web/index',
        'Origin': 'https://mops.twse.com.tw',
    }

    # 先訪問首頁建立 session
    print("\n1. 訪問首頁...")
    try:
        response = session.get('https://mops.twse.com.tw/mops/web/index',
                              headers=headers,
                              verify=False,
                              timeout=10)
        print(f"   狀態碼: {response.status_code}")
        print(f"   Cookies: {session.cookies.get_dict()}")
    except Exception as e:
        print(f"   錯誤: {e}")

    # 嘗試訪問資產負債表頁面
    print("\n2. 訪問資產負債表頁面...")
    try:
        headers['Referer'] = 'https://mops.twse.com.tw/mops/web/index'
        response = session.get('https://mops.twse.com.tw/mops/web/t164sb03',
                              headers=headers,
                              verify=False,
                              timeout=10)
        print(f"   狀態碼: {response.status_code}")
        if response.status_code == 200:
            print(f"   頁面標題: {BeautifulSoup(response.text, 'lxml').title.string if BeautifulSoup(response.text, 'lxml').title else 'N/A'}")
    except Exception as e:
        print(f"   錯誤: {e}")

    # 嘗試 POST 請求
    print("\n3. 測試 POST 請求...")
    try:
        headers['Referer'] = 'https://mops.twse.com.tw/mops/web/t164sb03'
        headers['Content-Type'] = 'application/x-www-form-urlencoded'

        data = {
            'encodeURIComponent': '1',
            'step': '1',
            'firstin': '1',
            'off': '1',
            'co_id': '2330',
            'year': '112',
            'season': '03',
        }

        response = session.post('https://mops.twse.com.tw/mops/web/ajax_t164sb03',
                               headers=headers,
                               data=data,
                               verify=False,
                               timeout=10)
        print(f"   狀態碼: {response.status_code}")
        print(f"   回應長度: {len(response.text)}")
        print(f"   前 500 字元:")
        print(f"   {response.text[:500]}")

        # 檢查是否包含錯誤訊息
        if '無法執行' in response.text or 'CANNOT BE ACCESSED' in response.text:
            print("\n   ⚠️ 被安全機制阻擋")
        elif '查無' in response.text:
            print("\n   ⚠️ 查無資料")
        else:
            print("\n   ✓ 可能成功取得資料")

    except Exception as e:
        print(f"   錯誤: {e}")

if __name__ == '__main__':
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    test_mops_api()

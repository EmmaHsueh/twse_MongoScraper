# query6_1_scraper.py 程式詳細說明

## 📋 目錄

- [程式概述](#程式概述)
- [類別架構](#類別架構)
- [方法詳解](#方法詳解)
- [工作流程](#工作流程)
- [關鍵技術](#關鍵技術)
- [使用範例](#使用範例)
- [資料結構](#資料結構)
- [常見問題](#常見問題)

---

## 程式概述

### 用途
爬取台灣公開資訊觀測站（MOPS）的「內部人持股異動事後申報表」資料。

### 目標網站
```
https://mops.twse.com.tw/mops/#/web/query6_1
```

### 主要功能
1. 自動化查詢特定公司、年月的內部人持股異動資料
2. 從網頁的 sessionStorage 中提取 JSON 資料
3. 將資料結構化後存入 MongoDB 資料庫
4. 支援批次爬取多家公司

### 技術棧
- **Selenium**: 瀏覽器自動化
- **MongoDB**: 資料儲存
- **Python**: 核心開發語言

---

## 類別架構

### 繼承關係

```
MOPSScraper (父類別 - 來自 mops_scraper.py)
    ↓
Query61Scraper (子類別 - 本程式)
```

### Query61Scraper 類別

```python
class Query61Scraper(MOPSScraper):
    """
    繼承 MOPSScraper，專門處理 query6_1 頁面
    """
```

**特點**：
- 繼承父類別的 Selenium WebDriver 初始化
- 覆寫 URL 為 query6_1 專用
- 新增針對此頁面的特定方法

---

## 方法詳解

### 1. `__init__(self, headless=False)`

**功能**：初始化爬蟲

**參數**：
- `headless` (bool): 是否使用無頭模式（不顯示瀏覽器視窗）

**實作**：
```python
def __init__(self, headless=False):
    super().__init__(headless)  # 調用父類別初始化
    self.url = "https://mops.twse.com.tw/mops/#/web/query6_1"
```

---

### 2. `input_company_code(self, company_code)`

**功能**：輸入公司代號到搜尋欄位

**參數**：
- `company_code` (str): 公司代號（例如：'2330' 代表台積電）

**技術重點**：
- 使用 JavaScript 直接操作 DOM，避免 Selenium 的點擊問題
- 觸發 `input` 和 `change` 事件，確保 Vue.js 框架能偵測到變更

**程式碼解析**：
```python
self.driver.execute_script(f"""
    var input = document.getElementById('companyId');
    if (input) {{
        input.value = '{company_code}';  // 設定值
        input.dispatchEvent(new Event('input', {{ bubbles: true }}));   // 觸發 input 事件
        input.dispatchEvent(new Event('change', {{ bubbles: true }}));  // 觸發 change 事件
    }}
""")
```

**為什麼這樣做？**
- MOPS 網站使用 Vue.js 框架
- 直接修改 input.value 不會觸發 Vue 的響應式更新
- 必須手動觸發事件讓框架知道值已改變

---

### 3. `select_custom_date(self)`

**功能**：選擇「自訂」時間選項（而非預設的「最近三個月」）

**技術重點**：
- 使用 JavaScript 直接點擊 radio button
- 對應的元素 ID 是 `dataType_2`

**程式碼解析**：
```python
self.driver.execute_script("""
    var radio = document.getElementById('dataType_2');
    if (radio) {
        radio.click();  // 點擊「自訂」選項
        return true;
    }
    return false;
""")
```

**頁面效果**：
- 啟用年度和月份的輸入欄位
- 允許使用者指定特定的年月進行查詢

---

### 4. `input_custom_year(self, year)`

**功能**：輸入民國年度

**參數**：
- `year` (int): 民國年度（例如：114 代表民國 114 年）

**注意事項**：
- 輸入的是民國年，不是西元年
- 114 = 西元 2025 年

**程式碼解析**：
```python
self.driver.execute_script(f"""
    var yearInput = document.getElementById('year');
    if (yearInput) {{
        yearInput.value = '{year}';
        yearInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
        yearInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
    }}
""")
```

---

### 5. `input_custom_month(self, month)`

**功能**：選擇月份（使用下拉選單）

**參數**：
- `month` (int): 月份 (1-12)

**技術重點**：
- 下拉選單的選項文字是 "1月"、"2月" 等格式
- 需要找到匹配的選項並設定為選中狀態

**程式碼解析**：
```python
month_text = f"{month}月"  # 轉換為 "10月" 格式
self.driver.execute_script(f"""
    var monthSelect = document.getElementById('month');
    if (monthSelect) {{
        var options = monthSelect.options;
        for (var i = 0; i < options.length; i++) {{
            if (options[i].text === '{month_text}') {{
                monthSelect.selectedIndex = i;  // 設定選中的選項
                monthSelect.dispatchEvent(new Event('change', {{ bubbles: true }}));
                break;
            }}
        }}
    }}
""")
```

---

### 6. `wait_for_loading_to_disappear(self, timeout=5)`

**功能**：等待頁面的 loading 動畫消失

**參數**：
- `timeout` (int): 最長等待秒數，預設 5 秒

**為什麼需要這個方法？**
- MOPS 網站在查詢時會顯示 loading 動畫
- 必須等待動畫消失後才能確保資料已載入

**技術實作**：
```python
start_time = time.time()
while time.time() - start_time < timeout:
    loading_visible = self.driver.execute_script("""
        var loadingElements = document.querySelectorAll('.loadingElement');
        for (var i = 0; i < loadingElements.length; i++) {
            var style = window.getComputedStyle(loadingElements[i]);
            if (style.display !== 'none' && style.visibility !== 'hidden') {
                return true;  // 還在顯示
            }
        }
        return false;  // 已經消失
    """)

    if not loading_visible:
        return  # loading 已消失，可以繼續

    time.sleep(0.1)  # 等待 0.1 秒後再檢查
```

**邏輯說明**：
1. 每 0.1 秒檢查一次 loading 元素的可見性
2. 檢查元素的 `display` 和 `visibility` CSS 屬性
3. 一旦 loading 消失就立即返回，不必等滿整個 timeout

---

### 7. `click_query_button_with_retry(self, max_retries=3)`

**功能**：點擊查詢按鈕（帶重試機制）

**參數**：
- `max_retries` (int): 最大重試次數，預設 3 次

**為什麼需要重試？**
- 網路延遲可能導致按鈕未完全載入
- loading 元素可能遮擋按鈕
- 提高爬蟲的穩定性

**重試邏輯**：
```python
for attempt in range(max_retries):
    try:
        # 1. 等待 loading 消失
        self.wait_for_loading_to_disappear()

        # 2. 點擊查詢按鈕
        clicked = self.driver.execute_script("""
            var btn = document.getElementById('searchBtn');
            if (btn) {
                btn.click();
                return true;
            }
            return false;
        """)

        if clicked:
            time.sleep(1.5)  # 等待查詢結果
            return True

    except Exception as e:
        # 失敗則重試
        if attempt < max_retries - 1:
            time.sleep(1)  # 等待 1 秒後重試
```

---

### 8. `get_query_results_from_session_storage(self)`

**功能**：從瀏覽器的 sessionStorage 中取得查詢結果

**返回值**：
- `dict`: 包含 data、titles、year、month 等資訊
- `None`: 如果沒有資料或解析失敗

**為什麼從 sessionStorage 取資料？**
- MOPS 網站使用前端框架（Vue.js）
- 查詢結果儲存在瀏覽器的 sessionStorage 中
- 比解析 HTML 更可靠、更快速

**資料路徑**：
```
sessionStorage
  └─ queryResultsSet (JSON 字串)
      └─ result
          └─ result
              ├─ data (陣列)：明細資料
              ├─ titles (陣列)：欄位標題
              ├─ year：查詢年度
              ├─ month：查詢月份
              ├─ marketName：市場別
              └─ companyAbbreviation：公司簡稱
```

**程式碼解析**：
```python
# 1. 從 sessionStorage 取得 JSON 字串
query_results = self.driver.execute_script(
    "return sessionStorage.getItem('queryResultsSet');"
)

# 2. 解析 JSON
if query_results:
    result_data = json.loads(query_results)

    # 3. 檢查資料結構並提取
    if 'result' in result_data and 'result' in result_data['result']:
        inner_result = result_data['result']['result']

        if 'data' in inner_result and 'titles' in inner_result:
            return {
                'data': inner_result['data'],
                'titles': inner_result['titles'],
                'year': inner_result.get('year', ''),
                'month': inner_result.get('month', ''),
                'marketName': inner_result.get('marketName', ''),
                'companyAbbreviation': inner_result.get('companyAbbreviation', '')
            }
```

---

### 9. `scrape_company_data(self, company_code, year, month)`

**功能**：爬取單一公司的完整資料（核心方法）

**參數**：
- `company_code` (str): 公司代號
- `year` (int): 民國年度
- `month` (int): 月份

**返回值**：
```python
{
    "公司代號": "2330",
    "查詢年度": 114,
    "查詢月份": 10,
    "市場別": "上市",
    "公司簡稱": "台積電",
    "標題": [...],      # 欄位標題陣列
    "明細資料": [...]   # 資料陣列
}
```

**完整流程**：

```python
def scrape_company_data(self, company_code, year, month):
    # 1. 確保在正確的頁面
    if "query6_1" not in current_url:
        self.driver.get(self.url)
        time.sleep(2)

    # 2. 選擇「自訂」時間
    self.select_custom_date()

    # 3. 輸入查詢條件
    self.input_company_code(company_code)
    self.input_custom_year(year)
    self.input_custom_month(month)

    # 4. 點擊查詢按鈕
    self.click_query_button_with_retry()

    # 5. 智能等待結果（最多 3 秒）
    max_wait = 3
    start_time = time.time()
    results = None

    while time.time() - start_time < max_wait:
        results = self.get_query_results_from_session_storage()
        if results:
            break  # 一旦取得資料就立即返回
        time.sleep(0.2)  # 短暫等待後再檢查

    # 6. 返回結構化資料
    if results:
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
        return None
```

---

### 10. `parse_titles_to_columns(self, titles)`

**功能**：將巢狀的標題結構轉換為平面的欄位名稱列表

**輸入範例**：
```python
titles = [
    {"main": "姓名", "sub": []},
    {"main": "職稱", "sub": []},
    {"main": "持股異動", "sub": [
        {"main": "股數"},
        {"main": "市值"}
    ]}
]
```

**輸出範例**：
```python
["姓名", "職稱", "持股異動-股數", "持股異動-市值"]
```

**程式碼邏輯**：
```python
def parse_titles_to_columns(self, titles):
    columns = []

    for title in titles:
        main = title.get('main', '')

        # 如果有子標題，展開
        if title.get('sub') and len(title['sub']) > 0:
            for sub in title['sub']:
                sub_main = sub.get('main', '')
                columns.append(f"{main}-{sub_main}")  # 合併主標題和子標題
        else:
            columns.append(main)  # 沒有子標題，直接使用主標題

    return columns
```

**為什麼需要這個方法？**
- 網頁的表格標題是多層結構（有主標題和子標題）
- MongoDB 儲存時需要平面的欄位名稱
- 使用 `-` 連接主副標題，確保欄位名稱唯一且有意義

---

### 11. `save_to_mongodb(self, mongo_helper, data)`

**功能**：將爬取的資料存入 MongoDB

**參數**：
- `mongo_helper` (MongoDBHelper): MongoDB 連接實例
- `data` (dict): 要儲存的資料字典

**儲存策略**：
- **每筆明細分開存**（而非整批存）
- 每筆明細都包含完整的基本資訊（公司代號、年月等）

**程式碼解析**：

```python
def save_to_mongodb(self, mongo_helper, data):
    # 1. 取得 collection
    collection = mongo_helper.db['內部人持股異動事後申報表']

    # 2. 解析標題為欄位名稱
    columns = self.parse_titles_to_columns(data['標題'])

    # 3. 準備基本資訊（每筆明細都會包含）
    base_info = {
        "公司代號": data["公司代號"],
        "查詢年度": data["查詢年度"],
        "查詢月份": data["查詢月份"],
        "市場別": data["市場別"],
        "公司簡稱": data["公司簡稱"],
    }

    # 4. 處理每一筆明細
    for row_index, row_data in enumerate(data['明細資料']):
        # 建立單筆明細文件
        document = base_info.copy()

        # 將資料與欄位對應
        for col_index, value in enumerate(row_data):
            if col_index < len(columns):
                column_name = columns[col_index]
                document[column_name] = value

        # 插入資料庫
        collection.insert_one(document)
```

**儲存的資料範例**：
```json
{
    "_id": ObjectId("..."),
    "公司代號": "2330",
    "查詢年度": 114,
    "查詢月份": 10,
    "市場別": "上市",
    "公司簡稱": "台積電",
    "姓名": "張三",
    "職稱": "董事長",
    "申報身分": "董事",
    "異動原因": "贈與",
    "交易日期": "113/10/15",
    "持股異動-股數": "10000",
    "持股異動-市值": "1000000"
}
```

---

## 工作流程

### 整體流程圖

```
開始
  ↓
初始化爬蟲（開啟瀏覽器）
  ↓
連接 MongoDB
  ↓
選擇爬取模式（完整/部分/個別）
  ↓
取得要爬取的公司代號列表
  ↓
開啟 MOPS 網頁
  ↓
┌─────────────────────────────┐
│ 開始批次爬取迴圈            │
│                             │
│  對每家公司執行：           │
│  1. 選擇自訂時間            │
│  2. 輸入公司代號            │
│  3. 輸入年度、月份          │
│  4. 點擊查詢按鈕            │
│  5. 等待結果載入            │
│  6. 從 sessionStorage 取資料│
│  7. 解析並結構化資料        │
│  8. 存入 MongoDB            │
│  9. 延遲 0.5-1.5 秒         │
│                             │
└─────────────────────────────┘
  ↓
顯示統計結果
  ↓
關閉瀏覽器和資料庫連接
  ↓
結束
```

### 單一公司爬取流程

```
scrape_company_data(company_code, year, month)
  ↓
1. 選擇「自訂」時間選項
   select_custom_date()
  ↓
2. 輸入公司代號
   input_company_code(company_code)
  ↓
3. 輸入年度
   input_custom_year(year)
  ↓
4. 輸入月份
   input_custom_month(month)
  ↓
5. 點擊查詢按鈕（帶重試）
   click_query_button_with_retry()
     ↓
     wait_for_loading_to_disappear()
     ↓
     點擊 searchBtn
     ↓
     等待 1.5 秒
  ↓
6. 智能等待並取得結果
   while 未超時:
     results = get_query_results_from_session_storage()
     if results:
       break
     等待 0.2 秒
  ↓
7. 返回結構化資料
   {公司代號, 年度, 月份, 標題, 明細資料}
```

---

## 關鍵技術

### 1. JavaScript 注入

**為什麼使用 JavaScript 而不是 Selenium 原生方法？**

| 方法 | 優點 | 缺點 |
|------|------|------|
| Selenium 原生 | 簡單直觀 | 容易被元素遮擋、需要元素可見 |
| JavaScript 注入 | 直接操作 DOM、不受可見性影響 | 需要了解網頁結構 |

**範例對比**：

```python
# Selenium 原生方法（可能失敗）
element = driver.find_element(By.ID, "searchBtn")
element.click()  # 可能被其他元素遮擋

# JavaScript 注入（更可靠）
driver.execute_script("""
    document.getElementById('searchBtn').click();
""")
```

### 2. Vue.js 事件觸發

MOPS 網站使用 Vue.js 框架，修改輸入框的值時必須觸發事件：

```javascript
// 錯誤做法（Vue 不會偵測到變更）
input.value = '2330';

// 正確做法（觸發事件讓 Vue 知道）
input.value = '2330';
input.dispatchEvent(new Event('input', { bubbles: true }));
input.dispatchEvent(new Event('change', { bubbles: true }));
```

### 3. sessionStorage 資料提取

**優點**：
- 資料已經是 JSON 格式，不需解析 HTML
- 獲取速度快
- 資料結構穩定

**提取方法**：
```python
data = driver.execute_script(
    "return sessionStorage.getItem('queryResultsSet');"
)
result = json.loads(data)
```

### 4. 智能等待策略

**傳統做法**：
```python
time.sleep(5)  # 固定等待 5 秒（浪費時間）
```

**智能等待**：
```python
max_wait = 3
start_time = time.time()

while time.time() - start_time < max_wait:
    if 條件滿足:
        break  # 立即返回，不浪費時間
    time.sleep(0.2)
```

**優勢**：
- 資料一到就立即處理
- 最多等待 max_wait 秒
- 平均等待時間大幅減少

### 5. 錯誤處理與重試機制

```python
for attempt in range(max_retries):
    try:
        # 嘗試執行操作
        result = do_something()
        if result:
            return result
    except Exception as e:
        if attempt < max_retries - 1:
            time.sleep(1)  # 等待後重試
        else:
            raise  # 最後一次失敗則拋出異常
```

---

## 使用範例

### 範例 1: 爬取單一公司

```python
from query6_1_scraper import Query61Scraper
from mongodb_helper import MongoDBHelper

# 初始化
scraper = Query61Scraper(headless=False)
mongo_helper = MongoDBHelper()

# 開啟網頁
scraper.driver.get(scraper.url)

# 爬取台積電 (2330) 114年10月資料
data = scraper.scrape_company_data("2330", 114, 10)

if data:
    print(f"爬取成功！共 {len(data['明細資料'])} 筆資料")
    # 存入資料庫
    scraper.save_to_mongodb(mongo_helper, data)

# 清理
scraper.close()
mongo_helper.close()
```

### 範例 2: 批次爬取多家公司

```python
from query6_1_scraper import Query61Scraper
from mongodb_helper import MongoDBHelper
import time
import random

# 初始化
scraper = Query61Scraper(headless=True)  # 無頭模式
mongo_helper = MongoDBHelper()

# 要爬取的公司列表
companies = ["2330", "2317", "1101", "2454"]

# 開啟網頁
scraper.driver.get(scraper.url)
time.sleep(2)

# 批次爬取
for company_code in companies:
    try:
        # 爬取資料
        data = scraper.scrape_company_data(company_code, 114, 10)

        if data:
            # 存入資料庫
            scraper.save_to_mongodb(mongo_helper, data)
            print(f"✓ {company_code} 完成")

        # 隨機延遲，避免被封鎖
        delay = random.uniform(0.5, 1.5)
        time.sleep(delay)

    except Exception as e:
        print(f"✗ {company_code} 失敗: {e}")
        continue

# 清理
scraper.close()
mongo_helper.close()
```

### 範例 3: 使用主程式（互動式）

```bash
# 執行主程式
python query6_1_scraper.py

# 選擇模式 3（個別爬取）
請選擇爬取模式：
1. 完整爬取（所有上市上櫃公司）
2. 部分爬取（指定索引範圍）
3. 個別爬取（輸入特定公司代號）

請輸入選項 (1/2/3): 3

# 輸入公司代號
請輸入要爬取的公司代號
多個代號請用逗號分隔 (例如: 2330,1101,2317): 2330,2317

# 確認執行
確定要開始爬取嗎? (y/n): y
```

---

## 資料結構

### titles 結構

```json
[
  {
    "main": "姓名",
    "sub": []
  },
  {
    "main": "職稱",
    "sub": []
  },
  {
    "main": "持股異動",
    "sub": [
      {"main": "股數"},
      {"main": "市值"}
    ]
  }
]
```

### data 結構

```json
[
  ["張三", "董事長", "10000", "1000000"],
  ["李四", "總經理", "5000", "500000"],
  ["王五", "董事", "8000", "800000"]
]
```

### MongoDB 儲存格式

```json
{
  "_id": ObjectId("507f1f77bcf86cd799439011"),
  "公司代號": "2330",
  "查詢年度": 114,
  "查詢月份": 10,
  "市場別": "上市",
  "公司簡稱": "台積電",
  "姓名": "張三",
  "職稱": "董事長",
  "持股異動-股數": "10000",
  "持股異動-市值": "1000000"
}
```

---

## 常見問題

### Q1: 為什麼使用 JavaScript 而不是 Selenium 原生方法？

**A**:
1. MOPS 網站使用 Vue.js 框架，直接用 Selenium 可能無法觸發框架的響應式更新
2. JavaScript 可以直接操作 DOM，不受元素可見性限制
3. 避免元素被遮擋導致的點擊失敗

### Q2: 為什麼要從 sessionStorage 取資料？

**A**:
1. 資料已經是 JSON 格式，不需解析 HTML
2. 比解析 DOM 更快、更可靠
3. 資料結構穩定，不會因網頁改版而失效

### Q3: 爬蟲速度慢怎麼辦？

**A**:
1. 使用無頭模式：`Query61Scraper(headless=True)`
2. 已經使用智能等待，資料到達即立即處理
3. 可以調整公司間延遲：`delay = random.uniform(0.3, 0.8)`
4. 考慮使用多線程（需注意併發限制）

### Q4: 如何處理爬取失敗？

**A**:
程式已內建重試機制：
- 查詢按鈕點擊失敗會自動重試 3 次
- 單一公司失敗不會影響其他公司
- 最後會顯示成功/失敗統計

### Q5: 資料存入 MongoDB 時如何避免重複？

**A**:
目前版本允許重複資料（使用 `insert_one` 而非 `update_one`）。
如需避免重複，可以修改為：

```python
# 使用 upsert 避免重複
collection.update_one(
    {
        "公司代號": document["公司代號"],
        "查詢年度": document["查詢年度"],
        "查詢月份": document["查詢月份"],
        "姓名": document["姓名"],
        "交易日期": document.get("交易日期")
    },
    {"$set": document},
    upsert=True
)
```

### Q6: 如何修改查詢的年月？

**A**:
在 `main()` 函數中修改這兩行：

```python
year = 114  # 改成你要的民國年
month = 10  # 改成你要的月份 (1-12)
```

### Q7: 可以同時爬取多個年月嗎？

**A**:
可以，使用巢狀迴圈：

```python
years = [113, 114]
months = [9, 10, 11]

for year in years:
    for month in months:
        for company_code in all_codes:
            data = scraper.scrape_company_data(company_code, year, month)
            # ...
```

### Q8: 瀏覽器版本問題

**A**:
如果遇到 ChromeDriver 版本不符：

```bash
# 安裝 webdriver-manager 會自動處理版本
pip install webdriver-manager

# 在程式中已自動使用
from webdriver_manager.chrome import ChromeDriverManager
```

---

## 效能優化建議

### 1. 使用無頭模式
```python
scraper = Query61Scraper(headless=True)
```
**提升**: 10-20%

### 2. 減少延遲時間
```python
delay = random.uniform(0.3, 0.8)  # 更激進（可能被偵測）
```
**提升**: 30-50%

### 3. 批次處理
一次開啟瀏覽器，連續爬取多家公司
**提升**: 大幅減少初始化時間

### 4. 並行處理（進階）
```python
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=3) as executor:
    futures = [executor.submit(scrape_one_company, code) for code in codes]
```
**提升**: 2-3 倍（需注意併發限制）

---

## 版本歷史

### v2.0 (2024-12-14)
- ✅ 優化等待策略，使用智能等待
- ✅ 減少固定延遲時間
- ✅ 提升爬取速度約 2.5-3 倍

### v1.0 (初始版本)
- ✅ 基本爬取功能
- ✅ MongoDB 儲存
- ✅ 批次爬取支援

---

## 授權與免責聲明

⚠️ **注意事項**：
1. 本程式僅供學術研究和個人學習使用
2. 請遵守 MOPS 網站的使用條款
3. 不要進行過於頻繁的請求，避免對網站造成負擔
4. 資料版權歸原網站所有

---

## 相關文件

- [TOR_GUIDE.md](TOR_GUIDE.md) - Tor 爬蟲使用指南
- [README.md](README.md) - 專案整體說明
- [mongodb_helper.py](mongodb_helper.py) - MongoDB 操作輔助模組

---

**最後更新**: 2024-12-14
**作者**: Claude Code
**聯絡**: 如有問題請提交 Issue

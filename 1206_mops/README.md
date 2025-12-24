# MOPS 網站爬蟲

自動化爬取公開資訊觀測站 (MOPS) 的上市櫃公司財務報表資料，並儲存至 MongoDB。

## 簡介

財務報表爬蟲程式：
- 資產負債表
- 綜合損益表
- 現金流量表

### 主要特色

-  **高效率**: 一次請求取得所有公司資料
-  **自動去重**: 智慧檢查避免重複爬取
-  **斷點續傳**: 可隨時中斷再繼續
-  **公司驗證**: 只爬取存在於「公司基本資料」的公司
-  **MongoDB 儲存**: 自動建立索引，查詢效率最佳化

## 檔案結構

```
1206_mops/
  ├── venv/                          # Python 虛擬環境
  ├── requirements.txt               # 套件相依性
  ├── run.sh                         # 快速啟動腳本
  ├── .gitignore                     # Git 忽略檔案
  ├── 紀錄.md                        # 開發過程記錄
  │
  ├── 【核心爬蟲程式】
  ├── mops_scraper.py                # MOPS 通用爬蟲引擎（使用 Selenium）
  ├── mongodb_helper.py              # MongoDB 資料庫操作輔助模組
  │
  ├── 【財報爬蟲】
  ├── batch_scraper_optimized.py     # 資產負債表爬蟲（批次優化版）
  ├── income_statement_scraper.py    # 綜合損益表爬蟲
  ├── cashflow_scraper.py            # 現金流量表爬蟲
  │
  ├── 【每月營收爬蟲】
  ├── monthly_revenue_scraper.py     # 每月營收爬蟲（透過網址變更方式）
  ├── test_revenue_scraper.py        # 每月營收測試腳本
  ├── README_monthly_revenue.md      # 每月營收爬蟲使用說明
  │
  └── 【除錯工具】
      ├── debug_elements.py          # 檢查網頁元素結構
      ├── debug_storage.py           # 檢查 sessionStorage 內容
      ├── debug_revenue_table.py     # 檢查營收表格結構
      └── diagnose_mongodb.py        # 診斷 MongoDB 資料結構

```

```
  兩種爬蟲的定位

  | 項目  | mops_scraper.py       | monthly_revenue_scraper.py |
  |-----|-----------------------|----------------------------|
  | 技術  | Selenium（動態操作）        | Requests（直接請求）             |
  | 用途  | 財務報表（需動態查詢）           | 每月營收（固定網址格式）               |
  | 依賴  | Chrome + ChromeDriver | 僅需 requests                |
  | 速度  | 較慢                    | 較快                         |
  | 適用  | 複雜查詢流程                | 簡單網址規則                     |

```


## QUICK STAR

### 1. 環境準備

```bash
# 啟動虛擬環境
source venv/bin/activate

# 確認套件已安裝
pip list | grep -E "selenium|pandas|pymongo"
```

### 2. MongoDB 連線

```bash
python mongodb_helper.py
```

預期輸出：
```
=== MongoDB 連線測試 ===
資料庫: TW_Stock
公司總數: 2284
上市公司: 1066
上櫃公司: 860
✓ 連線測試成功
```

### 3. 執行爬蟲

#### 資產負債表
```bash
python batch_scraper_optimized.py
```

#### 綜合損益表
```bash
python income_statement_scraper.py
```

#### 現金流量表
```bash
python cashflow_scraper.py
```

## 程式說明

### mops_scraper.py
**核心爬蟲關鍵**，處理 MOPS 網站的動態載入和反爬蟲機制。

主要功能：
- 使用 Selenium 模擬瀏覽器操作
- 處理市場別、年度、季別選擇
- 從 sessionStorage 讀取動態生成的查詢結果 URL
- 自動處理網頁跳轉

方法：
```python
scraper = MOPSScraper(headless=True)
result_url = scraper.scrape_data(
    market_type="sii",  # 上市
    year=113,           # 民國年度
    season=3            # 第三季
)
```

### mongodb_helper.py
**MongoDB 模組**，提供資料庫操作介面。

主要功能：
- 連線管理
- 索引建立
- 公司代號驗證
- 資料去重檢查
- 批次插入

方法：
```python
helper = MongoDBHelper()
codes = helper.get_all_company_codes("sii")  # 取得上市公司代號
exists = helper.company_exists("2330")       # 檢查公司是否存在
```

## 網站爬蟲說明

### batch_scraper_optimized.py
**資產負債表爬蟲** (t163sb05)

- **Collection**: `上市櫃公司資產負債表`
- **年份範圍**: 78-114 年
- **資料項目**: 流動資產、固定資產、負債、權益等

### income_statement_scraper.py
**綜合損益表爬蟲** (t163sb04)

- **Collection**: `上市櫃公司綜合損益表`
- **年份範圍**: 78-114 年
- **資料項目**: 營收、成本、毛利、淨利等

### cashflow_scraper.py
**現金流量表爬蟲** (t163sb20)

- **Collection**: `上市櫃公司現金流量表`
- **年份範圍**: 102-114 年
- **資料項目**: 營業活動、投資活動、籌資活動現金流量

## 執行模式

所有爬蟲都有三種執行模式：

### 模式 1: 完整爬取
```
爬取所有歷史資料
自動跳過已存在的資料
適合第一次執行
```

### 模式 2: 測試模式
```
只爬取 113Q3 上市公司資料
用於快速測試功能
```

### 模式 3: 自訂範圍
```
自訂市場別、起始年度、結束年度
彈性控制爬取範圍
```

## MongoDB 資料結構

### 資料庫: TW_Stock

#### Collection: 公司基本資料
```javascript
{
  "公司 代號": "2330",      // 注意有空格
  "公司名稱": "台積電",
  "市場別": "listed",       // listed(上市), otc(上櫃), emerging(興櫃)
  ...
}
```

#### Collection: 上市櫃公司資產負債表
```javascript
{
  "公司代號": "2330",
  "年度": 113,
  "季別": 3,
  "流動資產": 1234567890,
  "固定資產": 9876543210,
  ...
  "爬取時間": ISODate("2024-12-06T14:30:00Z")
}
```

#### Collection: 上市櫃公司綜合損益表
```javascript
{
  "公司代號": "2330",
  "年度": 113,
  "季別": 3,
  "營業收入": 1234567890,
  "營業成本": 9876543210,
  ...
}
```

#### Collection: 上市櫃公司現金流量表
```javascript
{
  "公司代號": "2330",
  "年度": 113,
  "季別": 3,
  "營業活動現金流量": 1234567890,
  "投資活動現金流量": -9876543210,
  ...
}
```

### 索引設計
```javascript
// 公司基本資料
{ "公司 代號": 1 }  // unique

// 各財報 collection
{ "公司代號": 1, "年度": 1, "季別": 1 }  // unique compound index
```

## 偵錯工具

### diagnose_mongodb.py
診斷 MongoDB 資料結構，檢查欄位名稱和值。

```bash
python diagnose_mongodb.py
```

用途：
- 檢查 collections 列表
- 顯示資料範例
- 自動偵測欄位名稱
- 統計市場別分佈

### debug_elements.py
檢查網頁元素結構，用於找出正確的選擇器。

```bash
python debug_elements.py
```

用途：
- 列出所有下拉選單
- 列出所有按鈕
- 顯示元素 ID、Name、Class
- 儲存完整 HTML

### debug_storage.py
檢查 sessionStorage 內容，用於偵錯查詢結果 URL。

```bash
python debug_storage.py
```

用途：
- 執行完整查詢流程
- 顯示 sessionStorage 所有鍵值
- 解析查詢結果 JSON
- 檢查新分頁


## 使用範例

### 範例 1: 爬取 2023 年上市公司資產負債表

```python
from batch_scraper_optimized import OptimizedBatchScraper

scraper = OptimizedBatchScraper(headless=True)

try:
    scraper.scrape_all_history_optimized(
        market_types=["sii"],
        start_year=112,
        end_year=112
    )
finally:
    scraper.close()
```

### 範例 2: 查詢 MongoDB 中的資料

```python
from mongodb_helper import MongoDBHelper

helper = MongoDBHelper()

# 取得台積電 2023Q3 資產負債表
data = helper.balance_sheet.find_one({
    "公司代號": "2330",
    "年度": 112,
    "季別": 3
})

print(data)
```

### 範例 3: 批次爬取所有財報

```bash
# 1. 資產負債表
python batch_scraper_optimized.py
# 選擇: 1

# 2. 綜合損益表
python income_statement_scraper.py
# 選擇: 1

# 3. 現金流量表
python cashflow_scraper.py
# 選擇: 1
```

## 注意事項

### 1. 反爬蟲機制
- 每次請求間隔 5 秒
- 使用真實 User-Agent
- 隱藏 webdriver 特徵

### 2. 資料正確性
- 爬取後建議抽查驗證
- 注意財報更新/更正的情況
- 某些年度可能無資料

### 3. 系統需求
- Chrome 瀏覽器 (最新版本)
- ChromeDriver (自動下載)
- MongoDB 服務執行中
- 穩定的網路連線

### 4. 效能優化
- 使用 `headless=True` 背景執行
- 定期清理 MongoDB 日誌
- 監控磁碟空間

## 常見問題

### Q1: 瀏覽器崩潰怎麼辦？
A: 程式會自動跳過失敗的請求，可以再次執行繼續爬取未完成的資料。

### Q2: 如何查看爬取進度？
```javascript
// MongoDB Shell
db.上市櫃公司資產負債表.aggregate([
  { $group: { _id: { year: "$年度", season: "$季別" }, count: { $sum: 1 } } },
  { $sort: { "_id.year": 1, "_id.season": 1 } }
])
```

### Q3: 如何只爬取特定公司？
需要修改程式碼，在 `parse_all_companies_from_table` 方法中加入公司代號過濾。

### Q4: 資料儲存在哪裡？
```
MongoDB 資料庫: TW_Stock
Collections:
  - 上市櫃公司資產負債表
  - 上市櫃公司綜合損益表
  - 上市櫃公司現金流量表
```

### Q5: 如何備份資料？
```bash
# 備份整個資料庫
mongodump --db TW_Stock --out ./backup

# 還原資料
mongorestore --db TW_Stock ./backup/TW_Stock
```

## 故障排除

### ChromeDriver 版本問題
```bash
pip install webdriver-manager
```

然後修改 `mops_scraper.py`:
```python
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

service = Service(ChromeDriverManager().install())
self.driver = webdriver.Chrome(service=service, options=chrome_options)
```

### MongoDB 連線失敗
檢查 MongoDB 服務狀態:
```bash
# macOS
brew services list | grep mongodb

# 啟動 MongoDB
brew services start mongodb-community
```

### 找不到元素
執行偵錯工具檢查網頁結構:
```bash
python debug_elements.py
```

## 技術細節

### 反爬蟲處理
```python
# 隱藏 webdriver 特徵
chrome_options.add_argument('--disable-blink-features=AutomationControlled')
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])

# 修改 navigator.webdriver
driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
    'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
})
```

### SessionStorage 讀取
```python
query_results = driver.execute_script(
    "return sessionStorage.getItem('queryResultsSet');"
)
result_data = json.loads(query_results)
url = result_data['result']['result']['url']  # 注意巢狀結構
```

### 批次處理邏輯
1. 選擇市場別、年度、季別
2. 查詢取得所有公司資料
3. 解析 HTML 表格
4. 驗證公司代號
5. 檢查資料是否已存在
6. 批次儲存到 MongoDB


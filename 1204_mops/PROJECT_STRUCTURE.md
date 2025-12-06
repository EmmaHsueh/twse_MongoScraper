# 專案結構說明

```
1204_mops/
│
├── config.py                    # 配置文件
│   ├── MongoDB 連接設定
│   ├── 爬蟲參數設定
│   └── MOPS API 設定
│
├── db_manager.py                # MongoDB 資料庫管理器
│   ├── MongoDBManager 類別
│   │   ├── __init__()          # 初始化連接
│   │   ├── _create_indexes()   # 建立索引
│   │   ├── get_all_companies() # 取得所有公司
│   │   ├── get_company_stock_codes() # 取得股票代碼
│   │   ├── save_balance_sheet_data() # 儲存資料
│   │   ├── get_existing_records() # 查詢已存在記錄
│   │   └── close()             # 關閉連接
│
├── mops_scraper.py              # MOPS 爬蟲核心
│   ├── MOPSScraper 類別
│   │   ├── __aenter__()        # 非同步上下文進入
│   │   ├── __aexit__()         # 非同步上下文退出
│   │   ├── _get_year_season_list() # 生成年季列表
│   │   ├── _fetch_balance_sheet() # 抓取單季資料
│   │   ├── _parse_balance_sheet() # 解析 HTML
│   │   ├── fetch_company_all_seasons() # 抓取單公司所有季度
│   │   ├── fetch_all_companies() # 批次抓取所有公司
│   │   └── get_statistics()    # 取得統計資訊
│
├── main.py                      # 主程式入口
│   ├── main()                  # 主函數
│   │   ├── 步驟 1: 取得公司清單
│   │   ├── 步驟 2: 爬取資料
│   │   └── 步驟 3: 儲存到 MongoDB
│
├── test_connection.py           # MongoDB 連接測試
│   └── test_mongodb_connection()
│       ├── 測試 1: 資料庫連接
│       ├── 測試 2: 公司基本資料
│       ├── 測試 3: 股票代碼取得
│       ├── 測試 4: 歷史負債資料
│       └── 測試 5: 索引檢查
│
├── test_scraper.py              # 爬蟲功能測試
│   ├── test_single_company()   # 測試單一公司
│   └── test_multiple_companies() # 測試多家公司
│
├── requirements.txt             # Python 套件依賴
│   ├── pymongo                 # MongoDB 驅動
│   ├── requests                # HTTP 請求
│   ├── beautifulsoup4          # HTML 解析
│   ├── lxml                    # XML/HTML 解析器
│   ├── pandas                  # 資料處理
│   ├── aiohttp                 # 非同步 HTTP
│   ├── asyncio                 # 非同步 I/O
│   ├── python-dotenv           # 環境變數
│   └── tqdm                    # 進度條
│
├── .env.example                 # 環境變數範例
│   ├── MONGODB_URI             # MongoDB 連接字串
│   ├── MONGODB_DATABASE        # 資料庫名稱
│   ├── COMPANY_COLLECTION      # 公司資料 collection
│   ├── BALANCE_SHEET_COLLECTION # 負債資料 collection
│   ├── MAX_CONCURRENT_REQUESTS # 最大並發數
│   ├── REQUEST_DELAY           # 請求延遲
│   ├── RETRY_TIMES             # 重試次數
│   └── TIMEOUT                 # 請求逾時
│
├── .gitignore                   # Git 忽略清單
├── README.md                    # 完整說明文件
├── QUICKSTART.md                # 快速啟動指南
└── PROJECT_STRUCTURE.md         # 本檔案
```

## 資料流程圖

```
┌─────────────────────────────────────────────────────────────┐
│                        執行流程                              │
└─────────────────────────────────────────────────────────────┘

1. 初始化階段
   ┌──────────────┐
   │   main.py    │
   └──────┬───────┘
          │
          ├─→ 讀取 .env 配置
          │
          ├─→ 建立 MongoDBManager
          │       └─→ 連接 MongoDB
          │       └─→ 建立索引
          │
          └─→ 建立 MOPSScraper
                  └─→ 初始化 aiohttp session

2. 取得公司清單
   ┌──────────────────┐
   │ MongoDBManager   │
   └────────┬─────────┘
            │
            ├─→ 查詢「公司基本資料」collection
            │
            └─→ 提取股票代碼清單
                    └─→ ['2330', '2317', '2454', ...]

3. 爬取資料（並發執行）
   ┌──────────────────┐
   │  MOPSScraper     │
   └────────┬─────────┘
            │
            ├─→ 分批處理公司（batch_size=10）
            │       │
            │       └─→ 對每家公司並發爬取所有季度
            │               │
            │               ├─→ POST 請求到 MOPS
            │               ├─→ 解析 HTML 回應
            │               ├─→ 提取資產負債表項目
            │               └─→ 返回結構化資料
            │
            └─→ 合併所有結果

4. 儲存資料
   ┌──────────────────┐
   │ MongoDBManager   │
   └────────┬─────────┘
            │
            ├─→ 批次寫入（bulk_write）
            │       │
            │       └─→ upsert 模式（避免重複）
            │
            └─→ 儲存到「歷史負債資料」collection

5. 完成
   └─→ 顯示統計資訊
   └─→ 關閉連接
   └─→ 記錄日誌
```

## MongoDB 資料結構

### 輸入：公司基本資料 Collection

```javascript
{
  "_id": ObjectId("..."),
  "stock_code": "2330",        // 股票代碼
  "name": "台積電",             // 公司名稱
  // ... 其他欄位
}
```

### 輸出：歷史負債資料 Collection

```javascript
{
  "_id": ObjectId("..."),
  "stock_code": "2330",        // 股票代碼
  "year": 112,                 // 民國年
  "season": 3,                 // 季度 (1-4)
  "crawl_time": ISODate("2024-12-04T05:50:00Z"),
  "items": {
    "流動資產": "1500000000",
    "非流動資產": "2000000000",
    "資產總計": "3500000000",
    "流動負債": "800000000",
    "非流動負債": "500000000",
    "負債總計": "1300000000",
    "股本": "2000000000",
    "資本公積": "150000000",
    "保留盈餘": "50000000",
    "股東權益總計": "2200000000",
    // ... 更多會計項目
  }
}
```

### 索引設計

```javascript
// 索引 1: 複合唯一索引
{
  "stock_code": 1,
  "year": -1,
  "season": -1
}
// 用途：防止重複資料，加速查詢

// 索引 2: 股票代碼索引
{
  "stock_code": 1
}
// 用途：快速查詢特定公司的所有資料
```

## 核心技術

### 1. 非同步並發爬取

使用 `asyncio` 和 `aiohttp` 實現高效能並發：

```python
# 控制並發數量
semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

# 批次執行任務
results = await asyncio.gather(*tasks)
```

### 2. 智慧重試機制

自動處理暫時性錯誤：

```python
async def _fetch_balance_sheet(self, stock_code, year, season, retry_count=0):
    try:
        # 執行請求
        ...
    except Exception as e:
        if retry_count < RETRY_TIMES:
            await asyncio.sleep(REQUEST_DELAY * 2)
            return await self._fetch_balance_sheet(..., retry_count + 1)
```

### 3. Upsert 批次寫入

避免重複資料，提升寫入效能：

```python
operations = [
    UpdateOne(
        {'stock_code': data['stock_code'], 'year': data['year'], 'season': data['season']},
        {'$set': data},
        upsert=True
    )
    for data in data_list
]
result = collection.bulk_write(operations, ordered=False)
```

### 4. 請求速率控制

避免對伺服器造成過大負擔：

```python
# 並發控制
async with self.semaphore:
    # 執行請求
    ...
    # 請求延遲
    await asyncio.sleep(REQUEST_DELAY)
```

## 效能優化重點

1. **並發控制**: 使用 Semaphore 限制同時請求數
2. **批次處理**: 分批處理公司列表，避免記憶體溢出
3. **批次寫入**: 使用 bulk_write 提升資料庫寫入效能
4. **索引優化**: 建立適當索引加速查詢
5. **錯誤處理**: 完善的錯誤處理和重試機制
6. **日誌記錄**: 詳細的日誌幫助監控和除錯

## 擴展性設計

系統設計考慮了未來擴展：

1. **新增其他報表類型**: 只需繼承 MOPSScraper 並修改解析邏輯
2. **支援其他資料來源**: 可建立新的 Scraper 類別
3. **資料處理管線**: 可在儲存前加入資料清洗和轉換
4. **分散式部署**: 可使用訊息佇列（如 RabbitMQ）分散任務
5. **監控和告警**: 可整合 Prometheus、Grafana 等監控工具

## 安全性考量

1. **環境變數**: 敏感資訊儲存在 .env 文件
2. **輸入驗證**: 對股票代碼等輸入進行驗證
3. **錯誤處理**: 避免洩漏敏感資訊
4. **速率限制**: 遵守爬蟲禮儀，避免被封鎖
5. **日誌脫敏**: 不在日誌中記錄敏感資訊

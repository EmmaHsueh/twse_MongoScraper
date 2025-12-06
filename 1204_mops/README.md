# MOPS 資產負債表爬蟲系統

高效能的 MOPS 資產負債表資料爬蟲系統，支援非同步並發爬取，自動儲存至 MongoDB。

## 功能特色

- 非同步並發爬取，大幅提升效率
- 自動從 MongoDB 讀取公司清單
- 智慧重試機制，提高成功率
- 批次儲存，使用 upsert 避免重複資料
- 建立索引優化查詢效能
- 完整的日誌記錄和錯誤處理
- 進度追蹤和統計資訊

## 系統架構

```
1204_mops/
├── config.py              # 配置文件
├── db_manager.py          # MongoDB 資料庫管理器
├── mops_scraper.py        # MOPS 爬蟲核心
├── main.py                # 主程式入口
├── requirements.txt       # Python 套件依賴
├── .env.example          # 環境變數範例
└── README.md             # 說明文件
```

## 安裝步驟

### 1. 安裝依賴套件

```bash
pip install -r requirements.txt
```

### 2. 設定環境變數

複製 `.env.example` 為 `.env` 並修改設定：

```bash
cp .env.example .env
```

編輯 `.env` 文件：

```env
# MongoDB 連接設定
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DATABASE=TW_Stock
COMPANY_COLLECTION=公司基本資料
BALANCE_SHEET_COLLECTION=歷史負債資料

# 爬蟲設定
MAX_CONCURRENT_REQUESTS=5    # 並發請求數
REQUEST_DELAY=2              # 請求間隔（秒）
RETRY_TIMES=3                # 重試次數
TIMEOUT=30                   # 請求逾時（秒）
```

### 3. 準備 MongoDB 資料

確保 MongoDB 中的 `TW_Stock` 資料庫包含 `公司基本資料` collection，並且包含股票代碼欄位（支援的欄位名稱：`stock_code`, `code`, `股票代碼`, `symbol`, `ticker`）。

## 使用方法

### 執行爬蟲

```bash
python main.py
```

### 自訂起始年份

編輯 `main.py` 中的 `start_year` 變數（使用民國年）：

```python
start_year = 102  # 民國 102 年（西元 2013 年）
```

### 調整並發數和批次大小

在 `.env` 中調整：

```env
MAX_CONCURRENT_REQUESTS=10   # 增加並發數以提升速度
```

或在 `main.py` 中調整批次大小：

```python
all_data = await scraper.fetch_all_companies(
    stock_codes=stock_codes,
    start_year=start_year,
    batch_size=20  # 增加批次大小
)
```

## 資料結構

### 輸入：公司基本資料 Collection

```javascript
{
  "stock_code": "2330",  // 或 code, 股票代碼, symbol, ticker
  // ... 其他公司資料
}
```

### 輸出：歷史負債資料 Collection

```javascript
{
  "stock_code": "2330",
  "year": 112,           // 民國年
  "season": 1,           // 季度 (1-4)
  "crawl_time": ISODate("2024-12-04T10:30:00Z"),
  "items": {
    "流動資產": "1234567890",
    "流動負債": "987654321",
    "股東權益總計": "2345678901",
    // ... 其他資產負債表項目
  }
}
```

### 索引設計

系統自動建立以下索引以優化查詢：

1. **複合唯一索引**: `(stock_code, year, season)` - 防止重複資料
2. **單一索引**: `stock_code` - 加速公司查詢

## 效能優化

### 1. 並發控制

使用 `asyncio.Semaphore` 控制並發請求數，避免對伺服器造成過大負擔：

```python
MAX_CONCURRENT_REQUESTS=5  # 保守設定
MAX_CONCURRENT_REQUESTS=10 # 激進設定（可能被封鎖）
```

### 2. 請求延遲

在請求之間加入延遲，模擬真實使用者行為：

```python
REQUEST_DELAY=2  # 較安全
REQUEST_DELAY=1  # 較快但風險較高
```

### 3. 批次處理

分批處理公司列表，避免一次性載入過多資料：

```python
batch_size=10  # 每批處理 10 家公司
```

### 4. 智慧重試

自動重試失敗的請求，提高資料完整性：

```python
RETRY_TIMES=3  # 最多重試 3 次
```

## 錯誤處理

系統包含完整的錯誤處理機制：

- **連接錯誤**: 自動重試
- **逾時錯誤**: 自動重試並增加延遲
- **解析錯誤**: 記錄並繼續處理其他資料
- **資料庫錯誤**: 批次寫入錯誤處理

## 日誌系統

所有執行記錄會同時輸出到：
- 終端機（即時顯示）
- 日誌檔案（格式：`scraper_YYYYMMDD_HHMMSS.log`）

日誌等級：
- `INFO`: 一般資訊
- `WARNING`: 警告訊息
- `ERROR`: 錯誤訊息
- `DEBUG`: 除錯資訊（預設關閉）

## 注意事項

1. **遵守爬蟲禮儀**: 請勿設定過高的並發數和過低的延遲時間
2. **資料更新頻率**: 季報通常在季度結束後 45 天內公布
3. **網路穩定性**: 建議在網路穩定的環境下執行
4. **MongoDB 空間**: 確保有足夠的儲存空間
5. **執行時間**: 完整爬取所有公司可能需要數小時

## 進階使用

### 只爬取特定公司

```python
# 在 main.py 中修改
stock_codes = ['2330', '2317', '2454']  # 只爬取台積電、鴻海、聯發科
```

### 只爬取最近幾季

```python
# 在 mops_scraper.py 的 _get_year_season_list 方法中
start_year = 112  # 只爬取民國 112 年之後的資料
```

### 匯出資料

```python
from db_manager import MongoDBManager

db = MongoDBManager()
data = list(db.balance_sheet_collection.find({'stock_code': '2330'}))
# 使用 pandas 匯出為 CSV
import pandas as pd
df = pd.DataFrame(data)
df.to_csv('balance_sheet_2330.csv', index=False)
```

## 疑難排解

### 1. MongoDB 連接失敗

```bash
# 檢查 MongoDB 是否執行中
mongosh

# 或使用 Docker 啟動 MongoDB
docker run -d -p 27017:27017 --name mongodb mongo
```

### 2. 找不到公司資料

檢查 collection 名稱和欄位名稱是否正確：

```python
# 在 db_manager.py 中查看日誌
logger.warning(f"可用欄位: {list(first_company.keys())}")
```

### 3. 爬取速度過慢

調整並發數和批次大小：

```env
MAX_CONCURRENT_REQUESTS=10
```

```python
batch_size=20
```

### 4. 被伺服器封鎖

降低並發數和增加延遲：

```env
MAX_CONCURRENT_REQUESTS=3
REQUEST_DELAY=3
```

## 授權

此專案僅供學習和研究使用，請遵守 MOPS 網站的使用條款。

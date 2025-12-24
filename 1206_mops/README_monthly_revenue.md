# 每月營收爬蟲使用說明

## 功能說明

自動爬取台灣證券交易所公開資訊觀測站的每月營收資料，支援：
- 上市（sii）、上櫃（otc）、興櫃（rotc）公司
- 民國 91 年至 113 年
- 民國 100 年起自動區分國內外營收

## 網址規則

範例網址：`https://mopsov.twse.com.tw/nas/t21/sii/t21sc03_91_1.html`

### 網址結構說明

```
https://mopsov.twse.com.tw/nas/t21/{market}/{page}_{year}_{month}_{type}.html
```

- **{market}**: 市場別
  - `sii` = 上市
  - `otc` = 上櫃
  - `rotc` = 興櫃

- **{page}**: `t21sc03` (固定，不變動)

- **{year}**: 民國年度（例如：91, 100, 113）

- **{month}**: 月份（1-12）

- **{type}**: 資料類型（僅民國 100 年起適用）
  - `0` = 國內營收
  - `1` = 國外營收
  - 民國 91-99 年：無此參數，不分國內外

### 網址範例

| 年度 | 月份 | 市場 | 類型 | 網址 |
|------|------|------|------|------|
| 91 | 1 | 上市 | - | `t21sc03_91_1.html` |
| 100 | 1 | 上市 | 國內 | `t21sc03_100_1_0.html` |
| 100 | 1 | 上市 | 國外 | `t21sc03_100_1_1.html` |
| 113 | 12 | 上櫃 | 國內 | `otc/t21sc03_113_12_0.html` |

## 資料儲存

### MongoDB 結構

- **資料庫**：`TW_Stock`
- **Collection**：`每月營收`
- **索引**：`(公司代號, 年度, 月份)` - 唯一索引

### 資料欄位

每筆記錄包含以下欄位：

```python
{
    "公司代號": "2330",           # 公司代號
    "年度": 113,                  # 民國年度
    "月份": 1,                    # 月份
    "市場別": "sii",              # 市場別 (sii/otc/rotc)
    "公司名稱": "台積電",         # 公司名稱
    "營業收入_當月營收": 123456,  # 當月營收（千元）
    "營業收入_上月營收": 120000,  # 上月營收（千元）
    "營業收入_去年當月營收": 110000,
    "營業收入_上月比較 增減(%)": 2.88,
    "營業收入_去年同月 增減(%)": 12.23,
    "累計營業收入_當月累計營收": 123456,
    "累計營業收入_去年累計營收": 110000,
    "累計營業收入_前期比較 增減(%)": 12.23,
    "更新時間": ISODate("2025-12-07T...")
}
```

## 使用方式

### 1. 基本使用

```bash
# 啟動虛擬環境
source venv/bin/activate

# 執行爬蟲
python monthly_revenue_scraper.py
```

### 2. 互動式選單

執行後會顯示以下選項：

```
每月營收爬蟲
============================================================
1. 爬取所有資料 (民國 91-113 年)
2. 爬取指定年份範圍
3. 爬取單一年度
4. 查看資料庫統計
============================================================
請選擇模式 (1-4):
```

### 3. 選項說明

#### 選項 1：爬取所有資料
- 爬取民國 91-113 年所有上市、上櫃、興櫃公司的每月營收
- **預估時間**：約 1-2 小時（取決於網路速度）
- **總請求次數**：
  - 91-99 年：3 市場 × 9 年 × 12 月 = 324 次
  - 100-113 年：3 市場 × 14 年 × 12 月 × 2 類型 = 1,008 次
  - **總計**：1,332 次請求

#### 選項 2：爬取指定年份範圍
```
請輸入起始年度 (民國): 110
請輸入結束年度 (民國): 113
```
- 適合分批爬取，避免一次執行時間過長

#### 選項 3：爬取單一年度
```
請輸入年度 (民國): 113
```
- 爬取特定年度的所有月份資料

#### 選項 4：查看資料庫統計
顯示目前資料庫中的資料筆數

### 4. 程式化使用

```python
from monthly_revenue_scraper import MonthlyRevenueScraper

scraper = MonthlyRevenueScraper()

try:
    # 方式 1: 爬取所有資料
    scraper.scrape_all(start_year=91, end_year=113, delay=2)

    # 方式 2: 爬取指定年份範圍
    scraper.scrape_year_range(110, 113, delay=2)

    # 方式 3: 爬取單一月份
    scraper.scrape_single_month(
        market_type="sii",  # 上市
        year=113,
        month=1,
        data_type="0",      # 國內（100年起需要）
        delay=2
    )

    # 查看統計
    stats = scraper.get_statistics()
    print(stats)

finally:
    scraper.close()
```

## 爬蟲邏輯

### 1. 資料驗證
- 只儲存在「公司基本資料」collection 中存在的公司
- 自動跳過已存在的資料（避免重複）

### 2. 年份區分
```python
if year < 100:
    # 民國 91-99 年：不分國內外
    爬取單一網址
else:
    # 民國 100 年起：分國內外
    爬取國內網址 (data_type="0")
    爬取國外網址 (data_type="1")
```

### 3. 表格解析
- 每個網頁包含多個產業別表格
- 自動解析所有表格並合併資料
- 處理多層次欄位名稱（tuple 格式）

### 4. 錯誤處理
- HTTP 404：資料不存在，自動跳過
- SSL 錯誤：已設定跳過 SSL 驗證
- 重複資料：使用 upsert 避免衝突

## 注意事項

### 1. 執行建議
- **分批執行**：建議每次爬取 2-3 年的資料，避免一次執行時間過長
- **請求延遲**：預設延遲 2 秒，避免請求過於頻繁
- **斷點續傳**：程式會自動跳過已存在的資料，可以隨時中斷並重新執行

### 2. 資料完整性
- 並非所有公司在所有月份都有資料
- 404 錯誤表示該月份無資料公布，屬正常現象
- 興櫃公司資料較少，可能有大量 404

### 3. MongoDB 注意
- 確保 MongoDB 服務正在運行
- 確保「公司基本資料」collection 已建立
- 首次執行會自動建立索引

## 範例執行流程

### 建議執行順序

```bash
# 1. 測試單一月份（確認程式正常）
python test_revenue_scraper.py

# 2. 爬取近期資料（民國 110-113 年）
python monthly_revenue_scraper.py
# 選擇選項 2，輸入 110 和 113

# 3. 爬取早期資料（民國 91-99 年）
python monthly_revenue_scraper.py
# 選擇選項 2，輸入 91 和 99

# 4. 爬取中期資料（民國 100-109 年）
python monthly_revenue_scraper.py
# 選擇選項 2，輸入 100 和 109

# 5. 查看最終統計
python monthly_revenue_scraper.py
# 選擇選項 4
```

### 預期輸出範例

```
============================================================
處理 113 年度資料
============================================================

[上市] 113年1月 (國內)
  URL: https://mopsov.twse.com.tw/nas/t21/sii/t21sc03_113_1_0.html
  ✓ 解析完成: 776 筆有效資料 (跳過 8 筆不在基本資料中)
  ✓ 成功儲存 776 筆資料到 MongoDB

[上市] 113年1月 (國外)
  URL: https://mopsov.twse.com.tw/nas/t21/sii/t21sc03_113_1_1.html
  ✓ 解析完成: 3 筆有效資料
  ✓ 成功儲存 3 筆資料到 MongoDB

[上櫃] 113年1月 (國內)
  URL: https://mopsov.twse.com.tw/nas/t21/otc/t21sc03_113_1_0.html
  ✓ 解析完成: 658 筆有效資料 (跳過 5 筆不在基本資料中)
  ✓ 成功儲存 658 筆資料到 MongoDB
```

## 資料查詢範例

### MongoDB 查詢

```javascript
// 查詢台積電 (2330) 113 年所有月份營收
db.每月營收.find({
  "公司代號": "2330",
  "年度": 113
}).sort({"月份": 1})

// 查詢 113 年 1 月所有上市公司營收，按營收排序
db.每月營收.find({
  "年度": 113,
  "月份": 1,
  "市場別": "sii"
}).sort({"營業收入_當月營收": -1})

// 統計每個市場別的資料筆數
db.每月營收.aggregate([
  {$group: {
    _id: "$市場別",
    count: {$sum: 1}
  }}
])
```

### Python 查詢

```python
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client['TW_Stock']
collection = db['每月營收']

# 查詢台積電 113 年營收
results = collection.find({
    "公司代號": "2330",
    "年度": 113
}).sort("月份", 1)

for r in results:
    print(f"{r['月份']}月: {r['營業收入_當月營收']:,} 千元")
```

## 故障排除

### 1. SSL 錯誤
已在程式中處理，如仍遇到問題：
```python
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
```

### 2. MongoDB 連線失敗
```bash
# 確認 MongoDB 是否運行
brew services list | grep mongodb

# 啟動 MongoDB
brew services start mongodb-community
```

### 3. 找不到公司代號
- 確認「公司基本資料」collection 已建立
- 檢查欄位名稱是否為「公司 代號」（有空格）

### 4. 重複資料錯誤
已使用 upsert 處理，如仍有問題，請確認索引正確：
```javascript
db.每月營收.getIndexes()
// 應該有: { "公司代號": 1, "年度": 1, "月份": 1 }
```

## 效能優化

### 調整請求延遲
```python
# 預設延遲 2 秒
scraper.scrape_all(start_year=91, end_year=113, delay=2)

# 加快速度（風險：可能被限制）
scraper.scrape_all(start_year=91, end_year=113, delay=1)

# 降低速度（更安全）
scraper.scrape_all(start_year=91, end_year=113, delay=3)
```


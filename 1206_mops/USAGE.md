# 上市櫃公司資產負債表爬蟲 - 使用指南

## 快速開始

### 1. 安裝相依套件

```bash
source venv/bin/activate
pip install pymongo
```

### 2. 測試 MongoDB 連線

```bash
python mongodb_helper.py
```

確認輸出:
```
=== MongoDB 連線測試 ===
資料庫: TW_Stock
公司總數: XXX
上市公司: XXX
上櫃公司: XXX
資產負債表資料: XXX 筆
```

### 3. 執行批次爬蟲

```bash
python batch_scraper.py
```

## 功能說明

### 核心功能

1. **自動驗證公司代號**
   - 只爬取存在於「公司基本資料」collection 中的公司
   - 使用「公司代號」進行比對

2. **智慧去重**
   - 爬取前自動檢查資料是否已存在
   - 使用複合索引 (公司代號 + 年度 + 季別) 確保唯一性
   - 避免重複爬取,提升效率

3. **斷點續傳**
   - 中斷後可繼續執行
   - 已爬取的資料不會重複處理

4. **批次儲存**
   - 自動儲存至 MongoDB
   - Collection: `TW_Stock.上市櫃公司資產負債表`

### 執行模式

#### 模式 1: 完整爬取
```
爬取所有歷史資料 (100-113 年)
自動跳過已存在的資料
適合第一次執行
```

#### 模式 2: 智慧補缺 (推薦)
```
只爬取缺少的資料
最高效率
適合定期更新
```

#### 模式 3: 測試模式
```
只爬取少量資料
用於測試連線和功能
```

## 資料結構

### MongoDB Collections

#### 輸入: `公司基本資料`
```javascript
{
  "公司代號": "2330",
  "公司名稱": "台積電",
  "市場別": "上市",
  ...
}
```

#### 輸出: `上市櫃公司資產負債表`
```javascript
{
  "公司代號": "2330",
  "年度": 113,
  "季別": 3,
  "流動資產": 1234567890,
  "固定資產": 9876543210,
  ...
  "爬取時間": ISODate("2024-12-06T14:30:00Z"),
  "更新時間": ISODate("2024-12-06T14:30:00Z")
}
```

### 索引設計

```javascript
// 公司基本資料
{ "公司代號": 1 }  // unique

// 上市櫃公司資產負債表
{ "公司代號": 1, "年度": 1, "季別": 1 }  // unique compound index
```

## 效率優化

### 1. 去重機制
- 爬取前檢查 `balance_sheet_exists()`
- 使用 MongoDB 索引加速查詢
- 避免重複下載相同資料

### 2. 批次處理
- 使用 `upsert` 操作避免重複
- 批次插入減少資料庫連線次數

### 3. 請求控制
- 每筆資料間隔 3 秒
- 每家公司間隔 10 秒
- 避免觸發反爬蟲機制

### 4. 斷點續傳
- 隨時可中斷
- 下次執行自動跳過已爬取資料
- 不需從頭開始

## 執行範例

### 範例 1: 首次完整爬取

```bash
python batch_scraper.py
# 選擇: 1 (完整爬取)
```

預估時間:
- 上市公司約 900 家 × 14 年 × 4 季 = 50,400 筆
- 上櫃公司約 800 家 × 14 年 × 4 季 = 44,800 筆
- 總計: 約 95,000 筆
- 每筆 3 秒 = 約 79 小時 (可分批執行)

### 範例 2: 定期更新

```bash
python batch_scraper.py
# 選擇: 2 (智慧補缺)
```

只爬取缺少的資料,通常只需數分鐘

### 範例 3: 測試功能

```bash
python batch_scraper.py
# 選擇: 3 (測試模式)
```

只爬取 113 年上市公司資料,快速測試

## 程式架構

```
1206_mops/
├── mops_scraper.py       # 核心爬蟲引擎
├── mongodb_helper.py     # MongoDB 操作輔助
├── batch_scraper.py      # 批次爬蟲主程式
├── debug_elements.py     # 網頁元素偵錯工具
├── debug_storage.py      # sessionStorage 偵錯工具
├── requirements.txt      # Python 相依套件
├── run.sh               # 快速啟動腳本
└── venv/                # 虛擬環境
```

## 常見問題

### Q1: 如何只爬取特定公司?

修改 `batch_scraper.py`:
```python
# 只爬取特定公司代號
company_codes = ["2330", "2317", "2454"]

for company_code in company_codes:
    batch_scraper.scrape_and_save_one("sii", company_code, 113, 3)
```

### Q2: 如何修改爬取年份範圍?

修改 `batch_scraper.py` 的 `main()` 函數:
```python
batch_scraper.scrape_all_history(
    market_types=["sii", "otc"],
    start_year=110,  # 修改起始年
    end_year=113     # 修改結束年
)
```

### Q3: 執行中斷後如何繼續?

直接再次執行即可,程式會自動跳過已爬取的資料:
```bash
python batch_scraper.py
```

### Q4: 如何查看爬取進度?

查詢 MongoDB:
```javascript
// 查看總筆數
db.上市櫃公司資產負債表.count()

// 查看特定公司的資料
db.上市櫃公司資產負債表.find({"公司代號": "2330"}).count()

// 查看各年度的資料量
db.上市櫃公司資產負債表.aggregate([
  { $group: { _id: "$年度", count: { $sum: 1 } } },
  { $sort: { _id: 1 } }
])
```

### Q5: 如何加快爬取速度?

1. 使用「智慧補缺」模式
2. 調整等待時間 (注意可能觸發反爬蟲)
3. 使用多個 IP 輪替 (需修改程式)

## 注意事項

1. **遵守網站使用條款**
   - 不要過度頻繁請求
   - 建議晚上或離峰時段執行

2. **資料正確性**
   - 爬取後建議抽查驗證
   - 注意財報更新/更正的情況

3. **資料庫備份**
   - 定期備份 MongoDB
   - 避免資料遺失

4. **效能監控**
   - 監控 MongoDB 效能
   - 適時清理舊資料或建立歸檔

## 進階使用

### 自訂爬蟲邏輯

編輯 `batch_scraper.py` 的 `parse_balance_sheet_table()` 方法:
```python
def parse_balance_sheet_table(self, html_content, company_code, year, season):
    # 自訂解析邏輯
    # ...
    return records
```

### 整合其他資料源

可參考相同架構爬取其他財報:
- 損益表 (t163sb04)
- 現金流量表 (t163sb20)
- 股東權益變動表 (t164sb06)

## 授權

本專案僅供學習研究使用,請遵守相關法律規範和網站使用條款。

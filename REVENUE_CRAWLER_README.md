# 月營收爬蟲 (Monthly Revenue Crawler)

台灣上市、上櫃、興櫃公司月營收資料爬蟲，使用台灣證券交易所（TWSE）和證券櫃檯買賣中心（TPEx）OpenAPI。

## 功能特色

- ✅ 支援**上市（Listed）、上櫃（OTC）、興櫃（Emerging）**三大市場
- ✅ 使用官方 OpenAPI，資料穩定可靠
- ✅ 自動儲存到 MongoDB
- ✅ 自動檢查資料覆蓋率
- ✅ 支援 upsert 更新機制（避免重複資料）

## 資料來源

### 台灣證券交易所（TWSE） OpenAPI
- **上市公司**: `https://openapi.twse.com.tw/v1/opendata/t187ap05_L`
- **公開發行公司**: `https://openapi.twse.com.tw/v1/opendata/t187ap05_P`

### 證券櫃檯買賣中心（TPEx） OpenAPI
- **上櫃公司**: `https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap05_O`
- **興櫃公司**: `https://www.tpex.org.tw/openapi/v1/t187ap05_R`

## 資料覆蓋率

根據最新測試結果：
- 上市公司：**99.2%**（1058/1066）
- 上櫃公司：**100.0%**（860/860）
- 興櫃公司：**99.7%**（357/358）
- 總計：**2583** 筆月營收資料

缺少的主要是 **TDR 存託憑證**公司（境外公司），這些公司通常無台灣月營收申報。

## 安裝

確保已安裝 Python 虛擬環境和依賴套件：

\`\`\`bash
bash setup_venv.sh
\`\`\`

## 使用方式

### 快速執行（推薦）

使用便利腳本執行爬蟲：

\`\`\`bash
bash run_revenue_crawler.sh
\`\`\`

### 自訂參數執行

\`\`\`bash
source venv/bin/activate

# 基本執行
python revenue_crawler.py

# 自訂 MongoDB 連接
python revenue_crawler.py --mongo-uri mongodb://localhost:27017

# 自訂資料庫和 collection
python revenue_crawler.py --database TW_Stock --collection 每月營收

# 清空 collection 後重新插入
python revenue_crawler.py --drop

# 檢查資料覆蓋率
python revenue_crawler.py --check-coverage

# 組合使用
python revenue_crawler.py --drop --check-coverage
\`\`\`

### 環境變數設定

使用環境變數自訂設定：

\`\`\`bash
MONGO_URI=mongodb://localhost:27017 \\
DATABASE=TW_Stock \\
COLLECTION=每月營收 \\
bash run_revenue_crawler.sh
\`\`\`

## 資料格式

每筆月營收資料包含以下欄位：

| 欄位名稱 | 說明 | 範例 |
|---------|------|-----|
| 出表日期 | 資料發布日期 | 1141117 |
| 資料年月 | 資料所屬年月（民國年） | 11410 |
| 公司代號 | 股票代碼 | 2330 |
| 公司名稱 | 公司名稱 | 台積電 |
| 產業別 | 產業分類 | 半導體業 |
| 營業收入-當月營收 | 當月營業收入（千元） | 123456789 |
| 營業收入-上月營收 | 上月營業收入（千元） | 120000000 |
| 營業收入-去年當月營收 | 去年同月營業收入（千元） | 100000000 |
| 營業收入-上月比較增減(%) | 月增率 | 2.88 |
| 營業收入-去年同月增減(%) | 年增率 | 23.46 |
| 累計營業收入-當月累計營收 | 本年累計營收（千元） | 1234567890 |
| 累計營業收入-去年累計營收 | 去年累計營收（千元） | 1000000000 |
| 累計營業收入-前期比較增減(%) | 累計年增率 | 23.46 |
| 備註 | 備註說明 | - |

## 資料庫結構

### 儲存位置
- **資料庫**: `TW_Stock`
- **Collection**: `每月營收`

### Unique Key
資料使用以下欄位組合作為唯一識別：
- `公司代號`
- `資料年月`

重複執行爬蟲時，相同的公司代號和年月會自動更新（upsert）。

## 命令列參數

| 參數 | 說明 | 預設值 |
|------|------|--------|
| `--mongo-uri` | MongoDB 連接字串 | mongodb://localhost:27017 |
| `--database` | MongoDB 資料庫名稱 | TW_Stock |
| `--collection` | MongoDB collection 名稱 | 每月營收 |
| `--drop` | 清空 collection 後再插入 | False |
| `--verify-ssl` | 驗證 SSL 憑證 | False |
| `--log-level` | 日誌等級（DEBUG/INFO/WARNING/ERROR） | INFO |
| `--check-coverage` | 檢查資料覆蓋率 | False |

## 常見問題

### Q: 為什麼有些公司沒有月營收資料？

A: 缺少資料的主要是：
1. **TDR 存託憑證**：境外公司，無需申報台灣月營收
2. **新上市/櫃公司**：尚未申報首次月營收
3. **暫停交易公司**：已下市或暫停營業

### Q: 資料更新頻率如何？

A: OpenAPI 提供的是**最新一期**的月營收資料。建議：
- **每月 10-15 日**執行爬蟲（公司申報截止日後）
- 定期執行以累積歷史資料

### Q: 如何查詢特定公司的月營收？

A: 使用 MongoDB 查詢：

\`\`\`python
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")
db = client["TW_Stock"]
revenue_col = db["每月營收"]

# 查詢台積電（2330）的月營收
tsmc_revenue = revenue_col.find({"公司代號": "2330"})
for record in tsmc_revenue:
    print(record)
\`\`\`

### Q: 可以抓取歷史資料嗎？

A: 目前 OpenAPI 只提供最新一期資料。若需歷史資料，有兩種方式：
1. **定期執行爬蟲**：每月自動執行以累積歷史記錄
2. **使用 MOPS API**：需要逐月查詢（較複雜，暫不支援）

## 相關腳本

- `revenue_crawler.py` - 主要爬蟲程式
- `run_revenue_crawler.sh` - 便利執行腳本
- `analyze_missing.py` - 分析缺失資料的公司
- `test_revenue_endpoints.py` - 測試 API 端點

## 技術架構

```
┌─────────────────┐
│  TWSE OpenAPI   │ ─┐
│  (上市、公開發行) │  │
└─────────────────┘  │
                     ├─> revenue_crawler.py ─> MongoDB (TW_Stock.每月營收)
┌─────────────────┐  │
│  TPEx OpenAPI   │ ─┘
│  (上櫃、興櫃)     │
└─────────────────┘
```

## 授權與免責聲明

- 資料來源：台灣證券交易所、證券櫃檯買賣中心 OpenAPI
- 本專案僅供教育和研究用途
- 使用者須遵守相關資料使用規範

## 更新日誌

### 2024-11-25
- ✅ 完成月營收爬蟲開發
- ✅ 支援上市、上櫃、興櫃三大市場
- ✅ 資料覆蓋率達 99%+
- ✅ 自動化執行腳本

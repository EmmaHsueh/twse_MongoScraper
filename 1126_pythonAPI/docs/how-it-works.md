# 系統運作說明

本文說明專案中「月營收爬蟲」與「歷史股價 API」的架構、流程與執行方式，涵蓋 TypeScript 與 Python 兩個版本的爬蟲。

## Mongo 設定與集合
- 連線設定：`.env` 由 `src/config/env.ts` 讀取，Python 版由啟動參數指定。
- 預設 DB 名稱：`mops`（TS） / `TW_Stock`（Python，可調）。
- 預設集合名稱：
  - `每月營收`
  - `公司基本資料`
  - `歷史股價`

## TypeScript 版：月營收爬蟲與 API
- 入口腳本：`src/scripts/fetchMonthlyRevenue.ts`
- 爬蟲核心：`src/crawler/mopsRevenueCrawler.ts`
  1. 針對上市(sii)/上櫃(otc)/興櫃(rotc) 呼叫 MOPS 介面 `https://mops.twse.com.tw/mops/web/ajax_t21sc04_ifrs`。
  2. 使用 cheerio 解析表格，依欄位名稱（公司代號、公司名稱、營業收入、本年累計、年增率等）抽取數值。
  3. 將 (stockId, year, month, market) 作為 upsert 條件，寫入 `每月營收`。
  4. 讀取 `公司基本資料` 集合，檢查哪些公司代號在本月沒有營收資料，列出缺漏。
- 執行方式：
  ```bash
  npm run crawler:revenue                  # 預設抓上個月，三市場
  npm run crawler:revenue -- --year=2024 --month=11 --markets=sii,otc,rotc
  ```
  輸出包含每市場筆數、總寫入數，以及缺漏公司代碼。

### 歷史股價 API
- 檔案：`src/api/server.ts`
- 路由：`GET /api/stock-price?stock_id=2330&start=YYYY-MM-DD&end=YYYY-MM-DD`
- 驗證：zod 檢查參數格式；start<=end 才通過。
- 查詢：從 `歷史股價` 集合以日期排序輸出 `{ Result, Status }`。
- 啟動：
  ```bash
  npm run api
  ```
  伺服器預設 port 來自 `.env` 的 `PORT`（預設 4000）。

## Python 版：月營收爬蟲（不影響原 TS 程式）
- 檔案：`python/fetch_monthly_revenue.py`
- 依賴：`pip install requests beautifulsoup4 pymongo`
- 流程：
  1. POST 同一個 MOPS 端點取得 HTML。
  2. BeautifulSoup 解析表格，抽取與 TS 版相同欄位。
  3. 以 (stockId, year, month, market) upsert 至 MongoDB `每月營收`。
  4. 檢查 `公司基本資料` 是否有缺漏。
- 預設 DB：`TW_Stock`，可用參數覆蓋；連線 URI 亦可指定。
- 執行範例（Windows 可用 `py -3`）：
  ```bash
  py -3 python/fetch_monthly_revenue.py
  py -3 python/fetch_monthly_revenue.py --year 2024 --month 11 --markets sii,otc,rotc --mongo-uri "mongodb://localhost:27017" --mongo-db TW_Stock
  ```
  終端輸出每市場抓取/寫入筆數與缺漏代碼。

## 錯誤排除與注意事項
- 若回傳筆數為 0：可能該月份尚未公布；可改抓已公布月份驗證。
-,headers 解析依賴表頭文字，如 MOPS 改版需同步更新關鍵字。
- `公司基本資料` 若為空，缺漏檢查會跳過；請先寫入公司清單再比對。

## 檔案總覽
- TS 爬蟲：`src/scripts/fetchMonthlyRevenue.ts`、`src/crawler/mopsRevenueCrawler.ts`
- API：`src/api/server.ts`
- 共用設定/型別：`src/config/env.ts`、`src/db/mongo.ts`、`src/types/mops.ts`
- Python 爬蟲：`python/fetch_monthly_revenue.py`

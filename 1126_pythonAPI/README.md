## 專案說明

新增後端腳本與 API：
- Mongo 連線 helper：`src/db/mongo.ts`
- MOPS 月營收爬蟲：`src/crawler/mopsRevenueCrawler.ts`，涵蓋上市/上櫃/興櫃寫入 `每月營收`，並比對 `公司基本資料` 缺漏
- Express API：`src/api/server.ts`，提供歷史股價查詢

## 安裝依賴
```bash
npm install
```

## 環境變數
- `MONGO_URI` (default: `mongodb://localhost:27017`)
- `MONGO_DB_NAME` (default: `mops`)
- `MONGO_REVENUE_COLLECTION` (default: `每月營收`)
- `MONGO_BASIC_COLLECTION` (default: `公司基本資料`)
- `MONGO_STOCK_PRICE_COLLECTION` (default: `歷史股價`)
- `PORT` (default: `4000`)

## 執行月營收爬蟲
```bash
# 預設爬取上一個月，上市/上櫃/興櫃
npm run crawler:revenue

# 指定年月與市場 (sii: 上市, otc: 上櫃, rotc: 興櫃)
npm run crawler:revenue -- --year=2024 --month=11 --markets=sii,otc,rotc
```
流程：
1. 爬取 `https://mops.twse.com.tw/mops/#/web/t21sc04_ifrs`
2. 解析表格後 upsert 至 `每月營收`（依 `stockId/year/month/market`）
3. 檢查 `公司基本資料` 內每家公司是否有該月營收，列出缺漏代碼

## 啟動歷史股價 API
```bash
npm run api
```
路由：
- `GET /api/stock-price?stock_id=2330&start=2024-01-01&end=2024-02-01`

回傳格式：
```json
{
  "Result": [ /* 股價資料 */ ],
  "Status": { "Code": 0, "Message": "Success" }
}
```
若驗證失敗回 400，內部錯誤回 500，Result 為空陣列。

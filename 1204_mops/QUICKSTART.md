# 快速啟動指南

## 步驟 1: 安裝依賴

```bash
pip install -r requirements.txt
```

## 步驟 2: 設定環境變數

```bash
# 複製範例檔案
cp .env.example .env

# 編輯 .env 文件，設定你的 MongoDB 連接資訊
# 預設設定通常適用於本地 MongoDB
```

## 步驟 3: 測試 MongoDB 連接

```bash
# 執行連接測試
python test_connection.py
```

預期輸出：
```
[測試 1] 檢查資料庫連接
資料庫中的 collections: ['公司基本資料', ...]

[測試 2] 檢查公司基本資料 collection
公司基本資料總數: 1000
第一筆公司資料的欄位: ['stock_code', 'name', ...]

[測試 3] 取得股票代碼
成功取得 1000 個股票代碼
前 10 個股票代碼: ['1101', '1102', ...]

測試完成！系統準備就緒
```

## 步驟 4: 測試爬蟲功能

### 測試單一公司（台積電）

```bash
python test_scraper.py
```

### 測試多家公司

```bash
python test_scraper.py multi
```

## 步驟 5: 執行完整爬蟲

```bash
python main.py
```

## 常見問題

### Q1: MongoDB 連接失敗

**解決方法：**
```bash
# 確認 MongoDB 是否執行
mongosh

# 如果沒有安裝 MongoDB，使用 Docker 啟動
docker run -d -p 27017:27017 --name mongodb mongo
```

### Q2: 找不到公司基本資料

**解決方法：**

確保 MongoDB 中有 `公司基本資料` collection，並包含股票代碼欄位。

支援的欄位名稱：
- `stock_code`
- `code`
- `股票代碼`
- `symbol`
- `ticker`

### Q3: 爬取速度太慢

**解決方法：**

調整 `.env` 中的並發設定：

```env
MAX_CONCURRENT_REQUESTS=10  # 增加並發數
REQUEST_DELAY=1            # 減少延遲（注意：可能被封鎖）
```

### Q4: 被 MOPS 伺服器封鎖

**解決方法：**

降低爬取速度：

```env
MAX_CONCURRENT_REQUESTS=3  # 減少並發數
REQUEST_DELAY=3           # 增加延遲
```

## 效能參考

基於以下設定：
```env
MAX_CONCURRENT_REQUESTS=5
REQUEST_DELAY=2
```

預估時間（1000 家公司，10 年資料）：
- 總請求數：約 40,000 次
- 預估時間：約 22-25 小時

優化設定（風險較高）：
```env
MAX_CONCURRENT_REQUESTS=10
REQUEST_DELAY=1
```
- 預估時間：約 11-13 小時

## 建議執行方式

### 方式 1: 後台執行（Linux/Mac）

```bash
nohup python main.py > output.log 2>&1 &

# 查看執行狀態
tail -f output.log

# 查看進程
ps aux | grep main.py
```

### 方式 2: 使用 screen（Linux/Mac）

```bash
# 建立新的 screen session
screen -S mops_scraper

# 執行爬蟲
python main.py

# 離開 screen（按鍵）
Ctrl+A, D

# 重新連接
screen -r mops_scraper
```

### 方式 3: 使用 tmux（Linux/Mac）

```bash
# 建立新的 tmux session
tmux new -s mops_scraper

# 執行爬蟲
python main.py

# 離開 tmux（按鍵）
Ctrl+B, D

# 重新連接
tmux attach -t mops_scraper
```

## 監控執行進度

### 查看日誌檔案

```bash
# 即時查看最新日誌
tail -f scraper_*.log

# 搜尋錯誤
grep ERROR scraper_*.log

# 查看統計資訊
grep "爬蟲統計" scraper_*.log
```

### 查詢資料庫

```javascript
// 連接到 MongoDB
use TW_Stock

// 查看資料筆數
db.歷史負債資料.count()

// 查看已爬取的公司數量
db.歷史負債資料.distinct("stock_code").length

// 查看特定公司的資料
db.歷史負債資料.find({stock_code: "2330"}).sort({year: -1, season: -1})

// 查看最新爬取時間
db.歷史負債資料.find().sort({crawl_time: -1}).limit(1)
```

## 進階使用

### 只爬取特定年份範圍

編輯 `main.py`：

```python
# 只爬取民國 110-112 年
start_year = 110
```

### 只爬取特定公司

編輯 `main.py`：

```python
# 替換這一行
# stock_codes = db_manager.get_company_stock_codes()

# 改為
stock_codes = ['2330', '2317', '2454']  # 指定公司
```

### 斷點續爬

系統使用 upsert 機制，重複執行會自動跳過已存在的資料。

如果爬蟲中斷，直接重新執行即可：

```bash
python main.py
```

## 技術支援

如有問題，請檢查：

1. MongoDB 連接狀態
2. 網路連接狀態
3. 日誌檔案中的錯誤訊息
4. MOPS 網站是否正常運作

## 授權與聲明

此工具僅供學習和研究使用，請遵守 MOPS 網站的使用條款和相關法律規定。

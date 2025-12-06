# 部署檢查清單

## 部署前準備

### 1. 環境檢查

- [ ] Python 版本確認（需要 3.8+）
  ```bash
  python --version
  # 或
  python3 --version
  ```

- [ ] MongoDB 安裝與執行
  ```bash
  mongosh
  # 或
  mongo
  ```

- [ ] 網路連接測試
  ```bash
  ping mops.twse.com.tw
  ```

### 2. 安裝依賴

- [ ] 建立虛擬環境（建議）
  ```bash
  python -m venv venv
  source venv/bin/activate  # Linux/Mac
  # 或
  venv\Scripts\activate     # Windows
  ```

- [ ] 安裝套件
  ```bash
  pip install -r requirements.txt
  ```

- [ ] 驗證安裝
  ```bash
  pip list | grep -E "pymongo|aiohttp|beautifulsoup4"
  ```

### 3. MongoDB 資料準備

- [ ] 確認資料庫存在
  ```javascript
  use TW_Stock
  ```

- [ ] 確認公司基本資料 collection
  ```javascript
  db.公司基本資料.count()
  ```

- [ ] 檢查資料格式
  ```javascript
  db.公司基本資料.findOne()
  ```

- [ ] 確認股票代碼欄位存在
  - 支援欄位：stock_code, code, 股票代碼, symbol, ticker

### 4. 配置設定

- [ ] 複製環境變數範例
  ```bash
  cp .env.example .env
  ```

- [ ] 編輯 .env 檔案
  - [ ] MONGODB_URI（預設：mongodb://localhost:27017/）
  - [ ] MONGODB_DATABASE（預設：TW_Stock）
  - [ ] COMPANY_COLLECTION（預設：公司基本資料）
  - [ ] BALANCE_SHEET_COLLECTION（預設：歷史負債資料）
  - [ ] MAX_CONCURRENT_REQUESTS（建議：5）
  - [ ] REQUEST_DELAY（建議：2）
  - [ ] RETRY_TIMES（建議：3）
  - [ ] TIMEOUT（建議：30）

## 測試階段

### 5. 連接測試

- [ ] 執行 MongoDB 連接測試
  ```bash
  python test_connection.py
  ```

- [ ] 預期輸出檢查
  - [x] 資料庫連接成功
  - [x] 找到公司基本資料
  - [x] 成功取得股票代碼
  - [x] 索引建立完成

### 6. 爬蟲功能測試

- [ ] 測試單一公司爬取
  ```bash
  python test_scraper.py
  ```

- [ ] 測試多家公司爬取
  ```bash
  python test_scraper.py multi
  ```

- [ ] 檢查測試結果
  - [ ] 成功取得資料
  - [ ] 資料儲存到 MongoDB
  - [ ] 無錯誤訊息

### 7. 資料驗證

- [ ] 檢查儲存的測試資料
  ```javascript
  use TW_Stock
  db.歷史負債資料.find({stock_code: "2330"})
  ```

- [ ] 驗證資料結構
  - [ ] stock_code 存在
  - [ ] year 存在
  - [ ] season 存在
  - [ ] items 包含資料
  - [ ] crawl_time 存在

## 正式執行

### 8. 執行前最後確認

- [ ] 磁碟空間充足（建議至少 10GB）
  ```bash
  df -h
  ```

- [ ] MongoDB 記憶體足夠
- [ ] 預估執行時間已規劃
- [ ] 監控方案已準備

### 9. 執行爬蟲

選擇執行模式：

#### 模式 A：前景執行（測試用）
```bash
python main.py
```

#### 模式 B：背景執行（生產用 - Linux/Mac）
```bash
nohup python main.py > output.log 2>&1 &
```

#### 模式 C：使用 screen（推薦 - Linux/Mac）
```bash
screen -S mops_scraper
python main.py
# 按 Ctrl+A, D 離開
```

#### 模式 D：使用 tmux（推薦 - Linux/Mac）
```bash
tmux new -s mops_scraper
python main.py
# 按 Ctrl+B, D 離開
```

### 10. 執行中監控

- [ ] 監控日誌檔案
  ```bash
  tail -f scraper_*.log
  ```

- [ ] 檢查進程狀態
  ```bash
  ps aux | grep main.py
  ```

- [ ] 監控 MongoDB 資料增長
  ```javascript
  use TW_Stock
  db.歷史負債資料.count()
  ```

- [ ] 監控系統資源
  ```bash
  top
  # 或
  htop
  ```

## 執行後驗證

### 11. 資料完整性檢查

- [ ] 檢查總資料筆數
  ```javascript
  db.歷史負債資料.count()
  ```

- [ ] 檢查已完成的公司數
  ```javascript
  db.歷史負債資料.distinct("stock_code").length
  ```

- [ ] 檢查資料分布
  ```javascript
  db.歷史負債資料.aggregate([
    {$group: {
      _id: "$stock_code",
      count: {$sum: 1}
    }},
    {$sort: {count: -1}},
    {$limit: 10}
  ])
  ```

- [ ] 檢查時間範圍
  ```javascript
  db.歷史負債資料.aggregate([
    {$group: {
      _id: null,
      minYear: {$min: "$year"},
      maxYear: {$max: "$year"}
    }}
  ])
  ```

### 12. 錯誤分析

- [ ] 檢查日誌中的錯誤
  ```bash
  grep "ERROR" scraper_*.log
  ```

- [ ] 統計錯誤類型
  ```bash
  grep "ERROR" scraper_*.log | sort | uniq -c
  ```

- [ ] 查看爬蟲統計
  ```bash
  grep "爬蟲統計" scraper_*.log
  ```

### 13. 資料品質檢查

- [ ] 隨機抽查幾家公司的資料
  ```javascript
  db.歷史負債資料.find({stock_code: "2330"}).sort({year: -1, season: -1}).limit(5)
  ```

- [ ] 檢查是否有空資料
  ```javascript
  db.歷史負債資料.find({
    $or: [
      {items: {}},
      {items: null},
      {items: {$exists: false}}
    ]
  }).count()
  ```

- [ ] 檢查資料欄位完整性
  ```javascript
  db.歷史負債資料.find({
    $or: [
      {stock_code: {$exists: false}},
      {year: {$exists: false}},
      {season: {$exists: false}}
    ]
  }).count()
  ```

## 後續維護

### 14. 定期更新

- [ ] 設定排程任務（每季執行）

  **Linux Crontab 範例：**
  ```bash
  # 每季第一天凌晨 2 點執行
  0 2 1 1,4,7,10 * cd /path/to/1204_mops && /path/to/venv/bin/python main.py >> cron.log 2>&1
  ```

  **Windows 工作排程器：**
  - 開啟「工作排程器」
  - 建立基本工作
  - 設定觸發程序（每季）
  - 設定動作（執行 python main.py）

### 15. 備份策略

- [ ] MongoDB 定期備份
  ```bash
  mongodump --db TW_Stock --out /backup/$(date +%Y%m%d)
  ```

- [ ] 日誌檔案歸檔
  ```bash
  mkdir -p logs_archive
  mv scraper_*.log logs_archive/
  ```

### 16. 效能優化

- [ ] 分析執行時間
- [ ] 調整並發參數
- [ ] 優化 MongoDB 索引
- [ ] 清理舊日誌

## 故障排除

### 常見問題快速檢查

1. **MongoDB 連接失敗**
   ```bash
   # 檢查 MongoDB 服務
   sudo systemctl status mongod  # Linux
   brew services list  # Mac
   ```

2. **找不到公司資料**
   ```javascript
   // 列出所有 collections
   show collections
   // 查看資料
   db.公司基本資料.findOne()
   ```

3. **爬蟲速度太慢**
   ```env
   # 調整 .env
   MAX_CONCURRENT_REQUESTS=10
   REQUEST_DELAY=1
   ```

4. **被伺服器封鎖**
   ```env
   # 降低速度
   MAX_CONCURRENT_REQUESTS=2
   REQUEST_DELAY=5
   ```

## 檢查清單總結

### 必要檢查（❗ 必須完成）
- ❗ Python 3.8+ 已安裝
- ❗ MongoDB 已安裝並執行
- ❗ 公司基本資料 collection 有資料
- ❗ requirements.txt 套件已安裝
- ❗ .env 已設定
- ❗ test_connection.py 測試通過

### 建議檢查（⭐ 強烈建議）
- ⭐ test_scraper.py 測試通過
- ⭐ 磁碟空間充足
- ⭐ 網路連接穩定
- ⭐ 使用 screen 或 tmux 執行
- ⭐ 監控日誌檔案

### 選用檢查（💡 最佳實踐）
- 💡 建立虛擬環境
- 💡 設定自動備份
- 💡 設定排程任務
- 💡 效能監控工具

---

## 快速啟動命令

```bash
# 1. 安裝
pip install -r requirements.txt

# 2. 設定
cp .env.example .env

# 3. 測試
python test_connection.py
python test_scraper.py

# 4. 執行
python main.py
```

**完成檢查清單後，系統即可投入生產使用！**

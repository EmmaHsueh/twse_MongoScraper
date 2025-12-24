# Tor 爬蟲使用指南

## 什麼是 Tor？

Tor（The Onion Router）是一個匿名網絡，可以：
- 隱藏您的真實 IP 地址
- 避免被網站追蹤
- 繞過 IP 封鎖

## 安裝與設置

### 1. 安裝 Tor（已完成）

```bash
# macOS（使用 Homebrew）
brew install tor

# 檢查是否安裝成功
which tor
```

### 2. 安裝 Python 套件

```bash
# 啟動虛擬環境
source venv/bin/activate

# 安裝 PySocks（用於 SOCKS 代理）
pip install pysocks
```

### 3. 啟動 Tor 服務

#### 方法 1：前台運行（可看到即時輸出）
```bash
tor
```

#### 方法 2：背景運行（推薦）
```bash
nohup tor > tor.log 2>&1 &

# 查看日誌
tail -f tor.log

# 查看 Tor 進程
ps aux | grep tor
```

#### 方法 3：停止 Tor
```bash
# 找到 Tor 進程 ID
ps aux | grep tor

# 停止 Tor
kill <PID>
```

## 使用方式

### 測試 Tor 連接

```bash
python test_tor_connection.py
```

應該會看到：
```
✓ Tor 連接成功！IP 已改變
  真實 IP: 36.226.206.235
  Tor IP:  185.220.100.253
```

### 使用 Tor 爬蟲

```bash
python query6_1_scraper_tor.py
```

## 重要提醒

### ✅ 優點
- 隱藏真實 IP
- 避免 IP 被封鎖
- 可以長時間爬取

### ⚠️ 缺點
- **速度較慢**（比正常慢 3-5 倍）
- 連接可能不穩定
- 不適合大量快速爬取

### 💡 建議
1. **推薦模式**：個別爬取（選項 3）或部分爬取（選項 2）
2. **不推薦**：完整爬取所有公司（會花費數小時）
3. **延遲設置**：Tor 版本已自動增加延遲（3-6 秒）

## 常見問題

### Q1: Tor 連接失敗？
```bash
# 檢查 Tor 是否運行
ps aux | grep tor

# 查看 Tor 日誌
tail -20 tor.log

# 重啟 Tor
killall tor
tor
```

### Q2: 如何更換 IP？
- **簡單方法**：重啟 Tor 服務
- **進階方法**：配置 Tor 控制端口（需要額外設置）

```bash
# 重啟 Tor 獲得新 IP
killall tor
tor &
```

### Q3: 速度太慢怎麼辦？
- 這是正常的，Tor 本身就比較慢
- 建議減少爬取數量
- 或改用正常爬蟲（`query6_1_scraper.py`）

## 文件對照表

| 文件名 | 說明 | 使用 Tor |
|--------|------|---------|
| `query6_1_scraper.py` | 正常爬蟲 | ❌ |
| `query6_1_scraper_tor.py` | Tor 爬蟲 | ✅ |
| `test_tor_connection.py` | 測試 Tor | ✅ |

## 完整流程範例

```bash
# 1. 啟動 Tor
nohup tor > tor.log 2>&1 &

# 2. 等待 5 秒讓 Tor 啟動
sleep 5

# 3. 測試 Tor 連接
python test_tor_connection.py

# 4. 運行 Tor 爬蟲
python query6_1_scraper_tor.py

# 選擇模式 3（個別爬取）
# 輸入公司代號：2330,1101

# 5. 完成後停止 Tor
killall tor
```

## 技術細節

### Tor 代理設置
```python
# Chrome 代理設置
chrome_options.add_argument('--proxy-server=socks5://127.0.0.1:9050')
```

### 預設端口
- SOCKS 代理：`127.0.0.1:9050`
- 控制端口：`127.0.0.1:9051`（需額外配置）

### IP 檢查服務
- `https://api.ipify.org` - 顯示當前 IP
- `https://check.torproject.org` - 檢查是否使用 Tor

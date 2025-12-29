# TW Stock MOPS 爬蟲專案

爬取台灣上市櫃公司的財務資料：
- 資產負債表
- 綜合損益表
- 現金流量表
- 每月營收
- 內部人持股異動事後申報表


## 檔案結構

```
TW_Stock/
  ├── venv/                                # Python 虛擬環境
  ├── requirements.txt                     # 套件相依性
  ├── run.sh                               # 快速啟動腳本
  ├── .gitignore                           # Git 忽略檔案
  │
  ├── 【核心模組】
  ├── mops_scraper.py                      # MOPS 通用爬蟲引擎 (Selenium)
  ├── mongodb_helper.py                    # MongoDB 資料庫操作輔助模組
  │
  ├── 【財報爬蟲】
  ├── batch_scraper_optimized.py           # 資產負債表爬蟲 (批次優化版)
  ├── income_statement_scraper.py          # 綜合損益表爬蟲
  ├── cashflow_scraper.py                  # 現金流量表爬蟲
  │
  ├── 【營收爬蟲】
  ├── monthly_revenue_scraper.py           # 每月營收爬蟲 (Requests)
  │
  ├── 【內部人持股爬蟲】
  ├── query6_1_scraper.py                  # 內部人持股異動事後申報表爬蟲
  └── query6_1_scraper_parallel.py         # 內部人持股爬蟲 (多進程並行版)
```

## 技術架構

### 兩種爬蟲技術

| 項目 | Selenium 爬蟲 | Requests 爬蟲 |
|-----|--------------|--------------|
| 使用檔案 | mops_scraper.py<br>batch_scraper_optimized.py<br>income_statement_scraper.py<br>cashflow_scraper.py<br>query6_1_scraper.py | monthly_revenue_scraper.py |
| 技術 | Selenium + ChromeDriver | Requests + Pandas |
| 用途 | 財務報表、內部人持股<br>(需動態查詢) | 每月營收<br>(固定網址格式) |
| 速度 | 較慢 | 較快 |
| 適用場景 | 複雜查詢流程 | 簡單網址規則 |

## 快速開始

### 1. 環境準備

```bash
# 啟動虛擬環境
source venv/bin/activate

# 確認套件已安裝
pip list | grep -E "selenium|pandas|pymongo|requests"
```

### 2. MongoDB 連線測試

```bash
python mongodb_helper.py
```

### 3. 執行爬蟲

#### 資產負債表
```bash
python batch_scraper_optimized.py
```

#### 綜合損益表
```bash
python income_statement_scraper.py
```

#### 現金流量表
```bash
python cashflow_scraper.py
```

#### 每月營收
```bash
python monthly_revenue_scraper.py
```

#### 內部人持股異動
```bash
# 單進程版本
python query6_1_scraper.py

# 多進程並行版本 (4個進程)
python query6_1_scraper_parallel.py
```


## 共同函式庫

本專案的各爬蟲程式使用以下共同函式：

### MongoDB 資料庫操作

所有爬蟲都使用這些函式進行資料庫操作：

```python
# 公司驗證
company_exists(company_code)              # 檢查公司是否存在於基本資料中

# 資料去重
xxx_exists(company_code, year, season)    # 檢查資料是否已存在
balance_sheet_exists()                    # 資產負債表
income_exists()                           # 綜合損益表
cashflow_exists()                         # 現金流量表
_revenue_exists()                         # 每月營收

# 資料插入
insert_xxx(data)                          # 插入單筆資料
insert_xxx_batch(data_list)               # 批次插入資料

# 索引管理
_create_indexes()                         # 建立 MongoDB 索引

# 連線管理
close()                                   # 關閉 MongoDB 連線
```

### Selenium 爬蟲操作

使用 Selenium 的爬蟲共享這些核心函式：

```python
# 網頁操作
select_market(market_type)                # 選擇市場別 (sii/otc/rotc)
input_year(year)                          # 輸入年度
select_season(season)                     # 選擇季別
input_company_code(company_code)          # 輸入公司代號
select_custom_date()                      # 選擇自訂日期

# 查詢執行
click_query_button()                      # 點擊查詢按鈕
wait_for_loading_to_disappear()          # 等待載入完成

# 結果取得
get_result_url_from_session_storage()    # 從 sessionStorage 取得結果 URL
get_query_results_from_session_storage() # 從 sessionStorage 取得查詢結果

# 瀏覽器管理
close()                                   # 關閉瀏覽器
```

### 資料解析

共同的資料解析邏輯：

```python
# HTML 表格解析
parse_all_companies_from_table(html_content, year, season)
    # 使用 pandas.read_html() 解析表格
    # 尋找公司代號欄位
    # 清理並驗證公司代號
    # 轉換數值格式
    # 返回結構化資料列表

# 欄位處理
parse_titles_to_columns(titles)           # 將巢狀標題轉換為欄位名稱

# 營收表格解析
_parse_revenue_table(html_content, year, month, market_type)
```

### 批次爬取流程

財報爬蟲 (資產負債表、損益表、現金流量表) 的共同爬取流程：

```python
# 單次批次爬取
scrape_and_save_batch(market_type, year, season)
    # 1. 執行查詢取得結果 URL
    # 2. 取得頁面內容
    # 3. 解析所有公司資料
    # 4. 過濾已存在的資料
    # 5. 批次儲存到 MongoDB
    # 6. 返回成功儲存的筆數

# 歷史資料完整爬取
scrape_all_history(market_types, start_year, end_year)
    # 遍歷市場別、年度、季別
    # 呼叫 scrape_and_save_batch()
    # 統計總成功筆數
    # 加入延遲避免被封鎖
```

### 輔助工具函式

```python
# 時間範圍生成
generate_year_month_list(start_year, start_month, end_year, end_month)
    # 生成 [(year, month), ...] 列表
    # 用於批次爬取所有年月

# URL 建構
_build_url(market_type, year, month, data_type)
    # 根據年份和參數動態建立爬蟲網址
    # 處理不同年份的 URL 格式差異

# 資料驗證
_is_valid_company(company_code)           # 檢查公司代號是否有效
_get_valid_company_codes()                # 取得所有有效公司代號集合

# 統計資訊
get_statistics()                          # 取得資料庫統計資訊
```

### 程式碼重用模式

所有爬蟲遵循相同的設計模式：

```python
class XXXScraper:
    def __init__(self, mongodb_uri, headless):
        # 初始化 MongoDB 連線
        # 初始化爬蟲 (Selenium 或 Requests)
        # 建立索引

    def company_exists(self, company_code):
        # 檢查公司是否存在

    def xxx_exists(self, company_code, year, season/month):
        # 檢查資料是否已存在

    def insert_xxx(self, data):
        # 插入單筆資料

    def insert_xxx_batch(self, data_list):
        # 批次插入資料

    def parse_xxx(self, html_content, ...):
        # 解析資料

    def scrape_and_save_batch(self, ...):
        # 爬取並儲存批次資料

    def scrape_all_history(self, ...):
        # 爬取所有歷史資料

    def close(self):
        # 關閉連線
```

## 注意事項

### 1. 反爬蟲機制
- 每次請求間隔 2-5 秒
- 使用真實 User-Agent
- 隱藏 webdriver 特徵
- 隨機延遲時間

### 2. 系統需求
- Chrome 瀏覽器 (最新版本)
- ChromeDriver (自動下載)
- MongoDB 



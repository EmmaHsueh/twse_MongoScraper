"""
配置文件
"""
import os
from dotenv import load_dotenv

load_dotenv()

# MongoDB 配置
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
MONGODB_DATABASE = os.getenv('MONGODB_DATABASE', 'TW_Stock')
COMPANY_COLLECTION = os.getenv('COMPANY_COLLECTION', '公司基本資料')
BALANCE_SHEET_COLLECTION = os.getenv('BALANCE_SHEET_COLLECTION', '歷史負債資料')

# 爬蟲配置
MAX_CONCURRENT_REQUESTS = int(os.getenv('MAX_CONCURRENT_REQUESTS', '5'))
REQUEST_DELAY = float(os.getenv('REQUEST_DELAY', '2'))
RETRY_TIMES = int(os.getenv('RETRY_TIMES', '3'))
TIMEOUT = int(os.getenv('TIMEOUT', '30'))

# MOPS API 配置
MOPS_BASE_URL = 'https://mops.twse.com.tw/mops/web/ajax_t163sb05'
MOPS_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Referer': 'https://mops.twse.com.tw/mops/web/t163sb05',
    'Origin': 'https://mops.twse.com.tw',
}

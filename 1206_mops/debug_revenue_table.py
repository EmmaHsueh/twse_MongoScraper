#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
除錯：檢查營收表格結構
"""

import requests
import pandas as pd
import urllib3

# 關閉 SSL 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def debug_table_structure(url):
    """檢查表格結構"""
    print(f"\n{'='*60}")
    print(f"檢查 URL: {url}")
    print(f"{'='*60}")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }

    try:
        # 發送請求
        response = requests.get(url, headers=headers, timeout=30, verify=False)
        response.encoding = 'big5'

        # 解析表格
        tables = pd.read_html(response.text)

        print(f"\n找到 {len(tables)} 個表格\n")

        for i, table in enumerate(tables):
            print(f"\n{'='*60}")
            print(f"表格 {i+1}")
            print(f"{'='*60}")
            print(f"維度: {table.shape}")
            print(f"\n欄位列表:")
            for j, col in enumerate(table.columns):
                print(f"  [{j}] {col} (類型: {type(col).__name__})")

            print(f"\n前 5 列資料:")
            print(table.head())

            print(f"\n前 2 列原始資料:")
            for idx, row in table.head(2).iterrows():
                print(f"\n第 {idx} 列:")
                for col in table.columns:
                    print(f"  {col}: {row[col]} (類型: {type(row[col]).__name__})")

    except Exception as e:
        print(f"錯誤: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 測試民國 91 年 1 月上市公司
    debug_table_structure("https://mopsov.twse.com.tw/nas/t21/sii/t21sc03_91_1.html")

    # 測試民國 100 年 1 月上市公司 (國內)
    debug_table_structure("https://mopsov.twse.com.tw/nas/t21/sii/t21sc03_100_1_0.html")

    # 測試民國 113 年 1 月上市公司 (國內)
    debug_table_structure("https://mopsov.twse.com.tw/nas/t21/sii/t21sc03_113_1_0.html")

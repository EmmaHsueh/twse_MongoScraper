#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每月營收爬蟲 - 透過動態更改網址參數爬取資料
https://mopsov.twse.com.tw/nas/t21/sii/t21sc03_91_1.html
"""

import time
import requests
import pandas as pd
from pymongo import MongoClient, ASCENDING
from datetime import datetime
import urllib3

# 關閉 SSL 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class MonthlyRevenueScraper:
    def __init__(self, connection_string="mongodb://localhost:27017/"):
        """
        初始化每月營收爬蟲

        Args:
            connection_string: MongoDB 連線字串
        """
        # MongoDB 設定
        self.client = MongoClient(connection_string)
        self.db = self.client['TW_Stock']
        self.company_basic = self.db['公司基本資料']
        self.revenue_collection = self.db['每月營收']

        # 建立索引
        self._create_indexes()

        # 取得有效公司代號列表
        self.valid_company_codes = self._get_valid_company_codes()
        print(f"✓ 載入 {len(self.valid_company_codes)} 家有效公司代號")

        # 設定請求 headers
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
        }

    def _create_indexes(self):
        """建立 MongoDB 索引"""
        try:
            # 公司基本資料索引
            self.company_basic.create_index([("公司 代號", ASCENDING)], unique=True)

            # 每月營收：複合索引 (公司代號 + 年度 + 月份)
            self.revenue_collection.create_index(
                [("公司代號", ASCENDING), ("年度", ASCENDING), ("月份", ASCENDING)],
                unique=True
            )
            print("✓ MongoDB 索引建立完成")
        except Exception as e:
            print(f"建立索引時發生警告: {e}")

    def _get_valid_company_codes(self):
        """
        從公司基本資料中取得所有有效的公司代號

        Returns:
            set: 公司代號集合
        """
        try:
            companies = self.company_basic.find({}, {"公司 代號": 1, "_id": 0})
            codes = {c["公司 代號"] for c in companies if "公司 代號" in c}
            return codes
        except Exception as e:
            print(f"✗ 取得公司代號失敗: {e}")
            return set()

    def _is_valid_company(self, company_code):
        """
        檢查公司代號是否在公司基本資料中

        Args:
            company_code: 公司代號

        Returns:
            bool: 是否為有效公司
        """
        return company_code in self.valid_company_codes

    def _revenue_exists(self, company_code, year, month):
        """
        檢查營收資料是否已存在

        Args:
            company_code: 公司代號
            year: 民國年度
            month: 月份

        Returns:
            bool: 是否存在
        """
        return self.revenue_collection.find_one({
            "公司代號": company_code,
            "年度": year,
            "月份": month
        }) is not None

    def _insert_revenue(self, data):
        """
        插入營收資料

        Args:
            data: 資料字典

        Returns:
            bool: 是否成功
        """
        try:

            # 使用 upsert 避免重複
            self.revenue_collection.update_one(
                {
                    "公司代號": data["公司代號"],
                    "年度": data["年度"],
                    "月份": data["月份"]
                },
                {"$set": data},
                upsert=True
            )
            return True
        except Exception as e:
            print(f"✗ 插入資料失敗 ({data.get('公司代號', 'N/A')}): {e}")
            return False

    def _build_url(self, market_type, year, month, data_type=None):
        """
        建立爬蟲網址

        Args:
            market_type: 市場別 ("sii": 上市, "otc": 上櫃, "rotc": 興櫃)
            year: 民國年度 (例如: 91, 100, 113)
            month: 月份 (1-12)
            data_type: 資料類型 (None: 91-99年無分國內外, "0": 國內, "1": 國外)

        Returns:
            str: 完整的 URL
        """
        base_url = "https://mopsov.twse.com.tw/nas/t21"

        # 根據年份決定是否需要加上國內外標記
        if year < 100:
            # 民國 91-99 年：無分國內外
            url = f"{base_url}/{market_type}/t21sc03_{year}_{month}.html"
        else:
            # 民國 100 年起：分國內外
            if data_type is None:
                raise ValueError("民國 100 年起需要指定 data_type (0: 國內, 1: 國外)")
            url = f"{base_url}/{market_type}/t21sc03_{year}_{month}_{data_type}.html"

        return url

    def _parse_revenue_table(self, html_content, year, month, market_type):
        """
        解析營收表格資料

        Args:
            html_content: HTML 內容
            year: 年度
            month: 月份
            market_type: 市場別

        Returns:
            list: 解析後的資料列表
        """
        try:
            # 使用 pandas 讀取 HTML 表格
            tables = pd.read_html(html_content)

            if not tables:
                print(f"  ✗ 未找到表格資料")
                return []

            revenue_data = []
            valid_count = 0
            skip_count = 0

            # 處理所有表格（每個產業別一個表格）
            for table_idx, df in enumerate(tables):
                # 尋找公司代號欄位
                # 欄位可能是 tuple 格式: ('Unnamed: 0_level_0', '公司 代號')
                code_column = None
                for col in df.columns:
                    # 處理 tuple 格式
                    if isinstance(col, tuple):
                        col_str = ' '.join(str(c) for c in col)
                    else:
                        col_str = str(col)

                    col_str = col_str.strip()

                    if '公司 代號' in col_str or '公司代號' in col_str:
                        code_column = col
                        break

                # 如果這個表格沒有公司代號欄位，跳過
                if code_column is None:
                    continue

                # 逐列處理
                for idx, row in df.iterrows():
                    try:
                        # 取得公司代號
                        company_code = str(row[code_column]).strip()

                        # 檢查是否為有效的公司代號 (純數字)
                        if not company_code.isdigit():
                            continue

                        # 檢查公司是否在基本資料中
                        if not self._is_valid_company(company_code):
                            skip_count += 1
                            continue

                        # 檢查是否已存在
                        if self._revenue_exists(company_code, year, month):
                            continue

                        # 建立資料記錄
                        record = {
                            "公司代號": company_code,
                            "年度": year,
                            "月份": month,
                            "市場別": market_type,
                        }

                        # 將所有欄位加入記錄
                        for col in df.columns:
                            # 處理欄位名稱
                            if isinstance(col, tuple):
                                # 對於 tuple，取第二個元素（實際欄位名稱）
                                # 例如: ('營業收入', '當月營收') -> '當月營收'
                                if len(col) >= 2:
                                    col_name = str(col[1]).strip()
                                    # 如果第一個元素不是 Unnamed，加上前綴
                                    if not str(col[0]).startswith('Unnamed'):
                                        col_name = f"{col[0]}_{col_name}"
                                else:
                                    col_name = str(col).strip()
                            else:
                                col_name = str(col).strip()

                            # 跳過公司代號欄位
                            if col == code_column:
                                continue

                            # 處理數值型態
                            value = row[col]
                            if pd.notna(value):
                                # 嘗試轉換為數值
                                try:
                                    # 移除逗號並轉換
                                    if isinstance(value, str):
                                        value = value.replace(',', '')
                                        if value and value != '-':
                                            value = float(value) if '.' in value else int(value)
                                        else:
                                            value = None
                                except:
                                    pass  # 保持原值

                                if value is not None:
                                    record[col_name] = value

                        revenue_data.append(record)
                        valid_count += 1

                    except Exception as e:
                        continue

            print(f"  ✓ 解析完成: {valid_count} 筆有效資料", end="")
            if skip_count > 0:
                print(f" (跳過 {skip_count} 筆不在基本資料中)")
            else:
                print()

            return revenue_data

        except Exception as e:
            print(f"  ✗ 解析表格失敗: {e}")
            return []

    def scrape_single_month(self, market_type, year, month, data_type=None, delay=2):
        """
        爬取單一月份的營收資料

        Args:
            market_type: 市場別 ("sii", "otc", "rotc")
            year: 民國年度
            month: 月份 (1-12)
            data_type: 資料類型 (None: 91-99年, "0": 國內, "1": 國外)
            delay: 請求間隔秒數

        Returns:
            int: 成功插入的資料筆數
        """
        try:
            # 建立 URL
            url = self._build_url(market_type, year, month, data_type)

            # 顯示資訊
            market_name = {"sii": "上市", "otc": "上櫃", "rotc": "興櫃"}.get(market_type, market_type)
            data_type_name = ""
            if year >= 100:
                data_type_name = " (國內)" if data_type == "0" else " (國外)"

            print(f"\n[{market_name}] {year}年{month}月{data_type_name}")
            print(f"  URL: {url}")

            # 發送請求 (跳過 SSL 驗證)
            response = requests.get(url, headers=self.headers, timeout=30, verify=False)

            # 檢查狀態碼
            if response.status_code == 404:
                print(f"  ⚠ 資料不存在 (404)")
                return 0

            response.raise_for_status()

            # 設定正確的編碼
            response.encoding = 'big5'

            # 解析資料
            revenue_data = self._parse_revenue_table(
                response.text,
                year,
                month,
                market_type
            )

            # 插入資料庫
            success_count = 0
            for data in revenue_data:
                if self._insert_revenue(data):
                    success_count += 1

            if success_count > 0:
                print(f"  ✓ 成功儲存 {success_count} 筆資料到 MongoDB")

            # 延遲避免請求過於頻繁
            time.sleep(delay)

            return success_count

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                print(f"  ⚠ 資料不存在 (404)")
            else:
                print(f"  ✗ HTTP 錯誤: {e}")
            return 0
        except Exception as e:
            print(f"  ✗ 爬取失敗: {e}")
            return 0

    def scrape_all(self, start_year=91, end_year=113, delay=2):
        """
        爬取所有年份、所有市場、所有月份的營收資料

        Args:
            start_year: 起始年度 (預設: 91)
            end_year: 結束年度 (預設: 113)
            delay: 請求間隔秒數
        """
        market_types = ["sii", "otc", "rotc"]
        total_success = 0
        total_requests = 0

        print(f"\n{'='*60}")
        print(f"開始爬取每月營收資料")
        print(f"年度範圍: {start_year}-{end_year}")
        print(f"市場別: 上市、上櫃、興櫃")
        print(f"{'='*60}")

        for year in range(start_year, end_year + 1):
            print(f"\n{'='*60}")
            print(f"處理 {year} 年度資料")
            print(f"{'='*60}")

            for market_type in market_types:
                for month in range(1, 13):
                    if year < 100:
                        # 民國 91-99 年：無分國內外
                        total_requests += 1
                        success = self.scrape_single_month(
                            market_type, year, month,
                            data_type=None,
                            delay=delay
                        )
                        total_success += success
                    else:
                        # 民國 100 年起：分國內外
                        for data_type in ["0", "1"]:
                            total_requests += 1
                            success = self.scrape_single_month(
                                market_type, year, month,
                                data_type=data_type,
                                delay=delay
                            )
                            total_success += success

        print(f"\n{'='*60}")
        print(f"爬取完成!")
        print(f"總請求次數: {total_requests}")
        print(f"成功儲存: {total_success} 筆資料")
        print(f"資料庫總筆數: {self.revenue_collection.count_documents({})}")
        print(f"{'='*60}")

    def scrape_year_range(self, start_year, end_year, delay=2):
        """
        爬取指定年份範圍的資料

        Args:
            start_year: 起始年度
            end_year: 結束年度
            delay: 請求間隔秒數
        """
        self.scrape_all(start_year, end_year, delay)

    def get_statistics(self):
        """
        取得資料庫統計資訊

        Returns:
            dict: 統計資訊
        """
        stats = {
            "總筆數": self.revenue_collection.count_documents({}),
            "上市筆數": self.revenue_collection.count_documents({"市場別": "sii"}),
            "上櫃筆數": self.revenue_collection.count_documents({"市場別": "otc"}),
            "興櫃筆數": self.revenue_collection.count_documents({"市場別": "rotc"}),
        }
        return stats

    def close(self):
        """關閉 MongoDB 連線"""
        if self.client:
            self.client.close()
            print("\n✓ MongoDB 連線已關閉")


def main():
    """主程式"""
    scraper = MonthlyRevenueScraper()

    try:
        # 選擇執行模式
        print("\n每月營收爬蟲")
        print("="*60)
        print("1. 爬取所有資料 (民國 91-112 年)")
        print("2. 爬取指定年份範圍")
        print("3. 爬取單一年度")
        print("4. 查看資料庫統計")
        print("="*60)

        choice = input("\n請選擇模式 (1-4): ").strip()

        if choice == "1":
            # 爬取所有資料
            confirm = input("\n確定要爬取所有資料嗎? (y/n): ").strip().lower()
            if confirm == 'y':
                scraper.scrape_all(start_year=91, end_year=112, delay=2)

        elif choice == "2":
            # 爬取指定年份範圍
            start_year = int(input("請輸入起始年度 (民國): "))
            end_year = int(input("請輸入結束年度 (民國): "))
            scraper.scrape_year_range(start_year, end_year, delay=2)

        elif choice == "3":
            # 爬取單一年度
            year = int(input("請輸入年度 (民國): "))
            scraper.scrape_year_range(year, year, delay=2)

        elif choice == "4":
            # 查看統計
            stats = scraper.get_statistics()
            print("\n資料庫統計:")
            print(f"  總筆數: {stats['總筆數']}")
            print(f"  上市: {stats['上市筆數']}")
            print(f"  上櫃: {stats['上櫃筆數']}")
            print(f"  興櫃: {stats['興櫃筆數']}")

        else:
            print("無效的選擇")

    except KeyboardInterrupt:
        print("\n\n程式已被使用者中斷")
    except Exception as e:
        print(f"\n發生錯誤: {e}")
        import traceback
        traceback.print_exc()
    finally:
        scraper.close()


if __name__ == "__main__":
    main()
